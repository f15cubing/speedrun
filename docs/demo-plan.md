# Demo video plan — Milestone 1 (live capture)

> Scope: **what's runnable today (W1–W4)** — the Rust mastery-query engine change, the desktop GRE
> dashboard, the shared engine on Android, and self-hosted sync. **No AI, no live
> Performance/Readiness scores** (deliberate — those land Thu/Fri). Target length **3–5 min**.
> Format: **live screen capture** of the running desktop app + Android emulator.
> State as of 2026-07-01, engine `f15cubing/anki@ea3acae`.

The through-line: **one exam, two apps on one engine, a real engine change, and honesty as a
feature.** Lead with the product (legible), prove the engineering underneath, then prove it's real on
two devices.

---

## What we're showing off vs. base Anki

| # | What we made | Base Anki has | Grade lever |
|---|---|---|---|
| 1 | **Mastery Query** — read-only Rust RPC returning per-topic `{total, reviewed, mastered, avg_recall}`, reusing the scheduler's own FSRS retrievability, one SQL pass, <50 ms @ 50k | Only global stats graphs; no per-topic mastery aggregate | Rust change (20%) + no-corruption ceiling |
| 2 | **Desktop GRE dashboard** — Memory as a **range**, 17-leaf **coverage map**, three **separated** score slots incl. an honest "Insufficient evidence to score" give-up state | Stats heatmaps; no exam readiness, ranges, coverage, or abstention | Scores (20%) + UX (8%) |
| 3 | **GRE deck + ETS taxonomy** — every card `topic::bucket::leaf`-tagged, reproducible from one command | Empty; generic tags | Data foundation |
| 4 | **Same engine on Android** — rsdroid rebuilt bundling *our* `rslib`; phone reviews the same deck with FSRS + our tags, survives restart, Check DB clean | Stock rsdroid backend | Phone-on-one-engine ceiling (10%) |
| 5 | **Sync on our own engine** — self-hosted `anki-sync-server` on our fork; phone review lands on desktop, documented conflict rule, no corruption | AnkiWeb only | Sync ceiling (10%) |

---

## Pre-flight checklist (before you hit record)

- [ ] Desktop dev build running (`./run` in the anki fork) with the seeded GRE deck imported
      (`pipeline/build_deck.py --seed 42`).
- [ ] Do **a handful of reviews** first so Memory has data to show a range (a fully-new deck shows the
      n=0 abstention — decide which state you want on camera; ideally show *some* Memory data + the
      Readiness give-up state).
- [ ] Android emulator (`anki_test`, arm64-v8a) booted with our AnkiDroid debug APK on our rebuilt
      `librsdroid.so`; the GRE deck present.
- [ ] Sync server ready to start: `make sync-server` (port 8080), account `greuser`.
- [ ] A terminal pane sized for readable text, ready to run the mastery tests.
- [ ] Screen recorder set to capture desktop + a second source for the emulator (or use the
      `docs/evidence/w3-android/` + `docs/evidence/w4-sync/` screenshots as B-roll if a live emulator
      capture is fiddly).
- [ ] Close AI/score work-in-progress windows so nothing half-built is on screen.

---

## Shooting script (scene by scene)

### 0:00 — Cold open (~10s)
**On screen:** the desktop app, GRE deck visible.
**Narration:** "This is a fork of Anki turned into one thing — a GRE Math Subject Test tutor that
measures memory, performance, and readiness *separately*, and refuses to fake a number it can't back
up."

### 0:10 — Deck + taxonomy (~25s)
**On screen:** open the Browser, expand the `topic::` tag tree (`topic::calculus::*`,
`topic::algebra::*`, `topic::additional::*`). Click a card, show its single leaf tag.
**Narration:** "Every card maps to exactly one ETS leaf topic. This tag tree is the substrate
everything else reads — the mastery query, the coverage map, the readiness gate."

### 0:35 — The dashboard, the showpiece (~60s)
**On screen:** Tools ▸ GRE dashboard. Walk top to bottom:
1. **Memory** — the range + confidence caveat.
2. **Coverage map** — 17 leaves, per-leaf recall estimate + 95% range.
3. **The three slots** — pause on **Readiness**: *"Insufficient evidence to score — studied X% of
   topics. Best next: …"* with its reasons.
**Narration:** "Stock Anki gives you a heatmap. We give you a calibrated *range* over exam topics, a
coverage map of what the deck actually covers, and three scores kept strictly separate. And this empty
Readiness slot? That's the feature. A confident readiness number on one week of data is an automatic
fail — abstaining honestly is the correct output, so it tells you the single best next topic instead."

### 1:35 — The Rust change under the hood (~60s)
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

### 2:35 — Same engine on the phone (~45s)
**On screen:** the emulator (or `docs/evidence/w3-android/` screenshots): the same deck; an FSRS
answer screen showing intervals + a `topic::calculus::differential_multi` tag; the counter changing;
after a force-stop + reopen the session persisted; Check DB → "Database rebuilt and optimized."
**Narration:** "This isn't a lookalike — it's our `rslib` compiled into the Android backend, proven by
a Kotlin binding test against the real engine. Same deck, same FSRS scheduling, same tags. It survives
a restart and reports no corruption."

### 3:20 — Cross-device sync (~40s)
**On screen:** `make sync-server` in a terminal; then the `docs/evidence/w4-sync/` round-trip — review
a card on Android, rate Good, sync up; on the desktop peer, pull → `revlog 1→2`, `quick_check=ok`.
**Narration:** "Sync runs on *our* engine, self-hosted, no AnkiWeb. Review a card on the phone, it
lands on the desktop — revlog grows, quick-check is clean, no corruption, on a documented conflict
rule."

### 4:00 — Honest close (~20s)
**On screen:** back to the dashboard's three slots.
**Narration:** "What you're *not* seeing yet is deliberate — no AI, no live Performance or Readiness
scores. Those come Thursday and Friday, with held-out evaluation. Everything shown here is merged and
reproducible from a single command."

---

## Honesty framing (say it out loud)

The Performance and Readiness slots are placeholders / give-up states, and there's no AI yet. **Don't
hide it — sell it.** The empty Readiness slot is a live demonstration of the give-up rule (abstention
under insufficient evidence), which is the project's core bet. The biggest current gap is, on-thesis,
a feature.

---

## Runnable proofs referenced in the demo

- Deck: `python pipeline/build_deck.py --seed 42`
- Desktop app: `./run` (in the anki fork)
- Mastery tests: Rust unit tests in `anki/rslib/src/stats/mastery.rs`; Python
  `anki/pylib/tests/test_mastery.py`
- Sync: `make sync-server`, `make sync-smoke`
- Existing B-roll: `docs/evidence/w3-android/`, `docs/evidence/w4-sync/`

## Grows into the Sunday cut

As Thu/Fri land, insert new segments after §0:35 (scores) and before the close: the **MCQ study
surface** — a "GRE MCQ" note type (5 single-select options, SymPy-generated distractors) reviewed on
the *same* FSRS loop, shown as the in-app format the Performance model scores (Thu); live Performance +
Readiness ranges (Thu); the AI card pipeline + gold-set gate (Fri); interleaving ablation + timed mode
(Sat). Keep the same lead (product → engine → two devices) and the same honest close.
