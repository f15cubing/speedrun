"""Unit tests for the distractor engine (pipeline/distractors.py)."""

import random

import sympy as sp

import distractors
import mathfmt

X = sp.Symbol("x")


def test_make_options_has_five_distinct_with_correct_at_index():
    rng = random.Random(0)
    correct = sp.sympify("x**2 + 3")
    wrongs = [sp.sympify("x**2 - 3"), sp.sympify("2*x"), sp.sympify("x**3 + 3")]
    options, idx = distractors.make_options(rng, correct, wrongs)
    assert len(options) == 5
    assert len(set(options)) == 5, options
    assert options[idx] == mathfmt.expr_inline(correct)


def test_options_are_latex_delimited():
    rng = random.Random(0)
    correct = sp.sympify("x**2 + 3")
    wrongs = [sp.sympify("x**2 - 3"), sp.sympify("2*x"), sp.sympify("x**3 + 3")]
    options, _idx = distractors.make_options(rng, correct, wrongs)
    for opt in options:
        assert opt.startswith("\\(") and opt.endswith("\\)"), opt


def test_make_options_is_deterministic_for_fixed_seed():
    correct = sp.Integer(7)
    wrongs = [sp.Integer(13), sp.Integer(1)]
    a = distractors.make_options(random.Random(5), correct, wrongs)
    b = distractors.make_options(random.Random(5), correct, wrongs)
    assert a == b


def test_make_options_drops_wrongs_equal_to_key():
    rng = random.Random(0)
    correct = sp.sympify("x + 1")
    # First wrong equals the key (after simplify) and must be discarded.
    wrongs = [sp.sympify("1 + x"), sp.sympify("x - 1")]
    options, idx = distractors.make_options(rng, correct, wrongs)
    assert options.count(mathfmt.expr_inline(correct)) == 1


def test_make_options_raises_when_too_few_distinct():
    rng = random.Random(0)
    correct = sp.Integer(0)
    # All variants collapse to 0 / duplicates -> cannot form 4 distinct wrongs.
    with __import__("pytest").raises(distractors.InsufficientDistractors):
        distractors.make_options(rng, correct, [sp.Integer(0)], n_options=12)
