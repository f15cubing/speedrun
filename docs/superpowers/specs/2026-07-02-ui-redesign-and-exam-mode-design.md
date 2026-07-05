# UI Redesign + Faithful Exam Mode — Design & Build Plan

> Two linked pieces of work, both **fast-lane by risk** (Qt/TS presentation only; **no** `rslib` /
> `.proto` / `pylib` FFI / scheduler / undo / store contact — no second engine change):
>
> 1. **Dashboard redesign** — give the GRE readiness dashboard (`anki/ts/routes/gre-dashboard/`) a
>    distinctive, intentional visual identity instead of the current default-Anki look.
> 2. **Exam Mode** — a testing surface that is **functionally identical to the official
>    computer-delivered GRE Mathematics Subject Test** (66 items / 2h50m / rights-only / mark & review /
>    no pause / no calculator), extending the timed-UI decisions already locked in
>    `2026-06-30-content-generation-and-timed-ui-design.md` §5.
>
> Companion to `docs/PRD.md` (§7 three scores, §8a study progression, D2 give-up rule), the two design
> specs in this folder (W2 dashboard, content-generation+timed-UI), and the exam-shell research verdict
> `research/responses/15-testing-ui-design-ablation-decision.md` (COMPLEMENT — opt-in Exam Mode gating
> Readiness). Dated 2026-07-02. Uses the installed `frontend-design` skill (`.agents/skills/`).

---

## 0. Why now / what exists

- The dashboard **works** (PR #9) but looks templated: system fonts, `1px solid #ccc` boxes, a blue
  `--accent` border, dashed give-up boxes. It reads as "unstyled Anki dialog," not as a calibrated
  GRE instrument. Files today: `+page.svelte`, `MemoryPanel.svelte`, `CoverageMap.svelte`,
  `ScoreSlot.svelte` (all four are plain).
- **Exam Mode does not exist yet.** MCQ *content* exists (`pipeline/generate_mcq.py`,
  `pipeline/tests/test_mcq_*`), but there is no timed exam-shell UI. The timed-UI **decisions** are
  locked in the content-gen spec §5 (official-interface element list, pace-preserving presets); this
  plan turns those decisions into a concrete build.

**Hard-ceiling check (both pieces):** read-only (dashboard consumes the existing W1 RPC; Exam Mode
reads eval-bank items and writes only its own local session/result records — **never** `OpChanges`,
never the scheduler/undo/store); never blend the three scores; never show a Readiness number without
the full evidence panel; Exam Mode draws **only** from the firewalled authored eval bank (never ETS
items, never the study deck). These are the same ceilings enforced by the shipping-changes gate.

---

## 0.5 Coordination with in-flight agents (READ FIRST — collision map)

Seven agent worktrees are active (`git worktree list`). This plan is written to **not collide** with
them. Snapshot as of 2026-07-02:

| Agent branch | Owns (files/dirs) | Overlap with us | Rule |
|---|---|---|---|
| **`agent/thu-scoring-layer`** | new `scoring/` pkg **+ extends the dashboard adapter `anki/qt/aqt/gre/` and renders live Performance/Readiness slots + evidence panel**; writes synced `col.conf` `gre_scorecard`; AnkiDroid 3-score panel | **HIGH — same dashboard.** It fills the Performance/Readiness slot *content*; we restyle the slot *shells*. It edits `dashboard_data.py`; we said "no view-model change" (keep that promise). | Split by **content vs. chrome** (see A6). Redesign ships the **shared design system**; scoring renders its ranges *through* our `CalibrationStrip`. Coordinate merge order. |
| **`agent/eval-bank`** (merged as **PR #17**, on `main`) | `eval/bank/` — `loader.py` (`load_eval_items`, `summarize`, `assert_firewall`), `items.yaml` (MCQ items: `difficulty` 1–5, `partition` p0–p3), `generate_eval.py` | **Dependency, not collision.** Exam Mode *reads* it. | **Consume, never modify.** `from eval.bank.loader import load_eval_items`. |
| **`agent/pipeline-mcq-content`** | `eval/goldset/` + MCQ content in `pipeline/` (older branch) | none direct (Exam Mode renders MCQ items already in the eval bank) | leave alone |
| **`agent/deck-scale`, `agent/deck-auto-incorporation`** | `pipeline/` (generators, `generate_deck.py`, `generate_mcq.py`, scale tests) | none — we add **no** `pipeline/` code | keep Exam Mode code out of `pipeline/` |
| **`agent/w3-android-build`, `agent/w4-sync-foundation`** | Android submodules, `sync/`; **running** emulator + rsdroid/AnkiDroid builds + sync server on **:8080** | none code-wise; **process** overlap | don't kill :8080, the emulator, or the `./run` app (terminal 1) |

**No agent has bumped the `anki` submodule pin yet** — so the fork UI is currently uncontested, but
**both this redesign and `agent/thu-scoring-layer` will bump it.** Sequence the bumps (see §Sequencing).

### The one real conflict: the dashboard is shared with `agent/thu-scoring-layer`

Both touch `anki/ts/routes/gre-dashboard/*` and `anki/qt/aqt/gre/`. Resolution = **separate concerns +
a shared component contract**, not two agents editing the same lines:

- **Redesign owns** *chrome*: `tokens.css`, `CalibrationStrip.svelte`, layout/`+page.svelte`,
  `MemoryPanel.svelte`, `CoverageMap.svelte`, and the **visual** styling of `ScoreSlot.svelte`.
- **Scoring owns** *content/semantics*: `dashboard_data.py` (adds Performance/Readiness numbers +
  interval-width reason), the score card, and **what** the Performance/Readiness slots say.
- **The seam:** `CalibrationStrip` is the shared primitive. When scoring turns Performance from
  "not available" into a live range, it renders that range **through `CalibrationStrip`** (same for the
  Readiness evidence panel). Redesign ships the strip + tokens; scoring imports them. Neither rewrites
  the other's file.

---

## PART A — DASHBOARD REDESIGN

### A1. Design direction (frontend-design pass 1: tokens)

**Subject, audience, job.** Subject: a GRE **Mathematics** Subject Test tutor whose whole thesis is
*honesty* — it shows **ranges, not fabricated point numbers**, and abstains when it can't back a
score. Audience: math majors/grads doing high-stakes, speeded prep. The page's single job: let a
student see, at a glance, *what they can reliably recall, how much of the exam that covers, and the
one honest next move* — with the uncertainty always visible.

**The idea.** Uncertainty is not a caveat here — it's the product. So the **interval itself becomes
the visual language**: every metric on the page is drawn as a *calibration strip* (a 0–100% axis with
a shaded 95% band and a point tick), never as a bare number. That single motif carries the brand at
three scales (exam headline → 3 buckets → 17 leaves) and makes the give-up states feel like part of
the same honest system rather than error boxes. Aesthetic reference: precision measuring instruments
and CAS/terminal output, not a marketing dashboard.

**Color (4–6 named tokens; layered over Anki's theme vars so night mode still works).**

| Token | Light | Dark | Role |
|---|---|---|---|
| `--gre-ink` | `#16202A` | `#E7EEF4` | primary text (deep blue-slate, not pure black) |
| `--gre-surface` | `#FBFCFD` | `#1B2530` | card surface, one step off Anki `--canvas` |
| `--gre-hairline` | `#D3DCE4` | `#33414F` | axis lines, dividers, grid |
| `--gre-signal` | `#0E7C86` | `#2BB3C0` | **the accent** — point-estimate tick + primary action (calibrated teal; instrument, not brand-blue) |
| `--gre-band` | `rgba(14,124,134,.16)` | `rgba(43,179,192,.22)` | the 95% confidence-band fill |
| `--gre-abstain` | `#B26B00` | `#E0A44A` | the give-up / "insufficient evidence" state — **amber, not red** (abstention is a feature, not an error) |

All six are defined as CSS custom properties with a light/dark pair, gated on Anki's existing
`.night-mode` root class so we inherit its theme switch instead of fighting it. We spend boldness in
exactly one place (the teal signal on the interval tick); everything else stays quiet.

**Type (roles — the IBM Plex scientific superfamily + one display).**

- **Data / numerals — `IBM Plex Mono`** (tabular figures). *Every* number, interval, and percentage.
  Tabular mono makes the CI bounds and n-counts line up in columns — the intervals read like an
  instrument readout, and it's on-brand for math (CAS, terminals, tables).
- **Body — `IBM Plex Sans`.** Microcopy, labels, reasons. Neutral, legible, scientific pedigree.
- **Display — `IBM Plex Sans` SemiBold, tightened tracking + an eyebrow in `Plex Mono` caps.** Score
  titles and section headers. (Kept in-family on purpose — restraint; the memorable element is the
  interval strip, not a loud display face.)
- **Fallback + delivery:** self-host the two Plex weights we use under `anki/ts/` (webview has no
  network guarantee); fall back to the platform mono/sans stack so it degrades cleanly.

**Signature element.** The **calibration strip** — one reusable Svelte component
(`CalibrationStrip.svelte`) rendering `{point, low, high, n}` on a 0–100% axis: hairline axis, teal
`--gre-band` shaded region for the CI, a single teal tick for the point, and a `Plex Mono` caption
`n=… · 95% CI …–…`. It appears everywhere a number would: the exam headline (large), each of the 3
buckets (medium, weight-labeled), each studied leaf (compact). When `n=0` it renders an *empty axis
with a dotted "not studied yet" rail* — so absence of evidence is drawn, not hidden. This is the one
thing the page is remembered by, and it literally *is* the honesty thesis.

### A2. Self-critique vs. generic defaults (frontend-design pass 2)

- Not the cream/serif/terracotta look, not the near-black/acid-green look, not the broadsheet-hairline
  look. The accent is an instrument teal chosen for "calibration," derived from the subject, not a
  default.
- The one real risk taken: **no bare numbers anywhere** — even the headline recall % is a strip, not
  a big number with a small label (the exact template answer the skill warns against). Justified
  because ranges-over-points is the product's core, hard-ceiling bet.
- Numbered markers (01/02/03) are **avoided** — the three scores are parallel, not a sequence, so they
  get equal-weight slots, not a numbered list.
- Motion: one restrained page-load reveal — strips animate their band/tick in from the point outward
  (~250ms, staggered), `prefers-reduced-motion` respected. No scattered hover effects.

### A3. Layout concept + wireframe

One column, max ~960px, three zones: **honest headline**, **the three separated slots**, **coverage
constellation**. Structure encodes the PRD's three-score separation (three equal slots, never a
blended total).

```
┌───────────────────────────────────────────────────────────┐
│  GRE · MATHEMATICS SUBJECT TEST            updated 2026-…   │  ← eyebrow (Plex Mono caps) + timestamp
│                                                             │
│  MEMORY                                                     │
│  You can reliably recall what you've studied:              │
│  ├──────────────[■■■■ 62% ■■■■]──────────┤  55–69%  n=140  │  ← headline CALIBRATION STRIP (signature)
│  aggregate-calibrated · not personalized                   │
│                                                             │
│  ┌───────── MEMORY / PERFORMANCE / READINESS ───────────┐  │  ← 3 equal slots, never blended
│  │ Memory (live)  │ Performance      │ Readiness         │  │
│  │ calculus  50%  │ Not available    │ ⚠ Insufficient    │  │
│  │  ├──[■ ]──┤    │ yet — arrives    │  evidence         │  │
│  │ algebra   25%  │ Thursday (MCQ    │  studied 41%      │  │
│  │  ├─[■]───┤     │ surface).        │  best next:       │  │
│  │ additional25%  │                  │  · series         │  │  ← amber, not red
│  │  ├[ ]────┤     │                  │  reasons: …       │  │
│  └────────────────┴──────────────────┴───────────────────┘ │
│                                                             │
│  COVERAGE  · deck 100% · studied 41%                        │
│   calculus      17-leaf grid, each cell a compact           │
│   ┌───┬───┬───┐ calibration strip; uncovered = dotted;      │
│   │▟  │▙  │·  │ studied = teal band; the single best-next   │
│   └───┴───┴───┘ leaf gets a subtle ring                     │
└───────────────────────────────────────────────────────────┘
```

### A4. Files touched (fast lane, in the fork)

| File | Change |
|---|---|
| `anki/ts/routes/gre-dashboard/CalibrationStrip.svelte` *(new)* | the signature interval component (`{point,low,high,n}`, `n=0` empty state) |
| `anki/ts/routes/gre-dashboard/tokens.css` *(new)* | the 6 color tokens (light/dark via `.night-mode`) + type roles + self-hosted Plex `@font-face` |
| `anki/ts/routes/gre-dashboard/+page.svelte` | restructure to the 3-zone layout; import tokens; page-load reveal |
| `anki/ts/routes/gre-dashboard/MemoryPanel.svelte` | headline + per-bucket now render `CalibrationStrip`; drop ad-hoc CSS |
| `anki/ts/routes/gre-dashboard/CoverageMap.svelte` | 17-leaf grid → compact strips; uncovered/studied/best-next states |
| `anki/ts/routes/gre-dashboard/ScoreSlot.svelte` | amber give-up styling; equal-weight slot; keep the `ALLOWED_STATES` guard (no fabricated numbers) |
| self-hosted Plex woff2 under `anki/ts/` | 2–3 weights only |
| `docs/codebase/qt.md`, `docs/STATUS.md` | note the redesign; bump submodule SHA in the same PR |

**No view-model change (deliberate, to stay off `agent/thu-scoring-layer`'s lines).**
`dashboard_data.py` already returns exactly `{point, low, high, reviewed}` per level — precisely the
strip's input — so the redesign is a pure presentation swap and does **not** edit `dashboard_data.py`.
That file is the scoring agent's to change (it adds Performance/Readiness numbers). We only touch `.svelte` + CSS + fonts.

### A6. Handoff contract with `agent/thu-scoring-layer`

The two dashboard workstreams meet at one component. Freeze this contract so they compose:

```ts
// CalibrationStrip.svelte — the shared primitive both agents use
props: {
  point: number | null;   // 0..1 (or scaled for readiness); null => empty "not yet" rail
  low:   number | null;
  high:  number | null;
  n?:    number;           // sample size caption
  scale?: "pct" | "raw";   // pct for memory/performance; raw for a 200–990 readiness band
  tone?: "signal" | "abstain";
}
```

- **Redesign delivers** `CalibrationStrip` + `tokens.css` and uses them for Memory/coverage/give-up.
- **Scoring consumes** them: Performance renders `strip(scale="pct")`; Readiness, when it clears the
  give-up gate, renders `strip(scale="raw", 200..990)`; when gated off it keeps the amber give-up slot
  (redesign's styling) with the evidence panel. **Scoring never restyles the strip; redesign never
  writes score numbers.**
- If merge order forces it, whichever agent lands second rebases onto the other's `.svelte`/`.py`
  files — the split (chrome vs. content) is line-disjoint by design, so rebases should be trivial.

### A5. Tests & acceptance (dashboard)

- **GUI smoke (required by PR #10):** build the deck, `./run` in a fork worktree, study a few cards,
  open Tools ▸ GRE readiness dashboard — confirm strips render at all three scales, night-mode
  toggles correctly, `n=0` shows the dotted "not studied" rail, and the fetch still emits **no**
  `OpChanges` (read-only preserved).
- **Component:** a Svelte/vitest render test for `CalibrationStrip` — point tick position, band
  extents, and the `n=0` empty state map correctly from props (guards against a strip ever implying
  more certainty than the data).
- **Quality floor:** responsive to mobile width, visible keyboard focus on the Tools action + any
  controls, `prefers-reduced-motion` honored.
- **Acceptance:** the dashboard is visually distinctive (the calibration-strip identity), still
  read-only, still enforces three-score separation and the give-up state with no fabricated numbers,
  and passes the existing dashboard tests unchanged.

---

## PART B — EXAM MODE (functionally identical to the GRE Math Subject Test)

### B1. Fidelity target (what "functionally identical" means)

Mirror the **official computer-delivered GRE Mathematics Subject Test** (ETS, Sept-2023+ format), per
the element list already locked in the content-gen spec §5.1 and the research verdict (SQ15). The
exam is a single **linear** form with free navigation — so we replicate:

| Official element | Our implementation |
|---|---|
| **66 items**, one screen at a time | item renderer, `Question N of 66` counter |
| **2h50m single global clock**, no separately timed sections | persistent countdown, top-right, `H:MM:SS` |
| **Five single-select options A–E** | radio group; exactly one selectable |
| **Rights-only scoring** (no penalty) | score = count correct; unanswered = wrong, no negative marking |
| **Mark / flag for review** | per-item flag toggle |
| **Back / Next free navigation**, change answers anytime | prev/next; answers editable until submit |
| **Review screen** — grid of all 66 showing answered / unanswered / marked, click to jump | navigator grid |
| **No on-screen calculator** (that's GRE General only) | deliberately absent |
| **No pause; auto-submit at 0:00** | timer hits zero → force submit |
| **No per-item feedback** (deferred; real exam gives none) | results only after submit |
| **Help / Exit** | help overlay (rules) + exit-with-confirm |

**Faithful ≠ punitive extras:** minimal item screen (one item, no live analytics — split-attention
risk from SQ15 Risk table), navigator/flag optional, timer announceable/muteable for a11y.

### B2. Scope & honesty constraints (from PRD + SQ15)

- **COMPLEMENT, opt-in.** Exam Mode is a separate "full mock" surface, **not** the daily FSRS loop.
  Entered deliberately from Tools ▸ GRE Exam Mode. Daily review stays the validated minimal-chrome
  default (SQ15 §E).
- **Gates Readiness only**, never blended into Memory/Performance (PRD §7). On submit it produces a
  rights-only score + **per-leaf breakdown** fed to Performance/Readiness and the prospective
  calibration log — as separate ranges, never a merged number.
- **Mastery-gated & ships last** (PRD §8a): surfaced on the Memory-high / timed-Performance-low gap,
  after interleaving + the ordering algorithm.
- **Firewalled corpus:** items come **only** from the authored eval bank (`eval::p*` partitions),
  **never** the study deck and **never** real ETS items (contamination = automatic fail).
- **Pace-preserving presets** (content-gen spec §5.2): Full 66 / Half 33 / Third 22 / Mini 11, all at
  the official **2.58 min/item** so short mocks stay genuinely speeded.

### B3. Exam-shell visual design (reuses Part A tokens, own chrome)

The shell is deliberately **clinical**, matching ETS's austere test-delivery look while inheriting our
type/token system for coherence:

```
┌───────────────────────────────────────────────────────────┐
│ GRE MATH · SECTION 1        Question 12 of 66     2:14:38 ▮ │ ← header: title · counter · countdown
├───────────────────────────────────────────────────────────┤
│                                                             │
│  12.  If f(x)=∫₀ˣ e^{-t²} dt, then f′(x) = …  (MathJax)     │ ← one item, no-scroll math render
│                                                             │
│      ○ A   e^{-x²}                                          │
│      ● B   2x·e^{-x²}                                       │
│      ○ C   -2x·e^{-x²}                                      │
│      ○ D   e^{-x²} - 1                                      │
│      ○ E   1 - e^{-x²}                                      │
│                                                             │
├───────────────────────────────────────────────────────────┤
│ ⚑ Mark      ◀ Back      Next ▶            Review   Help  ⏻ │ ← footer controls
└───────────────────────────────────────────────────────────┘

REVIEW SCREEN                                        2:14:12 ▮
 ▣ answered  □ unanswered  ⚑ marked   — click any number to go
 ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
 │ 1│ 2│ 3⚑│ 4│ 5│ 6│ 7│ 8│ 9│10│11│  …  66      [ Submit exam ]
 └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
```

- **Math rendering:** **MathJax** (reuse the `mathjax` dep already in `anki/package.json` — no KaTeX,
  no new package; identical to how the reviewer typesets cards, and offline-safe). One item per screen,
  **no vertical scroll** for a standard item (Bridgeman 2003 scrolling penalty — SQ15). Diagrams sized to
  fit. See `docs/superpowers/specs/2026-07-02-latex-math-rendering-design.md`.
- **Timer chrome:** whole-session countdown; turns amber under 5:00; auto-submit + lock at 0:00.
- **Navigator grid** reuses the coverage-grid visual grammar from Part A (cohesion), states =
  answered / unanswered / marked.
- **Results screen** (post-submit, deferred): rights-only score as a **calibration strip** (Wilson CI
  on correct/total — reusing `CalibrationStrip`), **per-leaf breakdown** table, and the honest hand-off
  ("feeds Readiness; not blended with Memory/Performance").

### B4. Architecture & files (fast lane; no engine change)

Follows the content-gen spec §7 "timed/" home; confirmed against `qt.md`'s webview/mediasrv pattern
(same three-edit rule the dashboard used: route + `is_sveltekit_page()` + Python loader). **Code home
is a new top-level `timed/` package + a new sibling Qt dialog** — deliberately kept out of `pipeline/`
(owned by the deck agents) and out of `anki/qt/aqt/gre/dashboard_data.py` (owned by scoring). Only
additive touches to `mediasrv.py` and the Tools-menu init overlap shared files.

| Layer | File | Action |
|---|---|---|
| Form assembler (pure) | `timed/exam_form.py` *(new, top-level)* | **consumes the landed eval bank** — `from eval.bank.loader import load_eval_items` + `taxonomy.bucket_of` — to draw a **blueprint-matched** (≈50/25/25), leakage-isolated form of N items; deterministic per seed; presets 66/33/22/11. **Does not modify `eval/bank/`.** |
| Scoring/pace (pure) | `timed/exam_model.py` *(new)* | pace math (2.58 min/item), rights-only score, per-leaf rollup, Wilson CI on the raw score — unit-testable, no Qt/DB |
| Results → scoring seam | `timed/results.py` *(new)* | write a documented attempts record `{item_id, leaf, chosen, correct, latency}` that the **scoring layer ingests** (its `scoring/data/real_attempts.csv` / calibration log, thu-scoring §4). Exam Mode **never computes Performance/Readiness itself** — it feeds them. |
| Dialog + menu | `anki/qt/aqt/gre_exam.py` *(new, sibling of `gre_dashboard.py`)* | `QDialog` loading the route; Tools-menu `QAction`; **mastery-gate check** before entry (PRD §8a) |
| Transport | `anki/qt/aqt/mediasrv.py` *(additive)* | register `gre-exam` in `is_sveltekit_page()`; read-only endpoint serving the assembled form JSON; a submit endpoint that persists via `timed/results.py` — **no `OpChanges`** |
| Presentation | `anki/ts/routes/gre-exam/` *(new, separate from `gre-dashboard/`)* | `+page.svelte` (shell), `ItemView.svelte`, `Countdown.svelte`, `Navigator.svelte`, `ReviewScreen.svelte`, `Results.svelte`; imports Part A `tokens.css` + `CalibrationStrip`; typesets item math with **MathJax** (`typesetPromise` on the item container) |
| Docs | new `docs/codebase/timed.md`, `INDEX.md`, `STATUS.md`, `execution-plan.md` | per codebase-docs; bump submodule SHA in the same PR |

**Eval-bank items are MCQ-only** (`options[5]`, `correct_index`, `explanation`, `difficulty` 1–5,
`partition` p0–p3) — exactly what the exam shell renders and scores. The assembler reuses
`loader.assert_firewall` semantics; the firewall test (B5) re-asserts zero study-deck/ETS overlap.

**Partition choice (coordinate):** timed forms must draw from a partition the scoring layer is **not**
using for its calibration/validation folds, to keep the train/test firewall intact. Proposed: reserve
**P2** (post-test) for timed mocks, or add a dedicated `eval::timed` subset — a one-line decision to
settle with the eval-bank/scoring owners before build.

**Where state lives:** the session (answers, marks, elapsed) is client-side during the run; on submit
it persists **only** the attempts record via `timed/results.py` to a local, non-collection store, so
the read-only ceiling holds by construction (no scheduler/undo/store writes, no sync churn). Scores are
produced downstream by the scoring layer, never blended here.

### B5. Tests & acceptance (exam mode)

Extends the content-gen spec §8 timed-UI tests:

- **Pace math** — each preset yields the official 2.58 min/item (66→2h50m, 33→~1h25m, …).
- **Rights-only scoring** — unanswered = wrong, no negative marking; score = Σ correct.
- **Blueprint match** — an assembled form is ≈50/25/25 across buckets and drawn only from `eval::p*`
  (firewall test: **zero** study-deck or ETS items present).
- **Navigator state machine** — answered/unanswered/marked transitions; jump-to-item.
- **Auto-submit** — clock at 0:00 force-submits and locks answers.
- **No feedback during the run** — item screen never reveals correctness before submit.
- **Read-only ceiling** — the whole session emits **no** `OpChanges`; the collection quick-check is
  unchanged before/after a mock (the dashboard's read-only test, repeated for exam endpoints).
- **GUI smoke (required):** `./run`, Tools ▸ GRE Exam Mode, run a Mini (11) mock end-to-end: timer
  counts, mark/back/next/review all work, MathJax renders one item with no scroll, submit shows
  rights-only score + per-leaf breakdown feeding Readiness (not blended).
- **Acceptance:** a full-length (66) and at least one short preset run under the official UI element
  set, correct pace, rights-only score, deferred feedback, per-leaf result feed — all read-only, all
  from the firewalled eval bank.

---

## Sequencing, worktrees & process hygiene

**Isolation (per `using-git-worktrees` + `shipping-changes`).** Do **not** work on `main` (this plan
doc is currently uncommitted on the primary `main` worktree — it moves in with the first PR). Two
dedicated worktrees, each initializing the `anki` submodule (both touch the fork UI):

- `agent/ui-redesign` → Part A.
- `agent/exam-mode` → Part B (may itself split into `B-1` pure `timed/` logic + tests, then `B-2` the
  webview + endpoints + GUI smoke).

**Merge order (to minimize rebases + `anki` pin thrash):**

1. **Part A first** — small, pure-presentation; self-hosts Plex + ships `CalibrationStrip` + `tokens.css`
   that *both* Part B **and** `agent/thu-scoring-layer` reuse. Landing it first gives scoring the shared
   primitives to render Performance/Readiness through (§A6), avoiding a two-sided edit war.
2. **`agent/thu-scoring-layer`** rebases onto A and fills the Performance/Readiness slot *content* +
   `dashboard_data.py` (its lines, not ours).
3. **Part B (Exam Mode)** — independent of the dashboard files (separate route + sibling dialog);
   depends only on the landed eval bank (`main`) and, at the results seam, on the scoring layer. Can
   proceed in parallel with steps 1–2 and land whenever green.

**Submodule-pin discipline.** Part A, Part B, and scoring each bump the `anki` submodule SHA. The
**last** of any two to merge re-bumps onto the newest fork commit (fork history is linear; these are
additive files, so fork-side conflicts are unlikely). Coordinate the bump with whoever merges around
the same time; never force-bump over another agent's fork commit.

**Don't disturb running processes** (from the terminals):

- Terminal 1 — the live desktop app (`./run` in `anki/`, pid 82224). Build/test in a **separate
  worktree**; do not rebuild the running app's bundle out from under it. Mind the **PR #10
  stale-bundle gotcha** (configure-time route globs) + the webview **api-access allowlist** (add a
  `GRE_EXAM` kind like the dashboard's `GRE_DASHBOARD`) or the new route 403s / renders blank.
- Sync servers on **:8080** (w4-sync + main) and the **Android emulator** + rsdroid/AnkiDroid builds
  (w3-android) — leave them running; don't reuse the port or the AVD.

**Docs contention.** `docs/STATUS.md`, `docs/execution-plan.md`, `docs/demo-plan.md`,
`docs/codebase/INDEX.md` are edited by several agents right now. Touch them **minimally and append**
(add our row; don't rewrite others' lines); expect a rebase at merge and re-apply just our line.

Both parts stay inside the hard ceilings: **no second Rust change**, read-only, three scores never
blended, no Readiness number without the evidence panel, eval bank never leaked into the study loop.

## Open questions (worth a quick decision before build)

- **Dashboard split with `agent/thu-scoring-layer`:** confirm the §A6 contract (redesign owns chrome +
  `CalibrationStrip`; scoring owns slot content + `dashboard_data.py`) and that Part A merges first. If
  scoring is already mid-edit on the `.svelte` files, we instead hand them the strip + tokens as a tiny
  shared PR and let them integrate. **This is the one coordination that needs a human/owner nod.**
- **Timed-form partition:** which eval-bank partition (proposed P2, or a new `eval::timed` subset) is
  reserved for mocks so it never overlaps the scoring calibration folds? (Coordinate with eval-bank +
  scoring owners.)
- **Fonts:** self-host IBM Plex Mono/Sans in the fork (~3 woff2) vs. a pure system stack (zero binary
  assets)? (Plan assumes self-host with system fallback.)
- **Results seam:** Exam Mode writes an attempts record the scoring layer ingests. Until scoring lands,
  it writes a documented local JSON; confirm the schema/location with the scoring owner so it drops
  straight into `scoring/data/`.
- **Demo gate:** Exam Mode is mastery-gated + "ships last"; a one-line dev flag can bypass the gate for
  filming. (Plan leaves gating on by default.)
