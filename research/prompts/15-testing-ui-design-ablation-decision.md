# Sub-prompt 15 — Testing-UI design, falsifiable ablation, and the interface decision

_Round 4 (testing-UI thread). Upstream inputs assumed in hand and **not separately filed**: (i) what the evidence says about test-taking UI affecting performance/measurement validity, and (ii) which UI interventions have evidence and are app-deliverable — the testing-UI analogues of the anxiety thread's SQ12–SQ13._

You are a specialist research agent in **UI/UX design and experimental methods for learning software**. Assume the two upstream testing-UI sub-questions above (UI→performance/measurement-validity evidence; UI interventions + app-deliverability) are in hand. Your job: turn the evidence into a concrete **UI design + a falsifiable ablation**, analyze the risks, and make the **explicit decision** on whether the proposed testing UI should **replace**, **complement**, or be **deprioritized** relative to the project's current baseline testing interface (the existing Anki-fork review screen).

## Project context you must respect
- App = GRE **Mathematics Subject Test** prep on an Anki fork; three separate scores (Memory / Performance / Readiness) with honest uncertainty.
- Prior research (this project) established the **baseline testing UI** (card-review style, no persistent timer chrome, minimal chrome) as the current default; any redesign must not silently degrade **measurement validity** of the three scores.
- Any ablation will be **tiny-n and underpowered** (detecting dz≈0.3 needs ~90 learners), so it must be a pre-registered **estimation/feasibility pilot** with a **delayed endpoint, TOST, and honest-null reporting**.
- A leakage-isolated, expert-rated **held-out item bank** already exists in the plan (4 partitions); reuse it. The GRE is **speeded** (~2.6 min/item) — the UI must render timing, item navigation, and answer-locking in a way that's faithful to real exam conditions.

## The exact question
1. **UI design specification.** Specify concrete, app-deliverable interface designs grounded in the top-ranked interventions, e.g.: (a) an **authentic exam-shell mode** (persistent countdown, item-navigator grid, flag-for-review, no-pause, locked answer changes after submission); (b) **progressive disclosure of difficulty/calibration feedback** timing (immediate vs. deferred); (c) **minimal-chrome "flow" mode vs. information-dense "dashboard" mode** during practice; (d) **mobile vs. desktop layout** tradeoffs given speeded conditions. For each: which evidence supports it, where it sits in the session flow, and fidelity to the real GRE testing interface.
2. **Outcome measurement (critical).** The **primary outcome must be objective performance under realistic pressure** — score and per-item latency on a **timed held-out item set** (reuse the existing bank + the speededness construct) — NOT self-reported UI preference or satisfaction. Specify validated/standard **secondary usability measures** (e.g., System Usability Scale, task-completion time, error/misclick rate, NASA-TLX for cognitive load) and how to collect them without contaminating the performance measure itself (e.g., survey fatigue, demand effects toward "liking" the novel UI).
3. **Ablation design (reuse the project's machinery).** Arms (new UI / baseline UI / plain Anki default screen), within- vs. between-subject at tiny n, what to hold constant (item content, timing rules, scoring), the **delayed + under-pressure** endpoint, an honest **power statement**, TOST equivalence bounds in **raw score and latency units**, and the pre-registered one-sentence hypothesis. Address **stratification by prior testing-software familiarity or device type** (effects may be concentrated in users unfamiliar with digital exam interfaces).
4. **Risk analysis.** Measurement contamination (a UI change that improves scores via interface familiarity rather than learning); cognitive load from added chrome (navigator grids, flags) hurting low-performers; novelty effects that wash out after repeated exposure; opportunity cost vs. content/interleaving work; accessibility regressions (screen readers, motor impairment, small-screen legibility); over-claiming from a noisy small pilot.
5. **THE DECISION.** Give an evidence-tagged recommendation: should the new testing UI **replace** the baseline, **complement** it (e.g., as an optional "exam mode" toggle, and if so, how to keep the ablation clean with two interfaces under tiny-n), or be **deprioritized**? The spec requires **one UI treatment** for the pilot; if you propose maintaining both permanently, confront the scope/maintenance/power cost honestly.

## Deliverable format and length
- ~1200–1800 words.
- Section A: UI component design table (component / source-evidence / placement in session flow / fidelity to real exam interface).
- Section B: measurement plan (primary objective-under-pressure outcome + secondary usability/load measures + anti-contamination safeguards).
- Section C: ablation protocol (arms, design, power statement, TOST, stratification, pre-registered hypothesis, honest-null template).
- Section D: risk table (risk / mechanism / mitigation).
- Section E: the replace/complement/deprioritize recommendation, each branch tagged to its evidence.

## Sourcing requirements
- Prefer peer-reviewed HCI/usability and testing-effects sources; reuse and name the testing-UI evidence base (interface/mode-effect + usability literature). For design/stats, cite as appropriate (e.g., Nielsen or Sauro on usability metrics, Lakens on TOST, relevant computer-based-testing-interface literature).
- Per claim: source, type, confidence; keep **[objective-score/latency]** vs **[self-report/usability-scale]** separate throughout.
- Do not invent effect sizes or fabricate that a UI redesign "works"; if the honest read is that gains are small/narrow/confounded with familiarity, say so.

## Counter-evidence / weak-spot demands
- Steelman BOTH: (a) an authentic exam-shell UI is a cheap, high-fidelity, differentiating feature that improves ecological validity of the Readiness score; (b) it is a UI change whose measured effects are likely confounded with novelty/familiarity, adds engineering and maintenance surface, and may not be distinguishable from noise at tiny n.
- Make the recommendation **contingent and falsifiable**, naming the user subgroup for which it flips (e.g., first-time digital test-takers), and the result that would change the call.
- Be explicit that, at tiny n, the deliverable is the **design + honest pilot result**, not a significant effect.

## Source list (REQUIRED, at the very bottom)
End with a `## Sources` section listing **every** source you explicitly cited **and** any you drew ideas from (author/title/venue/year + link/DOI), grouped by type. No uncited claims.

End with a self-confidence summary and a one-line recommendation (replace / complement / deprioritize) with its evidence tag.
