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
- `build_deck.py` — `load_all_cards(seed=42)` (merged generated + conceptual,
  canonical order), `cards_content_hash(cards)`, `note_for(card)`,
  `build(seed=42, out_path=..., verbose=True)` → `(cards, summary)`; CLI
  `python pipeline/build_deck.py --seed 42` writes `pipeline/dist/gre-study-deck.apkg`.
- `coverage_report.py` — `summarize(cards)`, `format_report(summary)`,
  `assert_coverage(cards)` (raises on violation); CLI
  `python pipeline/coverage_report.py --seed 42` (non-zero exit on violation).
- `conceptual_cards.yaml` — hand-authored cards (`cards:` list) for the conceptual
  leaves; the committed source of truth for those leaves.

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
  iteration order. Model id, deck id, and note GUIDs are content-derived (not
  random), and the package is written with a fixed timestamp. `tests/test_determinism.py`.
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

---
Last verified against: 6941192
