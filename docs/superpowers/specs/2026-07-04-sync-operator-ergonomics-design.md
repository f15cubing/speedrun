# Sync Operator Ergonomics — one command to bring sync up — Design Spec

> Make the self-hosted sync harness **painless to operate** for the demo operator (you): one command,
> `make sync-up`, that **preflights the build, starts the server in the background, waits until it truly
> listens, and prints a status card** with the exact desktop + emulator URLs and the first-contact rule —
> plus `status` / `verify` / `down` / `reset` / `urls` / `doctor` so the Sunday demo recording **and** the
> headless re-runs stop being a hand-run ritual with landmines. **No engine/collection/submodule change,
> no new dependencies (bash + optional `adb`) → fast lane.** Companion to `docs/codebase/sync.md`,
> `docs/PRD.md` (§10, D3), and the W4 foundation spec (`2026-07-01-w4-sync-foundation-design.md`). Dated
> 2026-07-04.

## Motivation — the friction today

The sync foundation works, but *operating* it lives entirely in the operator's head and in `sync.md`.
Every pain below is real and documented in `docs/codebase/sync.md` "Gotchas & invariants":

- **Is the server even up?** `make sync-server` is **foreground-only**; a naive background launch gets
  reaped, and you only discover a dead server when a client throws "A network error occurred" with
  **nothing in the log**. There is no `status`, no health check, no pid.
- **Which URL, again?** Desktop is `http://127.0.0.1:8080/`; the emulator is `http://10.0.2.2:8080/`
  (the classic "not `127.0.0.1` from inside the emulator" trap). These live only in the doc.
- **Did I break the direction?** Empty-server first contact forces a **full sync** — whoever syncs first
  must **upload**. Getting this wrong prompts a scary "download will overwrite" dialog.
- **Stale build / stale state.** A partial worktree build errors `No module named 'anki.buildinfo'`; a
  stale server DB flips the first-contact direction. The fix (`rm -rf sync/.sync-data`, rebuild) is
  tribal knowledge.
- **Re-runs are two-terminal choreography.** `make sync-smoke` needs the server already running in
  another terminal; there's no single "prove it still works" command.

None of this is an engine problem — it's an **operator-experience** problem. This spec wraps the existing,
working pieces in a thin, robust control tool.

## Status at time of writing

- The foundation exists and is proven: `sync/run-sync-server.sh` (foreground launcher), `make sync-server`
  / `make sync-smoke`, the headless `sync/roundtrip_smoke.py`, and the 7b/7g proofs
  (`sync/two_way_sync_7b.py`, `robustness/crash_test_7g.py`). Conflict rule documented in
  `docs/codebase/sync.md`.
- The server reads `SYNC_USER1`, `SYNC_HOST`, `SYNC_PORT` (default 8080), `SYNC_BASE` (data dir) and
  **panics without `SYNC_USER1`**; the launcher always sets it.
- **Desktop client endpoint is profile-driven, not env-driven** (verified in `anki/qt/aqt/profiles.py`):
  `sync_endpoint() = currentSyncUrl or customSyncUrl or None`. There is **no `SYNC_ENDPOINT` override for
  the client** — that env only configures the *server*/tests. (The older `sync.md`/W4 note claiming a
  client `SYNC_ENDPOINT` override is wrong and is corrected as part of this change.)
- `sync/roundtrip_smoke.py` **hardcodes** `ENDPOINT = "http://127.0.0.1:8080/"` and the creds, so it's
  pinned to `:8080`; `sync/two_way_sync_7b.py` already honors `SYNC_ENDPOINT`.

## Decisions (locked with owner, 2026-07-04)

- **Audience = the demo operator / harness**, not the in-app student. We are not touching the desktop or
  AnkiDroid sync *screens*; we wrap the *operating* of the local server + clients.
- **Approach B (chosen):** robust background server lifecycle + `doctor` preflight + `verify` + `urls`,
  **plus best-effort, optional client auto-config that degrades gracefully to printed copy-paste steps.**
  (Approach A = lifecycle only; Approach C = full live GUI/emulator orchestrator, rejected as brittle for
  little gain since the demo is screen-recorded by hand.)
- **Dependency-free.** Pure `bash`; `curl`/`lsof`/`adb` used only if present, always with a fallback. No
  Python packages, no daemonization framework.
- **Additive + back-compat.** `make sync-server` (foreground) and `make sync-smoke` keep working exactly
  as today. Everything new is additive.
- **Fast lane.** Only `sync/`, `Makefile`, `.gitignore`, and docs change. No `anki/` submodule, no
  `rslib`, no proto/FFI, nothing in scheduler/undo/store.
- **Correct the `SYNC_ENDPOINT`-client misconception** in `docs/codebase/sync.md` in the same change.

## Global constraints (hard ceilings)

- **No engine/collection/submodule change** → no undo/corruption risk introduced. The corruption guard
  remains the `quick_check` inside `verify` (via `roundtrip_smoke.py`) and Check-Database on device.
- **Self-hosted, local-only.** Server binds loopback-reachable addresses for two local clients; runtime
  files (pid/log) and the data dir are **gitignored**; committed creds stay throwaway, non-secret.
- **Idempotent + safe.** `up` never double-starts; `reset`/`down --reset` require confirmation (or an
  explicit `--yes`); nothing deletes a collection or touches `sync/.sync-data` implicitly.
- **Honest output.** The status card shows the real listening state, port, data dir, and engine buildhash
  — never a hard-coded "it's fine."

---

## 1. Architecture

One small control script, `sync/sync.sh <command> [flags]`, fronted by thin `Makefile` targets. It reuses
the existing `sync/run-sync-server.sh` for the actual server exec (so the resolved-build logic stays in one
place) but owns lifecycle, health, status, and client-config concerns around it.

```
            operator
               │  make sync-up / status / verify / down / reset / urls / doctor
               ▼
        sync/sync.sh  ── preflight (doctor) ─▶ resolves fork build via run-sync-server.sh
               │        ── background start + pid/log under sync/.run/
               │        ── health poll until LISTEN + HTTP responds
               │        ── status card (URLs, account, data dir, buildhash, first-contact rule)
               ▼
   anki-sync-server (python -m anki.syncserver, SYNC_PORT=8080, our fork engine)
        ▲ 127.0.0.1:8080 (desktop)          ▲ 10.0.2.2:8080 (emulator)
```

**Runtime vs. data separation (design choice):** lifecycle files live under **`sync/.run/`** (`server.pid`,
`server.log`), kept **separate** from the server DB under `sync/.sync-data/`. This lets `reset` wipe *data*
without fighting the *lifecycle*, and lets `status`/`verify` tail the log on failure. Both are gitignored.

## 2. Components & files

All in the **outer** repo. Nothing under `anki/` changes.

| Concern | Path | Action |
|---|---|---|
| Control tool | `sync/sync.sh` *(new)* | subcommands `up`/`status`/`down`/`verify`/`reset`/`urls`/`doctor`; reuses `run-sync-server.sh` for the exec |
| Make targets | root `Makefile` *(edit)* | add `sync-up`, `sync-status`, `sync-down`, `sync-verify`, `sync-reset`, `sync-urls`, `sync-doctor`; **keep** `sync-server`/`sync-smoke` |
| Port-configurable smoke | `sync/roundtrip_smoke.py` *(edit)* | honor `SYNC_ENDPOINT`/`SYNC_PORT`/`SYNC_USER`/`SYNC_PASSWORD` env (fallback = today's `127.0.0.1:8080` + `greuser:grepass`) so `verify` isn't pinned to `:8080` |
| Ignore | `.gitignore` *(append)* | `sync/.run/` (pid/log) |
| Codebase doc | `docs/codebase/sync.md` *(edit)* | new "Operating sync (`make sync-up`…)" section; **correct** the client-`SYNC_ENDPOINT` claim; cross-link the tool |
| Status | `docs/STATUS.md` *(edit on merge)* | one line recording the operator-ergonomics change |

## 3. CLI surface

`sync/sync.sh` dispatches on `$1`. Every command prints a clear one-line summary and uses meaningful exit
codes (`0` ok, non-zero on failure). Env overrides (`SYNC_PORT`, `SYNC_BASE`, `FORK_ANKI`, `FORK_PY`) match
`run-sync-server.sh` so `sync/.env` keeps working.

| Command | Make target | Behavior | Exit |
|---|---|---|---|
| `up` | `make sync-up` | **The headline.** Run `doctor`; if healthy already-up, print status and stop (idempotent). Else start the server **backgrounded** (pid/log in `sync/.run/`), **poll health** until it listens (≤ ~10 s), print the **status card** (§4). | `0` up & healthy; non-zero on preflight fail or health timeout (prints the tail of `server.log`) |
| `status` | `make sync-status` | Report from the pid file + a live health probe: `pid`, `port`, `uptime`, HTTP health (404 = serving), `data dir`, engine `version+buildhash`. Distinguishes **up / down / stale-pid**. | `0` if up & healthy, non-zero otherwise |
| `verify` | `make sync-verify` | Ensure the server is up (auto-`up` if not), then run `roundtrip_smoke.py` against the running port; print `PASS`/`FAIL`. The re-run path. | mirrors the smoke's exit |
| `down` | `make sync-down` | Stop the backgrounded server via the pid file (TERM, then KILL), remove the pid file. `--reset` also wipes data (confirm). Data kept by default. | `0` |
| `reset` | `make sync-reset` | Wipe `sync/.sync-data` for a clean first-contact. Refuses while the server is up (tells you to `down` first); requires confirm or `--yes`. | `0` |
| `urls` | `make sync-urls` | Print copy-paste client config (desktop `127.0.0.1`, emulator `10.0.2.2`), the account, and the **first-contact upload/download rule** — **without starting anything.** Best-effort auto-config behind flags (§7). | `0` |
| `doctor` | `make sync-doctor` | Preflight only (no start): build present + importable, port free-or-ours, `SYNC_USER1` set, engine buildhash; best-effort emulator reachability if `adb` present. Prints a ✓/✗ checklist. | `0` all pass, non-zero on any ✗ |

## 4. Server lifecycle (the core)

`up` is the one command that matters. Its contract:

1. **Preflight** (`doctor`, §5). Abort with an actionable message on any ✗ — never start a doomed server.
2. **Idempotency.** If `sync/.run/server.pid` names a live process that is **actually listening**, print the
   status card and exit `0` (no second server). If the pid is stale (process gone or port not listening),
   clean it up and continue.
3. **Background start.** `nohup … run-sync-server.sh > sync/.run/server.log 2>&1 &`, record the pid in
   `sync/.run/server.pid`. (The exec/env/build-resolution stays inside `run-sync-server.sh`.)
4. **Health poll.** Every ~0.5 s for ≤ ~10 s, check the port is `LISTEN` **and** HTTP responds (a `GET /`
   returning 404 counts as serving, per `sync.md`). Probe order: `curl` → the fork Python's `urllib` →
   `lsof`/`nc` — whichever exists. On timeout: print the tail of `server.log` and exit non-zero.
5. **Status card.** On success print, e.g.:

```
sync server UP  (pid 41255, port 8080, uptime 0s)
  engine   : anki 25.09.4  (buildhash d52ca669)
  data dir : /Users/.../speedrun/sync/.sync-data
  account  : greuser
  desktop  : http://127.0.0.1:8080/      → Preferences ▸ Syncing ▸ self-hosted URL
  emulator : http://10.0.2.2:8080/       → AnkiDroid ▸ Settings ▸ Sync ▸ custom sync server
  first contact: whoever syncs FIRST must UPLOAD (empty server ⇒ full sync); the other DOWNLOADS.
  next: `make sync-verify` (headless proof) · `make sync-status` · `make sync-down`
```

## 5. Preflight / `doctor`

A ✓/✗ checklist mapping one-to-one to the real failure modes in `sync.md`, so failures are diagnosed *before*
a client throws an opaque network error:

- **Build present & importable** — reuse `run-sync-server.sh`'s check: `$FORK_PY -c 'import anki,
  anki.buildinfo, anki.syncserver'`. ✗ prints the exact rebuild command (`cd $FORK_ANKI && ./ninja pylib qt`).
- **Port** — free, or already owned by *our* server (idempotent up). ✗ if a foreign process holds it.
- **Credentials** — `SYNC_USER1` resolvable (from `sync/.env` or the committed default). ✗ else (server
  would panic).
- **Engine buildhash** — print `version+buildhash` from `anki.buildinfo`; advisory reminder that **all
  clients must match** (parity is not auto-checkable across devices, so it's surfaced, not enforced).
- **Emulator reachability (best-effort, non-fatal)** — if `adb` + a device are present, note it and, where
  possible, probe `10.0.2.2:PORT` from inside the emulator; otherwise print the manual `adb shell` curl hint.

## 6. `verify` (the re-run path)

Reuses the existing `sync/roundtrip_smoke.py` (reviewed note + card + revlog cross A→server→B, `quick_check`
ok on both). Two small robustness edits:

- Make the script **port/endpoint-configurable** via env (`SYNC_ENDPOINT`/`SYNC_PORT`/`SYNC_USER`/
  `SYNC_PASSWORD`), defaulting to today's values — matching `two_way_sync_7b.py`.
- `make sync-verify` auto-`up`s the server if needed, runs the smoke with the fork Python + `PYTHONPATH`
  (same recipe as `sync-smoke`), and prints `PASS: …` / `FAIL: …`.

`sync-smoke` stays as the "server already running elsewhere" form; `sync-verify` is the "just prove it"
one-command form.

## 7. Client config (guaranteed copy-paste + best-effort auto-config)

**Guaranteed path — `urls`** prints exactly what to paste and the direction rule (see the status card). This
is always correct and always available.

**Best-effort auto-config (optional flags, degrade to copy-paste):**

- **Desktop — `urls --set-desktop`:** with the app **closed**, set the profile's `customSyncUrl` via the
  fork's `ProfileManager` API (`pm.set_custom_sync_url(url); pm.save()`), so the desktop launches
  ready-to-sync. This is the *correct* mechanism (there is **no** client `SYNC_ENDPOINT` override — §Status).
  If the profile can't be opened (app running, path unknown), it prints the Preferences steps instead. Off
  by default; never touches the collection, only the profile's sync URL field.
- **Emulator — `urls --emulator`:** on a **debuggable** AnkiDroid install, best-effort write the custom sync
  URL into shared-prefs via `adb shell run-as com.ichi2.anki …` and restart the app, then probe reachability.
  If `adb`/`run-as` isn't available or keys differ, print the manual AnkiDroid steps + the `10.0.2.2` note.

Both auto-config paths are **best-effort and non-load-bearing**: the demo can always be driven from the
printed steps. This keeps the risky, version-sensitive bits off the critical path.

## 8. Lane (fast lane, by risk)

Only outer-repo ops/docs/tests change — no `rslib`, no submodule pin, no proto/FFI, nothing in
scheduler/undo/store. Per `shipping-changes` this is the **fast lane**: self-review against the fast-lane
checklist (no separate reviewer agent); design gate = this spec's intent note; relevant docs updated in the
same PR; `docs/STATUS.md` line updated on merge. If any added path reached into `anki/`, it would flip to
engine lane — this spec deliberately stays outside the engine.

## 9. Risks & fallbacks

- **Background server reaped by a one-shot shell.** *Mitigation:* `nohup` + pid file + health-verified
  `up`; `status` always reports the true state; the demo runs from a persistent terminal or a tracked
  background job. This is strictly better than today's naive `&`.
- **Health probe false positive/negative.** *Mitigation:* require **both** port-`LISTEN` and an HTTP
  response; treat 404 as healthy (documented server behavior); fall back across `curl`/`urllib`/`lsof`.
- **Desktop profile poke drifts across versions.** *Mitigation:* use the public `ProfileManager` method,
  gate behind an explicit flag, and **default to copy-paste**. Never edit the collection.
- **Emulator auto-config is app-version-specific.** *Mitigation:* best-effort only, always prints the manual
  fallback; the reachability probe is advisory.
- **Port already in use.** *Mitigation:* `doctor` detects it and distinguishes "our stale server" (clean up
  + reuse) from "a foreign process" (abort with the pid).
- **Parity can't be auto-checked across devices.** *Mitigation:* surface the server buildhash prominently
  and remind that clients must match; don't pretend to enforce it.
- **`reset` foot-gun.** *Mitigation:* refuse while up, require confirm/`--yes`, only ever touch
  `sync/.sync-data` (gitignored).

## 10. Tests (spec-required)

- **`doctor` unit-ish smoke:** with a good build → all ✓ exit 0; with `SYNC_USER1` unset or a busy port →
  the matching ✗ and non-zero. (Bash-level, no engine.)
- **Lifecycle smoke:** `up` → `status` reports UP + healthy → `verify` prints `PASS` → `down` → `status`
  reports DOWN. Idempotency: a second `up` doesn't start a second server (pid unchanged).
- **`verify` non-vacuity:** with the server **down**, `roundtrip_smoke.py` fails with a network error (proves
  the test isn't hollow) — same guarantee as today's `sync-smoke`.
- **Port-config:** `SYNC_PORT=8091 make sync-up && SYNC_PORT=8091 make sync-verify` works end-to-end on a
  non-default port (proves the smoke edit).
- **No engine tests** — no engine code changes; corruption is guarded by `verify`'s `quick_check`.

## 11. Acceptance

- `make sync-up` is a **single command** that preflights, starts the server in the background, waits until it
  actually listens, and prints the status card (URLs + account + data dir + buildhash + first-contact rule).
  Running it twice does not start a second server.
- `make sync-status` / `sync-down` / `sync-reset` / `sync-verify` / `sync-urls` / `sync-doctor` behave per §3;
  `sync-verify` prints a clear `PASS`/`FAIL`.
- `make sync-server` and `make sync-smoke` still work unchanged (back-compat).
- `sync/roundtrip_smoke.py` honors `SYNC_ENDPOINT`/`SYNC_PORT` (defaults unchanged).
- `docs/codebase/sync.md` gains an "Operating sync" section and **corrects** the client-`SYNC_ENDPOINT`
  claim; `.gitignore` ignores `sync/.run/`; `docs/STATUS.md` updated on merge.
- Ships **fast lane** (self-review); no engine/submodule change; no new dependencies.

## 12. Out of scope (later)

- **In-app student sync UX** (desktop/AnkiDroid sync *screens*, one-tap sync, onboarding) — a different
  audience; not this change.
- **Full live orchestration** (launching the desktop app + booting the emulator + driving an end-to-end
  live sync automatically) — Approach C, rejected as brittle.
- **Any `rslib`/engine sync change**, incl. the deferred device-UUID tie-break.
- **Multi-user / auth / TLS / public exposure** — the server stays a local single-account test harness.
- **`make bench` sync timing** and media sync — unchanged by this work.
