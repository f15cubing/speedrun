"""Re-runnable study-deck ↔ eval-bank leakage audit CLI (PRD §11).

Loads both corpora via their existing **read-only** loaders and publishes the residual
leakage rate + the near-duplicate layers. Deterministic for a fixed ``--seed``.

    python pipeline/run_leakage_audit.py                 # print
    python pipeline/run_leakage_audit.py --strict        # non-zero exit if anything leaks
    python pipeline/run_leakage_audit.py --out pipeline/out/leakage_report.json

Run via ``make deck-leakage-audit`` (sets the PYTHONPATH so `build_deck` + the eval-bank
`loader` are importable). Never writes the eval bank.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import build_deck
import leakage_audit


def load_eval_items():
    """Read the frozen eval bank via its own loader (read-only)."""
    try:
        from loader import load_eval_items as _load  # eval/bank on PYTHONPATH
    except ModuleNotFoundError:
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.abspath(os.path.join(here, "..", "eval", "bank")))
        from loader import load_eval_items as _load
    return _load()


def build_report(seed: int = 42) -> leakage_audit.LeakageReport:
    study = build_deck.load_all_cards(seed=seed)
    eval_items = load_eval_items()
    return leakage_audit.scan_leakage(study, eval_items)


def main() -> None:
    ap = argparse.ArgumentParser(description="Study<->eval leakage audit (PRD §11).")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None, help="write JSON here (a sibling .md too)")
    ap.add_argument(
        "--strict", action="store_true", help="exit non-zero if any exact QA leakage"
    )
    args = ap.parse_args()

    report = build_report(seed=args.seed)
    text = leakage_audit.format_report(report)
    print(text, end="")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(report.as_dict(), fh, indent=2, sort_keys=True)
        with open(os.path.splitext(args.out)[0] + ".md", "w", encoding="utf-8") as fh:
            fh.write("# Leakage audit (PRD §11)\n\n```\n" + text + "```\n")

    if args.strict:
        leakage_audit.assert_no_leakage(report)


if __name__ == "__main__":
    main()
