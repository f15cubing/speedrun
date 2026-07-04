"""Re-runnable interleaving report on the real generated study deck.

Builds a representative **blocked** study session (a few cards per leaf, arranged
topic-by-topic — the worst case interleaving improves on) from the seeded deck, applies
:mod:`interleave`, and reports the spec's two metrics (adjacency dispersion before/after
+ FSRS displacement). Deterministic for a fixed ``--seed`` / ``--per-leaf`` so it is a
re-runnable check (PRD §11). Reads only study-deck leaf tags — never the held-out eval
bank, the scheduler, or the scoring layer.

    python pipeline/run_interleave_report.py            # print
    python pipeline/run_interleave_report.py --out pipeline/out/interleave_report.json
"""

from __future__ import annotations

import argparse
import json
import os

import build_deck
import interleave
import taxonomy


def blocked_session(cards, per_leaf: int):
    """A deterministic blocked session: up to ``per_leaf`` cards from each leaf, in
    taxonomy (bucket→leaf) order, so the same leaf's cards sit together (blocked)."""
    by_leaf: dict[str, list] = {}
    for c in cards:
        by_leaf.setdefault(c["leaf_tag"], []).append(c)
    session = []
    for leaf in taxonomy.LEAVES:
        pool = sorted(by_leaf.get(leaf.tag, []), key=lambda c: c["uid"])
        for c in pool[:per_leaf]:
            session.append((c["uid"], c["leaf_tag"]))
    return session


def build_report(seed: int = 42, per_leaf: int = 4) -> dict:
    cards = build_deck.load_all_cards(seed=seed)
    session = blocked_session(cards, per_leaf)
    res = interleave.interleave(session)
    return {
        "seed": seed,
        "per_leaf": per_leaf,
        "session_size": len(session),
        "distinct_leaves": len({leaf for _cid, leaf in session}),
        "k": interleave.DEFAULT_K,
        "w": interleave.DEFAULT_W,
        "blocked_dispersion": round(res.blocked_dispersion, 4),
        "interleaved_dispersion": round(res.adjacency_dispersion, 4),
        "dispersion_gain": round(res.adjacency_dispersion - res.blocked_dispersion, 4),
        "displacement_mean": round(res.displacement_mean, 4),
        "displacement_max": res.displacement_max,
        "used_fallback": res.used_fallback,
    }


def format_report(r: dict) -> str:
    return (
        "GRE interleaving report (seed={seed}, {session_size} cards across "
        "{distinct_leaves} leaves; K={k}, W={w})\n"
        "  adjacency dispersion : blocked {blocked_dispersion:.3f} -> interleaved "
        "{interleaved_dispersion:.3f}  (+{dispersion_gain:.3f})\n"
        "  FSRS displacement    : mean {displacement_mean:.3f}, max {displacement_max} "
        "(bounded by W={w})\n"
        "  used_fallback        : {used_fallback}\n"
    ).format(**r)


def main() -> None:
    ap = argparse.ArgumentParser(description="Interleaving metrics on the seeded deck.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--per-leaf", type=int, default=4)
    ap.add_argument("--out", default=None, help="write JSON here (a sibling .md too)")
    args = ap.parse_args()

    report = build_report(seed=args.seed, per_leaf=args.per_leaf)
    text = format_report(report)
    print(text, end="")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        md = os.path.splitext(args.out)[0] + ".md"
        with open(md, "w", encoding="utf-8") as fh:
            fh.write("# GRE interleaving report\n\n```\n" + text + "```\n")


if __name__ == "__main__":
    main()
