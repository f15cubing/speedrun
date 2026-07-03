# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""The gold-set gate (PRD §9): score generated cards and apply the pre-set cutoff.

**Cutoffs are lodged in code BEFORE any scoring runs** (:data:`FACT_PRECISION_MIN`,
:data:`USEFUL_YIELD_MIN`) — the asymmetric, safety-first gate from PRD §9: a wrong
fact is far worse than a missing card, so precision is near-perfect while yield is
allowed to be modest.

Two independent raters score every generated card ``CORRECT`` / ``WRONG`` /
``BAD_PEDAGOGY``:

* **Rater A** ("cas+entailment", the primary): SymPy re-derivation for computational
  cards; NLI-proxy entailment (threshold 0.70) for conceptual cards.
* **Rater B** ("numeric+entailment", the reliability check): an independent numeric
  probe for computational cards; NLI-proxy at a *different* threshold (0.60) for
  conceptual cards.

Rater B is a **deterministic second-rater proxy, NOT a human** — labelled honestly.
It exists to (a) give an independent audit of Rater A's fact calls and (b) produce a
real inter-rater reliability number (Cohen's kappa + percent agreement). A live run
would replace both with >=2 human raters; the harness (metrics + kappa) is unchanged.

Metric definitions (also lodged before scoring):
* **fact-precision** = fraction of the pipeline's *published* (verified) cards that
  the primary rater judges factually correct (i.e. not ``WRONG``). Gate: >= 0.98.
* **useful-yield** = published-and-``CORRECT`` cards / total candidates generated.
  Gate: >= 0.60. (Also reported over non-abstained cards, PRD's phrasing.)

Conceptual cards are emitted only as human-review drafts and are **excluded from the
verified counts** (they never auto-inflate precision or coverage — PRD §9).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import corpus
import verify
from cards import COMPUTATIONAL
from orchestrator import ABSTENTIONS, Decision

# --- LODGED BEFORE SCORING (pre-registered gate, PRD §9) --------------------- #
GATE_LODGED_ON = "2026-07-03"
FACT_PRECISION_MIN = 0.98   # <= 1 wrong-fact card per 50 published
USEFUL_YIELD_MIN = 0.60     # >= 60% of generated candidates are usable
PRIMARY_RATER = "A (cas+entailment)"
RATER_B_ENTAILMENT_THRESHOLD = 0.60  # Rater A uses verify.ENTAILMENT_THRESHOLD (0.70)

# Rater labels.
CORRECT = "correct"
WRONG = "wrong"
BAD_PEDAGOGY = "bad_pedagogy"
LABELS = (CORRECT, WRONG, BAD_PEDAGOGY)


# --------------------------------------------------------------------------- #
# Raters
# --------------------------------------------------------------------------- #
def _answer_leaked(card) -> bool:
    """Pedagogy red flag: the rendered answer appears inside the prompt."""
    back = corpus.normalize_ws(card.back or "")
    front = corpus.normalize_ws(card.front or "")
    return bool(back) and back in front


def rate_a(card) -> str:
    """Primary rater: SymPy CAS (computational) / entailment @0.70 (conceptual)."""
    if card.kind == COMPUTATIONAL:
        if card.check is None:
            return WRONG
        if not verify.verify_computational(card.check, card.check["claimed"]).ok:
            return WRONG
        return BAD_PEDAGOGY if _answer_leaked(card) else CORRECT
    quote = card.provenance.quote if card.provenance else ""
    if not verify.entails(card.back, quote, verify.ENTAILMENT_THRESHOLD):
        return WRONG
    return BAD_PEDAGOGY if _answer_leaked(card) else CORRECT


def rate_b(card) -> str:
    """Reliability rater (deterministic proxy, not human): numeric probe / entail @0.60."""
    if card.kind == COMPUTATIONAL:
        if card.check is None:
            return WRONG
        if not verify.numeric_check(card.check, card.check["claimed"]).ok:
            return WRONG
        return BAD_PEDAGOGY if _answer_leaked(card) else CORRECT
    quote = card.provenance.quote if card.provenance else ""
    if verify.entailment_score(card.back, quote) < RATER_B_ENTAILMENT_THRESHOLD:
        return WRONG
    return BAD_PEDAGOGY if _answer_leaked(card) else CORRECT


# --------------------------------------------------------------------------- #
# Inter-rater reliability
# --------------------------------------------------------------------------- #
def percent_agreement(labels_a, labels_b) -> float:
    if not labels_a:
        return 100.0
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    return 100.0 * agree / len(labels_a)


def cohens_kappa(labels_a, labels_b) -> float:
    """Cohen's kappa for two raters over a shared item list."""
    n = len(labels_a)
    if n == 0:
        return 1.0
    po = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    ca, cb = Counter(labels_a), Counter(labels_b)
    cats = set(ca) | set(cb)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


# --------------------------------------------------------------------------- #
# Gate result
# --------------------------------------------------------------------------- #
@dataclass
class GateResult:
    generated: int
    published: int
    human_review_drafts: int
    abstained: int
    decision_counts: dict
    label_counts_a: dict
    label_counts_b: dict
    cohens_kappa: float
    percent_agreement: float
    fact_precision: float
    fact_precision_secondary: float
    useful_yield: float
    useful_yield_nonabstained: float
    safety_recall: float
    passed: bool
    cutoffs: dict = field(default_factory=dict)

    def as_dict(self):
        d = dict(self.__dict__)
        d["decision_counts"] = {k.value if isinstance(k, Decision) else str(k): v
                                for k, v in self.decision_counts.items()}
        return d

    def format_report(self) -> str:
        lines = []
        lines.append("=" * 68)
        lines.append("AI CARD PIPELINE — GOLD-SET GATE REPORT")
        lines.append("=" * 68)
        lines.append("Cutoffs LODGED {} (before scoring):".format(GATE_LODGED_ON))
        lines.append("  fact-precision >= {:.2f}   AND   useful-yield >= {:.2f}".format(
            FACT_PRECISION_MIN, USEFUL_YIELD_MIN))
        lines.append("  primary rater: {}".format(PRIMARY_RATER))
        lines.append("")
        lines.append("Generation (deterministic stub — AI-off, no live model):")
        lines.append("  candidates generated : {}".format(self.generated))
        for dec in Decision:
            lines.append("    {:<24} {}".format(dec.value, self.decision_counts.get(dec, 0)))
        lines.append("")
        lines.append("  published (verified, computational) : {}".format(self.published))
        lines.append("  conceptual human-review drafts      : {}".format(self.human_review_drafts))
        lines.append("  abstained (dropped)                 : {}".format(self.abstained))
        lines.append("")
        lines.append("Inter-rater reliability (Rater A vs Rater B, all {} candidates):".format(self.generated))
        lines.append("  Rater A labels: {}".format(self.label_counts_a))
        lines.append("  Rater B labels: {}".format(self.label_counts_b))
        lines.append("  percent agreement : {:.1f}%".format(self.percent_agreement))
        lines.append("  Cohen's kappa     : {:.3f}".format(self.cohens_kappa))
        lines.append("")
        lines.append("Gate metrics (primary rater A over the published set):")
        lines.append("  fact-precision           : {:.4f}   (>= {:.2f}?  {})".format(
            self.fact_precision, FACT_PRECISION_MIN,
            "PASS" if self.fact_precision >= FACT_PRECISION_MIN else "FAIL"))
        lines.append("  fact-precision (rater B) : {:.4f}   (independent numeric audit)".format(
            self.fact_precision_secondary))
        lines.append("  useful-yield             : {:.4f}   (>= {:.2f}?  {})".format(
            self.useful_yield, USEFUL_YIELD_MIN,
            "PASS" if self.useful_yield >= USEFUL_YIELD_MIN else "FAIL"))
        lines.append("  useful-yield (of non-abstained) : {:.4f}".format(self.useful_yield_nonabstained))
        lines.append("  safety recall (wrong comp abstained) : {:.4f}".format(self.safety_recall))
        lines.append("")
        lines.append("GATE: {}".format("PASSED" if self.passed else "FAILED"))
        lines.append("=" * 68)
        return "\n".join(lines)


def run_gate(outcomes) -> GateResult:
    """Score pipeline ``outcomes`` against the lodged cutoffs; return a GateResult."""
    generated = len(outcomes)
    cards = [o.card for o in outcomes]

    labels_a = [rate_a(c) for c in cards]
    labels_b = [rate_b(c) for c in cards]
    label_a_by_id = {o.card.card_id: la for o, la in zip(outcomes, labels_a)}

    published = [o for o in outcomes if o.decision == Decision.PUBLISH_VERIFIED]
    drafts = [o for o in outcomes if o.decision == Decision.DRAFT_HUMAN_REVIEW]
    abst = [o for o in outcomes if o.decision in ABSTENTIONS]

    n_pub = len(published)
    wrong_pub_a = sum(1 for o in published if label_a_by_id[o.card.card_id] == WRONG)
    # Rater B precision (independent audit).
    label_b_by_id = {o.card.card_id: lb for o, lb in zip(outcomes, labels_b)}
    wrong_pub_b = sum(1 for o in published if label_b_by_id[o.card.card_id] == WRONG)

    fact_precision = 1.0 if n_pub == 0 else (n_pub - wrong_pub_a) / n_pub
    fact_precision_b = 1.0 if n_pub == 0 else (n_pub - wrong_pub_b) / n_pub

    useful = sum(1 for o in published if label_a_by_id[o.card.card_id] == CORRECT)
    useful_yield = 0.0 if generated == 0 else useful / generated
    non_abstained = n_pub + len(drafts)
    useful_yield_na = 0.0 if non_abstained == 0 else useful / non_abstained

    # Safety recall: of computational candidates the primary rater calls WRONG,
    # what fraction did the pipeline abstain on?
    wrong_comp = [o for o in outcomes
                  if o.card.kind == COMPUTATIONAL and label_a_by_id[o.card.card_id] == WRONG]
    if wrong_comp:
        recalled = sum(1 for o in wrong_comp if o.decision in ABSTENTIONS)
        safety_recall = recalled / len(wrong_comp)
    else:
        safety_recall = 1.0

    passed = fact_precision >= FACT_PRECISION_MIN and useful_yield >= USEFUL_YIELD_MIN

    return GateResult(
        generated=generated,
        published=n_pub,
        human_review_drafts=len(drafts),
        abstained=len(abst),
        decision_counts=dict(Counter(o.decision for o in outcomes)),
        label_counts_a=dict(Counter(labels_a)),
        label_counts_b=dict(Counter(labels_b)),
        cohens_kappa=cohens_kappa(labels_a, labels_b),
        percent_agreement=percent_agreement(labels_a, labels_b),
        fact_precision=fact_precision,
        fact_precision_secondary=fact_precision_b,
        useful_yield=useful_yield,
        useful_yield_nonabstained=useful_yield_na,
        safety_recall=safety_recall,
        passed=passed,
        cutoffs={
            "fact_precision_min": FACT_PRECISION_MIN,
            "useful_yield_min": USEFUL_YIELD_MIN,
            "lodged_on": GATE_LODGED_ON,
            "primary_rater": PRIMARY_RATER,
        },
    )
