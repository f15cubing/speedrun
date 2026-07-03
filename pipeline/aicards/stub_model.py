# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""A deterministic, transparent **stub** generator standing in for a live LLM.

No API key is available in this environment (AI-off; see aicards.md), so the
pipeline's real machinery — retrieval, provenance enforcement, abstention, CAS /
NLI verification, and the gold-set gate — is exercised by this fixed fixture
instead of a model. The stub is:

* **RAG-grounded:** for grounded cards it lifts its provenance quote *verbatim*
  from the passage the retriever returns for the card's query (retrieval -> quote),
  so the provenance path is genuinely exercised end-to-end.
* **Transparent:** the exact composition (how many good / wrong / ungrounded /
  bad-pedagogy / conceptual cards) is declared in :data:`COMPOSITION`, so the gate
  numbers are honestly attributable to a fixture, not a black box.
* **Adversarial on purpose:** it deliberately emits wrong-answer, hallucinated-quote,
  answer-leaking, and un-entailed cards so the abstention / CAS / entailment gates
  have something real to catch.

A live-model backend implements the same tiny interface (:meth:`plan` + :meth:`build`)
and plugs in unchanged; see ``orchestrator.py`` (:class:`LlmBackend`).
"""

from __future__ import annotations

import random
import re
from collections import namedtuple

import sympy as sp

import corpus
import retriever as _retriever
from cards import COMPUTATIONAL, CONCEPTUAL, GeneratedCard
from provenance import Provenance

x = sp.Symbol("x")

# --- transparent composition of the 50-card fixture ------------------------- #
# Computational cards, by outcome the pipeline SHOULD produce:
GOOD_COMP = 32          # grounded, correct, good pedagogy   -> publish (verified)
WRONG_COMP = 4          # grounded, WRONG answer             -> CAS drops (abstain)
UNGROUNDED_COMP = 3     # correct answer, HALLUCINATED quote -> provenance drops
BAD_PED_COMP = 3        # grounded, correct, answer LEAKED   -> publishes; raters flag
# Conceptual cards (never auto-verified; only human-review-eligible when entailed):
GOOD_CONCEPT = 5        # grounded, entailed claim           -> draft for human review
BORDERLINE_CONCEPT = 1  # entailment ~0.67 (between raters)  -> pipeline (0.70) abstains
UNENTAILED_CONCEPT = 2  # claim not supported by quote       -> entailment drops

COMPOSITION = {
    "good_computational": GOOD_COMP,
    "wrong_computational": WRONG_COMP,
    "ungrounded_computational": UNGROUNDED_COMP,
    "bad_pedagogy_computational": BAD_PED_COMP,
    "good_conceptual": GOOD_CONCEPT,
    "borderline_conceptual": BORDERLINE_CONCEPT,
    "unentailed_conceptual": UNENTAILED_CONCEPT,
}
TOTAL = sum(COMPOSITION.values())  # 50

# Spread the good computational cards across calculus-heavy leaves (mirrors the
# gold-set's ~76% calculus weight without ever reading the gold-set).
_COMP_LEAVES = (
    [("differential_single", "diff")] * 10
    + [("integral_single", "antideriv")] * 8
    + [("applications", "deriv_at")] * 9
    + [("differential_equations", "diffeq")] * 5
)  # == 32

OP_QUERY = {
    "diff": "differentiate derivative power rule x raised to the power n",
    "antideriv": "indefinite integral antiderivative power rule constant of integration",
    "deriv_at": "slope of the tangent line derivative evaluated at a point",
    "diffeq": "antiderivative indefinite integral constant of integration solve",
}

Request = namedtuple("Request", ["idx", "leaf_tag", "kind", "op", "variant", "query", "payload"])

# A plausible-sounding but ungrounded "quote" — not present verbatim in any source
# passage, so provenance.check drops any card that carries it (models a hallucinated
# citation / a fact the retriever could not ground).
FABRICATED_QUOTE = "The answer follows immediately from the usual rules, as is well known."
_FABRICATED_QUOTE = FABRICATED_QUOTE  # backwards-compatible alias

# The shared computational generation core (used by BOTH the AI-pipeline arm and the
# beat-baseline arm — only the *pipeline* around it differs).
CompInstance = namedtuple("CompInstance", ["prompt", "correct", "check", "render", "wrong_delta"])

_SENT_SPLIT = re.compile(r"(?<=\.)\s+")


def _leaf_tag(leaf):
    return "topic::calculus::{}".format(leaf) if leaf in (
        "differential_single", "integral_single", "applications", "differential_equations",
    ) else leaf


def _rng(seed, idx):
    return random.Random("{}:{}".format(seed, idx))


def _poly(rng, min_deg=2, max_deg=3, lo=-4, hi=4):
    deg = rng.randint(min_deg, max_deg)
    expr = sp.Integer(0)
    for power in range(deg, -1, -1):
        c = rng.randint(lo, hi)
        if power == deg and c == 0:
            c = rng.choice([-2, 2, 3])
        expr += c * x ** power
    return sp.expand(expr)


def make_computational_instance(op, rng):
    """The shared computational generation core: return a :class:`CompInstance`.

    SymPy builds both the problem and the correct answer (correct-by-construction).
    This is the SAME core used by the AI-pipeline arm and the beat-baseline arm — so
    the beat-baseline comparison isolates the *pipeline* (RAG + provenance + CAS +
    abstention) from the generation templates, which are identical.
    """
    if op == "diff":
        f = _poly(rng, 2, 3)
        return CompInstance(
            "Differentiate with respect to x: f(x) = {}.".format(sp.sstr(f)),
            sp.diff(f, x), {"op": "diff", "f": f, "var": x},
            lambda a: "f'(x) = {}".format(sp.sstr(a)), sp.Integer(1))
    if op == "antideriv":
        f = _poly(rng, 1, 3)
        return CompInstance(
            "Find an antiderivative (indefinite integral) of f(x) = {}.".format(sp.sstr(f)),
            sp.integrate(f, x), {"op": "antideriv", "f": f, "var": x},
            lambda a: "F(x) = {} + C".format(sp.sstr(a)), x)  # non-constant delta breaks equivalence
    if op == "deriv_at":
        f = _poly(rng, 2, 3)
        at = rng.randint(-3, 3)
        return CompInstance(
            "Find the slope of the tangent line to f(x) = {} at x = {}.".format(sp.sstr(f), at),
            sp.diff(f, x).subs(x, at), {"op": "deriv_at", "f": f, "var": x, "at": at},
            lambda a: "slope = {}".format(sp.sstr(a)), sp.Integer(1))
    if op == "diffeq":
        f = _poly(rng, 1, 2)
        return CompInstance(
            "Solve the differential equation y'(x) = {} for the general solution y(x).".format(sp.sstr(f)),
            sp.integrate(f, x), {"op": "antideriv", "f": f, "var": x},
            lambda a: "y(x) = {} + C".format(sp.sstr(a)), x)
    raise ValueError("unknown computational op {!r}".format(op))


def _sentences(passage_text):
    return _SENT_SPLIT.split(corpus.normalize_ws(passage_text))


def pick_sentence(passage, query):
    """Return the passage sentence most lexically relevant to ``query`` (verbatim)."""
    q = set(_retriever.tokenize(query))
    best, best_score = None, -1
    for sent in _sentences(passage.text):
        score = sum(1 for t in _retriever.tokenize(sent) if t in q)
        if score > best_score:
            best, best_score = sent, score
    return best


# --- conceptual claim construction ------------------------------------------ #
def _entailed_claim(passage, query, n_tokens=8):
    """A short claim clearly entailed by the picked sentence.

    The claim is built purely from the quote's own content tokens, so every claim
    token is a guaranteed hit -> entailment score 1.0 (well above both raters'
    thresholds). It reads as a faithful extraction, which is exactly what a
    grounded conceptual card should be.
    """
    sent = pick_sentence(passage, query)
    toks = _retriever.tokenize(sent)[:n_tokens]
    claim = " ".join(toks)
    return sent, claim[:1].upper() + claim[1:] + "."


def borderline_claim(passage, query, n_keep=12, n_novel=6):
    """A claim with entailment fraction n_keep/(n_keep+n_novel) ~ 0.67.

    Built FROM the tokenizer's output so the fraction is robust to tokenization:
    n_keep tokens are copied from the quote (guaranteed hits) and n_novel fresh
    tokens are appended (guaranteed misses).
    """
    sent = pick_sentence(passage, query)
    uniq = []
    seen = set()
    for t in _retriever.tokenize(sent):
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    keep = uniq[:n_keep]
    novel = ["moreover", "consequently", "heuristically", "approximately",
             "typically", "generally", "presumably", "arguably"][:n_novel]
    return sent, " ".join(keep + novel) + "."


class StubBackend:
    """Deterministic stand-in for a live model (implements plan + build)."""

    name = "deterministic-stub (AI-off / no live model)"

    def __init__(self, seed=42, retriever=None):
        self.seed = seed
        self.retriever = retriever or _retriever.DEFAULT

    def plan(self):
        """The fixed generation plan: TOTAL requests in a deterministic order."""
        reqs = []
        idx = 0

        def add(leaf, kind, op, variant, query, payload=None):
            nonlocal idx
            reqs.append(Request(idx, _leaf_tag(leaf), kind, op, variant, query, payload or {}))
            idx += 1

        # good computational, spread across leaves
        for leaf, op in _COMP_LEAVES:
            add(leaf, COMPUTATIONAL, op, "good", OP_QUERY[op])
        # wrong computational
        for leaf, op in [("differential_single", "diff"), ("integral_single", "antideriv"),
                         ("applications", "deriv_at"), ("differential_equations", "diffeq")]:
            add(leaf, COMPUTATIONAL, op, "wrong", OP_QUERY[op])
        # ungrounded (hallucinated quote) but correct answer
        for leaf, op in [("differential_single", "diff"), ("integral_single", "antideriv"),
                         ("applications", "deriv_at")]:
            add(leaf, COMPUTATIONAL, op, "ungrounded", OP_QUERY[op])
        # bad-pedagogy (answer leaked into the prompt), correct + grounded
        for leaf, op in [("differential_single", "diff"), ("integral_single", "antideriv"),
                         ("applications", "deriv_at")]:
            add(leaf, COMPUTATIONAL, op, "bad_ped", OP_QUERY[op])
        # good conceptual (grounded + entailed)
        concept_specs = [
            ("topic::additional::real_analysis", "harmonic series diverges reciprocals positive integers"),
            ("topic::additional::real_analysis", "cauchy sequence real numbers converges prescribed distance"),
            ("topic::additional::real_analysis", "geometric series common ratio converges absolute value less than one"),
            ("topic::calculus::differential_single", "differentiable at a point is also continuous"),
            ("topic::additional::real_analysis", "sequence converges limit terms arbitrarily close"),
        ]
        for leaf, query in concept_specs:
            add(leaf, CONCEPTUAL, "concept", "good", query)
        # borderline conceptual (entailment between the two raters' thresholds)
        add("topic::additional::real_analysis", CONCEPTUAL, "concept", "borderline",
            "geometric series common ratio converges absolute value less than one")
        # unentailed conceptual (claim not supported by its quote)
        add("topic::additional::real_analysis", CONCEPTUAL, "concept", "unentailed",
            "cosine sine derivative elementary functions",
            payload={"claim": "Matrix multiplication is generally not commutative for square matrices."})
        add("topic::additional::real_analysis", CONCEPTUAL, "concept", "unentailed",
            "definite integral fundamental theorem antiderivative",
            payload={"claim": "The set of prime numbers is infinite by Euclid's classic argument."})
        return reqs

    # -- generation ---------------------------------------------------------- #
    def build(self, request, retrieved):
        top = retrieved[0][0] if retrieved else None
        if request.kind == COMPUTATIONAL:
            return self._build_computational(request, top)
        return self._build_conceptual(request, top)

    def _build_computational(self, request, top_passage):
        rng = _rng(self.seed, request.idx)
        inst = make_computational_instance(request.op, rng)
        correct = inst.correct

        claimed = correct
        front = inst.prompt
        if request.variant == "wrong":
            claimed = sp.expand(correct + inst.wrong_delta)
        elif request.variant == "bad_ped":
            # Leak the fully-rendered answer into the prompt. The answer carries a
            # distinctive prefix ("f'(x) =", "slope =", ...) that never appears in a
            # well-posed prompt, so "answer text appears in the prompt" is a robust,
            # false-positive-free pedagogy signal.
            front = inst.prompt + " (Hint: {}.)".format(inst.render(correct))

        back = inst.render(claimed)
        check = dict(inst.check)
        check["claimed"] = claimed

        if request.variant == "ungrounded":
            prov = Provenance(quote=_FABRICATED_QUOTE, anchor=top_passage.id if top_passage else "svc-03-power-rule")
        else:
            quote = pick_sentence(top_passage, request.query)
            prov = Provenance(quote=quote, anchor=top_passage.id)

        return GeneratedCard(
            card_id="ai-{:03d}".format(request.idx),
            leaf_tag=request.leaf_tag, kind=COMPUTATIONAL,
            front=front, back=back, provenance=prov, check=check,
        )

    def _build_conceptual(self, request, top_passage):
        if request.variant == "good":
            quote, claim = _entailed_claim(top_passage, request.query)
            front = "State the fact this source supports."
        elif request.variant == "borderline":
            quote, claim = borderline_claim(top_passage, request.query)
            front = "State the related fact."
        else:  # unentailed
            quote = pick_sentence(top_passage, request.query)
            claim = request.payload["claim"]
            front = "State a fact about this topic."

        prov = Provenance(quote=quote, anchor=top_passage.id)
        return GeneratedCard(
            card_id="ai-{:03d}".format(request.idx),
            leaf_tag=request.leaf_tag, kind=CONCEPTUAL,
            front=front, back=claim, provenance=prov, check=None,
        )
