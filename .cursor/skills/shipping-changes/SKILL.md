---
name: shipping-changes
description: Use when making any code change in the Anki fork that will be merged, when about to commit/push or open a pull request, or when reviewing another agent's PR. Covers creating an isolated git worktree and branch, opening a real GitHub pull request, and having a different subagent verify it against a tiered checklist before merge.
---

# Shipping Changes

## Overview

Every change ships on its **own branch in its own git worktree**, as a **real `gh` pull request**, verified by a **different agent**. Never commit to `main` directly. Never review or merge your own PR.

This skill has two roles: **builder** (makes the change) and **reviewer** (verifies it). They MUST be different agents.

## Builder role

1. `git fetch`; create a new branch off the latest `main` **in a new git worktree** named `agent/<area>-<task>`. **REQUIRED:** use `using-git-worktrees`.
2. In the new worktree, run `git submodule update --init --recursive`. **REQUIRED:** use `working-with-submodules`.
3. **Before editing**, invoke `codebase-docs` and read the docs relevant to the files you'll touch.
4. Make the change, scoped to one task. Use TDD where it applies.
5. Update the relevant docs in the same change (bump `Last verified against:` SHA).
6. Verify locally: build + run the tests for the touched area. **REQUIRED:** use `building-and-testing` for the exact commands, then `verification-before-completion` before claiming green.
7. Commit (conventional message) → push → open a PR with `gh pr create`, filling the body template in `pr-checklist.md`.
8. Hand off to a reviewer subagent. **Never self-merge.**

## Reviewer role (must be a different agent)

1. `gh pr checkout <pr>` into a fresh worktree of your own.
2. Run the tiered checklist in `pr-checklist.md`:
   - **Base gate** — every PR.
   - **Extra gate** — engine/Rust PRs (see `pr-checklist.md` for what counts), in addition to base.
3. Leave review comments via `gh`; approve or request changes. **REQUIRED:** use `requesting-code-review` for what to look for. The builder uses `receiving-code-review` to respond.
4. Merge only when green + approved → squash to `main` → remove the worktree + delete the branch. **REQUIRED:** use `finishing-a-development-branch`.

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
| "I'll just commit straight to `main`." | No — branch + worktree + PR, always. |
| "I'll review and merge my own PR." | No — a different agent reviews. Never self-merge. |
| "Tests are flaky, I'll merge anyway." | No — use `ci-investigator` / `babysit`; merge only when green. |
| "Small change, skip the worktree." | No — worktree every time; it's how parallel agents stay isolated. |
| "It's an engine change but the base gate passed." | Engine/Rust PRs also need the EXTRA gate (undo, no corruption, invariant test). |

## Checklist

Full tiered checklist + PR body template: `pr-checklist.md`.
