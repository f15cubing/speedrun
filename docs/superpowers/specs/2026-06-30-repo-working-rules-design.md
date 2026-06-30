# Design Spec — Repo Working Rules for the Anki Fork

| Field | Value |
|---|---|
| Status | Draft for review |
| Date | 2026-06-30 |
| Topic | Multi-agent repo workflow + codebase documentation discipline |
| Related | `docs/PRD.md`, `docs/project-spec.md`, `research/brainlift.md` |

## 1. Context & Problem

`speedrun/` is a hackathon project to build a GRE Math study app on a public AGPL fork of
Anki — a large multi-language codebase (Rust engine `rslib`, Python bindings `pylib`, Qt UI,
Android `rsdroid` with `anki` as a submodule). Work is done by multiple Cursor agents
(an orchestrator + subagents). Today the workspace is **not yet a git repo** and the Anki
fork has not been cloned.

Two problems to solve:

1. **Safe parallel collaboration.** Multiple subagents editing one large codebase will collide,
   ship unreviewed changes, and break the engine (which carries hard grading ceilings — a real
   Rust change is required, the collection must never corrupt, undo must keep working).
2. **Navigability of a large unfamiliar codebase.** Agents need to understand "what everything
   does," read the relevant documentation *before* changing code, and keep that documentation
   current *after* changing it.

## 2. Goals / Non-Goals

**Goals**
- A subagent git workflow: each change goes on its own branch in an isolated worktree, ships as a
  real GitHub PR, and is verified by a *different* subagent before merge.
- A documentation system that makes the codebase navigable and enforces read-before-change /
  update-after discipline.
- Encode the project's hard ceilings so agents cannot violate them unknowingly.
- Compose existing generic skills rather than duplicating them.

**Non-Goals (this session)**
- Documenting Anki's real source (the fork isn't cloned yet) — instead we ship the *system* +
  skeletons + a queued post-clone documentation pass.
- Full RED-GREEN-REFACTOR pressure-testing of the skills (see §8 for honest scope).
- Initializing the outer git repo or cloning the fork (separate setup step).

## 3. Locked Decisions

| # | Decision | Choice |
|---|---|---|
| D1 | Git topology | `speedrun/` becomes our GitHub repo; Anki fork(s) are git submodule(s); all branches/PRs target the outer repo. |
| D2 | Parallel isolation | git worktrees — one isolated working directory + branch per subagent. |
| D3 | PR mechanism | real GitHub PRs via the `gh` CLI; merge only when green + approved. |
| D4 | Reviewer scope | tiered checklist — a base gate on every PR + an extra gate for engine/Rust PRs. |
| D5 | Docs structure | hybrid — central architecture map + index in `docs/codebase/`, plus co-located docs in key code dirs. |
| D6 | This-session scope | build the system (skills + `AGENTS.md` + templates + map skeleton) and queue a post-clone documentation pass. |
| D7 | Packaging | two focused project skills + `AGENTS.md` + docs scaffold (Approach A). |

## 4. Architecture (files created)

```
speedrun/
├─ AGENTS.md                         # always-loaded: hard rules + routes agents into the skills
├─ .cursor/skills/
│  ├─ shipping-changes/
│  │  ├─ SKILL.md                    # worktree → branch → PR → independent review → merge
│  │  └─ pr-checklist.md             # tiered checklist + PR-body template (heavy reference)
│  └─ codebase-docs/
│     ├─ SKILL.md                    # find/read docs before editing; update after
│     ├─ module-doc-template.md
│     └─ architecture-template.md
└─ docs/codebase/
   ├─ architecture.md                # central map skeleton
   ├─ INDEX.md                       # area → doc file → code paths → last-verified SHA
   └─ DOCUMENTATION-PASS.md          # first post-clone task definition
```

Skill names `shipping-changes` and `codebase-docs` are provisional and easy to rename.
Skills are **project** skills (`.cursor/skills/`) so they are committed to the repo and shared
with every agent. They are auto-invocable (no `disable-model-invocation`) and `AGENTS.md`
guarantees agents are told to use them.

## 5. Component — Skill `shipping-changes`

One workflow, two roles. The reviewer MUST be a different agent than the builder (no
self-approval, no self-merge).

### Builder subagent
1. `git fetch`; create a new branch off latest `main` **in a new git worktree**. Branch name
   `agent/<area>-<task>`. Run `git submodule update --init --recursive` in the new worktree.
2. **Before editing** → invoke `codebase-docs`; read the docs relevant to the area.
3. Make the change (TDD where it applies). Keep the PR small and scoped to one task.
4. **Update the relevant docs** as part of the same change.
5. Verify locally: build + run tests for the touched area before pushing.
6. Commit (conventional message) → push branch → `gh pr create` using the PR-body template.
7. Hand off to a reviewer subagent. **Never self-merge.**

### Reviewer subagent (different agent)
1. `gh pr checkout` into its own fresh worktree.
2. Run the tiered checklist (full text in `pr-checklist.md`):
   - **Base gate (every PR):** builds; existing + new tests pass; app runs; change scoped to the
     task; relevant docs updated; PR body complete.
   - **Extra gate (engine/Rust PRs):** undo still works; no collection corruption; read-only
     invariant test present + passing; ≥3 Rust unit tests + 1 Python-calling test; read RPC
     returns a plain response (never `OpChanges`); "files touched + merge-difficulty" note present.
3. Comment via `gh`; approve or request changes.
4. Merge only when green + approved → squash to `main` → remove worktree + delete branch.

### Composition
REQUIRED references (skill name only, no force-load): `using-git-worktrees` (isolation),
`dispatching-parallel-agents` (when fanning out), `requesting-code-review` /
`receiving-code-review` (the review exchange), `verification-before-completion` (before claiming
green), `finishing-a-development-branch` (merge/cleanup), Cursor `babysit` (keep a PR
merge-ready), `ci-investigator` (failing checks).

## 6. Component — Skill `codebase-docs`

- **Where docs live:** central `docs/codebase/architecture.md` + `INDEX.md`, plus co-located
  `<area>.md` / `AGENTS.md` inside key code dirs.
- **Find:** start at `INDEX.md`; map the files you're about to touch → their doc(s). A co-located
  doc is authoritative for that directory.
- **Read-before-change (REQUIRED):** read the area's doc(s) before editing. If no doc exists for
  an area you must change, create a stub from `module-doc-template.md` in your PR.
- **Update-after (REQUIRED):** any change to behavior, interfaces, or file layout updates the
  corresponding doc(s) **in the same PR**. Each doc records the **commit SHA it was last verified
  against** so staleness is detectable.
- **Loop closure:** "docs updated" is a base-gate item the reviewer enforces in `shipping-changes`.

Templates shipped: `module-doc-template.md` (purpose, public interface, dependencies, gotchas,
related tests, last-verified SHA) and `architecture-template.md`.

## 7. Components — `AGENTS.md` + docs scaffold + documentation pass

**`AGENTS.md` (repo root, short, always loaded):** project orientation + pointers to
`docs/PRD.md` / `docs/project-spec.md`; "before you change code → `codebase-docs`"; "to ship a
change → `shipping-changes`, independent reviewer, never self-merge"; submodule reminder; and the
spec's hard ceilings (real Rust change required; never corrupt the collection / break undo; never
blend the three scores; no readiness number without the evidence panel; never reuse/leak ETS
items; AGPL-3.0 + credit Anki).

**docs/ scaffold:** `architecture.md` and `INDEX.md` ship as skeletons (sections per area:
`rslib`/Rust engine, `pylib` bindings, Qt UI, `rsdroid`/Android, our app additions, scoring
models, sync), each marked "TODO: fill during documentation pass; verify against cloned source."

**Documentation pass (`DOCUMENTATION-PASS.md`):** the first post-clone task — after cloning the
fork + submodules, dispatch parallel subagents (one per area) to map real files, fill module docs
from the template, verify against source, record the SHA, and open PRs via `shipping-changes`.
Gated *before* feature work so agents have docs to read.

## 8. Testing Approach (honest scope)

`writing-skills` requires testing skills with subagent pressure scenarios before deployment. Given
the hackathon timeline and that the fork isn't cloned, this session does **lightweight validation**:
for each skill, a single dry-run subagent scenario (e.g., "make a small change") checking that the
agent (a) creates a worktree + branch, (b) reads docs first, (c) opens a PR, (d) does not
self-merge; plus a reviewer scenario. Fuller pressure-testing (multiple combined pressures,
rationalization-table hardening) is flagged as a follow-up. We will not claim more testing than was
performed.

## 9. Success Criteria

- An agent asked to change code creates a worktree + branch, reads relevant docs first, updates
  docs, opens a real `gh` PR, and does not self-merge.
- A reviewer agent checks out the PR, runs the correct tier of the checklist, and blocks merge when
  red.
- `AGENTS.md` surfaces the hard ceilings and routes to both skills.
- The docs scaffold + documentation-pass task are in place for execution right after the fork is
  cloned.

## 10. Deferred / Open

- Initializing the outer git repo and cloning the fork (prerequisite for actually running the
  workflow) — separate setup step; spec "commit" is deferred until then.
- Full pressure-testing of the skills (§8).
- Whether the documentation pass content lives in `DOCUMENTATION-PASS.md` or folds into a broader
  execution plan.
