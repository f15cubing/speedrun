#!/usr/bin/env python3
"""GRE fork — headless sync round-trip smoke (W4 foundation).

Proves the self-hosted server + Anki sync protocol move a reviewed, topic-tagged
note from collection A -> server -> collection B with revlog + scheduling intact
and `pragma quick_check` = ok on both. Run OUR desktop-build Python:

    make sync-server            # terminal A (leave running)
    make sync-smoke             # terminal B  (or: $FORK_PY sync/roundtrip_smoke.py)

Exits non-zero on any mismatch. LOCAL TEST ONLY (creds are throwaways).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from anki.collection import Collection

ENDPOINT = os.environ.get("SYNC_ENDPOINT") or f"http://127.0.0.1:{os.environ.get('SYNC_PORT', '8080')}/"
USER = os.environ.get("SYNC_USER", "greuser")
PASSWORD = os.environ.get("SYNC_PASSWORD", "grepass")
TAG = "topic::calculus::integral_single"
FRONT = "w4-sync-smoke-front"


def _sync(col: Collection, *, prefer_upload: bool) -> None:
    """One sync; if a full sync is required (empty-server first contact), resolve it
    in the intended direction."""
    auth = col.sync_login(USER, PASSWORD, ENDPOINT)
    out = col.sync_collection(auth, False)  # sync_media=False
    if out.required == out.NO_CHANGES:
        return
    if out.required == out.FULL_UPLOAD:
        upload = True
    elif out.required == out.FULL_DOWNLOAD:
        upload = False
    else:  # FULL_SYNC (ambiguous) — use our controlled direction
        upload = prefer_upload
    col.full_upload_or_download(auth=auth, server_usn=None, upload=upload)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="w4-sync-"))
    a = Collection(str(tmp / "a.anki2"))
    b = Collection(str(tmp / "b.anki2"))
    try:
        # A: add a tagged note and review its card once (creates a revlog row + schedules it).
        note = a.new_note(a.models.by_name("Basic"))
        note["Front"], note["Back"] = FRONT, "back"
        note.tags = [TAG]
        a.add_note(note, 1)  # deck 1 = Default
        card = a.sched.getCard()
        assert card is not None, "no card queued to review on A"
        a.sched.answerCard(card, 3)  # 3 = Good
        reps_a = a.db.scalar("select count() from revlog")
        assert reps_a >= 1, f"expected a revlog row on A, got {reps_a}"

        # A -> server (full upload; server starts empty), then server -> B (full download).
        _sync(a, prefer_upload=True)
        _sync(b, prefer_upload=False)

        # B must now have the note, its card, and the revlog row; both DBs stay clean.
        n_notes = b.db.scalar("select count() from notes where flds like ?", f"{FRONT}%")
        n_revlog = b.db.scalar("select count() from revlog")
        n_cards = b.db.scalar(
            "select count() from cards c join notes n on c.nid=n.id where n.flds like ?",
            f"{FRONT}%",
        )
        assert n_notes == 1, f"note did not cross to B (notes={n_notes})"
        assert n_cards >= 1, f"card did not cross to B (cards={n_cards})"
        assert n_revlog >= 1, f"revlog did not cross to B (revlog={n_revlog})"
        for name, col in (("A", a), ("B", b)):
            qc = col.db.scalar("pragma quick_check")
            assert qc == "ok", f"quick_check on {name} = {qc!r}"

        print(f"OK: note+card+revlog crossed A->server->B; quick_check ok (revlog A={reps_a}, B={n_revlog})")
        return 0
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        a.close()
        b.close()


if __name__ == "__main__":
    raise SystemExit(main())
