# Critique 07 — AI card generation & safety

**Verdict: strong and well-evidenced.** The central architecture is right: **provenance enforced by schema** (not trust), **CAS/tool verification as the decisive trust anchor** for computational cards, **model self-critics demoted to advisory** (they demonstrably rubber-stamp and even introduce errors), and an **asymmetric strict gate** that accepts low yield as the correct safe tradeoff.

## What is genuinely useful (carry into synthesis) — [strong] unless noted
- **CAS (SymPy/PAL) is decisively better than model-based checking** for arithmetic/algebra because it is deterministic. Backed by PAL (Gao et al., 61.2% vs 23.3% GSM-Hard), Lightman et al. 2023 (process > outcome supervision; "right answer via wrong reasoning"). [strong]
- **Model critics are unreliable alone:** Huang et al. 2024 (self-correction can degrade accuracy), FlipFlop (Laban et al.; "Are you sure?" drops accuracy 8–34%), RiddleBench (misses own errors 67.7%). Justifies CAS-over-critic. [strong]
- **Generator fragility is systematic:** GSM-Symbolic (Mirzadeh/Apple) — up to 65% drop from one irrelevant clause; Phi-3-mini 83.7→18.0. ⇒ verification must be **independent of the generator**. [strong]
- **Provenance schema:** verbatim quote + page/line anchor as a non-nullable field; auto-zero any card whose quote doesn't entail the claim; **abstention enforced by pipeline logic, not the prompt** (AbstentionBench). This is what prevents the "untraceable claim → AI section zeroed" failure. [strong]
- **Asymmetric pre-set gate:** fact-precision ≥0.98 (≤1 wrong card/50) AND useful-yield ≥0.60, lodged before scoring; ≥2 raters, Cohen/Fleiss κ **with** percent agreement + Gwet's AC1 (kappa paradox). [strong]
- **Beat-the-baseline design:** template/cloze extraction (high-precision-by-construction) + non-RAG prompting, McNemar's exact test + paired bootstrap. Matches the Friday milestone. [strong]

## Problems / gaps
1. **[HIGH for GRE specifically — conceptual-card weakness] CAS only certifies *computational* cards.** But the GRE Math Subject Test is ~50% calculus + 25% abstract algebra/number theory + real analysis/topology — **a large share is conceptual/definitional/proof-flavored**, which CAS *cannot* verify; those fall back to NLI-entailment + human adjudication (weaker guarantees, and the response notes κ<0.35 for pedagogy-type judgments). **Risk:** the safely-certifiable subset skews toward computational calculus, **under-covering exactly the conceptual topics** — and this interacts dangerously with the coverage map (SQ1/7c): the app could report "topic covered" when it only has weakly-verified conceptual cards. **Action:** in synthesis, require the coverage map to distinguish *CAS-verified* vs *entailment+human-verified* cards, and don't let conceptual cards inflate apparent coverage/readiness.
2. **[medium — statistical] The n=50 gate is a screen, not proof.** At n=50, a 0.98 precision estimate has a wide CI (roughly 89–99.9%); "passing" does not establish a ≤2% *population* error rate. The response flags this (necessary-not-sufficient) — keep that framing explicit; never market the gate as validation.
3. **[low] Fact-precision ≥0.98 is anchored by *analogy* to GSM8K's <2% human-curation error**, not derived for this corpus. Reasonable default; tune. (Flagged by the response.)

## Cross-links (for synthesis dedupe)
- **Leakage/isolation (Section E) duplicates prompt 3 Section C** (Yang et al. 2023 rephrased samples, 13-gram, embedding cosine, canaries). → Merge into **one shared leakage methodology** serving both the performance model and the AI eval.
- **The 50-item gold set is one instance of the broader held-out item-bank need** that prompts 3 and 4 also have → consolidated in follow-up 11.

## Decision
- **No new prompt for AI now** (P2 per priorities). Two items carry forward: (a) **conceptual-card limitation** must constrain coverage/readiness claims; (b) **leakage methodology is shared** with the performance model. Add the conceptual-vs-computational coverage distinction to the synthesis recommendations.
