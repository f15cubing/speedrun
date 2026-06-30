# Critique 11 — Shared held-out eval item bank

**Verdict: strong, accept.** Correctly identifies that **the keystone deliverable is the leakage-isolation protocol, not the items**, and is blunt that with ~1 examinee this is a *pilot-grade* artifact only. Converges with 01b (official items are contaminated) and with prompt 3 (small-n underpowering).

## What is genuinely useful (carry forward) — [strong]
- **Author original items; official ETS items are unusable as held-out** (contaminated + copyright). Use a few only as a private *style anchor*. Direct convergence with 01b. [strong]
- **Four disjoint, version-locked partitions** (P0 frozen held-out / P1 ablation practice / P2 delayed post-test / P3 paraphrase pairs) with content-hashing — this is the clean structure that lets one bank serve performance-eval, ablation, paraphrase, and AI-gold-set without cross-contamination.
- **Leakage protocol** (Kapoor & Narayanan L1 taxonomy; project-specific canary GUID — *not* the memorized BIG-bench one; n-gram **and** embedding/LLM-decontaminator scans because Yang et al. 2023 rephrasing defeats n-grams; difficulty-estimation firewall; report a residual-leakage rate). Implementable and grader-credible.
- **Honest power math:** 30×2 paraphrase ≈ **12–16% power** at OR=2 → it is a **descriptive consistency probe with Wilson CIs (~±17% at n=30)**, NOT a significance test. Converges with prompt 3's mid-p McNemar caution.

## Problems / calibration notes
1. **Difficulty is provisional and noisy — this compounds the performance model.** Expert-rated (Angoff-style) difficulty correlates only **r≈0.6** with true difficulty (Taube 1997); experts rank-order better than they estimate absolute values. Since "item difficulty" is an input feature to the performance model (prompt 3), that feature is itself uncertain → **widens the readiness interval further**. Make this explicit in the readiness model's uncertainty budget.
2. **Item-count thresholds (~60–100 minimum, 100–150 ideal) are rules-of-thumb, not derived** — the response says so. Fine; the binomial/Wilson precision numbers (±16.8% at n=30, ±9.6% at n=100) are the honest anchor.
3. **AI-generated eval items risk circularity** (don't let the evaluated model's family author the eval set; CAS+human verify; keep AI items out of P0). Good — and it ties to prompt 7's leakage section. Dedupe the leakage methodology across 03/07/11 in synthesis.

## Decision
- **No follow-up.** SQ11 closed.
- **Carry to synthesis [strong]:** the held-out bank is a leakage-isolated, expert-rated, **pilot-grade** artifact; ~60–100 original blueprint-matched canary-tagged items in a frozen P0 disjoint from P1/P2/P3; every number reported with Wilson CIs; all difficulties flagged provisional; residual-leakage rate published. It cannot support a *generalizable* performance claim at n≈1 — and per the spec that honest limitation is the correct, grade-rewarded posture.
