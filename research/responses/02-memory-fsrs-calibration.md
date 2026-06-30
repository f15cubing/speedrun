<!-- Raw sub-agent response. Captured: 2026-06-29. Round 1. -->
<!-- Prompt: prompts/02-memory-fsrs-calibration.md | Critique: critiques/02-memory-fsrs-calibration.md -->
<!-- Do not edit; this is the source record. -->

# FSRS Memory Model, Calibration, and the Card-to-Exam Gap

**TL;DR**
- FSRS is a well-specified, openly benchmarked recall-probability model: on 349,923,850 held-out Anki reviews (9,999 collections) it beats Anki's default SM-2 on log-loss for 99.6% of users, and its predicted recall probabilities are demonstrably close to observed recall — but that benchmark is run by the FSRS maintainers themselves, and the one 2025 "independent" study (LECTOR) is a simulation-only, AI-authored paper that does not test calibration at all.
- You *can* credibly prove a calibrated card-level memory model on held-back reviews using a time-ordered split, reliability diagrams, ECE, Brier score and log-loss — but one week of one student's data is far below the threshold for stable single-user calibration; FSRS itself historically required ~1,000 reviews before per-user fitting beat population defaults.
- Card-level calibration is necessary but NOT sufficient for an exam-readiness score: P(recall this card)=0.8 does not equal P(answer an unseen exam item)=0.8, because of recognition-vs-recall/transfer gaps; the bridge rests on representative card coverage and on transfer, neither of which calibration evidence establishes.

## Section A — FSRS Model Description

FSRS (Free Spaced Repetition Scheduler) is built on the **DSR three-component model of memory**, derived by Jarrett (Junyao) Ye from Piotr Woźniak's SuperMemo theory and MaiMemo's DHP model. Every card carries three latent variables [high — fsrs4anki wiki "The Algorithm," srs-benchmark README, author-identified maintainers]:

- **Difficulty (D):** a real number in [1, 10] capturing how intrinsically hard the card is; adjusts with review performance with mean-reversion.
- **Stability (S):** a real number in days, defined as the time for retrievability to fall from 100% to 90%. Higher S = slower forgetting. S increases after successful recalls and (after a lapse) is recomputed by a post-lapse-stability formula that converges to an upper limit rather than growing linearly like SM-2.
- **Retrievability (R):** the probability of recalling the card right now, in [0, 1], computed on demand from S and elapsed time t.

**Forgetting-curve form and its evolution.** The probability of recall is computed from a *forgetting curve*. This form changed across versions [high — fsrs4anki/awesome-fsrs wiki, srs-benchmark DeepWiki, primary code]:
- **FSRS v3** used an **exponential** curve, R = exp(ln(0.9)·t/S) (equivalently 0.9^(t/S)).
- **FSRS v4** replaced it with a **power function**, R(t,S) = (1 + FACTOR·t/S)^DECAY with DECAY = −1, FACTOR = 1/9.
- **FSRS-4.5 / FSRS-5** changed to a different power function with **DECAY = −0.5, FACTOR = 19/81** (R = (1 + (19/81)·t/S)^(−0.5)). This "drops sharply before S and flatly after S," fitting data better.
- **FSRS-6** made the curve's flatness a per-user **optimizable parameter (w20, range ~0.1–0.8, usually <0.2)**, so the decay shape differs per user.
- **FSRS-7** (newest) uses fractional intervals and a more complex dual-power-law curve with 8 curve parameters.
In all versions, by construction R = 0.9 when t = S. The power form is justified because a *superposition* of exponential forgetting curves (across items of differing stability) is better approximated by a power function — a point both Expertium and SuperMemo's Woźniak make.

**Parameter set and counts.** FSRS uses a fixed set of trainable weights: **FSRS v3 = 13, FSRS v4 = 17, FSRS-4.5 = 17, FSRS-5 = 19, FSRS-6 = 21, FSRS-rs = 21 (Rust port of FSRS-6 with recency weighting), FSRS-7 = 35** [high — srs-benchmark README parameter column, awesome-fsrs wiki]. The first four parameters (since FSRS-5) are the initial stability values for the four grades (Again/Hard/Good/Easy). The weights govern initial stability, stability growth on success, post-lapse stability, and difficulty updates.

**How parameters are fit.** Default parameters are pretrained on the population (the ~700M-review dataset). A user can then run the **optimizer**, which refits weights to that individual's review history. Fitting is by **maximum likelihood estimation via stochastic gradient descent** (historically with Back-Propagation-Through-Time over each card's review sequence), minimizing the discrepancy between predicted R and the binary recall outcomes [high — Domenic Denicola, Expertium Algorithm.html, fsrs4anki wiki]. Scheduling then inverts the curve: given a user-chosen **desired retention** (default 90%), the next interval is I = (S/FACTOR)·(r^(1/DECAY) − 1).

## Section B — Predictive-Accuracy Evidence Table

The primary evidence is the **open-spaced-repetition/srs-benchmark**, run by the FSRS maintainers (L-M-Sherlock / Jarrett Ye and collaborators). Current dataset: **9,999–10,000 Anki collections, ~727 million reviews total, of which 349,923,850 are used for evaluation without same-day reviews** (an older version used 20k users / ~1.7 billion reviews). Split is by time (TimeSeriesSplit). Metrics: **Log Loss** and **RMSE(bins)** measure calibration; **AUC** measures discrimination. Lower log-loss/RMSE better; higher AUC better. The figures below are author-reported (mean ± 99% CI) [high — srs-benchmark README, full table fetched].

| Algorithm | Params | Log Loss ↓ | RMSE(bins) ↓ | AUC ↑ | Who ran it | Replicated? |
|---|---|---|---|---|---|---|
| RWKV-P (neural) | 2.76M | 0.2773 | 0.0250 | 0.833 | OSR maintainers | No (self-run) |
| LSTM | 8,869 | 0.3332 | 0.0538 | 0.733 | OSR maintainers | No |
| GRU | 503 | 0.3333 | 0.0556 | 0.732 | OSR maintainers | No |
| FSRS-7 | 35 | 0.3437 | 0.0655 | 0.707 | OSR maintainers | No |
| FSRS-rs | 21 | 0.3443 | 0.0635 | 0.707 | OSR maintainers | No |
| FSRS-6 | 21 | 0.3460 | 0.0653 | 0.703 | OSR maintainers | No |
| FSRS-5 | 19 | 0.3560 | 0.0741 | 0.701 | OSR maintainers | No |
| FSRS-4.5 | 17 | 0.3624 | 0.0764 | 0.689 | OSR maintainers | No |
| FSRS-7 default (no per-user fit) | 0 | 0.3629 | 0.0910 | 0.694 | OSR maintainers | No |
| DASH | 9 | 0.3682 | 0.0836 | 0.631 | OSR maintainers | No |
| FSRS v4 | 17 | 0.3726 | 0.0838 | 0.685 | OSR maintainers | No |
| AVG (baseline) | 0 | 0.3945 | 0.1034 | 0.500 | OSR maintainers | No |
| ACT-R | 5 | 0.4033 | 0.1074 | 0.523 | OSR maintainers | No |
| FSRS v3 | 13 | 0.4364 | 0.1097 | 0.661 | OSR maintainers | No |
| HLR (Duolingo Half-Life Regression) | 3 | 0.4694 | 0.1275 | 0.637 | OSR maintainers | No |
| Ebisu v2 | 0 | 0.4989 | 0.1627 | 0.605 | OSR maintainers | No |

SM-2 is not listed with the others because **it was not designed to output probabilities**; its interval must be converted to a recall probability under assumptions, so SM-2 numbers are not strictly apples-to-apples. Practitioner sources report the head-to-head "superiority" (fraction of users for whom FSRS has lower log-loss): per Expertium's Benchmark.html, *"FSRS-6 (with recency weighting) has a 99.6% superiority over Anki SM-2, meaning that for 99.6% of users, log loss will be lower with FSRS-6 than with SM-2. But please remember that SM-2 wasn't designed to predict probabilities."* Against the harder *trainable* SM-2 variant the margin is 97.4% (Expertium, Anki Forums: *"according to the benchmark, FSRS-5 outperforms SM-2 trainable in 97.4..."*). These figures are practitioner-reported and version-dependent [moderate — Expertium Benchmark.html / Anki Forums, author-identified practitioner].

**Key prior work:** Ye, Su & Cao (2022), *A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling* (KDD '22, pp. 4381–4390, doi:10.1145/3534678.3539081) — the peer-reviewed origin (the SSP-MMC scheduler / DHP memory model built on 220M MaiMemo behavior logs), reporting a **12.6% performance improvement over prior methods** [high — ACM DL, ResearchGate]. FSRS itself, as deployed in Anki, has not been the subject of an independent peer-reviewed predictive-accuracy benchmark.

**Independent replication — weak.** The only 2025 "independent" benchmark, **LECTOR** (Zhao, arXiv:2508.03275), is a **simulation-only** study: 100 *simulated* learners over 100 days, with recall outcomes generated by the paper's own forgetting-curve model. It reports a "Success Rate" (proportion of successful recall attempts) of **FSRS 89.6% vs LECTOR 90.2% vs SSP-MMC 88.4% vs THRESHOLD 84.7% vs HLR 76.6% vs ANKI 60.5% vs SM2 47.1%** — but FSRS reached its rate using ~3× more reviews (151,848 vs LECTOR's 50,706 attempts). Critically, it does **not** test calibration (no log-loss, Brier, or reliability diagram), used no real human reviews, released no code/data at submission, had no error bars or confidence intervals, and was submitted to "Agents4Science 2025," an AI-authored/AI-reviewed venue [high — subagent verification of arXiv:2508.03275v1]. It therefore does **not** independently corroborate FSRS's calibration claims; it is at best a simulated scheduling comparison.

## Section C — Calibration-Evaluation Recipe on Held-Back Reviews

**Definition (the goal).** A model is *calibrated* if, among all predictions of probability p, the observed recall rate is p: formally P(Y=1 | p̂ = p) = p for all p (DeGroot & Fienberg 1983; Guo et al. 2017). "When it says 80%, recall is ~80%" is exactly this.

**Step 1 — Split by time, not at random.** Reviews of one card are serially dependent (each review changes future stability). Use **TimeSeriesSplit**: train on older reviews, evaluate on strictly newer ones, never mixing a card's past and future across the boundary. This is exactly what srs-benchmark does and prevents leakage [high — srs-benchmark README; sklearn TimeSeriesSplit].

**Step 2 — Generate predictions.** For each held-out review, record FSRS's predicted R and the binary outcome (1 = recalled, 0 = lapse).

**Step 3 — Scalar proper scores.**
- **Log loss (binary cross-entropy):** −mean[y·ln p + (1−y)·ln(1−p)]. A strictly proper score; lower is better; sensitive to confident wrong predictions.
- **Brier score** (Brier 1950, *Verification of Forecasts Expressed in Terms of Probability*, Monthly Weather Review 78:1–3, doi:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2): mean[(p − y)²], the MSE of probabilistic forecasts; range 0–1, lower better; decomposes into reliability + resolution + uncertainty.

**Step 4 — Reliability diagram (DeGroot & Fienberg 1983; Guo et al. 2017).** Bin predictions, plot mean predicted probability (x) vs observed recall rate (y) per bin. Perfect calibration = the 45° diagonal; points below the line = overconfidence. Attach **binomial confidence intervals** to each bin's observed rate (critical for a single user with sparse bins).

**Step 5 — Expected Calibration Error.** ECE (popularized by Guo et al. 2017, *On Calibration of Modern Neural Networks*, ICML; building on Naeini, Cooper & Hauskrecht 2015 Bayesian-binning work) = Σ_m (|B_m|/N)·|acc(B_m) − conf(B_m)| — the sample-weighted average gap between bin confidence and bin accuracy. Report **Maximum Calibration Error (MCE)** too for worst-case. FSRS's own RMSE(bins) is a domain-specific cousin: it bins on interval length, review count and lapse count, and an RMSE≈0.05 means FSRS is off by ~5 percentage points on average.

**Step 6 — Binning pitfalls.** ECE/reliability diagrams are sensitive to the binning scheme. **Equal-width bins** leave high-confidence bins overpopulated and low-confidence bins nearly empty; **equal-mass (quantile) bins** stabilize per-bin counts. Bin count matters: too few hides miscalibration, too many adds noise. Report results for ≥2 bin schemes, and prefer Bayesian-binning (BBQ, Naeini 2015) or a proper score (Brier/log-loss) as the bin-free anchor since ECE is a biased, non-proper statistic.

**What counts as "calibrated."** Practically: reliability-diagram points lie within their confidence bands of the diagonal across the probability range; ECE small (e.g., a few percent) relative to bin CIs; Brier and log-loss near the model's own resolution limit and not beaten by a recalibrated version. Calibration is necessary but not the whole story — also report **AUC/resolution** (a model can be calibrated yet useless if it predicts everyone's mean).

## Section D — The Recall-vs-Exam-Performance Gap

P(recall this card) = 0.8 is **not** P(answer an unseen exam item on the topic) = 0.8. The gap has named cognitive-science backing:

1. **Recognition vs recall vs problem-solving.** A flashcard typically probes cued recall or recognition of a specific fact in a specific format. Exam items often demand free recall, application, or novel problem-solving. **Morris, Bransford & Franks (1977), "Levels of processing versus transfer appropriate processing"** (J. Verbal Learning & Verbal Behavior 16:519–533) showed memory performance depends on the *match* between encoding and retrieval conditions — rhyme encoding beat semantic encoding on a rhyme test, reversing the usual depth effect. So performance is format-bound: a card mastered in one format does not guarantee performance in another.

2. **Card-level vs construct-level.** Calibration is per-card. An exam measures a *construct* (a topic/skill) sampled by items the student has never seen. A calibrated per-card probability says nothing about coverage of the construct unless the card set representatively samples it.

3. **Memorized fact vs transferable procedure — the transfer problem.** **Barnett & Ceci (2002), "When and where do we apply what we learn? A taxonomy for far transfer"** (Psychological Bulletin 128:612–637, doi:10.1037/0033-2909.128.4.612) catalog 9 dimensions (knowledge domain, physical/temporal/functional/social context, modality, etc.) along which transfer can fail, and conclude that **far transfer is fragile** — evidence for transfer to substantially different contexts is weak and often confounded by hints/instructions (Detterman's critique). Near transfer (similar context) is more reliable; far transfer to complex, educationally-relevant tasks has much weaker support.

4. **What flashcards DO buy you — the testing effect.** Retrieval practice (which FSRS schedules) robustly improves *retention* of the practiced material. **Roediger & Karpicke (2006)** ("The Power of Testing Memory," Perspectives on Psychological Science 1:181–210; and the Psychological Science paper "Test-Enhanced Learning," 17:249–255) established that testing beats restudy on delayed tests. Meta-analyses confirm a medium-to-large effect: **Rowland (2014)** (Psychological Bulletin 140:1432–1463) reports a testing-effect Hedges' g ≈ 0.50, and **Adesope, Trevisan & Sundararajan (2017), "Rethinking the Use of Tests: A Meta-Analysis of Practice Testing"** (Review of Educational Research 87(3):659–701, doi:10.3102/0034654316689306, 217 studies) reports mean g = 0.61 [95% CI 0.58, 0.65] — i.e., the literature's average testing effect spans roughly g = 0.50–0.61. But these are gains on *retention of tested content*; transfer of retrieval practice to *new* problems is smaller (Pan & Rickard 2018 report small-to-medium effects, weakest for problem-solving).

**Implication for the bridge.** Card-level calibration certifies the "Memory" score's internal honesty (80% means 80% recall of *that card*). It does **not** certify that the deck representatively covers the exam construct, nor that recall transfers to exam-format application. The exam-readiness bridge therefore rests on two extra, unverified-by-calibration assumptions: **representative card coverage** of the tested construct, and **transfer** from card format to exam format. Both must be argued/measured separately.

## Section E — Minimum-Data Caveats for Single-User Calibration

- **FSRS's own cold-start threshold.** Historically Anki required **~1,000 reviews** before per-user optimization; lowered to **400** in Anki 24.04, and the minimum was removed in 24.06+ (the optimizer chooses how many parameters to fit based on available data). Below ~1,000 reviews, per-user weights tend to **overfit noise**, and the population defaults are usually better. A maintainer experiment on a forked benchmark suggests optimization can beat defaults from as few as ~16 reviews in the simplest FSRS-4.5 case, but this is not a guarantee of calibration at that size [high — ankitects/anki issue #3094; fsrs4anki tutorial; AnkiWeb FAQ].
- **Calibration needs many *outcomes per bin*, not just many cards.** A reliability diagram with 10 bins needs enough held-out reviews that each bin's binomial CI is tight (e.g., ~100+ outcomes/bin → CI ≈ ±5–10pp). One week of one student might yield only dozens-to-a-few-hundred *first-time* review outcomes, concentrated in the high-R region (because cards are scheduled at ~90% R), leaving most of the probability axis empty. You cannot estimate calibration where you have no low-probability predictions.
- **Single-user variance & drift.** One user's data is noisy and non-stationary (motivation, content mix, cramming). The benchmark's tight CIs come from aggregating ~10k users; a single user's ECE has wide uncertainty.
- **Does FSRS's advantage survive on small/single-user data?** Largely **no** at cold-start: the calibration advantage is strongest with large data (per-user fit) or borrowed from the large-aggregate default fit. With one week of data you are effectively evaluating the **population-default** model, not a personalized one.

**Counter-critiques to flag.** (1) The benchmark is **run by FSRS's own maintainers** — a selection/conflict-of-interest concern, only weakly mitigated by open code and the absence of strong independent replication. (2) **SM-2 comparison is not apples-to-apples** — SM-2 outputs intervals, not probabilities, so its log-loss depends on the conversion assumptions. (3) The "99.6% beats SM-2" figure is practitioner-reported and version-dependent (97.4% against trainable SM-2). (4) SuperMemo's Woźniak disputes the comparisons, arguing unoptimized FSRS is pitted against optimized SuperMemo, and notes the recall predictions were derived from SuperMemo logs assuming ideal exponential forgetting; a head-to-head awaits a SuperMemo API (claimed for 2026).

## Recommendations

1. **Stage 1 — Adopt FSRS-6/FSRS-rs with population defaults as the "Memory" engine now.** It is the best-justified openly-available recall-probability model and is calibrated in aggregate. Treat the per-card R as an *aggregate-calibrated* estimate, not a personalized one, until the student has data.
2. **Stage 2 — Do not claim a *personally calibrated* memory model on one week of data.** Threshold to revisit: accumulate **≥1,000 reviews with ≥a few hundred distinct cards** before running the per-user optimizer; only then attempt single-user calibration evaluation.
3. **Stage 3 — When data suffices, prove calibration with the Section C recipe:** TimeSeriesSplit, reliability diagram with binomial CIs, ECE (≥2 binning schemes, prefer quantile bins), plus Brier and log-loss as bin-free proper-score anchors. Declare "calibrated" only if diagram points sit within CI of the diagonal and ECE is small relative to those CIs. Benchmark against the recalibrated and AVG baselines.
4. **Stage 4 — Treat exam-readiness as a separate construct.** Do not surface card-level R as an exam-pass probability. Build the bridge explicitly: (a) measure **coverage** (do the cards representatively sample the syllabus/blueprint?), and (b) validate **transfer** by correlating the Memory aggregate against performance on *held-out, exam-format* practice items. The benchmark/threshold that would change the claim: a demonstrated, calibrated relationship between the aggregate Memory score and unseen exam-format item performance for the target population.

## Caveats

- FSRS's predictive-accuracy evidence is strong but **maintainer-run and not independently peer-reviewed**; the 2025 LECTOR paper is simulation-only, AI-authored/reviewed, and does not test calibration.
- All benchmark numbers are point estimates with 99% CIs on aggregate data; **single-user calibration will be far noisier**.
- SM-2 and exam-prediction comparisons rest on conversion/coverage assumptions that should be stated whenever the numbers are cited.
- Cognitive-science effect sizes (testing effect g ≈ 0.50–0.61) describe **retention of tested content**, not transfer to novel exam problems, where evidence is weaker.

**Self-confidence summary.** High confidence: FSRS model internals, version/parameter counts, forgetting-curve forms, the srs-benchmark dataset size (9,999 collections; 349,923,850 evaluation reviews) and metric definitions, the calibration-statistics methodology and its primary sources, and the transfer/testing-effect literature. Moderate confidence: exact SM-2 log-loss figures and the "99.6%/97.4% superiority" figures (practitioner-reported, version-dependent). High confidence that LECTOR does not constitute independent calibration replication.

**One-line verdict.** No — on one week of one student's data you cannot credibly claim a *calibrated* memory model: you can at most rely on FSRS's *aggregate*-calibrated population defaults, and even a defensible single-user calibration proof (let alone an exam-readiness claim, which additionally requires coverage and transfer evidence) needs on the order of a thousand-plus reviews spread across the probability range.
