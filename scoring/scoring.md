# Scoring layer (Performance + Readiness)

> Co-located doc for `scoring/`. Read before changing anything here. Pure-Python,
> dependency-light (stdlib only — the anki pyenv has no numpy/scipy). Computes the two
> harder scores on top of the shared engine; consumed by a desktop adapter that writes a
> synced `col.conf` score card (Task 6) and a read-only AnkiDroid panel (Task 7).

## Purpose

Build **Performance** (P(correct) on a new, unseen exam-style item) and **Readiness** (a
projected GRE 200–990 score, always a **range** with a full evidence panel + give-up rule)
above the FSRS/Memory engine. Validated on a **hybrid** attempt set (deterministic simulated
students + an optional real self-answered anchor), labelled honestly — *"validated on simulated
data (machinery check); real predictive validity unestablished at n≈1."* (PRD §4/§7/§9, D2.)

## Public interface

- `scoring/logistic.py` — `sigmoid(z)`; `LogisticModel` (`fit`, `decision` = raw logit,
  `predict_proba_one`); `platt_fit(scores, y) -> (a, b)`, `platt_apply(a, b, score)`.
- `scoring/poisson_binomial.py` — `pmf(probs)` (exact DP convolution), `expected_and_var(probs)`.
- `scoring/features.py` — `FEATURE_ORDER = ("mastery_recall","difficulty_z","time_z","coverage")`;
  `build_features(item, mastery_by_leaf, coverage, time_z=0.0)`; `zscore(values)`.
- `scoring/simulate.py` — `Attempt`; `simulate_attempts(items, n_students, seed)` (1PL:
  `Bernoulli(sigmoid(θ_leaf − b_z))`, deterministic); `load_real_attempts(csv)`;
  `student_mastery(attempts, student_id)`.
- `scoring/performance.py` — `fit_performance(attempts, mastery_fn, coverage, seed) -> PerformanceModel`;
  `PerformanceModel.predict(item, mastery, coverage) -> p` (Platt-calibrated);
  `PerformanceModel.predict_interval(item, mastery, coverage) -> (point, lo, hi)` (analytic
  Fisher-information SE, so a **single** item gets a real non-zero width).
- `scoring/readiness.py` — `project(probs, table, form_residuals=None, *, reviews, coverage,
  max_width) -> {shown, estimate, low, high, width, reasons, bayes_low, bayes_high, sd_frac}`;
  `give_up(reviews, coverage, width)`; `scaled_from_percentile`; `conformal_halfwidth`;
  `fraction_sd`; `READINESS_MAX_INTERVAL_WIDTH = 120`.
- `scoring/calibration.py` — `brier`, `reliability_bins`, `ece`, `append_log(path, entry)`.
- `scoring/scorecard.py` — `build(memory, performance, readiness, *, source, updated_at)` → the
  `gre_scorecard` JSON payload.
- `scoring/eval_cli.py` — `make score-eval` entry: simulate → student-split → fit (Platt) →
  validate → project Readiness → write `out/metrics.json` + `out/sample_scorecard.json` +
  append `out/calibration_log.jsonl`. Deterministic.
- `scoring/data/ets_percentiles.json` — vendored ETS percentile→scaled-score anchors.

## The uncertainty math (the graded core — PRD §7, 20%)

- **Performance interval = analytic logistic SE.** `se(z) = sqrt(xᵀ Σ x)`, `Σ = (Xᵀ W X)⁻¹`
  (Fisher information, `W = diag(p(1−p))`), mapped through Platt. Captures **parameter/estimation**
  uncertainty, so one new item still yields a real range (a naive prediction-bootstrap collapses to
  width 0 at n=1 — deliberately avoided).
- **Readiness range = aggregate-level, not per-item.** Spread of the exam score *fraction* from the
  **Poisson-binomial** `sd_frac = sqrt(Σ p(1−p))/n` (shrinks ~1/√n) + a **split-conformal**
  half-width from held-out **form-level** residuals `|predicted_frac − realized_frac|` (also shrinks
  with form size). Headline = conformal (floored at the aleatoric band); **Bayesian normal-posterior
  band = cross-check** (`bayes_low`/`bayes_high`). A well-prepared, high-coverage student can clear the
  width gate (e.g. 711 [678–748], width 70); a thin record stays honestly gated.

## Give-up rule (D2 — ALL must hold, else no Readiness number)

≥ **200** graded reviews · ≥ **50%** leaf coverage · conformal interval width ≤
**`READINESS_MAX_INTERVAL_WIDTH = 120`** scaled-score points. Declared before any run; **never tuned
to make a number appear**. When gated, `shown=False`, `estimate=None`, and `reasons` lists why —
the caller renders the evidence panel (coverage, reasons, best-next topic), never a bare number.

## Gotchas & invariants

- **Pure stdlib only** — do NOT add numpy/scipy/sklearn (the anki pyenv has none; re-runnability).
- **Never blend the three scores** — Memory / Performance / Readiness are separate, each with a range.
- **Never show Readiness without the evidence panel** + give-up rule (a bare number is an auto-fail).
- **Difficulty is authored/imported** (`item["difficulty"]`, 1–5) — never estimated from the student
  being scored; the model never sees the generative θ (firewall).
- **Deterministic:** fixed seeds; `eval_cli` uses a fixed timestamp; `make score-eval` is byte-stable.
- **ETS anchors** in `data/ets_percentiles.json` are placeholder-shaped (monotone) — replace with the
  exact published table + citation before any real-score claim (flagged in the PR).
- **Honest at n≈1:** the CLI split is by student and mastery is a documented mild-optimism stand-in;
  every metric is labelled "validated on simulated data … unestablished at n≈1."

## Related tests

`scoring/tests/` (32 tests): `test_logistic.py`, `test_poisson_binomial.py`, `test_features.py`,
`test_simulate.py`, `test_performance.py` (incl. non-degenerate single-item interval + Platt-prob),
`test_readiness.py` (incl. well-prepared-shows-a-range, Bayesian cross-check, conformal coverage),
`test_calibration.py` (incl. `append_log`), `test_scorecard.py`, `test_eval_cli.py` (determinism).
Run: `. .venv-scoring/bin/activate && python -m pytest scoring/tests -q`; end-to-end `make score-eval`.

## Dependencies

- **External:** none (Python stdlib) + `pytest` for tests.
- **Consumes (at integration, Tasks 6–7):** the W1 mastery query (`col.mastery_query`), the W2
  dashboard view-model (`anki/qt/aqt/gre/dashboard_data.py`), the eval bank (`eval/bank/`), and
  `col.get_config`/`col.set_config` for the synced `gre_scorecard`.
- Nothing here touches `anki/` or `Anki-Android/`. Not an engine/Rust change.

## Deferred (documented follow-ups)

- The desktop adapter (Task 6) + AnkiDroid read-only panel (Task 7) that wire the score card into the
  apps (engine-lane PRs).
- Replacing the ETS anchor placeholders with the exact published table.
- The polished calibration-chart artifact + written paraphrase-gap results (Saturday).

---
Last verified against: `agent/thu-scoring-layer` (scoring package @ ea55d81, on `f15cubing/anki` main `8698b1a`)
