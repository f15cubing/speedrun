# Robustness proofs (Block C) — crash-safety (7g) + two-way sync (7b)

> Co-located doc for `robustness/crash_test_7g.py` and the root `Makefile` `crash-7g` target.
> The companion **7b** two-way sync proof lives with the sync harness
> (`sync/two_way_sync_7b.py`, documented in `docs/codebase/sync.md`). Both are the
> execution-plan **Block C** robustness proofs. **Evidence + tests only — no engine/collection
> code change (fast lane).** Read this before touching the crash harness.

## What these prove

| # | Property | Harness | Evidence |
|---|----------|---------|----------|
| **7g** | A collection survives repeated **hard crashes mid-review** with **zero corruption**. | `robustness/crash_test_7g.py` (`make crash-7g`) | `docs/evidence/robustness/7g-crash/` |
| **7b** | **No-loss** two-way sync (10 phone-offline + 10 desktop-offline → all 20 land) **and** the documented same-card **conflict rule** (revlog union · scheduling LWW). | `sync/two_way_sync_7b.py` (`make sync-7b`) | `docs/evidence/robustness/7b-sync/` |

Both run on **our fork's engine** via the primary desktop build
(`FORK_ANKI/out/pylib` + its `pyenv` python — the same importable engine `sync-smoke` uses,
`anki 25.09.4`, `f15cubing/anki@ea3acae`). They are read-only w.r.t. engine code: 7b **proves the
existing** stock conflict rule, it does not change it (D3 ceiling).

## 7g — crash-durability (`robustness/crash_test_7g.py`)

One evolving collection is hard-killed **20 times in a row**, each time *mid-review*:

- A child process opens the collection and runs a tight `getCard()`/`answerCard()` loop. Answers
  are Again/Hard so ~20 cards churn in the learning queue indefinitely — the real review write path
  (revlog insert + card update + queue update), forever, no throttle.
- The parent waits (via a heartbeat file written **outside** the collection, so it never perturbs
  the crash surface) until reviews are committing, dwells a random 0.05–0.60 s so the kill lands at
  varied points in the write cycle, then sends **SIGKILL**. The child gets no chance to close the
  DB, flush, or roll back — SQLite's WAL must recover atomically on the next open.
- After every crash the collection is reopened and must satisfy **all** of:
  `pragma quick_check = ok`, `pragma integrity_check = ok`, revlog **non-decreasing** (committed
  reviews never disappear), and the scheduler still builds a queue (usable).

`--selftest` proves the gate is **not vacuous**: a deliberately byte-corrupted collection is
reported unclean (`DBError` on open), while a pristine one reads `ok/ok`.

Run: `make crash-7g` (defaults to 20; `robustness/crash_test_7g.py --iters N` to change,
`--selftest` for the non-vacuity check).

**Result (2026-07-03, `anki 25.09.4` `d52ca669`):** **20/20 collections CLEAN**, all 20 kills
confirmed mid-review (hot ~4 MB WAL), 31,405 committed reviews survived with zero revlog loss;
self-test PASS. Full logs in `docs/evidence/robustness/7g-crash/`.

## 7b — two-way sync (`sync/two_way_sync_7b.py`)

Two headless peers (A "desktop", B "phone") on our engine + our self-hosted `anki-sync-server`:

- **Phase 1 (no-loss):** A reviews 10 cards offline, B reviews 10 *different* cards offline →
  reconnect → **all 20 land on both peers** (revlog union), `quick_check = ok`. Reviews are spaced
  a few ms apart on purpose: a revlog row's primary key is its epoch-ms timestamp, so a sub-ms
  automated loop would mint identical ids on both peers and the merge would collapse them — real
  devices review seconds apart and never collide.
- **Phase 2 (same-card conflict, pure review divergence):** both peers review the *same* graduated
  card C offline — A answers Good (interval grows), B answers Again (a lapse) with a strictly later
  `mod` — then reconnect in a controlled order (A, then B, then A pulls). The documented rule holds:
  **revlog union** (both C reviews survive, +2 on both) **and scheduling LWW** (the later-`mod`
  writer B wins; A's offline scheduling for C is overwritten; both converge on B's state).
  Determinism comes from controlling sync order + `mod` timestamps (recorded per peer), **not** a
  code-level tie-break — the device-UUID tie-break stays DEFERRED (see `docs/codebase/sync.md`).

Run: `make sync-server-7b` (fresh server on :8090) in one terminal, then `make sync-7b` in another.

**Result (2026-07-03):** Phase 1 **20/20 landed on both**; Phase 2 **revlog union +2 on both AND
scheduling LWW (later-mod peer B won)**; `quick_check = ok` throughout. Full log in
`docs/evidence/robustness/7b-sync/`.

## Android leg (representative round) — status

The desktop proofs above are the primary, fully-headless evidence. A live Android round on the
`anki_test` emulator was **CUT** this session: the emulator is a **shared** resource and was
actively in use by the Task-7 re-review subagent (AnkiDroid foreground on `SingleFragmentActivity`),
so driving it (force-stop mid-review + Check database) would have disrupted that work. The Android
side of both properties is already captured in prior evidence:

- **7g (no corruption on device):** `docs/evidence/w3-android/` — a real FSRS review session
  persists across a **force-stop/reopen** and **Check database → "Database rebuilt and optimized."**
- **7b (two-way sync on device):** `docs/evidence/w4-sync/` — the **live AnkiDroid ↔ desktop-peer**
  round-trip through our server, both directions, ending in **Check database → "rebuilt and
  optimized."**

To run the emulator round when the device is free: review a few cards in AnkiDroid, `adb -s
emulator-5554 shell am force-stop com.ichi2.anki.debug` mid-session, relaunch, then **Check database**
→ expect "Database rebuilt and optimized."

## Invariants / gotchas

- **Run with the primary build's python** (`FORK_ANKI/out/pylib`), never a feature worktree's
  partial `anki/out` — same rule as `sync-smoke` (see `docs/codebase/sync.md`).
- **7b needs its own server on :8090** with a distinct data dir (`sync/.sync-data-7b`, gitignored) so
  it never collides with the shared `:8080` sync server or the emulator.
- **These add no engine code.** 7b proves the stock conflict rule; it must not change it.

---
Last verified against: `f15cubing/anki@ea3acae` (`anki 25.09.4`, buildhash `d52ca669`; server engine + both peers).
