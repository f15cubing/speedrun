# UI/UX Redesign Brief — GRE Math Readiness

> **Paste this whole file into Claude** (or any design tool) as the prompt for a UI/UX redesign.
> It is self-contained: it says what the app is, who uses it, every screen that needs designing
> (with real sample data so you never render lorem ipsum), the constraints you may not break, and
> the visual direction. Ask the tool for **high-fidelity mockups** of the screens in §4 — desktop
> and mobile, light and dark — plus a short rationale for palette, type, and the signature element.

---

## 1. The one-line ask

Redesign the look and feel of a **GRE Mathematics Subject Test prep app** whose entire personality
is **honesty about uncertainty**. It never shows a fake number — every metric is a **range**, and it
**abstains** (says "not enough evidence yet") rather than guess. Make it feel like a **precision
instrument for a math student**, not a marketing SaaS dashboard. Keep the honesty constraints in §5
intact; everything about the visual identity in §6 is yours to push.

## 2. What the app is

It is a fork of **Anki** (the spaced-repetition flashcard app) specialized for one exam: the **GRE
Mathematics Subject Test** (~66 five-option multiple-choice items, 2h50m, scored 200–990, no
calculator). On top of Anki's normal card review, it adds a scoring system that separates **three
things that are usually blended into one "you're 80% ready" lie**:

- **Memory** — *P(you can recall a card right now)*. Comes from the spaced-repetition engine.
- **Performance** — *P(you get a new, unseen exam-style question right)*. A calibrated model.
- **Readiness** — *your projected GRE 200–990 score*, shown only as a range with full evidence.

The product's thesis: **memory ≠ performance ≠ readiness.** These are three separate scores, each
with its own honest range, and the app **refuses to show a readiness number until it has the evidence
to back one** — showing instead the coverage map and the single best next thing to study.

Runs on **desktop** (embedded webview inside the Anki app) and **Android** (a read-only score panel).
It works **offline**; math renders with **MathJax** (LaTeX).

## 3. Who it's for / context

- **Audience:** math majors and grad students doing high-stakes, time-pressured prep. They are
  numerate and skeptical — they trust an instrument that admits what it doesn't know more than one
  that sounds confident. Talk to them like a good TA, not a growth marketer.
- **Tone of the product:** calm, exact, unshowy, quietly rigorous. The uncertainty is the feature,
  not an apology.
- **Surfaces render inside a webview** on desktop and phone, so designs must be **responsive**
  (≈360px phone → ≈960px desktop) and support **light and dark** (dark = Anki "night mode").

---

## 4. The screens to redesign (with real content + sample data)

There are three custom surfaces. **The Readiness Dashboard (4A) is the hero** — spend your best idea
here. Use the sample numbers verbatim so the mockups look real.

### 4A. Readiness Dashboard (the hero) — desktop + a read-only mobile version

One scrollable page. Zones, top to bottom:

**(1) Masthead** — eyebrow `GRE · MATHEMATICS SUBJECT TEST`, title **Readiness**, and a right-aligned
`updated Jul 3, 2026, 4:02 PM`.

**(2) Memory panel** — the headline metric, then a per-area breakdown:
- Lede: *"You can reliably recall about **60%** of what you've studied."*
- Headline range: **60%**, likely **54–66%**, `n = 238` reviews.
- Caveat line: *"Headline reflects 2 of 3 exam areas — the rest have no graded reviews yet."*
- Three exam areas, each with its own range and weight (weights are fixed by ETS: **50 / 25 / 25**):

  | Area | Weight | Recall | Range | Reviews |
  |---|---|---|---|---|
  | Calculus | 50% of exam | 62% | 56–68% | n=174 |
  | Algebra | 25% of exam | 55% | 45–65% | n=64 |
  | Additional topics | 25% of exam | *not studied yet* | — | n=0 |

- Footer caveat: *"Aggregate-calibrated on population defaults — not a personalized model."*

**(3) Three separated score slots** — Memory / Performance / Readiness, shown **side by side as
equals, never summed into a total.** This separation is a load-bearing design idea, not a layout
detail. Two of the three are currently in an honest "can't score yet" state:
- **Performance →** badge *"Not available yet"*, body *"Arrives with the multiple-choice surface."*
- **Readiness →** badge *"Insufficient evidence"* (this is a **designed state, amber — not a red
  error**). Body: *"Insufficient evidence to score a projected exam result — you've studied 41% of
  the exam's topics. That's the honest output, not a gap to paper over."*
  - **Best next:** `real analysis`
  - **Reasons:** only 41% of exam topics studied (need ≥ 50%) · fewer than 200 graded reviews in some
    areas · projection interval still too wide to be useful.

  **Also design the *unlocked* Readiness state** (what it looks like once the gate clears — e.g. 58%
  coverage, 240+ reviews). It must show **all seven** of these together, or none:
  `Projected GRE Math ~711 (likely 678–748)` · confidence **low** · **41→58%** topics covered ·
  updated timestamp · top driver *single-variable calculus* · biggest gap *real analysis* ·
  next best *real analysis → sequences & series.*

**(4) Coverage map** — the 17 official exam leaf topics, grouped by area, each a small cell showing
its recall range. Header stats: **88% in deck · 41% studied.** Three cell states to design:
*studied* (has a range), *not studied yet* (has cards, empty range), *no cards* (dimmed). The single
**best-next** topic gets a quiet highlight/ring.

```
Calculus
  differential single ......... studied  78% (70–86)  n=52
  integral single ............. studied  69% (60–78)  n=41
  integral multi .............. studied  51% (38–64)  n=24
  differential multi .......... studied  44% (30–58)  n=22
  applications ................ studied  55% (44–66)  n=35
  differential equations ...... not studied yet
Algebra
  elementary .................. studied  61% (50–72)  n=38
  linear ...................... studied  47% (34–60)  n=26
  abstract .................... not studied yet
  number theory ............... not studied yet
Additional topics
  real analysis ............... not studied yet   ◀ BEST NEXT (highlight)
  discrete .................... not studied yet
  topology .................... no cards
  geometry .................... not studied yet
  complex ..................... not studied yet
  probability & statistics .... not studied yet
  numerical analysis .......... no cards
```

**Mobile version of 4A** is read-only and condensed: the three scores stacked, each honest state
legible on a phone; the coverage map collapses to a compact list. Same content, one column.

### 4B. Exam Mode — a faithful GRE Math Subject Test simulator

A separate, opt-in "full mock" surface (not the daily study loop). It must feel **clinical and
austere, like the real computer-delivered ETS test**, while staying visually coherent with the rest
of the app. Presets: **Full 66 / Half 33 / Third 22 / Mini 11**, all at the official ~2.58 min/item.

- **Item screen:** header with `GRE MATH` · `Question 12 of 66` · a single global countdown
  `2:14:38` (one clock for the whole test — no per-section timers). Body = one item, no scroll, math
  typeset. Five single-select options A–E. Footer: **Mark**, **Back**, **Next**, **Review**, **Help**,
  **Exit**. Sample item:

  > **12.** If `f(x) = ∫₀ˣ e^(−t²) dt`, then `f′(x) =`
  > (A) `e^(−x²)`  (B) `2x·e^(−x²)`  (C) `−2x·e^(−x²)`  (D) `e^(−x²) − 1`  (E) `1 − e^(−x²)`

- **Timer chrome:** counts down; turns **amber under 5:00**; at **0:00 it auto-submits and locks**.
- **Review / navigator screen:** a grid of all items showing *answered / unanswered / marked*, click
  any number to jump, and a **Submit exam** action.
- **Results screen (after submit only — no per-item feedback during the test):** a **rights-only**
  score shown *as a range* (e.g. **47 / 66 correct**, with a confidence interval), a **per-topic
  breakdown** table, and an honest hand-off line: *"This feeds your Readiness estimate — it is not
  blended into Memory or Performance."*
- **Deliberately absent:** on-screen calculator, pause button, mid-test feedback. Don't add them.

### 4C. Interactive multiple-choice study card (inside the normal review loop)

A flashcard that is itself an MCQ. Design the card face and its answer reveal:
- Front: a question + five tappable options A–E (math typeset).
- On tap: the chosen option turns **green if correct / red if wrong**, the **correct** option is
  highlighted, and an **explanation** reveals below.
- Then the normal review grade buttons appear: **Again / Hard / Good / Easy**.
- Must look right in both light and dark, on desktop and phone.

> The plain daily review screen itself is stock Anki — you don't need to redesign it, but your type
> and color choices should sit comfortably next to it.

---

## 5. Hard constraints (do NOT break these — they are the product)

These come from the app's core promise. A design that violates one is wrong, however pretty.

1. **Never show a bare Readiness number.** A projected score may appear **only** alongside all of:
   point estimate, range, % of exam topics covered, a confidence indicator, last-updated timestamp,
   the main reasons, and the single best next step. All seven, or show the give-up state instead.
2. **Never blend the three scores.** Memory, Performance, Readiness are always separate, each with
   its own range. There is no single "overall %" or combined gauge. Ever.
3. **Every metric is a range, not a point.** No lone big number with a small label. Uncertainty is
   always visible.
4. **Abstention is a designed state, not an error.** "Insufficient evidence" / "not available yet"
   should look calm and intentional — use **amber, never red**; no alarm iconography.
5. **Light + dark, responsive, accessible.** Support night mode; work from ~360px to ~960px; visible
   keyboard focus; respect `prefers-reduced-motion`; don't encode meaning in color alone.
6. **Offline + webview.** No reliance on external CDNs/fonts at runtime; math is MathJax/LaTeX.
7. **Exam Mode is faithful to ETS:** one global clock, one item per screen, no calculator, no pause,
   auto-submit at zero, no feedback until submit, rights-only scoring.

---

## 6. Visual direction (this is the "what it should look like")

You have real freedom on the identity — but spend it deliberately, and ground it in the subject.

**Ground it in the subject.** The world to borrow from is **precision measuring instruments,
scientific readouts, CAS/terminal output, and mathematical typesetting** — calipers, oscilloscope
traces, lab gauges, monospaced tables — *not* a generic analytics dashboard. The student should feel
they're reading an instrument that was calibrated, not a landing page.

**The signature idea — make uncertainty the visual language.** Because "range, never a point" is the
whole product, the *interval itself* should be the memorable, repeated motif. The current app draws
every metric as a **"calibration strip"**: a 0–100% axis with a shaded confidence band and a single
point tick, reused at three scales (exam headline → 3 areas → 17 leaves), and an *empty dotted rail*
when there's no data yet. **You may evolve this or invent a stronger visual for uncertainty** — but
whatever you choose must carry the honesty thesis and repeat coherently across all scales and states
(including the empty / "not studied yet" state, which should be *drawn*, not hidden).

**Typography.** Characterful but restrained; the numbers are the star. Use **tabular (monospaced)
figures for every number, range, percentage, and timer** so digits line up in columns like an
instrument readout — this is non-negotiable for the data; the range bounds and counts must align.
Pair a clean body face with that mono for data. (Current app uses IBM Plex Sans + IBM Plex Mono;
feel free to propose a more distinctive pairing as long as data stays tabular-mono.)

**Color.** Quiet, instrument-like. Spend boldness in **one** place — a single calibrated accent for
the point estimate / primary action (current app uses an instrument **teal**), plus a dedicated
**amber** for the abstain/give-up state. Everything else stays neutral (ink, surface, hairline).
Provide a light and a dark palette. 4–6 named tokens total.

**Motion.** Restrained. One tasteful page-load reveal (e.g. the range bands drawing in) is plenty;
respect reduced-motion. Avoid scattered hover effects that read as "AI-generated."

**Avoid the generic AI-design defaults** unless you can justify one for this brief: (1) warm
cream + high-contrast serif + terracotta; (2) near-black + one acid-green/vermilion accent;
(3) broadsheet hairline columns with zero border-radius. Pick a direction that comes from *this*
subject. **Take one real, justifiable aesthetic risk.**

**Copy voice.** Plain, active, honest, sentence case. Name things by what the student controls.
Errors and empty states give direction, not mood ("Study a few cards and reopen this dashboard,"
not "Oops! Nothing here 🙁"). The give-up copy in §4A is the exact register to match.

---

## 7. The current look (reference, not a cage)

The app already ships a first-pass "calibration-strip" identity: instrument-teal accent, amber
abstain state, IBM Plex Sans/Mono with tabular numerals, hairline-bordered cards on a near-white /
near-black surface, one subtle page-load reveal. It works but reads a little plain. **Your job is to
give it a distinctive, intentional identity** — keep the honesty motif and the constraints in §5, and
push the typography, palette, layout, and signature element somewhere memorable. You may keep the
calibration strip if you make it unmistakably yours, or replace it with a stronger uncertainty motif.

## 8. What to produce

- **High-fidelity mockups** of: 4A Dashboard (desktop **and** mobile, **light and dark**), 4B Exam
  Mode (item screen, review/navigator, results), and 4C the interactive MCQ card. Static HTML/CSS or
  a React prototype is ideal; use the §4 sample data so they look real.
- A short **rationale**: the 4–6 color tokens (hex, light + dark), the type pairing and scale, and a
  one-line description of the signature element and the one risk you took.
- Show at least these **states**: Readiness *gated* (insufficient evidence) **and** *unlocked*
  (scored, full evidence panel); coverage cells *studied / not-studied / no-cards*; Exam timer
  *normal* and *under-5-min amber*.

---

*Source of truth for the product (in the repo, if you have access): `docs/PRD.md` (§7 three scores,
§8a study surfaces, D2 give-up rule), the design spec `docs/superpowers/specs/2026-07-02-ui-redesign-and-exam-mode-design.md`,
and the current components under `anki/ts/routes/gre-dashboard/` and `anki/ts/routes/gre-exam/`.*
