# GRE Home page + 70% exam-mode lock — design (2026-07-05)

> Fast-lane (Qt-UI + Svelte + pure view-model; **no** rslib/proto/scheduler change). Makes the app
> friendlier: a landing "Home" that surfaces the three scores + study stats + a one-click "study
> next", and gates the timed Exam Mode behind real topic coverage. Honesty ceilings unchanged.

## Goal

Four asks, all in the presentation layer:

1. **A friendly Home page** with the three key scores (Memory / Performance / Readiness).
2. **A study-stats section** (cards reviewed / topics covered / exam questions answered) — a compact
   section *on the Home* (not a separate page).
3. **A "study next" button** that drops the learner straight into a review session for the single
   best topic to study next.
4. **A 70% lock on Exam Mode** — the timed mock is unavailable until the learner has studied ≥70% of
   the 17 ETS leaf topics (studied coverage = ≥1 graded review per leaf).

## Non-negotiable guardrails (unchanged)

- The three scores stay **separate**; never blended into one number.
- **Readiness is never a bare number** — the Home shows its gated evidence panel / give-up state,
  reusing the dashboard's `ScoreSlot`.
- **Performance is an observed range** (Wilson + n) or an honest "not available" — not the model.
- **Read-only** except two normal, non-corrupting writes: the "study next" filtered deck (a standard
  undoable Anki op) and one `col.conf` flag for the startup toggle (`undoable=False`, like the
  scoring adapter). No read RPC returns `OpChanges`; no Rust/proto/scheduler change.

## Architecture

Reuses the existing "Readout" identity + data:

- **New SvelteKit route** `ts/routes/gre-home/+page.svelte` (imports the dashboard's `tokens.css`,
  `fonts.css`, `CalibrationStrip`, `ScoreSlot`). It fetches the **existing** `greDashboardData`
  (extended, below) and `greExamCapacity` (extended). Layout top→bottom: primary **Study next →
  {topic}** CTA · three compact score cards · a stats strip · quick links (full dashboard · exam
  mode with 🔒/coverage · how-it-differs) · a "Show on startup" toggle.
- **New `AnkiWebViewKind.GRE_HOME`** (webview.py) + api-access allowlist entry + `"gre-home"` in
  mediasrv's sveltekit-page list (the 403 / stale-bundle gotchas from `building-and-testing`).
- **New dialog** `qt/aqt/gre_home.py` (`GreHome(QDialog)`): a webview + `set_bridge_command`.
  Bridge actions (all main-thread): `gre:study` (build/enter the filtered deck), `gre:dashboard`,
  `gre:exam`, `gre:method`, `gre:startup:on|off`. Singleton (reopen focuses the live dialog).
- **Menu + startup**: `Tools ▸ GRE Home`; auto-open once per profile open via `profile_did_open`
  (deferred with a short `QTimer`, guarded on `mw.col`, gated by `gre_home_show_on_startup`, default
  on).

### View-model additions (pure `dashboard_data.py` — unit-tested headless)

- `LEAF_LABELS` + `leaf_label(leaf)` — friendly names (PRD Appendix A), fallback to prettified.
- `studied_coverage(rows, tax) -> {studied, total, pct}`.
- `study_next(rows, tax) -> {tag, bucket, leaf, label, reason} | None` — the best **studyable** topic
  (has cards): highest-weight unstudied leaf, else weakest studied leaf by Wilson lower bound.
- `stats_block(rows, tax, attempts)` — cards reviewed/total, topics covered/total + %, exam questions
  answered, per-bucket reviewed/total. Derived from the same mastery rows + exam side-file; no new
  engine reads. `build_view_model` gains `stats`, `study_next`, and a `label` on each coverage leaf.

### Exam-mode lock (pure `exam.py` + mediasrv)

- `exam.MIN_STUDIED_COVERAGE = 0.70`, `coverage_meets_threshold(...)`, `coverage_lock_reason(...)`.
- `gre_exam_capacity` returns a `coverage` block (studied/total/pct/threshold/unlocked/reason).
- `gre_exam_form` enforces the gate server-side before the capacity gate (returns `{locked, reason,
  coverage}` when < 70%). The exam **setup screen** renders a friendly locked panel (coverage bar +
  "study next" link) until unlocked; the Home's exam link mirrors it.

## Study-next flow (filtered deck → review)

Bridge `gre:study` recomputes the current `study_next` tag server-side (never trusts a client search
string), then builds/reuses a single filtered deck **"GRE · Study next"** with search
`tag:<leaf> -is:suspended` (rescheduling on → real FSRS study) via the standard
`get_or_create_filtered_deck` → `add_or_update_filtered_deck` (undoable `CollectionOp`), selects it,
closes the Home dialog, and `moveToState("review")`. Empty/deck-missing degrades to a message /
overview. Defensive throughout.

## Testing

- Pure unit tests (headless, no build): `studied_coverage`, `study_next` (unstudied→weakest paths,
  no-cards→None), `stats_block`, `leaf_label`; exam `coverage_meets_threshold` /
  `coverage_lock_reason` boundaries; the view-model additions.
- `./ninja check:svelte` for the route (force a bundle rebuild: `rm -rf out/sveltekit*`).
- **GUI smoke (human step, as with every GRE page)**: Home auto-opens; three cards + stats render;
  "study next" enters a topic review; Exam Mode shows the lock < 70% and unlocks ≥ 70%.

## Ship

Fast-lane PR (worktree/branch `agent/gre-home-ux`), self-review against the fast-lane checklist,
docs (`qt.md`, `INDEX.md`, `STATUS.md`) in the same PR, anki fork pushed + outer pin bumped.
