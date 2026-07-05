"""Tests for the study-deck <-> eval-bank leakage self-audit (PRD §11)."""

import os
import sys

import leakage_audit as la


def _study_mcq(cid, q, ans, others=("w1", "w2", "w3", "w4")):
    return {
        "uid": cid,
        "format": "mcq",
        "question": q,
        "options": [ans, *others],
        "correct_index": 0,
    }


def _eval_mcq(eid, q, ans, others=("w1", "w2", "w3", "w4")):
    return {"id": eid, "format": "mcq", "question": q, "options": [ans, *others], "correct_index": 0}


# --- helper metrics ---


def test_normalize_and_jaccard():
    assert la.normalize("  Foo   BAR ") == "foo bar"
    assert la.jaccard(set(), set()) == 0.0
    assert la.jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert la.jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_word_ngrams_needs_enough_tokens():
    assert la.word_ngrams("one two three", n=13) == set()  # too short
    long = " ".join("t%d" % i for i in range(15))
    assert len(la.word_ngrams(long, n=13)) == 3  # 15 - 13 + 1


# --- the layers ---


def test_exact_qa_collision_is_leakage():
    study = [_study_mcq("s1", "What is 2+2?", "4")]
    ev = [_eval_mcq("e1", "what is 2+2?", "4")]  # case/space-normalised match
    r = la.scan_leakage(study, ev)
    assert r.exact_qa == ["e1"]
    assert r.residual_leakage_rate == 1.0


def test_stem_only_collision_is_flagged_not_leakage():
    study = [_study_mcq("s1", "Compute the derivative of x^2.", "2x")]
    ev = [_eval_mcq("e1", "Compute the derivative of x^2.", "2*x")]  # same stem, diff answer
    r = la.scan_leakage(study, ev)
    assert r.exact_qa == []            # not counted as leakage
    assert r.stem_only == ["e1"]
    assert r.residual_leakage_rate == 0.0


def test_disjoint_corpora_have_zero_leakage():
    study = [_study_mcq("s1", "Integrate 3x + 4.", "3x^2/2 + 4x")]
    ev = [_eval_mcq("e1", "Name a compact Hausdorff space.", "the unit interval")]
    r = la.scan_leakage(study, ev)
    assert r.residual_leakage_rate == 0.0
    assert r.exact_qa == [] and r.stem_only == [] and r.high_jaccard == []


def test_shared_template_is_high_jaccard_but_not_leakage():
    # Same template, DIFFERENT parameters + answer: expected structural overlap, not leakage.
    study = [_study_mcq("s1", "Give the antiderivative (omit + C): integral of 3x + 4 dx", "3x^2/2 + 4x")]
    ev = [_eval_mcq("e1", "Give the antiderivative (omit + C): integral of 6x + 1 dx", "3x^2 + x")]
    r = la.scan_leakage(study, ev, jaccard_threshold=0.5)
    assert r.residual_leakage_rate == 0.0     # not leakage
    assert r.exact_qa == []
    assert r.max_jaccard > 0.5                # but structurally similar (shared template)
    assert any(h["eval_id"] == "e1" for h in r.high_jaccard)


def test_flashcard_study_cards_are_scanned():
    study = [{"uid": "s1", "format": "flashcard", "front": "Define a limit.", "back": "epsilon-delta"}]
    ev = [_eval_mcq("e1", "define a limit.", "epsilon-delta")]
    r = la.scan_leakage(study, ev)
    assert r.exact_qa == ["e1"]  # front/back normalised match


# --- gate + determinism ---


def test_assert_no_leakage_gate():
    clean = la.scan_leakage([_study_mcq("s1", "q1", "a1")], [_eval_mcq("e1", "q2", "a2")])
    la.assert_no_leakage(clean)  # no raise
    leaky = la.scan_leakage([_study_mcq("s1", "q1", "a1")], [_eval_mcq("e1", "q1", "a1")])
    try:
        la.assert_no_leakage(leaky)
        assert False, "expected AssertionError"
    except AssertionError as exc:
        assert "leakage" in str(exc)


def test_report_is_deterministic():
    study = [_study_mcq("s%d" % i, "q%d" % i, "a%d" % i) for i in range(5)]
    ev = [_eval_mcq("e%d" % i, "q%d" % i, "a%d" % i) for i in range(3)]
    a = la.scan_leakage(study, ev).as_dict()
    b = la.scan_leakage(study, ev).as_dict()
    assert a == b


# --- real corpora: the published residual rate must be zero (read-only) ---


def test_real_deck_has_zero_residual_leakage(all_cards):
    # uses the actual study deck (shared fixture) + frozen eval bank (read-only)
    # and asserts no exact (question, answer) leakage even now that MCQ spans all
    # 11 computational leaves.
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "eval", "bank"))
    )
    from loader import load_eval_items

    eval_items = load_eval_items()
    r = la.scan_leakage(all_cards, eval_items)
    assert r.residual_leakage_rate == 0.0, r.as_dict()
    la.assert_no_leakage(r)
