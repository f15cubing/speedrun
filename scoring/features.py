"""Feature assembly for the Performance model (pure stdlib).

Features (stable order): the item's leaf-topic mastery (mean FSRS recall from
the W1 mastery query), authored difficulty (z-ish, centered on the 1-5 mid),
response-time z-score, and topic coverage. Difficulty is imported/authored —
never estimated from the student being scored (firewall).
"""
from __future__ import annotations

import statistics

FEATURE_ORDER = ("mastery_recall", "difficulty_z", "time_z", "coverage")

_DIFF_MID = 3.0     # midpoint of the authored 1-5 scale
_DIFF_SCALE = 1.414  # ~sd of a uniform 1-5, keeps difficulty_z O(1)


def build_features(item, mastery_by_leaf, coverage, time_z=0.0) -> list[float]:
    mastery = float(mastery_by_leaf.get(item["leaf_tag"], 0.0))
    difficulty_z = (float(item["difficulty"]) - _DIFF_MID) / _DIFF_SCALE
    values = {
        "mastery_recall": mastery,
        "difficulty_z": difficulty_z,
        "time_z": float(time_z),
        "coverage": float(coverage),
    }
    return [values[name] for name in FEATURE_ORDER]


def zscore(values) -> list[float]:
    if not values:
        return []
    mean = statistics.fmean(values)
    if len(values) < 2:
        return [0.0 for _ in values]
    sd = statistics.pstdev(values)
    if sd == 0:
        return [0.0 for _ in values]
    return [(v - mean) / sd for v in values]
