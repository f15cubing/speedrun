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

## In flight

- **`agent/workflow-risk-tiers`** — workflow tuning: change-risk tiers + fast lane, compile-cache +
  trust-green, this `STATUS.md`, process-freeze guardrail (fast-lane PR, self-reviewed).
- Uncommitted in-progress doc edits exist in the working tree (not owned by this branch).

## Next (per execution-plan)

- **Wednesday — Milestone 1:** Rust mastery-query change end-to-end (read RPC, never `OpChanges`) →
  desktop review + memory score as a range + coverage map; Android reviews the shared deck on the
  same engine; sync-server smoke test. **This is the critical path — front-load it.**
