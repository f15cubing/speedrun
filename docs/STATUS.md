# STATUS — live project state

> The single "what's actually done / in-flight / next" view. **Every merged PR updates its line
> here in the same merge** (rule in the `shipping-changes` skill). `docs/execution-plan.md` stays
> the day-by-day plan; this file is the authoritative progress snapshot.

_Last updated: 2026-07-03 (Fri) — Exam-Mode LaTeX merged (PR #27); scoring layer package (Performance + Readiness)._

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
  stamped. Desktop `test_gre_autoimport` 6/6 (adds pre-uid-no-dup + uid-in-place + scheme-stamp);
  AnkiDroid ktlint clean; APK built with our rsdroid + installed on the emulator. (Also corrected the
  earlier "no Java" note — the full Android toolchain, incl. JDK 21, was present.) Different-agent review
  pending.

## In flight

- _Dashboard redesign (PR #20) + Exam Mode (PR #21 core, PR #22 shell) + deck auto-incorporation +
  LaTeX math rendering (PR #25) + Exam-Mode LaTeX + LaTeX study-deck rebundle + `gre_deck_version` bump
  shipped. Scoring `scoring/` package (Tasks 1–5) done + math-reviewed; desktop scoring adapter (Task 6)
  shipped; AnkiDroid read-only panel (Task 7) pending. **Only deferred gate:** Android build + emulator
  smoke of the LaTeX deck re-import (no Android toolchain on this host)._

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
    conflict rule documented (`docs/codebase/sync.md`). 7b/7g deferred to Thursday.
