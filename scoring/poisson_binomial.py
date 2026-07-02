"""Poisson-binomial distribution (sum of independent non-identical Bernoullis).

pmf via O(n^2) DP convolution — exact, pure stdlib. Used to turn per-item
P(correct) into a raw-correct distribution for the Readiness projection.
"""
from __future__ import annotations


def pmf(probs) -> list[float]:
    dist = [1.0]  # P(0 successes) = 1 before adding any item
    for p in probs:
        p = max(0.0, min(1.0, float(p)))
        nxt = [0.0] * (len(dist) + 1)
        for k, dk in enumerate(dist):
            nxt[k] += dk * (1.0 - p)      # item wrong
            nxt[k + 1] += dk * p          # item right
        dist = nxt
    return dist


def expected_and_var(probs) -> tuple[float, float]:
    mean = sum(float(p) for p in probs)
    var = sum(float(p) * (1.0 - float(p)) for p in probs)
    return mean, var
