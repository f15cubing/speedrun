---
name: building-and-testing
description: Use when you need to build, run, or test any part of this fork — the desktop app (Qt), the Android app (AnkiDroid), or the Rust engine — e.g. to satisfy a PR's build/test gate or to get the Day-1 builds green.
---

# Building and Testing

## Overview

Canonical commands to build, run, and test each surface of this fork. Use these to satisfy
`shipping-changes`' "builds cleanly / tests pass" gates and the Day-1 "get both builds green"
priority, instead of re-discovering the toolchain each time.

> **Provenance & status.** Commands are taken from upstream docs — `anki/docs/development.md`
> (`anki@25.09.4`, `d52ca66`) and AnkiDroid `.github/workflows/README.md` (`Anki-Android@v2.24.0`,
> `ebcf8e0`). They are **NOT yet verified on this machine.** Treat this like a codebase doc: the
> first time you run a command and confirm it, mark it verified; if one is wrong, fix it here in the
> same change.

## Desktop — `anki/` (Rust + Python + Qt + Svelte)

One-time setup: install Rustup (toolchain is pinned in `anki/rust-toolchain.toml`, auto-downloaded);
install N2/Ninja via `cd anki && ./tools/install-n2`. macOS also needs Xcode + Command Line Tools
(open Xcode once) and `brew install ninja mpv lame` (mpv/lame for audio).

Run from `anki/`:

| Goal | Command |
|---|---|
| Build + run the app in place | `./run` |
| Run ALL tests/checks | `./ninja check` |
| Run a subset | `./ninja check:svelte` (list targets: `./ninja -t targets all`) |
| Auto-fix formatting | `./ninja format` |
| Auto-fix lint / copyright headers | `./ninja fix` |
| Fix clippy | `cargo clippy --fix` |
| Optimized run | `./tools/runopt` (or `RELEASE=1`) |
| Build wheels | `./tools/build` → `out/wheels` |
| Clean build | delete `anki/out/` |

First `./run` is slow (downloads + builds deps). `./run` auto-sets `ANKIDEV` (extra logs, backups
off — test profiles only); `TRACESQL` prints SQL. Proto changes: see `anki/docs/protobuf.md` and
`docs/codebase/proto-rpc.md`.

## Android — `Anki-Android/` (Kotlin over rsdroid/JNI)

One-time setup: JDK 21 + Android SDK. Copy the repo's `.androidenv.example` → `.androidenv`, edit
`JAVA_HOME` / `ANDROID_HOME`, then `source .androidenv` **before** any `gradlew` call.

Run from `Anki-Android/` (these are the authoritative CI quality checks):

| Goal | Command |
|---|---|
| Build a debug APK | `./gradlew assembleDebug` |
| Install on device/emulator | `./gradlew installDebug` |
| Kotlin lint + format | `./gradlew lintPlayDebug :api:lintDebug :libanki:lintDebug ktLintCheck lintVitalFullRelease lint-rules:test --daemon` |
| Unit tests | `./gradlew jacocoUnitTestReport --daemon` |
| Emulator (instrumented) tests | `TEST_RELEASE_BUILD=true ./gradlew jacocoAndroidTestReport --daemon` |

Authoritative list: `Anki-Android/.github/workflows/README.md` + the AnkiDroid Wiki
"Development-Guide". The Rust engine reaches Android via the external `rsdroid` AAR (see
`docs/codebase/rsdroid.md`); building AnkiDroid does **not** rebuild `rslib`.

## Rust engine tests (feeds the `shipping-changes` extra gate)

Engine PRs require "≥3 Rust unit tests + ≥1 test calling from Python" plus undo / no-corruption
checks. Run the integrated Rust + Python checks via `./ninja check` (uses the pinned toolchain). For
a focused crate during dev, `cargo test -p anki` works but isn't the integrated path. Invariants
(e.g. read paths must not return `OpChanges`) are in `docs/codebase/rslib.md`.

## Common mistakes

- Calling `gradlew` without `source .androidenv` → wrong/missing JDK. Source it first.
- Hand-editing generated protobuf/backend code → regenerate via the build (`proto-rpc.md`,
  `pylib.md`).
- An `anki/` checkout path containing spaces → the build forbids it.

---
Sourced from `anki@25.09.4` (`d52ca66`: `docs/development.md`, `build.md`, `mac.md`) and
`Anki-Android@v2.24.0` (`ebcf8e0`: `.github/workflows/README.md`). Not yet verified on this machine.
