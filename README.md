# Speedrun — a GRE *Mathematics Subject Test* study app on a fork of Anki

> **Exam:** GRE **Mathematics** Subject Test (200–990 scale).
> **Thesis:** flashcards measure *memory*; a real exam needs *performance* and *readiness* too.
> This project builds the two missing bridges on top of Anki's engine and is **honest about
> uncertainty** — every score is a range with an evidence panel, and the app refuses to score when
> it lacks evidence.

Two apps over **one shared engine**: a desktop app (Anki/Qt) and an Android companion (AnkiDroid),
both driving the same Rust engine (`rslib`) and syncing between devices. The one real engine change
is a read-only **Mastery Query** RPC (see `docs/PRD.md` §5).

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

**Pinned upstream versions** (what the docs are verified against): `anki` fork
`f15cubing/anki@ea3acae` (25.09.4 `d52ca66` + our W1/W2 work), `Anki-Android` fork
`f15cubing/Anki-Android@67364a7` (of `v2.24.0` `ebcf8e0`), `Anki-Android-Backend` (rsdroid) fork
`f15cubing/Anki-Android-Backend@3dc30c2` (built locally from source; bundles `anki@ea3acae`).

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

The desktop app builds and runs in place from the `anki/` submodule.

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
make sync-server     # foreground; Ctrl-C to stop. Point both apps at http://<host>:8080/
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
| Rules for changing code | `AGENTS.md` |

## The rsdroid backend (Android)

The Android backend (`rsdroid` / `Anki-Android-Backend`) is wired as a recursive submodule of our fork
and **built locally** (step 1 of "Run the mobile app" above) so its bundled `rslib` carries our engine
change. AnkiDroid consumes that local build via `local_backend=true` in
`Anki-Android/local.properties` (gitignored). Full recipe + design notes: `docs/codebase/rsdroid.md`.

> Status: **Milestone 1 (W1–W4) complete** — see `docs/STATUS.md` for the live progress snapshot.
> AGPL-3.0-or-later.
