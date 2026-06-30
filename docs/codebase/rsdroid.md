# Android client — `libanki` + `rsdroid`

> Doc for `Anki-Android/` (the AnkiDroid fork) and how it runs the **same** Rust engine via the
> external `rsdroid` AAR over JNI. **Read before Android work** — our Mastery Query must reach this
> client too. Engine: `rslib.md`. RPC contract: `proto-rpc.md`.

## Purpose

The Android app is AnkiDroid (Kotlin). Its `libanki` module wraps the Rust engine the same way
`pylib` does on desktop, but the bridge is **JNI** through the external `net.ankiweb.rsdroid` AAR
(the `Anki-Android-Backend` / `rsdroid` repo, which bundles a compiled `rslib`). All collection work
— scheduling, storage, sync — happens in that shared Rust engine; Kotlin only marshals protobuf.

> **External-repo caveat.** The `rsdroid` / `Anki-Android-Backend` source is **not** in this
> workspace. JNI internals (the native method names, serialization, thread model) live inside the
> AAR and could not be verified here. Everything below about *AnkiDroid's own* usage is verified
> against `Anki-Android@v2.24.0` (`ebcf8e0`).

## Public interface

### `libanki` (`Anki-Android/libanki/src/main/java/com/ichi2/anki/libanki/`)
The Kotlin engine wrapper. Key files:
- `Collection.kt` — central facade; holds `val backend: Backend` and delegates domain ops to typed
  `backend.*` RPCs with `anki.*` protobuf types (search, import/export, undo, sync).
- `Storage.kt` — `Storage.collection(...)` gets a `Backend` from `BackendFactory.getBackend()` and
  calls `backend.openCollection(...)`.
- `LibAnki.kt` — global `backend`/`collection` slots (deprecated; prefer `CollectionManager`).
- `DB.kt` / `backend/BackendUtils.kt` — SQLite wrapper + JSON↔protobuf `ByteString` helpers. The
  collection DB is served by the Rust backend (`AnkiSupportSQLiteDatabase.withRustBackend(backend)`,
  via `AnkiDroid/.../backend/BackendDBUtils.kt`), not a separate Android DB handle.
- `sched/Scheduler.kt` — scheduler facade; `answerCard`, `getQueuedCards`, `buryOrSuspendCards`, … all
  go through `col.backend.*`.
- `stats/BackendStats.kt` — `Collection` extensions calling `backend.cardStatsRaw`, `backend.graphsRaw`
  — **the best template for adding a new read RPC wrapper** (e.g. mastery query).
- `Sync.kt` — sync helpers on `Collection`.

### Production entry — `Anki-Android/AnkiDroid/src/main/java/com/ichi2/anki/CollectionManager.kt`
- `BackendFactory.getBackend()` in `ensureBackendInner()` obtains the long-lived backend.
- `withCol { ... }` serialises all collection access on a single IO queue. Feature code should reach
  the engine as `CollectionManager.withCol { ... }`, **not** via `LibAnki` globals.

### How Kotlin runs RPCs
- Pattern: `col.backend.someMethod(protobufRequest)` (typed) or `backend.someMethodRaw(bytes)`.
- There is **no** generic `.command()` / `runMethod` / `NativeMethods` in this tree — the API is
  generated typed methods on `net.ankiweb.rsdroid.Backend`. (Grep confirmed: no such symbols here.)

### The rsdroid dependency
- Declared in `Anki-Android/gradle/libs.versions.toml`: `ankiBackend = '0.1.64-anki25.09.2'`
  (`io.github.david-allison:anki-android-backend`, plus `-testing`).
- Wired in `Anki-Android/libanki/build.gradle.kts` and `Anki-Android/AnkiDroid/build.gradle`
  (exposes `BACKEND_VERSION` in `BuildConfig`).
- Local override: `local.properties` `local_backend=true` → file deps to `../Anki-Android-Backend/rsdroid/...`.

## Surfacing the Mastery Query on Android (PRD §5 / §10 — planned)

**External first (rsdroid repo):**
1. Add the RPC + messages in shared `rslib` (`rslib.md`, `proto-rpc.md`).
2. Rebuild `Anki-Android-Backend`/`rsdroid` → new AAR with a generated `Backend.masteryQuery(...)`
   (name illustrative) + `anki.*` types + the updated native lib.
3. Publish or wire it locally; bump `ankiBackend` in `gradle/libs.versions.toml` (or `local_backend=true`).

**In-repo (this AnkiDroid fork):**
1. Add a `Collection.masteryQuery(...)` wrapper in `libanki` (follow `stats/BackendStats.kt`).
2. Call it from a ViewModel/Fragment via `CollectionManager.withCol { masteryQuery(...) }`.
3. Add tests (below).

## Other key flows

### Review loop
- `AnkiDroid/.../AbstractFlashcardViewer.kt` (base) and `Reviewer.kt` (activity); newer path
  `AnkiDroid/.../ui/windows/reviewer/ReviewerFragment.kt` + `ReviewerViewModel.kt`.
- Answer path: ease button → `answerCard(rating)` → `col.sched.answerCard(...)` (`libanki/.../sched/Scheduler.kt`)
  → `col.backend.answerCard(CardAnswer)`. Queue state via `col.backend.getQueuedCards(...)`.
- Third-party answers: `AnkiDroid/.../provider/CardContentProvider.kt`.

### Sync (PRD §10 conflict rule)
- libanki: `Collection.kt` — `syncLogin`, `syncCollection(auth, syncMedia)`, `syncMedia`,
  `fullUploadOrDownload`; `Sync.kt` one-way conflict helper.
- AnkiDroid: `AnkiDroid/.../Sync.kt` (interactive: `DeckPicker.sync` → `handleNormalSync` →
  `withCol { syncCollection(...) }`), `worker/SyncWorker.kt` (background collection sync),
  `worker/SyncMediaWorker.kt` (media sync, non-blocking). Error UX:
  `servicelayer/ThrowableFilterService.kt`.

## Dependencies
- **Outbound:** external `net.ankiweb.rsdroid` AAR (bundles `rslib`) over JNI. SQLite for the
  collection is served through the backend, not directly.
- **Inbound:** AnkiDroid feature code (`AnkiDroid/src/main/java/com/ichi2/anki/`) reaches the engine
  via `CollectionManager.withCol { }`.

## Gotchas & invariants
- **Version skew to reconcile:** AnkiDroid's backend is `0.1.64-anki25.09.2`; desktop is
  `anki@25.09.4`. Our Rust change must be built into an rsdroid AAR whose bundled `rslib` matches the
  desktop pin, or the two clients diverge.
- **Engine code is not in this repo.** You cannot add/inspect an RPC's JNI surface from
  `Anki-Android/` alone — the AAR must be rebuilt and re-wired.
- **All collection access goes through `CollectionManager.withCol { }`** (single IO queue); avoid the
  deprecated `LibAnki` globals.
- **Read RPCs stay read-only** here too — mirror the engine invariant (`rslib.md`); don't wrap a read
  in `undoableOp { }`.

## Related tests
- libanki JVM: `Anki-Android/libanki/src/test/java/com/ichi2/anki/libanki/` (e.g. `CollectionTest.kt`,
  `SchedulerTest.kt`, `CardTest.kt`); fixtures in `libanki/src/testFixtures/.../testutils/`
  (`InMemoryAnkiTest.kt` uses `RustBackendLoader`; `TestCollectionManager.kt`).
- AnkiDroid JVM/Robolectric: `Anki-Android/AnkiDroid/src/test/java/com/ichi2/anki/`
  (`ReviewerTest.kt`, `RobolectricTest.kt`, `worker/SyncMediaWorkerTest.kt`).
- Instrumented: `Anki-Android/AnkiDroid/src/androidTest/java/com/ichi2/anki/` (`ReviewerTest.kt`,
  `tests/libanki/`, `tests/CollectionTest.kt`).

---
Last verified against: `Anki-Android@v2.24.0` (`ebcf8e0`); rsdroid backend `0.1.64-anki25.09.2`
