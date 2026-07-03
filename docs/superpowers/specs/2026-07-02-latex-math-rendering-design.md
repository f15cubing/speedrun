# LaTeX Math Rendering — Design Spec

> Makes **all mathematical notation render as real math** (MathJax + `\(...\)` / `\[...\]`) across every
> surface that shows it — study-deck flashcards, MCQ cards, the Exam Mode webview, and the authored eval
> bank. Today every math string is ASCII SymPy output (`5*x**2`, `∫ (3*x + 4) dx`, `sum_{n=0}^{inf} x^n/n!`)
> and nothing is LaTeX-delimited. Companion to `docs/PRD.md` (§8a/§12), the content-generation spec
> (`2026-06-30-content-generation-and-timed-ui-design.md`), and the exam-mode redesign spec
> (`2026-07-02-ui-redesign-and-exam-mode-design.md`). Dated 2026-07-02.

## Status at time of writing

The study-deck pipeline (`pipeline/`, ~5,400 cards), the authored eval bank (`eval/bank/`, 80 items),
the desktop dashboard, Exam Mode (core `anki/qt/aqt/gre/exam.py` + `gre-exam` SvelteKit webview), and
deck auto-incorporation into both apps are all merged. **None of them render math** — the content is
ASCII SymPy (`sympy.sstr`) with occasional Unicode operators (`∫`, `∂`), and no `\(...\)`, `\[...\]`, or
`[latex]` delimiters exist anywhere. This spec adds LaTeX rendering as a **presentation-layer** change
with **no engine (`rslib`/proto/FFI) change** — Anki's reviewer and AnkiDroid already load MathJax 3.

## Decisions (locked with owner, 2026-07-02)

- **Scope = everything math is shown:** study-deck flashcards + MCQ cards (desktop + Android review), the
  Exam Mode webview items, and a **re-freeze of the authored eval bank**.
- **One renderer everywhere = MathJax** via `\(...\)` (inline) / `\[...\]` (display) delimiters. Cards use
  Anki's already-bundled MathJax (loaded by the reviewer on every card, desktop + AnkiDroid). The Exam
  Mode webview **reuses the same `mathjax` dependency** already in `anki/package.json` (`^3.1.2`) — **no
  KaTeX, no new package**. Chosen for "simplest + most offline-safe": zero new deps, identical rendering
  on cards and the exam page, proven offline on both platforms. (Supersedes the KaTeX assumption in the
  exam-mode redesign spec, which this spec updates.)
- **Correctness stays expression-level (Approach A):** math *truth* is a SymPy expression object; LaTeX is
  only its rendering. Generators keep building answers as SymPy expressions and render `\(sympy.latex(e)\)`
  for display; correctness tests validate the **expression objects** (`sympy.simplify(a-b)==0`), never the
  rendered string. No LaTeX-parsing round-trip, no note-type schema change.
- **`[latex]…[/latex]` image rendering is rejected** — it needs a LaTeX + `dvipng`/`dvisvgm` toolchain on
  every device, breaking Android and clean-machine installs (the "either app fails on a clean device →
  50% ceiling", PRD §3).
- **Conceptual LaTeX migration is a re-verification pass** — LaTeX-ifying a `status: verified` conceptual
  card touches its verified text, so each migrated record is re-checked and its `verified_on` bumped; the
  §12a hard-fail gate stays intact.

## Global constraints

- **No engine change.** MathJax is already in the engine; this is pipeline + eval + deck content +
  Qt/TS-UI-only (exam webview) + docs. Keeps the locked "exactly one engine change" ceiling (D1, PRD §5).
- **Offline-safe.** No CDN. Cards use the reviewer's vendored MathJax; the exam webview must bundle MathJax
  into its offline build exactly as the reviewer does.
- **Deterministic / re-runnable.** `sympy.latex()` is deterministic for a fixed seed; one command still
  rebuilds a byte-stable deck (PRD §11).
- **Two corpora stay firewalled** (PRD §12) — the study deck and the eval bank are re-rendered
  independently; the exam simulator still draws only from the (re-frozen) eval bank.
- **Taxonomy frozen** — LaTeX changes text only, never `topic::*` leaf tags.

---

## 1. Architecture & principle

**Math truth is a SymPy expression; LaTeX is its rendering; MathJax is the one renderer.**

A new helper module `pipeline/mathfmt.py` is the single formatting contract:

- `inline(expr) -> str` — returns `"\\(" + sympy.latex(expr) + "\\)"`.
- `block(expr) -> str` — returns `"\\[" + sympy.latex(expr) + "\\]"` for standalone display equations.
- A small set of **hand-math helpers** for the prose templates that build math strings by hand today
  rather than from a SymPy object (the Unicode `∫`/`∂` stems and the ODE template — see §2). These emit the
  same delimited LaTeX (e.g. `\(\displaystyle\int (\ldots)\,dx\)`, `\(\partial f/\partial x\)`).

Everything that displays math imports `mathfmt`, so conversion lives in one tested place. The reviewer and
AnkiDroid already typeset `\(...\)` / `\[...\]`; the exam webview is wired to do the same (§5).

## 2. Content pipeline (Lane A — computational)

Replace the ASCII formatter with `mathfmt` across the generators:

- `pipeline/generate_deck.py` — the `_s()` formatter (currently `sympy.sstr`) is retired for display; math
  is rendered via `mathfmt.inline`. Convert the hand-built stems:
  - `Differentiate with respect to x: f(x) = …` → prose + `\(f(x) = …\)`.
  - `∫ (…) dx` (Unicode) → `\(\displaystyle\int (\ldots)\,dx\)`; back `F(x) = … + C` → `\(F(x) = … + C\)`.
  - `∂f/∂x` (Unicode) → `\(\partial f/\partial x\)`.
  - the exponential ODE template (`y'(x) = {}*y(x)`, `y(x) = C*exp({}*x)`) is rebuilt so the math is a
    SymPy expression rendered via `mathfmt` (or hand-authored delimited LaTeX with a covering test).
- `pipeline/generate_mcq.py` — stems + explanations use `mathfmt` identically.
- `pipeline/distractors.py` — option strings render via `mathfmt.inline(expr)`. **Dedup and "≠ key"
  checks keep comparing SymPy expression objects** (as today) — never the LaTeX strings — so distractor
  integrity (4 distinct, all ≠ key) is unchanged.

Prose stays prose; only math spans get delimiters.

## 3. Correctness strategy (protecting the SymPy guarantees)

`pipeline/tests/test_recompute.py` currently re-parses card backs with `sympy.sympify` — impossible once a
back is `\(f'(x) = 10 x\)`. Refactor so correctness is checked on **expression objects, not markup**:

- Generators expose the ground-truth SymPy object(s) for each card in the in-memory card dict under a
  **test-only key that is never written to the note** (preferred over re-running the seeded generator
  inside the test, which is a fallback only if threading the object through is impractical for a template).
- `test_recompute.py` asserts `sympy.simplify(answer_expr - sympy.diff(f, x)) == 0` (and the integral
  analogue), validating the math rather than its rendering.
- `test_distractors.py` — expected option format updated to `mathfmt.inline(...)`; the distinctness/≠-key
  assertions stay expression-based.
- `test_determinism.py`, `test_tagging.py`, `test_template_capacity.py`, `test_mcq_generation.py`,
  `test_scale.py` — expected-string assertions updated to the LaTeX forms. Determinism still holds
  (`sympy.latex()` is deterministic for a fixed seed).
- New `pipeline/tests/test_mathfmt.py` — unit tests for `inline`/`block`/hand-math helpers (delimiters
  present, known expressions → known LaTeX).

## 4. Conceptual cards (Lane B — human-verified)

Hand-migrate the ~57 authored records in `pipeline/conceptual_cards.yaml` from informal ASCII
(`sum_{n=0}^{inf} x^n/n!`, `sqrt((x2-x1)^2 + …)`, `e^(i*pi)`, `theta`, `lambda`) to delimited LaTeX,
wrapping **only the math spans** inside each prose sentence (front, back, `options`, `explanation`).

- Treated as a **re-verification pass** (§12a): each migrated record is re-checked for correctness and
  rendering, and its `verified_on` is bumped (attribution preserved). The build's hard-fail on
  `draft`/unattributed records (`build_deck.py` / `coverage_report.py`) is unchanged.
- `test_conceptual_gate.py` stays green; add a check that no migrated field still contains bare ASCII math
  markers outside delimiters where feasible (best-effort lint, not a hard gate — prose legitimately
  contains letters).

## 5. Eval bank + Exam Mode (re-freeze + wire the renderer)

- `eval/bank/generate_eval.py` inherits `mathfmt` (it shares the Lane-A generators). Regenerate and
  **re-freeze** `eval/bank/items.yaml` (80 items). The P0/P3 partitions and item IDs are preserved via the
  fixed seed; `eval/bank/loader.py` schema validation and the leakage checks (PRD §11) must still pass.
- **Re-vendor** `anki/qt/aqt/gre/exam_items.json` from the re-frozen bank; the outer
  `test_exam_items_sync.py` guard enforces the vendored copy matches `eval/bank/`.
- **Wire MathJax into the `gre-exam` SvelteKit route** (`+page`, `ItemView` (5×A–E), `Navigator` review
  grid, `Results`): import the existing `mathjax` dependency and call `MathJax.typesetPromise([node])` on
  the item container each time an item mounts/changes, so stems, the five options, and explanations
  typeset. Match the reviewer's MathJax config (`anki/ts/mathjax/index.ts`).
- **Offline bundling risk (explicit task):** confirm MathJax is bundled into the exam webview's offline
  build (no CDN), the same way the reviewer vendors it (`anki/qt/aqt/reviewer.py` loads
  `js/vendor/mathjax/tex-chtml-full.js`). If SvelteKit tree-shaking or CSP blocks it, vendor the same
  bundle the reviewer uses.

## 6. Templates, rebuild, re-bundle, version bump

- `pipeline/build_deck.py` — the genanki models need **no** MathJax `<script>` tags (the reviewer loads
  MathJax already). Fix one gotcha: `_to_html()` currently `html.escape()`s each field, turning `<` / `&`
  inside LaTeX (e.g. `a < b`, matrix `&` alignment) into entities. Verify these round-trip through MathJax
  (DOM text decodes `&lt;`→`<`), or stop escaping the trusted build-time math and add a regression test.
- Rebuild the `.apkg` (`python pipeline/build_deck.py --seed 42`), run `make deck-asset` to re-sync the
  bundled decks in both apps (`anki/qt/aqt/gre/data/gre-study-deck.apkg` +
  `Anki-Android/.../assets/gre-study-deck.apkg`; `make deck-asset-check` enforces), and **bump
  `gre_deck_version`** so existing installs re-import the re-rendered cards through the auto-import path
  (add/update by content GUID, `with_scheduling=false` — scheduling history preserved).

## 7. Tests

- **Pipeline:** expression-level correctness (`test_recompute` on objects); `test_mathfmt`; determinism
  (same seed → identical LaTeX); every card still has exactly one valid leaf tag; distractor
  distinctness/≠-key intact.
- **Escaping regression:** a `<`-containing item and a matrix (`&`-containing) item render to valid MathJax
  output after `build_deck`.
- **Gate:** `test_conceptual_gate` green; a `draft`/unattributed record still fails the build.
- **Eval:** `loader.py` schema + leakage checks green on the re-frozen bank; `test_exam_items_sync` green
  after re-vendoring.
- **Exam webview:** `check:svelte` + a GUI smoke that the item container actually typesets (assert a
  rendered `<mjx-container>` in the DOM, or a headless snapshot), covering stem + options + explanation.
- **Manual visual pass:** one desktop review + one Android review of real cards confirm math renders
  (flashcard front/back + an MCQ), and one Exam Mode session renders items.

## 8. Docs (same PR, per `codebase-docs`)

- `pipeline/pipeline.md` — record that content is LaTeX-delimited and `mathfmt` is the formatting contract.
- `eval/bank/eval_bank.md` — note the re-freeze and LaTeX format.
- `docs/superpowers/specs/2026-07-02-ui-redesign-and-exam-mode-design.md` — switch its KaTeX assumption to
  MathJax reuse.
- `docs/codebase/INDEX.md` — update the pipeline / eval-bank / exam-mode rows and bump their
  `Last verified against` SHAs.
- Short PRD/spec note (§8a/§12) that all shown math is `\(...\)` / `\[...\]` LaTeX rendered by MathJax.

## 9. Shipping lane

**Fast lane** — no `rslib`/proto/FFI/scheduler change. It spans the `anki` fork submodule (exam-webview TS,
vendored `exam_items.json`, bundled `.apkg`) and the AnkiDroid bundled asset, plus `pipeline/`, `eval/`,
and docs. Self-review against the fast-lane checklist; ship as a normal `gh` PR; update `STATUS.md` on
merge.

## 10. Acceptance

- One documented command rebuilds a deterministic deck whose flashcard and MCQ fields are `\(...\)`-
  delimited LaTeX; the coverage gate and the conceptual verification gate stay green.
- Real cards render as typeset math in desktop review and in AnkiDroid review.
- The Exam Mode webview typesets stems, all five options, and explanations, offline.
- The eval bank is re-frozen (IDs/partitions stable) and the vendored `exam_items.json` matches.
- The bundled deck is re-synced in both apps and `gre_deck_version` is bumped; existing installs re-import
  cleanly with scheduling history preserved.
- All pipeline/eval/exam tests pass; docs + INDEX rows updated; STATUS line added.

## 10a. Implementation status (2026-07-02)

**Shipped in the pipeline lane (`agent/pipeline-latex-math`, in-repo, tests green):**

- `pipeline/mathfmt.py` — the formatting contract (+ `test_mathfmt.py`).
- `generate_deck.py`, `generate_mcq.py`, `distractors.py` — all study-deck flashcards + MCQ render
  LaTeX; ground-truth SymPy exposed via test-only `_expr`/`_correct_expr`; every affected test updated
  (recompute is now expression-level). Integral stems parenthesize the integrand.
- `conceptual_cards.yaml` — all ~57 records migrated to LaTeX as a re-verification pass (`verified_on`
  bumped 2026-07-02); the verification gate still passes.
- `build_deck.py` — documented the safe LaTeX/`html.escape` round-trip + `test_latex_escaping.py`.
- `eval/bank/generate_eval.py` — LaTeX authoring aid (frames as functions; no more `_s`).
- Deck rebuilds clean end-to-end (`build_deck.py --seed 42`): coverage + verification gates green.
- Docs: `pipeline.md`, `eval_bank.md`, this spec, and the exam-mode redesign spec (KaTeX → MathJax).

**Shipped in the exam-mode session (`anki` fork branch `agent/gre-exam-latex` → `a631ec3`; outer pin
bumped):**

- `eval/bank/items.yaml` (80-item freeze) migrated to LaTeX **together with** the vendored
  `anki/qt/aqt/gre/exam_items.json` — `tests/test_exam_items_sync.py` + the eval-bank suite (loader,
  firewall, P3 same-key) green. Computational strings converted via SymPy (round-trip-verified);
  prose/conceptual hand-mapped with an exhaustive coverage check.
- MathJax wired into the `gre-exam` SvelteKit route: `mathjax.ts` (sets config, dynamically imports the
  engine → offline code-split chunk, `typesetMath()`); `ItemView`/`Results` typeset their content;
  `+page` keys `ItemView` by item id (fresh DOM per item). Verified: `check:svelte`, `check:eslint`,
  format, and a clean SvelteKit **bundle build** whose exam page dynamically imports the local MathJax
  chunk (offline). **Live GUI smoke (open the app, run a mock, watch typeset) remains the one manual
  gate** — not runnable headlessly here.

**Still deferred (needs the `Anki-Android` fork submodule + an Android build):**

- `make deck-asset` re-sync of the bundled `.apkg` into both apps + bump `gre_deck_version`, so first-run
  auto-import ships the LaTeX study deck. The `Anki-Android` working tree is at upstream `v2.24.0`, not the
  fork commit with the importer.

## 11. Out of scope

- Adding KaTeX (decided against — MathJax reuse is simpler and offline-safe).
- `[latex]`-image rendering (rejected — toolchain dependency breaks mobile/clean installs).
- A math-input/editing UI for authors (authoring stays YAML + templated SymPy).
- Any change to FSRS, the review loop, sync, or the Mastery Query RPC (no engine change).
- The Friday AI card pipeline (its drafts will flow through the same `mathfmt` contract, but that work is
  separate, PRD §9).
