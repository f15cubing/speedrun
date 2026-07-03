# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Memory/Performance calibration proof (Block D, Step-1 proof).

Trains the Performance model on a held-out split of the simulated attempt set
(the same pure-stdlib machinery in ``scoring/``), then measures how well the
predicted P(correct) matches realized accuracy — a reliability curve + ECE +
Brier. "Predicted 80% ⇒ ~80% realized" is the honest calibration claim.

HONESTY LABEL: validated on SIMULATED data (machinery check); real predictive
validity is unestablished at n≈1. This proves the calibration math is sound, not
that the model predicts a specific real student.

Deterministic (fixed seed). Emits JSON + (if matplotlib present) a PNG chart.
"""
from __future__ import annotations

import argparse
import json
import os

from scoring import calibration
from scoring.performance import fit_performance
from scoring.simulate import simulate_attempts, student_mastery

_NOTE = (
    "validated on simulated data (machinery check); "
    "real predictive validity unestablished at n\u22481"
)


def _items(n_leaves: int = 12):
    leaves = [
        "topic::calculus::differential_single",
        "topic::calculus::integral_single",
        "topic::calculus::sequences_series",
        "topic::algebra::linear",
        "topic::algebra::abstract_group",
        "topic::algebra::number_theory",
        "topic::additional::discrete",
        "topic::additional::probability",
        "topic::additional::statistics",
        "topic::additional::geometry",
        "topic::additional::real_analysis",
        "topic::additional::complex",
    ][:n_leaves]
    items = []
    for i in range(n_leaves * 6):
        items.append({
            "id": f"i{i}",
            "leaf_tag": leaves[i % n_leaves],
            "difficulty": (i % 5) + 1,
        })
    return items


def run(seed: int, students: int, n_bins: int) -> dict:
    items = _items()
    attempts = simulate_attempts(items, n_students=students, seed=seed)
    # Student-level split: fit on 70% of students, test on the held-out 30%.
    sids = sorted({a.student_id for a in attempts})
    cut = max(1, int(0.7 * len(sids)))
    train_ids, test_ids = set(sids[:cut]), set(sids[cut:])
    train = [a for a in attempts if a.student_id in train_ids]
    test = [a for a in attempts if a.student_id in test_ids]

    model = fit_performance(train, lambda sid: student_mastery(train, sid), coverage=1.0)

    probs, y = [], []
    for a in test:
        mastery = student_mastery(train, a.student_id).get(a.leaf_tag, 0.5)
        p = model.predict({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                          mastery=mastery, coverage=1.0)
        probs.append(p)
        y.append(a.correct)

    bins = calibration.reliability_bins(probs, y, n_bins=n_bins)
    return {
        "note": _NOTE,
        "seed": seed,
        "students": students,
        "n_train_attempts": len(train),
        "n_test_attempts": len(test),
        "brier": round(calibration.brier(probs, y), 4),
        "ece": round(calibration.ece(probs, y, n_bins=n_bins), 4),
        "reliability_bins": [
            {k: (round(v, 4) if isinstance(v, float) else v) for k, v in b.items()}
            for b in bins
        ],
    }


def chart(result: dict, out_png: str) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False
    bins = result["reliability_bins"]
    conf = [b["confidence"] for b in bins]
    acc = [b["accuracy"] for b in bins]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "--", color="#888", label="perfect calibration")
    ax.plot(conf, acc, "o-", color="#2b6cb0", label="Performance model")
    ax.set_xlabel("Predicted P(correct)")
    ax.set_ylabel("Realized accuracy (held-out)")
    ax.set_title(f"Memory/Performance calibration\nBrier={result['brier']}  ECE={result['ece']}")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left", fontsize=8)
    ax.text(0.02, -0.13, result["note"], transform=ax.transAxes, fontsize=6, color="#666")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--students", type=int, default=400)
    ap.add_argument("--bins", type=int, default=10)
    ap.add_argument("--out", default="docs/evidence/proofs/calibration.json")
    ap.add_argument("--png", default="docs/evidence/proofs/calibration.png")
    args = ap.parse_args(argv)

    result = run(args.seed, args.students, args.bins)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, sort_keys=True, indent=2)
    charted = chart(result, args.png)
    print(f"calibration: Brier={result['brier']}  ECE={result['ece']}  "
          f"bins={len(result['reliability_bins'])}  chart={'yes' if charted else 'no (matplotlib absent)'}")
    print(f"  note: {result['note']}")
    print(f"  -> {args.out}" + (f", {args.png}" if charted else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
