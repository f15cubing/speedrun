# Python bindings / FFI — `pylib`

> Doc for `anki/pylib/`. The desktop FFI boundary: Python ↔ Rust engine. **Read before adding a
> Python binding for an engine RPC.** Engine: `rslib.md`. RPC contract/codegen: `proto-rpc.md`.
> Desktop UI that consumes this: `qt.md`.

## Purpose

`pylib` is the `anki` Python package plus the `rsbridge` native module that bridges Python to the
Rust engine. It gives the desktop app (and scripts) a Pythonic `Collection` facade while all real
work happens in `rslib`. The boundary carries **protobuf bytes**: a Python call serialises a request,
crosses into Rust via PyO3, and parses the protobuf response.

## Public interface

### `Collection` facade — `anki/pylib/anki/collection.py`
The main object desktop code uses. Domain helpers hang off it (`col.decks`, `col.tags`,
`col.sched`, `col.cards`, …, in `anki/pylib/anki/decks.py`, `tags.py`, `scheduler/`, `cards.py`).
It holds the backend as `col._backend` (private — never exposed to add-ons).

### `rsbridge` — `anki/pylib/rsbridge/`
A PyO3 `cdylib` crate exposing the `_rsbridge` module (`rsbridge/lib.rs`):

```python
# anki/pylib/anki/_rsbridge.pyi
def open_backend(data: bytes) -> Backend: ...
def buildhash() -> str: ...
def initialize_logging(log_file: str | None) -> None: ...

class Backend:
    def command(service: int, method: int, data: bytes) -> bytes: ...   # protobuf in/out
    def db_command(data: bytes) -> bytes: ...                            # JSON in/out
```

`command()` releases the GIL (`py.allow_threads`) and calls
`anki::backend::Backend::run_service_method(service, method, input)` in Rust.

### Backend wrapper layers — `anki/pylib/anki/_backend.py` (+ generated)
```
RustBackendGenerated   ← out/pylib/anki/_backend_generated.py (one method per RPC; generated)
      ▲
RustBackend            ← anki/pylib/anki/_backend.py (_run_command, error mapping, db_* , i18n)
      ▲
col._backend           ← held by Collection
```
- Generated methods come in two shapes: typed `get_card(cid) -> Card` and raw
  `get_card_raw(bytes) -> bytes`.
- `RustBackend._run_command(service, method, input)` calls `self._backend.command(...)` and maps a
  `BackendError` protobuf into the right Python exception (`anki/pylib/anki/errors.py`).
- Build-hash guard: `_rsbridge.buildhash()` must match `anki.buildinfo.buildhash`.

### Call path (typical)
```
collection.py  Collection.remove_cards_and_orphaned_notes(ids)
  → _backend.remove_cards(card_ids=...)                 # _backend_generated.py
  → RemoveCardsRequest.SerializeToString()
  → _run_command(service=CardsService, method=…, bytes) # _backend.py
  → _rsbridge.Backend.command(service, method, bytes)   # rsbridge/lib.rs (PyO3)
  → rslib Backend.run_service_method(...)               # Rust dispatch
  → impl CardsService for Collection (rslib/src/card/service.rs)
  ← OpChangesWithCount (protobuf) → ParseFromString → caller
```

## Adding a binding (e.g. Mastery Query)

> **Status:** `Collection.mastery_query(topics: Sequence[str])` is **implemented** in
> `anki/pylib/anki/collection.py` (W1). Note the codegen **unwraps the single-field
> `MasteryResponse`**, so the binding returns `Sequence[stats_pb2.TopicMastery]` directly (not a
> `MasteryResponse` with a `.topics` field). Tests: `anki/pylib/tests/test_mastery.py`.

After the proto + Rust impl exist (`proto-rpc.md`, `rslib.md`):

1. Rebuild so `_backend_generated.py` gains `mastery_query()` / `mastery_query_raw()`.
2. Add a public method on `Collection` in `anki/pylib/anki/collection.py` that calls
   `self._backend.mastery_query(topics=...)` and returns the typed response (or a small dataclass).
3. Only extend `anki/pylib/anki/_backend.py` if you need custom error handling or marshalling.
4. **Never expose `_backend` to add-ons** — wrap it in a public `Collection` method.

## Dependencies

- **Inbound:** the Qt desktop UI (`anki/qt/aqt/`) holds a `Collection` as `mw.col` (`qt.md`).
- **Outbound:** `rsbridge` links the compiled `rslib` (`_rsbridge.so`/`.pyd`); protobuf message
  classes come from generated `*_pb2.py`.
- **Build/packaging:** `anki/pylib/hatch_build.py` copies prebuilt artifacts from `out/pylib/anki/`
  (`_rsbridge.*`, `_backend_generated.py`, `*_pb2.py`) into a non-pure wheel. Build wiring:
  `build/configure/src/pylib.rs`.

## Gotchas & invariants

- **`db_command` is JSON, not protobuf** — an intentional speed exception for the high-frequency SQL
  proxy (`to_json_bytes`/`from_json_bytes` in `_backend.py`); normal RPCs use protobuf.
- **`(service, method)` indices are build-stable but not a public API** — always call generated
  wrappers, never pass raw integers.
- **`_backend_generated.py` isn't in git** — it appears under `out/pylib/anki/` after a build. If
  bindings look missing, you haven't rebuilt.
- **`anki/pylib/anki/rsbackend.py` is a deprecated re-export shim** — don't add to it.
- Mutating RPCs return `OpChanges`; the desktop UI relies on that to refresh (`qt.md`). Keep reads
  read-only on the Python side too (don't fabricate `OpChanges`).

## Related tests

- `anki/pylib/tests/` — e.g. `test_collection.py`, `test_cards.py`, `test_decks.py`,
  `test_models.py`, `test_find.py`, `test_stats.py`, `test_schedv3.py`, `test_importing.py`,
  `test_exporting.py`, `test_media.py`; shared fixtures in `anki/pylib/tests/shared.py`
  (`getEmptyCol`).
- CI: `check:pytest:pylib` (`build/configure/src/pylib.rs`).
- For the Mastery Query, PRD §5.3 wants 1 Python integration test: open a temp collection, add
  tagged notes, call the binding, assert the protobuf, and assert `add_note → undo` round-trips with
  the mastery call in between.

---
Last verified against: `f15cubing/anki@3f5b2b2` (25.09.4 `d52ca66` + Mastery Query)
