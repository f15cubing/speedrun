# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the deterministic lexical RAG retriever."""

import retriever
import stub_model


def test_retrieves_power_rule_for_derivative_query():
    hits = retriever.retrieve("power rule derivative of x raised to the power n", k=3)
    assert hits, "expected at least one hit"
    top_passage, top_score = hits[0]
    assert top_passage.id == "svc-03-power-rule"
    assert top_score > 0


def test_retrieves_integral_passage_for_integral_query():
    hits = retriever.retrieve("indefinite integral constant of integration plus C", k=3)
    top_ids = [p.id for p, _ in hits]
    assert any(pid.startswith("svc-09") or pid.startswith("svc-10") for pid in top_ids)


def test_topk_sorted_and_bounded():
    hits = retriever.retrieve("derivative", k=3)
    assert len(hits) <= 3
    scores = [s for _, s in hits]
    assert scores == sorted(scores, reverse=True)


def test_deterministic_across_calls():
    a = [(p.id, round(s, 6)) for p, s in retriever.retrieve("chain rule composition", k=5)]
    b = [(p.id, round(s, 6)) for p, s in retriever.retrieve("chain rule composition", k=5)]
    assert a == b


def test_empty_query_returns_nothing():
    assert retriever.retrieve("", k=3) == []


def test_out_of_vocabulary_query_returns_no_positive_hits():
    hits = retriever.retrieve("zzzz qwerty nonsense token", k=3)
    assert all(score == 0 for _, score in hits) or hits == []


def test_diff_query_does_not_rank_integral_ahead_of_derivative():
    # The disambiguated diff query must not let the integral-of-a-power passage
    # outrank the derivative power-rule passage (the "integral confused with a
    # differential" cross-ranking).
    hits = retriever.retrieve(stub_model.OP_QUERY["diff"], k=5)
    ids = [p.id for p, _ in hits]
    assert ids[0] == "svc-03-power-rule"
    if "svc-10-integral-of-a-power" in ids:
        assert ids.index("svc-03-power-rule") < ids.index("svc-10-integral-of-a-power")


def test_antideriv_query_top_is_not_the_derivative_power_rule():
    # The disambiguated antiderivative query must ground in an integral/antiderivative
    # passage, never the derivative power-rule passage.
    hits = retriever.retrieve(stub_model.OP_QUERY["antideriv"], k=3)
    top_id = hits[0][0].id
    assert top_id != "svc-03-power-rule"
    assert top_id.startswith(("svc-09", "svc-10", "svc-11"))
