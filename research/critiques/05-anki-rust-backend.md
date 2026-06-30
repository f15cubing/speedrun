# Critique 05 — Anki Rust backend (DEFERRED track)

_Per the Round-1 steer, the codebase track is parked for hands-on work later. Critique kept proportionate; no follow-up prompt now._

**Verdict: sound and safe.** Recommends candidate **(c) the read-only Mastery query** for the right reason — read-only means it never enters `transact`, so it is *structurally incapable* of breaking undo or corrupting the collection, while still being a genuine Rust change (new proto message + read RPC + SQL aggregate + pylib binding). Good risk/reward for a hard-ceiling-gated 20%.

## Useful (carry forward) — [strong] reasoning, [verify] specifics
- **Read-only ⇒ undo-safe** (the `is_dql()` read path never touches the undo stack). The cleanest way to satisfy "real Rust change" without endangering collection integrity. [strong logic]
- **Tags as the topic substrate (no schema change).** This is an **architectural keystone**: the *same* `topic::*` tag taxonomy feeds the mastery query (SQ5), the coverage map (SQ1/7c), and interleaving (SQ4). One taxonomy, four uses. Avoid a new SQLite column (would bump `SCHEMA_MAX_VERSION`, breaking sync). [strong]
- **Footgun catalog is the right one:** the `card.mtime == entry.mtime()` panic ("bug: card modified without updating queue"); returning `OpChanges` from a read RPC (would imply mutation / clear undo); schema-version bump breaking sync round-trip. [strong]
- **Avoid candidate (b) topic-aware scheduling** (touches FSRS interval correctness + undo of `answerCard` — the most version-volatile code). Correct call for a one-week scope. [strong]

## Caveats / must-verify (at build time, not now)
1. **Many paths/symbols are explicitly `[inferred]`** (`UndoManager`, `UndoableChange` variants, `begin/end_undoable_operation`, base `open_test_collection`). The response is *appropriately honest* about confirmed-vs-inferred. **Before building, verify every path/symbol against your pinned Anki release.**
2. **Specific version/commit details** (DeepWiki commit `8f214453`, `SCHEMA_MAX_VERSION = 18`, Criterion 0.8.2 / MSRV 1.86, FSRS-6 in 25.07) are unverifiable from here and the scheduler churns between releases. **Pin to a tagged release and re-confirm.**
3. **Note FSRS-7 does not appear here** — consistent with critique-02's suspicion that prompt 2's "FSRS-7" may not exist. Anki ships **FSRS-6/FSRS-rs**.

## Decision
- **Deferred; no follow-up prompt.** Carry two things into synthesis: (a) **read-only mastery query is the recommended Rust change**, and (b) **tags are the single shared topic taxonomy** across mastery/coverage/interleaving. Re-open this track when build begins and verify all `[inferred]` symbols.
