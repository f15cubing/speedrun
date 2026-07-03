# Demo plan — Friday cut (record today)

> The **today-Friday** recording script: everything shipped through the compressed-Friday
> push — the Rust engine change, three scores **separated** on desktop *and* the read-only
> panel on the phone, self-hosted sync, the **AI card pipeline** (honest AI-off), and the
> quantitative + robustness proofs. Target **3–5 min**, live screen capture.
> State: `main @ 4b6a473` (v0.3.0); engine `f15cubing/anki@a7e8992`; Android `@c6d0250`.
>
> Companions: `docs/demo-plan.md` (fuller Sunday cut + Milestone-1 appendix),
> `docs/ai-run-howto.md` (the AI run, step by step), `docs/submission-checklist.md`.

The through-line stays the same: **one exam, two apps on one engine, a real engine
change, and honesty as a feature** — now with live Performance/Readiness plumbing and AI.

---

## Pre-flight (before you hit record)

- [ ] Desktop dev build running: `cd anki && ./run`; GRE deck imported (auto-imports on
      first run; else `python pipeline/build_deck.py --seed 42`).
- [ ] Do **a handful of reviews** so Memory shows a range (not the n=0 empty state).
- [ ] Open the desktop **GRE dashboard once** (Tools ▸ GRE readiness dashboard) so it
      writes the synced `gre_scorecard`.
- [ ] **Interactive MCQ deck loaded.** It now **ships bundled** (v0.3.0 / #40, `GRE_DECK_VERSION
      2026-07-03b`) — a **fresh profile auto-imports it**. But your already-running `./run` is an
      **existing** collection, and the note-type *template* does **not** auto-refresh on an existing
      install (documented limitation), so re-import once to get the interactive template on screen:
      `python pipeline/build_deck.py --seed 42` → **File ▸ Import** `pipeline/dist/gre-study-deck.apkg`
      (stable GUIDs → updates in place, no dupes). Confirm on an MCQ card that the options are
      **tappable buttons** (not plain `A. … B. …` text). *(Or demo on a fresh profile, where it's automatic.)*
- [ ] Emulator `anki_test` booted with our debug APK (our `librsdroid.so`); GRE deck present.
- [ ] Sync ready: `make sync-server` (port 8080, account `greuser`).
- [ ] Two terminals sized for readable text: one for the mastery tests, one for the AI run
      (`docs/ai-run-howto.md`).
- [ ] `make ai-gate` / `make ai-baseline` dry-run once off-camera so they're warm + you
      know the numbers.

---

## Shooting script

### 0:00 — Cold open (~10s)
**On screen:** desktop app, GRE deck.
**Say:** "A fork of Anki turned into one thing — a GRE Math Subject Test tutor that
measures memory, performance, and readiness *separately*, and refuses to fake a number
it can't back up."

### 0:10 — Deck + taxonomy (~20s)
**On screen:** Browser; expand `topic::calculus::*` / `algebra::*` / `additional::*`; click
a card → one leaf tag.
**Say:** "Every card maps to exactly one ETS leaf topic. That tag tree is the substrate
the mastery query, the coverage map, and the scores all read."

### 0:30 — Desktop: the three scores (~55s)
**On screen:** Tools ▸ GRE readiness dashboard. Walk it: **Memory** range + caveat →
**Coverage map** (17 leaves, per-leaf range) → the **three separated slots**; pause on
**Readiness** showing the give-up state with its evidence panel (coverage %, reasons,
best-next topic).
**Say:** "Three scores, strictly separate — never blended. Memory is a calibrated *range*,
not a point. And Readiness? It shows a projected 200–990 *only* when it has the evidence;
otherwise it abstains and shows the panel — reasons, coverage, the single best next topic.
A confident readiness number on thin data is an automatic fail; abstaining honestly is the
feature."

### 1:25 — MCQ study surface (the format Performance scores) (~35s)

> **Get an interactive MCQ card on screen (do this off-camera first).** The interactive template
> now **ships in the bundled deck** (v0.3.0 / #40) — a **fresh profile auto-imports it**. On an
> **existing** collection (your already-running `./run`) the template won't auto-refresh (documented
> limitation), so re-import once:
> 1. Rebuild the deck: `python pipeline/build_deck.py --seed 42` (writes
>    `pipeline/dist/gre-study-deck.apkg`).
> 2. In the desktop app: **File ▸ Import** → pick `pipeline/dist/gre-study-deck.apkg` → Import.
>    (Stable GUIDs update in place — no duplicates.)
> 3. Line up an MCQ card to review: open the **Browse** window, click the **`GRE Math MCQ
>    (leaf-tagged)`** note type (or the `note:"GRE Math MCQ*"` search) to confirm cards exist,
>    then **Custom Study ▸ study by card state/tag** (or just study the deck) until an MCQ card
>    comes up. Sanity check: the options are **tappable buttons**, not plain `A. … B. …` text.
>
> On the **phone**: a fresh AnkiDroid install auto-imports the interactive MCQ too (verified on the
> emulator: 5,408 cards, MathJax renders) — same existing-install caveat applies.

**On screen — do these steps live (~35s):**
1. In the reviewer, land on a **GRE Math MCQ** card — five options rendered as **buttons** A–E,
   question typeset in LaTeX.
2. **Tap a wrong option** → it turns **red**; the **correct** option turns **green**; the
   **explanation** reveals below (MathJax typesets it).
3. (Optional) show a second card and **tap the correct option first** → green, no red.
4. Press a normal **Good / Again** ease button to grade it — same FSRS flow as any card.

**Say:** "The GRE is five-option multiple choice, so we ship an **interactive MCQ card
type** — five tappable options, instant right/wrong feedback, worked explanation, math
typeset. Distractors are generated by a computer-algebra system as *named* common errors —
a sign flip, a dropped `+C` — not random noise. It's the exact format the **Performance**
score reads, and it grades on the **same FSRS loop** as every other card. Because it's a
card template, the same interactive card renders on the phone too — no separate engine code."

> Timing: this MCQ beat pushes the full cut toward ~5 min. If you're running long, tighten to
> a single wrong-then-right tap (~15s), or cut it (it's the **trimmable** segment).
> Honesty note if asked: the interactive template reaches **fresh installs** now; refreshing it
> on an *existing* install is a documented follow-up (`docs/STATUS.md` — MCQ re-bundle limitation).

### 2:00 — Same three scores on the phone, read-only (~35s)
**On screen:** emulator → DeckPicker ▸ overflow ▸ **"GRE readiness"** → the read-only
3-score panel (Memory / Performance / Readiness, each with its range/gated state + the
"computed on desktop, last updated…" footer).
**Say:** "The phone doesn't recompute anything — the desktop is authoritative, it writes
the score card into the collection, and it **syncs** to the phone, which renders it
read-only. Same three scores, same honesty rules, no scoring math on the device."

### 2:35 — The Rust change under the hood (~55s)
**On screen:** split view of `anki/rslib/src/stats/mastery.rs` + the `stats.proto` diff;
then run the tests live to green (the 3 Rust unit tests incl. `mastery_query_is_read_only`
+ the Python integration test).
**Say:** "The numbers come from a **read-only query inside Anki's Rust engine**, using the
same FSRS math the scheduler uses, in one database pass. It *provably* never writes, never
touches undo, never corrupts the collection — that's this test. It's the hardest 20% of
the grade, and because it lives in the shared engine it ships to the phone for free."

### 3:30 — Sync + durability proofs (~35s)
**On screen:** `make sync-server`; then run `make crash-7g` (or show
`docs/evidence/robustness/`) and `make sync-7b`.
**Say:** "Sync runs on *our* engine, self-hosted. We kill the app mid-review twenty times
— twenty out of twenty reopen clean, zero corruption. Ten offline reviews on each side all
land on both peers, on a documented conflict rule. This is the durability ceiling, proven."

### 4:05 — The AI card pipeline (~50s)
**On screen:** a terminal — run `make ai-gate` then `make ai-baseline` (see
`docs/ai-run-howto.md`). Let the reports print.
**Say:** "Our AI card generator. Every fact must carry a **verbatim source quote** or it's
dropped; every computational answer is **re-derived by a CAS** — a wrong answer can't
publish; conceptual cards go to human review, never auto-trusted. It clears a gate whose
cutoffs were locked before scoring — fact-precision ≥ 0.98, useful-yield ≥ 0.60 — and it
beats a naive baseline at McNemar p ≈ 6-in-a-million while shipping zero wrong facts. And
it's **AI-off** — no live model here — so these numbers validate the *machinery*, not a
model. That's deliberate honesty."

### 4:55 — Honest close (~20s)
**On screen:** back to the three dashboard slots.
**Say:** "Everything shown is merged and reproducible from a single command each. What's
*not* here — a live model run, the interleaving ablation — is documented as deferred, not
faked. One exam, two apps, one real engine change, and honesty as a feature."

---

## Runnable proofs referenced (each one command)

| Segment | Command |
|---|---|
| Deck (incl. interactive MCQ cards) | `python pipeline/build_deck.py --seed 42` |
| Desktop app | `cd anki && ./run` |
| Mastery tests | Rust unit tests in `anki/rslib/src/stats/mastery.rs`; `anki/pylib/tests/test_mastery.py` |
| Bench (50k) | `make bench` (p50 650 / p95 667 / worst 709 ms) |
| Calibration + paraphrase | `make proofs` (Brier 0.219 / ECE 0.061; paraphrase gap 0.006) |
| Crash-safety 7g | `make crash-7g` (20/20 clean) |
| Two-way sync 7b | `make sync-server-7b` then `make sync-7b` |
| AI pipeline + gate | `make ai-gate` (see `docs/ai-run-howto.md`) |
| Beat-baseline + AI-off | `make ai-baseline` |
| Sync | `make sync-server`, `make sync-smoke` |
| B-roll | `docs/evidence/{w3-android,w4-sync,task7-android,robustness,proofs}/` |

## Honesty framing (say it, don't hide it)
- **AI-off** — the pipeline runs on a deterministic stub; numbers validate the machinery,
  not a live model. A live run needs the seam wired (`docs/ai-run-howto.md` appendix).
- **Scoring proofs are simulated** machinery-checks (validity unestablished at n≈1).
- **Readiness** is always a range + evidence panel + give-up rule; a bare number is an
  auto-fail — the empty/gated state is the feature.
- **Deferred (documented, not faked):** live-model run, interleaving ablation, signed-APK
  clean-device recording (see `docs/STATUS.md` § Sat/Sun buffer + `docs/submission-checklist.md`).
