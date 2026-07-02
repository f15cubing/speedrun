# GRE Math study-deck pipeline

A re-runnable, fully deterministic pipeline that emits a leaf-tagged Anki study
deck (`.apkg`) for **GRE Mathematics Subject Test** prep, plus a coverage gate
that proves the deck is well-formed.

- **No AI / no model calls.** Cards are produced by a seeded SymPy generator and
  a small set of hand-authored conceptual cards.
- **No ETS items.** Everything here is original; official ETS material is
  contaminated and is never used (PRD §11/§12).
- **Re-runnable.** Pinned dependencies, a fixed RNG seed, one documented command,
  and byte-stable output (content-derived note GUIDs; fixed model/deck ids).

## One command

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r pipeline/requirements.txt
python pipeline/build_deck.py --seed 42
```

This writes `pipeline/dist/gre-study-deck.apkg`, prints the coverage report, and
**fails (non-zero exit) if the coverage gate is violated**.

## What gets built

- Every card carries **exactly one** valid leaf tag `topic::<bucket>::<leaf>`
  (the 17-leaf taxonomy from PRD Appendix A; see `taxonomy.py`).
- The deck covers **all 17** taxonomy leaves (gate requires ≥ 9 = ≥ 50%).
- **≥ 50 % of cards are calculus-tagged**, reflecting the ETS ~50% calculus weight.
- **~5,370 cards total** (≈ 4,880 flashcards + ≈ 490 MCQ, seed 42 build). Heavy
  calculus leaves (`differential_single`, `integral_single`) each generate 825
  cards; `differential_multi` 700; other calculus leaves 500; algebra/additional
  leaves scaled to match exam-weight targets.
- Two card formats: **basic flashcards** (the Memory surface) and **MCQ** cards
  (the Performance surface, §8a) via a new **"GRE MCQ"** note type. Computational
  MCQ are generated for `differential_single`, `integral_single`, `linear`,
  `number_theory` with SymPy-templated distractors; conceptual MCQ are
  hand-authored. All MCQ review through the same FSRS loop — no engine change.
- **~57 conceptual cards** are reference-sourced originals (hand-authored for the
  conceptual leaves; every entry carries `status: verified` + full attribution).
- **Conceptual cards are gated:** only `status: verified` (with attribution) cards
  ship; drafts are skipped by the dev build and rejected by the production gate.

## Files

| File | Role |
|---|---|
| `taxonomy.py` | Single source of truth: leaves, buckets, weights, `bucket_of`, `validate_leaf_tag`. |
| `generate_deck.py` | Seeded SymPy generator for the templatable (computational) flashcard leaves. SymPy computes every answer, so backs are correct by construction. |
| `distractors.py` | Deterministic MCQ option assembly + common-error distractors (SymPy dedupe, wrongs ≠ key). |
| `generate_mcq.py` | Seeded computational MCQ generator (5-option items, SymPy-computed key + distractors). |
| `conceptual_cards.yaml` | Hand-authored, correct flashcard + MCQ cards for the conceptual leaves; every entry gated by `status: verified` + attribution. |
| `build_deck.py` | Merges flashcards + MCQ + verified conceptual, packs the deterministic `.apkg` (basic + "GRE MCQ" note types) via `genanki`, runs the coverage gate. |
| `coverage_report.py` | Computes/prints leaf coverage % + calculus weight % + per-format counts; asserts coverage + the verification gate; non-zero exit on violation. |
| `requirements.txt` | Pinned dependency versions. |
| `tests/` | pytest suite (tagging, determinism, coverage, recomputation, distractors, MCQ generation, verification gate, MCQ note type). |

## Regenerate / verify

```bash
. .venv/bin/activate
python pipeline/build_deck.py --seed 42      # rebuild deck + run coverage gate
python pipeline/coverage_report.py --seed 42 # coverage report only
python -m pytest pipeline/tests -q           # run the test suite
```

The built `.apkg` lives in `pipeline/dist/` and is **git-ignored** — the source of
truth is the generator plus `conceptual_cards.yaml`, not the artifact. Changing the
`--seed` changes the generated problems but the deck stays deterministic for any
fixed seed.

## Importing the deck

Open the Anki desktop app → *File → Import* → choose
`pipeline/dist/gre-study-deck.apkg`. Cards arrive under the
*GRE Math Subject Test → Study Deck* deck, each tagged with its single
`topic::<bucket>::<leaf>` tag.
