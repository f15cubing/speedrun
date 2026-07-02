"""Per-(student,item) feature assembly."""
from scoring.features import FEATURE_ORDER, build_features, zscore


def test_feature_vector_order_and_values():
    item = {"leaf_tag": "topic::calculus::integral_single", "difficulty": 5}
    vec = build_features(item, {"topic::calculus::integral_single": 0.8}, coverage=0.6, time_z=1.0)
    assert len(vec) == len(FEATURE_ORDER)
    assert abs(vec[FEATURE_ORDER.index("mastery_recall")] - 0.8) < 1e-9
    assert abs(vec[FEATURE_ORDER.index("difficulty_z")] - (5 - 3) / 1.414) < 1e-6
    assert vec[FEATURE_ORDER.index("time_z")] == 1.0
    assert abs(vec[FEATURE_ORDER.index("coverage")] - 0.6) < 1e-9


def test_unseen_leaf_defaults_zero_mastery():
    item = {"leaf_tag": "topic::algebra::linear", "difficulty": 3}
    vec = build_features(item, {}, coverage=0.0)
    assert vec[FEATURE_ORDER.index("mastery_recall")] == 0.0


def test_zscore_zeroes_when_constant():
    assert zscore([2.0, 2.0, 2.0]) == [0.0, 0.0, 0.0]
    z = zscore([1.0, 2.0, 3.0])
    assert abs(sum(z)) < 1e-9  # mean-centered
