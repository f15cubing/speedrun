"""Test 4: generated computational backs match an independent SymPy recomputation.

For differential_single cards we re-differentiate the integrand parsed from the
front and compare to the parsed back; for integral_single cards we differentiate
the parsed antiderivative and compare to the parsed integrand. Both are independent
re-derivations (we do not trust the generator's stored value).
"""

import re

import sympy as sp

import generate_deck
import taxonomy

X = sp.Symbol("x")


def _cards_for(leaf, seed=42):
    tag = taxonomy.TAG_BY_LEAF[leaf]
    return [c for c in generate_deck.generate_cards(seed=seed) if c["leaf_tag"] == tag]


def test_differential_single_backs_are_correct():
    checked = 0
    for card in _cards_for("differential_single"):
        m_front = re.search(r"f\(x\) = (.+)$", card["front"], re.M)
        m_back = re.search(r"f'\(x\) = (.+)$", card["back"], re.M)
        assert m_front and m_back, "unexpected card format: {!r}".format(card)
        f = sp.sympify(m_front.group(1))
        claimed = sp.sympify(m_back.group(1))
        assert sp.simplify(sp.diff(f, X) - claimed) == 0, card
        checked += 1
    assert checked >= 2


def test_integral_single_backs_are_correct():
    checked = 0
    for card in _cards_for("integral_single"):
        m_front = re.search(r"\u222b \((.+)\) dx", card["front"])
        m_back = re.search(r"F\(x\) = (.+) \+ C$", card["back"], re.M)
        assert m_front and m_back, "unexpected card format: {!r}".format(card)
        integrand = sp.sympify(m_front.group(1))
        antiderivative = sp.sympify(m_back.group(1))
        # d/dx of the claimed antiderivative must equal the integrand.
        assert sp.simplify(sp.diff(antiderivative, X) - integrand) == 0, card
        checked += 1
    assert checked >= 2
