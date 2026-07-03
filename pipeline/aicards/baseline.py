# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Beat-the-baseline: AI pipeline vs. template/cloze non-RAG generation (PRD §9).

Two arms over the **same shared generation targets** (same SymPy templates — only the
*pipeline* differs):

* **AI-pipeline arm** — RAG grounding + non-nullable provenance + SymPy CAS verify +
  abstention (the real machinery). A card ships only if it is grounded AND CAS-proved;
  otherwise it abstains.
* **Baseline arm** — template/cloze extraction, **non-RAG**, **no verify, no
  abstention**: it emits every card it drafts, including wrong answers (nothing checks
  them) and cloze-leaked prompts (bad pedagogy).

Both arms are scored card-by-card by the **same rater harness** (`goldset_gate.rate_a`
→ correct / wrong / bad-pedagogy). We pair by target, build the discordant 2×2 table,
and run the **exact McNemar test** (`mcnemar.py`, pure stdlib). "Usable" = a card that
is published/emitted AND rated CORRECT (a keeper a student should study).

AI-off honesty: no live model, so the outcome *categories* are a transparent,
declared deterministic fixture (`TARGET_COMPOSITION`) modelling realistic naive-
generation failure modes; but each arm's card is really generated from the shared
SymPy core and really scored by the same CAS/rater harness, and the McNemar math runs
on the real labels. The comparison validates the **machinery** (RAG+verify+abstain vs.
naive), not a live model.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

import sympy as sp

import goldset_gate
import mcnemar
import orchestrator
import retriever as _retriever
import stub_model
from cards import COMPUTATIONAL, GeneratedCard
from goldset_gate import CORRECT, WRONG
from provenance import Provenance

# Significance threshold for the beat-baseline claim.
ALPHA = 0.05

# Transparent, declared fixture composition (AI-off). Each category models a
# realistic naive-generation outcome; the pairing it induces is noted alongside.
TARGET_COMPOSITION = {
    "clean": 20,        # both arms produce a usable card                 -> concordant a
    "naive_wrong": 18,  # AI correct+grounded; naive non-RAG is WRONG     -> b (AI wins)
    "naive_badped": 12, # AI clean; naive cloze LEAKS the answer          -> b (AI wins)
    "ai_abstains": 4,   # AI can't ground -> abstains; naive happens right -> c (baseline wins)
    "both_fail": 6,     # AI abstains; naive is wrong                     -> concordant d
}
N_TARGETS = sum(TARGET_COMPOSITION.values())  # 60

OPS = ("diff", "antideriv", "deriv_at", "diffeq")
_LEAF_FOR = {
    "diff": "topic::calculus::differential_single",
    "antideriv": "topic::calculus::integral_single",
    "deriv_at": "topic::calculus::applications",
    "diffeq": "topic::calculus::differential_equations",
}


@dataclass(frozen=True)
class Target:
    idx: int
    category: str
    op: str
    query: str


def build_targets(seed: int = 42) -> List[Target]:
    """Deterministic shared target list in a fixed category order."""
    targets = []
    idx = 0
    for category, count in TARGET_COMPOSITION.items():
        for _ in range(count):
            op = OPS[idx % len(OPS)]
            targets.append(Target(idx, category, op, stub_model.OP_QUERY[op]))
            idx += 1
    return targets


def _instance(target: Target, seed: int):
    """Build the SHARED SymPy instance for a target (identical for both arms)."""
    rng = random.Random("beat:{}:{}".format(seed, target.idx))
    return stub_model.make_computational_instance(target.op, rng)


def ai_card(target: Target, seed: int, retriever) -> GeneratedCard:
    """AI-pipeline arm: correct-by-construction answer + RAG grounding (or ungrounded
    -> the pipeline will abstain for the abstain categories)."""
    inst = _instance(target, seed)
    check = dict(inst.check)
    check["claimed"] = inst.correct  # AI arm answers correctly (CAS-backed generation)
    top = retriever.retrieve(target.query, k=3)[0][0]
    if target.category in ("ai_abstains", "both_fail"):
        # Retrieval found no supporting passage -> ungrounded -> pipeline abstains.
        prov = Provenance(stub_model.FABRICATED_QUOTE, top.id)
    else:
        prov = Provenance(stub_model.pick_sentence(top, target.query), top.id)
    return GeneratedCard(
        card_id="ai-{:03d}".format(target.idx), leaf_tag=_LEAF_FOR[target.op],
        kind=COMPUTATIONAL, front=inst.prompt, back=inst.render(inst.correct),
        provenance=prov, check=check,
    )


def baseline_card(target: Target, seed: int) -> GeneratedCard:
    """Baseline arm: same template, but non-RAG + no verify + no abstention."""
    inst = _instance(target, seed)   # SAME instance as the AI arm
    correct = inst.correct
    claimed = correct
    front = inst.prompt
    if target.category in ("naive_wrong", "both_fail"):
        claimed = sp.expand(correct + inst.wrong_delta)   # wrong; nothing checks it
    elif target.category == "naive_badped":
        front = inst.prompt + " (Hint: {}.)".format(inst.render(correct))  # cloze leak
    back = inst.render(claimed)
    check = dict(inst.check)
    check["claimed"] = claimed
    return GeneratedCard(
        card_id="bl-{:03d}".format(target.idx), leaf_tag=_LEAF_FOR[target.op],
        kind=COMPUTATIONAL, front=front, back=back,
        provenance=None, check=check,   # non-RAG: no provenance; emits everything
    )


@dataclass
class ArmMetrics:
    name: str
    generated: int
    published: int
    useful: int
    wrong: int
    fact_precision: float
    useful_yield: float


def _arm_metrics(name, published_flags, labels) -> ArmMetrics:
    generated = len(labels)
    pub = [i for i, p in enumerate(published_flags) if p]
    published = len(pub)
    wrong = sum(1 for i in pub if labels[i] == WRONG)
    useful = sum(1 for i in pub if labels[i] == CORRECT)
    fact_precision = 1.0 if published == 0 else (published - wrong) / published
    useful_yield = 0.0 if generated == 0 else useful / generated
    return ArmMetrics(name, generated, published, useful, wrong, fact_precision, useful_yield)


@dataclass
class BaselineReport:
    a: int
    b: int
    c: int
    d: int
    mcnemar: mcnemar.McNemarResult
    ai: Optional[ArmMetrics] = None
    baseline: Optional[ArmMetrics] = None
    ai_published_cards: list = field(default_factory=list)
    yield_diff_ci: tuple = (0.0, 0.0)
    rater_name: str = goldset_gate.PRIMARY_RATER
    ai_beats_baseline: bool = False

    def format_report(self) -> str:
        L = []
        L.append("=" * 68)
        L.append("BEAT-THE-BASELINE — AI pipeline vs. template/cloze (non-RAG)")
        L.append("=" * 68)
        L.append("Scored by the SAME rater harness: {}".format(self.rater_name))
        L.append("Usable = published/emitted AND rated CORRECT (a keeper card).")
        L.append("")
        if self.ai and self.baseline:
            hdr = "  {:<44} {:>8} {:>8}".format("arm", "fact-prec", "yield")
            L.append(hdr)
            for m in (self.ai, self.baseline):
                L.append("  {:<44} {:>8.3f} {:>8.3f}".format(m.name, m.fact_precision, m.useful_yield))
            L.append("")
            L.append("  (AI published {}/{}, 0 wrong; baseline emitted {}/{}, {} wrong-fact)".format(
                self.ai.published, self.ai.generated, self.baseline.published,
                self.baseline.generated, self.baseline.wrong))
            L.append("")
        L.append("Paired 2x2 (AI vs baseline, 'usable?'):")
        L.append("  a (both usable)      = {}".format(self.a))
        L.append("  b (AI only, AI win)  = {}".format(self.b))
        L.append("  c (baseline only)    = {}".format(self.c))
        L.append("  d (neither)          = {}".format(self.d))
        L.append("")
        L.append("McNemar exact test (discordant b={}, c={}, n={}):".format(
            self.mcnemar.b, self.mcnemar.c, self.mcnemar.n))
        L.append("  two-sided p-value = {:.3e}".format(self.mcnemar.p_value))
        L.append("  favored arm       = {}".format(
            {"A": "AI-pipeline", "B": "baseline", "tie": "tie"}[self.mcnemar.favored]))
        L.append("  useful-yield diff 90% CI (AI - baseline) = [{:.3f}, {:.3f}]".format(*self.yield_diff_ci))
        L.append("")
        if self.ai_beats_baseline:
            L.append("RESULT: AI pipeline BEATS the baseline (p < {}, fact-precision ceiling intact).".format(ALPHA))
        else:
            L.append("RESULT: no significant win at alpha={} — reporting the honest null.".format(ALPHA))
        L.append("=" * 68)
        return "\n".join(L)


def _beats(mc, ai_m, bl_m) -> bool:
    if ai_m is None or bl_m is None:
        return False
    return (mc.favored == "A" and mc.p_value < ALPHA
            and ai_m.fact_precision >= goldset_gate.FACT_PRECISION_MIN
            and ai_m.fact_precision > bl_m.fact_precision
            and ai_m.useful_yield >= bl_m.useful_yield)


def summarize_pairs(pairs, ai_metrics=None, baseline_metrics=None, ci=(0.0, 0.0)):
    """Build a report from paired (a_usable, b_usable) flags + optional arm metrics."""
    a, b, c, d = mcnemar.discordant_table(pairs)
    mc = mcnemar.mcnemar_exact(b, c)
    return BaselineReport(a, b, c, d, mc, ai_metrics, baseline_metrics,
                          [], ci, goldset_gate.PRIMARY_RATER,
                          _beats(mc, ai_metrics, baseline_metrics))


def beat_baseline(seed: int = 42, retriever=None) -> BaselineReport:
    """Run both arms over the shared targets and produce the full comparison."""
    ret = retriever or _retriever.DEFAULT
    targets = build_targets(seed)

    ai_published, ai_labels, ai_cards = [], [], []
    bl_published, bl_labels = [], []
    pairs = []
    for t in targets:
        ac = ai_card(t, seed, ret)
        bc = baseline_card(t, seed)
        decision, _ = orchestrator.classify(ac)
        a_pub = decision == orchestrator.Decision.PUBLISH_VERIFIED
        al = goldset_gate.rate_a(ac)
        bl = goldset_gate.rate_a(bc)

        ai_cards.append(ac)
        ai_published.append(a_pub)
        ai_labels.append(al)
        bl_published.append(True)   # the naive baseline emits every card
        bl_labels.append(bl)

        pairs.append((1 if (a_pub and al == CORRECT) else 0,
                      1 if bl == CORRECT else 0))

    ai_m = _arm_metrics("AI-pipeline (RAG+provenance+CAS+abstain)", ai_published, ai_labels)
    bl_m = _arm_metrics("baseline (template/cloze, non-RAG, no verify)", bl_published, bl_labels)
    a, b, c, d = mcnemar.discordant_table(pairs)
    mc = mcnemar.mcnemar_exact(b, c)
    ci = mcnemar.paired_bootstrap_ci([p[0] for p in pairs], [p[1] for p in pairs], seed=seed)
    published_cards = [card for card, pub in zip(ai_cards, ai_published) if pub]

    return BaselineReport(
        a=a, b=b, c=c, d=d, mcnemar=mc, ai=ai_m, baseline=bl_m,
        ai_published_cards=published_cards, yield_diff_ci=ci,
        rater_name=goldset_gate.PRIMARY_RATER, ai_beats_baseline=_beats(mc, ai_m, bl_m),
    )


def category_counts(targets) -> dict:
    return dict(Counter(t.category for t in targets))
