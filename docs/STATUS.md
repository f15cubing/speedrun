# STATUS — live project state

> The single "what's actually done / in-flight / next" view. **Every merged PR updates its line
> here in the same merge** (rule in the `shipping-changes` skill). `docs/execution-plan.md` stays
> the day-by-day plan; this file is the authoritative progress snapshot.

_Last updated: 2026-07-01 (Wed)._

## Done

- **Decisions** signed off (PRD §16: D1 Rust=mastery query, D2 three-score + give-up, D3 Android via
  rsdroid, D4 taxonomy, D5 ablation pre-registered).
- **Repo + licensing:** public AGPL-3.0 fork, `LICENSE` + Anki credit; submodules pinned
  (`anki@25.09.4`, `Anki-Android@v2.24.0`).
- **Spike 1 — desktop build:** `./run` compiled + ran a full review loop (exit 0).
- **Spike 2 — Android build:** `assembleFullDebug` SUCCESSFUL with `librsdroid.so`; emulator booted,
  AnkiDroid launched.
- **PR #1** (merged) — seeded GRE study-deck generator + `topic::*` tagging + coverage gate
  (`pipeline/`).
- **PR #2** (merged) — MIT OCW gold-set store + canary + validator, data gitignored (`eval/goldset/`).
- **PR #3** (merged) — workflow change-risk tiers + fast lane, compile-cache + trust-green, live
  `STATUS.md`, process-freeze guardrail (`.cursor/skills/`, `AGENTS.md`).
- **PR #4** (merged) — content-generation + timed-UI design spec, tuesday-data-foundation spec, and
  the content-generation pipeline plan, with matching PRD/INDEX/architecture/execution-plan updates
  (§8 interleaving algorithm, §8a flashcards→MCQ→timed, §12a two-lane generation, Appendix A
  tag/verification conventions).
- **PR #5** (merged) — Mastery Query (W1) design spec + implementation plan: read-only
  `StatsService.MasteryQuery` RPC (per-topic FSRS mastery aggregate), single-pass SQL + Rust
  aggregation, TDD task breakdown (docs only; the engine-lane implementation is separate).
- **PR #6** (merged) — Round-4 testing-UI research thread (SQ15: authentic exam-shell UI
  design/ablation/decision) added to `research/` + folded into SYNTHESIS/frame/sources. Verdict:
  COMPLEMENT (opt-in "Exam Mode" gating Readiness only); does not consume interleaving's ablation slot.
- **PR #7** (merged) — **W1 Mastery Query engine change** (the real Rust engine change, D1):
  read-only `StatsService.MasteryQuery` RPC + pylib `Collection.mastery_query` + 3 Rust unit tests
  (empty/zero · aggregation+hierarchy · read-only invariant asserting undo step + study-queue counts +
  `quick_check_corrupt`) + Python integration test + `#[ignore]`d 50k perf bench (p50 ~19 ms) +
  rsdroid codegen reachability. anki fork bumped to `f15cubing/anki@352135e`; `.gitmodules` repointed
  to the fork. Engine extra gate passed (different-agent review). Live Android AAR rebuild + review is W3.
- **PR #8** (merged) — **W2 desktop dashboard** design spec + implementation plan: read-only Memory
  score as a range (Wilson CI + ETS 50/25/25 rollup) + 17-leaf coverage map consuming the W1 RPC;
  three separated score slots (Readiness = honest give-up state, Performance = Thursday placeholder);
  Python view-model + vendored taxonomy + standalone SvelteKit route; TDD task breakdown (docs only;
  the Qt/TS implementation is a separate fast-lane PR).
- **PR #9** (merged) — **W2 desktop dashboard build** (fast lane, in the fork): read-only Memory score
  as a range (Wilson CI + ETS 50/25/25 rollup, n=0 renorm) + 17-leaf coverage map (per-leaf recall
  estimate + 95% range) consuming the W1 RPC; three separated slots (Readiness give-up state w/
  next-best topic + reasons, Performance Thursday placeholder); pure-Python view-model + vendored
  taxonomy (drift-guarded) + standalone SvelteKit route + read-only `greDashboardData` endpoint +
  Tools-menu QDialog. Playtested end-to-end; fixed a stale-bundle rebuild gotcha + the webview
  API-access allowlist (`GRE_DASHBOARD` kind). anki fork → `f15cubing/anki@ea3acae`.
- **PR #10** (merged) — **testing-process refinement:** require a GUI smoke test for any new webview
  page / SvelteKit route / dialog (fast-lane + base checklists), and document the two W2 gotchas
  (configure-time route globs → stale bundle; `webview.py` api-access allowlist → 403) in
  `building-and-testing`. Closes the gap where handler-level unit tests passed on an end-to-end-broken page.
- **PR #11** (merged) — **W3 Android review** design spec + implementation plan: rebuild rsdroid against
  our anki fork (bundles `rslib` w/ the W1 mastery query) + AnkiDroid-fork wiring (`local_backend`) + a
  real review session on an emulator + a read-only Kotlin `Collection.masteryQuery` binding proven by a
  Robolectric test (host `.jar`) + an on-emulator smoke; both Android repos tracked as recursive
  submodules; engine-lane w/ different-agent review. Docs only; the Android build is a separate PR.
- **PR #12** (merged) — **W3 Android review build** (engine lane): rebuilt `rsdroid` from source (our
  fork) so its bundled `rslib` carries the W1 mastery query; wired AnkiDroid via `local_backend=true`;
  added a read-only Kotlin `Collection.masteryQuery` binding proven by a host-JVM test against the real
  compiled `rslib` (`MasteryQueryTest`, green); on-emulator smoke shows `librsdroid.so` loads + the
  DeckPicker launches. Forks (recursive submodules): `f15cubing/Anki-Android@67364a7`,
  `f15cubing/Anki-Android-Backend@3dc30c2` (bundles `f15cubing/anki@ea3acae`). Different-agent review
  passed (read-only + no-`OpChanges` ceilings hold; no new engine code). **⚠️ Deferred Milestone-1
  follow-up (not yet captured):** the manual on-device review-session evidence — study a real FSRS
  session on the emulator + Settings ▸ Advanced ▸ Check Database no-corruption smoke.

## In flight

- **W3 Milestone-1 evidence (follow-up to merged PR #12):** capture the on-emulator review-session
  screenshot + the Check-Database no-corruption smoke and attach them. The build, binding, host-JVM
  proof, and `librsdroid.so`-loads smoke already merged; this is the remaining hands-on-device proof.

## Next (per execution-plan)

- **Wednesday — Milestone 1 (decomposed):**
  - **W1 — Mastery Query (Rust engine change):** ✅ **shipped (PR #7).** Read RPC, never `OpChanges`.
  - **W2 — Desktop dashboard:** ✅ **shipped (PR #9).** Memory score as a range + coverage map
    (consumes the RPC); read-only, three separated slots. Spec + plan were PR #8.
  - **W3 — Android review:** ✅ **build shipped (PR #12).** rsdroid rebuilt with our change + APK on the
    local backend + `masteryQuery` binding proven (host-JVM test) + `librsdroid.so`-loads smoke.
    Deferred: the hands-on-device review-session + Check-Database evidence (follow-up above).
  - **W4 — Sync foundation:** `anki-sync-server` + conflict-rule smoke test.
