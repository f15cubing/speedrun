<!-- Raw sub-agent response. Captured: 2026-06-29. Round 2 (follow-up). -->
<!-- Prompt: prompts/10-olympiad-risks-synthesis.md | Critique: critiques/10-olympiad-risks-synthesis.md -->
<!-- Do not edit; this is the source record. -->

# Olympiad Problems in a GRE Math Subject Test Prep App: Risk, Opportunity Cost, and Sequencing (Spec Dimensions 4 & 5)

**Bottom line:** Do **not** ship olympiad-style problems as a core feature; the evidence base predicts a low-yield, demoralizing distraction for a breadth-and-speed exam. There is a narrow, falsifiable, defensible role for them as an **optional, capped supplement** for already-strong students late in prep — but only with strict guardrails, and the recommendation flips to "remove" for struggling students.

## TL;DR
- **Don't ship as core.** The GRE Math Subject Test rewards broad coverage (calculus ~50%, algebra ~25%, additional topics ~25%) and triage speed (~2.6 min/item); olympiad problems are proof-oriented, far harder per item, and reward slow deep work — a construct and pacing mismatch with high opportunity cost.
- **Defensible only as an optional, ≤10% supplement** for already-strong students (those already scoring ~80th percentile / ~750+) in the back third of a study plan, targeted at the discrete-math/combinatorics/number-theory topics where competition framing genuinely overlaps the exam.
- **For struggling or time-boxed (1-week) students, remove it entirely**: cognitive-load theory and the expertise-reversal effect predict it becomes an *undesirable* difficulty that crowds out higher-yield calculus breadth and spaced retrieval.

## Key Findings
- **The exam construct is breadth + speed, not depth.** Per ETS ("GRE Subject Test Content and Structure"), the test "consists of approximately 66 multiple-choice questions… Approximately 50% of the questions involve calculus and its applications… About 25% of the questions in the test are in elementary algebra, linear algebra, abstract algebra and number theory," with the remaining ~25% in "additional topics"; total testing time is 2 hours 50 minutes (~2.6 min/item). ETS cautions that "the percents given are estimates; actual percents will vary somewhat from one edition of the test to another." Number theory sits *inside* the 25% algebra block; combinatorics is one of five items in the "discrete mathematics" bullet, itself one of three bullets in the 25% additional-topics block. ETS publishes **no sub-percentage** for combinatorics/number theory — so olympiad-favored topics are a genuinely small, unquantified slice. *(Institutional/ETS; high confidence.)*
- **Olympiad problems are a different construct.** They are proof-based, reward sustained creative effort over ~30–60 min, and award partial credit for reasoning — none of which the GRE measures. *(Practitioner + institutional; high confidence on the descriptive claim.)*
- **Cognitive-load theory predicts harm for novices.** Unguided hard problem-solving via means-ends analysis imposes heavy working-memory load that does not build schemas (Sweller 1988); worked examples beat problem-solving for novices. *(Peer-reviewed; strong.)*
- **The expertise-reversal effect makes the recommendation level-dependent.** Techniques (and difficulty levels) that help advanced learners can be neutral or harmful for novices, and vice versa (Kalyuga, Ayres, Chandler & Sweller 2003). This is the empirical hinge for "who benefits." *(Peer-reviewed; strong.)*
- **Desirable difficulty has a precondition.** Bjork's framework: difficulties are desirable only if the learner has the background knowledge to overcome them; otherwise they are *undesirable* (E. Bjork & R. Bjork 2011). *(Peer-reviewed/named expert; strong theoretical.)*
- **Time-on-task buys less than folk theory claims.** Macnamara, Hambrick & Oswald (2014) found "deliberate practice explained 26% of the variance in performance for games, 21% for music, 18% for sports, 4% for education, and less than 1% for professions"; Ericsson disputes the broad definition. Either way, *which* practice matters — and practice should resemble the criterion task. *(Peer-reviewed; contested — reported honestly.)*
- **Far transfer is weak and format-dependent.** Pan & Rickard (2018), a meta-analysis of 192 transfer effect sizes from 122 experiments (N = 10,396), found a grand weighted transfer effect of d ≈ 0.40 but a larger "medium-large effect (d = 0.58) for transfer across initial and final test formats" — i.e., transfer is strongest when practice and test *formats match*. Cognitive-training meta-analyses separately conclude far transfer "rarely occurs." Olympiad→GRE is a far-transfer, format-mismatched bet. *(Peer-reviewed; strong.)*

## Section A — Risk / Inefficiency Table

| # | Risk | Mechanism | Supporting evidence (type; strength) | Severity (1-week → months horizon) |
|---|------|-----------|--------------------------------------|-------------------------------------|
| 1 | **Difficulty mismatch / over-hard items** (frustration, demoralization, low return per hour) | For a learner without prerequisite schemas, an olympiad problem is an *undesirable* difficulty: working memory is consumed by means-ends search, leaving nothing for schema construction; persistent failure depresses motivation and persistence. The optimal-difficulty "sweet spot" is badly violated (olympiad success rates approach zero for non-experts). | Bjork & Bjork 2011 (desirable/undesirable difficulty, peer-reviewed, strong theoretical); Sweller 1988 + Kalyuga et al. 2003 expertise-reversal (peer-reviewed, strong); Wilson et al. 2019 — "the optimal error rate for training is around 15.87% or… optimal training accuracy is about 85%," derived for "stochastic gradient-descent based learning algorithms" in "binary classification tasks" (peer-reviewed, moderate — analogical to test prep); dropout/demotivation literature (peer-reviewed, moderate) | **1 week: Severe. Months: High** (esp. struggling students) |
| 2 | **Breadth/coverage neglect** | Olympiad depth concentrates on combinatorics/number theory/proof — topics that are a tiny, unquantified slice of the GRE, while ~50% calculus and broad "additional topics" go under-practiced. Each hour on olympiad is an hour not spent on the modal scored item. | ETS content spec (institutional, high); deliberate-practice/specificity logic (peer-reviewed, strong) | **1 week: Severe. Months: Moderate-High** |
| 3 | **Pacing mismatch** | Olympiad trains slow, deep, single-problem immersion; GRE rewards ~2.6 min/item triage and rapid "skip-and-return." Habituating to deep work can train in slowness and impair time-management under the real constraint. | ETS timing + practitioner pacing consensus (Magoosh, Kaplan, ETS strategies — practitioner/institutional, high on the prescription); transfer-appropriate processing / format-match (Pan & Rickard 2018, peer-reviewed, moderate) | **1 week: High. Months: Moderate** |
| 4 | **Format mismatch / negative transfer** | Proof skill is untested on a 5-choice MC exam. Over-rigor (proving rather than eliminating) and neglect of answer-elimination/back-solving strategies can transfer negatively, costing time and points. | Pan & Rickard 2018 (format-match transfer strongest, d = 0.58; peer-reviewed, strong); practitioner strategy guides (high on prescription) | **1 week: High. Months: Moderate** |

## Section B — Opportunity-Cost Analysis

Frame the decision as allocation of a fixed study budget *H* hours between (a) olympiad problems and (b) targeted GRE-style practice (mixed-topic, timed, MC, calculus-heavy) plus spaced retrieval on calculus and algebra breadth.

The deliberate-practice literature — even read generously — says the *content and design* of practice, not raw hours, drives gains, and that effective practice has clear goals, immediate feedback, and targets the performance task. Olympiad problems fail the "targets the performance task" test for a breadth-and-speed MC exam. The **specificity principle** and the format-dependence of transfer (Pan & Rickard 2018: transfer is strongest, d = 0.58, when practice and test formats match) jointly predict that an hour of mixed, timed, MC calculus practice yields more GRE points than an hour of olympiad combinatorics.

Crucially, the **deliberate-practice debate cuts against olympiad, not for it.** Ericsson's camp says practice must be *specifically designed to improve the target performance* — olympiad isn't designed for GRE speed/breadth. Macnamara et al.'s skeptical camp found deliberate practice "explained… 4% of the variance in performance for education," so the marginal hour is even less likely to justify a high-risk, low-specificity activity. Both readings favor reallocating hours to GRE-style practice and spaced retrieval. The relevant math-specific evidence is itself modest: Murray, Horner & Göbel (2025) report "a robust small to medium effect of spaced versus massed practice overall (g = 0.28, 27 studies, 53 effect sizes)," while for testing vs. restudy in mathematics "the weighted mean effect… was g = 0.18. However, the 95% confidence interval crossed zero, suggesting the testing effect is not robust" in mathematics. The opportunity cost of olympiad time is therefore **high in expectation and especially high under a short horizon**, where there is no time to amortize any speculative schema-deepening benefit.

## Section C — Conditional Recommendation (Decision Tree)

**Q1: Is the horizon ≤ ~2 weeks, OR is the student below ~50th percentile / struggling with calculus fundamentals?**
- **YES → DON'T SHIP / hide the feature.** *Evidence tag:* expertise-reversal (Kalyuga et al. 2003) + undesirable difficulty (Bjork & Bjork 2011) + breadth opportunity cost (ETS spec). Higher-yield alternative: **targeted timed MC practice + spaced retrieval on calculus and linear algebra breadth.**

**Q2: Is the student already strong (≈80th percentile+, ~750+ scaled), with calculus/algebra breadth secured, and ≥6 weeks remaining?**
- **YES → SHIP AS OPTIONAL SUPPLEMENT WITH GUARDRAILS.** *Evidence tag:* expertise-reversal (advanced learners tolerate/benefit from reduced guidance and higher difficulty); desirable-difficulty precondition satisfied; motivation/engagement upside for high-achievers.
  - **Dose:** ≤10% of practice volume; hard cap (e.g., ≤2 items/session).
  - **Placement:** back third of the plan, *after* a full-length timed diagnostic confirms breadth mastery.
  - **Topic targeting:** only olympiad problems that map to GRE-scored topics — **discrete math/combinatorics, number theory, probability, sequences/series** — never pure proof-geometry or topics off the GRE spec.
  - **Format guardrail:** present in MC form with a **2.5-minute soft timer** and an explicit "skip and guess" affordance, so the feature trains triage, not slow immersion.
  - **Difficulty guardrail:** keep per-item success near the 85% band by selecting "olympiad-flavored but tractable" items, not true competition problems.

**Q3: Default (most users — mid-range, moderate horizon)?**
- **OFF by default, available as opt-in "challenge" mode** with the same guardrails, clearly labeled as enrichment that does not substitute for core practice. *Evidence tag:* contested transfer + opportunity cost ⇒ make it contingent and user-controlled.

**Profile where the recommendation flips:** The pivot is **prior knowledge/percentile**. For an already-strong student, olympiad items are a desirable difficulty and a plausible engagement/schema-deepening supplement; for a struggling student, the *identical* items become an undesirable difficulty that predicts frustration, dropout, and coverage neglect. This is the expertise-reversal effect operationalized as a product rule.

## Section D — Ablation Study & Falsifiable Hypothesis

**Feature:** "Olympiad-style problem injection" — replacing a capped fraction of a study session's items with harder, competition-flavored (but GRE-topic-aligned, MC-formatted, timed) problems.

**Falsifiable hypothesis (one sentence):** *Among already-strong users (baseline ≥80th percentile) with ≥6 weeks to test, injecting olympiad-style problems at a 10% dose with triage guardrails will raise simulated full-length GRE Math Subject Test scores by ≥0.2 SD relative to a matched-time control of GRE-style practice — and will NOT reduce scores or increase dropout among any subgroup.*

**Ablation design:**
- **Arms:** (A) 100% GRE-style practice [control]; (B) 90% GRE-style + 10% olympiad-injection with guardrails; (C) 90% + 10% olympiad **without** the pacing/format guardrails (isolates the guardrails); (D) 80% + 20% olympiad (isolates dose). Hold total practice **time** constant across arms (time-matched, not item-matched — this is the key opportunity-cost control).
- **Randomization & stratification:** stratify by baseline percentile band (the expertise-reversal moderator) and horizon.
- **Primary outcome:** change in timed full-length practice-test score. **Secondary:** items-per-minute / pacing on the timed test; topic-level breadth coverage; **dropout/engagement** (the demoralization risk); self-reported frustration.
- **Falsification conditions:** the feature is rejected if Arm B ≤ Arm A on score, OR if any arm shows higher dropout or worse pacing, OR if effects appear only for already-strong users but the feature is shipped to all (the expertise-reversal trap).
- **Decision thresholds:** ship-to-strong-users if B beats A by ≥0.2 SD with no subgroup harm; otherwise keep opt-in or remove.

**Better-evidenced alternative feature (recommended to prioritize):** an **interleaved + spaced-retrieval engine** that mixes GRE topic types within sessions and re-surfaces calculus/algebra items on expanding intervals. This is backed by stronger, more directly relevant evidence (interleaving improves math discrimination, though Brunmair & Richter's 2019 meta-analysis shows effect sizes are small and design-dependent; spacing in math g ≈ 0.28) and aligns with the exam's breadth-and-discrimination demands. If engineering capacity is limited, build this before olympiad injection.

## Recommendations
1. **Now:** Do not build olympiad injection as a core feature. Build the interleaving + spaced-retrieval engine first (higher and more direct evidence).
2. **If pursuing olympiad at all:** ship as an **opt-in, ≤10%, guardrailed "challenge mode,"** gated to already-strong users with ≥6 weeks, and instrument it for the ablation in Section D.
3. **Kill/keep thresholds:** keep only if the guardrailed arm beats time-matched control by ≥0.2 SD on timed full-length scores **with zero subgroup harm** (no increased dropout, no worse pacing). Otherwise remove.
4. **Never** expose true (proof-based, untimed) competition problems to struggling or short-horizon users.

## Caveats
- The pro-olympiad case rests on **schema-deepening and motivation** benefits that are real in principle (desirable difficulty for the prepared learner; engagement for high-achievers) but **weakly supported for this specific transfer** (olympiad→MC breadth/speed exam). The recommendation is therefore contingent and falsifiable, not categorical.
- Effect sizes cited are largely **domain-general**; the spacing/retrieval evidence is weaker and less robust *specifically in mathematics* (testing-vs-restudy g = 0.18 with a CI crossing zero) than in verbal domains. The "85% Rule" is derived from machine/perceptual-learning models and is analogical when applied to test prep.
- The deliberate-practice variance figure (4% in education) is **contested** (Ericsson vs. Macnamara); I report both and note that both readings disfavor olympiad injection.
- ETS does not publish sub-percentages within its 25% categories, so "olympiad topics are a small slice" is directionally certain but not precisely quantified.

## Sources

**Peer-reviewed**
- Sweller, J. (1988). "Cognitive Load During Problem Solving: Effects on Learning." *Cognitive Science* 12(2): 257–285. https://doi.org/10.1207/s15516709cog1202_4
- Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). "The Expertise Reversal Effect." *Educational Psychologist* 38(1): 23–31. https://doi.org/10.1207/S15326985EP3801_4
- Kalyuga, S. (2007). "Expertise Reversal Effect and Its Implications for Learner-Tailored Instruction." *Educational Psychology Review* 19: 509–539. https://doi.org/10.1007/s10648-007-9054-3
- Bjork, E. L., & Bjork, R. A. (2011). "Making Things Hard on Yourself, But in a Good Way: Creating Desirable Difficulties to Enhance Learning." In *Psychology and the Real World*. https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/04/EBjork_RBjork_2011.pdf
- Macnamara, B. N., Hambrick, D. Z., & Oswald, F. L. (2014). "Deliberate Practice and Performance in Music, Games, Sports, Education, and Professions: A Meta-Analysis." *Psychological Science* 25(8): 1608–1618. https://doi.org/10.1177/0956797614535810
- Macnamara, B. N., Hambrick, D. Z., & Moreau, D. (2016). "How Important Is Deliberate Practice? Reply to Ericsson (2016)." *Perspectives on Psychological Science* 11(3): 333–350. https://doi.org/10.1177/1745691616635614
- Hambrick, D. Z., Macnamara, B. N., & Oswald, F. L. (2020). "Is the Deliberate Practice View Defensible? A Review of Evidence and Discussion of Issues." *Frontiers in Psychology* 11:1134. https://doi.org/10.3389/fpsyg.2020.01134
- Pan, S. C., & Rickard, T. C. (2018). "Transfer of Test-Enhanced Learning: Meta-Analytic Review and Synthesis." *Psychological Bulletin* 144(7): 710–756. https://pdf.retrievalpractice.org/transfer/Pan_Rickard_2018.pdf
- Rohrer, D., Dedrick, R. F., & Stershic, S. (2015). "Interleaved Practice Improves Mathematics Learning." *Journal of Educational Psychology* 107(3): 900–908. https://files.eric.ed.gov/fulltext/ED557355.pdf
- Brunmair, M., & Richter, T. (2019). "Similarity Matters: A Meta-Analysis of Interleaved Learning and Its Moderators." *Psychological Bulletin* 145(11): 1029–1052. https://doi.org/10.1037/bul0000209
- Wilson, R. C., Shenhav, A., Straccia, M., & Cohen, J. D. (2019). "The Eighty Five Percent Rule for Optimal Learning." *Nature Communications* 10:4646. https://doi.org/10.1038/s41467-019-12552-4
- Murray, Horner & Göbel (2025). "A Meta-Analytic Review of the Effectiveness of Spacing and Retrieval Practice for Mathematics Learning." *Educational Psychology Review* 37, Art. 75. https://doi.org/10.1007/s10648-025-10035-1

**Institutional**
- ETS. "GRE Subject Test Content and Structure." https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html
- ETS. *GRE Mathematics Test Practice Book* (2024). https://www.ets.org/pdfs/gre/practice-book-math.pdf
- ETS. *GRE Subject Test Interpretive Data, Tables 2A/2B* (Mathematics Test: mean 680, SD 161, N = 5,180; July 2021–June 2024). https://www.ets.org/pdfs/gre/gre-guide-table-2.pdf
- ETS. "Strategies & Tips for the GRE Subject Tests." https://www.ets.org/gre/test-takers/subject-tests/prepare/strategies-tips.html

**Named expert**
- Robert A. Bjork & Elizabeth L. Bjork, UCLA Bjork Learning & Forgetting Lab. https://bjorklab.psych.ucla.edu/
- K. Anders Ericsson (deliberate-practice framework), as represented in the Ericsson–Macnamara exchange (Ericsson 2016, *Perspectives on Psychological Science* 11(3): 351–354).

**Practitioner (clearly labeled, not peer-reviewed)**
- Magoosh. "Pacing on the GRE Math Sections." https://magoosh.com/gre/pacing-on-the-gre-math-sections/
- Kaplan. "Math GRE Subject Test: What's Tested?" https://www.kaptest.com/study/gre/math-gre-subject-test/
- Marks Education. "Skipping Questions on the GRE: A Key Strategy." https://markseducation.com/skipping-questions-on-the-gre-key-strategy/

**Self-confidence summary:** High confidence in the construct-mismatch, breadth, and pacing arguments (anchored in ETS primary data and well-replicated CLT/expertise-reversal findings). Moderate confidence in the precise opportunity-cost magnitude (transfer and deliberate-practice evidence is contested and domain-general). The conditional "optional supplement for strong students" branch is the most uncertain and is deliberately framed as a falsifiable bet.

**One-line recommendation:** **Optional supplement with guardrails — opt-in, ≤10%, strong-students-only — defaulting to "off"; do not ship as core.** *Evidence tag: expertise-reversal + desirable-difficulty precondition (for the narrow yes) vs. breadth/pacing opportunity cost + weak/format-dependent far transfer (for the default no).*
