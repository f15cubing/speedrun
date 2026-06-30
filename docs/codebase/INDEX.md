# Codebase Docs Index

> Map of area → doc file → code paths. **Start here** to find the docs relevant to the files you're
> about to change, then read that doc before editing (see `.cursor/skills/codebase-docs/SKILL.md`).
> The central map with diagrams is `docs/codebase/architecture.md`.

## Built areas (verified against vendored source)

| Area | Doc file | Code paths | Last verified |
|---|---|---|---|
| Rust engine | `docs/codebase/rslib.md` | `anki/rslib/` | `anki@25.09.4` (`d52ca66`) |
| Protobuf / RPC boundary | `docs/codebase/proto-rpc.md` | `anki/proto/`, `anki/rslib/build.rs`, `anki/rslib/rust_interface.rs`, `anki/rslib/proto_gen/` | `anki@25.09.4` (`d52ca66`) |
| Python bindings / FFI | `docs/codebase/pylib.md` | `anki/pylib/` (`rsbridge/`, `anki/_backend.py`, `anki/collection.py`) | `anki@25.09.4` (`d52ca66`) |
| Qt desktop UI | `docs/codebase/qt.md` | `anki/qt/` (`aqt/`), `anki/ts/` | `anki@25.09.4` (`d52ca66`) |
| Android (rsdroid) | `docs/codebase/rsdroid.md` | `Anki-Android/libanki/`, `Anki-Android/AnkiDroid/`, external `rsdroid` AAR | `Anki-Android@v2.24.0` (`ebcf8e0`); backend `0.1.64-anki25.09.2` |
| AI gold-set (eval) | `eval/goldset/goldset.md` | `eval/goldset/` | `6941192` |
| Study-deck + tagging pipeline | `pipeline/pipeline.md` | `pipeline/` | `6941192` |

## Planned areas (designed in the PRD, not built yet)

Create a co-located/module doc from `.cursor/skills/codebase-docs/module-doc-template.md` as part of
the PR that first builds each of these.

| Area | Will live in | Design reference |
|---|---|---|
| Our app additions — Mastery Query Rust change | `anki/proto/anki/stats.proto`, `anki/rslib/src/stats/service.rs`, `anki/rslib/src/storage/card/` | PRD §5; `rslib.md` + `proto-rpc.md` insertion-point sections |
| Our app additions — 3-score dashboard + coverage map + interleaving toggle | `anki/ts/routes/`, `anki/qt/aqt/` | PRD §7/§8; `qt.md` "dashboard attachment" section |
| Scoring models — memory / performance / readiness | Python sidecar (desktop-authoritative), location TBD | PRD §7, §9 (Step 1–3) |
| Sync conflict rules (revlog union + scheduling LWW + device-UUID tie-break) | builds on `anki/rslib/src/sync/` | PRD §10 / D3; `architecture.md` Diagram 6 |
| AI card pipeline (RAG + provenance schema + CAS/SymPy verify) | desktop, AI-off-able, location TBD | PRD §9 |

---

Last verified against: `anki@25.09.4` (`d52ca66`), `Anki-Android@v2.24.0` (`ebcf8e0`)
