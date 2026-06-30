# Critique 01b — GRE scoring verification (contradiction resolution)

**Verdict: accept fully — this is the strongest, most decisive return so far.** It resolved the cross-source contradiction with primary citations, confirmed the load-bearing table verbatim, and surfaced a leakage fact that reshapes the item-bank strategy. This closes SQ1.

## The contradiction is resolved — and prompt 1 was the stale one
- **GR3768 raw→scaled: CONFIRMED verbatim** (ETS *Practice Book*, © 2024, p. 35). Both load-bearing rows verified: **60→880** and **57–58→860**. So my prompt-1 critique (flag the values, don't trust them unverified) was the right call, and the *values* survive.
- **Interpretive data: prompt 1 was SUPERSEDED, prompt 3 was CURRENT.** The current edition (ETS *Subject Test Interpretive Data*, © 2025, cohort **Jul 2021–Jun 2024**) is **Mean 680 / SD 161 / N 5,180**, with **880→88, 860→84, 800→71, 680→49**. Prompt 1's 676/154/7,452 (2019–2023) is the prior edition. → **Use the © 2025 numbers everywhere; date-stamp them.** This vindicates the "percentiles drift annually, never hardcode" rule — the numbers shifted within one cycle.
- **Document artifact noted honestly:** the live PDF's Table 2B sub-header still says 2019–2023 while Table 2A/copyright say 2021–2024; the percentile *values* match the newer cohort. Flag, don't block.

## High-value new finding (carry into synthesis + item-bank)
- **All ~431 official released items are contaminated.** Six full 66-item forms (GR3768, GR1268/GR1768, GR0568, GR9768, GR9367, GR8767) + a 35-item booklet are long-public PDFs → almost certainly in any LLM training corpus. **Implication: author original items; treat the entire official corpus as "known-contaminated" and exclude from held-out evaluation.** This independently converges with prompt 11's conclusion. **[strong]**

## Minor / residual caveats
1. **GR3768 representativeness still applies.** The table is now verified, but it is *one retired form's* equating. Converting a *practice* raw score via GR3768 still assumes the practice items match GR3768's difficulty — the same caveat from critique 01 (§2). 01b handles this with the right labeling ("nominal scale; achievable ceiling form-dependent, 970 on GR3768"). Keep that caveat in the UI.
2. **GR8767/GR9367 per-row values: PARTIALLY VERIFIED** (image-only scans, secondary rehosts). Not load-bearing for us. Honestly flagged.
3. **Scale ceiling:** confirmed modern Math forms top out below 990 (GR3768 = 970) due to form-specific equating, not a scale change. Good — kills the "you can hit 990" implication.

## Decision
- **No further follow-up.** SQ1 is closed.
- **Synthesis actions:** (a) replace all interpretive figures with © 2025 values + visible date stamp; (b) ship a GR3768-based estimator labeled form-specific, range only; (c) author original items, exclude all official ETS items from held-out sets (shared with prompt 11).
- **Retags:** GR3768 table **[strong — primary, p.35]**; current norms **[strong — ETS © 2025]**; "~60/66 ≈ 880 ≈ ~88th" chain **[moderate — still assumes GR3768 representativeness]**; official-item contamination **[strong]**.
