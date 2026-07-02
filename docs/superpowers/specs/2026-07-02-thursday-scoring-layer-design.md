# Thursday — Scoring Layer (Performance + Readiness) — Design Spec

> Build the two harder scores on top of the shared engine: **Performance** (P(correct) on a new,
> unseen exam-style item) and **Readiness** (a projected GRE 200–990 score, always a **range** with a
> full evidence panel and a give-up rule). Ships as a standalone, pure-Python **`scoring/`** package
> consumed by a thin desktop adapter, with the three scores computed **desktop-authoritatively**,
> written to a **synced `col.conf` "score card,"** and rendered **read-only on the phone** — so
> AnkiDroid shows all three scores now (pulling PRD Friday item forward). Validated on a **hybrid**
> attempt set (simulated students for calibration curves + a small real self-answered anchor), with an
> honest "predictive validity unestablished at n≈1." **No engine change → fast lane.** Companion to
> `docs/PRD.md` (§4/§7/§9, D2), `docs/execution-plan.md` (Thursday), the W2 dashboard
> (`anki/qt/aqt/gre/`), and the content-generation spec (eval bank + MCQ surface). Dated 2026-07-02.

## Decisions (locked with owner, 2026-07-01)

- **Attempt data = hybrid.** Simulated students (known latent ability) generate attempts on the eval
  bank to fit/calibrate the full pipeline and draw a real calibration curve; PLUS a small real
  self-answered set as a sanity anchor and the first calibration-log entries. Score card is labeled
  honestly: *"simulated (S students) + N real; predictive validity unestablished at n≈1."*
- **Item difficulty = authored single parameter (`b`), imported/firewalled.** Baked into each eval
  item at creation, fixed before any attempt — never estimated from the student being validated on.
- **Code home = standalone pure-Python `scoring/` package** (no Qt/engine deps), consumed by a thin
  in-app adapter in `anki/qt/aqt/gre/` and by offline eval/calibration scripts.
- **Readiness anchors = the real published ETS GRE Math Subject Test percentile→scaled-score table**,
  vendored + cited in `scoring/data/`, interpolated between anchors. (If any exact value can't be
  sourced at build time, flag it in the PR and use a clearly-labeled normal-approximation for that gap.)
- **Phone shows all three scores now** (Approach A): desktop computes → synced `col.conf` score card →
  AnkiDroid renders read-only. One source of truth; no model duplication.

## Global constraints

- **No engine/collection-schema change → fast lane.** Nothing under `anki/rslib/`, no `.proto`, no FFI,
  no submodule pin bump. The Qt adapter and AnkiDroid panel are **UI-only**; writing the score card uses
  the existing backend `set_config`/`get_config` API. (The W1 mastery RPC stays read-only.)
- **Never blend the three scores.** Memory, Performance, Readiness are always shown separately, each
  with a range. (PRD D2 / AGENTS.md ceiling.)
- **Never show Readiness without the full evidence panel** (estimate, range, %coverage, confidence,
  last-updated, reasons, best-next topic) and the give-up rule. A bare number is an automatic fail.
- **Firewall difficulty + eval items.** Difficulty is imported/authored; train/test never share items;
  the study deck and the authored eval bank never mix (PRD §12).
- **Honesty over flattery.** At n≈1 report wide intervals + "no track record yet." Calibration metrics
  are explicitly labeled as validated on simulated data.
- **Re-runnable.** Fixed seeds, pinned deps, one documented command, deterministic output.
- **Spec dependency:** real validation consumes the **eval bank** (authored `b` + P0–P3 partitions) and
  the **MCQ surface** from `docs/superpowers/specs/2026-06-30-content-generation-and-timed-ui-design.md`.
  Scoring is developed against simulated attempts + authored stub items until that bank lands; the plan
  sequences them.

---

## 1. Architecture & data flow

```
   DESKTOP (authoritative)                                     PHONE (read-only display)
   ┌───────────────────────────────────────────┐             ┌──────────────────────────┐
   │ qt/aqt/gre adapter                         │   Anki      │ AnkiDroid 3-score panel   │
   │   gathers: mastery (W1 RPC), coverage,     │   sync      │  reads col.conf           │
   │   attempts (revlog + MCQ), timing          │  (W4)       │  "gre_scorecard"          │
   │            │  calls                        │  ───────►   │  renders Memory /         │
   │            ▼                               │             │  Performance / Readiness  │
   │  scoring/ (pure Python)                    │             │  each w/ range + give-up  │
   │   features → performance → readiness       │             │  "computed on desktop,    │
   │   calibration · scorecard                  │             │   last updated <t>"       │
   │            │  writes                       │             └──────────────────────────┘
   │            ▼                               │
   │  col.set_config("gre_scorecard", json)     │
   └───────────────────────────────────────────┘
```

**`scoring/` package (new top-level, pure Python):**

| Module | Responsibility |
|---|---|
| `scoring/features.py` | Build per-`(student,item)` feature vectors: leaf-topic mastery (from W1 query), authored difficulty `b`, z-scored response time, topic coverage %. |
| `scoring/performance.py` | Logistic regression + **Platt (sigmoid) calibration**; bootstrap predictive interval (B≈1000) for honest width at n≈1. `predict_proba(features) -> (p, lo, hi)`. |
| `scoring/readiness.py` | Poisson-binomial raw-correct → ETS percentile → 200–990; **split-conformal** interval (headline) + **Bayesian** posterior (cross-check); give-up gate. |
| `scoring/calibration.py` | Brier, reliability-curve bins, ECE; append to the prospective calibration log. |
| `scoring/simulate.py` | Hybrid harness: simulated students (per-topic ability θ) + real-attempt loader. |
| `scoring/scorecard.py` | Assemble the three-score evidence-panel payload (the synced JSON). |
| `scoring/data/ets_percentiles.json` | Vendored ETS percentile→scaled-score anchors (cited). |
| `scoring/data/calibration_log.jsonl` | Prospective predicted-vs-realized log (appended over time). |

**Adapter (`anki/qt/aqt/gre/`):** extends the W2 dashboard — gathers live inputs, calls `scoring/`,
writes `col.set_config("gre_scorecard", …)`, and renders the three slots + evidence panel on desktop.

**Transport = `col.conf` (not media).** The score card is a small JSON stored via
`col.set_config("gre_scorecard", payload)`. It rides normal collection sync (W4) to the phone and is
readable there via `col.get_config`. Chosen over a media file to avoid media-sync "unused file" quirks
and guarantee phone-readability.

## 2. Performance model — P(correct) on a new item (PRD §7b)

- **Features** (per `(student, item)`): the item's **leaf-topic mastery** (mean FSRS recall and/or
  mastered fraction from the W1 mastery query), **authored difficulty `b`**, **z-scored response
  time**, **topic coverage %**.
- **Model:** logistic regression, then **Platt scaling** (sigmoid calibration) fit on a held-out fold.
  At n≈1 the point estimate is meaningless without spread, so the reported output is a **90% predictive
  interval via bootstrap** over the available attempts (B≈1000 resamples).
- **Output:** `(p_correct, lo, hi)` per item, and an aggregate per topic for the dashboard.
- **Firewall:** difficulty is authored/imported; the train fold and the validation fold never share
  items; the paraphrase pairs (eval-bank P0–P3) are the held-out probe.
- **Paraphrase go/no-go (harness Thursday, report Saturday):** compare recall-on-original vs.
  accuracy-on-reworded. If Performance ≈ Memory (no gap), surface that Performance is merely copying
  Memory — the honest failure signal PRD §7b/§11 requires.

## 3. Readiness model — projected 200–990 as a range (PRD §7c)

- **Pipeline:** predict `p_correct` over a **taxonomy-weighted (ETS 50/25/25) representative item
  set** → **Poisson-binomial** raw-correct distribution → **percentile** via the vendored ETS table →
  **200–990** scaled score, propagating uncertainty through every step.
- **Interval:** **split-conformal** (from held-out residuals) is the **headline**; a **Bayesian
  posterior** (parameter + Poisson-binomial uncertainty) is the **cross-check**. Output is always a
  RANGE, never a single number.
- **Give-up gate (D2, ALL must hold, else no number):**
  1. ≥ **200** graded reviews,
  2. ≥ **50%** leaf-topic coverage,
  3. conformal interval **width ≤ a pre-declared threshold** (the real gate; 1–2 are proxies). The
     threshold is a named config constant declared **before any run** (e.g.
     `READINESS_MAX_INTERVAL_WIDTH` ≈ 120 scaled-score points, total width; final value set in the
     implementation plan and never tuned to make a number appear).
  When gated off, show the evidence panel only (coverage, reasons, single best-next topic).
- **Evidence panel (PRD §4):** point estimate, likely range, %coverage, confidence indicator,
  last-updated, main reasons, single best next topic. Extends the W2 dashboard's existing
  coverage/give-up rendering (`dashboard_data.py` already emits `<200 reviews` / `<50% coverage`
  reasons — add the interval-width reason).
- **Prospective calibration log:** append `(timestamp, predicted range, realized=null)` to
  `scoring/data/calibration_log.jsonl` on each compute, so predicted-vs-realized can be audited later.

## 4. Hybrid attempt harness (`scoring/simulate.py`)

- **Simulated students:** S students, each with a per-topic ability vector θ drawn from a prior; item
  outcome `~ Bernoulli(σ(θ_topic − b_item))` (Rasch/1PL using authored `b`). Deterministic under a fixed
  seed. Produces enough `(features → outcome)` rows to fit Platt, run the bootstrap, and draw a real
  reliability curve.
- **Real anchor:** a loader for a small self-answered set (`scoring/data/real_attempts.csv`, you fill
  it by actually answering some eval items) — a sanity check + the first calibration-log rows. Optional
  and small; the pipeline runs without it.
- **Firewall:** θ and `b` are the generative truth; the model never sees θ; item-level train/test split;
  eval-bank items never overlap the study deck (already firewalled by the content-gen spec).

## 5. Validation (`scoring/calibration.py`)

- On a held-out split of the simulated attempts: **Brier score**, **reliability curve** (binned
  predicted vs. empirical), **ECE**. Emitted as a metrics JSON (`scoring/out/metrics.json`) that feeds
  Saturday's polished calibration chart. Thursday produces the numbers; Saturday renders the artifact.
- Every metric is labeled **"validated on simulated data (machinery check); real predictive validity
  unestablished at n≈1."**

## 6. Score card + phone panel

- **Schema** (`gre_scorecard` config value):
  ```json
  {
    "version": 1,
    "updated_at": "<ISO-8601>",
    "source": "simulated (S=… students) + N real attempts; validity unestablished at n≈1",
    "memory":      { "estimate": 0.0, "low": 0.0, "high": 0.0, "coverage_pct": 0.0 },
    "performance": { "estimate": 0.0, "low": 0.0, "high": 0.0 },
    "readiness":   { "shown": false, "estimate": null, "low": null, "high": null,
                     "coverage_pct": 0.0, "confidence": "low",
                     "reasons": ["<200 graded reviews", "interval too wide"],
                     "best_next_topic": "topic::…" }
  }
  ```
- **Desktop:** write it after each compute (dashboard open / a "Recompute scores" action).
- **Phone (AnkiDroid):** read `col.get_config("gre_scorecard")`; render three **separated** slots, each
  with its range; Readiness shows the evidence panel (not a number) when `shown=false`; footer stamps
  "computed on desktop, last updated <t>." New Kotlin fragment; **UI-only, fast lane.**

## 7. Testing & re-runnability

- **Python unit tests:** feature assembly; Platt calibration on a fixed synthetic set; percentile
  lookup + interpolation (known anchors); conformal empirical coverage ≈ target on synthetic; each
  give-up condition (reviews / coverage / width) independently; Poisson-binomial correctness; scorecard
  schema validity.
- **Kotlin (host-JVM):** the 3-score panel renders correctly from a fixed scorecard JSON, including the
  give-up (Readiness-hidden) state.
- **Determinism:** fixed seeds; one documented command (`make score-eval`) reproduces `metrics.json` +
  a sample score card byte-stably.

## 8. Lane, risks, dependencies

- **Lane:** fast lane — Python `scoring/` + Qt adapter (UI) + AnkiDroid Kotlin (UI). No engine/Rust/
  proto/submodule-pin change. (Implementation touches the `anki` and `Anki-Android` submodules for the
  UI only; init them in the impl worktree.)
- **Dependencies:** eval bank (authored `b` + P0–P3) + MCQ surface from the content-gen spec — develop
  against simulated attempts + authored stub items until they land; the plan sequences the join.
- **Risks:** (a) tiny real data → honest wide intervals + "no track record"; (b) ETS table sourcing →
  vendor real, flag + normal-approx any missing value; (c) phone UI is new Kotlin work but bounded to
  display; (d) `col.conf` size — the score card is a few hundred bytes, negligible for sync.

## 9. Acceptance criteria

- `scoring/` computes **all three** scores + the evidence panel deterministically from plain inputs.
- Performance produces calibrated `(p, lo, hi)` and **Brier/reliability/ECE** on a held-out simulated
  split.
- Readiness produces a **range** via split-conformal (headline) + Bayesian (cross-check), gated by the
  **3-condition** give-up rule (incl. interval width); never a bare number.
- Desktop writes the synced `gre_scorecard`; the **phone renders a read-only 3-score panel** with
  ranges + give-up state + "computed on desktop, last updated <t>."
- Prospective calibration log is being appended.
- All tests green; `make score-eval` reproduces metrics + a sample score card byte-stably.

## 10. Out of scope (explicitly deferred)

- The polished calibration-chart artifact + written paraphrase-gap results (Saturday).
- The AI card pipeline and any model calls (Friday+).
- Timed exam-pressure mode and MCQ *authoring* (content-gen spec / later).
- Real longitudinal student data / Step-4 external validation (bonus only).
