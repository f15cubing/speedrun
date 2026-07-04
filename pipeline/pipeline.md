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

> **AI card pipeline (PRD §9) lives in the `aicards/` subpackage** — RAG +
> non-nullable provenance + in-pipeline abstention + SymPy/NLI verification + the
> pre-lodged gold-set gate, plus the **beat-the-baseline (McNemar)** and **AI-off
> degradation** proofs. It is separate from this deterministic study-deck generator
> (which is deliberately AI-free) and has its own authoritative doc:
> `pipeline/aicards/aicards.md`. Run it with `make ai-gate` and `make ai-baseline`.

## Public interface
- `mathfmt.py` — the single math-formatting contract. `tex(expr)` → raw
  `sympy.latex`; `inline(s)`/`block(s)` wrap an already-LaTeX string in MathJax
  delimiters (`\(...\)` / `\[...\]`); `expr_inline(expr)`/`expr_block(expr)`
  compose the two. **All displayed math goes through this module**, so every
  surface renders identically and Anki's MathJax typesets it on desktop + Android.
- `taxonomy.py` — single source of truth for the 17-leaf taxonomy:
  - `BUCKETS`, `BUCKET_WEIGHTS` / `WEIGHTS`, `LEAVES_BY_BUCKET`, `LEAVES`
    (`namedtuple(bucket, leaf, tag)`), `LEAF_TAGS`, `TAG_BY_LEAF`.
  - `bucket_of(leaf)` → bucket name (accepts a bare leaf name or a full tag).
  - `validate_leaf_tag(tag)` → `bool` (strict membership of the 17 valid tags).
  - `parse_leaf_tag(tag)` → `(bucket, leaf)` or `None`.
  - Gate thresholds: `MIN_LEAF_COVERAGE = 0.50`, `MIN_CALCULUS_CARD_WEIGHT = 0.50`.
- `generate_deck.py` — `generate_cards(seed=42)` → ordered `list` of card dicts
  `{"front", "back", "leaf_tag"}` for the templatable leaves. `GENERATED_COUNTS`
  maps leaf → card count (scale: `differential_single`/`integral_single` = 825,
  `differential_multi` = 700, `differential_equations`/`integral_multi`/`applications` = 500,
  `linear` = 375, `elementary` = 250, `probability_stats`/`numerical` = 250,
  `number_theory` = 370, `abstract`/`real_analysis`/`discrete`/`topology`/`geometry`/`complex` = 8).
  SymPy both builds the problem and computes the answer.
- `distractors.py` — `make_options(rng, correct, wrong_exprs, n_options=5)` →
  `(options: list[str], correct_index)`; `generic_variants(expr)`;
  `InsufficientDistractors`. Deterministic MCQ option assembly; **options are
  inline-LaTeX** (`mathfmt.expr_inline`) while dedupe / wrongs-≠-key checks run on
  the canonical `sympy.sstr` string (presentation-independent integrity).
- `generate_mcq.py` — `generate_mcq_cards(seed=42)` → ordered list of MCQ card
  dicts `{leaf_tag, format:"mcq", question, options[5], correct_index, explanation}`;
  `MCQ_COUNTS` maps leaf → count. Reuses `generate_deck` helpers; SymPy computes
  both key and distractors.
- `build_deck.py` — `load_all_cards(seed=42)` (generated flashcards + MCQ +
  verified conceptual, canonical order), `cards_content_hash(cards)` (both
  formats), `note_for(card)` (dispatches basic/MCQ), `mcq_note_for(card)`,
  `load_conceptual_cards(path=, strict=)` + `assert_all_verified(path=)` (the
  verification gate), `MODEL` / `MCQ_MODEL` (9-field "GRE MCQ" note type — **interactive
  card template**: five tappable A–E options with instant green/red feedback + explanation
  reveal + MathJax typeset; grades on the normal FSRS ease path; renders in the reviewer
  webview on both desktop + Android. Spec: `docs/superpowers/specs/2026-07-03-interactive-mcq-webview-design.md`),
  `build(seed=42, out_path=..., verbose=True)` → `(cards, summary)`; CLI
  `python pipeline/build_deck.py --seed 42` writes `pipeline/dist/gre-study-deck.apkg`.
- `coverage_report.py` — `summarize(cards)` (now includes `by_format`),
  `format_report(summary)`, `assert_coverage(cards)` (raises on violation); CLI
  `python pipeline/coverage_report.py --seed 42` also runs `assert_all_verified`
  (non-zero exit on any coverage or verification violation).
- `deck_report.py` — **quality report + integrity gate** (complements `coverage_report`:
  coverage proves the deck *covers* the taxonomy, this proves each card is *well-formed*).
  `audit_mcq(card)` (exactly 5 **distinct** options, valid `correct_index`, and — when the
  ground-truth `_correct_expr` is present — the option at `correct_index` renders exactly
  that key), `required_fields(card)` (no empty stem/answer/explanation), `summarize_quality`,
  `assert_deck_quality` (raises on any violation), `format_report`. Whole-deck version of the
  per-generator integrity unit tests (PRD §12/§12a "distractors provably ≠ key"). Stem/option
  lengths are reported, not gated. `run_deck_report.py` CLI + `make deck-report` (a `--strict`
  GATE). Seed 42: **5,407 cards (526 MCQ), integrity OK, 0 violations**.
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
- **Math is delimited LaTeX; truth stays a SymPy expression.** Card/MCQ text is
  prose with math spans wrapped by `mathfmt` (`\(...\)` / `\[...\]`). Anki's
  reviewer + AnkiDroid already load MathJax and typeset these — **no `[latex]`
  image toolchain** (that would break offline / clean-device installs). Generators
  keep the answer as a SymPy object and expose it to tests under a **test-only
  `_expr` / `_correct_expr` key that is never written to the note** (so correctness
  is checked on expressions, not markup).
- **LaTeX survives field escaping.** `build_deck._to_html` HTML-escapes fields;
  this is safe because the browser decodes `&amp;`/`&lt;` (matrix `&`, inequality
  `<`) back in the text node before MathJax reads it (`tests/test_latex_escaping.py`).
- **Exactly one leaf tag per card.** Every card dict has a single `leaf_tag`, and
  it must be a valid `topic::<bucket>::<leaf>` (`validate_leaf_tag`). The built
  genanki note carries exactly that one tag. Enforced by the coverage gate and
  `tests/test_tagging.py`.
- **Determinism.** Same `--seed` ⇒ identical ordered card list. Each leaf draws
  from its own RNG seeded by `sha256(seed:leaf_tag)`, so output is independent of
  iteration order. **MCQ uses a distinct RNG namespace** (`tag + "::mcq"`) so
  adding MCQ never perturbs flashcard determinism. Model id + deck id are fixed.
  The `.apkg` is **byte-reproducible**: `build_deck._rewrite_apkg_deterministically`
  re-zips with a fixed 1980 timestamp + fixed perms (genanki otherwise stamps zip
  entries with wall-clock time), so `make deck-asset-check` can byte-compare.
  `tests/test_determinism.py`.
- **Stable, rendering-independent note GUIDs.** Each card carries a `uid`
  (`<leaf>::<format>::<ordinal>`, generated; `::c<ordinal>` for conceptual) and the
  note GUID derives from it (`build_deck._guid_for`), **not** from the rendered
  front/back. So re-rendering the deck (e.g. ASCII → LaTeX) keeps GUIDs stable and
  the version-gated auto-importer updates cards **in place** (no duplicates).
  `tests/test_stable_guids.py`.
- **Scale & capacity.** The generator is template-based: per-leaf counts are
  controlled by `GENERATED_COUNTS` (flashcards) and `MCQ_COUNTS` (MCQ). At the
  current scale (~5,400 cards, seed 42) all problems are unique within each leaf
  (enforced by `tests/test_template_capacity.py`). If a leaf's count approaches
  the combinatorial limit of its SymPy template, the capacity test will catch it
  before any duplicates ship.
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
- `pipeline/tests/test_stable_guids.py` — every card has a unique `uid`; note GUID derives from it and is stable across re-rendering.
- `pipeline/tests/test_mathfmt.py` — the LaTeX formatting contract (delimiters, composition, determinism).
- `pipeline/tests/test_latex_escaping.py` — matrix `&` / inequality `<` survive field escaping for MathJax.
- `pipeline/tests/test_tagging.py` — exactly one valid leaf tag per card / note.
- `pipeline/tests/test_determinism.py` — same seed ⇒ identical card list.
- `pipeline/tests/test_coverage.py` — coverage assertions hold (all 17 leaves, calc ≥ 50 %).
- `pipeline/tests/test_recompute.py` — generated backs match independent SymPy recomputation.
- `pipeline/tests/test_distractors.py` — deterministic 5-option assembly; wrongs ≠ key; raises when too few.
- `pipeline/tests/test_mcq_generation.py` — MCQ determinism, well-formedness, correct-key integrity.
- `pipeline/tests/test_conceptual_gate.py` — verification gate (verified-only load, hard-fails, MCQ records).
- `pipeline/tests/test_mcq_notetype.py` — GRE MCQ note type (9 fields, one topic tag, stable hash).
- `pipeline/tests/test_template_capacity.py` — uniqueness of generated cards within each leaf at current scale; catches approaching combinatorial limits early.
- `pipeline/tests/test_deck_report.py` — quality/integrity gate: MCQ option distinctness, valid index, ground-truth key match, required non-empty fields, the `assert_deck_quality` gate, and a real-deck smoke asserting the whole deck passes.
- `pipeline/tests/test_scale.py` — total card count ≥ 5 000 and per-leaf minimums for the high-volume leaves.

---
Last verified against: agent/pipeline-latex-math
