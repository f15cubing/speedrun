#!/usr/bin/env python3
"""GRE fork — headless two-way sync proof (execution-plan Block C, 7b).

Two peers on our fork's engine + our self-hosted `anki-sync-server` prove:

  PHASE 1 — no-loss (10 + 10).  Peer A ("desktop") reviews 10 cards offline; peer B
    ("phone") reviews 10 *different* cards offline; both reconnect → **all 20 reviews
    land on both peers** (revlog union) with `pragma quick_check = ok`. Pure additive
    merge — no scheduling conflict, nothing dropped.

  PHASE 2 — same-card conflict (pure review divergence).  Both peers review the *same*
    graduated card C offline: A answers Good (interval grows), B answers Again (a lapse:
    interval collapses, +1 lapse) with a strictly later `mod`. Reconnect in a controlled
    order (A, then B, then A pulls). The documented rule holds:
      * **revlog union**  — BOTH reviews of C survive on both peers (+2 rows).
      * **scheduling LWW** — the later-`mod` writer (B) wins; A's offline scheduling for
        C is overwritten and both peers converge on B's state.
    Determinism comes from controlling sync order + the `mod` timestamps (recorded per
    peer), NOT a code-level tie-break (the device-UUID tie-break is DEFERRED — see
    docs/codebase/sync.md). This is the pure-review-divergence case the doc requires
    (a shared schema, so it merges instead of degrading to a forced full sync).

Server must already be running on OUR engine:

    FORK_ANKI=/…/anki SYNC_PORT=8090 SYNC_BASE=…/sync/.sync-data-7b sync/run-sync-server.sh
    # then, with the same FORK_ANKI build's python:
    SYNC_ENDPOINT=http://127.0.0.1:8090/ \
      PYTHONPATH=$FORK_ANKI/out/pylib $FORK_ANKI/out/pyenv/bin/python sync/two_way_sync_7b.py

Exit code 0 iff both phases pass. LOCAL TEST ONLY (creds are throwaways).
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

from anki.collection import Collection

ENDPOINT = os.environ.get("SYNC_ENDPOINT", "http://127.0.0.1:8090/")
USER, PASSWORD = "greuser", "grepass"
TAG = "topic::algebra::linear_equations"
N_OFFLINE = 10  # reviews per side in phase 1
SCHED_COLS = "type,queue,due,ivl,factor,reps,lapses,left,odue,mod"  # excludes usn/id


def _req_name(out) -> str:
    for name in ("NO_CHANGES", "NORMAL_SYNC", "FULL_SYNC", "FULL_DOWNLOAD", "FULL_UPLOAD"):
        if getattr(out, name, object()) == out.required:
            return name
    return f"?({out.required})"


def _sync(col: Collection, *, prefer_upload: bool) -> str:
    """Perform one sync; resolve a required full sync in the intended direction.
    Returns the ChangesRequired name so callers can assert normal (mergeable) syncs.

    A full sync must be wrapped in close_for_full_sync()/reopen(after_full_sync=True)
    exactly as the desktop does (aqt/sync.py) — otherwise the handle can't track later
    changes and subsequent normal syncs wrongly report NO_CHANGES."""
    auth = col.sync_login(USER, PASSWORD, ENDPOINT)
    out = col.sync_collection(auth, False)  # performs a NORMAL sync in-place
    name = _req_name(out)
    upload: bool | None = None
    if out.required == out.FULL_UPLOAD:
        upload = True
    elif out.required == out.FULL_DOWNLOAD:
        upload = False
    elif out.required == out.FULL_SYNC:
        upload = prefer_upload
    if upload is not None:
        col.close_for_full_sync()
        col.full_upload_or_download(auth=auth, server_usn=None, upload=upload)
        col.reopen(after_full_sync=True)
    return name


def _answer(col: Collection, cid: int, ease: int) -> int:
    """Review one specific card by id (start_timer mirrors what getCard() does). Returns mod."""
    card = col.get_card(cid)
    card.start_timer()
    col.sched.answerCard(card, ease)
    return col.db.scalar("select mod from cards where id=?", cid)


def _snap(col: Collection, cid: int) -> tuple:
    return tuple(col.db.first(f"select {SCHED_COLS} from cards where id=?", cid))


def _fmt(snap: tuple) -> str:
    return ", ".join(f"{k}={v}" for k, v in zip(SCHED_COLS.split(","), snap))


def _revlog_total(col: Collection) -> int:
    return col.db.scalar("select count() from revlog")


def _revlog_for(col: Collection, cid: int) -> int:
    return col.db.scalar("select count() from revlog where cid=?", cid)


def _qc(col: Collection) -> str:
    return col.db.scalar("pragma quick_check")


def _identity(col: Collection, label: str) -> str:
    crt = col.db.scalar("select crt from col")
    return f"{label}: path={Path(col.path).name} crt={crt}"


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="sync7b-"))
    A = Collection(str(work / "A_desktop.anki2"))
    B = Collection(str(work / "B_phone.anki2"))

    import anki.buildinfo as bi
    print("=" * 82)
    print("GRE fork — 7b two-way sync proof (10+10 no-loss  +  same-card conflict / LWW)")
    print(f"engine   : anki {bi.version}  (buildhash {bi.buildhash})")
    print(f"server   : {ENDPOINT}   account: {USER}")
    print(f"started  : {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 82)

    try:
        # ---------------------------------------------------------------- SETUP / baseline
        m = A.models.by_name("Basic")
        for i in range(30):
            note = A.new_note(m)
            note["Front"], note["Back"] = f"q{i}: 2x+{i}=0, x=?", f"x=-{i}/2"
            note.tags = [TAG]
            A.add_note(note, 1)  # deck 1 = Default
        cids = A.db.list("select id from cards order by id")
        C = cids[20]  # the same-card-conflict card (disjoint from the 0..19 no-loss sets)
        for _ in range(4):  # graduate C into the review state (so a lapse is dramatic)
            _answer(A, C, 4)  # Easy
        base_total = _revlog_total(A)
        base_C = _revlog_for(A, C)
        print(f"SETUP    : A seeded 30 cards; graduated conflict card C={C} "
              f"(baseline revlog={base_total}, C revlog={base_C})")

        # Publish the shared baseline: A full-uploads, B full-downloads → identical schema.
        s_up = _sync(A, prefer_upload=True)
        s_dn = _sync(B, prefer_upload=False)
        print(f"         : A publish={s_up}  B pull={s_dn}")
        assert _revlog_total(B) == base_total, "baseline did not fully cross to B"
        assert _snap(A, C) == _snap(B, C), "C differs after baseline full sync"
        print(f"         : {_identity(A, 'peer A (desktop)')}")
        print(f"         : {_identity(B, 'peer B (phone)  ')}")

        # ---------------------------------------------------------------- PHASE 1: no-loss
        a_set = cids[0:N_OFFLINE]           # A reviews these 10 offline
        b_set = cids[N_OFFLINE:2 * N_OFFLINE]  # B reviews these *other* 10 offline
        # Space reviews out: a revlog row's primary key is its epoch-ms timestamp, so a
        # sub-ms automated loop would make A and B mint IDENTICAL ids and the merge would
        # collapse the colliding rows. Real devices review seconds apart; a few ms here
        # gives each review a distinct id and keeps A's/B's id windows disjoint.
        for cid in a_set:
            _answer(A, cid, 3)  # Good
            time.sleep(0.006)
        time.sleep(0.2)
        for cid in b_set:
            _answer(B, cid, 3)  # Good
            time.sleep(0.006)
        print(f"\nPHASE 1  : A reviewed {len(a_set)} cards offline; "
              f"B reviewed {len(b_set)} *different* cards offline (both disconnected)")
        print(f"         : local before reconnect  A revlog={_revlog_total(A)} "
              f"B revlog={_revlog_total(B)}  (baseline {base_total} + 10 each)")
        # reconnect: A pushes, B pushes+merges, A pulls B's — all mergeable (no full sync)
        r1 = _sync(A, prefer_upload=True)
        r2 = _sync(B, prefer_upload=True)
        r3 = _sync(A, prefer_upload=True)
        print(f"         : reconnect syncs = A:{r1}  B:{r2}  A:{r3}")
        assert {r1, r2, r3} <= {"NO_CHANGES", "NORMAL_SYNC"}, \
            f"expected mergeable syncs, got {r1},{r2},{r3}"
        # every one of the 20 offline reviews present on BOTH peers (revlog union)
        landed_A = sum(_revlog_for(A, cid) >= 1 for cid in a_set + b_set)
        landed_B = sum(_revlog_for(B, cid) >= 1 for cid in a_set + b_set)
        totA, totB = _revlog_total(A), _revlog_total(B)
        qcA, qcB = _qc(A), _qc(B)
        print(f"         : reviews landed on A={landed_A}/20  on B={landed_B}/20  "
              f"| revlog A={totA} B={totB} (baseline {base_total}+20={base_total + 20})")
        print(f"         : quick_check A={qcA} B={qcB}")
        assert landed_A == 20 and landed_B == 20, "some of the 20 reviews did not land on both"
        assert totA == base_total + 20 and totB == base_total + 20, "revlog union count wrong"
        assert qcA == "ok" and qcB == "ok", "quick_check failed after phase 1"
        print("PHASE 1  : PASS — all 20 offline reviews landed on both peers, no corruption")

        # ---------------------------------------------------------------- PHASE 2: conflict
        pre = _snap(A, C)
        assert pre == _snap(B, C), "C diverged before the conflict test"
        mod_A = _answer(A, C, 3)   # A: Good on C  → interval grows
        snap_A = _snap(A, C)
        time.sleep(1.2)            # ensure B's mod is strictly later (LWW key is mod seconds)
        mod_B = _answer(B, C, 1)   # B: Again on C → lapse (interval collapses, +1 lapse)
        snap_B = _snap(B, C)
        print(f"\nPHASE 2  : same card C={C} reviewed on BOTH peers offline (pure review divergence)")
        print(f"         : A(Good)  mod={mod_A}  -> {_fmt(snap_A)}")
        print(f"         : B(Again) mod={mod_B}  -> {_fmt(snap_B)}")
        assert mod_B > mod_A, f"expected B's mod ({mod_B}) later than A's ({mod_A})"
        # controlled reconnect order: A first, then B (later mod → wins), then A pulls
        c1 = _sync(A, prefer_upload=True)
        c2 = _sync(B, prefer_upload=True)
        c3 = _sync(A, prefer_upload=True)
        print(f"         : reconnect syncs (A,then B,then A) = {c1}, {c2}, {c3}")
        assert {c1, c2, c3} <= {"NO_CHANGES", "NORMAL_SYNC"}, \
            f"same-card conflict must merge, not full-sync: {c1},{c2},{c3}"
        final_A, final_B = _snap(A, C), _snap(B, C)
        revC_A, revC_B = _revlog_for(A, C), _revlog_for(B, C)
        qcA, qcB = _qc(A), _qc(B)
        print(f"         : converged C on A -> {_fmt(final_A)}")
        print(f"         : converged C on B -> {_fmt(final_B)}")
        print(f"         : C revlog A={revC_A} B={revC_B} (baseline {base_C} + 2 = {base_C + 2})")
        print(f"         : quick_check A={qcA} B={qcB}")
        # scheduling LWW: both converge, and on B's (later-mod) state, overwriting A's
        assert final_A == final_B, "peers did not converge on the conflict card"
        assert final_A == snap_B, "LWW winner is not B's later-mod scheduling state"
        assert final_A != snap_A, "A's offline scheduling should have been overwritten"
        # revlog union: BOTH reviews of C survive on both peers
        assert revC_A == base_C + 2 and revC_B == base_C + 2, "both C reviews did not union"
        assert qcA == "ok" and qcB == "ok", "quick_check failed after phase 2"
        winner_lapses = final_A[SCHED_COLS.split(",").index("lapses")]
        print(f"PHASE 2  : PASS — revlog union (+2 on both) AND scheduling LWW → B won "
              f"(lapses={winner_lapses}); A's schedule overwritten; no corruption")

        print("=" * 82)
        print("7b RESULT: PASS  |  10+10 no-loss: all 20 landed  |  "
              "same-card conflict: revlog union + scheduling LWW (later-mod peer B won)")
        print(f"  finished : {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print("=" * 82)
        return 0
    except AssertionError as exc:
        print(f"\n7b RESULT: FAIL — {exc}", file=sys.stderr)
        return 1
    finally:
        A.close()
        B.close()


if __name__ == "__main__":
    raise SystemExit(main())
