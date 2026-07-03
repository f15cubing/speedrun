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
   │  anki-sync-server   (python -m anki.syncserver, SYNC_PORT=8080)     │
   │        ▲  http://127.0.0.1:8080/            ▲  http://10.0.2.2:8080/│
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
SYNC_USER1=greuser:grepass  SYNC_HOST=0.0.0.0  SYNC_PORT=8080  SYNC_BASE=sync/.sync-data
```

Equivalent one-liner the launcher runs:
`PYTHONPATH=$FORK_ANKI/out/pylib SYNC_USER1=greuser:grepass $FORK_ANKI/out/pyenv/bin/python -m anki.syncserver`
→ logs `INFO listening addr=0.0.0.0:8080` (a `GET /` returns HTTP 404 = serving).

**Client config** (set the URL **before first login**; never leave it blank):

- **Desktop (127.0.0.1):** Preferences ▸ Syncing ▸ self-hosted sync server URL = `http://127.0.0.1:8080/`.
- **AnkiDroid (10.0.2.2):** Settings ▸ Sync ▸ **Custom sync server** ▸ enable *Sync URL* =
  `http://10.0.2.2:8080/` (`10.0.2.2` is the emulator's alias for the host loopback — `127.0.0.1`
  from inside the emulator points at the phone, not the host). Then Sync ▸ log in as `greuser`.

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

- **Server dies if `SYNC_USER1` is unset** — the launcher always exports it. Committed
  `greuser:grepass` is a **local throwaway**, never a real secret.
- **`10.0.2.2`, not `127.0.0.1`, from the emulator.** Getting this wrong = "A network error occurred:
  error sending request" on the phone with nothing in the server log.
- **The server must stay running for the whole test.** A backgrounded `& ` launched inside a one-shot
  shell can be reaped between steps; keep `make sync-server` in its own live terminal (or a tracked
  background job). Symptom of a dead server: emulator/desktop login fails with a network error and
  `lsof -iTCP:8080 -sTCP:LISTEN` shows nothing.
- **Empty-server first contact = full sync.** Whoever syncs first should **upload**, the other
  **downloads**. `roundtrip_smoke.py`'s `_sync(prefer_upload=...)` encodes this; for the live test,
  choose "keep AnkiWeb" / Replace to pull the server (desktop) copy to the phone.
- **Reset server state** with `rm -rf sync/.sync-data` (gitignored). A stale server DB leaves the
  account non-empty and flips the first-contact direction.
- **Engine parity:** keep server engine **==** both clients **==** `f15cubing/anki@ea3acae`. A
  patch-version skew can force a full sync or a protocol error.

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
`:8080` server or the emulator.

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
+ both peers; `python -m anki.syncserver`). Foundation `SYNC_PORT=8080`; 7b proof `SYNC_PORT=8090`.
Block C 7b/7g verified 2026-07-03.
