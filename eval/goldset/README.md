# AI gold-set (held-out answer key)

This directory is the **gold-set**: a set of independently known-correct GRE-math
Q&A pairs used **only** to evaluate AI-generated flashcards on Friday (PRD §9).
It is the held-out answer key the AI card pipeline is scored against — the gate is
**fact-precision ≥ 0.98** (≤ 1 wrong-fact card per 50) plus a useful-yield floor.
Because it is the held-out key, the data must stay **out of training and out of
generation**, and out of this public repo.

## What is committed vs. held out

| File | Committed? | Contents |
|---|---|---|
| `README.md` | ✅ | This file. |
| `schema.json` | ✅ | JSON Schema for one record (fields, leaf-tag enum, canary pattern). |
| `canary-manifest.md` | ✅ | Project canary GUID + per-item sentinel convention. |
| `validate.py` | ✅ | Validates the data file; prints count + per-leaf distribution. |
| `goldset.md` | ✅ | Module doc (see `docs/codebase/INDEX.md`). |
| `data/` | ❌ **gitignored** | `pairs.jsonl` (the Q&A keys), the source PDFs, and the builder. |

`eval/goldset/data/` is listed in the repo-root `.gitignore`. **Never commit it.**

## Source (single course family)

All pairs are transcribed from one MIT OpenCourseWare course that publishes
official solutions, chosen to match the exam's ~50% calculus weight:

> **Single Variable Calculus (18.01SC)**, Massachusetts Institute of Technology:
> MIT OpenCourseWare, <https://ocw.mit.edu>. Fall 2010.
> **License: Creative Commons BY-NC-SA 4.0** (<https://creativecommons.org/licenses/by-nc-sa/4.0/>).

Course home: <https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/>

The specific official **solution** PDFs each item is checked against (one of these
URLs is recorded in every record's `source.url`):

- Exam 1 solutions — `.../0817fc547c8edd2c29172f670a4d1d66_MIT18_01SCF10_exam1sol.pdf`
- Exam 2 solutions — `.../8bc1745cc348551cb9b30fb6cc7f9ecf_MIT18_01SCF10_exam2sol.pdf`
- Exam 3 solutions — `.../2045fef2f2fa83e391fd95b39b083173_MIT18_01SCF10_exam3sol.pdf`
- Exam 4 solutions — `.../f1c8096b6d2d8021709b313e87991bd0_MIT18_01SCF10_exam4sol.pdf`
- Final Exam solutions — `.../bbbf05286af4bd705af325080bea0e23_MIT18_01SCF10_finalsol.pdf`

(prefix every path with `https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/`)

**Non-ETS only.** No GRE/ETS exam item is used anywhere — the entire official ETS
corpus is treated as contaminated and is never sourced, transcribed, or referenced.

### Attribution / license interaction

MIT OCW material is CC-BY-NC-SA; this repo is AGPL-3.0-or-later. There is no license
conflict because **we do not redistribute the OCW material** — the transcribed Q&A
and the downloaded PDFs live only in the gitignored, access-controlled `data/` store.
Only our own files (schema, validator, docs) are committed under AGPL. This README is
the required CC-BY-NC-SA attribution.

## Verification standard (honesty over count)

Every record is **double-checked**:

1. **Transcribed** from the official OCW solution (the answer key), with the exact
   exam + problem number and the solution URL recorded in `source`.
2. **Second-solver checked** — re-derived / sanity-checked independently; the
   `second_solver_check` field records how, and confirms it matches the official key.

If an item cannot be confidently verified it is **dropped or flagged**, never
fabricated. Target is 50 verified pairs; the current set has **50** (see below).

## Canary scheme

Every record carries a per-item `canary` sentinel built from the project canary GUID
(see `canary-manifest.md`). The sentinel is a random, meaningless string that has no
reason to appear anywhere except this gold-set, so Thursday's leakage scanner can grep
training/generation corpora for it: a hit means a gold item leaked. The canary value
is safe to commit (it is exactly what the scanner searches for); the **Q&A it is
attached to is not**.

## How to regenerate / verify

The data is access-controlled, so a fresh clone has no `data/`. To rebuild it:

1. Download the official solution PDFs from the URLs above into
   `eval/goldset/data/_src/` (e.g. with `curl`).
2. Transcribe each problem + official answer and **second-solve** it; record the
   exact `source` anchor, the matching `leaf_tag` (one of the 17 in `schema.json`),
   and a per-item `canary`. The builder used to assemble this set lives at
   `eval/goldset/data/_src/build_pairs.py` (also gitignored, since it embeds the
   answers) and writes `eval/goldset/data/pairs.jsonl`.
3. Validate:

   ```bash
   python eval/goldset/validate.py
   ```

   It loads `data/pairs.jsonl`, asserts required fields + a valid leaf tag + a full
   source anchor + `second_solver_check` + the canary on every record, prints the
   total count and per-leaf distribution, and exits non-zero on any violation.

## Current contents

- **50** verified Q&A pairs from MIT 18.01SC (Exams 1–4 + Final).
- Per-leaf distribution (calculus weight 38/50 = 76%):

  | count | leaf tag |
  |---|---|
  | 10 | `topic::calculus::differential_single` |
  | 8 | `topic::calculus::integral_single` |
  | 5 | `topic::calculus::differential_equations` |
  | 15 | `topic::calculus::applications` |
  | 10 | `topic::additional::real_analysis` |
  | 2 | `topic::additional::numerical` |
