# scoring/performance.py
"""Performance model: calibrated P(correct) on a new item + bootstrap interval."""
from __future__ import annotations

import random

from scoring.features import build_features
from scoring.logistic import LogisticModel


class PerformanceModel:
    def __init__(self, model: LogisticModel):
        self._model = model

    def predict(self, item, mastery, coverage) -> float:
        x = build_features({"leaf_tag": item["leaf_tag"], "difficulty": item["difficulty"]},
                           {item["leaf_tag"]: mastery}, coverage)
        return self._model.predict_proba_one(x)

    def predict_interval(self, feats, *, b: int = 1000, seed: int = 0):
        # Bootstrap over the provided feature rows for an honest width.
        rng = random.Random(seed)
        base = [self._model.predict_proba_one(_vec(f)) for f in feats]
        point = sum(base) / len(base)
        means = []
        for _ in range(b):
            sample = [base[rng.randrange(len(base))] for _ in base]
            means.append(sum(sample) / len(sample))
        means.sort()
        lo = means[int(0.05 * len(means))]
        hi = means[min(len(means) - 1, int(0.95 * len(means)))]
        return point, lo, hi


def _vec(f):
    return build_features({"leaf_tag": f["leaf_tag"], "difficulty": f["difficulty"]},
                          {f["leaf_tag"]: f.get("mastery", 0.0)}, f.get("coverage", 0.0),
                          f.get("time_z", 0.0))


def fit_performance(attempts, mastery_fn, coverage, *, seed: int = 0) -> PerformanceModel:
    X, y = [], []
    for a in attempts:
        mastery = mastery_fn(a.student_id).get(a.leaf_tag, 0.0)
        X.append(build_features({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                                {a.leaf_tag: mastery}, coverage, a.time_z))
        y.append(a.correct)
    model = LogisticModel()
    model.fit(X, y, lr=0.3, epochs=3000, l2=1e-4, seed=seed)
    return PerformanceModel(model)
