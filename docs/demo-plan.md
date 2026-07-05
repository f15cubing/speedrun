# Demo video plan — the **Sunday cut** (live capture)

> Scope: the **full merged project** — the Rust mastery-query engine change, the desktop GRE
> dashboard with **live three scores**, the **read-only 3-score panel on the phone**, self-hosted
> two-way sync, the **AI card pipeline + gold-set gate** (honestly framed **AI-off**), and the
> **proofs** (bench @ 50k · memory calibration · crash 20/20 · two-way sync + conflict). Target
> length **3–5 min**. Format: **live screen capture** of the running desktop app + Android emulator,
> with `docs/evidence/` charts/screenshots as B-roll where a live capture is fiddly.
> State as of 2026-07-03, engine `f15cubing/anki@ea3acae`; scoring/AI/proofs merged (PRs #32–#36).
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
| 2 | **Desktop GRE dashboard, live 3 scores** — Memory as a **range**, 17-leaf **coverage map**, and three **separated** slots: Memory (range), Performance (**not available**, honest), Readiness (**gated** with the full evidence panel + give-up rule) | Stats heatmaps; no exam readiness, ranges, coverage, or abstention | Scores (20%) + UX (8%) |
| 3 | **Same engine on Android + a read-only 3-score panel** — rsdroid rebuilt bundling *our* `rslib`; the phone reviews the same deck **and** shows the same three ranges the desktop computed, read-only | Stock rsdroid backend; no readiness panel | Phone-on-one-engine ceiling (10%) |
| 4 | **Sync on our own engine** — self-hosted; phone review lands on desktop; documented conflict rule (**revlog union + scheduling LWW**), no corruption | AnkiWeb only | Sync ceiling (10%) |
| 5 | **AI card pipeline + gold-set gate (AI-off)** — RAG + non-nullable provenance + in-pipeline abstention + **SymPy CAS** verify + gate scored by 2 raters (κ), and it **beats a non-RAG baseline** (McNemar) | No card generation, no provenance/verify gate | AI checking + safety (15%) |
| 6 | **The proofs** — `make bench` @ 50k, memory calibration curve, crash 20/20, two-way sync + conflict, all re-runnable and seeded | No re-runnable benchmark/calibration harness | Fair re-runnable tests (12%) |

---

## Pre-flight checklist (before you hit record)

- [ ] Desktop dev build running (`cd anki && ./run`) with the seeded GRE deck imported / auto-imported.
- [ ] Do **enough reviews** first that the give-up rule's review-count + coverage proxies are in a
      state you want on camera — ideally **some Memory data + a still-gated Readiness** so the
      evidence panel and abstention are both visible. (Readiness stays gated off honestly at n≈1.)
- [ ] Open the **GRE dashboard** once so the Task 6 adapter writes the synced `gre_scorecard`; sync so
      the phone panel has data to render.
- [ ] Android emulator (`anki_test`, arm64-v8a) booted with our AnkiDroid debug APK on our rebuilt
      `librsdroid.so`; the GRE deck present; **DeckPicker overflow → "GRE readiness"** opens the panel.
- [ ] Sync server ready: `make sync-server` (port 8452), account `greuser`.
- [ ] Terminal panes sized for readable text, ready to run: the mastery read-only-invariant test,
      `make ai-gate` / `make ai-baseline`, `make bench`, `make crash-7g`, `make sync-7b`.
- [ ] Have the B-roll ready: `docs/evidence/proofs/calibration.png`, `docs/evidence/robustness/`,
      `docs/evidence/w3-android/`, `docs/evidence/w4-sync/`, `docs/evidence/task7-android/`.
- [ ] Close any half-built windows so nothing unfinished is on screen.

---

## Shooting script (scene by scene) — target ~5:00

### 0:00 — Cold open (~10s)
**On screen:** the desktop app, GRE deck visible.
**Narration:** "This is a fork of Anki turned into one thing — a GRE Math Subject Test tutor that
measures memory, performance, and readiness *separately*, and refuses to fake a number it can't back
up."

### 0:10 — Deck + taxonomy (~20s)
**On screen:** the Browser, `topic::` tag tree expanded (`topic::calculus::*`, `topic::algebra::*`,
`topic::additional::*`); click a card, show its single leaf tag; math renders as real LaTeX.
**Narration:** "Every card maps to exactly one ETS leaf topic. This tag tree is the substrate
everything reads — the mastery query, the coverage map, and the readiness gate."

### 0:30 — The dashboard, live three scores (~55s)  ← **new vs. Milestone-1**
**On screen:** Tools ▸ GRE dashboard. Walk top to bottom:
1. **Memory** — the range + confidence caveat (aggregate-calibrated, not personalized).
2. **Coverage map** — 17 leaves, per-leaf recall estimate + 95% range.
3. **The three slots**, kept strictly separate:
   - **Memory** — a range.
   - **Performance** — **"not available"** (honest: the desktop adapter does not fabricate it).
   - **Readiness** — **gated off** with the **full evidence panel**: estimate + likely range, %
     coverage, "how sure", last-updated, the main reasons, and the single best next topic.
**Narration:** "Stock Anki gives you a heatmap. We give you a calibrated *range* over exam topics, a
coverage map, and three scores kept strictly separate — never blended. Readiness here is *gated off*:
a confident readiness number on one week of data is an automatic fail, so the app abstains and shows
the evidence panel and the single best next topic instead. Abstaining honestly is the correct output."

### 1:25 — The Rust change under the hood (~50s)
**On screen:** split view — `anki/rslib/src/stats/mastery.rs` and the `anki/proto/anki/stats.proto`
diff (the new `MasteryQuery` RPC + 3 messages). Run the tests live and let them go green:
the 3 Rust unit tests incl. **`mastery_query_is_read_only`**, plus the Python integration test.
**Narration:** "The dashboard's numbers come from this — a read-only query inside Anki's Rust engine,
using the exact FSRS math the scheduler uses, in one database pass. It *provably* never writes, never
returns `OpChanges`, never touches the undo stack — that's this test right here. It's the hardest 20%
of the grade, and because it lives in the shared engine, it ships to the phone for free."

### 2:15 — Same engine on the phone + the read-only 3-score panel (~45s)  ← **new vs. Milestone-1**
**On screen:** the emulator (or `docs/evidence/w3-android/` + `docs/evidence/task7-android/`): the
same deck; an FSRS answer screen (intervals + a `topic::*` tag); then **DeckPicker overflow → "GRE
readiness"** opens `GreScorecardFragment` showing the **same three scores** the desktop computed —
Memory range, Performance not-available, Readiness gated with the evidence panel. Stamp: "computed on
desktop, last updated …".
**Narration:** "This isn't a lookalike — it's our `rslib` compiled into the Android backend. Same
deck, same FSRS scheduling, same tags. And the phone shows the *same* three ranges the desktop
computed — read-only, no scoring math on the device, and it enforces the *same* give-up rule: no bare
readiness number, ever."

### 3:00 — Cross-device sync + the conflict rule (~35s)
**On screen:** `make sync-server`; then the `docs/evidence/w4-sync/` round-trip (review a card on
Android, sync up, pull on the desktop peer → `revlog` grows, `quick_check=ok`). Optionally flash the
`make sync-7b` result: 10+10 land on both, same-card conflict → **revlog union + scheduling LWW**.
**Narration:** "Sync runs on *our* engine, self-hosted, no AnkiWeb. Review on the phone, it lands on
the desktop — revlog grows, quick-check clean, no corruption. And when the same card is reviewed on
both devices offline, the documented rule holds: every review survives — revlog union — and card
scheduling is last-writer-wins."

### 3:35 — AI card pipeline + gold-set gate (AI-off) (~50s)  ← **new; honesty-critical**
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

### 4:25 — The proofs (~25s)
**On screen:** `make bench` output (p50 **650 ms** / p95 **667 ms** @ 50k), then B-roll of
`calibration.png` (Brier 0.219, ECE 0.061), the crash result (**20/20 clean**), and the two-way sync
result.
**Narration:** "Everything is re-runnable and seeded. The mastery query at 50,000 cards: p50 under
seven hundred milliseconds. Memory calibration hugs the diagonal. Twenty hard crashes mid-review,
twenty clean collections. And I'll flag it: the **scoring proofs are simulated machinery-checks** —
they show the math is sound, not that we've predicted a specific real student at n≈1."

### 4:50 — Honest close (~15s)
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
- **Performance shows "not available"** on the desktop adapter rather than a fabricated number.
- **AI is AI-off today.** The gate/beat-baseline numbers validate the **machinery, not a live model.**
  Say the words "AI-off" and "validates the machinery, not a live model." **Do not overclaim.**
- **Scoring proofs are simulated machinery-checks at n≈1** (calibration/paraphrase); real predictive
  validity is unestablished. The bench and crash/sync proofs are real on our engine.
- **A real read-only Rust engine change exists** and provably never mutates the collection.
- **No ETS items** are reused in training or evaluation.

---

## Runnable proofs referenced in the demo

- Deck: `python pipeline/build_deck.py --seed 42` (or first-run auto-import in either app)
- Desktop app: `cd anki && ./run`
- Mastery tests: Rust unit tests in `anki/rslib/src/stats/mastery.rs` (incl. the read-only invariant);
  Python `anki/pylib/tests/` integration test
- AI: `make ai-gate` (gold-set gate + firewall) · `make ai-baseline` (McNemar beat-baseline + AI-off)
- Proofs: `make bench` (50k mastery latency) · `make proofs` (calibration + paraphrase)
- Robustness: `make crash-7g` (20/20) · `make sync-server-7b` + `make sync-7b` (two-way + conflict)
- Sync: `make sync-server`, `make sync-smoke`
- B-roll: `docs/evidence/proofs/`, `docs/evidence/robustness/`, `docs/evidence/w3-android/`,
  `docs/evidence/w4-sync/`, `docs/evidence/task7-android/`

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
