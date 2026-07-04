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
| Our app additions — 3-score dashboard + coverage map (W2) + desktop scoring adapter (Task 6) | `docs/codebase/qt.md` (§ dashboard, § scoring adapter) | `anki/qt/aqt/gre/` (`__init__.py`, `taxonomy.json`, `dashboard_data.py`, `scoring_adapter.py`), `anki/qt/aqt/gre_dashboard.py`, `anki/ts/routes/gre-dashboard/` (`+page.svelte`, `MemoryPanel.svelte`, `CoverageMap.svelte`, `ScoreSlot.svelte`), `anki/qt/aqt/mediasrv.py` (`greDashboardData` endpoint + `is_sveltekit_page`), `anki/qt/aqt/main.py` (Tools-menu hook), `anki/qt/aqt/webview.py` (`AnkiWebViewKind.GRE_DASHBOARD`), `anki/qt/aqt/gre/scoring_adapter.py` (writes synced `gre_scorecard`) | `f15cubing/anki@a7e8992` |
| Android (rsdroid) | `docs/codebase/rsdroid.md` | `Anki-Android/libanki/`, `Anki-Android/AnkiDroid/`, locally-built `Anki-Android-Backend/` (rsdroid) AAR | `f15cubing/Anki-Android@c6d0250` (fork of `v2.24.0`); rsdroid `f15cubing/Anki-Android-Backend@3dc30c2` (bundles `anki@ea3acae`) |
| Our app additions — Mastery Query (read-only RPC, W1) | `docs/codebase/rslib.md` (§ Mastery Query) | `anki/proto/anki/stats.proto`, `anki/rslib/src/stats/mastery.rs`, `anki/rslib/src/storage/card/mod.rs`, `anki/rslib/src/stats/service.rs`, `anki/pylib/anki/collection.py` | `f15cubing/anki@352135e` |
| Our app additions — Mastery Query on Android (read-only binding, W3) | `docs/codebase/rsdroid.md` (§ Mastery Query on Android) | `Anki-Android/libanki/src/main/java/com/ichi2/anki/libanki/stats/BackendStats.kt` (`Collection.masteryQuery`), `Anki-Android/libanki/src/test/.../stats/MasteryQueryTest.kt`; backend rebuilt from `Anki-Android-Backend/` bundling `anki@ea3acae` | `f15cubing/Anki-Android@c6d0250`, `f15cubing/Anki-Android-Backend@3dc30c2` |
| Sync foundation (self-hosted server + conflict rule, W4) | `docs/codebase/sync.md` | `sync/run-sync-server.sh`, `sync/roundtrip_smoke.py`, root `Makefile` (`sync-server`/`sync-smoke`); server engine `anki@ea3acae` | `f15cubing/anki@ea3acae` |
| Block C robustness proofs — crash-safety (7g) + two-way sync (7b) | `robustness/README.md`; `docs/codebase/sync.md` (§ Block C proofs) | `robustness/crash_test_7g.py`, `sync/two_way_sync_7b.py`, root `Makefile` (`crash-7g`/`sync-7b`/`sync-server-7b`); evidence `docs/evidence/robustness/` | `f15cubing/anki@ea3acae` |
| Deck auto-incorporation (bundled first-run import, both apps) — now bundles the **interactive MCQ** deck (`GRE_DECK_VERSION=2026-07-03b`); fresh installs get it, existing-install template-refresh is a documented limitation | `docs/superpowers/specs/2026-07-02-deck-auto-incorporation-design.md` | desktop `anki/qt/aqt/gre/deck_autoimport.py` + `data/gre-study-deck.apkg` (hook in `qt/aqt/main.py`); AnkiDroid `GreDeckAutoImport.kt` + `assets/gre-study-deck.apkg` (DeckPicker hook); root `Makefile` (`deck-asset`/`deck-asset-check`) | `f15cubing/anki@a7e8992`, `f15cubing/Anki-Android@c6d0250` |
| AI gold-set (eval) | `eval/goldset/goldset.md` | `eval/goldset/` | `6941192` |
| Authored eval bank (P0 held-out + P3 paraphrase; LaTeX-migrated) | `eval/bank/eval_bank.md` | `eval/bank/` (`loader.py`, `generate_eval.py`, `items.yaml`) | `agent/pipeline-latex-math` |
| LaTeX math rendering (study deck + eval bank + Exam Mode webview) | `docs/superpowers/specs/2026-07-02-latex-math-rendering-design.md`; `pipeline/pipeline.md`, `eval/bank/eval_bank.md` | `pipeline/mathfmt.py` + generators (stable `uid` GUIDs, deterministic `.apkg`); `eval/bank/items.yaml`; `anki/qt/aqt/gre/exam_items.json` + `data/gre-study-deck.apkg`; `anki/ts/routes/gre-exam/` (`mathjax.ts`, `ItemView.svelte`, `Results.svelte`, `+page.svelte`); `Anki-Android/.../assets/gre-study-deck.apkg` | `f15cubing/anki@a7e8992`, `f15cubing/Anki-Android@c6d0250` |
| Scoring layer — Performance + Readiness (Thu, pure-Python package) | `scoring/scoring.md` | `scoring/` (`logistic.py`, `poisson_binomial.py`, `features.py`, `simulate.py`, `performance.py`, `readiness.py`, `calibration.py`, `scorecard.py`, `eval_cli.py`); `make score-eval`. Desktop adapter **shipped** (`anki/qt/aqt/gre/scoring_adapter.py` writes the synced `gre_scorecard`; see `qt.md` § scoring adapter); AnkiDroid read-only panel **shipped** (Task 7; `Anki-Android/.../GreScorecardFragment.kt` + `GreScorecard.kt` read the synced `gre_scorecard`; see `rsdroid.md` § score card panel). The **D2 give-up gate** ("never a bare Readiness number") has a re-runnable evidence audit — `proofs/giveup_audit.py` + `make giveup-audit` (read-only consumer of `readiness.py`; evidence in `docs/evidence/proofs/giveup_audit.json`). | `agent/thu-scoring-layer` (on `8698b1a`) |
| Study-deck + tagging pipeline (~5,400 cards: flashcards + MCQ + 57 verified conceptual; scale-up + capacity/uniqueness tests) | `pipeline/pipeline.md` | `pipeline/` (`generate_deck.py`, `distractors.py`, `generate_mcq.py`, `build_deck.py` incl. "GRE MCQ" note type, `conceptual_cards.yaml`, `coverage_report.py`) | `agent/deck-scale` |
| AI card pipeline + gold-set gate (RAG + non-nullable provenance + abstention + SymPy/NLI verify + pre-lodged gate w/ κ; AI-off / deterministic-stub-driven) | `pipeline/aicards/aicards.md` | `pipeline/aicards/` (`corpus.py`, `provenance.py`, `retriever.py`, `verify.py`, `cards.py`, `stub_model.py`, `orchestrator.py`, `goldset_gate.py`, `firewall.py`, `run_gate.py`, `sources/`); `make ai-gate` | `agent/ai-pipeline` |

## Planned areas (designed in the PRD, not built yet)

Create a co-located/module doc from `.cursor/skills/codebase-docs/module-doc-template.md` as part of
the PR that first builds each of these.

| Area | Will live in | Design reference |
|---|---|---|
| Our app additions — interleaving toggle | `anki/ts/routes/`, `anki/qt/aqt/` | PRD §8; `qt.md` |
| Our app additions — MCQ study surface (Performance) | **built** in `pipeline/` — the "GRE MCQ" note type (SymPy-templated generation + verified conceptual MCQ) now has an **interactive card template** (five tappable A–E options, instant feedback + explanation reveal + MathJax; grades on FSRS, renders in the reviewer webview on desktop + Android). See `pipeline/pipeline.md` + `docs/superpowers/specs/2026-07-03-interactive-mcq-webview-design.md`. Follow-ups (engine-lane): re-bundle the `.apkg` into both app assets + `GRE_DECK_VERSION` bump; the auto-grade reviewer hook | PRD §8a/§12 — content/data-model change, **not** a second engine change; reviews via the same FSRS loop |
| Our app additions — timed practice mode (exam-pressure simulator, mastery-gated) | `anki/ts/routes/`, `anki/qt/aqt/` | PRD §8/§8a — sequenced last, after interleaving + ordering algorithm |
| Scoring models — memory / performance / readiness | Python sidecar (desktop-authoritative), location TBD | PRD §7, §9 (Step 1–3) |
| Sync conflict rules — engine-level device-UUID tie-break (foundation shipped W4; the tie-break itself is deferred, Thursday) | builds on `anki/rslib/src/sync/` | PRD §10 / D3; `docs/codebase/sync.md`; `architecture.md` Diagram 6 |

---

Last verified against: `f15cubing/anki@a7e8992` (25.09.4 `d52ca66` + Mastery Query + W2 dashboard + Exam Mode + deck auto-import + Exam-Mode LaTeX + desktop scoring adapter + LaTeX study-deck rebundle + `gre_deck_version` 2026-07-03b + pre-uid dedup migration + interactive-MCQ deck re-bundle), `f15cubing/Anki-Android@c6d0250` (fork of `v2.24.0` `ebcf8e0`; + mastery binding + deck auto-import + LaTeX study-deck rebundle + `gre_deck_version` 2026-07-03b + pre-uid dedup migration + read-only GRE score card panel (Task 7) + interactive-MCQ deck re-bundle), `f15cubing/Anki-Android-Backend@3dc30c2` (built locally, bundles `anki@ea3acae`)
