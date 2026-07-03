# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the beat-the-baseline comparison (AI pipeline vs template/cloze non-RAG)."""

import pytest

import baseline
import goldset_gate
import verify
from goldset_gate import CORRECT, WRONG


def _report(seed=42):
    return baseline.beat_baseline(seed=seed)


def test_targets_match_declared_composition():
    targets = baseline.build_targets(seed=42)
    assert len(targets) == baseline.N_TARGETS
    from collections import Counter
    counts = Counter(t.category for t in targets)
    assert counts == baseline.TARGET_COMPOSITION


def test_ai_arm_never_publishes_a_wrong_fact():
    r = _report()
    # Every AI-arm published card is CAS-correct: fact-precision is 1.0.
    assert r.ai.fact_precision == pytest.approx(1.0)
    for card in r.ai_published_cards:
        assert verify.verify_computational(card.check, card.check["claimed"]).ok


def test_baseline_arm_leaks_wrong_facts():
    r = _report()
    # The naive baseline publishes wrong facts (no CAS/abstention) -> low precision.
    assert r.baseline.fact_precision < goldset_gate.FACT_PRECISION_MIN
    assert r.baseline.fact_precision == pytest.approx(0.60, abs=1e-9)


def test_per_arm_useful_yield():
    r = _report()
    assert r.ai.useful_yield == pytest.approx(50 / 60)      # 0.8333
    assert r.baseline.useful_yield == pytest.approx(24 / 60)  # 0.40


def test_discordant_counts_and_mcnemar():
    r = _report()
    assert r.b == 30    # AI usable, baseline not (AI wins)
    assert r.c == 4     # AI not, baseline usable
    assert r.a + r.b + r.c + r.d == baseline.N_TARGETS
    assert r.mcnemar.favored == "A"
    assert r.mcnemar.p_value < 0.001
    assert r.ai_beats_baseline is True


def test_bootstrap_ci_excludes_zero_favoring_ai():
    r = _report()
    lo, hi = r.yield_diff_ci
    assert lo > 0     # AI's useful-yield advantage CI excludes 0


def test_same_rater_harness_used_for_both_arms():
    # The comparison must score both arms with the identical rater (goldset_gate.rate_a).
    r = _report()
    assert r.rater_name == "A (cas+entailment)"


def test_determinism():
    a = _report(seed=42)
    b = _report(seed=42)
    assert (a.b, a.c, a.mcnemar.p_value) == (b.b, b.c, b.mcnemar.p_value)
    assert a.ai.useful_yield == b.ai.useful_yield


def test_honest_null_when_arms_are_equal():
    # If we hand the reporter two identical arms, it must NOT claim a win.
    r = baseline.beat_baseline(seed=42)
    equal = baseline.summarize_pairs([(1, 1)] * 20 + [(0, 0)] * 5,
                                     ai_metrics=r.ai, baseline_metrics=r.ai)
    assert equal.mcnemar.favored == "tie"
    assert equal.mcnemar.p_value == 1.0
    assert equal.ai_beats_baseline is False
