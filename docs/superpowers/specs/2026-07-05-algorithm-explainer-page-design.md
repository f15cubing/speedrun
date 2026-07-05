# Algorithm explainer page — "Built on FSRS. Not just FSRS." — Design Spec

> A desktop in-app page (Tools ▸ **"How this app differs from FSRS"**) that makes our study
> method legible: we **build on** FSRS rather than replacing it, and add interleaving, a timed
> exam mode, three separated scores, and an honesty/give-up rule. Technical tone; the read-only
> engine change is a one-line aside, not a hero. The interleaving section is **interactive**,
> running the **real** vendored `pipeline/interleave.py` on an example queue. Desktop only. Fast
> lane (Qt-UI-only in the `anki` fork + outer docs). Dated 2026-07-05.

## Decisions (locked with owner)

- **Audience/tone:** technical, but **without** emphasis on the read-only mastery-query engine
  change (folded into a one-line aside inside the "build on FSRS" framing).
- **Interactivity:** the interleaving section runs the **real vendored algorithm** (a copy of
  `pipeline/interleave.py`) via a read-only endpoint on a small deterministic example GRE queue —
  not a JS re-implementation, not the live due queue.
- **Scope:** the full "different from FSRS" story — (1) build on FSRS, (2) interleaving, (3) timed
  exam mode, (4) three separated scores, (5) honesty/give-up.
- **App:** desktop only (mirrors the dashboard + exam-mode SvelteKit-dialog pattern).

## Global constraints

- **Fast lane.** Only `anki/qt/aqt/` (Python UI) + `anki/ts/` (frontend) + outer docs/tests. **No**
  `rslib`, `.proto`, `pylib` FFI, scheduler/undo/store. Self-reviewed against the fast-lane checklist.
- **Read-only.** The one endpoint runs a **pure function on a canned example queue** — it does not
  touch `mw.col`, never returns `OpChanges`, cannot mutate the collection or undo.
- **Reuse the design system.** Import the dashboard's `tokens.css` + `CalibrationStrip.svelte` so the
  page reads as one product with the dashboard and exam mode. No new fonts.
- **Honesty preserved.** Every quantitative claim on the page is either (a) computed live by the real
  algorithm (interleaving metrics) or (b) a cited literature effect size **with** its honest
  incremental caveat (dz≈0.2–0.35). No fabricated numbers; the three scores stay separate.
- **Vendoring is a copy, drift-guarded.** `pipeline/interleave.py` is copied verbatim into
  `anki/qt/aqt/gre/interleave.py` (the app can't import the outer `pipeline/` at runtime, same reason
  `exam.py`/`exam_items.json` are vendored). An outer test (`tests/test_interleave_sync.py`) fails if
  the copy drifts from the source.

## 1. Component & data flow

```
Tools ▸ "How this app differs from FSRS"
  → GreMethod QDialog (anki/qt/aqt/gre_method.py)
    → load_sveltekit_page("gre-method")
      → +page.svelte renders 5 sections (mostly static, technical prose)
        └─ Interleave.svelte (the interactive centerpiece):
             on mount + on K/W change → POST /_anki/greMethodInterleave {k, w}
               → mediasrv handler → gre/method_data.build_interleave_demo(k, w)
                 → runs the REAL vendored gre/interleave.py on the canned EXAMPLE_QUEUE
                 → returns {blocked:[...], interleaved:[...], metrics:{...}}  (read-only, no col)
             renders blocked vs interleaved as cluster-coloured chips + live metrics
      → "Open exam mode" / "Open dashboard" buttons (reuse existing dialogs)
```

Units, each with one job:
- **`gre/interleave.py`** — vendored pure ordering algorithm (unchanged copy).
- **`gre/method_data.py`** — the canned `EXAMPLE_QUEUE` (authentic `topic::*` leaves) + `build_interleave_demo(k, w)` view-model wrapper. Headless-importable (no aqt deps), mirrors `dashboard_data.py`/`exam.py`.
- **mediasrv handler** — thin: parse `{k, w}`, call `build_interleave_demo`, return JSON. No `col`.
- **`Interleave.svelte`** — the interactive viz (chips + metrics + K/W sliders).
- **`+page.svelte`** — the page shell + the 4 static sections + the interactive one.

## 2. Content sections (single scrolling page, technical)

1. **Build on FSRS, don't replace it.** FSRS answers one question (retrievability `R` → when you'll
   forget a card). An exam asks three. We keep FSRS's scheduling **byte-for-byte** and add
   switch-off-able layers above it. *One-line aside:* the only change inside the engine is a
   **read-only** mastery query; everything else lives above the engine.
2. **Interleaving (interactive).** FSRS orders by urgency, which tends to **block** same-type cards
   together. We add a **constrained re-sort** that disperses confusable problem types while (a)
   leaving FSRS fields untouched and (b) bounding displacement so urgent cards never starve. Live
   demo (see §3). Evidence: Rohrer 2020 (classroom d≈0.83), Brunmair & Richter 2019 (math g≈0.34),
   with the honest **incremental** caveat over an already-spaced app (dz≈0.2–0.35).
3. **Timed exam mode.** FSRS has no notion of test conditions; the GRE Math Subject Test is
   **speeded** (~2.58 min/item). We add a faithful simulator — one clock, no calculator, no pause,
   auto-submit, rights-only — with pace-preserving presets. Construct = **speededness**, not the
   fragile anxiety literature. Button → open exam mode.
4. **Three scores, never blended.** FSRS gives you memory only. We separate **memory ≠ performance ≠
   readiness**, each an honest **range** (illustrated with a `CalibrationStrip`). Button → open dashboard.
5. **Honesty / give-up rule.** We refuse a readiness number without evidence: **≥200 graded reviews ·
   ≥50% topic coverage · interval width below threshold**, plus the full evidence panel. "No track
   record yet" is the correct output at n≈1.

## 3. The interactive interleaving demo

- **Input:** a fixed, deterministic `EXAMPLE_QUEUE` of ~12 `(card_id, leaf_tag)` pairs in FSRS
  priority order, deliberately blocked-ish (e.g. runs of `differential_single`, `integral_single`,
  then `linear`, `real_analysis`) so the reorder is visible. Authentic taxonomy leaves.
- **Compute:** `build_interleave_demo(k, w)` calls the vendored `interleave(EXAMPLE_QUEUE, k=k, w=w)`
  and `blocked_order(EXAMPLE_QUEUE)`, returning both orders + `{adjacency_dispersion,
  blocked_dispersion, displacement_mean, displacement_max, used_fallback}`.
- **Render:** two rows of chips (Blocked = FSRS order, Interleaved), each chip coloured by
  confusable cluster/leaf; the two live metrics (adjacency dispersion `blocked → interleaved`,
  mean/max FSRS displacement); **K** (avoid last K clusters, 0–3) and **W** (displacement bound, 1–6)
  sliders that re-POST to recompute through the **real** algorithm. Caption states the load-bearing
  invariant: *shown multiset == due set — FSRS fields untouched; W bounds starvation.*
- **Clamp** `k`/`w` server-side to sane ranges (k∈[0,5], w∈[1,12]) so a hand-crafted POST can't do
  anything pathological (still pure — worst case a different ordering of the example).

## 4. Files

**New (anki fork, `agent/gre-method-page`):**
- `anki/qt/aqt/gre/interleave.py` — vendored copy of `pipeline/interleave.py`.
- `anki/qt/aqt/gre/method_data.py` — `EXAMPLE_QUEUE`, `CLUSTER_COLORS` (leaf→palette index),
  `build_interleave_demo(k, w)`.
- `anki/qt/aqt/gre_method.py` — `GreMethod` QDialog + `setup_gre_method_menu()`.
- `anki/ts/routes/gre-method/+page.svelte` — page shell + 5 sections.
- `anki/ts/routes/gre-method/Interleave.svelte` — interactive viz.
- `anki/ts/routes/gre-method/lib.ts` + `lib.test.ts` — pure helpers (chip model, metric formatting) + vitest.
- `anki/qt/tests/test_gre_method.py` — endpoint read-only + demo correctness + menu wiring.

**Modified (anki fork):**
- `anki/qt/aqt/mediasrv.py` — `is_sveltekit_page("gre-method")` + read-only `gre_method_interleave` handler → POST `/_anki/greMethodInterleave`.
- `anki/qt/aqt/webview.py` — `AnkiWebViewKind.GRE_METHOD` + `_profileForPage` api-access allowlist entry.
- `anki/qt/aqt/main.py` — Tools-menu hook via `main_window_did_init`.

**Outer repo (`agent/gre-method-page`, outer):**
- `docs/superpowers/specs/2026-07-05-algorithm-explainer-page-design.md` — this spec.
- `tests/test_interleave_sync.py` — vendored-copy drift guard (`anki/qt/aqt/gre/interleave.py` == `pipeline/interleave.py`).
- `docs/codebase/qt.md` (+ `docs/codebase/INDEX.md`) — new "How-it-differs page" section, SHA bumped.
- `docs/STATUS.md` — one line on merge.
- anki submodule pin bump → the new fork sha.

## 5. Testing

- **`test_gre_method.py` (aqt):** `build_interleave_demo` returns both orders as the same multiset as
  `EXAMPLE_QUEUE`; interleaved adjacency dispersion ≥ blocked; `displacement_max ≤ w`; k/w clamps
  hold; the mediasrv handler is registered, returns the demo dict, and **never touches `col`** (call
  it on a fresh collection and assert undo count + `quick_check` unchanged, mirroring the dashboard
  read-only test). Menu action is added at init.
- **`lib.test.ts` (vitest):** pure chip-model + metric formatting (e.g. a null/absent metric never
  renders a fabricated number; percentage formatting; cluster→colour mapping is stable).
- **Outer `test_interleave_sync.py`:** the vendored copy is byte-identical to `pipeline/interleave.py`
  (drift guard), mirroring `test_exam_items_sync.py`/`test_taxonomy_sync.py`.
- **GUI smoke (human-gated):** per the "adding a new webview page" gotchas — force a bundle rebuild
  (`rm -rf out/sveltekit out/sveltekit.marker && ./run`), confirm the page loads (route registered),
  the interleaving demo POSTs successfully (api-access allowlist present → no 403), the chips reorder
  and metrics update on the K/W sliders, and the two buttons open the dashboard/exam dialogs.
  (Offscreen QtWebEngine has not initialised headlessly on this machine, so the click-through is the
  one manual step; everything below it is unit-verified.)

## 6. Lane, risks, follow-ups

- **Lane:** fast lane. Qt-UI-only in the `anki` fork + outer docs/tests. No engine/proto/scheduler.
- **Risks:** (a) new SvelteKit route needs the three edits (route + `is_sveltekit_page` + loader) **and**
  the webview api-access allowlist, or the page is blank / POST 403s — both covered in Files/Testing.
  (b) stale bundle: force the rebuild. (c) vendored-copy drift: the outer sync test guards it.
- **Follow-ups (out of scope):** a "run it on my real due queue" mode (needs a read-only queue
  endpoint); an Android parity page; wiring the interleaved↔blocked **toggle** into the reviewer (that
  touches the review loop → engine lane, separate).

## 7. Acceptance criteria

- Tools ▸ "How this app differs from FSRS" opens a page with the five sections in a coherent,
  dashboard-consistent visual system.
- The interleaving section reorders an example queue **through the real vendored algorithm**, shows
  blocked vs interleaved with cluster-coloured chips, and updates adjacency-dispersion + displacement
  metrics live as K/W change.
- The endpoint is strictly read-only (no `col` access, no `OpChanges`); vendored copy matches source.
- `test_gre_method.py` + `lib.test.ts` + `test_interleave_sync.py` green; SvelteKit bundle builds; docs
  updated in the same change (SHA bumped). No engine/submodule-code change beyond the pin bump.
