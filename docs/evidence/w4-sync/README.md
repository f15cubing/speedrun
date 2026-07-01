# W4 — Sync-foundation live cross-device evidence

A card + its review state round-trips **both directions** through our **self-hosted
`anki-sync-server`** (running our fork's engine, `f15cubing/anki@ea3acae`, version `25.09.4`),
with **no corruption** on the client. Captured 2026-07-01.

## Topology used for this capture

One self-hosted server (`make sync-server`, `SYNC_PORT=8080`), one account (`greuser`), two peers:

- **Peer A ("desktop"):** a headless collection driven by our desktop build's engine
  (`/tmp/w4_desktop.py`, run with `PYTHONPATH=$FORK_ANKI/out/pylib $FORK_ANKI/out/pyenv/bin/python`).
  **Honest substitution** (approved): we used a headless collection on the *same desktop engine*
  as the "desktop" device instead of driving the Qt GUI by hand — the GUI can't be automated from
  the agent shell the way the emulator can over `adb`. The engine, sync protocol, and server are
  identical to what the GUI uses; only the front-end differs. The full GUI round-trip remains the
  Thursday target.
- **Peer B ("Android"):** the **real AnkiDroid** debug build (`com.ichi2.anki.debug`) on the
  `anki_test` emulator (arm64-v8a), pointed at the custom sync server `http://10.0.2.2:8080/` and
  logged in through the app's normal login flow.

## What the round-trip proved

1. **Desktop → server (full upload).** Peer A created 3 `topic::…`-tagged notes, reviewed one
   (revlog=1), and uploaded: `seed-upload: notes=3 revlog=1 sync=FULL_UPLOAD quick_check=ok`.
2. **Server → Android (full download).** AnkiDroid logged in (`/sync/hostKey` 200) and, because the
   phone already held the W3 deck, the engine reported `FullSyncRequired` — the exact **structural
   divergence → forced full sync** case from our conflict rule. We kept the server copy
   ("Replace collection … from AnkiWeb") → `Full Download Completed`.
3. **Android review on the shared engine.** The exact desktop card appears and is reviewed on the
   phone with **FSRS** intervals (screens 03–04), proving mastery/scheduling come from the *same*
   bundled `rslib`, not a re-implementation.
4. **Android → server → desktop (normal sync, both directions).** The Android review synced up
   (normal sync, `begin stream to server … finalize`), then Peer A pulled it:
   `pull: sync=NO_CHANGES notes=3 cards=3 revlog=2 quick_check=ok` — **revlog grew 1 → 2**, i.e. the
   Android review landed back on the desktop peer, with `quick_check=ok`.
5. **No corruption on the client.** AnkiDroid **Check database → "Database rebuilt and optimized."**

### Server access log (our engine served both peers)

```
/sync/hostKey  status=200         # AnkiDroid login  (client=25.09.4,…,android)
/sync/meta     status=200
/sync/download status=200         # full download to Android
/sync/meta     status=200         # Android normal-sync upload of the review
/sync/hostKey  status=200         # desktop peer pull (client=25.09.4,…,macos)
/sync/meta     status=200
```

## Screenshots

| # | File | Shows |
|---|------|-------|
| 1 | `01-fullsync-conflict-keep-server.png` | "Select collection to keep — the collections can't be combined": the D3 structural-divergence → **forced full sync** decision. We keep the server (desktop) copy. |
| 2 | `02-android-downloaded-desktop-deck.png` | After download: AnkiDroid shows the **Default** deck (`2 1 0`, "3 cards due", "Studied 1 card today") — the desktop peer's collection landed on the phone; sync icon clean (logged in). |
| 3 | `03-android-reviewing-desktop-card.png` | Reviewing the exact desktop-created card on Android: *"W4-desktop: integral of x dx ?"*. |
| 4 | `04-android-answer-fsrs.png` | Answer *"x^2/2 + C"* with **FSRS** buttons (Again <1m · Hard <6m · Good <10m · Easy 5d) — the shared engine schedules the review. |
| 5 | `05-android-reviewed-synced-back.png` | After rating **Good** on Android and syncing up: `1 2 0`, **"Studied 2 cards today"** (desktop's 1 + Android's 1), sync icon clean. The desktop pull then confirmed `revlog=2`. |
| 6 | `06-android-checkdb-ok.png` | **Check ▸ Check database → "Database rebuilt and optimized."** — no corruption after the full sync round-trip. |

## Re-run

- Automated regression (no emulator needed): `make sync-server` then `make sync-smoke`.
- This live capture: see `docs/codebase/sync.md` for the step-by-step (server + AnkiDroid custom
  sync server config + the headless desktop peer).
