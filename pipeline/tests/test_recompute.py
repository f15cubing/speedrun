"""Test 4: generated computational backs match an independent SymPy recomputation.

Cards render math as LaTeX, so we no longer parse the rendered strings. Instead
each recheckable card exposes its ground-truth SymPy objects under ``_expr`` (a
test-only key never written to the note). For differential_single we
re-differentiate the stored integrand and compare to the stored answer; for
integral_single we differentiate the stored antiderivative and compare to the
stored integrand. Both are independent re-derivations (we do not trust equality
of the stored value with itself — we recompute from the problem side).
"""

import sympy as sp

import generate_deck
import taxonomy

X = generate_deck.x


def _cards_for(leaf, seed=42):
    tag = taxonomy.TAG_BY_LEAF[leaf]
    return [c for c in generate_deck.generate_cards(seed=seed) if c["leaf_tag"] == tag]


def test_differential_single_backs_are_correct():
    checked = 0
    for card in _cards_for("differential_single"):
        meta = card["_expr"]
        f = meta["f"]
        claimed = meta["answer"]
        assert sp.simplify(sp.diff(f, X) - claimed) == 0, card
        checked += 1
    assert checked >= 2


def test_integral_single_backs_are_correct():
    checked = 0
    for card in _cards_for("integral_single"):
        meta = card["_expr"]
        integrand = meta["integrand"]
        antiderivative = meta["antiderivative"]
        # d/dx of the claimed antiderivative must equal the integrand.
        assert sp.simplify(sp.diff(antiderivative, X) - integrand) == 0, card
        checked += 1
    assert checked >= 2
