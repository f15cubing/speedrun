# Demo video plan — the **Sunday cut** (live capture)

> Scope: the **full merged project** — the Rust mastery-query engine change; a desktop **review
> session** (basic + **interactive MCQ** cards, FSRS-graded); the **live interleaving toggle** + the
> interactive **"How this differs from FSRS"** explainer (the study feature, 15%); the desktop GRE
> **dashboard with live three scores** (Memory range · **observed Performance** range · gated
> Readiness); the **timed Exam Mode** shell; the **read-only 3-score panel on the phone**; self-hosted
> two-way sync; the **AI card pipeline + gold-set gate** (honestly framed **AI-off**); and the
> **proofs** (bench @ 50k: mastery + next-card · memory calibration · crash 20/20 · two-way sync +
> conflict). Format: **live screen capture** of the running desktop app + Android emulator, with
> `docs/evidence/` charts/screenshots as B-roll where a live capture is fiddly.
> State as of 2026-07-05, engine `f15cubing/anki@4c991c9`; **everything below is merged on `main`.**
>
> **Length:** the **spec-required 3–5 min cut** is the ⭐-marked scenes (review session · Rust change ·
> phone→desktop sync · three scores with ranges · AI · test results). The un-starred scenes
> (interleaving, Exam Mode, MCQ, the FSRS explainer) are **optional showcase** — this plan is
> intentionally a **superset**; cut to taste. Recording length can go over or under.
>
> **Recording is human-gated** (needs a person at the keyboard) — this is a CUT-FIRST buffer item
> per `docs/STATUS.md`; every segment it shows is already merged and reproducible from one command.
> The **Milestone-1 cut** (W1–W4, no AI/scores) is preserved verbatim in the **Appendix** so it can
> be shot first and grown into this cut, exactly as originally planned.

The through-line is unchanged: **one exam, two apps on one engine, a real engine change, and honesty
as a feature.** Lead with the product (legible), prove the engineering underneath, prove it's real on
two devices, then be explicit about what is and isn't validated (AI-off; simulated proofs at n≈1).

---

## What we're showing off vs. base Anki

| # | What we made | Base Anki has | Grade lever |
|---|---|---|---|
| 1 | **Mastery Query** — read-only Rust RPC returning per-topic `{total, reviewed, mastered, avg_recall}`, reusing the scheduler's own FSRS retrievability, one SQL pass | Only global stats graphs; no per-topic mastery aggregate | Rust change (20%) + no-corruption ceiling |
| 2 | **Interactive MCQ study surface** — a new note type with **tappable 5-option** cards: tap → instant green/red + correct-option highlight + explanation, graded on the **FSRS** ease path (correct→Hard/Good/Easy, wrong→Again). Renders in **both** apps' reviewer webview | Basic front/back cards only | Performance surface (20%) + UX (8%) |
| 3 | **Interleaving — the learning-science feature** — a **live reviewer toggle** (Tools ▸ "GRE: Interleave reviews") that reorders the review queue so consecutive cards come from **different confusable topics** (pure presentation; FSRS untouched), plus an **interactive explainer** ("How this differs from FSRS") running the real algorithm | Blocked, FSRS-priority order only; no interleaving | Study feature (15%) |
| 4 | **Desktop GRE dashboard, live 3 scores** — Memory as a **range**, 17-leaf **coverage map**, three **separated** slots: Memory (range), **Performance (observed accuracy range** from in-app exam answers, honest — *not* the calibrated model), Readiness (**gated** with the full evidence panel + give-up rule) | Stats heatmaps; no exam readiness, ranges, coverage, or abstention | Scores (20%) + UX (8%) |
| 5 | **Timed Exam Mode** — a faithful GRE Math Subject Test shell: one global countdown, item counter, Mark, Review grid, **no calculator / no pause / auto-submit**, **rights-only** scoring, per-leaf breakdown + range; honest **capacity gating** (only presets the firewalled held-out bank can fill are enabled) | No timed/exam simulator | Performance + UX; speededness construct |
| 6 | **Same engine on Android + a read-only 3-score panel** — rsdroid rebuilt bundling *our* `rslib`; the phone reviews the same deck **and** shows the same three ranges the desktop computed, read-only | Stock rsdroid backend; no readiness panel | Phone-on-one-engine ceiling (10%) |
| 7 | **Sync on our own engine** — self-hosted; phone review lands on desktop; documented conflict rule (**revlog union + scheduling LWW**), no corruption | AnkiWeb only | Sync ceiling (10%) |
| 8 | **AI card pipeline + gold-set gate (AI-off)** — RAG + non-nullable provenance + in-pipeline abstention + **SymPy CAS** verify + gate scored by 2 raters (κ), and it **beats a non-RAG baseline** (McNemar) | No card generation, no provenance/verify gate | AI checking + safety (15%) |
| 9 | **The proofs** — `make bench` @ 50k (mastery **and** next-card cycle), memory calibration curve, crash 20/20, two-way sync + conflict, leakage/deck-quality/give-up gates, all re-runnable and seeded | No re-runnable benchmark/calibration harness | Fair re-runnable tests (12%) |

---

## Pre-flight checklist (before you hit record)

- [ ] Desktop dev build running (`cd anki && ./run`) with the seeded GRE deck imported / auto-imported.
- [ ] Do **enough reviews** first (basic **and** a few interactive MCQ cards) that Memory has a range
      to show and the give-up proxies are in the state you want on camera — ideally **some Memory data
      + a still-gated Readiness** so the evidence panel and abstention are both visible. (Readiness
      stays gated off honestly at n≈1.)
- [ ] Run **one Exam Mode form** (Tools ▸ **GRE exam mode** → **Mini**, the only preset the firewalled
      held-out bank fills) and submit it, so the dashboard's **Performance** slot has attempts to render
      an **observed accuracy range** (and a per-leaf breakdown), instead of the n=0 "not available".
- [ ] Know where the study-feature surfaces live: Tools ▸ **"GRE: Interleave reviews (ablation)"**
      (the toggle) and Tools ▸ **"How this app differs from FSRS"** (the interactive interleaving demo).
- [ ] Open the **GRE dashboard** once so the Task 6 adapter writes the synced `gre_scorecard`; sync so
      the phone panel has data to render.
- [ ] Android emulator (`anki_test`, arm64-v8a) booted with our AnkiDroid debug APK on our rebuilt
      `librsdroid.so`; the GRE deck present; **DeckPicker overflow → "GRE readiness"** opens the panel.
- [ ] Sync server ready: `make sync-server` (port 8452), account `greuser`.
- [ ] Terminal panes sized for readable text, ready to run: the mastery read-only-invariant test,
      `make ai-gate` / `make ai-baseline`, `make bench`, `make crash-7g`, `make sync-7b`.
- [ ] Have the B-roll ready: `docs/evidence/proofs/calibration.png`,
      `docs/evidence/proofs/bench_actions.json`, `docs/evidence/robustness/`,
      `docs/evidence/w3-android/`, `docs/evidence/w4-sync/`, `docs/evidence/task7-android/`.
- [ ] Close any half-built windows so nothing unfinished is on screen.

---

## Shooting script (scene by scene)

> ⭐ = the **spec-required 3–5 min core** (review session · Rust change · phone→desktop sync · three
> scores with ranges · AI · test results). Un-starred scenes are optional showcase — shoot them if you
> want the fuller story, drop them for a tight cut. Durations are approximate.

### ⭐ Cold open (~10s)
**On screen:** the desktop app, GRE deck visible.
**Narration:** "This is a fork of Anki turned into one thing — a GRE Math Subject Test tutor that
measures memory, performance, and readiness *separately*, and refuses to fake a number it can't back
up."

### Deck + taxonomy (~20s)
**On screen:** the Browser, `topic::` tag tree expanded (`topic::calculus::*`, `topic::algebra::*`,
`topic::additional::*`); click a card, show its single leaf tag; math renders as real LaTeX.
**Narration:** "Every card maps to exactly one ETS leaf topic. This tag tree is the substrate
everything reads — the mastery query, the coverage map, and the readiness gate."

### ⭐ Review session — basic + interactive MCQ (~40s)
**On screen:** start a review. Answer a **basic** card (Show Answer → an FSRS ease button). Then hit an
**interactive MCQ** card: **tap an option** → instant **green/red** feedback, the correct option
highlights, the explanation reveals, math typeset as LaTeX; a **correct** tap offers Hard/Good/Easy, a
**wrong** tap a single Continue → **Again**. Show the FSRS intervals on the buttons.
**Narration:** "Here's the core loop. Basic recall cards drive Memory — and these **multiple-choice
cards**, five options like the real exam, drive Performance. Tap an answer: instant feedback, the
worked explanation, and it grades straight onto Anki's FSRS schedule — correct earns Hard/Good/Easy, a
miss is a lapse. Same review loop, same engine — the MCQ is a note type, not a second scheduler."

### Interleaving — the learning-science feature (~45s)
**On screen:** Tools ▸ **"GRE: Interleave reviews (ablation)"** — toggle it **on**; resume reviews and
point out consecutive cards now come from **different** confusable topics (e.g. a differentiation card,
then an integration card) instead of a block of one type. Then open Tools ▸ **"How this app differs
from FSRS"** and scrub the **interactive interleaving panel** (blocked vs interleaved chips coloured by
topic, live adjacency-dispersion / FSRS-displacement metrics, the K/W sliders re-running the real
algorithm).
**Narration:** "This is our pre-registered learning-science feature. Anki already does spacing and
retrieval; we add **interleaving** — mixing confusable problem types so you have to pick the strategy
before executing, exactly what a GRE item demands. It's a **pure re-ordering** of the due queue —
FSRS intervals are untouched — and it's a real toggle, so it's the interleaved-vs-blocked **ablation**
in the app. This page runs the *actual* algorithm live. The honest caveat: the ablation is
**pre-registered but not yet run** with human subjects — the toggle is what makes that run possible."

### ⭐ The dashboard, live three scores (~55s)
**On screen:** Tools ▸ GRE dashboard. Walk top to bottom:
1. **Memory** — the range + confidence caveat (aggregate-calibrated, not personalized).
2. **Coverage map** — 17 leaves, per-leaf recall estimate + 95% range.
3. **The three slots**, kept strictly separate:
   - **Memory** — a range.
   - **Performance** — an **observed accuracy range** (Wilson interval with its `n`) from your real
     in-app **Exam-Mode** answers; at n=0 it honestly reads "not available". This is *observed*
     accuracy — **not** the calibrated multi-student model (which needs a corpus we don't have at n≈1).
   - **Readiness** — **gated off** with the **full evidence panel**: estimate + likely range, %
     coverage, "how sure", last-updated, the main reasons, and the single best next topic.
**Narration:** "Stock Anki gives you a heatmap. We give you a calibrated *range* over exam topics, a
coverage map, and three scores kept strictly separate — never blended. Memory is recall; Performance is
the accuracy you actually got on unseen exam-style items, shown as a range with its sample size —
observed, not a model we can't back up yet; and Readiness here is *gated off*: a confident readiness
number on one week of data is an automatic fail, so the app abstains and shows the evidence panel and
the single best next topic instead. Abstaining honestly is the correct output."

### Exam Mode — the timed GRE shell (~40s)
**On screen:** Tools ▸ **GRE exam mode** → pick **Mini** (the enabled preset). Show the shell: one
**global countdown**, item counter, five A–E options, **Mark**, the **Review** grid; note **no
calculator, no pause**. Answer a few items, jump via the grid, then submit (or let it auto-submit) →
the **Results** screen: rights-only score with a **range** + per-leaf breakdown (reusing the
`CalibrationStrip`). Point at the greyed-out Full/Half/Third presets.
**Narration:** "Exam Mode mirrors the real computer-delivered test: one clock, no calculator, no pause,
auto-submit, rights-only scoring. These answers are what feed the observed Performance range you just
saw. And notice only **Mini** is offered — the others are greyed out because our **held-out** item bank
is firewalled from training and only has enough items for the short form. We'd rather offer an honest
short form than pad the exam with leaked questions."

### ⭐ The Rust change under the hood (~50s)
**On screen:** split view — `anki/rslib/src/stats/mastery.rs` and the `anki/proto/anki/stats.proto`
diff (the new `MasteryQuery` RPC + 3 messages). Run the tests live and let them go green:
the 3 Rust unit tests incl. **`mastery_query_is_read_only`**, plus the Python integration test.
**Narration:** "The dashboard's numbers come from this — a read-only query inside Anki's Rust engine,
using the exact FSRS math the scheduler uses, in one database pass. It *provably* never writes, never
returns `OpChanges`, never touches the undo stack — that's this test right here. It's the hardest 20%
of the grade, and because it lives in the shared engine, it ships to the phone for free."

### ⭐ Same engine on the phone + the read-only 3-score panel (~45s)
**On screen:** the emulator (or `docs/evidence/w3-android/` + `docs/evidence/task7-android/`): the
same deck; an FSRS answer screen (intervals + a `topic::*` tag); then **DeckPicker overflow → "GRE
readiness"** opens `GreScorecardFragment` showing the **same three scores** the desktop computed —
Memory range, Performance not-available, Readiness gated with the evidence panel. Stamp: "computed on
desktop, last updated …".
**Narration:** "This isn't a lookalike — it's our `rslib` compiled into the Android backend. Same
deck, same FSRS scheduling, same tags. And the phone shows the *same* three ranges the desktop
computed — read-only, no scoring math on the device, and it enforces the *same* give-up rule: no bare
readiness number, ever."

### ⭐ Cross-device sync + the conflict rule (~35s)
**On screen:** `make sync-server`; then the `docs/evidence/w4-sync/` round-trip (review a card on
Android, sync up, pull on the desktop peer → `revlog` grows, `quick_check=ok`). Optionally flash the
`make sync-7b` result: 10+10 land on both, same-card conflict → **revlog union + scheduling LWW**.
**Narration:** "Sync runs on *our* engine, self-hosted, no AnkiWeb. Review on the phone, it lands on
the desktop — revlog grows, quick-check clean, no corruption. And when the same card is reviewed on
both devices offline, the documented rule holds: every review survives — revlog union — and card
scheduling is last-writer-wins."

### ⭐ AI card pipeline + gold-set gate (AI-off) (~50s)  ← honesty-critical
**On screen:** run `make ai-gate` and let the report print; show a generated card with its
**verbatim source quote + anchor**; then `make ai-baseline` (McNemar). Point at the numbers on
screen.
**Narration:** "Now the AI pipeline — and I'm going to be precise about what this is. Every generated
card carries a **non-nullable source quote and anchor**; if it can't be grounded, the pipeline
**abstains**. Computational cards are re-derived with a **SymPy CAS** — a wrong answer literally
cannot publish. The pre-lodged gate — fact-precision at least 0.98, useful-yield at least 0.60 —
**passes**: fact-precision **1.000**, useful-yield **0.64**, two raters at Cohen's **κ 0.938**. And it
**beats** a non-RAG template baseline: McNemar **p ≈ 6e-6**, with the fact-precision ceiling intact.
**The honest caveat:** there's **no live-model API key** in this environment, so this runs **AI-off**
on a deterministic stub. These numbers validate the *machinery* — RAG, provenance, CAS, abstention,
the gate — **not a live model.** Going live is a one-file change, and it's blocked only on a key."

### ⭐ The proofs (~30s)
**On screen:** `make bench` output — **both** numbers: the **next-card cycle** (grade→next) **p50
0.11 ms / p95 0.33 ms** @ 50k (interleave overhead ~0.005 ms), and the **mastery query** p50 650 ms /
p95 667 ms @ 50k. Then B-roll of `calibration.png` (Brier 0.219, ECE 0.061), the crash result
(**20/20 clean**), and the two-way sync result. Optionally flash the re-runnable gates
(`make deck-leakage-audit` residual 0.0000, `make giveup-audit` 1 shown / 4 gated).
**Narration:** "Everything is re-runnable and seeded. The next card after grading lands in about a
third of a millisecond at 50,000 cards — and interleaving adds essentially nothing. The per-topic
mastery aggregate is heavier, about two-thirds of a second, so the dashboard batches it. Memory
calibration hugs the diagonal. Twenty hard crashes mid-review, twenty clean collections. And I'll flag
it honestly: the **scoring proofs are simulated machinery-checks** — they show the math is sound, not
that we've predicted a specific real student at n≈1."

### ⭐ Honest close (~15s)
**On screen:** back to the dashboard's three slots + a quick cut to `docs/STATUS.md` buffer section.
**Narration:** "What's *not* here is deliberate and logged: the live-model run waits on an API key,
the interleaving ablation is pre-registered but not yet run, and the score projection is honest about
n≈1. Everything you saw is merged and reproducible from a single command. We'd rather show you a
range we can back up than a number we can't."

---

## Honesty framing (say it out loud)

Non-negotiable, and it *is* the pitch — don't hide the gaps, sell them:

- **Three scores stay separate.** Memory ≠ Performance ≠ Readiness; never blended.
- **Readiness is always a range + evidence panel + give-up rule.** A bare readiness number is an
  **automatic fail** — the gated slot on camera is a live demonstration of the give-up rule.
- **Performance is an *observed* accuracy range** (Wilson interval + `n`) from real in-app Exam-Mode
  answers — not a fabricated number, and **not** the calibrated multi-student model (unbuilt at n≈1);
  at n=0 it abstains ("not available").
- **Interleaving is live (a real reviewer toggle) but its ablation is pre-registered, not yet run**
  with human subjects. Say so — a documented "not yet run" scores; a fabricated effect does not. The
  reorder is pure presentation: FSRS intervals are untouched.
- **AI is AI-off today.** The gate/beat-baseline numbers validate the **machinery, not a live model.**
  Say the words "AI-off" and "validates the machinery, not a live model." **Do not overclaim.**
- **Scoring proofs are simulated machinery-checks at n≈1** (calibration/paraphrase); real predictive
  validity is unestablished. The bench and crash/sync proofs are real on our engine.
- **A real read-only Rust engine change exists** and provably never mutates the collection.
- **Exam Mode offers only presets the firewalled held-out bank can fill** (Mini) — no leaked/padded
  items, honest capacity gating.
- **No ETS items** are reused in training or evaluation.

---

## Runnable proofs referenced in the demo

- Deck: `python pipeline/build_deck.py --seed 42` (or first-run auto-import in either app)
- Desktop app: `cd anki && ./run`
- Desktop surfaces (menus): Tools ▸ **GRE dashboard** · **GRE exam mode** · **GRE: Interleave reviews
  (ablation)** · **How this app differs from FSRS**
- Mastery tests: Rust unit tests in `anki/rslib/src/stats/mastery.rs` (incl. the read-only invariant);
  Python integration test
- Interleaving tests: `anki/qt/tests/test_gre_interleave_review.py` (reviewer wiring) ·
  `anki/qt/tests/test_gre_method.py` (explainer)
- AI: `make ai-gate` (gold-set gate + firewall) · `make ai-baseline` (McNemar beat-baseline + AI-off)
- Study feature: `make interleave-report` (adjacency-dispersion / FSRS-displacement metrics) ·
  `make ablation-analysis` (paired effect + 90% CI + TOST + honest-null on the pre-registered design)
- Proofs: `make bench` (50k: **mastery RPC + next-card cycle** latency) · `make proofs` (memory
  calibration + paraphrase)
- Re-runnable gates: `make deck-leakage-audit` (residual 0.0000) · `make deck-report` (deck integrity) ·
  `make giveup-audit` (Readiness never bare) · `make scorecard-validate` (synced artifact honesty)
- Robustness: `make crash-7g` (20/20) · `make sync-server-7b` + `make sync-7b` (two-way + conflict)
- Sync: `make sync-server`, `make sync-smoke`
- B-roll: `docs/evidence/proofs/` (incl. `bench_actions.json`), `docs/evidence/robustness/`,
  `docs/evidence/w3-android/`, `docs/evidence/w4-sync/`, `docs/evidence/task7-android/`

---

## Appendix — Milestone-1 cut (original live script, preserved)

> The W1–W4 cut: **what was runnable at Milestone 1** — the Rust mastery-query engine change, the
> desktop dashboard, the shared engine on Android, and self-hosted sync. **No AI, no live
> Performance/Readiness scores.** Preserved verbatim so it can be shot first and grown into the
> Sunday cut above (insert the live-scores, phone-panel, AI, and proofs segments in place).
> State as of 2026-07-01, engine `f15cubing/anki@ea3acae`.

### M1 — What we're showing off vs. base Anki

| # | What we made | Base Anki has | Grade lever |
|---|---|---|---|
| 1 | **Mastery Query** — read-only Rust RPC returning per-topic `{total, reviewed, mastered, avg_recall}`, reusing the scheduler's own FSRS retrievability, one SQL pass, <50 ms @ 50k | Only global stats graphs; no per-topic mastery aggregate | Rust change (20%) + no-corruption ceiling |
| 2 | **Desktop GRE dashboard** — Memory as a **range**, 17-leaf **coverage map**, three **separated** score slots incl. an honest "Insufficient evidence to score" give-up state | Stats heatmaps; no exam readiness, ranges, coverage, or abstention | Scores (20%) + UX (8%) |
| 3 | **GRE deck + ETS taxonomy** — every card `topic::bucket::leaf`-tagged, reproducible from one command | Empty; generic tags | Data foundation |
| 4 | **Same engine on Android** — rsdroid rebuilt bundling *our* `rslib`; phone reviews the same deck with FSRS + our tags, survives restart, Check DB clean | Stock rsdroid backend | Phone-on-one-engine ceiling (10%) |
| 5 | **Sync on our own engine** — self-hosted `anki-sync-server` on our fork; phone review lands on desktop, documented conflict rule, no corruption | AnkiWeb only | Sync ceiling (10%) |

### M1 — Pre-flight checklist (before you hit record)

- [ ] Desktop dev build running (`./run` in the anki fork) with the seeded GRE deck imported
      (`pipeline/build_deck.py --seed 42`).
- [ ] Do **a handful of reviews** first so Memory has data to show a range (a fully-new deck shows the
      n=0 abstention — decide which state you want on camera; ideally show *some* Memory data + the
      Readiness give-up state).
- [ ] Android emulator (`anki_test`, arm64-v8a) booted with our AnkiDroid debug APK on our rebuilt
      `librsdroid.so`; the GRE deck present.
- [ ] Sync server ready to start: `make sync-server` (port 8452), account `greuser`.
- [ ] A terminal pane sized for readable text, ready to run the mastery tests.
- [ ] Screen recorder set to capture desktop + a second source for the emulator (or use the
      `docs/evidence/w3-android/` + `docs/evidence/w4-sync/` screenshots as B-roll if a live emulator
      capture is fiddly).
- [ ] Close AI/score work-in-progress windows so nothing half-built is on screen.

### M1 — Shooting script (scene by scene)

#### 0:00 — Cold open (~10s)
**On screen:** the desktop app, GRE deck visible.
**Narration:** "This is a fork of Anki turned into one thing — a GRE Math Subject Test tutor that
measures memory, performance, and readiness *separately*, and refuses to fake a number it can't back
up."

#### 0:10 — Deck + taxonomy (~25s)
**On screen:** open the Browser, expand the `topic::` tag tree (`topic::calculus::*`,
`topic::algebra::*`, `topic::additional::*`). Click a card, show its single leaf tag.
**Narration:** "Every card maps to exactly one ETS leaf topic. This tag tree is the substrate
everything else reads — the mastery query, the coverage map, the readiness gate."

#### 0:35 — The dashboard, the showpiece (~60s)
**On screen:** Tools ▸ GRE dashboard. Walk top to bottom:
1. **Memory** — the range + confidence caveat.
2. **Coverage map** — 17 leaves, per-leaf recall estimate + 95% range.
3. **The three slots** — pause on **Readiness**: *"Insufficient evidence to score — studied X% of
   topics. Best next: …"* with its reasons.
**Narration:** "Stock Anki gives you a heatmap. We give you a calibrated *range* over exam topics, a
coverage map of what the deck actually covers, and three scores kept strictly separate. And this empty
Readiness slot? That's the feature. A confident readiness number on one week of data is an automatic
fail — abstaining honestly is the correct output, so it tells you the single best next topic instead."

#### 1:35 — The Rust change under the hood (~60s)
**On screen:** split view — `anki/rslib/src/stats/mastery.rs` and the `anki/proto/anki/stats.proto`
diff (the new `MasteryQuery` RPC + 3 messages). Then run the tests live in the terminal and let them
go green:
- the 3 Rust unit tests incl. `mastery_query_is_read_only`
- the Python integration test (`anki/pylib/tests/test_mastery.py`)
**Narration:** "The dashboard's numbers come from this — a read-only query inside Anki's Rust engine,
using the exact same FSRS math the scheduler uses, in one database pass. And it *provably* never
writes, never touches the undo stack, never corrupts the collection — that's this test right here.
It's the hardest 20% of the grade, and because it lives in the shared engine, it ships to the phone
for free."

#### 2:35 — Same engine on the phone (~45s)
**On screen:** the emulator (or `docs/evidence/w3-android/` screenshots): the same deck; an FSRS
answer screen showing intervals + a `topic::calculus::differential_multi` tag; the counter changing;
after a force-stop + reopen the session persisted; Check DB → "Database rebuilt and optimized."
**Narration:** "This isn't a lookalike — it's our `rslib` compiled into the Android backend, proven by
a Kotlin binding test against the real engine. Same deck, same FSRS scheduling, same tags. It survives
a restart and reports no corruption."

#### 3:20 — Cross-device sync (~40s)
**On screen:** `make sync-server` in a terminal; then the `docs/evidence/w4-sync/` round-trip — review
a card on Android, rate Good, sync up; on the desktop peer, pull → `revlog 1→2`, `quick_check=ok`.
**Narration:** "Sync runs on *our* engine, self-hosted, no AnkiWeb. Review a card on the phone, it
lands on the desktop — revlog grows, quick-check is clean, no corruption, on a documented conflict
rule."

#### 4:00 — Honest close (~20s)
**On screen:** back to the dashboard's three slots.
**Narration:** "What you're *not* seeing yet is deliberate — no AI, no live Performance or Readiness
scores. Those come Thursday and Friday, with held-out evaluation. Everything shown here is merged and
reproducible from a single command."

### M1 — Honesty framing (say it out loud)

The Performance and Readiness slots are placeholders / give-up states, and there's no AI yet. **Don't
hide it — sell it.** The empty Readiness slot is a live demonstration of the give-up rule (abstention
under insufficient evidence), which is the project's core bet. The biggest current gap is, on-thesis,
a feature.
