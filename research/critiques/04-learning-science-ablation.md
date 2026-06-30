# Critique 04 — Learning-science feature & ablation

**Verdict: excellent and directly actionable — and intellectually honest in exactly the way the spec rewards.** It resists the obvious move (ship "retrieval practice") by pointing out that retrieval and spacing are *already delivered by Anki*, so the only genuine *increment* with far-transfer math evidence is **interleaving**. It also tells the truth about power: a one-week tiny-n run cannot detect the realistic effect.

## What is genuinely useful (carry into synthesis) — [strong] unless noted
- **Ship interleaving.** Best evidence-to-effort ratio: Rohrer et al. 2020 (preregistered cluster RCT, d=0.83, *novel* problems requiring discrimination = mirrors timed GRE quant) + Brunmair & Richter 2019 (math-specific g=0.34). [strong]
- **Honesty about the effect size:** the d=0.83 is **confounded with spacing**; the "pure" math interleaving estimate is only g≈0.34, so the realistic *increment over an already-spaced app* is dz≈0.2–0.35, not 0.8. This candor is gold for the grade. [strong]
- **Retrieval + spacing are the Anki baseline, not shippable increments.** Sharp, correct framing that shapes the ablation. [strong]
- **Power analysis:** dz=0.3 needs ~90 learners; tiny-n is powered only for dz≈0.8. Pre-register as an estimation/feasibility pilot with TOST equivalence, not a confirmatory trial. [strong]
- **Delayed test (≥1 week) as primary endpoint** (Soderstrom & Bjork 2015 learning-vs-performance): an immediate test would *underestimate* interleaving (a desirable difficulty). Methodologically crucial. [strong]
- **Carryover is the real within-subject threat** (you can't unlearn) → parallel item sets + mixed model with sequence/period factors. [strong]

## Problems / gaps
1. **[medium — design tension] "Same questions across arms" (spec) vs "parallel non-overlapping item sets" (the carryover fix) are mutually exclusive in a within-subject design.** Resolution to specify: practice on *different* matched item sets per arm, but evaluate all arms on a *common, held-out delayed test*. "Same study time" and "matched difficulty," not "same items," is the honest reading. This needs to be stated explicitly so the ablation is reproducible. → addressed by follow-up 11 (the shared held-out test instrument).
2. **[medium — feasibility] Realistic n is team-size (~1–5), not 10–20.** In a one-week hackathon you likely cannot recruit 10–20 naive GRE-math learners. Be explicit that the deliverable is **the design + analysis machinery + an honest "inconclusive/underpowered" result** (which the spec explicitly rewards over "feels better"), possibly as an N-of-few. Don't imply a real powered ablation is achievable.
3. **[low — implementation] Interleaving is not quite a "trivial reorder."** Genuine interleaving requires (a) cards **tagged by problem type/topic** — the *same tag taxonomy* as prompt 5's mastery query and prompt 1's coverage map — and (b) deliberately mixing **confusable** categories (Brunmair & Richter; Carvalho & Goldstone), since interleaving dissimilar types yields little. So the feature depends on the topic-tag substrate and on a confusability design choice. Not a flaw, but a dependency to surface.
4. **[fine] Far-transfer caveat is correctly the crux:** Rohrer is 7th-grade classroom math, not adult GRE; generalization is an inference, not a measurement. This is the same skeptical lens the olympiad thread (SQ9) must apply.

## Cross-cutting: the FEATURE-DECISION TENSION (flag for the user)
The spec allows **one** learning-science feature with an ablation. This response makes a strong evidence case for **interleaving**. The **olympiad-problem idea (SQ8–SQ10, the user's preferred direction)** is competing for that same slot — and on current evidence, *olympiad-for-GRE far transfer is far less established than interleaving's*. Two ways to reconcile, to be decided **after** prompts 9/10 return:
- **(A) They're complementary, not competing:** interleaving is the *mechanism* (card-ordering rule); olympiad-style items could be *content* that gets interleaved with standard items — but only if SQ9 shows the transfer holds and SQ10's opportunity-cost analysis clears it.
- **(B) They compete:** if olympiad transfer evidence is weak (likely, per the transfer literature), ship **interleaving** as the ablated feature and treat olympiad problems as an optional, clearly-caveated supplement — not the headline learning-science claim.
This is the most important strategic decision in the learning-science track. Do not let enthusiasm for the olympiad idea override the much stronger interleaving evidence in the *graded* feature slot.

## Decision
- **Write follow-up 11** (shared held-out GRE-style test instrument) — resolves problem #1 and serves prompts 3, 4, and 7 at once.
- **No 04b needed**; the ablation design is otherwise sound. Carry forward [strong].
- **Defer the feature-choice (A vs B) to post-SQ9/SQ10 synthesis.**
