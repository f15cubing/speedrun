# Sub-prompt 04 — Learning-science study feature + a valid one-week ablation

You are a specialist research agent in the **science of learning** (cognitive psychology of memory and instruction) and experimental design. The project must ship ONE study feature grounded in learning science and prove it with an **ablation** (full app / feature-off / plain Anki) on the same learners, questions, and study time, reporting null results honestly. Your job: rank the candidate features by *evidence strength and transfer relevance to a timed multiple-choice math exam*, and design an ablation that is statistically honest given a 1-week, small-n reality.

## Exact question and scope

IN SCOPE:
1. **Candidate features, ranked by evidence.** For each of: **interleaving**, **retrieval practice / testing effect**, **spaced practice / distributed practice**, **worked-example → faded practice**, **desirable difficulties**, and (optional) **error-driven/feedback timing** — give:
   - The core finding and the **best meta-analytic effect size** (Cohen's d / g) with the citation (e.g., Dunlosky et al. 2013; Rohrer & Taylor on interleaving; Roediger & Karpicke on testing effect; Cepeda et al. on spacing).
   - **Transfer distance**: is the evidence for *near* transfer (same/similar items) or *far* transfer (novel problems, timed standardized exam)? Be explicit — this is the crux.
   - Domain match: how much of the evidence is in **mathematics / problem-solving** specifically vs. vocabulary/facts.
2. **Recommendation** for which single feature gives the best evidence-to-implementation-effort ratio for THIS app (Anki-based, GRE math), with the one-sentence falsifiable hypothesis to pre-register before testing.
3. **Ablation design.** Specify: assignment (within-subject vs between-subject) given tiny n; what to hold constant (questions, study time); the outcome measure (accuracy on held-out exam-style items, not on studied cards); the statistic and an honest **power analysis** — i.e., state plainly how many learners would be needed to detect the expected effect, and therefore what a 1-week run can and cannot show. Provide the honest-null reporting template.

OUT OF SCOPE: the GRE content list, the scoring models, code.

## Deliverable format and length

- ~1000–1500 words.
- Section A: evidence table (feature / effect size + citation / near-or-far transfer / math-domain evidence / implementation effort).
- Section B: recommendation + pre-registered hypothesis sentence.
- Section C: ablation protocol + power analysis + null-result reporting template.

## Sourcing requirements

- **Source list (REQUIRED, at the very bottom):** End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from, each with author(s)/title/publisher/year and a working link or DOI where available, grouped by type (peer-reviewed / institutional / named expert / practitioner). No uncited claims.

- Prefer peer-reviewed meta-analyses and the canonical primary studies. Name the researchers and note where they disagree (e.g., debates on interleaving's boundary conditions, contextual-interference limits).
- Per claim: source, type, confidence rating (e.g., `[high — meta-analysis, k>20 studies]` vs `[moderate — single lab study]`).
- Do not inflate effect sizes; report ranges and heterogeneity where the literature is mixed.

## Counter-evidence / weak-spot demands

- **Transfer is the key skeptical lens.** Many robust effects are demonstrated for *near* transfer; explicitly flag where evidence for *far* transfer to a timed standardized math exam is weak or absent. If the best-evidenced technique has weak far-transfer support, say so — do not paper over it.
- Surface boundary conditions and failures (e.g., interleaving can hurt when categories are too dissimilar; testing effect depends on feedback; spacing gains depend on retention interval).
- Be explicit that a 1-week, few-learner ablation is likely **underpowered**, and that the spec rewards an honest underpowered/null report over a "feels better" claim. Provide the language to report this credibly.

End with a self-confidence summary and a one-line verdict on which feature to ship and whether a meaningful effect is detectable in the available window.
