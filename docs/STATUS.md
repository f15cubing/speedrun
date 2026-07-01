# STATUS — live project state

> The single "what's actually done / in-flight / next" view. **Every merged PR updates its line
> here in the same merge** (rule in the `shipping-changes` skill). `docs/execution-plan.md` stays
> the day-by-day plan; this file is the authoritative progress snapshot.

_Last updated: 2026-06-30 (Tue)._

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

## In flight

- **W1 — Mastery Query (Rust engine change):** implemented on outer branch
  `agent/rslib-mastery-query` (anki fork `f15cubing/anki@engine/mastery-query`, `352135e`); **PR open,
  awaiting the different-agent extra gate** (engine lane — never self-merge). Read-only
  `StatsService.MasteryQuery` RPC (per-topic FSRS mastery aggregate) + pylib `Collection.mastery_query`
  + 3 Rust unit tests (empty/zero · aggregation+hierarchy · read-only-invariant) + Python integration
  test + `#[ignore]`d 50k perf bench (p50 ~19 ms, < 50 ms target) + rsdroid **codegen** reachability
  (RPC in proto descriptor + generated `backend.rs`/`_backend_generated.py`/`backend.ts`; live AAR
  rebuild deferred to W3). On merge, the reviewer moves this to **Done** with the PR number.

## Next (per execution-plan)

- **Wednesday — Milestone 1 (decomposed):**
  - **W1 — Mastery Query (Rust engine change):** **implemented; in review** (see "In flight"). Read
    RPC, never `OpChanges`.
  - **W2 — Desktop dashboard:** memory score as a range + coverage map (consumes the RPC).
  - **W3 — Android review:** rebuild rsdroid with our change; review the shared deck on the same engine.
  - **W4 — Sync foundation:** `anki-sync-server` + conflict-rule smoke test.
  - **This is the critical path — front-load W1.**
