# Documentation Pass — First Task After Cloning

**Run this BEFORE any feature work.** Goal: turn the `docs/codebase/` skeletons into real,
verified module docs so every later agent has docs to read before changing code.

> **Status (2026-06-30):** the pass is **done for the built areas** — `architecture.md` (big
> picture + 6 mermaid diagrams + cross-cutting) and verified module docs for `rslib`, the
> `proto`/RPC boundary, `pylib`, `qt`, and `rsdroid` (see `INDEX.md`). This initial pass was a
> **single bootstrap pass** (committed directly while standing the repo up), not the
> parallel-subagent + worktree + PR flow below. The repo is now git-initialized with `anki` /
> `Anki-Android` as submodules and pushed to `f15cubing/speedrun`, so **from the first real code
> change onward, follow `shipping-changes` (worktree + branch + PR + different-agent review).** The
> remaining areas (mastery query, scoring models, sync conflict, AI) are **not built yet** and are
> listed as *planned* in `INDEX.md`; each gets its module doc in the PR that first builds it.

## Prerequisites
- Outer repo initialized; Anki fork(s) added as submodule(s); `git submodule update --init --recursive` done.

## Dispatch (parallel)
Use `dispatching-parallel-agents`. Dispatch ONE subagent per area from `docs/codebase/INDEX.md`
(rslib, pylib, qt, rsdroid, our app, scoring models, sync). Each subagent:
1. Uses `shipping-changes` (worktree + branch + PR).
2. Maps the area's real files against the cloned source.
3. Writes `docs/codebase/<area>.md` from `module-doc-template.md` (purpose, public interface,
   dependencies, gotchas/invariants, related tests).
4. Records the commit SHA in `Last verified against:` and updates the row in `INDEX.md` +
   `architecture.md`.
5. Opens a PR; a DIFFERENT agent reviews it against the base gate.

## Done when
- Every area in `INDEX.md` has a verified doc with a real SHA (no remaining `TODO` rows).
- `architecture.md` "Big picture" + "Cross-cutting concerns" are filled and verified.
