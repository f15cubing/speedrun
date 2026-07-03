# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""End-to-end tests for the AI card pipeline orchestrator (stub-driven)."""

import pytest

import orchestrator
import provenance
import verify
from cards import COMPUTATIONAL, CONCEPTUAL
from orchestrator import Decision
from stub_model import StubBackend


def _outcomes(seed=42):
    return orchestrator.run_pipeline(StubBackend(seed=seed))


def test_pipeline_processes_every_planned_card():
    outcomes = _outcomes()
    assert len(outcomes) == 50


def test_decision_counts_match_expected_mix():
    outcomes = _outcomes()
    counts = orchestrator.decision_counts(outcomes)
    assert counts[Decision.PUBLISH_VERIFIED] == 35
    assert counts[Decision.DRAFT_HUMAN_REVIEW] == 5
    assert counts[Decision.ABSTAIN_NO_PROVENANCE] == 3
    assert counts[Decision.ABSTAIN_WRONG_FACT] == 4
    assert counts[Decision.ABSTAIN_UNSUPPORTED] == 3


def test_every_published_card_is_grounded_and_cas_verified():
    for o in _outcomes():
        if o.decision == Decision.PUBLISH_VERIFIED:
            assert provenance.is_valid(o.card.provenance)
            assert o.card.kind == COMPUTATIONAL
            v = verify.verify_computational(o.card.check, o.card.check["claimed"])
            assert v.ok, "published card failed independent CAS re-check: {}".format(o.card.card_id)


def test_no_wrong_fact_card_is_ever_published():
    for o in _outcomes():
        if o.card.kind == COMPUTATIONAL and o.card.check is not None:
            v = verify.verify_computational(o.card.check, o.card.check["claimed"])
            if not v.ok:
                assert o.decision == Decision.ABSTAIN_WRONG_FACT


def test_drafts_are_conceptual_and_flagged_for_human_review():
    for o in _outcomes():
        if o.decision == Decision.DRAFT_HUMAN_REVIEW:
            assert o.card.kind == CONCEPTUAL
            assert verify.needs_human_review(o.card) is True
            assert o.card.status == "draft"
            assert "gen::ai" in o.card.anki_tags()


def test_ungrounded_cards_are_abstained_even_when_answer_is_correct():
    # The 3 ungrounded computational cards have CORRECT answers but hallucinated
    # quotes; provenance (not correctness) must be what drops them.
    abstained_no_prov = [o for o in _outcomes()
                         if o.decision == Decision.ABSTAIN_NO_PROVENANCE]
    assert len(abstained_no_prov) == 3
    for o in abstained_no_prov:
        # answer itself is fine ...
        assert verify.verify_computational(o.card.check, o.card.check["claimed"]).ok
        # ... but provenance is not grounded
        assert not provenance.is_valid(o.card.provenance)


def test_determinism_across_runs():
    a = [(o.card.card_id, o.decision) for o in _outcomes(seed=42)]
    b = [(o.card.card_id, o.decision) for o in _outcomes(seed=42)]
    assert a == b


def test_llm_backend_without_key_raises_clear_error(monkeypatch):
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AI_CARDS_LLM_KEY"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(orchestrator.NoLiveModelError):
        orchestrator.LlmBackend().plan()
