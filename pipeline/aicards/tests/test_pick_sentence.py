# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Operation-aware grounding: pick_sentence must never cross derivative <-> integral.

The derivative power-rule passage (``svc-03-power-rule``) and the integral-of-a-power
passage (``svc-10-integral-of-a-power``) share the generic phrasing
"power rule ... x raised to the power n". The old ``pick_sentence`` scored purely by
query-token overlap with no operation guard, so it could ground a *derivative* card
on the *integration* sentence (and vice-versa) — "an integral confused with a
differential". These tests lock in the operation guard added to ``pick_sentence``.
"""

import pytest

import corpus
import stub_model
from stub_model import pick_sentence

BY = corpus.PASSAGE_BY_ID
DERIV_PASSAGE = BY["svc-03-power-rule"]
INTEGRAL_PASSAGE = BY["svc-10-integral-of-a-power"]

# The operation-correct power-rule sentence in each passage (taken verbatim from the
# corpus so the assertions can't drift from the source text).
DERIV_SENTENCE = stub_model._sentences(DERIV_PASSAGE.text)[0]
INTEGRAL_SENTENCE = stub_model._sentences(INTEGRAL_PASSAGE.text)[0]

# A single adversarial passage that carries BOTH confusable power-rule sentences —
# exactly the situation the retriever can hand to pick_sentence.
CONFUSABLE = corpus.Passage(
    id="test-confusable-power-rule",
    heading="Power rule (both operations)",
    text=DERIV_SENTENCE + " " + INTEGRAL_SENTENCE,
)

DERIVATIVE_OPS = ["diff", "deriv_at"]
INTEGRAL_OPS = ["antideriv", "diffeq"]


def test_sentences_are_the_expected_confusable_pair():
    assert "derivative of x raised to the power n" in DERIV_SENTENCE
    assert "integral of x raised to the power n" in INTEGRAL_SENTENCE
    assert stub_model._sentences(CONFUSABLE.text) == [DERIV_SENTENCE, INTEGRAL_SENTENCE]


@pytest.mark.parametrize("op", DERIVATIVE_OPS)
def test_derivative_op_grounds_on_the_derivative_sentence(op):
    query = stub_model.OP_QUERY[op]
    # On a passage that contains BOTH power-rule sentences, a derivative op returns
    # the derivative sentence, never the integration one.
    assert pick_sentence(CONFUSABLE, query, op=op) == DERIV_SENTENCE
    # And on the real derivative power-rule passage it still returns it.
    assert pick_sentence(DERIV_PASSAGE, query, op=op) == DERIV_SENTENCE


@pytest.mark.parametrize("op", INTEGRAL_OPS)
def test_integral_op_grounds_on_the_integral_sentence(op):
    query = stub_model.OP_QUERY[op]
    # On the confusable passage, an antidifferentiation op returns the integration
    # sentence, never the derivative one.
    assert pick_sentence(CONFUSABLE, query, op=op) == INTEGRAL_SENTENCE
    # And on the real integral-of-a-power passage it still returns it.
    assert pick_sentence(INTEGRAL_PASSAGE, query, op=op) == INTEGRAL_SENTENCE


def test_guard_never_returns_the_opposing_operation_sentence():
    # The exact cross-contamination the old code produced (verified against the old
    # implementation): a diff query picked the integral sentence and an antideriv
    # query picked the derivative sentence. The guard forbids both.
    assert pick_sentence(CONFUSABLE, stub_model.OP_QUERY["diff"], op="diff") != INTEGRAL_SENTENCE
    assert pick_sentence(CONFUSABLE, stub_model.OP_QUERY["deriv_at"], op="deriv_at") != INTEGRAL_SENTENCE
    assert pick_sentence(CONFUSABLE, stub_model.OP_QUERY["antideriv"], op="antideriv") != DERIV_SENTENCE
    assert pick_sentence(CONFUSABLE, stub_model.OP_QUERY["diffeq"], op="diffeq") != DERIV_SENTENCE


def test_backward_compatible_without_op():
    # No op -> original pure query-overlap behavior (deterministic), and passing
    # op=None is identical to omitting it.
    got = pick_sentence(DERIV_PASSAGE, stub_model.OP_QUERY["diff"])
    assert got == pick_sentence(DERIV_PASSAGE, stub_model.OP_QUERY["diff"], op=None)
    assert got == DERIV_SENTENCE


def test_falls_back_when_passage_has_no_discriminating_sentence():
    # A derivative op on a pure-integration passage has no derivative sentence to
    # ground on; rather than crash or return nothing, it falls back to the best
    # overlap sentence, which is still a verbatim sentence from that passage.
    got = pick_sentence(INTEGRAL_PASSAGE, stub_model.OP_QUERY["diff"], op="diff")
    assert got in stub_model._sentences(INTEGRAL_PASSAGE.text)


def test_full_plan_grounds_every_computational_card_on_its_operation():
    # End-to-end: no good/wrong/bad-pedagogy computational card in the fixed plan is
    # grounded on an opposing-operation sentence.
    backend = stub_model.StubBackend()
    integral_markers = ("integral", "integration", "antiderivative", "indefinite")
    for req in backend.plan():
        if req.kind != stub_model.COMPUTATIONAL or req.variant == "ungrounded":
            continue  # ungrounded cards deliberately carry a fabricated quote
        top = backend.retriever.retrieve(req.query, k=3)[0][0]
        quote = pick_sentence(top, req.query, op=req.op).lower()
        is_integral_quote = any(m in quote for m in integral_markers)
        if req.op in ("antideriv", "diffeq"):
            assert is_integral_quote, (req.op, quote)
        else:  # diff / deriv_at
            assert not is_integral_quote, (req.op, quote)
