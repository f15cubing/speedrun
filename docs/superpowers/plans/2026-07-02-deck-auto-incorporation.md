# Deck Auto-Incorporation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **This ships via the ENGINE-LANE PROCESS: isolated worktree with recursive submodules, each app-touching PR verified by a DIFFERENT agent, NEVER self-merge.**

**Goal:** Ship the 5,407-card study deck **inside both apps** so it auto-loads on first run (no manual File→Import): commit the built `.apkg` as an asset in the `anki` (desktop) and `Anki-Android` forks, and add a **version-gated add/update auto-importer** to each (preserving FSRS history via content-derived GUIDs). Idempotent, offline, sync-safe.

**Architecture:** Desktop = a `gui_hooks`-registered startup importer in `qt/aqt/gre/` calling `col.import_anki_package(...)`. AnkiDroid = a DeckPicker-start importer calling the existing `importAnkiPackage(path, options)` (as `BackendImporting.importAnkiPackageUndoable` does). Both gate on a synced `col.conf` key `gre_deck_version`. Outer repo bumps both submodule pins + adds a `make deck-asset` regenerate/copy/hash-check tool.

**Tech Stack:** Python/Qt (`anki` fork), Kotlin (`Anki-Android` fork), the built `.apkg` from `pipeline/`, `genanki` content-GUIDs, `col.conf` (synced), `make`.

## Global Constraints

- **No engine/Rust/proto/scheduler/undo/store change.** Import via each platform's EXISTING package-import API only. (The mastery RPC + read-only invariant are untouched.)
- **Never wipe/replace — add/update only.** Preserve FSRS review history on unchanged cards (content-derived GUIDs make re-import an update).
- **Idempotent + version-gated.** Import only when the bundled `GRE_DECK_VERSION` is newer than `col.conf["gre_deck_version"]`; then set it. Re-run at same version = no-op / no dupes.
- **Offline + deterministic.** Bundled committed asset; no network for import.
- **Sync-safe (W4).** `gre_deck_version` lives in synced `col.conf`; a device that receives the deck via sync skips its own import; identical GUIDs mean sync never duplicates.
- **Asset can't drift** from `pipeline/` output (hash check).
- **Engine-lane process:** worktree + `git submodule update --init --recursive`; each app PR verified by a **different agent**; **never self-merge**. (Rust-specific extra-gate items — ≥3 Rust tests / undo / no-`OpChanges` — are **N/A**; this is UI/import glue.)
- **Spec:** `docs/superpowers/specs/2026-07-02-deck-auto-incorporation-design.md`.

## Environment / API facts (verified against the current forks)

- **Desktop import:** `from anki.collection import ImportAnkiPackageRequest, ImportAnkiPackageOptions`; `col.import_anki_package(ImportAnkiPackageRequest(package_path=<abs>, options=ImportAnkiPackageOptions(...)))` → `ImportLogWithChanges`. Confirm the exact `ImportAnkiPackageOptions` fields (e.g. `with_scheduling`, `update_notes`, `merge_notetypes`) against `anki/proto/anki/import_export.proto` at build time and choose add/update-preserving values (do NOT enable a "reset scheduling"/replace mode).
- **Desktop hook:** the W2 dashboard registers `gui_hooks.main_window_did_init.append(_add_gre_dashboard_menu)` in `qt/aqt/main.py` → `qt/aqt/gre_dashboard.py`. Use an analogous hook that fires **after a collection is loaded** (confirm: `gui_hooks.collection_did_load` or run inside a `profile_did_open`/`main_window_did_init` handler that guards `mw.col is not None`). Do the import off the UI thread via `QueryOp`/`taskman` if it blocks.
- **AnkiDroid import:** `Anki-Android/AnkiDroid/src/main/java/com/ichi2/anki/BackendImporting.kt` shows `withCol { importAnkiPackage(path, request.options) }` + `undoableOp { output.changes }`. Reuse that call with an asset copied to a temp file. DeckPicker is `com/ichi2/anki/DeckPicker.kt`.
- **Deck facts:** built `.apkg` ≈ 2.4 MB, 5,407 notes; deck name `GRE Math Subject Test::Study Deck`; note GUIDs are content-derived (stable across rebuilds unless a card's content changes).
- **Worktree:** engine lane — this worktree needs `git submodule update --init --recursive` before building either app. Build/test per `.cursor/skills/building-and-testing`.

---

## Task 1 — Desktop importer + bundled asset (`anki` fork → PR #1)

**Files (in the `anki` submodule):**
- Create: `qt/aqt/gre/data/gre-study-deck.apkg` (committed asset), `qt/aqt/gre/deck_autoimport.py`
- Modify: `qt/aqt/main.py` (register the hook), `qt/aqt/gre/__init__.py` if needed
- Test: `qt/tests/test_gre_autoimport.py` (or the fork's Python test location)

**Interfaces produced:** `GRE_DECK_VERSION: str`; `maybe_import_gre_deck(mw)` (version-gated add/update import + `col.set_config`).

- [ ] **Step 1: Put the asset in place** — copy the current built deck into the fork:
```bash
# from the outer worktree root, after submodule init + building the deck (pipeline)
python pipeline/build_deck.py --seed 42
mkdir -p anki/qt/aqt/gre/data
cp pipeline/dist/gre-study-deck.apkg anki/qt/aqt/gre/data/gre-study-deck.apkg
```

- [ ] **Step 2: Write the failing Python test** (`anki/qt/tests/test_gre_autoimport.py`) — using a fresh in-memory/temp collection:
```python
# Idempotent, version-gated add/update import.
from anki.collection import Collection
from aqt.gre import deck_autoimport as ai   # module under test (no Qt needed for the core fn)

def _fresh(tmp_path):
    return Collection(str(tmp_path / "col.anki2"))

def test_first_import_adds_deck(tmp_path):
    col = _fresh(tmp_path)
    n = ai._import_bundled(col)              # core import fn (no mw); returns imported count
    assert n > 5000
    assert col.get_config("gre_deck_version") == ai.GRE_DECK_VERSION
    col.close()

def test_reimport_same_version_is_noop(tmp_path):
    col = _fresh(tmp_path)
    ai._run_if_needed(col)                    # version-gated wrapper
    before = col.card_count()
    ai._run_if_needed(col)                    # second run: gated off
    assert col.card_count() == before
    col.close()
```
(Adjust import paths to the fork's test layout; the point is: first run imports >5000 cards + sets the version; second run at the same version is a no-op.)

- [ ] **Step 3: Run → FAIL** (`./ninja check` subset or `pytest qt/tests/test_gre_autoimport.py`) — module missing.

- [ ] **Step 4: Implement `qt/aqt/gre/deck_autoimport.py`:**
```python
import os
from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions

GRE_DECK_VERSION = "2026-07-02"   # bump when the bundled .apkg changes
_ASSET = os.path.join(os.path.dirname(__file__), "data", "gre-study-deck.apkg")
_CONFIG_KEY = "gre_deck_version"

def _import_bundled(col: Collection) -> int:
    # add/update import: content GUIDs update existing, add new, preserve scheduling.
    opts = ImportAnkiPackageOptions(with_scheduling=True, update_notes=..., merge_notetypes=...)  # CONFIRM fields
    before = col.card_count()
    col.import_anki_package(ImportAnkiPackageRequest(package_path=_ASSET, options=opts))
    col.set_config(_CONFIG_KEY, GRE_DECK_VERSION)
    return col.card_count() - before

def _run_if_needed(col: Collection) -> bool:
    if col.get_config(_CONFIG_KEY, None) == GRE_DECK_VERSION:
        return False
    _import_bundled(col)
    return True

def maybe_import_gre_deck(mw) -> None:
    if getattr(mw, "col", None) is None:
        return
    if col_needs := (mw.col.get_config(_CONFIG_KEY, None) != GRE_DECK_VERSION):
        from aqt.operations import QueryOp
        QueryOp(parent=mw, op=lambda col: _import_bundled(col),
                success=lambda _n: mw.reset()).run_in_background()
```
Register in `qt/aqt/main.py` next to the dashboard hook:
```python
def _autoimport_gre_deck() -> None:
    from aqt.gre.deck_autoimport import maybe_import_gre_deck
    maybe_import_gre_deck(aqt.mw)
gui_hooks.collection_did_load.append(lambda _col: _autoimport_gre_deck())  # CONFIRM hook name
```

- [ ] **Step 5: Run → PASS** + `./ninja check` (Python subset) green.
- [ ] **Step 6: GUI smoke** — fresh profile → `./run` → the GRE deck appears with no manual import; re-open = no second copy. Record it.
- [ ] **Step 7: Commit + open PR #1** on a fork branch; **different-agent review** (base gate; engine extra-gate = N/A, note "UI/import glue, no engine change"); **do not self-merge.**

---

## Task 2 — AnkiDroid importer + bundled asset (`Anki-Android` fork → PR #2)

**Files (in the `Anki-Android` submodule):**
- Create: `AnkiDroid/src/main/assets/gre-study-deck.apkg`, a `GreDeckAutoImport.kt` (in `com/ichi2/anki/`)
- Modify: `com/ichi2/anki/DeckPicker.kt` (invoke the importer on start)
- Test: a host-JVM test under `AnkiDroid/src/test/.../GreDeckAutoImportTest.kt`

**Interfaces produced:** `GRE_DECK_VERSION` const; `suspend fun maybeImportGreDeck(context, col)` (version-gated add/update).

- [ ] **Step 1: Place the asset** — `cp pipeline/dist/gre-study-deck.apkg Anki-Android/AnkiDroid/src/main/assets/gre-study-deck.apkg`.
- [ ] **Step 2: Write the failing host-JVM test** — with the real `libanki` backend (as `libanki` tests do): open a temp collection, run `maybeImportGreDeck` → assert card count > 5000 + config set; run again → no-op (idempotent).
- [ ] **Step 3: Run → FAIL** (`./gradlew :AnkiDroid:testPlayDebugUnitTest --tests '*GreDeckAutoImport*'` or the libanki test target).
- [ ] **Step 4: Implement `GreDeckAutoImport.kt`:**
```kotlin
const val GRE_DECK_VERSION = "2026-07-02"
private const val CONFIG_KEY = "gre_deck_version"

suspend fun maybeImportGreDeck(context: Context) {
    val current = withCol { config.getString(CONFIG_KEY, "") }   // CONFIRM col.conf accessor
    if (current == GRE_DECK_VERSION) return
    val tmp = File.createTempFile("gre-study-deck", ".apkg", context.cacheDir)
    context.assets.open("gre-study-deck.apkg").use { it.copyTo(tmp.outputStream()) }
    val options = importAnkiPackageOptions()   // add/update; CONFIRM fields vs BackendImporting usage
    withCol { importAnkiPackage(tmp.absolutePath, options) }      // same call as BackendImporting
    withCol { config.setString(CONFIG_KEY, GRE_DECK_VERSION) }
    tmp.delete()
}
```
Invoke from `DeckPicker` startup (after the collection is ready), off the main thread (`launchCatchingTask`), then refresh the deck list. Reuse `undoableOp { output.changes }` semantics from `BackendImporting` if required by the observability layer.

- [ ] **Step 5: Run → PASS** + AnkiDroid unit-test + lint targets green (per `building-and-testing`).
- [ ] **Step 6: Emulator smoke** — fresh install of the debug APK → first launch auto-imports the deck (visible in DeckPicker); relaunch = no dupes. Record it (screenshot/screenrecord).
- [ ] **Step 7: Commit + open PR #2**; **different-agent review**; **do not self-merge.**

---

## Task 3 — Outer repo: `make deck-asset` + pin bumps + docs (→ PR #3, after #1 & #2 merge)

**Files (outer repo):**
- Create: `sync`... no — root `Makefile` `deck-asset` target + `scripts/build-deck-asset.sh` (or inline), a hash-freshness check + test.
- Modify: `.gitmodules`/submodule pins for `anki` + `Anki-Android`; `docs/codebase/INDEX.md`, `docs/codebase/architecture.md` (deck-distribution note), `docs/STATUS.md`, a new/updated `docs/codebase/` note or `pipeline/pipeline.md` "distribution" section.

- [ ] **Step 1: `make deck-asset` target** — regenerate the deck + copy into both fork asset dirs + print/verify the content hash:
```make
deck-asset: ## Rebuild the study deck and refresh the bundled app assets.
	python pipeline/build_deck.py --seed 42
	cp pipeline/dist/gre-study-deck.apkg anki/qt/aqt/gre/data/gre-study-deck.apkg
	cp pipeline/dist/gre-study-deck.apkg Anki-Android/AnkiDroid/src/main/assets/gre-study-deck.apkg
	@shasum -a 256 pipeline/dist/gre-study-deck.apkg
```

- [ ] **Step 2: Freshness check** — a small pytest (outer `tests/` or `pipeline/tests`) that builds the deck to a temp path and asserts its content hash equals the committed assets' hash (so the bundled asset can't silently drift from the generator). Run it; it should pass right after `make deck-asset`.

- [ ] **Step 3: Bump submodule pins** — after PR #1 and PR #2 merge, update the `anki` and `Anki-Android` gitlinks to those merged commits; record the new SHAs in the docs' `Last verified against:` lines.

- [ ] **Step 4: Docs** — `docs/codebase/architecture.md` (a "deck distribution: bundled + first-run auto-import" note), `INDEX.md` (row), `STATUS.md` (done line). `pipeline/pipeline.md`: note the deck is bundled into both apps + `make deck-asset` keeps assets in sync.

- [ ] **Step 5: Commit + open PR #3**; **different-agent review** (base gate + the engine-lane extra gate's non-Rust items: no corruption on import — covered by Tasks 1–2 tests; "files touched + merge difficulty" note). **Do not self-merge.**

---

## Self-Review (plan vs. spec)

- **Spec coverage:** §1 architecture → Tasks 1–3; §2 components (asset+version, desktop importer, android importer, make deck-asset) → Tasks 1/2/3; §3 idempotency/history/sync → version-gated add/update + config key + tests; §4 testing → per-task unit + GUI/emulator smoke + freshness check; §5 lane/3-PR → Tasks 1/2/3 each different-agent-reviewed, never self-merge; §6 acceptance → per-task smokes + freshness; §7 out-of-scope honored. No gaps.
- **API confirmations flagged:** `ImportAnkiPackageOptions` field names, the exact desktop collection-load hook, and the AnkiDroid `col.conf` accessor are marked "CONFIRM" — the implementer verifies each against the initialized submodule (the calls themselves — `col.import_anki_package`, `withCol { importAnkiPackage(path, options) }` — are verified present).
- **Consistency:** `gre_deck_version` config key + `GRE_DECK_VERSION` constant + `.apkg` asset path are used identically across desktop, Android, and the freshness check.

## Execution Handoff

**ENGINE-LANE PROCESS.** Implement in an isolated worktree with `git submodule update --init --recursive`. Each app PR (#1 desktop, #2 AnkiDroid) is **verified by a different agent** and **never self-merged**; PR #3 (pins + tooling) lands last. Both app builds must be exercised (desktop `./run`+`./ninja check`; AnkiDroid `./gradlew` + emulator). Execution options: (1) subagent-driven-development (recommended — fresh implementer + different-agent reviewer per task), (2) executing-plans (inline).
