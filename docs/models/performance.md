# Performance model — "Would you get a new, unseen exam item right?"

> One of **three scores that are never blended** (PRD §7b, D2). Performance is the first bridge Anki
> does not give us: **memory → performance**. Read alongside [`memory.md`](memory.md) and
> [`readiness.md`](readiness.md). Implementation: `scoring/performance.py` (+ `logistic.py`,
> `features.py`); co-located doc `scoring/scoring.md`.

## What it measures

**Performance = P(correct on a *new, unseen* exam-style item)** of a given topic and difficulty.
This is a different question from Memory: recalling a flashcard you have seen many times (Memory) is
not the same as solving a fresh five-option GRE problem (Performance). Performance is scored on the
in-app **MCQ surface** (PRD §8a) — the GRE's native format — so we measure real in-app answers, not a
bolt-on quiz. The **paraphrase test** (below) is the go/no-go on whether Performance is *real* or is
merely echoing Memory.

## Inputs / features

Per `(student, item)`, in the fixed `FEATURE_ORDER`
`("mastery_recall", "difficulty_z", "time_z", "coverage")`:

| Feature | Source | Notes |
|---|---|---|
| `mastery_recall` | per-topic mastery from the **Mastery Query** RPC (PRD §5) | the leaf-topic mean FSRS recall — this is the memory→performance link |
| `difficulty_z` | **imported / authored** item difficulty `b` (1–5), z-scored | **firewalled**: never estimated from the student being scored |
| `time_z` | z-scored response time | |
| `coverage` | % of leaf topics studied | shared taxonomy substrate |

## The math — logistic regression + Platt calibration

1. **Logistic regression** on the attempt set: raw logit `z = w·x + b₀`
   (`LogisticModel.decision`), fit with L2 regularization on a training fold.
2. **Platt (sigmoid) scaling** fit on a **held-out fold**: the calibrated probability is
   `p = σ(a·z + b)`, where `(a, b)` are the Platt parameters (`platt_fit` / `platt_apply`). Platt
   correction turns the raw logit into an *honestly calibrated* probability — the number that says
   "70%" should be right ~70% of the time.
3. **Evaluation:** Brier score + reliability curve + **ECE** on a **leakage-audited, held-out**
   split (train and validation folds never share items).

## How uncertainty is expressed as a range

Output is always `(p, low, high)` — a **90% interval**, never a bare point. The width is the
**analytic logistic standard error** from the **Fisher information**, mapped through the same Platt
transform:

```
se(z) = √( xᵀ Σ x ),   Σ = ( Xᵀ W X )⁻¹,   W = diag( pᵢ(1−pᵢ) )
low, high = σ( a·(z ∓ 1.645·se) + b )
```

This captures **parameter / estimation** uncertainty, so **a single new item still gets a real,
non-zero width** driven by how little the model has learned. This is deliberate: a naive
prediction-bootstrap collapses to width 0 at `n = 1`, which would *look* confident precisely when we
know the least — the opposite of honest. At `n ≈ 1` the interval is (correctly) wide.

## Honesty labels & abstention

- **Difficulty is imported and firewalled** — authored per item, fixed before any attempt, never
  estimated in-house from the student we're validating on. The model never sees the generative
  ability `θ`.
- **"Validated on simulated data (machinery check); real predictive validity unestablished at
  n ≈ 1."** The calibration curves and Brier/ECE numbers are computed against a deterministic
  simulated-student harness (`scoring/simulate.py`) plus a small real self-answered anchor. They
  prove the *machinery* is calibrated, not that it predicts one real student's exam.
- **Paraphrase go/no-go (PRD §7b/§11).** We compare recall-on-original vs. accuracy-on-reworded
  items. If Performance ≈ Memory (no gap), we **surface that Performance is merely copying Memory** —
  the honest failure signal the spec requires — rather than claiming a second, independent score.
  Reported descriptively with Wilson CIs (30×2 pairs is a consistency probe, not a powered test).
- **Never blended.** Performance is displayed as its own score with its own range; it *feeds*
  Readiness but is never averaged into Memory or Readiness.

## Live surface (desktop dashboard)

The calibrated model above is the **eval/research artifact** — it is validated on the
simulated-student harness and answers "P(correct on a new item)" given a trained attempt corpus.
The **desktop dashboard's live Performance slot** shows something narrower and more honest at the
sample sizes a single learner actually produces: the **observed rights-only accuracy** across their
timed Exam Mode items, as a **Wilson range with `n`** (`aqt/gre/dashboard_data.py::observed_performance`,
fed by `load_exam_attempts` from the `gre_exam_results.jsonl` side-file). We deliberately do **not**
fit the logistic+Platt model on one learner's handful of attempts — that would look confident exactly
when it knows least. With no attempts the slot is a give-up state, never a fabricated 0; a number
only ever renders with its range (`CalibrationStrip`). See `docs/codebase/qt.md` (§ Observed
Performance). The synced `gre_scorecard` (Android panel) still reports Performance `not_available`;
carrying observed Performance across sync is a follow-up.

## Give-up rule (context)

Performance has no separate abstention gate, but it is the per-item engine behind Readiness, whose
**give-up rule** (≥ 200 graded reviews · ≥ 50% leaf coverage · conformal interval width ≤ 120
scaled-score points; **a bare readiness number is an automatic fail**) decides whether a score is
shown at all. See [`readiness.md`](readiness.md).

## Where it lives

`scoring/performance.py` (`PerformanceModel.predict` / `predict_interval`, `fit_performance`,
`_fisher_cov`), `scoring/logistic.py` (logistic + Platt), `scoring/features.py`,
`scoring/simulate.py` (hybrid harness), `scoring/calibration.py` (Brier / reliability / ECE). Pure
Python stdlib; deterministic under fixed seeds (`make score-eval`).
