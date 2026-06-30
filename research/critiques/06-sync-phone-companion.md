# Critique 06 — Shared-engine phone + sync (DEFERRED track)

_Per the Round-1 steer, the codebase/sync track is parked for hands-on work later. Critique kept proportionate; no follow-up prompt now._

**Verdict: sound, and the conflict-model section is the strongest part.** It is well-sourced (Anki Manual + a verbatim Damien Elmes forum statement) and it surfaces a subtle trap that would otherwise wreck the demo.

## Useful (carry forward) — [strong] unless noted
- **Conflict model (answers spec 7b):** `revlog` entries are **unioned** (both reviews survive; PK = epoch-ms id); card **scheduling state is last-writer-wins** ("kept in the state it was when most recently answered"); genuinely unmergeable structural divergence forces a **one-way full sync** (whole-side overwrite). [strong — manual + maintainer quote]
- **Critical demo caveat:** the same-card conflict demo must be **constructed carefully** — if you trip a schema/sanity mismatch, Anki falls back to full-sync (overwrite) instead of merging, which would *not* demonstrate the scheduling winner rule. Keep the test to pure review divergence. This prevents a meaningless demo. [strong]
- **Proposed winner rule** (latest-review-timestamp wins for scheduling + revlog union + deterministic device-ID tie-break) is a defensible improvement over Anki's order-dependent LWW: it makes the outcome reproducible/testable. [moderate→strong]
- **Realistic platform path:** Android via AnkiDroid's `rsdroid` (real shared `rslib`, sync works out of the box) clears the 70% no-phone ceiling; **iOS from scratch in one week is not realistic** — honest and correct. [strong judgment]
- **Crash-safety** (SQLite `BEGIN IMMEDIATE` + WAL) and **`make bench`** (Criterion + hyperfine, synthetic 50k deck) are standard and sound. [moderate]

## Caveats / must-verify (at build time)
1. **Integration effort understated:** our **custom Rust change (the mastery query) must flow into the `rsdroid` build** (build the Anki fork as the submodule `rsdroid` compiles). Feasible but a real step — the "free" sync only stays free if the fork stays compatible.
2. **Some module filenames and the exact WAL PRAGMA are `[inferred]`** — verify in the pinned repo.
3. **"Same engine on both" is honest only if the phone really runs your forked `rslib`** — confirm the AnkiDroid backend builds against your fork, not upstream.

## Decision
- **Deferred; no follow-up prompt.** Carry into synthesis: the **conflict model (revlog union + scheduling LWW + careful demo construction)** and the **Android-only realistic path**. Re-open when build begins.
