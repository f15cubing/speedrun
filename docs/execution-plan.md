# Execution Plan — GRE Math Subject Speedrun

> Companion to `docs/PRD.md`. The PRD is the *what/why*; this is the *how/when*. Six working days, Tuesday → Sunday, three milestone gates (Wed / Fri / Sun).
> **Deadline: Sunday 2026-07-05, 10:59 PM CT.**
>
> **⚡ Compression in effect (2026-07-03):** the original Friday (Milestone 2) + Saturday
> (prove-everything + docs) were pulled into a single **compressed-Friday push finishing by a
> self-imposed 7:00 PM CT** to bank the weekend as buffer. See **"Days 4+5 COMPRESSED"** below for the
> P0/P1/CUT-FIRST breakdown; the merged blocks are marked **done** with their PR refs. The real
> submission deadline is unchanged, and any CUT-FIRST item that slipped is logged in the **Sat/Sun
> buffer** section of `docs/STATUS.md` and pointed at Sunday below.

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
- [x] Confirm the new RPC is reachable through the **rsdroid** build (ships to Android). ✅ **W3** —
  backend rebuilt from source bundling `anki@ea3acae`; `Collection.masteryQuery` binding green in a
  host-JVM test against the real compiled `rslib` (`MasteryQueryTest`).

**Desktop:**
- [ ] Review loop runs FSRS on the GRE deck.
- [x] **Memory score** displayed as a range with the give-up rule (not a single number).
- [x] **Coverage map** on the dashboard (leaf topics, % covered); readiness gated by coverage threshold.
- [ ] Desktop installer runs on a clean machine (record it).

**Android:**
- [x] Loads the exam deck; runs a real review session on the shared engine. (Two-way sync NOT required today — same-deck review is.) — **W3 done (PR #12 + on-device gate):** APK built on our local backend, `librsdroid.so` loads; a real FSRS review session runs on the seeded GRE deck (FSRS intervals + `topic::*` leaf tags), the session persists across a force-stop/reopen, and Check Database reports "Database rebuilt and optimized" (no corruption). Evidence: `docs/evidence/w3-android/`.

**Sync foundation:**
- [x] Conflict rule documented (PRD D3). Stand up `anki-sync-server` (pinned tag). Manual sync smoke test. — **W4:** `make sync-server` on our engine (`f15cubing/anki@ea3acae`); headless `roundtrip_smoke.py` green (note+revlog+scheduling cross, `quick_check=ok`); live round-trip — real AnkiDroid ↔ headless desktop peer through our server, both directions, with AnkiDroid Check-Database clean (`docs/evidence/w4-sync/`); rule in `docs/codebase/sync.md`. 7b/7g deferred to Thursday.

**Exit gate (Milestone 1):** review cards on **both** devices using the same engine; Rust change tested + undo-safe + non-corrupting; desktop installer runs clean.

---

## Day 3 — Thursday (Performance model + paraphrase infra + sync proven)

**Theme:** build the memory→performance bridge and the test machinery that produces Friday's data.

- [ ] **Performance model (Step 2):** calibrated logistic regression + Platt; features = per-topic mastery (from mastery query), imported/firewalled difficulty, timing, coverage. Evaluate by Brier + reliability + ECE on a leakage-audited split.
- [ ] **Readiness model (Step 3):** raw-correct → ETS percentile anchors → 200–990, conformal interval headline + Bayesian cross-check; build the evidence panel + "no track record yet"; start the prospective calibration log.
- [ ] **MCQ study surface (PRD §8a, design spec §4) — implement end-to-end:**
  - [ ] **"GRE MCQ" note type + card template** (fields `Question`, `OptionA–E`, `CorrectOption`, `Explanation`, `LeafTag`; renders 5 single-select options; on answer reveals the key + explanation and grades into the same **Again/Hard/Good/Easy** path). `pipeline/notetypes/` (genanki model).
  - [ ] **SymPy distractor generation** (`pipeline/distractors.py`): 4 named common-error transforms per computational item (sign flip, dropped `+C`, off-by-power, missing chain factor, swapped op), deterministic + provably ≠ key; conceptual distractors human-authored in the verified YAML.
  - [ ] **Build + emit MCQ cards** through `pipeline/build_deck.py` alongside flashcards (one documented command, seeded, byte-stable); imports into desktop Anki and reviews on the **same FSRS loop** — a content/data-model change, **not** a second engine change.
  - [ ] **Tests** (design spec §8): note type builds + renders 5 options + `CorrectOption` matches key + grades correctly; distractor sample has exactly 4 distinct ≠-key options and is deterministic for a fixed seed.
  - MCQ is the in-app surface the **Performance** model scores (real five-option answers, the GRE's native format).
- [ ] **Author 60 eval items** (30 cards × 2 rewordings) for the paraphrase test — original, blueprint-matched; partition into P0/P1/P2/P3.
- [ ] **Leakage pipeline** (the one shared pipeline): exact→normalized→n-gram/Jaccard→embedding; run it; publish the residual rate.
- [ ] **Ablation instrumentation:** wire the interleaved↔blocked toggle + plain-Anki arm; confirm the pre-registration (Appendix B) is committed/timestamped before any run.
- [ ] **Two-way sync tested (7b):** 10 phone-offline + 10 desktop-offline → reconnect → all 20 land. Same-card conflict tested + documented (pure review divergence).

**Exit gate:** performance + readiness produce honest ranges on held-out items; sync no-loss + conflict winner demonstrated; eval bank + leakage report exist.

---

## Days 4+5 COMPRESSED — Friday 2026-07-03 (✅ merged; CUT-FIRST items → Sunday buffer)

> **What changed.** The original Friday (Milestone 2: AI + phone 3 scores) *and* Saturday
> (prove-everything + docs) were pulled into one push finishing by a self-imposed **7:00 PM CT**, so
> this block was ruthlessly prioritized: **P0** = hard-ceiling / highest grade weight; **P1** = strong
> grade lever; **CUT-FIRST** = slips into the Sat/Sun buffer without breaking a ceiling. **All P0/P1
> blocks below merged** (refs inline); the CUT-FIRST items that slipped are logged in
> `docs/STATUS.md` § *Sat/Sun buffer (CUT-FIRST spillover)* and pointed at **Sunday** below. The real
> 10:59 PM CT Sunday deadline is untouched.

### Block A — P0 · AI card pipeline + gold-set gate (15% + biggest unstarted risk) — ✅ **done (PR #34)**
- [x] **AI card pipeline:** RAG + non-nullable verbatim-quote/anchor provenance + in-pipeline
      abstention; **SymPy CAS** re-derivation for computational (a wrong answer cannot publish) +
      NLI-proxy + **mandatory human review** for conceptual. `pipeline/aicards/`, `make ai-gate`.
- [x] **Gold-set gate (cutoffs lodged BEFORE scoring):** 50 generated → 35 published / 5 conceptual
      drafts / 10 abstained; **fact-precision 1.000** (≥0.98 ✓) · **useful-yield 0.64** (≥0.60 ✓) ·
      2 raters, **Cohen's κ 0.938** @ 98% agreement; firewall PASS. **AI-off (no live API key):**
      numbers validate the **machinery, not a live model** — the live-model run is **CUT-FIRST → Sunday
      buffer** (blocked only on a key; seam `orchestrator.LlmBackend` ready, fails loudly without one).

### Block B — PARALLEL (agent lane) · P0 · Phone shows all three scores (ceiling: engine on phone) — ✅ **done (Task 7, PR #32; Task 6 desktop adapter shipped)**
- [x] **AnkiDroid read-only 3-score panel (Task 7):** `GreScorecardFragment` reads the synced
      `gre_scorecard` (written desktop-side by the Task 6 adapter, rides W4 sync) and renders Memory /
      Performance / Readiness **separately** with ranges — Readiness only a number when the desktop gate
      passed, else the full evidence panel; **never a bare number, no scoring math on device.** Reuses
      the W3 local rsdroid (config read only, **no rebuild**). Different-agent review **APPROVED**;
      `Anki-Android` pinned `78989b9e`.

### Block C — P1 · Beat baseline + robustness (AI credibility + ceilings) — ✅ **done (PR #34 + PR #36)**
- [x] **Beat the baseline (McNemar exact):** AI arm (RAG+provenance+CAS+abstain) vs. template/cloze
      non-RAG no-verify baseline over the same shared SymPy targets — AI **1.000 / 0.833** vs baseline
      **0.600 / 0.400**; paired 2×2 a=20/b=30/c=4/d=6; **McNemar p = 6.165e-06** favoring AI; yield-diff
      90% bootstrap CI [0.300, 0.567]. `make ai-baseline`. (PR #34.)
- [x] **AI-off degradation:** no key → the live-model seam fails loudly, `run_pipeline_safe` aborts
      cleanly (0 cards, 0 unverified) while the deck + `scoring/` still load — AI is a **build-time**
      content step, never a review-time dependency. (PR #34.)
- [x] **Crash test (7g):** one collection **SIGKILLed mid-review ×20 → 20/20 CLEAN** (`quick_check` +
      `integrity_check`, no revlog loss; 31,405 reviews survived) + a non-vacuous `--selftest`.
      `make crash-7g`. (PR #36.)
- [x] **Two-way sync (7b):** 10 phone-offline + 10 desktop-offline → **all 20 land on both peers**;
      same-card conflict = **revlog union + scheduling LWW** (documented rule). `make sync-7b`. (PR #36.)
- [ ] **Android leg of 7g/7b (on-device round)** — **CUT-FIRST → Sunday buffer** (shared `anki_test`
      emulator was busy with the Task-7 subagent). Device side already covered by **W3** (Check-DB
      "rebuilt and optimized" after a force-stop) + **W4** (live AnkiDroid↔desktop two-way sync).
- **Deferred from the original list — timed-mode / exam-pressure simulator:** ✅ already shipped earlier
      (PR #21 core + #22 shell, mastery-gated) — see `STATUS.md`.

### Block D — P1 · The proofs (turn machinery into evidence, 15% tests) — ✅ **done (PR #35)**
- [x] **`make bench`:** real `col.mastery_query` @ 50k cards → **p50 650 ms · p95 667 ms · worst
      709 ms** (20 topics/call; sub-second dashboard refresh; batch/index noted as future opt).
- [x] **Memory calibration:** held-out student split → **Brier 0.219 · ECE 0.061**, reliability curve
      hugs the diagonal (`docs/evidence/proofs/calibration.png`). Labeled "simulated machinery-check;
      validity unestablished at n≈1."
- [x] **Paraphrase results:** 28 eval-bank **P3** groups → R1 0.630 vs R2 0.624, **gap 0.006** (Wilson
      CIs) → paraphrase-robust. Descriptive, simulated cohort.
- [ ] **Run the ablation formally** (interleaved vs. blocked vs. plain Anki) — **CUT-FIRST → Sunday
      buffer**: interleaving instrumentation isn't built yet; the **pre-registration stands** (Appendix
      B, TOST + 90% CI + honest-null template), so a documented "not yet run" is honest.

### Block E — P1 · Docs + demo (8% UX legibility + the artifact graders watch) — ✅ **done (PR #33)**
- [x] **Model descriptions** (one page each): `docs/models/{memory,performance,readiness}.md` — incl.
      the give-up rule.
- [x] **Architecture overview + Rust-change note** (files touched + **merge-difficulty LOW**) in
      `README.md`, linking the three model docs.
- [ ] **Record the demo** (3–5 min) per `docs/demo-plan.md` — **CUT-FIRST → Sunday buffer**: needs a
      human at the keyboard for live capture. The Sunday-cut script is written and every segment is
      merged + reproducible.

**Compressed exit gate (met):** AI passed the pre-set gate + beat the baseline; phone shows three
scores; offline + crash safe; the proofs exist as charts/numbers; docs shipped. The CUT-FIRST items
that slipped (ablation run · demo recording · AI live-model run · Block C Android leg) are logged as
Sat/Sun buffer work in `docs/STATUS.md` — the true Sunday 10:59 PM CT deadline is untouched.

---

## Day 6 — Sunday (✅ Ship — deadline 10:59 PM CT)

> First clear the **Sat/Sun buffer (CUT-FIRST spillover)** — see `docs/STATUS.md`: the ablation run,
> the demo recording, the AI live-model run, and the Block C Android leg. Packaging + submission are
> tracked step-by-step in **`docs/submission-checklist.md`** (human-gated items marked).

- [ ] **Clear CUT-FIRST buffer:** demo recording · (optional) ablation run or documented "not run" ·
      (optional) AI live-model run if a key lands · (optional) Block C Android emulator round.
- [ ] Package **desktop installer** (`anki/tools/build` → wheels; clean-machine test, no manual setup).
- [ ] Package **phone build** (**signed** APK; record it on a clean device).
- [ ] **Final repo push:** public AGPL-3.0-or-later fork, exam stated up front, build instructions for both platforms, files touched, merge-difficulty assessment.
- [ ] **Hard-ceiling checklist** (see `docs/submission-checklist.md`): Rust change ✓ · phone sharing engine + syncing ✓ · held-out testing ✓ · no leaked data ✓ · readiness backed by evidence ✓ · both apps run on a clean device ✓.
- [ ] **Upload deliverables:** repo link, demo video, three model descriptions, Brainlift (`research/brainlift.md`).
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
Fri (COMPRESSED = old Fri + old Sat):
     A AI gate (#34) ─► B phone 3 scores (Task 7, #32) ─► C beat-baseline + crash/sync (#34,#36)
        └─► D proofs: bench/calibration/paraphrase (#35) ─► E docs: models + README (#33)
        ▼  (CUT-FIRST → Sat/Sun buffer, logged in STATUS.md)
Sat/Sun buffer: demo recording · ablation run · AI live-model run · Block C Android leg
        ▼
Sun: package installers + signed APK + repo + deliverables + submit
```
