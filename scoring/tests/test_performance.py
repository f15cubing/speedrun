# scoring/tests/test_performance.py
from scoring.performance import fit_performance
from scoring.simulate import simulate_attempts, student_mastery

_ITEMS = [{"id": f"i{i}", "leaf_tag": "topic::calculus::integral_single",
           "difficulty": (i % 5) + 1} for i in range(20)]


def test_performance_predicts_higher_for_easier_low_difficulty():
    at = simulate_attempts(_ITEMS, n_students=200, seed=7)
    model = fit_performance(at, lambda sid: student_mastery(at, sid), coverage=1.0)
    easy = model.predict({"leaf_tag": "topic::calculus::integral_single", "difficulty": 1},
                         mastery=0.9, coverage=1.0)
    hard = model.predict({"leaf_tag": "topic::calculus::integral_single", "difficulty": 5},
                         mastery=0.9, coverage=1.0)
    assert 0.0 <= hard <= 1.0 and 0.0 <= easy <= 1.0
    assert easy > hard


def test_single_item_interval_is_nondegenerate_and_brackets_point():
    # The key n≈1 case: a SINGLE new item must still get a real, non-zero width
    # (analytic Fisher-information SE) — not the degenerate width-0 of a naive
    # prediction-bootstrap.
    at = simulate_attempts(_ITEMS, n_students=120, seed=2)
    model = fit_performance(at, lambda sid: student_mastery(at, sid), coverage=1.0)
    item = {"leaf_tag": "topic::calculus::integral_single", "difficulty": 3}
    point, lo, hi = model.predict_interval(item, mastery=0.5, coverage=1.0)
    assert 0.0 <= lo <= point <= hi <= 1.0
    assert hi - lo > 1e-3, "single-item interval must have real width"


def test_predict_is_platt_calibrated_probability():
    at = simulate_attempts(_ITEMS, n_students=120, seed=5)
    model = fit_performance(at, lambda sid: student_mastery(at, sid), coverage=1.0)
    p = model.predict({"leaf_tag": "topic::calculus::integral_single", "difficulty": 3},
                      mastery=0.5, coverage=1.0)
    assert 0.0 <= p <= 1.0
