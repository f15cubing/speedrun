# scoring/performance.py
"""Performance model: Platt-calibrated P(correct) on a new item + an honest
estimation-uncertainty interval.

Pipeline (spec §2): logistic regression, then Platt (sigmoid) calibration on a
held-out fold. The predictive interval is the analytic logistic standard error
(Fisher information: se(z) = sqrt(xᵀ Σ x), Σ = (Xᵀ W X)⁻¹), mapped through the
same Platt transform — so a SINGLE new item gets a real, non-zero width driven
by parameter/estimation uncertainty (not by item heterogeneity). Pure stdlib.
"""
from __future__ import annotations

import math

from scoring.features import build_features
from scoring.logistic import LogisticModel, platt_apply, platt_fit
from scoring.logistic import sigmoid  # noqa: F401  (re-export convenience)

_Z90 = 1.6448536269514722  # standard-normal 90% two-sided z


class PerformanceModel:
    def __init__(self, model: LogisticModel, platt_a: float, platt_b: float, cov):
        self._model = model
        self._a = platt_a
        self._b = platt_b
        self._cov = cov  # (f+1)x(f+1) covariance of [bias, w...]

    def predict(self, item, mastery, coverage) -> float:
        z = self._model.decision(_feat(item, mastery, coverage))
        return platt_apply(self._a, self._b, z)

    def predict_interval(self, item, mastery, coverage, *, z_mult: float = _Z90):
        x = _feat(item, mastery, coverage)
        z = self._model.decision(x)
        x_aug = [1.0] + list(x)
        var = 0.0
        for i, xi in enumerate(x_aug):
            row = self._cov[i]
            for j, xj in enumerate(x_aug):
                var += xi * row[j] * xj
        se = math.sqrt(var) if var > 0 else 0.0
        point = platt_apply(self._a, self._b, z)
        lo = platt_apply(self._a, self._b, z - z_mult * se)
        hi = platt_apply(self._a, self._b, z + z_mult * se)
        return point, min(lo, hi), max(lo, hi)


def _feat(item, mastery, coverage):
    return build_features({"leaf_tag": item["leaf_tag"], "difficulty": item["difficulty"]},
                          {item["leaf_tag"]: mastery}, coverage)


def _fisher_cov(model: LogisticModel, X, *, ridge: float = 1e-6):
    """Covariance of the fitted params via the inverse Fisher information.

    I = Xaugᵀ W Xaug (W = diag(p_i(1-p_i))); Σ = (I + ridge·Id)⁻¹. Xaug prepends
    a bias column so index 0 is the intercept.
    """
    dim = len(model.weights) + 1
    info = [[0.0] * dim for _ in range(dim)]
    for x in X:
        p = model.predict_proba_one(x)
        w = p * (1.0 - p)
        xa = [1.0] + list(x)
        for i in range(dim):
            wi = w * xa[i]
            row = info[i]
            for j in range(dim):
                row[j] += wi * xa[j]
    for i in range(dim):
        info[i][i] += ridge
    return _invert(info)


def _invert(matrix):
    """Gauss-Jordan inverse of a small square matrix (pure stdlib)."""
    n = len(matrix)
    aug = [list(row) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-15:
            aug[pivot][col] += 1e-12  # nudge a singular pivot rather than crash
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pv = aug[col][col]
        aug[col] = [v / pv for v in aug[col]]
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor:
                aug[r] = [rv - factor * cv for rv, cv in zip(aug[r], aug[col])]
    return [row[n:] for row in aug]


def fit_performance(attempts, mastery_fn, coverage, *, seed: int = 0) -> PerformanceModel:
    X, y = [], []
    for a in attempts:
        mastery = mastery_fn(a.student_id).get(a.leaf_tag, 0.0)
        X.append(build_features({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                                {a.leaf_tag: mastery}, coverage, a.time_z))
        y.append(a.correct)
    # Held-out fold for Platt calibration (spec §2).
    k = max(1, int(0.8 * len(X)))
    Xf, yf, Xc, yc = X[:k], y[:k], X[k:], y[k:]
    model = LogisticModel()
    model.fit(Xf, yf, lr=0.3, epochs=3000, l2=1e-4, seed=seed)
    if Xc and len(set(yc)) == 2:
        a_platt, b_platt = platt_fit([model.decision(x) for x in Xc], yc, seed=seed)
    else:
        a_platt, b_platt = 1.0, 0.0  # identity when the calib fold is degenerate
    cov = _fisher_cov(model, Xf)
    return PerformanceModel(model, a_platt, b_platt, cov)
