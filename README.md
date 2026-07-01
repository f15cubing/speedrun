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

```bash
# Clone with submodules (or run the second line in an existing clone):
git clone --recurse-submodules https://github.com/f15cubing/speedrun.git
git submodule update --init --recursive
```

Build instructions live with each app: desktop in `anki/README.md` / `anki/docs/`, Android in
`Anki-Android/docs/`. Start with `docs/execution-plan.md` for the day-by-day build order (the Day-1
priority is getting both builds green before any features).

### Local setup (machine-specific)

Android tooling paths are kept out of git. Copy the example and edit it for your machine:

```bash
cp .androidenv.example .androidenv   # then edit JAVA_HOME / ANDROID_HOME
source .androidenv
```

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
and **built locally** so its bundled `rslib` carries our engine change (W3). It vendors `anki` itself,
so always init recursively:

```bash
git submodule update --init --recursive   # populates Anki-Android-Backend/ + its nested anki/
```

Build + run recipe: `docs/codebase/rsdroid.md` (§ Building rsdroid from source). AnkiDroid consumes the
local build via `local_backend=true` in `Anki-Android/local.properties` (gitignored).

> Status: **Day 1 (setup)** — work in progress toward the Sunday deadline. AGPL-3.0-or-later.
