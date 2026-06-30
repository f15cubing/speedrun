# Sub-prompt 14 — Anxiety-inoculation feature: app design, falsifiable ablation, and the feature decision

You are a specialist research agent in **instructional/product design and experimental methods**. Assume sub-prompt 12 (is test anxiety a causal lever?) and sub-prompt 13 (which interventions, what evidence, app-deliverability) are in hand. Your job: turn the evidence into a concrete app feature + a falsifiable ablation, analyze the risks, and make the **explicit decision** on whether anxiety inoculation should **replace**, **complement**, or be **deprioritized** relative to the project's current learning-science feature (interleaving). Follow the evidence; do not boost the idea.

## Project context you must respect
- App = GRE **Mathematics Subject Test** prep on an Anki fork; three separate scores (Memory / Performance / Readiness) with honest uncertainty.
- Prior research (this project) concluded: **interleaving** is the current pick for the single required "learning-science feature + ablation" slot; the whole learning-science effect base is **weaker in math than verbal**; the ablation will be **tiny-n and underpowered** (detecting dz≈0.3 needs ~90 learners) so it must be a pre-registered **estimation/feasibility pilot** with a **delayed endpoint, TOST, and honest-null reporting**.
- A leakage-isolated, expert-rated **held-out item bank** already exists in the plan (4 partitions); reuse it. The GRE is **speeded** (~2.6 min/item) — "performance under pressure" is part of the construct.

## The exact question

1. **Feature design.** Specify concrete, app-deliverable designs grounded in sub-prompt 13's top-ranked interventions, e.g.: (a) an **"exam-pressure simulator"** mode (authentic timing, scored stakes, on-screen countdown, no-pause) = the literal *inoculation* via graded exposure; (b) **pre-session arousal-reappraisal microcopy** and a **worry-dump (expressive writing)** step; (c) optional **paced-breathing/downregulation**; (d) difficulty calibrated under the timer. For each: which evidence supports it, dose/placement, and fidelity to the source intervention.
2. **Outcome measurement (critical).** The **primary outcome must be objective performance under realistic pressure** — score on a **timed held-out item set** (reuse the existing bank + the speededness construct) — NOT self-reported calm. Specify validated **secondary/mechanism** measures of state anxiety (e.g., STAI-state; Cognitive Test Anxiety Scale, Cassady & Johnson) and how to collect them without inducing demand effects.
3. **Ablation design (reuse the project's machinery).** Arms (full app w/ anxiety feature / feature-off / plain Anki), within- vs between-subject at tiny n, what to hold constant, the **delayed + under-pressure** endpoint, an honest **power statement**, TOST equivalence bounds in raw score units, and the pre-registered one-sentence hypothesis. Address **trait-anxiety stratification** (effects likely concentrated in high-anxious students).
4. **Risk analysis.** Iatrogenic anxiety (cueing anxiety can worsen it for some); **placebo/demand** effects (especially on self-report); **opportunity cost** vs content study; moderation (helps high-anxious, possibly null/negative for low-anxious); over-claiming from a noisy small pilot.
5. **THE DECISION.** Give an evidence-tagged recommendation: should anxiety inoculation **replace** interleaving, **complement** it (and if so, how to keep the ablation clean with two features under tiny-n), or be **deprioritized**? The spec requires *one* feature+ablation; if you propose two, confront the scope/time/power cost honestly.

## Deliverable format and length
- ~1200–1800 words.
- Section A: feature designs table (feature / source-intervention & evidence / dose & placement / app fidelity).
- Section B: measurement plan (primary objective-under-pressure outcome + secondary anxiety measures + anti-demand safeguards).
- Section C: ablation protocol (arms, design, power statement, TOST, stratification, pre-registered hypothesis, honest-null template).
- Section D: risk table (risk / mechanism / mitigation).
- Section E: the replace/complement/deprioritize recommendation, each branch tagged to its evidence.

## Sourcing requirements
- Prefer peer-reviewed methods/intervention sources; reuse and name the evidence from sub-prompts 12–13. For design/stats, cite as appropriate (Soderstrom & Bjork on learning-vs-performance and delayed tests; Lakens on TOST; validated anxiety scales).
- Per claim: source, type, confidence; keep **[objective-score]** vs **[self-report]** separate throughout.
- Do not invent effect sizes or fabricate that a brief feature "works"; if the honest read is that the credible win is small/narrow, say so.

## Counter-evidence / weak-spot demands
- Steelman BOTH: (a) anxiety inoculation is a cheap, high-leverage, differentiating feature; (b) it is a noisy, smaller-than-interleaving effect whose only robust wins (reappraisal microcopy + worry-dump) are too trivial to be a "feature." Then weigh them.
- Make the recommendation **contingent and falsifiable**, naming the trait-anxiety subgroup for which it flips, and the result that would change the call.
- Be explicit that, at tiny n, the deliverable is the **design + honest pilot result**, not a significant effect.

## Source list (REQUIRED, at the very bottom)
End with a `## Sources` section listing **every** source you explicitly cited **and** any you drew ideas from (author/title/venue/year + link/DOI), grouped by type. No uncited claims.

End with a self-confidence summary and a one-line recommendation (replace / complement / deprioritize) with its evidence tag.
