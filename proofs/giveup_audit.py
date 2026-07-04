# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Give-up rule (D2) evidence audit — proves the "no bare Readiness number" ceiling.

A **read-only consumer** of ``scoring/readiness.py``: it never modifies the scoring
definitions, the held-out eval bank, or the Anki engine. It sweeps simulated evidence
levels through the EXISTING ``give_up()`` / ``project()`` and documents exactly when
Readiness is *shown* vs *gated*, then asserts the honesty invariant — **whenever the gate
fails, no scaled-score number is emitted anywhere** (estimate/low/high all ``None``) and
the evidence-panel reasons are present.

D2 gate (PRD §7c): Readiness is shown only when **≥200 graded reviews AND ≥50% topic
coverage AND the projected interval width ≤ 120 scaled points**. Showing a bare Readiness
number without clearing the gate is an **automatic fail**, so this proof guards the single
highest-stakes ceiling in the scoring layer.

HONESTY LABEL: this exercises the *gate logic* on constructed evidence levels; it proves
the gate behaves correctly, not that any real student has a particular readiness.

Deterministic (fixed seed → byte-identical JSON). Stdlib-only.
"""

from __future__ import annotations

import argparse
import json
import os

from scoring import readiness

_TABLE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "scoring", "data", "ets_percentiles.json"
)


def load_table(path: str = _TABLE_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def scenario(name, probs, reviews, coverage, *, table, form_residuals=None) -> dict:
    """Run one evidence level through the real `project()` and capture the gate outcome."""
    r = readiness.project(
        probs, table, form_residuals, reviews=reviews, coverage=coverage
    )
    return {
        "name": name,
        "n_items": len(probs),
        "reviews": reviews,
        "coverage": coverage,
        "width": r["width"],
        "shown": r["shown"],
        "estimate": r["estimate"],
        "low": r["low"],
        "high": r["high"],
        "reasons": list(r["reasons"]),
    }


def run(seed: int = 42, *, table: dict | None = None) -> dict:
    """Sweep boundary + representative evidence levels across the D2 gate."""
    table = table or load_table()
    strong = [0.72] * 66      # a full, consistent form → narrow interval
    noisy_small = [0.5] * 4   # few maximally-uncertain items → wide interval
    scenarios = [
        scenario("cleared: strong full-form record", strong, 500, 0.90, table=table),
        scenario("gated: 199 reviews (<200)", strong, 199, 0.90, table=table),
        scenario("gated: 49% coverage (<50%)", strong, 500, 0.49, table=table),
        scenario("gated: interval too wide", noisy_small, 500, 0.90, table=table),
        scenario("gated: brand-new learner (all three fail)", noisy_small, 10, 0.10, table=table),
    ]
    shown = [s for s in scenarios if s["shown"]]
    gated = [s for s in scenarios if not s["shown"]]
    return {
        "seed": seed,
        "note": (
            "read-only audit of the D2 give-up gate; a bare Readiness number without "
            "clearing >=200 reviews AND >=50% coverage AND width<=120 is an auto-fail"
        ),
        "max_width": readiness.READINESS_MAX_INTERVAL_WIDTH,
        "scenarios": scenarios,
        "summary": {"n_shown": len(shown), "n_gated": len(gated)},
    }


def assert_giveup_invariants(result: dict) -> None:
    """The honesty ceiling: gated → no number anywhere; shown → a full range with reasons=[]."""
    for s in result["scenarios"]:
        if s["shown"]:
            assert (
                s["estimate"] is not None and s["low"] is not None and s["high"] is not None
            ), ("shown scenario missing a bound", s)
            assert s["low"] <= s["estimate"] <= s["high"], ("range not ordered", s)
            assert not s["reasons"], ("shown scenario should have no give-up reasons", s)
        else:
            assert (
                s["estimate"] is None and s["low"] is None and s["high"] is None
            ), ("GATED scenario leaked a Readiness number (auto-fail)", s)
            assert s["reasons"], ("gated scenario must give reasons", s)


def format_report(result: dict) -> str:
    lines = [
        "Give-up rule (D2) evidence audit  [max interval width = {} scaled pts]".format(
            result["max_width"]
        ),
        "  {} shown / {} gated".format(
            result["summary"]["n_shown"], result["summary"]["n_gated"]
        ),
    ]
    for s in result["scenarios"]:
        if s["shown"]:
            verdict = "SHOWN  {} [{}-{}] (width {})".format(
                s["estimate"], s["low"], s["high"], s["width"]
            )
        else:
            verdict = "GATED  (no number) — " + "; ".join(s["reasons"])
        lines.append(
            "  - {:42s} reviews={:>4} coverage={:.2f} -> {}".format(
                s["name"], s["reviews"], s["coverage"], verdict
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="D2 give-up rule evidence audit.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None, help="write JSON here (a sibling .md too)")
    args = ap.parse_args()

    result = run(seed=args.seed)
    assert_giveup_invariants(result)  # the audit fails loudly if the ceiling is ever violated
    text = format_report(result)
    print(text, end="")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
        with open(os.path.splitext(args.out)[0] + ".md", "w", encoding="utf-8") as fh:
            fh.write("# Give-up rule (D2) evidence audit\n\n```\n" + text + "```\n")


if __name__ == "__main__":
    main()
