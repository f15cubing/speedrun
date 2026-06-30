# PR Checklist & Body Template

## Which lane / gate? (the "engine PR?" test)

A PR is an **engine/Rust PR** if it touches any of: `rslib/`, the `anki`/`Anki-Android` submodules,
protobuf/`.proto` definitions, FFI bindings in `pylib`, or anything affecting the scheduler, undo,
or the collection store.

- **Engine PR →** engine lane: base gate **+ extra gate**, verified by a **different agent**.
- **Everything else →** fast lane: the **fast-lane self-review checklist** below (no separate
  reviewer agent). When in doubt, treat it as an engine PR.

## Fast-lane self-review checklist (non-engine changes)

- [ ] Change is non-engine (passes the "engine PR?" test as *no*) and scoped to one task.
- [ ] On a branch + real PR (never committed to `main`).
- [ ] What's verifiable was verified (tests/lint for the touched files); result noted in the PR body.
- [ ] Relevant docs updated in THIS PR.
- [ ] PR body has the 2–3 sentence intent note (template below).
- [ ] On merge, `docs/STATUS.md` line updated.

## Base gate (every engine-lane PR)

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

Fast-lane PRs: "What & why" is the 2–3 sentence intent note; mark the extra-gate section `N/A`.

```
## What & why
<one paragraph — for fast-lane, the 2–3 sentence intent note>

## Area(s) touched
<paths> — engine/Rust PR? yes/no

## Docs updated
<doc file(s) + new Last-verified SHA (engine lane)>

## Test evidence
<commands run + results>

## Engine/Rust extra gate (if applicable)
<undo proof, invariant test name, rust+python test names, files touched + merge difficulty — or N/A>
```
