# Sub-prompt 07 — AI card generation: safety, factual accuracy, and the 50-item gold-set quality gate

You are a specialist research agent in **LLM evaluation, factual-accuracy/hallucination measurement, and content provenance**, focused on generating **GRE-math flashcards** from source material. The spec is strict: wrong facts are worse than no card; AI claims with no traceable source zero out the AI section; AI must beat a simpler baseline; and a 50-item gold-set gate with a *pre-set* cutoff is required. Design the generation + evaluation system and surface where LLM math content fails.

## Exact question and scope

IN SCOPE:
1. **Generation with provenance.** Methods to generate math Q&A cards from a real source (textbook section, problem set) such that every card is **traceable to its source** (citations/quotes/page anchors, retrieval-augmented generation with source binding). What concretely prevents "untraceable claims"?
2. **Gold-set evaluation protocol (challenge 7f).** How to build a 50-item gold set of known-correct Q&A; how to score 50 generated cards into: correct+useful / **wrong fact** / correct-but-bad-pedagogy; how to set a defensible **passing cutoff before** seeing results; inter-rater process; and the right metrics (precision on facts, useful-yield rate).
3. **Detecting wrong math facts.** Techniques to catch factual errors in generated math: verification via a symbolic/CAS check (SymPy) or a solver, self-consistency / multi-sample agreement, an independent "critic" model, retrieval-grounded verification against the source. What error rates does the literature report for LLM-generated math/educational content, and which verification methods measurably reduce them? Cite named studies/benchmarks (e.g., math reasoning benchmarks, hallucination-rate studies, factuality eval frameworks).
4. **Baseline to beat (Friday milestone).** Define a credible *simpler* baseline (e.g., template/cloze extraction from the source, or non-RAG vanilla prompting) so "AI beats baseline" is a fair, measurable comparison — specify the metric and test.
5. **Interaction with leakage (challenge 7e).** How AI generation could accidentally introduce test items into training/eval, and how the gold set + leakage scan must be kept isolated.

OUT OF SCOPE: scoring models, Rust, sync.

## Deliverable format and length

- ~1100–1600 words.
- Section A: provenance-preserving generation design (RAG with source binding).
- Section B: gold-set eval protocol + pre-set cutoff rationale + rubric.
- Section C: wrong-fact detection methods, ranked by evidence of effectiveness, with reported error rates and citations.
- Section D: baseline definition + fair-comparison metric.
- Section E: leakage/isolation safeguards for the eval.

## Sourcing requirements

- **Source list (REQUIRED, at the very bottom):** End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from, each with author(s)/title/publisher/year and a working link or DOI where available, grouped by type (peer-reviewed / institutional / named expert / practitioner / vendor). No uncited claims.

- Prefer peer-reviewed / arXiv evaluation papers and reputable benchmarks (math reasoning, factuality/hallucination, RAG faithfulness — e.g., works on GSM8K/MATH, hallucination surveys, RAGAS/faithfulness metrics), and named researchers.
- Vendor model cards/docs admissible for capability claims but mark as vendor-sourced.
- Per claim: source, type, confidence rating. Report error-rate numbers only with a citation; otherwise give qualitative direction and mark unverified.
- Never invent benchmark scores.

## Counter-evidence / weak-spot demands

- Be candid about **LLM math reliability**: even strong models make confident arithmetic/symbolic errors; quantify with cited rates and note that GRE-math cards (definitions, theorems, computations) have different error profiles than word problems.
- Flag the danger that verification methods (self-consistency, critic models) have their **own** failure modes and can rubber-stamp errors; note where CAS/symbolic verification is decisively better than model-based checking.
- Address whether a strict gate could reject so many cards that yield is impractical — and why, per spec, that is the correct safe tradeoff.

End with a self-confidence summary and a one-line verdict: can an AI card pipeline with verification pass a strict gold-set gate, and what cutoff is defensible?
