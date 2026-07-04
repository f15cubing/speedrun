"""Re-runnable study-deck quality report + integrity gate (CLI).

    python pipeline/run_deck_report.py                 # print report
    python pipeline/run_deck_report.py --strict        # non-zero exit on any violation
    python pipeline/run_deck_report.py --json-out pipeline/dist/deck_report.json

Run via ``make deck-report``. Reads the study deck only (never the held-out eval bank).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import build_deck
import deck_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="GRE study-deck quality report + gate.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--strict", action="store_true", help="exit non-zero on any violation")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    cards = build_deck.load_all_cards(seed=args.seed)
    summary = deck_report.summarize_quality(cards)
    print(deck_report.format_report(summary), end="")

    if args.json_out:
        os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)
        # drop the full per-card failure list from the artifact when clean
        artifact = {k: v for k, v in summary.items() if k != "failures"}
        artifact["failures"] = summary["failures"]
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, sort_keys=True)

    if args.strict:
        try:
            deck_report.assert_deck_quality(cards)
        except AssertionError as exc:
            print("\n" + str(exc), file=sys.stderr)
            return 1
        print("\nDeck quality gate PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
