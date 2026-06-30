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

```
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
```
