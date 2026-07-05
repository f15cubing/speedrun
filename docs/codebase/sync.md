# Sync foundation (self-hosted `anki-sync-server`)

> Co-located doc for `sync/` (`run-sync-server.sh`, `roundtrip_smoke.py`), the root `Makefile`
> `sync-server`/`sync-smoke` targets, and the W4 evidence in `docs/evidence/w4-sync/`. Read this
> before touching the sync harness. **This is a local test harness — never expose the server
> publicly, and the committed credentials are throwaways, not secrets.**

## Purpose

Stand up a **self-hosted Anki sync server running our fork's engine** and prove a card + its review
state round-trips between two real clients with no corruption — the Wednesday "sync foundation" that
makes the full two-way proof (execution-plan 7b) testable. The foundation's follow-ons — the
**10+10 no-loss matrix**, the **same-card conflict demo (7b)**, and **crash-safety (7g)** — are now
**PROVEN** headlessly on this engine (see *Block C proofs (7b/7g)* below). **No engine/collection
code changes → fast lane** (7b proves the stock conflict rule; it does not change it). Companion to
`docs/PRD.md` (§10, D3) and `docs/execution-plan.md` (Wednesday / Milestone 1 · Days 4+5 Block C).

## Topology

One server, one account (`greuser`), two peers — all on the **same engine**
(`f15cubing/anki@ea3acae`, version `25.09.4`):

```
                     host machine (one engine: f15cubing/anki@ea3acae)
   ┌───────────────────────────────────────────────────────────────────┐
   │  anki-sync-server   (python -m anki.syncserver, SYNC_PORT=8452)     │
   │        ▲  http://127.0.0.1:8452/            ▲  http://10.0.2.2:8452/│
   │        │                                    │                       │
   │  Desktop peer (our fork engine)        Android emulator (anki_test) │
   │  Preferences ▸ Syncing (127.0.0.1)     AnkiDroid ▸ custom sync URL  │
   └───────────────────────────────────────────────────────────────────┘
                    one account (SYNC_USER1), two devices
```

## Public interface (how to run it)

**Start the server** (foreground; Ctrl-C to stop):

```bash
make sync-server
```

`sync/run-sync-server.sh` resolves the desktop fork's **complete** build and execs
`python -m anki.syncserver`. **Verified run recipe (2026-07-01):** the importable engine is the
**primary worktree's** build — its `out/pylib` carries the generated `buildinfo.py` + `_rsbridge.so`.
A fresh feature *worktree's* own `anki/out` is typically only partially built and errors
`No module named 'anki.buildinfo'`. Defaults (override in `sync/.env`, gitignored):

```
FORK_ANKI = /Users/felipecaicedo/Desktop/alpha/speedrun/anki     # complete desktop build
FORK_PY   = $FORK_ANKI/out/pyenv/bin/python
PYTHONPATH= $FORK_ANKI/out/pylib   # prepended by the launcher
SYNC_USER1=greuser:grepass  SYNC_HOST=0.0.0.0  SYNC_PORT=8452  SYNC_BASE=sync/.sync-data
```

Equivalent one-liner the launcher runs:
`PYTHONPATH=$FORK_ANKI/out/pylib SYNC_USER1=greuser:grepass $FORK_ANKI/out/pyenv/bin/python -m anki.syncserver`
→ logs `INFO listening addr=0.0.0.0:8452` (a `GET /` returns HTTP 404 = serving).

**Client config** (set the URL **before first login**; never leave it blank):

- **Desktop (127.0.0.1):** Preferences ▸ Syncing ▸ self-hosted sync server URL = `http://127.0.0.1:8452/`.
- **AnkiDroid (10.0.2.2):** Settings ▸ Sync ▸ **Custom sync server** ▸ enable *Sync URL* =
  `http://10.0.2.2:8452/` (`10.0.2.2` is the emulator's alias for the host loopback — `127.0.0.1`
  from inside the emulator points at the phone, not the host). Then Sync ▸ log in as `greuser`.

## Operating sync (`make sync-up` — the one-command path)

`sync/sync.sh` (fronted by the Makefile `sync-*` targets) wraps the foreground launcher above with a
**background lifecycle + preflight + health check + status**, so you don't hand-manage a foreground
server or rediscover the URLs each time. **`make sync-server` (foreground) and `make sync-smoke` still
work unchanged.**

| Command | What it does |
|---|---|
| `make sync-up` | Preflight (`doctor`) → start the server **backgrounded** (pid + log under `sync/.run/`) → poll until it actually listens (≤ ~10 s) → print a **status card** (URLs, account, data dir, engine buildhash, first-contact rule). **Idempotent:** a second `up` reports the running server, never starts a second. |
| `make sync-status` | Report UP / DOWN / stale from the pid file + a live HTTP probe (pid, port, data dir, engine buildhash). |
| `make sync-verify` | Ensure up, then run `roundtrip_smoke.py` against the running port → `PASS`/`FAIL`. The re-run path. |
| `make sync-down` | Stop the backgrounded server via the pid file (`ARGS=--reset` also wipes data). |
| `make sync-reset` | Wipe `SYNC_BASE` for a clean first-contact (`ARGS=--yes` to skip the confirm; refuses while up). |
| `make sync-urls` | Print copy-paste desktop + emulator config + the upload-first rule **without starting anything**. `ARGS=--set-desktop`/`--emulator` attempt best-effort auto-config, degrading to printed steps. |
| `make sync-doctor` | Preflight checklist only: engine build importable, `SYNC_USER1` set, port free-or-ours, engine buildhash; best-effort emulator (adb) note. |

- **Runtime vs. data:** the pid + server log live under **`sync/.run/`** (gitignored), separate from the
  server DB under `sync/.sync-data/`, so `reset` and the lifecycle don't collide.
- **One server per data dir.** A second server pointed at a `SYNC_BASE` already open elsewhere fails with
  `open media db … Locked` — `doctor` catches a *port* clash, but if you changed only the port, stop the
  other server or use a fresh `SYNC_BASE`. A leftover foreground `make sync-server` is **not** tracked by
  `make sync-down` (different mechanism) — stop it in its own terminal (`lsof -iTCP:8452 -sTCP:LISTEN`).
- **Non-default port/base:** `SYNC_PORT=8095 make sync-up` (same on `sync-verify`/`sync-down`), or set
  `SYNC_PORT`/`SYNC_BASE`/`FORK_ANKI` in `sync/.env` (gitignored).
- **Verified 2026-07-04** on a dedicated port/base: `doctor` → `up` → `status` → `verify` (`OK … A=1, B=1`
  + `PASS`) → `down`; idempotent `up` reused the running pid.

## The two proofs

1. **Automated headless regression** — `make sync-smoke` (server must be running). `sync/roundtrip_smoke.py`
   spins up two temp collections, reviews a `topic::…`-tagged note on A, syncs A→server→B, and
   asserts the note + card + revlog crossed to B and `pragma quick_check = ok` on both. Prints
   `OK: note+card+revlog crossed A->server->B; quick_check ok (revlog A=1, B=1)`, exit 0. Run it
   with the server stopped first to confirm it fails (`NetworkError`) — proof it isn't vacuous.
2. **Live cross-device round-trip** — `docs/evidence/w4-sync/` (6 screenshots + README): the **real
   AnkiDroid emulator** ↔ our server ↔ a **headless desktop peer** (same desktop engine; the honest
   substitution for driving the Qt GUI by hand — engine/protocol/server identical). Full upload →
   full download → FSRS review on the phone → normal sync back; the desktop peer pull confirmed
   `revlog` grew 1→2 with `quick_check=ok`, and AnkiDroid **Check database → "Database rebuilt and
   optimized."**

## Gotchas & invariants

- **Why the default port is 8452, not 8080.** Running the desktop fork via `anki/run` (`./run`,
  `ANKIDEV=1`) opens Qt WebEngine's Chromium remote-debugger on **8080** (`anki/run` sets
  `QTWEBENGINE_REMOTE_DEBUGGING=8080`). Upstream `anki-sync-server` also defaults to 8080, so an 8080
  sync default would collide with the dev app every time. This fork therefore **defaults `SYNC_PORT` to
  8452** so `make sync-up` just works while the desktop app is running. If a chosen port is already held
  (e.g. you force `SYNC_PORT=8080` with Anki open, or leave an old server up), `doctor`/`up` **identify
  the holder** — `pid … tools/run.py` = Anki's dev app (free 8080 with `QTWEBENGINE_REMOTE_DEBUGGING=9222
  ./run`), `… -m anki.syncserver` = a leftover server (stop it) — and print a concrete free-port command.
  `status` names the holder too and points at `make sync-doctor`.
- **Server dies if `SYNC_USER1` is unset** — the launcher always exports it. Committed
  `greuser:grepass` is a **local throwaway**, never a real secret.
- **`10.0.2.2`, not `127.0.0.1`, from the emulator.** Getting this wrong = "A network error occurred:
  error sending request" on the phone with nothing in the server log.
- **The server must stay running for the whole test.** A backgrounded `& ` launched inside a one-shot
  shell can be reaped between steps; keep `make sync-server` in its own live terminal (or a tracked
  background job). Symptom of a dead server: emulator/desktop login fails with a network error and
  `lsof -iTCP:8452 -sTCP:LISTEN` shows nothing.
- **Empty-server first contact = full sync.** Whoever syncs first should **upload**, the other
  **downloads**. `roundtrip_smoke.py`'s `_sync(prefer_upload=...)` encodes this; for the live test,
  choose "keep AnkiWeb" / Replace to pull the server (desktop) copy to the phone.
- **Reset server state** with `rm -rf sync/.sync-data` (gitignored). A stale server DB leaves the
  account non-empty and flips the first-contact direction.
- **Engine parity:** keep server engine **==** both clients **==** `f15cubing/anki@ea3acae`. A
  patch-version skew can force a full sync or a protocol error.
- **Desktop client endpoint is profile-driven, not env.** The desktop app reads its sync URL from the
  profile (`customSyncUrl`, set in Preferences ▸ Syncing), resolved by `mw.pm.sync_endpoint()`
  (`anki/qt/aqt/profiles.py`). There is **no `SYNC_ENDPOINT` override for the client** — that env var
  configures the **server** (and the headless `roundtrip_smoke.py`) only. Set the URL in Preferences
  **before** first login; `make sync-urls` prints the exact value. (Corrects an earlier note that implied
  a client-side `SYNC_ENDPOINT`.)

## Conflict rule (honest — PRD §10 / D3)

We run **stock** `anki-sync-server` behavior and document it; **no engine change** in W4:

- **Review log (`revlog`): union.** Reviews from both devices are additive — nothing is dropped when
  each side reviewed *different* cards. This is what the Thursday 7b no-loss test relies on.
- **Card scheduling state: last-writer-wins by modification time.** When the *same* card is reviewed
  on both devices while offline, the later `mod` timestamp wins; the other side's scheduling delta
  for that card is overwritten (its revlog rows still survive via the union above).
- **Device-UUID tie-break: DEFERRED (documented, not implemented).** The PRD's proposed UUID
  tie-breaker for identical timestamps would be an engine change — out of scope for the fast-lane
  foundation. The 7b same-card conflict demo is made **deterministic** by controlling sync order
  (sync one device fully before the other) and the `mod` timestamps (recorded per peer), not by a
  code-level tie-break. **Proven** in `sync/two_way_sync_7b.py` (later-`mod` writer wins; see
  *Block C proofs* below).
- **Structural divergence → forced full sync.** If the two collections' schemas diverge (e.g. a phone
  with a different deck/notetype history vs. the server), the engine reports `FullSyncRequired` and
  refuses a normal merge — you must pick a side (upload or download). Observed live in W4 (screenshot
  `01-fullsync-conflict-keep-server.png`). **Honored by 7b:** the same-card conflict demo is
  **pure review divergence** on a shared schema (both peers full-sync from one baseline first), so it
  merges as a mergeable conflict — the reconnect syncs are all normal (`NO_CHANGES`/`NORMAL_SYNC`),
  never a full sync.

## Block C proofs (7b/7g) — PROVEN (2026-07-03)

The Block-C robustness proofs now stand on this engine, fully headless. Both are **evidence + tests
only — no engine/collection change** (7b proves the stock conflict rule above; it does not change
it). Harnesses run with the primary build's python (same rule as `sync-smoke`); the 7b server runs
on its **own** port/data dir (`:8090`, `sync/.sync-data-7b`) so it never collides with the shared
foundation server (default `:8452`) or the emulator.

- **7b — two-way sync** (`sync/two_way_sync_7b.py`, `make sync-server-7b` + `make sync-7b`):
  - *No-loss:* A reviews 10 cards offline, B reviews 10 *different* cards offline → reconnect →
    **all 20 land on both peers** (revlog union), `quick_check=ok`. Reconnect syncs are all normal
    (never a full sync).
  - *Same-card conflict (pure review divergence):* A(Good) vs B(Again, later `mod`) on one graduated
    card → both converge on **B's later-`mod` state** (**scheduling LWW**) while **both reviews
    survive** (**revlog union**, +2 on both); `quick_check=ok`. This is exactly the *Conflict rule*
    above. Determinism = controlled sync order + `mod` times, not a code-level tie-break.
  - **Result:** Phase 1 **20/20 landed on both**; Phase 2 **union + LWW (peer B won)**.
    Evidence: `docs/evidence/robustness/7b-sync/`.
- **7g — crash-safety** (`robustness/crash_test_7g.py`, `make crash-7g`; doc `robustness/README.md`):
  one evolving collection **SIGKILLed mid-review ×20**; every reopen requires `quick_check=ok` **and**
  `integrity_check=ok` with **no revlog loss**. `--selftest` shows the gate rejects a corrupted DB
  (non-vacuous). **Result:** **20/20 CLEAN** (31,405 reviews survived).
  Evidence: `docs/evidence/robustness/7g-crash/`.
- **Android leg:** CUT this session (shared emulator busy with the Task-7 subagent). The device side
  of both properties is already captured: `docs/evidence/w3-android/` (Check-DB "rebuilt and
  optimized" after a force-stop) and `docs/evidence/w4-sync/` (live AnkiDroid↔desktop two-way sync).

## Related tests / evidence

- `sync/roundtrip_smoke.py` — the automated foundation regression (`make sync-smoke`).
- `sync/two_way_sync_7b.py` — the 7b two-way proof (`make sync-7b`); evidence `docs/evidence/robustness/7b-sync/`.
- `robustness/crash_test_7g.py` — the 7g crash proof (`make crash-7g`); evidence `docs/evidence/robustness/7g-crash/`; doc `robustness/README.md`.
- `docs/evidence/w4-sync/` — the live AnkiDroid ↔ desktop-peer round-trip (README + 6 screenshots).

---
Last verified against: `f15cubing/anki@ea3acae` (`anki 25.09.4`, buildhash `d52ca669`; server engine
+ both peers; `python -m anki.syncserver`). Foundation `SYNC_PORT=8452` (was 8080 before 2026-07-05); 7b proof `SYNC_PORT=8090`.
Block C 7b/7g verified 2026-07-03. Operator tooling `sync/sync.sh` (`make sync-up`/`status`/`verify`/
`down`/`reset`/`urls`/`doctor`) added + verified 2026-07-04 (full lifecycle on a dedicated port/base;
engine buildhash `d52ca669`; no engine change). **2026-07-05:** default `SYNC_PORT` changed 8080→**8452**
so `make sync-up` no longer collides with Anki's dev WebEngine remote-debugger (which `anki/run` binds on
8080); `doctor`/`status` now **identify** a foreign port holder (Anki dev app vs. a leftover sync server)
and suggest a concrete free port. Verified live: `doctor` all-green on 8452 while the dev app still held
8080; own-server + free-port paths unchanged. Fast lane, no engine change.
