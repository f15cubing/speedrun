# Protobuf / RPC boundary

> Doc for `anki/proto/` and the codegen that turns it into Rust traits, Python bindings, and TS.
> **Read this before adding or changing any RPC** (including the Mastery Query). Engine internals:
> `rslib.md`. Desktop binding: `pylib.md`. Android binding: `rsdroid.md`.

## Purpose

The `.proto` files are **the contract** between the Rust engine and every client. Each domain
declares two services — `FooService` (collection-scoped) and `BackendFooService` (backend handle) —
plus its request/response messages. A build step compiles these to a descriptor set and generates
the Rust dispatch layer, the Python bindings, and the TypeScript bindings. You change behaviour by
editing a `.proto` + implementing the Rust trait method; **you never hand-edit generated code.**

## Public interface

### The proto files (`anki/proto/anki/*.proto`, 23 files)

| File | Covers |
|---|---|
| `backend.proto` | messages only (no service): `BackendInit`, `BackendError` (+ error `Kind`) |
| `generic.proto` | scalar wrappers: `Empty`, `Int32`, `String`, `Bool`, `Json`, `StringList`, … |
| `collection.proto` | lifecycle, undo/redo, progress, **`OpChanges*` types**, backups |
| `cards.proto` / `notes.proto` / `notetypes.proto` / `decks.proto` / `deck_config.proto` | CRUD per domain |
| `scheduler.proto` | FSRS/v3 scheduling, queues, bury/suspend, FSRS param simulation |
| `stats.proto` | card stats, review logs, graph data — **recommended home for Mastery Query** |
| `search.proto` / `tags.proto` / `config.proto` / `media.proto` / `import_export.proto` | search, tags, config, media, import/export |
| `card_rendering.proto` / `image_occlusion.proto` / `i18n.proto` / `links.proto` | rendering & misc |
| `frontend.proto` | Qt↔TS bridge only — **not** exposed to Python `rsbridge` |
| `sync.proto` / `ankiweb.proto` / `ankihub.proto` | backend-only services |
| `ankidroid.proto` | AnkiDroid DB bridge — excluded from Python/TS codegen |

### Declaring a service (standard proto3, no custom options)

```proto
service CollectionService {
  rpc Undo(generic.Empty) returns (OpChangesAfterUndo);
  rpc MergeUndoEntries(generic.UInt32) returns (OpChanges);
  // ...
}
service BackendCollectionService {
  rpc OpenCollection(OpenCollectionRequest) returns (generic.Empty);
  // ...
}
```

There are **no custom protobuf options/attributes**. Backend-vs-collection and read-vs-write are
**conventions**, not annotations (rules documented in `anki/rslib/proto_gen/src/lib.rs`):

- RPC only in `BackendFooService` → backend-only (e.g. `OpenCollection`, all of `BackendSyncService`).
- RPC only in `FooService` → auto-delegated onto `Backend` via `with_col(|col| ...)`.
- RPC in **both** → separate trait impls allowed on `Collection` and `Backend`.
- An empty `BackendFooService {}` means "all of `FooService` delegates" (e.g. `BackendStatsService {}`).
- **Read vs write is by return type, not options:** mutations return `collection.OpChanges` /
  `OpChangesWithCount` / `OpChangesWithId`; reads return a domain message or a `generic.*` wrapper.

### Codegen pipeline

```
proto/anki/*.proto
   ├─ protoc (build/ninja_gen/src/protobuf.rs) ─► descriptor set + out/pylib/anki/*_pb2.py(+.pyi)
   └─ anki_proto (rslib/proto/build.rs, rust.rs)
         ├─ prost ─► Rust message types (OUT_DIR)
         ├─ proto_gen::get_services() ─► split Collection vs Backend services, merge delegating
         ├─ python.rs    ─► out/pylib/anki/_backend_generated.py
         ├─ typescript.rs ─► out/ts/lib/generated/backend.ts
         └─ rslib/build.rs ─► rslib/rust_interface.rs ─► OUT_DIR/backend.rs
                 (traits *Service / Backend*Service + run_service_method dispatch)
                 included by rslib/src/services.rs
```

`(service, method)` are stable **numeric indices** from descriptor order — never hard-code them;
always go through the generated client wrappers.

## Adding an RPC (e.g. the Mastery Query)

> **Status:** `rpc MasteryQuery(MasteryRequest) returns (MasteryResponse)` is **implemented** on
> `StatsService` (W1). `BackendStatsService {}` stays empty, so it auto-delegates to `Collection`
> (generated dispatch in `OUT_DIR/backend.rs`; also generated into `_backend_generated.py` and
> `backend.ts`, and present in the proto descriptor). The steps below are the general recipe.

1. Edit `anki/proto/anki/stats.proto`: add `MasteryRequest`/`MasteryResponse`/`TopicMastery`
   messages and `rpc MasteryQuery(MasteryRequest) returns (MasteryResponse);` to `StatsService`
   (leave `BackendStatsService {}` empty → auto-delegates).
2. Rebuild → regenerates Rust traits/dispatch, `_backend_generated.py`, `stats_pb2.py`, `backend.ts`.
3. Implement the trait method in `anki/rslib/src/stats/service.rs` (return the response, **not**
   `OpChanges`). See `rslib.md`.
4. Add a thin client wrapper: Python in `anki/pylib/anki/collection.py` (`pylib.md`); Kotlin in
   `Anki-Android/libanki/.../Collection.kt` after the rsdroid AAR is rebuilt (`rsdroid.md`).

## Dependencies

- **Build tooling:** `protoc` (bundled via `build/ninja_gen/src/protobuf.rs`), `prost` +
  `prost-reflect` (Rust), a mypy plugin for Python stubs. Wiring: `build/configure/src/rust.rs`
  (`rslib:proto`, `pylib:rsbridge`), `build/configure/src/pylib.rs`.
- **Consumers:** `rslib/src/services.rs` (Rust dispatch), `pylib/anki/_backend_generated.py`
  (Python), `ts/lib/generated/backend.ts` (web UI).

## Gotchas & invariants

- **Generated files are not hand-edited.** `_backend_generated.py`, `*_pb2.py`, `OUT_DIR/backend.rs`,
  `backend.ts` are all build output. `_backend_generated.py` is present only after a build (in
  `out/pylib/anki/`), not committed.
- **Pick the right service.** Put read-only collection methods on `FooService` with an empty
  `BackendFooService` so they delegate; reserve `BackendFooService`-only for methods that must run
  without an open collection (sync, open/close).
- **Mutations return `OpChanges`; reads don't.** Honour this so the Mastery Query stays read-only.
- **`db_command` uses JSON, not protobuf** — a deliberate perf exception for the high-frequency SQL
  proxy (`pylib.md`); not relevant to normal RPCs.
- **`frontend.proto` / `ankidroid.proto` are special** — filtered out of the standard Python/Rust
  trait generation.

## Related tests

- Proto contract overview: `anki/proto/README.md`.
- Behaviour is exercised through the engine tests (`rslib.md`) and the Python binding tests
  (`anki/pylib/tests/`, see `pylib.md`); there is no separate "proto" test suite.

---
Last verified against: `f15cubing/anki@3f5b2b2` (25.09.4 `d52ca66` + Mastery Query)
