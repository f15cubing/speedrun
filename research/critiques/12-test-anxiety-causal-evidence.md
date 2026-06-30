# Critique 12 — Test anxiety: causal audit

**Verdict: strong, accept.** A genuinely skeptical audit that mirrors the discipline that served the olympiad thread: it refused to assume the premise, separated [self-report] from [objective-score] everywhere, and named the confound as the central threat. Closes SQ12.

## What is genuinely useful (carry forward)
- **The correlation is real but small** (r ≈ −.26 general test anxiety, von der Embse 2018; −.28 math anxiety, Barroso 2021) — ~7% of variance *before* controls, and a substantial chunk of that is confounded with ability/WM/preparation. **[strong]**
- **Interference vs deficit — both operate, in different students** [strong]: the decisive nuance is that **interference/"choking" concentrates in high-WM, high-ability, *prepared* students** (Beilock & Carr 2005) — i.e., the closest profile to a strong GRE-Math candidate. **The deficit model dominates for the under-prepared.** This is the load-bearing finding: the anxiety lever is most credible *exactly* for our target user, but is a symptom-of-under-preparation for everyone else.
- **The asymmetry [strong]:** interventions reliably reduce self-reported anxiety (g ≈ −0.64 to −0.76) but barely move objective scores (g ≈ 0.28–0.37, shrinking with outliers, publication bias documented). → reducing anxiety is a *small, unreliable* lever on scores.
- **"Rule out the deficit first" [strong, actionable product idea]:** diagnose mastery and the **low-stakes vs high-stakes / untimed vs timed performance gap** before treating "anxiety." A large gap = anxiety/choking is live; both low = it's preparation. **This maps directly onto the app's three-score architecture** — a Memory-high / timed-Performance-low gap is the in-product signal for an anxiety bottleneck. Carry into the feature design.

## Problems / calibration notes
1. **The Jamieson 2010 GRE study (n≈28, d≈1.0) is doing heavy lifting here and is contradicted by newer evidence.** Prompt 14 surfaces a **2026 multi-institution reappraisal replication that came back null**. So 12's "encouraging… Jamieson" framing is **outdated** — temper it: the GRE-specific reappraisal effect is fragile, plan for the meta-analytic d≈0.2 (or less). Reconcile toward 14.
2. **A couple of citation attributions are shaky** — the Frontiers WM mediation meta-analysis is attributed "Caviola/Korhonen," and a "906,311 participants" Educational Psychology Review meta is loosely cited. Verify authorship/figures before quoting in the deliverable. **[minor]**
3. **Pooled intervention g (0.28–0.37) lumps heterogeneous methods** — per-intervention breakdown matters and is handled in prompt 13.

## Decision
- **No follow-up.** SQ12 closed.
- **Carry to synthesis [strong]:** test anxiety is a *real but small, partially-confounded* causal contributor; credibly manipulable mainly in **prepared high-WM "chokers"** (our target population); the score lever is small and self-report ≠ score. Use the low-stakes-vs-high-stakes gap as the in-app diagnostic.
- **Retags:** correlation magnitude **[strong]**; interference-in-prepared-chokers **[moderate-strong]**; deficit-dominates-for-underprepared **[moderate]**; intervention asymmetry **[strong]**; Jamieson GRE effect **[weak — small n, 2026 null replication per p14]**.
