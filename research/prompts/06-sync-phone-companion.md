# Sub-prompt 06 — Shared-engine phone companion + offline sync with documented conflict resolution

You are a specialist research agent in **cross-platform Rust, mobile architecture, and Anki's sync protocol**. The spec requires desktop + phone running the **same Rust engine** with working two-way sync, an offline→reconnect test, a documented conflict winner, plus crash/corruption tests and a `make bench` benchmark. Determine the realistic path in one week and the honest tradeoffs (no phone companion → 70% grade ceiling).

## Exact question and scope

IN SCOPE:
1. **Anki's sync protocol.** How AnkiWeb/self-hosted sync works at a high level: the HTTP sync endpoints, what gets synced (the collection, review log/revlog, cards/notes), normal sync vs full sync, and how the Rust engine implements it (`sync` module in `rslib`). Cite source paths.
2. **Conflict model — the key question.** When the *same card* is reviewed offline on two devices and both sync, what actually happens? Does Anki use last-writer-wins, USN (update sequence numbers), timestamps, or merge of revlog entries? Document the *actual* conflict-resolution behavior and what a "clear, correct winner" rule would be for our app (challenge 7b). Be precise; if Anki avoids true conflicts by design (single-source-of-truth server, full-sync fallback), explain that.
3. **Running the same Rust engine on phone.**
   - **Android:** build on **AnkiDroid** (which already uses the Rust `anki` backend via `rsdroid`/JNI) vs. compiling `rslib` to an Android library yourself. Effort, toolchain (NDK, cargo-ndk/UniFFI/JNI), and what AnkiDroid already gives for free.
   - **iOS:** running `rslib` via its **C FFI**, Swift bridging, TestFlight/sideload constraints. Realistic in a week?
   - Recommend the **minimum viable shared-engine path** that still satisfies "same Rust engine on both" honestly.
4. **The required tests:**
   - **7b offline/sync test:** 10 cards offline on phone + 10 different on desktop → reconnect → all 20 land, none lost/double-counted; then same-card-on-both → conflict rule demonstrably picks a winner. Exact steps.
   - **7g crash/offline test:** kill app mid-review 20×, show zero corrupted collections (how SQLite transactions/WAL protect this); network-pull behavior (AI off cleanly, apps still show a score).
   - **7h `make bench`:** measure p50/p95/worst-case for button ack, next-card, dashboard load/refresh, sync completion on a 50k-card deck. How to instrument and what tooling.

OUT OF SCOPE: the Rust *feature* change (sub-prompt 05), scoring, AI.

## Deliverable format and length

- ~1200–1800 words.
- Section A: sync protocol overview (with paths).
- Section B: conflict-resolution behavior + proposed documented winner rule.
- Section C: shared-engine-on-phone options table (Android/iOS, effort, what AnkiDroid provides, recommendation).
- Section D: test recipes for 7b, 7g, 7h.

## Sourcing requirements

- **Source list (REQUIRED, at the very bottom):** End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from (repo paths/files, docs, maintainer statements), each with a working link where available, grouped by type (source code / official docs / maintainer / practitioner). No uncited claims.

- Prefer the **actual Anki / AnkiDroid source** (cite paths: `rslib/src/sync`, AnkiDroid `rsdroid`), Anki developer docs, and maintainer (Damien Elmes) statements. AnkiDroid wiki admissible if attributed.
- Per claim: source, type, confidence rating; mark inferences `[inferred — verify in repo]`.
- Do not invent endpoints, module names, or conflict behavior. If the conflict model is uncertain, say so and state how to confirm empirically.

## Counter-evidence / weak-spot demands

- Be blunt about **feasibility**: if running the real Rust engine on iOS with two-way sync in a week is unrealistic, say so and identify what subset is achievable (e.g., Android-via-AnkiDroid only) and the grade-ceiling consequence.
- Flag whether Anki's design even *produces* true two-device conflicts to resolve, or whether the "conflict winner" demo must be constructed carefully to be meaningful (avoid a demo that trivially can't conflict).
- Identify the biggest corruption risk during offline/crash testing and how Anki's storage guards against it.

End with a self-confidence summary and a one-line recommendation on the minimum viable shared-engine + sync path that avoids the 70% ceiling.
