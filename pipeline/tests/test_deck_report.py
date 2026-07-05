"""Tests for the study-deck quality report + integrity gate."""

import sympy as sp

import build_deck
import deck_report
import mathfmt


def _good_mcq(uid="u1"):
    return {
        "uid": uid,
        "leaf_tag": "topic::algebra::linear",
        "format": "mcq",
        "question": "q?",
        "options": ["a", "b", "c", "d", "e"],
        "correct_index": 0,
        "explanation": "because a",
    }


# --- MCQ integrity ---


def test_good_mcq_has_no_issues():
    assert deck_report.audit_mcq(_good_mcq()) == []


def test_audit_catches_duplicate_options():
    c = _good_mcq()
    c["options"] = ["a", "a", "c", "d", "e"]
    assert any("duplicate" in i for i in deck_report.audit_mcq(c))


def test_audit_catches_bad_correct_index():
    c = _good_mcq()
    c["correct_index"] = 9
    assert any("out of range" in i for i in deck_report.audit_mcq(c))


def test_audit_catches_key_mismatch_against_ground_truth():
    c = _good_mcq()
    key = sp.Integer(4)
    c["_correct_expr"] = key
    c["options"] = [mathfmt.expr_inline(key), "b", "c", "d", "e"]  # index 0 matches
    assert deck_report.audit_mcq(c) == []
    c["correct_index"] = 1  # now points at "b", not the rendered key
    assert any("key mismatch" in i for i in deck_report.audit_mcq(c))


def test_required_fields_catches_empties():
    mcq = _good_mcq()
    mcq["explanation"] = "  "
    assert any("empty explanation" in i for i in deck_report.required_fields(mcq))
    flash = {"format": "flashcard", "front": "f", "back": ""}
    assert any("empty back" in i for i in deck_report.required_fields(flash))


# --- summary + gate ---


def test_assert_deck_quality_raises_on_bad_card():
    bad = _good_mcq()
    bad["options"] = ["a", "a", "c", "d", "e"]
    try:
        deck_report.assert_deck_quality([_good_mcq("ok"), bad])
        assert False, "expected AssertionError"
    except AssertionError as exc:
        assert "Deck quality gate FAILED" in str(exc)


def test_summary_is_deterministic():
    cards = [_good_mcq("a"), {"format": "flashcard", "front": "f", "back": "b",
                              "leaf_tag": "topic::calculus::applications"}]
    assert deck_report.summarize_quality(cards) == deck_report.summarize_quality(cards)


# --- the real deck must pass the gate ---


def test_real_deck_passes_quality_gate(all_cards):
    summary = deck_report.assert_deck_quality(all_cards)  # raises if any card is malformed
    assert summary["mcq_integrity_ok"] is True
    assert summary["mcq_total"] > 0
    assert summary["num_failures"] == 0
    # MCQ integrity now spans all 11 computational leaves.
    assert summary["leaves_with_mcq"] >= 11
