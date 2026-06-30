---
name: shipping-changes
description: Use when making any code change in the Anki fork that will be merged, when about to commit/push or open a pull request, or when reviewing another agent's PR. Covers creating an isolated git worktree and branch, opening a real GitHub pull request, and having a different subagent verify it against a tiered checklist before merge.
---

# Shipping Changes

## Overview

Every change ships on **a branch** (never `main` directly) as a **real `gh` pull request**. How
much ceremony rides on that depends on the **change-risk tier** below. Never commit to `main`
directly. Never review or merge your own PR in the engine lane.

## Change-risk tiers

Pick the lane with the "engine PR?" test in `pr-checklist.md`.

| | **Engine lane** | **Fast lane** |
|---|---|---|
| **What** | Touches `rslib/`, `.proto`, `pylib` FFI, the `anki`/`Anki-Android` submodules, or the scheduler/undo/collection store | Non-engine only: `pipeline/`, `eval/`, `docs/`, `.cursor/skills/`, deck content, Qt-UI-only |
| **Worktree** | Required (isolation + build) | Optional — a dedicated branch in place is fine |
| **Submodule init** | `git submodule update --init --recursive` | **Skip** — change doesn't touch submodule code |
| **Review** | A **different agent** verifies (extra gate) | **Self-review** against the fast-lane checklist |
| **Design gate** | Full `brainstorming` → spec as warranted | 2–3 sentence intent note in the PR body |
| **Docs** | Updated in same PR, SHA bumped | Updated in same PR |

The hard ceilings live in the engine lane — it keeps its full armor. The fast lane only ever
applies to changes that **cannot** touch the collection, undo, or the three-score/readiness rules.

## Builder role (engine lane)

1. `git fetch`; create a new branch off the latest `main` **in a new git worktree** named `agent/<area>-<task>`. **REQUIRED:** use `using-git-worktrees`.
2. In the new worktree, run `git submodule update --init --recursive`. **REQUIRED:** use `working-with-submodules`.
3. **Before editing**, invoke `codebase-docs` and read the docs relevant to the files you'll touch.
4. Make the change, scoped to one task. Use TDD where it applies.
5. Update the relevant docs in the same change (bump `Last verified against:` SHA).
6. Verify locally: build + run the tests for the touched area. **REQUIRED:** use `building-and-testing` for the exact commands, then `verification-before-completion` before claiming green.
7. Commit (conventional message) → push → open a PR with `gh pr create`, filling the body template in `pr-checklist.md`.
8. Hand off to a reviewer subagent. **Never self-merge.**

## Builder role (fast lane — non-engine changes only)

Only for changes that cannot touch the collection, undo, or the scoring/readiness rules
(`pipeline/`, `eval/`, `docs/`, `.cursor/skills/`, deck content, Qt-UI-only). If in doubt, it's the
engine lane.

1. Create a branch `agent/<area>-<task>` off the latest `main` (worktree optional). **Skip**
   `git submodule update --init --recursive`.
2. **Before editing**, read the relevant docs (`codebase-docs`). Make the change, scoped to one task.
3. Update the relevant docs in the same change.
4. Verify what's verifiable (tests/lint for the touched files) — `verification-before-completion`.
5. Commit → push → open a PR; the design gate is a **2–3 sentence intent note** in the PR body.
6. **Self-review** against the fast-lane checklist in `pr-checklist.md`, then squash-merge yourself.
   On merge, update the change's line in `docs/STATUS.md`.

## Reviewer role (engine lane — must be a different agent)

1. `gh pr checkout <pr>` into a fresh worktree of your own.
2. Run the tiered checklist in `pr-checklist.md`:
   - **Base gate** — every PR.
   - **Extra gate** — engine/Rust PRs (see `pr-checklist.md` for what counts), in addition to base.
   - **Trust posted green + spot-check:** if the builder posted green (`./ninja check` output or CI),
     trust it and spot-check the ceiling items (undo, no-corruption, read-only invariant) rather than
     rebuilding blind. No green posted → rebuild. See `building-and-testing`.
3. Leave review comments via `gh`; approve or request changes. **REQUIRED:** use `requesting-code-review` for what to look for. The builder uses `receiving-code-review` to respond.
4. Merge only when green + approved → squash to `main` → remove the worktree + delete the branch → update `docs/STATUS.md`. **REQUIRED:** use `finishing-a-development-branch`.

## Composition

Reach for these (reference by name; don't duplicate them):

- `building-and-testing` — exact build/run/test commands per surface (desktop, Android, Rust).
- `working-with-submodules` — submodule init / pinning / footguns.
- `using-git-worktrees` — isolated working dir + branch per agent.
- `dispatching-parallel-agents` — when fanning out independent changes.
- `requesting-code-review` / `receiving-code-review` — the review exchange.
- `verification-before-completion` — before claiming tests/build are green.
- `finishing-a-development-branch` — merge + cleanup.
- `babysit` — keep a PR merge-ready (triage comments, resolve conflicts, fix CI).
- `ci-investigator` — diagnose a failing CI check.

For an engine/RPC change, also read the insertion-point sections in `docs/codebase/proto-rpc.md`,
`rslib.md`, and `pylib.md` (via `codebase-docs`) before editing.

## Red flags — STOP

| Thought | Reality |
|---|---|
| "I'll just commit straight to `main`." | No — a branch + PR, always, in either lane. |
| "I'll self-review my engine change." | No — engine lane needs a **different agent**. Self-review is fast-lane only. |
| "Tests are flaky, I'll merge anyway." | No — use `ci-investigator` / `babysit`; merge only when green. |
| "It's a UI tweak but it changes the scheduler/undo/store." | Then it's the **engine lane**, not fast lane. When in doubt, engine lane. |
| "Fast lane, so I'll skip the PR / skip updating docs." | No — fast lane still needs a real PR, scoped task, docs in the same PR, and a `STATUS.md` line. |
| "It's an engine change but the base gate passed." | Engine/Rust PRs also need the EXTRA gate (undo, no corruption, invariant test). |

## Checklist

Full tiered checklist + PR body template: `pr-checklist.md`.
