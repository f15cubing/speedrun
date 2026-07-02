"""Poisson-binomial via DP convolution (pure stdlib)."""
from scoring.poisson_binomial import expected_and_var, pmf


def test_pmf_sums_to_one_and_length():
    p = pmf([0.2, 0.5, 0.9, 0.1])
    assert len(p) == 5  # 0..4 successes
    assert abs(sum(p) - 1.0) < 1e-12


def test_reduces_to_binomial_when_equal():
    # All p=0.5, n=3 -> pmf = [1,3,3,1]/8
    p = pmf([0.5, 0.5, 0.5])
    assert abs(p[0] - 0.125) < 1e-12
    assert abs(p[1] - 0.375) < 1e-12
    assert abs(p[3] - 0.125) < 1e-12


def test_expected_matches_sum_of_probs():
    probs = [0.1, 0.4, 0.7, 0.9]
    mean, var = expected_and_var(probs)
    assert abs(mean - sum(probs)) < 1e-12
    assert abs(var - sum(pi * (1 - pi) for pi in probs)) < 1e-12


def test_deterministic_edge_cases():
    assert pmf([]) == [1.0]
    assert pmf([1.0]) == [0.0, 1.0]
    assert pmf([0.0]) == [1.0, 0.0]
