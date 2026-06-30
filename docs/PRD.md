# PRD — GRE Math Subject Speedrun

> **One exam. Two apps on one engine. A real engine change. Three scores we can back up.**
> A public AGPL-3.0-or-later fork of Anki that prepares students for the **GRE Mathematics Subject Test**, measures **memory ≠ performance ≠ readiness** separately with honest ranges, and refuses to score when it lacks evidence.

---

## 0. Document Control

| Field | Value |
|---|---|
| Status | **v0.2 — Tuesday decisions locked & SIGNED OFF (2026-06-30)** |
| Date | 2026-06-30 (Day 1, Tuesday) |
| Owner | Technical lead |
| Deadline | **Sunday 2026-07-05, 10:59 PM CT** |
| Sources of truth (in priority order) | `research/brainlift.md` → `research/SYNTHESIS.md` → `research/responses/*` → `docs/project-spec.md` (the assignment) → this PRD |
| Confidence tags | `[strong] / [moderate] / [weak-contested]` carried over from the research synthesis; they describe **evidence strength**, not certainty of opinion. |

**Reading order for the team:** this PRD (the what/why) → `docs/execution-plan.md` (the how/when, day-by-day).

---

## 1. Mission & Thesis

Flashcards measure one thing: memory. A real exam asks for three. Our job is to build the two bridges Anki does **not** give us — *memory → performance* (answering unseen exam-style questions) and *performance → readiness* (a real GRE score) — and to be ruthlessly honest about the uncertainty in both.

**The spiky bet (from `brainlift.md`, DOK 4):** the highest-scoring, most defensible posture is *honesty as a feature*. There is **no public raw→scaled GRE mapping** [strong], we have **n≈1 student over one week** [strong], and the whole learning-science effect base is **weaker in math than in verbal domains** [moderate]. So a readiness *range* with an evidence panel and a "no track record yet" disclosure is not a consolation prize — it is the correct, grade-rewarded output. A confident number with no evidence is an automatic fail.

**What we are explicitly NOT doing:** blending the three scores; claiming a personally-calibrated memory model on one week of data; claiming a validated readiness number; making olympiad problems a core feature (the evidence does not support far transfer — they ship only as an optional, off-by-default, capped enrichment for already-strong students).

---

## 2. Locked Decisions (the five irreversible Tuesday calls)

These are locked per the research. **Do not switch mid-week** — the risk register exists because switching kills the testing buffer. Two of the five (D1, D3) are flagged for explicit sign-off in §16 before any code is written.

### D1 — Rust change: **read-only Mastery Query** (candidate c)  `[moderate, code-confirmed-with-caveats]`

A new backend call returning, per topic, mastered-card count + average recall, fast enough to power the dashboard on 50,000 cards.

- **Why this one:** it is the only candidate that **never calls `transact`**, so it is *structurally incapable* of corrupting the collection or breaking undo, while still being a genuine Rust change (new proto message + new read RPC + SQL aggregate + `pylib` binding). It lands on Anki's most stable insertion points (additive proto + storage/service read layer), avoiding the version-volatile `scheduler/answering/` and `scheduler/fsrs/` code. Finishable and testable in a week. (`responses/05`, critique 05.)
- **Rejected:** (a) points-at-stake queue — medium risk, persisting a re-sort writes `due` and trips the `card.mtime == entry.mtime()` queue assertion; (b) topic-aware scheduling — highest risk, touches FSRS interval correctness + undo of `answerCard`. **Avoid (b) entirely this week.**
- **Stretch (additive, never a switch):** if Wednesday buffer holds, prototype (a) as a **non-persistent, flag-gated, in-memory re-sort inside `QueueBuilder`** (never writes `due`). This also becomes the engine-level home for interleaving (§8).
- **Topic metadata lives in tags, not a schema column** (§6). A new SQLite column bumps `SCHEMA_MAX_VERSION` (currently 18) and breaks sync round-trip. `[strong]`
- **Footguns to encode in tests:** read RPC must return a plain response message, **never `OpChanges`** (would imply mutation/clear undo); include a read-only-invariant test asserting undo stack + queue counts are byte-for-byte unchanged.
- **Build-time caveat:** many internal symbols in `responses/05` are `[inferred]`. **Pin Anki to a tagged release and verify every path/symbol against it before building.**

### D2 — Three-score architecture + give-up rule  `[strong]`

Three scores, **never blended**, each with an honest range:

| Score | Definition | Engine | One-week honest claim |
|---|---|---|---|
| **Memory** | P(recall this card now) | FSRS-6 / FSRS-rs (Anki built-in) | **Aggregate-calibrated** (population defaults), not personalized. Don't claim personal calibration < ~1,000 reviews. |
| **Performance** | P(correct on a new, unseen exam-style item) | Calibrated logistic regression + Platt scaling | Calibrated probability with honest (wide) intervals; difficulty **imported/firewalled**, never estimated in-house from this student. |
| **Readiness** | Projected GRE 200–990 score | raw-correct distribution → published ETS percentile anchors → scale, with conformal interval (headline) + Bayesian cross-check | A **RANGE + evidence panel + "no track record yet"**, never a single number. |

**The Honesty Rule (hard requirement).** The app may not display a readiness score unless it simultaneously shows: (1) the point estimate, (2) the likely range, (3) % of exam topics covered, (4) a "how sure" indicator, (5) last-updated timestamp, (6) the main reasons behind it, and (7) the single best next thing to study.

**The give-up rule (LOCKED today).** Readiness is shown **only when ALL hold**:
1. **≥ 200 graded reviews** (operational proxy), **AND**
2. **≥ 50% topic coverage** = ≥ 50% of taxonomy leaf nodes (§6, Appendix A) have at least one graded review, **AND**
3. **Principled target:** the conformal/credible interval width is **below a pre-declared usefulness threshold** (the review-count and coverage minima are proxies; interval width is the real gate).

Below threshold the app shows **"Insufficient evidence to score"** with the coverage map and the next best topic to study. (`responses/03` §D; SYNTHESIS SQ3.)

### D3 — Mobile + sync: **Android via AnkiDroid `rsdroid` + desktop Anki; iOS deferred**  `[moderate-strong judgment]`

- **Path:** Android client built on AnkiDroid's `rsdroid` backend — the *real* shared `rslib` over JNI, with collection + media **sync working out of the box**. Desktop runs the same `rslib`. This is genuinely "one engine on both" and **clears the 70% no-phone grade ceiling**. (`responses/06` §C.)
- **iOS is OUT OF SCOPE** for the deadline: there is no open-source Anki iOS app; a from-scratch `rslib` → UniFFI → xcframework port with working two-way sync **is not realistic in one week**. Listed as a documented bonus only. *(Flagged for sign-off in §16 — this diverges from "set up both environments.")*
- **Our custom Rust change must flow into the rsdroid build** (anki as a git submodule); verify the mastery-query proto/RPC is reachable from the Android backend.
- **Conflict rule (DOCUMENTED today, mirrors Anki's decade-tested model):**
  - **revlog entries are UNIONED** — both reviews survive (revlog PK = epoch-ms, distinct per device). No review is ever lost.
  - **Card scheduling state (due/interval/ease/queue/reps/lapses) is LAST-WRITER-WINS** by most-recent answer.
  - **Deterministic tie-break:** lexicographically lower device-UUID wins (removes Anki's order-dependence → makes the test reproducible).
  - **Structural/schema divergence → forced one-way full sync** (mirror Anki; the losing side's structural changes are discarded). **Construct the conflict demo as pure review divergence** (no notetype/template edits) or Anki falls back to full-sync overwrite and the demo proves nothing.
  - **Test harness:** Anki's built-in Rust `anki-sync-server` (self-hosted), pinned to our release tag.

### D4 — GRE topic taxonomy: **ETS three-bucket outline, verbatim leaf nodes, hierarchical tags**  `[strong]`

- Build directly on ETS's official outline: **Calculus ~50% / Algebra ~25% / Additional ~25%**. Use ETS's verbatim sub-bullets as leaf nodes. **Do not invent sub-percentages within buckets** — ETS does not publish them.
- **Tags are the single shared substrate** for the mastery query (D1), the coverage map (§7c), and interleaving (§8). One taxonomy, used four ways. Hierarchical `topic::bucket::leaf` strings (full list in **Appendix A**).
- **Every card maps to exactly one leaf topic.** Re-tagging later is expensive — the taxonomy is frozen at the leaf level today.
- **Scoring facts locked (Appendix C):** 200–990 scale, ~66 items, 2h50m, rights-only. Use **© 2025 ETS norms (mean 680, SD 161, N 5,180; 880 → 88th pct)**, **date-stamped in-app, never hard-coded**. Offer a GR3768-based estimator labeled "form-specific, ceiling 970, 60→880." Corrected benchmark: **~60/66 → 880 → ~88th**, not the folklore "57–58/66 → 880."

### D5 — Learning-science feature + ablation: **Interleaving, pre-registered today**  `[strong method]`

- **Ship interleaving** (mix confusable GRE problem types within a session via topic tags). It is the only learning-science increment over Anki (which already does retrieval + spacing) with direct preregistered far-transfer **math** evidence (Rohrer 2020, classroom d≈0.83; Brunmair & Richter math g≈0.34). Mechanism = forcing *strategy selection before execution*, exactly the GRE task.
- **Honest caveat baked in:** the realistic *incremental* effect over an already-spaced app is **dz≈0.2–0.35**, not 0.83 — and a 1-week tiny-n run is powered only for dz≈0.8. This is an **estimation/feasibility pilot**, not a confirmatory trial.
- **Pre-registered hypothesis + full protocol locked in Appendix B (dated 2026-06-30).** Three arms (full app / feature-off / plain Anki), within-subject, Latin-square counterbalanced, **delayed (≥1 wk) primary endpoint**, TOST + 90% CIs, honest-null template.
- **Interleaving keeps the single ablation slot.** Anxiety inoculation ships as an **un-ablated complement** (reappraisal microcopy + optional worry-dump/breathing) and the **exam-pressure simulator justified on the GRE speededness construct**, NOT the (fragile) anxiety literature.

---

## 3. Hard Ceilings & Grade-Weight Map

Every decision above maps to a grade lever. We optimize in weight order, but the **hard ceilings come first** because they cap everything.

| Hard ceiling | Consequence | Our guarantee |
|---|---|---|
| No real Rust change | 50% max | D1 mastery query, end-to-end, tested |
| No phone sharing engine + syncing | 70% max | D3 Android via rsdroid + working sync |
| No re-runnable test setup | 60% max | `make bench`, seeded fixtures, pinned deps, documented commands |
| No held-out testing | 60% max | Leakage-isolated authored item bank (§11/§12) |
| Made-up readiness numbers | **automatic fail** | D2 ranges + give-up rule + "no track record" |
| Either app fails on clean device | 50% max | Clean-machine install + signed APK, recorded |
| Leaked test data | that score → 0 | One leakage pipeline; author original eval items |
| AI claims with no traceable source | AI section → 0 | Provenance-by-schema; abstain if unsupported |

| Grade area | Weight | Primary days | PRD section |
|---|---|---|---|
| Rust change & fit with Anki | 20% | Wed–Thu | §5 |
| Score accuracy + honest uncertainty | 20% | Fri–Sat | §7 |
| Study feature (interleaving ablation) | 15% | Fri–Sun | §8 |
| AI checking + safety | 15% | Sat–Sun | §9 |
| Fair, re-runnable tests | 12% | Fri–Sun | §11 |
| Desktop + phone one engine + sync | 10% | Wed–Fri | §10 |
| Product + UX (both apps) | 8% | Sat–Sun | §7, §10 |

---

## 4. Architecture Overview

```
                         ┌──────────────────────────────────────┐
                         │   Shared engine:  Anki rslib (Rust)    │
                         │  FSRS · queue · storage(SQLite) · sync │
                         │  + NEW: Mastery Query RPC (read-only)  │
                         └──────────────────────────────────────┘
                            ▲ protobuf            ▲ JNI (rsdroid)
                            │ (pylib/rsbridge)    │
              ┌─────────────┴───────────┐   ┌─────┴───────────────┐
              │  DESKTOP (Anki/Qt+Py)   │   │  ANDROID (AnkiDroid  │
              │  - review loop (FSRS)   │   │  fork via rsdroid)   │
              │  - 3-score dashboard    │   │  - review loop       │
              │  - coverage map         │   │  - 3 scores + ranges │
              │  - interleaving toggle  │   │  - give-up rule      │
              │  - AI card pipeline     │   │  - offline review    │
              │  - exam-pressure sim    │   │                      │
              └─────────────────────────┘   └──────────────────────┘
                            │  two-way sync (revlog union + sched LWW) │
                            └──────────────►  anki-sync-server  ◄──────┘

   Scoring services (Python sidecar, desktop-authoritative):
     Memory (FSRS R) → Performance (logistic+Platt) → Readiness (percentile-anchored + conformal)
   AI pipeline (desktop, AI-off-able): RAG + provenance schema + CAS/SymPy verify → gold-set gate
   Eval/tests: leakage pipeline · authored item bank (4 partitions) · paraphrase · crash · make bench
```

**Key principle:** the engine is shared and unmodified except for the additive, read-only mastery query. Everything score/AI-related lives *above* the engine so it can be switched off (AI-off requirement) without affecting the review loop.

---

## 5. The Rust Change (20%) — Mastery Query

### 5.1 What it does
A new read-only RPC: given a set of topic tags, return per topic `{ mastered_count, avg_recall, total_cards }`, computed as one grouped SQL aggregate over `cards` joined to notes/tags, using existing FSRS retrievability SQL helpers for "avg recall." Powers the dashboard mastery view and feeds the Performance model's per-topic mastery feature.

### 5.2 Surface area (verify against pinned release before coding)
- `proto/anki/` — new `MasteryRequest { repeated string topics }` / `MasteryResponse { repeated TopicMastery }` message (in a new `stats`-style service or additive to an existing read service).
- `rslib/src/.../service/mod.rs` — new read RPC returning the response message (**never `OpChanges`**).
- `rslib/src/storage/card/` — grouped SQL aggregate; reuse `extract_fsrs_relative_retrievability()` / FSRS variable helpers.
- `pylib/anki/collection.py` — new binding.
- `rsdroid` build — confirm the new RPC is reachable from Android.

### 5.3 Tests (spec-required)
- **≥3 Rust unit tests:** (1) empty/zero case; (2) aggregation correctness vs hand-computed values across two topics; (3) **read-only invariant** — undo stack + study-queue counts unchanged after the call.
- **1 Python integration test:** open temp collection, add tagged notes, call binding, assert protobuf; assert `add_note → undo` round-trips with the mastery call in between.
- **Corruption assert:** `PRAGMA quick_check` → `ok` and collection reopens after the op.
- **Perf:** benchmark the aggregate at 50k cards; if > ~50 ms, add/confirm an index rather than caching.

### 5.4 "Why Rust, not Python" (the graded one-pager — draft)
1. **Performance at scale:** the dashboard needs per-topic mastery over 50,000 cards on every refresh. In Rust it is **one indexed grouped aggregate inside the engine**; in Python it would mean pulling all card states across the protobuf/`rsbridge` boundary and aggregating in the interpreter — many round-trips, far slower, blowing the p95 dashboard targets.
2. **Reuses engine-only primitives:** FSRS retrievability is computed by Rust SQL helpers (`extract_fsrs_relative_retrievability`) not exposed to Python; computing "avg recall" correctly means doing it where those primitives live.
3. **Ships to both platforms for free:** because it lives in `rslib`, the same change runs on desktop and on Android via `rsdroid` — a Python-only helper would have to be re-implemented per client.
4. **Correctness boundary:** keeping it read-only and in-engine means it cannot drift from the engine's own notion of card state.

Deliverable also includes: the diff, the list of upstream files touched, and a **merge-difficulty assessment** (low — additive proto message + read RPC + read SQL on stable insertion points).

---

## 6. Data Model — The Topic Tag Taxonomy

The taxonomy is the **architectural keystone**: one `topic::*` tag tree feeds the mastery query, the coverage map, the readiness gate, and interleaving. Frozen at the leaf level today (see **Appendix A** for the full list and exact tag strings).

- **Form:** hierarchical Anki tags `topic::<bucket>::<leaf>` (e.g., `topic::calculus::integral_single`). No schema change; syncs cleanly; user-visible.
- **Rule:** every card carries exactly one leaf `topic::` tag. Cards may carry additional non-topic tags (e.g., `src::stewart_ch7`, `gen::ai`, `eval::p0`).
- **Coverage definitions:**
  - *Deck coverage* (coverage map on dashboard) = % of leaf topics with ≥ 1 card.
  - *Studied coverage* (readiness gate, D2) = % of leaf topics with ≥ 1 graded review.
- **Bucket weights** (50/25/25) come from ETS and are used only at the bucket level for readiness weighting; never fabricate intra-bucket weights.

---

## 7. Three-Score System (20%) + Honesty

### 7a. Memory
FSRS-6 / FSRS-rs retrievability `R`. Presented as **aggregate-calibrated** (population defaults). Calibration proof (Day 5) only *when* enough reviews exist: TimeSeriesSplit → reliability diagram with binomial CIs → ECE (≥2 binning schemes, prefer quantile) → Brier + log-loss as bin-free anchors. Declare "calibrated" only if diagram points sit within CI of the diagonal. **Do not surface card-level `R` as an exam-pass probability.** (`responses/02`.)

### 7b. Performance
Calibrated **logistic regression + Platt scaling**. Features: per-topic mastery (from D1), **imported** item difficulty (firewalled — never estimated on the same data used to validate), response timing, topic coverage. Evaluated by **Brier score + reliability curve + ECE** on a **leakage-audited held-out split**. Hierarchical/Bayesian wrapper for honest (wide) intervals at n≈1. **Paraphrase test (§11) is the go/no-go** on whether Performance is real vs. just copying Memory. (`responses/03` §A–B.)

### 7c. Readiness + Coverage Map
Pipeline: predict raw-correct distribution on a representative item set → map to percentile via **published ETS percentile anchors** → percentile → 200–990 scaled score → **propagate uncertainty** through all three steps. **Conformal interval as headline, Bayesian posterior as cross-check.** Ship a **RANGE + evidence panel + "no track record yet"** panel (predictive validity is unestablished at n≈1; intervals reflect model-internal uncertainty only). Start a **prospective calibration log** (predicted vs. realized) immediately. Coverage map lists every leaf topic, marks covered, shows %, and **gates the score** per the give-up rule. (`responses/03` §D, `responses/01` §C–E.)

**Honest display format (target):**
```
Projected GRE Math Subject:  ~810   (likely 740–880)
Confidence: low — you've covered 41% of exam topics; no track record yet.
Top driver: strong on single-var calculus; Biggest gap: real analysis.
Next best study: real analysis → sequences & series.   Updated: 2026-07-05 14:02
```

---

## 8. Learning-Science Feature (15%) — Interleaving + Ablation

- **Implementation:** interleaving is a **card-ordering rule** over the already-gathered due queue — mix confusable problem types (by `topic::` tag) within a session rather than blocking by topic. Default home: Python/presentation layer (safe, FSRS-invariant). Stretch: implement the ordering as the flag-gated in-memory re-sort in `QueueBuilder` (ties into D1 stretch). A simple toggle switches interleaved ↔ blocked for the ablation.
- **Three builds:** (1) full app, interleaving ON; (2) full app, interleaving OFF (blocked) — the ablation; (3) plain unmodified Anki — the baseline.
- **Pre-registration:** see **Appendix B** (locked 2026-06-30). Primary endpoint is a **delayed (≥1 wk) test of novel mixed-topic items**; analysis is TOST + 90% CIs with the honest-null template. Expect an honest inconclusive result and report it as a win.
- **Complement (un-ablated):** exam-pressure simulator (timed full-length: 66 items / 2h50m / on-screen countdown / no pauses) justified on **format-matched transfer + speededness**, plus reappraisal microcopy. Surface the anxiety bundle only when the app detects a **Memory-high / timed-Performance-low gap**.
- **Olympiad:** optional, ≤10% dose, off by default, gated to already-strong students (~80th pct+) with ≥6 weeks, topic-targeted to GRE-scored overlap, MC-formatted with a ~2.5-min timer. Positioned as *content to interleave*, not a separate pedagogy.

---

## 9. AI Card Pipeline (15%) — Safety First

- **Generation:** RAG with **source binding** — every card carries a **verbatim source quote + page/line anchor as a non-nullable schema field**. Abstention enforced by **pipeline logic, not the prompt**; any card lacking an entailed source span is auto-zeroed before evaluation.
- **Verification by card type:** *computational* cards → **CAS/SymPy re-derivation** (symbolic + numerical equality) as the gate (decisive, deterministic, independent of the generator); *conceptual/definitional* cards → NLI entailment against source (RAGAS faithfulness) + **mandatory human adjudication**. Self-consistency / model critics only as pre-filters that reduce CAS workload — **never the final gate**.
- **Pre-registered asymmetric gate (lodged before scoring):** **fact-precision ≥ 0.98 (≤ 1 wrong-fact card / 50) AND useful-yield ≥ 0.60** among non-abstained cards. Expect **low yield — that is the correct safe tradeoff.** Wrong facts are worse than no card.
- **Gold set:** 50 independently-verified Q&A pairs (textbook keys, second-solver checked), each with a source anchor, in an **access-controlled store** with canary strings. Identify the source for these **today** (Tuesday checklist).
- **Beat a baseline:** vs. template/cloze extraction + non-RAG prompting, McNemar's exact test + paired bootstrap CI on useful-yield, fact-precision ceiling intact.
- **Don't let weakly-verified conceptual cards inflate apparent topic coverage** (interacts with §7c readiness honesty).

---

## 10. Mobile + Sync (10%)

- **Android:** AnkiDroid fork consuming `rsdroid` (anki as submodule, with our mastery-query change). Loads the GRE deck, runs a real review session on the shared engine (Wed), two-way sync + three scores + give-up rule (Fri).
- **Sync conflict rule:** as locked in D3 (revlog union + scheduling LWW + device-UUID tie-break + structural→full-sync). Documented Thursday; tested Thursday/Friday.
- **Sync test (7b):** 10 cards offline on phone + 10 different on desktop → reconnect → all 20 land (none lost/double-counted). Then same card both devices offline → sync → documented winner. Keep it pure review divergence.
- **Crash/offline (7g):** kill each app mid-review ×20 → zero corrupted collections (SQLite `BEGIN IMMEDIATE` + WAL makes this safe); pull network → AI off cleanly, both apps keep working and still show a score.

---

## 11. Evaluation, Tests & Re-Runnability (12%)

- **One leakage pipeline** (shared by performance eval, AI-gen, item bank): exact → normalized → n-gram/Jaccard (>0.7–0.8, flag shared 13-gram) → embedding cosine (>0.85–0.9), MinHash+LSH for scale, human-adjudicate the 0.75–0.90 band, **publish the residual leakage rate**. Project-specific canary GUID.
- **Paraphrase test (7d):** 30 cards × 2 rewordings = 60 pairs. The real test: does Performance predict **reworded** accuracy **better than a memory-only baseline**? McNemar **mid-p** + TOST (±10pp) + paired bootstrap, reported **descriptively with Wilson CIs** (30×2 is underpowered → consistency probe, not a significance test). Pre-screen to mid-difficulty cards.
- **`make bench` (7h):** load the 50,000-card deck, print p50/p95/worst for button-ack, next-card, dashboard load, dashboard refresh, sync. Criterion for engine ops; custom harness/hyperfine for sync. Targets in Appendix C.
- **Re-runnability:** pinned Anki release tag, pinned dependency versions, seeded synthetic deck generator, one documented command per test, deterministic outputs.

---

## 12. Decks & Item Banks

Two **separate** corpora — do not conflate (this protects the held-out test):

1. **Study deck** (for review): textbook-derived + AI-generated (gated) cards, every card leaf-tagged. Must cover **≥ 50% of taxonomy leaf nodes** before Wednesday's build. Target ≥ 50% calculus weight.
2. **Authored eval item bank** (for performance/readiness/paraphrase/ablation): **original, blueprint-matched items only.** All ~431 official ETS items are public PDFs → **treat the entire ETS corpus as contaminated; never reuse it.** ~60–100 items across **4 disjoint, version-locked partitions**: P0 frozen held-out / P1 ablation-practice / P2 delayed post-test / P3 paraphrase pairs. Difficulty is **expert-rated, provisional, noisy (r≈0.6)** → widens the readiness interval; flag every difficulty as provisional; every number reported with Wilson CIs.

---

## 13. Milestones & Acceptance Criteria

### Milestone 1 — Wednesday (foundations, NO AI)
- [ ] Anki forked, building from source (commit hash, clean-build recording).
- [ ] Mastery-query Rust change end-to-end: diff + 3 Rust unit tests + 1 Python integration test + undo-still-works + no-corruption proof.
- [ ] Desktop loads the GRE deck and runs a real FSRS review session.
- [ ] Memory score displayed with an honest **range** (not a single number).
- [ ] Coverage map visible on the dashboard; readiness gated by the coverage threshold.
- [ ] Android app loads the exam deck and runs a real review session on the shared engine.
- [ ] Sync conflict rule documented; manual sync smoke test passes.
- [ ] Desktop installer runs on a clean machine (recorded).
- **Gate:** can we review cards on both devices using the same engine?

### Milestone 2 — Friday (AI on + sync proven + phone shows 3 scores)
- [ ] AI gold-set run: 50 cards scored into correct/wrong/bad-pedagogy with the **pre-set** cutoff; passes fact-precision ≥0.98 & useful-yield ≥0.60 (or documented honest failure).
- [ ] AI beats the defined baseline (McNemar).
- [ ] Phone shows all three scores with ranges; give-up rule enforced.
- [ ] Two-way sync proven (10+10 test); same-card conflict resolved per the documented rule.
- [ ] Exam-pressure simulator (timed full-length) working.
- [ ] AI degrades cleanly offline; both apps keep working and still score.
- [ ] Crash test: kill each app mid-review ×20 → zero corrupted collections.

### Final — Sunday 10:59 PM CT (prove + ship)
- [ ] Ablation run formally (3 arms); results reported honestly (null is fine).
- [ ] Memory calibration chart (80% ⇒ ~80% on held-back reviews).
- [ ] Paraphrase test results (original vs. reworded gap reported honestly).
- [ ] `make bench` on 50k deck (p50/p95/worst).
- [ ] Three model-description one-pagers (memory, performance, readiness, incl. give-up rule).
- [ ] Architecture overview + Rust change note + files-touched + merge-difficulty in README.
- [ ] Desktop installer + signed APK both run on clean devices (recorded).
- [ ] Demo video (3–5 min). Public AGPL-3.0-or-later repo. Brainlift. Submit.

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Rust change scope creep / switching candidates | Locked D1 (mastery query) today; (a)/(b) are additive stretch only, never a switch. |
| Build pain (Anki compile + mobile) eats the week | **Day 1–2 priority is getting Anki to compile, one tiny Rust change to show up, and the engine on a phone** — before features. Pin a release tag. |
| iOS FFI unresolved | Already decided: **Android-only**; iOS is documented bonus. No time spent on iOS env. |
| `[inferred]` Rust symbols wrong | Verify every path/symbol against the pinned release before coding (build-time check). |
| AI card quality failure | Pre-commit the asymmetric cutoff; a documented failure still scores. |
| Sync conflict edge cases | Conflict rule documented Thursday; keep the demo to pure review divergence; don't redesign later. |
| No longitudinal data for readiness | Step 1–3 with honest ranges + "no track record"; Step 4 is bonus only. Wide interval is the correct output. |
| Leaked ETS data zeroes a score | Author all eval items; never reuse ETS; run the leakage pipeline; publish residual rate. |

---

## 15. Deliverables (Sunday)

1. **Public GitHub repo** (AGPL-3.0-or-later, credit Anki): exam stated up front, build instructions for both platforms, architecture overview, Rust change note, files touched, merge-difficulty assessment.
2. **Demo video (3–5 min):** review session → Rust change in action → card synced phone→desktop → three scores with ranges → AI features → test results.
3. **Three model descriptions** (one page each: memory, performance, readiness — incl. give-up rule).
4. **Brainlift** (`research/brainlift.md`).

---

## 16. Sign-Off Log (resolved 2026-06-30)

All irreversible calls confirmed by the project owner — **no switching mid-week.**

1. ✅ **D1 Rust change = read-only Mastery Query.** Confirmed.
2. ✅ **D3 = Android-only via rsdroid; iOS = documented bonus only.** Confirmed (no Tuesday hours spent on iOS).
3. ✅ **Exam target = GRE Mathematics Subject Test.** Confirmed.
4. ✅ **Give-up thresholds = ≥200 graded reviews + ≥50% leaf-topic coverage + interval-width target.** Confirmed.

D2, D4, D5, the taxonomy, the ablation pre-registration, and the AI gate are locked per research (above + appendices).

---

## Appendix A — GRE Topic Taxonomy (leaf nodes + tag strings)

Bucket weights are ETS-official (50/25/25). **No intra-bucket sub-percentages** (ETS does not publish them). Every card gets exactly one leaf tag.

### I. Calculus — 50%  (`topic::calculus::*`)
| Leaf | Tag |
|---|---|
| Single-variable differential calculus | `topic::calculus::differential_single` |
| Single-variable integral calculus | `topic::calculus::integral_single` |
| Multivariable differential calculus | `topic::calculus::differential_multi` |
| Multivariable integral calculus | `topic::calculus::integral_multi` |
| Differential equations | `topic::calculus::differential_equations` |
| Applications, coordinate geometry & trig connections | `topic::calculus::applications` |

### II. Algebra — 25%  (`topic::algebra::*`)
| Leaf | Tag |
|---|---|
| Elementary algebra | `topic::algebra::elementary` |
| Linear algebra (matrices, systems, vector spaces, linear transformations, char. polynomials, eigenvalues/vectors) | `topic::algebra::linear` |
| Abstract algebra (group theory, rings & modules, field theory) | `topic::algebra::abstract` |
| Number theory | `topic::algebra::number_theory` |

### III. Additional Topics — 25%  (`topic::additional::*`)
| Leaf | Tag |
|---|---|
| Introductory real analysis (sequences & series of numbers/functions, continuity, differentiability, integrability, elementary topology of ℝ and ℝⁿ) | `topic::additional::real_analysis` |
| Discrete mathematics (logic, set theory, combinatorics, graph theory, algorithms) | `topic::additional::discrete` |
| General topology | `topic::additional::topology` |
| Geometry | `topic::additional::geometry` |
| Complex variables | `topic::additional::complex` |
| Probability & statistics | `topic::additional::probability_stats` |
| Numerical analysis | `topic::additional::numerical` |

**Non-topic tag conventions:** `src::<source>` (provenance), `gen::ai` / `gen::human` (generation), `eval::p0|p1|p2|p3` (held-out partitions), `diff::<1-5>` (provisional difficulty), `olympiad` (enrichment, off by default).

---

## Appendix B — Ablation Pre-Registration (LOCKED 2026-06-30)

> Pre-registered **before** any data collection, per the spec. A pre-registered null still scores well; a post-hoc hypothesis scores nothing.

- **Feature:** interleaving (mixed-topic vs. blocked-topic review order).
- **H1 (primary, one sentence):** *On a delayed (≥ 1 week after last practice) test of novel GRE-style mixed-topic problems requiring strategy selection, accuracy in the interleaved (full-app) condition will exceed the blocked (feature-off) condition, holding item count and study time constant* — one-sided, **SESOI = dz 0.3 specified in raw score points.**
- **H2 (boundary/mechanism):** the interleaving advantage is larger for *confusable* problem types than for *dissimilar* types.
- **Secondary contrasts:** full-app vs. plain Anki; feature-off vs. plain Anki (isolates feature from platform).
- **Design:** three arms — (1) full app interleaving ON, (2) full app interleaving OFF (blocked), (3) plain unmodified Anki. **Within-subject**, Latin-square counterbalanced over arm sequences, **parallel non-overlapping item sets per arm** (drawn from eval partitions), longest feasible washout between arms. Analyze sequence + period as factors in a linear mixed model.
- **Primary endpoint:** delayed (≥1 wk) accuracy on novel mixed-topic items (reuse the leakage-isolated bank, P2 partition). Immediate test, if collected, is secondary (interleaving is a desirable difficulty → immediate tests *underestimate* it).
- **Analysis:** report effect estimate with **90% CI**; **TOST equivalence** against ±SESOI bounds **in raw score units**; honest-null language template.
- **Power reality:** n≈team-size (1–5) → powered only for dz≈0.8; detecting dz=0.3 needs ~90 learners. **This is an estimation/feasibility pilot, not a confirmatory trial.** Deliverable = the design + analysis machinery + an honest inconclusive result.

---

## Appendix C — Scoring Facts, Norms & Speed Targets

**Exam facts (ETS primary):** ~66 five-option MC items · 2h50m · single session · all items equal value · **rights-only** scoring · **200–990** scale (10-pt increments) · computer-delivered since Sept 2023 · no calculator.

**Norms — © 2025 ETS (cohort Jul 2021–Jun 2024), date-stamp in-app, never hard-code:** Mathematics **mean 680, SD 161, N 5,180**; **880 → 88th**, 860 → 84th, 800 → 71st, 680 ≈ 50th. Percentiles drift annually — re-check and show the source year.

**Raw→scaled:** **no public stable function exists** (ETS equates per form). Only the retired **GR3768** form is public: **60 → 880**, 57–58 → 860, ceiling **970**. Ship a GR3768-based estimator labeled "form-specific." Corrected benchmark: **~60/66 → 880 → ~88th** (not the folklore 57–58/66).

**Speed/reliability targets (`make bench`, both platforms):** button-ack p95 < 50 ms · next-card p95 < 100 ms · dashboard first load p95 < 1 s · dashboard refresh p95 < 500 ms · normal-session sync < 5 s · cold start < 5 s desktop / < 4 s phone · no UI freeze > 100 ms · **zero corrupted collections** in the crash test.

---

*End of PRD v0.1. Trace every requirement back to `research/` — that is the objective source of truth.*
