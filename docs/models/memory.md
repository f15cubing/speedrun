# Memory model — "How likely are you to recall this, right now?"

> One of **three scores that are never blended** (PRD §7, D2). Memory is the foundation the other
> two are built on; it is the *only* one Anki already gives us. Read alongside
> [`performance.md`](performance.md) and [`readiness.md`](readiness.md).

## What it measures

**Memory = P(recall a card right now)** — FSRS *retrievability* `R`, the probability the student
would answer a given card correctly if it were shown this instant. It is a **memory** claim only:
"you have this card encoded and retrievable today." It is deliberately **not** an exam claim
(that's Performance) and **not** a score claim (that's Readiness). We never surface a card-level `R`
as an "exam-pass probability."

## Inputs / features

- **Per-card FSRS-6 memory state** (`stability`, `difficulty`) stored in the collection, plus
  **days elapsed** since the card was due. These feed Anki's own retrievability function
  `extract_fsrs_retrievability(...)` (a SQLite UDF in `rslib`), so our number is the *same* `R` the
  scheduler uses — not a lookalike re-implementation.
- **Topic tags** (`topic::<bucket>::<leaf>`, the frozen ETS taxonomy, PRD §6 / Appendix A) group
  cards for aggregation.
- These are gathered in **one read-only SQL pass** by our engine change, the **Mastery Query** RPC
  (PRD §5), which returns per topic `{ total_cards, reviewed_count, mastered_count, avg_recall }`.
  A card counts as **mastered** when it has an FSRS memory state **and** `R ≥ 0.9`
  (`MASTERY_RETRIEVABILITY_THRESHOLD`); `reviewed_count` = cards that have any memory state.

## The math — mastered fraction + Wilson score interval

The headline Memory number for a topic is the **mastered fraction** `p̂ = mastered_count /
reviewed_count`. Because that fraction is a proportion estimated from a finite number of reviewed
cards, we report it as a **Wilson score interval** (95%, `z = 1.96`) rather than a bare point —
Wilson is well-behaved near 0 and 1 and at small `n`, where the naive normal interval breaks:

```
center = (p̂ + z²/2n) / (1 + z²/n)
half   = ( z · √( p̂(1−p̂)/n + z²/4n² ) ) / (1 + z²/n)
range  = [ center − half , center + half ]   (clipped to [0,1])
```

The **exam-level headline** is an **ETS-weighted (50/25/25) roll-up** across the three buckets
(Calculus / Algebra / Additional). Buckets with **zero** reviewed cards are *excluded and the
remaining weights renormalized* (we never impute a topic you haven't studied), and the headline
interval is obtained by **weighted normal error propagation** over the pooled per-bucket
proportions. Implementation: `anki/qt/aqt/gre/dashboard_data.py` (`wilson_interval`, `headline`).

## How uncertainty is expressed as a range

Every Memory figure — each leaf, each bucket, and the exam headline — ships as **`point [low, high]`**,
never a lone number. Narrower intervals mean more reviewed cards in that topic; wide intervals are an
honest signal of thin data. On the dashboard this renders as the shaded 95% band + point tick of the
shared `CalibrationStrip`.

## Honesty labels & abstention

- **Aggregate-calibrated, not personalized.** `R` comes from FSRS **population defaults**, not
  parameters fit to this one student. We do **not** claim personal calibration below ~1,000 reviews
  (PRD §7a). The label the UI carries is "aggregate-calibrated (population defaults)."
- **Abstains at `n = 0`.** A topic (or the whole deck) with no reviewed cards shows a dotted
  "not yet" rail, not a fabricated `0`/`100%`. This is the same abstention discipline that, at the
  exam level, becomes the Readiness **give-up rule**.
- **Calibration is a claim we have to earn.** "Calibrated" (80% predicted ⇒ ~80% observed) is only
  asserted once enough reviews exist to draw a reliability diagram whose points sit within CI of the
  diagonal (TimeSeriesSplit → reliability + binomial CIs → ECE; Brier/log-loss as bin-free anchors).
- **Feeds, never blends.** Memory's per-topic `avg_recall` is an *input feature* to Performance
  (see [`performance.md`](performance.md)); the two scores are always displayed separately.

## Give-up rule (context)

Memory itself has no 200-review/50%-coverage gate — but its per-topic recall and coverage are the
raw material for the **Readiness give-up rule** (≥ 200 graded reviews · ≥ 50% leaf coverage ·
interval width ≤ 120 scaled points; a bare readiness number is an automatic fail). See
[`readiness.md`](readiness.md).

## Where it lives

`anki/rslib/src/stats/mastery.rs` + `storage/card/mod.rs` (the Rust Mastery Query),
`anki/pylib/anki/collection.py` (`mastery_query`), `anki/qt/aqt/gre/dashboard_data.py` (Wilson +
roll-up view-model). Docs: `docs/codebase/rslib.md` (§ Mastery Query), `docs/codebase/qt.md`
(§ dashboard).
