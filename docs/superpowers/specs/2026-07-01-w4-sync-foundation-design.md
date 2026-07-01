# W4 — Sync Foundation (self-hosted `anki-sync-server`) — Design Spec

> Stand up a **self-hosted, pinned Anki sync server running our fork's engine**, wire **both** real clients
> (desktop Anki + AnkiDroid on the emulator) to it, and prove a card + its review state **round-trips
> desktop↔Android with no corruption** — the Wednesday "sync foundation" that makes Thursday's full
> two-way proof testable. Ships with a one-command re-runnable launcher, a **headless pylib round-trip**
> regression, and an honest write-up of the D3 conflict rule. **Foundation only** — the 10+10 no-loss test
> + same-card conflict demo (7b) and crash/offline safety (7g) are Thursday. **No engine change → fast
> lane.** Companion to `docs/PRD.md` (§10, D3), `docs/execution-plan.md` (Wednesday / Milestone 1), and a
> new `docs/codebase/sync.md`. Dated 2026-07-01.

## Where this sits (Wednesday decomposition)

- **W1 — Mastery Query (shipped, PR #7):** read-only `rslib` change (`f15cubing/anki@ea3acae`).
- **W2 — Desktop dashboard (shipped, PR #9):** memory score as a range + coverage map on desktop.
- **W3 — Android review (shipped, PR #12 + on-device gate):** rsdroid rebuilt with our change; a real
  FSRS review session runs on the emulator on the shared engine.
- **W4 — Sync foundation (this spec):** self-host `anki-sync-server`, wire both clients, prove one
  round-trip, document the conflict rule. **No conflict demo, no 10+10, no crash test, no engine change.**
- **Thursday:** the full two-way proof (7b: 10+10 no-loss + same-card conflict winner) and crash/offline
  safety (7g) — separate spec, built on this foundation.

## Status at time of writing

- Desktop fork build runs a full FSRS review loop (W2); AnkiDroid runs on our rebuilt rsdroid backend on
  the `anki_test` emulator (W3). **Both clients run the same engine, `f15cubing/anki@ea3acae`.**
- **No sync server has been stood up.** Both clients still default to AnkiWeb (never exercised). No custom
  sync URL is set on either.
- The self-hosted server ships in our fork already: `python -m anki.syncserver` →
  `RustBackend.syncserver()` (`anki/pylib/anki/syncserver.py`, `anki/rslib/src/sync/http_server/`). It
  reads `SYNC_USER1..N=user:pass`, `SYNC_HOST`, `SYNC_PORT` (default 8080), `SYNC_BASE` (data dir); it
  **panics if no `SYNC_USER1` is set**.
- Desktop custom endpoint: Preferences ▸ Syncing ▸ *Self-hosted sync server* (profile key `customSyncUrl`,
  `anki/qt/aqt/profiles.py`); `SYNC_ENDPOINT` env also overrides.
- AnkiDroid custom endpoint: Settings ▸ Sync ▸ custom sync server (collection + media URLs).

## Decisions (locked with owner, 2026-07-01)

- **Foundation only.** This spec ends at *one* successful desktop↔Android round-trip + the headless
  regression + docs. The conflict demo and no-loss matrix are Thursday.
- **No engine change; run the STOCK sync server from our fork.** Anki's sync code is untouched. Our W1
  change is a read RPC, irrelevant to sync, so the fork's server behaves exactly like stock — we get "one
  engine" fidelity without touching the most delicate subsystem in the tree.
- **The D3 device-UUID tie-break is documented, not implemented.** "Lexicographically-lower-device-UUID
  wins" is **not** stock Anki behavior (stock resolves a same-card divergence by sync order — last syncer
  wins — with a full-sync fallback). We **document** the rule and, for Thursday, make the winner
  reproducible by **controlling sync order + recording each device's UUID**. We add an `rslib` tie-break
  later **only if** the demo actually needs determinism we can't get from ordering.
- **Approach A (chosen):** committed launcher + **headless pylib round-trip** (automated, re-runnable, no
  emulator) **+** the **live desktop↔Android manual round-trip** (the real cross-device proof, evidence
  captured). Rationale in §4.
- **Run the server from our fork's built Python env** (the same `out/pyenv` the desktop W2 build uses) for
  engine fidelity. A stock upstream `25.09.4` server is schema-compatible (both are `SCHEMA_MAX_VERSION`
  18) and is the documented fallback only.

## Global constraints (hard ceilings)

- **No engine/collection code is touched** → no undo or corruption risk introduced by us. The corruption
  guard for this work is a **Check Database on both clients** after the round-trip (must report clean).
- **Read RPCs never return `OpChanges`** (unchanged — we add no RPC). Nothing here blends the three scores
  or shows readiness (no scoring surface in W4).
- **Self-hosted only.** Clients point at our local server, never AnkiWeb. Server **data dir + credentials
  are gitignored**; the committed test creds are throwaway local-only values, not secrets.
- **Pin the server engine to the clients (`ea3acae`).** A patch-version skew between client and server can
  force a full sync or error; keeping all three identical avoids it.
- **Keep any future conflict demo pure review divergence.** Structural/schema divergence triggers Anki's
  forced one-way full sync (the losing side's structural edits are discarded) — documented here so
  Thursday's demo is built correctly.

---

## 1. Architecture & topology

One server process on the host; two real clients; one shared engine. The Android emulator reaches the
host's loopback through the special alias `10.0.2.2`, so no LAN or tunneling is needed.

```
                 host machine (one engine: f15cubing/anki@ea3acae)
   ┌───────────────────────────────────────────────────────────────────┐
   │  anki-sync-server  (python -m anki.syncserver, SYNC_PORT=8080)     │
   │        ▲  http://127.0.0.1:8080/            ▲  http://10.0.2.2:8080/│
   │        │                                    │                       │
   │  Desktop Anki (our fork build)         Android emulator (anki_test) │
   │  Preferences▸Syncing▸self-hosted URL   AnkiDroid ▸ custom sync URL  │
   └───────────────────────────────────────────────────────────────────┘
                    one account (SYNC_USER1), two devices
```

Three isolated concerns, each independently checkable: **(a) the server** (starts, accepts the account),
**(b) client wiring** (each client points at the right URL and logs in), **(c) the round-trip proof**
(data + review state crosses, no corruption). The seeded GRE deck (`pipeline/`) is the payload.

## 2. Components & files

All new files live in the **outer** repo (no submodule edits). Nothing under `anki/` changes.

| Concern | Path | Action |
|---|---|---|
| Launcher | `sync/run-sync-server.sh` *(new)* | start the pinned server from our fork's pyenv with seeded env (`SYNC_USER1`, `SYNC_HOST=0.0.0.0`, `SYNC_PORT=8080`, `SYNC_BASE=$repo/.sync-data`); print both client URLs |
| One command | root `Makefile` `sync-server` target *(created if absent)* | `make sync-server` → the script above (the same `Makefile` will later host `make bench`, PRD §11) |
| Test creds sample | `sync/.env.example` *(new)* | documents `SYNC_USER1=greuser:grepass` (local-only, non-secret); real overrides via env/gitignored `.env` |
| Headless regression | `sync/roundtrip_smoke.py` *(new)* | two temp collections ↔ local server; assert a reviewed note lands on the second + `quick_check` ok (see §4.1) |
| Ignore | `.gitignore` *(append)* | ignore `sync/.sync-data/`, `sync/.env`, `docs/evidence/w4-sync/*.tmp` |
| Evidence | `docs/evidence/w4-sync/` *(new, small)* | the desktop↔Android round-trip screenshots + Check-Database (§4.2) |
| Codebase doc | `docs/codebase/sync.md` *(new)* | topology, run command, both clients' config, the D3 rule, gotchas |
| Index/status | `docs/codebase/INDEX.md`, `docs/STATUS.md`, `docs/execution-plan.md` | move "Sync conflict rules" Planned → Built-foundation; record PR; check the Wednesday sync box |

## 3. Run recipe (one documented command + client wiring)

1. **Start the server** (from repo root): `make sync-server` — wraps
   `SYNC_USER1=greuser:grepass SYNC_HOST=0.0.0.0 SYNC_PORT=8080 SYNC_BASE="$PWD/sync/.sync-data" \
   $FORK_PY -m anki.syncserver`, where `$FORK_PY` is **the desktop build's Python interpreter — the one
   with our compiled `anki` package (`_rsbridge` = engine `ea3acae`)**. The script resolves it from the W2
   desktop build (path recorded in `building-and-testing`/`sync.md` on first success) and fails loudly if
   it's missing.
2. **Desktop:** Preferences ▸ Syncing ▸ *Self-hosted sync server* = `http://127.0.0.1:8080/`; log in with
   `greuser` / `grepass`; Sync.
3. **AnkiDroid (emulator):** Settings ▸ Sync ▸ custom sync server; collection + media URL =
   `http://10.0.2.2:8080/`; log in with the same account; Sync.
4. **First-contact direction is expected and documented:** against an empty server the first client does a
   **full upload**, the second a **full download**; only subsequent syncs are incremental. The round-trip
   proof (§4.2) is run *after* both sides are in sync.

The exact verified commands are captured in `docs/codebase/sync.md` on first success (per the
`building-and-testing` "mark verified on first success" rule).

## 4. The two proofs

### 4.1 Headless pylib round-trip (automated, re-runnable, no emulator)

`sync/roundtrip_smoke.py` proves the server + protocol work deterministically in CI without a phone:

- Create two throwaway collections **A** and **B** (temp dirs) using our fork's `anki` Python package.
- `auth = col.sync_login("greuser", "grepass", "http://127.0.0.1:8080/")` on each.
- On **A**: add a `topic::*`-tagged note, review its card once, then
  `A.sync_collection(auth, sync_media=False)`; complete the full-upload handshake
  (`full_upload_or_download(..., upload=True)`) since the server starts empty.
- On **B**: `B.sync_collection(auth, ...)` → full-download handshake → assert the note **and** its revlog
  entry + card scheduling landed, and `B.db.scalar("pragma quick_check") == "ok"` (same on A).
- Exit non-zero on any mismatch. One documented command:
  `$FORK_PY sync/roundtrip_smoke.py` (server must be running; `$FORK_PY` as in §3).

This is the re-runnable regression (PRD §11). It exercises the **real** sync protocol against the pinned
server, but on the desktop engine only — it does **not** prove the Android path, which is why §4.2 exists.

### 4.2 Live desktop↔Android manual round-trip (the real cross-device proof)

The Milestone-foundation evidence, mirroring the W3 capture pattern:

1. Desktop: review a card on the seeded GRE deck → Sync (uploads).
2. AnkiDroid: Sync (downloads) → the same card shows the **updated** scheduling/review state.
3. Reverse: review a (different) card on AnkiDroid → Sync; desktop → Sync → the change appears on desktop.
4. **No-corruption guard:** Check Database on **both** clients → clean.

Capture screenshots into `docs/evidence/w4-sync/` (desktop review + sync, AnkiDroid post-sync state, both
Check-Database results). This is what proves "one engine, two devices, syncing" — the D3 grade story.

## 5. Conflict-rule documentation (honest)

`docs/codebase/sync.md` restates D3 and marks exactly what is *stock* vs *deferred*:

- **revlog union — stock, holds today.** revlog rows key on epoch-ms and are distinct per device, so both
  devices' reviews survive a merge. **No review is ever lost.**
- **Card scheduling = last-writer-wins — stock, holds today.** On a same-card divergence Anki keeps the
  most-recently-modified card record; the other side's scheduling for that card is overwritten.
- **Deterministic device-UUID tie-break — DEFERRED (not stock, not implemented).** Thursday's demo will be
  made reproducible by **controlling sync order** (sync device X, then device Y ⇒ Y's write wins
  predictably) and **recording each device's UUID** so the outcome is explained, not by an engine change.
  An `rslib` tie-break is a future option, gated on the demo needing determinism ordering can't provide.
- **Structural/schema divergence → forced one-way full sync — stock.** Note-type/template edits on both
  sides make Anki fall back to a full overwrite; therefore the Thursday conflict demo **must be pure
  review divergence**.

## 6. Lane (fast lane, by risk)

W4 touches only outer-repo ops/docs/tests — **no `rslib`, no submodule pin, no proto/FFI, nothing in the
scheduler/undo/store**. Per `shipping-changes` it is the **fast lane**:

- Fast-lane **self-review checklist** (no separate reviewer agent); design gate = this spec's intent note.
- Verifiable pieces verified and noted in the PR: `make sync-server` starts; `roundtrip_smoke.py` passes;
  the desktop↔Android evidence + both Check-Database results attached.
- Relevant docs updated in the same PR; `docs/STATUS.md` line updated on merge.
- **If any code path we add reached into `anki/rslib/src/sync/`, it would flip to engine lane** — this spec
  deliberately keeps everything outside the engine so it stays fast lane.

## 7. Risks & fallbacks

- **#1 — the fork's `python -m anki.syncserver` runs from our built pyenv.** It needs the compiled
  `_rsbridge` from the W2 desktop build. *Mitigation:* the launcher resolves + checks the pyenv and errors
  clearly. *Fallback:* the official Docker image (`anki/docs/syncserver/`) or a stock `25.09.4` server
  (schema-compatible) — documented, used only if the fork pyenv is unavailable.
- **Emulator → host reachability.** Must use `10.0.2.2`, not `127.0.0.1` (which is the emulator itself).
  *Mitigation:* documented in the recipe + `sync.md`; verify with a `curl` from `adb shell` if login fails.
- **First-sync direction confusion.** Empty server ⇒ first client full-uploads, second full-downloads;
  syncing in the wrong order can prompt an unexpected "download will overwrite" dialog. *Mitigation:* the
  recipe fixes the order (desktop uploads first) and the round-trip proof runs only once both are in sync.
- **`SYNC_USER1` required.** The server panics without it. *Mitigation:* the launcher always sets it.
- **Media sync.** Not required for the foundation (the GRE deck is text/LaTeX, no media). Collection sync is
  the proof; `sync_media` stays off in the headless test and is noted as out of scope here.
- **Accidental AnkiWeb login.** *Mitigation:* the recipe sets the custom URL *before* first login on both
  clients; `sync.md` warns never to leave the URL blank during this work.
- **Version skew.** Keep server + both clients on `ea3acae`; a skew can force a full sync or a protocol
  error. *Mitigation:* pin explicitly and note it in `sync.md`.

## 8. Tests (spec-required)

- **Headless round-trip (automated):** `sync/roundtrip_smoke.py` — reviewed note + revlog + scheduling
  cross A→server→B; `quick_check` ok on both; non-zero exit on mismatch (§4.1).
- **Live desktop↔Android round-trip (manual, evidence-captured):** §4.2 — both directions, plus a
  Check-Database (no corruption) on each client. Screenshots in `docs/evidence/w4-sync/`.
- **Launcher smoke:** `make sync-server` starts the pinned server and serves the account (a `curl
  http://127.0.0.1:8080/` health/handshake check documented in `sync.md`).
- **No engine tests** — no engine code changes; corruption is guarded by the two `quick_check`/Check-DB
  passes above.

## 9. Acceptance

- `make sync-server` starts the **pinned** self-hosted server (engine `ea3acae`) from one documented
  command; account login works.
- **Both** desktop Anki and AnkiDroid (emulator) are wired to it (`127.0.0.1` / `10.0.2.2`) and a card +
  its review state **round-trips desktop↔Android both directions**, with **Check Database clean on both**.
- `sync/roundtrip_smoke.py` passes as the re-runnable regression.
- `docs/codebase/sync.md` exists (topology + recipe + honest D3 rule + gotchas); `INDEX.md` moves "Sync
  conflict rules" Planned → Built-foundation; `STATUS.md` + `execution-plan.md` updated (Wednesday sync box
  checked); evidence saved under `docs/evidence/w4-sync/`.
- Ships **fast lane** (self-review); no engine/submodule changes.

## 10. Out of scope (later)

- **Two-way no-loss matrix (7b):** 10 phone-offline + 10 desktop-offline → reconnect → all 20 land
  (Thursday).
- **Same-card conflict-winner demo (7b):** pure review divergence → documented winner, with device-UUIDs
  recorded (Thursday).
- **Crash/offline safety (7g):** kill each app mid-review ×20 → zero corrupted collections; network-off
  degradation (Thursday/Friday).
- **Any `rslib` sync change**, including a real device-UUID tie-break (only if a later demo requires it).
- **Media sync**, three-scores-on-phone, and `make bench` sync timing (Friday+ / Saturday).
- **Multi-user / auth hardening / TLS** — the server is a local single-account test harness only.
