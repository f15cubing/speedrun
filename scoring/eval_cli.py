# scoring/eval_cli.py
"""make score-eval entry: simulate -> split -> fit -> validate -> emit metrics + sample scorecard."""
from __future__ import annotations

import argparse
import json
import os

from scoring import calibration, performance, readiness, scorecard
from scoring.simulate import simulate_attempts, student_mastery

_NOTE = "validated on simulated data (machinery check); real predictive validity unestablished at n≈1"


def _stub_items():
    # Deterministic stub item set when the eval bank isn't importable in a pure-stdlib run.
    return [{"id": f"i{i}", "leaf_tag": t, "difficulty": (i % 5) + 1}
            for i, t in enumerate(["topic::calculus::integral_single",
                                    "topic::calculus::differential_single",
                                    "topic::algebra::linear"] * 8)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--students", type=int, default=40)
    ap.add_argument("--out", default="scoring/out")
    args = ap.parse_args(argv)

    items = _stub_items()
    attempts = simulate_attempts(items, n_students=args.students, seed=args.seed)
    split = int(0.7 * len(attempts))
    train, test = attempts[:split], attempts[split:]
    model = performance.fit_performance(train, lambda sid: student_mastery(attempts, sid), coverage=1.0)

    probs = [model.predict({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                           student_mastery(attempts, a.student_id).get(a.leaf_tag, 0.0), 1.0)
             for a in test]
    y = [a.correct for a in test]
    residuals = [p - yi for p, yi in zip(probs, y)]

    table = json.load(open(os.path.join(os.path.dirname(__file__), "data", "ets_percentiles.json")))
    metrics = {"brier": calibration.brier(probs, y), "ece": calibration.ece(probs, y),
               "reliability": calibration.reliability_bins(probs, y), "note": _NOTE}

    read = readiness.project(probs[:66] or probs, table, residuals, reviews=10**9, coverage=1.0)
    sc = scorecard.build(
        memory={"estimate": 0.0, "low": 0.0, "high": 0.0, "coverage_pct": 0.0},
        performance={"estimate": round(sum(probs) / len(probs), 4), "low": 0.0, "high": 1.0},
        readiness={**read, "coverage_pct": 1.0, "confidence": "low",
                   "reasons": read.get("reasons", []), "best_next_topic": items[0]["leaf_tag"]},
        source=f"simulated (S={args.students}) + 0 real; {_NOTE}",
        updated_at="1970-01-01T00:00:00Z",
    )

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, sort_keys=True, indent=2)
    with open(os.path.join(args.out, "sample_scorecard.json"), "w") as fh:
        json.dump(sc, fh, sort_keys=True, indent=2)
    print(f"scoring: brier={metrics['brier']:.4f} ece={metrics['ece']:.4f} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
