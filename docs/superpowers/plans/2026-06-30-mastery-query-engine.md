# Mastery Query (Rust Engine Change) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`)
> syntax for tracking.
>
> **This is an ENGINE-LANE change** (`shipping-changes`): implement in a **git worktree**, run
> `git submodule update --init --recursive`, verify with `building-and-testing`, and hand the PR to a
> **DIFFERENT** agent for the **extra gate**. **Never self-merge.** Spec:
> `docs/superpowers/specs/2026-06-30-mastery-query-engine-design.md`.

**Goal:** Add a read-only `StatsService.MasteryQuery` RPC that returns, per topic tag,
`{ topic, total_cards, reviewed_count, mastered_count, avg_recall }` — computed by one FSRS-retrievability
SQL pass aggregated in Rust — with a Python binding, tests, a 50k benchmark, and an rsdroid reachability
check. No mutation, no `OpChanges`, no schema change.

**Architecture:** Additive protobuf message + RPC on the existing `StatsService` (empty
`BackendStatsService` auto-delegates to `Collection`). A pure Rust aggregation function
(`aggregate_mastery`) is unit-tested in isolation; a thin storage function runs the single SQL pass
(reusing the `extract_fsrs_retrievability` UDF exactly as `search/mod.rs` does); a `Collection` method
wires timing → storage → aggregation; a `collection.py` wrapper exposes it to desktop. The same change
ships to Android because it lives in `rslib`.

**Tech Stack:** Rust (`anki` crate / `rslib`), protobuf (`prost`, Anki codegen), `rusqlite`,
Python (`anki` pylib + `pytest`), Anki build (`./check`, `./ninja`), Android/rsdroid (Gradle + NDK).

## Global Constraints

- **Read-only hard ceiling (PRD D1 §5.3):** pure `SELECT`; **never** call `transact` /
  `transact_no_undo`; the RPC returns `MasteryResponse`, **never** `OpChanges`. Do **not** replicate
  `card_stats`'s `last_review_time` write-back.
- **No schema change:** topics come from `notes.tags`; `SCHEMA_MAX_VERSION` stays 18.
- **Don't touch** `scheduler/answering/` or `scheduler/fsrs/` interval math.
- **Engine generic:** match whatever tag strings the caller passes — **no GRE taxonomy in the engine**.
- **`mastered` = has FSRS memory state AND `R >= 0.9`** (`MASTERY_RETRIEVABILITY_THRESHOLD`).
  `reviewed_count` = cards with a memory state (non-null `R`). `total_cards` = every matching card,
  **including suspended/buried** (no `queue` filter). `avg_recall` = mean `R` over reviewed cards, or
  `0.0`.
- **Hierarchical match:** a requested tag matches that tag **and** its `::*` descendants; one
  independent row per requested topic, in request order.
- **Verify symbols against the pin** `anki@25.09.4` (`d52ca66`) as you go; a `.proto` change requires a
  **full build** (`./check`) before generated types/traits exist (anki `CLAUDE.md`).
- **Docs in the same PR** (`codebase-docs`): bump `Last verified against:` SHAs.

---

## Task 1: Proto contract + Rust engine change (proto + storage + aggregation + service)

**Files:**
- Modify: `anki/proto/anki/stats.proto` (add 3 messages + 1 rpc)
- Create: `anki/rslib/src/stats/mastery.rs` (aggregation + `Collection` method + unit tests)
- Modify: `anki/rslib/src/stats/mod.rs` (add `mod mastery;`)
- Modify: `anki/rslib/src/stats/service.rs` (implement the trait method)
- Modify: `anki/rslib/src/storage/card/mod.rs` (single-pass fetch fn)

**Interfaces:**
- Consumes: the `extract_fsrs_retrievability` SQLite UDF; `Collection::timing_today()`; `crate::prelude`.
- Produces:
  - Proto `anki.stats.MasteryRequest { repeated string topics }`,
    `TopicMastery { string topic; uint32 total_cards; uint32 reviewed_count; uint32 mastered_count; double avg_recall }`,
    `MasteryResponse { repeated TopicMastery topics }`, and `rpc MasteryQuery(MasteryRequest) returns (MasteryResponse)`.
  - `pub(crate) const MASTERY_RETRIEVABILITY_THRESHOLD: f64 = 0.9;`
  - `pub(crate) fn aggregate_mastery(rows: &[(String, Option<f64>)], topics: &[String], threshold: f64) -> Vec<anki_proto::stats::TopicMastery>`
  - `Collection::mastery_for_topics(&mut self, topics: &[String]) -> error::Result<anki_proto::stats::MasteryResponse>`
  - `SqliteStorage::all_card_tags_and_retrievability(&self, days_elapsed: u32, next_day_at: i64, now: i64) -> Result<Vec<(String, Option<f64>)>>`

- [ ] **Step 1: Add the proto messages + rpc**

In `anki/proto/anki/stats.proto`, add the rpc to `StatsService` (leave `BackendStatsService {}` empty):

```proto
service StatsService {
  rpc CardStats(cards.CardId) returns (CardStatsResponse);
  rpc GetReviewLogs(cards.CardId) returns (ReviewLogs);
  rpc Graphs(GraphsRequest) returns (GraphsResponse);
  rpc GetGraphPreferences(generic.Empty) returns (GraphPreferences);
  rpc SetGraphPreferences(GraphPreferences) returns (generic.Empty);
  rpc MasteryQuery(MasteryRequest) returns (MasteryResponse);
}
```

and add these messages (anywhere at top level in the file):

```proto
message MasteryRequest {
  // Tag strings; each matches that tag AND its ::* descendants (hierarchical).
  repeated string topics = 1;
}

message TopicMastery {
  string topic = 1;          // echoes the requested tag
  uint32 total_cards = 2;    // matching cards (incl. suspended/buried/new)
  uint32 reviewed_count = 3; // of those, cards with an FSRS memory state (non-null R)
  uint32 mastered_count = 4; // of reviewed, cards with R >= 0.9
  double avg_recall = 5;     // mean R over reviewed cards; 0.0 when reviewed_count == 0
}

message MasteryResponse {
  repeated TopicMastery topics = 1; // one row per requested topic, in request order
}
```

- [ ] **Step 2: Full build to regenerate bindings (expected to FAIL to compile)**

Run (see `building-and-testing` for the canonical invocation): `cd anki && ./check`
Expected: codegen regenerates `TopicMastery`/`MasteryRequest`/`MasteryResponse` and adds
`mastery_query` to the generated `StatsService` trait, then **rslib fails to compile** with a
"not all trait items implemented: `mastery_query`" error. That error confirms the proto wired through.

- [ ] **Step 3: Register the new module + add the SQL fetch fn**

In `anki/rslib/src/stats/mod.rs` add `mod mastery;` next to the others:

```rust
mod card;
mod graphs;
mod mastery;
mod service;
mod today;

pub use today::studied_today;
```

In `anki/rslib/src/storage/card/mod.rs`, add to the `impl SqliteStorage` block (mirrors the UDF call
form used in `search/mod.rs`; timing ints are interpolated, no user input in the SQL):

```rust
/// One read-only pass: every card's note tags + its current FSRS retrievability
/// R (NULL when the card has no memory state). No queue/suspension filter, so
/// suspended and buried cards are included (mastery = knowledge, not scheduling).
pub(crate) fn all_card_tags_and_retrievability(
    &self,
    days_elapsed: u32,
    next_day_at: i64,
    now: i64,
) -> Result<Vec<(String, Option<f64>)>> {
    let sql = format!(
        "SELECT n.tags, \
         extract_fsrs_retrievability(c.data, \
           case when c.odue != 0 then c.odue else c.due end, c.ivl, \
           {days_elapsed}, {next_day_at}, {now}) \
         FROM cards c JOIN notes n ON c.nid = n.id"
    );
    self.db
        .prepare(&sql)?
        .query_and_then([], |row| -> Result<(String, Option<f64>)> {
            Ok((row.get(0)?, row.get(1)?))
        })?
        .collect()
}
```

- [ ] **Step 4: Write the failing unit tests for the pure aggregator**

Create `anki/rslib/src/stats/mastery.rs` with imports, the constant, a **stub** aggregator, and tests:

```rust
// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
use anki_proto::stats::MasteryResponse;
use anki_proto::stats::TopicMastery;

use crate::prelude::*;

/// A card counts as "mastered" when it has an FSRS memory state and its current
/// retrievability R is at least this value.
pub(crate) const MASTERY_RETRIEVABILITY_THRESHOLD: f64 = 0.9;

/// True if `card_tags` (space-delimited) contains `topic` exactly or any ::* descendant.
fn tag_matches(card_tags: &str, topic: &str) -> bool {
    let prefix = format!("{topic}::");
    card_tags
        .split_whitespace()
        .any(|t| t == topic || t.starts_with(&prefix))
}

/// Pure aggregation over (tags, R) rows into one TopicMastery per requested topic.
pub(crate) fn aggregate_mastery(
    _rows: &[(String, Option<f64>)],
    _topics: &[String],
    _threshold: f64,
) -> Vec<TopicMastery> {
    unimplemented!("Step 5")
}

impl Collection {
    pub(crate) fn mastery_for_topics(&mut self, topics: &[String]) -> Result<MasteryResponse> {
        let timing = self.timing_today()?;
        let rows = self.storage.all_card_tags_and_retrievability(
            timing.days_elapsed,
            timing.next_day_at.0,
            timing.now.0,
        )?;
        Ok(MasteryResponse {
            topics: aggregate_mastery(&rows, topics, MASTERY_RETRIEVABILITY_THRESHOLD),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_and_no_match_yield_zeros() {
        let none: Vec<(String, Option<f64>)> = vec![];
        let out = aggregate_mastery(&none, &["topic::calculus".to_string()], MASTERY_RETRIEVABILITY_THRESHOLD);
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].total_cards, 0);
        assert_eq!(out[0].reviewed_count, 0);
        assert_eq!(out[0].mastered_count, 0);
        assert_eq!(out[0].avg_recall, 0.0);

        let rows = vec![(" topic::algebra::linear ".to_string(), Some(0.95))];
        let out = aggregate_mastery(&rows, &["topic::calculus".to_string()], MASTERY_RETRIEVABILITY_THRESHOLD);
        assert_eq!(out[0].total_cards, 0);
    }

    #[test]
    fn aggregation_and_hierarchy() {
        let rows = vec![
            (" topic::calculus::integral_single ".to_string(), Some(0.95)), // mastered
            (" topic::calculus::integral_single ".to_string(), Some(0.80)), // reviewed, not mastered
            (" topic::calculus::differential_single ".to_string(), Some(0.90)), // mastered (== threshold)
            (" topic::calculus::differential_single ".to_string(), None),   // new, unreviewed
            (" topic::algebra::linear src::x ".to_string(), Some(0.99)),    // other bucket + extra tag
        ];

        let leaf = aggregate_mastery(
            &rows,
            &["topic::calculus::integral_single".to_string()],
            MASTERY_RETRIEVABILITY_THRESHOLD,
        );
        assert_eq!(leaf[0].total_cards, 2);
        assert_eq!(leaf[0].reviewed_count, 2);
        assert_eq!(leaf[0].mastered_count, 1);
        assert!((leaf[0].avg_recall - 0.875).abs() < 1e-9);

        // hierarchical: the bucket rolls up both calculus leaves; the new card counts in total only
        let bucket = aggregate_mastery(&rows, &["topic::calculus".to_string()], MASTERY_RETRIEVABILITY_THRESHOLD);
        assert_eq!(bucket[0].total_cards, 4);
        assert_eq!(bucket[0].reviewed_count, 3);
        assert_eq!(bucket[0].mastered_count, 2);
        assert!((bucket[0].avg_recall - (0.95 + 0.80 + 0.90) / 3.0).abs() < 1e-9);
    }
}
```

Run: `cd anki && cargo test -p anki stats::mastery::tests -- --nocapture`
Expected: FAIL — `empty_and_no_match_yield_zeros` / `aggregation_and_hierarchy` panic at
`unimplemented!("Step 5")`.

- [ ] **Step 5: Implement `aggregate_mastery` (make the tests pass)**

Replace the stub body in `mastery.rs`:

```rust
pub(crate) fn aggregate_mastery(
    rows: &[(String, Option<f64>)],
    topics: &[String],
    threshold: f64,
) -> Vec<TopicMastery> {
    topics
        .iter()
        .map(|topic| {
            let mut total_cards = 0u32;
            let mut reviewed_count = 0u32;
            let mut mastered_count = 0u32;
            let mut sum_r = 0.0f64;
            for (tags, r) in rows {
                if tag_matches(tags, topic) {
                    total_cards += 1;
                    if let Some(r) = r {
                        reviewed_count += 1;
                        sum_r += *r;
                        if *r >= threshold {
                            mastered_count += 1;
                        }
                    }
                }
            }
            TopicMastery {
                topic: topic.clone(),
                total_cards,
                reviewed_count,
                mastered_count,
                avg_recall: if reviewed_count > 0 {
                    sum_r / reviewed_count as f64
                } else {
                    0.0
                },
            }
        })
        .collect()
}
```

Run: `cd anki && cargo test -p anki stats::mastery::tests -- --nocapture`
Expected: the two pure tests PASS (the read-only invariant test is added in Step 7).

- [ ] **Step 6: Implement the trait method**

In `anki/rslib/src/stats/service.rs`, add inside `impl crate::services::StatsService for Collection`:

```rust
    fn mastery_query(
        &mut self,
        input: anki_proto::stats::MasteryRequest,
    ) -> error::Result<anki_proto::stats::MasteryResponse> {
        self.mastery_for_topics(&input.topics)
    }
```

Run: `cd anki && cargo build -p anki`
Expected: rslib now compiles (trait fully implemented).

- [ ] **Step 7: Add the read-only invariant test (the hard-ceiling proof)**

Append to the `#[cfg(test)] mod tests` in `mastery.rs`:

```rust
    #[test]
    fn mastery_query_is_read_only() {
        let mut col = Collection::new();
        let mut note = col.basic_notetype().new_note();
        note.tags = vec!["topic::calculus::integral_single".to_string()];
        note.set_field(0, "q").unwrap();
        note.set_field(1, "a").unwrap();
        col.add_note(&mut note, DeckId(1)).unwrap();

        let undo_before = col.undo_status().last_step;
        let card_count_before = col.storage.get_all_cards().len();

        let res = col
            .mastery_for_topics(&["topic::calculus".to_string()])
            .unwrap();
        assert_eq!(res.topics[0].total_cards, 1);
        assert_eq!(res.topics[0].reviewed_count, 0); // brand-new card, no memory state

        // read-only: no new undo step, no corruption, nothing added/removed.
        assert_eq!(col.undo_status().last_step, undo_before, "must not create an undo step");
        assert_eq!(col.storage.get_all_cards().len(), card_count_before);
        assert!(!col.storage.quick_check_corrupt(), "collection must not be corrupted");
    }
```

Run: `cd anki && cargo test -p anki stats::mastery -- --nocapture`
Expected: all three PASS.

- [ ] **Step 8: Format + full check, then commit**

Run: `cd anki && ./check` (formats + builds + runs checks; see `building-and-testing`). Confirm green
with `verification-before-completion` before claiming success.

```bash
git add anki/proto/anki/stats.proto anki/rslib/src/stats/mastery.rs anki/rslib/src/stats/mod.rs \
  anki/rslib/src/stats/service.rs anki/rslib/src/storage/card/mod.rs
git commit -m "feat(rslib): read-only MasteryQuery RPC (per-topic FSRS mastery aggregate)"
```

---

## Task 2: Python binding + integration test

**Files:**
- Modify: `anki/pylib/anki/collection.py` (add `mastery_query`)
- Create: `anki/pylib/tests/test_mastery.py`

**Interfaces:**
- Consumes: the generated `self._backend.mastery_query(topics=...)` (exists after Task 1's build);
  `stats_pb2.MasteryResponse` (already imported in `collection.py`).
- Produces: `Collection.mastery_query(self, topics: Sequence[str]) -> stats_pb2.MasteryResponse`.

- [ ] **Step 1: Write the failing Python test**

Create `anki/pylib/tests/test_mastery.py`:

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from tests.shared import getEmptyCol


def _add(col, front, tag):
    note = col.newNote()
    note["Front"] = front
    note["Back"] = "a"
    note.tags.append(tag)
    col.addNote(note)


def test_mastery_query_counts_and_hierarchy():
    col = getEmptyCol()
    for i in range(3):
        _add(col, f"c{i}", "topic::calculus::integral_single")
    _add(col, "alg", "topic::algebra::linear")

    res = col.mastery_query(
        ["topic::calculus", "topic::calculus::integral_single", "topic::algebra"]
    )
    by = {t.topic: t for t in res.topics}
    assert by["topic::calculus::integral_single"].total_cards == 3
    assert by["topic::calculus"].total_cards == 3  # hierarchical rollup
    assert by["topic::algebra"].total_cards == 1
    # brand-new cards have no FSRS memory state
    assert by["topic::calculus"].reviewed_count == 0
    assert by["topic::calculus"].mastered_count == 0
    assert by["topic::calculus"].avg_recall == 0.0
    col.close()


def test_mastery_query_is_read_only_with_undo():
    col = getEmptyCol()
    for i in range(3):
        _add(col, f"c{i}", "topic::calculus::integral_single")

    # add a note, run the mastery query in between, then undo the add
    _add(col, "extra", "topic::calculus::integral_single")
    assert col.mastery_query(["topic::calculus"]).topics[0].total_cards == 4
    assert col.undo_status().undo  # the "Add Note" is undoable despite the read
    col.undo()
    assert col.mastery_query(["topic::calculus"]).topics[0].total_cards == 3
    col.close()
```

- [ ] **Step 2: Run to verify it fails**

Run (see `building-and-testing`): `cd anki && ./ninja check:pytest:pylib` (or, after `./ninja wheels`,
`python -m pytest pylib/tests/test_mastery.py -q`).
Expected: FAIL — `AttributeError: 'Collection' object has no attribute 'mastery_query'`.

- [ ] **Step 3: Add the binding**

In `anki/pylib/anki/collection.py`, near the other stats methods (e.g. after `get_review_logs`,
around line 1025), add:

```python
    def mastery_query(
        self, topics: Sequence[str]
    ) -> stats_pb2.MasteryResponse:
        """Per-topic mastery over the collection (read-only).

        Each requested tag matches that tag and its ``::*`` descendants. Returns one
        row per requested topic with total/reviewed/mastered counts and mean recall.
        """
        return self._backend.mastery_query(topics=list(topics))
```

(`Sequence` is already imported in `collection.py`; `stats_pb2` is already imported.)

- [ ] **Step 4: Run to verify it passes**

Run: `cd anki && ./ninja check:pytest:pylib` (or `python -m pytest pylib/tests/test_mastery.py -q`).
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add anki/pylib/anki/collection.py anki/pylib/tests/test_mastery.py
git commit -m "feat(pylib): Collection.mastery_query binding + integration test"
```

---

## Task 3: 50k-card performance check

**Files:**
- Modify: `anki/rslib/src/stats/mastery.rs` (add an `#[ignore]`d perf test)

**Interfaces:**
- Consumes: `Collection::new`, `add_note`, `mastery_for_topics`.
- Produces: `mastery_query_50k_perf` (manual, ignored) printing p50/p95 and asserting p50 < 50 ms.

- [ ] **Step 1: Add the perf test**

Append to `#[cfg(test)] mod tests` in `mastery.rs`:

```rust
    // Run manually: cargo test -p anki stats::mastery::tests::mastery_query_50k_perf \
    //   --release -- --ignored --nocapture
    #[test]
    #[ignore]
    fn mastery_query_50k_perf() {
        use std::time::Instant;

        let leaves = [
            "topic::calculus::integral_single",
            "topic::calculus::differential_single",
            "topic::algebra::linear",
            "topic::additional::probability_stats",
        ];
        let mut col = Collection::new();
        for i in 0..50_000usize {
            let mut note = col.basic_notetype().new_note();
            note.tags = vec![leaves[i % leaves.len()].to_string()];
            note.set_field(0, &format!("q{i}")).unwrap();
            note.set_field(1, "a").unwrap();
            col.add_note(&mut note, DeckId(1)).unwrap();
        }
        let topics: Vec<String> = leaves.iter().map(|s| s.to_string()).collect();

        let mut samples = Vec::new();
        for _ in 0..20 {
            let t = Instant::now();
            let _ = col.mastery_for_topics(&topics).unwrap();
            samples.push(t.elapsed().as_secs_f64() * 1000.0);
        }
        samples.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let p50 = samples[samples.len() / 2];
        let p95 = samples[(samples.len() as f64 * 0.95) as usize];
        println!("mastery 50k: p50={p50:.2}ms p95={p95:.2}ms");
        assert!(p50 < 50.0, "p50 {p50:.2}ms exceeds 50ms target");
    }
```

- [ ] **Step 2: Run the perf test**

Run: `cd anki && cargo test -p anki stats::mastery::tests::mastery_query_50k_perf --release -- --ignored --nocapture`
Expected: prints `mastery 50k: p50=…ms p95=…ms` and PASSES (p50 < 50 ms). **If it fails the 50 ms
target:** implement the spec's §3.5 fallback — build a dynamic `WHERE` of the requested topics'
`LIKE` patterns (reusing `search/sqlwriter.rs` tag patterns) to narrow the scan — then re-measure.
Do **not** cache (PRD §5.3).

- [ ] **Step 3: Commit**

```bash
git add anki/rslib/src/stats/mastery.rs
git commit -m "test(rslib): 50k-card MasteryQuery performance check (<50ms p50)"
```

---

## Task 4: rsdroid reachability check

**Files:** none in-repo (a build + verification step); notes captured in the PR body.

**Interfaces:** consumes the Android toolchain via `building-and-testing` + `working-with-submodules`.

- [ ] **Step 1: Rebuild the Android backend with our engine change**

Following `building-and-testing` (Android/rsdroid section) and `working-with-submodules`, rebuild the
rsdroid backend/AAR against our modified `anki` submodule (the same path used in Spike 2).

- [ ] **Step 2: Confirm the RPC crossed the JNI/codegen boundary**

Confirm the regenerated Android backend bindings expose the new RPC. Search the generated backend
interface/sources produced by the build for the new method/messages:

```bash
rg -i "masteryQuery|MasteryResponse|MasteryRequest" <rsdroid/AnkiDroid generated backend output dir>
```

Expected: the generated Kotlin/Java backend surface contains `masteryQuery` (proving the additive proto
flowed to Android). A full on-device call is deferred to W3 (Android review spec). Record the command
+ result in the PR body's extra-gate note.

---

## Task 5: Docs, STATUS, and open the engine-lane PR

**Files:**
- Modify: `docs/codebase/rslib.md`, `docs/codebase/proto-rpc.md`, `docs/codebase/pylib.md`
- Modify: `docs/codebase/INDEX.md`, `docs/STATUS.md`

- [ ] **Step 1: Update the engine docs (mark built + bump SHA)**

- `rslib.md`: in "Mastery Query insertion points", note it is **implemented** — files
  `stats/mastery.rs` (aggregation + `mastery_for_topics`), `storage/card/mod.rs`
  (`all_card_tags_and_retrievability`), `stats/service.rs` (trait impl); bump `Last verified against:`.
- `proto-rpc.md`: mark the `MasteryQuery` rpc on `StatsService` as added; bump SHA.
- `pylib.md`: note `Collection.mastery_query(topics)` exists; bump SHA.

- [ ] **Step 2: Move the INDEX row to "Built"**

In `docs/codebase/INDEX.md`, move **"Our app additions — Mastery Query Rust change"** from "Planned"
to the "Built areas" table: Doc = `docs/codebase/rslib.md` (§ Mastery Query), Code paths =
`anki/proto/anki/stats.proto`, `anki/rslib/src/stats/mastery.rs`, `anki/rslib/src/storage/card/`,
`anki/pylib/anki/collection.py`; set "Last verified" to the new branch HEAD SHA.

- [ ] **Step 3: Update STATUS.md**

Move the "Wednesday Mastery Query spec — drafting" line to reflect the shipped engine change (e.g.
`PR #N (merged) — read-only MasteryQuery RPC + pylib binding + tests + 50k bench + rsdroid reachability`),
and update "Next" to the remaining Wednesday sub-specs (W2 dashboard, W3 Android review, W4 sync).

- [ ] **Step 4: Verify, push, open the engine-lane PR (different-agent review)**

Confirm `cd anki && ./check` is green and the Python + perf tests pass
(`verification-before-completion`). Then push the branch and open the PR with the `pr-checklist.md`
body template, filling the **extra gate** section: undo proof (`mastery_query_is_read_only` +
`test_mastery_query_is_read_only_with_undo`), read-only invariant test name, the ≥3 Rust + 1 Python
test names, "no `OpChanges`" confirmation, the rsdroid reachability result, and the files-touched +
merge-difficulty note.

```bash
git push -u origin agent/rslib-mastery-query
gh pr create --base main --head agent/rslib-mastery-query --title \
  "feat(rslib): read-only MasteryQuery RPC (per-topic FSRS mastery)" --body "<pr-checklist.md template>"
```

**Hand off to a DIFFERENT agent** for the engine extra gate. **Never self-merge.** On merge, the
reviewer updates `docs/STATUS.md` and deletes the branch (`finishing-a-development-branch`).

---

## Self-Review

**1. Spec coverage** (`2026-06-30-mastery-query-engine-design.md`):
- §1 proto contract (3 messages + rpc, empty `BackendStatsService`) → Task 1 Step 1. ✓
- §2 file layout (proto, `stats/mastery.rs`, `stats/service.rs`, `storage/card/mod.rs`, `collection.py`,
  tests, docs) → Tasks 1, 2, 5. ✓
- §3 data flow (timing → single-pass UDF SQL → Rust aggregation; hierarchical `tag_matches`; perf
  fallback) → Task 1 Steps 3–5 + Task 3 Step 2. ✓
- §4 read-only guarantee (no `transact`/`OpChanges`; invariant test) → Task 1 Step 7 + Task 2 read-only
  test. ✓
- §5 tests (≥3 Rust: empty/zero, aggregation+hierarchy, read-only invariant; 1 Python integration;
  corruption via `quick_check_corrupt`; 50k perf; rsdroid reachability) → Tasks 1, 2, 3, 4. ✓
- §6 merge-difficulty note → Task 5 Step 4 (PR body). ✓
- Decisions: `mastered = memory-state AND R>=0.9`, `reviewed_count`, suspended included, hierarchical
  match, enriched shape → encoded in `aggregate_mastery` + the SQL (no queue filter) + proto. ✓

**2. Placeholder scan:** No "TBD"/"add error handling"/"similar to Task N". The only intentional
`unimplemented!` is the Step-4 TDD stub, replaced in Step 5. Task 4's `rg` target dir is
build-output-dependent and marked as such (resolved at build time), not a plan placeholder.

**3. Type consistency:** `aggregate_mastery(rows: &[(String, Option<f64>)], topics: &[String], threshold: f64) -> Vec<TopicMastery>`
is defined and called identically (Task 1 Steps 4/5, `mastery_for_topics`). `all_card_tags_and_retrievability`
returns `Vec<(String, Option<f64>)>`, matching the aggregator input. `TopicMastery` field names/types
(`total_cards`/`reviewed_count`/`mastered_count` `uint32`; `avg_recall` `double`/`f64`) match the proto,
the Rust struct usage, and the Python assertions. Binding `mastery_query(topics)` → `_backend.mastery_query(topics=...)`
→ trait `mastery_query(MasteryRequest)` → `mastery_for_topics(&input.topics)` are consistent end to end.

## Execution Handoff

Engine-lane: implement in a git worktree on branch `agent/rslib-mastery-query` (superpowers:using-git-worktrees
+ `git submodule update --init --recursive`), build/test via `building-and-testing`, and ship through
`shipping-changes` with a **DIFFERENT** agent running the extra gate. **Two execution options:**
1. **Subagent-Driven (recommended)** — a fresh subagent per task, review between tasks (superpowers:subagent-driven-development).
2. **Inline Execution** — execute tasks in this session with checkpoints (superpowers:executing-plans).
