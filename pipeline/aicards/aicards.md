# AI card pipeline + gold-set gate

> Co-located doc for `pipeline/aicards/`. Read this before changing anything here.
> Authoritative for this directory (see `.cursor/skills/codebase-docs`).

## Purpose

The AI card pipeline (PRD §9): generate GRE-math flashcards from a source chapter
with **RAG + provenance-by-schema**, **abstain in-pipeline**, **verify** each card
(SymPy CAS for computational, NLI-proxy + mandatory human review for conceptual),
and score the batch against a **pre-lodged gold-set gate** (fact-precision ≥ 0.98
AND useful-yield ≥ 0.60) with two raters + Cohen's κ. It is a **content/data
pipeline** — no engine/Rust change, nothing imports `anki/`.

**AI-off status (honest):** no live-model API key is available in this environment,
so — exactly as the compressed plan permits — the *full machinery* (retrieval,
provenance enforcement, abstention, CAS/NLI verification, the scoring harness with κ,
and the firewall) is real and unit-tested, and it is driven by a **deterministic
stub generator** standing in for the LLM. The gate is run on the stub and the honest
"no live model" status is documented here and in the report. Going live is a
one-file change (`orchestrator.LlmBackend`); nothing downstream changes.

## Public interface

- `sources/single_variable_calculus.md` — the committable, **original** RAG source
  chapter (same *subject* as the held-out MIT-OCW gold-set, but original text — train
  and test share the topic, never the items). Contains no ETS/GRE markers and no
  canary (firewall).
- `corpus.py` — parse the chapter into anchored `Passage(id, heading, text)`;
  `load_corpus()`, `PASSAGES`, `PASSAGE_BY_ID`, `quote_in_passage(anchor, quote)`
  (whitespace-normalised **verbatim** match), `passages_containing(quote)`,
  `corpus_text()`.
- `provenance.py` — `Provenance(quote, anchor)` (a frozen dataclass with **no
  defaults** → non-nullable), `check()`/`is_valid()`: a card is grounded iff quote
  and anchor are both non-blank AND the quote is verbatim in the anchored passage.
- `retriever.py` — deterministic TF-IDF cosine `Retriever`; `retrieve(query, k)`.
  Lexical on purpose (no embeddings/network → byte-stable, PRD §11); the interface a
  neural retriever would slot into unchanged.
- `verify.py` — `verify_computational(check, claimed)` (symbolic CAS re-derivation),
  `numeric_check(...)` (independent numeric probe), `recompute(check)`,
  `entailment_score`/`entails` (NLI **proxy**), `needs_human_review(card)`.
- `cards.py` — `GeneratedCard` (front/back, `provenance`, `check` SymPy payload kept
  separate from rendered text, `gen="ai"`, `status`); `COMPUTATIONAL`/`CONCEPTUAL`.
- `stub_model.py` — `StubBackend` (deterministic stand-in LLM: `plan()` + `build()`);
  transparent `COMPOSITION`. RAG-grounded (lifts quotes from retrieved passages) and
  adversarial on purpose (emits wrong / hallucinated-quote / answer-leaking /
  un-entailed cards so the gates have something to catch). `OP_QUERY` foregrounds each
  operation's own discriminating terms (no shared "power rule" collision), and
  `pick_sentence(passage, query, op=None)` applies an **operation guard**
  (`OP_DISCRIMINATORS`): a card's quote must share its operation's vocabulary, so a
  derivative card can't be grounded on an integration sentence (or vice-versa). The
  `op` arg is optional/backward-compatible (falls back to plain query overlap).
- `orchestrator.py` — `run_pipeline(backend)` → ordered `Outcome`s with a `Decision`
  (`PUBLISH_VERIFIED` / `DRAFT_HUMAN_REVIEW` / `ABSTAIN_*`); `classify(card)`;
  `decision_counts`, `published`, `human_review_drafts`, `abstained`; the live-model
  seam `LlmBackend` (raises `NoLiveModelError` when no key); `run_pipeline_safe(backend)
  → AiOffResult` (the **AI-off degradation** wrapper: aborts cleanly with 0 cards when
  no model).
- `stub_model.make_computational_instance(op, rng) → CompInstance` — the **shared
  generation core** (SymPy builds problem + answer) reused by both the AI arm and the
  beat-baseline arm, so the comparison isolates the *pipeline*, not the templates.
- `mcnemar.py` — pure-stdlib exact paired test: `mcnemar_exact(b, c) → McNemarResult`
  (two-sided binomial p-value, `math.comb`, no scipy), `discordant_table(pairs)`,
  `mcnemar_from_pairs`, `paired_bootstrap_ci(a_flags, b_flags, seed)` (deterministic
  90% CI for the usable-rate difference).
- `baseline.py` — the **beat-the-baseline** comparison: `build_targets(seed)` (shared
  targets, declared `TARGET_COMPOSITION`), `ai_card`/`baseline_card`, `beat_baseline(seed)
  → BaselineReport` (per-arm `ArmMetrics` fact-precision/useful-yield, the 2×2 table,
  `McNemarResult`, `yield_diff_ci`, `ai_beats_baseline`), `summarize_pairs(...)`.
- `run_gate.py` / `run_baseline.py` — the two one-command CLIs (below).
- `goldset_gate.py` — **lodged cutoffs** `FACT_PRECISION_MIN=0.98`,
  `USEFUL_YIELD_MIN=0.60`; `rate_a`/`rate_b` (the two raters), `cohens_kappa`,
  `percent_agreement`, `run_gate(outcomes) → GateResult` (`.format_report()`,
  `.as_dict()`).
- `firewall.py` — `read_canary_guid()`, `scan_corpus`, `scan_generation_inputs`,
  `scan_outputs`, `generation_modules_referencing_heldout`, `run_firewall(...)`.
- `run_gate.py` — one-command CLI (`make ai-gate`): run pipeline → gate → firewall,
  print the report, write `out/gate_report.{json,md}`.
- `run_baseline.py` — one-command CLI (`make ai-baseline`): the two A-gated proofs —
  beat-the-baseline (McNemar) + AI-off degradation — printed + written to
  `out/baseline_report.{json,md}`.

## Dependencies

- External (already pinned in `pipeline/requirements.txt`): `sympy` (CAS verify),
  stdlib only otherwise. `pytest` for tests. **No network, no model calls, no new
  dependency.** (`genanki`/`PyYAML` are unused by this subpackage.)
- Internal: flat imports; reuses the sibling `retriever.tokenize`. Reads the
  committed `eval/goldset/canary-manifest.md` (the GUID) for the firewall — **never**
  the gitignored `eval/goldset/data/`.
- Not an engine/Rust change; nothing here touches `anki/` or `Anki-Android/`.

## Gotchas & invariants

- **Provenance is non-nullable and verbatim.** A card without a quote + anchor, or
  whose quote is not found verbatim in its anchored passage, is dropped
  (`ABSTAIN_NO_PROVENANCE`) *before* any other check. Abstention lives in pipeline
  logic, never in a prompt.
- **CAS is decisive for computational cards.** A wrong computational answer cannot be
  published — so computational fact-precision is 1.0 *by construction*; the cost is
  yield, not safety. The independent numeric probe (Rater B) audits this.
- **Conceptual cards are never auto-verified.** Entailment is a *necessary* NLI-proxy
  filter only; passing cards are emitted as `status: draft` + `gen::ai` for
  **mandatory human review** (the same gate as `pipeline/conceptual_cards.yaml`), and
  are **excluded from the verified counts** so they never inflate precision/coverage.
- **Firewall (train/test never share items).** The held-out gold-set + eval-bank
  answers must never enter generation. Enforced re-runnably off the *committed* canary
  GUID (not the gitignored data): corpus + generation inputs + outputs are canary- and
  ETS-free; every card anchors to a `svc-*` corpus passage (never a `gNNN` gold id);
  the generation modules never reference the held-out store paths.
- **Operation-aware grounding.** Retrieval + `pick_sentence` must never cross
  differentiation and integration. The derivative passage (`svc-03-power-rule`) and
  the integral passage (`svc-10-integral-of-a-power`) share "power rule … x raised to
  the power n"; `OP_QUERY` disambiguates on each op's own terms and `pick_sentence`'s
  `op` guard restricts to sentences carrying the operation's discriminating tokens
  (ties break toward MORE such tokens). Conceptual fixtures must be grounded
  consistently with their leaf tag (e.g. an FTC/definite-integral quote is
  `integral_single`, not `real_analysis`; the "differentiable ⇒ continuous" fact
  grounds in `svc-01`, not the Mean Value Theorem). Locked by
  `tests/test_pick_sentence.py` + `tests/test_retriever.py`.
- **Determinism.** Fixed seed ⇒ identical run (stub RNG, retriever, numeric-probe
  sample points all seeded). One command: `make ai-gate`.
- **AI-off honesty.** The gate PASSES on the deterministic stub; those numbers
  validate the *machinery*, not a live model. A real-LLM run is pending API access.

## Results (deterministic stub, seed 42 — AI-off)

Reproduce: `make ai-gate` (or `AI_PY=<python-with-sympy> make ai-gate`).

- Generated 50 candidates → **35 published** (verified computational) · **5 conceptual
  human-review drafts** · **10 abstained** (4 wrong-fact caught by CAS, 3 ungrounded
  dropped by provenance, 3 un-entailed/borderline conceptual).
- **fact-precision = 1.0000** (≥ 0.98 ✓), confirmed by the independent numeric-probe
  rater (also 1.0000). **useful-yield = 0.64** (≥ 0.60 ✓); 0.80 among non-abstained.
- **Inter-rater reliability:** Rater A vs Rater B — **98.0% agreement, Cohen's κ =
  0.938** (they differ only on one borderline conceptual card, by design of their
  different entailment thresholds). Rater B is a **deterministic proxy, not a human**.
- **Safety recall = 1.0** (every rater-flagged wrong computational card was abstained).
- **Firewall: PASS** (all 8 checks). **GATE: PASSED.**

## Proofs — beat-the-baseline + AI-off degradation (execution-plan Block C)

Reproduce: `make ai-baseline` (deterministic; `out/baseline_report.{json,md}` byte-stable).

### 1. Beat-the-baseline (McNemar exact test)
The **AI-pipeline arm** (RAG + provenance + CAS + abstain) vs. a **baseline arm**
(template/cloze, non-RAG, **no** verify/abstain), over the **same shared SymPy targets**
(only the pipeline differs), scored by the **same rater** (`goldset_gate.rate_a`).
Usable = published/emitted AND rated CORRECT.

| arm | fact-precision | useful-yield |
|---|---|---|
| **AI-pipeline** (RAG+provenance+CAS+abstain) | **1.000** | **0.833** |
| baseline (template/cloze, non-RAG, no verify) | 0.600 | 0.400 |

Paired 2×2: a=20 (both usable) · **b=30** (AI-only wins) · **c=4** (baseline-only) ·
d=6 (neither). **McNemar exact two-sided p = 6.165e-06**, favoring the AI arm; the
useful-yield-difference 90% bootstrap CI (AI − baseline) = **[0.300, 0.567]** (excludes
0). **The AI pipeline beats the baseline with the fact-precision ceiling intact (1.000
≥ 0.98).** The baseline emits 24/60 wrong-fact cards (no CAS/abstention to stop them);
the AI arm publishes 0 wrong. AI-off caveat: this validates the **machinery** (RAG +
verify + abstention vs. naive), not a live model — the outcome categories are a declared
fixture, but every card is really generated + scored and the McNemar math runs on real
labels. Honest-null language triggers automatically if a run does not reach `alpha=0.05`.

### 2. AI-off degradation (graceful with no model / no network)
With no API key, `orchestrator.run_pipeline_safe(LlmBackend())` returns
`ok=False`, **0 cards emitted, 0 unverified shipped**, and a clear message — the seam
fails loudly and the pipeline aborts cleanly instead of emitting ungrounded content.
The **study/review deck and the `scoring/` layer are unaffected**: they are build-time /
read-time and never call a model or the network (asserted by `test_degrade.py`, incl. a
static guard that `scoring/` never imports the generator or a model/network client). AI
is a **build-time content pipeline, not a runtime dependency** — pulling the network
turns generation off without touching review or scoring.

## Related tests

- `tests/test_corpus.py` — passage anchoring; verbatim quote match across line-wrapping.
- `tests/test_provenance.py` — non-nullable + verbatim enforcement (missing/blank/
  ungrounded/wrong-anchor all rejected).
- `tests/test_retriever.py` — TF-IDF retrieval, determinism, top-k ordering; the
  `diff` query never ranks the integral-of-a-power passage ahead of the derivative
  passage, and the `antideriv` query never tops out on the derivative power-rule passage.
- `tests/test_pick_sentence.py` — the operation guard: for each op, grounding on the
  confusable derivative/integral power-rule passages returns the operation-correct
  sentence; backward-compatible with no `op`; full-plan cards never cross operations.
- `tests/test_verify.py` — CAS (diff/antideriv/defint/gcd), numeric probe, NLI-proxy,
  human-review routing.
- `tests/test_pipeline.py` — decision counts; only grounded + CAS-verified cards
  publish; wrong facts never publish; drafts are conceptual + flagged; determinism;
  `LlmBackend` fails loudly without a key.
- `tests/test_gate.py` — κ math (perfect + hand-computed), rater distributions, gate
  metrics + pass, and the gate FAILS on a wrong-fact / low-yield batch (it has teeth).
- `tests/test_firewall.py` — canary/ETS/OCW-URL free; anchors all from the corpus;
  generation never references the held-out store.
- `tests/test_mcnemar.py` — exact test math (sign test, known values, symmetry → p=1,
  large discordant → tiny p, direction, p∈[0,1]); paired bootstrap CI determinism.
- `tests/test_baseline.py` — declared target composition; AI arm never publishes a wrong
  fact (precision 1.0); baseline leaks wrong facts (precision 0.60); per-arm yields;
  b/c counts + McNemar favors AI; bootstrap CI excludes 0; same rater harness for both
  arms; determinism; **honest-null** when the arms are equal.
- `tests/test_degrade.py` — no key → seam raises; `run_pipeline_safe` aborts with 0
  cards / 0 unverified + clear message; study deck + `scoring/` load with no model; a
  static guard that review/scoring code never imports the generator or a model/network client.

## `make` targets
- `make ai-gate` — pipeline + gold-set gate + firewall (writes `out/gate_report.*`).
- `make ai-baseline` — beat-the-baseline (McNemar) + AI-off degradation (writes `out/baseline_report.*`).
- `make ai-gate-test` — the full `pipeline/aicards/tests` suite (76 tests).
(All accept `AI_PY=<python-with-sympy>`; seed 42; byte-reproducible.)

---
Last verified against: `main` (merged as `f15cubing/speedrun#34`, commit `3f68a46`)
+ uncommitted working-tree fix: operation-aware grounding (`OP_QUERY`/`OP_DISCRIMINATORS`
disambiguation, `pick_sentence` `op` guard, two conceptual-fixture regroundings; gate
numbers unchanged — 35 published / 5 drafts / 10 abstained, precision 1.0, yield 0.64).
