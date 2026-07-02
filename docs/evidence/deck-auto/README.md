# Deck auto-incorporation — validation evidence

## Desktop (PR #1, f15cubing/anki#1)
- Unit: `qt/tests/test_gre_autoimport.py` 3/3 (first import adds >5000 + stamps version; second run no-op; missing-version triggers).
- Hook `_autoimport_gre_deck` registered on `gui_hooks.collection_did_load` (verified in built app).
- Manual GUI smoke (user): fresh profile → GRE deck auto-appears, no File→Import; reopen → no dupes.

## AnkiDroid (PR #2)
Validated against the **real custom rsdroid** (`local_backend=true`, W3 toolchain, `masteryQuery` intact):
- Unit: `GreDeckAutoImportTest` **2/2 PASS** — first import loads >5000 cards + stamps `gre_deck_version`; second import idempotent (`:AnkiDroid:testPlayDebugUnitTest`).
- **Emulator smoke (arm64 emulator, fresh install):**
  - `01-android-fresh-install-autoimport.png` — first launch: **GRE Math Subject Test ▸ Study Deck auto-appears** with no manual File→Import.
  - Collection DB after first run: **5,435 cards** (5,407 bundled GRE + 28 AnkiDroid defaults), `gre_deck_version=2026-07-02` stamped.
  - `02-android-reopen-no-dupes.png` — force-stop + relaunch: **still 5,435 cards** (idempotent, no re-import).
