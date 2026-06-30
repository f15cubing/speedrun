# Sub-prompt 10 — Olympiad prep: risks, opportunity cost, and practical sequencing

You are a specialist research agent in **instructional design and test preparation**, handling spec Dimensions 4 and 5. Assume the reader has the construct comparison (sub-prompt 08) and the transfer/mechanism evidence (sub-prompt 09). Your job: assess **where olympiad prep is inefficient or harmful for the GRE Math Subject Test**, frame the **opportunity cost** against conventional prep, and produce a **concrete, evidence-tagged recommendation** on whether and how to integrate olympiad-style problems into the app — including a clear recommendation *against* it if the evidence points that way. Do not boost the olympiad idea; follow the evidence.

## Exact question and scope

IN SCOPE:
1. **Risk / inefficiency analysis.** For each, give the mechanism and any supporting evidence:
   - **Difficulty mismatch / over-hard problems**: olympiad items far exceed GRE difficulty; risk of frustration, demoralization, and low return per hour. Tie to learning literature on desirable vs. *undesirable* difficulty and the expertise-reversal / problem-difficulty effects.
   - **Breadth / coverage neglect**: time on deep olympiad topics (combinatorics, NT) may starve the ~50% calculus and broad coverage the GRE actually weights (use coverage findings from sub-prompt 01).
   - **Pacing mismatch**: olympiad trains slow deep work; the GRE rewards ~2.6 min/item triage. Risk of trained-in slowness.
   - **Format mismatch**: proof skill is untested on the MC exam; possible negative transfer of habits (e.g., over-rigor, ignoring answer-elimination).
   - **Opportunity cost & motivation/time**: explicit framing — hours on olympiad vs. hours on targeted GRE-style practice; what does the time-on-task / deliberate-practice literature predict?
2. **Conditional recommendation.** Given SQ08/SQ09 outcomes, specify:
   - **If** there is a defensible role: exactly *how* to sequence olympiad-style problems (dose %, placement in a study plan, which GRE topics they best reinforce, which student level benefits, guardrails to avoid the risks above). Make it concrete enough to implement as an app feature with measurable parameters.
   - **If not**: say so and recommend the higher-yield alternative (targeted GRE-style practice, spaced retrieval on calculus breadth, etc.).
3. **Tie to the project's ablation requirement.** Suggest how an "olympiad-style problem injection" feature could be framed as the learning-science feature with a falsifiable hypothesis and an ablation (coordinate with sub-prompt 04) — or argue why a better-evidenced feature should be chosen instead.

OUT OF SCOPE: re-deriving construct comparison or transfer evidence (assume from 08/09); the scoring models; code.

## Deliverable format and length
- ~1100–1600 words.
- Section A: risk/inefficiency table (risk / mechanism / supporting evidence + strength / severity for a 1-week-to-months GRE prep horizon).
- Section B: opportunity-cost analysis grounded in deliberate-practice / time-on-task literature.
- Section C: the conditional recommendation (decision tree: ship as core / ship as optional supplement with guardrails / don't ship), each branch tagged with the evidence that supports it.
- Section D: how it maps to the ablation feature + a one-sentence falsifiable hypothesis if pursued.

## Sourcing requirements
- Prefer peer-reviewed learning/instructional-design literature (cognitive load theory — Sweller; expertise reversal — Kalyuga; deliberate practice — Ericsson with the critical literature, e.g., Macnamara meta-analyses; desirable difficulties — Bjork) and credible test-prep practitioner analysis (clearly labeled).
- Per claim: source, type, confidence rating; separate empirical from argued.
- Do not overstate effect sizes; report contested findings (e.g., deliberate-practice debates) honestly.

## Counter-evidence / weak-spot demands
- Steelman BOTH sides: (a) the case that olympiad problems are a motivating, schema-deepening supplement; (b) the case that they are a low-yield, demoralizing distraction for a breadth+speed exam. Then weigh them.
- Flag where your recommendation depends on assumptions from 08/09 that were rated weak — make the recommendation contingent and falsifiable.
- Explicitly name the student profile (e.g., already-strong vs. struggling) for which the recommendation flips.

## Source list (REQUIRED, at the very bottom)
End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from, each with author(s)/title/publisher/year and a working link or DOI where available, grouped by type (peer-reviewed / institutional / named expert / practitioner). No uncited claims.

End with a self-confidence summary and a one-line recommendation (ship as core / optional supplement with guardrails / don't ship) with its evidence tag.
