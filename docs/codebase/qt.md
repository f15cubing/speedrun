# Qt desktop UI — `aqt`

> Doc for `anki/qt/` (and the `anki/ts/` web frontend it serves). **Read before adding desktop
> screens** — our 3-score dashboard + coverage map attach here. Engine facade it uses: `pylib.md`.

## Purpose

The desktop GUI: Qt (PyQt/QWebEngine) + Python, package `aqt`. It owns the main window, the review
loop, dialogs, a local HTTP server that serves modern web screens, and the add-on manager. It does
**no** scheduling itself — it drives the engine through a `pylib` `Collection` (`mw.col`).

## Public interface

### Boot & collection ownership
- Entry: `anki/qt/runanki.py` → `import aqt; aqt.run()`.
- `anki/qt/aqt/__init__.py` — `run()` parses CLI, builds `AnkiApp`, `ProfileManager`, i18n +
  `RustBackend`, then creates the global `mw = AnkiQt(...)`. Exposes `aqt.mw`, `aqt.dialogs`
  (`DialogManager`).
- `anki/qt/aqt/main.py` — `AnkiQt`: `setupUI()` → `setupProfile()` → `loadCollection()` →
  `moveToState("deckBrowser")`. Holds `mw.col: Collection | None` (created as
  `Collection(path, backend=...)`). State machine `moveToState()` → `_deckBrowserState`,
  `_overviewState`, `_reviewState`.
- Global access pattern: `from aqt import mw` then `mw.col`.

### Talking to the engine — `anki/qt/aqt/operations/`
- **`CollectionOp`** (`operations/__init__.py`): runs `op(col)` on a background thread, shows
  progress, and on success fires **`gui_hooks.operation_did_execute(changes, initiator)`** with the
  `OpChanges` from the engine. Per-domain ops: `operations/deck.py`, `card.py`, `note.py`,
  `scheduling.py`, `collection.py`.
- **`QueryOp`**: same threading for reads; does **not** emit `operation_did_execute`. Use this for
  read-only calls like the Mastery Query / coverage map.
- **UI refresh:** `AnkiQt.setupHooks()` subscribes `on_operation_did_execute`, which dispatches to
  `reviewer.op_executed` / `overview.op_executed` / `deckBrowser.op_executed`; each sets
  `_refresh_needed` based on `OpChanges` fields (e.g. `study_queues`).

### Web screens — `anki/qt/aqt/webview.py` + `anki/qt/aqt/mediasrv.py`
- `AnkiWebView` (`webview.py`): QWebEngineView + `QWebChannel` bridge (`pycmd`). Three load paths:
  - `stdHtml()` — legacy HTML screens (deck browser, overview) served via `/_anki/legacyPageData`.
  - `load_sveltekit_page(path)` — modern SvelteKit SPA (graphs, deck-options, congrats).
  - `load_ts_page(name)` — older static TS pages.
- `mediasrv.py` — background Flask/Waitress server (`MediaServer`): serves bundled web assets from
  `anki/qt/aqt/data/web/`, maps SvelteKit routes (`is_sveltekit_page()`), and exposes
  **POST `/_anki/{endpoint}`** as the backend bridge for the web UI (handlers call `mw.col` or
  `mw.col._backend.*_raw()`; `exposed_backend_list` includes `"graphs"`, `"card_stats"`, …).

### Modern screen precedents
| Screen | Pattern | Files |
|---|---|---|
| Stats / graphs | SvelteKit dialog | `aqt/stats.py` → `load_sveltekit_page("graphs")` |
| Deck options | SvelteKit in dialog webview | `aqt/deckoptions.py` → `load_sveltekit_page("deck-options/{id}")` |
| Deck browser | legacy `stdHtml` + jQuery | `aqt/deckbrowser.py` |
| Overview / congrats | legacy `stdHtml`; finished → SvelteKit | `aqt/overview.py` |

### TS / Svelte frontend — `anki/ts/`
SvelteKit app (Vite). Routes in `anki/ts/routes/` (`graphs/`, `deck-options/`, `congrats/`). Built
by `anki/ts/svelte.config.js` to `out/sveltekit/`, packaged to `anki/qt/aqt/data/web/sveltekit/`,
served by `mediasrv`. The web UI calls the engine via POST to `/_anki/{camelCaseEndpoint}`.

## Where the 3-score dashboard + coverage map attach (W2 — implemented)

Implemented following the **graphs / deck-options** SvelteKit dialog precedent.

**New files:**
- `anki/qt/aqt/gre/__init__.py` — package init
- `anki/qt/aqt/gre/taxonomy.json` — frozen 17-leaf / 3-bucket / 50/25/25 taxonomy
- `anki/qt/aqt/gre/dashboard_data.py` — pure view-model: taxonomy loader, Wilson interval, `headline()` (50/25/25 rollup with n=0 renorm), coverage/next-best-topic, `build_view_model()`. Also owns the **observed-Performance** surface: `load_exam_attempts(path)` (flattens the Exam Mode results side-file, best-effort) + `observed_performance(attempts)` (pooled rights-only accuracy as a Wilson **range** with `n`; a give-up `not_available` state when there are no attempts — never a fabricated 0)
- `anki/qt/aqt/gre_dashboard.py` — `GreDashboard` QDialog + `setup_gre_dashboard_menu()` Tools-menu action; on open, `_write_scorecard(mw)` computes + persists the synced `gre_scorecard` (see "GRE scoring adapter" below)
- `anki/ts/routes/gre-dashboard/+page.svelte` — SvelteKit page root (fetches `greDashboardData` on mount); 3-zone layout (masthead · Memory · the two other slots · coverage)
- `anki/ts/routes/gre-dashboard/MemoryPanel.svelte` — memory range headline + per-bucket/per-leaf ranges
- `anki/ts/routes/gre-dashboard/CoverageMap.svelte` — 17-leaf coverage, each studied leaf as a compact calibration strip; best-next leaf ringed
- `anki/ts/routes/gre-dashboard/ScoreSlot.svelte` — generic score slot; Readiness shows the `insufficient_evidence` gate (amber); **Performance** renders a `CalibrationStrip` range when `state=="observed"` (a real `point`+`low`+`high` payload) and otherwise a give-up state. The guard is strict: any state other than the two give-up states + `observed`, or an `observed` state missing its range, collapses to `not_available` — a fabricated point can never render.

**Design system (redesign):**
- `anki/ts/routes/gre-dashboard/tokens.css` — the dashboard's design tokens (6-colour palette + type roles + system tabular-mono for numerals); light/dark via Anki's `.night-mode`. No bundled fonts.
- `anki/ts/routes/gre-dashboard/CalibrationStrip.svelte` — **signature component**: renders `{point, low, high, n}` as a shaded 95% band + point tick on a 0..max axis (used at exam / bucket / leaf scale); `point==null` → explicit dotted "not yet" rail. This is the shared primitive the Thursday scoring layer renders Performance/Readiness ranges through.
- `anki/ts/routes/gre-dashboard/lib.ts` + `lib.test.ts` — pure strip geometry (`stripGeometry`, `formatValue`) + 8 vitest cases; the geometry guarantees a null point never yields a fabricated position.
- Redesign is **pure presentation** — no `dashboard_data.py` / view-model change (that surface belongs to the scoring layer).

**Modified files:**
- `anki/qt/aqt/mediasrv.py` — `is_sveltekit_page("gre-dashboard")` registration + read-only `gre_dashboard_data` handler → POST `/_anki/greDashboardData` endpoint (calls `col.mastery_query(20 topics)` on the request thread, same pattern as `graphs`/`congrats_info`; never emits `OpChanges`). The handler also **reads** (never writes) the Exam Mode attempts side-file (`pm.profileFolder()/gre_exam_results.jsonl`) via `dd.load_exam_attempts` and passes it to `build_view_model(exam_attempts=…)`; the read is wrapped best-effort so a missing/unreadable file never breaks the dashboard.
- `anki/qt/aqt/main.py` — Tools-menu hook via `main_window_did_init`
- `anki/qt/aqt/webview.py` — `AnkiWebViewKind.GRE_DASHBOARD`

**Data flow:** Tools ▸ "GRE readiness dashboard" → `GreDashboard` QDialog → `load_sveltekit_page("gre-dashboard")` → Svelte page POSTs `/_anki/greDashboardData` → handler calls read-only `col.mastery_query(17 leaves + 3 buckets)` **and** reads the Exam Mode attempts side-file → `build_view_model()` JSON → Svelte renders the memory range + coverage map + 3 separated score slots (Performance now a live observed range once the learner has taken a timed mock). Strictly read-only (no `OpChanges`).

**Observed Performance (how the score goes live).** Exam Mode's `greExamSubmit` appends per-item attempts to a profile side-file (`gre_exam_results.jsonl`; never the collection). The dashboard handler pools every recorded attempt and shows Performance as the **rights-only accuracy with a Wilson range + `n`** — the honest low-`n` surface, deliberately *not* the calibrated logistic+Platt model in `scoring/performance.py` (that needs a multi-student attempt corpus; fitting it on one learner's handful of attempts would look confident exactly when it knows least). The three scores stay **separate**; Performance is never blended into Memory or Readiness. Note this is the desktop **dashboard** surface only — the synced `gre_scorecard` (Android panel) still reports Performance `not_available` (see the scoring-adapter note below); wiring observed Performance into the synced card is a documented follow-up.

**Tests:** `anki/qt/tests/test_gre_dashboard_data.py` (20 unit tests covering taxonomy, Wilson, headline renorm, view-model, **observed Performance** + the side-file loader), `anki/qt/tests/test_gre_dashboard_mediasrv.py` (2 tests: route registration + endpoint read-only invariant). Outer drift guard: `tests/test_taxonomy_sync.py`.

## Exam Mode — faithful GRE Math Subject Test

An opt-in "full mock" surface faithful to the computer-delivered GRE Math Subject Test (Tools ▸ GRE
exam mode). Vendored into the fork (the app can't read the outer `eval/bank/` at runtime), so the
logic + items live in `anki/qt/aqt/gre/` (the `dashboard_data.py` + `taxonomy.json` pattern).

**Core (B-1) — new files:**
- `anki/qt/aqt/gre/exam.py` — deterministic, blueprint-matched (ETS 50/25/25) form assembly at the
  official pace (2.58 min/item; presets `full 66 / half 33 / third 22 / mini 11`) + **rights-only**
  scoring with per-leaf/bucket breakdown + Wilson CI + the attempts record for the scoring seam.
  Headless-importable (no aqt deps), mirrors `dashboard_data.py`. **Preset-feasibility helpers**
  (`bucket_pool_sizes` / `size_is_feasible` / `max_feasible_size` / `feasible_presets`) report which
  presets the firewalled bank can actually build, so a mock the bank can't fill is never offered.
- `anki/qt/aqt/gre/exam_items.json` — vendored copy of the authored eval bank (drift-guarded by the
  outer `tests/test_exam_items_sync.py`). Firewalled: only eval items ever reach a mock.

**Webview shell (B-2) — new files:**
- `anki/ts/routes/gre-exam/` — `+page.svelte` (session state machine + one global countdown timer;
  on mount fetches `greExamCapacity` and **disables presets the firewalled bank can't fill**, shown
  as a calm dashed/amber "not enough held-out items yet" state with a capacity note — never a red
  error), `ItemView.svelte` (one item, five A–E single-select options), `Countdown.svelte`, `Navigator.svelte`
  (review-screen grid: answered/unanswered/marked, jump-to), `Results.svelte` (rights-only range +
  per-area breakdown + item review, reusing the dashboard's `CalibrationStrip`), `lib.ts`/`lib.test.ts`.
  Faithful: one global clock, one item at a time, Mark + free Back/Next, Review screen, **no
  calculator**, **no pause**, auto-submit at 0:00, **no per-item feedback** (results only after submit).

**Modified files (B-2):**
- `anki/qt/aqt/mediasrv.py` — `is_sveltekit_page("gre-exam")` + three read-only handlers:
  `greExamCapacity` (reports feasible presets + max feasible size so the setup screen only offers
  buildable mocks), `greExamForm` (pre-checks feasibility, then assembles a blueprint-matched form;
  **never sends the answer keys to the client**; an unfillable preset returns an honest `locked`
  reason, not an internal `InsufficientItemsError` dump), and `greExamSubmit` (rights-only
  **server-side** scoring; persists an attempts side-file — not the collection — for the scoring
  layer; reveals keys only in the post-submit result; a forged submit for an infeasible preset
  returns a clean `locked` reason, never a 500).
- `anki/qt/aqt/webview.py` — `AnkiWebViewKind.GRE_EXAM` + api-access allowlist.
- `anki/qt/aqt/main.py` — Tools-menu action via `main_window_did_init` (`gre_exam.py`
  `GreExam` QDialog). Mastery-gate structure present (`EXAM_MODE_MIN_STUDIED_PCT`, 0.0 for now).

**Tests:** `anki/qt/tests/test_gre_exam.py` (pace/blueprint/assembly determinism/insufficient/
firewall/rights-only scoring/Wilson/attempts + **preset feasibility**: pool sizes, feasibility
boundary, preset flags, and the p0-only regression) + `anki/ts/routes/gre-exam/lib.test.ts`
(clock/tally). Outer drift guard: `tests/test_exam_items_sync.py`.

**Preset capacity gate (why presets can be disabled).** The vendored held-out bank is small — the
`p0` partition the mock draws from holds **24 items (8 calc / 7 alg / 9 add)** — so only the `mini`
(11) preset can currently be assembled under the 50/25/25 blueprint; `full`/`half`/`third` need more
items than exist and previously failed *after* the user picked them (`InsufficientItemsError` →
`locked` reason exposing raw counts). The fix keeps the mock **p0-only and read-only** (no change to
the held-out bank, the scoring defs, or the partition semantics) and instead makes Exam Mode honest
about capacity: `greExamCapacity` drives the setup screen to enable only buildable presets. **Known
limitation:** even the entire authored bank (p0+p3 = 80) can't build `full` (66) — calculus caps at
28 < the 33 needed — so larger mocks unlock only when the firewalled bank grows (a
content/eval-bank follow-up, not a UI change).

**Data flow (read-only):** Tools ▸ GRE exam mode → `GreExam` QDialog → `load_sveltekit_page("gre-exam")`
→ page POSTs `greExamCapacity` (feasible presets) then `greExamForm` (server assembles + withholds
keys) → timed session → `greExamSubmit` (server re-assembles deterministically from the echoed seed,
scores rights-only, persists attempts, returns the revealed result). No `OpChanges`; attempts go to a
profile side-file, never the collection.

## GRE scoring adapter — synced 3-score card (Task 6 — implemented)

Desktop-authoritative scoring: on dashboard open, compute the three-score
`gre_scorecard` and write it to `col.conf` so it rides W4 collection sync to AnkiDroid
(rendered read-only there — Task 7).

**New file:**
- `anki/qt/aqt/gre/scoring_adapter.py` — `compute_and_write_scorecard(col)`: gathers the
  W1 mastery rows (`col.mastery_query(query_topics())`) + coverage via the W2
  `dashboard_data.build_view_model()`, calls the pure-stdlib **outer-repo** `scoring/`
  package (importable via a `sys.path` bridge to the repo root — four levels up from
  `qt/aqt/gre/`), and writes `col.set_config("gre_scorecard", …)` (`undoable=False`, so
  undo history is preserved). Read-only w.r.t. study data; that one config write is the
  only mutation.

**Modified file:**
- `anki/qt/aqt/gre_dashboard.py` — `_write_scorecard(mw)` called in `GreDashboard.__init__`
  (guarded: never blocks opening the dialog if scoring raises).

**Score card** (`gre_scorecard` col.conf JSON, spec §6): `{version, updated_at, source,
memory{estimate,low,high,coverage_pct}, performance{…,state},
readiness{shown,estimate,low,high,reasons,coverage_pct,confidence,best_next_topic}}`. The
three scores stay **separate** — never blended.

**Honesty ceilings:** Memory is the FSRS-mastery Wilson range (`None` at n=0); Performance
in the **synced card** is still `not_available` (the dashboard now surfaces observed exam
accuracy — see "Observed Performance" above — but wiring that into the synced `gre_scorecard`
for the Android panel is a documented follow-up);
**Readiness is gated OFF** (`shown=false`) with reasons + the evidence panel — desktop has
no P(correct) model without attempts, and we deliberately do **not** derive Readiness from
Memory (firewall / no-blend). Never a bare number.

**Tests:** `anki/qt/tests/test_scoring_adapter.py` (3: schema/persist/gated on a fresh
collection · evidence panel present when gated · the dashboard-open hook writes the card).
Run the aqt suite with `PYTHONPATH=pylib:out/pylib:out/qt ANKI_TEST_MODE=1
out/pyenv/bin/pytest -p no:cacheprovider qt/tests` — note `PYTHONPATH=out/pylib` alone is
**insufficient** for aqt tests: the generated `_aqt` package lives in `out/qt`.

## Add-ons & hooks
- `anki/qt/aqt/addons.py` — `AddonManager` imports enabled add-ons.
- `anki/qt/aqt/gui_hooks.py` re-exports hooks; the source of truth is `anki/qt/tools/genhooks_gui.py`
  (~100+ hooks: `main_window_did_init`, `collection_did_load`, `deck_browser_will_render_content`,
  `webview_did_receive_js_message`, `operation_did_execute`, browser menu hooks, …).
- Seams to extend without deep forking: append `gui_hooks.*` callbacks; register managed dialogs via
  `aqt.dialogs.register_dialog(name, creator)`; serve add-on web UIs under `/_addons/`. There's no
  first-class "register menu item" hook — add `QAction`s at an init hook.

## Dependencies
- **Outbound:** `pylib` (`anki.Collection` via `mw.col`) — `pylib.md`. The web UI reaches the engine
  through `mediasrv` POST endpoints, not directly.
- **Inbound:** add-ons and our first-party screens hook into `aqt`.

## Gotchas & invariants
- **All engine access is via `mw.col`** (don't reach into `_backend` from UI; wrap in pylib).
- **Reads use `QueryOp`, mutations use `CollectionOp`** so undo + UI refresh behave correctly. A read
  that fabricates `OpChanges` would wrongly trigger refresh/undo churn.
- **New SvelteKit pages need three edits** (route + `is_sveltekit_page()` + Python loader); missing
  any one yields a blank webview.
- **Dev HMR:** `load_sveltekit_page` points to port 5173 when `anki.utils.hmr_mode` is set.

## Related tests
- `anki/qt/tests/` — `test_mediasrv.py` (path safety, CSP), `test_i18n.py`, `test_addons.py`,
  `qwebengine_csp_smoke.py`. No broad `AnkiQt`/`CollectionOp`/SvelteKit integration tests here.

---
Last verified against: `f15cubing/anki@b7cf7c2` (25.09.4 `d52ca66` + Mastery Query + W2 dashboard + dashboard redesign + exam mode + Exam-Mode LaTeX + desktop scoring adapter + Exam Mode API-error fix: Content-Type/body-parse/preset-capacity + submit-guard hardening + observed Performance on the dashboard)
