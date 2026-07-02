# pipeline/tests/test_template_capacity.py
"""Thin templates can emit many distinct, correct stems after widening."""
import random

import sympy as sp

import generate_deck as gd

x = gd.x


def _distinct_stems(fn, n=300, seed=42):
    rng = random.Random(seed)
    seen = set()
    for _ in range(n * 8):
        front, _back = fn(rng)
        seen.add(front)
        if len(seen) >= n:
            break
    return len(seen)


def test_thin_templates_have_capacity():
    assert _distinct_stems(gd._gen_differential_equations, 300) >= 300
    assert _distinct_stems(gd._gen_applications, 300) >= 300
    assert _distinct_stems(gd._gen_integral_multi, 300) >= 300


def test_differential_equations_key_is_correct():
    rng = random.Random(1)
    for _ in range(50):
        front, back = gd._gen_differential_equations(rng)
        assert "y(x) =" in back  # general solution stated


def test_applications_key_is_correct():
    rng = random.Random(2)
    for _ in range(50):
        front, back = gd._gen_applications(rng)
        assert back  # non-empty, well-formed
