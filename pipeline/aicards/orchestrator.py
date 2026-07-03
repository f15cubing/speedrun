# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""The AI card pipeline orchestrator (PRD §9).

For every planned card the orchestrator:

1. **retrieves** grounding passages from the source chapter (RAG),
2. asks the backend to **generate** a candidate card from that context,
3. enforces **non-nullable provenance** — a card whose verbatim quote is not found
   in its source anchor is dropped (``ABSTAIN_NO_PROVENANCE``), before any other
   check; abstention lives in *pipeline logic*, not in the prompt,
4. **verifies**: computational cards must pass the **SymPy CAS** re-derivation
   (``ABSTAIN_WRONG_FACT`` otherwise); conceptual cards must pass the **NLI-proxy**
   entailment against their quote (``ABSTAIN_UNSUPPORTED`` otherwise) and, when they
   pass, are emitted only as **human-review drafts** (``DRAFT_HUMAN_REVIEW``) — never
   auto-verified.

The backend is a tiny interface (``plan()`` + ``build()``). :class:`StubBackend`
(deterministic, AI-off) is the default; :class:`LlmBackend` is the live-model seam,
which fails loudly when no API key is present.
"""

from __future__ import annotations

import enum
import os
from collections import Counter, namedtuple

import provenance
import retriever as _retriever
import verify
from cards import COMPUTATIONAL


class Decision(enum.Enum):
    PUBLISH_VERIFIED = "publish_verified"           # computational, CAS-proved
    DRAFT_HUMAN_REVIEW = "draft_human_review"       # conceptual, entailed, awaits human
    ABSTAIN_NO_PROVENANCE = "abstain_no_provenance"  # missing / ungrounded quote
    ABSTAIN_WRONG_FACT = "abstain_wrong_fact"        # CAS says the answer is wrong
    ABSTAIN_UNSUPPORTED = "abstain_unsupported"      # claim not entailed by its quote


ABSTENTIONS = frozenset({
    Decision.ABSTAIN_NO_PROVENANCE,
    Decision.ABSTAIN_WRONG_FACT,
    Decision.ABSTAIN_UNSUPPORTED,
})

Outcome = namedtuple("Outcome", ["card", "decision", "detail", "request"])


def classify(card):
    """Return ``(Decision, detail)`` for a candidate card. Never raises."""
    # 1) Provenance is the first, non-negotiable gate.
    if not provenance.is_valid(card.provenance):
        return Decision.ABSTAIN_NO_PROVENANCE, "provenance missing or not grounded verbatim"

    # 2) Verify by card kind.
    if card.kind == COMPUTATIONAL:
        result = verify.verify_computational(card.check, card.check["claimed"])
        if result.ok:
            return Decision.PUBLISH_VERIFIED, result.detail
        return Decision.ABSTAIN_WRONG_FACT, result.detail

    # conceptual
    if verify.entails(card.back, card.provenance.quote):
        return Decision.DRAFT_HUMAN_REVIEW, "entailed by source; awaiting mandatory human review"
    return Decision.ABSTAIN_UNSUPPORTED, "claim not entailed by its source quote"


def run_pipeline(backend, retriever=None):
    """Run the full pipeline for ``backend``; return an ordered list of Outcomes."""
    ret = retriever or _retriever.DEFAULT
    outcomes = []
    for request in backend.plan():
        retrieved = ret.retrieve(request.query, k=3)
        card = backend.build(request, retrieved)
        decision, detail = classify(card)
        if decision == Decision.PUBLISH_VERIFIED:
            card.status = "verified"
        elif decision == Decision.DRAFT_HUMAN_REVIEW:
            card.status = "draft"
        outcomes.append(Outcome(card=card, decision=decision, detail=detail, request=request))
    return outcomes


def decision_counts(outcomes) -> Counter:
    return Counter(o.decision for o in outcomes)


def published(outcomes):
    """Cards the pipeline would ship as verified (computational, CAS-proved)."""
    return [o for o in outcomes if o.decision == Decision.PUBLISH_VERIFIED]


def human_review_drafts(outcomes):
    return [o for o in outcomes if o.decision == Decision.DRAFT_HUMAN_REVIEW]


def abstained(outcomes):
    return [o for o in outcomes if o.decision in ABSTENTIONS]


# --------------------------------------------------------------------------- #
# Live-model seam (AI-off in this environment)
# --------------------------------------------------------------------------- #
class NoLiveModelError(RuntimeError):
    """Raised when a live-model backend is used but no API key is configured."""


class LlmBackend:
    """Seam for a real LLM. Implements the same ``plan()`` + ``build()`` interface.

    In this environment no API key is present, so it fails loudly rather than
    silently pretending. To go live: set one of ``LLM_KEYS`` and implement the two
    methods to call the model with the retrieved context; **nothing downstream
    changes** — provenance, CAS/NLI verification, and the gold-set gate are all
    model-agnostic.
    """

    LLM_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AI_CARDS_LLM_KEY")

    def __init__(self, model=None):
        self.model = model

    def _api_key(self):
        for var in self.LLM_KEYS:
            if os.environ.get(var):
                return os.environ[var]
        return None

    def _require_key(self):
        if not self._api_key():
            raise NoLiveModelError(
                "no live-model API key found (looked for {}). The pipeline machinery "
                "and the gold-set gate run on the deterministic stub instead — see "
                "pipeline/aicards/aicards.md (AI-off status).".format(", ".join(self.LLM_KEYS))
            )

    def plan(self):
        self._require_key()
        raise NotImplementedError("live-model generation is not wired in this AI-off build")

    def build(self, request, retrieved):
        self._require_key()
        raise NotImplementedError("live-model generation is not wired in this AI-off build")
