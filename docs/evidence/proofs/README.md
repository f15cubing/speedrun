# Block D — quantitative proofs

Re-runnable evidence for the compressed-Friday Block D. Three proofs, each with a
committed JSON artifact (+ chart where applicable). All deterministic (seed 42).

- **Bench:** `make bench` (runs the REAL engine via the built `anki/out` pylib)
- **Calibration + paraphrase:** `make proofs` (pure-stdlib `scoring/` + eval bank; charts via `.venv-proofs`)

> Honesty labels are baked into each artifact. The scoring proofs are validated on
> **simulated** data (a machinery check); real predictive validity is unestablished
> at n≈1. They prove the math is sound, not that the model predicts a specific
> real student.

---

## 1. Mastery-query latency @ 50k cards (`bench_mastery.json`)

Times the W1 `col.mastery_query(topics)` RPC — the exact read path the desktop
dashboard and the AnkiDroid panel consume — over 300 iterations on a freshly
seeded 50,000-card collection, 20 topics/call (17 leaves + 3 bucket rollups).

| metric | value |
|---|---|
| cards | 50,000 |
| topics / call | 20 |
| iterations | 300 |
| **p50** | **650 ms** |
| **p95** | **667 ms** |
| **worst** | **709 ms** |
| mean | 650 ms |

**Honest reading.** This is the *end-to-end* RPC (Python → FFI → Rust aggregate →
SQLite, marshaled back to dicts) with **20 topics per call**, each doing a
hierarchical `topic::*` scan over 50k cards. That decomposes to ≈32 ms/topic —
consistent with the isolated single-pass Rust aggregate bench (`#[ignore]`d in
`rslib`, ~19 ms) plus the per-topic hierarchical scans ×20 and the FFI/dict
marshaling. The dashboard issues this once on open, so a sub-second refresh at 50k
is acceptable; the obvious future optimization (batch the 20 topics into one
grouped pass, or index the tag prefix) is noted, not required. Numbers will differ
by machine — re-run `make bench` to reproduce locally.

## 2. Memory/Performance calibration (`calibration.json`, `calibration.png`)

Fits the Performance model (logistic + Platt + Fisher-SE) on 70% of simulated
students and measures predicted-vs-realized accuracy on the held-out 30%.

| metric | value |
|---|---|
| Brier | 0.219 |
| ECE | 0.061 |
| test attempts | held-out student split |

Low ECE (≈0.06) ⇒ the reliability curve tracks the diagonal: **predicted ~80% ⇒
~80% realized** (see `calibration.png`). This is the Step-1 calibration proof — on
simulated data (machinery check), labeled accordingly.

## 3. Paraphrase robustness (`paraphrase.json`)

The eval bank's **P3** partition = 28 paraphrase groups (2 rewordings each, same
key). A simulated cohort (500 students, shared latent ability) answers both
rewordings of every group; if accuracy is stable across rewordings the signal is
paraphrase-robust rather than surface-form memorization (design spec §2 go/no-go).

| rewording | accuracy | 95% Wilson CI |
|---|---|---|
| R1 ("original") | 0.630 | [0.622, 0.638] |
| R2 ("reworded") | 0.624 | [0.616, 0.632] |

Accuracy gap **0.006** (overlapping CIs); mean within-group |gap| **0.022** →
**paraphrase-robust** on the authored bank. Descriptive, simulated cohort;
real per-student validity unestablished at n≈1.
