# Brainlift: Hard Problems + Anxiety Inoculation for GRE Math Subject Prep

## DOK 1 — Concrete Facts (Sourced)

### The Exam

- 66 MC questions, 5 options, 2 hr 50 min → ~2.6 min/item. Rights-only scoring. [¹]
- Content: ~50% calculus, ~25% algebra, ~25% additional topics (real analysis, discrete math, topology, probability). [¹]
- Scale: raw 60 → 880 (88th pct); raw 50 → 800 (71st pct); mean 680 / SD 161 (N = 5,180, cohort 2021–24). [¹]
- All ~431 official ETS items are public PDFs — treat the entire corpus as contaminated for held-out evaluation. [¹]

### Interleaving

- Rohrer et al. (2020) RCT, 54 classes: interleaved practice d ≈ 0.83 vs. blocked; positive across all teachers. [²]
- Mechanism: forces strategy *selection* before execution — exactly the GRE's task demand. [²]

### Hard Problems

- Kalyuga et al. (2003): expertise-reversal effect — the same problem deepens schemas for experts but causes overload for novices. [³]
- Wilson et al. (2019): optimal training accuracy ≈ 85%. True competition problems sit near 0% for non-experts — undesirable difficulty. [⁶]

### Anxiety & Stress

- Huntley et al. (2019), 44 RCTs: anxiety interventions move self-reported anxiety (g = −0.76) far more than objective scores (g = 0.28). [⁴]
- Beilock & Carr (2005): choking under pressure concentrates in *high-WM, high-ability* individuals — precisely the prepared student. [⁵]

### FSRS / Memory Model

- FSRS-6 uses 21 parameters fit per user; needs ~20–30% fewer reviews than SM-2 for equal retention (Anki default since Nov 2023).
- Critical gap: P(recall card) ≠ P(answer unseen exam question). The bridge is the project's core engineering challenge.

---

## DOK 2 — Summaries

### 2a. What Interleaving Actually Does (and Why Classroom Effects Are Partly Confounded)

Rohrer et al.'s classroom RCT (2020, 54 classes) showed d ≈ 0.83 — one of the largest effect sizes in math learning research. But Brunmair & Richter's (2019) meta-analysis separates out that the "pure" interleaving effect in math is closer to g ≈ 0.34, because the large classroom effects are partly driven by the *spacing* that interleaved practice incidentally creates between topics. This distinction matters for app design: an interleaved engine that also embeds spaced retrieval captures both effects simultaneously, giving you more than either alone. Murray et al. (2025) confirm spacing adds g ≈ 0.28 in math, but the testing-effect CI crossed zero — suggesting that *what* you test matters more than *that* you test.

### 2b. The Expertise-Reversal Effect Is the Central Moderator for Hard Problems

Kalyuga et al. (2003) established the expertise-reversal effect: the same problem that deepens a schema for an expert creates cognitive overload for a novice, who spends all working memory on means-ends search rather than schema formation. A difficulty is only *desirable* if the learner has enough background to overcome it. Wilson et al. (2019) operationalize this: optimal training accuracy ≈ 85%. True competition problems sit near 0% success rate for non-experts — precisely the opposite. This is not a reason to abandon hard problems entirely; it is a reason to make them level-gated. [³][⁶]

### 2c. Anxiety Is Real But Mostly Confounded — and Interventions Move Feelings More Than Scores

The anxiety ↔ performance correlation (r ≈ −.26 to −.28) sounds meaningful but ~7% of score variance explains little, and a substantial portion doesn't survive controls for prior ability and working memory. The causal story splits: for *under-prepared* students, anxiety is a symptom of low mastery (deficit model) — studying fixes it, not relaxation. For *well-prepared, high-WM* students, anxiety can cause genuine choking (interference model — Beilock & Carr 2005), but this is precisely the subgroup that can least afford to be told "don't panic" without evidence. Huntley et al.'s meta-analysis (2019) shows interventions move self-reported anxiety (g ≈ −0.76) far more reliably than objective scores (g ≈ 0.28), and the replication record for brief "magic bullet" interventions (expressive writing: failed; reappraisal: well-powered 2026 replication null) is poor. The one intervention with GRE-specific evidence — Jamieson's arousal reappraisal (2010, d ≈ 1.03 on actual GRE-Quant) — is promising but rests on N = 28, and the 2024 meta-analytic estimate is only d = 0.23.

### 2d. Far Transfer from Olympiads to the GRE Is Plausible But Unproven

The GRE rewards breadth (50% calculus) + speed (2.6 min/item) + MC format. Olympiads reward depth + proof + sustained reasoning over hours. Barnett & Ceci (2002) show these differ on multiple transfer axes — this is squarely "far transfer." The closest controlled study (Rebholz et al. 2022) shows some transfer to a curriculum test in 9-year-olds, but the training group started 1 SD ahead and the result was only significant in one of two grades. Detterman's verdict holds: transfer is rare and proportional to task similarity. The most defensible transfer channels — near-content overlap (olympiad number theory ↔ GRE additional topics) and stress/anxiety inoculation — are *near transfer*, not far. The brain-training collapse (Simons, Owen, Sala & Gobet) serves as the cautionary analogy: impressive near-task gains, near-zero far-transfer, especially once active controls are used.

### 2e. The Three-Score Architecture — Memory ≠ Performance ≠ Readiness

Flashcard recall (FSRS's retrievability) is not the same as exam-question performance, which is not the same as projected GRE score. These require three distinct inference steps, each with its own uncertainty: (1) card-level calibration — does FSRS's 80% mean ~80% recall on held-back reviews? (2) performance bridge — does topic mastery predict held-out exam-style question accuracy? (3) readiness projection — does question accuracy predict the GRE score scale? Collapsing them produces a confident-sounding but ungrounded number. Showing them separately, with honest ranges and explicit coverage requirements, is the key product decision.

---

## DOK 3 — Insights

### 3a. Interleaving Already Does What Hard Problems Try to Do — for Less Risk

Hard olympiad problems are sometimes justified as forcing "strategy selection" under pressure. But interleaving (mixing GRE topic types within sessions) achieves this *exactly* — it **forces the student to identify which technique applies before applying it**, which is precisely the discrimination skill the GRE demands. The difference: interleaving operates at GRE difficulty (near the 85% success zone) while olympiad problems operate near 0% for non-experts (undesirable difficulty). Interleaving is the mechanism; hard problems are an extreme, risky implementation of a subset of that mechanism. If you build the interleaved engine well, hard problems add noise more than signal for most students.

### 3b. The Exam-Pressure Simulator Is Better-Justified Than Anxiety Interventions

The speededness of the GRE (~2.6 min/item, no pausing, 66 items) is itself a scored construct — it's not just a container for math ability, it's partly what the test measures. This gives a different justification for timed practice: not "exposure reduces anxiety" (weak, replication-fragile) but "format-matched practice trains the performance you'll be tested on" (transfer-appropriate processing, Pan & Rickard 2018, d = 0.58 for format-matched transfer). The exam-pressure simulator can be shipped on construct grounds without depending on the fragile anxiety-reduction literature at all. This makes it lower-risk to build and more intellectually honest to claim.

### 3c. The Interleaving Ablation Is More Scientifically Testable Than the Anxiety Ablation

An ablation comparing interleaved vs. blocked practice is clean: same items, same time, binary condition, objective metric (accuracy on a delayed mixed-topic test). An anxiety ablation is harder: the expected effect is g ≈ 0.28, sits right below typical detectable thresholds at small n, the flagship studies have failed to replicate, and self-reported anxiety reductions decouple from score gains. Running both ablations with a small n produces two underpowered, uninterpretable results. The strategic choice: keep interleaving as the single pre-registered ablation; ship anxiety components as cheap un-ablated defaults and justify the simulator on construct grounds.

### 3d. Hard Problems Are Conditionally Valuable — Gated by Percentile and Horizon

The expertise-reversal effect predicts a flip: for students already at ~80th percentile (≥750 scaled), with ≥6 weeks remaining, and after calculus/algebra breadth is secured — hard, competition-flavored problems become a *desirable* difficulty that deepens schemas. For struggling or short-horizon students, the identical problems are undesirable difficulty that wastes time on content (olympiad number theory/geometry) that is a small, unquantified fraction of the GRE. The practical implementation: hard problems are an opt-in "challenge mode," MC-formatted with a 2.5-min soft timer, targeting only GRE-scored topics (discrete math, combinatorics, number theory, sequences/series — never pure proof-geometry), capped at ≤10% of session volume, gated to the back third of the study plan. Default: off.

### 3e. The Deficit Model Means Anxiety Reduction Only Works After Content Mastery

The biggest practical insight from the anxiety research: for under-prepared students, anxiety is a *symptom* of low mastery, not the primary cause of low scores. Reducing anxiety without building mastery is treating the symptom. The correct diagnostic is to compare low-stakes vs. high-stakes performance: if both are low, the problem is preparation; if high-stakes underperforms low-stakes, anxiety/choking is the live bottleneck. The app should surface this distinction explicitly — only route users to the anxiety bundle after they've hit a mastery threshold.

---

## DOK 4 — Spiky Point of View

### The Hard-Problems + Anxiety-Inoculation Thesis

**The central bet:** Timed exposure to hard, GRE-topic-aligned problems simultaneously trains two things that standard flashcard-based prep cannot: (1) the *strategy-selection reflex* under time pressure — knowing instantly which technique applies to an unfamiliar-looking problem — and (2) *desensitization to the pressure itself*, so that the student's working memory remains available for math rather than being consumed by anxiety about the clock.

A *GRE-topic-aligned, MC-formatted, timed* hard problem — solved at the correct difficulty level (near 85% success for the target student) — trains the exact construct the GRE measures while simultaneously inoculating against the exact pressure the GRE creates.

**Why this is non-consensus:** Standard edtech philosophy optimizes for engagement, which means reducing struggle, adding hints on first failure, and keeping difficulty near a comfortable level. The research base (Bjork's desirable difficulties, Kapur's productive failure, Sweller's CLT) says this optimization is anti-correlated with long-term retention and transfer. The "sink or swim" framing is not a rejection of those principles — it is a precise application of them, where "swim" means reaching the 85% zone through adaptive difficulty, not throwing novices into deep water.

**The anxiety half:** Test anxiety for prepared, high-WM students is a genuine interference effect (Beilock & Carr 2005) — it crowds out the working memory needed to execute the math they already know. The mechanism of inoculation is not relaxation (which doesn't move scores reliably) but *habituation through repeated exposure to the pressure condition*. An exam-pressure simulator — authentic timing, no pauses, on-screen countdown, scored stakes — is the correct implementation. Reappraisal microcopy ("arousal is a resource") is a cheap add-on with a plausible mechanism, even if the effect size is small (d ≈ 0.23 meta-analytic estimate) and the 2026 replication came back null.

**Why they belong together (the synthesis):** Hard problems without pressure training produce students who can solve the problems slowly but freeze under the 2.6-min budget. Pressure training without hard problems produces students who are calm but haven't developed the strategy-selection reflex the hard problems build. Combined — in the correct sequence (breadth first, hard+timed second) and at the correct level (gated to strong students) — they address the two remaining failure modes after content mastery is secured: *not knowing which technique to reach for* and *not reaching for it fast enough under pressure*.

**The falsifiable version:** Among students already at ≥80th percentile (≥750 scaled) with ≥6 weeks remaining, injecting GRE-topic-aligned hard problems (MC-formatted, 2.5-min timer, ≤10% of session volume) combined with the exam-pressure simulator will raise delayed simulated GRE scores by ≥0.2 SD vs. a matched-time control of standard interleaved GRE practice — and will NOT increase dropout or reduce pacing in any subgroup. The recommendation flips to "remove" if either condition fails: any subgroup harm, or no score benefit for the strong-student subgroup specifically.

**What this is NOT:** It is not a claim that olympiad problems (proof-based, untimed, open-ended) improve GRE performance — they won't, for most students. It is not a claim that anxiety reduction alone raises scores — it doesn't, reliably. It is the claim that *hard + timed + GRE-aligned + gated by expertise* is a different animal from either of those, and that the combination addresses a genuine gap in what standard flashcard review can train.

---

## Sources

1. ETS. *Practice Book for the GRE® Subject Test in Mathematics*, Form GR3768, © 2024. Score Conversion Table, p. 35. https://www.ets.org/pdfs/gre/practice-book-math.pdf
2. Rohrer, D., Dedrick, R. F., Hartwig, M. K., & Cheung, C.-N. (2020). A randomized controlled trial of interleaved mathematics practice. *Journal of Educational Psychology*, 112(1), 40–52. http://uweb.cas.usf.edu/~drohrer/pdfs/Rohrer_et_al_2020JEdPsych.pdf
3. Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). The Expertise Reversal Effect. *Educational Psychologist*, 38(1), 23–31. https://doi.org/10.1207/S15326985EP3801_4
4. Huntley, C. D., et al. (2019). The efficacy of interventions for test-anxious university students: A meta-analysis of RCTs. *Journal of Anxiety Disorders*, 63, 36–50. https://doi.org/10.1016/j.janxdis.2019.01.007
5. Beilock, S. L., & Carr, T. H. (2005). When high-powered people fail: Working memory and "choking under pressure" in math. *Psychological Science*, 16(2), 101–105. https://doi.org/10.1111/j.0956-7976.2005.00789.x
6. Wilson, R. C., Shenhav, A., Straccia, M., & Cohen, J. D. (2019). The Eighty Five Percent Rule for optimal learning. *Nature Communications*, 10, 4646. https://doi.org/10.1038/s41467-019-12552-4
7. Bjork, E. L., & Bjork, R. A. (2011). Making things hard on yourself, but in a good way: Creating desirable difficulties to enhance learning. In M. A. Gernsbacher et al. (Eds.), *Psychology and the Real World* (pp. 56–64). Worth Publishers.
