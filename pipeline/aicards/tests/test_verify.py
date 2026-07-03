# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the verification layer: SymPy CAS + numeric probe + NLI-proxy."""

import sympy as sp

import verify

x = sp.Symbol("x")


# --- computational: symbolic CAS (Rater A / pipeline gate) ------------------
def test_diff_correct_and_wrong():
    f = x ** 3 + 2 * x
    good = verify.verify_computational({"op": "diff", "f": f, "var": x}, 3 * x ** 2 + 2)
    bad = verify.verify_computational({"op": "diff", "f": f, "var": x}, 3 * x ** 2 + 1)
    assert good.ok is True
    assert bad.ok is False


def test_antiderivative_verified_via_derivative():
    f = 2 * x
    # x**2 + C is correct for any C; the check must accept it (constant killed).
    good = verify.verify_computational({"op": "antideriv", "f": f, "var": x}, x ** 2 + 7)
    wrong = verify.verify_computational({"op": "antideriv", "f": f, "var": x}, x ** 3)
    assert good.ok is True
    assert wrong.ok is False


def test_definite_integral_and_gcd():
    di = verify.verify_computational(
        {"op": "defint", "f": x ** 2, "var": x, "lo": 0, "hi": 3}, sp.Integer(9)
    )
    assert di.ok is True
    g_ok = verify.verify_computational({"op": "gcd", "m": 48, "n": 36}, sp.Integer(12))
    g_bad = verify.verify_computational({"op": "gcd", "m": 48, "n": 36}, sp.Integer(6))
    assert g_ok.ok is True and g_bad.ok is False


# --- computational: numeric probe (Rater B, independent method) -------------
def test_numeric_probe_agrees_with_symbolic():
    f = x ** 3 + 2 * x
    good = verify.numeric_check({"op": "diff", "f": f, "var": x}, 3 * x ** 2 + 2)
    bad = verify.numeric_check({"op": "diff", "f": f, "var": x}, 3 * x ** 2 + 100)
    assert good.ok is True
    assert bad.ok is False


def test_numeric_probe_on_antiderivative():
    f = sp.cos(x)
    good = verify.numeric_check({"op": "antideriv", "f": f, "var": x}, sp.sin(x) + 3)
    bad = verify.numeric_check({"op": "antideriv", "f": f, "var": x}, -sp.sin(x))
    assert good.ok is True
    assert bad.ok is False


# --- conceptual: NLI-proxy entailment ---------------------------------------
def test_entailment_high_when_claim_supported_by_quote():
    quote = (
        "The harmonic series, the sum of the reciprocals of the positive integers, "
        "diverges even though its terms tend to zero."
    )
    claim = "The harmonic series diverges."
    assert verify.entailment_score(claim, quote) >= 0.8
    assert verify.entails(claim, quote) is True


def test_entailment_low_when_claim_unsupported():
    quote = "The derivative of the sine function is the cosine function."
    claim = "Every continuous function is differentiable everywhere."
    assert verify.entailment_score(claim, quote) < 0.5
    assert verify.entails(claim, quote) is False


# --- human-review routing ---------------------------------------------------
def test_conceptual_cards_always_need_human_review():
    from cards import GeneratedCard, CONCEPTUAL, COMPUTATIONAL

    concept = GeneratedCard(
        card_id="c1", leaf_tag="topic::additional::real_analysis",
        kind=CONCEPTUAL, front="q", back="a",
    )
    comp = GeneratedCard(
        card_id="c2", leaf_tag="topic::calculus::differential_single",
        kind=COMPUTATIONAL, front="q", back="a",
    )
    assert verify.needs_human_review(concept) is True
    assert verify.needs_human_review(comp) is False
