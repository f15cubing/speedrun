# scoring/tests/test_readiness.py
import json

from scoring.readiness import give_up, project, raw_correct_distribution, scaled_from_percentile

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
    probs = [0.5] * 10
    out = project(probs, _TABLE, residuals=[1.0], max_width=1)  # wide residual -> interval too wide -> gated
    assert out["shown"] is False and out["estimate"] is None
