# Study-deck + tagging pipeline

> Co-located doc for `pipeline/`. Read this before changing anything here.

## Purpose
A re-runnable, fully deterministic pipeline that emits a leaf-tagged Anki study
deck (`.apkg`) for GRE Mathematics Subject Test prep, plus a coverage gate that
proves the deck is well-formed. It exists to satisfy the Tuesday exit-gate item
"study deck + `topic::*` tagging pipeline" (PRD §6/§11, Appendix A) without any
AI/model calls and without ever touching official ETS items. The `topic::*` tag
tree it stamps onto every card is the shared substrate the mastery query,
coverage map, readiness gate, and interleaving all build on.

## Public interface
- `taxonomy.py` — single source of truth for the 17-leaf taxonomy:
  - `BUCKETS`, `BUCKET_WEIGHTS` / `WEIGHTS`, `LEAVES_BY_BUCKET`, `LEAVES`
    (`namedtuple(bucket, leaf, tag)`), `LEAF_TAGS`, `TAG_BY_LEAF`.
  - `bucket_of(leaf)` → bucket name (accepts a bare leaf name or a full tag).
  - `validate_leaf_tag(tag)` → `bool` (strict membership of the 17 valid tags).
  - `parse_leaf_tag(tag)` → `(bucket, leaf)` or `None`.
  - Gate thresholds: `MIN_LEAF_COVERAGE = 0.50`, `MIN_CALCULUS_CARD_WEIGHT = 0.50`.
- `generate_deck.py` — `generate_cards(seed=42)` → ordered `list` of card dicts
  `{"front", "back", "leaf_tag"}` for the templatable leaves. `GENERATED_COUNTS`
  maps leaf → card count. SymPy both builds the problem and computes the answer.
- `distractors.py` — `make_options(rng, correct, wrong_exprs, n_options=5)` →
  `(options: list[str], correct_index)`; `generic_variants(expr)`;
  `InsufficientDistractors`. Deterministic MCQ option assembly (SymPy equality
  dedupe, wrongs ≠ key, common-error top-up).
- `generate_mcq.py` — `generate_mcq_cards(seed=42)` → ordered list of MCQ card
  dicts `{leaf_tag, format:"mcq", question, options[5], correct_index, explanation}`;
  `MCQ_COUNTS` maps leaf → count. Reuses `generate_deck` helpers; SymPy computes
  both key and distractors.
- `build_deck.py` — `load_all_cards(seed=42)` (generated flashcards + MCQ +
  verified conceptual, canonical order), `cards_content_hash(cards)` (both
  formats), `note_for(card)` (dispatches basic/MCQ), `mcq_note_for(card)`,
  `load_conceptual_cards(path=, strict=)` + `assert_all_verified(path=)` (the
  verification gate), `MODEL` / `MCQ_MODEL` (9-field "GRE MCQ" note type),
  `build(seed=42, out_path=..., verbose=True)` → `(cards, summary)`; CLI
  `python pipeline/build_deck.py --seed 42` writes `pipeline/dist/gre-study-deck.apkg`.
- `coverage_report.py` — `summarize(cards)` (now includes `by_format`),
  `format_report(summary)`, `assert_coverage(cards)` (raises on violation); CLI
  `python pipeline/coverage_report.py --seed 42` also runs `assert_all_verified`
  (non-zero exit on any coverage or verification violation).
- `conceptual_cards.yaml` — hand-authored cards (`cards:` list) for the conceptual
  leaves; the committed source of truth. Every entry carries the verification block
  `status: verified` + `verified_by` / `verified_on` / `source` (required). Entries
  may be `format: mcq` (with `options`/`correct_index`/`explanation`).

## Dependencies
- External (pinned in `pipeline/requirements.txt`): `sympy` (generation + answer
  computation), `genanki` (`.apkg` packing), `PyYAML` (conceptual cards), `pytest`
  (tests). No network, no model calls.
- Internal: everything imports `taxonomy`. `build_deck` imports `generate_deck` +
  `coverage_report`; `coverage_report.main()` lazily imports `build_deck`
  (avoids an import cycle). Tests reach the modules via `pipeline/tests/conftest.py`,
  which puts `pipeline/` on `sys.path`.
- Nothing here touches `anki/` or `Anki-Android/`. Not an engine/Rust change.

## Gotchas & invariants
- **Exactly one leaf tag per card.** Every card dict has a single `leaf_tag`, and
  it must be a valid `topic::<bucket>::<leaf>` (`validate_leaf_tag`). The built
  genanki note carries exactly that one tag. Enforced by the coverage gate and
  `tests/test_tagging.py`.
- **Determinism.** Same `--seed` ⇒ identical ordered card list. Each leaf draws
  from its own RNG seeded by `sha256(seed:leaf_tag)`, so output is independent of
  iteration order. **MCQ uses a distinct RNG namespace** (`tag + "::mcq"`) so
  adding MCQ never perturbs flashcard determinism. Model id, deck id, and note
  GUIDs are content-derived (not random), and the package is written with a fixed
  timestamp. `tests/test_determinism.py`.
- **Verification gate (PRD §12a).** Conceptual cards must be `status: verified`
  with non-empty `verified_by`/`verified_on`/`source`. The dev build skips drafts
  with a warning; `assert_all_verified` (run by the coverage CLI) hard-fails on any
  draft or unattributed-verified card. A human is the only path to `verified` —
  this is also the gate Friday's AI drafts (`gen: ai`, `status: draft`) pass through.
- **Correct by construction.** Backs are computed by SymPy, never hand-typed for
  the generated leaves; `tests/test_recompute.py` independently re-derives a sample.
- **Coverage gate is hard.** `build_deck` calls `assert_coverage` after writing
  the deck; ≥ 50 % leaf coverage (≥ 9/17; we ship all 17) and ≥ 50 % calculus
  card weight, or the command exits non-zero.
- **No ETS items, no AI.** All content is original; do not import ETS material or
  add model calls here.
- **`pipeline/dist/` is git-ignored.** The `.apkg` is a regenerated artifact; the
  source of truth is the generator + `conceptual_cards.yaml`.

## Related tests
- `pipeline/tests/test_tagging.py` — exactly one valid leaf tag per card / note.
- `pipeline/tests/test_determinism.py` — same seed ⇒ identical card list.
- `pipeline/tests/test_coverage.py` — coverage assertions hold (all 17 leaves, calc ≥ 50 %).
- `pipeline/tests/test_recompute.py` — generated backs match independent SymPy recomputation.
- `pipeline/tests/test_distractors.py` — deterministic 5-option assembly; wrongs ≠ key; raises when too few.
- `pipeline/tests/test_mcq_generation.py` — MCQ determinism, well-formedness, correct-key integrity.
- `pipeline/tests/test_conceptual_gate.py` — verification gate (verified-only load, hard-fails, MCQ records).
- `pipeline/tests/test_mcq_notetype.py` — GRE MCQ note type (9 fields, one topic tag, stable hash).

---
Last verified against: agent/pipeline-mcq-content (built on main 3b224e2) — MCQ surface + verification gate
