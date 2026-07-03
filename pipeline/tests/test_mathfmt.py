"""Unit tests for the math-formatting contract (pipeline/mathfmt.py)."""

import sympy as sp

import mathfmt

x = sp.Symbol("x")


def test_tex_renders_sympy_latex_without_delimiters():
    assert mathfmt.tex(x**2 + 3 * x) == "x^{2} + 3 x"


def test_inline_wraps_with_paren_delimiters():
    assert mathfmt.inline("a + b") == "\\(a + b\\)"


def test_block_wraps_with_bracket_delimiters():
    assert mathfmt.block("a + b") == "\\[a + b\\]"


def test_expr_inline_composes_tex_and_inline():
    assert mathfmt.expr_inline(sp.Rational(1, 2)) == "\\(\\frac{1}{2}\\)"


def test_expr_block_composes_tex_and_block():
    assert mathfmt.expr_block(x**2) == "\\[x^{2}\\]"


def test_rendering_is_deterministic():
    assert mathfmt.expr_inline(x**2 + 3 * x) == mathfmt.expr_inline(x**2 + 3 * x)
