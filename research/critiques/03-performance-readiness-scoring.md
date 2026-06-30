# Critique 03 — Performance & Readiness scoring

**Verdict: excellent — the best-reasoned output of the batch.** It refuses to overpromise, and its strongest conclusion is a *negative* one that is independently corroborated by prompt 1: **there is no public number-correct→scaled (200–990) mapping, so readiness must ship as a range + evidence panel, never a single number.** That convergence across two independent agents makes it **[strong]**.

## What is genuinely useful (carry into synthesis) — [strong] unless noted
- **No public raw→scaled anchor → range only.** Corroborated by prompt 1. The single most important scoring conclusion. [strong]
- **n=1 examinee kills in-house IRT.** Sample-size floors (~100–200 Rasch, ~250–500 2PL, ~1000+ 3PL) cited to Lord / Embretson & Reise. Item difficulty must be *imported* from a calibrated bank, never estimated in-house from this student — and never on the same sample used to validate (double-dipping; Kapoor & Narayanan 2023). [strong]
- **Calibrated logistic + Platt** as the Performance engine, evaluated by Brier + reliability diagram + ECE on a leakage-audited split. [strong]
- **Paraphrase decision rule — a real improvement over the spec.** The right test is not "original recall ≈ reworded accuracy" alone, but whether Performance's calibrated probabilities **beat a memory-only baseline at predicting reworded outcomes** (McNemar mid-p for small n — Fagerland et al. 2013; TOST equivalence at ±10pp; paired bootstrap over cards). This sharpens spec challenge 7d. [strong]
- **Give-up rule tied to interval width / SEM**, with ≥200 reviews + ≥50% coverage as operational proxies — principled, not arbitrary. [strong]
- **"No track record yet" panel** + prospective calibration log. Exactly the honesty the spec rewards. [strong]
- **Scale-versioning catch:** 200–990 is the *Subject* Test (and pre-2011 General) scale, not the modern 130–170 General Test. Confirms our target scale is right and warns against cross-scale confusion. [moderate→strong]

## Problems / must-resolve
1. **[HIGH — cross-source contradiction] ETS norm numbers disagree with prompt 1.**
   - Prompt 1: Math **N=7,452, mean=676, SD=154** (2019–2023 cohort, ©2024); percentiles **800→74th, 820→77th, 840→82nd, 880→90th**.
   - Prompt 3: Math **N=5,180, mean=680, SD=161** (cites Table 2B ©2025, and *notes the PDF itself says 2021–2024 in body vs 2019–2023 in header*); percentiles **800→71st, 820→75th, 840→79th, 900→91st**.
   - These differ in exactly the way both agents predicted: **annual percentile drift across interpretive-data editions.** This is reconcilable but **must be pinned**. → folded into follow-up **01b**: lock ONE edition, date-stamp it in-app, and treat percentiles as non-stationary (don't hardcode). The discrepancy *validates* the "date-stamp, don't hardcode" recommendation. **[contested until 01b]**
2. **[medium] Reframed paraphrase rule adds complexity.** The "beat memory-only baseline" framing is superior, but graders will also expect the simpler original-vs-reworded gap. **Report both**: the raw paired gap (with CI) *and* the incremental-prediction test.
3. **[low] Thresholds are literature defaults, not data-derived** (Jaccard 0.7–0.8, cosine 0.85–0.9, ±10pp, 200 reviews). The response flags this; tune on a labeled slice. Acceptable.
4. **[note] GR3768 tension.** Prompt 3 (correctly) refuses to publish *any* raw→scaled table, which is more conservative than prompt 1's use of the GR3768 form table. This reinforces critique-01's point #2: using GR3768 as if it generalizes is an approximation. In synthesis, present GR3768 only as "one retired form, illustrative," never as the conversion function.

## Cross-links (for synthesis dedupe)
- **Leakage pipeline duplicates prompt 7 Section E** (same Yang et al. 2023 rephrased-samples lineage, 13-gram, embedding cosine, canaries). → Merge into a single shared leakage methodology used by both the performance model and the AI-gen eval.
- **Converges with prompt 2**: n=1 / one-week data ⇒ aggregate-only memory calibration ⇒ no validated readiness. Two independent agents, same conclusion. [strong]

## Decision
- **Update 01b** to resolve the ETS-numbers contradiction (pin one edition).
- **Write follow-up 11** (shared held-out evaluation item bank): the performance model, the paraphrase test, and the AI gold set all depend on a leakage-isolated GRE-style item set that no prompt has actually *designed* yet. This is the missing keystone.
- Carry everything else forward [strong].
