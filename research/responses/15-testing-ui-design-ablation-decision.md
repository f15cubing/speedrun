<!-- Raw sub-agent response. Captured: 2026-06-30. Round 4 (testing-UI thread). -->
<!-- Prompt: prompts/15-testing-ui-design-ablation-decision.md | Critique: critiques/15-testing-ui-design-ablation-decision.md -->
<!-- Do not edit; this is the source record. -->
<!-- Filing note: the source was authored as the "14-role" of a testing-UI triad; its H1 ("Sub-Prompt 14") was renumbered to Sub-prompt 15 to fit this repo's slot. Its upstream "sub-prompt 12/13" inputs (UI→validity evidence; UI interventions/deliverability) are assumed in hand and not separately filed. All substance, claims, and sources are unchanged. -->

# Sub-prompt 15 — Testing-UI Design Specification, Ablation Design, Risk Analysis, and the Interface (REPLACE / COMPLEMENT / DEPRIORITIZE) Decision

**Bottom line:** The proposed authentic exam-shell UI should **COMPLEMENT** the baseline Anki-fork review screen as an opt-in "Exam Mode" gating the Readiness score only — not replace the daily practice loop — because the ecological-validity gain is real and cheap, but the measured objective performance effect is likely small, plausibly confounded with interface familiarity/novelty, and undetectable at the pilot's tiny n.

## TL;DR
- The mode-effect and interface literature says a faithful exam shell most credibly improves the **ecological validity** of the Readiness score (matching the real speeded, rights-only, computer-delivered GRE Math Subject Test), but is unlikely to move objective scores by a detectable, non-confounded amount at tiny n.
- Keep the deliverable honest: a pre-registered estimation/feasibility pilot with a delayed under-pressure endpoint, TOST equivalence bounds in raw-score and latency units, and strict separation of objective score/latency from self-report usability (SUS, NASA-TLX).
- The recommendation flips toward REPLACE only for the subgroup of **first-time digital test-takers**, where interface unfamiliarity is a genuine construct-irrelevant threat the exam shell can neutralize.

## Key Findings
- **Mode effects are generally null but larger for linear than adaptive tests, and materially larger for speeded tests.** Wang, Jiao, Young, Brooks & Olson (2007) meta-analysis found no statistically significant computer-vs-paper administration effect on K–12 math, with differences larger for linear than adaptive tests. Mead & Drasgow (1993, *Psychological Bulletin* 114(3):449–458) meta-analyzed 159 corrected correlations (123 power, 36 speeded) and estimated "the cross-mode correlation was estimated to be .97 for timed power tests but only .72 for speeded tests" — a ~0.25 gap that is directly relevant because GRE Math is speeded (~2.6 min/item).
- **On-screen timer evidence is thin and mixed, not clearly harmful.** He (2024, *Frontiers in Psychology* 15:1369920, n=21 undergraduates) found a visible clock produced faster reaction times (F(2,60)=4.588, p=0.014) with no accuracy difference. Hallez & Vallier (2025, n=44 children) found a visible timer lowered anticipatory anxiety with no performance change. No direct experimental study isolates a persistent countdown clock in adult high-stakes CBT — a genuine gap that limits any strong claim about timer chrome.
- **Answer review/change reliably helps and should be allowed.** Bridgeman (2012) reanalysis found an overwhelming majority of students improved after changing answers; Liu et al. (2015) on the GRE revised General Test (n≈8,538 Quant / 9,140 Verbal) confirmed a net benefit that increases with ability. Van der Linden, Jeon & Ferrara (2011) argued the opposite ("substantial losses… for all ability levels") but retracted the empirical basis via erratum (model failed to converge on corrected data).
- **Screen size/scrolling matters for reading, less for math.** Bridgeman, Lennon & Jackenthal (2003, n=357) found smaller screens/resolutions hurt reading scores (~quarter SD) but not math, where little scrolling was required.
- **Time pressure degrades cognitive processing beyond mere speeding.** The Raven's study (PMC10299616) reports "time pressure came with lower confidence and poorer strategy use and a substantial decrease of accuracy (d = 0.35), even when controlling for response time at the item level," and "time pressure disproportionately reduced response times for difficult items and participants with high ability, working memory capacity, or need for cognition." Faithful timing is therefore a construct-relevant stressor to render accurately, not to soften.

## Section A: UI Component Design Table

| Component | Source-evidence (type; confidence) | Placement in session flow | Fidelity to real GRE Math interface |
|---|---|---|---|
| **(a) Authentic exam-shell mode**: persistent countdown timer (2:50:00), item-navigator grid (66 items), flag-for-review, no-pause, answer-locking on final submit | He 2024 (primary lab; Low-Med, indirect); Bridgeman 2012 & Liu et al. 2015 on answer review (primary/large-sample; High); Mead & Drasgow 1993 speeded-test effect (meta-analysis; Med); Wang et al. 2007 mode effects (meta-analysis; High) | Gated "full mock" sessions only; entered deliberately, not the default daily loop | High fidelity IF it mirrors ETS: single-item-at-a-time, review/flag permitted (GRE Math is a linear form allowing navigation), rights-only scoring, one global 2h50m clock, no separately timed sections |
| **(b) Progressive disclosure of difficulty/calibration feedback**: immediate vs deferred | Immediate/delayed feedback roughly equivalent for retention (Kulik & Kulik 1988; Ryan 2024); Van der Kleij, Feskens & Eggen (2015) found "elaborated feedback (EF…) produced larger effect sizes (0.49) than feedback regarding the correctness of the answer (KR; 0.05) or providing the correct answer (KCR; 0.32)" (meta-analysis; High); Bjork desirable difficulties / learning≠performance (Soderstrom & Bjork 2015; High) | **Deferred** during exam-shell mode (no per-item feedback, matching the real exam); immediate *elaborated* feedback in practice mode only, and post-session in exam mode | The real exam gives NO feedback; immediate calibration display during a mock would break fidelity and inflate scores via cueing |
| **(c) Minimal-chrome "flow" mode vs information-dense "dashboard" mode (practice)** | Chandler & Sweller split-attention & extraneous cognitive load (primary/textbook; High); Bjork friction-vs-desirable-difficulty distinction (High) | Flow mode = default FSRS card review (minimal chrome, preserves Memory/Performance measurement); dashboard mode = optional post-session review of the three scores + CIs | Neither maps to the exam; both are practice affordances. Chrome that adds extraneous load (grids, live analytics) should be absent during item attempts |
| **(d) Mobile vs desktop layout under speeded conditions** | Bridgeman et al. 2003 (screen size hurts reading, not math; primary; High); modern responsive-design studies show near-zero device effect when one item per screen (Med) | Desktop/large-screen recommended and logged for any session feeding Readiness; mobile permitted for practice, flagged in metadata | Math items with diagrams/notation need no-scroll rendering per item; mobile must avoid the scrolling penalty Bridgeman identified. Device is a stratification/covariate, not a free choice for scored mocks |

## Section B: Measurement Plan

**PRIMARY OUTCOME (objective-score/latency, kept strictly separate):** score (rights-only count and Wilson-interval P(correct)) and per-item response latency on a **timed held-out item set** drawn from P2 (post-test partition), administered under the speededness construct (~2.6 min/item pacing). All ~431 released ETS items are training-contaminated and excluded from held-out evaluation. Latency is captured at item granularity from rslib logs. This is the only outcome that can arbitrate the design question; it is never mixed with preference data.

**SECONDARY OUTCOMES (self-report/usability-scale, kept strictly separate):**
- **SUS** (Brooke 1996; 10 items) — benchmarked against the Sauro & Lewis mean of 68 (SD 12.5); interpret as percentile/grade, not percent.
- **Task-completion time and error/misclick rate** — instrumented behaviorally (distinct from item latency; measures interface operation, e.g., mis-taps on the navigator grid).
- **NASA-TLX** (Hart & Staveland 1988; raw/unweighted six subscales) — cognitive-load proxy, especially temporal demand and frustration.

**Contamination controls:** (1) Administer ALL self-report instruments **only after** the objective post-test is complete and locked, never interleaved. (2) Use neutral framing ("rate the interface you used") to blunt demand effects toward liking the novel UI; do not reveal which arm is "new." (3) Counterbalance instrument order (SUS/TLX) to control fatigue. (4) Pre-register that usability data are descriptive/secondary and cannot override a null or negative primary result. (5) Log device type and prior digital-exam familiarity at intake as covariates, not outcomes.

## Section C: Ablation Protocol

**Arms:** (1) New authentic exam-shell UI; (2) Baseline testing UI (current card-review style, minimal chrome, no persistent timer); (3) Plain Anki default review screen.

**Design:** Given tiny n, use a **within-subject** delayed crossover on the *primary* endpoint (each learner sees all arms on parallel, leakage-isolated item subsets from P1/P2, order counterbalanced) to maximize power, while measuring SUS/TLX per arm. Hold constant: item content difficulty (matched partitions, expert-rated), timing rules (identical ~2.6 min/item pacing across arms), scoring (rights-only, Wilson CIs), and feedback timing (deferred in all scored blocks). The only manipulated variable is interface chrome.

**Endpoint:** delayed (≥1 week post-exposure) and **under-pressure** — the scored block runs under authentic speeded conditions so any interface-familiarity advantage is measured where it would matter, and novelty is given time to decay.

**Honest power statement:** Detecting dz ≈ 0.3 needs ~90 learners; the pilot is underpowered for confirmatory inference. It is an **estimation/feasibility** study reporting effect estimates with CIs and TOST equivalence, NOT a significance test. A non-significant difference will not be read as "no effect"; a significant one will not be over-claimed.

**TOST equivalence bounds (pre-registered):** raw-score SESOI = ±2 items (≈±3% of 66; below the smallest score change plausibly meaningful for a Readiness band shift); latency SESOI = ±15 s/item. Equivalence is declared only if the 90% CI falls entirely within both bounds (Lakens 2017). Report both the NHST and TOST outcome regardless of direction (honest-null reporting).

**Pre-registered one-sentence hypothesis:** *"Relative to the baseline review UI, the authentic exam-shell UI produces an objective timed-post-test score and per-item latency that are statistically equivalent (within ±2 items and ±15 s/item) at a delayed, under-pressure endpoint, with any observed difference not exceeding the SESOI."*

**Stratification:** pre-stratify by (a) prior testing-software familiarity (first-time vs experienced digital test-takers) and (b) device type (desktop vs mobile). The literature predicts effects concentrate in the unfamiliar subgroup; report subgroup estimates as exploratory given power limits.

## Section D: Risk Table

| Risk | Mechanism | Mitigation |
|---|---|---|
| **Measurement contamination via familiarity** | Exam-shell raises scores by teaching the interface, not the math — inflating Readiness | Delayed under-pressure endpoint; hold timing/scoring constant across arms; treat familiarity as a stratifier; TOST to bound the score gain |
| **Cognitive-load harm to low performers** | Navigator grid + flags add extraneous load (Chandler & Sweller split-attention), stealing working memory from math under time pressure | Keep item screen minimal (one item, no live analytics); make navigator/flags optional; monitor NASA-TLX and low-scorer subgroup latency |
| **Novelty effect** | Initial engagement/score bump from a new UI decays with exposure. Rodrigues et al. (2022, N=756, 14-week study) found novelty "i) starts to act after four weeks of intervention, ii) lasts for two to six weeks, and iii) diminishes a moderate effect," following a U-shaped pattern before familiarization partially recovers the gain between weeks 6–10 | Delayed endpoint + repeated exposure before scoring; report only post-decay estimates |
| **Opportunity cost** | Engineering the exam shell diverts effort from content/interleaving work with larger evidenced payoff. Pan & Rickard (2018, 192 effect sizes / 122 experiments, N=10,382) found transfer "d = 0.40, 95% CI [0.31, 0.50]"; and "if response congruency held… yielding an estimated effect size of d = 0.58" | Scope exam-shell as a thin opt-in layer over rslib timer/navigation; do not build dual permanent UIs unless the pilot justifies it |
| **Accessibility regressions** | Timer/grid chrome breaks screen readers, harms motor-impaired users (mis-tap on dense grid), and small-screen legibility (Bridgeman 2003) | WCAG audit; keyboard/AT navigation for the navigator; no-scroll per-item math rendering; large tap targets; timer announceable/muteable |
| **Over-claiming from a noisy pilot** | Tiny-n false positive or spurious subgroup effect gets reported as "UI works" | Pre-registration; TOST + honest-null reporting; label subgroup analyses exploratory; deliverable is design + honest result, not a significant effect |

## Section E: REPLACE / COMPLEMENT / DEPRIORITIZE Recommendation

**Recommendation: COMPLEMENT** (opt-in "Exam Mode" gating the Readiness score; baseline review screen remains the default daily loop).

- **Steelman for REPLACE:** A faithful exam shell is cheap given rslib already renders timing/navigation, and it directly improves the *ecological validity* of the Readiness score — the one score explicitly benchmarked to the real 200–990 scaled GRE Math Subject Test under speeded, rights-only, computer-delivered conditions. Answer-review evidence (Bridgeman 2012; Liu et al. 2015) shows the real exam's review affordance materially affects scores, so a Readiness estimate produced without it is biased. *Evidence tag: mode-effect + answer-review literature; High confidence on the validity argument.*
- **Steelman for DEPRIORITIZE:** The measured objective performance effect is likely small, confounded with familiarity/novelty, and undetectable at tiny n; math scores are relatively robust to interface (Bridgeman 2003 null for math), engineering/maintenance of a second UI adds surface area, and content/interleaving work has a larger evidenced payoff (Pan & Rickard 2018 transfer d=0.40). *Evidence tag: mode-effect nulls + cognitive-load + opportunity-cost; Medium confidence.*
- **Resolution — COMPLEMENT:** Maintaining two *permanent, co-equal* UIs is not justified; instead the exam shell is a thin, opt-in mode reusing baseline machinery, invoked for periodic mocks that feed Readiness, while Memory (FSRS) and Performance measurement stay on the validated minimal-chrome default. The pilot uses ONE treatment (exam-shell vs baseline) to respect power.

**Contingent, falsifiable flip conditions:**
- Flips toward **REPLACE** if, in the **first-time digital test-taker subgroup**, the exam-shell arm shows a delayed, under-pressure objective-score advantage that **exceeds the +2-item SESOI** with a CI excluding zero — i.e., the interface removes a construct-irrelevant barrier for those users.
- Flips toward **DEPRIORITIZE** if TOST demonstrates **equivalence within ±2 items and ±15 s/item** AND SUS/TLX show no usability advantage — meaning the shell adds maintenance cost for no measurable objective or experiential benefit.
- At tiny n the honest expectation is equivalence or an inconclusive interval; the deliverable is the design + the honest pilot result, explicitly NOT a claimed significant effect.

## Sources

**Peer-reviewed / meta-analysis**
- Wang, S., Jiao, H., Young, M. J., Brooks, T., & Olson, J. (2007). A Meta-Analysis of Testing Mode Effects in Grade K–12 Mathematics Tests. *Educational and Psychological Measurement*, 67(2), 219–238. https://journals.sagepub.com/doi/10.1177/0013164406288166
- Mead, A. D., & Drasgow, F. (1993). Equivalence of computerized and paper-and-pencil cognitive ability tests: A meta-analysis. *Psychological Bulletin*, 114(3), 449–458.
- Bridgeman, B., Lennon, M. L., & Jackenthal, A. (2003). Effects of Screen Size, Screen Resolution, and Display Rate on Computer-Based Test Performance. *Applied Measurement in Education*, 16(3), 191–205. https://doi.org/10.1207/S15324818AME1603_2
- He, J. (2024). The impact of clock timing on VDT visual search performance under time constraint. *Frontiers in Psychology*, 15:1369920. https://doi.org/10.3389/fpsyg.2024.1369920
- Hallez, Q., & Vallier, V. (2025). Time on Their Side: How Visual Timers Affect Anticipatory Anxiety, Performance, and On-Task Behavior in Elementary Math Assessments. *EJIHPE*, 15(12):243. https://doi.org/10.3390/ejihpe15120243
- van der Linden, W. J., Jeon, M., & Ferrara, S. (2011). A Paradox in the Study of the Benefits of Test-Item Review. *Journal of Educational Measurement*, 48(4), 380–398 (with erratum). https://doi.org/10.1111/j.1745-3984.2011.00151.x
- Bridgeman, B. (2012). A Simple Answer to a Simple Question on Changing Answers. *Journal of Educational Measurement*, 49(4), 467–468. https://doi.org/10.1111/j.1745-3984.2012.00189.x
- Liu, O. L., Bridgeman, B., Gu, L., Xu, J., & Kong, N. (2015). Investigation of Response Changes in the GRE Revised General Test. *Educational and Psychological Measurement*, 75(6), 1002–1020. https://pmc.ncbi.nlm.nih.gov/articles/PMC5965601/
- Pan, S. C., & Rickard, T. C. (2018). Transfer of Test-Enhanced Learning: Meta-Analytic Review and Synthesis. *Psychological Bulletin*, 144(7), 710–756. https://doi.org/10.1037/bul0000151
- Van der Kleij, F. M., Feskens, R. C. W., & Eggen, T. J. H. M. (2015). Effects of Feedback in a Computer-Based Learning Environment on Students' Learning Outcomes: A Meta-Analysis. *Review of Educational Research*, 85(4), 475–511.
- Lakens, D. (2017). Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses. *Social Psychological and Personality Science*, 8(4), 355–362. https://doi.org/10.1177/1948550617697177
- Chandler, P., & Sweller, J. (1992). The split-attention effect as a factor in the design of instruction. *British Journal of Educational Psychology*, 62, 233–246. https://doi.org/10.1111/j.2044-8279.1992.tb01017.x
- Soderstrom, N. C., & Bjork, R. A. (2015). Learning versus Performance: An Integrative Review. *Perspectives on Psychological Science*, 10, 176–199.
- Kulik, J. A., & Kulik, C.-L. C. (1988). Timing of feedback and verbal learning. *Review of Educational Research*, 58, 79–97.
- Rodrigues, L., et al. (2022). Gamification suffers from the novelty effect but benefits from the familiarization effect. *International Journal of Educational Technology in Higher Education*, 19. https://link.springer.com/article/10.1186/s41239-021-00314-6

**Standard / textbook / instrument**
- Brooke, J. (1996). SUS: A "quick and dirty" usability scale. In *Usability Evaluation in Industry*.
- Sauro, J., & Lewis, J. R. (2016). *Quantifying the User Experience* (SUS benchmark mean 68, SD 12.5).
- Hart, S. G., & Staveland, L. E. (1988). Development of NASA-TLX (Task Load Index). In *Human Mental Workload*, 139–183.
- Bjork, E. L., & Bjork, R. A. (2011). Making Things Hard on Yourself, But in a Good Way: Creating Desirable Difficulties to Enhance Learning.

**Primary/secondary (context)**
- ETS. GRE Subject Tests: Content and Structure (66 items, 2h50m, computer-delivered since Sept 2023, scaled 200–990). https://www.ets.org/gre/test-takers/subject-tests/about/content-structure.html
- "Should Intelligence Tests Be Speeded or Unspeeded?" (2023), PMC10299616 (time pressure d≈0.35 accuracy decrement, concentrated in high-ability/WM examinees). https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10299616/

**Self-confidence summary:** High confidence on the ecological-validity argument and on the answer-review and mode-effect literature; Medium confidence on the magnitude/direction of any objective score effect (evidence for adult high-stakes countdown-clock chrome is genuinely thin — one small lab study plus a children's study, no direct adult high-stakes CBT experiment); High confidence that a tiny-n pilot cannot confirm an effect and should report estimation + TOST equivalence honestly.

**One-line recommendation:** COMPLEMENT — an opt-in exam-shell mode gating Readiness only, with the baseline default retained; it flips to REPLACE for first-time digital test-takers if their delayed under-pressure score advantage exceeds the +2-item SESOI (evidence tag: mode-effect + answer-review + first-time-user familiarity).
