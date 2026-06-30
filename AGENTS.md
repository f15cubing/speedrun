# Working in this repo (agent rules)

This is a public AGPL-3.0-or-later fork of Anki for GRE Math prep. Orientation: read
`docs/PRD.md` (what/why) and `docs/project-spec.md` (the assignment). The Anki engine lives in
git submodule(s) — run `git submodule update --init --recursive` in every new worktree (see the
`working-with-submodules` skill).

## Before you change code
Invoke the `codebase-docs` skill. Read the docs relevant to the files you'll touch BEFORE editing,
and update them in the SAME change. Start at `docs/codebase/INDEX.md`.

## To ship a change
Invoke the `shipping-changes` skill. Every change goes on its own branch in a git worktree, ships
as a real `gh` pull request, and is verified by a DIFFERENT agent. Never self-merge. Never commit
to `main` directly.

## Build, test, submodules
For build/run/test commands on any surface (desktop, Android, Rust engine), use the
`building-and-testing` skill. For initializing, pinning, or bumping the `anki` / `Anki-Android`
submodules, use the `working-with-submodules` skill.

## Hard ceilings (do not violate)
- A real change inside Anki's Rust engine is required — not just Python/UI work.
- Never corrupt the collection or break undo. Read RPCs never return `OpChanges`.
- Never blend the three scores (memory / performance / readiness). Keep them separate, always with ranges.
- Never show a readiness number without the full evidence panel (estimate, range, % coverage,
  confidence, last-updated, reasons, best next step).
- Never reuse or leak official ETS items into training or evaluation.
- License: AGPL-3.0-or-later, credit Anki.

These ceilings are checked by the `shipping-changes` engine extra gate
(`.cursor/skills/shipping-changes/pr-checklist.md`).
