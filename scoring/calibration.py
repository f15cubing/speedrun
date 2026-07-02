# scoring/calibration.py
"""Calibration metrics + prospective log (pure stdlib)."""
from __future__ import annotations

import json
import os


def brier(probs, y) -> float:
    return sum((p - yi) ** 2 for p, yi in zip(probs, y)) / len(probs)


def reliability_bins(probs, y, n_bins: int = 10):
    bins = []
    for i in range(n_bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        idx = [j for j, p in enumerate(probs) if (p >= lo and (p < hi or (i == n_bins - 1 and p <= hi)))]
        if not idx:
            continue
        conf = sum(probs[j] for j in idx) / len(idx)
        acc = sum(y[j] for j in idx) / len(idx)
        bins.append({"lo": lo, "hi": hi, "n": len(idx), "confidence": conf, "accuracy": acc})
    return bins


def ece(probs, y, n_bins: int = 10) -> float:
    n = len(probs)
    return sum(b["n"] / n * abs(b["accuracy"] - b["confidence"]) for b in reliability_bins(probs, y, n_bins))


def append_log(path, entry) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
