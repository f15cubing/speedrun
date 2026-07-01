# Mastery Query (Rust Engine Change) — Design Spec

> The one real Anki engine change (PRD §5, D1): a **read-only** `StatsService.MasteryQuery` RPC that
> returns, per topic tag, `{ total_cards, reviewed_count, mastered_count, avg_recall }` via a single
> FSRS-retrievability SQL pass aggregated in Rust. Additive, never mutating, and shipped to desktop
> *and* Android because it lives in `rslib`. Companion to `docs/PRD.md` (§5, §5.2–§5.4, D1) and
> `docs/execution-plan.md` (Wednesday / Milestone 1). Verified insertion points:
> `docs/codebase/rslib.md`, `docs/codebase/proto-rpc.md`, `docs/codebase/pylib.md`. Dated 2026-06-30.

## Wednesday decomposition

Wednesday (execution-plan Day 2 / Milestone 1) is decomposed into per-subsystem sub-specs so each is
independently reviewable. **This is W1, the critical path — everything else hangs off it.**

- **W1 — Mastery Query (this spec):** the engine change, proven on desktop + reachable on Android.
- **W2 — Desktop dashboard:** memory score as a range + coverage map (consumes this RPC).
- **W3 — Android review:** rebuild rsdroid with our change, load the deck, run a review session.
- **W4 — Sync foundation:** stand up `anki-sync-server`, conflict-rule smoke test.

## Status at time of writing

The fork builds on both surfaces (Spike 1 desktop `./run`, Spike 2 Android `assembleFullDebug`),
submodules are pinned (`anki@25.09.4` `d52ca66`, `Anki-Android@v2.24.0` `ebcf8e0`), the seeded
`topic::*`-tagged study deck exists (PR #1), and the engine docs are verified against the pin. No
engine code has been changed yet — this spec defines that change.

## Decisions (locked with owner, 2026-06-30)

- **Definition of "mastered":** a card is mastered iff it has an FSRS memory state **and** its current
  absolute retrievability `R ≥ 0.9` (a named constant `MASTERY_RETRIEVABILITY_THRESHOLD`). `R` is
  "P(recall now)", matching the Memory score (PRD §7a).
- **`avg_recall`:** mean `R` over the topic's **reviewed** cards (those with a memory state, i.e.
  non-null `R`); `0.0` when `reviewed_count == 0`.
- **`total_cards`:** every card whose note carries the topic tag, **including suspended/buried** cards
  (mastery reflects knowledge, not scheduling state). New/unreviewed cards count here only.
- **Tag matching = hierarchical:** a requested topic matches that exact tag **and** its `::*`
  descendants (Anki's native tag hierarchy), so `topic::calculus` rolls up all calculus leaves while
  `topic::calculus::integral_single` returns just that leaf. One independent result row per requested
  topic, in request order; a card may contribute to several rows if the requested topics nest.
- **Response shape (enriched, additive to PRD §5.2):** `{ topic, total_cards, reviewed_count,
  mastered_count, avg_recall }`. `reviewed_count` is added so the client can distinguish "0% recall"
  from "no reviewed cards yet" and compute coverage honestly. *(Reflect this in PRD §5.2 when W1
  ships.)*
- **Implementation = single-pass SQL + Rust aggregation (Approach B):** one SQL scan computes `R` per
  card via the existing UDF; Rust aggregates per requested topic. One DB round-trip; hierarchy and
  multi-topic membership handled in Rust.
- **Engine stays generic:** the RPC matches whatever tag strings the caller passes — **no GRE
  taxonomy baked into the engine** — to keep merge difficulty low. The dashboard (W2) owns the
  17-leaf taxonomy and the 50/25/25 bucket rollups.
- **Scope boundary:** proto + Rust impl + SQL + pylib binding + tests + 50k benchmark + a lightweight
  rsdroid reachability check. The Kotlin `Collection.kt` wrapper, dashboard UI, and Android review UI
  are W2/W3.

## Global constraints

- **Read-only, hard ceiling (PRD D1, §5.3):** pure `SELECT`; **never** call `transact` /
  `transact_no_undo`; **never** return `OpChanges`. Must not copy `Collection::card_stats`'s
  `last_review_time` write-back (the one known non-pure "read").
- **No schema change:** topic data lives in `notes.tags`, not a new column (`SCHEMA_MAX_VERSION = 18`;
  a new column breaks sync round-trip — PRD §5, `rslib.md`).
- **Don't touch volatile areas:** no `scheduler/answering/` or `scheduler/fsrs/` interval math.
- **Verify symbols against the pin** (`anki@25.09.4`) before coding; re-verify if the pin bumps.
- **Engine lane (`shipping-changes`):** worktree + `git submodule update --init --recursive` + the
  **extra gate**, reviewed by a **different** agent. Docs updated + SHA bumped in the same PR.

---

## 1. Proto contract (additive to `anki/proto/anki/stats.proto`)

```proto
message MasteryRequest {
  repeated string topics = 1;   // tag strings; each matches that tag + its ::* descendants
}

message TopicMastery {
  string topic = 1;             // echoes the requested tag
  uint32 total_cards = 2;       // cards whose note carries `topic` (or a ::* descendant)
  uint32 reviewed_count = 3;    // of those, cards with an FSRS memory state (non-null R)
  uint32 mastered_count = 4;    // of reviewed, cards with R >= MASTERY_RETRIEVABILITY_THRESHOLD
  double avg_recall = 5;        // mean R over reviewed cards; 0.0 when reviewed_count == 0
}

message MasteryResponse {
  repeated TopicMastery topics = 1;   // one row per requested topic, in request order
}

service StatsService {
  // ...existing rpcs...
  rpc MasteryQuery(MasteryRequest) returns (MasteryResponse);
}
// BackendStatsService stays empty {} -> the method auto-delegates onto Collection via with_col.
```

Read-vs-write is by return type (`proto-rpc.md`): returning `MasteryResponse` (not `OpChanges`) is
what makes this a read. `(service, method)` indices are generated — never hand-edited or hard-coded.

## 2. File layout (engine lane)

| Layer | File | Action |
|---|---|---|
| Proto | `anki/proto/anki/stats.proto` | add the three messages + the `MasteryQuery` rpc on `StatsService` |
| Generated dispatch | `OUT_DIR/backend.rs`, `_backend_generated.py`, `stats_pb2.py` | regenerated by the build — **do not hand-edit** |
| Aggregation | `anki/rslib/src/stats/mastery.rs` *(new)* | `mastery_query(topics)` core + `tag_matches(card_tags, topic)` helper + `#[cfg(test)]` unit tests; declared `mod mastery;` in `stats/mod.rs` |
| RPC impl | `anki/rslib/src/stats/service.rs` | `impl StatsService for Collection { fn mastery_query(&mut self, input) -> Result<MasteryResponse> }` delegating to `mastery.rs` |
| SQL | `anki/rslib/src/storage/card/mastery.sql` *(new)* + loader fn in `storage/card/mod.rs` | single-pass select of `(tags, R)`, `include_str!`-loaded like `due_counts.sql` |
| Python binding | `anki/pylib/anki/collection.py` | `mastery_query(topics: list[str]) -> MasteryResponse` calling `self._backend.mastery_query(topics=...)` |
| Rust tests | in `stats/mastery.rs` | the ≥3 unit tests (§5) |
| Python test | `anki/pylib/tests/test_mastery.py` *(new)* | the integration test (§5) |
| Benchmark | criterion bench or a documented timing script over a 50k seeded deck | the perf gate (§5) |
| Docs | `docs/codebase/rslib.md`, `proto-rpc.md`, `pylib.md`, `INDEX.md`, `docs/STATUS.md` | mark built, bump `Last verified against:` SHA, move the INDEX row to "Built" |

## 3. Data flow (Approach B)

1. `Collection::timing_today()` → `(days_elapsed, next_day_at, now)`.
2. **One SQL pass** (`mastery.sql`) returns, for every card, its note's tags and its retrievability:

```sql
SELECT n.tags,
       extract_fsrs_retrievability(c.data, c.due, c.ivl, ?1, ?2, ?3) AS r
FROM cards c
JOIN notes n ON c.nid = n.id;
```

   `extract_fsrs_retrievability` is the registered SQLite UDF (`rslib.md`); it returns `NULL` when the
   card has no FSRS memory state. Bind `?1=days_elapsed, ?2=next_day_at, ?3=now`. **No `queue` /
   suspension filter is applied** — suspended and buried cards participate in every count (per the
   locked decision). Cards with no FSRS memory state (new cards, or a non-FSRS deck) return `NULL` `R`
   and count toward `total_cards` only.
3. **Rust aggregation:** iterate the rows once. For each card, split `tags` on whitespace into its tag
   set; for each requested `topic`, `tag_matches` is true iff some card tag `== topic` **or**
   `starts_with(topic + "::")`. On a match accumulate into that topic's counters:
   `total += 1`; if `R` is non-null `reviewed += 1`, `sum_r += R`, and if `R >= 0.9` `mastered += 1`.
4. Build one `TopicMastery` per requested topic (request order): `avg_recall = sum_r / reviewed` or
   `0.0` when `reviewed == 0`. Empty `topics` → empty `MasteryResponse`; a topic with no matching
   cards → an all-zeros row.
5. **Perf fallback (only if the 50k bench > 50 ms):** narrow the scan with a dynamic `WHERE` built
   from the requested topics' `LIKE` patterns (`tags LIKE '% topic %' OR tags LIKE '% topic::%'`),
   reusing the matching pattern from `search/sqlwriter.rs`. Prefer this over caching (PRD §5.3).

`notes.tags` is the space-delimited, space-padded canonical form (e.g. `" topic::calculus::x src::y "`);
whitespace splitting + exact/`::`-prefix tests reproduce Anki's tag semantics without a schema change.

## 4. Read-only guarantee (the hard ceiling)

- The method runs a `SELECT` only — no `transact` / `transact_no_undo`, returns `MasteryResponse`,
  never `OpChanges`. It must **not** replicate `card_stats`'s `last_review_time` write-back.
- **Invariant test (required):** capture the undo-stack depth and the due/new/review queue counts,
  call `mastery_query`, and assert all are byte-identical afterward.

## 5. Tests (spec-required)

- **Rust unit (≥3, in `mastery.rs`):**
  1. **Empty/zero** — empty collection, and a requested topic with no matching cards, both yield
     all-zeros rows (`avg_recall == 0.0`).
  2. **Aggregation correctness** — fixture with two leaves under one bucket and known `R` values
     (some new/no-memory-state); assert `total/reviewed/mastered/avg_recall` per leaf **and** that a
     bucket-level request (`topic::calculus`) rolls up the leaves (hierarchical match) vs hand-computed.
  3. **Read-only invariant** — undo-stack depth + queue counts unchanged after the call (§4).
- **Python integration (×1, `test_mastery.py`):** open a temp collection, add `topic::*`-tagged notes,
  review some (so they gain a memory state), call `col.mastery_query([...])`, assert the protobuf
  fields; assert `add_note → undo` round-trips with the mastery call interleaved.
- **Corruption:** `PRAGMA quick_check` → `ok` and the collection reopens after the call.
- **Perf:** a 50k-card seeded deck; report p50/p95; target **< 50 ms**. If exceeded, apply the §3.5
  `WHERE` narrowing / confirm an index — not caching.
- **rsdroid reachability:** rebuild the rsdroid AAR with our `anki` submodule change and confirm
  `mastery_query` is present in the generated backend binding and callable across JNI (smoke).

## 6. Merge-difficulty assessment (PRD §5.4 deliverable)

**Low.** Additive proto message + one read RPC on `StatsService` + one read `.sql` on stable insertion
points (`stats/`, `storage/card/`). No contact with `scheduler/answering/`, `scheduler/fsrs/` interval
math, undo, or the collection store. The diff is mechanical to rebase; the only generated-code churn is
re-running the build.

## 7. Acceptance

- `MasteryQuery` is callable from Python on desktop and returns correct
  `{ total_cards, reviewed_count, mastered_count, avg_recall }` for hierarchical topic requests.
- All Rust unit tests + the Python integration test pass; `quick_check` is `ok`; undo round-trips.
- The 50k benchmark is under 50 ms (or the documented `WHERE`/index mitigation is applied and re-measured).
- The RPC is reachable in the rebuilt rsdroid AAR.
- `rslib.md` / `proto-rpc.md` / `pylib.md` / `INDEX.md` / `STATUS.md` updated (SHA bumped); the change
  ships engine-lane with a different-agent extra-gate review.

## 8. Out of scope (other Wednesday sub-specs)

- **W2:** desktop dashboard — memory score as a range + coverage map (consumes this RPC).
- **W3:** Android — Kotlin `Collection.kt` mastery binding + a real review session on the shared engine.
- **W4:** sync foundation — `anki-sync-server` + the conflict-rule smoke test.
- Desktop installer packaging; the Performance/Readiness models (Thursday); interleaving (Thursday).
