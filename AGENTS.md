# Working in this repo (agent rules)

This is a public AGPL-3.0-or-later fork of Anki for GRE Math prep. Orientation: read
`docs/PRD.md` (what/why) and `docs/project-spec.md` (the assignment). The Anki engine lives in
git submodule(s) — run `git submodule update --init --recursive` in every engine-lane worktree (see
the `working-with-submodules` skill; the fast lane below skips it).

## Before you change code
Invoke the `codebase-docs` skill. Read the docs relevant to the files you'll touch BEFORE editing,
and update them in the SAME change. Start at `docs/codebase/INDEX.md`.

## To ship a change
Invoke the `shipping-changes` skill. Every change goes on a branch and ships as a real `gh` pull
request — never commit to `main` directly. Ceremony scales with the **change-risk tier**:
- **Engine lane** (`rslib/`, `.proto`, `pylib` FFI, submodules, scheduler/undo/store): worktree +
  submodule init + extra gate + verified by a **DIFFERENT agent**. Never self-merge.
- **Fast lane** (non-engine: `pipeline/`, `eval/`, `docs/`, `.cursor/skills/`, deck content,
  Qt-UI-only): worktree optional, skip submodule init, **self-review** against the fast-lane
  checklist, design gate is a 2–3 sentence PR intent note. When in doubt, use the engine lane.

Current state lives in `docs/STATUS.md`; every merge updates its line there.

## Build, test, submodules
For build/run/test commands on any surface (desktop, Android, Rust engine), use the
`building-and-testing` skill. For initializing, pinning, or bumping the `anki` / `Anki-Android`
submodules, use the `working-with-submodules` skill.

## Keep the process lean
- **Process is frozen for the rest of the sprint.** Do not write new process / skills /
  working-rules design specs unless something is *actively blocking a feature PR*. Build the
  product, not the workflow.
- **Link, don't restate.** When a fact already lives in the PRD (taxonomy, "no AI before Friday",
  ETS no-leak, the three scores), reference it — don't copy it into another doc.

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
