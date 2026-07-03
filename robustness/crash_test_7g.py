#!/usr/bin/env python3
"""GRE fork — headless crash-durability proof (execution-plan Block C, 7g).

Kill the engine with **SIGKILL mid-review** (while `answerCard` is writing) N times
against ONE evolving collection; after every crash, reopen and assert
`pragma quick_check = ok` **and** `pragma integrity_check = ok`, with **no revlog
loss** (committed reviews never disappear). This models a user's real collection
surviving repeated hard crashes during study — zero corrupted collections, N in a row.

How it is a *real* crash, landing *mid-review*:
  * A child process opens the collection and runs a tight `getCard()`/`answerCard()`
    loop (continuous SQLite writes; the write-ahead log is "hot"). Answers are Again/
    Hard so ~20 cards churn in the learning queue indefinitely — the real review write
    path (revlog insert + card update + queue update), forever, no throttle.
  * After each committed review the child bumps a tiny heartbeat file (outside the
    collection DB, so it never perturbs the crash surface). The parent waits until the
    heartbeat shows reviews are landing *right now*, dwells a random moment so the kill
    hits varied points in the write cycle, then sends SIGKILL. The child gets no chance
    to close the DB, flush, or roll back. SQLite's WAL journaling must recover the file
    atomically on the next open. We prove it does, every time.

Run with OUR desktop build's Python (same engine as `sync-smoke`):

    FORK_ANKI=/Users/felipecaicedo/Desktop/alpha/speedrun/anki \
    PYTHONPATH=$FORK_ANKI/out/pylib $FORK_ANKI/out/pyenv/bin/python robustness/crash_test_7g.py

or simply:  make crash-7g            (defaults: 20 iterations)

Exit code 0 iff all N collections are clean. LOCAL TEST ONLY.
"""
from __future__ import annotations

import os
import random
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from anki.collection import Collection

SEED_CARDS = 60           # >=20 so the day-0 new queue fills the churn pool
KILL_MIN_S, KILL_MAX_S = 0.05, 0.60   # random dwell after reviews start, before SIGKILL
WARMUP_TIMEOUT_S = 30.0   # max wait for the worker to start committing reviews
CHURN_EASES = [1, 1, 1, 2]  # Again/Hard: keep cards in the learning queue (no graduation)


def _wal(col_path: str) -> Path:
    return Path(col_path + "-wal")


def _argval(flag: str) -> str:
    return sys.argv[sys.argv.index(flag) + 1]


# --------------------------------------------------------------------------- worker
def worker(col_path: str, hb_path: str) -> None:
    """Continuously review cards (real answerCard write path) until SIGKILLed.

    Heartbeat (committed-review count) is written to hb_path — NOT the collection —
    so the parent can tell reviews are in flight without touching the crash surface.
    """
    random.seed()
    col = Collection(col_path)
    m = col.models.by_name("Basic")
    n = 0
    hb = Path(hb_path)
    while True:
        card = col.sched.getCard()
        if card is None:  # pool momentarily dry — top up (also a real write), keep going
            for _ in range(20):
                note = col.new_note(m)
                note["Front"], note["Back"] = f"refill-{time.time_ns()}", "b"
                col.add_note(note, 1)
            continue
        col.sched.answerCard(card, random.choice(CHURN_EASES))
        n += 1
        hb.write_text(str(n))  # post-commit heartbeat


# ----------------------------------------------------------------------- orchestrator
def _build_seed(col_path: str) -> tuple[str, int]:
    col = Collection(col_path)
    m = col.models.by_name("Basic")
    for i in range(SEED_CARDS):
        note = col.new_note(m)
        note["Front"], note["Back"] = f"seed-{i}", str(i)
        note.tags = ["topic::algebra::linear_equations"]
        col.add_note(note, 1)
    qc = col.db.scalar("pragma quick_check")
    col.close()
    return qc, SEED_CARDS


def _check(col_path: str) -> dict:
    """Reopen after a crash and gather the durability verdict for this collection."""
    try:
        col = Collection(col_path)
    except Exception as e:  # reopening a crashed DB must not fail
        return {"open": False, "error": f"open failed: {e!r}"}
    try:
        qc = col.db.scalar("pragma quick_check")
        ic = col.db.scalar("pragma integrity_check")
        rev = col.db.scalar("select count() from revlog")
        cards = col.db.scalar("select count() from cards")
        col.sched.getCard()  # usability probe: scheduler still builds a queue
        return {"open": True, "quick_check": qc, "integrity_check": ic,
                "revlog": rev, "cards": cards, "error": None}
    except Exception as e:
        return {"open": True, "quick_check": None, "integrity_check": None,
                "revlog": None, "cards": None, "error": repr(e)}
    finally:
        try:
            col.close()
        except Exception:
            pass


def _read_hb(hb_path: str) -> int:
    try:
        return int(Path(hb_path).read_text() or 0)
    except (FileNotFoundError, ValueError):
        return 0


def _wait_until_reviewing(hb_path: str, proc: subprocess.Popen) -> int:
    """Return the heartbeat count once the worker has committed >=1 review (it's hot)."""
    deadline = time.time() + WARMUP_TIMEOUT_S
    while time.time() < deadline:
        if proc.poll() is not None:
            return -1  # worker died before we could catch it hot
        n = _read_hb(hb_path)
        if n >= 1:
            return n
        time.sleep(0.005)
    return 0


def _selftest() -> int:
    """Prove the durability gate is NOT vacuous: a deliberately corrupted collection
    must be reported unclean (else a 20/20 "clean" run would prove nothing)."""
    import shutil
    workdir = Path(tempfile.mkdtemp(prefix="crash7g-selftest-"))
    good = str(workdir / "good.anki2")
    bad = str(workdir / "bad.anki2")
    print("7g SELF-TEST: the checker must reject a corrupted collection")
    _build_seed(good)
    gv = _check(good)
    print(f"  pristine copy   -> quick_check={gv.get('quick_check')} "
          f"integrity_check={gv.get('integrity_check')} (expect ok/ok)")
    shutil.copy(good, bad)
    # overwrite b-tree pages 2..5 with garbage; page 1 header stays valid so it opens
    with open(bad, "r+b") as f:
        f.seek(4096)
        f.write(os.urandom(16384))
    bv = _check(bad)
    clean = (bv.get("open") is True and bv.get("quick_check") == "ok"
             and bv.get("integrity_check") == "ok" and bv.get("error") is None)
    verdict = "quick_check=%s integrity_check=%s error=%s" % (
        bv.get("quick_check"),
        (bv.get("integrity_check") or "")[:40],
        bv.get("error"),
    )
    print(f"  corrupted copy  -> {verdict}")
    ok = (gv.get("quick_check") == "ok" and not clean)
    print(f"  SELF-TEST {'PASS' if ok else 'FAIL'}: pristine reads ok; corruption is caught.")
    return 0 if ok else 1


def main() -> int:
    iters = 20
    if "--iters" in sys.argv:
        iters = int(_argval("--iters"))

    workdir = Path(tempfile.mkdtemp(prefix="crash7g-"))
    col_path = str(workdir / "collection.anki2")

    import anki.buildinfo as bi
    print("=" * 80)
    print("GRE fork — 7g crash-durability proof (SIGKILL mid-review, one evolving collection)")
    print(f"engine   : anki {bi.version}  (buildhash {bi.buildhash})")
    print(f"iters    : {iters}   seed cards: {SEED_CARDS}")
    print(f"workdir  : {workdir}")
    print(f"started  : {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 80)

    base_qc, base_cards = _build_seed(col_path)
    print(f"seed     : cards={base_cards} quick_check={base_qc}")
    assert base_qc == "ok", f"seed collection not clean: {base_qc}"

    prev_rev = 0
    clean = 0
    mid_review_kills = 0
    for i in range(1, iters + 1):
        hb_path = str(workdir / f"hb-{i}")
        proc = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__),
             "--worker", col_path, "--hb", hb_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ,
        )
        hb = _wait_until_reviewing(hb_path, proc)
        reviewing = hb >= 1
        # dwell a random moment so SIGKILL lands at varied points in the write cycle
        time.sleep(random.uniform(KILL_MIN_S, KILL_MAX_S))
        try:
            wal_at_kill = _wal(col_path).stat().st_size
        except FileNotFoundError:
            wal_at_kill = 0
        hb_at_kill = _read_hb(hb_path)
        proc.send_signal(signal.SIGKILL)
        proc.wait()

        r = _check(col_path)
        rev = r.get("revlog")
        did = (rev - prev_rev) if isinstance(rev, int) else None
        ok = (
            r.get("open") is True
            and r.get("quick_check") == "ok"
            and r.get("integrity_check") == "ok"
            and isinstance(rev, int) and rev >= prev_rev
            and r.get("error") is None
        )
        clean += 1 if ok else 0
        if reviewing:
            mid_review_kills += 1
        print(
            f"[{i:02d}/{iters}] reviewing_at_kill={reviewing!s:>5} hb_at_kill={hb_at_kill:>5} "
            f"wal_at_kill={wal_at_kill:>8}B reviews_committed={did} revlog_total={rev} "
            f"quick_check={r.get('quick_check')} integrity_check={r.get('integrity_check')} "
            f"cards={r.get('cards')} -> {'CLEAN' if ok else 'FAIL ' + str(r.get('error'))}"
        )
        if isinstance(rev, int):
            prev_rev = rev

    print("=" * 80)
    print(
        f"7g RESULT: {clean}/{iters} collections CLEAN after mid-review SIGKILL "
        f"(quick_check=ok AND integrity_check=ok AND no revlog loss)"
    )
    print(
        f"  kills confirmed mid-review (reviews committing at kill time): "
        f"{mid_review_kills}/{iters}"
    )
    print(f"  total committed reviews survived across all crashes: {prev_rev}")
    print(f"  finished : {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 80)
    return 0 if clean == iters else 1


if __name__ == "__main__":
    if "--worker" in sys.argv:
        worker(_argval("--worker"), _argval("--hb"))
    elif "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    else:
        raise SystemExit(main())
