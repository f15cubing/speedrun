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


def test_bootstrap_interval_brackets_point():
    at = simulate_attempts(_ITEMS, n_students=120, seed=2)
    model = fit_performance(at, lambda sid: student_mastery(at, sid), coverage=1.0)
    feats = [{"leaf_tag": "topic::calculus::integral_single", "difficulty": 3, "mastery": 0.5, "coverage": 1.0}]
    mean, lo, hi = model.predict_interval(feats, b=200, seed=0)
    assert lo <= mean <= hi
