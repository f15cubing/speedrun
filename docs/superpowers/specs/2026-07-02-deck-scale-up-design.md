# Deck Scale-Up (~5,000 cards) — Design Spec

> Grow the study deck from ~104 cards to **~5,000+ unique, deterministic** cards so the app ships a
> substantial review set — by (a) scaling the **templated computational** generators (with wider
> parameter ranges + a few new template sub-types so thin leaves stay unique) and (b) **expanding the
> hand-authored conceptual set** from ~20 to ~60 original questions, **sourced from reputable
> references** (ETS content outline + standard textbooks/OCW/Wikipedia math facts), original wording,
> `src`-attributed, human-verified, **never ETS items**. Keeps the coverage + ≥50% calculus gates,
> byte-stable output, no AI, no engine change → **fast lane**. Bundling/auto-import into the apps is a
> **separate** sub-project (B). Companion to `docs/PRD.md` (§6/§11/§12, Appendix A), the pipeline docs
> (`pipeline/pipeline.md`), and `docs/execution-plan.md`. Dated 2026-07-02.

## Decisions (locked with owner, 2026-07-02)

- **Target ≈ 5,000–5,500 cards.** Scale comes from the 11 templatable flashcard leaves + 4 MCQ leaves;
  calculus stays ≥ 50% by card count.
- **Conceptual set expanded to ~60** (from ~20). More concept questions across the conceptual leaves,
  **sourced from the internet/references** — author ORIGINAL questions on the standard topics; cite the
  source in `src`; **never copy ETS items or copyrighted question text**. Agent-drafted content is
  committed as `gen: human` and passes the existing verification gate (`status: verified` + attribution).
- **Bundling the built `.apkg` + first-run auto-import is sub-project B** (separate spec/plan). This
  spec only enlarges the generated corpus + coverage reporting.

## Global constraints

- **No AI / no model-call generation.** Computational cards are SymPy-templated; conceptual cards are
  human-authored (reference-sourced) and pass the verification gate. (PRD §9/§11.)
- **No ETS items, ever.** The ETS practice book / official items are contaminated — author original
  questions on the standard topics only; `src` names the concept source, never an ETS item. (PRD §11/§12.)
- **Determinism & re-runnability.** Same `--seed` ⇒ identical ordered card list; content-derived GUIDs;
  fixed package timestamp. Scaling is a build-time count knob, not runtime generation.
- **Coverage gate stays hard:** all 17 leaves covered; **≥ 50% calculus** by card count; exactly one
  valid `topic::<bucket>::<leaf>` tag per card; build exits non-zero on violation.
- **Uniqueness:** every card stem is distinct; a leaf's template capacity must exceed its target count
  or the build fails loud (never pads with duplicates).
- **No engine change → fast lane.** Pure `pipeline/` change (counts, template ranges/variants,
  conceptual YAML, tests, docs). Nothing under `anki/` or `Anki-Android/`.

## Reference (grounds the conceptual expansion — ETS content outline)

Official GRE Mathematics Subject Test content (ETS fact sheet / practice book): **Calculus 50%**
(differential & integral calculus of one and several variables, applications, coordinate geometry,
trig, differential equations); **Algebra 25%** (elementary; linear — matrix algebra, vector spaces,
linear transformations, eigenvalues; abstract algebra & number theory — groups, rings, modules,
fields); **Additional 25%** (introductory real analysis — sequences/series, continuity,
differentiability, integrability, elementary topology of ℝ/ℝⁿ; discrete math — logic, set theory,
combinatorics, graph theory, algorithms; general topology; complex variables; geometry; probability &
statistics; numerical analysis). We author original conceptual questions across these; we do **not**
reuse any ETS example.

---

## 1. Scope: two workstreams (both in `pipeline/`)

**W1 — Computational scale-up** (`generate_deck.py`, `generate_mcq.py`): raise per-leaf counts to reach
~5,000 flashcards + ~500 MCQ, and ensure each leaf's distinct-instance capacity ≥ ~2× its count.

**W2 — Conceptual expansion** (`conceptual_cards.yaml`): grow from ~20 to ~60 original,
reference-sourced, verified questions across the conceptual leaves (and conceptual linear-algebra:
eigenvalues, vector spaces, linear transformations — which the `linear` computational template omits).

## 2. Allocation (approx; final numbers tuned in the plan to satisfy capacity + calc ≥50%)

| Bucket | Leaves (templated) | ~cards |
|---|---|---|
| Calculus (50%+) | differential_single, integral_single, differential_multi, integral_multi, differential_equations, applications | ~3,600 |
| Algebra | elementary, linear, number_theory (templated) | ~700 |
| Additional | probability_stats, numerical (templated) | ~500 |
| MCQ | differential_single, integral_single, linear, number_theory | ~500 |
| Conceptual (authored) | real_analysis, topology, geometry, complex, discrete, abstract (+ linear-algebra concepts) | ~60 |

→ **~5,360 total**, calculus ≈ 70% by card count (well above the 50% floor).

## 3. Uniqueness / capacity (the core technical requirement)

Each leaf's generator must be able to emit its target count of **distinct** stems. From the current
audit, three templates are **thin** and must be widened before scaling:
- **`differential_equations`** — the `exponential` branch has ~10 distinct instances. Widen `k`'s range
  and add a **second-order / linear-ODE** (or logistic-separable) sub-type.
- **`applications`** — moderate. Widen ranges and add a third sub-type (e.g. average value, or
  velocity→distance).
- **`integral_multi`** — few-thousand cap. Widen coefficient/bound ranges.

Everything else (single-variable poly/trig/exp templates, `differential_multi`, `elementary`,
`linear` det2/det3, `number_theory`, `probability_stats` mean/choose/prob) has ample space once counts
are set within capacity. The generator keeps its per-leaf seeded RNG (and the `::mcq` namespace),
dedupes by stem, and **raises `RuntimeError` if it cannot reach the count** (raise `max_attempts`
proportional to count). A new **capacity/uniqueness test** asserts each leaf reaches its target with all
stems distinct.

## 4. Conceptual expansion (W2) — sourcing + authoring rules

- Author ~40 additional conceptual questions (flashcards and/or `format: mcq`) across the conceptual
  leaves, aiming for ~8–10 per leaf, using the ETS content outline (§Reference) to pick standard topics
  (e.g. eigenvalues, vector-space axioms, ring vs field, uniform continuity, compactness, graph
  connectivity, Bayes/expected value, Taylor series, residues).
- **Original wording**; each record carries `src` naming the concept reference (e.g.
  "original (standard linear-algebra fact)", or a specific textbook/OCW/Wikipedia topic), `gen: human`,
  and passes the verification gate (`status: verified` + `verified_by`/`verified_on`).
- **Never** transcribe an ETS practice item or any copyrighted question. Correctness is paramount — one
  unambiguous correct option, four plausible-but-wrong; keys double-checked.
- These stay in the **study deck** corpus (firewalled from `eval/bank/` — the eval bank's
  `assert_firewall` still must pass, so avoid duplicating an eval stem).

## 5. Tests & gates

- **Scale/uniqueness test:** `load_all_cards(seed=42)` yields ≥ ~5,000 cards; each leaf hits its target
  count; **all stems distinct**; calc weight ≥ 0.50; all 17 leaves covered.
- **Determinism:** same seed ⇒ identical ordered list (extend the existing determinism test to the new
  scale); content hash stable.
- **New-template units:** each new/ widened generator sub-type produces well-formed, correct
  (SymPy-recomputed) cards.
- **Conceptual gate:** existing verification-gate tests still pass on the expanded YAML; a count check
  (`>= ~60` conceptual).
- **Eval firewall:** running `eval/bank` `assert_firewall()` still passes (no study/eval overlap).
- **End-to-end:** `python pipeline/build_deck.py --seed 42` writes the `.apkg`, prints the coverage +
  per-format report, exits 0. Record generation+pack time and `.apkg` size.

## 6. Performance / footprint

~5,000 cards: generation + `genanki` packing should complete in a few seconds; the `.apkg` is expected
to be a few MB (flag the actual size in the PR — it matters for sub-project B, which commits the built
`.apkg` as an app asset). Note if generation time or file size warrants a follow-up.

## 7. Lane, dependencies, out of scope

- **Lane:** fast lane — `pipeline/` only.
- **Feeds:** sub-project B (auto-incorporation) consumes the resulting `.apkg`.
- **Out of scope:** bundling / first-run auto-import (B); the timed simulator; any engine change; P1/P2
  eval partitions; the leakage pipeline.

## 8. Acceptance criteria

- `python pipeline/build_deck.py --seed 42` builds **≥ ~5,000** unique cards, all 17 leaves, calc ≥ 50%,
  gate PASSED, deterministic (stable content hash), `.apkg` written.
- Conceptual set ≥ ~60 verified, attributed, original items (no ETS reuse); eval-bank firewall still holds.
- New/widened templates produce SymPy-correct cards; capacity/uniqueness test green; full `pipeline/tests` green.
- `pipeline/pipeline.md` / `pipeline/README.md` / `docs/codebase/INDEX.md` updated with the new scale + sourcing note.
