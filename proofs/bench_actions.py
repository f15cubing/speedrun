# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Latency bench for the reviewer's next-card path at 50k cards (§10 / 7h).

Complements ``proofs/bench_mastery.py`` (the dashboard mastery RPC). Times the
engine components of "next card appears after grading" through the REAL built
pylib — the same scheduler call the desktop reviewer makes:

* ``next_card_default``   — ``col.sched.get_queued_cards(fetch_limit=1)``: the
  upstream / interleaving-OFF next-card fetch (what ships by default).
* ``next_card_lookahead`` — ``get_queued_cards(fetch_limit=16)``: the fetch when
  review interleaving is ON (a bounded lookahead window).
* ``interleave_reorder``  — the pure ordering cost the interleaving toggle adds,
  on a worst-case 16-card single batch, via the vendored
  ``pipeline/interleave.interleave_order`` (byte-identical to
  ``aqt/gre/interleave.py``, drift-guarded). No Qt import required.

Interleaving-ON next-card cost ≈ ``next_card_lookahead + interleave_reorder``;
both are reported so the sum can be checked against the **p95 < 100 ms** target.

**Honest scope:** button-ack and the full webview render are GUI-bound (shown in
the demo, not measurable headless here); sync latency is ``make sync-verify`` /
the 7b harness; cold-start + memory are process-level. This bench covers the
engine-measurable actions. Re-runnable + deterministic (fixed seed).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)  # reuse the mastery-bench seeding
sys.path.insert(0, os.path.join(_REPO, "pipeline"))  # vendored interleave core

from bench_mastery import _LEAVES, _percentile, seed  # noqa: E402
from interleave import interleave_order  # noqa: E402  (== aqt/gre/interleave.py)


def _stats(samples_ms: list[float]) -> dict:
    if not samples_ms:
        return {"p50_ms": 0.0, "p95_ms": 0.0, "worst_ms": 0.0, "mean_ms": 0.0, "n": 0}
    samples_ms.sort()
    return {
        "p50_ms": round(_percentile(samples_ms, 0.50), 3),
        "p95_ms": round(_percentile(samples_ms, 0.95), 3),
        "worst_ms": round(samples_ms[-1], 3),
        "mean_ms": round(statistics.fmean(samples_ms), 3),
    }


def _raise_limits(col, deck_id) -> None:
    """Lift the per-day new/review caps so the bench can grade many cards."""
    conf = col.decks.config_dict_for_deck_id(deck_id)
    conf["new"]["perDay"] = 999999
    conf["rev"]["perDay"] = 999999
    col.decks.update_config(conf)


def _bench_answer_next(col, iters: int, fetch_limit: int) -> dict:
    """The real "next card appears after grading" cycle: answer_card + get_queued_cards.

    Grades the top card Good (build_answer is prep, timed outside), then fetches the
    next — the engine work between a button press and the next card showing. Uses the
    given fetch_limit (1 = interleaving off / default; 16 = the interleaving lookahead).
    """
    from anki.cards import Card
    from anki.scheduler.v3 import CardAnswer

    # warm up
    for _ in range(3):
        out = col.sched.get_queued_cards(fetch_limit=fetch_limit)
        if not out.cards:
            break
        qc = out.cards[0]
        card = Card(col, backend_card=qc.card)
        card.start_timer()  # build_answer reads card.time_taken()
        ans = col.sched.build_answer(
            card=card, states=qc.states, rating=CardAnswer.GOOD
        )
        col.sched.answer_card(ans)

    samples = []
    for _ in range(iters):
        out = col.sched.get_queued_cards(fetch_limit=fetch_limit)
        if not out.cards:
            break
        qc = out.cards[0]
        card = Card(col, backend_card=qc.card)
        card.start_timer()  # build_answer reads card.time_taken()
        ans = col.sched.build_answer(
            card=card, states=qc.states, rating=CardAnswer.GOOD
        )
        t0 = time.perf_counter()
        col.sched.answer_card(ans)
        col.sched.get_queued_cards(fetch_limit=fetch_limit)
        samples.append((time.perf_counter() - t0) * 1000.0)
    return _stats(samples)


def _bench_fetch(col, fetch_limit: int, iters: int) -> dict:
    """Idempotent ``get_queued_cards`` cost (steady-state fetch; does not answer).

    Shows the interleaving lookahead (fetch_limit 1 → 16) adds negligible fetch cost.
    """
    for _ in range(5):
        col.sched.get_queued_cards(fetch_limit=fetch_limit)
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        col.sched.get_queued_cards(fetch_limit=fetch_limit)
        samples.append((time.perf_counter() - t0) * 1000.0)
    return _stats(samples)


def _bench_reorder(iters: int, seed_val: int, window: int = 16) -> dict:
    rng = random.Random(seed_val)
    # Worst case: a full lookahead window of review cards spanning many clusters.
    batch = [(i, rng.choice(_LEAVES)) for i in range(window)]
    for _ in range(5):  # warm up
        interleave_order(batch)
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        interleave_order(batch)
        samples.append((time.perf_counter() - t0) * 1000.0)
    return _stats(samples)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", type=int, default=50000)
    ap.add_argument("--iters", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="docs/evidence/proofs/bench_actions.json")
    args = ap.parse_args(argv)

    from anki.collection import Collection  # lazy: only for a live bench run

    path = f"/tmp/gre-bench-actions-{args.cards}-{args.seed}.anki2"
    if os.path.exists(path):
        os.remove(path)
    col = Collection(path)
    try:
        t0 = time.perf_counter()
        seed(col, args.cards, args.seed)
        seed_s = time.perf_counter() - t0
        deck_id = col.decks.id("GRE Bench")
        _raise_limits(col, deck_id)
        col.decks.select(deck_id)  # get_queued_cards only serves the selected deck
        result = {
            "cards": col.card_count(),
            "iters": args.iters,
            "seed": args.seed,
            "seed_seconds": round(seed_s, 2),
            "next_card_cycle": _bench_answer_next(col, args.iters, fetch_limit=1),
            "fetch_default": _bench_fetch(col, 1, args.iters),
            "fetch_lookahead": _bench_fetch(col, 16, args.iters),
            "interleave_reorder": _bench_reorder(args.iters, args.seed),
        }
    finally:
        col.close()
        if os.path.exists(path):
            os.remove(path)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, sort_keys=True, indent=2)

    def _line(name: str, s: dict, target: str) -> str:
        return (
            f"  {name:<21} p50={s['p50_ms']:.3f}  p95={s['p95_ms']:.3f}  "
            f"worst={s['worst_ms']:.3f} ms   ({target})"
        )

    print(
        f"reviewer next-card path @ {result['cards']} cards, {result['iters']} iters:\n"
        + _line(
            "next_card_cycle",
            result["next_card_cycle"],
            "grade->next; target p95<100ms",
        )
        + "\n"
        + _line("fetch_default", result["fetch_default"], "get_queued_cards(1)")
        + "\n"
        + _line(
            "fetch_lookahead",
            result["fetch_lookahead"],
            "get_queued_cards(16), interleave on",
        )
        + "\n"
        + _line(
            "interleave_reorder",
            result["interleave_reorder"],
            "reorder overhead, 16-card",
        )
        + "\n"
        "  next_card_cycle = the real grade->next engine cost (answer_card + fetch).\n"
        "  interleave-ON adds only (fetch_lookahead - fetch_default) + interleave_reorder.\n"
        f"  -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
