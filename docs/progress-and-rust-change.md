# What we've built so far (in plain terms) + the Rust change, in depth

> A non-technical-friendly tour of the project as of **2026-07-01 (Wed)**, repo commit `84ec5c8`,
> engine `f15cubing/anki@ea3acae` (Anki 25.09.4). The second half is a deep, precise explanation of
> the Rust engine change — the part the assignment weighs most (20%) and the part most people gloss over.

---

## 1. The one-paragraph version

We forked Anki (the open-source flashcard app) and are turning it into a study tool for **one exam —
the GRE Mathematics Subject Test**. It runs in two places that share the *same* underlying engine: a
**desktop app** and an **Android phone app**. We made a real change *inside Anki's Rust core* (not
just the screens) that can answer, per topic, "how well does this student actually know this?" On top
of that engine we built an honest **memory dashboard** (it shows a *range*, and refuses to show a
number when it doesn't have enough data), and we stood up **sync** so a card reviewed on the phone
shows up on the desktop and vice-versa. No AI yet — that's deliberate; AI comes later in the plan.

---

## 2. What's done so far (plain terms)

| Piece | What it means for a user | Where it lives |
|---|---|---|
| **The study deck** | A ready-made GRE math deck where every card is labeled with its exact topic (e.g. "single-variable integrals"). | `pipeline/` → `pipeline/dist/gre-study-deck.apkg` |
| **The Rust engine change** | The app can ask the engine, "for each topic, how many cards are there, how many has the student actually learned, and what's their average recall?" — fast, even on 50,000 cards. | `anki/rslib/src/stats/mastery.rs` (+ proto + SQL + Python binding) |
| **Desktop dashboard** | A "Memory" score shown as an honest *range* (not a fake single number), plus a **coverage map** of which topics the deck covers. It **abstains** — shows no score — until you've done enough reviews and covered enough of the exam. | `anki/qt/aqt/gre/`, `anki/ts/routes/gre-dashboard/` |
| **Android app on the same engine** | The phone runs *the same* Rust engine (via a rebuilt "rsdroid" backend), reviews the same deck, and schedules with the same algorithm (FSRS). | `Anki-Android/`, `Anki-Android-Backend/` |
| **Sync foundation** | A self-hosted sync server (running our engine) so a review on one device lands on the other, with no corruption. | `sync/`, `docs/codebase/sync.md` |

Everything above is merged and reproducible. What's **not** done yet: the Performance and Readiness
scores, the AI card pipeline, the study-feature experiment (interleaving), the formal test proofs,
and the packaged installers. (See the live gap tracker canvas for the full remaining list.)

---

## 3. The Rust change, in depth

### 3.1 Why change Rust at all (and why *this* change)

Anki is built in layers. The **engine** — scheduling, storage, the spaced-repetition math — is
written in **Rust** (`rslib`) for speed and correctness. The **screens** (desktop menus, the phone
UI) are written in Python/Kotlin/JavaScript *on top of* that engine. The assignment requires a real
change **inside the Rust engine**, because that's the hard, shared, high-stakes part: a change there
ships to *both* the desktop and the phone automatically, and a mistake there can corrupt everyone's
data.

Our change is a **Mastery Query**: a new read-only request that returns, **per topic**, four numbers:

- `total_cards` — how many cards are in that topic,
- `reviewed_count` — how many of them the student has actually started learning (have a memory state),
- `mastered_count` — how many are currently "mastered," and
- `avg_recall` — the student's average probability of remembering a card in that topic *right now*.

**Why this belongs in Rust, not Python.** The "probability of remembering right now" (called
*retrievability*, `R`) is computed by Anki's FSRS memory model, whose helpers live in the Rust engine
and read the raw per-card memory state stored in the database. Doing this in Python would mean either
(a) re-implementing the FSRS math (risky, and it would drift from the real engine), or (b) pulling
every card's raw data across the language boundary and looping in Python (slow on 50k cards, and it
duplicates logic the engine already has). Doing it in Rust means we reuse the *exact* same math the
scheduler uses, in one fast database pass. This is the honesty principle in code: the dashboard's
mastery numbers come from the same engine that schedules the reviews — not a lookalike.

### 3.2 The contract (protobuf)

Anki's engine talks to the screens through **protobuf** messages — a strict, versioned "API
contract." We added three messages in `anki/proto/anki/stats.proto` and one new RPC on the existing
read-only `StatsService`:

```proto
rpc MasteryQuery(MasteryRequest) returns (MasteryResponse);

message MasteryRequest {
  repeated string topics = 1;   // e.g. ["topic::calculus", "topic::algebra::linear"]
}
message TopicMastery {
  string topic = 1;             // echoes the requested tag
  uint32 total_cards = 2;       // matching cards (incl. new/suspended/buried)
  uint32 reviewed_count = 3;    // of those, cards that have an FSRS memory state
  uint32 mastered_count = 4;    // of the reviewed, those with R >= 0.9
  double avg_recall = 5;        // mean R over reviewed cards; 0.0 if none
}
message MasteryResponse {
  repeated TopicMastery topics = 1;   // one row per requested topic, in request order
}
```

A key design choice: a request for `topic::calculus` matches that tag **and every descendant**
(`topic::calculus::integral_single`, `topic::calculus::differential_single`, …). That mirrors Anki's
hierarchical tag tree, so the dashboard can ask for a whole bucket ("Calculus") or a single leaf.

### 3.3 The data pass (one SQL query)

The engine gathers the raw data in a **single read-only SQL query**
(`anki/rslib/src/storage/card/mod.rs`, `all_card_tags_and_retrievability`). Simplified:

```sql
SELECT n.tags,
       case when c.type = 0 then null
            else extract_fsrs_retrievability(c.data, /* due, ivl, day math… */)
       end
FROM cards c JOIN notes n ON c.nid = n.id
```

What this says in plain terms, row by row over every card:
- `n.tags` — the card's topic labels (a space-separated string like `" topic::calculus::integral_single "`).
- `c.type = 0` means a **brand-new, never-studied card** → it has no memory state, so retrievability is `null`.
- Otherwise, `extract_fsrs_retrievability(...)` computes `R`, the **current probability of recall**,
  from the card's stored FSRS memory state plus how many days have passed. This is a custom SQL
  function the engine registers — the *same* FSRS math the scheduler uses.

So one pass returns a list of `(tags, R-or-null)` for the whole collection. No writes, no locks held
open — just a `SELECT`.

### 3.4 The aggregation (pure Rust fold)

`aggregate_mastery` in `mastery.rs` folds those rows into one `TopicMastery` per requested topic.
For each row it checks `tag_matches(tags, topic)` (exact tag *or* a `topic::…` descendant), and if it
matches:
- always counts it toward `total_cards`;
- if `R` is present (card has been studied), counts it toward `reviewed_count`, adds `R` to a running
  sum, and — if `R >= 0.9` (`MASTERY_RETRIEVABILITY_THRESHOLD`) — toward `mastered_count`.

At the end, `avg_recall = sum_R / reviewed_count` (or `0.0` when nothing's been reviewed). The `0.9`
threshold is our definition of "mastered": a 90%-or-better chance of recalling the card right now.

The whole thing is split into two functions on purpose: a **pure** function
(`aggregate_mastery(rows, topics, threshold)`) that has no database and is trivial to unit-test, and a
thin method (`mastery_for_topics`) that fetches the rows and calls it. That separation is why the math
can be tested exhaustively without a database.

### 3.5 The hard invariant: read-only, never corrupts, never breaks undo

Anki has an absolute rule: a **read** must never look like a **write**. Concretely, our query:
- **never returns `OpChanges`** (the struct Anki uses to signal "something changed"),
- **never calls** `transact` / `transact_no_undo` (the write paths),
- **adds no undo step**, and leaves the study-queue counts byte-identical.

Why this matters: if a read accidentally registered as a change, it would pollute the undo history,
trigger needless sync uploads, and could corrupt the collection. This invariant is the project's #1
"do not violate" ceiling, and it's enforced by a test (below).

### 3.6 The tests (proof it works and stays honest)

**3 Rust unit tests** (`anki/rslib/src/stats/mastery.rs`):
1. `empty_and_no_match_yield_zeros` — no cards, or cards in a different topic, return all-zeros.
2. `aggregation_and_hierarchy` — mixed reviewed/new/mastered cards across two calculus leaves; checks
   the counts, the `avg_recall` average, and that asking for the `topic::calculus` bucket correctly
   rolls up both leaves (and that a new, unreviewed card counts toward `total_cards` only).
3. `mastery_query_is_read_only` — runs the query against a real collection and asserts **no new undo
   step**, **unchanged study-queue counts**, **no cards added/removed**, and **`quick_check` reports
   no corruption**. This is the invariant from §3.5, enforced.

Plus an `#[ignore]`d **50,000-card performance smoke test** (`mastery_query_50k_perf`) asserting the
query's median stays under the 50 ms target.

**2 Python integration tests** (`anki/pylib/tests/test_mastery.py`), which call the change the way the
real app does — through the language boundary:
1. `test_mastery_query_counts_and_hierarchy` — same counts/hierarchy check, but end-to-end from Python.
2. `test_mastery_query_is_read_only_with_undo` — adds a note, runs the query, and confirms the "Add
   Note" is **still undoable** afterward (the read didn't disturb the undo stack), then undoes it.

### 3.7 How it reaches the phone

Because the change is in the shared engine, the phone gets it "for free" — but only after we
**rebuild the Android backend** (`rsdroid`) from our fork so its bundled copy of the engine carries
the change. We did that (W3): the Android build links our locally-built backend, and a Kotlin binding
(`Collection.masteryQuery`) calls the exact same RPC, proven by a host-JVM test against the real
compiled engine.

### 3.8 Files touched + merge difficulty

| File | Change |
|---|---|
| `anki/proto/anki/stats.proto` | +1 RPC, +3 messages (additive) |
| `anki/rslib/src/stats/mastery.rs` | **new** — aggregation + tests |
| `anki/rslib/src/stats/mod.rs` | register the new module |
| `anki/rslib/src/stats/service.rs` | wire the RPC to `mastery_for_topics` |
| `anki/rslib/src/storage/card/mod.rs` | **new** read-only SQL helper |
| `anki/pylib/anki/collection.py` | Python binding `mastery_query(...)` |

**Merge difficulty: low.** Every change is *additive* on stable insertion points — a new proto
message, a new read RPC, a new SQL helper, a new binding. We touched no existing scheduler, storage
write, or undo logic, so a future rebase onto upstream Anki is very unlikely to conflict.

---

## 4. The simplest possible analogy

Think of the deck as a big library where every book has a subject sticker. Anki already knows, for any
one book, "how likely is this student to remember it today?" Our Rust change adds a **librarian's
report**: hand it a list of subjects and it walks the shelves once and hands back, per subject, how
many books there are, how many the student has actually started, how many they've truly mastered, and
their average recall — quickly, and **without moving or damaging a single book**. The desktop and the
phone both ask this same librarian, so their reports always agree.
