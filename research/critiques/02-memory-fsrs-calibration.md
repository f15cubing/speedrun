# Critique 02 — FSRS memory model & calibration

**Verdict: strong; accept the conceptual core, verify three specific numeric claims before citing.** This is the highest-value kind of response — it actively debunks a weak source (LECTOR), flags the maintainer-run conflict of interest itself, and lands the one conclusion that matters most for the project: **you cannot claim a *personally* calibrated memory model on one week of one student's data.**

## What is genuinely useful (carry into synthesis) — [strong]
- **Card-level calibration ≠ exam performance.** The recall-vs-exam gap (transfer-appropriate processing — Morris/Bransford/Franks 1977; far-transfer fragility — Barnett & Ceci 2002) is correctly argued. This is the seam the whole "bridge" lives in. [strong]
- **One-week single-user reality:** you are effectively evaluating the *population-default* model, not a personalized one; FSRS historically needs ~1,000 reviews before per-user fitting beats defaults. → directly supports the give-up rule. [strong — converges with prompt 3's n=1 IRT conclusion]
- **LECTOR debunk:** simulation-only, AI-authored/reviewed venue, no calibration metrics, no real reviews → does NOT independently corroborate FSRS calibration. Excellent skeptical work; prevents us citing a junk "independent" study. [strong]
- **Calibration recipe** (TimeSeriesSplit, reliability diagram + binomial CIs, ECE with ≥2 binning schemes, Brier/log-loss as bin-free anchors, the "calibrated yet useless if it predicts the mean" caveat) is textbook-correct and implementable. [strong]

## Problems / must-verify
1. **[HIGH — likely error] "FSRS-7 (newest), 35 parameters, dual-power-law, 8 curve params."** I cannot corroborate an FSRS-7; the latest *shipped* algorithm in Anki is **FSRS-6 (21 params)**, with FSRS-rs as the Rust port. "FSRS-7 = 35 params" has the texture of a hallucinated/extrapolated row. **Action:** verify against the `open-spaced-repetition/srs-benchmark` repo; if it does not exist, strike it. **The project recommendation is unaffected** — the response itself says ship FSRS-6/FSRS-rs (what Anki uses). Retag FSRS-7 specifics **[low/unverified]**.
2. **[verify] Benchmark figures** (349,923,850 evaluation reviews / 9,999 collections; the log-loss/RMSE/AUC table). Plausible and likely from the README, but **maintainer-run and self-reported** (the response commendably flags this). Treat all absolute numbers as **[moderate — author-reported]**; cite the *direction* (FSRS beats SM-2 on log-loss for the large majority of users) not the precise "99.6%."
3. **[verify] Cold-start thresholds** ("~1,000 → 400 in 24.04 → minimum removed in 24.06+"; "as few as ~16 reviews" hedged). Directionally right and well-hedged; pin exact versions to the Anki changelog/issue #3094 before stating them as fact. **[moderate]**
4. **[fine] Forgetting-curve forms/parameters** (v3 exponential; v4 power DECAY=−1/FACTOR=1/9; FSRS-4.5/5 DECAY=−0.5/FACTOR=19/81; v6 optimizable `w20`) match my understanding. **[high]**

## Source discipline
Good: per-claim tags, explicit COI disclosure, primary-vs-practitioner separation, and it ended with a self-confidence summary. It did **not** include a consolidated `## Sources` list (this prompt predated that rule). Not blocking; future agents must comply.

## Decision
- **No new prompt.** The FSRS-7 check is a 2-minute build-time verification, not a research question. Pin to FSRS-6/FSRS-rs regardless.
- **Carry to synthesis [strong]:** memory model is *aggregate-calibrated only* in a one-week build; personalized calibration and any exam-readiness claim require (a) ~1,000+ reviews across the probability range and (b) separate coverage + transfer evidence. This is a load-bearing input to the honesty/give-up rule and is independently corroborated by prompt 3.
