# Agent Workflow Starter Kit

> **What this is.** A portable guide for standing up the multi-agent development workflow used in
> this repo (`speedrun/`, a large Anki fork built by Cursor agents) inside a **new** project. It is
> written to be handed to an agent on Day 1 of that project. It tells you what to build, in what
> order, why each piece exists, and — critically — **what to take as-is, what to adapt, and what to
> leave behind.**
>
> **How it was produced.** By reading this repo's skills (`.cursor/skills/`), the generic
> "superpowers" skills, `AGENTS.md`, the `docs/` system, and the design specs + overnight logs that
> record how the workflow actually behaved under load. The evaluation below is opinionated on
> purpose: it front-loads the lessons this project only learned mid-sprint.
>
> **How to read it.** §1–2 are the mental model. **§3 is the take/adapt/drop verdict** (the heart of
> it). §4 is the build order. §5 has ready-to-adapt templates. §6 is the hard-won lessons. §7 is a
> minimal Day-1 subset if you don't want the whole thing.

---

## 0. Adapt this to your project first

This guide is deliberately conditional — the right subset depends on three questions. Answer them
before you build anything; every later section refers back to them.

| Question | If **yes / large** | If **no / small** |
|---|---|---|
| **A. Large or unfamiliar codebase?** (you'll edit code you didn't write) | Build `codebase-docs` + the `docs/codebase/` map. | Skip it; a short README is enough. |
| **B. Multiple agents / parallel work?** | Build worktrees + `dispatching-parallel-agents` + independent review. | Single-branch, self-review is fine. |
| **C. A "blast radius" core that must never break?** (engine, migrations, auth, billing, a public API) | Keep the **engine lane** with its extra gate + different-agent review. | Everything is "fast lane"; one gate. |

The system in this repo answers **yes/yes/yes**. Most new projects answer at least one **no** — so
**do not clone the whole thing.** Take the spine (§7), add the parts your answers demand.

---

## 1. The mental model: three layers

The workflow is not one thing. It's three cooperating layers, and keeping them separate is the
single most reusable idea here.

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 3 — INSTRUCTION FILE (AGENTS.md, always loaded)                 │
│   Hard ceilings ("never do X"), product invariants, and ROUTES into   │
│   the skills. Short. The only thing guaranteed in every agent's       │
│   context. Says WHAT MUST HOLD and WHERE TO LOOK — not how.            │
└─────────────────────────────────────────────────────────────────────┘
            │ routes to
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 2 — PROJECT SKILLS (.cursor/skills/, committed to the repo)     │
│   Project-shaped procedures every agent shares: how we ship a change, │
│   how we read/update docs, how we build & test, submodule mechanics.  │
│   Compose Layer 1; don't duplicate it.                                │
└─────────────────────────────────────────────────────────────────────┘
            │ composes / references by name
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 1 — GENERIC WORKFLOW SKILLS ("superpowers", user-level)         │
│   Reusable across all projects: brainstorming, writing-plans,         │
│   TDD, verification-before-completion, worktrees, code review,        │
│   subagent-driven execution, writing-skills.                          │
└─────────────────────────────────────────────────────────────────────┘
```

**Why the separation matters:** Layer 1 is portable and you rarely rewrite it. Layer 2 is where a
project's real conventions live (build commands, risk tiers, doc locations). Layer 3 is the tiny
always-on contract. When people conflate them — e.g. putting build commands in `AGENTS.md`, or
baking product rules into a generic skill — the instruction file bloats, skills stop being portable,
and agents can't tell a hard rule from a suggestion.

**The golden boundary rule** (from the `writing-skills` skill): *project-specific conventions go in
the instruction file; broadly-reusable techniques go in skills; mechanical constraints get
automated, not documented.* Follow it and you'll rarely be confused about where something belongs.

---

## 2. The core flow (what an agent actually does)

```
        IDEA
         │  superpowers:brainstorming   (design → docs/…/specs/DATE-topic.md, user-approved)
         ▼
        SPEC
         │  superpowers:writing-plans   (bite-sized TDD tasks → docs/…/plans/DATE-feature.md)
         ▼
        PLAN
         │  subagent-driven-development / executing-plans
         │    per task: fresh subagent → TDD (RED→GREEN→REFACTOR) → self-review → task review
         ▼
        CHANGE  (on a branch, in a worktree)
         │  PROJECT skill: shipping-changes
         │    pick a risk tier → build & test (building-and-testing) → verify (no false green)
         │    → open a real PR → review (self or different-agent by tier) → merge
         ▼
        MERGED  → update STATUS.md line in the same merge
```

Cross-cutting disciplines ride along the whole flow:

- **`codebase-docs`** — read the area's doc *before* editing; update it *in the same change*; stamp
  the commit SHA it was verified against so staleness is detectable.
- **`test-driven-development`** — no production code without a failing test first.
- **`verification-before-completion`** — never claim "done/passing/fixed" without fresh command
  output in the same message.
- **`systematic-debugging`** — root cause before fix, when something breaks.

The whole thing is **ceremony that scales with risk** (see §3.1). That is the design's best trait,
and it was *not* there on Day 1 — it was retrofitted after the process ate the schedule (§6).

---

## 3. The verdict: take / adapt / drop

### 3.1 TAKE — port these almost verbatim (highest value, most portable)

| Thing | Why it's worth taking | Porting note |
|---|---|---|
| **Change-risk tiers** in the ship workflow (an "engine/high-risk lane" vs a "fast lane") | The single best idea here. One heavy path for everything is what made Day 1 slow; one light path for everything is unsafe. Tiering gives time back on the 80% of low-risk changes while keeping full armor on the dangerous 20%. | Rename "engine lane" to your blast-radius core (migrations, auth, public API, payments). Keep the rule **"when in doubt, high-risk lane."** |
| **A tiny, always-loaded instruction file** (`AGENTS.md`) with **hard ceilings + skill routing** | Gives every agent the non-negotiables and a map, in the one place that's always in context. | Keep it under ~1 page. Ceilings must be *checkable*, not vibes. |
| **`STATUS.md` — one live "what's actually done" file, updated on every merge** | Kills "what's the real state?" archaeology across PRs/branches/chats. The merge-updates-STATUS rule is what keeps it honest. | Make updating it part of the merge step, not a separate chore. |
| **`codebase-docs` discipline: read-before-change, update-after, SHA-stamped, INDEX + co-located docs** | For a large/unfamiliar codebase this is the difference between confident edits and blind ones. The SHA stamp makes staleness *detectable* instead of silent. | Only if Question A = large (§0). For small projects it's overkill. |
| **`building-and-testing` as a skill, treated like a doc** with a "verified / not-yet-verified on this machine" marker | Stops every agent from re-discovering the toolchain. The provenance marker is honest about what's actually been run. | See the improvement in §3.3 — resolve "unverified" *fast*, don't let it linger a whole project. |
| **The brainstorm → plan → execute pipeline with dated artifacts** (`specs/DATE-topic.md`, `plans/DATE-feature.md`) | Forces a design gate before code and leaves a durable trail. Dated filenames make history skimmable. | For tiny changes this collapses to a 2–3 sentence intent note in the PR (see fast lane). Don't spec a one-liner. |
| **TDD + verification-before-completion as iron laws** | These are the quality floor. "Evidence before claims" alone prevents the most common agent failure (confident false "done"). | Non-negotiable regardless of project size. |
| **Worktrees for isolation + parallel agents** | Lets independent changes proceed without collisions and lets a reviewer check out a PR without disturbing the builder. | Only if Question B = multiple agents. Prefer your harness's native worktree tool over raw `git worktree`. |
| **"Trust posted green + spot-check" for expensive verification** | When a build/test cycle is slow, a reviewer re-running everything from zero doubles cost. Trust the builder's *posted* green output; independently re-check only the ceiling items. | Pair with a shared compile cache (`sccache` / shared target dir) so fresh worktrees don't recompile the world. |
| **Green-or-revert; never self-merge a high-risk change** | Keeps `main` always shippable and puts a second set of eyes on the dangerous stuff. | In a solo context the "different agent" is a fresh review subagent — still valuable, still cheap. |

### 3.2 ADAPT — take the shape, change the contents

| Thing | Keep the shape | Change |
|---|---|---|
| **The hard ceilings in `AGENTS.md`** | The *format*: a short list of checkable "never" rules with the consequence of violating each. | The *contents*. This repo's ceilings ("never corrupt the collection", "never blend the three scores", "no readiness number without the evidence panel", "never leak ETS items") are 100% product-specific. Write **your** project's ceilings — or, if you have none, don't invent ceremony. |
| **`subagent-driven-development` with its file-handoff machinery** (task-brief / review-package scripts, progress ledger) | The pattern: fresh subagent per task, review between tasks, artifacts passed as files not pasted text. | The heaviness. The full ledger + scripts pay off at high subagent volume; for a handful of tasks, a lighter loop (dispatch → review → next) is enough. Scale to your volume. |
| **The `docs/` taxonomy** (`PRD` / `project-spec` / `execution-plan` / `codebase/` / `superpowers/specs|plans` / `evidence` / `models`) | The idea of **separate files for separate jobs**: what/why vs when vs current-state vs code-map vs design trail vs proof. | The exact set. A greenfield product needs a `PRD`; an internal tool might need only a `README` + `STATUS.md` + `docs/codebase/`. Take the ones your project earns. |
| **`working-with-submodules`** | Only relevant if you vendor other repos. | Drop entirely unless you actually use submodules. If you do, keep the two rules that matter: never commit *inside* a submodule from the outer repo, and bump the pin's doc SHA in the same change. |
| **The PR body template + tiered checklist** | Having a template at all — it makes reviews uniform and self-review meaningful. | Trim to your gates. The engine "extra gate" here (undo works, no corruption, read-only invariant test, ≥3 Rust + 1 Python test, "never returns OpChanges") is Anki-specific. Replace with your core's invariants. |

### 3.3 DROP or FIX — don't inherit these

| Thing | Why not | Do instead |
|---|---|---|
| **Day-1 heavy uniform ceremony** | This repo's Day 1 produced **3 design specs about the workflow itself and ~2,446 lines of process docs against ~1,444 lines of actual code** before tiers existed. That's the meta-work recursion trap. | Adopt the *tuned* end-state on Day 1: tiers + process-freeze from the start (§6). This guide *is* that shortcut. |
| **Writing process-about-process specs mid-project** | Same trap, later. Process work begets process work and eats the critical path. | Bake in a **process freeze**: no new skills/working-rules/process specs unless something is *actively blocking a feature*. Build the product, not the workflow. |
| **Unbounded append-only `STATUS.md` / duplicated `INDEX.md`** | The live files here have grown very long, and the codebase `INDEX.md` accumulated literal duplicate rows. A status file nobody can skim stops being a status file. | Cap them. Keep `STATUS.md` to *in-flight + recent*; roll older entries into a `CHANGELOG`. Add a cheap check that flags duplicate INDEX rows and stale SHAs. |
| **Letting "not yet verified on this machine" linger** | The build commands shipped marked unverified and stayed that way — useful honesty, but a smell if it never resolves. | Resolve it in the first build: run each command once, mark it verified or fix it. Treat "unverified" as a Day-1 todo, not a permanent disclaimer. |
| **Mechanical rules enforced by discipline alone** | "Update the SHA", "add a STATUS line", "don't leave a duplicate row" are all things agents forget under pressure. `writing-skills` itself says: if it's enforceable by regex/validation, automate it. | Write a tiny CI/pre-commit check for each mechanical invariant. Save the prose skills for judgment calls. |
| **Copying the product ceilings verbatim** | They only make sense for a GRE/Anki app. | Delete them; write your own (or none). |
| **Over-indexing on "different-agent review" for trivial changes** | Ceremony on a doc typo is waste. | Different-agent review is for the high-risk lane only; fast-lane self-review is explicitly enough here, and it should be for you too. |

---

## 4. Build order (the Day-1 checklist)

Do these in order. Each is small. Stop when your §0 answers say the rest isn't earned.

- [ ] **1. Instruction file.** Create `AGENTS.md` at the repo root (template §5.1). Fill in: 3-line
      orientation, your hard ceilings (or "none yet"), and routing to the skills you're about to
      build. Keep it to one page.
- [ ] **2. Ship skill.** Create `.cursor/skills/shipping-changes/SKILL.md` (template §5.2) with your
      two tiers and a `pr-checklist.md`. Define the "high-risk PR?" test in one sentence.
- [ ] **3. Build/test skill.** Create `.cursor/skills/building-and-testing/SKILL.md` (template §5.4)
      with your real build/run/test commands. Run each once; mark verified.
- [ ] **4. Status file.** Create `docs/STATUS.md` (template §5.5): Done / In-flight / Next. Add the
      "merging updates STATUS" line to the ship skill.
- [ ] **5. (If Question A = large) Codebase docs.** Create `.cursor/skills/codebase-docs/SKILL.md`
      (template §5.3) + `docs/codebase/INDEX.md` + a `module-doc-template.md`. Seed INDEX with the
      areas you already know.
- [ ] **6. (If Question B = multiple agents) Isolation.** Confirm worktrees work in your harness;
      note the native tool in the ship skill. Otherwise skip.
- [ ] **7. Confirm the generic skills are available.** brainstorming, writing-plans, TDD,
      verification-before-completion, code review, subagent-driven-development. If your runtime
      doesn't ship them, that's a one-time install — don't rewrite them per project.
- [ ] **8. Automate one mechanical check** (§3.3): e.g. a pre-commit hook that fails if a PR changes
      code under `docs/codebase/`-mapped paths without touching its doc. Start small.
- [ ] **9. Freeze the process.** Add the process-freeze line to `AGENTS.md`. You're done building
      workflow; go build the product.

---

## 5. Ready-to-adapt templates

These are generalized from this repo's real files. Replace `<ANGLE BRACKETS>`. Keep them short.

### 5.1 `AGENTS.md`

```markdown
# Working in this repo (agent rules)

<ONE-PARAGRAPH ORIENTATION: what this project is, and the two docs to read first —
e.g. docs/PRD.md (what/why) and docs/STATUS.md (current state).>

## Before you change code
Invoke the `codebase-docs` skill. Read the doc for the area you'll touch BEFORE editing, and
update it in the SAME change.   <-- delete this section if you skipped codebase-docs>

## To ship a change
Invoke the `shipping-changes` skill. Every change goes on a branch and ships as a real pull
request — never commit to `main`. Ceremony scales with the change-risk tier:
- **High-risk lane** (<YOUR BLAST-RADIUS CORE: e.g. migrations / auth / public API>): worktree +
  extra gate + review by a DIFFERENT agent. Never self-merge.
- **Fast lane** (everything else): self-review against the fast-lane checklist; design gate is a
  2–3 sentence intent note in the PR body. When in doubt, use the high-risk lane.

## Build, test
Use the `building-and-testing` skill for all build/run/test commands.

## Keep the process lean
- **Process is frozen.** Do not write new skills / process / working-rules specs unless something
  is actively blocking a feature. Build the product, not the workflow.
- **Link, don't restate.** If a fact already lives in <PRD/spec>, reference it — don't copy it.

## Hard ceilings (do not violate)
<LIST YOUR CHECKABLE "NEVER" RULES + the consequence of each. Examples of the FORM:
- Never <corrupt/lose user data> — <how it's checked>.
- Never <ship without test X>.
If you have no real ceilings yet, write "None beyond the standard gates." Do not invent ceremony.>
```

### 5.2 `.cursor/skills/shipping-changes/SKILL.md`

```markdown
---
name: shipping-changes
description: Use when making any code change that will merge, when about to commit/push or open a
  pull request, or when reviewing another agent's PR.
---

# Shipping Changes

Every change ships on a branch (never `main`) as a real pull request. Ceremony rides on the
change-risk tier.

## Which lane? (the high-risk test)
A PR is **high-risk** if it touches <YOUR CORE: schema/migrations, auth, the public API,
money paths, the shared engine>. Everything else is **fast lane**. When in doubt → high-risk.

## Fast lane (most changes)
1. Branch `agent/<area>-<task>` off latest `main` (worktree optional).
2. Read the relevant docs; make the change, scoped to ONE task; TDD where it applies.
3. Update docs in the same change.
4. Verify what's verifiable (tests/lint for touched files) — use `verification-before-completion`.
5. Open a PR; the design gate is a 2–3 sentence intent note in the body.
6. Self-review against `pr-checklist.md`; merge; update `docs/STATUS.md` in the same merge.

## High-risk lane
Same as fast lane, plus: worktree required; the **extra gate** in `pr-checklist.md`; and a
**different agent** reviews and merges. NEVER self-merge. Trust the builder's posted green output
and spot-check the ceiling items rather than rebuilding blind.

## Compose (reference by name, don't duplicate)
`building-and-testing`, `using-git-worktrees`, `verification-before-completion`,
`requesting-code-review` / `receiving-code-review`, `finishing-a-development-branch`.

## Red flags — STOP
| Thought | Reality |
|---|---|
| "I'll commit straight to main." | No — branch + PR, always. |
| "I'll self-review my high-risk change." | No — different agent. |
| "It's a small tweak but it touches <core>." | Then it's high-risk. When in doubt, high-risk. |
| "Fast lane, so skip the PR / skip docs." | No — still a real PR, scoped, docs in the same PR, STATUS line. |
```

And a `pr-checklist.md` beside it:

```markdown
# PR Checklist & Body Template

## Fast-lane self-review
- [ ] Non-<core> and scoped to one task.
- [ ] On a branch + real PR (never committed to main).
- [ ] Verifiable things verified (tests/lint); result noted in the PR body.
- [ ] UI-facing? Actually opened the surface and confirmed it works end-to-end (unit tests bypass it).
- [ ] Relevant docs updated in THIS PR.
- [ ] On merge, docs/STATUS.md line updated.

## Extra gate (high-risk PRs, in addition)
- [ ] <YOUR CORE INVARIANTS as checkable items — e.g. migration is reversible; no data loss on
      round-trip; the read path has an invariant test; N unit tests + 1 integration test.>
- [ ] "Files touched + merge-difficulty" note in the body.

## PR body template
## What & why  <one paragraph; fast-lane = the 2–3 sentence intent note>
## Area(s) touched  <paths> — high-risk? yes/no
## Docs updated  <files>
## Test evidence  <commands run + results>
## Extra gate (if applicable)  <invariant proof + test names — or N/A>
```

### 5.3 `.cursor/skills/codebase-docs/SKILL.md`  *(only if Question A = large)*

```markdown
---
name: codebase-docs
description: Use when about to read, modify, or add code anywhere in this codebase — before editing
  any module, when navigating an unfamiliar area, or when docs may be stale.
---

# Codebase Docs

Read the doc for an area before you change it, and update that doc in the same change. Docs record
the commit SHA they were last verified against, so staleness is detectable. Never edit blind.

## Where docs live
- Index: `docs/codebase/INDEX.md` — area → doc file → code paths → last-verified SHA. Start here.
- Co-located `<area>.md` inside key code dirs is authoritative for that dir.

## The loop (both REQUIRED)
1. Before editing: map the files you'll touch → their doc(s) via INDEX; read them (they carry
   invariants the code doesn't state). No doc? Create a stub from `module-doc-template.md` in your PR.
2. After changing behavior/interface/layout: update the doc(s) in the SAME PR; bump the
   `Last verified against:` SHA. The reviewer enforces "docs updated" as a gate.

## Red flags — STOP
| Thought | Reality |
|---|---|
| "I'll update docs in a follow-up PR." | No — same PR. |
| "No doc here, so skip docs." | No — create a stub from the template. |
| "I read the code, the doc is optional." | No — the doc carries invariants the code doesn't. |
```

Plus `module-doc-template.md`:

```markdown
# <Area / Module Name>
> Co-located doc for `<relative/code/path/>`. Read before changing anything here.

## Purpose
<What this does, 2–4 sentences. Why it exists.>
## Public interface
<Functions / types / endpoints other code depends on. Signatures.>
## Dependencies
<What it calls, and what calls into it.>
## Gotchas & invariants
<Footguns, ordering, things that must stay true.>
## Related tests
<Paths to covering tests.>

---
Last verified against: <commit SHA>
```

### 5.4 `.cursor/skills/building-and-testing/SKILL.md`

```markdown
---
name: building-and-testing
description: Use when you need to build, run, or test any surface of this project — to satisfy a
  PR's build/test gate or to get a clean baseline.
---

# Building and Testing

Canonical commands. Treat this like a codebase doc: the first time you run a command and confirm it,
mark it **verified**; if one is wrong, fix it here in the same change.

## <Surface / package name>
One-time setup: <...>

| Goal | Command |
|---|---|
| Build + run | `<...>` |
| Run all tests | `<...>` |
| Run a subset | `<...>` |
| Lint / format | `<...>` |

> Status: <verified on this machine YYYY-MM-DD | NOT yet verified — resolve on first run>.

## Don't recompile from zero (if builds are slow)
Use a shared compile cache (`sccache` or a shared target dir) so fresh worktrees reuse artifacts.
Reviewers trust the builder's posted green and spot-check, rather than rebuilding blind.

## Common mistakes
<The 2–3 real footguns you hit. Add as you find them.>
```

### 5.5 `docs/STATUS.md`

```markdown
# STATUS — live project state
> The single "what's actually done / in-flight / next" view. Every merged PR updates its line here
> in the same merge (rule in `shipping-changes`). Keep this SKIMMABLE — roll old entries into a
> CHANGELOG, don't append forever.

_Last updated: <DATE> — <one line on the latest merge>._

## Done
- <feature> (PR #N) — <one line>.

## In flight
- <branch/PR> — <one line + open/blocked>.

## Next
- <the next 1–3 things, per the plan>.
```

---

## 6. Lessons this project learned the hard way (so you don't have to)

These are the parts you can only see from the logs and the mid-sprint "workflow-tuning" spec. They
are the real value of studying an existing setup rather than a clean one.

1. **Meta-work recursion is the #1 risk, and it's invisible while it's happening.** Day 1 here:
   3 specs *about the workflow* + ~2,446 lines of process docs vs ~1,444 lines of product code. It
   felt productive. It wasn't. **Front-load the tuned process (this guide), then freeze it.**

2. **Uniform ceremony is a tax on the common case.** The first ship skill forced a full worktree +
   submodule init + different-agent review + docs-SHA-bump for a one-line doc tweak. Tiers fixed it.
   Start tiered.

3. **Expensive verification wants a trust protocol, not more rebuilds.** A reviewer in a fresh
   worktree recompiling a slow engine from zero, per PR, doubles cost for nothing. Shared cache +
   "trust posted green, spot-check ceilings" recovered it. Decide this before your builds get slow.

4. **"What's done?" must have one home.** Before `STATUS.md`, progress required archaeology across
   specs, PRs, and chat sessions — and the day-by-day plan's checkboxes were all still unchecked
   while builds were green and PRs merged. One live file, updated on merge, ends that.

5. **Docs rot toward length and duplication.** The live `STATUS.md` and `INDEX.md` here grew very
   long, and INDEX picked up duplicate rows. Docs that can't be skimmed stop being read. Cap them;
   automate a duplicate/stale check.

6. **Automate the mechanical, document the judgment.** Every "remember to bump the SHA / add the
   STATUS line" is a discipline you'll drop under pressure. If a regex can catch it, a regex should.

7. **The workflow *does* scale when it's tuned.** The overnight autonomous run shipped 9 independent,
   green, documented, individually-reviewed PRs in ~2 hours without touching `main` or any ceiling —
   because the tiers, the isolation, and the green-or-revert rule let it move fast *safely*. That's
   the payoff of getting §3.1 right.

8. **Prefer a reviewable handful over volume.** That same run stopped at 9 PRs on purpose: the
   remaining candidates were coupled or marginal, and more would trade reviewability for count.
   Quality + reviewability is the goal; the workflow exists to protect it, not to maximize churn.

---

## 7. The minimal spine (if you take nothing else)

For a small or greenfield project, skip Layers, tiers, and codebase-docs. Keep just this — it's ~90%
of the benefit for ~10% of the setup:

1. **`AGENTS.md`** (half a page): "branch + PR always; never commit to `main`; keep the process
   lean." Plus any real ceilings.
2. **One `shipping-changes` habit:** branch → TDD the change → verify with real command output →
   PR → self-review → merge → update `STATUS.md`.
3. **`docs/STATUS.md`:** Done / In-flight / Next, updated on merge.
4. **The two iron laws:** test-first, and no completion claim without fresh evidence.

Add a second (high-risk) lane, worktrees, and codebase-docs **only when your §0 answers turn "yes."**
Grow the process to meet the project — never the reverse.

---

*Provenance: distilled from `speedrun/`'s `.cursor/skills/{shipping-changes,codebase-docs,building-and-testing,working-with-submodules}`, the generic superpowers skills, `AGENTS.md`, the `docs/superpowers/specs/2026-06-30-{repo-working-rules,skills-optimization,workflow-tuning}` design specs, and the `OVERNIGHT_LOG.md` / `docs/STATUS.md` records of the workflow under load.*
