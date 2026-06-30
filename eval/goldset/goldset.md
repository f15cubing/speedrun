# AI gold-set (eval)

> Co-located doc for `eval/goldset/`. Read this before changing anything here.

## Purpose
The gold-set is the **held-out answer key** for Friday's AI-card evaluation (PRD §9):
50 independently known-correct GRE-math Q&A pairs that AI-generated cards are scored
against, with the pre-registered gate **fact-precision ≥ 0.98** plus a useful-yield
floor. It exists so "the AI is correct" is measured against facts verified *without*
the AI, and so those facts can never silently leak into training or generation. Source
is a single MIT OpenCourseWare course with official solutions (18.01SC Single Variable
Calculus, CC-BY-NC-SA); see `README.md` for full attribution and the access-control
model.

## Public interface
- **`schema.json`** — JSON Schema for one record. Required fields: `id` (`^g\d{3}$`),
  `question`, `answer`, `source{course, problem_set, problem_no, url}`, `leaf_tag`
  (one of the 17 `topic::<bucket>::<leaf>` leaves from PRD Appendix A),
  `second_solver_check`, `canary`. Single source of truth for the leaf enum and canary
  pattern; the validator reads it.
- **`validate.py`** — CLI gate. `python eval/goldset/validate.py` loads
  `data/pairs.jsonl`, validates every record against the rules above, prints the total
  count + per-leaf distribution + calculus weight, and exits non-zero on any violation
  (including a missing/empty data file). Stdlib-only; runs on python 3.9+.
- **`canary-manifest.md`** — project canary GUID + the `CANARY-GRE-SPEEDRUN-<guid>-item-<NNN>`
  per-item sentinel convention the Thursday leakage scanner greps for.
- **`data/pairs.jsonl`** — the records themselves. **Gitignored / access-controlled**;
  consumed by the Friday AI eval and the leakage scan, never published.

## Dependencies
- **Taxonomy:** `leaf_tag` values are the frozen 17-leaf taxonomy in `docs/PRD.md`
  Appendix A (`topic::calculus|algebra|additional::<leaf>`). Keep the `schema.json`
  enum in sync if the taxonomy ever changes.
- **Consumers (not yet built):** the AI card pipeline + gold-set gate (PRD §9, Friday)
  reads `data/pairs.jsonl`; the leakage pipeline (PRD §11/§12, Thursday) greps for the
  canary. Neither is in this PR.
- **Isolation:** `eval/goldset/data/` is gitignored (repo-root `.gitignore`). Nothing
  in `anki/` or `Anki-Android/` depends on this directory.

## Gotchas & invariants
- **Never commit `data/`.** It holds the held-out keys (and the source PDFs + builder).
  Only schema/README/canary-manifest/validator/this doc are committed. Leaking the keys
  zeroes the AI score.
- **Never use ETS items.** Source is MIT OCW (non-ETS) only; the ETS corpus is
  contaminated.
- **Honesty over count.** Every answer is transcribed from the official solution **and**
  second-solver re-derived (`second_solver_check`). Unverifiable items are dropped, not
  guessed. Target 50; shortfalls are documented, never padded.
- **Canary is committable, data is not.** The sentinel is meant to be grepped for; the
  Q&A it tags is not.
- **One leaf tag per record**, exactly, from the 17-leaf enum.

## Related tests
- `validate.py` is the executable gate (run it in CI / before the Friday eval). Its
  red/green behavior was verified: it exits non-zero on a record with a bad leaf tag,
  empty `second_solver_check`/`answer`, non-OCW url, or malformed canary, and exits 0
  on the clean 50-record set.

---
Last verified against: 6941192
