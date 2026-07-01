# W2 — Desktop Dashboard (Memory Score + Coverage Map) — Design Spec

> The desktop **read-only dashboard** that turns the merged `StatsService.MasteryQuery` RPC (W1) into
> the honest **Memory score as a range** + the **17-leaf coverage map** (PRD §7/D2, execution-plan
> Wednesday / Milestone 1). The GRE knowledge (taxonomy, ETS bucket weights, statistics) lives in a
> Python view-model *inside the anki fork*; the SvelteKit route is pure presentation; the engine stays
> generic. Companion to `docs/PRD.md` (§6–§7, D2), `docs/execution-plan.md` (Day 2), the W1 spec
> `2026-06-30-mastery-query-engine-design.md`, and the verified insertion points in
> `docs/codebase/qt.md`. Dated 2026-06-30.

## Where this sits (Wednesday decomposition)

- **W1 — Mastery Query (shipped, PR #7):** the read-only engine change this dashboard consumes.
- **W2 — Desktop dashboard (this spec):** Memory score (range) + coverage map on desktop.
- **W3 — Android review:** rebuild rsdroid with our change, run a review session (no dashboard).
- **W4 — Sync foundation:** `anki-sync-server` + conflict-rule smoke test.

## Status at time of writing

W1 is merged: `mw.col.mastery_query(topics)` returns, per requested tag (hierarchical), a
`TopicMastery { topic, total_cards, reviewed_count, mastered_count, avg_recall }`. The seeded deck
(`pipeline/`) carries the frozen `topic::<bucket>::<leaf>` tags. The desktop app builds/runs
(`./run`). No dashboard exists yet — this spec defines it.

## Decisions (locked with owner, 2026-06-30)

- **Memory score = proportion + Wilson interval (no new engine work).** Headline reads as "% of your
  *studied* cards you can reliably recall now" = `mastered_count / reviewed_count`, shown with a
  **Wilson 95% interval** that widens honestly at small samples. `avg_recall` (mean FSRS `R`) is shown
  as secondary context, not the headline. Uses only counts W1 already returns.
- **Exam headline weights buckets 50/25/25** (calculus/algebra/additional) per ETS composition; a
  per-bucket and per-leaf breakdown is also shown. **Never fabricate intra-bucket weights** — within a
  bucket, counts are pooled (PRD §6).
- **Coverage map shows both coverages + per-leaf memory.** Each of the 17 leaves shows deck coverage
  (`total_cards > 0`), studied coverage (`reviewed_count > 0`), and a per-leaf memory mini-range when
  studied. Header shows deck-coverage % and studied-coverage % (studied is the readiness-relevant one).
- **All three score slots render; only Memory is live.** Readiness shows the honest **give-up state**
  ("Insufficient evidence to score" + studied-coverage % + single best next topic); Performance shows
  "Not available yet (Thursday)". This enforces the three-score separation and matches execution-plan
  line 56 ("readiness gated by coverage threshold").
- **Compute in a Python view-model in aqt.** A pure, unit-testable module builds the view-model from
  the RPC counts; the Svelte route only renders. GRE logic lives in one place; the engine stays generic.
- **Vendor the taxonomy into the fork + sync test.** `anki/qt/aqt/gre/taxonomy.json` (source: PRD
  Appendix A) is the dashboard's copy (it cannot import the outer `pipeline/`); an outer-repo test
  asserts it matches `pipeline/taxonomy.py` so it can't drift.
- **Surface = standalone SvelteKit route** `gre-dashboard/` opened from a Tools-menu `QAction`, fed by
  one read-only mediasrv endpoint (Approach A; closest precedent is graphs/deck-options per `qt.md`).

## Global constraints (hard ceilings)

- **Read-only.** All data via a `QueryOp`; the endpoint must never emit `OpChanges` (a fabricated
  `OpChanges` on a read wrongly triggers undo/refresh churn — `qt.md`). We only *call* the existing W1
  read RPC; we add no engine RPC.
- **Never blend the three scores** (PRD §7, AGENTS.md). Memory / Performance / Readiness stay in
  separate slots, each with its own state; no combined "overall" number.
- **Never show a readiness number without the full evidence panel** (PRD §7 Honesty Rule). W2 shows
  **no** readiness number at all — only the "insufficient evidence" gate state — so the ceiling holds
  by construction.
- **Memory is aggregate-calibrated, not personalized** (PRD §7, one-week claim). Microcopy says so; we
  do not claim a personally-calibrated model.
- **Lane.** Fast lane by *risk* (Qt/TS-UI only, read-only; no `rslib`/`.proto`/`pylib` FFI/undo/store
  contact) but executed with the same fork-worktree + `.gitmodules`/gitlink-bump *mechanics* as W1
  because the files live in `f15cubing/anki`. Self-review against the fast-lane checklist; docs +
  submodule SHA bumped in the same PR. If a reviewer judges the submodule surface engine-risky,
  escalate to the engine lane.

---

## 1. Architecture & boundary

```
Tools ▸ "GRE readiness dashboard" (QAction)
        │
        ▼
aqt/gre_dashboard.py (QDialog)  ──loads──▶  SvelteKit route  ts/routes/gre-dashboard/
        │                                          │  (pure presentation)
        │  read-only POST (mediasrv)               │
        ▼                                          │
aqt/gre/dashboard_data.py  ──QueryOp──▶ mw.col.mastery_query(17 leaves + 3 buckets)
        │  (taxonomy + Wilson + 50/25/25 rollup + coverage + next-best)
        └──▶ JSON view-model ────────────────────▶ page render
```

Three isolated units: **presentation** (Svelte), **view-model/statistics** (`dashboard_data.py`,
pure), **transport/UI shell** (`gre_dashboard.py` + mediasrv). Each is independently testable; the
statistics unit has no Qt or DB dependency (it takes RPC rows in, returns a dict out).

## 2. Components & files

All new; minimal contact with upstream files.

| Layer | File | Action |
|---|---|---|
| Taxonomy | `anki/qt/aqt/gre/taxonomy.json` *(new)* | 17 leaves + 3 buckets + 50/25/25 weights (source: PRD Appendix A) |
| View-model | `anki/qt/aqt/gre/dashboard_data.py` *(new)* | pure functions: `wilson_interval(m,n)`, `bucket_rollup`, `headline`, `coverage`, `next_best_topic`, `build_view_model(rows)` |
| View-model pkg | `anki/qt/aqt/gre/__init__.py` *(new)* | package marker |
| Dialog + menu | `anki/qt/aqt/gre_dashboard.py` *(new)* | `QDialog` that loads the route; a `QAction` on the Tools menu wired at an init hook (`main_window_did_init`) |
| Transport | `anki/qt/aqt/mediasrv.py` | register `gre-dashboard` in `is_sveltekit_page()`; add one read-only POST endpoint returning the view-model JSON |
| Presentation | `anki/ts/routes/gre-dashboard/+page.svelte` (+ small components) *(new)* | render headline range, per-bucket bars, coverage grid, the three slots |
| Python tests | `anki/qt/tests/` and/or a pylib pytest | unit tests on `dashboard_data`; mediasrv path/read-only test |
| Sync test | outer repo (`pipeline/tests/` or `tests/`) *(new)* | assert `taxonomy.json` == `pipeline/taxonomy.py` |
| Docs | `docs/codebase/INDEX.md`, `qt.md`, `STATUS.md`, `execution-plan.md` | move dashboard row to Built; bump SHA; check the Wednesday boxes |

**Three-edit rule (`qt.md`):** a SvelteKit page needs route + `is_sveltekit_page()` + Python loader;
missing any one yields a blank webview.

## 3. Data flow (read-only)

1. User opens **Tools ▸ GRE readiness dashboard**; the dialog loads route `gre-dashboard/`.
2. The page POSTs to the mediasrv view-model endpoint. The handler runs a **`QueryOp`** that calls
   `mw.col.mastery_query(<17 leaf tags> + <3 bucket tags>)` — **one call, 20 topics**. Hierarchical
   matching returns the 3 bucket rows already rolled-up and the 17 leaf rows in detail.
3. `dashboard_data.build_view_model(rows)` computes the JSON view-model (below).
4. Svelte renders. No mutation, no `OpChanges`.

**View-model shape (illustrative):**

```json
{
  "generated_at": "2026-06-30T20:00:00Z",
  "memory": {
    "headline": { "point": 0.62, "low": 0.55, "high": 0.69, "reviewed": 140, "total": 300,
                  "mean_r": 0.81, "buckets_reflected": 3, "buckets_total": 3 },
    "buckets": [ { "bucket": "calculus", "weight": 0.50, "point": 0.6, "low": 0.5, "high": 0.7,
                   "reviewed": 90, "total": 150, "mean_r": 0.8 } ]
  },
  "coverage": {
    "deck_pct": 1.0, "studied_pct": 0.41,
    "leaves": [ { "tag": "topic::calculus::integral_single", "bucket": "calculus",
                  "has_cards": true, "studied": true,
                  "memory": { "point": 0.7, "low": 0.55, "high": 0.82, "reviewed": 20 } } ]
  },
  "readiness": { "state": "insufficient_evidence", "studied_pct": 0.41,
                 "next_best_topic": "topic::calculus::series", "reasons": ["<200 graded reviews", "<50% studied coverage"] },
  "performance": { "state": "not_available", "note": "Arrives Thursday (MCQ surface)." }
}
```

## 4. Memory score + range math

Inputs per row: `m = mastered_count`, `n = reviewed_count`, `mean_r = avg_recall`.

- **Per leaf / per bucket:** point `p = m/n`; **Wilson 95% interval** on `(m, n)`:
  `center = (p̂ + z²/2n) / (1 + z²/n)`, `half = z·√(p̂(1−p̂)/n + z²/4n²) / (1 + z²/n)`, `z = 1.96`.
  When `n = 0` there is no interval → the cell is "not studied yet" (contributes to coverage only).
  Bucket rows use the RPC's rolled-up pooled counts directly (no intra-bucket weighting). `mean_r`
  is displayed as secondary context.
- **Headline (exam-level), buckets weighted 50/25/25:**
  `point = Σ wᵢ·pᵢ`; `SE = √(Σ wᵢ²·pᵢ(1−pᵢ)/nᵢ)`; `CI = clamp(point ± 1.96·SE, 0, 1)`.
  A bucket with `nᵢ = 0` is **excluded** and the remaining weights **renormalized** to sum to 1; the
  view-model reports `buckets_reflected` / `buckets_total` and the UI states "headline reflects k/3
  buckets." If all buckets have `n = 0`, the headline is suppressed ("insufficient evidence").
- **Microcopy (honesty):** "aggregate-calibrated (population FSRS defaults), not personalized";
  "n reviewed of m cards"; last-updated timestamp. Example headline phrasing: *"You can reliably
  recall ~62% of what you've studied (95% CI 55–69%); average recall probability 0.81."*

Per-leaf/bucket cells use Wilson (accurate at small n); the headline uses weighted normal-approx
error propagation over pooled bucket proportions (standard for a weighted sum). Both are honest and
require only counts we already have.

## 5. Coverage map

The 17 leaves grouped under the 3 buckets. Per-leaf cell: **has-cards** (`total_cards > 0`, deck
coverage), **studied** (`reviewed_count > 0`), and the per-leaf memory mini-range when studied.
Header: **deck-coverage %** = covered-leaves / 17, **studied-coverage %** = studied-leaves / 17. The
studied-coverage % is exactly the readiness-gate input (PRD D2), pre-wiring Thursday.

## 6. The three score slots (separation enforced)

- **Memory** — live (§4): headline range + per-bucket bars (weights labeled) + secondary mean R.
- **Readiness** — always the **give-up state** in W2: "Insufficient evidence to score" + studied
  coverage % + the **single best next topic** + machine reasons (e.g. "<200 graded reviews",
  "<50% studied coverage"). No number, ever, in W2.
  **Next-best-topic rule (deterministic):** the highest exam-weight **uncovered** leaf (no studied
  reviews), ties broken by bucket weight then taxonomy order; if every leaf is studied, the studied
  leaf with the **lowest memory lower-bound**.
- **Performance** — static "Not available yet — arrives Thursday (MCQ surface)." No number.

## 7. Empty / error states

- **No FSRS memory states / zero reviews:** headline suppressed ("insufficient evidence"); coverage
  map still shows deck coverage; readiness slot shows the gate.
- **Non-FSRS deck:** `avg_recall` is null → treated as `reviewed = 0` for that card.
- **Leaves with no cards:** deck-uncovered; surfaced as the coverage gap and candidate next-best topic.
- **RPC/endpoint error:** the page shows a non-blocking error state; no partial/blended numbers.

## 8. Tests (spec-required)

- **Python unit (`dashboard_data`, pure — feed synthetic RPC rows):**
  1. **Wilson correctness** — known `(m,n)` vs hand-computed bounds; `n=0` → no interval.
  2. **Headline weighting** — 50/25/25 point + SE; a bucket with `n=0` is excluded and weights
     renormalize; `buckets_reflected` correct.
  3. **Coverage** — deck % and studied % over a fixture with covered/uncovered/studied leaves.
  4. **Next-best-topic** — picks the highest-weight uncovered leaf; the all-studied fallback picks the
     lowest memory lower-bound; deterministic tie-breaks.
  5. **Empty collection** — all zeros → headline suppressed, readiness "insufficient evidence".
- **mediasrv:** the endpoint returns valid JSON, is registered in `is_sveltekit_page()`, and is
  **read-only** (asserts no `OpChanges` / undo-stack unchanged around the call).
- **Taxonomy sync (outer repo):** `taxonomy.json` leaves/buckets/weights == `pipeline/taxonomy.py`.
- **Manual:** build the deck, `./run` (fork worktree), study some cards, open the dashboard, confirm
  headline range + coverage map render and update after reviews (the documented playtest path).
- **No new engine tests** — W1 covers the RPC.

## 9. Acceptance

- Tools menu opens a `gre-dashboard` webview showing a **Memory score as a range** (Wilson,
  50/25/25 headline), per-bucket + per-leaf breakdown, and secondary mean R.
- **Coverage map** shows all 17 leaves with deck + studied coverage and header %s.
- **Readiness** slot shows only the honest give-up state (no number); **Performance** slot shows the
  Thursday placeholder; the three scores are never blended.
- All Python unit tests + the mediasrv read-only test + the taxonomy sync test pass; the dashboard
  fetch never emits `OpChanges`.
- `INDEX.md` / `qt.md` / `STATUS.md` / `execution-plan.md` updated; the fork submodule SHA bumped in
  the same PR; ships fast-lane with self-review.

## 10. Out of scope (later)

- **Performance & Readiness models + numbers** (Thursday); the full readiness **evidence panel** with a
  real number.
- **MCQ study surface**, **interleaving**, the **timed exam-pressure mode** (Thursday+).
- **Android dashboard** (W3 is a review session on the shared engine, not a dashboard).
- Desktop **installer packaging**; **personalized** memory calibration (needs ~1,000+ reviews).
