# Deck Auto-Incorporation (bundled, first-run auto-import) — Design Spec

> Ship the study deck **inside both apps** so it loads with **zero manual import**: commit the built
> `.apkg` (~2.4 MB, 5,407 cards) as an asset in the desktop (`anki`) and AnkiDroid forks, and add a
> **first-run / version-gated auto-importer** to each that runs an **add/update import** (preserving
> FSRS review history via content-derived GUIDs) when the bundled deck is newer than what the
> collection already has. Idempotent, offline, sync-safe. **No engine/Rust/proto/scheduler change** —
> UI + import glue only — but because it edits **both app submodules** it ships via the **engine-lane
> process** (worktree + submodule init + a **different-agent** review, **never self-merge**), split
> into **3 PRs**. Companion to `docs/PRD.md` (§3 two-apps-one-engine, §10), the pipeline docs, and the
> W4 sync foundation (`docs/codebase/sync.md`). Dated 2026-07-02.

## Decisions (locked with owner, 2026-07-02)

- **Bundle the built `.apkg` as a committed asset** in each app fork (not built at app-build time).
- **Version-gated add/update import.** Store a deck version in the collection; import only when the
  bundled version is newer; use add/update semantics so the user's **review history is preserved** on
  unchanged cards (content-derived GUIDs), changed cards update, new cards are added.
- **Both apps auto-import on first run** (desktop + AnkiDroid), independently + offline.
- **Lane = engine-lane process** (different-agent verification, never self-merge), **3-PR split**:
  (1) desktop importer in the `anki` fork, (2) AnkiDroid importer in the `Anki-Android` fork, (3)
  outer-repo submodule-pin bumps + the `make deck-asset` sync tooling/docs. (The engine *extra-gate*
  items specific to Rust — ≥3 Rust tests, undo, no-`OpChanges` — are **N/A**; this is UI/import glue.
  The point of the lane is the stricter review + no self-merge because it touches the app submodules.)

## Global constraints

- **No engine change.** Nothing under `anki/rslib/`, no `.proto`, no FFI, no scheduler/undo/store edit.
  Import uses each platform's **existing** package-import API. The W1 mastery RPC / read-only invariant
  are untouched.
- **Never corrupt the collection or lose review history.** Add/update import only — never wipe/replace.
- **Offline + deterministic.** No network for import; the bundled asset is a committed artifact; the
  version constant is explicit.
- **Sync-safe (W4).** Content-derived GUIDs mean an imported deck on desktop and on phone are the *same*
  notes; syncing does not duplicate. The version flag lives in synced `col.conf` so a device that
  receives the deck via sync does not re-import.
- **Asset can't drift.** A committed check ties the bundled `.apkg` to the `pipeline/` output (content
  hash), so the asset always matches the generator.
- **Deck provenance unchanged.** The bundled deck is exactly the `pipeline/` output (5,407 cards,
  original/templated, no AI, no ETS).
- **Spec:** this file. Consumes sub-project A (the built deck) + the W4 sync foundation.

## 1. Architecture & data flow

```
   pipeline/ (source of truth)  --build-->  gre-study-deck.apkg (2.4 MB, 5,407 cards)
        │  make deck-asset (regenerate + copy + hash-stamp)
        ├─────────────► anki fork:  qt/aqt/gre/data/gre-study-deck.apkg  + GRE_DECK_VERSION
        └─────────────► Anki-Android fork: AnkiDroid/src/main/assets/gre-study-deck.apkg + version

   DESKTOP (Qt/Python)                         ANDROID (Kotlin)
   on profile/collection open:                 on DeckPicker start:
     v = col.get_config("gre_deck_version")       v = col.get_config("gre_deck_version")
     if bundled > v:                              if bundled > v:
        AnkiPackageImporter(add/update)              copy asset -> temp; backend import (add/update)
        col.set_config(version); tooltip            col.set_config(version)
```

Both read/write the **same** `col.conf` key (`gre_deck_version`), which syncs (W4). First importer to
run sets it; the other device receives the deck + flag via sync and skips its own import. Offline, each
imports independently; GUIDs match so a later sync dedupes.

## 2. Components

| # | Component | Where | Responsibility |
|---|---|---|---|
| 1 | Bundled asset + `GRE_DECK_VERSION` | `anki/qt/aqt/gre/data/…apkg` (+ const in `gre/`); `Anki-Android/AnkiDroid/src/main/assets/…apkg` (+ const) | the committed deck each app ships |
| 2 | `make deck-asset` (+ hash check) | outer repo (root `Makefile`) + a small script | regenerate the deck from `pipeline/`, copy into both asset dirs, stamp the version, and assert the committed asset's hash matches the generator |
| 3 | Desktop importer | `anki/qt/aqt/gre/` + a hook in the profile-open flow (`aqt/main.py`, like the W2 dashboard hook) | version-gated `AnkiPackageImporter` add/update + set config + tooltip |
| 4 | AnkiDroid importer | `Anki-Android/AnkiDroid/.../` (Kotlin), DeckPicker start hook | version-gated asset→temp→backend import add/update + set config |

## 3. Idempotency, history, sync

- **Idempotent:** re-running at the same version is a no-op (version check short-circuits). Even if the
  import runs, content-derived GUIDs make it an update, not a duplicate.
- **History preserved:** add/update import keeps FSRS state (`due`, `ivl`, reps) on cards whose content
  (GUID) is unchanged; only genuinely changed cards update.
- **Sync-safe:** desktop-import → sync → phone already has the deck + version → phone skips. Phone-first
  → same. Both-offline-then-sync → identical GUIDs → clean merge, no dupes.
- **User customization:** if the user manually imported the deck before, GUIDs match → the auto-import
  updates in place (no second copy); the version flag then suppresses future redundant imports.

## 4. Testing

- **Desktop (Python, `anki` fork):** import the bundled asset into a fresh in-memory collection →
  asserts deck present + card count == pipeline count; second run at same version → **no new
  notes/dupes** (idempotent); a simulated version bump → re-import adds a new card while leaving an
  existing card's FSRS state intact. Plus a **GUI smoke** (fresh profile → `./run` → GRE deck appears
  with no manual File→Import).
- **AnkiDroid (Kotlin, `Anki-Android` fork):** host-JVM test the importer runs once per version + is
  idempotent (re-run = no dupes); **emulator smoke** (fresh install → deck present in DeckPicker).
- **Asset-freshness (outer repo):** a check that `sha256(committed .apkg)` equals the `pipeline/`
  build's content hash (or that re-running `make deck-asset` leaves the tree clean) — guards drift.

## 5. Lane, PRs, dependencies

- **Lane:** engine-lane **process** — isolated worktree with recursive submodules, each app-touching PR
  **verified by a different agent**, **never self-merge**. (Rust-specific extra-gate items are N/A.)
- **3 PRs:**
  1. **`anki` fork** — desktop importer + bundled asset + `GRE_DECK_VERSION` + Python test.
  2. **`Anki-Android` fork** — AnkiDroid importer + bundled asset + version + Kotlin test.
  3. **outer repo** — bump both submodule pins to the fork commits above, add `make deck-asset` +
     the hash-freshness check + docs (`docs/codebase/`), update `STATUS.md`.
  (PR 3 lands after 1 & 2 so the pins point at merged fork commits. PRs 1 & 2 are independent.)
- **Dependencies:** the built `.apkg` from sub-project A (merged, #19); the W4 sync foundation (for the
  sync-safe reasoning); the existing `qt/aqt/gre/` desktop surface + AnkiDroid DeckPicker.
- **Build/test infra:** desktop `./run` + `./ninja check`; AnkiDroid `./gradlew` + emulator (per
  `building-and-testing`). Both app builds are required to verify — this is why it's engine-lane ceremony.

## 6. Acceptance criteria

- Fresh desktop profile: opening the app **auto-imports** the GRE deck (no manual import); re-open is a
  no-op; a version bump re-imports/adds while preserving review history. GUI-smoke recorded.
- Fresh AnkiDroid install: first launch **auto-imports** the deck; idempotent; version-gated. Emulator
  smoke recorded.
- Both apps hold the **same** deck (content-derived GUIDs); a sync round-trip does **not** duplicate.
- `make deck-asset` regenerates + syncs the asset into both forks and the freshness check passes (no drift).
- Each app-touching PR passes a **different-agent** review; outer-repo PR bumps both pins with the docs' `Last verified` SHAs. No engine/Rust change.

## 7. Out of scope

- Any change to the deck content/generator (that was sub-project A).
- Timed mode, scoring, AI — separate tracks.
- iOS.
- A settings UI to re-trigger import (the version-gated auto-run + normal File→Import already cover it).
