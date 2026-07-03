# Block C robustness evidence — crash-safety (7g) + two-way sync (7b)

Headless proofs on **our fork's engine** (`anki 25.09.4`, buildhash `d52ca669`,
`f15cubing/anki@ea3acae`), captured 2026-07-03. Harnesses + how-to:
`robustness/README.md` and `docs/codebase/sync.md`. **Evidence + tests only — no engine change.**

## 7g — crash-durability (SIGKILL mid-review ×20)

`robustness/crash_test_7g.py` (`make crash-7g`) hard-kills **one evolving collection 20 times in a
row**, each time while `answerCard` is writing, then reopens and requires
`quick_check = ok` **and** `integrity_check = ok` with **no revlog loss**.

- **`7g-crash/crash_test_7g.txt`** — the 20-iteration run.
  **Result: 20/20 collections CLEAN**; 20/20 kills confirmed mid-review (hot ~4 MB WAL);
  31,405 committed reviews survived across all crashes with a monotonic (never-decreasing) revlog.
- **`7g-crash/checker_not_vacuous.txt`** — the `--selftest`: a pristine copy reads `ok/ok`, a
  byte-corrupted copy is caught (`DBError` on open). Proves the 20/20 result is meaningful, not a
  gate that always says "ok".

```
7g RESULT: 20/20 collections CLEAN after mid-review SIGKILL (quick_check=ok AND integrity_check=ok AND no revlog loss)
  kills confirmed mid-review (reviews committing at kill time): 20/20
  total committed reviews survived across all crashes: 31405
```

## 7b — two-way sync (10+10 no-loss + same-card conflict)

`sync/two_way_sync_7b.py` (`make sync-7b`) drives two headless peers through our self-hosted
`anki-sync-server`.

- **`7b-sync/two_way_sync_7b.txt`** — the full run.
  - **Phase 1 (no-loss):** A reviews 10 cards offline, B reviews 10 *different* cards offline →
    reconnect → **all 20 reviews land on both peers** (revlog 24/24 = baseline 4 + 20),
    `quick_check = ok`.
  - **Phase 2 (same-card conflict, pure review divergence):** A(Good) vs B(Again, later `mod`) on the
    same graduated card C → both peers **converge on B's later-`mod` state** (scheduling **LWW**:
    `type=3, ivl=1, lapses=1`) while **both C reviews survive** (revlog **union**, +2 on both);
    `quick_check = ok`.

```
PHASE 1  : PASS — all 20 offline reviews landed on both peers, no corruption
PHASE 2  : PASS — revlog union (+2 on both) AND scheduling LWW → B won (lapses=1); A's schedule overwritten; no corruption
7b RESULT: PASS  |  10+10 no-loss: all 20 landed  |  same-card conflict: revlog union + scheduling LWW (later-mod peer B won)
```

This is exactly the rule documented in `docs/codebase/sync.md` (revlog union · scheduling LWW ·
device-UUID tie-break DEFERRED; made deterministic by controlling sync order + `mod` timestamps, not
a code-level tie-break). Earlier iterations of the harness that mis-ordered the review timestamps
failed loudly (11–13/20 landed) before the fix — i.e. the assertions have teeth.

## Android leg — CUT this session (shared emulator)

A live Android round on the `anki_test` emulator was **cut**: the device was actively in use by the
Task-7 re-review subagent (AnkiDroid foreground), and driving it (force-stop + Check database) would
have disrupted that work. The **desktop proofs above stand on their own**, and the Android side of
both properties is already captured:

- **7g on device:** `../w3-android/` — a real FSRS session persists across a **force-stop/reopen** and
  **Check database → "Database rebuilt and optimized."**
- **7b on device:** `../w4-sync/` — the **live AnkiDroid ↔ desktop-peer** two-way round-trip through
  our server, ending in **Check database → "rebuilt and optimized."**

## Re-run

```bash
make crash-7g                       # 7g (no server needed)
make crash-7g ... --selftest        # (or: robustness/crash_test_7g.py --selftest)
make sync-server-7b                 # terminal A: fresh server on :8090
make sync-7b                        # terminal B: the 10+10 + conflict proof
```
