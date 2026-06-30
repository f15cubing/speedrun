# Content Generation + Faithful Timed UI — Design Spec

> Formalizes the **content-generation pipeline** (two lanes: templated-computational + human-verified
> conceptual), the **MCQ note type / data model** that drives Performance, **SymPy-templated distractor
> generation**, the **FSRS-cooperative interleaving algorithm**, and a **faithful timed exam-pressure UI**
> with pace-preserving short sections. Companion to `docs/PRD.md` (§5/§7b/§8/§8a/§9/§12, Appendix A/B/C)
> and `docs/execution-plan.md` (Thu MCQ + interleaving instrumentation; Fri timed mode). Builds on the
> already-merged `pipeline/` (PR #1). Dated 2026-06-30.

## Status at time of writing

The Tuesday data foundation is merged: the seeded SymPy generator + `topic::*` tagging + coverage gate
(`pipeline/`, PR #1) and the MIT-OCW gold-set store (`eval/goldset/`, PR #2). This spec extends that
foundation into the study-surface progression (PRD §8a: flashcards → MCQ → timed) and pins the
generation machinery. **No AI before Friday** — everything here is templated or human-authored.

## Decisions (locked with owner, 2026-06-30)

- **"Infinite" generation = build-time scaled** (not runtime). Templates are the authoring surface; one
  template → N deterministic cards baked into the `.apkg` at build. "Infinite" is the seed × parameter
  space, mined by raising `count` or changing `--seed`. Preserves re-runnability (PRD §11).
- **Conceptual verification = enforced status-field gate.** Each conceptual record carries
  `status: draft|verified` + attribution; the build emits only `verified` cards and hard-fails on any
  `draft`/unattributed card. Same gate governs Friday's AI drafts.
- **MCQ distractors = SymPy-templated, auto-generated** for computational items via named common-error
  transforms (deterministic, provably ≠ key); **human-authored** for conceptual items.
- **Timed UI = desktop-first**, faithful to the official computer-delivered GRE Subject Test interface.
- **Short timed sections = pace-preserving.** Shorter sessions keep the exact official per-item pace
  (~2.58 min/item) with fewer items, so they stay high-stakes (construct = speededness).
- **Interleaving = FSRS-cooperative constrained re-sort** over the due queue; never a competing scheduler;
  toggleable for the D5 ablation.

## Global constraints

- **No AI before Friday** — templated + human-authored only.
- **One engine change only** — MCQ, timed mode, and interleaving are content/UX layers *above* the engine
  (note types, templates, presentation-order re-sort, timers). They add **no** second Rust change and keep
  the locked D1 ceiling (PRD §5) intact.
- **Two corpora stay firewalled** (PRD §12) — the **study deck** (review / Memory / MCQ practice) and the
  **authored eval bank** (P0–P3; Performance/Readiness/paraphrase/ablation/**timed forms**) never mix.
  The timed simulator draws only from the eval bank.
- **Taxonomy frozen** — every card/item carries exactly one `topic::<bucket>::<leaf>` leaf tag
  (PRD Appendix A).
- **Re-runnable** — pinned deps, fixed seed, one documented command, deterministic output.

---

## 1. Content architecture (two lanes → format layer → two corpora)

```
Lane A: TEMPLATED (computational)          Lane B: CONCEPTUAL (human-verified)
  template = params + SymPy answer            authored YAML record + status gate
  + named distractor-rules                    status: draft|verified (+ verified_by/on, source)
  answer & distractors correct-by-SymPy       build HARD-FAILS on any draft/unattributed
            │                                          │
            └────────────────────┬──────────────────────┘
                                 ▼
                       FORMAT LAYER (per item)
              flashcard  ───────►  drives MEMORY (FSRS recall)     [exists]
              MCQ (5 opts + key) ►  drives PERFORMANCE (§7b)       [new note type, §8a]
                                 │
            ┌────────────────────┴────────────────────┐
            ▼                                          ▼
     STUDY DECK corpus                          AUTHORED EVAL BANK corpus
     (daily review; FSRS; MCQ practice)         (P0–P3; leakage-isolated)
            │                                          ▼
            │                                  TIMED EXAM SIMULATOR
            └─ coverage gate (≥9 leaves,       (blueprint-matched forms,
               ≥50% calc)                       full + short presets)
```

Both lanes feed both corpora through one format layer. The firewall is enforced by partition tags
(`eval::p0..p3` mark eval items) + the leakage pipeline (PRD §11).

---

## 2. Lane A — templated computational generation

### 2.1 Template structure

Promote today's implicit generators (`pipeline/generate_deck.py`) to a first-class **template** object.
Each template declares:

- `leaf_tag` — the single taxonomy leaf it serves.
- `params` — parameter ranges / draws (integers, polynomials, matrices, …) sampled from a deterministic
  leaf-local RNG derived from `(seed, leaf_tag, template_id)`.
- `build(params) -> (stem, correct)` — the SymPy construction. SymPy builds **both** the problem and the
  answer, so the back is **correct by construction** (no hand-typed answers, no model calls).
- `distractor_rules` — an ordered list of named common-error transforms (see §4) used only when the item
  is rendered as MCQ.

### 2.2 "Infinite" via build-time scale

- The card set for a leaf is `count` distinct draws from the template's parameter space, de-duplicated by
  stem (today's `GENERATED_COUNTS` pattern, generalized). The parameter space is effectively unbounded;
  `count` and `--seed` choose a deterministic, byte-stable slice.
- Raising `count` or adding templates per leaf increases variety without any runtime generation. This is
  what "templates generate infinite questions" means operationally while staying re-runnable.

### 2.3 Output

`{ "front", "back", "leaf_tag", "format": "flashcard"|"mcq", "options"?, "correct"?, "distractor_meta"? }`
— flashcards as today; MCQ adds the option set + key.

---

## 3. Lane B — conceptual cards with an enforced verification gate

### 3.1 Record schema (extends `conceptual_cards.yaml`)

```yaml
- leaf_tag: "topic::algebra::abstract"
  format: flashcard            # or: mcq
  front: "..."
  back: "..."                  # flashcard
  options: ["...", "...", "...", "...", "..."]   # mcq only
  correct_index: 0             # mcq only
  explanation: "..."           # mcq only
  status: verified             # draft | verified   <-- the gate
  verified_by: "fc"            # required when status: verified
  verified_on: "2026-06-30"    # required when status: verified
  source: "original (Lagrange's theorem, standard)"   # required, non-empty
  gen: human                   # human | ai
```

### 3.2 The gate (mechanically enforced)

- The build (`build_deck.py`) and validator (`coverage_report.py` / a dedicated check) **emit only
  `status: verified` records** and **hard-fail (non-zero exit)** if any record is `draft`, or is
  `verified` but missing `verified_by`/`verified_on`/`source`.
- This is the literal "a human must verify before sending to production" requirement, enforced by the
  pipeline rather than convention.

### 3.3 Forward-compatibility with Friday's AI (PRD §9)

AI-drafted conceptual cards land in the **same** YAML pipeline as `status: draft` + `gen: ai`. The only
path to `verified` is human adjudication. No separate machinery is built later; §9's "mandatory human
adjudication for conceptual cards" is exactly this gate.

---

## 4. MCQ note type, data model & distractor generation

### 4.1 Note type "GRE MCQ" (the §8a content/data-model change)

- **Fields:** `Question`, `OptionA`, `OptionB`, `OptionC`, `OptionD`, `OptionE`, `CorrectOption` (A–E),
  `Explanation`, `LeafTag`.
- **Card template:** renders the stem + 5 single-select options; on answer, reveals correct option +
  explanation and grades into the existing **Again/Hard/Good/Easy** path.
- **Engine view:** it is just a note — same due queue, same FSRS scheduling, same review loop, same
  `topic::*` tag. **No second Rust change**; the D1 ceiling holds.
- This is the surface the **Performance** model scores (PRD §7b) — real in-app five-option answers, the
  GRE's native format, not a bolt-on quiz.

### 4.2 Distractor generation (computational lane)

Four distractors per MCQ, produced by **named common-error transforms** evaluated by SymPy on the same
instance, e.g.:

| Rule | Error modeled |
|---|---|
| `dropped_constant` | omit the `+ C` / constant term |
| `sign_flip` | flip a sign (e.g. derivative/integral sign error) |
| `forgot_chain_factor` | omit the inner-derivative / chain-rule factor |
| `off_by_power` | exponent ±1 (power-rule misfire) |
| `swapped_op` | differentiate where integration was asked (or vice versa) |

Generation rules:
- Each transform yields a candidate; keep the first four that are **defined, distinct from each other, and
  ≠ the key** (SymPy equality check). De-duplicate; if a template can't yield 4 valid distractors for an
  instance, that instance is **skipped** (re-drawn) — never padded with a wrong-but-equal option.
- Distractors are **deterministic** for a given seed (same re-runnability guarantee as the keys).

### 4.3 Distractors (conceptual lane)

Human-authored in the verified YAML (`options` + `correct_index`). No error-transform rules for prose —
the verifier writes plausible wrong statements and is accountable via the `status` gate.

---

## 5. Timed exam-pressure UI (desktop-first, faithful to the official exam)

### 5.1 Official interface elements we mirror

Sourced from ETS (computer-delivered GRE Subject Test, Sept-2023+; "mark and review" docs) and the shared
ETS computer-test conventions:

- **Persistent countdown** timer (whole-session; the Math test has **no separately timed sections**).
- **Item counter** "Question N of M".
- **Mark** (flag a question to revisit).
- **Review screen** — full list/grid of all items showing **answered / unanswered / marked**; click any
  number to jump directly.
- **Back / Next** free navigation (move even without answering; change answers any time while the clock
  runs).
- **Help** and **Exit**.
- **Five single-select options (A–E)**, **rights-only** scoring, **no on-screen calculator** (the Calc
  button is GRE-General-Quant only — deliberately absent here).
- **No pause**; **auto-submit at 0:00**.

### 5.2 Pace-preserving short sections

The official pace is `170 min / 66 ≈ 2.58 min/item`. Short sections keep that exact pace with fewer items,
so they remain genuinely high-stakes (the construct is speededness, not raw duration):

| Preset | Items | Time | Pace |
|---|---|---|---|
| Full-length (canonical) | 66 | 2h50m | 2.58 min/item |
| Half | 33 | ~1h25m | 2.58 min/item |
| Third | 22 | ~57m | 2.58 min/item |
| Mini | 11 | ~28m | 2.58 min/item |

Every preset is **blueprint-matched** (≈50% calculus / ≈25% algebra / ≈25% additional), drawn from the
**authored eval bank** (leakage-isolated), and uses the **full official UI** above. The full-length form
stays the headline deliverable; short sections are the realistic daily variant.

### 5.3 Behavior & integration

- On submit → rights-only score + **per-leaf breakdown**, fed to Performance/Readiness (never blended,
  PRD §7) and logged to the prospective calibration log.
- **Gating (PRD §8a):** mastery-gated; surfaced on the Memory-high / timed-Performance-low gap; ships
  **last**, after interleaving + the ordering algorithm.
- **Platform:** desktop (Qt/TS) first; Android only if time allows (out of scope here).

---

## 6. Interleaving algorithm (FSRS-cooperative)

### 6.1 Principle

Interleaving **never touches FSRS scheduling** (due/interval/ease/queue/reps/lapses). FSRS decides *which*
cards are due and their priority; interleaving only re-sequences the **presentation order** of that
already-gathered queue. It is a **constrained re-sort layered on FSRS**, not a competing scheduler — this
is what "combines well with Anki's algorithm" means.

### 6.2 The algorithm

1. **Input:** FSRS's due queue, in FSRS priority order (the preserved baseline).
2. **Confusable clusters** over the taxonomy (interleaving pays off most for *confusable* types — PRD
   Appendix B, H2), e.g. `{differential_single, integral_single}`, `{differential_multi, integral_multi}`,
   single↔multi pairs. Dispersion is by **cluster**, not just leaf.
3. **Constrained dispersion re-sort** (greedy, frequency-aware): at each step, emit the
   **highest-FSRS-priority** card whose cluster differs from the last *K* shown, subject to a
   **displacement bound W** — no card may drift more than a window from its FSRS position. The bound keeps
   it cooperative: urgent cards stay near the front; interleaving never starves FSRS priority.
4. **Fallback:** when the queue is too small or homogeneous to satisfy the constraints, degrade gracefully
   to plain FSRS order (don't loop/stall).

### 6.3 Invariants & metrics (tested)

- **FSRS-invariance:** shown multiset == FSRS due set (nothing added/dropped); scheduling fields
  **byte-unchanged** after a session.
- **Reported metrics** (so "pretty good" is provable): **adjacency dispersion** (% of consecutive pairs
  from different clusters) and **FSRS displacement** (mean/max position shift).
- **Ablation lever (D5):** a single toggle switches interleaved ↔ blocked; the blocked arm and plain-Anki
  baseline are the other two arms (PRD §8, Appendix B).

### 6.4 Home

Default: Python/presentation layer (safe, FSRS-invariant). Stretch (PRD D1/§8): the same ordering as a
flag-gated, **non-persistent** in-memory re-sort inside `QueueBuilder` (never writes `due`).

---

## 7. File layout (proposed)

New / changed (pure Python + Anki note-type assets; no `rslib/` changes):

- `pipeline/templates/` — first-class templates (one module per leaf or a registry) with `params`,
  `build`, and `distractor_rules`. Refactors today's `generate_deck.py` generators into this shape.
- `pipeline/distractors.py` — the named common-error transforms + the 4-distractor selector (dedupe, ≠ key).
- `pipeline/conceptual_cards.yaml` — extended with `status`/`verified_by`/`verified_on`/`source`/`format`
  (+ `options`/`correct_index`/`explanation` for MCQ).
- `pipeline/build_deck.py` / `pipeline/coverage_report.py` — emit only `verified` conceptual cards; **hard
  fail** on `draft`/unattributed; build the **GRE MCQ** note type alongside the flashcard note type.
- `pipeline/notetypes/` — the "GRE MCQ" note-type + card-template definitions (genanki model).
- `timed/` (desktop) — the exam-pressure simulator UI (countdown, Mark, Review screen, Back/Next, presets)
  + form assembler that pulls a blueprint-matched form from the eval bank. (Detailed home in `anki/ts/` /
  `anki/qt/aqt/` confirmed at implementation time.)
- `pipeline/interleave.py` — the constrained dispersion re-sort + cluster map + metrics.
- Module docs (`pipeline.md`, a new `timed.md`) + `docs/codebase/INDEX.md` rows, per `codebase-docs`.

---

## 8. Tests

- **Templated lane:** every generated card has exactly one valid leaf tag; deterministic (same seed →
  identical set); a sample of computational answers re-checked against SymPy ground truth (extends today's
  `test_recompute.py`).
- **Distractors:** for a sample of MCQ instances — exactly 4 distractors, all distinct, all ≠ key (SymPy
  equality); deterministic for a fixed seed.
- **Verification gate:** a `draft` record (or `verified` missing attribution) makes the build **exit
  non-zero**; only `verified` cards appear in the deck.
- **MCQ note type:** builds; renders 5 options; `CorrectOption` matches the key; grades into
  Again/Hard/Good/Easy (smoke).
- **Interleaving:** FSRS-invariance (multiset + byte-unchanged fields); adjacency-dispersion improves vs.
  blocked order on a fixture; displacement bound respected; graceful fallback on tiny/homogeneous queues;
  toggle flips order deterministically.
- **Timed UI:** pace math per preset (2.58 min/item); auto-submit at 0:00; rights-only scoring;
  blueprint-match (≈50/25/25) of an assembled form; Review-screen state transitions
  (answered/unanswered/marked).

## 9. Acceptance

- One documented command rebuilds the deck (flashcards + MCQ) deterministically with the coverage gate
  green and the verification gate enforced.
- MCQ note type imports into desktop Anki and reviews through the normal FSRS loop.
- Interleaving toggle produces a measurably more dispersed order with bounded FSRS displacement and a
  proven invariance test.
- Timed simulator runs a full-length and at least one short preset with the official UI elements, correct
  pace, and a per-leaf result feed.
- PRD updated (§7b/§8/§8a/§9/§12 + Appendix A); module docs + INDEX rows added; tests pass.

## 10. Out of scope (later)

- Runtime / truly-infinite generation (decided against for re-runnability).
- Android timed UI (desktop-first).
- The actual **AI** card generation (Friday, §9) — only the *gate* it flows through is built here.
- Authoring the full 66-item eval form / partitions (Thursday eval-bank task, PRD §12) — here we build the
  **machinery + schema**, not the final item content.

## 11. PRD changes made alongside this spec

- **§8** — interleaving algorithm (constrained, FSRS-cooperative, displacement-bounded; metrics).
- **§8a** — MCQ note-type field spec; pace-preserving short timed presets + UI-fidelity element list.
- **§12** — two-lane content generation; enforced conceptual verification gate; distractor generation.
- **§9** — AI conceptual drafts flow through the same status gate.
- **Appendix A** — format + verification-metadata conventions.
