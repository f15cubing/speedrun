# SYNTHESIS — GRE Speedrun research

_Synthesis across Round 1 (prompts 01–07) + Round 2 follow-ups (01b, 08–11) + Round 3 anxiety-inoculation thread (12–14) + Round 4 testing-UI thread (15). Each finding tagged **[strong] / [moderate] / [weak-contested] / [no good evidence]**. Empirical findings are distinguished from theoretical arguments. Bibliography → `sources.md`; raw returns → `responses/`; per-item review → `critiques/`._

**Confidence tag = strength of the underlying evidence, not how sure the sub-agent sounded.**

---

## 0. Headline conclusions (read this first)

1. **The scoring thesis is defensible — but only as ranges, never as a single readiness number.** [strong] There is **no public raw→scaled GRE mapping** (ETS equates each form; only the retired GR3768 form has a public table). Independently confirmed by three returns (01, 03, 01b). → The "honesty rule" and the give-up rule are not constraints to grudgingly satisfy; they are the *correct* design and the highest-scoring posture.
2. **In one week, with ~1 student, you can honestly ship: a calibrated *memory* model (population-default FSRS), a *performance* probability with honest calibration, and a *readiness range* with an explicit "no track record yet" panel — and NOT a validated readiness number.** [strong] Card-level calibration ≠ exam performance; n≈1 cannot calibrate IRT or power the paraphrase test.
3. **The olympiad hypothesis does not survive its own evidence test as a core feature.** [moderate→strong] Construct overlap is partial-to-low (08); there is **no direct evidence** that olympiad training raises standardized timed-MC math scores and the prior for far transfer is low (09); opportunity cost + expertise reversal argue against it for most users (10). **Ship interleaving as the learning-science feature; relegate olympiad problems to an optional, capped, guardrailed enrichment for already-strong students, off by default.**
4. **Author original assessment items.** [strong] All ~431 official ETS released items are long-public and almost certainly in LLM training data → contaminated; reusing them voids the held-out test (01b, 11).
5. **The whole learning-science effect-size base is weaker in *mathematics* than in verbal domains** [moderate] — temper all feature claims (interleaving math g≈0.34, spacing math g≈0.28, testing-in-math g≈0.18 *ns*).
6. **Codebase track (Rust + sync) is sound and deferred per steer:** the safe "real" Rust change is a **read-only mastery query**; the sync conflict model is **revlog-union + scheduling-last-writer-wins**. [moderate, code-confirmed-with-caveats]
7. **Anxiety inoculation is a *complement*, not the headline — and it must NOT take the ablation slot from interleaving.** [moderate→strong] The test-anxiety→score effect is **real but small, partly confounded with under-preparation, and replication-fragile** (12, 13, 14). The honest move: ship the cheap pieces (reappraisal microcopy + optional worry-dump + optional breathing) as **un-ablated defaults**, and build an **exam-pressure simulator justified by the GRE *speededness* construct (SQ8), not the anxiety literature**. The simulator doubles as timed content practice → near-zero replication risk. Interleaving keeps the single pre-registered ablation.
8. **The authentic exam-shell testing UI is a *complement* too — an opt-in "Exam Mode" that gates the *Readiness* score only, not a replacement for the baseline review screen and NOT a second ablation.** [moderate→strong] (15) The one non-confounded win is **ecological validity of the Readiness score** (the real GRE is speeded, rights-only, computer-delivered, and *permits answer review* — Bridgeman 2012; Liu et al. 2015 — so a Readiness estimate produced without review is biased). But the *objective-score* effect of the UI itself is likely **small, confounded with interface familiarity/novelty, and undetectable at tiny n** (math scores are robust to interface — Bridgeman 2003 null for math). Keep the validated minimal-chrome baseline as the default daily loop; the exam shell reuses the SQ14 exam-pressure-simulator sessions and is evaluated as a **secondary interface-validity estimation pilot**, never displacing interleaving's single slot.

---

## 1. Findings by sub-question

### SQ1 — GRE content, format, scoring norms  → **CLOSED**
- Content blueprint (Calc ~50% / Algebra ~25% / Additional ~25%), ~66 five-option items, 2h50m, **rights-only** scoring. **[strong — ETS primary]**
- **No public number-correct→scaled function**; each form separately equated. The only public table is the retired **GR3768** form (verbatim, © 2024 p.35): **60→880, 57–58→860**, ceiling **970**. **[strong — primary, verified in 01b]**
- **Current norms (ETS © 2025, cohort Jul 2021–Jun 2024): Mean 680, SD 161, N 5,180; 880→88th, 860→84th, 800→71st, 680≈50th.** **[strong]** Prompt 1's 676/154/7,452 (2019–2023) is **superseded** — percentiles drift annually; **date-stamp, never hardcode.** [strong]
- The project's "57–58/66 ≈ 880 ≈ 90th" was **wrong on two counts**: GR3768 gives **60→880**, and current norms put **880 at the 88th** percentile. Corrected chain: **~60/66 → 880 → ~88th (assuming GR3768 is representative — a caveat, since it's one retired form).** [moderate]

### SQ2 — Memory model (FSRS) + calibration  → **CLOSED**
- FSRS (DSR model) is the best-justified open recall-probability engine; ship **FSRS-6 / FSRS-rs** (what Anki uses). **[strong]** (A claimed "FSRS-7/35-param" is **unverified — likely spurious**; irrelevant to the recommendation. [weak])
- Benchmark evidence (FSRS beats SM-2 on log-loss for the large majority of users) is **maintainer-run / self-reported**; cite the *direction*, not "99.6%." **[moderate]** The lone "independent" study (LECTOR) is simulation-only, AI-authored, no calibration metrics → **does not corroborate.** [strong critique]
- **On one week of one student's data you have only an *aggregate-calibrated* (population-default) model, not a personalized one** (FSRS historically needs ~1,000 reviews). Calibration recipe is sound: TimeSeriesSplit, reliability diagram + binomial CIs, ECE (≥2 binnings) + Brier/log-loss anchors. **[strong]**
- **Card-level calibration ≠ exam performance** (transfer-appropriate processing — Morris/Bransford/Franks 1977; far-transfer fragility — Barnett & Ceci 2002). The bridge needs *coverage* + *transfer* evidence on top of calibration. **[strong — empirical for the gap]**

### SQ3 — Performance + Readiness  → **CLOSED**
- **Performance model:** with n≈1 examinee, **IRT is infeasible** (needs 100–1,000+ examinees/item). The defensible engine is a **calibrated classifier (logistic + Platt)**, evaluated by **Brier + reliability curve** on a leakage-audited held-out split; a **hierarchical/Bayesian** wrapper is the only principled way to get honest (wide) intervals from sparse data. **[strong — psychometrics/ML standard]**
- **Paraphrase test (the bridge instrument):** the real test is whether Performance predicts *reworded-item* accuracy **better than a memory-only baseline** — not merely original-vs-reworded accuracy. Use paired McNemar **mid-p** + TOST equivalence (±10pp) + paired bootstrap. But **30×2 is underpowered (~12–16% power)** → report as a **descriptive consistency probe with Wilson CIs**, not a significance test (corroborated by 11). **[strong on method; the test itself is weak-by-n]**
- **Readiness → 200–990:** **no defensible anchor without proprietary ETS equating** → honest path = predict raw-correct distribution, map via published percentile anchors, **propagate uncertainty** (conformal interval as headline, Bayesian posterior as cross-check). **Ship a RANGE + evidence panel, never a number.** Give-up rule tied to **interval width / SEM** (principled), with ≥200 reviews + ≥50% coverage as operational proxies. Show a **"no track record yet"** panel — predictive validity is unestablished at n≈1. **[strong]**
- **Leakage detection:** layered exact → normalized → n-gram/Jaccard (>0.7–0.8) → embedding cosine (>0.85–0.9); MinHash+LSH; human-adjudicate the 0.75–0.90 band; publish the residual rate (Yang et al. 2023; Kapoor & Narayanan 2023). **[strong]** (Shared method with SQ7/SQ11 — dedupe into one pipeline.)

### SQ4 — Learning-science feature + ablation  → **CLOSED**
- **Ship interleaving.** It is the only candidate that is a genuine *increment* over Anki (which already does retrieval + spacing) and has direct preregistered far-transfer **math** evidence (Rohrer et al. 2020, classroom d=0.83) plus meta-analytic math support (Brunmair & Richter 2019, **math g≈0.34**). **[strong for the effect; moderate for our setting]**
- **Honest caveat:** the headline d=0.83 is **confounded with spacing**; the realistic *incremental* effect over an already-spaced app is **dz≈0.2–0.35**. [moderate]
- **Ablation is underpowered by design:** detecting dz=0.3 needs ~90 learners; a 1-week tiny-n run is powered only for dz≈0.8. → Pre-register as an **estimation/feasibility pilot**, **delayed test (≥1 wk) as primary endpoint** (Soderstrom & Bjork 2015: immediate tests *underestimate* desirable-difficulty benefits), report **TOST + 90% CIs**, use the honest-null template. **[strong — this is exactly what the spec rewards]**
- Real n is likely team-size (1–5), so the *deliverable is the design + analysis machinery + an honest inconclusive result*, not a significant effect.

### SQ5 — Anki Rust backend  → **CLOSED (deferred build per steer)**
- **Pick the read-only "mastery query"** (new proto message + read RPC + SQL aggregate + pylib binding): a *real* Rust change that is **structurally incapable of corrupting collections or breaking undo** (never enters `transact`), landing on Anki's most stable insertion points. Avoid topic-aware *scheduling* (touches FSRS correctness/undo — highest risk). **[moderate — code-confirmed with some inferred symbols; verify against the pinned release]**
- **Topic metadata via tags** (no schema change; schema bump breaks sync). Tags are the **shared substrate** for coverage map, mastery query, and interleaving. **[strong, architectural keystone]**
- Footguns: the `card.mtime == entry.mtime()` queue assertion; returning `OpChanges` (implies mutation). Tests: ≥3 Rust unit (incl. a read-only-invariant test) + 1 Python integration + `quick_check` corruption assert.

### SQ6 — Shared engine + sync  → **CLOSED (deferred build per steer)**
- **Conflict model (well-sourced, incl. a verbatim Damien Elmes statement):** **revlog entries are unioned** (both reviews survive); **card scheduling state is last-writer-wins** by most-recent answer; **structural divergence forces a one-way full sync** (no field merge). **[moderate-strong]**
- **Construct the conflict demo carefully** — pure review divergence (no notetype/schema edits), or Anki falls back to full-sync overwrite and the demo proves nothing. [strong caution]
- **Feasible path:** Android via AnkiDroid's `rsdroid` (real shared `rslib`, sync works out of the box) + desktop Anki → clears the 70% no-phone ceiling. **iOS-from-scratch in a week is not realistic.** [moderate-strong judgment] Your custom Rust change must flow into the rsdroid build (anki as submodule).

### SQ7 — AI card generation  → **CLOSED**
- **CAS/symbolic verification (SymPy/PAL) is the decisive trust anchor for *computational* cards; model self-critics are supplementary and can introduce/rubber-stamp errors** (Huang et al.; FlipFlop −8% to −34%; RiddleBench). Generator fragility is real (GSM-Symbolic: up to −65% from an irrelevant clause) → verification must be **independent of the generator**. **[strong]**
- **Provenance by schema** (mandatory verbatim source quote + anchor; pipeline-enforced abstention) prevents the untraceable-claim auto-zero. **[strong]**
- **Asymmetric pre-registered gate:** fact-precision ≥0.98 (≤1 wrong-fact card/50) AND useful-yield ≥0.60; n=50 is a **screening gate, not statistical proof** (wide CI). Expect **low yield — that's the correct safe tradeoff.** **[strong on method]**
- **GRE-specific risk [moderate]:** CAS only certifies computational cards, but much of the GRE (abstract algebra, real analysis, number theory) is **conceptual/proof-flavored**; those rest on weaker source-entailment + human adjudication. → **Don't let weakly-verified conceptual cards inflate apparent topic coverage** (interacts with SQ1 coverage map and the readiness honesty rule).
- Beat a **simpler baseline** (template/cloze extraction + non-RAG prompting), McNemar's exact test. [strong]

### SQ8 — Construct comparison (olympiad)  → **CLOSED**
- **Overlap PARTIAL-to-LOW.** [moderate] Shared: algebraic fluency, problem decomposition, pattern recognition, some discrete/number-theory content (the small GRE "additional" band). Divergent (and these dominate the GRE's *scored* variance): calculus breadth, MC selection technique, **speed**. Olympiad's distinctive construct (rigorous proof) is one the GRE format **cannot test**.
- **Format is itself a construct:** speeded MC recognition ≠ untimed proof construction (speededness as a separable latent factor; AIME-vs-USAMO proof gap as illustration). [moderate; cognitive-framework mappings are *theoretical*, not empirical codings]

### SQ9 — Transfer evidence + mechanisms (olympiad)  → **CLOSED**
- **Causal claim "olympiad training raises GRE Subject scores" is NOT empirically supported.** [strong] No direct study exists; the far-transfer prior is low (Thorndike; Barnett & Ceci; Detterman; Sala & Gobet; Owen et al. 2010). The single positive datapoint (Rebholz/Trautwein 2022) is a **quasi-experiment in 9-year-olds**, selection-confounded (training group +1 SD at baseline), transfer significant in **one grade only** — does not generalize to adult GRE. **[weak-contested for any positive claim]**
- **Mechanisms:** strongest *mechanism-level* backing is **anxiety/stress-inoculation** (indirect); "content" channels (schemas/heuristics/fluency) are **near transfer on overlapping topics**, not a far-transfer dividend. **[moderate]** Net: any benefit likely accrues to **already-strong students** via content overlap + reduced test stress.
- Precise framing: *far* transfer of general problem-solving = unsupported; *near* transfer on shared content = plausible. (The brain-training analogy sets a low prior but is *more* distant than olympiad→GRE, so don't read it as "zero.")

### SQ10 — Olympiad risks, opportunity cost, sequencing  → **CLOSED**
- **Don't ship as core.** [moderate-strong] Opportunity cost (specificity + format-matched transfer, Pan & Rickard 2018 d=0.58 when formats match) + expertise reversal (Kalyuga 2003) + desirable-difficulty precondition (Bjork) ⇒ for struggling/short-horizon students olympiad items are an **undesirable** difficulty that crowds out calculus breadth.
- **Defensible narrow role:** opt-in, **≤10% dose**, **already-strong students (~80th pct+) with ≥6 weeks**, topic-targeted to GRE-scored overlap (discrete/NT/probability/sequences), MC-formatted with a ~2.5-min timer (train triage, not slow immersion), **off by default**. Falsifiable ablation with subgroup-harm kill switch. [moderate]
- **Better feature exists:** interleaving + spaced retrieval (converges with SQ4). [moderate]

### SQ11 — Shared held-out eval item bank  → **CLOSED**
- **Keystone = the leakage-isolation protocol, not the items.** [strong] Four disjoint version-locked partitions (P0 frozen held-out / P1 ablation-practice / P2 delayed post-test / P3 paraphrase pairs); project-specific canary GUID; n-gram **and** embedding/LLM-decontaminator scans; difficulty-estimation firewall; **published residual-leakage rate**.
- **Author ~60–100 original blueprint-matched items**; official ETS items are contaminated (converges with 01b). Difficulty is **expert-rated, provisional, noisy (r≈0.6 to truth)** → widens the readiness interval. Every number reported with **Wilson CIs**; difficulties flagged provisional. **Pilot-grade only at n≈1.** [strong]

### SQ12 — Does test anxiety *cause* underperformance, and does reducing it raise scores?  → **CLOSED**
- **Correlation is real but small** (general test anxiety r≈−.26, von der Embse 2018; math anxiety r≈−.28, Barroso 2021) → ~7% of variance *before* controls, much of that confounded with ability/WM/preparation. **[strong]**
- **Interference and deficit both operate, in different people.** The decisive nuance: interference/"choking" concentrates in **high-WM, high-ability, *prepared* students** (Beilock & Carr 2005) — the closest profile to a strong GRE-Math candidate — while the **deficit model dominates for the under-prepared** (anxiety is a *symptom* of low mastery). So the anxiety lever is most credible *exactly* for our target user, and is mostly noise for everyone else. **[moderate-strong]**
- **The asymmetry that governs design:** interventions reliably reduce *self-reported* anxiety (g≈−0.64 to −0.76) but barely move *objective* scores (g≈0.28–0.37, publication bias + failed replications). **Self-report win ≠ score win.** **[strong]**
- **Actionable diagnostic:** rule out the deficit first — the **untimed/low-stakes vs timed/high-stakes performance gap** is the signal that anxiety/choking (not preparation) is the live bottleneck. This maps onto the app's three-score architecture: **Memory-high / timed-Performance-low = anxiety flag.** **[strong, product idea]**

### SQ13 — Stress-inoculation & specific interventions: comparative evidence + mechanisms  → **CLOSED**
- **Evidence-to-implementability ranking:** (1) **arousal reappraisal**, (2) **realistic timed simulated testing / graded exposure**, (3) sustained (~2-wk) mindfulness, (4) relaxation/breathing, (5) expressive writing **(demoted)**, (6) full SIT (not app-faithful — harvest *components*), (7) CBM (insufficient). **[strong on the ordering]**
- **Mechanism that actually moves a timed-MC score = WM/attentional protection** (Attentional Control Theory, Eysenck 2007); choking (Beilock & Carr) and challenge-vs-threat (Blascovich/Mendes) explain *why*, not *that*. GRE-Math is WM-intensive → protecting WM under time pressure is the plausible score channel. **[moderate-strong]**
- **Expressive writing demoted** (SSRP failed replication, Camerer 2018; original d≈2.48 is an implausible-magnitude red flag); **brief mindfulness is null** — only the *sustained* 2-wk course transfers (Mrazek 2013). **[strong]**
- **Sharp lens:** *brevity/app-friendliness correlates inversely with replication robustness* — the most scalable interventions are the most fragile. **[strong]**

### SQ14 — Anxiety feature design, ablation, and the slot decision  → **CLOSED (resolves the SQ4 slot question)**
- **COMPLEMENT, do not replace interleaving, and do NOT consume the single ablation slot.** Performance g≈0.28 (Huntley, outliers removed) sits *right at* the detectable threshold (dz≈0.3 needs ~90 learners) → an anxiety ablation at tiny-n is a guaranteed uninterpretable null; two ablated features split power into two nulls. **[strong]**
- **The defensible feature = exam-pressure simulator justified by *speededness* (SQ8) + transfer-appropriate processing, NOT the anxiety literature.** It doubles as content practice → lowest replication risk, in-construct for the GRE. Ship reappraisal microcopy + optional worry-dump + optional breathing as **un-ablated defaults** (near-zero cost, no performance over-claim). **[strong]**
- **Measurement (if ablated at all):** objective **timed, no-pause, delayed (≥1 wk) held-out** score as primary (reuse the SQ11 leakage-isolated bank — reserve a partition for this endpoint); **STAI-state collected *after* performance** as secondary; **CTAS at baseline** as stratifier; anti-demand safeguards (self-report-only win = null on primary). Within-subject crossover + **TOST (±2-item SESOI)** + honest-null template. **[strong]**
- **Falsifiable flip:** elevate to co-primary only if the **high-CTAS top-tertile subgroup** shows a >2-item benefit whose 90% CI excludes zero in a powered follow-up. **[strong]**
- **Replication caveat:** a 2026 multi-institution reappraisal replication (Thormodsæter et al., CBE-LSE) reportedly came back **null on anxiety *and* performance, no moderation** — `[verify]`, but even discounting it, Huntley g=0.28 + Camerer 2018 already carry the "small/fragile" verdict. **This supersedes the relative optimism about reappraisal in 12/13.**

### SQ15 — Testing-UI design, ablation, and the interface decision  → **CLOSED** (Round 4 testing-UI thread)
- **COMPLEMENT, do not replace the baseline review screen, and do NOT create a second ablation.** [moderate→strong] Ship an **opt-in "Exam Mode" (authentic exam shell) that gates the *Readiness* score only**; keep the validated minimal-chrome card-review UI as the default daily loop for Memory (FSRS) and Performance measurement. The pilot uses **one** UI treatment (exam-shell vs baseline); a UI ablation is a *secondary interface-validity estimation pilot* that piggybacks on the SQ14 exam-pressure-simulator sessions — **interleaving keeps the single pre-registered slot** (three ablated features at tiny n = three uninterpretable nulls).
- **The one non-confounded win is measurement validity, not learning.** [strong] The real GRE Math Subject Test is speeded (~2.6 min/item), rights-only, computer-delivered, and **permits answer review/change** — which reliably *helps* scores (Bridgeman 2012; Liu et al. 2015, large-sample GRE). A Readiness estimate produced on a UI that forbids review is therefore *biased*; the exam shell removes that bias. This is an ecological-validity argument, not a "UI boosts scores" claim.
- **The objective-score effect of the UI itself is likely small, familiarity-confounded, and undetectable at tiny n.** [moderate] Mode effects are generally null but larger for *speeded* than power tests (Mead & Drasgow 1993: cross-mode r ≈ .97 power vs .72 speeded) and for *linear* than adaptive forms (Wang et al. 2007); math scores are relatively robust to interface (Bridgeman et al. 2003: screen size hurts *reading*, not math). On-screen countdown-timer evidence in adult high-stakes CBT is **genuinely thin** (He 2024 n=21; Hallez & Vallier 2025 children) → justify the timer on *fidelity*, tag performance claims `[verify]`.
- **Measurement (if evaluated at all):** objective **score + per-item latency** on a delayed, under-pressure timed held-out partition (reuse SQ11 P2) as primary; **SUS** (benchmark 68), **NASA-TLX**, task-time, misclick rate as *secondary/self-report*, collected **only after** the locked objective post-test (a self-report-only "likes the new UI" win = null on primary). Within-subject crossover + **TOST in two units (±2 items AND ±15 s/item)** + honest-null template. [strong]
- **Falsifiable flip:** elevate toward **REPLACE** only if the **first-time digital test-taker** subgroup shows a delayed under-pressure score advantage exceeding the +2-item SESOI with 90% CI excluding zero; flip to **DEPRIORITIZE** if TOST shows equivalence in both units *and* no SUS/TLX advantage. At tiny n the honest expectation is equivalence/inconclusive; the deliverable is the design + honest pilot result. [strong]

---

## 2. Cross-cutting convergences (multiple independent returns agree)

- **No scale anchor → ranges only.** (01, 03, 01b) [strong]
- **n≈1 in one week → aggregate-calibrated memory + descriptive (not powered) validity probes + give-up rule.** (02, 03, 04, 11) [strong]
- **Transfer is the recurring crux**, and the **paraphrase test is the instrument that measures it** — for the performance model *and* for whether interleaving/olympiad benefits are real. (02, 03, 04, 09) [strong frame]
- **Tags = one shared topic taxonomy** for coverage map, mastery query, and interleaving. (01, 04, 05, 07) [strong, architectural]
- **One leakage pipeline** serves performance eval, AI-gen, and the item bank. (03, 07, 11) [strong]
- **Author original items; all official ETS items contaminated.** (01b, 11) [strong]
- **Learning-science effects are systematically weaker in math than verbal.** (04, 10) [moderate]
- **The same tiny-n machinery serves every candidate feature:** delayed held-out primary endpoint + TOST + honest-null template + the leakage-isolated bank now underpin the interleaving ablation, the eval bank, the (optional) anxiety pilot, *and* the (secondary) testing-UI interface-validity pilot. (04, 11, 14, 15) [strong, architectural]
- **"Speededness is a separable, GRE-dominant construct" does triple duty:** it explains low olympiad overlap (08), justifies the exam-pressure simulator (14), *and* grounds the exam-shell UI's ecological-validity framing (15) — all without leaning on the fragile anxiety literature. (08, 14, 15) [moderate]
- **The "already-prepared/high-ability" subgroup recurs:** it's where olympiad near-transfer might accrue (09) *and* where the anxiety/choking lever is most credible (12). Both threads point at the same narrow user, not the median one. (09, 12) [moderate]
- **Self-report ≠ objective outcome** — the anxiety thread's central asymmetry is the same discipline as the scoring thread's "don't trust the comfortable number" *and* the testing-UI thread's "don't trust the SUS score": collect felt-anxiety / usability ratings *after* the locked objective performance, and treat a self-report-only win (feels calmer / "likes the new UI") as a **null** on the primary. (03, 12, 14, 15) [strong]
- **The "COMPLEMENT, don't consume the single ablation slot" verdict recurs across every rival feature:** olympiad (10), anxiety inoculation (14), and now the testing UI (15) each reached the same shape — a guarded complement that does not displace interleaving's one pre-registered ablation. (10, 14, 15) [strong]

---

## 3. What we still don't know  (honest gaps)

- **Whether the readiness number is actually accurate.** [no good evidence] Zero resolved predictions at n≈1; only model-internal uncertainty is quantifiable. Step 4 (validate vs. real students with study history + practice scores) is out of reach this week — say so.
- **Whether interleaving's incremental benefit over Anki's existing spacing is non-zero for adult GRE-math.** [no good evidence in-population] The 1-week pilot will be underpowered; expect an honest inconclusive/TOST result.
- **Whether olympiad practice causally helps any GRE subgroup.** [no good evidence] Requires the ability-matched, format-controlled RCT that we can design but not power.
- **Real per-item difficulty.** [weak] Expert-rated only (r≈0.6); no examinee calibration sample.
- **Whether the AI pipeline clears the strict gate for *conceptual* (non-CAS-verifiable) GRE topics.** [weak] Likely lower yield there; unmeasured until the gold-set runs.
- **Exact current Anki internal symbols / paths** for the Rust change. [moderate] Must be verified against the pinned release before building (deferred track).
- **Whether *any* anxiety intervention raises this app's objective scores.** [no good evidence in-population] The flagship effects are small and replication-fragile (Camerer 2018; the `[verify]` 2026 reappraisal null); our pilot is powered only to return an honest TOST/equivalence result, not a significant gain.
- **Whether the Memory-high / timed-Performance-low gap reliably flags choking vs. mismeasurement** at n≈1. [weak] It's a principled in-app signal but unvalidated on real users this week.
- **Whether the authentic exam-shell UI changes objective scores at all (vs. the baseline review screen), and whether any change is learning-relevant or just interface familiarity.** [no good evidence in-population] The tiny-n pilot is powered only to return a TOST/equivalence result; the credible *a priori* read is small/near-zero and familiarity-confounded, with any real effect concentrated in first-time digital test-takers. Direct countdown-timer evidence in adult high-stakes CBT is `[verify]`/thin.

---

## 4. Recommendations (each tagged to its evidence)

**Scoring & honesty (20% + 20% of grade)**
1. Ship **three separate scores**; Readiness is a **range + evidence panel + "no track record yet"**, gated by interval-width/SEM with ≥200-review/≥50%-coverage proxies. **[strong]**
2. Use **© 2025 ETS norms** (680/161/5,180; 880→88th), **date-stamped in-app**; offer a **GR3768-based** estimator labeled "form-specific, nominal scale, ceiling 970." **[strong]**
3. Memory model = **FSRS-6/FSRS-rs**, presented as **aggregate-calibrated**; prove calibration with the TimeSeriesSplit + reliability-diagram + ECE/Brier recipe *when* enough reviews exist. **[strong]**
4. Performance = **calibrated logistic + Platt** with **imported/firewalled** difficulty; evaluate by Brier + reliability on a **leakage-audited** split. **[strong]**
5. Run the **paraphrase probe** (beat memory-only baseline) but report it **descriptively with Wilson CIs**, not as a powered test. **[strong]**

**Tests & leakage (12% of grade)**
6. Build **one** leakage pipeline (exact→normalized→n-gram→embedding + canaries + residual-rate report) shared by performance/AI-gen/item-bank. **Author original items; exclude all official ETS items.** **[strong]**
7. Stand up the **shared item bank** with 4 disjoint partitions; flag all difficulties provisional. **[strong]**

**Learning-science feature (15% of grade)**
8. **Ship interleaving** (interleave *confusable* GRE problem types via topic tags); pre-register the **estimation pilot** with a **delayed primary endpoint** + TOST + honest-null template. Temper claims (math g≈0.34, incremental dz≈0.2–0.35). **Interleaving keeps the single ablation slot.** **[strong method]**
8b. **Anxiety inoculation = un-ablated complement.** Ship reappraisal microcopy + optional worry-dump + optional paced breathing as defaults (cheap, low-risk, no score over-claim). Build the **exam-pressure simulator justified by speededness (SQ8)** — it doubles as timed practice. Surface these when the app detects a **Memory-high / timed-Performance-low gap.** Only run an anxiety ablation as a clearly-labeled *secondary* TOST estimation pilot (high-CTAS subgroup, ±2-item bound); flip to co-primary only on a CI-excludes-zero subgroup benefit. **[moderate→strong allocation; objective-score evidence weak/fragile]**
8c. **Testing UI = opt-in "Exam Mode" complement, gating Readiness only.** Keep the validated minimal-chrome card-review UI as the default for Memory/Performance; ship an **authentic exam shell** (persistent 2h50m clock, item-navigator grid, flag-for-review, no-pause, **answer review/change permitted** — Bridgeman 2012 / Liu et al. 2015 — deferred feedback) that runs the periodic mock sessions feeding Readiness. Justify it on **Readiness ecological validity + answer-review measurement bias**, secondarily on speededness (SQ8) — **not** on a "UI raises scores" claim. Evaluate it as a *secondary* interface-validity estimation pilot (objective score + latency primary; SUS/NASA-TLX secondary, collected after the locked post-test; TOST ±2 items / ±15 s/item), reusing the SQ14 simulator sessions. **Do not consume interleaving's single ablation slot; do not build two permanent co-equal UIs.** Flip toward *replace* only for first-time digital test-takers on a CI-excludes-zero, >2-item subgroup benefit. **[moderate→strong allocation; objective-score UI effect small/confounded; timer chrome `[verify]`/thin]**

**AI generation (15% of grade)**
9. RAG + **provenance schema** + **CAS verification** for computational cards; **pre-registered asymmetric gate** (fact-precision ≥0.98, useful-yield ≥0.60); route conceptual cards to source-entailment + human adjudication and **don't let them inflate coverage**. Beat a template/cloze baseline. **[strong]**

**Olympiad (the steer — answered on the evidence)**
10. **Do not make olympiad the core feature.** Implement it as an **optional, ≤10%, guardrailed, off-by-default enrichment for already-strong students**, instrumented for an ablation with a subgroup-harm kill switch. Position olympiad problems as **content to interleave**, not a separate pedagogy. **[moderate-strong — and this is the "say it plainly" call]**

**Codebase (deferred per steer; 20% Rust + 10% sync)**
11. When you build: **read-only mastery query** in Rust (topics via **tags**); sync = revlog-union + scheduling-LWW with a deterministic device-ID tie-break; Android-via-rsdroid + desktop; **verify all paths against the pinned Anki release first.** **[moderate]**

---

## 5. Changelog — how conclusions shifted across rounds

- **R1 → R2 (steer):** Reweighted toward learning-science + olympiad; codebase (SQ5/SQ6) parked. Added SQ8–SQ11. Added a source-list requirement to every prompt.
- **ETS norms — CORRECTED:** R1 prompt 1 gave 676/154/7,452 (880→90th). R2 (01b) proved these **superseded**; **current = 680/161/5,180 (880→88th)**. The two earlier returns (1 vs 3) didn't actually disagree on the world — they read **different annual editions**; 3 was current, 1 was stale. Net: trust the © 2025 numbers; treat percentiles as drifting.
- **"57–58/66 ≈ 880 ≈ 90th" — CORRECTED twice:** GR3768 gives **60→880**, and 880 is now the **88th** percentile.
- **Olympiad — moved from open question to a *soft no for core use*:** R2 (08+09+10) found partial-low construct overlap, no direct transfer evidence, and net-negative opportunity cost for most users. The optimistic premise is **not supported**; defensible role narrowed to optional strong-student enrichment.
- **Learning-science feature — sharpened:** from "pick one technique" to "**interleaving specifically**, because retrieval+spacing are already in Anki," with the added caution that **math-specific effect sizes are weak** across the board.
- **Item strategy — hardened:** from "build a held-out set" to "**author original items; all official ETS items are contaminated**" (01b + 11 converged).
- **FSRS — narrowed:** dropped the unverified "FSRS-7" claim; pinned to FSRS-6/FSRS-rs; reframed benchmark numbers as maintainer-reported.
- **R2 → R3 (steer):** Pivoted to **anxiety inoculation** (SQ12–14). Verdict: the test-anxiety→score lever is **real but small, confounded, and replication-fragile** → ship it as a **low-cost complement**, not the headline, and **don't let it take interleaving's ablation slot**. The exam-pressure simulator is re-justified on the **speededness construct (SQ8)** rather than the anxiety literature.
- **Reappraisal — tempered within R3:** prompts 12 and 13 leaned on Jamieson's GRE result (d≈1.0, n≈28); prompt 14 brought the meta-analytic d≈0.23 (Bosshard & Gomez 2024) + a `[verify]` 2026 multi-site **null** replication (Thormodsæter et al.) → **plan for ~0 to small, not large.** 14 supersedes 12/13 on this point.
- **R3 → R4 (steer):** Opened the **testing-UI thread** (SQ15). Verdict mirrors the olympiad and anxiety threads: the authentic exam-shell UI is a **COMPLEMENT** (opt-in "Exam Mode" gating Readiness only), not a replacement for the baseline review screen and **not a second ablation**. The one non-confounded win is **Readiness ecological validity** (real GRE permits answer review — Bridgeman 2012 / Liu et al. 2015), not a "UI raises scores" effect; the objective-score effect is expected small/familiarity-confounded and undetectable at tiny n. The UI pilot reuses the SQ14 simulator sessions and the SQ11 bank; **interleaving keeps the single pre-registered ablation.**

_Stopping criterion: SQ1–SQ15 closed. R2 resolved the only hard contradiction; the olympiad (R2), anxiety (R3), and testing-UI (R4) threads all reached stable, evidence-backed "complement-not-core / don't-take-the-ablation-slot" verdicts. Remaining unknowns are empirical (require real students/longitudinal data), not resolvable by more literature search. Open `[verify]` items (2026 reappraisal replication; a few R3 author attributions; R4 countdown-timer + van der Linden erratum + recent UI cites) are build-time checks, not blockers._
