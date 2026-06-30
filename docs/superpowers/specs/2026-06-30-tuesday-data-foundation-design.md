# Tuesday Data Foundation — Design Spec

> Closes the remaining Tuesday exit-gate items: **study deck + `topic::*` tagging pipeline** and the
> **AI gold-set**. The builds (desktop `./run`, AnkiDroid APK on emulator) are already done; this is
> the only outstanding gap. Companion to `docs/PRD.md` (§6, §9, §11, §12, Appendix A) and
> `docs/execution-plan.md` (Tuesday section). Dated 2026-06-30.

## Status at time of writing

Done ✅: decisions signed off (PRD §16); fork + AGPL `LICENSE` + submodules pinned (`anki@25.09.4`,
`Anki-Android@v2.24.0`); rslib insertion points documented; **Spike 1 desktop build** (`./run`
compiled + ran a full review loop, exit 0); **Spike 2 Android build** (SDK installed,
`assembleFullDebug` BUILD SUCCESSFUL with `librsdroid.so`, emulator booted, AnkiDroid launched).

Remaining ❌ (this spec): study deck, `topic::*` tagging pipeline, AI gold-set.

## Decisions (locked with owner, 2026-06-30)

- **Deck source:** hybrid — seeded SymPy generator for computational leaves + a small set of
  hand-authored conceptual cards for the leaves that don't templatize. Fully original (no
  leakage/licensing risk), re-runnable.
- **Gold-set source:** MIT OpenCourseWare (CC-BY-NC-SA), one course's problem set/exam with
  published solutions. Non-ETS. Internal eval use only (not redistributed).
- **Scope today:** minimal-but-real to clear the exit gate; expand later in the week.

## Global constraints (apply to both tracks)

- **No AI before Friday** — the deck and gold-set are generated/sourced without any model calls.
- **Never reuse ETS items** — all ~431 official ETS items are contaminated; do not use them anywhere.
- **Taxonomy is frozen** at the leaf level — the 17 `topic::<bucket>::<leaf>` tags in PRD Appendix A
  are the single source of truth. Every card/item carries **exactly one** leaf tag.
- **Re-runnable** — pinned dependency versions, fixed RNG seed, one documented command, deterministic
  output (PRD §11).
- **Ships via `shipping-changes`** — each track on its own worktree → branch `agent/<area>-<task>` →
  real `gh` PR → verified by a **different** agent. Base gate only (neither track touches
  `rslib/`/proto/`pylib`/submodules → no engine extra gate). Each PR adds a co-located module doc
  (from `module-doc-template.md`) and a row in `docs/codebase/INDEX.md`.

## Taxonomy (PRD Appendix A — 17 leaves; ≥9 = ≥50% coverage)

- **Calculus (50%)** `topic::calculus::` — `differential_single`, `integral_single`,
  `differential_multi`, `integral_multi`, `differential_equations`, `applications`
- **Algebra (25%)** `topic::algebra::` — `elementary`, `linear`, `abstract`, `number_theory`
- **Additional (25%)** `topic::additional::` — `real_analysis`, `discrete`, `topology`, `geometry`,
  `complex`, `probability_stats`, `numerical`

Templatable (generator): calculus leaves, `algebra::elementary/linear/number_theory`,
`additional::probability_stats/numerical`. Hand-authored (conceptual): `algebra::abstract`,
`additional::real_analysis/topology/geometry/complex/discrete`.

---

## Track A — Study deck + `topic::*` tagging pipeline (one PR)

**Goal:** a re-runnable pipeline that emits a leaf-tagged GRE study deck `.apkg` covering ≥9 of 17
leaves at ≥50% calculus weight, plus a coverage validator.

**File layout** (new top-level `pipeline/`, pure Python):
- `pipeline/taxonomy.py` — canonical leaves/buckets/weights from Appendix A; `LEAVES`, `BUCKETS`,
  `bucket_of(leaf)`, `validate_leaf_tag(tag)`. Single source of truth, imported by everything.
- `pipeline/generate_deck.py` — seeded SymPy generator for the templatable leaves; returns card
  dicts `{front, back, leaf_tag}`.
- `pipeline/conceptual_cards.yaml` — hand-authored cards for conceptual leaves (committed, readable).
- `pipeline/build_deck.py` — merges generator + yaml, packs to `.apkg` via `genanki` with
  deterministic model/deck IDs + note GUIDs and a fixed `--seed` (default 42).
- `pipeline/coverage_report.py` — prints leaf coverage % + calc weight %; asserts ≥50% leaves, ≥50%
  calc, and exactly-one-leaf-tag per card; non-zero exit on violation.
- `pipeline/requirements.txt` — pinned (`genanki`, `sympy`, `pyyaml`).
- `pipeline/README.md` + `pipeline/pipeline.md` (module doc from template).
- `.gitignore` += `pipeline/dist/` (the built `.apkg` is a gitignored artifact; source of truth is
  the generator + yaml).

**One command:** `python pipeline/build_deck.py --seed 42` → `pipeline/dist/gre-study-deck.apkg` +
coverage report.

**Tests** (`pipeline/tests/`, pytest): every card has exactly one valid leaf tag; deterministic build
(same seed → identical card set); coverage assertions hold for the produced deck; a couple of
generated computational answers checked against SymPy ground truth.

**Acceptance:** command runs clean; deck imports into the desktop app (smoke); coverage report shows
≥9 leaves and ≥50% calc; tests pass; module doc + INDEX row added.

---

## Track B — AI gold-set (one PR)

**Goal:** 50 known-correct Q&A pairs from one MIT OCW source, leaf-tagged, canary-stamped, in an
access-controlled (gitignored) store, for Friday's AI gold-set gate (PRD §9).

**File layout** (new top-level `eval/goldset/`):
- `eval/goldset/README.md` — access-control model (data gitignored, never published), source +
  CC-BY-NC-SA attribution, canary scheme, regeneration/verification instructions. **Committed.**
- `eval/goldset/schema.json` — record schema. **Committed.**
- `eval/goldset/canary-manifest.md` — the project canary GUID + per-item sentinel scheme (the canary
  value is a random sentinel, safe to commit; scanned for in Thursday's leakage pipeline). **Committed.**
- `eval/goldset/validate.py` — checks all 50 records: required fields present, valid leaf tag, canary
  present, source anchor present. **Committed.**
- `eval/goldset/data/pairs.jsonl` — the 50 Q&A records. **Gitignored** (held-out keys).
- `eval/goldset/goldset.md` (module doc) + INDEX row. **Committed.**
- `.gitignore` += `eval/goldset/data/`.

**Each record:** `id`, `question`, `answer`, `source{course, problem_set, problem_no, url}`,
`leaf_tag`, `second_solver_check` (note/bool), `canary`.

**Sourcing:** pick one OCW course with published solutions (e.g., 18.01 Single Variable Calculus —
matches the 50% calc emphasis). Transcribe carefully from the official solution; record the exact
anchor. **Second-solver check** each answer (re-derive/sanity-check). **Honesty over count:** if an
item can't be confidently verified, flag it or drop it and document the gap — never fabricate an
answer. Aim for 50; deliver the verified subset + documented gap if 50 isn't confidently reachable.

**Tests/validation:** `python eval/goldset/validate.py` passes on the committed schema with the
gitignored data present; documents expected count.

**Acceptance:** store + schema + canary manifest committed; ≥1 verified batch toward 50 (target 50)
in gitignored data; validator passes; attribution + access-control documented; module doc + INDEX row.

---

## Parallelization & integration

Tracks A and B touch disjoint new dirs → fully parallel, dispatched as two builder agents in their
own worktrees. Only shared file is `docs/codebase/INDEX.md` (each adds one row) and `.gitignore`
(each adds one line) → trivial merge; second PR to merge rebases if needed. A **different** agent
reviews each PR against `pr-checklist.md` base gate before squash-merge to `main`.

## Out of scope (later in the week)

50,000-card **benchmark** deck + `make bench` (Saturday, §11); authored eval item bank P0–P3
(Thursday, §12); full leakage pipeline (Thursday, §11); AI generation of cards (Friday, §9).
