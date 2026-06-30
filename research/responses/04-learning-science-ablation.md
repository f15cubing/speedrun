<!-- Raw sub-agent response. Captured: 2026-06-29. Round 1. -->
<!-- Prompt: prompts/04-learning-science-ablation.md | Critique: critiques/04-learning-science-ablation.md -->
<!-- Do not edit; this is the source record. -->

# Shipping One Learning-Science Feature for an Anki-Based GRE-Math App: Evidence, Recommendation, and Ablation Protocol

## TL;DR
- **Ship interleaving** (mixing problem types within a deck rather than blocking by topic): it has the best combination of genuine *far-transfer* evidence on a timed, strategy-selection math test (Rohrer et al. 2020, d = 0.83) and direct mathematics-domain meta-analytic support (Brunmair & Richter 2019, math g = 0.34), at near-zero build cost — it is fundamentally a card-ordering rule.
- The honest skeptical read: retrieval practice and spacing are **already delivered by Anki itself**, so they are the baseline, not a shippable increment; and retrieval's *far*-transfer to novel math problems is weak/conditional (Pan & Rickard 2018, d = 0.40, often ~0 without specific moderators). Interleaving is the only increment with preregistered far-transfer math evidence.
- A 1-week, tiny-n within-subject run is **almost certainly underpowered** to detect the realistic incremental effect of one feature on a strong Anki baseline (dz ≈ 0.2–0.35; detecting dz = 0.3 needs ~90 learners). Pre-register it as a feasibility/estimation pilot with a delayed test and TOST equivalence testing — not a confirmatory trial.

---

## Key Findings
1. **Interleaving wins on the evidence-to-effort ratio** because its defining mechanism — forcing the learner to *select* a strategy rather than *execute* a pre-cued one — is exactly the GRE-quant task, and it costs almost nothing to implement in Anki.
2. **The biggest interleaving effects are partly confounded with spacing.** The dramatic classroom d = 0.83 (Rohrer et al. 2020) reflects interleaving *plus* the spacing it smuggles in; the "pure" math interleaving estimate is only g = 0.34. So the incremental value of an interleaving toggle on an app that already spaces is modest.
3. **Transfer is the crux, and it cuts against the most-cited technique.** The testing effect is robust for near transfer/retention but its far transfer to novel problem-solving is weak and moderator-dependent (Pan & Rickard 2018). Researchers genuinely disagree here.
4. **The study design is the binding constraint, not the science.** With tiny n over one week, you have ~80% power only for *large* effects (dz ≈ 0.8). The realistic incremental effect is undetectable; honest null-reporting machinery (CIs, TOST, pre-registration) is therefore mandatory.

---

## Section A — Evidence Table

**1. Interleaving (interleaved vs blocked practice).** Mixing problem types forces strategy *selection*, not just *execution*. Best meta-analysis: **Brunmair & Richter (2019)**, *Psychological Bulletin* 145(11):1029–1052, 59 studies / 238 effect sizes — overall **Hedges g = 0.42 (95% CI [0.34, 0.50])**; mathematical tasks specifically **g = 0.34 (95% CI [0.11, 0.57], p = .005)** — small, positive, but heterogeneous (some math studies null or negative, e.g., Rau et al.). Canonical math RCT: **Rohrer, Dedrick, Hartwig & Cheung (2020)**, *J. Educational Psychology* 112(1):40–52, preregistered cluster RCT across 54 seventh-grade Florida classes; on an unannounced test one month later the interleaved group scored **61% vs 38% blocked, d = 0.83 (95% CI [0.68, 0.97])**. Transfer: the strongest far-transfer case here — the criterion is *novel* problems requiring discrimination, mirroring timed GRE quant. Domain match: high (technique developed in math; Doug Rohrer, Kelli Taylor). Boundary condition and locus of researcher disagreement: interleaving helps when categories are *confusable/similar* and can *hurt* when too dissimilar — Brunmair & Richter's "similarity matters"; Paulo Carvalho & Robert Goldstone's sequential-attention account explains why (interleaving directs attention to discriminating features). Implementation: trivial in Anki (deck-ordering rule). **Confidence: [high — meta-analysis k=59 + preregistered RCT].**

**2. Retrieval practice / testing effect.** Retrieving beats restudying. **Rowland (2014)**, *Psychological Bulletin* 140(6):1432–1463, 159 effect sizes, **g = 0.50 [0.42, 0.58]** (recall tests larger, g≈0.72–0.82, than recognition/MC, g≈0.36); **Adesope, Trevisan & Sundararajan (2017)** practice-testing meta-analysis **g = 0.61 [0.58, 0.65]** (with MC g≈0.70). CRITICAL far-transfer limit: **Pan & Rickard (2018)**, *Psychological Bulletin* 144(7):710–756, 192 transfer effect sizes / 122 experiments / N=10,382 — transfer **d = 0.40 [0.31, 0.50]**, but "weakest … to problems involving worked examples" and to rearranged stimulus–response items; transfer depends on **response congruency** (d rises from 0.28 to 0.58), elaborated retrieval, and initial test performance; publication-bias-corrected intercepts "often indicat[e] no positive transfer when none of the aforementioned moderators are present." Domain match: most evidence is verbal/factual, not math problem-solving. Feedback-dependent. Implementation: **Anki *is* retrieval practice**, so this is the baseline, not an increment. **Confidence: [high for the effect; moderate/mixed for far transfer to novel math].**

**3. Spaced / distributed practice.** **Cepeda, Pashler, Vul, Wixted & Rohrer (2006)**, *Psychological Bulletin* 132(3):354–380, 839 assessments / 317 experiments — optimal inter-study gap scales with retention interval (ISI for maximal retention grows as the test delay grows). Applied classroom meta-analysis: **Mawson & Kang (2025)**, "The Distributed Practice Effect on Classroom Learning," *Behavioral Sciences* 15(6):771 (University of Melbourne), 22 reports / 31 effect sizes (N > 3,000): **d = 0.54 [0.31, 0.77]**, larger with longer retention intervals. Dunlosky, Rawson, Marsh, Nathan & Willingham (2013) rate spacing "high utility." Transfer: robust for retention; a **1-week window severely limits** both the spacing you can implement and the retention interval you can test. Domain match: mostly verbal. Implementation: Anki's SRS already does this — baseline. **Confidence: [high — meta-analysis], but poorly testable in 1 week.**

**4. Worked example → faded practice.** Sweller & Cooper (1985); faded examples (Renkl, Atkinson). Best math meta-analysis: **Barbieri, Miller-Cotto, Clerjuste & Chawla (2023)**, *Educational Psychology Review* 35:11 (8,033 abstracts screened; 43 articles / 55 studies / 181 effect sizes): worked examples on mathematics performance **g = 0.48 (p = .01)** — the **strongest math-domain match** of any technique here. Transfer: good to similar problem-solving, but Wittwer & Renkl (2010) found near/far transfer effects not significantly different from zero — contested. Boundary: **expertise-reversal effect** (worked examples help novices, hinder experts; Sweller, Kalyuga). Implementation: moderate — requires authoring step-by-step solutions and a fading schedule, more than card reordering. **Confidence: [high — meta-analysis; moderate for far transfer].**

**5. Desirable difficulties (umbrella framework).** Robert & Elizabeth Bjork (2011); Soderstrom & Bjork (2015). Not a single manipulation — it subsumes spacing, interleaving, testing, generation; effect sizes vary by manipulation, and "desirable" is conditional on prior knowledge (difficulties can become *undesirable* for low-knowledge learners). Chief contribution to this design: the learning-vs-performance distinction (see Section C). **Confidence: [low — theoretical/framework].**

**6. Feedback timing (optional).** Hattie & Timperley (2007); **Shute (2008)** *Review of Educational Research* 78(1):153–189 review; Kulik & Kulik (1988). Findings are mixed: immediate feedback tends to help procedural skills and short-run performance, delayed feedback sometimes aids transfer/concept formation; a recent RCT (Ryan et al. 2024, *Medical Education*) found immediate and delayed feedback "equally beneficial." **Confidence: [low — mixed].**

---

## Section B — Recommendation + Pre-Registered Hypothesis

**Recommendation: ship interleaving.** Among techniques that are a genuine *increment* over the Anki baseline (which already delivers retrieval practice and spaced repetition), interleaving is the only one with direct, preregistered, far-transfer mathematics evidence (Rohrer et al. 2020) and trivial implementation. Worked examples have comparable math evidence (Barbieri et al. 2023, g = 0.48) but higher build cost and contested far transfer; retrieval and spacing are largely *already shipped* by Anki.

**Honest transfer caveat to state in the spec:** the headline d = 0.83 comes from classroom studies in which interleaving also induced spacing; the "pure" interleaving meta-analytic estimate for math is only g = 0.34. The realistic incremental effect of an interleaving toggle, on top of an app that already spaces, is therefore **modest** — expect dz ≈ 0.2–0.35, not 0.8.

**Pre-registered hypotheses:**
- **H1 (primary):** On a *delayed* test (≥1 week after last practice) of novel GRE-style problems requiring strategy selection, accuracy in the full-app (interleaved) condition exceeds the feature-off (blocked) condition, dz > 0 (one-sided), with a smallest effect size of interest **SESOI = dz 0.3**, specified in raw score-point units.
- **H2 (boundary/mechanism):** The interleaving advantage is larger for *confusable* problem types than for *dissimilar* types (tests whether the benefit is genuine discrimination learning per Brunmair & Richter / Carvalho & Goldstone, rather than an artifact).
- **Secondary:** full-app vs plain Anki, and feature-off vs plain Anki, to isolate the *feature* from the *platform*.

---

## Section C — Ablation Protocol, Power Analysis, Null-Reporting Template

**Design.** Within-subject (each learner experiences all three arms — full app / feature-off / plain Anki) on the same questions and matched study time. Within-subject is far more powerful than between-subject at tiny n because it removes between-person variance from the error term: dz = d / √(2(1−r)), so a between-groups d of 0.3 can correspond to a substantially larger dz when the two conditions are positively correlated within learner. Note the corollary — dz is the standardized mean of the *difference scores*, so a between-groups d = 0.3 is **not** the same as dz = 0.3; report which you assumed.

**Counterbalancing and threats.** Randomly assign learners to condition *sequences* in equal numbers (Latin square over the three arms). Threats and mitigations:
- *Order/practice and fatigue* → counterbalancing neutralizes the average effect and, analyzed by sequence, makes order effects detectable.
- *Differential (asymmetric) carryover* is the serious threat: in learning studies you cannot "unlearn," so carryover can be effectively irreversible and becomes confounded with the treatment effect (Penn State STAT 509 gives the canonical educational-test example; arXiv 2505.03937 notes the required symmetry "is unverifiable a priori"). Mitigations: use **parallel, non-overlapping item sets** per arm; insert the **longest feasible gap/washout** between arms; and analyze **sequence and period as factors in a linear mixed model** rather than relying on a bare paired t-test, to surface asymmetry. With tiny n the between-subjects carryover test is itself underpowered, so prevention by design beats post-hoc testing.

**Power analysis (two-sided paired t-test, α = 0.05, power = 0.80; G*Power "difference between two dependent means," Faul, Erdfelder, Lang & Buchner 2007):**

| Effect size dz | Required n (pairs/learners) | Interpretation |
|---|---|---|
| 0.2 (small) | **199** | Out of reach |
| 0.3 (realistic increment) | **90** | Out of reach for 1-week tiny-n |
| 0.5 (medium) | **34** | Feasible only with a larger cohort |
| 0.8 (large) | **15** | Detectable; ~Rohrer classroom magnitude |

(These two-sided values were cross-checked against the G*Power tutorial in Kang 2021, the `pwr` R package, and applied protocols. One-sided tests need fewer — e.g., dz 0.5 → 27 — but two-sided is the honest default.)

**Plain statement of what the pilot can and cannot do:** A tiny-n one-week run (n ≈ 10–20) has ~80% power only for *large* effects (dz ≈ 0.8). It would catch the dramatic Rohrer classroom effect *if it were that large*, but it is badly underpowered for the realistic incremental dz ≈ 0.2–0.35 of one feature layered on a strong baseline. **Detecting dz = 0.3 requires roughly 90 learners.**

**Learning-vs-performance bias (Soderstrom & Bjork 2015).** A 1-week *immediate* post-test is biased in specific, predictable directions: (a) it can show performance gains that do not reflect durable learning, and (b) it can *miss* spacing/desirable-difficulty benefits that emerge only at delayed test. Because interleaving is a desirable difficulty, an immediate test will tend to **under-estimate** its true benefit (performance during interleaved practice often looks worse even as learning is better). Therefore the **primary endpoint must be a delayed test (≥1 week after last practice)**; an immediate test, if collected, is secondary and interpreted with this asymmetry flagged.

**Honest null-reporting template.**
1. **Pre-register** hypotheses, the SESOI (dz = 0.3, in raw points), the analysis plan, and the stopping rule before data collection (e.g., OSF).
2. Report the **effect estimate with its 90% CI** (90%, not 95%, to match TOST at α = 0.05), never p alone.
3. Run **TOST equivalence testing** (Lakens 2017, *SPPS*; Lakens, Scheel & Isager 2018, *AMPPS*) against the SESOI bounds to distinguish "evidence of no *meaningful* effect" from "no evidence / underpowered." Set equivalence bounds in **raw score units, not standardized d** (standardized bounds bias the test). Justify the SESOI explicitly — e.g., anchor-based (smallest score change students/instructors call meaningful) or the minimal effect the design could detect at this n.
4. **Credible underpowered-null language (use verbatim style):** *"With n = X, the design had 80% power only for effects of dz ≥ [value]. The observed effect was dz = [estimate], 90% CI [lower, upper]. Because this interval includes both zero and our SESOI of dz = 0.3, and the equivalence test was non-significant, the pilot is **inconclusive**: we can neither confirm a meaningful benefit nor reject one. This was an estimation/feasibility pilot, not a confirmatory test."* Avoid "the feature has no effect" or "interleaving doesn't work."

---

## Recommendations (staged, with thresholds)
1. **Now:** Build the interleaving toggle (lowest cost) and run the three-arm within-subject pilot purely to (a) validate instrumentation, (b) estimate the within-learner correlation r between conditions, and (c) get a preliminary dz with its 90% CI. Pre-register first.
2. **Decision threshold to scale up:** If the pilot's point estimate is dz ≳ 0.3 *and* r is high enough that a feasible cohort (~30–90) can reach 80% power, run the confirmatory delayed-test study. If the TOST shows equivalence within the SESOI, deprioritize interleaving and revisit worked-example/faded-practice (Barbieri et al. 2023, g = 0.48) as the next candidate despite its higher build cost.
3. **Always:** Make the **delayed test** (≥1 week) the primary endpoint; treat any immediate-test gain as suggestive only, given the learning-vs-performance asymmetry.
4. **What would change the recommendation:** Direct evidence that interleaving's incremental benefit *over Anki's existing spacing* is near zero (a well-powered equivalence result) would shift the ship decision to worked examples; evidence that your users are already high-mastery (expertise reversal) would also down-weight worked examples specifically.

---

## Caveats
- The standout interleaving effect (d = 0.83) is from 7th-grade classroom math, not adult GRE test-takers, and is partly a spacing effect; generalization to your population and to an already-spaced app is an inference, not a measurement.
- The testing-effect and worked-example far-transfer literatures are genuinely contested (Pan & Rickard vs more optimistic accounts; Wittwer & Renkl's near-zero transfer finding); I have reported both sides rather than picking the rosier estimate.
- Spacing's large applied effects are mostly verbal-material and require long retention intervals — structurally hard to test or even implement meaningfully in a 1-week window.
- Power numbers assume a two-sided paired t-test with normal difference scores; a mixed-model analysis that properly models sequence/period will have somewhat different effective power, and real attrition will erode it further.

**One-line verdict:** Ship interleaving — the best evidence-to-effort ratio of any increment over an Anki baseline — but pre-register the ablation as an underpowered estimation pilot with a delayed primary endpoint and TOST equivalence testing, because a realistic incremental effect (dz ≈ 0.3) is **not** reliably detectable in a 1-week small-n window (which would require roughly 90 learners).
