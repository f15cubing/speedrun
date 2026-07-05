# Authored Eval Bank

> Co-located doc for `eval/bank/`. Read this before changing anything here.

## Purpose
A firewalled corpus of **original, verified GRE-Math MCQ items** that the scoring layer
(Performance + Readiness) trains and validates on, and that powers the **paraphrase test** (7d). It is
kept strictly separate from the daily-review **study deck** (`pipeline/`) and the **AI gold-set**
(`eval/goldset/`); the three corpora never mix (PRD §12). "Held out" means held out from *our* model
fitting and version-locked — the items are original, so nothing is secret; the file is committed as the
source of truth.

## Public interface
- `eval/bank/items.yaml` — the frozen, verified corpus (`items:` list). Each record:
  `id, leaf_tag, format:"mcq", question, options[5 distinct], correct_index, explanation,
  difficulty(int 1–5, PROVISIONAL), partition(p0|p1|p2|p3), paraphrase_group, base_ref,
  src, gen, status:"verified", verified_by, verified_on`. Only **p0** (frozen held-out) and **p3**
  (paraphrase rewordings) are populated; the schema/loader also accept **p1** (ablation-practice) and
  **p2** (delayed post-test) for later.
- `eval/bank/loader.py`:
  - `load_eval_items(path=ITEMS_YAML, partition=None) -> list[dict]` — parse + fully validate; raises
    `ValueError` on any schema / gate / integrity violation; `partition` filters.
  - `summarize(items) -> dict` — `total`, `by_partition`, `by_bucket`, `by_difficulty`,
    `paraphrase_groups`, `calc_weight`.
  - `assert_firewall(items=None, seed=42)` — raises if any eval `(stem, answer)` collides with a
    study-deck card (loads the study deck via `pipeline.build_deck.load_all_cards`).
  - `PARTITIONS = ("p0","p1","p2","p3")`, `ITEMS_YAML`.
- `eval/bank/generate_eval.py` — deterministic SymPy authoring aid: `gen_p0_items(seed)`,
  `gen_p3_pairs(seed)` (each P3 group = 2 same-key rewordings, guaranteed by a single
  `distractors.make_options` call), `gen_demo_p0_items(seed)` (see **Demo items** below),
  `emit_yaml(items)` / `emit_items(items)` (bare-list dump for appending), and a `__main__` that
  prints p0+p3 YAML to freeze into `items.yaml`. **Stems/options are delimited LaTeX** via
  `pipeline/mathfmt`; P3 surface framings are functions (not `str.format` templates) so LaTeX braces
  don't collide with format fields.
- `eval/bank/vendor_exam_items.py` — regenerates the in-app copy
  `anki/qt/aqt/gre/exam_items.json` from `items.yaml` (validated projection of the 8 exam-facing
  fields). Run `python eval/bank/vendor_exam_items.py` after editing `items.yaml`; the drift guard
  `tests/test_exam_items_sync.py` enforces the two stay identical.

## Dependencies
- External (pinned in `pipeline/requirements.txt`): `PyYAML`, `sympy` (authoring aid), `pytest`.
- Internal (code reuse, **not** corpus mixing): `pipeline/distractors` (`make_options`),
  `pipeline/generate_deck` helpers, `pipeline/taxonomy` (leaf-tag validation), and — only inside
  `assert_firewall` — `pipeline/build_deck.load_all_cards`. Tests reach modules via
  `eval/bank/tests/conftest.py`, which puts `eval/bank/` and `pipeline/` on `sys.path`.
- Consumed by the scoring layer (`docs/superpowers/specs/2026-07-02-thursday-scoring-layer-design.md`):
  items + provisional difficulty feed Performance; a taxonomy-weighted **P0** set feeds Readiness; the
  **P3** groups drive the paraphrase go/no-go.
- Nothing here touches `anki/` or `Anki-Android/`. Not an engine/Rust change.

## Demo items (unlock the full-length Exam-Mode mock)
`items.yaml` also carries **47 generated demo items** (`id: eval-p0-gen-*`, `gen: generated`,
`src: generated`, `demo: true`) produced by `gen_demo_p0_items(seed=42)`. They enlarge the **p0**
pool to **35 calculus / 18 algebra / 18 additional** so Exam Mode can build the official full-length
(66-item) form under the 50/25/25 blueprint (`anki/qt/aqt/gre/exam.py`). They are deterministic and
correct-by-construction (SymPy keys) — **not a live-model run** (same AI-off posture as the AI card
pipeline) — and authored in a high-coefficient / distinct-phrasing regime disjoint from the study
deck, so `assert_firewall` holds. The `demo: true` flag + `eval-p0-gen-*` id prefix let the scoring
layer exclude them from real calibration/validation folds.

## Gotchas & invariants
- **Frozen / version-locked.** `items.yaml` is the source of truth; the SymPy generator is an authoring
  aid, not run at load. The frozen `eval-p0-*` / `eval-p3-*` items must not be reseeded. The demo
  `eval-p0-gen-*` items are an **additive, deterministic** extension (regenerable via
  `gen_demo_p0_items(seed=42)`); appending more is fine, re-vendor with `vendor_exam_items.py`.
- **Difficulty is PROVISIONAL (expert-rated, r≈0.6).** Flag it provisional wherever surfaced; it widens
  the Readiness interval (report accuracy with Wilson CIs downstream).
- **P3 = rewordings only.** The base recall item is the **study-deck** card (7d); the bank holds the 2
  same-key rewordings per base. Loader enforces: each `paraphrase_group` has exactly 2 rewordings
  sharing the same `options[correct_index]` text and the same `base_ref`.
- **Firewall.** Distinct `eval::` tag namespace; never imported into the study-deck build;
  `assert_firewall` guards against `(stem, answer)` overlap with the study deck. The **layered
  leakage scan (7e / PRD §11)** is now built in `pipeline/leakage_audit.py` (`make
  deck-leakage-audit`): it extends this boolean guard to exact → normalised-stem → 13-gram →
  token-Jaccard layers and **publishes a residual leakage rate** (currently **0.0**, 0/80). It reads
  this bank via `load_eval_items` and **never modifies it**. Embedding-cosine remains a phase-2 item.
- **Verification gate.** Every item must be `status: verified` with non-empty
  `verified_by`/`verified_on`/`src`, or the loader hard-fails.
- **One leaf tag per item**; exactly 5 distinct options; `correct_index ∈ 0..4`; `difficulty ∈ 1..5`.

## Related tests
- `eval/bank/tests/test_loader.py` — schema, verification gate, difficulty/partition/MCQ validation, P3 group integrity, partition filter.
- `eval/bank/tests/test_generate_eval.py` — generator determinism, well-formedness, same-key P3, loader round-trip.
- `eval/bank/tests/test_bank_composition.py` — committed bank: all verified, P0≥20 / P3≥56 (==2×groups), calc weight ≥0.30, firewall holds.

## Composition
127 items: **P0 = 71** (24 frozen held-out, taxonomy-weighted + 47 generated demo items, see above)
+ **P3 = 56** (28 paraphrase groups × 2 same-key rewordings). The frozen-only P0 is 24; the demo
items bring P0 to 35 calculus / 18 algebra / 18 additional so a full 66-item mock is buildable.

## LaTeX rendering (2026-07-02)
Math in `items.yaml` is **delimited LaTeX** (`\(...\)` / `\[...\]`), migrated together with the vendored
`anki/qt/aqt/gre/exam_items.json` so `tests/test_exam_items_sync.py` stays green as a unit, and typeset by
MathJax in the Exam Mode webview (`anki/ts/routes/gre-exam/`). The authoring aid (`generate_eval.py`) emits
the same LaTeX. Computational strings were converted via SymPy (round-trip-verified); prose/conceptual
strings were hand-mapped. See `docs/superpowers/specs/2026-07-02-latex-math-rendering-design.md` §5.

---
Last verified against: `agent/exam-demo-items` (added 47 `eval-p0-gen-*` demo items + `vendor_exam_items.py`)
