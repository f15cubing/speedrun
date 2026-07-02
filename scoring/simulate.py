"""Hybrid attempt harness (pure stdlib).

Simulated students give the pipeline enough (features -> outcome) rows to fit
Platt, bootstrap intervals, and draw a real reliability curve. A small real
self-answered CSV is an honest sanity anchor. The model never sees the
generative theta/b — only the resulting outcomes + authored difficulty.
"""
from __future__ import annotations

import csv
import os
import random
from collections import namedtuple

from scoring.logistic import sigmoid

Attempt = namedtuple("Attempt", "student_id item_id leaf_tag difficulty correct time_z")

_DIFF_MID = 3.0
_DIFF_SCALE = 1.414


def simulate_attempts(items, n_students: int = 40, seed: int = 42):
    rng = random.Random(seed)
    leaves = sorted({it["leaf_tag"] for it in items})
    attempts = []
    for s in range(n_students):
        theta = {leaf: rng.gauss(0.0, 1.0) for leaf in leaves}
        for it in items:
            b_z = (float(it["difficulty"]) - _DIFF_MID) / _DIFF_SCALE
            p = sigmoid(theta[it["leaf_tag"]] - b_z)
            correct = 1 if rng.random() < p else 0
            time_z = rng.gauss(0.0, 1.0)
            attempts.append(Attempt(f"sim{s}", it["id"], it["leaf_tag"],
                                    int(it["difficulty"]), correct, round(time_z, 6)))
    return attempts


def load_real_attempts(path: str = "scoring/data/real_attempts.csv"):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("item_id"):
                continue
            out.append(Attempt(row["student_id"], row["item_id"], row["leaf_tag"],
                               int(row["difficulty"]), int(row["correct"]),
                               float(row.get("time_z", 0.0))))
    return out


def student_mastery(attempts, student_id):
    by_leaf: dict[str, list[int]] = {}
    for a in attempts:
        if a.student_id == student_id:
            by_leaf.setdefault(a.leaf_tag, []).append(a.correct)
    return {leaf: sum(v) / len(v) for leaf, v in by_leaf.items() if v}
