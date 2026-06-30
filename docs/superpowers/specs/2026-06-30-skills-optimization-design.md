# Design — optimize project skills for this workflow

**Date:** 2026-06-30
**Status:** implemented (scope = both; rigor = pragmatic; build commands sourced from upstream,
marked unverified-on-this-machine). Verified by a read-only subagent retrieval check — both new
skills were discovered by search alone and the commands/steps extracted correctly.

## Context

The repo ships two project skills: `codebase-docs` (read/update area docs, SHA-stamped) and
`shipping-changes` (worktree → PR → different-agent review, base + engine extra gate). Both are
solid. Gap analysis against this fork's real workflow surfaced missing *workflow techniques* and a
boundary question (skill vs. instructions file).

## Decisions

- **Two new skills** (workflow techniques, broadly reusable here):
  - `building-and-testing` — canonical build/run/test commands for desktop (Qt), Android
    (AnkiDroid), and the Rust engine. Sourced from `anki/docs/development.md` (`anki@25.09.4`
    `d52ca66`) and AnkiDroid `.github/workflows/README.md` (`Anki-Android@v2.24.0` `ebcf8e0`),
    explicitly marked **not yet verified on this machine**; kept current like a codebase doc.
  - `working-with-submodules` — recursive init (rsdroid vendors `anki`), bump-a-pin-and-its-doc-SHA
    together, never commit inside a submodule, detached-HEAD recovery.
- **Three edits:**
  - `shipping-changes` — point the build/test gate at `building-and-testing` and the submodule step
    at `working-with-submodules`; add an engine/RPC pointer to the `proto-rpc.md`/`rslib.md`/
    `pylib.md` insertion-point sections.
  - `codebase-docs` — bumping a submodule pin must bump every doc's `Last verified against:` SHA in
    the same change.
  - `AGENTS.md` — reinforce product invariants as a checkable list and add the two new skills to the
    workflow pointers.
- **Not a skill:** product invariants (3-score separation + ranges, readiness evidence panel/give-up
  gate, ETS no-leak, undo/no-corruption). Per `writing-skills`, project-specific conventions live in
  the instructions file (`AGENTS.md`), where they already are — reinforced, not duplicated.
- **Not building** a standalone engine-RPC skill — it would duplicate existing codebase docs; a
  cross-reference suffices.

## Verification (pragmatic)

Each new skill gets a read-through plus one subagent retrieval check ("given task X, find and apply
the right commands/steps"). No full `writing-skills` pressure-test ceremony (overridden by the
solo-speedrun rigor choice). Build commands stay marked unverified until actually run on a machine.

## Out of scope

Actually running the builds; turning the invariants into skills; engine-RPC skill.
