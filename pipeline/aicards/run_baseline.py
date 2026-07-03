# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""One-command runner for the two A-gated proofs (PRD §9, execution-plan Block C):

    python pipeline/aicards/run_baseline.py --seed 42     # or: make ai-baseline

1. **Beat-the-baseline** — AI pipeline (RAG+provenance+CAS+abstain) vs. a template/
   cloze non-RAG baseline (no verify/abstain), scored by the same rater harness, with
   an **exact McNemar test** + per-arm fact-precision/useful-yield.
2. **AI-off degradation** — with no live model the pipeline aborts cleanly (zero
   unverified cards) while study/review + scoring are unaffected.

Deterministic for a fixed seed. Writes JSON + Markdown to ``pipeline/aicards/out/``.
Exit 0 always (the proofs are reports; an honest null still "ran").
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.dirname(HERE)
for _p in (HERE, PIPELINE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import baseline  # noqa: E402
import orchestrator  # noqa: E402
from orchestrator import LlmBackend  # noqa: E402

OUT_DIR = os.path.join(HERE, "out")


def ai_off_proof():
    """Run the AI-off degradation proof against the live-model seam (no key here)."""
    return orchestrator.run_pipeline_safe(LlmBackend())


def main(argv=None):
    parser = argparse.ArgumentParser(description="Beat-the-baseline + AI-off degradation proofs.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=OUT_DIR)
    args = parser.parse_args(argv)

    report = baseline.beat_baseline(seed=args.seed)
    targets = baseline.build_targets(seed=args.seed)

    print("PROOF 1 — BEAT THE BASELINE")
    print("target composition (declared fixture): {}".format(baseline.category_counts(targets)))
    print("")
    print(report.format_report())
    print("")

    degrade = ai_off_proof()
    print("PROOF 2 — AI-OFF DEGRADATION (live-model seam, no API key)")
    print("  live-model backend used; degraded cleanly: ok={}".format(degrade.ok))
    print("  cards emitted: {}   published: {}".format(len(degrade.outcomes), len(degrade.published)))
    print("  message: {}".format(degrade.message))
    assert degrade.ok is False and degrade.published == [], "degradation proof invariant violated"
    print("  ASSERTED: no model -> 0 cards, 0 unverified shipped; study/review + scoring unaffected.")

    os.makedirs(args.out, exist_ok=True)
    payload = {
        "seed": args.seed,
        "beat_baseline": {
            "target_composition": baseline.TARGET_COMPOSITION,
            "table": {"a": report.a, "b": report.b, "c": report.c, "d": report.d},
            "mcnemar": {
                "b": report.mcnemar.b, "c": report.mcnemar.c, "n": report.mcnemar.n,
                "p_value": report.mcnemar.p_value, "favored": report.mcnemar.favored,
            },
            "yield_diff_ci_90": list(report.yield_diff_ci),
            "rater": report.rater_name,
            "ai_arm": vars(report.ai),
            "baseline_arm": vars(report.baseline),
            "ai_beats_baseline": report.ai_beats_baseline,
        },
        "ai_off_degradation": {
            "ok": degrade.ok, "cards_emitted": len(degrade.outcomes),
            "published": len(degrade.published), "message": degrade.message,
        },
    }
    with open(os.path.join(args.out, "baseline_report.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(args.out, "baseline_report.md"), "w", encoding="utf-8") as fh:
        fh.write("# Beat-the-baseline + AI-off degradation proofs\n\n")
        fh.write("- **Seed:** {}\n\n".format(args.seed))
        fh.write("```\n{}\n```\n\n".format(report.format_report()))
        fh.write("## AI-off degradation\n\n{}\n".format(degrade.message))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
