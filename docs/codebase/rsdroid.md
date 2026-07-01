# Android client — `libanki` + `rsdroid`

> Doc for `Anki-Android/` (the AnkiDroid fork) and how it runs the **same** Rust engine via the
> external `rsdroid` AAR over JNI. **Read before Android work** — our Mastery Query must reach this
> client too. Engine: `rslib.md`. RPC contract: `proto-rpc.md`.

## Purpose

The Android app is AnkiDroid (Kotlin). Its `libanki` module wraps the Rust engine the same way
`pylib` does on desktop, but the bridge is **JNI** through the external `net.ankiweb.rsdroid` AAR
(the `Anki-Android-Backend` / `rsdroid` repo, which bundles a compiled `rslib`). All collection work
— scheduling, storage, sync — happens in that shared Rust engine; Kotlin only marshals protobuf.

> **Now vendored (W3).** `rsdroid` / `Anki-Android-Backend` is a recursive git submodule at the repo
> root (`f15cubing/Anki-Android-Backend@3dc30c2`), and we build the AAR **locally** from our fork so
> its bundled `rslib` carries the W1 mastery query. AnkiDroid consumes that local build via
> `local_backend=true` (see "The rsdroid dependency" + "Building rsdroid from source" below).
> Everything below about *AnkiDroid's own* usage is verified against `Anki-Android@v2.24.0` (fork
> `f15cubing/Anki-Android@67364a7`).

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
- `stats/BackendStats.kt` — `Collection` extensions calling `backend.cardStatsRaw`, `backend.graphsRaw`,
  and (W3) **`Collection.masteryQuery(topics: List<String>): List<anki.stats.TopicMastery>`** — the
  read-only wrapper over the shared `rslib` MasteryQuery RPC (`backend.masteryQuery(topics = ...)`),
  never wrapped in `undoableOp`. This is the template for adding a new read RPC wrapper.
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
- Published fallback: `Anki-Android/gradle/libs.versions.toml` `ankiBackend = '0.1.64-anki25.09.2'`
  (`io.github.david-allison:anki-android-backend`, plus `-testing`), wired in
  `Anki-Android/libanki/build.gradle.kts` + `Anki-Android/AnkiDroid/build.gradle`.
- **Active for W3 — `local_backend=true`** in `Anki-Android/local.properties` (gitignored) switches
  both modules to **file** deps on the locally-built sibling backend:
  `../Anki-Android-Backend/rsdroid/build/outputs/aar/rsdroid-release.aar` +
  `../Anki-Android-Backend/rsdroid-testing/build/libs/rsdroid-testing.jar`. Because these are raw
  `files(...)` (no POM), the published Maven coordinate — and thus any `VERSION_NAME` /
  `ext.ankidroid_backend_version` string match — is **irrelevant** in this mode; identity is "whatever
  `rslib` that local build bundled" (here `f15cubing/anki@ea3acae`). Two consequences we had to patch:
  the raw `rsdroid-testing.jar` drops its transitive `commons-exec` (used by `RustBackendLoader`), so
  `libanki/build.gradle.kts`'s `local_backend` branch adds `commons-exec:1.6.0` to the test classpaths.

## Mastery Query on Android (PRD §5 / §10 — DONE, W3)

The shared `rslib` MasteryQuery RPC (W1) is now reachable from Kotlin on our rebuilt backend:
- **Backend (rsdroid fork):** the nested `anki` submodule points at `f15cubing/anki@ea3acae`, so
  `./build.sh` regenerates `GeneratedBackend.kt` with `masteryQuery(topics): List<anki.stats.TopicMastery>`
  + `masteryQueryRaw` and compiles our `rslib` into `librsdroid.so`.
- **Binding (this AnkiDroid fork):** `libanki/.../stats/BackendStats.kt` adds the read-only
  `Collection.masteryQuery(...)` wrapper. Call it from a ViewModel/Fragment via
  `CollectionManager.withCol { masteryQuery(listOf("topic::calculus", ...)) }`.
- **Proven:** host-JVM reachability test (below) is green against the locally-built backend, and the
  `librsdroid.so` loads at runtime on an arm64 emulator (see STATUS / the W3 PR).

### Building rsdroid from source (W3) — verified recipe
From the repo root, with the Android toolchain exported (JDK 21, `ANDROID_HOME`,
`ANDROID_NDK_HOME=$ANDROID_HOME/ndk/29.0.14206865`, Rust target `aarch64-linux-android`):
```bash
# 1) backend bundling OUR engine (arm64-v8a emulator ABI + host .jar, current platform only)
cd Anki-Android-Backend && ./build.sh && cd ..      # logs "Anki commit: ea3acae…"
# 2) AnkiDroid APK on the local backend (local.properties has local_backend=true)
cd Anki-Android && ./gradlew assembleFullDebug && cd ..
```
Outputs: `Anki-Android-Backend/rsdroid/build/outputs/aar/rsdroid-release.aar` (+ `rsdroid-testing.jar`),
and `Anki-Android/AnkiDroid/build/outputs/apk/full/debug/AnkiDroid-full-arm64-v8a-debug.apk` (bundles
our `librsdroid.so`). All-ABI builds are CI-only (Sunday packaging).

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
- **Version skew (reconciled, with one shim):** upstream AnkiDroid v2.24.0 expects backend
  `*-anki25.09.2`; our engine is `anki@25.09.4` (`ea3acae`). We build the backend against 25.09.4 and
  patch the single symbol the app compile actually hit: `Backend.MAX_INDIVIDUAL_MEDIA_FILE_SIZE`
  (a `100 MiB` const AnkiDroid reads, which 25.09.2 emitted but 25.09.4 no longer does) is re-added in
  the rsdroid fork's `Backend.kt` companion. No engine downgrade.
- **Engine code IS now in this repo** (submodule `Anki-Android-Backend/`, nested `anki/`), but the
  RPC's generated JNI surface only appears **after** `./build.sh` regenerates `GeneratedBackend.kt` —
  editing `libanki` alone won't expose a new RPC until the backend is rebuilt + re-wired.
- **Submodule builds trip `installGitHook`:** a submodule's `.git` is a file (gitdir pointer), so the
  `Copy` hook task fails output validation. Both `rsdroid/build.gradle` and `AnkiDroid/build.gradle`
  guard it behind `rootDir/.git` being a real directory.
- **All collection access goes through `CollectionManager.withCol { }`** (single IO queue); avoid the
  deprecated `LibAnki` globals.
- **Read RPCs stay read-only** here too — mirror the engine invariant (`rslib.md`); don't wrap a read
  in `undoableOp { }`.

## Related tests
- libanki JVM: `Anki-Android/libanki/src/test/java/com/ichi2/anki/libanki/` (e.g. `CollectionTest.kt`,
  `SchedulerTest.kt`, `CardTest.kt`); fixtures in `libanki/src/testFixtures/.../testutils/`
  (`InMemoryAnkiTest.kt` uses `RustBackendLoader`; `TestCollectionManager.kt`).
  - **W3:** `stats/MasteryQueryTest.kt` — extends `InMemoryAnkiTest` (plain JUnit4, host JVM via the
    rsdroid-testing native lib = real compiled `rslib`). Seeds tagged Basic notes and asserts
    `masteryQuery([leaf, bucket])` returns one row per requested topic, in order, with hierarchical
    `::*` roll-up. Run: `./gradlew :libanki:testDebugUnitTest --tests "*MasteryQueryTest"`.
- AnkiDroid JVM/Robolectric: `Anki-Android/AnkiDroid/src/test/java/com/ichi2/anki/`
  (`ReviewerTest.kt`, `RobolectricTest.kt`, `worker/SyncMediaWorkerTest.kt`).
- Instrumented: `Anki-Android/AnkiDroid/src/androidTest/java/com/ichi2/anki/` (`ReviewerTest.kt`,
  `tests/libanki/`, `tests/CollectionTest.kt`).

---
Last verified against: `f15cubing/Anki-Android@67364a7` (fork of `v2.24.0` `ebcf8e0`); rsdroid
`f15cubing/Anki-Android-Backend@3dc30c2` (built locally, bundles `f15cubing/anki@ea3acae`)
