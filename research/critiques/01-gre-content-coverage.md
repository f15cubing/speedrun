# Critique 01 — GRE content / coverage / scoring norms

_Reviewer stance: skeptical. The response is above-average: it correctly identifies the single most important downstream fact (no stable public raw→scaled function) and it challenges the project's own working assumption instead of rubber-stamping it. The issues below are mostly about **verifiability of specific numbers** and **one internal-consistency seam**, not about direction._

## Verdict
**Accept with mandatory verification.** The qualitative conclusions are sound and usable now; the specific numeric tables (GR3768 conversion and the percentile table) must be verified against primary PDFs before we let them "correct" anything user-facing or feed them into the score model. One follow-up prompt (01b) is warranted.

---

## What is genuinely useful (carry into synthesis)
- **[strong, carry forward] "No stable public raw→scaled function; each form is separately equated."** This is the highest-value finding for the whole project. It directly justifies the honesty rule: a readiness *number* cannot be defended; a *range with disclosed evidence* can. This raises the bar for sub-prompt 03 (readiness conversion) and should be quoted in `SYNTHESIS.md`. Sourced to ETS equating language — credible. [strong]
- **[strong, carry forward] Content outline at ETS leaf granularity (50/25/25, no sub-percentages).** Directly usable to build the coverage map (challenge 7c). The agent correctly refused to invent sub-bucket percentages. [strong]
- **[moderate, carry forward] The challenge to "57–58/66 = 880."** Even if the exact GR3768 values need checking (below), the agent is right that this figure circulates without a primary anchor and likely conflates table rows / old paper data. Treat the *direction* of the correction as moderate-confidence pending 01b.
- **[strong] Pre-2023 vs online: count/timing/options/scale unchanged; only delivery mode changed (Math stayed 2h50m).** Useful and plausibly correct.

---

## Problems and gaps

### 1. [HIGH PRIORITY — verify] The headline correction rests on un-reproduced GR3768 table values
The entire "57–58 is wrong → it's actually 60→880" correction depends on specific anchor points (`60→880`, `57–58→860`, `65–66→970`, …) attributed to the retired GR3768 practice form. But:
- No page/figure citation or link is given for the table; the values are asserted, not reproduced from a quotable location.
- These are exactly the kind of specific numbers an agent can misremember. If even one row is off, the "correction" is itself wrong.
- **Action:** 01b must reproduce the full GR3768 raw→scaled table from the primary ETS *GRE Mathematics Test Practice Book (Form GR3768)* with an explicit source location, so we can confirm `60→880` and `57–58→860`. Until then, tag the correction **[moderate — single un-reproduced table]**, not [high].

### 2. [Internal inconsistency] The "corrected chain" silently re-introduces the thing it warns against
The agent concludes **"~60/66 → 880 → ≈90th percentile"** by chaining (a) the GR3768 *form-specific* raw→scaled table with (b) the 2019–2023 *multi-year* percentile cohort. But the report's own central thesis is that each form is equated separately and no single mapping is representative. So the clean chain is only valid **if GR3768's difficulty ≈ the operational forms behind the percentile cohort** — an assumption the report elsewhere tells us not to make. This isn't fatal, but the chain should be presented as *"an approximation that assumes GR3768 is representative,"* not as a crisp fact. [contested — flag in synthesis]

### 3. [Verify, but plausible] Percentile table + mean/SD/N need a primary citation
`Mean 676, SD 154, N 7,452 (2019–2023)` and the full percentile table are asserted to ETS Interpretive Data. A credibility check I ran: the percentiles are **roughly consistent with an approximately-normal distribution** at that mean/SD (e.g., 880 → z≈1.32 → ~91st vs. stated 90; 500 → z≈−1.14 → ~13th vs. stated 14), with deviations of ≤~5 points in the 760–800 band (expected for a real, slightly non-normal distribution). That internal consistency *increases* confidence the numbers are real rather than fabricated — but it is not a substitute for the primary PDF. **Action (01b):** confirm against the actual ETS *GRE Subject Tests Interpretive Data* document, with table label and copyright year.

### 4. [Gap] No enumeration of the universe of official released material
For building exam-style items (sub-prompt 03's paraphrase test) and for the leakage check (challenge 7e), we need to know *what official ETS items exist and where* (which retired forms: GR0568, GR8767, GR9367, GR1268, GR3768, etc.; how many official questions total; which have public conversion tables). The response only mentions GR3768. **Action:** add to 01b.

### 5. [Minor — source type] A few primary facts lean on secondary relays
- The rights-only quote is attributed "ETS via Kaplan"; the practice book states it directly — cite the primary, drop the relay.
- Calculator prohibition rests on Study.com + test-taker reports ([medium], correctly flagged). Low stakes for our app; optionally pin to ETS Subject Test policy. Not blocking.

### 6. [Minor — overstated precision] "several tens of points" prediction error
The claim that operational equating introduces error "plausibly several tens of points" is a *reasonable inference* but is presented adjacent to sourced facts. It is explicitly self-flagged as inference, which is acceptable — just keep it clearly labeled [inference, not ETS-published] in synthesis.

---

## Source-discipline assessment
Good overall: per-claim confidence tags are present and mostly well-calibrated; stale data (2011–2014 mean 659/137) is correctly identified and quarantined; the agent distinguished primary ETS from institutional/practitioner. Two improvements: (a) reproduce/locate the numeric tables rather than assert them, (b) prefer primary over relayed quotes. **One process gap: the response did not end with a consolidated source list** — exactly the discipline we're now requiring of every prompt going forward.

---

## Decision
- **Follow-up required:** yes → `prompts/01b-gre-scoring-verification.md` (verify GR3768 table + percentile/mean/SD primary sources; enumerate all official released forms/items; flag any discrepancy with this round's numbers).
- **Confidence retagging for synthesis:**
  - Content outline & weighting — **[strong]**
  - Format facts — **[strong]**
  - "No stable public raw→scaled function" — **[strong]**
  - "60→880 / 57–58→860" specific values — **[moderate, pending 01b]**
  - "~60/66 ≈ 880 ≈ 90th" chain — **[contested — depends on GR3768 representativeness]**
  - Percentile table & mean/SD — **[moderate→strong pending primary citation; internally consistent]**
  - Calculator / penalty-removal date — **[moderate, self-flagged]**
