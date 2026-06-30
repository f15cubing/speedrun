# Workflow Tuning — Design Spec

> Cuts process overhead for the remaining sprint days without weakening the engine ceilings.
> Companion to the `shipping-changes`, `codebase-docs`, and `building-and-testing` skills and
> `AGENTS.md`. Dated 2026-06-30.

## Problem (evidence, Day 1)

Day 1 produced **2 merged PRs** but **3 design specs about the workflow itself** (`repo-working-rules`,
`skills-optimization`, plus this conversation) and ~2,446 lines of project docs vs ~1,444 lines of our
code. Observed waste:

1. **Meta-work recursion** — process work begetting process work, eating the time meant for the
   irreversible critical path (Rust change + mobile build).
2. **Uniform ceremony** — `shipping-changes` mandates the *same* heavy path (new worktree + real PR +
   a **different** reviewer agent + docs-in-same-PR + SHA bump + `git submodule update --init
   --recursive`) for a one-line doc tweak as for a Rust engine change.
3. **Reviewer-agent + rebuild cost** — a separate reviewer in a *fresh worktree* per PR doubles
   sessions and implies recompiling Anki's Rust engine from zero each time.
4. **Stale progress tracking** — `execution-plan.md` checkboxes are all still unchecked though builds
   are done and 2 PRs merged; "what's actually done?" requires archaeology across specs/PRs/sessions.

## Goals / Non-Goals

**Goals:** give time back on the *majority* of remaining changes (non-engine) while keeping the full
armor on engine/Rust work; make "what's done" answerable in one place; stop the meta-recursion.

**Non-Goals:** rewriting the ~2,446 lines of docs into a single source of truth (itself meta-work);
weakening any hard ceiling; changing the engine-lane review at all.

## Fixes

### A. Change-risk tiers (the core change)

Split changes into two lanes in `shipping-changes`:

- **Engine lane** — touches `rslib/`, protobuf/`.proto`, `pylib` FFI, the `anki`/`Anki-Android`
  submodules, or anything affecting the scheduler/undo/collection store. **Unchanged:** worktree +
  real PR + **different-agent** review + extra gate + docs-in-same-PR + submodule init. The hard
  ceilings live here; this lane keeps its full armor.
- **Fast lane** — non-engine changes only: `pipeline/`, `eval/`, `docs/`, `.cursor/skills/`, deck
  content, Qt-UI-only tweaks. Relaxations: (1) **self-review** against a short checklist — no separate
  reviewer agent; (2) **worktree optional** — a dedicated branch in place is fine (worktrees exist for
  parallel-agent and engine-build isolation, neither of which a solo doc edit needs); (3) **skip
  `git submodule update --init --recursive`** — the change doesn't touch submodule code; (4) the
  brainstorm/spec gate collapses to a **2–3 sentence intent note in the PR body** instead of a full
  design doc.

Still required in the fast lane: a branch (never commit to `main`), a real PR, scoped-to-one-task,
relevant docs updated in the same PR. Lane is chosen by the "engine PR?" test already in
`pr-checklist.md`.

### B. Build cache + trust-green spot-check (engine lane)

In `building-and-testing`: (1) use a **shared Rust compile cache** (`sccache`, or a shared
`CARGO_TARGET_DIR`) so a reviewer's fresh worktree reuses build artifacts instead of compiling from
zero; (2) the engine-lane reviewer **trusts the builder's posted green** (CI / pasted `./ninja check`
output) and **spot-checks the ceiling items** (undo, no-corruption, read-only-invariant test) rather
than blindly rebuilding everything. Green must be *posted* to be trusted; if absent, reviewer rebuilds.

### C. One live status file

Add `docs/STATUS.md` — a single, short "what's actually done / in-flight / next" view (builds,
merged PRs, current branches). Rule added to `shipping-changes`: **merging a PR updates its line in
`docs/STATUS.md`** in the same merge. This is the authoritative progress view; `execution-plan.md`
stays the day-by-day plan. (Left `execution-plan.md` itself untouched here to avoid colliding with
in-flight uncommitted edits.)

### D. Process-freeze guardrail + cheap SSOT note

Add to `AGENTS.md`: **the workflow/process is frozen for the rest of the sprint** — no new
process/skills/working-rules specs unless something is *actively blocking a feature PR*. Plus a cheap
single-source-of-truth rule: when a fact (taxonomy, "no AI before Friday", ETS no-leak) is already in
the PRD, **link to it rather than restating it**.

## Files touched (all non-engine → fast lane)

- `.cursor/skills/shipping-changes/SKILL.md` — risk-tier overview + fast-lane role + merge-updates-STATUS.
- `.cursor/skills/shipping-changes/pr-checklist.md` — fast-lane self-review checklist + lane selector.
- `.cursor/skills/building-and-testing/SKILL.md` — compile-cache + trust-green spot-check section.
- `AGENTS.md` — tiers pointer, scale-the-gate guidance, process-freeze + link-don't-restate.
- `docs/STATUS.md` — new live status file.
- `docs/superpowers/specs/2026-06-30-workflow-tuning-design.md` — this spec.

## Acceptance

An agent making a non-engine change can self-review + ship via the fast lane (no reviewer agent, no
submodule init); engine changes still hit the full extra gate; `docs/STATUS.md` shows current state;
`AGENTS.md` freezes further process work. Shipped as one fast-lane PR, self-reviewed.

## Trade-offs (accepted)

- Fast-lane changes ship with **self-review only** — lower safety net on non-engine code, acceptable
  since it can't touch the collection or the ceilings.
- `sccache` setup costs ~20–30 min up front; pays back on the first reviewer rebuild (Wed + Fri both
  have engine PRs).
