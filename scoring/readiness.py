# scoring/readiness.py
"""Readiness: raw-correct distribution -> ETS percentile -> 200-990 + give-up gate."""
from __future__ import annotations

from scoring.poisson_binomial import pmf

READINESS_MAX_INTERVAL_WIDTH = 120  # scaled-score points (total). Declared pre-run; never tuned.


def raw_correct_distribution(probs):
    return pmf(probs)


def scaled_from_percentile(raw_frac, table):
    anchors = sorted(table["anchors"], key=lambda a: a["raw_frac"])
    lo_s, hi_s = table["scale_min"], table["scale_max"]
    if raw_frac <= anchors[0]["raw_frac"]:
        return max(lo_s, int(anchors[0]["scaled"]))
    if raw_frac >= anchors[-1]["raw_frac"]:
        return min(hi_s, int(anchors[-1]["scaled"]))
    for a0, a1 in zip(anchors, anchors[1:]):
        if a0["raw_frac"] <= raw_frac <= a1["raw_frac"]:
            t = (raw_frac - a0["raw_frac"]) / (a1["raw_frac"] - a0["raw_frac"])
            return int(round(a0["scaled"] + t * (a1["scaled"] - a0["scaled"])))
    return int(anchors[-1]["scaled"])


def give_up(reviews, coverage, width, *, max_width: float = READINESS_MAX_INTERVAL_WIDTH):
    reasons = []
    if reviews < 200:
        reasons.append("<200 graded reviews")
    if coverage < 0.50:
        reasons.append("<50% topic coverage")
    if width > max_width:
        reasons.append("interval too wide")
    return reasons


def project(probs, table, residuals, *, reviews=10**9, coverage=1.0,
            max_width: float = READINESS_MAX_INTERVAL_WIDTH):
    n = len(probs)
    dist = raw_correct_distribution(probs)
    exp_frac = sum(k * dk for k, dk in enumerate(dist)) / n if n else 0.0
    point = scaled_from_percentile(exp_frac, table)
    # Split-conformal half-width from held-out residuals (quantile), mapped to scaled points.
    q = _quantile(sorted(abs(r) for r in residuals), 0.90) if residuals else 0.5
    lo = scaled_from_percentile(max(0.0, exp_frac - q), table)
    hi = scaled_from_percentile(min(1.0, exp_frac + q), table)
    width = hi - lo
    reasons = give_up(reviews, coverage, width, max_width=max_width)
    if reasons:
        return {"shown": False, "estimate": None, "low": None, "high": None,
                "width": width, "reasons": reasons}
    return {"shown": True, "estimate": point, "low": lo, "high": hi, "width": width, "reasons": []}


def _quantile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(q * len(sorted_vals)))
    return sorted_vals[idx]
