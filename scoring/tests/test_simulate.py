"""Hybrid attempt harness: deterministic simulation + real-CSV loader."""
from scoring.simulate import Attempt, load_real_attempts, simulate_attempts, student_mastery

_ITEMS = [
    {"id": "i1", "leaf_tag": "topic::calculus::integral_single", "difficulty": 2},
    {"id": "i2", "leaf_tag": "topic::calculus::integral_single", "difficulty": 5},
    {"id": "i3", "leaf_tag": "topic::algebra::linear", "difficulty": 3},
]


def test_simulation_is_deterministic_and_shaped():
    a = simulate_attempts(_ITEMS, n_students=10, seed=42)
    b = simulate_attempts(_ITEMS, n_students=10, seed=42)
    assert a == b
    assert len(a) == 10 * len(_ITEMS)
    assert all(x.correct in (0, 1) for x in a)


def test_harder_items_are_answered_worse_on_average():
    a = simulate_attempts(_ITEMS, n_students=300, seed=1)
    easy = [x.correct for x in a if x.item_id == "i1"]
    hard = [x.correct for x in a if x.item_id == "i2"]
    assert sum(easy) / len(easy) > sum(hard) / len(hard)


def test_real_loader_missing_is_empty():
    assert load_real_attempts("scoring/data/does_not_exist.csv") == []


def test_student_mastery_is_per_leaf_mean():
    a = simulate_attempts(_ITEMS, n_students=50, seed=3)
    m = student_mastery(a, a[0].student_id)
    assert set(m) <= {"topic::calculus::integral_single", "topic::algebra::linear"}
    assert all(0.0 <= v <= 1.0 for v in m.values())
