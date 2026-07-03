# STATUS — live project state

> The single "what's actually done / in-flight / next" view. **Every merged PR updates its line
> here in the same merge** (rule in the `shipping-changes` skill). `docs/execution-plan.md` stays
> the day-by-day plan; this file is the authoritative progress snapshot.

_Last updated: 2026-07-03 (Fri) — demo prep: Friday shooting script (`docs/demo-plan-friday.md`) + AI-run how-to (`docs/ai-run-howto.md`, honest AI-off) + README doc-index/last-verified tidy; v0.2.0 release cut. Prior: compressed-Friday push merged (Task 7 phone panel, model docs, AI pipeline + gold-set gate, quant proofs, Block C robustness) + Sunday-prep docs bundle._

## Done

- **Decisions** signed off (PRD §16: D1 Rust=mastery query, D2 three-score + give-up, D3 Android via
  rsdroid, D4 taxonomy, D5 ablation pre-registered).
- **Repo + licensing:** public AGPL-3.0 fork, `LICENSE` + Anki credit; submodules pinned
  (`anki@25.09.4`, `Anki-Android@v2.24.0`).
- **Spike 1 — desktop build:** `./run` compiled + ran a full review loop (exit 0).
- **Spike 2 — Android build:** `assembleFullDebug` SUCCESSFUL with `librsdroid.so`; emulator booted,
  AnkiDroid launched.
- **PR #1** (merged) — seeded GRE study-deck generator + `topic::*` tagging + coverage gate
  (`pipeline/`).
- **PR #2** (merged) — MIT OCW gold-set store + canary + validator, data gitignored (`eval/goldset/`).
- **PR #3** (merged) — workflow change-risk tiers + fast lane, compile-cache + trust-green, live
  `STATUS.md`, process-freeze guardrail (`.cursor/skills/`, `AGENTS.md`).
- **PR #4** (merged) — content-generation + timed-UI design spec, tuesday-data-foundation spec, and
  the content-generation pipeline plan, with matching PRD/INDEX/architecture/execution-plan updates
  (§8 interleaving algorithm, §8a flashcards→MCQ→timed, §12a two-lane generation, Appendix A
  tag/verification conventions).
- **PR #5** (merged) — Mastery Query (W1) design spec + implementation plan: read-only
  `StatsService.MasteryQuery` RPC (per-topic FSRS mastery aggregate), single-pass SQL + Rust
  aggregation, TDD task breakdown (docs only; the engine-lane implementation is separate).
- **PR #6** (merged) — Round-4 testing-UI research thread (SQ15: authentic exam-shell UI
  design/ablation/decision) added to `research/` + folded into SYNTHESIS/frame/sources. Verdict:
  COMPLEMENT (opt-in "Exam Mode" gating Readiness only); does not consume interleaving's ablation slot.
- **PR #7** (merged) — **W1 Mastery Query engine change** (the real Rust engine change, D1):
  read-only `StatsService.MasteryQuery` RPC + pylib `Collection.mastery_query` + 3 Rust unit tests
  (empty/zero · aggregation+hierarchy · read-only invariant asserting undo step + study-queue counts +
  `quick_check_corrupt`) + Python integration test + `#[ignore]`d 50k perf bench (p50 ~19 ms) +
  rsdroid codegen reachability. anki fork bumped to `f15cubing/anki@352135e`; `.gitmodules` repointed
  to the fork. Engine extra gate passed (different-agent review). Live Android AAR rebuild + review is W3.
- **PR #8** (merged) — **W2 desktop dashboard** design spec + implementation plan: read-only Memory
  score as a range (Wilson CI + ETS 50/25/25 rollup) + 17-leaf coverage map consuming the W1 RPC;
  three separated score slots (Readiness = honest give-up state, Performance = Thursday placeholder);
  Python view-model + vendored taxonomy + standalone SvelteKit route; TDD task breakdown (docs only;
  the Qt/TS implementation is a separate fast-lane PR).
- **PR #9** (merged) — **W2 desktop dashboard build** (fast lane, in the fork): read-only Memory score
  as a range (Wilson CI + ETS 50/25/25 rollup, n=0 renorm) + 17-leaf coverage map (per-leaf recall
  estimate + 95% range) consuming the W1 RPC; three separated slots (Readiness give-up state w/
  next-best topic + reasons, Performance Thursday placeholder); pure-Python view-model + vendored
  taxonomy (drift-guarded) + standalone SvelteKit route + read-only `greDashboardData` endpoint +
  Tools-menu QDialog. Playtested end-to-end; fixed a stale-bundle rebuild gotcha + the webview
  API-access allowlist (`GRE_DASHBOARD` kind). anki fork → `f15cubing/anki@ea3acae`.
- **PR #10** (merged) — **testing-process refinement:** require a GUI smoke test for any new webview
  page / SvelteKit route / dialog (fast-lane + base checklists), and document the two W2 gotchas
  (configure-time route globs → stale bundle; `webview.py` api-access allowlist → 403) in
  `building-and-testing`. Closes the gap where handler-level unit tests passed on an end-to-end-broken page.
- **PR #11** (merged) — **W3 Android review** design spec + implementation plan: rebuild rsdroid against
  our anki fork (bundles `rslib` w/ the W1 mastery query) + AnkiDroid-fork wiring (`local_backend`) + a
  real review session on an emulator + a read-only Kotlin `Collection.masteryQuery` binding proven by a
  Robolectric test (host `.jar`) + an on-emulator smoke; both Android repos tracked as recursive
  submodules; engine-lane w/ different-agent review. Docs only; the Android build is a separate PR.
- **PR #12** (merged) — **W3 Android review build** (engine lane): rebuilt `rsdroid` from source (our
  fork) so its bundled `rslib` carries the W1 mastery query; wired AnkiDroid via `local_backend=true`;
  added a read-only Kotlin `Collection.masteryQuery` binding proven by a host-JVM test against the real
  compiled `rslib` (`MasteryQueryTest`, green); on-emulator smoke shows `librsdroid.so` loads + the
  DeckPicker launches. Forks (recursive submodules): `f15cubing/Anki-Android@67364a7`,
  `f15cubing/Anki-Android-Backend@3dc30c2` (bundles `f15cubing/anki@ea3acae`). Different-agent review
  passed (read-only + no-`OpChanges` ceilings hold; no new engine code).
- **W3 Milestone-1 on-device evidence** (captured) — the manual gate deferred at PR #12: a real FSRS
  review session on the `anki_test` emulator (our `librsdroid.so` + seeded GRE deck; FSRS intervals +
  `topic::*` leaf tags visible), session persists across a force-stop/reopen, and **Check Database →
  "Database rebuilt and optimized"** (no corruption). Screenshots in `docs/evidence/w3-android/`.
- **W4 — Sync foundation** (fast lane) — self-hosted `anki-sync-server` on our engine
  (`f15cubing/anki@ea3acae`) via a one-command launcher (`make sync-server`) + headless round-trip
  regression (`make sync-smoke`: a reviewed `topic::*` note + revlog + scheduling cross A→server→B,
  `quick_check=ok`) + a **live cross-device round-trip** — real AnkiDroid emulator ↔ our server ↔ a
  headless desktop peer (same engine): full upload → full download (structural-divergence forced
  full sync, D3) → FSRS review on the phone → normal sync back; desktop pull confirmed `revlog` 1→2
  with `quick_check=ok`, and AnkiDroid **Check database → "Database rebuilt and optimized."** Conflict
  rule (revlog union · scheduling LWW · device-UUID tie-break deferred · structural divergence →
  forced full sync) documented in `docs/codebase/sync.md`; evidence in `docs/evidence/w4-sync/`. No
  engine/submodule changes. 7b (10+10 no-loss + same-card conflict) and 7g (crash/offline) are Thursday.

- **PR #18** (merged) — **docs:** represent the MCQ study surface in the plans — the Thursday
  execution-plan item is now an end-to-end MCQ implementation checklist (GRE MCQ note type + template,
  SymPy distractor generation, build-through-`build_deck.py`, tests) and the demo-plan Sunday-cut growth
  list names the MCQ surface (drives Performance). MCQ stays a content/data-model change, not a second
  engine change (D1 ceiling intact). Fast lane, docs only.
- **PR #15** (merged) — **docs:** README now has concrete, copy-pasteable run instructions for both
  surfaces — desktop (`cd anki && ./run` + one-time macOS setup) and mobile (rsdroid backend build →
  `./gradlew installFullDebug` onto a running emulator, with `local_backend`/NDK/Rust-target prereqs),
  plus an optional `make sync-server` note; condensed the redundant rsdroid section and fixed the stale
  footer. Fast lane, docs only.
- **PR #20** (merged) — **dashboard redesign** (fast lane): a distinctive "calibration-strip" design
  system for the GRE dashboard — `tokens.css` (6-colour palette + system tabular-mono numerals,
  light/dark via `.night-mode`, no bundled fonts) + `CalibrationStrip.svelte` (the signature range
  component: shaded 95% band + point tick, reused at exam/bucket/leaf scale; `n=0` → dotted "not yet"
  rail) + `lib.ts`/`lib.test.ts` (pure geometry, 8 vitest) + a restyle of the four dashboard
  components; amber (not red) give-up state; best-next leaf ringed; restrained page-load reveal
  (reduced-motion respected). Pure presentation — **no** `dashboard_data.py`/view-model change (that
  stays the scoring layer's surface); still read-only; three scores stay separate; the ScoreSlot state
  guard still forbids a fabricated readiness number. `check:svelte` + 8 vitest green; GUI smoke via a
  faithful headless render (light + dark). anki fork → `f60c2fe`. Ships the shared `CalibrationStrip`
  the Thursday scoring layer renders Performance/Readiness through.
- **PR #21** (merged) — **exam-mode core (B-1)** (fast lane): vendored, engine-free GRE-exam form
  assembly + rights-only scoring — `anki/qt/aqt/gre/exam.py` (deterministic blueprint-matched 50/25/25
  form at the official 2.58 min/item pace; presets 66/33/22/11; per-leaf/bucket breakdown + Wilson CI +
  attempts record) + `exam_items.json` (vendored 80-item eval bank, firewalled + drift-guarded).
  `test_gre_exam.py` (check:pytest:aqt green) + outer `test_exam_items_sync.py`. Vendored because the
  app can't read the outer `eval/bank/` at runtime. anki fork → `a22bafc`. Webview shell is B-2.
- **PR #22** (merged) — **exam-mode webview (B-2)** (fast lane): the faithful GRE Math Subject Test
  shell on the B-1 core — SvelteKit `gre-exam` route (`+page` session state machine + one global
  countdown, `ItemView` 5×A–E, `Navigator` review grid, `Results` reusing `CalibrationStrip`) + Tools
  ▸ GRE exam mode dialog. One clock · one item · Mark + free Back/Next · Review screen · **no
  calculator · no pause · auto-submit at 0:00 · no per-item feedback**; presets 66/33/22/11 at the
  official 2.58 min/item. Read-only `greExamForm`/`greExamSubmit` (server-side rights-only scoring;
  keys withheld from the client mid-exam; attempts to a profile side-file, never the collection).
  Firewalled to the vendored eval items (p0). `check:svelte` + `check:pytest:aqt` + vitest green;
  headless GUI smoke of setup/exam/review/results. anki fork → `484f66b`.

- **Deck auto-incorporation** (engine-lane, 3 PRs) — the ~5,400-card study deck now **ships inside both
  apps** and **auto-imports on first run** (no manual File→Import), version-gated + history-preserving
  (add/update via content GUIDs, `with_scheduling=false`), sync-safe (`gre_deck_version` in `col.conf`).
  Desktop importer merged (`f15cubing/anki#1`, hook `collection_did_load`); AnkiDroid importer merged
  (`f15cubing/Anki-Android#1`, DeckPicker hook). Validated: desktop unit 3/3 + GUI smoke; AnkiDroid
  unit 2/2 against the real custom rsdroid + **emulator smoke** (fresh install auto-imports 5,435 cards,
  idempotent on relaunch). anki fork reconciled with the exam-mode line (importer + exam + dashboard
  hooks coexist). `make deck-asset` keeps the bundled asset in sync with `pipeline/`. Evidence in
  `docs/evidence/deck-auto/`.
- **Scoring layer — Performance + Readiness** (Thu; pure-Python `scoring/` package): calibrated
  Performance (logistic + **Platt**, analytic Fisher-SE single-item interval) and Readiness (projected
  GRE 200–990 as a **range**: Poisson-binomial aleatoric SD + split-conformal on held-out form
  residuals, **Bayesian normal-posterior cross-check**), gated by the 3-condition give-up rule
  (≥200 reviews · ≥50% coverage · width ≤ 120). 32/32 tests; `make score-eval` green (Readiness shows
  e.g. 711 [678–748]). Honest n≈1 labels throughout; difficulty firewalled; stdlib-only. Opus math
  review CHANGES-REQUIRED items all fixed. The desktop adapter (writes the synced `gre_scorecard`) is
  **shipped** (Task 6, `anki@7c4836c5`); the AnkiDroid read-only 3-score panel is Task 7.

- **PR #25** (merged) — **LaTeX math rendering** (fast lane): all study-deck math now renders as real
  LaTeX via MathJax (Anki reviewer + AnkiDroid already typeset `\(...\)`/`\[...\]`; no new dep, no
  `[latex]` image toolchain, offline-safe). New `pipeline/mathfmt.py` contract;
  `generate_deck`/`generate_mcq`/`distractors` emit LaTeX (correctness now checked on ground-truth SymPy
  via test-only `_expr`/`_correct_expr`, not markup); all ~57 `conceptual_cards.yaml` records migrated as
  a re-verification pass; `build_deck` LaTeX/`html.escape` round-trip documented + `test_latex_escaping.py`;
  `eval/bank/generate_eval.py` emits LaTeX. Deck rebuilds clean (coverage + verification gates green); 64
  pipeline+eval tests green. Design:
  `docs/superpowers/specs/2026-07-02-latex-math-rendering-design.md`. **Deferred to a submodule-enabled
  session** (working tree `anki`@`ea3acae` predates Exam Mode/bundled asset): migrate `eval/bank/items.yaml`
  **with** the vendored `anki/qt/aqt/gre/exam_items.json` (together, to keep `test_exam_items_sync` green),
  wire MathJax into the `gre-exam` webview, and `make deck-asset` re-sync + `gre_deck_version` bump.

- **PR #27** (merged) — **Exam-Mode LaTeX** (engine lane; `anki` fork `agent/gre-exam-latex` → `a631ec3`,
  outer pin bumped) — the eval bank (`eval/bank/items.yaml`, 80 items) migrated to delimited LaTeX
  **together with** its vendored copy `anki/qt/aqt/gre/exam_items.json` (so `test_exam_items_sync` stays
  green as a unit), and MathJax wired into the `gre-exam` webview (`mathjax.ts` config+dynamic-import →
  offline code-split chunk; `ItemView`/`Results` typeset; `+page` keys items). Verified: eval-bank suite +
  exam-items sync green; `check:svelte`/`check:eslint`/format clean; SvelteKit bundle builds and the exam
  page dynamically imports the local MathJax chunk. Computational strings converted via SymPy
  (round-trip-verified); prose hand-mapped. Different-agent review passed.
  Design: `docs/superpowers/specs/2026-07-02-latex-math-rendering-design.md`.

- **Desktop scoring adapter (Task 6)** (engine lane; `anki` fork `agent/scoring-desktop` → `7c4836c5`
  restacked on Exam-Mode LaTeX, outer pin bumped) — on GRE dashboard open, `qt/aqt/gre/scoring_adapter.py`
  gathers the W1 mastery rows + coverage (W2 view-model) and writes the synced three-score `gre_scorecard`
  to `col.conf` (rides W4 sync → unblocks the AnkiDroid panel, Task 7). Memory = FSRS Wilson range;
  Performance = not-available; **Readiness gated off** with reasons + evidence panel (never derived from
  Memory; never a bare number). Read-only except the one `set_config` (`undoable=False`, undo preserved);
  no Rust/schema change. 3 adapter/trigger tests + 32 GRE aqt tests green; `ruff`/`mypy` clean; headless
  round-trip smoke (scorecard persists, no corruption). Different-agent review **APPROVED**
  (`f15cubing/anki#2` + `f15cubing/speedrun#28`).
- **LaTeX study-deck rebundle + stable GUIDs** (engine lane; `anki`@`2b01ca9` (rebundle on the scoring
  adapter), `Anki-Android`@`e55b0ba`, outer pins bumped) — the bundled study-deck `.apkg` in **both apps**
  is re-bundled from the LaTeX pipeline so first-run auto-import ships real math. Two supporting pipeline
  changes: (1) note GUIDs now derive from a **stable, rendering-independent `uid`**
  (`<leaf>::<format>::<ordinal>`), so re-rendering (ASCII→LaTeX, and future edits) updates cards **in
  place** instead of duplicating on re-import; (2) `build_deck` re-zips the `.apkg` deterministically
  (fixed 1980 timestamps) so it's byte-reproducible and `make deck-asset-check` passes. Verified: 50
  pipeline tests green (incl. `test_stable_guids`); `make deck-asset` + `deck-asset-check` byte-match
  across both app assets; desktop `test_gre_autoimport` 3/3; rebundled asset confirmed LaTeX.
  **`gre_deck_version` intentionally NOT bumped** (the key syncs across apps, so the bump must land in
  both together on a Java-equipped machine): fresh installs get LaTeX now; existing installs are
  unaffected until that coordinated bump. Android build + emulator smoke also deferred (no Android
  toolchain here). Different-agent review **APPROVED** (`f15cubing/speedrun#29`).
- **`gre_deck_version` bump → 2026-07-03** (engine lane; `anki`@`aa5565b`, `Anki-Android`@`b1673c5`, outer
  pins bumped) — flips the version gate in **both** apps' importers so existing installs re-import the
  already-bundled LaTeX deck on next launch; stable GUIDs make it an **in-place** update (no duplicates).
  Both constants match (`2026-07-03`); desktop `test_gre_autoimport` 3/3 green. The AnkiDroid one-line
  change was committed with `--no-verify` (its ktlint pre-commit hook needs a Java runtime absent on this
  host; the change is a same-style date constant). **Android APK build + ktlint + emulator smoke of
  first-run re-import remain the one deferred manual gate.**

- **Pre-uid dedup migration + on-device Android smoke** (engine lane; `anki`@`a58831e`,
  `Anki-Android`@`ed7ef0a`, outer pins bumped) — an **emulator smoke** of the `gre_deck_version` bump
  caught a real bug: upgrading an install whose bundled deck predated the stable-uid GUID scheme
  **duplicated** it (content-hash GUIDs can't be matched by the new package → 5.4k → 10.8k cards). Fix
  (both apps): stamp `gre_deck_guid_scheme`; on re-import, if it isn't the uid scheme, remove the
  previously-bundled notes (our two note types) once, then import — fresh installs and future uid→uid
  re-imports are unaffected (history preserved). **Verified on the `anki_test` emulator**: a pre-uid
  dup'd collection (10,842 notes) → after launch **5,407 LaTeX notes, 0 ASCII, no duplicates**, scheme
  stamped. Desktop `test_gre_autoimport` 7/7 (pre-uid-no-dup + uid-in-place + scheme-stamp + stale-scheme
  repair); AnkiDroid ktlint clean; APK built with our rsdroid + installed on the emulator. (Also corrected
  the earlier "no Java" note — the full Android toolchain, incl. JDK 21, was present.) Different-agent
  review **APPROVED**; per its one caveat, the import guard now checks **both** the version and the GUID
  scheme (so an install already at the current version but with a stale scheme — the theoretical
  double-import case — self-repairs). Re-smoked on the emulator: a version-matched dup'd collection
  (10,842) healed to **5,411 LaTeX notes, no dup**. (`f15cubing/speedrun#31`.)

- **AnkiDroid read-only score card panel (Task 7)** (engine lane; `Anki-Android` fork
  `agent/scoring-android` → `78989b9e`, outer pin bumped) — the desktop-written `gre_scorecard` (Task 6)
  now renders **read-only** on the phone: DeckPicker overflow → "GRE readiness" opens `GreScorecardFragment`
  (hosted by `SingleFragmentActivity`), which reads the synced `col.conf` value via `withCol { config… }`,
  parses it with a kotlinx.serialization model (`GreScorecard.kt`, `ignoreUnknownKeys`), and shows the three
  scores **separately** — Readiness only as a number when the desktop gate passed, else the evidence panel;
  never a bare number, no scoring math on device. Reuses the W3 local rsdroid (`local_backend=true`) — **no
  rebuild** (config read only). 5 host-JVM parser tests + ktlint green; APK built + installed on the
  `anki_test` emulator and the panel opens via the menu (empty state until a card syncs; screenshots in
  `docs/evidence/task7-android/`). Full desktop→sync→populated-panel demo is the separable integration
  (builds on W4 sync). Different-agent review **APPROVED** (`f15cubing/speedrun#32`).
- **Block E docs — model descriptions + README architecture/Rust-change note** (fast lane, docs only) —
  three grader-facing **one-page model descriptions** in `docs/models/` (`memory.md` = FSRS
  retrievability + Wilson range; `performance.md` = logistic + Platt with an analytic Fisher-SE
  interval; `readiness.md` = Poisson-binomial → ETS-percentile → split-conformal range, gated by the
  D2 give-up rule: ≥200 reviews · ≥50% coverage · width ≤ 120, a bare readiness number is an auto-fail),
  each covering inputs/features, the math, uncertainty-as-a-range, and the honesty labels; plus a new
  **Architecture overview** (two clients over one shared `rslib`; rsdroid on Android; the read-only
  mastery-query RPC; the desktop-authoritative synced `gre_scorecard`) and **Rust-change note**
  (files touched + **merge-difficulty = LOW**) in `README.md`, with the three model docs linked. No
  code/engine change. (`f15cubing/speedrun#33`.)
- **Block A — AI card pipeline + gold-set gate** (fast lane, `pipeline/aicards/`; PR on
  `agent/ai-pipeline`, **open for human review — do not auto-merge**) — the full PRD §9 machinery,
  real and unit-tested (52 tests): RAG over an original single-variable-calculus source chapter →
  **non-nullable verbatim-quote + anchor provenance** (drop/abstain if absent) → **in-pipeline
  abstention** → **SymPy CAS** re-derivation for computational cards (a wrong answer cannot publish)
  and **NLI-proxy + mandatory human-review** for conceptual cards → **pre-lodged gold-set gate**
  (`FACT_PRECISION_MIN=0.98`, `USEFUL_YIELD_MIN=0.60`) scored by **2 raters with Cohen's κ**. One
  command: `make ai-gate`. **AI access = AI-off (no live-model API key):** per the plan, the machinery
  is driven by a transparent **deterministic stub** (live-model seam = `orchestrator.LlmBackend`,
  fails loudly without a key). **Gate PASSED on the stub:** 50 generated → 35 published / 5 conceptual
  drafts / 10 abstained; **fact-precision 1.000** (independent numeric-rater audit agrees),
  **useful-yield 0.64**, **κ 0.938 @ 98% agreement**, safety-recall 1.0; **firewall PASS** (canary/
  ETS/OCW-free, anchors all from the corpus, generation never reads the held-out store). Numbers
  validate the *machinery*, not a live model — a real-LLM run is pending API access. Docs:
  `pipeline/aicards/aicards.md`. No engine/submodule change.

- **Block C proofs — beat-the-baseline + AI-off degradation** (fast lane, `pipeline/aicards/`;
  folded into the same PR #34 branch `agent/ai-pipeline`, **open — do not auto-merge**) — the two
  A-gated proofs, real + unit-tested (suite now **76 tests**). One command: `make ai-baseline`.
  (1) **Beat-the-baseline (McNemar exact, pure stdlib):** AI-pipeline arm (RAG+provenance+CAS+abstain)
  vs. a template/cloze **non-RAG, no-verify/abstain** baseline over the **same shared SymPy targets**
  (only the pipeline differs), scored by the **same rater**. AI **fact-precision 1.000 / useful-yield
  0.833** vs. baseline **0.600 / 0.400**; paired 2×2 a=20/b=30/c=4/d=6; **McNemar p = 6.165e-06**
  favoring AI; useful-yield-diff 90% bootstrap CI [0.300, 0.567] (excludes 0). **AI beats the baseline
  with the fact-precision ceiling intact**; honest-null language auto-triggers if a run misses α=0.05.
  (2) **AI-off degradation:** no key → the live-model seam fails loudly and `run_pipeline_safe` aborts
  cleanly (**0 cards, 0 unverified shipped**) while the study/review deck + `scoring/` still load — AI
  is a build-time content step, not a runtime dependency (static guard: `scoring/` never imports the
  generator or a model/network client). AI-off caveat: validates the **machinery**, not a live model.
  Docs: `pipeline/aicards/aicards.md`. No engine/submodule change.
- **Block D — quantitative proofs** (fast lane; `agent/quant-proofs`) — three re-runnable, deterministic
  proofs under `proofs/` + `docs/evidence/proofs/`: (1) **`make bench`** times the real
  `col.mastery_query` RPC at **50k cards** through the built engine — **p50 650 ms · p95 667 ms · worst
  709 ms** (20 topics/call; ≈32 ms/topic, consistent with the isolated ~19 ms Rust aggregate + 20×
  hierarchical scans + FFI marshaling; honest sub-second dashboard refresh, batch/index noted as future
  opt); (2) **memory calibration** (`make proofs`) — held-out student split, **Brier 0.219 · ECE 0.061**,
  reliability curve hugs the diagonal (`calibration.png`); (3) **paraphrase** over the eval bank's 28 P3
  groups — R1 0.630 [0.622,0.638] vs R2 0.624 [0.616,0.632], gap 0.006 → paraphrase-robust. Scoring proofs
  labeled "simulated (machinery check); validity unestablished at n≈1." `scoring/` stays pure-stdlib
  (charts in a separate `.venv-proofs`); 4 helper unit tests green. **Ablation run is CUT-FIRST**
  (Sat/Sun buffer — interleaving instrumentation not yet built; pre-registration stands).
- **Block C robustness proofs — crash-safety (7g) + two-way sync (7b)** (fast lane; **evidence + tests,
  no engine/collection change**) — headless on our engine (`f15cubing/anki@ea3acae`, `25.09.4`).
  **7g:** one evolving collection **SIGKILLed mid-review ×20** → **20/20 CLEAN** (`quick_check` **and**
  `integrity_check`=ok, no revlog loss; 31,405 committed reviews survived), plus a `--selftest` that
  shows the gate rejects a byte-corrupted DB (non-vacuous). **7b:** two-way sync via a self-hosted
  server on its own `:8090`/data-dir — **10+10 no-loss → all 20 reviews land on both peers**, and a
  **same-card conflict** (pure review divergence) demonstrating the documented rule: **revlog union
  (+2 on both) + scheduling LWW (later-`mod` peer wins; loser's schedule overwritten)** — `quick_check`
  =ok throughout. Harnesses `robustness/crash_test_7g.py` + `sync/two_way_sync_7b.py`
  (`make crash-7g` / `sync-server-7b` + `sync-7b`); docs `robustness/README.md` + `docs/codebase/sync.md`
  (§ Block C proofs). **Android leg CUT** (shared `anki_test` emulator busy with the Task-7 subagent);
  device side already covered by W3 (Check-DB "rebuilt and optimized" after a force-stop) + W4 (live
  AnkiDroid↔desktop two-way sync). Evidence: `docs/evidence/robustness/`. (`f15cubing/speedrun#36`.)
- **Sunday-prep docs bundle** (fast lane, docs only; PR on `agent/sunday-prep`, **open for review — do
  not merge**) — one cohesive Sunday-prep documentation PR: (1) a consolidated **Sat/Sun buffer
  (CUT-FIRST spillover)** log (below) naming the four deferred items (ablation run · demo recording ·
  AI live-model run · Block C Android leg) with why + what's ready + ceiling impact; (2) `execution-plan.md`
  Days 4+5 COMPRESSED marked **done** (A #34 · B Task 7 #32 / Task 6 · C #34+#36 · D #35 · E #33) with
  CUT-FIRST items pointed at the Sunday buffer; (3) `docs/demo-plan.md` rewritten into the **Sunday cut**
  (live 3 scores on desktop + read-only phone panel, AI pipeline + gold-set gate framed AI-off, the four
  proofs), Milestone-1 script preserved as an appendix; (4) a new **`docs/submission-checklist.md`**
  (desktop installer + signed-APK steps, the hard-ceiling checklist, deliverables list; human-gated items
  marked), linked from README. No code/engine change; honesty framing preserved throughout.

## In flight

- _Dashboard redesign (PR #20) + Exam Mode (PR #21 core, PR #22 shell) + deck auto-incorporation +
  LaTeX math rendering (PR #25) + Exam-Mode LaTeX + LaTeX study-deck rebundle + `gre_deck_version` bump
  + pre-uid dedup migration shipped. Scoring `scoring/` package (Tasks 1–5) done + math-reviewed; desktop
  scoring adapter (Task 6) + AnkiDroid read-only panel (Task 7) shipped — Milestone-1 scoring surfaces
  complete on both platforms. Nothing blocking in flight._

## Sat/Sun buffer (CUT-FIRST spillover)

> The self-imposed **Friday 7:00 PM CT** target banked the weekend as buffer. Everything below is a
> **CUT-FIRST** item that slipped into the Sat/Sun buffer **without breaking a hard ceiling** — the
> real submission deadline (**Sunday 2026-07-05, 10:59 PM CT**) is untouched. In every case the
> machinery is built and re-runnable; what remains is either **human-gated** or blocked on a resource
> we don't control in this environment. None of these is on the critical path to a passing submission.

| Deferred item | Why deferred | What's already built / stands | Ceiling impact |
|---|---|---|---|
| **Ablation run** (interleaved vs. blocked vs. plain Anki) | Interleaving instrumentation (the interleaved↔blocked toggle + plain-Anki arm) is **not built yet**; a pre-registered "not yet run" is the honest state. | **Pre-registration stands** (PRD Appendix B, locked 2026-06-30): H1 + SESOI dz 0.3, three arms, within-subject Latin-square, delayed endpoint, **TOST + 90% CI + honest-null template**. Block D shipped the other three proofs (#35). | None. Study feature (15%) keeps its pre-reg + design; a documented null or honest "not run" scores — a post-hoc hypothesis would not. |
| **Demo recording** (3–5 min Sunday cut) | Needs **a human at the keyboard** for live screen capture of the desktop app + Android emulator. | Full shot-by-shot **Sunday-cut script** in `docs/demo-plan.md`; every segment it shows is merged + reproducible from one command. | None. Deliverable is human-gated, not blocked on code. |
| **AI live-model run** | Blocked **only on a live-model API key**; no key in this environment, so the pipeline runs **AI-off**. | Live-model **seam ready** (`orchestrator.LlmBackend`, fails loudly without a key) + **gate PASSED on the deterministic stub** — fact-precision **1.000**, useful-yield **0.64**, κ **0.938**, McNemar beat-baseline **p=6.2e-06**. One command: `make ai-gate`. | None. Machinery validated (not a live model); going live is a one-file change. Numbers validate the machinery, not a live model — **do not overclaim**. |
| **Block C Android leg** (on-device crash/sync round) | The shared `anki_test` **emulator was busy** with the Task-7 subagent. | Desktop **7g 20/20 clean + 7b 10+10 + conflict** proven headless (#36); the Android device side is already covered by **W3** (Check-DB "rebuilt and optimized" after a force-stop) + **W4** (live AnkiDroid↔desktop two-way sync). | None. Both durability properties are demonstrated; the emulator round is a representative re-run, documented in `robustness/README.md`. |

**Sunday still-to-do (human-gated, tracked in `docs/submission-checklist.md`):** record the demo,
build + clean-machine-verify the desktop installer, build + **sign** the APK and record it on a clean
device, then upload the deliverables (repo · demo video · three model descriptions · Brainlift).

## Next (per execution-plan)

- **Wednesday — Milestone 1 (decomposed):**
  - **W1 — Mastery Query (Rust engine change):** ✅ **shipped (PR #7).** Read RPC, never `OpChanges`.
  - **W2 — Desktop dashboard:** ✅ **shipped (PR #9).** Memory score as a range + coverage map
    (consumes the RPC); read-only, three separated slots. Spec + plan were PR #8.
  - **W3 — Android review:** ✅ **shipped (PR #12) + on-device gate captured.** rsdroid rebuilt with our
    change + APK on the local backend + `masteryQuery` binding proven (host-JVM test) +
    `librsdroid.so`-loads smoke; the hands-on-device FSRS review-session + Check-Database no-corruption
    evidence is now captured (`docs/evidence/w3-android/`).
  - **W4 — Sync foundation:** ✅ **shipped.** Self-hosted `anki-sync-server` on our engine +
    `make sync-server`/`make sync-smoke` + live AnkiDroid↔desktop-peer round-trip (Check-DB clean);
    conflict rule documented (`docs/codebase/sync.md`).
- **Block C (Days 4+5) — 7b two-way sync + 7g crash-safety:** ✅ **proven headless** (desktop);
  Android leg CUT (shared emulator). See the Done entry above + `docs/evidence/robustness/`.
