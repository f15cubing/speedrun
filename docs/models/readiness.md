# Readiness model — "What GRE Math Subject score are you likely to get?"

> One of **three scores that are never blended** (PRD §7c, D2). Readiness is the second bridge:
> **performance → a real GRE score**. It is the highest-stakes and most-constrained score: it is
> **always a range with a full evidence panel**, and the app **refuses to show it** without enough
> evidence. **A made-up readiness number is an automatic fail** (PRD §3, AGENTS.md ceiling). Read
> alongside [`memory.md`](memory.md) and [`performance.md`](performance.md). Implementation:
> `scoring/readiness.py`; co-located doc `scoring/scoring.md`.

## What it measures

**Readiness = projected GRE Mathematics Subject Test score on the 200–990 scale**, expressed as a
**range**. It answers "if you sat the exam now, where would you likely land?" — propagating
uncertainty from every upstream step, and gating itself off when the evidence is too thin to be
useful.

## Inputs / features

- Per-item **`p_correct`** from the [Performance model](performance.md), evaluated over a
  **taxonomy-weighted (ETS 50/25/25) representative item set** drawn from the firewalled authored
  eval bank (never ETS items — PRD §12).
- **`reviews`** (graded-review count) and **`coverage`** (% of leaf topics studied) — the give-up
  proxies.
- **Held-out form-level residuals** `|predicted_frac − realized_frac|` for the conformal interval.
- Vendored, **cited + date-stamped ETS percentile → scaled-score anchors**
  (`scoring/data/ets_percentiles.json`).

## The math — Poisson-binomial → ETS percentile → conformal range

1. **Raw-correct distribution.** The `p_correct` values across the item set are combined with the
   exact **Poisson-binomial** PMF (`scoring/poisson_binomial.py`) — the right distribution for a sum
   of *independent, non-identical* Bernoulli trials. The point estimate is the expected fraction
   `exp_frac = mean(pᵢ)`.
2. **Percentile → scale.** `scaled_from_percentile(exp_frac, table)` maps the fraction to a 200–990
   score by **interpolating between the published ETS anchors**.
3. **Uncertainty at the aggregate (whole-exam) level, not per item:**
   - **Aleatoric spread** from the Poisson-binomial: `sd_frac = √(Σ pᵢ(1−pᵢ)) / n` (shrinks ~`1/√n`).
   - **Split-conformal half-width** (the **headline**) from held-out **form-level** residuals, using
     the finite-sample-corrected quantile `⌈(n+1)·0.90⌉ / n` of `|residual|`. Falls back to the
     normal aleatoric band when no residuals are supplied.
   - `half = max(conformal_half, aleatoric_half)` — the range is **never narrower than the exam's own
     noise**. Endpoints: `scaled_from_percentile(exp_frac ± half)`.
   - **Bayesian normal-posterior band = cross-check** (`bayes_low`/`bayes_high`), a second opinion on
     the headline conformal interval.

A well-prepared, high-coverage student can genuinely clear the width gate (e.g. **711 [678–748]**,
width 70); a thin record stays honestly gated.

## How uncertainty is expressed as a range

The output is a dict: `{shown, estimate, low, high, width, reasons, bayes_low, bayes_high, sd_frac}`.
When shown, the UI renders **`estimate [low–high]`** (headline = conformal, cross-checked by the
Bayesian band) — never a lone number.

## The give-up rule (D2 — LOCKED; ALL three must hold, else no number)

Readiness is displayed **only when every condition holds**:

1. **≥ 200 graded reviews**, **AND**
2. **≥ 50% leaf-topic coverage** (≥ 50% of taxonomy leaf nodes have ≥ 1 graded review), **AND**
3. **conformal interval width ≤ `READINESS_MAX_INTERVAL_WIDTH = 120`** scaled-score points.

Conditions 1–2 are **operational proxies**; **condition 3 (interval width) is the real gate**. All
three are **declared before any run and never tuned to make a number appear**. When any condition
fails, `give_up(...)` returns the failing `reasons`, and `project(...)` returns `shown = False,
estimate = None` — the caller renders the **evidence panel only** (coverage map + reasons + single
best-next topic), never a bare number. **A bare readiness number is an automatic fail.**

## The honesty rule — the evidence panel (7 required elements, PRD §7c)

Readiness may not be shown unless it *simultaneously* shows all of:

1. the point **estimate**, 2. the likely **range**, 3. **% of exam topics covered**, 4. a
**"how sure" / confidence** indicator, 5. a **last-updated** timestamp, 6. the **main reasons**, and
7. the **single best next thing to study**.

Example honest display:

```
Projected GRE Math Subject:  ~810   (likely 740–880)
Confidence: low — you've covered 41% of exam topics; no track record yet.
Top driver: strong on single-var calculus;  Biggest gap: real analysis.
Next best study: real analysis → sequences & series.   Updated: 2026-07-05 14:02
```

## Honesty labels

- **"No track record yet."** At `n ≈ 1` the interval reflects **model-internal uncertainty only** —
  *predictive validity is unestablished*. We do not claim the range is empirically validated against
  real GRE outcomes.
- **No public raw→scaled mapping exists.** ETS equates per form; only the retired **GR3768** form is
  public (60/66 → 880, ceiling 970), offered as a clearly-labeled "form-specific" estimator. The
  norm table is **cited and date-stamped in-app, never hard-coded**, because percentiles drift
  annually.
- **Prospective calibration log.** Each compute appends `(timestamp, predicted range, realized=null)`
  to `scoring/data/calibration_log.jsonl` so predicted-vs-realized can be audited later.
- **Never blended.** Readiness is its own score; Memory and Performance feed it but are always shown
  separately, each with its own range.

## Where it lives

`scoring/readiness.py` (`project`, `give_up`, `scaled_from_percentile`, `conformal_halfwidth`,
`fraction_sd`, `READINESS_MAX_INTERVAL_WIDTH`), `scoring/poisson_binomial.py`,
`scoring/data/ets_percentiles.json`. The desktop adapter (`anki/qt/aqt/gre/scoring_adapter.py`)
writes the synced `gre_scorecard`; the phone renders it read-only (PRD §7c / scoring spec §6).
