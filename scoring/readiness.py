# scoring/readiness.py
"""Readiness: projected raw-correct -> ETS percentile -> 200-990, as a RANGE
with a give-up gate. (Spec §3.)

The uncertainty is computed at the AGGREGATE (whole-exam) level, not per item:
- aleatoric spread of the exam score fraction from the Poisson-binomial:
  sd_frac = sqrt(Σ p(1-p)) / n  (shrinks ~1/√n),
- a split-conformal half-width from held-out FORM-level residuals
  |predicted_frac − realized_frac| (also shrinks with form size).
Headline interval = conformal (falls back to the normal aleatoric band when no
form residuals are supplied). A Bayesian normal-posterior band is the
cross-check. A well-prepared, high-coverage student can therefore actually clear
the width gate — while a thin record stays honestly gated.
"""
from __future__ import annotations

import math

from scoring.poisson_binomial import pmf

READINESS_MAX_INTERVAL_WIDTH = 120  # scaled-score points (total). Declared pre-run; never tuned.
_Z90 = 1.6448536269514722


def raw_correct_distribution(probs):
    return pmf(probs)


def fraction_sd(probs) -> float:
    """SD of the exam score fraction under the Poisson-binomial (aleatoric)."""
    n = len(probs)
    if n == 0:
        return 0.0
    var_count = sum(p * (1.0 - p) for p in probs)
    return math.sqrt(var_count) / n


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


def conformal_halfwidth(form_residuals, *, level: float = 0.90) -> float:
    """Split-conformal half-width in fraction space from held-out FORM residuals.

    Finite-sample corrected quantile (ceil((n+1)·level)/n) of |residual|.
    """
    vals = sorted(abs(r) for r in form_residuals)
    if not vals:
        return 0.0
    n = len(vals)
    rank = min(n, math.ceil((n + 1) * level))
    return vals[rank - 1]


def give_up(reviews, coverage, width, *, max_width: float = READINESS_MAX_INTERVAL_WIDTH):
    reasons = []
    if reviews < 200:
        reasons.append("<200 graded reviews")
    if coverage < 0.50:
        reasons.append("<50% topic coverage")
    if width > max_width:
        reasons.append("interval too wide")
    return reasons


def project(probs, table, form_residuals=None, *, reviews=10**9, coverage=1.0,
            max_width: float = READINESS_MAX_INTERVAL_WIDTH):
    """Project a scaled-score RANGE + give-up decision.

    ``form_residuals`` are aggregate |predicted_frac − realized_frac| over
    held-out exam-sized forms. Headline interval is conformal (or the normal
    aleatoric band when no form residuals are given); ``bayes_*`` is the
    normal-posterior cross-check from the Poisson-binomial SD.
    """
    n = len(probs)
    exp_frac = sum(probs) / n if n else 0.0
    point = scaled_from_percentile(exp_frac, table)

    sd = fraction_sd(probs)
    aleatoric_half = _Z90 * sd
    conformal_half = conformal_halfwidth(form_residuals) if form_residuals else aleatoric_half
    half = max(conformal_half, aleatoric_half)  # never narrower than the exam's own noise

    lo = scaled_from_percentile(max(0.0, exp_frac - half), table)
    hi = scaled_from_percentile(min(1.0, exp_frac + half), table)
    width = hi - lo

    # Bayesian cross-check: normal posterior on the fraction (aleatoric spread).
    bayes_lo = scaled_from_percentile(max(0.0, exp_frac - aleatoric_half), table)
    bayes_hi = scaled_from_percentile(min(1.0, exp_frac + aleatoric_half), table)

    reasons = give_up(reviews, coverage, width, max_width=max_width)
    if reasons:
        return {"shown": False, "estimate": None, "low": None, "high": None,
                "width": width, "reasons": reasons,
                "bayes_low": bayes_lo, "bayes_high": bayes_hi, "sd_frac": sd}
    return {"shown": True, "estimate": point, "low": lo, "high": hi, "width": width,
            "reasons": [], "bayes_low": bayes_lo, "bayes_high": bayes_hi, "sd_frac": sd}
