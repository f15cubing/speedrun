<!-- Raw sub-agent response. Captured: 2026-06-29. Round 1. -->
<!-- Prompt: prompts/01-gre-content-coverage.md | Critique: critiques/01-gre-content-coverage.md -->
<!-- Do not edit; this is the source record. -->

# GRE Mathematics Subject Test (Online Format, Since September 2023): A Citable Reference

## TL;DR
- ETS publishes a fixed three-bucket content outline (Calculus ~50%, Algebra ~25%, Additional Topics ~25%); the test is approximately 66 five-option multiple-choice questions in one 2-hour-50-minute session with no separately-timed sections, scored rights-only (no wrong-answer penalty), and reported on a 200–990 scale in 10-point increments.
- There is **NO stable public raw→scaled conversion function**: each test edition is separately equated for difficulty. The only public raw→scaled table is form-specific (the retired GR3768 practice test). Any app projecting a 200–990 number is approximating an unpublished, form-dependent function and should report a range, not a point estimate.
- The working assumption "57–58/66 ≈ 90th percentile ≈ 880" is **incorrect as stated**: on the official GR3768 table, 880 corresponds to **60** correct (57–58 → 860). Combined with ETS's current interpretive table (880 ≈ 90th percentile), the corrected, internally consistent chain is **~60/66 ≈ 880 ≈ 90th percentile**.

## Key Findings
1. The content outline and 50/25/25 weighting are stable and identical across the ETS website, the 2024 practice book, and the 2023 fact sheet. [high — ETS primary]
2. Format: ~66 questions, 5 options each, 2h50m, single session with no separately-timed sections, all questions equal value, rights-only scoring. [high — ETS primary]
3. Scoring is equated per form. ETS does NOT publish a current fixed raw→scaled table; the only public table is the retired GR3768 practice form. [high — ETS primary]
4. Most recent ETS interpretive data: Mathematics mean = 676, SD = 154, N = 7,452, based on July 1, 2019–June 30, 2023 test-takers (Copyright 2024). [high — ETS primary]
5. The old paper test carried a ¼-point-per-wrong-answer penalty; this was removed (best evidence: 2017–2018 testing year), well before the September 2023 online move. ETS does not publish an exact dated changeover announcement. [medium — ETS primary for both scoring rules; transition date inferred]

## Details

### Section A — Content Outline (verbatim ETS phrasing, with weighting bucket)

ETS states: "The percentages given are estimates; actual percentages will vary somewhat from one edition of the test to another." [high — ETS 2024 practice book / 2023 fact sheet]

**I. Calculus — 50%**
- "Material learned in the usual sequence of elementary calculus courses — differential and integral calculus of one and of several variables — including calculus-based applications and connections with coordinate geometry, trigonometry, differential equations, and other branches of mathematics." [Calculus 50%]

**II. Algebra — 25%**
- Elementary algebra: "basic algebraic techniques and manipulations acquired in high school and used throughout mathematics" [Algebra 25%]
- Linear algebra: "matrix algebra, systems of linear equations, vector spaces, linear transformations, characteristic polynomials, and eigenvalues and eigenvectors" [Algebra 25%]
- Abstract algebra and number theory: "elementary topics from group theory, theory of rings and modules, field theory, and number theory" [Algebra 25%]

**III. Additional Topics — 25%**
- Introductory real analysis: "sequences and series of numbers and functions, continuity, differentiability and integrability, and elementary topology of ℝ and ℝⁿ" [Additional 25%]
- Discrete mathematics: "logic, set theory, combinatorics, graph theory, and algorithms" [Additional 25%]
- Other topics: "general topology, geometry, complex variables, probability and statistics, and numerical analysis" [Additional 25%]

ETS caveat: "The above descriptions of topics covered in the test should not be considered exhaustive… questions requiring no more than a good precalculus background may be quite challenging; such questions can be among the most difficult questions on the test." [high — ETS primary]

This is the finest granularity ETS publishes. **ETS does not assign sub-percentages within the three buckets** — the only numeric weights are 50/25/25. A university advising page (Syracuse University) maps these topics to course numbers but adds no additional ETS granularity. [secondary — institutional]

### Section B — Format Facts Table

| Attribute | Value | Source/Confidence |
|---|---|---|
| Number of questions | Approximately 66 multiple-choice ("The GRE Mathematics Test consists of approximately 66 multiple-choice questions") | [high — ETS 2024 practice book] |
| Options per question | 5 ("each of the questions or incomplete statements below is followed by five suggested answers… select the one that is best") | [high — ETS primary] |
| Total testing time | 2 hours 50 minutes (170 min) | [high — ETS primary] |
| Sections | Single test; "there are no separately-timed sections" | [high — ETS primary] |
| Question weighting | "All questions are of equal value" | [high — ETS primary] |
| Wrong-answer penalty | None — rights-only ("Nothing is subtracted from a score if you answer a question incorrectly"); ETS via Kaplan: "No points are subtracted from your score for incorrect answers, so answer every question on the test" | [high — ETS primary] |
| Score scale | 200–990, 10-point increments | [high — ETS primary] |
| Delivery mode (since Sept 2023) | Computer-delivered ("their computer-based administration beginning in September 2023") at test centers worldwide and at home in most countries | [high — ETS primary] |
| Calculator | Not permitted or provided (Study.com: "The GRE Mathematics subject test… does not allow you to use a calculator"; test-takers confirm none provided at administration) | [medium — practitioner + test-taker reports] |
| Scratch work | Test center: scratch paper provided; at-home: small whiteboard or plastic transparency sheet, proctored by ProctorU | [high — ETS primary for at-home] |

### Section C — Scoring + Equating

ETS scoring is rights-only: "Your score will be determined by the number of questions you answer correctly. Questions you answer incorrectly or for which you mark no answer or more than one answer are counted as incorrect. Nothing is subtracted from a score if you answer a question incorrectly." [high — ETS 2024 practice book]

Conversion: "The number of questions you answered correctly on the entire test (total correct score) is converted to the total scaled score for score reporting. This conversion ensures that a scaled score reported for any edition of a GRE Mathematics Test is comparable to the same scaled score earned on any other edition of the test." [high — ETS primary]

**Critical point — no stable public raw→scaled table.** Each test edition is separately equated to adjust for difficulty. ETS publishes only ONE public raw→scaled table, and it is tied to a single retired practice form (GR3768). Because the equating function differs per administration, **no fixed public raw→scaled function exists**. Any app that converts a raw practice score to a 200–990 number is using either (a) the GR3768 form-specific table or (b) an estimate; it cannot reproduce the unpublished operational equating, so projected scaled scores carry inherent uncertainty (plausibly several tens of points on a 200–990 scale). [high — ETS primary on equating; inference on prediction magnitude]

For reference, the GR3768 practice form's official total-score conversion (selected anchor points): 65–66→970; 64→960; 63→920; 62→900; 61→890; **60→880**; 59→870; **57–58→860**; 50→800; 40→670; 33→580. [high — ETS GR3768 practice form, single-form only]

This directly corrects the working assumption: on GR3768, **57–58 correct → 860**, and **60 correct → 880**. The "57–58 ≈ 880" pairing conflates two adjacent rows of the table.

### Section D — Norms / Percentiles (source year explicit)

Most recent ETS interpretive data is "based on all individuals who tested between July 1, 2019, and June 30, 2023" (Copyright 2024). [high — ETS GRE Subject Test Interpretive Data, Table 2]

Mathematics performance statistics (Table 2A, verbatim): "Mathematics Test · 7,452 · 676 · 154" — i.e., N = 7,452; Mean = 676; SD = 154. [high — ETS primary]

Selected percentile ranks (percent of test-takers scoring below each scaled score), Mathematics Test, Table 2B:

| Scaled score | Percentile |
|---|---|
| 960 | 96 |
| 920 | 95 |
| 900 | 93 |
| **880** | **90** |
| 860 | 86 |
| 840 | 82 |
| 820 | 77 |
| 800 | 74 |
| 760 | 66 |
| 700 | 54 |
| 680 (≈ mean) | 50 |
| 600 | 34 |
| 500 | 14 |
| 400 | 2 |

[high — ETS primary, July 2019–June 2023 cohort]

Combining Sections C and D: **~60/66 correct on GR3768 → 880 → ≈ 90th percentile** is the corrected, internally consistent chain. The widely repeated "57–58/66 = 880" figure is forum lore / table-row conflation and does not match the ETS GR3768 table (where 57–58 → 860 ≈ 86th percentile).

Note: older figures (mean 659, SD 137) cited on Wikipedia — verbatim, "The mean score for all test takers from July 1, 2011, to June 30, 2014, was 659, with a standard deviation of 137" — are **stale** and superseded by the current ETS 2019–2023 figures (676 / 154). Do not use the 2011–2014 numbers. [secondary — superseded]

### Section E — Implications for Predicting a Scaled Score

- **No public, stable raw→scaled function exists.** The only legitimate public anchor is the GR3768 form-specific table. An app may present GR3768-based estimates honestly labeled as "based on one retired form," but should NOT advertise a precise operational scaled-score prediction.
- Because each operational form is equated separately, the same raw count can map to different scaled scores across administrations. **Prediction error is unavoidable and should be communicated as a range**, not a point estimate.
- **Percentiles drift.** The interpretive table is updated roughly annually and reflects a rolling multi-year cohort; the current published table is the 2019–2023 cohort. Hard-coding percentiles risks staleness.
- **Content-coverage mapping can be precise** (the 50/25/25 outline is stable); scaled-score prediction cannot.

### Counter-evidence / Weak Spots
- **"57–58 = 880" is wrong** per ETS GR3768 (that is 60 correct; 57–58 = 860). Likely a conflation circulating on prep forums.
- **Wrong-answer penalty history:** The OLD paper test used "correct minus one-fourth incorrect" (confirmed in ETS's 2001 Rescaled Mathematics practice book: raw score = "the number of questions you answered correctly minus one-fourth of the number you answered incorrectly"). The penalty was removed — best-supported timing is the **2017–2018 testing year** (the ETS Subject scoring page stated by mid-2017 that "1/4th of a point is no longer subtracted… on 2017-2018 GRE subject tests," marked by the GR1768 practice-form directions update; the September 2017 administration was reportedly the first without a penalty). ETS publishes no explicit dated announcement. The removal **predates** the September 2023 online move, so the online format did NOT change the (already rights-only) scoring. The occasionally repeated "removed in 2011" claim conflates the GRE General Test revision (August 2011) with the Subject Tests and should not be relied upon. [medium]
- **Pre-2023 vs. online format:** Question count (~66), timing (2h50m), options (5), and the 200–990 scale are **unchanged**. The September 2023 change was delivery mode (paper → computer, at home or test center) plus greater frequency/locations — not content weighting, timing, count, or scoring. (For the Mathematics Test, total time stayed at 2h50m; only the Physics and Psychology tests were shortened to 2 hours.) [high — ETS primary]

## Recommendations
1. **Build the topic map directly on ETS's three-bucket outline** (Section A), using ETS's verbatim sub-bullets as leaf nodes, and tag each leaf with its bucket weight (50/25/25). Do not invent sub-percentages within buckets — ETS does not publish them.
2. **For score prediction, ship a clearly-labeled GR3768-based estimator only.** Display output as a range with a disclaimer that operational forms are separately equated and the true scaled score may differ. *Threshold to revisit:* if ETS releases a new retired form with its own conversion table, add it and show the spread across forms as the honest uncertainty band.
3. **Pull percentiles from the current ETS Subject Test Interpretive Data (2019–2023 cohort) and date-stamp them in-app.** Re-check annually; update when ETS publishes a newer cohort table. Never hard-code percentile claims without showing the source year.
4. **State the corrected benchmark** to users: on the GR3768 form, ~60/66 ≈ 880 ≈ 90th percentile (not 57–58). Frame all such mappings as form-specific, not universal.
5. **Drop any "¼-point penalty" guidance**; current scoring is rights-only, so advise answering every question.

## Caveats
- **Solidly sourced (primary ETS):** content outline and weights (Section A); format facts (Section B); rights-only scoring and equating language (Section C); mean/SD and the percentile table with cohort year (Section D); the GR3768 conversion table (explicitly form-specific).
- **Partially sourced / inferred:** the exact date the wrong-answer penalty was removed (ETS publishes no dated announcement; 2017–2018 is the best-supported inference from the GR1768 form change and corroborating forum/prep accounts); the magnitude of scaled-score prediction error (logical inference from per-form equating, not an ETS-published figure); the calculator prohibition (consistent across practitioner sources and test-taker reports, and aligned with ETS Subject Test policy, but not restated on a single dedicated Mathematics-test ETS page found in this research).
- **Non-primary/secondary only:** course-number mappings (university advising pages); the historical mean 659 / SD 137 (stale, 2011–2014, superseded by 676 / 154).
- **Self-confidence summary:** Sections A, B, C (scoring/equating), and D are anchored in ETS primary documents (2024 practice book Form GR3768, 2023 fact sheet, the ETS Subject Test Content & Structure page, and the 2024 Subject Test Interpretive Data Table 2). Section C's "no stable public table" conclusion is a direct, high-confidence reading of ETS's own equating language. The single weakest element is the precise penalty-removal date, which is inferred rather than stated by ETS.
