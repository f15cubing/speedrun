# 00 — Research Frame: GRE Speedrun

_Role: research orchestrator. This file frames the problem and is the index for the sub-prompts in `/research/prompts/`. It does not answer the questions._

---

## Core research question

Can a small team, in one week, fork Anki and ship a GRE Mathematics Subject Test study app that produces **three separately-reported, evidence-backed scores** (Memory, Performance, Readiness) with **honest uncertainty**, anchored by a **real change in Anki's Rust engine** and a **working desktop+phone shared-engine sync** — and, critically, is the central scientific premise defensible: **that study-derived signals (calibrated memory + topic mastery + difficulty + timing + coverage) can be turned into a projected GRE 200–990 scaled score with a documented method and an honest range, given no longitudinal data?**

## The key assumption that must be tested, not assumed

> **The "bridge" assumption:** that performance on unseen exam-style questions is predictable from study-derived signals, AND that this performance can be mapped onto the GRE 200–990 scale in a way that is more honest than a guess.

This is the single highest-risk premise. If it fails, the project should pivot to *"calibrated memory + transparent give-up rule"* (which the spec says scores higher than a polished-but-unbacked number). Everything else (Rust change, sync, AI gen) is engineering risk; this is *epistemic* risk. Two distinct ways it can fail must each be tested:

1. **No bridge (paraphrase failure):** the performance model just copies the memory model — original-card recall ≈ reworded-question accuracy. The spec's paraphrase test (7d) is designed to catch exactly this.
2. **No scale anchor:** even with a good performance estimate, there is no defensible public mapping from internal accuracy → ETS 200–990 scale without ETS's equating tables / norms. The readiness number may be unfalsifiable in a week.

## Empirical vs. theoretical, up front

Most of what we can establish in a week is **theoretical/methodological** (what method is defensible, what the literature says is possible) plus **internal validation** (calibration on held-back reviews, paraphrase gap, leakage scan). True predictive validity against real GRE scaled scores is **bonus (Step 4)** and almost certainly out of reach. The synthesis must keep these separate.

---

## Steer update (after Round 1) — research weighting

Per direction on 2026-06-29: **weight the next research rounds toward learning science and the olympiad-math-for-GRE hypothesis; treat the codebase track (Anki Rust + sync, SQ5/SQ6) as deferred** (it will be worked on later, hands-on). Codebase prompts remain on file but are not the focus of the next dispatch. A new parallel thread is elevated:

> **Olympiad hypothesis (open empirical question, NOT a premise):** _Can olympiad-style problems effectively prepare a student for the GRE Mathematics Subject Test?_ Per the spec, this must be tested, not assumed. It is decomposed into the spec's five dimensions → SQ8–SQ10 below.

This is itself a transfer question, so it shares a skeptical lens with SQ4: **the burden is on demonstrating *far* transfer to a timed, breadth-heavy, multiple-choice exam — not assuming it.**

---

## Sub-questions

Each sub-question lists: the question, **what a good answer looks like**, and **what would falsify the optimistic case**. Prompt files are named to match.

### SQ1 — GRE Math Subject Test: authoritative content map, structure, scoring norms
`prompts/01-gre-content-coverage.md`
- **Good answer:** the official ETS content outline (every topic + sub-topic), exact format/timing, the raw→scaled (200–990) conversion mechanics and the percentile/norm tables, with primary ETS citations. Enough to build the coverage map (challenge 7c) and to know what the scaled score *is*.
- **Falsifies optimism:** ETS does not publish a stable raw→scaled table or percentile norms (each form is equated separately), meaning any "projected scaled score" is built on shifting sand.

### SQ2 — Memory model: FSRS mechanics, calibration on held-back reviews, and what recall probability does/doesn't mean
`prompts/02-memory-fsrs-calibration.md`
- **Good answer:** precise description of FSRS (DSR model, parameters, how `retrievability` is computed), the correct way to calibrate and measure calibration (reliability diagrams, ECE/Brier, log-loss) on held-back reviews, and named evidence on FSRS predictive accuracy. Clear statement of what recall probability of a *specific card* does NOT tell you about *exam* performance.
- **Falsifies optimism:** FSRS calibration on small single-user data is too noisy to claim "when it says 80%, recall is ~80%"; or recall-probability is conceptually disconnected from exam-question success.

### SQ3 — Performance + Readiness: predicting unseen-question accuracy, the paraphrase/leakage tests, and converting to the 200–990 scale with honest uncertainty
`prompts/03-performance-readiness-scoring.md`
- **Good answer:** a defensible modeling approach (e.g., IRT/item-response, a calibrated classifier, hierarchical/Bayesian estimate with credible intervals) for predicting exam-style accuracy from mastery+difficulty+timing+coverage; a sound paraphrase-test design (7d) that can distinguish "real bridge" from "copying memory"; a leakage-detection method (7e); and a documented, citable method to convert accuracy → 200–990 with a *range* and the give-up rule, plus how to report calibration of the readiness number itself.
- **Falsifies optimism:** no method exists to anchor to the ETS scale without proprietary norms; or honest uncertainty intervals are so wide the number is useless; or the paraphrase gap is ~0 (no bridge).

### SQ4 — Learning-science study feature + a valid one-week ablation
`prompts/04-learning-science-ablation.md`
- **Good answer:** ranked candidate features (interleaving, retrieval practice, spacing, worked-examples, desirable difficulties) with **effect sizes from meta-analyses**, an explicit statement of **transfer distance** to a timed multiple-choice math exam, and a concrete ablation design (full / feature-off / plain Anki) that is statistically meaningful or honestly under-powered, with a pre-registered one-sentence hypothesis.
- **Falsifies optimism:** the strongest-evidence technique shows weak/no *far* transfer to standardized math performance, or no ablation run in a week on few learners can yield an interpretable result (so report it as a null/underpowered design honestly).

### SQ5 — Anki Rust backend change: architecture, feasibility of the three candidates, testing/undo/integrity
`prompts/05-anki-rust-backend.md`
- **Good answer:** a map of `rslib` (scheduler, collection, protobuf/`backend.proto`, undo, storage) with file paths; a feasibility + merge-difficulty ranking of the three candidate changes (points-at-stake queue / topic-aware scheduling / mastery query); the idiomatic way to add a protobuf message and a backend method; how undo and the FSRS scheduler must be respected to avoid corruption; and how to write the ≥3 Rust unit tests + 1 Python integration test.
- **Falsifies optimism:** the lowest-risk candidate still requires invasive scheduler changes that endanger undo/collection integrity within the timeline → pick the safest (likely the read-only mastery query) and say why.

### SQ6 — Shared-engine phone companion + offline sync with documented conflict resolution
`prompts/06-sync-phone-companion.md`
- **Good answer:** how Anki's sync protocol and the Rust engine work across platforms (AnkiDroid / iOS C-FFI), the realistic path to running the *same* Rust engine on phone in a week, how the sync conflict model actually resolves same-card-reviewed-on-both-devices, and how to build the offline→reconnect test (7b) + crash/corruption test (7g) + `make bench` (7h).
- **Falsifies optimism:** running Anki's real Rust engine on a phone with two-way sync is infeasible in the timeline → identify the minimum viable shared-engine path or accept the 70%-ceiling tradeoff knowingly.

### SQ7 — AI card generation: safety, factual accuracy, and the 50-item gold-set quality gate
`prompts/07-ai-card-generation-safety.md`
- **Good answer:** methods to generate math cards from a source with **traceable provenance** (no untraceable claims → AI section zeroed), a gold-set evaluation protocol (50 known-correct pairs, pre-set cutoff), techniques to detect wrong facts / bad pedagogy, how AI gen interacts with the leakage check (7e), and a simpler baseline the AI must beat (Friday milestone).
- **Falsifies optimism:** LLM-generated math cards have a factual-error rate too high to pass a strict gate even with verification, given wrong facts are worse than no card.

---

## Olympiad thread (elevated) — SQ8–SQ10

### SQ8 — Construct comparison: what the GRE Math Subject Test vs. olympiad problems actually measure
`prompts/08-construct-comparison.md`
- **Good answer:** a cognitive task analysis of each — GRE Math Subject (breadth across undergrad curriculum, calculus-heavy, ~2.6 min/item, multiple-choice recognition, speed + fluency) vs. olympiad (deep multi-step reasoning, proof construction, novelty, few problems over long time, pre-calculus-but-hard) — grounded in ETS construct statements and named math-education/competition sources. A clear map of where the constructs **overlap** (problem-solving fluency, algebraic manipulation) and where they **diverge** (proof vs. select-an-answer; breadth vs. depth; pacing).
- **Falsifies optimism:** the constructs barely overlap on the dimensions the GRE actually rewards (speed, breadth recall, MC technique), making olympiad training a poor fit on construct grounds alone.

### SQ9 — Transfer evidence + mechanisms: does olympiad training transfer to GRE-style performance, and how?
`prompts/09-transfer-evidence-mechanisms.md`
- **Good answer:** the actual empirical evidence (or its absence) on whether competition-math training improves performance on timed, curriculum/standardized math assessments; the near-vs-far transfer literature applied to this specific case; and, **if** benefit exists, the specific mechanisms (fluency, comfort with novel/hard problems, reduced test anxiety, faster pattern recognition, stronger algebra) each rated by evidence strength. Named researchers; explicit distinction between empirical findings and plausible-but-untested mechanism stories.
- **Falsifies optimism:** evidence for far transfer from competition math to standardized exam scores is weak/absent or confounded by selection (strong students do both), so the causal claim "olympiad prep raises GRE Subject scores" is unsupported.

### SQ10 — Risks, opportunity cost, and practical sequencing
`prompts/10-olympiad-risks-synthesis.md`
- **Good answer:** where olympiad prep is *inefficient or harmful* for this exam (over-hard problems, breadth/coverage neglect, pacing mismatch, motivation/time sink), with opportunity-cost framing vs. conventional GRE prep; then a concrete, evidence-tagged recommendation on **whether and how** to sequence olympiad-style problems alongside standard prep inside our app (dose, placement, topic-targeting), or a recommendation against it.
- **Falsifies optimism:** the opportunity cost dominates — time on olympiad problems reliably underperforms time on targeted GRE-style practice for this exam, so the feature shouldn't ship as a core study mode.

---

## Anxiety-inoculation thread (Round 3 pivot) — SQ12–SQ14

_Direction on 2026-06-29: research **test anxiety / stress inoculation as a mechanism to prepare students for test day**. This follows the olympiad thread's one positive lead — stress-inoculation had the strongest mechanism-level backing (Saunders et al. 1996) — and is itself a candidate (or rival) for the single learning-science "feature + ablation" slot currently held by interleaving (SQ4)._

> **Core question:** Can a study app meaningfully improve GRE **test-day** performance by reducing test anxiety / inoculating against stress — or is test anxiety mostly a *marker* of under-preparation, such that the highest-yield "anxiety" intervention is simply better content mastery?

> **Key assumption to TEST, not assume:** that test anxiety is a **causal, manipulable** contributor to underperformance on a timed quantitative exam, AND that a brief, app-deliverable intervention can both reduce it **and improve objective scores** — not merely lower self-reported anxiety. The recurring trap (mirroring the olympiad *selection* confound) is the **deficit-vs-interference** confound: anxiety and low scores may share a common cause (poor preparation / low working-memory capacity).

### SQ12 — Does test anxiety *cause* underperformance, and does reducing it raise scores?
`prompts/12-test-anxiety-causal-evidence.md`
- **Good answer:** meta-analytic magnitude of the test-anxiety↔performance relationship (Hembree 1988; von der Embse et al. 2018; for math specifically Barroso et al. 2021, Ashcraft & Kirk), the causal models (interference vs deficit) and which the evidence supports, the degree of confounding by prior ability/preparation/WM, and—critically—whether anxiety-reduction interventions move **objective scores**, not just self-reported anxiety.
- **Falsifies optimism:** the anxiety–score link is largely a proxy for skill/preparation deficits, or interventions reliably reduce self-reported anxiety but **don't move objective scores**.

### SQ13 — Stress inoculation & specific interventions: comparative evidence + mechanisms
`prompts/13-stress-inoculation-interventions-mechanisms.md`
- **Good answer:** ranked candidate interventions (Meichenbaum's Stress Inoculation Training; **arousal reappraisal — Jamieson et al., who used actual GRE quant**; **expressive writing/worry-dump — Ramirez & Beilock 2011, Science**; graded exposure / simulated timed testing; relaxation/breathing; **mindfulness — Mrazek et al. 2013, also GRE**), each with effect size, **transfer to real timed exam scores**, mechanism (Attentional Control Theory — Eysenck; choking/WM — Beilock; challenge-vs-threat — Blascovich/Mendes), and **app-deliverability** (brief & self-administered vs clinician/multi-session).
- **Falsifies optimism:** the best-evidenced techniques require clinician delivery / many sessions and don't survive as a self-administered app feature; brief app versions show null/weak *score* effects or fail replication.

### SQ14 — Operationalization, ablation, and the feature decision (replace/complement interleaving?)
`prompts/14-anxiety-feature-ablation-design.md`
- **Good answer:** concrete app feature designs grounded in SQ13's winners (exam-pressure simulator = literal "inoculation"; pre-session reappraisal microcopy + worry-dump; breathing), an **objective under-pressure outcome** (reuse the SQ11 held-out bank + SQ8 speededness construct) with state-anxiety as a secondary check, a tiny-n-honest **ablation** (reuse SQ4/SQ11 machinery: delayed + under-pressure endpoint, TOST, honest-null), risk analysis (iatrogenic anxiety, placebo/demand, opportunity cost, moderation by trait anxiety), and an explicit **evidence-tagged recommendation**: should anxiety inoculation **replace** interleaving as the shipped feature, **complement** it, or be **deprioritized**?
- **Falsifies optimism:** opportunity cost dominates, the effect is smaller/noisier than interleaving, or the only credible win is the trivial-to-build reappraisal + worry-dump combo (not a differentiating feature).

## Time-criticality vs. milestones

_Status after Round 3: **SQ1–SQ14 all CLOSED**; `SYNTHESIS.md` updated (anxiety thread folded into §0.7, §1 SQ12–14, §2, §4 rec 8b, §5 changelog). The anxiety thread resolved the SQ4 slot question: **interleaving keeps the single ablation slot; anxiety inoculation is an un-ablated complement.** Codebase build deferred per steer. Remaining `[verify]` items are build-time checks, not blockers._

| Sub-question | Status | Gating milestone | Verdict (see SYNTHESIS.md) |
|---|---|---|---|
| SQ1 GRE content/coverage | **CLOSED** (01b resolved the contradiction) | Wed (coverage map) | No public scale map; use © 2025 norms (880→88th); GR3768 60→880 |
| SQ2 Memory/FSRS calibration | **CLOSED** | Wed (memory model) | Aggregate-calibrated only at n≈1; FSRS-6/rs |
| SQ3 Performance/Readiness | **CLOSED** | Fri/Sun (Steps 2–3) | Ship a RANGE + "no track record"; calibrated logistic, not IRT |
| SQ4 Learning-science feature + ablation | **CLOSED** | Sunday (ablation) | **Ship interleaving**; underpowered estimation pilot, delayed endpoint |
| SQ5 Rust backend | **CLOSED; build deferred** | Wed (Rust change) | Read-only mastery query; topics via tags |
| SQ6 Sync + phone | **CLOSED; build deferred** | Fri (sync) | revlog-union + scheduling-LWW; Android-via-rsdroid |
| SQ7 AI card gen | **CLOSED** | Fri (beats baseline) | CAS-verified, asymmetric gate; conceptual-card weakness |
| SQ8 Construct comparison | **CLOSED** | research deliverable | Construct overlap PARTIAL-to-LOW |
| SQ9 Transfer + mechanisms | **CLOSED** | research deliverable | Olympiad→GRE transfer **unproven**; low prior |
| SQ10 Olympiad risks + sequencing | **CLOSED** | research deliverable | **Don't ship as core**; optional strong-student enrichment |
| SQ11 Shared eval item bank | **CLOSED** | infra for 3/4/7 | Author original items; leakage protocol is the keystone |
| SQ12 Test-anxiety causal status | **CLOSED** | research deliverable | Real but small + confounded; causal mainly in prepared high-WM "chokers"; self-report ≫ score |
| SQ13 Inoculation / interventions + mechanisms | **CLOSED** | research deliverable | Reappraisal + timed exposure are top app picks (but fragile); expressive writing demoted; harvest SIT components |
| SQ14 Anxiety feature + ablation | **CLOSED** | feature decision vs interleaving | **COMPLEMENT, not replace**; don't take the ablation slot; simulator justified by speededness |

## Cross-cutting convergences (after Round 1 of SQ1–SQ7)

These recur across multiple independent agents and should anchor `SYNTHESIS.md`:

1. **[strong] No public number-correct→scaled (200–990) mapping exists** (SQ1 + SQ3 independently). ⇒ Readiness must ship as a **range + evidence panel**, never a single number. This is the project's epistemic backbone and aligns perfectly with the honesty rule.
2. **[strong] One week of one student ⇒ aggregate-calibrated memory only; no validated readiness** (SQ2 cold-start ~1,000 reviews + SQ3 n=1 kills in-house IRT). ⇒ The give-up rule is not a limitation to apologize for — it is the scientifically correct posture.
3. **[strong] Transfer is the recurring crux.** Recall→exam (SQ2), far-transfer to novel math (SQ4: Pan & Rickard), and olympiad→GRE (SQ9, pending) are the *same skeptical question*. The **paraphrase test (SQ3/7d) is the empirical instrument** that measures it directly — its result should inform the interleaving *and* olympiad feature decisions.
4. **[strong] Tags are the single shared topic taxonomy** across the Rust mastery query (SQ5), the coverage map (SQ1/7c), and interleaving (SQ4). One `topic::*` taxonomy, four uses. Architectural keystone.
5. **[moderate] Leakage methodology is shared** by the performance model (SQ3) and the AI eval (SQ7) — same layered pipeline (exact→normalized→n-gram→embedding, canaries). Consolidate; do not duplicate.
6. **[contested → resolve in 01b] ETS norm numbers conflict** between SQ1 (N=7,452/676/154, 2019–2023) and SQ3 (N=5,180/680/161, ~2021–2024) — likely annual percentile drift across editions. Pin one edition, date-stamp, never hardcode.

### Strategic decision — RESOLVED (Round 2)
**The single learning-science "feature + ablation" slot → ship INTERLEAVING.** SQ8–SQ10 settled it on the evidence: construct overlap is partial-to-low, olympiad→GRE transfer is unproven with a low prior, and opportunity cost is net-negative for most users. **Olympiad problems are repositioned as an optional, ≤10%, guardrailed, off-by-default enrichment for already-strong students — content to interleave, not the core pedagogy.** This is the "say it plainly when the optimistic premise isn't supported" call. Full reasoning + recommendations in `SYNTHESIS.md` §1 (SQ8–10) and §4 (rec 8, 10).

**CONFIRMED (Round 3):** the anxiety thread (SQ12–14) reached the *same* shape of verdict and did **not** dislodge interleaving. Anxiety inoculation is a **low-cost complement** (reappraisal microcopy + optional worry-dump + optional breathing as un-ablated defaults), and the only differentiating piece — the **exam-pressure simulator** — is justified by the **speededness construct (SQ8)**, not the replication-fragile anxiety literature. The single ablation slot stays with interleaving; an anxiety ablation, if run at all, is a secondary TOST estimation pilot. Full reasoning in `SYNTHESIS.md` §0.7, §1 (SQ12–14), §4 (rec 8b).

## Sequencing note (revised)

**Sequencing note (revised):** The olympiad thread is now the centerpiece. **SQ8 (construct) → SQ9 (transfer/mechanisms) → SQ10 (risks/sequencing)** run in order; SQ8 and SQ9 can be dispatched in parallel since SQ9's transfer scrutiny doesn't strictly require SQ8 first. **SQ4** (in-app learning-science feature) shares transfer literature with SQ9 — keep them coordinated to avoid duplicate citations and to reuse effect sizes. **SQ1→SQ3** dependency stands (coverage + scale feed the readiness model). **SQ5/SQ6 (codebase)** are paused per the steer and will be handled hands-on, not via research prompts, for now.
