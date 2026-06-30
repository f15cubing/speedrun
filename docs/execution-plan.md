# Execution Plan — GRE Math Subject Speedrun

> Companion to `docs/PRD.md`. The PRD is the *what/why*; this is the *how/when*. Six working days, Tuesday → Sunday, three milestone gates (Wed / Fri / Sun).
> **Deadline: Sunday 2026-07-05, 10:59 PM CT.**

---

## Sequencing principle (non-negotiable order)

Front-load the irreversible, hard-ceiling work. The hard-constraint chain:

```
Rust change  →  Memory model  →  Phone / Sync  →  AI  →  Polish & Prove
(20% + ceiling) (20%)           (10% + ceiling)  (15%)  (15% tests, 8% UX)
```

> **The hardest part of the week is not features — it is getting Anki to compile from source, making one tiny Rust change appear in the desktop app, and getting the same engine running on a phone. Do that before anything else.** Teams that defer the Rust or mobile build to Thursday do not finish.

**Critical path:** fork+build Anki → mastery-query Rust change → rsdroid build with our change → both apps review the shared deck. Everything else (scores, AI, ablation) hangs off this and can parallelize once the engine is live on both platforms.

---

## Today — Tuesday 2026-06-30 (Decisions & Setup, no feature code)

Goal: every irreversible decision locked in writing, environments building, deck + gold-set sourced. The PRD already locks the decisions; today's *doing* is setup + the unblocking spikes.

**Decisions (DONE — captured in PRD):** D1 Rust=mastery query · D2 three-score + give-up rule · D3 Android-only via rsdroid · D4 taxonomy/tags · D5 interleaving ablation pre-registered. → **Get sign-off on §16 open items (D1, D3, exam, thresholds).**

**Setup tasks:**
- [ ] Fork `ankitects/anki` (AGPL-3.0-or-later); add license + credit; `git init` this workspace and wire the fork as a submodule or sibling.
- [ ] **Pin a tagged Anki release** (e.g., a recent `25.x`). Record the tag — all `[inferred]` symbols in `research/responses/05` get verified against it.
- [ ] Read `rslib/` structure; locate the real insertion points for the mastery query: `proto/anki/`, `rslib/src/.../service/mod.rs`, `rslib/src/storage/card/`, `pylib/anki/collection.py`. Confirm vs. PRD §5.2.
- [ ] **Spike 1 — desktop build:** compile Anki from source; get the dev desktop app running. (Highest-risk unblock; do first.)
- [ ] **Spike 2 — Android build:** clone `ankidroid/Anki-Android-Backend` (`rsdroid`); build `rsdroid.aar` with anki as submodule; confirm AnkiDroid runs on an emulator. Install Android Studio + NDK.
- [ ] Source/generate the **study deck**: ≥50% of taxonomy leaf nodes, ≥50% calculus weight; leaf-tag every card (`topic::*`). (Textbook-derived + later AI-gen.)
- [ ] Identify the **AI gold-set source** (one textbook chapter/notes) and the 50 known-correct Q&A pairs for Friday's check; put them in an access-controlled store with canaries.
- [ ] Draft the `topic::*` tagging schema into the deck pipeline (Appendix A).

**Exit gate for today:** decisions signed off; desktop Anki compiles; rsdroid/AnkiDroid builds; deck + gold-set sourced and tagged.

---

## Day 2 — Wednesday (✅ Milestone 1: Rust + both apps run, NO AI)

**Theme:** real engine change, desktop + Android both reviewing the shared deck, memory score with honest range.

**Rust (critical path, do first):**
- [ ] Implement the mastery-query end-to-end: new proto message → read RPC (returns a plain response, **never `OpChanges`**) → grouped SQL aggregate over `cards`⋈notes/tags reusing FSRS retrievability helpers → `pylib` binding.
- [ ] Tests: 3 Rust unit (empty/zero · aggregation correctness · **read-only invariant**) + 1 Python integration; `PRAGMA quick_check` = ok; `add_note→undo` round-trip intact.
- [ ] Benchmark the aggregate at 50k cards (< ~50 ms; add an index if not).
- [ ] Confirm the new RPC is reachable through the **rsdroid** build (ships to Android).

**Desktop:**
- [ ] Review loop runs FSRS on the GRE deck.
- [ ] **Memory score** displayed as a range with the give-up rule (not a single number).
- [ ] **Coverage map** on the dashboard (leaf topics, % covered); readiness gated by coverage threshold.
- [ ] Desktop installer runs on a clean machine (record it).

**Android:**
- [ ] Loads the exam deck; runs a real review session on the shared engine. (Two-way sync NOT required today — same-deck review is.)

**Sync foundation:**
- [ ] Conflict rule documented (PRD D3). Stand up `anki-sync-server` (pinned tag). Manual sync smoke test.

**Exit gate (Milestone 1):** review cards on **both** devices using the same engine; Rust change tested + undo-safe + non-corrupting; desktop installer runs clean.

---

## Day 3 — Thursday (Performance model + paraphrase infra + sync proven)

**Theme:** build the memory→performance bridge and the test machinery that produces Friday's data.

- [ ] **Performance model (Step 2):** calibrated logistic regression + Platt; features = per-topic mastery (from mastery query), imported/firewalled difficulty, timing, coverage. Evaluate by Brier + reliability + ECE on a leakage-audited split.
- [ ] **Readiness model (Step 3):** raw-correct → ETS percentile anchors → 200–990, conformal interval headline + Bayesian cross-check; build the evidence panel + "no track record yet"; start the prospective calibration log.
- [ ] **MCQ study surface (PRD §8a):** new MCQ note type + card template (captures the selected option, grades into the same Again/Hard/Good/Easy path). Behaves like a flashcard on the same FSRS review loop — a content/data-model change, **not** a second engine change — and is what the Performance model scores.
- [ ] **Author 60 eval items** (30 cards × 2 rewordings) for the paraphrase test — original, blueprint-matched; partition into P0/P1/P2/P3.
- [ ] **Leakage pipeline** (the one shared pipeline): exact→normalized→n-gram/Jaccard→embedding; run it; publish the residual rate.
- [ ] **Ablation instrumentation:** wire the interleaved↔blocked toggle + plain-Anki arm; confirm the pre-registration (Appendix B) is committed/timestamped before any run.
- [ ] **Two-way sync tested (7b):** 10 phone-offline + 10 desktop-offline → reconnect → all 20 land. Same-card conflict tested + documented (pure review divergence).

**Exit gate:** performance + readiness produce honest ranges on held-out items; sync no-loss + conflict winner demonstrated; eval bank + leakage report exist.

---

## Day 4 — Friday (✅ Milestone 2: AI on + sync proven + phone shows 3 scores)

**Theme:** AI with safety, three scores on the phone, exam-pressure simulator.

- [ ] **AI card pipeline:** RAG + provenance schema (verbatim quote + anchor, non-nullable) + abstention-in-pipeline; CAS/SymPy verify for computational, NLI+human for conceptual.
- [ ] **Gold-set gate (cutoff lodged BEFORE scoring):** generate 50 cards from the source; score correct/wrong/bad-pedagogy; require **fact-precision ≥0.98 & useful-yield ≥0.60** (or document the honest failure). ≥2 raters, κ + percent agreement.
- [ ] **Beat the baseline:** vs. template/cloze + non-RAG; McNemar exact test.
- [ ] **Phone shows all three scores** with ranges + give-up rule.
- [ ] **Exam-pressure simulator (timed mode):** timed full-length (66 items / 2h50m / on-screen countdown / no pauses), justified on speededness. **Sequenced last and mastery-gated** — unlocks only after interleaving + the ordering algorithm ship and the student clears a per-topic mastery threshold (PRD §8a).
- [ ] **AI-off degradation:** pull network → AI off cleanly; both apps keep working and still score.
- [ ] **Crash test (7g):** kill each app mid-review ×20 → zero corrupted collections.

**Exit gate (Milestone 2):** AI passes (or honestly fails) the pre-set gate and beats baseline; phone shows three scores + syncs two-way; offline + crash safe.

---

## Day 5 — Saturday (Prove everything + documentation)

**Theme:** turn the machinery into evidence and write the docs.

- [ ] **Run the ablation formally** (full interleaved vs. blocked vs. plain Anki); record honestly (null is fine) with TOST + 90% CIs + honest-null language.
- [ ] **Memory calibration chart** (80% ⇒ ~80% on held-back reviews) — Step 1 proof.
- [ ] **Paraphrase results:** recall-on-original vs. accuracy-on-reworded; report the gap honestly (Wilson CIs; descriptive, not powered).
- [ ] **`make bench`:** 50,000-card deck → p50/p95/worst for button-ack, next-card, dashboard load/refresh, sync.
- [ ] **Model descriptions** (one page each): memory, performance, readiness — including the give-up rule.
- [ ] **Architecture overview + Rust change note** (files touched + merge difficulty) into README.
- [ ] **Record the demo video** (3–5 min): review → Rust change → phone↔desktop sync → three scores with ranges → AI → test results.

**Exit gate:** every claim has a chart/number behind it; all docs drafted; demo recorded.

---

## Day 6 — Sunday (✅ Ship — deadline 10:59 PM CT)

- [ ] Package **desktop installer** (clean-machine test, no manual setup).
- [ ] Package **phone build** (signed APK).
- [ ] **Final repo push:** public AGPL-3.0-or-later fork, exam stated up front, build instructions for both platforms, files touched, merge-difficulty assessment.
- [ ] **Hard-ceiling checklist:** Rust change ✓ · phone sharing engine + syncing ✓ · held-out testing ✓ · no leaked data ✓ · readiness backed by evidence ✓ · both apps run on a clean device ✓.
- [ ] **Upload deliverables:** repo link, demo video, three model descriptions, Brainlift.
- [ ] **Submit by 10:59 PM CT.**

---

## Standing rules

- **No AI before Friday.** The Wednesday build has zero model calls, generated cards, or chatbot.
- **Don't switch the Rust candidate.** (a)/(b) are additive stretch only.
- **Author all eval items; never reuse ETS items** (contaminated).
- **Readiness is always a range** with the evidence panel + give-up rule. A made-up number is an automatic fail.
- **Pin everything** (Anki release tag, dependency versions, seeded deck) so every test is re-runnable with one documented command.
- **If iOS tempts you mid-week: don't.** Android-only is the decision.
- **Study-surface order (PRD §8a):** basic-concept flashcards → MCQ cards → timed mode. MCQ is a note-type/template change (**not** a second engine change) that behaves like a flashcard; timed mode ships **last**, mastery-gated, only after interleaving + the ordering algorithm.

---

## Daily dependency map

```
Tue: forks build (desktop + rsdroid) ─┐
                                       ▼
Wed: Rust mastery query ──► desktop review + memory range + coverage map
        │                   Android review on shared engine
        ▼
Thu: performance + readiness ──► eval bank + leakage + paraphrase infra
        │                        sync proven (no-loss + conflict)
        ▼
Fri: AI gate + beat baseline ──► phone 3 scores + simulator + crash/offline
        ▼
Sat: ablation + calibration + paraphrase results + bench + docs + demo
        ▼
Sun: package installers + repo + deliverables + submit
```
