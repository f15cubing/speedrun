# Sub-prompt 05 — Anki Rust backend: architecture, feasibility of the three candidate changes, testing/undo/integrity

You are a specialist research agent with strong **Rust** and codebase-archaeology skills, investigating **Anki's open-source backend** (the `anki` / `ankidroid` ecosystem; the Rust engine is `rslib` / `anki` crate, with `pylib` Python bindings and protobuf interfaces). The project must make a *real* change inside Anki's Rust engine and prove it doesn't corrupt collections or break undo. Map the territory and rank the three candidate changes by feasibility and merge difficulty.

## Exact question and scope

IN SCOPE:
1. **Architecture map** (with file paths/module names, current as of the latest Anki release):
   - Where the **scheduler** lives (the v3/FSRS scheduler), how the review queue is built, where due-card ordering is decided.
   - The **collection** object, storage layer (SQLite via `rusqlite`), and transaction model.
   - The **protobuf** layer: `proto/anki/*.proto` (esp. `backend.proto`, `scheduler.proto`), how messages map to backend service methods, and how Python calls into Rust.
   - The **undo** system: how operations register undo entries (`OpChanges`, undo stack), and what an operation must do to be undoable.
2. **Feasibility ranking of the three candidate Rust changes** (from the spec):
   - (a) **Points-at-stake queue** — re-sort due cards by `topic_weight × student_weakness`; requires a new protobuf message. What must change, where, and how risky for undo/queue integrity?
   - (b) **Topic-aware scheduling** — surface weak-topic cards sooner while keeping FSRS intervals valid and undo working. (Likely the riskiest — touches scheduling correctness.)
   - (c) **Mastery query** — a new backend call returning per-topic mastered count + avg recall, fast on 50k cards. (Likely the safest — read-only, no scheduler mutation.)
   For each: files touched, whether it mutates scheduling state, undo/corruption risk, merge difficulty vs upstream, and performance considerations at 50k cards.
3. **Testing approach.** How to write ≥3 Rust unit tests (where Anki's tests live, test harness/fixtures for an in-memory collection) + 1 Python integration test calling the new method; how to assert undo works and the collection round-trips without corruption.
4. **Recommendation:** which candidate to pick for best (grade-weighted) risk/reward in a week, and a "where to put `topic`" note — how topic metadata can attach to cards/notes (tags, note fields, a deck/subdeck convention) without schema-breaking changes.

OUT OF SCOPE: scoring math, AI, the phone build (separate sub-prompt 06), UI styling.

## Deliverable format and length

- ~1200–1800 words.
- Section A: annotated architecture map with concrete file paths and module names.
- Section B: candidate-comparison table (change / files touched / mutates scheduler? / undo risk / merge difficulty / perf / verdict).
- Section C: testing recipe (Rust unit + Python integration), with where tests live and how to spin up a test collection.
- Section D: recommendation + topic-metadata strategy.

## Sourcing requirements

- **Source list (REQUIRED, at the very bottom):** End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from (repo paths/files, docs, maintainer statements), each with a working link where available, grouped by type (source code / official docs / maintainer / practitioner). No uncited claims.

- Prefer the **actual source code** (cite repo paths and, where possible, file/module names and function names), Anki's developer docs (`docs/` in the repo, `docs.ankiweb.net` developer/contributing pages), and Damien Elmes / maintainer statements.
- Practitioner sources (AnkiDroid wiki, add-on dev forums) admissible if identifiable; mark as such.
- Per claim: source, type, confidence rating. If you are inferring structure rather than confirming from a file, say `[inferred — verify in repo]`.
- Do NOT invent file paths or function names. If unsure of the current path, say so and give the likely location to verify.

## Counter-evidence / weak-spot demands

- Flag where a candidate that *looks* simple actually entangles the scheduler/undo (the spec hard-ceilings a fake Rust change at 50%, so the change must be *real* yet *safe*).
- Note upstream churn risk: scheduler internals change between versions; identify the most stable insertion points.
- Call out the single biggest corruption/undo footgun for each candidate.

End with a self-confidence summary and a one-line pick: which Rust change, and why it is both real enough to score and safe enough to finish.
