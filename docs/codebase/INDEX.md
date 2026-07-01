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
| Our app additions — 3-score dashboard + coverage map (W2) | `docs/codebase/qt.md` (§ dashboard) | `anki/qt/aqt/gre/` (`__init__.py`, `taxonomy.json`, `dashboard_data.py`), `anki/qt/aqt/gre_dashboard.py`, `anki/ts/routes/gre-dashboard/` (`+page.svelte`, `MemoryPanel.svelte`, `CoverageMap.svelte`, `ScoreSlot.svelte`), `anki/qt/aqt/mediasrv.py` (`greDashboardData` endpoint + `is_sveltekit_page`), `anki/qt/aqt/main.py` (Tools-menu hook), `anki/qt/aqt/webview.py` (`AnkiWebViewKind.GRE_DASHBOARD`) | `f15cubing/anki@d8408db` |
| Android (rsdroid) | `docs/codebase/rsdroid.md` | `Anki-Android/libanki/`, `Anki-Android/AnkiDroid/`, external `rsdroid` AAR | `Anki-Android@v2.24.0` (`ebcf8e0`); backend `0.1.64-anki25.09.2` |
| Our app additions — Mastery Query (read-only RPC, W1) | `docs/codebase/rslib.md` (§ Mastery Query) | `anki/proto/anki/stats.proto`, `anki/rslib/src/stats/mastery.rs`, `anki/rslib/src/storage/card/mod.rs`, `anki/rslib/src/stats/service.rs`, `anki/pylib/anki/collection.py` | `f15cubing/anki@352135e` |
| AI gold-set (eval) | `eval/goldset/goldset.md` | `eval/goldset/` | `6941192` |
| Study-deck + tagging pipeline | `pipeline/pipeline.md` | `pipeline/` | `6941192` |

## Planned areas (designed in the PRD, not built yet)

Create a co-located/module doc from `.cursor/skills/codebase-docs/module-doc-template.md` as part of
the PR that first builds each of these.

| Area | Will live in | Design reference |
|---|---|---|
| Our app additions — interleaving toggle | `anki/ts/routes/`, `anki/qt/aqt/` | PRD §8; `qt.md` |
| Our app additions — MCQ study surface (Performance) | new note type + card template (collection data model); review templates in `anki/ts/`, `anki/qt/aqt/` | PRD §8a/§12 — content/data-model change, **not** a second engine change; reviews via the same FSRS loop |
| Our app additions — timed practice mode (exam-pressure simulator, mastery-gated) | `anki/ts/routes/`, `anki/qt/aqt/` | PRD §8/§8a — sequenced last, after interleaving + ordering algorithm |
| Scoring models — memory / performance / readiness | Python sidecar (desktop-authoritative), location TBD | PRD §7, §9 (Step 1–3) |
| Sync conflict rules (revlog union + scheduling LWW + device-UUID tie-break) | builds on `anki/rslib/src/sync/` | PRD §10 / D3; `architecture.md` Diagram 6 |
| AI card pipeline (RAG + provenance schema + CAS/SymPy verify) | desktop, AI-off-able, location TBD | PRD §9 |

---

Last verified against: `f15cubing/anki@d8408db` (25.09.4 `d52ca66` + Mastery Query + W2 dashboard), `Anki-Android@v2.24.0` (`ebcf8e0`)
