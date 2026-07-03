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
  un-entailed cards so the gates have something to catch).
- `orchestrator.py` — `run_pipeline(backend)` → ordered `Outcome`s with a `Decision`
  (`PUBLISH_VERIFIED` / `DRAFT_HUMAN_REVIEW` / `ABSTAIN_*`); `classify(card)`;
  `decision_counts`, `published`, `human_review_drafts`, `abstained`; the live-model
  seam `LlmBackend` (raises `NoLiveModelError` when no key).
- `goldset_gate.py` — **lodged cutoffs** `FACT_PRECISION_MIN=0.98`,
  `USEFUL_YIELD_MIN=0.60`; `rate_a`/`rate_b` (the two raters), `cohens_kappa`,
  `percent_agreement`, `run_gate(outcomes) → GateResult` (`.format_report()`,
  `.as_dict()`).
- `firewall.py` — `read_canary_guid()`, `scan_corpus`, `scan_generation_inputs`,
  `scan_outputs`, `generation_modules_referencing_heldout`, `run_firewall(...)`.
- `run_gate.py` — one-command CLI (`make ai-gate`): run pipeline → gate → firewall,
  print the report, write `out/gate_report.{json,md}`.

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

## Related tests

- `tests/test_corpus.py` — passage anchoring; verbatim quote match across line-wrapping.
- `tests/test_provenance.py` — non-nullable + verbatim enforcement (missing/blank/
  ungrounded/wrong-anchor all rejected).
- `tests/test_retriever.py` — TF-IDF retrieval, determinism, top-k ordering.
- `tests/test_verify.py` — CAS (diff/antideriv/defint/gcd), numeric probe, NLI-proxy,
  human-review routing.
- `tests/test_pipeline.py` — decision counts; only grounded + CAS-verified cards
  publish; wrong facts never publish; drafts are conceptual + flagged; determinism;
  `LlmBackend` fails loudly without a key.
- `tests/test_gate.py` — κ math (perfect + hand-computed), rater distributions, gate
  metrics + pass, and the gate FAILS on a wrong-fact / low-yield batch (it has teeth).
- `tests/test_firewall.py` — canary/ETS/OCW-URL free; anchors all from the corpus;
  generation never references the held-out store.

---
Last verified against: agent/ai-pipeline
