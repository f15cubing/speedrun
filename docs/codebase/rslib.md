# Rust engine — `rslib`

> Doc for `anki/rslib/`. **Read this before changing the engine** — it carries invariants the code
> alone won't tell you (read RPCs must never return `OpChanges`). Central map: `architecture.md`.
> RPC mechanics: `proto-rpc.md`. This is where our one engine change (Mastery Query, PRD §5) lives.

## Purpose

`rslib` is Anki's collection engine: FSRS scheduling, the due-card queue, SQLite storage, collection
+ media sync, and undo/transaction management. It is the single source of truth for card state and
is embedded into both the desktop app (via `rsbridge`) and Android (via `rsdroid`). Every capability
is exposed as a protobuf RPC, so all clients share the same behaviour.

## Public interface

The engine's public surface is the set of **generated service traits** (one pair per domain), not
free functions. The proto contract lives in `anki/proto/anki/*.proto`; `proto-rpc.md` covers codegen.

- **Dispatch entry:** `Backend::run_service_method(service, method, input: &[u8]) -> Vec<u8>` and
  `Collection::run_service_method(...)` — generated into `OUT_DIR/backend.rs`, included by
  `anki/rslib/src/services.rs`. Clients call by numeric `(service, method)` index.
- **Backend handle:** `anki/rslib/src/backend/mod.rs` — `Backend` holds `Mutex<Option<Collection>>`;
  `with_col(|col| ...)` runs a closure against the open collection. Backend-only methods (e.g.
  open/close collection, sync) take `&Backend`; collection methods take `&mut Collection`.
- **Service impls** live at `anki/rslib/src/<domain>/service.rs` (e.g. `stats/service.rs`,
  `search/service/mod.rs`, `scheduler/service/mod.rs`, `notes/service.rs`, `tags/service.rs`,
  `cards`/`card/service.rs`, `decks/service.rs`, `collection/service.rs`). Backend-only impls live
  under `anki/rslib/src/backend/` (e.g. `backend/sync.rs`, `backend/collection.rs`).

### Subsystem map (where things are)

| Subsystem | Path | Notes |
|---|---|---|
| Service dispatch (generated) | `rslib/src/services.rs`, `rslib/rust_interface.rs`, `rslib/build.rs` | traits + `run_service_method` |
| Backend handle | `rslib/src/backend/` (`mod.rs`, `collection.rs`, `sync.rs`, `dbproxy.rs`, `ops.rs`) | `with_col`, DB proxy, `OpChanges` proto conversion |
| Undo / transaction | `rslib/src/ops.rs`, `rslib/src/undo/` (`mod.rs`, `changes.rs`), `rslib/src/collection/transact.rs` | `Op`, `OpChanges`, `OpOutput<T>`, `transact()` |
| Storage (SQLite) | `rslib/src/storage/` (`sqlite.rs`, `card/`, `note/`, `revlog/`, `tag/`, `graves/`, `schema11.sql`, `upgrades/`) | one `.sql` file per query, `include_str!`-loaded |
| FSRS | `rslib/src/scheduler/fsrs/` (`memory_state.rs`, `params.rs`, `retention.rs`, `rescheduler.rs`, `simulator.rs`) | memory state, retrievability `R` |
| Queue builder | `rslib/src/scheduler/queue/` (`mod.rs`, `builder/`) | `build_queues()`, `QueueBuilder` |
| Sync (library) | `rslib/src/sync/` (`collection/`, `media/`, `http_client/`, `http_server/`, `version.rs`) | normal vs full sync |
| Sync (binary) | `rslib/sync/main.rs` | self-hosted `anki-sync-server` |
| Stats (read RPCs) | `rslib/src/stats/` (`service.rs`, `card.rs`, `graphs/`) | template for read-only methods |

### Retrievability ("R") helpers — reuse these for the Mastery Query
- **SQLite UDFs** registered in `rslib/src/storage/sqlite.rs`:
  - `extract_fsrs_retrievability(card.data, due, ivl, days_elapsed, next_day_at, now) -> float|null`
  - `extract_fsrs_relative_retrievability(card.data, due, days_elapsed, ivl, next_day_at, now) -> float|null`
  - The timing args (`days_elapsed`, `next_day_at`, `now`) come from `Collection::timing_today()`.
- Rust-side: `CardData::memory_state()` (`rslib/src/storage/card/data.rs`);
  `Collection::compute_memory_state(card_id)` (`rslib/src/scheduler/fsrs/memory_state.rs`).
- Ordering clauses: `build_retrievability_clauses(...)` (`rslib/src/storage/card/mod.rs`).

### SQL aggregate pattern (cards ⋈ notes ⋈ tags)
- Join key: `cards.nid = notes.id`. Note **tags live in `notes.tags`** (a text column), not FK-linked
  to the `tags` registry table. Tag filtering in search is emitted by `rslib/src/search/sqlwriter.rs`.
- Existing aggregate example: `rslib/src/storage/deck/due_counts.sql` — `SELECT did, sum(...),
  COUNT(1) FROM cards GROUP BY did`. New aggregates follow the same one-`.sql`-file pattern under
  `rslib/src/storage/card/` and are loaded with `include_str!` in `storage/card/mod.rs`.

## Mastery Query (PRD §5 — implemented, W1)

A read-only RPC returning, per requested topic tag, `{ topic, total_cards, reviewed_count,
mastered_count, avg_recall }`. Implemented on **Collection** (`StatsService`); `BackendStatsService`
stays empty so the method auto-delegates to `Backend` (generated dispatch confirmed in
`OUT_DIR/backend.rs`). "Mastered" = the card has an FSRS memory state **and** retrievability
`R >= MASTERY_RETRIEVABILITY_THRESHOLD` (0.9); `reviewed_count` = cards with a memory state;
`total_cards` includes suspended/buried/new; tag match is hierarchical (`topic` **and** its `::*`
descendants), one row per requested topic in request order.

| Layer | File | Status |
|---|---|---|
| Proto messages + rpc | `anki/proto/anki/stats.proto` | `MasteryRequest { repeated string topics }`, `TopicMastery { topic, total_cards, reviewed_count, mastered_count, avg_recall }`, `MasteryResponse { repeated TopicMastery }`, `rpc MasteryQuery(...)` on `StatsService` |
| Aggregation + Collection method | `anki/rslib/src/stats/mastery.rs` (new; `mod mastery;` in `stats/mod.rs`) | pure `aggregate_mastery(rows, topics, threshold)` fold + `tag_matches` helper + `Collection::mastery_for_topics` |
| RPC impl | `anki/rslib/src/stats/service.rs` | `fn mastery_query(&mut self, MasteryRequest) -> Result<MasteryResponse>` delegating to `mastery_for_topics` |
| SQL (single pass) | `anki/rslib/src/storage/card/mod.rs` → `all_card_tags_and_retrievability(...)` | one `SELECT n.tags, extract_fsrs_retrievability(...) FROM cards c JOIN notes n`; **inline `format!`** (not a `.sql` file) because the timing ints are interpolated, mirroring `search/sqlwriter.rs`; new cards (`type = 0`) short-circuit to `NULL` to skip the UDF (avoids a debug-only overflow) |
| Python binding | `anki/pylib/anki/collection.py` → `Collection.mastery_query(topics)` | see `pylib.md` |
| Android binding | `Anki-Android/libanki/.../Collection.kt` + rebuilt rsdroid AAR | **W3** — codegen reachability confirmed (RPC present in the proto descriptor + generated `backend.rs`/`_backend_generated.py`/`backend.ts`); the live AAR rebuild + on-device call are deferred to W3 (`rsdroid.md`) |

## Dependencies

- **Inbound:** `rsbridge` (desktop) and `rsdroid` (Android) call `Backend::run_service_method`. The
  proto codegen (`anki/rslib/proto_gen/`, `build.rs`) generates the trait/dispatch layer.
- **Outbound:** `prost`/`prost-reflect` (protobuf), `rusqlite` (SQLite), `fsrs`/`fsrs-rs` (scheduling
  math), `reqwest`/`axum` (sync HTTP). FSRS retrievability math is engine-internal and **not**
  exposed to Python — a reason "avg recall" must be computed here, not in a client (PRD §5.4).

## Gotchas & invariants

- **Read RPCs must NOT return `OpChanges` and must NOT call `transact()` / `transact_no_undo()`.**
  Mutations return `OpChanges*` and go through `Collection::transact(Op, |col| ...)`
  (`rslib/src/collection/transact.rs`). This is the structural guarantee the Mastery Query can't
  corrupt the collection or clear undo. Test it: undo stack + study-queue counts unchanged after the
  call (PRD §5.3).
- **One known non-pure "read":** `Collection::card_stats` (`rslib/src/stats/card.rs`) may call
  `storage.update_card` when `last_review_time` is missing. Don't copy that pattern into a new read.
- **No schema column for topics.** `SCHEMA_MAX_VERSION = 18` (`rslib/src/storage/upgrades/mod.rs`);
  adding a column bumps it and breaks sync round-trip. Use tags (`notes.tags`) instead.
- **Avoid the volatile areas.** Don't touch `scheduler/answering/` or `scheduler/fsrs/` interval
  math for our change — those are version-sensitive and risk undo/correctness (PRD D1). The mastery
  query lands on stable insertion points (additive proto + read service + read SQL).
- **Verify symbols against the pin.** Many symbols cited in research were `[inferred]`; this doc is
  verified against `anki@25.09.4` — re-verify if the pin changes.
- **Two version numbers, don't confuse them:** DB `SCHEMA_MAX_VERSION = 18`
  (`storage/upgrades/mod.rs`) vs sync wire `SYNC_VERSION_MAX = 11` (`rslib/src/sync/version.rs`).

## Related tests

- Shared test helpers: `anki/rslib/src/tests.rs` (`open_test_collection()`, note adders, fixtures);
  registered via `pub(crate) mod tests;` in `rslib/src/lib.rs`.
- Per-module `#[cfg(test)]`: e.g. `storage/card/mod.rs`, `storage/sqlite.rs`,
  `scheduler/queue/builder/mod.rs`, `undo/mod.rs`, `search/sqlwriter.rs`, `stats/card.rs`.
- Sync integration: `rslib/src/sync/collection/tests.rs`, `rslib/src/sync/media/tests.rs`.
- There is **no** top-level `rslib/tests/` dir — integration tests live inside modules.
- Mastery Query tests (implemented): `stats/mastery.rs` unit tests — `empty_and_no_match_yield_zeros`,
  `aggregation_and_hierarchy`, and `mastery_query_is_read_only` (asserts unchanged undo `last_step` +
  card count + `quick_check_corrupt() == false`), plus an `#[ignore]`d `mastery_query_50k_perf`
  (p50 < 50 ms; measured ~19 ms on a 50k deck). Python: `pylib/tests/test_mastery.py` (hierarchy +
  `add_note → mastery_query → undo` round-trip).

---
Last verified against: `f15cubing/anki@3f5b2b2` (25.09.4 `d52ca66` + Mastery Query)
