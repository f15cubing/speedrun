# Sub-prompt 11 — Designing the shared held-out GRE-style evaluation item bank (serves SQ3, SQ4, SQ7)

You are a specialist research agent in **educational measurement and test construction**. Three separate parts of this project all depend on one artifact that no prior research pass actually designed: a **held-out set of GRE-Mathematics-Subject-style assessment items** used as the common outcome measure. It is needed for (1) validating the **Performance model** (predicting accuracy on unseen items — SQ3), (2) the **paraphrase/transfer test** (SQ3 challenge 7d), (3) the **learning-science ablation's** common delayed post-test (SQ4), and (4) is the cousin of the **AI gold set** (SQ7). Your job: specify how to build this item bank so it is *valid, difficulty-appropriate, leakage-isolated, and reusable* across all four uses — in a one-week, tiny-sample reality.

## Exact question and scope

IN SCOPE:
1. **Sourcing the items.** Where do legitimate GRE-Math-Subject-style items come from given that official ETS released items are scarce (coordinate with sub-prompt 01b's inventory)? Compare: (a) official ETS retired items, (b) human-authored new items matched to the ETS content blueprint (50/25/25), (c) AI-generated-then-CAS/human-verified items (reusing the SQ7 pipeline), (d) adapted textbook/competition items. For each: validity, difficulty realism, legal/leakage status, and effort.
2. **Content & difficulty representativeness.** How to balance the bank across the ETS blueprint (calculus ~50%, algebra ~25%, additional ~25%) and across difficulty so it isn't all easy/computational. How many items are minimally needed for (a) a stable Performance-model evaluation and (b) the paraphrase test's 30-card × 2 design — and what the precision limits are at those sizes.
3. **Leakage isolation — the keystone requirement.** Specify how to keep this bank provably separate from anything the models "see": from FSRS study cards, from AI-generation prompts/sources, and from any difficulty-estimation sample (the double-dipping trap from SQ3). Define the isolation protocol (separate store, canary strings, hash/embedding overlap scan against study content) and how to *report* the residual leakage rate so a grader trusts the held-out split.
4. **Reuse without contamination across the four uses.** The same bank feeds performance-validation, the paraphrase test, and the ablation post-test. How to partition/version it so using it for one purpose doesn't invalidate another (e.g., items shown in the ablation practice phase must not appear in the post-test; paraphrase "reworded" items must be matched-but-disjoint from study cards).
5. **Difficulty calibration without a calibration sample.** Since we have ~1 examinee (SQ3 says in-house IRT is infeasible), how should item difficulty be assigned for the bank — expert rating? imported anchors? provisional and flagged? — and how to honestly caveat it.

OUT OF SCOPE: the scoring math itself (SQ3), the AI generation pipeline internals (SQ7), the learning-science effect sizes (SQ4) — assume those and focus on the *item bank as shared infrastructure*.

## Deliverable format and length
- ~900–1400 words.
- Section A: sourcing options table (source / validity / difficulty realism / leakage-legal status / effort / recommendation).
- Section B: blueprint + size recommendation with precision/power caveats for each downstream use.
- Section C: the leakage-isolation protocol (concrete steps + how to report residual rate).
- Section D: the partition/versioning scheme that lets one bank serve all four uses without cross-contamination.
- Section E: difficulty-assignment recommendation given no calibration sample, with honest caveats.

## Sourcing requirements
- Prefer peer-reviewed measurement/test-construction sources (e.g., AERA/APA/NCME *Standards for Educational and Psychological Testing*; Haladyna & Rodriguez on item writing; Kolen & Brennan on linking) and the ML leakage literature (Kapoor & Narayanan 2023; Yang et al. 2023). ETS blueprint facts come from sub-prompt 01/01b.
- Per claim: source, type, confidence rating.
- Do not invent item counts as if empirically derived; mark rules-of-thumb as such.

## Counter-evidence / weak-spot demands
- Be blunt: with scarce official items and ~1 examinee, can this bank support *any* trustworthy performance-model evaluation, or only a heavily-caveated pilot? Say which.
- Flag the biggest contamination risk in reusing one bank for four purposes, and whether the sizes are simply too small for the paraphrase test to have power (coordinate with SQ3's small-n warning).
- Identify where AI-generated eval items would create a circularity (AI model evaluated on AI-written items) and how to avoid it.

## Source list (REQUIRED, at the very bottom)
End your deliverable with a `## Sources` section listing **every** source you explicitly cited **and** any source you drew ideas from, each with author(s)/title/publisher/year and a working link or DOI where available, grouped by type (peer-reviewed / institutional / named expert / practitioner). No uncited claims.

End with a self-confidence summary and a one-line verdict on whether a defensible shared item bank is buildable in one week, and the minimum honest version of it.
