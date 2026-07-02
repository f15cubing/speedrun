# scoring/tests/test_readiness.py
import json
import random

from scoring.readiness import (
    conformal_halfwidth,
    give_up,
    project,
    raw_correct_distribution,
    scaled_from_percentile,
)

_TABLE = json.load(open("scoring/data/ets_percentiles.json"))


def test_raw_distribution_sums_to_one():
    d = raw_correct_distribution([0.3, 0.6, 0.9])
    assert abs(sum(d) - 1.0) < 1e-12


def test_scaled_is_monotone_and_clamped():
    lo = scaled_from_percentile(0.02, _TABLE)
    hi = scaled_from_percentile(0.99, _TABLE)
    assert _TABLE["scale_min"] <= lo <= hi <= _TABLE["scale_max"]


def test_give_up_conditions():
    assert "<200 graded reviews" in give_up(reviews=10, coverage=0.9, width=50)
    assert "<50% topic coverage" in give_up(reviews=500, coverage=0.2, width=50)
    assert "interval too wide" in give_up(reviews=500, coverage=0.9, width=999, max_width=120)
    assert give_up(reviews=500, coverage=0.9, width=50, max_width=120) == []


def test_project_gated_off_hides_number():
    # A ludicrously tight width gate forces the "interval too wide" reason even
    # for a large, confident exam -> Readiness must hide the number.
    probs = [0.9] * 66
    out = project(probs, _TABLE, form_residuals=[0.01], max_width=1)
    assert out["shown"] is False and out["estimate"] is None
    assert "interval too wide" in out["reasons"]


def test_well_prepared_high_coverage_can_show_a_range():
    # A well-prepared student over a full exam-sized set, tight form residuals,
    # ample reviews + coverage -> Readiness SHOWS a bounded range (the feature
    # is reachable, not permanently gated).
    probs = [0.85] * 66
    out = project(probs, _TABLE, form_residuals=[0.02, 0.03, 0.025, 0.02, 0.03],
                  reviews=500, coverage=0.9)
    assert out["shown"] is True
    assert out["estimate"] is not None
    assert out["low"] <= out["estimate"] <= out["high"]
    assert out["width"] <= 120


def test_bayesian_crosscheck_present_and_bracketing():
    probs = [0.7] * 66
    out = project(probs, _TABLE, form_residuals=[0.03], reviews=500, coverage=0.9)
    assert "bayes_low" in out and "bayes_high" in out
    assert out["bayes_low"] <= out["bayes_high"]


def test_conformal_halfwidth_empirical_coverage():
    # The split-conformal half-width from a calibration sample should cover ~90%
    # of a fresh sample drawn from the same distribution.
    rng = random.Random(0)
    calib = [rng.gauss(0, 0.05) for _ in range(500)]
    half = conformal_halfwidth(calib, level=0.90)
    fresh = [rng.gauss(0, 0.05) for _ in range(2000)]
    covered = sum(1 for r in fresh if abs(r) <= half) / len(fresh)
    assert 0.85 <= covered <= 0.95
