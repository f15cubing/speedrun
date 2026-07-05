# Speedrun — a GRE *Mathematics Subject Test* study app on a fork of Anki

> **Exam:** GRE **Mathematics** Subject Test (200–990 scale).
> **Thesis:** flashcards measure *memory*; a real exam needs *performance* and *readiness* too.
> This project builds the two missing bridges on top of Anki's engine and is **honest about
> uncertainty** — every score is a range with an evidence panel, and the app refuses to score when
> it lacks evidence.

Two apps over **one shared engine**: a desktop app (Anki/Qt) and an Android companion (AnkiDroid),
both driving the same Rust engine (`rslib`) and syncing between devices. The one real engine change
is a read-only **Mastery Query** RPC (see `docs/PRD.md` §5).

## Architecture overview

The system is **two client apps over one shared Rust engine.**

- **The engine** is Anki's `rslib` (Rust): FSRS scheduling, the due-card queue, SQLite storage,
  collection sync, and undo/transactions. It is the single source of truth for card state, and every
  capability is exposed as a **protobuf RPC**. Our one engine change lives here.
- **Desktop** (`anki/`) is Qt + Python (`aqt`). Python reaches the engine through `pylib` and the
  `rsbridge` PyO3 native module — a method call serialises a protobuf request, crosses into Rust, and
  parses the protobuf response.
- **Android** (`Anki-Android/`) is AnkiDroid (Kotlin). It reaches the **same** `rslib` through the
  **`rsdroid`** AAR over JNI (again, protobuf in/out). Because our change is in `rslib`, it ships to
  the phone for free once `rsdroid` is rebuilt from our fork.
- **Sync** reconciles the two runtimes through a self-hosted `anki-sync-server` (revlog **unioned**,
  card scheduling **last-writer-wins**).

```
           DESKTOP (Anki / Qt + Python)                ANDROID (AnkiDroid / Kotlin)
           review · dashboard · scoring                review · read-only 3-score panel
                   │ pylib + rsbridge (protobuf)               │ rsdroid AAR — JNI (protobuf)
                   ▼                                           ▼
      ┌──────────────────────────────────────────────────────────────────┐
      │  SHARED ENGINE — Anki rslib (Rust), embedded in BOTH apps          │
      │  FSRS · due queue · SQLite storage · sync · undo / transaction     │
      │  + NEW: Mastery Query RPC  (read-only — never returns OpChanges)    │
      └──────────────────────────────────────────────────────────────────┘
                   ▲  two-way sync (revlog union + scheduling LWW)
                   └──────────────►  anki-sync-server (self-hosted)  ◄───────

   Scoring / AI / UX layers sit ABOVE the engine (switch-off-able):
     Memory (FSRS R) → Performance (logistic + Platt) → Readiness (percentile + conformal)
```

*(Full mermaid diagrams — engine module map, RPC/FFI boundary, mastery-query data flow, three-score
gate, sync conflict resolution — are in `docs/codebase/architecture.md`.)*

**The three-score layer is desktop-authoritative.** Memory / Performance / Readiness are computed on
the desktop (the pure-Python `scoring/` package + a thin Qt adapter), written to a small **synced
`gre_scorecard`** JSON in `col.conf`, and rendered **read-only on the phone**. One source of truth,
no model duplication: the phone shows the same three ranges the desktop computed, stamped "computed
on desktop, last updated \<t\>." The three scores are **never blended**, and **Readiness is always a
range with an evidence panel** that refuses to show a number without enough evidence (the give-up
rule). One-page model descriptions:

| Score | Measures | Math | Doc |
|---|---|---|---|
| **Memory** | P(recall a card now) | FSRS retrievability + **Wilson** interval | [`docs/models/memory.md`](docs/models/memory.md) |
| **Performance** | P(correct on an unseen exam item) | **logistic + Platt**, Fisher-SE interval | [`docs/models/performance.md`](docs/models/performance.md) |
| **Readiness** | projected GRE 200–990 (a range) | **Poisson-binomial → ETS percentile → conformal**, give-up gated | [`docs/models/readiness.md`](docs/models/readiness.md) |

**Key principle:** the engine is shared and unmodified except for the additive, read-only mastery
query. Everything score/AI/UX-related lives *above* the engine so it can be switched off (the AI-off
requirement) without touching the review loop.

## The Rust engine change — Mastery Query

The single change inside Anki's Rust engine (PRD §5, D1) is a **read-only Mastery Query** RPC. Given
a set of `topic::*` tags it returns, per topic, `{ total_cards, reviewed_count, mastered_count,
avg_recall }` in **one indexed SQL pass**, reusing the scheduler's *own* FSRS retrievability helpers
— so the dashboard's mastery numbers come from the same math that schedules reviews, not a lookalike.
It powers the Memory score and feeds the Performance model's per-topic mastery feature.

**Why Rust, not Python:** (1) per-topic mastery over 50k cards on every dashboard refresh is one
indexed grouped aggregate *inside* the engine, vs. many protobuf round-trips + interpreter
aggregation; (2) FSRS retrievability is computed by Rust SQL helpers not exposed to Python; (3)
living in `rslib` means the change ships to desktop **and** Android from one place; (4) read-only +
in-engine means it cannot drift from the engine's own notion of card state.

**The hard invariant (the project's #1 ceiling):** a read must never look like a write. The RPC
**never returns `OpChanges`**, **never calls `transact`**, adds **no undo step**, and leaves the
study-queue counts byte-identical — enforced by a read-only-invariant test.

### Files touched

| File | Change |
|---|---|
| `anki/proto/anki/stats.proto` | +1 RPC (`MasteryQuery`) + 3 messages (`MasteryRequest`, `TopicMastery`, `MasteryResponse`) — additive |
| `anki/rslib/src/stats/mastery.rs` | **new** — pure `aggregate_mastery` fold + `tag_matches` + `Collection::mastery_for_topics` + unit tests |
| `anki/rslib/src/stats/mod.rs` | register the new module |
| `anki/rslib/src/stats/service.rs` | wire the RPC to `mastery_for_topics` |
| `anki/rslib/src/storage/card/mod.rs` | **new** read-only SQL helper (`all_card_tags_and_retrievability`) |
| `anki/pylib/anki/collection.py` | Python binding `Collection.mastery_query(topics)` |

**Tests:** 3 Rust unit tests (empty/zero · aggregation + hierarchy · **read-only invariant** —
unchanged undo step + queue counts + `quick_check` clean) + an `#[ignore]`d 50k-card perf smoke
(p50 ≈ 19 ms, < 50 ms target) + 2 Python integration tests (hierarchy + `add_note → mastery_query →
undo` round-trip). It reaches Android too: `rsdroid` was rebuilt from our fork and a Kotlin
`Collection.masteryQuery` binding is proven by a host-JVM test against the real compiled `rslib`.

**Merge-difficulty assessment — LOW.** Every change is *additive* on Anki's most stable insertion
points: a new proto message, a new read RPC on the existing read-only `StatsService`, a new SQL
helper, a new binding. We touched **no** existing scheduler, storage-write, or undo logic, and
deliberately avoided the version-volatile `scheduler/answering/` and `scheduler/fsrs/` interval math
(PRD D1). A future rebase onto upstream Anki is therefore very unlikely to conflict. Full deep-dive:
`docs/progress-and-rust-change.md`; engine doc: `docs/codebase/rslib.md` (§ Mastery Query).

## License & credits

Licensed **AGPL-3.0-or-later** (`LICENSE`). This is a fork that builds on:

- **Anki** — © Ankitects Pty Ltd and contributors, AGPL-3.0-or-later (some parts BSD-3-Clause; see
  `anki/LICENSE` and `anki/CONTRIBUTORS`). Upstream: https://github.com/ankitects/anki
- **AnkiDroid** — GPL-3.0-or-later. Upstream: https://github.com/ankidroid/Anki-Android
- **rsdroid / Anki-Android-Backend** (added later) — the JNI backend that bundles `rslib` for Android.

We do not reuse or redistribute official ETS exam items (see `docs/PRD.md` §12).

## Repository layout

```
speedrun/
├─ anki/             # submodule → ankitects/anki   (desktop engine: rslib, pylib, qt, proto, ts)
├─ Anki-Android/     # submodule → f15cubing/Anki-Android  (Android client; uses rsdroid over JNI)
├─ Anki-Android-Backend/   # submodule → f15cubing/Anki-Android-Backend  (rsdroid: rslib-over-JNI; recursively vendors anki)
├─ docs/             # PRD, execution plan, assignment spec, and codebase docs + diagrams
│  └─ codebase/      # architecture.md (start here) + per-area module docs
├─ research/         # source-of-truth research synthesis + the brainlift (a deliverable)
├─ AGENTS.md         # agent working rules (read before changing code)
└─ .cursor/skills/   # project skills: codebase-docs, shipping-changes
```

**Pinned upstream versions** (the actual submodule pins — what a fresh `--recurse-submodules` clone
checks out): `anki` fork `f15cubing/anki@6d05314` (25.09.4 `d52ca66` + our Mastery-Query engine
change, dashboard, Exam Mode, LaTeX, scoring adapter, method page), `Anki-Android` fork
`f15cubing/Anki-Android@c6d02501` (of `v2.24.0` `ebcf8e0`; + mastery-query binding, deck auto-import,
read-only 3-score panel (Task 7), interactive-MCQ deck), `Anki-Android-Backend` (rsdroid) fork
`f15cubing/Anki-Android-Backend@3dc30c2` (built locally from source; bundles `anki@ea3acae` — the
`rslib`/Mastery-Query is unchanged through the current pin, so the phone engine matches the desktop).

## Getting started

Clone with submodules (or run the second line in an existing clone):

```bash
git clone --recurse-submodules https://github.com/f15cubing/speedrun.git
cd speedrun
git submodule update --init --recursive   # populates anki/, Anki-Android/, Anki-Android-Backend/ + nested anki/
```

> The `--recursive` flag matters: `Anki-Android-Backend/` (rsdroid) vendors its own `anki/`, and the
> Android build needs it.

## Run the desktop app (Anki / Qt)

The desktop app builds and runs in place from the `anki/` submodule. If you just want to **try it on
an Apple-Silicon Mac without building**, download the prebuilt installer instead.

### Download the prebuilt app (macOS, Apple Silicon — no build)

Grab the latest self-contained installer from the
[**Releases**](https://github.com/f15cubing/speedrun/releases/latest) page —
`GRE-Anki-v<version>-arm64.dmg` bundles Python + Qt + our engine (it does **not** download stock Anki)
and installs **alongside** any normal Anki:

1. Open the `.dmg` and drag **GRE Anki** to **Applications**.
2. It's ad-hoc signed (not notarized), so the first launch needs **right-click ▸ Open ▸ Open** once
   (or run `xattr -dr com.apple.quarantine "/Applications/GRE Anki.app"`).
3. Launch it — the GRE study deck **auto-imports on first run**; open **Tools ▸ GRE dashboard**.

Intel Mac / Linux / Windows / Android: build from source (below).

### Build from source

**One-time setup (macOS):**

```bash
# Rust toolchain (auto-pinned by anki/rust-toolchain.toml on first build)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build tools + audio codecs; also open Xcode once for Command Line Tools
brew install ninja mpv lame
cd anki && ./tools/install-n2 && cd ..
```

**Build + run:**

```bash
cd anki
./run          # first run is slow: it downloads + builds all deps, then launches the app
```

Useful variants (all from `anki/`): `./tools/runopt` (optimized build), `./ninja check` (all
tests/checks), `./ninja format` (auto-format). Note: the checkout path must not contain spaces.

## Run the mobile app (AnkiDroid, in an emulator)

The Android app runs the **same** Rust engine through the locally-built `rsdroid` backend, so you
build the backend first, then the APK, then install it on a running emulator.

**One-time setup:**

1. Install **JDK 21** and the **Android SDK** (Android Studio is the easy path; it also provides the
   emulator + an NDK). Then copy the env template and point it at your machine, and `source` it in
   every shell you build from:

   ```bash
   cp .androidenv.example .androidenv   # then edit JAVA_HOME / ANDROID_HOME
   source .androidenv
   ```

2. Add the Rust Android target and set the NDK path (the backend build needs both):

   ```bash
   rustup target add aarch64-linux-android
   export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/29.0.14206865"   # match your installed NDK version
   ```

3. Tell AnkiDroid to use the locally-built backend — add this line to
   `Anki-Android/local.properties` (gitignored; create the file if absent):

   ```properties
   local_backend=true
   ```

**Start an emulator** (arm64 image; create one in Android Studio's Device Manager if you have none):

```bash
emulator -list-avds                 # find your AVD name
emulator -avd <your_avd_name> &     # boot it (leave running)
adb devices                         # confirm it shows up before installing
```

**Build the backend + APK, then install (run from the repo root, with `.androidenv` sourced):**

```bash
# 1) Build rsdroid bundling our engine (arm64-v8a emulator ABI + host .jar)
cd Anki-Android-Backend && ./build.sh && cd ..     # logs "Anki commit: ea3acae…"

# 2) Build + install the AnkiDroid debug APK onto the running emulator
cd Anki-Android && ./gradlew installFullDebug && cd ..
```

Then open **AnkiDroid** in the emulator. (`./gradlew assembleFullDebug` just builds the APK at
`Anki-Android/AnkiDroid/build/outputs/apk/full/debug/AnkiDroid-full-arm64-v8a-debug.apk` without
installing.) Full backend/build details: `docs/codebase/rsdroid.md`.

## Sync between desktop and mobile (optional)

To sync the two apps against a self-hosted server on our engine:

```bash
make sync-server     # foreground; Ctrl-C to stop. Point both apps at http://<host>:8452/
```

More per-app build/test commands live in the `building-and-testing` skill
(`.cursor/skills/building-and-testing/SKILL.md`). Start with `docs/execution-plan.md` for the
day-by-day build order.

## Where to read next

| You want… | Read |
|---|---|
| What we're building & why | `docs/PRD.md` |
| The day-by-day plan | `docs/execution-plan.md` |
| The assignment | `docs/project-spec.md` |
| How the code fits together (+ diagrams) | `docs/codebase/architecture.md` |
| The three scores (memory ≠ performance ≠ readiness), one page each | `docs/models/` |
| The Rust engine change, in depth | `docs/progress-and-rust-change.md`, `docs/codebase/rslib.md` |
| Packaging + submission runbook (both builds, hard-ceiling checklist, deliverables) | [`docs/submission-checklist.md`](docs/submission-checklist.md) |
| Demo shooting scripts (Friday cut / fuller Sunday cut) | [`docs/demo-plan-friday.md`](docs/demo-plan-friday.md), [`docs/demo-plan.md`](docs/demo-plan.md) |
| How to run the AI card pipeline (the demo "AI run") | [`docs/ai-run-howto.md`](docs/ai-run-howto.md) |
| Rules for changing code | `AGENTS.md` |

## The rsdroid backend (Android)

The Android backend (`rsdroid` / `Anki-Android-Backend`) is wired as a recursive submodule of our fork
and **built locally** (step 1 of "Run the mobile app" above) so its bundled `rslib` carries our engine
change. AnkiDroid consumes that local build via `local_backend=true` in
`Anki-Android/local.properties` (gitignored). Full recipe + design notes: `docs/codebase/rsdroid.md`.

> Status: **Milestone 1 (W1–W4) complete** — see `docs/STATUS.md` for the live progress snapshot.
> AGPL-3.0-or-later.
