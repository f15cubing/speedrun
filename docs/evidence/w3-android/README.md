# W3 — Milestone-1 Android review-session evidence

Captured on the `anki_test` arm64-v8a emulator (API 35) running our locally-built AnkiDroid
(`AnkiDroid-full-arm64-v8a-debug.apk`) on **our** rebuilt `rsdroid` backend — i.e. `librsdroid.so`
bundling `f15cubing/anki@ea3acae` (the W1 mastery-query engine). Deck: the seeded, leaf-tagged GRE
study deck from `pipeline/build_deck.py --seed 42`. This closes the manual gate deferred at PR #12.

| # | File | Shows |
|---|------|-------|
| 1 | `01-studyoptions-86-cards.png` | GRE Math Subject Test ▸ Study Deck: 86 total cards on our engine. |
| 2 | `02-review-question.png` | A real card front — multivariable calculus: compute ∂f/∂x. |
| 3 | `03-review-answer-fsrs-tag.png` | Answer shown with **FSRS** intervals (Again <1m · Hard <6m · Good <10m · Easy 5d) and our leaf tag `topic::calculus::differential_multi` — proof the shared engine schedules the review. |
| 4 | `04-review-progressed.png` | Session advanced to a second leaf (`topic::calculus::integral_multi`, answer `25/3`); counter moved `10 0 0` → `6 3 0` (an *Again* pushed a card into learning) — real scheduler state change. |
| 5 | `05-reopened-persisted.png` | After a full force-stop + reopen: collection reopens cleanly and the session persisted — footer went from "Studied 29 cards" to **"Studied 34 cards in 3.02 minutes today"**. |
| 6 | `06-checkdb-no-corruption.png` | **Settings/overflow ▸ Check ▸ Check database → "Database rebuilt and optimized."** — the backend `quick_check` on our engine reports **no corruption**. |

## Conclusion
Android runs a real FSRS review session on the shared engine (Wednesday Milestone-1 Android exit
gate), the review history survives an app restart, and the on-device no-corruption smoke passes on the
same `rslib` that carries our W1 change. Combined with the green host-JVM `MasteryQueryTest` (PR #12),
the RPC is reachable from Kotlin and the engine is undamaged.
