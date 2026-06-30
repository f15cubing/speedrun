# Sub-prompt 01b — Verify GRE Math Subject scoring tables + enumerate official released material (follow-up to 01)

You are a verification-focused research agent. A prior agent produced specific scoring numbers for the GRE Mathematics Subject Test that our project will rely on. Your job is to **confirm or correct them against primary ETS documents** and to **enumerate the universe of official released material**. Treat every number as unverified until you locate it in a primary source. If you cannot locate a primary source, say so plainly — do not paper over a gap with a plausible-looking number.

## Exact claims to verify (confirm, correct, or mark unverified)

1. **GR3768 raw→scaled conversion table.** A prior agent asserted (from the retired ETS *GRE Mathematics Test Practice Book*, Form GR3768) anchor points including: `65–66→970, 64→960, 63→920, 62→900, 61→890, 60→880, 59→870, 57–58→860, 50→800, 40→670, 33→580`. 
   - Reproduce the **full** official GR3768 total-score conversion table, and state exactly where it appears (document title, edition/year, page/figure).
   - Confirm or correct the specific rows `60→880` and `57–58→860` (these are load-bearing for a correction we are about to rely on).
2. **Interpretive data — RESOLVE A DIRECT CONTRADICTION between two prior agents.** Two sub-agents reported *different* Mathematics norm numbers, almost certainly because they read different annual editions of the ETS interpretive-data PDF:
   - **Source A** ("Interpretive Data," ©2024, cohort **2019–2023**): **N=7,452, mean=676, SD=154**; percentiles **800→74th, 820→77th, 840→82nd, 880→90th, 700→54th, 600→34th**.
   - **Source B** ("Interpretative Data," Table 2B, ©2025; the PDF reportedly shows **2019–2023 in a header but 2021–2024 in body text**): **N=5,180, mean=680, SD=161**; percentiles **800→71st, 820→75th, 840→79th, 900→91st, 700→53rd, 600→34th**.
   Your tasks: (a) determine which is the **most recent published edition** and its exact cohort window; (b) reproduce that edition's Mathematics row (N, mean, SD) and full percentile table verbatim with the exact document title + table label + copyright year; (c) explain the discrepancy (is it annual percentile drift across editions? a within-PDF header/body inconsistency?); (d) state the verdict label (CONFIRMED / CORRECTED / UNVERIFIED) for each disputed number. The implication we will adopt: **percentiles are non-stationary — date-stamp them in-app and never hardcode** — so confirm whether ETS updates this table annually.
3. **Scale ceiling.** Confirm whether the Math Subject Test's reported scores in practice top out below 990 (e.g., GR3768 max = 970), and explain why (form-specific equating ceiling) — or correct this.

## Enumerate (this is new, not in round 1)

4. **All official released forms / practice material** for the GRE Mathematics Subject Test: list every retired practice form and official practice book ETS has published (e.g., GR0568, GR8767, GR9367, GR1268, GR3768, and any current online practice test), with year and whether each includes its **own** raw→scaled conversion table. 
5. **Total count of official released questions** available across all these sources, and where to obtain them legally.
6. Whether **any** raw→scaled conversion table other than GR3768's is public.

## Why this matters (context for you)
- Our app must build a topic coverage map and may show a projected 200–990 range; we need to know exactly which numbers are publicly defensible.
- We must run a **leakage check**: any official released item that ends up in our model's training data invalidates the test. To do that we must know the full set of official items that exist.

## Deliverable format and length
- ~600–1000 words.
- Section A: GR3768 full conversion table (verbatim) + exact citation, with a clear "CONFIRMED / CORRECTED / COULD-NOT-VERIFY" verdict on `60→880` and `57–58→860`.
- Section B: interpretive-data verification (numbers + exact document + cohort/year) with the same verdict labels.
- Section C: enumerated list of official released forms/material (table: form ID / year / has-conversion-table? / where available).
- Section D: total official-item inventory + leakage implications.
- Section E: explicit list of anything you could NOT verify.

## Sourcing requirements
- **Primary ETS only** for the numeric verifications (the actual practice books / interpretive-data PDFs). University or prep-site reproductions are admissible **only** to locate or corroborate, and must be labeled secondary.
- Per claim: source, type (primary ETS / secondary), confidence rating, and a verdict label (CONFIRMED / CORRECTED / UNVERIFIED).
- **Never invent table values.** If you cannot find the primary table, state "could not verify against primary source" and stop — a wrong number here is worse than an admitted gap.

## Counter-evidence / weak-spot demands
- If reproductions of GR3768 disagree with each other, report the disagreement and which is primary.
- Flag if the "most recent" interpretive data has been superseded since the prior agent looked.
- Note any sign that figures circulating online trace to old paper-format editions rather than current ETS docs.

## Source list (REQUIRED, at the very bottom)
End with a `## Sources` section listing **every** source you cited or drew ideas from — each with title/publisher/year/edition and a working link where available, grouped by type (primary ETS / secondary). No uncited numbers.
