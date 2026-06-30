# Sub-prompt 02 — Memory model: FSRS mechanics, calibration on held-back reviews, and the limits of recall probability

You are a specialist research agent in spaced-repetition science and probabilistic calibration. The project uses Anki's **FSRS** scheduler as its "Memory" score (probability a student recalls a specific fact now). We must (a) describe FSRS precisely, (b) define how to *calibrate and prove* the memory model on held-back reviews ("when it says 80%, recall is ~80%"), and (c) state honestly what card-level recall probability does and does **not** imply about exam performance.

## Exact question and scope

IN SCOPE:
1. **FSRS model internals.** Describe the DSR (Difficulty, Stability, Retrievability) formulation, how retrievability/recall-probability is computed from stability and elapsed time (the forgetting curve form FSRS uses), the parameter set (the ~17–21 weights), and how parameters are fit per user. Name versions (FSRS v4 / v5 / FSRS-rs) and what changed. Cite the primary sources (Jarrett Ye / "Expertium" and collaborators, the open FSRS repos and the published benchmark).
2. **Predictive accuracy evidence.** Summarize the published FSRS benchmark results comparing FSRS vs. SM-2 vs. other algorithms (metrics: log-loss, RMSE, calibration), including dataset size and who ran it. Distinguish independently-replicated results from author-reported ones.
3. **Calibration methodology.** Define the correct way to *measure* calibration on held-back reviews: train/validation split by time (not random, to avoid leakage across a card's history), reliability diagrams, Expected Calibration Error (ECE), Brier score, log-loss, and how much data is needed for stable estimates. Explain bucketing pitfalls and confidence intervals on calibration curves for a single user.
4. **The conceptual gap to exam performance.** Explain rigorously why "P(recall this card) = 0.8" is NOT the same as "P(answer an unseen exam question on this topic) = 0.8": recognition vs. recall vs. problem-solving, card-level vs. construct-level, memorized fact vs. transferable procedure.

OUT OF SCOPE: implementing FSRS in code, Anki UI, comparison shopping of flashcard apps.

## Deliverable format and length

- ~900–1500 words.
- Section A: FSRS model description (precise enough to explain to a grader).
- Section B: evidence table on predictive accuracy (algorithm, metric, dataset, who, replicated?).
- Section C: a concrete calibration-evaluation recipe we can implement on held-back reviews, including the exact metrics and how to plot the reliability diagram and what counts as "calibrated."
- Section D: the recall-vs-exam-performance gap, with named cognitive-science backing (e.g., retrieval-practice and transfer literature).
- Section E: minimum-data caveats for single-user calibration.

## Sourcing requirements

- **Source list (REQUIRED, at the very bottom):** End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from, each with author(s)/title/publisher/year and a working link or DOI where available, grouped by type (peer-reviewed / institutional / named expert / practitioner). No uncited claims.

- Prefer: peer-reviewed memory/psychometric papers; the FSRS benchmark paper/preprint and repo; named authors (Jarrett Ye and collaborators). For calibration metrics, cite primary statistics/ML sources (e.g., reliability diagrams, Brier 1950, ECE references).
- Practitioner/GitHub sources admissible only if author is identified and credible; mark as practitioner evidence.
- Per claim: source, type, confidence rating (e.g., `[high — FSRS benchmark, ~10k+ collections, independently citable]` vs `[moderate — author blog]`).
- Never invent benchmark numbers. If exact figures aren't verifiable, give the qualitative finding and mark the number unverified.

## Counter-evidence / weak-spot demands

- Address: is FSRS's calibration advantage robust on **small/single-user** datasets, or does it depend on large aggregate fits? What happens with cold-start (few reviews)?
- Surface any critiques of FSRS or of self-reported benchmarks (selection bias, who controls the benchmark, whether comparisons are apples-to-apples).
- Be explicit that good card-level calibration is **necessary but not sufficient** for a trustworthy exam-readiness number — this is the seam where the project's "bridge" assumption lives.

End with a self-confidence summary and a one-line verdict: can we credibly claim a calibrated memory model on one week of one student's data?
