# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Latency bench for the W1 mastery-query RPC at scale (Block D proof).

Seeds a temp collection with N cards tagged across the GRE taxonomy, then times
``col.mastery_query(topics)`` over many iterations and reports p50/p95/worst.
This exercises the REAL shared Rust engine through the built pylib (the same RPC
the desktop dashboard + the AnkiDroid panel consume) — not a reimplementation.

Run via ``make bench`` (points PYTHONPATH at the built ``anki/out/pylib`` and
uses that pyenv's python). Re-runnable + deterministic (fixed seed).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import time

# 17 GRE leaf tags + 3 bucket rollups (mirrors qt/aqt/gre/taxonomy.json).
_LEAVES = [
    "topic::calculus::differential_single",
    "topic::calculus::integral_single",
    "topic::calculus::sequences_series",
    "topic::calculus::multivariable",
    "topic::calculus::differential_equations",
    "topic::algebra::linear",
    "topic::algebra::abstract_group",
    "topic::algebra::abstract_ring",
    "topic::algebra::number_theory",
    "topic::additional::discrete",
    "topic::additional::probability",
    "topic::additional::statistics",
    "topic::additional::geometry",
    "topic::additional::topology",
    "topic::additional::real_analysis",
    "topic::additional::complex",
    "topic::additional::numerical",
]
_BUCKETS = ["topic::calculus", "topic::algebra", "topic::additional"]


def _percentile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def seed(col: Collection, n_cards: int, seed_val: int) -> None:
    rng = random.Random(seed_val)
    basic = col.models.by_name("Basic")
    deck_id = col.decks.id("GRE Bench")
    col.models.set_current(basic)
    # Batch inside a single DB transaction for speed.
    for i in range(n_cards):
        note = col.new_note(basic)
        note["Front"] = f"q{i}"
        note["Back"] = f"a{i}"
        note.tags = [rng.choice(_LEAVES)]
        col.add_note(note, deck_id)


def bench(col: Collection, iters: int, seed_val: int) -> dict:
    topics = _LEAVES + _BUCKETS
    rng = random.Random(seed_val)
    # Warm up (first call pays any lazy init / cache cost).
    for _ in range(5):
        col.mastery_query(topics)
    samples_ms = []
    for _ in range(iters):
        rng.shuffle(topics)
        t0 = time.perf_counter()
        col.mastery_query(topics)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    samples_ms.sort()
    return {
        "iters": iters,
        "topics_per_call": len(topics),
        "p50_ms": round(_percentile(samples_ms, 0.50), 3),
        "p95_ms": round(_percentile(samples_ms, 0.95), 3),
        "worst_ms": round(samples_ms[-1], 3),
        "mean_ms": round(statistics.fmean(samples_ms), 3),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", type=int, default=50000)
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="docs/evidence/proofs/bench_mastery.json")
    args = ap.parse_args(argv)

    from anki.collection import Collection  # lazy: only needed for a live bench run

    path = f"/tmp/gre-bench-{args.cards}-{args.seed}.anki2"
    if os.path.exists(path):
        os.remove(path)
    col = Collection(path)
    try:
        t0 = time.perf_counter()
        seed(col, args.cards, args.seed)
        seed_s = time.perf_counter() - t0
        result = bench(col, args.iters, args.seed)
        result["cards"] = col.card_count()
        result["seed_seconds"] = round(seed_s, 2)
        result["seed"] = args.seed
    finally:
        col.close()
        if os.path.exists(path):
            os.remove(path)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, sort_keys=True, indent=2)
    print(
        f"mastery_query @ {result['cards']} cards, {result['iters']} iters "
        f"({result['topics_per_call']} topics/call):\n"
        f"  p50={result['p50_ms']} ms  p95={result['p95_ms']} ms  "
        f"worst={result['worst_ms']} ms  mean={result['mean_ms']} ms\n"
        f"  -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
