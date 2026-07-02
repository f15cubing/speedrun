# Authored Eval Bank — Design Spec

> Build a **firewalled, original, blueprint-matched MCQ item bank** (`eval/bank/`) that the
> Performance + Readiness models train/validate on and that powers the **paraphrase test** (7d).
> Thursday MVP: **P3 paraphrase pairs (~60: ~30 base × 2 same-key rewordings) + P0 frozen held-out
> (~24, taxonomy-weighted)** — ~84 verified items with expert-rated **provisional** difficulty
> (`diff::1–5`). Items are frozen YAML (version-locked) gated by the existing verification gate;
> computational keys are SymPy-correct-by-construction (reusing `pipeline/distractors`), conceptual
> items + all rewordings hand-authored. Ships a loader/validator + tests; **no AI, no engine change →
> fast lane.** Companion to `docs/PRD.md` (§7b/§7c/§11/§12, Appendix A, tag conventions),
> `docs/execution-plan.md` (Thursday), and the parked scoring spec
> (`2026-07-02-thursday-scoring-layer-design.md`). Dated 2026-07-02.

## Decisions (locked with owner, 2026-07-01)

- **Rewording = authored same-key surface rephrasing.** Each P3 base item gets 2 rewordings that ask
  the *same* question (same numbers/answer) in different wording/notation/framing — a true paraphrase
  that tests recognition under new presentation, not a new computation. Computational keys stay
  SymPy-verified.
- **Thursday size = lean MVP:** P3 ~60 (≈30 groups) + P0 ~24; P1 (ablation-practice) / P2
  (delayed post-test) deferred to when Saturday's ablation needs them (schema already supports them).
- **Storage/production = firewalled `eval/bank/` verified YAML + a Python loader/validator.**
  Computational items SymPy-generated (reusing `pipeline/distractors`) and **frozen** into the YAML;
  conceptual items + rewordings hand-authored. Gated by the verified/attribution check. Pure data
  corpus consumed by scoring — **no `.apkg` packing now** (the timed simulator can pack forms later).

## Global constraints (from PRD §11/§12 + Appendix)

- **No AI, no ETS items.** All items original + blueprint-matched; the entire ETS corpus is treated as
  contaminated and never reused.
- **Three corpora stay firewalled:** study deck (`pipeline/`), AI gold-set (`eval/goldset/`), and this
  eval bank (`eval/bank/`) never mix. Enforced by the `eval::` tag namespace + a firewall assertion +
  (separately) the leakage pipeline.
- **Partitions are role-based** (PRD §12): `eval::p0` frozen held-out · `p1` ablation-practice · `p2`
  delayed post-test · `p3` paraphrase pairs. Version-locked (frozen) once authored.
- **Difficulty is expert-rated, PROVISIONAL, noisy (r≈0.6).** Flag it provisional everywhere it
  surfaces; it widens the Readiness interval; report accuracy with Wilson CIs.
- **Exactly one `topic::<bucket>::<leaf>` leaf tag per item** (Appendix A taxonomy).
- **No engine change → fast lane.** Data + Python loader only; nothing under `anki/` or `Anki-Android/`.
- **Re-runnable:** frozen YAML source of truth, deterministic loader, pinned deps.

---

## 1. Purpose & placement

A new corpus directory `eval/bank/` holding the authored evaluation items. It is the **held-out /
paraphrase corpus** the scoring layer consumes — kept strictly separate from the daily-review study
deck (`pipeline/`) and the AI gold-set (`eval/goldset/`). Committed as source of truth (the items are
original and authored here; there is no external secret set to protect — "held-out" means held out
from *our* model fitting, version-locked, not hidden from the world).

```
pipeline/            study deck (review / Memory / MCQ practice)   [exists]
eval/goldset/        AI gold-set (canaried, gitignored)            [exists]
eval/bank/           authored eval items (P0..P3)                  [NEW, this spec]
   items.yaml        frozen verified records
   loader.py         load + validate + firewall assertion
   eval_bank.md      module doc
   tests/            loader/validator + composition tests
```

## 2. Record schema (`eval/bank/items.yaml`)

```yaml
- id: "eval-p3-pg0001-r1"
  leaf_tag: "topic::calculus::integral_single"
  format: mcq
  question: "A particle's velocity is v(t) = 6t + 4. Which expression gives its position s(t) up to a constant?"
  options: ["3*t**2 + 4*t", "6", "3*t**2 + 4", "6*t**2 + 4*t", "3*t + 4"]
  correct_index: 0
  explanation: "s(t) = ∫v dt = ∫(6t+4)dt = 3t^2 + 4t (+ C)."
  difficulty: 2                 # diff::1-5, expert-rated, PROVISIONAL
  partition: p3                 # p0 | p1 | p2 | p3
  paraphrase_group: "pg-0001"   # p3 only: the 2 rewordings of ONE base share this
  base_ref: "topic::calculus::integral_single :: antiderivative of 6x+4"
                                # p3 only: the STUDY-DECK concept these reword (recall side of 7d)
  src: "original"
  gen: human
  status: verified              # verification gate (attribution required)
  verified_by: "fc"
  verified_on: "2026-07-02"
```

**Field rules.** `format` is `mcq` (5 options, `0 <= correct_index < 5`, options distinct). `difficulty`
is an integer 1–5. `partition ∈ {p0,p1,p2,p3}`. **P3 items are the *rewordings*** (the base recall
item lives in the study deck, per 7d); for `p3`, `paraphrase_group` (shared by the 2 rewordings of one
base) and `base_ref` (the study-deck concept being paraphrased) are required; for non-p3 both are
`null`. `status: verified` requires non-empty `verified_by`/`verified_on`/`src`. **Derived tags** a
consumer/packer may emit: the one `topic::` leaf tag + `eval::p{n}`, `diff::{1-5}`, `src::original`,
`gen::human`, `fmt::mcq`.

## 3. Composition (Thursday MVP ≈84 items)

- **P3 paraphrase (~60):** ~30 `paraphrase_group`s, each = **2 authored MCQ rewordings** of one
  study-deck base concept (same key, new surface). The **base recall item is the study-deck card**
  (not duplicated in the bank); the bank holds the 60 rewordings, each carrying `base_ref` +
  `paraphrase_group`. This is exactly 7d: compare recall on the study card vs. accuracy on its
  rewordings. Spread across the taxonomy, calculus-weighted.
- **P0 held-out (~24):** taxonomy-weighted (ETS 50/25/25 across calculus/algebra/additional) MCQ,
  **disjoint** from the study deck and from P3, for Performance/Readiness validation.
- **P1/P2:** none authored now; the schema + loader accept them so Saturday's ablation can add
  parallel non-overlapping item sets without a schema change.

## 4. Production (hybrid, frozen)

- **Computational items:** built with SymPy (reusing `pipeline/distractors.make_options` and the
  correct-by-construction pattern from `pipeline/generate_mcq.py` — importing pipeline **code** is fine;
  it is not corpus mixing). A one-time authoring aid produces candidate items; the chosen instances are
  **frozen verbatim into `items.yaml`** (options + key baked in) so the partitions are version-locked
  and never regenerate at load.
- **Conceptual items + all rewordings:** hand-authored directly in YAML; computational rewordings keep
  the SymPy-verified key and only change surface wording/notation/framing.
- **Verification gate:** every record must be `status: verified` with attribution — same mechanism as
  `pipeline/conceptual_cards.yaml`; the loader hard-fails otherwise.

## 5. Loader / validator (`eval/bank/loader.py`)

Pure Python, no Anki/engine deps.

- `load_eval_items(path=ITEMS_YAML, partition=None) -> list[dict]` — parse YAML and **enforce**:
  schema (required fields, types), verification gate, exactly-one valid leaf tag, `difficulty ∈ 1..5`,
  `partition` valid, MCQ well-formedness (5 distinct options, index in range), and **P3 group
  integrity** — every `paraphrase_group` has exactly 2 rewordings that share the same `base_ref` and
  the same correct-answer text (a genuine same-key paraphrase). Raises `ValueError` on any violation.
  Optional `partition` filters the result.
- `assert_firewall(study_cards=None)` — guardrail that no eval item's normalized `(stem, answer)`
  collides with a study-deck card (loads the study deck via `pipeline.build_deck.load_all_cards` for
  the check). **This is a lightweight overlap guard, not the rigorous leakage scan** — the n-gram /
  embedding leakage pipeline (7e) is a separate Thursday task; note the dependency.
- `summarize(items) -> dict` — counts by partition, by leaf/bucket, by difficulty; paraphrase-group
  count — for a quick composition report + the scoring/readiness weighting.

Consumed by the scoring package: `features`/`simulate` read items + `difficulty`; Readiness draws a
taxonomy-weighted representative set from **P0**; the paraphrase go/no-go uses **P3** groups.

## 6. Firewall & re-runnability

Distinct `eval::` tag namespace; `eval/bank/` is **never imported into** `pipeline/build_deck.py`'s
study-deck build; `items.yaml` is frozen (version-locked); the loader is deterministic. Difficulty is
labeled **provisional** wherever it surfaces (it feeds wider Readiness intervals per PRD §12). Pinned
deps (reuse `pipeline/requirements.txt`: PyYAML + sympy for the authoring aid + pytest).

## 7. Tests (`eval/bank/tests/`)

- **Loader/validator units:** schema enforcement; verification gate (draft/unattributed → raise);
  exactly-one leaf tag; difficulty out of range → raise; invalid partition → raise; MCQ malformed
  (≠5 options / dup / bad index) → raise; **P3 group integrity** (a group without exactly 2 rewordings,
  or rewordings whose keys/`base_ref` disagree → raise); determinism (load twice → identical).
- **Firewall test:** `assert_firewall()` passes for the committed bank (no study-deck overlap).
- **Composition test:** P3 has ~30 groups each with exactly 2 rewordings (≈60 items); P0 is
  taxonomy-weighted (calculus share ≥ ~50%); every committed item is `verified`.

## 8. Lane, dependencies, out of scope

- **Lane:** fast lane — new `eval/` data + Python loader; no `anki/`/`Anki-Android/` changes.
- **Reuses:** `pipeline/distractors` (code) for computational distractors; the verification-gate pattern.
- **Feeds:** the parked scoring sub-project (`2026-07-02-thursday-scoring-layer-design.md`).
- **Out of scope:** P1/P2 authoring (Saturday ablation); the rigorous leakage pipeline (7e, separate);
  `.apkg` packing / timed-form assembly (Friday timed mode); AI-drafted items (Friday, via the same
  gate as `gen: ai` + `status: draft`).

## 9. Acceptance criteria

- `eval/bank/items.yaml` holds ~84 **verified** items: P3 ≈60 (≈30 `paraphrase_group`s × 2 same-key
  rewordings, each with `base_ref` to a study-deck concept) + P0 ≈24 (taxonomy-weighted, disjoint from
  study deck & P3), each with a valid leaf tag + `difficulty ∈ 1..5` + attribution.
- `load_eval_items` enforces the full schema + gate + P3 integrity; `assert_firewall()` passes;
  `summarize` reports the composition.
- All loader/validator/composition tests green; deterministic; documented in `eval/bank/eval_bank.md`
  and linked from `docs/codebase/INDEX.md`.
- Consumption-ready for the scoring layer (items + provisional difficulty + P0 weighting + P3 groups).
