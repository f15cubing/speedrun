"""Hand-rolled logistic regression + Platt scaling (pure stdlib)."""
import math

from scoring.logistic import LogisticModel, platt_apply, platt_fit, sigmoid


def test_sigmoid_basic():
    assert abs(sigmoid(0.0) - 0.5) < 1e-9
    assert sigmoid(50) > 0.999
    assert sigmoid(-50) < 0.001


def test_learns_separable_1d():
    # y = 1 when x > 0. Model should learn a positive weight + near-zero bias.
    X = [[-3.0], [-2.0], [-1.0], [1.0], [2.0], [3.0]]
    y = [0, 0, 0, 1, 1, 1]
    m = LogisticModel()
    m.fit(X, y, lr=0.5, epochs=5000, seed=0)
    assert m.predict_proba_one([2.0]) > 0.8
    assert m.predict_proba_one([-2.0]) < 0.2


def test_fit_is_deterministic():
    X = [[-1.0], [1.0], [2.0], [-2.0]]
    y = [0, 1, 1, 0]
    a = LogisticModel(); a.fit(X, y, seed=0)
    b = LogisticModel(); b.fit(X, y, seed=0)
    assert a.weights == b.weights and a.bias == b.bias


def test_platt_maps_scores_to_calibrated_probs():
    # Raw scores correlated with label; Platt should push positives high.
    scores = [-2.0, -1.0, 0.5, 1.5, 2.5]
    y = [0, 0, 1, 1, 1]
    a, b = platt_fit(scores, y)
    assert platt_apply(a, b, 2.5) > platt_apply(a, b, -2.0)
