# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""One-command runner for the AI card pipeline + gold-set gate (PRD §9).

    python pipeline/aicards/run_gate.py --seed 42          # or: make ai-gate

Runs the full pipeline on the selected backend (deterministic stub by default,
since no live model is configured here), scores it against the **pre-lodged** gate,
runs the firewall/leakage checks, prints a report, and writes JSON + Markdown to
``pipeline/aicards/out/``. Deterministic for a fixed seed (re-runnable, PRD §11).

Exit codes: 0 = ran (report written; gate pass/fail is in the report — an honest
documented failure is acceptable per the plan); 1 = gate failed AND ``--strict``;
2 = firewall/leakage check failed (always hard-fails — a leak is never acceptable).
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

import firewall  # noqa: E402
import goldset_gate  # noqa: E402
import orchestrator  # noqa: E402
import stub_model  # noqa: E402

OUT_DIR = os.path.join(HERE, "out")


def _api_status():
    key = orchestrator.LlmBackend()._api_key()
    return "LIVE ({} set)".format("api key") if key else "AI-off (no live model API key)"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the AI card pipeline + gold-set gate.")
    parser.add_argument("--seed", type=int, default=42, help="deterministic seed (default 42)")
    parser.add_argument("--out", default=OUT_DIR, help="output dir for the reports")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if the gate fails (default: report and exit 0)")
    args = parser.parse_args(argv)

    backend = stub_model.StubBackend(seed=args.seed)
    outcomes = orchestrator.run_pipeline(backend)
    result = goldset_gate.run_gate(outcomes)
    fw = firewall.run_firewall(backend, outcomes)

    print("AI ACCESS: {}".format(_api_status()))
    print("BACKEND:   {}".format(backend.name))
    print("COMPOSITION (stub fixture): {}".format(stub_model.COMPOSITION))
    print("")
    print(result.format_report())
    print("")
    print("FIREWALL / LEAKAGE: {}".format("PASS" if fw["passed"] else "FAIL"))
    for name, ok in fw["checks"].items():
        print("  [{}] {}".format("ok" if ok else "XX", name))

    os.makedirs(args.out, exist_ok=True)
    payload = {
        "api_access": _api_status(),
        "backend": backend.name,
        "seed": args.seed,
        "composition": stub_model.COMPOSITION,
        "gate": result.as_dict(),
        "firewall": fw,
    }
    with open(os.path.join(args.out, "gate_report.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(args.out, "gate_report.md"), "w", encoding="utf-8") as fh:
        fh.write("# AI card pipeline — gold-set gate report\n\n")
        fh.write("- **AI access:** {}\n- **Backend:** {}\n- **Seed:** {}\n\n".format(
            _api_status(), backend.name, args.seed))
        fh.write("```\n{}\n```\n\n".format(result.format_report()))
        fh.write("Firewall/leakage: **{}**\n".format("PASS" if fw["passed"] else "FAIL"))

    if not fw["passed"]:
        print("\nFIREWALL FAILED — leakage detected. This is a hard failure.", file=sys.stderr)
        return 2
    if args.strict and not result.passed:
        print("\nGATE FAILED under --strict.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
