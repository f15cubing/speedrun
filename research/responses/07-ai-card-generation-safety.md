<!-- Raw sub-agent response. Captured: 2026-06-29. Round 1. -->
<!-- Prompt: prompts/07-ai-card-generation-safety.md | Critique: critiques/07-ai-card-generation-safety.md -->
<!-- Do not edit; this is the source record. -->

# Designing a Safety-First AI Flashcard Pipeline for GRE-Math Q&A: Generation, Verification, and a 50-Item Gold Gate

**Bottom line:** An AI card pipeline *with layered verification* — RAG-grounded generation, mandatory source provenance, and decisive symbolic (CAS) checking — can plausibly pass a strict gold-set gate for *computational* GRE-math cards, but only at the cost of rejecting a large fraction of drafts; for definitional/conceptual cards the case is weaker and provenance plus human adjudication must carry the load.

---

## TL;DR

- **Yes, with verification — and only with it.** Deterministic CAS/tool-based checking (SymPy, PAL) is the decisive trust anchor for computational cards; model self-critics are supplementary because they demonstrably rubber-stamp and even introduce errors. Provenance (RAG source binding + verbatim quote anchors + enforced abstention) is what prevents the "untraceable claim" that zeroes out the AI section.
- **The defensible pre-set cutoff is asymmetric:** fact-precision ≥ 0.98 (≤1 wrong-fact card in 50) **and** useful-yield ≥ 0.60 among non-abstained cards, lodged/timestamped before any card is scored. The 2% factual-error ceiling mirrors the human-curation error bar of GSM8K itself.
- **Expect low yield, and accept it.** Because wrong facts are worse than no card, the gate is deliberately strict; stakeholders should plan to generate many drafts per accepted card, and should treat the 50-item gate as a screening gate, not statistical proof of population quality (n=50 has limited power).

---

## Key Findings

1. **Provenance is enforceable by schema, not trust.** Make a verbatim source quote + page/line anchor a hard required field; auto-zero any card lacking an entailed source span before evaluation. Abstention cannot be delegated to the model — it must be pipeline logic.
2. **CAS verification is decisively better than model-based checking for arithmetic/algebra**, and is the single highest-evidence control. It does *not* apply to conceptual/definitional cards, which need entailment-against-source plus human adjudication.
3. **Frontier-model math is fragile in ways that matter for cards.** Performance collapses on superficial perturbations, so a card that "looks right" is not certified right; only re-derivation or source-entailment certifies it.
4. **A fair "beat the baseline" test exists:** paired comparison vs template/cloze extraction (and vs non-RAG prompting), scored with McNemar's exact test plus paired bootstrap CIs.
5. **Leakage must be controlled by isolation, not just detection**, because string-overlap scans miss paraphrased contamination and, for math specifically, no current detector is reliable.

---

## Details

### Section A — Generation with Provenance

The governing rule ("AI claims with no traceable source zero out the AI section") maps directly onto the **attributed text generation** literature. The canonical evaluation frame is **Attributable to Identified Sources (AIS)** (Rashkin et al., 2023, *Computational Linguistics*/TACL-track; peer-reviewed; *high confidence*), where each output sentence scores 1 only if fully supported by its cited source. For span-level traceability, **Slobodkin et al. (2024), "Attribute First, then Generate"** selects source spans *before* generation and emits sub-sentence citations; their user study found sentence-level granularity most useful for human fact-checking (arXiv; *high confidence*). Two complementary paradigms exist: **end-to-end citation** (Tianyu Gao, Yen, Yu & Chen, 2023, "Enabling LLMs to Generate Text with Citations"/ALCE, EMNLP) and **post-hoc** (Luyu Gao et al., 2023, RARR, ACL), which researches and revises claims after generation (both *high confidence*).

For GRE-math cards the concrete provenance controls are: (1) **RAG with source binding** — retrieve the exact textbook section/problem and bind each card to a chunk ID plus page/line anchor; (2) **quote-and-anchor requirement** — every card carries a verbatim quote span; (3) **abstention when support is absent**. Abstention is grounded in **AbstentionBench** (Kirichenko et al., 2025, FAIR/Meta, arXiv; *high confidence*), which finds abstention "an unsolved problem… where scaling models is of little use" and that reasoning fine-tuning can *degrade* it — so abstention must be enforced by pipeline logic. The **TRUST-SCORE / Learning-to-Refuse** work (Song et al., 2024, arXiv; *medium confidence*) operationalizes this: a question is "answerable" only if retrieved documents entail a gold claim; otherwise the gold output is a refusal. **Verdict for A:** make the quote-anchor a hard schema field; any card lacking an entailed source span is auto-zeroed before it reaches evaluation.

### Section B — Gold-Set Evaluation Protocol

Build the 50-item gold set from independently verified Q&A (textbook answer keys cross-checked by a second solver), each item carrying its source anchor. Score the 50 *generated* cards into the three mandated buckets — correct+useful / wrong-fact / correct-but-bad-pedagogy — using a written rubric finalized before generation.

**Pre-registered cutoff.** Preregistration specifies "designs and analysis plans before observing the research outcomes" to prevent "p‑hacking or specification searching" (OSF/Surrey/Australian-Treasury guidance, *high confidence*). The cutoff must be lodged (timestamped) before any card is scored. Because the spec states wrong facts are worse than no card, the gate is **asymmetric**: a hard ceiling on factual errors plus a floor on useful yield. The defensible pre-set: **fact-precision ≥ 0.98 (≤1 wrong-fact card in 50) AND useful-yield ≥ 0.60 among non-abstained cards.** The ≤2% factual ceiling is aligned with the GSM8K human-curation error bar — Cobbe et al. (2021) state verbatim: "After performing extensive quality control based on workers' answer agreement, we estimate that less than 2 percent of problems contain breaking errors" (arXiv 2110.14168; *high confidence*).

**Inter-rater reliability.** Use ≥2 raters; report **Cohen's κ** (two raters) or **Fleiss' κ** (>2), with adjudication of disagreements. Interpretation follows Landis & Koch: 0.61–0.80 "substantial," 0.81–1.00 "almost perfect" (*high confidence*). Shared rubrics raise agreement sharply — one study moved κ from 0.35–0.49 (independent) to 0.53–0.84 (shared rubric) (arXiv 2511.10865; *medium confidence*). Report κ **with raw percent agreement** because of the kappa paradox (high agreement can yield low κ under class imbalance); Gwet's AC1 is a paradox-resistant supplement (Wongpakaran et al., 2013, *BMC Med Res Methodol*; *high confidence*). Subjective dimensions like pedagogy will show lower κ (rubric studies report κ<0.35 for "well-justified rationale"; arXiv 2512.23707; *medium confidence*) — so pedagogy needs explicit scale anchors and adjudication.

### Section C — Detecting Wrong Math Facts (ranked by evidence)

**1. Symbolic/CAS verification (strongest where applicable).** For computational cards, re-derive the answer in **SymPy** and check equality symbolically *and* numerically. FrontierMath (Glazer et al., 2024) verifies via "SymPy evaluation to check that the difference… simplifies to 0" (*high confidence*); SymCode (2025) executes generated SymPy "eliminating arithmetic errors" with a deterministic pass/fail (*medium confidence*). This is **decisively better than model-based checking** for arithmetic/algebra because it is deterministic. Its limit: a SymPy-augmented verifier "struggles with mathematics that is highly abstract or lacks a straightforward algorithmic" implementation (theoretical-physics study, ML4PS 2025; *medium confidence*) — i.e., not applicable to conceptual/definitional cards.

**2. Tool-augmented generation (PAL).** Gao et al. (PAL, ICML 2023) offload computation to a Python interpreter; on **GSM-Hard, PAL scores 61.2% vs CoT's 23.3% — "PaL outperforms CoT by an absolute 40%"** (arXiv 2211.10435, author-reported; *high confidence*). This addresses the documented fact that "LLMs often make logical and arithmetic mistakes… even when the problem is decomposed correctly."

**3. Trained verifiers / process reward.** Cobbe et al. (2021) showed verification "significantly improves performance on GSM8K," letting a 6B+verifier match a 175B baseline (*high confidence*). Lightman et al. (2023, "Let's Verify Step by Step," arXiv 2305.20050) found **process supervision** beats outcome supervision: their process-supervised reward model **"solves 78.2% of problems on a representative subset of the MATH test set"** (Best-of-N) versus the outcome-supervised ORM's 72.4%, and they warn that "models trained with outcome supervision regularly use incorrect reasoning to reach the correct final answer" (*high confidence*) — so a right final answer does not certify a right card.

**4. Self-consistency (Wang et al., 2022/2023, arXiv 2203.11171).** Majority vote over sampled reasoning paths "boosts the performance of chain-of-thought prompting… including **GSM8K (+17.9%), SVAMP (+11.0%), AQuA (+12.2%)**," raising GSM8K from 56.5% (single CoT) to 74.4% with 40 samples (*high confidence*). Useful but probabilistic — consistent-but-wrong answers survive.

**5. RAG-grounded verification.** Check each card claim against its source via NLI entailment; **RAGAS faithfulness** = (claims supported by context)/(total claims) (Es et al., 2023, EACL; *high confidence*). This is the right verifier for *conceptual/definitional* cards where CAS does not apply.

**Failure modes (counter-evidence).** Model-based checking can rubber-stamp or *introduce* errors: intrinsic self-correction "often fails to improve, and can degrade, reasoning accuracy" (Huang et al., 2024; *high confidence*). A single challenger utterance is destabilizing — in the **FlipFlop experiment** (Laban et al., 2024, arXiv 2311.08596) asking "Are you sure?" produced accuracy drops "between −8% (GPT-4) and −34% (Claude V2)" on TruthfulQA (*high confidence*). RiddleBench (arXiv 2510.24932) found Qwen QwQ 32B "failed to identify its own errors in 67.7% of trials, successfully flagging its flawed logic only 17.3% of the time" — well below the 44.1% it achieved evaluating a *peer* — "a powerful self-confirmation bias" (*medium confidence*). A self-critic can also "hallucinate flaws" on easy items, cutting accuracy (Snorkel AI, vendor blog; *low–medium confidence*, vendor-sourced). **Conclusion:** CAS is the trust anchor for computational cards; model critics are supplementary and must never be the sole gate.

**Error profiles differ — and frontier models are fragile.** GRE-math cards span computations, definitions, and theorems, with different failure modes than word problems. **GSM-Symbolic** (Mirzadeh et al., Apple, 2024, arXiv 2410.05229; peer-reviewed/ICLR; *high confidence*) shows models "exhibit noticeable variance when responding to different instantiations of the same question," with worst-to-best gaps of ~12–15% (Gemma2-9B, Phi-3.5-mini) from merely changing names/numbers. Critically, "when we add a single clause that appears relevant to the question, we observe significant performance drops (up to 65%) across all state-of-the-art models, even though the added clause does not contribute to the reasoning chain" — Phi-3-mini fell from 83.7% to 18.0% on GSM-NoOp; even o1-preview dropped (94.9→77.4). The lesson for cards: a generator can be confidently, systematically wrong, so verification must be independent of the generator. For directly comparable educational content, "Can we trust LLMs as a tutor…" (arXiv 2511.04213; *medium confidence*) found **6.99% (167/2,389) of LLM-generated statistics-exam feedback instances contained at least one error**, concentrated in feedback on incorrect student answers — evidence that ungated AI educational content carries a non-trivial factual-error rate.

### Section D — Baseline to Beat

Define a credible **non-AI baseline**: template/cloze extraction directly from the source (structured/regex extraction of a worked example into Q/A with the answer copied verbatim from the key). This is high-precision-by-construction (it copies, doesn't generate) but low-coverage and pedagogically flat — a fair, simpler comparator. A second baseline is **non-RAG vanilla prompting** (no source binding) to isolate the value of retrieval/grounding.

**Metric & test.** Compare on the same 50 gold items (paired design). Primary binary metric: per-item "correct+useful" pass. Use **McNemar's exact test** on discordant pairs (Dietterich, 1998; *high confidence*), which "compares paired responses… focusing on discordant pairs" — the standard for two systems on one fixed test set; apply continuity correction / exact binomial at n=50. Report a **paired bootstrap 95% CI** on the difference in useful-yield and in fact-precision (resampling items with replacement). With n=50, power is limited, so pre-register the minimum detectable effect and treat ties honestly. "AI beats baseline" must mean a statistically significant *and* practically meaningful gain on useful-yield **without** breaching the fact-precision ceiling — a faithful card factory that produces more usable cards than copy-extraction while staying at least as safe.

### Section E — Leakage / Isolation

AI generation can contaminate evaluation two ways: (a) the generator was pretrained on the same textbook/benchmark, inflating apparent accuracy; (b) generated cards leak into any future training/eval set. The literature is direct: GPT-3 used **13-gram overlap** detection; GPT-4 used a 50-character overlap signal (Brown et al., 2020; OpenAI, 2023; *high confidence*). But string matching is fragile — Yang et al. (2023) showed a 13B model trained on *rephrased* MMLU/GSM8K reached 85.9 on MMLU while "undetectable by n-gram overlap," motivating the **LLM Decontaminator** (embedding search + LLM judge; LMSYS, 2023; *high confidence*). For math specifically, MathCONTA (TU Wien thesis, 2025) found that *none* of minK%, n-gram, or CDD reliably detect incidental math contamination (*medium confidence*) — so detection alone is insufficient.

**Isolation controls:** keep the 50-item gold set in a **separate, access-controlled store**; never feed gold items into generation prompts; embed **canary strings** so future leakage is detectable; run an **n-gram + embedding overlap scan** between generated cards and the gold set, discarding near-duplicates; and version/hold-out the gold set so it never tunes the pipeline. Treat paraphrased overlaps as contamination.

---

## Recommendations

1. **Stage 1 — Build with provenance (now).** Implement RAG with source binding; require a verbatim quote span + page anchor as a non-nullable schema field; auto-zero any card whose quote does not entail the claim. Force abstention in pipeline logic, not the prompt.
2. **Stage 2 — Verify by card type.** Route *computational* cards through PAL/SymPy re-derivation (symbolic + numerical equality) as the gate; route *definitional/conceptual* cards through NLI entailment against the source (RAGAS faithfulness) plus mandatory human adjudication. Use self-consistency and a critic model only as pre-filters that *reduce* CAS workload — never as the final gate.
3. **Stage 3 — Pre-register and run the gate.** Lodge the cutoff (fact-precision ≥ 0.98 AND useful-yield ≥ 0.60) and the rubric, timestamped, before scoring. Use ≥2 raters, adjudicate, and report Cohen's/Fleiss' κ **with** percent agreement and Gwet's AC1.
4. **Stage 4 — Prove value over baseline.** Run template/cloze and non-RAG baselines on the same 50 items; require a McNemar-significant useful-yield gain with the fact-precision ceiling intact.
5. **Stage 5 — Isolate and scan.** Air-gap the gold set, seed canaries, and run n-gram + embedding overlap scans, discarding near-duplicates.

**Thresholds that would change the plan:** If fact-precision cannot reach ≥0.98 even after CAS gating, **do not ship** — tighten retrieval/abstention or narrow scope to card types CAS can certify. If useful-yield after gating is so low (e.g., <0.30) that the factory is uneconomic, that is an acceptable *safe* outcome under the spec; revisit generation quality, not the safety ceiling. If conceptual cards cannot clear adjudication with κ ≥ 0.61, restrict the product to computational cards until the rubric is fixed.

---

## Caveats

- **Statistical power:** n=50 is a screening gate, not population proof; small true differences vs baseline may be undetectable. Pre-register the minimum detectable effect and treat the gate as necessary-not-sufficient.
- **CAS coverage:** symbolic checking does not certify conceptual/definitional/theorem-statement cards; those rest on source-entailment and human judgment, which are weaker guarantees.
- **Model-based verification is not trustworthy alone:** the cited self-correction and FlipFlop results show critics can entrench or introduce errors; treat any model-only "approval" as advisory.
- **Generator fragility is real and systematic** (GSM-Symbolic): independent (non-generator) verification is mandatory, not optional.
- **Vendor-sourced items** (Snorkel AI critic-paradox blog) are flagged as such and weighted lower than peer-reviewed/arXiv sources.
- **Yield/safety tradeoff:** a strict gate may reject most drafts. Per the spec this is correct — wrong facts are worse than no card — but it is an explicit cost stakeholders must accept.

## Self-Confidence Summary

- **Well-supported (high confidence):** All named papers and their core quoted claims — RAGAS faithfulness, Cobbe verifiers, Lightman process supervision (78.2% on MATH), Wang self-consistency (+17.9% GSM8K), PAL (61.2% vs 23.3% GSM-Hard), AIS/RARR/ALCE attribution, McNemar's test, 13-gram/LLM decontamination, GSM-Symbolic fragility (up to 65% drop; Phi-3-mini 83.7→18.0), FlipFlop (−8% to −34%), and the GSM8K <2% human-error bar are primary/peer-reviewed and quoted directly.
- **Moderately supported (medium confidence):** specific κ-uplift figures, the exact useful-yield this corpus will achieve, the 6.99% educational-feedback error rate (single study), and CAS coverage limits — direction-correct but corpus/model-dependent.
- **Genuinely uncertain:** the precise pass-rate on conceptual/definitional cards, and whether n=50 yields adequate power — likely not for small effects.

## One-Line Verdict

**Yes — an AI pipeline with mandatory provenance and decisive CAS/tool-based verification can pass a strict gold-set gate for computational GRE-math cards; the defensible pre-set cutoff is fact-precision ≥ 0.98 (≤1 wrong-fact card in 50) plus useful-yield ≥ 0.60 among non-abstained cards, with the explicit expectation of low yield and weaker guarantees on conceptual cards.**
