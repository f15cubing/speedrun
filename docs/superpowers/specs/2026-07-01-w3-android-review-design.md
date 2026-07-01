# W3 — Android Review on the Shared Engine — Design Spec

> Rebuild the **rsdroid** backend against our fork so its bundled `rslib` carries the W1 mastery-query
> change, wire it into an AnkiDroid fork, and **run a real FSRS review session on the shared GRE deck on
> an emulator** — the Milestone-1 hard gate ("phone sharing engine"). Adds a read-only Kotlin
> `Collection.masteryQuery(...)` binding + an on-device reachability proof so "one engine on both
> platforms" is demonstrated, not asserted. Companion to `docs/PRD.md` (§5, §10, D3),
> `docs/execution-plan.md` (Wednesday / Milestone 1), the W1 spec
> `2026-06-30-mastery-query-engine-design.md`, and `docs/codebase/rsdroid.md`. Dated 2026-07-01.

## Where this sits (Wednesday decomposition)

- **W1 — Mastery Query (shipped, PR #7):** the read-only `rslib` engine change (`f15cubing/anki@ea3acae`).
- **W2 — Desktop dashboard (shipped, PR #9):** memory score as a range + coverage map on desktop.
- **W3 — Android review (this spec):** rebuild rsdroid with our change, wire it, run a review session,
  prove the RPC is reachable across JNI. **No Android dashboard, no sync** (those are Fri+/W4).
- **W4 — Sync foundation:** `anki-sync-server` + conflict-rule smoke test.

## Status at time of writing

- W1 is merged; `mw.col.mastery_query(topics)` runs on desktop and returns, per requested tag
  (hierarchical), a `TopicMastery { topic, total_cards, reviewed_count, mastered_count, avg_recall }`.
- The seeded `topic::*`-tagged GRE deck exists (`pipeline/`, PR #1).
- **Android currently runs a *stock* engine.** Spike 2 built `assembleFullDebug` against the **published**
  rsdroid AAR (`net.ankiweb.rsdroid 0.1.64-anki25.09.2`): `Anki-Android/local.properties` holds only
  `sdk.dir`, `local_backend` is unset, and `Anki-Android-Backend` is not cloned. **Our W1 change is not
  on Android yet** — putting it there is the substance of W3.
- Submodules pinned: `anki@ea3acae` (our fork), `Anki-Android@v2.24.0` (`ebcf8e0`, still upstream).

## Decisions (locked with owner, 2026-07-01)

- **Rebuild rsdroid from source against our fork (not the published AAR).** The published backend is
  `anki25.09.2` and carries no mastery query; we must compile an rsdroid AAR whose bundled `rslib` is our
  `f15cubing/anki@ea3acae`. This is the only way the *same* engine (with our change) runs on Android.
- **Fork both Android repos + track as submodules (full reproducibility).** Fork
  `ankidroid/Anki-Android-Backend` → `f15cubing/Anki-Android-Backend` (rsdroid) and
  `ankidroid/Anki-Android` → `f15cubing/Anki-Android`; add both as outer git submodules; repoint
  rsdroid's **nested** `anki` submodule to `f15cubing/anki@ea3acae`. `git clone --recursive` then
  reproduces the whole graph. (Mirrors how we forked `anki` for W1.)
- **Current-platform build only (this is rsdroid's default).** rsdroid's `./build.sh` compiles `rslib`
  for the **current platform only** — the emulator ABI (`arm64-v8a` on Apple Silicon; `x86_64` on Intel)
  plus a **host `.jar` for Robolectric** — so we need no ABI configuration; we just run the default
  build. All-ABI cross-compiles happen only in rsdroid's CI release workflow; the all-ABI signed release
  APK (physical phones) is **deferred to Sunday packaging** (Day 6).
- **Add a read-only Kotlin `Collection.masteryQuery(...)` binding + prove reachability (two layers).** The
  W1 spec explicitly hands the Kotlin wrapper + review session to W3. Proof is two complementary layers
  (see §4): a fast **Robolectric JVM test** against the host `.jar` `build.sh` produces (proves the
  binding + our compiled `rslib` logic), **plus** a light **on-emulator smoke** calling `masteryQuery` on
  the running emulator (the definitive "crosses JNI on Android" proof). An instrumented `androidTest` is
  an optional automated upgrade of that on-emulator smoke.
- **Do not re-test the engine per platform.** Undo / no-corruption / read-only invariants were proven in
  W1 against this exact `rslib`; Android runs the identical compiled engine. W3 adds only a light
  **on-device no-corruption smoke** (review → close → reopen → `quick_check` ok), not a second full
  invariant suite.

## Global constraints (hard ceilings)

- **Read-only mastery path on Android too.** The Kotlin wrapper mirrors the engine invariant: it calls
  the read RPC and must **not** be wrapped in `undoableOp { }`; the RPC returns a plain response message,
  never `OpChanges` (`rslib.md`, `rsdroid.md`). All collection access goes through
  `CollectionManager.withCol { }` (single IO queue), never the deprecated `LibAnki` globals.
- **Never corrupt the collection / break undo.** The on-device smoke asserts a clean reopen +
  `quick_check` after a real review session; the review path is stock AnkiDroid (we add no scheduler code).
- **Same engine, not a reimplementation.** The mastery numbers on Android come from the bundled `rslib`
  via JNI — no Kotlin-side statistics. (This is the whole point of D1/D3: one engine, shipped to both.)
- **Version skew must be reconciled, not ignored.** Published backend `anki25.09.2` vs our `25.09.4`:
  handled by repointing rsdroid's nested `anki` to our fork and choosing the rsdroid base commit whose
  vendored anki is closest to `25.09.x` (§3).
- **Lane = engine lane by risk** (§6): touches the `Anki-Android` submodule, adds the
  `Anki-Android-Backend` submodule, and ships `rslib` to a new platform. Extra gate + verified by a
  **different agent**; never self-merge.

---

## 1. Architecture & submodule topology

The fork graph (new pieces marked **NEW**):

```
speedrun (outer repo)
├── anki                    → f15cubing/anki@ea3acae            (ours; W1 rslib change — unchanged here)
├── Anki-Android            → f15cubing/Anki-Android@<pin>      NEW fork: Kotlin masteryQuery binding
│                                                                        + local_backend wiring + test
└── Anki-Android-Backend    → f15cubing/Anki-Android-Backend@<pin>  NEW fork: rsdroid (build the AAR)
        └── anki (nested)   → f15cubing/anki@ea3acae            repointed to OUR fork ⇒ bundles our rslib
```

Data path once built (no new engine RPC — we only *call* W1's):

```
AnkiDroid feature/test (Kotlin)
   │  CollectionManager.withCol { masteryQuery(topics) }
   ▼
libanki Collection.masteryQuery(...)  ──typed──▶ net.ankiweb.rsdroid.Backend.masteryQuery(req)
   │                                                     │ JNI
   ▼                                                     ▼
   rebuilt librsdroid.so (bundled rslib = f15cubing/anki@ea3acae) ── same MasteryQuery RPC as desktop
```

Three isolated concerns: **backend build** (rsdroid AAR), **binding** (`libanki` Kotlin wrapper),
**proof/UX** (review session + reachability test). Each is independently verifiable.

## 2. Components & files

| Layer | Repo / path | Action |
|---|---|---|
| Backend fork | `f15cubing/Anki-Android-Backend` *(new fork)* | fork rsdroid; repoint nested `anki` → `f15cubing/anki@ea3acae`; build the AAR (emulator ABI) |
| Outer submodule | `.gitmodules` + gitlink `Anki-Android-Backend/` *(new)* | add rsdroid fork as a recursive submodule, pinned |
| Android fork | `f15cubing/Anki-Android` *(new fork)* | repoint outer `Anki-Android` submodule url from upstream → our fork; pin |
| Backend wiring | `Anki-Android/local.properties` | `local_backend=true` → file-deps to the locally built rsdroid AAR (overrides the published `0.1.64-anki25.09.2`) |
| Kotlin binding | `Anki-Android/libanki/.../Collection.kt` (+ a small `stats/` extension) | `Collection.masteryQuery(topics): List<TopicMastery>`, following `stats/BackendStats.kt` (`backend.graphsRaw`/`cardStatsRaw`); read-only |
| Reachability test | `Anki-Android/libanki/src/test/.../stats/MasteryQueryTest.kt` *(new)* + on-emulator smoke | Robolectric JVM test (host `.jar`) asserting `col.masteryQuery` rows/rollup; plus a light on-emulator `masteryQuery` smoke (§4) |
| Docs | `docs/codebase/rsdroid.md`, `INDEX.md`, `architecture.md`, `README.md` (pinned versions), `STATUS.md`, `execution-plan.md` | record the rebuilt-backend + fork SHAs; move Android row to Built; check Wednesday's Android box |

**No changes to `anki/` (rslib/pylib/qt) in W3** — the engine is done. W3 is Android-side wiring + a
backend rebuild only.

## 3. Build & wiring recipe (the risky part — sequenced defensively)

1. **Toolchain probe FIRST (before any forking/wiring).** Confirm the Android Rust cross-compile works
   at all: install the emulator's Rust target (e.g. `aarch64-linux-android`) + `cargo-ndk`, ensure NDK is
   present, and build a *trivial* rsdroid artifact for the one ABI. This is the single highest-risk
   unknown (Spike 2 used the **published** AAR and never cross-compiled `rslib`). If this can't be made
   to work in-budget, invoke the fallback (§7) instead of burning the day.
2. **Fork rsdroid** → `f15cubing/Anki-Android-Backend`; pick the base commit whose vendored `anki` is
   closest to `25.09.x`; recursively init; **repoint its nested `anki`** to `f15cubing/anki@ea3acae`;
   rebuild.
3. **Build via rsdroid's `./build.sh`** (default = current platform → emulator `.aar` + host `.jar`); it
   installs `cargo-ndk` and drives `./gradlew assembleRelease`. Repoint the nested `anki` to our fork
   using rsdroid's own "test a specific anki version" recipe (`cd anki && git fetch <ours> && git
   checkout ea3acae --recurse-submodules`, then `./build.sh`, then `cargo check` to refresh `Cargo.lock`;
   confirm `rust-toolchain.toml` matches our anki). Bump `gradle.properties` `VERSION_NAME`
   (→ `<backend>-anki25.09.4`), bundling **our** `librsdroid.so`.
4. **Fork AnkiDroid** → `f15cubing/Anki-Android`; repoint the outer `Anki-Android` submodule url to it;
   set `local_backend=true` in `local.properties`; make `build.gradle`'s `ext.ankidroid_backend_version`
   equal rsdroid's `VERSION_NAME` (rsdroid **requires** the two match) so AnkiDroid links our local
   backend (resolving the `25.09.2`→`25.09.4` skew).
5. `source .androidenv` → `./gradlew assembleFullDebug` → install on the running emulator.

All commands are captured in `docs/codebase/rsdroid.md` (build recipe) as they're verified, per the
`building-and-testing` "mark verified on first success" rule.

## 4. Kotlin mastery binding + reachability proof

**Binding.** Add `Collection.masteryQuery(topics: List<String>): List<TopicMastery>` in `libanki`,
modeled on `stats/BackendStats.kt` (the doc-blessed template for a new read RPC wrapper). It calls the
typed generated `backend.masteryQuery(...)` (name mirrors the desktop RPC) and marshals the `anki.*`
protobuf response. **Read-only:** no `undoableOp { }`; reached via `CollectionManager.withCol { }`.

**Reachability proof (two complementary layers).** `./build.sh` produces **both** the emulator `.aar`
*and* a host `.jar` (for Robolectric) from our fork, so we prove reachability at two levels:

1. **Automated — Robolectric JVM test (host `.jar`).** In `libanki/src/test`, extend `InMemoryAnkiTest`
   (which loads the host lib via `RustBackendLoader`), add a couple of `topic::*`-tagged cards, call
   `col.masteryQuery(...)`, and assert the rows are well-formed (`totalCards` counts matching cards; a
   hierarchical parent tag returns rolled-up counts ≥ its leaf). Because the host `.jar` is built from
   our fork, this exercises **our** `rslib` + the generated `backend.masteryQuery` + the Kotlin wrapper —
   fast, deterministic, and the natural AnkiDroid test pattern. Its one limit: it runs on the desktop JVM,
   not on Android.
2. **On-device — emulator smoke (the `.aar`, real JNI).** On the running emulator, invoke `masteryQuery`
   once (debug entry point or logged during the review flow) and record a sane result. This is the
   definitive proof our change **crosses JNI on Android**. An instrumented `androidTest` asserting the
   same is an optional automated upgrade if the harness cooperates within budget.

Together: layer 1 proves the logic + binding against our compiled engine; layer 2 proves it actually
executes on Android. The assertion in both: *`masteryQuery` returns our engine's numbers.*

## 5. Review-session gate + engine-safety

- **Gate (Milestone 1):** install the app on the emulator, load the seeded `topic::*` GRE deck, run a
  **real FSRS review session** — answer several cards across Again/Hard/Good/Easy through the normal
  AnkiDroid reviewer — on the shared engine.
- **On-device no-corruption smoke:** after the session, close and reopen the app; the collection opens
  cleanly and `quick_check` (via the standard AnkiDroid check-database path) reports OK. This is the only
  engine-safety check W3 adds — the heavy invariants were W1's job on the same `rslib`.
- **No scheduler/engine code is added on Android** — the review path is stock AnkiDroid; we only put our
  engine underneath it and add a read-only query binding.

## 6. Lane (engine lane, by risk)

W3 is **engine-lane** even though it adds no new `rslib` logic, because it (a) modifies the `Anki-Android`
submodule url + gitlink, (b) adds the `Anki-Android-Backend` submodule, and (c) ships `rslib` to a new
runtime. Consequences per `shipping-changes`:

- **Base gate + extra gate**, verified by a **different agent**; **never self-merge.**
- The extra gate is **light because no new engine logic ships** — W1 already proved undo / no-corruption /
  read-only / ≥3 Rust + Python tests on this exact code. For W3 the reviewer confirms: the Kotlin wrapper
  is read-only (no `undoableOp`), the RPC returns a plain message (not `OpChanges`), the on-device
  no-corruption smoke passed, and the reachability proof was run **against the rebuilt AAR** (not the
  published one). "Files touched + merge-difficulty" note included.
- Submodule mechanics per `working-with-submodules`: pin bumps + `.gitmodules` edits land with the docs'
  `Last verified against:` SHAs in the same PR.

## 7. Risks & fallbacks

- **#1 — rsdroid compiles from source at all.** NDK + Android Rust target + `cargo-ndk` was never
  exercised (Spike 2 used the published AAR). *Mitigation:* the §3.1 toolchain probe up front. *Fallback:*
  if the full build is intractable within budget, **record the blocker honestly** and keep W1's desktop
  proof as the shipped Rust evidence, explicitly noting the Android-engine gap — after a real attempt, not
  instead of one. (This is a documented honest-failure, not a silent skip.)
- **Version skew (`25.09.2` vs `25.09.4`).** *Mitigation:* repoint rsdroid's nested `anki` to our fork +
  choose the rsdroid base commit closest to `25.09.x`; if the rsdroid build scripts assume a different
  anki layout, pin to the rsdroid tag matching our anki minor.
- **Two proof layers, one build.** `./build.sh` emits both the emulator `.aar` and the host `.jar`, so
  the Robolectric test (host) and the on-emulator smoke (Android) both come from a single default build —
  no extra ABI cross-compiles needed (§4).
- **`BACKEND_VERSION` mismatch.** rsdroid requires `gradle.properties` `VERSION_NAME` to equal AnkiDroid
  `build.gradle` `ext.ankidroid_backend_version`; a mismatch fails the local-backend wiring. Set both to
  the same `<backend>-anki25.09.4` value in the same change.
- **Two-level submodule friction.** rsdroid vendors `anki` as its own submodule; always
  `git submodule update --init --recursive`. Documented in `working-with-submodules`.
- **Emulator image.** arm64 system image on Apple Silicon; confirm the emulator boots our
  `assembleFullDebug` before wiring the backend.

## 8. Tests (spec-required)

- **Reachability — Robolectric (host `.jar`):** a `libanki` JVM test asserting `col.masteryQuery(...)`
  returns well-formed rows (leaf `totalCards` + hierarchical rollup) against our compiled `rslib` (§4).
- **Reachability — on-emulator smoke (`.aar`, real JNI):** call `masteryQuery` once on the emulator and
  record a sane result (optional instrumented `androidTest` upgrade). Both must run against our rebuilt
  backend, never the published one.
- **Read-only assertion (Kotlin):** a unit/instrumented check (or code-review confirmation in the PR) that
  the wrapper does not go through `undoableOp { }` and the response carries no `OpChanges`.
- **On-device no-corruption smoke:** review session → close/reopen → `quick_check` OK.
- **Review-session gate:** manual, recorded (screenshot / short clip) — the Milestone-1 evidence.
- **No new engine tests** — W1 covers the RPC on the shared `rslib`.

## 9. Acceptance

- The rebuilt **rsdroid AAR bundles our `rslib`** (`f15cubing/anki@ea3acae`) and AnkiDroid links it via
  `local_backend=true` (not the published `0.1.64-anki25.09.2`).
- AnkiDroid **runs a real FSRS review session on the shared GRE deck on the emulator**; collection reopens
  cleanly + `quick_check` OK.
- `Collection.masteryQuery(...)` exists in `libanki` (read-only) and is **proven reachable**: a green
  Robolectric test against our host `.jar` **and** an on-emulator `masteryQuery` smoke against the rebuilt
  `.aar` (never the published backend).
- Both new forks pushed; `Anki-Android-Backend` added as a recursive submodule and `Anki-Android`
  repointed to our fork; all pins recorded.
- `rsdroid.md` / `INDEX.md` / `architecture.md` / `README.md` (pinned versions) / `STATUS.md` /
  `execution-plan.md` updated with the new SHAs; the Wednesday Android box is checked.
- Ships **engine-lane**: base + light extra gate, verified by a different agent; no self-merge.

## 10. Out of scope (later)

- **Two-way sync + conflict rules** (W4 / Thursday).
- **Three scores on the phone** and **any Android dashboard/UI** (Friday+; W3 is a review session, not a
  dashboard — mirrors W2 being desktop-only).
- **All-ABI signed release APK** + **physical-device install** (Sunday packaging, Day 6).
- **Interleaving / MCQ / timed mode** on Android (Thursday+).
- Bumping `Anki-Android` off `v2.24.0` for any reason other than the binding + wiring this spec requires.
