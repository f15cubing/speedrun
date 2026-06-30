## What Is the GRE Speedrun?

**Speedrun** is a hackathon-style project spec to build a rigorous, exam-focused study application on top of Anki's open-source codebase. The chosen exam is the **GRE Mathematics Subject Test**. The project has a hard deadline of **Sunday 10:59 PM CT** and is structured across three intermediate milestones (Wednesday, Friday, Sunday).

The core thesis: flashcards alone measure memory. This app must measure three distinct things — memory, performance, and exam readiness — and show them separately, with honest uncertainty ranges, rather than a single blended score.

---

## The Target Exam: GRE Mathematics Subject Test

- **Format**: 66 multiple-choice questions, 5 options each, 2 hours 50 minutes, no separate sections
- **Scoring scale**: 200–990 (converted from raw score)
- **Content split**: ~50% calculus and applications, ~25% algebra/linear algebra/abstract algebra/number theory, ~25% other undergraduate math topics
- **90th percentile target**: approximately 57–58 correct out of 66 (~scaled score 880)
- **Since September 2023**: administered online (previously paper-based)
- **Strategy note**: All questions are equally weighted; triage long problems and return to them

---

## Core Architecture Requirements

### Two Apps, One Engine
- **Desktop app**: primary tool — full review loop, score dashboard, AI features
- **Phone companion**: offline review + readiness check, two-way sync with desktop
- Both must share Anki's **Rust backend engine** — not a rewrite in JavaScript/Swift/Python
- Android: build on AnkiDroid or run Anki's Rust backend on-device
- iOS: run Anki's Rust backend through its C FFI interface
- Sync must handle conflicts: same card reviewed offline on both devices must resolve to a documented, correct winner

### Required Rust Change (Non-Negotiable)
The app must make a real change inside Anki's Rust engine — not just Python UI work. Candidate implementations (pick one):
1. **Points-at-stake queue**: new review order sorting due cards by `topic_weight × student_weakness`, highest-value first; requires new protobuf message
2. **Topic-aware scheduling**: surface weak-topic cards sooner while keeping FSRS intervals valid and undo working
3. **Mastery query**: backend call returning per-topic mastered count + average recall, fast enough for a dashboard on 50,000 cards

Deliverables for whichever Rust change is chosen:
- ≥3 Rust unit tests + 1 test calling the change from Python
- Proof that undo still works and the collection does not corrupt
- One-page note explaining why this belongs in Rust, not Python
- List of upstream files touched + merge difficulty assessment

---

## Three Scores — Show Them Separately

| Score | What It Measures |
|---|---|
| **Memory** | Probability the student recalls a specific fact right now (handled by Anki's FSRS) |
| **Performance** | Probability the student gets a new, unseen exam-style question right |
| **Readiness** | Projected score on the GRE 200–990 scale, with range and confidence level |

**Example honest readiness display:**
> Projected GRE Math Subject: 820  
> Likely range: 760–870  
> Confidence: low — you've covered only 38% of exam topics

### The Honesty Rule (Hard Requirement)
The app **may not show a readiness score** unless it also shows:
- What evidence produced the number
- What data is still missing
- How accurate past predictions have been
- A range (not a single number)
- The single best next thing to study

**Give-up rule**: Set a concrete threshold (e.g., "no score until 200 graded reviews and 50% topic coverage") and state it explicitly. The app must refuse to score when data is insufficient. A confident number with no evidence behind it is an automatic fail.

---

## Milestone Schedule

| Deadline | Requirement |
|---|---|
| **Wednesday** | Both apps run and review the same deck. No AI. Desktop: Rust change working, memory model with honest range, installer on clean machine. Mobile: loads exam deck, runs real review session on shared engine. |
| **Friday** | AI added and evaluated. Phone syncs two-way with desktop. Offline review + sync working. Phone shows three scores with ranges. AI beats a simpler baseline method. |
| **Sunday** | Prove everything. Ship installable builds for both platforms. Calibration charts, ablation test results, packaged installers, demo video (3–5 min). Due 10:59 PM CT. |

---

## Key Technical Challenges

### 7a: The Rust Change
See "Required Rust Change" above. This is 20% of the grade and a hard ceiling constraint (no real Rust change = 50% max).

### 7b: Sync Test
Review 10 cards on phone while offline. Review 10 *different* cards on desktop. Reconnect. Show all 20 land correctly — none lost, none double-counted. Then review the *same* card on both devices offline, sync, and demonstrate the conflict rule picks a clear, correct winner. Document what that rule is.

### 7c: Coverage Map
List every topic on the official GRE Math Subject Test outline. Mark which ones the deck covers. Show coverage percentage on the dashboard. App must refuse to give a readiness score if coverage is below the stated threshold.

### 7d: Paraphrase Test
Take 30 cards. Write 2 exam-style questions per card that test the same concept in new words. Compare student recall on the original card vs. accuracy on reworded questions. If the two numbers are basically the same, the performance model is just copying the memory model — the bridge hasn't been built. Report this gap honestly.

### 7e: Leakage Check
Script that scans training data and flags any test item (or near-copy) that slipped into training. A model that trained on its own test items is automatically zeroed.

### 7f: AI Card Quality Check
Build a gold set of 50 known-correct Q&A pairs. Generate 50 AI cards from one real source. Report: how many were correct and useful / wrong (wrong facts are worse than no card) / correct but bad pedagogy. Set a passing cutoff *before* looking at results.

### 7g: Crash & Offline Tests
Kill each app mid-review 20 times. Show zero corrupted collections. Pull the network: AI features turn off cleanly, both apps keep working and still show a score.

### 7h: One-Command Benchmark
`make bench` loads the 50,000-card deck and prints p50/p95/worst-case for: button acknowledgement, next card after grading, dashboard first load, dashboard refresh, sync completion.

---

## Study Feature Test (Ablation Requirement)

Pick one learning-science-based study feature (example: interleaving). State the hypothesis in one sentence *before* running the test. Build three versions:
1. Full app (feature on)
2. App with only that feature turned off (ablation)
3. Plain, unmodified Anki (baseline)

Compare all three on the same learners, same questions, same study time. Report results honestly — including null results. "Interleaving made no difference here" scores well. "Our app feels better" scores nothing.

---

## Score Model Strategy

You won't have longitudinal data in a week. Grade the bridge steps instead:
- **Step 1** (required): Memory model is calibrated — when it says 80%, recall is ~80%. Prove on held-back reviews.
- **Step 2** (required): Predict held-back exam-style question performance using topic mastery, question difficulty, timing, and coverage.
- **Step 3** (required): Convert question performance into a GRE scale score with a documented method and range.
- **Step 4** (bonus): Validate against real students with both study history and practice test scores.

Saying "we calibrated memory but don't yet have data to prove the projected score is right" scores higher than a polished score you can't back up.

---

## Grading Weights and Hard Limits

| Area | Weight |
|---|---|
| Rust change and how well it fits Anki | 20% |
| Score accuracy and honest uncertainty | 20% |
| Study feature built on learning science | 15% |
| AI checking and safety | 15% |
| Fair tests others can re-run | 12% |
| Desktop + phone sharing one engine, with working sync | 10% |
| Useful product and clean UX (both apps) | 8% |

**Hard ceilings:**
- No real Rust change → 50% max
- No phone companion sharing engine and syncing → 70% max
- No re-runnable test setup → 60% max
- No held-out testing → 60% max
- Made-up readiness numbers → automatic fail
- Either app doesn't run on a clean device → 50% max
- Leaked test data → that score is zero
- AI claims with no traceable source → AI section is zero

---

## Deliverables (Due Sunday 10:59 PM CT)

1. **GitHub repo**: public AGPL-3.0-or-later fork, exam stated up front, build instructions for both apps, architecture overview, Rust change note, files touched
2. **Demo video (3–5 min)**: review session, Rust change in action, card syncing phone→desktop, three scores with ranges, AI features, test results
3. **Model descriptions**: one page each for memory, performance, and readiness models (including the give-up rule)
4. **Brainlift**: as per Patrick's class outline

---

## Pedagogical Research Thread

In parallel, there's an active research question being explored: **can olympiad-style problems be used to effectively prepare students for the GRE Math Subject Test?** This is being treated as an open empirical question (not a premise), structured around five research dimensions:

1. **Construct comparison** — what each assessment actually measures (GRE: breadth, calculus-heavy, timed; olympiad: deep creative reasoning, proof construction)
2. **Transfer evidence** — what learning-science literature says about near vs. far transfer between olympiad training and standardized content exams
3. **Mechanisms of benefit** — if olympiad problems help, through what specific channels (fluency, comfort with novelty, speed under pressure)?
4. **Risks and opportunity cost** — where olympiad prep is inefficient (over-difficult problems, breadth neglect, pacing mismatch)
5. **Practical synthesis** — how to sequence olympiad problems alongside conventional GRE Math prep

A Cursor orchestrator agent prompt has been drafted for this research track, structured as: frame → write sub-agent prompts → dispatch and collect → critique → iterate → synthesize, with strict source rules (peer-reviewed > institutional > named experts > credible practitioner writing).

---

## Key Constraints Summary for Cursor

- Exam: **GRE Mathematics Subject Test** (66 questions, 2h50m, 200–990 scale, 90th percentile ≈ 57–58/66 correct)
- Engine: **Anki's Rust backend** — must fork and modify the actual Rust code, not just Python UI
- License: **AGPL-3.0-or-later** with credit to Anki (some parts BSD-3-Clause)
- Scores: **three separate** (memory / performance / readiness) — never blended, always with ranges
- Honesty: the app **must refuse to score** when it lacks sufficient data
- Platform: desktop installer + phone build (signed APK or iOS TestFlight/sideload), both running the same Rust engine
- Timeline: Wednesday → Friday → Sunday 10:59 PM CT
