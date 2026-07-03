# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the gold-set gate: raters, Cohen's kappa, fact-precision, useful-yield."""

from collections import Counter

import pytest

import goldset_gate as gate
import orchestrator
from goldset_gate import BAD_PEDAGOGY, CORRECT, WRONG
from orchestrator import Decision, Outcome
from stub_model import StubBackend


def _run():
    outcomes = orchestrator.run_pipeline(StubBackend(seed=42))
    return outcomes, gate.run_gate(outcomes)


# --- lodged cutoffs ---------------------------------------------------------
def test_cutoffs_are_lodged_constants():
    assert gate.FACT_PRECISION_MIN == 0.98
    assert gate.USEFUL_YIELD_MIN == 0.60


# --- Cohen's kappa math (independent of the stub) ---------------------------
def test_kappa_perfect_agreement():
    a = [CORRECT, WRONG, BAD_PEDAGOGY, CORRECT]
    assert gate.cohens_kappa(a, list(a)) == 1.0
    assert gate.percent_agreement(a, list(a)) == 100.0


def test_kappa_known_value():
    # 10 items, 8 agree -> Po = 0.8. One C->W and one W->C so both marginals stay
    # C=6, W=4.  Pe = 0.6*0.6 + 0.4*0.4 = 0.52.  kappa = (0.8-0.52)/(1-0.52) = 0.5833.
    a = [CORRECT] * 6 + [WRONG] * 4
    b = [CORRECT] * 5 + [WRONG] * 4 + [CORRECT] * 1
    assert gate.percent_agreement(a, b) == 80.0
    assert gate.cohens_kappa(a, b) == pytest.approx(0.5833, abs=1e-4)


# --- rater label distribution on the stub -----------------------------------
def test_rater_label_distributions():
    outcomes, _ = _run()
    cards = [o.card for o in outcomes]
    la = Counter(gate.rate_a(c) for c in cards)
    lb = Counter(gate.rate_b(c) for c in cards)
    # Rater A (entailment threshold 0.70): borderline conceptual -> WRONG
    assert la[CORRECT] == 40 and la[WRONG] == 7 and la[BAD_PEDAGOGY] == 3
    # Rater B (entailment threshold 0.60): borderline conceptual -> CORRECT
    assert lb[CORRECT] == 41 and lb[WRONG] == 6 and lb[BAD_PEDAGOGY] == 3


def test_interrater_reliability_reported():
    _, result = _run()
    assert result.percent_agreement == pytest.approx(98.0)  # 49/50
    assert 0.85 < result.cohens_kappa < 1.0


# --- gate metrics on the stub -----------------------------------------------
def test_gate_metrics_and_pass():
    _, result = _run()
    assert result.generated == 50
    assert result.published == 35
    assert result.human_review_drafts == 5
    assert result.fact_precision == pytest.approx(1.0)       # CAS is decisive
    assert result.fact_precision_secondary == pytest.approx(1.0)  # numeric audit agrees
    assert result.useful_yield == pytest.approx(32 / 50)     # 0.64
    assert result.passed is True


def test_safety_recall_all_wrong_computational_abstained():
    _, result = _run()
    # every rater-flagged wrong computational card was abstained by the pipeline
    assert result.safety_recall == pytest.approx(1.0)


# --- the gate has teeth: it can FAIL ---------------------------------------
def _fake_published(card_correct):
    """Build a minimal Outcome list: publish one card, rater label controllable."""
    from cards import GeneratedCard, COMPUTATIONAL
    import sympy as sp
    from provenance import Provenance
    x = sp.Symbol("x")
    good_prov = Provenance(
        quote="The power rule states that the derivative of x raised to the power n "
              "is n times x raised to the power n minus one.",
        anchor="svc-03-power-rule",
    )
    claimed = 2 * x if card_correct else 2 * x + 1  # wrong answer if not correct
    card = GeneratedCard("f1", "topic::calculus::differential_single", COMPUTATIONAL,
                         "Differentiate f(x) = x**2.", "f'(x) = ...", good_prov,
                         {"op": "diff", "f": x ** 2, "var": x, "claimed": claimed})
    return [Outcome(card=card, decision=Decision.PUBLISH_VERIFIED, detail="", request=None)]


def test_gate_fails_on_a_wrong_fact_in_published_set():
    # Force a wrong-fact card into the published set (simulating a verifier bug).
    result = gate.run_gate(_fake_published(card_correct=False))
    assert result.fact_precision < gate.FACT_PRECISION_MIN
    assert result.passed is False


def test_gate_fails_on_low_useful_yield():
    from cards import GeneratedCard, COMPUTATIONAL
    import sympy as sp
    from provenance import Provenance
    x = sp.Symbol("x")
    prov = Provenance(
        quote="The power rule states that the derivative of x raised to the power n "
              "is n times x raised to the power n minus one.",
        anchor="svc-03-power-rule",
    )
    # 10 generated, but only 1 publishable+correct -> yield 0.1 < 0.60
    outcomes = []
    good = GeneratedCard("g", "topic::calculus::differential_single", COMPUTATIONAL,
                         "Differentiate f(x) = x**2.", "f'(x) = 2*x", prov,
                         {"op": "diff", "f": x ** 2, "var": x, "claimed": 2 * x})
    outcomes.append(Outcome(good, Decision.PUBLISH_VERIFIED, "", None))
    for i in range(9):
        c = GeneratedCard("a%d" % i, "topic::calculus::differential_single", COMPUTATIONAL,
                          "q", "a", None, {"op": "diff", "f": x, "var": x, "claimed": 1})
        outcomes.append(Outcome(c, Decision.ABSTAIN_NO_PROVENANCE, "", None))
    result = gate.run_gate(outcomes)
    assert result.useful_yield < gate.USEFUL_YIELD_MIN
    assert result.passed is False
