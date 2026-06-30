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

## Files

| File | Role |
|---|---|
| `taxonomy.py` | Single source of truth: leaves, buckets, weights, `bucket_of`, `validate_leaf_tag`. |
| `generate_deck.py` | Seeded SymPy generator for the templatable (computational) leaves. SymPy computes every answer, so backs are correct by construction. |
| `conceptual_cards.yaml` | Hand-authored, correct cards for the conceptual leaves that don't templatize. |
| `build_deck.py` | Merges generator + YAML, packs the deterministic `.apkg` via `genanki`, runs the coverage gate. |
| `coverage_report.py` | Computes/prints leaf coverage % + calculus weight %; asserts the invariants; non-zero exit on violation. |
| `requirements.txt` | Pinned dependency versions. |
| `tests/` | pytest suite (tagging, determinism, coverage, recomputation). |

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
