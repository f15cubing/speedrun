# Anki Fork Architecture Map

> Central map for this GRE Math Subject speedrun. Read this first, then the per-area docs in
> `docs/codebase/INDEX.md`. Every path here was verified against the vendored source at the SHAs in
> the footer. See `docs/PRD.md` for *why* (product) and `docs/execution-plan.md` for *when*.

**Repo layout note.** The outer `speedrun/` folder is not yet a git repo; the two upstream forks are
vendored as sibling folders (`anki/`, `Anki-Android/`) and are slated to become submodules. Our
codebase docs live **centrally here**, not co-located inside the forks, so they don't pollute
upstream code or complicate the eventual merge/submodule wiring.

---

## Big picture

The system is **two client apps over one shared Rust engine**.

- **The engine** is Anki's `rslib` (Rust): FSRS scheduling, the due-card queue, SQLite storage,
  collection sync, and undo/transaction management. Every capability is exposed as a **protobuf
  RPC**. The engine is the single source of truth for card state; clients never reimplement
  scheduling.
- **The desktop app** (`anki/`) is Qt + Python (`aqt`). Python reaches the engine through `pylib`
  (the `anki` package) and the `rsbridge` PyO3 native module: a method call serialises a protobuf
  request, crosses into Rust, and parses the protobuf response.
- **The Android app** (`Anki-Android/`) is AnkiDroid (Kotlin). Its `libanki` module reaches the
  **same `rslib`** through the external `rsdroid` AAR over JNI — again as protobuf in/out.
- **Sync** is how the two runtimes reconcile: each app embeds its own compiled copy of `rslib` and
  they exchange data through a self-hosted `anki-sync-server` (revlog unioned, scheduling
  last-writer-wins — see Diagram 6).

Our project adds exactly one engine change — a **read-only Mastery Query RPC** (PRD §5) — plus
score/AI/UX layers that sit *above* the engine so they can be switched off without touching the
review loop. The `topic::<bucket>::<leaf>` **tag taxonomy** (PRD §6, Appendix A) is the keystone:
one tag tree feeds the mastery query, the coverage map, the readiness gate, and interleaving.

### Diagram 1 — System / container view

```mermaid
flowchart TB
    subgraph Desktop["DESKTOP app — anki/"]
        QtUI["Qt UI - aqt (Python)<br/>review loop · 3-score dashboard<br/>coverage map · interleaving toggle"]
        Pylib["pylib — anki.Collection facade"]
        Rsbridge["rsbridge (PyO3 native module)"]
        QtUI --> Pylib --> Rsbridge
    end
    subgraph Android["ANDROID app — Anki-Android/"]
        Kotlin["AnkiDroid UI (Kotlin)<br/>Reviewer · 3 scores + ranges · give-up rule"]
        LibAnki["libanki — Collection wrapper (Kotlin)"]
        Rsdroid["rsdroid AAR (JNI)"]
        Kotlin --> LibAnki --> Rsdroid
    end
    subgraph Engine["SHARED ENGINE — anki/rslib (Rust), embedded in BOTH apps"]
        Backend["Backend + generated service dispatch"]
        Sched["FSRS · scheduler · due queue"]
        Store["storage (SQLite collection)"]
        SyncC["sync client"]
        Mastery["NEW · Mastery Query RPC (read-only)"]
        Backend --> Sched
        Backend --> Mastery
        Backend --> Store
        Backend --> SyncC
        Sched --> Store
        Mastery --> Store
    end
    Rsbridge -->|"protobuf bytes"| Backend
    Rsdroid -->|"protobuf over JNI"| Backend
    SyncC <-->|"revlog union + scheduling LWW"| SyncServer["anki-sync-server (self-hosted)"]
```

*Each app embeds its own build of `rslib` (desktop via `rsbridge`, Android via `rsdroid`); the single
"engine" box represents that shared codebase. The two running instances reconcile through the sync
server.*

---

## Areas

| Area | Code path(s) | Doc | Verified at |
|---|---|---|---|
| Rust engine | `anki/rslib/` | `docs/codebase/rslib.md` | `anki@25.09.4` (`d52ca66`) |
| Protobuf / RPC boundary | `anki/proto/`, `anki/rslib/build.rs`, `anki/rslib/rust_interface.rs`, `anki/rslib/proto_gen/` | `docs/codebase/proto-rpc.md` | `anki@25.09.4` (`d52ca66`) |
| Python bindings / FFI | `anki/pylib/` (`rsbridge/`, `anki/_backend.py`, `anki/collection.py`) | `docs/codebase/pylib.md` | `anki@25.09.4` (`d52ca66`) |
| Qt desktop UI | `anki/qt/` (`aqt/`), `anki/ts/` | `docs/codebase/qt.md` | `anki@25.09.4` (`d52ca66`) |
| Android (rsdroid) | `Anki-Android/libanki/`, `Anki-Android/AnkiDroid/`, external `rsdroid` AAR | `docs/codebase/rsdroid.md` | `Anki-Android@v2.24.0` (`ebcf8e0`); backend `0.1.64-anki25.09.2` |
| Our app additions (mastery query, dashboard, interleaving) | *(not built yet)* | planned — see PRD §5/§7/§8 | n/a |
| Scoring models (memory / performance / readiness) | *(not built yet — Python sidecar)* | planned — see PRD §7 | n/a |
| Sync conflict rules | builds on `anki/rslib/src/sync/` | planned — see PRD §10 / D3 | n/a |
| AI card pipeline | *(not built yet)* | planned — see PRD §9 | n/a |

### Diagram 2 — `rslib` engine module map

Where the engine's pieces live and where the new Mastery Query attaches (highlighted).

```mermaid
flowchart TB
    Proto["proto/anki/*.proto<br/>RPC contract (paired Service / BackendService)"]
    Gen["build.rs → rust_interface.rs<br/>generates traits + run_service_method dispatch"]
    Proto --> Gen
    subgraph rslib["anki/rslib/src"]
        Services["services.rs<br/>generated *Service / Backend*Service traits"]
        BackendMod["backend/<br/>Backend holds Mutex&lt;Option&lt;Collection&gt;&gt; · with_col()"]
        SchedM["scheduler/<br/>fsrs · queue/builder · answering · states"]
        StorageM["storage/<br/>sqlite.rs · card/ · note/ · revlog/ · tag/ · schema*.sql"]
        SyncM["sync/<br/>collection · media · http_client/server"]
        UndoM["undo/ + ops.rs + collection/transact.rs<br/>Op · OpChanges · transact()"]
        StatsM["stats/<br/>read RPCs (graphs, card_stats)"]
    end
    Gen --> Services
    BackendMod --> Services
    Services --> SchedM
    Services --> StorageM
    Services --> StatsM
    Services --> SyncM
    SchedM --> StorageM
    StatsM --> StorageM
    SchedM --> UndoM
    NewProto["NEW · MasteryQuery rpc<br/>in proto/anki/stats.proto"]:::new
    NewImpl["NEW · impl StatsService for Collection<br/>in rslib/src/stats/service.rs"]:::new
    NewSQL["NEW · grouped aggregate<br/>in rslib/src/storage/card/*.sql"]:::new
    NewProto -.-> Proto
    NewImpl -.-> StatsM
    NewSQL -.-> StorageM
    classDef new fill:#fde68a,stroke:#b45309,color:#111;
```

### Diagram 3 — RPC + FFI boundary (both clients converge on the same engine)

```mermaid
flowchart LR
    subgraph DesktopPath["DESKTOP call path"]
        direction TB
        A1["Collection method<br/>pylib/anki/collection.py"] --> A2["_backend_generated.py<br/>req.SerializeToString()"]
        A2 --> A3["_backend.py<br/>_run_command(service, method, bytes)"]
        A3 --> A4["rsbridge (PyO3)<br/>Backend.command()"]
    end
    subgraph AndroidPath["ANDROID call path"]
        direction TB
        B1["ViewModel / Fragment<br/>CollectionManager.withCol { }"] --> B2["libanki Collection.kt<br/>col.backend.someMethod(req)"]
        B2 --> B3["rsdroid AAR<br/>net.ankiweb.rsdroid.Backend"]
    end
    A4 -->|"protobuf bytes"| C["rslib Backend.run_service_method(service, method, input)"]
    B3 -->|"protobuf over JNI"| C
    C --> D["service trait impl<br/>rslib/src/**/service.rs"]
    D --> E["storage / scheduler"]
    E --> F["SQLite collection (collection.anki2)"]
```

### Diagram 4 — Mastery Query data flow (the read-only Rust change)

```mermaid
flowchart TB
    Topics["request: topics = [topic::calculus::*, ...]"] --> RPC["MasteryQuery RPC<br/>impl in rslib/src/stats/service.rs"]
    RPC --> SQL["grouped SQL aggregate<br/>rslib/src/storage/card/*.sql"]
    SQL --> Join["cards JOIN notes ON cards.nid = notes.id<br/>filter notes.tags ~ topic::*<br/>AVG(extract_fsrs_retrievability(...))<br/>GROUP BY leaf topic"]
    Join --> Resp["MasteryResponse<br/>repeated TopicMastery { topic, mastered_count, avg_recall, total_cards }"]
    Resp --> Dash["desktop dashboard + Android scores"]
    Resp --> Perf["Performance model: per-topic mastery feature"]
    RPC --- Inv["INVARIANT: read-only<br/>never returns OpChanges · never calls transact()"]:::inv
    classDef inv fill:#fee2e2,stroke:#b91c1c,color:#111;
```

### Diagram 5 — Three-score pipeline + give-up gate (planned, PRD §7)

```mermaid
flowchart TB
    Rev["graded reviews (revlog)"] --> Mem["MEMORY<br/>FSRS-6 retrievability R<br/>aggregate-calibrated (not personalized)"]
    Mastery["per-topic mastery<br/>(Mastery Query RPC)"] --> Perf
    Diff["imported item difficulty (firewalled)"] --> Perf
    Timing["response timing"] --> Perf
    Mem --> Perf["PERFORMANCE<br/>logistic regression + Platt scaling<br/>P(correct on unseen exam item)"]
    Perf --> Read["READINESS<br/>raw-correct → ETS percentile anchors → 200–990<br/>conformal interval + Bayesian cross-check"]
    Cov["coverage map<br/>(% leaf topics studied)"] --> Gate
    Read --> Gate{"give-up gate (ALL required)<br/>≥200 graded reviews AND<br/>≥50% leaf coverage AND<br/>interval width &lt; threshold"}
    Gate -->|"pass"| Panel["Readiness RANGE + evidence panel<br/>estimate · range · %coverage · confidence<br/>last-updated · reasons · next best step"]
    Gate -->|"fail"| Abstain["'Insufficient evidence to score'<br/>+ coverage map + next best topic"]
```

*The three scores are **never blended** — each is shown separately, always with a range.*

### Diagram 6 — Sync conflict resolution (planned, PRD §10 / D3; mirrors Anki's model)

```mermaid
flowchart TB
    Start["two devices sync via anki-sync-server"] --> Meta{"structural / schema<br/>divergence?"}
    Meta -->|"yes"| Full["forced one-way FULL sync<br/>losing side's structural changes discarded"]
    Meta -->|"no"| Normal["normal chunked sync"]
    Normal --> Rev["revlog entries → UNIONED<br/>PK = epoch-ms, distinct per device<br/>both reviews survive"]
    Normal --> Sched["card scheduling state → LAST-WRITER-WINS<br/>due / ivl / ease / queue / reps / lapses<br/>by most recent answer"]
    Sched --> Tie{"same mtime tie?"}
    Tie -->|"yes"| TieBreak["lexicographically lower device-UUID wins<br/>(deterministic → reproducible demo)"]
    Tie -->|"no"| Done["most recent answer wins"]
    Rev --> NoLoss["no review lost or double-counted"]
    TieBreak --> Done
```

---

## Cross-cutting concerns

### Build & protobuf/RPC codegen
The protobuf files in `anki/proto/anki/*.proto` are the **contract**. The build compiles them to a
descriptor set, then generates: Rust message types (prost) + the service traits and dispatch
(`anki/rslib/build.rs` → `anki/rslib/rust_interface.rs` → `OUT_DIR/backend.rs`, included by
`anki/rslib/src/services.rs`); the Python layer (`_backend_generated.py` + `*_pb2.py`); and the
TypeScript layer for the web UI. **You never hand-edit generated code** — change the `.proto`, then
implement the trait method in Rust and add a thin client wrapper. Full detail: `proto-rpc.md`.

### FFI boundaries
Two boundaries cross into the same Rust engine, both carrying protobuf bytes:
- **Desktop:** Python → `rsbridge` (PyO3) → Rust (`Backend.command(service, method, bytes)`). See `pylib.md`.
- **Android:** Kotlin → `rsdroid` AAR (JNI) → Rust (`net.ankiweb.rsdroid.Backend`). See `rsdroid.md`.

Our Mastery Query must reach **both**: implementing it in `rslib` gives desktop access immediately,
but Android additionally needs the `rsdroid` AAR rebuilt against an `rslib` that contains the change
(and the version bumped in `Anki-Android/gradle/libs.versions.toml`). **Version skew to reconcile:**
desktop is pinned to `anki@25.09.4`, AnkiDroid's backend is `0.1.64-anki25.09.2`.

### Undo / transaction model (a hard ceiling)
Mutations go through `Collection::transact(op, ...)` (`anki/rslib/src/collection/transact.rs`), which
opens an undoable operation and returns an `OpChanges` describing what changed; clients use that to
refresh the UI. **Read RPCs must NOT return `OpChanges` and must NOT call `transact`.** This is the
structural guarantee that the Mastery Query cannot corrupt the collection or break undo (PRD §5.3).
Encode it as a test: undo stack + study-queue counts byte-for-byte unchanged after the call.

### The topic-tag taxonomy (data keystone)
Topic metadata lives in **Anki tags** (`notes.tags`), not a new schema column — a new column would
bump `SCHEMA_MAX_VERSION` (currently `18`, in `anki/rslib/src/storage/upgrades/mod.rs`) and break
sync round-trips. Hierarchical `topic::<bucket>::<leaf>` tags are the shared substrate for the
mastery query, coverage map, readiness gate, and interleaving (PRD §6, Appendix A).

### Sync
Anki's decade-tested sync (`anki/rslib/src/sync/`) unions the revlog and chunks card/note/deck
changes; structural divergence forces a one-way full sync. Our conflict policy (Diagram 6) layers a
deterministic device-UUID tie-break on top so the conflict demo is reproducible. The test harness is
the built-in Rust `anki-sync-server` (`anki/rslib/sync/main.rs`), pinned to our release tag.

---

Last verified against: `anki@25.09.4` (`d52ca66`), `Anki-Android@v2.24.0` (`ebcf8e0`), rsdroid backend `0.1.64-anki25.09.2`
