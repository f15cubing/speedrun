# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the source-corpus loader (the RAG source chapter)."""

import corpus


# A sentence that appears VERBATIM in the chapter but is line-wrapped in the file,
# so a single-line quote only matches after whitespace normalization.
POWER_RULE = (
    "The power rule states that the derivative of x raised to the power n is n "
    "times x raised to the power n minus one."
)


def test_load_corpus_returns_anchored_passages():
    passages = corpus.load_corpus()
    assert len(passages) >= 10
    ids = [p.id for p in passages]
    assert len(ids) == len(set(ids)), "passage ids must be unique"
    for p in passages:
        assert p.id and p.heading and p.text.strip()


def test_passage_by_id_matches_load():
    passages = corpus.load_corpus()
    by_id = corpus.PASSAGE_BY_ID
    for p in passages:
        assert by_id[p.id].text == p.text


def test_quote_matches_verbatim_across_line_wrapping():
    # The power-rule sentence is wrapped over two lines in the source file; a
    # single-line quote must still be recognised as verbatim (ws-normalised).
    hits = corpus.passages_containing(POWER_RULE)
    assert len(hits) == 1, "power-rule sentence should live in exactly one passage"
    anchor = hits[0].id
    assert corpus.quote_in_passage(anchor, POWER_RULE) is True


def test_quote_not_in_wrong_passage():
    passages = corpus.load_corpus()
    other = [p for p in passages if POWER_RULE.split(".")[0] not in corpus.normalize_ws(p.text)]
    assert other, "expected some passage without the power rule"
    assert corpus.quote_in_passage(other[0].id, POWER_RULE) is False


def test_hallucinated_quote_is_absent():
    fake = "The derivative of x is always seventeen regardless of context."
    assert corpus.passages_containing(fake) == []


def test_unknown_anchor_returns_false():
    assert corpus.quote_in_passage("no-such-anchor", POWER_RULE) is False
