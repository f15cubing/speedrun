# Sub-prompt 03 — Performance + Readiness: predicting unseen-question accuracy, paraphrase/leakage tests, and an honest 200–990 conversion

You are a specialist research agent in **psychometrics, item-response theory, and predictive-model calibration**. This is the highest-risk part of the project. We must turn study-derived signals into two scores beyond memory: **Performance** (P(correct on a new, unseen exam-style question)) and **Readiness** (projected GRE 200–990 score with a range and confidence). Your job is to determine which methods are *defensible* and to design the validity tests, **not** to overpromise.

## Exact question and scope

IN SCOPE — answer all four:

1. **Performance model.** What is a sound, citable method to predict P(correct on an unseen exam-style item) from: per-topic mastery (from the memory model), item difficulty, response timing, and topic coverage? Compare candidate approaches with their assumptions and data requirements:
   - Item-Response Theory (1PL/Rasch, 2PL, 3PL) and what it needs (item calibration sample sizes).
   - A calibrated supervised classifier (logistic/GBM) with held-out evaluation.
   - Hierarchical/Bayesian estimation giving credible intervals from sparse data.
   State, for each, the minimum data to be trustworthy and the failure modes with a single student.

2. **Paraphrase test design (project challenge 7d).** Specify a rigorous protocol: 30 cards × 2 reworded exam-style questions each; how to compute "original-card recall" vs "reworded-question accuracy"; the correct statistic to compare them (paired, with CI); and crucially, the **decision rule** that distinguishes "the performance model copies the memory model" (gap ≈ 0) from "a real bridge exists." Address confounds: item difficulty drift between original and reworded, small-n, ceiling/floor effects.

3. **Leakage detection (challenge 7e).** Specify a method/script design to flag test items (or near-duplicates) that leaked into training data: exact-match, normalized-text match, n-gram/Jaccard, and **semantic** near-duplicate detection (embeddings + threshold). What threshold, what review step, and how to report it so a grader trusts the held-out split.

4. **Readiness conversion to 200–990 with honest uncertainty (Steps 3 + honesty rule).** Given a performance estimate, what is a *documented, defensible* method to map to the ETS scale, and how to attach a **range** and **confidence**? Cover:
   - The hard problem: ETS equates each form and may not publish a stable raw→scaled table (coordinate with findings from sub-prompt 01). If no public mapping exists, what is the most honest approximation (e.g., map predicted raw-correct distribution → published percentile/scale anchors, propagate uncertainty), and how to caveat it.
   - Uncertainty propagation: how to turn model + sampling + coverage uncertainty into a credible interval (Bayesian posterior, bootstrap, conformal prediction).
   - The **give-up rule**: justify a concrete threshold (e.g., ≥200 graded reviews AND ≥50% topic coverage) and discuss how to set it non-arbitrarily.
   - How to report "how accurate past predictions have been" when you have ~no longitudinal data (honest answer: you mostly can't yet — say how to communicate that).

OUT OF SCOPE: building the GRE content list (sub-prompt 01), FSRS internals (sub-prompt 02), UI design.

## Deliverable format and length

- ~1200–1800 words.
- Section A: performance-model options table (method / assumptions / min data / failure modes / verdict for our setting).
- Section B: paraphrase-test protocol with the explicit decision rule and stats.
- Section C: leakage-detection design with concrete thresholds.
- Section D: readiness-conversion method + uncertainty propagation + give-up rule justification.
- Section E: a blunt "what is and isn't honestly claimable in one week" verdict.

## Sourcing requirements

- **Source list (REQUIRED, at the very bottom):** End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from, each with author(s)/title/publisher/year and a working link or DOI where available, grouped by type (peer-reviewed / institutional / named expert / practitioner). No uncited claims.

- Prefer peer-reviewed psychometrics (IRT: Lord, Embretson & Reise; equating: Kolen & Brennan), calibration/ML literature (Platt scaling, isotonic, conformal prediction — Vovk/Shafer/Angelopoulos), and Bayesian methods (Gelman et al.).
- ETS technical documentation for scaling/equating where available.
- Per claim: source, type, confidence rating. Mark anything about ETS's *specific* current conversion as unverified if not public.
- Never fabricate a conversion table or a validity coefficient.

## Counter-evidence / weak-spot demands

- State plainly if there is **no defensible way** to anchor to 200–990 without proprietary ETS norms, and what the fallback honest framing is.
- Address the real risk that honest credible intervals will be **so wide** the readiness number is near-useless — and whether that is actually the correct, grade-rewarded outcome per the spec.
- Warn about over-fitting/leakage when item difficulty is itself estimated from the same small sample used to validate.
- Identify where teams typically fool themselves (training on test items, paraphrase items that are too close to originals, treating IRT as valid below its sample-size requirements).

End with a self-confidence summary and a one-sentence recommendation on whether to ship a readiness *number* or only a readiness *range + evidence panel*.
