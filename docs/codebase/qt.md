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

## Where the 3-score dashboard + coverage map attach (PRD §7 — planned)

Closest precedent is **graphs / deck-options**, not the legacy deck-browser HTML:
1. Add a SvelteKit route under `anki/ts/routes/` (e.g. `gre-dashboard/`).
2. Register the path in `mediasrv.is_sveltekit_page()` and add any read endpoints to the exposed
   backend list (mastery query, coverage).
3. Add a Python loader/dialog in `aqt/` (a dialog like `stats.py`, or a section integrated via the
   state machine like `overview._show_finished_screen()`), and a menu `QAction`.
4. Fetch data with `QueryOp` (read-only) so it never emits `operation_did_execute`.

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
Last verified against: `anki@25.09.4` (`d52ca66`)
