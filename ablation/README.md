# Interleaving ablation — analysis machinery (D5)

> Co-located doc for `ablation/`. Read this before changing it.

## Purpose
The **analysis** half of the pre-registered interleaving ablation (PRD **D5**, **Appendix B**,
locked 2026-06-30). Given the **within-subject** arm scores (interleaved ON vs blocked OFF) on the
delayed test of novel mixed-topic items, it computes the paired effect + a **90% CI** (paired
bootstrap) and runs the pre-registered **TOST equivalence** against the ±**SESOI = dz 0.3** (converted
to raw score units at the observed paired SD), then emits the **honest-null verdict template**.

Per Appendix B the deliverable is *the design + the analysis machinery + an honest inconclusive
result*: **a pre-registered null (or inconclusive) result scores; a post-hoc hypothesis does not.**
With team-size *n* the run is powered only for large effects, so it is explicitly an
**estimation/feasibility pilot**, reported honestly.

## The pieces (`ablation/analysis.py`)
- `paired_diffs(interleaved, blocked)` — per-subject differences (equal-length arms).
- `cohen_dz(diffs)` — standardized paired effect.
- `bootstrap_ci(diffs, level=0.90, seed=42)` — percentile bootstrap CI (deterministic, stdlib; same
  approach as `proofs/paraphrase.py`).
- `tost_verdict(ci_low, ci_high, sesoi_raw)` — `equivalent` / `meaningful_effect` /
  `directional_effect` / `inconclusive` from the CI vs the ±SESOI band.
- `min_detectable_dz(n)` — honest power note (team-size only powers large dz).
- `analyze(...) -> AblationResult` and `honest_null_template(result)` — the reported paragraph.
- `demo_dataset(seed, n)` — **synthetic** pilot data (clearly labelled) to exercise the machinery.

## Run
```
make ablation-analysis            # synthetic pilot demo -> honest inconclusive report
python ablation/analysis.py --seed 42 --out docs/evidence/proofs/ablation_demo.json
```
Feed real arm scores to `analyze(interleaved, blocked)` when the ablation run happens (the run itself
needs human subjects and is CUT-FIRST per STATUS; the **ordering** machinery it pairs with is
`pipeline/interleave.py`).

## Boundaries
Pure stdlib + deterministic. Analyses *provided* arm scores only — it does **not** touch the three
learner scores, the scoring definitions, the held-out eval bank, or the Anki engine.

## Evidence basis
Interleaving effect sizes: Rohrer et al. 2020 (classroom d≈0.83, confounded with spacing); Brunmair &
Richter 2019 (math g≈0.34). Honest incremental caveat over an already-spaced app: **dz≈0.2–0.35**
(PRD D5); the pre-registration (Appendix B) sets SESOI dz 0.3 and mandates the honest-null template.
