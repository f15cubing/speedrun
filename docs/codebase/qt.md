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
- `anki/ts/routes/gre-dashboard/tokens.css` — the **"Readout" identity** tokens (design spec
  `docs/superpowers/specs/2026-07-05-readout-identity-design.md`): a calibrated CAS/terminal look
  where the **monospaced data face is the hero**. 6-colour palette (ink/muted/faint · teal `signal` ·
  amber `abstain`) + type roles; light/dark via Anki's `.night-mode`.
- `anki/ts/routes/gre-dashboard/fonts.css` + `fonts/` — **JetBrains Mono + Inter bundled locally**
  (SIL OFL, only used weights as `woff2`) so the identity works fully **offline** (no CDN); the
  sveltekit/vite build emits + fingerprints them (verified). `--gre-mono`/`--gre-sans` fall back to
  system faces if absent.
- `anki/ts/routes/gre-dashboard/CalibrationStrip.svelte` — **signature component**: renders
  `{point, low, high, n}` as a shaded 95% band + point tick on a 0..max axis, with the readout in
  math notation (`0.60 ∈ [0.54, 0.66]  n=238`) + an optional faint `method` tag (e.g. `Wilson`) so it
  "shows its work"; used at exam / bucket / leaf scale; `point==null` → explicit dotted "not yet"
  rail. The shared primitive the Thursday scoring layer renders Performance/Readiness ranges through.
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

## "How this differs from FSRS" page — the study-method explainer

A read-only desktop page (Tools ▸ **"How this app differs from FSRS"**) that makes the study method
legible: we build **on** FSRS (never replacing the scheduler) and add interleaving, a timed exam
mode, three separated scores, and the give-up rule. Same SvelteKit-dialog pattern as the
dashboard/exam. The interleaving section is **interactive** and runs the **real** vendored
interleaving algorithm (a verbatim copy of `pipeline/interleave.py`) on a fixed example queue.

**New files:**
- `anki/qt/aqt/gre/interleave.py` — vendored verbatim from `pipeline/interleave.py` (the app can't
  import the outer `pipeline/` at runtime), drift-guarded by the outer `tests/test_interleave_sync.py`.
- `anki/qt/aqt/gre/method_data.py` — pure, read-only view-model: a deterministic example due queue
  (authentic `topic::*` leaves) + `build_interleave_demo(k, w)` running the vendored algorithm
  (blocked vs interleaved orders + adjacency-dispersion / FSRS-displacement metrics; k/w clamped).
- `anki/qt/aqt/gre_method.py` — `GreMethod` QDialog + `setup_gre_method_menu()` Tools-menu action.
- `anki/ts/routes/gre-method/+page.svelte` — page shell (five sections: build-on-FSRS · interleaving
  · timed mode · three separated scores · give-up rule), reusing the dashboard's `tokens.css` +
  `CalibrationStrip`.
- `anki/ts/routes/gre-method/Interleave.svelte` — the interactive viz (colour-by-type chips, live
  metrics, K/W sliders that re-run the real algorithm; `animate:flip` reorder, reduced-motion aware).
- `anki/ts/routes/gre-method/lib.ts` + `lib.test.ts` — pure chip-colour + metric formatting (vitest).

**Modified files:**
- `anki/qt/aqt/mediasrv.py` — `is_sveltekit_page("gre-method")` + read-only `gre_method_interleave`
  handler → POST `/_anki/greMethodInterleave` (runs the vendored algorithm on the example queue;
  **never touches `col`**, no `OpChanges`).
- `anki/qt/aqt/webview.py` — `AnkiWebViewKind.GRE_METHOD` + `_profileForPage` api-access allowlist.
- `anki/qt/aqt/main.py` — Tools-menu hook via `main_window_did_init`.

**Data flow (read-only):** Tools ▸ "How this app differs from FSRS" → `GreMethod` QDialog →
`load_sveltekit_page("gre-method")` → `Interleave.svelte` POSTs `greMethodInterleave {k,w}` → handler
→ `method_data.build_interleave_demo` runs the vendored `interleave.py` on the example queue → JSON
(blocked/interleaved orders + metrics). Pure — no collection access, no `OpChanges`.

**Tests:** `anki/qt/tests/test_gre_method.py` (multiset/permutation invariant, dispersion ≥ blocked,
`displacement_max ≤ w`, k/w clamps, endpoint read-only + registration) + `anki/ts/routes/gre-method/
lib.test.ts` (colour mapping + formatters). Outer drift guard: `tests/test_interleave_sync.py`.
Design spec: `docs/superpowers/specs/2026-07-05-algorithm-explainer-page-design.md`.

## Review interleaving — live reviewer wiring (ablation — implemented)

The explainer above *demonstrates* interleaving; this wires it into the **actual review loop** so
interleaved vs blocked is a real, toggleable study mode (the ablation's two app arms). It is a
**pure presentation-layer reorder** of the batch the v3 scheduler already returned — it never
changes FSRS scheduling, the collection, or undo.

**Off by default.** With `col.conf["gre_interleave"]` unset the reviewer behaves byte-for-byte as
upstream (`get_queued_cards(fetch_limit=1)`, no reorder), so the default app — and every demo /
installer recording — is unaffected.

**New files:**
- `anki/qt/aqt/gre/interleave_review.py` — the reorder core. `interleave_enabled(col)` /
  `fetch_limit(col)` (1 when off, 16 when on) / `reorder_output(col, queued_cards)`. When on, it
  reorders **only the `REVIEW` cards** of the batch for confusable-type dispersion via the vendored
  `aqt.gre.interleave.interleave_order`; `NEW` / `LEARNING` cards keep their scheduler positions
  (intraday-learning timing preserved). Each `QueuedCard` (card + states + context) moves as a
  self-contained unit, so the shown card is always paired with **its own** scheduling states. Safe
  fallbacks (no-op) on `<3` review cards, a homogeneous cluster, or any review card missing a
  `topic::` leaf tag.
- `anki/qt/aqt/gre_interleave.py` — `setup_gre_interleave_menu()`: a **checkable** Tools-menu action
  ("GRE: Interleave reviews (ablation)") that flips `col.conf["gre_interleave"]` via
  `set_config(..., undoable=False)` (persists + syncs, no undo entry). On = interleaved arm, off =
  blocked arm; takes effect from the next card.

**Modified files:**
- `anki/qt/aqt/reviewer.py` — `_get_next_v3_card` now fetches `fetch_limit(col)` cards and calls
  `reorder_output(col, output)` before `V3CardInfo.from_queue`. The **only** review-loop change; a
  no-op when the flag is off.
- `anki/qt/aqt/main.py` — Tools-menu hook via `main_window_did_init`.

**Invariant (why this respects the engine ceilings):** the reorder mutates an in-memory protobuf
batch only. No `col` write, no `OpChanges`, no scheduling-field change → undo and the collection are
untouched; the "same cards, different presentation order" multiset invariant is unit-tested.

**Tests:** `anki/qt/tests/test_gre_interleave_review.py` (9): flag gate + `fetch_limit` switch,
dispersion of a blocked queue, **multiset invariant**, `NEW`/`LEARNING` positions preserved, and the
three safe fallbacks. Live GUI click-through (flip the toggle mid-review, confirm the order changes)
is the one human smoke step — offscreen QtWebEngine won't init headlessly here.

## Graded MCQ — wrong answer grades Again only (implemented)

The bundled "GRE Math MCQ" card template is interactive + graded: tapping an option reveals
correctness + the explanation, then binds the grade to the FSRS ease enum. A **wrong** answer is a
lapse — it must only ever grade **Again(1)**, never Hard/Good/Easy. The template's in-card flow
already enforces this (a wrong tap offers a single Continue); this closes the remaining desktop path
— Anki's built-in bottom answer bar (and its keyboard shortcuts), which the card webview cannot
touch (it lives in a separate `bottom.web`).

**How it works:** the template reports the tapped option's correctness to the reviewer the moment the
learner taps, via a bridge command `pycmd("gremcq:right")` / `pycmd("gremcq:wrong")` (guarded by
`typeof pycmd==='function'`, so it's a no-op on AnkiDroid, which has no `pycmd` and falls back to the
built-in ease buttons). This is a **state hint only** — selecting an option never answers or advances
the card. The reviewer stores the verdict for the current card and enforces the rule at two seams.

**New file:**
- `anki/qt/aqt/gre/mcq_lockdown.py` — pure, dependency-free helpers: `parse_verdict(url)`
  (`gremcq:` → `"right"`/`"wrong"`/`None`), `clamp_ease(verdict, ease)` (→ `1` only when wrong),
  `restrict_answer_buttons(verdict, buttons)` (keep only Again when wrong; defensively never blanks
  the bar). Only a **wrong** verdict restricts; a correct MCQ keeps Hard/Good/Easy (FSRS still needs
  the difficulty rating) and non-MCQ cards (no verdict → `None`) are untouched.

**Modified files:**
- `anki/qt/aqt/reviewer.py` — four thin seams: `__init__` inits `self._gre_mcq_verdict`; `nextCard`
  resets it per card; `_linkHandler` captures the `gremcq:` hint; `_answerCard` clamps a wrong MCQ's
  ease to Again (covers button, keyboard, and auto-advance — all funnel here); `_answerButtonList`
  collapses the bottom bar to Again after a wrong MCQ (last word, after the add-on hook).
- `pipeline/build_deck.py` (outer repo) — the MCQ template's `answer(i)` emits the guarded `gremcq:`
  hint; re-bundled into both app assets via `make deck-asset` (byte-identical).

**Invariant (engine ceilings):** the reviewer only reads its own in-memory verdict flag and reorders
which answer buttons are shown / clamps an ease value — **no `col` write, no `OpChanges`, no
scheduling-field or Rust/proto change**; undo and the collection are untouched. Grading still flows
through the normal FSRS `answer_card` path (a wrong answer is a real Again lapse the scheduler
re-queues).

**Existing-install template refresh:** the graded template reaches installs that imported an earlier
bundle via `deck_autoimport._refresh_bundled_notetype_templates` (see the deck-auto doc) — a
text-only note-type update, gated by a `gre_deck_template_revision` `col.conf` key, that needs no deck
re-import.

**Tests:** `anki/qt/tests/test_gre_mcq_lockdown.py` (13): the pure helpers (parse/clamp/restrict incl.
correct + non-MCQ pass-through and the never-blank guard) and the importer refresh (in-place update,
no-op-when-current, absent-notetype, unreadable-apkg degrade, revision gate, refresh-without-reimport).
`pipeline/tests/test_mcq_notetype.py` asserts the template emits the guarded verdict hint and still
does not grade/advance on selection. The live GUI click-through — a wrong MCQ shows only Again on the
bottom bar, and keyboard 2/3/4 no longer grade it — is the one human smoke step (offscreen QtWebEngine
won't init headlessly here).

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
Last verified against: `f15cubing/anki@f3acc684` (25.09.4 `d52ca66` + Mastery Query + W2 dashboard + dashboard redesign + exam mode + Exam-Mode LaTeX + desktop scoring adapter + Exam Mode API-error fix: Content-Type/body-parse/preset-capacity + submit-guard hardening + "How this differs from FSRS" study-method page: interactive interleaving demo + observed Performance on the dashboard + live-reviewer interleaving toggle + graded-MCQ wrong-answer lockdown + Readout dashboard identity: bundled JetBrains Mono/Inter + math-notation calibration strip + Readout cascade: exam mode imports the bundled fonts + a big mono countdown; deck browser home restyled to the mono identity (`qt/aqt/data/web/css/deckbrowser.scss` + `deckbrowser.py`))
