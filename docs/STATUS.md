# STATUS — live project state

> The single "what's actually done / in-flight / next" view. **Every merged PR updates its line
> here in the same merge** (rule in the `shipping-changes` skill). `docs/execution-plan.md` stays
> the day-by-day plan; this file is the authoritative progress snapshot.

_Last updated: 2026-07-01 (Wed)._

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

## In flight

- **W2 — Desktop dashboard** (memory score as a range + 17-leaf coverage map): playtested (fixed stale route bundle + webview API access); **PR #9** open on `feat/gre-dashboard` (`f15cubing/anki@ea3acae`).

## Next (per execution-plan)

- **Wednesday — Milestone 1 (decomposed):**
  - **W1 — Mastery Query (Rust engine change):** ✅ **shipped (PR #7).** Read RPC, never `OpChanges`.
  - **W2 — Desktop dashboard:** memory score as a range + coverage map (consumes the RPC). Spec +
    plan shipped (PR #8); **build is next** (fast lane, in the fork).
  - **W3 — Android review:** rebuild rsdroid with our change; review the shared deck on the same engine.
  - **W4 — Sync foundation:** `anki-sync-server` + conflict-rule smoke test.
