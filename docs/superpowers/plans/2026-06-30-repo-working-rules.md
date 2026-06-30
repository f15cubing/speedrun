# Repo Working Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish multi-agent repo rules for the Anki fork — two project skills (a branch/PR/review workflow and a read-before/update-after docs discipline), an always-loaded `AGENTS.md`, a docs scaffold, and a queued post-clone documentation pass.

**Architecture:** Two thin *project* skills under `.cursor/skills/` orchestrate existing generic skills and add Anki-specific gates. `AGENTS.md` is the always-loaded enforcement layer that routes agents into the skills and surfaces hard ceilings. A `docs/codebase/` scaffold provides the central map + index, and `DOCUMENTATION-PASS.md` defines the first task to run after the fork is cloned.

**Tech Stack:** Cursor Agent Skills (`SKILL.md` + YAML frontmatter), Markdown, git worktrees, git submodules, GitHub CLI (`gh`).

## Global Constraints

- Skills are **project** skills under `.cursor/skills/<name>/`, auto-invocable (do **not** set `disable-model-invocation`).
- Skill `name`: lowercase letters/numbers/hyphens only. `description`: third person, starts with "Use when…", includes trigger keywords. `SKILL.md` body < 500 lines.
- Cross-reference other skills by **name only** with REQUIRED markers — never `@`-link (avoids force-loading context).
- Reviewer subagent MUST be a different agent than the builder. **Never self-merge.**
- Branch naming: `agent/<area>-<task>`. Every new worktree runs `git submodule update --init --recursive`.
- `speedrun/` is **not yet a git repo**, so tasks end with a **validation step, not a commit**. All files are committed together after `git init` (tracked as a final follow-up, out of scope for these tasks).
- Hard ceilings text (used verbatim in `AGENTS.md`, Task 4): real Rust change required; never corrupt the collection / break undo; never blend the three scores; no readiness number without the evidence panel; never reuse or leak ETS items; AGPL-3.0-or-later + credit Anki.

---

### Task 1: `codebase-docs` skill + templates

**Files:**
- Create: `.cursor/skills/codebase-docs/SKILL.md`
- Create: `.cursor/skills/codebase-docs/module-doc-template.md`
- Create: `.cursor/skills/codebase-docs/architecture-template.md`

**Interfaces:**
- Produces: the doc-location contract consumed by Task 2 (scaffold), Task 3 (reviewer's "docs updated" gate), Task 4 (`AGENTS.md` routing), Task 5 (doc pass). Canonical paths: central map `docs/codebase/architecture.md`, index `docs/codebase/INDEX.md`, co-located `<area>.md` inside code dirs. Each module doc ends with a `Last verified against: <commit SHA>` line.

- [ ] **Step 1: Write `module-doc-template.md` (verbatim content)**

```markdown
# <Area / Module Name>

> Co-located doc for `<relative/code/path/>`. Read this before changing anything here.

## Purpose
<What this module does, in 2-4 sentences. Why it exists.>

## Public interface
<The functions / types / protobuf messages / RPCs other code depends on. Signatures.>

## Dependencies
<What this module calls / imports, and what calls into it.>

## Gotchas & invariants
<Footguns, ordering requirements, things that must stay true (e.g. "read RPC must never return OpChanges").>

## Related tests
<Paths to the tests that cover this module.>

---
Last verified against: <commit SHA>
```

- [ ] **Step 2: Write `architecture-template.md` (verbatim content)**

```markdown
# <System> Architecture Map

## Big picture
<One paragraph: how the pieces fit together and the data flow.>

## Areas
| Area | Code path(s) | Doc | Owner agent | Last verified SHA |
|---|---|---|---|---|
| <e.g. Rust engine> | `rslib/` | `docs/codebase/rslib.md` | <agent> | <sha> |

## Cross-cutting concerns
<Build system, sync, FFI boundaries, protobuf, anything spanning areas.>
```

- [ ] **Step 3: Write `SKILL.md`** with frontmatter and these required sections:
  - Frontmatter: `name: codebase-docs`; `description: Use when about to read, modify, or add code in the Anki fork — explains where codebase documentation lives, how to find the docs relevant to the files you're touching, and the requirement to read them before changing code and update them afterward. Use when navigating an unfamiliar area, before editing any module, or when docs may be stale.`
  - `## Overview` — core principle: read the relevant doc before you change an area; update it in the same change; docs record the SHA they were verified against.
  - `## Where docs live` — central `docs/codebase/architecture.md` + `INDEX.md`; co-located `<area>.md` inside key dirs; a co-located doc is authoritative for its directory.
  - `## Find the relevant docs` — numbered: (1) open `docs/codebase/INDEX.md`; (2) map the files you'll touch → their doc(s); (3) prefer a co-located doc if present.
  - `## Read before you change (REQUIRED)` — read the area's doc(s) first; if none exists for an area you must change, create a stub from `module-doc-template.md` **in your PR**.
  - `## Update after you change (REQUIRED)` — any behavior/interface/layout change updates the doc(s) in the **same PR**; bump the `Last verified against` SHA. Note this is enforced by the reviewer base gate in the `shipping-changes` skill.
  - `## Templates` — point to `module-doc-template.md` and `architecture-template.md` (one level deep).
  - `## Red flags — STOP` — small table: "I'll update docs in a follow-up PR" → no, same PR; "This area has no doc so I'll skip" → create a stub; "I read the code, docs are optional" → read the doc, it carries invariants.

- [ ] **Step 4: Validate (dry-run subagent scenario)**

Dispatch a readonly `explore` subagent with: *"You must modify `rslib/src/scheduler/queue.rs` in this repo. Before reading the code, what does this project require you to do first? Answer using only the `codebase-docs` skill."*
Expected: it consults `docs/codebase/INDEX.md`, reads the relevant co-located/area doc first, notes it must create a stub if none exists, and commits to updating the doc in the same PR. If it skips reading docs first, tighten the "Read before you change" + Red flags wording and re-run.

- [ ] **Step 5: Lint check**

Run the linter on the three new files (markdown). Confirm `SKILL.md` body < 500 lines and frontmatter parses.

---

### Task 2: `docs/codebase/` scaffold (central map + index)

**Files:**
- Create: `docs/codebase/architecture.md`
- Create: `docs/codebase/INDEX.md`

**Interfaces:**
- Consumes: `architecture-template.md` structure from Task 1.
- Produces: the skeleton map + index that the documentation pass (Task 5) fills in and that `codebase-docs` (Task 1) points agents to.

- [ ] **Step 1: Write `architecture.md` skeleton**

Use the `architecture-template.md` shape. Include an `## Areas` table with one row per area, each `Doc`/`SHA` cell marked `TODO (documentation pass)`:

```markdown
# Anki Fork Architecture Map

> Skeleton. Fill during the documentation pass (see docs/codebase/DOCUMENTATION-PASS.md). Verify every path against the cloned source before trusting it.

## Big picture
TODO (documentation pass): how rslib ↔ pylib ↔ Qt UI ↔ rsdroid fit together; where our app code and scoring models attach.

## Areas
| Area | Code path(s) | Doc | Owner agent | Last verified SHA |
|---|---|---|---|---|
| Rust engine | `rslib/` | TODO | TODO | TODO |
| Python bindings | `pylib/` | TODO | TODO | TODO |
| Qt desktop UI | `qt/` | TODO | TODO | TODO |
| Android | `rsdroid/` (+ `anki` submodule) | TODO | TODO | TODO |
| Our app additions | TODO | TODO | TODO | TODO |
| Scoring models (memory/performance/readiness) | TODO | TODO | TODO | TODO |
| Sync | TODO | TODO | TODO | TODO |

## Cross-cutting concerns
TODO (documentation pass): build system, protobuf/RPC, FFI boundaries, undo/transaction model.
```

- [ ] **Step 2: Write `INDEX.md` skeleton**

```markdown
# Codebase Docs Index

> Map of area → doc file → code paths. Start here to find the docs relevant to files you're about to change. Filled by the documentation pass.

| Area | Doc file | Code paths | Last verified SHA |
|---|---|---|---|
| Rust engine | `docs/codebase/rslib.md` (TODO) | `rslib/` | TODO |
| Python bindings | `docs/codebase/pylib.md` (TODO) | `pylib/` | TODO |
| Qt desktop UI | `docs/codebase/qt.md` (TODO) | `qt/` | TODO |
| Android | `docs/codebase/rsdroid.md` (TODO) | `rsdroid/`, `anki/` | TODO |
| Our app additions | TODO | TODO | TODO |
| Scoring models | TODO | TODO | TODO |
| Sync | TODO | TODO | TODO |
```

- [ ] **Step 3: Validate (structural check)**

Read both files. Confirm: every area from the spec (rslib, pylib, qt, rsdroid, our app, scoring models, sync) appears in both tables; the `INDEX.md` has the columns area/doc file/code paths/SHA; the `architecture.md` matches the template sections.

---

### Task 3: `shipping-changes` skill + tiered checklist

**Files:**
- Create: `.cursor/skills/shipping-changes/SKILL.md`
- Create: `.cursor/skills/shipping-changes/pr-checklist.md`

**Interfaces:**
- Consumes: `codebase-docs` (read/update docs), and the doc-location contract from Task 1.
- Produces: the branch/PR/review/merge workflow referenced by `AGENTS.md` (Task 4) and the doc pass (Task 5). Defines branch naming `agent/<area>-<task>` and the reviewer-independence rule.

- [ ] **Step 1: Write `pr-checklist.md` (verbatim content)**

```markdown
# PR Checklist & Body Template

## When does the EXTRA gate apply?
A PR is an "engine/Rust PR" (extra gate required) if it touches any of: `rslib/`, the `anki`
submodule, protobuf/`.proto` definitions, FFI bindings in `pylib`, or anything affecting the
scheduler, undo, or the collection store. Everything else uses the base gate only.

## Base gate (every PR)
- [ ] Builds cleanly.
- [ ] Existing tests pass.
- [ ] New tests added for the change and pass.
- [ ] App runs (smoke check of the touched surface).
- [ ] Change is scoped to one task (no unrelated edits).
- [ ] Relevant docs updated in THIS PR; `Last verified against` SHA bumped.
- [ ] PR body complete (template below).

## Extra gate (engine/Rust PRs — in addition to base)
- [ ] Undo still works (manual + test).
- [ ] No collection corruption (round-trip / open-close verified).
- [ ] Read-only invariant test present and passing (read paths assert undo stack + queue counts unchanged).
- [ ] ≥3 Rust unit tests + ≥1 test calling the change from Python.
- [ ] Any new read RPC returns a plain response message — never `OpChanges`.
- [ ] "Files touched + merge-difficulty" note included in the PR body.

## PR body template
\`\`\`
## What & why
<one paragraph>

## Area(s) touched
<paths> — engine/Rust PR? yes/no

## Docs updated
<doc file(s) + new Last-verified SHA>

## Test evidence
<commands run + results>

## Engine/Rust extra gate (if applicable)
<undo proof, invariant test name, rust+python test names, files touched + merge difficulty>
\`\`\`
```

- [ ] **Step 2: Write `SKILL.md`** with frontmatter and these required sections:
  - Frontmatter: `name: shipping-changes`; `description: Use when making any code change in the Anki fork that will be merged — covers creating an isolated git worktree and branch, opening a real GitHub pull request, and having a different subagent verify it before merge. Use when starting a coding task, when about to commit/push/open a PR, or when reviewing another agent's PR.`
  - `## Overview` — every change ships via its own branch in a worktree, as a real `gh` PR, verified by a *different* agent; never self-merge.
  - `## Builder role` — numbered steps exactly matching spec §5 builder (fetch; worktree+branch `agent/<area>-<task>`; `git submodule update --init --recursive`; **invoke `codebase-docs` and read docs before editing**; make scoped change with TDD where it applies; update docs; verify build+tests locally; `gh pr create` with the template from `pr-checklist.md`; hand off; never self-merge).
  - `## Reviewer role` — numbered steps matching spec §5 reviewer (must be a different agent; `gh pr checkout` into a fresh worktree; run the tiered checklist from `pr-checklist.md`; comment via `gh`; approve/request changes; merge only when green+approved; squash; remove worktree + delete branch).
  - `## Composition` — REQUIRED references by name: `using-git-worktrees`, `dispatching-parallel-agents`, `requesting-code-review`, `receiving-code-review`, `verification-before-completion`, `finishing-a-development-branch`, `babysit`, `ci-investigator`. One line each on when to reach for it.
  - `## Red flags — STOP` — table: "I'll just commit to main" → no, branch+PR; "I'll review my own PR" → no, different agent; "tests are flaky, merge anyway" → no, use `ci-investigator`/`babysit`; "small change, skip the worktree" → no, worktree every time.
  - `## Checklist` — point to `pr-checklist.md` (one level deep).

- [ ] **Step 3: Validate — builder scenario (dry-run subagent)**

Dispatch a readonly subagent: *"You need to fix a typo in `pylib/anki/collection.py` in this repo and get it merged. Walk me through exactly what you do, using the `shipping-changes` skill."*
Expected: fetch → worktree + `agent/...` branch → submodule init → read docs first (codebase-docs) → make change → update docs → local build/tests → `gh pr create` → hand to a different reviewer → does NOT self-merge. Tighten wording + re-run if it self-merges or skips the worktree.

- [ ] **Step 4: Validate — reviewer scenario (dry-run subagent)**

Dispatch a readonly subagent: *"Another agent opened a PR adding a new read-only Rust RPC in `rslib/`. As the reviewer, what must you check before merge? Use the `shipping-changes` skill."*
Expected: identifies it as an engine/Rust PR → applies BOTH base + extra gates (undo, no corruption, read-only invariant test, ≥3 Rust + 1 Python test, no `OpChanges`, files-touched note) → blocks merge if any fail. Tighten if it applies only the base gate.

- [ ] **Step 5: Lint check**

Lint both files; confirm `SKILL.md` < 500 lines and frontmatter parses.

---

### Task 4: `AGENTS.md` (repo root)

**Files:**
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: skill names from Tasks 1 and 3; hard-ceilings text from Global Constraints.
- Produces: the always-loaded routing + rules layer.

- [ ] **Step 1: Write `AGENTS.md` (verbatim content)**

```markdown
# Working in this repo (agent rules)

This is a public AGPL-3.0-or-later fork of Anki for GRE Math prep. Orientation: read
`docs/PRD.md` (what/why) and `docs/project-spec.md` (the assignment). The Anki engine lives in
git submodule(s) — run `git submodule update --init --recursive` in every new worktree.

## Before you change code
Invoke the `codebase-docs` skill. Read the docs relevant to the files you'll touch BEFORE editing,
and update them in the SAME change. Start at `docs/codebase/INDEX.md`.

## To ship a change
Invoke the `shipping-changes` skill. Every change goes on its own branch in a git worktree, ships
as a real `gh` pull request, and is verified by a DIFFERENT agent. Never self-merge. Never commit
to `main` directly.

## Hard ceilings (do not violate)
- A real change inside Anki's Rust engine is required — not just Python/UI work.
- Never corrupt the collection or break undo. Read RPCs never return `OpChanges`.
- Never blend the three scores (memory / performance / readiness). Keep them separate, always with ranges.
- Never show a readiness number without the full evidence panel (estimate, range, % coverage,
  confidence, last-updated, reasons, best next step).
- Never reuse or leak official ETS items into training or evaluation.
- License: AGPL-3.0-or-later, credit Anki.
```

- [ ] **Step 2: Validate (structural check)**

Read `AGENTS.md`. Confirm it: references both skills by name, states reviewer independence + no self-merge, lists all six hard ceilings, and includes the submodule reminder.

---

### Task 5: `DOCUMENTATION-PASS.md` (first post-clone task)

**Files:**
- Create: `docs/codebase/DOCUMENTATION-PASS.md`

**Interfaces:**
- Consumes: `shipping-changes` (PRs), `codebase-docs` templates, the `INDEX.md`/`architecture.md` skeletons.
- Produces: the executable definition of the documentation sprint that must run before feature work.

- [ ] **Step 1: Write `DOCUMENTATION-PASS.md` (verbatim content)**

```markdown
# Documentation Pass — First Task After Cloning

**Run this BEFORE any feature work.** Goal: turn the `docs/codebase/` skeletons into real,
verified module docs so every later agent has docs to read before changing code.

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
```

- [ ] **Step 2: Validate (structural check)**

Read the file. Confirm it: gates before feature work, dispatches one subagent per area, routes through `shipping-changes` + `codebase-docs` templates, and has a concrete "done when" with no remaining TODO rows.

---

## Self-Review

**1. Spec coverage:**
- Spec §5 `shipping-changes` (builder+reviewer, tiered checklist, composition) → Task 3. ✓
- Spec §6 `codebase-docs` (find/read/update, templates, SHA, loop closure) → Task 1. ✓
- Spec §7 `AGENTS.md` → Task 4; docs scaffold → Task 2; documentation pass → Task 5. ✓
- Spec §8 testing (lightweight dry-run validation per skill) → Tasks 1.4, 3.3, 3.4. ✓
- Spec §3 decisions (worktrees, gh PRs, tiered gate, hybrid docs, project skills) → encoded across tasks + Global Constraints. ✓
- Spec §10 deferred (git init / clone, full pressure-testing) → Global Constraints note + spec; not in scope. ✓

**2. Placeholder scan:** The only `TODO` strings are *intentional skeleton content* inside the scaffold files (Tasks 2 & 5), which the documentation pass fills. No plan-level placeholders.

**3. Type consistency:** Skill names (`codebase-docs`, `shipping-changes`), canonical paths (`docs/codebase/INDEX.md`, `docs/codebase/architecture.md`, `<area>.md`), branch pattern (`agent/<area>-<task>`), the `Last verified against:` line, and the base/extra gate split are used identically across all tasks.
