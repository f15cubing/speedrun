# scoring/eval_cli.py
"""make score-eval entry: simulate -> student-split -> fit (Platt) -> validate ->
project Readiness (aggregate conformal + Bayesian cross-check) -> emit metrics +
sample scorecard + append the prospective calibration log. Deterministic."""
from __future__ import annotations

import argparse
import json
import os

from scoring import calibration, performance, readiness, scorecard
from scoring.simulate import simulate_attempts, student_mastery

_NOTE = "validated on simulated data (machinery check); real predictive validity unestablished at n≈1"
_FIXED_TS = "1970-01-01T00:00:00Z"  # fixed so CLI output is byte-deterministic


def _stub_items():
    # Deterministic stub item set when the eval bank isn't importable in a pure-stdlib run.
    return [{"id": f"i{i}", "leaf_tag": t, "difficulty": (i % 5) + 1}
            for i, t in enumerate(["topic::calculus::integral_single",
                                    "topic::calculus::differential_single",
                                    "topic::algebra::linear"] * 22)]  # 66 items ~ one exam form


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--students", type=int, default=40)
    ap.add_argument("--out", default="scoring/out")
    args = ap.parse_args(argv)

    items = _stub_items()
    attempts = simulate_attempts(items, n_students=args.students, seed=args.seed)
    students = sorted({a.student_id for a in attempts})
    k = max(1, int(0.7 * len(students)))
    train_students = set(students[:k])
    test_students = set(students[k:])
    train = [a for a in attempts if a.student_id in train_students]
    test = [a for a in attempts if a.student_id in test_students]

    # Mastery per student from that student's own answers (documented mild optimism
    # for held-out students; honest label carried through). Firewalled from theta/b.
    mastery_cache = {s: student_mastery(attempts, s) for s in students}
    model = performance.fit_performance(train, lambda sid: mastery_cache[sid], coverage=1.0)

    # Per-item calibration on held-out students.
    probs = [model.predict({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                           mastery_cache[a.student_id].get(a.leaf_tag, 0.0), 1.0)
             for a in test]
    y = [a.correct for a in test]

    # Form-level residuals: |predicted_frac - realized_frac| per held-out student
    # (aggregate; shrinks with form size) -> feeds the conformal Readiness width.
    form_residuals = []
    for s in sorted(test_students):
        m = mastery_cache[s]
        preds = [model.predict({"leaf_tag": it["leaf_tag"], "difficulty": it["difficulty"]},
                               m.get(it["leaf_tag"], 0.0), 1.0) for it in items]
        realized = [a.correct for a in attempts if a.student_id == s]
        if realized:
            form_residuals.append(sum(preds) / len(preds) - sum(realized) / len(realized))

    table = json.load(open(os.path.join(os.path.dirname(__file__), "data", "ets_percentiles.json")))
    metrics = {"brier": calibration.brier(probs, y), "ece": calibration.ece(probs, y),
               "reliability": calibration.reliability_bins(probs, y),
               "n_form_residuals": len(form_residuals), "note": _NOTE}

    # Project Readiness over one exam-sized set of item predictions.
    exam_probs = probs[:66] if len(probs) >= 66 else probs
    read = readiness.project(exam_probs, table, form_residuals, reviews=10**9, coverage=1.0)

    # Performance aggregate interval (analytic SE) for a representative mid item.
    perf_point, perf_lo, perf_hi = model.predict_interval(
        {"leaf_tag": items[0]["leaf_tag"], "difficulty": 3}, mastery=0.5, coverage=1.0)

    sc = scorecard.build(
        memory={"estimate": 0.0, "low": 0.0, "high": 0.0, "coverage_pct": 0.0},
        performance={"estimate": round(perf_point, 4), "low": round(perf_lo, 4), "high": round(perf_hi, 4)},
        readiness={**read, "coverage_pct": 1.0, "confidence": "low",
                   "reasons": read.get("reasons", []), "best_next_topic": items[0]["leaf_tag"]},
        source=f"simulated (S={args.students}) + 0 real; {_NOTE}",
        updated_at=_FIXED_TS,
    )

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, sort_keys=True, indent=2)
    with open(os.path.join(args.out, "sample_scorecard.json"), "w") as fh:
        json.dump(sc, fh, sort_keys=True, indent=2)
    # Prospective calibration log: predicted range now, realized filled in later.
    calibration.append_log(os.path.join(args.out, "calibration_log.jsonl"), {
        "timestamp": _FIXED_TS, "readiness_low": read.get("low"),
        "readiness_high": read.get("high"), "shown": read.get("shown"), "realized": None})

    print(f"scoring: brier={metrics['brier']:.4f} ece={metrics['ece']:.4f} "
          f"readiness_shown={read.get('shown')} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
