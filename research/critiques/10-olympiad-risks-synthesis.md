# Critique 10 — Olympiad risks, opportunity cost, sequencing

**Verdict: strong, accept.** Lands a defensible, falsifiable product decision — **don't ship olympiad as a core feature; optional ≤10% guardrailed supplement for already-strong students, off by default** — grounded in cognitive-load theory and expertise reversal. It also (correctly) recommends interleaving + spaced retrieval as the better-evidenced feature, converging with prompt 4.

## What is genuinely useful (carry forward)
- **Expertise reversal as a product rule [strong]:** the same olympiad item is a *desirable* difficulty for a strong, prepared student and an *undesirable* one for a struggling student (Kalyuga et al. 2003; Bjork & Bjork 2011 desirable-difficulty precondition). The recommendation correctly *flips on prior knowledge/percentile* — this is the right axis.
- **Opportunity cost is real and double-supported:** specificity principle + format-matched transfer (Pan & Rickard 2018, d=0.58 when formats match) ⇒ an hour of timed-MC calculus practice beats an hour of olympiad combinatorics for *this* exam. Both readings of the deliberate-practice debate (Ericsson vs. Macnamara) disfavor olympiad. [moderate→strong]
- **Concrete, falsifiable ablation** with time-matched (not item-matched) arms and a subgroup-harm kill switch — exactly the honest design the spec rewards.

## Problems / calibration notes (important for synthesis)
1. **The recommended alternative's math-specific evidence is itself soft — flag this prominently.** The response honestly reports: interleaving in math **g≈0.34** (Brunmair & Richter, design-dependent), spacing in math **g≈0.28**, and testing-vs-restudy in **math g=0.18 with CI crossing zero (not robust)** (Murray, Horner & Göbel 2025). So "interleaving + spaced retrieval" is the *best available* increment, but the entire learning-science evidence base is **weaker in mathematics than in verbal domains**. Synthesis must temper feature claims accordingly — this is a cross-cutting finding (also implicit in prompt 4).
2. **The "85% Rule" (Wilson et al. 2019) is analogical** — derived for SGD binary classifiers, applied to human test prep. The guardrail "keep per-item success ~85%" is a reasonable heuristic but rests on a borrowed result; tag [low-moderate, analogical]. Don't present it as an established human-learning constant.
3. **Dose/percentile thresholds (≤10%, ≥80th percentile, ≥6 weeks) are reasoned defaults, not empirically derived.** Fine as product defaults; label as such, tune later.

## Decision
- **No follow-up.** SQ10 closed; the olympiad thread (8→9→10) is internally consistent and conclusions have converged.
- **Carry to synthesis [moderate-strong]:** ship **interleaving** as the ablated learning-science feature; treat olympiad problems as an **optional, capped, guardrailed enrichment** for strong students only, instrumented for the ablation, off by default — never the core differentiator. State the math-specific weakness of the whole effect-size literature.
