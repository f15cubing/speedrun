# W3 — Android Review on the Shared Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the rsdroid Android backend against our anki fork so its bundled `rslib` carries the W1 mastery-query change, wire it into an AnkiDroid fork, run a real FSRS review session on the shared GRE deck on an emulator (the Milestone-1 gate), and prove `masteryQuery` is reachable from Kotlin.

**Architecture:** Fork `Anki-Android-Backend` (rsdroid) and `Anki-Android`, track both as outer git submodules. Repoint rsdroid's nested `anki` submodule to `f15cubing/anki@ea3acae` and rebuild via rsdroid's `./build.sh` (current-platform only → emulator `.aar` + host `.jar`). AnkiDroid links the local backend (`local_backend=true`). A read-only `Collection.masteryQuery(...)` binding in `libanki` is proven by a Robolectric JVM test (host `.jar`) plus an on-emulator smoke (real JNI). No new engine code — we only ship the existing W1 `rslib` to Android and add a read wrapper.

**Tech Stack:** Rust (rslib, cross-compiled via `cargo-ndk`), Android NDK, Gradle (AnkiDroid + rsdroid), Kotlin (`libanki`), Robolectric (JVM tests), git submodules (two-level), `gh` (forking), an Android emulator.

## Global Constraints

- **Read-only on Android too:** the Kotlin wrapper calls the read RPC and is **never** wrapped in `undoableOp { }`; the RPC returns a plain `MasteryResponse`, never `OpChanges`. All collection access goes through `CollectionManager.withCol { }` / the test collection — never the deprecated `LibAnki` globals. (`docs/codebase/rsdroid.md`, `rslib.md`.)
- **Same engine, not a reimplementation:** mastery numbers come from the bundled `rslib` via JNI — no Kotlin-side statistics. (PRD D1/D3.)
- **No new engine tests / no `anki/` changes:** W1 already proved undo / no-corruption / read-only on this exact `rslib`. W3 adds only Android-side wiring + a read wrapper + a light on-device no-corruption smoke.
- **Version skew reconciled:** published backend is `anki25.09.2`; our fork is `25.09.4` (`ea3acae`). Repoint rsdroid's nested `anki` to our fork; rsdroid `gradle.properties` `VERSION_NAME` **must equal** AnkiDroid `build.gradle` `ext.ankidroid_backend_version`.
- **Current-platform build only:** rsdroid's `./build.sh` builds the current platform by default (emulator ABI + host `.jar`); all-ABI is CI-only and deferred to Sunday packaging.
- **Lane = engine lane (by risk):** touches the `Anki-Android` submodule, adds the `Anki-Android-Backend` submodule, ships `rslib` to a new platform. Base + light extra gate; **verified by a different agent; never self-merge.** Submodule pin bumps land with the docs' `Last verified against:` SHAs in the same PR.
- **Spec:** `docs/superpowers/specs/2026-07-01-w3-android-review-design.md`. **Consumes W1:** proto `MasteryQuery(MasteryRequest{repeated string topics}) -> MasteryResponse{repeated TopicMastery topics}`; `TopicMastery{topic, total_cards, reviewed_count, mastered_count, avg_recall}`.

## Environment (known facts for this machine)

- Repo root: `/Users/felipecaicedo/Desktop/alpha/speedrun` (outer). Submodules are siblings at the root: `anki/`, `Anki-Android/`, and (new) `Anki-Android-Backend/`.
- macOS on **Apple Silicon** → emulator ABI `arm64-v8a`, Rust target `aarch64-linux-android`.
- `ANDROID_HOME` = `/Users/felipecaicedo/Library/Android/sdk` (from `Anki-Android/local.properties` `sdk.dir`).
- Our anki fork: `https://github.com/f15cubing/anki.git`, commit `ea3acae`.
- GitHub owner for forks: `f15cubing`. Use `gh` for forking.
- rsdroid **must** be named exactly `Anki-Android-Backend` and sit beside `Anki-Android` (hard-coded in AnkiDroid gradle) — our root layout already satisfies this.

**Worktree note:** engine-lane work uses an isolated worktree with recursive submodules. Run all outer-repo git in the worktree root; run submodule builds inside each submodule dir. Because this touches submodules, do **not** reuse the desktop W1/W2 worktree — set up a fresh one per the `using-git-worktrees` + `shipping-changes` skills at execution time.

---

## File Structure

**New outer submodule** `Anki-Android-Backend/` (fork `f15cubing/Anki-Android-Backend`):
- `.gitmodules` (nested) — `anki` submodule url → `https://github.com/f15cubing/anki.git`.
- `anki` (nested gitlink) → `ea3acae`.
- `gradle.properties` — `VERSION_NAME` → `<backend>-anki25.09.4`.
- `Cargo.lock`, `rust-toolchain.toml` — refreshed/aligned to our anki.

**`Anki-Android/` submodule** (repointed to fork `f15cubing/Anki-Android`):
- `local.properties` — add `local_backend=true` (untracked; local only).
- `AnkiDroid/build.gradle` — `ext.ankidroid_backend_version` → match rsdroid `VERSION_NAME`.
- `libanki/src/main/java/com/ichi2/anki/libanki/stats/BackendStats.kt` — **modify**: add `Collection.masteryQuery(...)`.
- `libanki/src/test/java/com/ichi2/anki/libanki/stats/MasteryQueryTest.kt` — **new** Robolectric test.

**Outer repo:**
- `.gitmodules` — add `Anki-Android-Backend`; repoint `Anki-Android` url → fork.
- Docs: `docs/codebase/rsdroid.md`, `docs/codebase/INDEX.md`, `docs/codebase/architecture.md`, `README.md`, `docs/STATUS.md`, `docs/execution-plan.md`.

---

## Task 1: Toolchain probe — fork rsdroid, add submodule, build the stock backend

**Goal/deliverable:** prove the Android Rust cross-compile toolchain works *before* introducing our fork's version skew. Fork rsdroid, add it as a recursive submodule pinned to a `25.09.x`-era base, and build it **unmodified** for the current platform. If this can't be made to work in-budget, STOP and invoke the fallback (spec §7) rather than burning the day.

**Files:**
- Create (outer): `.gitmodules` entry + gitlink `Anki-Android-Backend/`

**Interfaces:**
- Produces: a locally-built stock `rsdroid` `.aar` + host `.jar`; a pinned `Anki-Android-Backend` submodule.

- [ ] **Step 1: Fork rsdroid on GitHub**

```bash
gh repo fork ankidroid/Anki-Android-Backend --clone=false   # forks to your account (f15cubing)
# if f15cubing is an org instead: add --org f15cubing
```
Expected: `f15cubing/Anki-Android-Backend` exists.

- [ ] **Step 2: Add it as a recursive submodule at the repo root**

Run from the outer worktree root:
```bash
git submodule add https://github.com/f15cubing/Anki-Android-Backend.git Anki-Android-Backend
cd Anki-Android-Backend && git submodule update --init --recursive && cd ..
```
Expected: `Anki-Android-Backend/` exists with its nested `anki/` populated.

- [ ] **Step 3: Pin rsdroid to a `25.09.x`-era base (script compatibility)**

Find the rsdroid commit whose bundled anki matches our base minor, to minimize skew:
```bash
cd Anki-Android-Backend
grep -n "VERSION_NAME" gradle.properties        # note the current -anki<version> suffix
git log --oneline -- gradle.properties | head -20
# check out the commit whose VERSION_NAME ends with -anki25.09.2 (matches Spike 2's published backend);
# if main already vendors 25.09.x you may stay on main.
# git checkout <that-commit>
cd ..
```
Record the chosen commit in the PR notes. (If `main` already targets `25.09.x`, staying on `main` is fine.)

- [ ] **Step 4: Install the Android Rust target + NDK + build env**

Run inside `Anki-Android-Backend/`:
```bash
cd Anki-Android-Backend
rustup target add aarch64-linux-android
cargo install toml-cli
export ANDROID_HOME="$HOME/Library/Android/sdk"
ANDROID_NDK_VERSION=$(toml get gradle/libs.versions.toml versions.ndk --raw)
sdkmanager --install "ndk;$ANDROID_NDK_VERSION"     # if sdkmanager is on PATH; else install via Android Studio SDK Manager
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/$ANDROID_NDK_VERSION"
# JDK 21 (or Android Studio's bundled JBR):
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
./tools/install-n2 || true   # n2/ninja for the anki build
```
Expected: target added, NDK present at `$ANDROID_NDK_HOME`, `cargo`/`java` on PATH.

- [ ] **Step 5: Build the stock backend (the probe)**

```bash
# still in Anki-Android-Backend/, env from Step 4 exported
./build.sh
```
Expected: build completes; a `.aar` and a host `.jar` are produced. Locate them:
```bash
ls -R . | grep -Ei '\.(aar|jar)$' | grep -i rsdroid
```
If `build.sh` fails on toolchain/NDK, fix env and retry. If it is fundamentally intractable within budget, STOP → fallback (spec §7): record the blocker, keep W1's desktop proof, and skip to Task 5 documenting the honest gap.

- [ ] **Step 6: Commit the submodule addition (outer repo)**

```bash
cd ..   # outer worktree root
git add .gitmodules Anki-Android-Backend
git commit -m "build(w3): add Anki-Android-Backend (rsdroid) fork as submodule; toolchain probe green"
```

---

## Task 2: Bundle our engine — repoint rsdroid's nested anki to our fork and rebuild

**Goal/deliverable:** an rsdroid backend whose bundled `rslib` is `f15cubing/anki@ea3acae` (our mastery-query change), with the version skew reconciled and the version label bumped.

**Files:**
- Modify (rsdroid fork): `.gitmodules` (nested), `anki` gitlink, `gradle.properties`, `Cargo.lock`, `rust-toolchain.toml`
- Modify (outer): `Anki-Android-Backend` gitlink

**Interfaces:**
- Consumes: the working `./build.sh` from Task 1.
- Produces: a rebuilt `.aar` + host `.jar` bundling our `rslib`; rsdroid `VERSION_NAME = <backend>-anki25.09.4`.

- [ ] **Step 1: Point the nested anki submodule at our fork**

```bash
cd Anki-Android-Backend
# add our fork as the anki submodule's URL and sync
git config -f .gitmodules submodule.anki.url https://github.com/f15cubing/anki.git
git submodule sync anki
cd anki
git fetch origin
git checkout ea3acae --recurse-submodules
cd ..
```
Expected: `Anki-Android-Backend/anki` HEAD is `ea3acae`.

- [ ] **Step 2: Rebuild against our anki + refresh lockfile**

```bash
# env from Task 1 Step 4 still exported
./build.sh
cargo check       # updates Cargo.lock with any versions from our submodule
```
Expected: build + `cargo check` succeed. If `rust-toolchain.toml` differs from our anki's, align it:
```bash
diff <(cat rust-toolchain.toml) <(cat anki/rust-toolchain.toml) || cp anki/rust-toolchain.toml rust-toolchain.toml
./build.sh   # rebuild if toolchain changed
```

- [ ] **Step 3: Bump the version label**

Edit `Anki-Android-Backend/gradle.properties`: set `VERSION_NAME` so its `-anki` suffix reads `25.09.4` (keep the `<backend>` prefix, e.g. `0.1.64-anki25.09.4`). Record the exact value — Task 3 must match it.

- [ ] **Step 4: Commit inside the rsdroid fork and push**

```bash
cd Anki-Android-Backend
git add .gitmodules anki gradle.properties Cargo.lock rust-toolchain.toml
git commit -m "feat: bundle f15cubing/anki@ea3acae (W1 mastery query); bump VERSION_NAME -> *-anki25.09.4"
git push origin HEAD
cd ..
```

- [ ] **Step 5: Bump the outer submodule pin**

```bash
git add Anki-Android-Backend
git commit -m "build(w3): pin rsdroid fork to our-rslib build (anki@ea3acae)"
```

---

## Task 3: Wire AnkiDroid to the local backend + run the review-session gate

**Goal/deliverable:** the Milestone-1 gate — AnkiDroid runs a real FSRS review session on the shared GRE deck on the emulator, using **our** rebuilt backend, and the collection reopens cleanly.

**Files:**
- Modify (outer): `.gitmodules` (`Anki-Android` url → fork), `Anki-Android` gitlink
- Modify (AnkiDroid fork): `AnkiDroid/build.gradle` (`ext.ankidroid_backend_version`)
- Local only (untracked): `Anki-Android/local.properties` (`local_backend=true`)

**Interfaces:**
- Consumes: rsdroid `VERSION_NAME` from Task 2 Step 3; the built backend artifacts from Task 2.
- Produces: an installed debug APK running our engine; a recorded review session.

- [ ] **Step 1: Fork AnkiDroid and repoint the submodule**

```bash
gh repo fork ankidroid/Anki-Android --clone=false   # forks to your account (f15cubing)
git config -f .gitmodules submodule.Anki-Android.url https://github.com/f15cubing/Anki-Android.git
git submodule sync Anki-Android
cd Anki-Android && git remote set-url origin https://github.com/f15cubing/Anki-Android.git && cd ..
```
Expected: `.gitmodules` `Anki-Android` url is the fork; the submodule's `origin` is the fork.

- [ ] **Step 2: Enable the local backend + match the version**

Append to `Anki-Android/local.properties` (untracked — keeps `sdk.dir`):
```
local_backend=true
```
Edit `Anki-Android/AnkiDroid/build.gradle`: set `ext.ankidroid_backend_version` to the exact rsdroid `VERSION_NAME` from Task 2 Step 3 (e.g. `0.1.64-anki25.09.4`).

- [ ] **Step 3: Build the debug APK**

```bash
cd Anki-Android
export ANDROID_HOME="$HOME/Library/Android/sdk"
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
# if .androidenv.example exists, prefer: cp .androidenv.example .androidenv && edit && source .androidenv
./gradlew assembleFullDebug
cd ..
```
Expected: `BUILD SUCCESSFUL`; APK under `Anki-Android/AnkiDroid/build/outputs/apk/full/debug/`. (If the variant name differs, list with `./gradlew tasks --all | grep -i assemble`.)

- [ ] **Step 4: Boot an arm64 emulator and install**

```bash
"$ANDROID_HOME/emulator/emulator" -list-avds
# create one if needed via Android Studio Device Manager (arm64-v8a system image)
"$ANDROID_HOME/emulator/emulator" -avd <avd-name> -no-snapshot -no-boot-anim &
"$ANDROID_HOME/platform-tools/adb" wait-for-device
cd Anki-Android && ./gradlew installFullDebug && cd ..
```
Expected: AnkiDroid installs and launches on the emulator.

- [ ] **Step 5: Load the deck and run a real review session (the gate)**

Manual, on the emulator:
1. Build the seeded GRE deck if not already an `.apkg`: from repo root, `python pipeline/build_deck.py --seed 42` (see `pipeline/README.md`), then push + import it, or import via `adb push` to the emulator's storage and open in AnkiDroid.
2. Enable FSRS (Deck options ▸ FSRS) if not on.
3. Study several cards, pressing **Again / Hard / Good / Easy** across the buttons.
4. Record a screenshot or short screen-capture of the review in progress — this is the Milestone-1 evidence.

- [ ] **Step 6: On-device no-corruption smoke**

On the emulator: fully close AnkiDroid, reopen it, then run **Settings ▸ Advanced ▸ Check Database** (the `quick_check` path). Expected: "Database rebuilt/optimized" with **no** corruption reported; the deck + review history persist.

- [ ] **Step 7: Commit the wiring**

```bash
cd Anki-Android
git add AnkiDroid/build.gradle
git commit -m "build: link local rsdroid backend (anki25.09.4) for W3"
git push origin HEAD
cd ..
git add .gitmodules Anki-Android
git commit -m "build(w3): repoint Anki-Android to fork; pin local-backend wiring"
```

---

## Task 4: Kotlin `masteryQuery` binding + Robolectric proof + on-emulator smoke

**Goal/deliverable:** a read-only `Collection.masteryQuery(...)` in `libanki`, proven reachable by a green Robolectric test (host `.jar`) and confirmed once on the emulator (real JNI).

**Files:**
- Modify: `Anki-Android/libanki/src/main/java/com/ichi2/anki/libanki/stats/BackendStats.kt`
- Create: `Anki-Android/libanki/src/test/java/com/ichi2/anki/libanki/stats/MasteryQueryTest.kt`

**Interfaces:**
- Consumes: generated `backend.masteryQuery(...)` + `anki.stats.*` types from the rebuilt backend (Task 2).
- Produces: `fun Collection.masteryQuery(topics: List<String>): List<anki.stats.TopicMastery>`.

- [ ] **Step 1: Write the failing Robolectric test**

Create `Anki-Android/libanki/src/test/java/com/ichi2/anki/libanki/stats/MasteryQueryTest.kt`:

```kotlin
/*
 * Copyright (c) 2026 Ankitects Pty Ltd and contributors
 * License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
 */
package com.ichi2.anki.libanki.stats

import com.ichi2.anki.libanki.testutils.InMemoryAnkiTest
import org.hamcrest.MatcherAssert.assertThat
import org.hamcrest.Matchers.equalTo
import org.hamcrest.Matchers.greaterThanOrEqualTo
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class MasteryQueryTest : InMemoryAnkiTest() {
    @Test
    fun masteryQuery_is_reachable_and_rolls_up_hierarchically() {
        val leafTag = "topic::calculus::integral_single"
        val basic = col.notetypes.byName("Basic")!!
        repeat(2) { i ->
            val note = col.newNote(basic)
            note.setItem("Front", "front$i")
            note.setItem("Back", "back$i")
            note.addTag(leafTag)
            col.addNote(note)
        }

        val rows = col.masteryQuery(listOf(leafTag, "topic::calculus"))

        assertThat(rows.size, equalTo(2))
        val leaf = rows.first { it.topic == leafTag }
        val bucket = rows.first { it.topic == "topic::calculus" }
        assertThat(leaf.totalCards.toInt(), greaterThanOrEqualTo(2))
        // hierarchical parent tag includes the leaf's cards
        assertThat(bucket.totalCards.toInt(), greaterThanOrEqualTo(leaf.totalCards.toInt()))
    }
}
```

- [ ] **Step 2: Run it to verify it fails**

```bash
cd Anki-Android
./gradlew :libanki:testDebugUnitTest --tests "com.ichi2.anki.libanki.stats.MasteryQueryTest"
cd ..
```
Expected: FAIL — `col.masteryQuery` unresolved (binding missing). (If the whole module fails to compile because the generated `masteryQuery`/`anki.stats.*` symbols are absent, that means the local backend from Task 2 isn't wired — fix Task 3 Step 2 before continuing.)

- [ ] **Step 3: Implement the read-only binding**

Append to `Anki-Android/libanki/src/main/java/com/ichi2/anki/libanki/stats/BackendStats.kt`:

```kotlin
import anki.stats.TopicMastery

/**
 * Read-only per-topic mastery aggregate (GRE, PRD §5 / W1). Calls the shared
 * rslib MasteryQuery RPC over JNI. Read-only: never wrapped in undoableOp.
 * Each tag matches itself AND its ::* descendants (hierarchical).
 */
fun Collection.masteryQuery(topics: List<String>): List<TopicMastery> =
    backend.masteryQuery(topics = topics).topicsList
```

If the generated typed method is named/shaped differently, use the always-present raw variant (same result):

```kotlin
import anki.stats.MasteryRequest
import anki.stats.MasteryResponse
import anki.stats.TopicMastery

fun Collection.masteryQuery(topics: List<String>): List<TopicMastery> {
    val req = MasteryRequest.newBuilder().addAllTopics(topics).build()
    return MasteryResponse.parseFrom(backend.masteryQueryRaw(req.toByteArray())).topicsList
}
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd Anki-Android
./gradlew :libanki:testDebugUnitTest --tests "com.ichi2.anki.libanki.stats.MasteryQueryTest"
cd ..
```
Expected: PASS (1 test). This proves the binding + generated backend method + our compiled `rslib` on the host JVM.

- [ ] **Step 5: On-emulator smoke (real JNI)**

With the emulator running (Task 3) and the app rebuilt/installed (`./gradlew installFullDebug`), invoke the binding once on-device and capture the result. Lightweight options (pick one):
- Temporary debug hook: in a debug-only menu/action, call `CollectionManager.withCol { masteryQuery(listOf("topic::calculus")) }` and `Timber.i(...)` the rows; read via `adb logcat | grep -i mastery`.
- Or the built-in JS/dev console if enabled.

Record the logged rows (screenshot / paste) as the on-device proof. Remove any temporary debug hook before committing (or guard it behind `BuildConfig.DEBUG` and note it).

- [ ] **Step 6: Commit**

```bash
cd Anki-Android
git add libanki/src/main/java/com/ichi2/anki/libanki/stats/BackendStats.kt libanki/src/test/java/com/ichi2/anki/libanki/stats/MasteryQueryTest.kt
git commit -m "feat(libanki): read-only Collection.masteryQuery + Robolectric reachability test"
git push origin HEAD
cd ..
git add Anki-Android
git commit -m "build(w3): pin AnkiDroid fork with masteryQuery binding"
```

---

## Task 5: Docs, pins, STATUS/execution-plan (engine-lane finalization)

**Goal/deliverable:** every doc that records an Android/rsdroid pin is updated in this same change; the Android row moves to Built; the Wednesday Android box is checked; the PR is ready for a **different-agent** review.

**Files (outer repo):**
- Modify: `docs/codebase/rsdroid.md`, `docs/codebase/INDEX.md`, `docs/codebase/architecture.md`, `README.md`, `docs/STATUS.md`, `docs/execution-plan.md`

- [ ] **Step 1: Update `rsdroid.md`**

- Record that AnkiDroid now links a **locally-built** rsdroid from our fork (`f15cubing/Anki-Android-Backend`) whose bundled `rslib` = `f15cubing/anki@ea3acae`, via `local_backend=true` + matched `VERSION_NAME`/`ext.ankidroid_backend_version` (`*-anki25.09.4`).
- Add the `Collection.masteryQuery(topics): List<TopicMastery>` binding under "Public interface" (read-only, follows `BackendStats.kt`).
- Capture the verified build recipe (Task 1–2 commands) in a "Building rsdroid from source (W3)" subsection — the first verified run, per `building-and-testing`.
- Bump `Last verified against:` to the new fork SHAs.

- [ ] **Step 2: Update INDEX + architecture + README pins**

- `docs/codebase/INDEX.md`: move the Android row to reflect our forks; add a "Mastery Query on Android (W3)" code-path row (`Anki-Android/libanki/.../stats/BackendStats.kt`, `Anki-Android-Backend` bundling `anki@ea3acae`); bump the footer `Last verified against:`.
- `docs/codebase/architecture.md`: update the pinned SHAs / rsdroid arrow to show our locally-built backend.
- `README.md`: update the **"Pinned upstream versions"** block — repoint `Anki-Android` to the fork commit, add `Anki-Android-Backend` (fork commit; bundles `anki@ea3acae`).

- [ ] **Step 3: Update STATUS + execution-plan**

- `docs/STATUS.md`: add a **Done** line — "PR #<n> — W3 Android review: rebuilt rsdroid (our `rslib`) + `local_backend` + review session on emulator + `masteryQuery` binding (Robolectric + on-emulator smoke). Forks: `Anki-Android@<sha>`, `Anki-Android-Backend@<sha>` (bundles `anki@ea3acae`)."; clear In flight.
- `docs/execution-plan.md`: check the Wednesday **Android** box ("Loads the exam deck; runs a real review session on the shared engine") and the critical-path "rsdroid build with our change" item.

- [ ] **Step 4: Commit**

```bash
git add docs/codebase/rsdroid.md docs/codebase/INDEX.md docs/codebase/architecture.md README.md docs/STATUS.md docs/execution-plan.md
git commit -m "docs(w3): record Android review + local rsdroid backend; bump pins"
```

- [ ] **Step 5: Open the PR and request a different-agent review (engine lane)**

Push the branch and open the PR with the engine-lane body (base + extra gate). The extra-gate section is light (no new engine logic): confirm the Kotlin wrapper is read-only (no `undoableOp`), the RPC returns a plain message (not `OpChanges`), the on-device no-corruption smoke passed, and the reachability proofs ran against **our rebuilt backend** (host `.jar` + emulator `.aar`), not the published one. Include the "files touched + merge-difficulty" note and the two-level-submodule pins. **Do not self-merge** — a different agent verifies against `.cursor/skills/shipping-changes/pr-checklist.md`.

---

## Self-Review

**1. Spec coverage:**
- §Decisions (rebuild rsdroid vs fork; fork both + submodules; current-platform build; read-only binding + two-layer proof; no per-platform engine re-test) → Task 1 (fork+probe), Task 2 (bundle our rslib), Task 3 (fork AnkiDroid + wire + gate + no-corruption smoke), Task 4 (binding + Robolectric + on-emulator smoke).
- §1 topology / §2 components → Tasks 1–4 build the exact fork graph + files in the table.
- §3 build recipe (build.sh, "specific anki version" checkout, BACKEND_VERSION match) → Task 1 Step 4–5, Task 2 Step 1–3, Task 3 Step 2.
- §4 reachability (Robolectric host `.jar` + on-emulator smoke) → Task 4 Steps 1–5.
- §5 review gate + on-device no-corruption smoke → Task 3 Steps 5–6.
- §6 engine lane + different-agent review → Task 5 Step 5 + Global Constraints.
- §7 risks (toolchain probe first; version skew; BACKEND_VERSION; two-level submodules) → Task 1 (probe + fallback), Task 2 (skew), Task 3 (version match).
- §8 tests → Task 3 (gate + smoke) + Task 4 (Robolectric + on-emulator).
- §9 acceptance → Task 5 (docs/pins) + the deliverables of Tasks 2–4.

**2. Placeholder scan:** No "TBD"/"implement later". Build/gradle steps give the known command plus a real discovery fallback (`toml get`, `./gradlew tasks`, `ls`) where a name is environment-determined — these are executable, not placeholders. Kotlin code (binding + test) is complete, with a guaranteed raw-variant fallback for the one codegen-name assumption.

**3. Type consistency:** `Collection.masteryQuery(topics: List<String>): List<TopicMastery>` is defined once (Task 4 Step 3) and consumed identically by the test (Task 4 Step 1) and the on-emulator smoke (Step 5). `TopicMastery` fields used (`topic`, `totalCards`) match the proto (`topic`, `total_cards` → generated `totalCards`). rsdroid `VERSION_NAME` (Task 2 Step 3) == AnkiDroid `ext.ankidroid_backend_version` (Task 3 Step 2) — same `*-anki25.09.4` string. Submodule pins bumped in Tasks 2/3/4 are finalized/recorded in Task 5.

---

## Execution Handoff

Two execution options:
1. **Subagent-Driven (recommended)** — a fresh subagent per task, two-stage review between tasks. Note: Tasks 1–3 are environment-heavy (emulator, NDK, real builds) and may need an interactive/mac session rather than a headless subagent.
2. **Inline Execution** — batch execution in this session with checkpoints.
