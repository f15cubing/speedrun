# Deck Scale-Up (~5,000 cards) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scale the study deck to **~5,000+ unique, deterministic** cards — widen/extend the thin computational templates, raise per-leaf counts, and expand the hand-authored conceptual set from ~20 to ~60 reference-sourced original questions — keeping the coverage + ≥50% calculus gates, byte-stable output, no AI, no engine change.

**Architecture:** Pure-Python changes to `pipeline/`. `generate_deck.py` gains wider parameter ranges + new template sub-types for the three thin leaves (differential_equations, applications, integral_multi); `GENERATED_COUNTS` / `generate_mcq.MCQ_COUNTS` are rebalanced to the target scale; a capacity/uniqueness test guards distinctness; `conceptual_cards.yaml` grows by ~40 verified original items; `coverage_report`/docs reflect the new scale. Everything stays seeded + gated.

**Tech Stack:** Python 3.9, `sympy==1.14.0`, `genanki==0.13.1`, `PyYAML==6.0.3`, `pytest==8.4.2` (pinned in `pipeline/requirements.txt`).

## Global Constraints

- **No AI / no model calls.** Computational = SymPy-templated; conceptual = human-authored, reference-sourced, gated. (PRD §9/§11.)
- **No ETS items.** Author original questions on standard topics; `src` names the concept source; never transcribe an ETS/copyrighted item. (PRD §11/§12.)
- **Determinism.** Same `--seed` ⇒ identical ordered list; content-derived GUIDs; fixed timestamp. Scaling is a build-time count knob.
- **Coverage gate hard:** 17/17 leaves, **≥50% calculus** by card count, exactly one valid leaf tag per card; non-zero exit on violation.
- **Uniqueness:** every stem distinct; a leaf's template capacity must exceed its count or the build fails loud (never pad with duplicates).
- **No engine change → fast lane.** `pipeline/` only; nothing under `anki/` or `Anki-Android/`.
- **Eval firewall intact:** the `eval/bank` `assert_firewall()` must still pass (don't duplicate an eval stem in the study deck).
- **Spec:** `docs/superpowers/specs/2026-07-02-deck-scale-up-design.md`.

## Environment

- Worktree: `/Users/felipecaicedo/Desktop/alpha/speedrun-worktrees/deck-scale`, branch `agent/deck-scale`.
- Venv: `python3 -m venv .venv && . .venv/bin/activate && pip install -r pipeline/requirements.txt`. Tests: `python -m pytest pipeline/tests -q`.
- Current per-leaf helpers in `generate_deck.py`: `_poly`, `_nonzero`, `_s`, `x`, `y`, `_leaf_rng`, `DEFAULT_SEED`, the `_gen_<leaf>` builders, and `GENERATED_COUNTS`. MCQ counts in `generate_mcq.py::MCQ_COUNTS`.

---

## Task 1: Widen the thin templates (capacity for scale)

**Goal/deliverable:** `differential_equations`, `applications`, `integral_multi` gain wider ranges + a new sub-type each, so each can emit hundreds of distinct stems. All keys remain SymPy-correct.

**Files:**
- Modify: `pipeline/generate_deck.py` (`_gen_differential_equations`, `_gen_applications`, `_gen_integral_multi`)
- Test: `pipeline/tests/test_template_capacity.py` (new)

- [ ] **Step 1: Write the failing capacity + correctness test**

```python
# pipeline/tests/test_template_capacity.py
"""Thin templates can emit many distinct, correct stems after widening."""
import random

import sympy as sp

import generate_deck as gd

x = gd.x


def _distinct_stems(fn, n=300, seed=42):
    rng = random.Random(seed)
    seen = set()
    for _ in range(n * 8):
        front, _back = fn(rng)
        seen.add(front)
        if len(seen) >= n:
            break
    return len(seen)


def test_thin_templates_have_capacity():
    assert _distinct_stems(gd._gen_differential_equations, 300) >= 300
    assert _distinct_stems(gd._gen_applications, 300) >= 300
    assert _distinct_stems(gd._gen_integral_multi, 300) >= 300


def test_differential_equations_key_is_correct():
    rng = random.Random(1)
    for _ in range(50):
        front, back = gd._gen_differential_equations(rng)
        assert "y(x) =" in back  # general solution stated


def test_applications_key_is_correct():
    rng = random.Random(2)
    for _ in range(50):
        front, back = gd._gen_applications(rng)
        assert back  # non-empty, well-formed
```

- [ ] **Step 2: Run to verify it fails**

Run: `. .venv/bin/activate && python -m pytest pipeline/tests/test_template_capacity.py -q`
Expected: FAIL — current thin templates can't produce 300 distinct stems.

- [ ] **Step 3: Widen the three generators in `pipeline/generate_deck.py`**

Replace `_gen_differential_equations` with (wider `k`, added trig + power sub-types):
```python
def _gen_differential_equations(rng):
    kind = rng.choice(["separable_poly", "separable_poly", "exponential", "trig", "power"])
    if kind == "separable_poly":
        f = _poly(rng, x, 1, 4)
        sol = sp.integrate(f, x)
        front = "Solve the differential equation (general solution):\n\ny'(x) = {}".format(_s(f))
        back = "y(x) = {} + C".format(_s(sol))
    elif kind == "exponential":
        k = _nonzero(rng, -9, 9)
        front = "Solve the differential equation (general solution):\n\ny'(x) = {}*y(x)".format(k)
        back = "y(x) = C*exp({}*x)".format(k)
    elif kind == "trig":
        a = _nonzero(rng, -6, 6)
        k = rng.randint(2, 6)
        f = a * sp.sin(k * x)
        sol = sp.integrate(f, x)
        front = "Solve the differential equation (general solution):\n\ny'(x) = {}".format(_s(f))
        back = "y(x) = {} + C".format(_s(sol))
    else:  # power
        n = rng.randint(2, 7)
        a = _nonzero(rng, -6, 6)
        f = a * x ** n
        sol = sp.integrate(f, x)
        front = "Solve the differential equation (general solution):\n\ny'(x) = {}".format(_s(f))
        back = "y(x) = {} + C".format(_s(sol))
    return front, back
```

Replace `_gen_applications` with (wider ranges + `average_value` sub-type):
```python
def _gen_applications(rng):
    kind = rng.choice(["tangent_slope", "area", "average_value"])
    if kind == "tangent_slope":
        f = _poly(rng, x, 2, 4)
        a = rng.randint(-6, 6)
        slope = sp.diff(f, x).subs(x, a)
        front = ("Find the slope of the tangent line to\n\nf(x) = {}\n\n"
                 "at x = {}.".format(_s(f), a))
        back = "slope = f'({}) = {}".format(a, _s(slope))
    elif kind == "area":
        c1 = rng.randint(1, 6); c2 = rng.randint(1, 6)
        f = sp.expand(c1 * x ** 2 + c2)
        a = rng.randint(0, 3); b = a + rng.randint(1, 4)
        area = sp.integrate(f, (x, a, b))
        front = ("Find the area under\n\nf(x) = {}\n\nfrom x = {} to x = {}.".format(_s(f), a, b))
        back = "area = {}".format(_s(area))
    else:  # average_value
        c1 = rng.randint(1, 6); c2 = rng.randint(-6, 6)
        f = sp.expand(c1 * x + c2)
        a = rng.randint(0, 3); b = a + rng.randint(1, 5)
        avg = sp.integrate(f, (x, a, b)) / (b - a)
        front = ("Find the average value of\n\nf(x) = {}\n\non [{}, {}].".format(_s(f), a, b))
        back = "average value = {}".format(_s(avg))
    return front, back
```

Replace `_gen_integral_multi` coefficient/bound ranges (wider):
```python
def _gen_integral_multi(rng):
    c1 = _nonzero(rng, 1, 6)
    c2 = rng.randint(0, 5)
    c3 = rng.randint(0, 5)
    px = rng.randint(0, 3)
    py = rng.randint(0, 3)
    g = sp.expand(c1 * x ** px * y ** py + c2 * x + c3 * y)
    a = rng.randint(1, 4)
    b = rng.randint(1, 4)
    inner = sp.integrate(g, (x, 0, a))
    value = sp.integrate(inner, (y, 0, b))
    front = ("Evaluate the double integral over R = [0, {}] \u00d7 [0, {}]:\n\n"
             "\u222c_R ({}) dA".format(a, b, _s(g)))
    back = "\u222c_R ({}) dA = {}".format(_s(g), _s(value))
    return front, back
```

- [ ] **Step 4: Run to verify it passes** — `python -m pytest pipeline/tests/test_template_capacity.py -q` → PASS. Then full suite `python -m pytest pipeline/tests -q` → PASS (determinism/coverage still green; existing seed changes card content but tests are structural). If `test_recompute` pins specific values, update its expected sample.

- [ ] **Step 5: Commit** — `git add pipeline/generate_deck.py pipeline/tests/test_template_capacity.py && git commit -m "feat(pipeline): widen thin templates (DE/applications/integral_multi) for scale"`

---

## Task 2: Rebalance counts to ~5,000 + scale/uniqueness test

**Files:**
- Modify: `pipeline/generate_deck.py` (`GENERATED_COUNTS`), `pipeline/generate_mcq.py` (`MCQ_COUNTS`, raise `max_attempts` if needed)
- Test: `pipeline/tests/test_scale.py` (new)

- [ ] **Step 1: Write the failing scale test**

```python
# pipeline/tests/test_scale.py
"""The deck scales to ~5000 unique cards, calc >= 50%, deterministic."""
import build_deck
import coverage_report
import taxonomy


def test_deck_has_target_scale():
    cards = build_deck.load_all_cards(seed=42)
    assert len(cards) >= 5000


def test_all_stems_distinct():
    cards = build_deck.load_all_cards(seed=42)
    keys = [build_deck._card_identity(c) for c in cards]
    assert len(keys) == len(set(keys)), "duplicate card identity"


def test_calc_weight_and_coverage_hold_at_scale():
    cards = build_deck.load_all_cards(seed=42)
    s = coverage_report.assert_coverage(cards)
    assert s["calc_weight"] >= 0.50
    assert s["num_covered"] == 17


def test_scale_is_deterministic():
    assert build_deck.load_all_cards(seed=42) == build_deck.load_all_cards(seed=42)
```

- [ ] **Step 2: Run to verify it fails** — `python -m pytest pipeline/tests/test_scale.py -q` → FAIL (only ~104 cards).

- [ ] **Step 3: Set the counts.** In `generate_deck.py`:
```python
GENERATED_COUNTS = {
    "differential_single": 700,
    "integral_single": 700,
    "differential_multi": 700,
    "integral_multi": 500,
    "differential_equations": 500,
    "applications": 500,
    "elementary": 250,
    "linear": 250,
    "number_theory": 250,
    "probability_stats": 250,
    "numerical": 250,
}
```
In `generate_mcq.py`: bump each `MCQ_COUNTS` leaf to `125` and ensure the generation loop's `max_attempts` scales (e.g. `max_attempts = max(2000, count * 60)`); do the same for the flashcard generator loop in `generate_deck.generate_cards` if it has a fixed cap.

> Capacity note: these counts sit within each widened template's distinct space (Task 1 proved ≥300 for the thin three; the poly/trig calculus templates and det2/det3, gcd/mod/divisors, mean/choose/prob all exceed 700). If any leaf raises `RuntimeError: could not generate N`, lower that leaf's count or widen its ranges further — do not pad.

- [ ] **Step 4: Run to verify it passes** — `python -m pytest pipeline/tests/test_scale.py -q` → PASS; then `python -m pytest pipeline/tests -q` → PASS.

- [ ] **Step 5: Commit** — `git add pipeline/generate_deck.py pipeline/generate_mcq.py pipeline/tests/test_scale.py && git commit -m "feat(pipeline): scale generated deck to ~5000 cards (calc>=50%, unique)"`

---

## Task 3: Expand the conceptual set to ~60 (reference-sourced, verified)

**Files:**
- Modify: `pipeline/conceptual_cards.yaml` (append ~40 verified original items)
- Test: `pipeline/tests/test_conceptual_gate.py` (add a count assertion)

- [ ] **Step 1: Add a count test** to `pipeline/tests/test_conceptual_gate.py`:
```python
def test_conceptual_set_is_expanded():
    cards = build_deck.load_conceptual_cards()
    assert len(cards) >= 55
```

- [ ] **Step 2: Author ~40 more original conceptual records** across the conceptual leaves, ~8–10 per leaf, using the ETS content outline (spec §Reference) to choose standard topics. For each topic, look up the standard fact from a reputable reference (textbook / MIT OCW / Wikipedia math article), then write an **original** question + answer. Suggested topics per leaf:
  - `additional::real_analysis`: uniform vs pointwise continuity, Bolzano–Weierstrass, Taylor series of e^x/sin, monotone convergence, sup/inf, differentiable ⇒ continuous.
  - `additional::topology`: open/closed sets, compactness (open-cover def), connectedness, continuity via preimages, closure/interior, metric spaces.
  - `additional::complex`: Cauchy–Riemann, analytic ⇒ harmonic, residues, roots of unity, |e^{iθ}|=1, contour integral of 1/z.
  - `additional::geometry`: triangle/circle facts, distance/midpoint, conic definitions, volume of sphere, law of cosines.
  - `additional::discrete`: pigeonhole, inclusion–exclusion, C(n,k) identities, graph handshake, logic equivalences, countability.
  - `algebra::abstract`: Lagrange, cyclic groups, order of elements, ring/field definitions, homomorphism kernel, ideals.
  - **Linear-algebra concepts** (tag `algebra::linear`, complementing the determinant computational template): eigenvalue definition, rank–nullity, invertibility ⇔ det≠0, vector-space axioms, basis/dimension, linear independence.

  Record shape (flashcard or `format: mcq`), all fields required by the gate:
```yaml
  - leaf_tag: "topic::algebra::linear"
    format: mcq
    question: "A square matrix A is invertible if and only if:"
    options:
      - "det(A) != 0"
      - "A is symmetric"
      - "A has a zero row"
      - "trace(A) = 0"
      - "A equals its transpose"
    correct_index: 0
    explanation: "A is invertible iff det(A) != 0 (equivalently, full rank / trivial null space)."
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
    source: "original (standard linear-algebra fact; ETS content outline: linear algebra)"
```
  Rules: **original wording**; exactly one unambiguous correct option + four plausible wrong; MCQ has exactly 5 distinct options; `source` names the concept reference and **never** an ETS item; correctness double-checked. Avoid duplicating a stem already in the eval bank (`eval/bank/items.yaml`).

- [ ] **Step 3: Run the gate + count tests** — `python -m pytest pipeline/tests/test_conceptual_gate.py -q` → PASS (incl. `test_conceptual_set_is_expanded`). Also verify the eval firewall still holds:
```bash
python -c "import sys; sys.path[:0]=['eval/bank','pipeline']; import loader; loader.assert_firewall(); print('firewall OK')"
```
Expected: `firewall OK` (if a collision is reported, reword the offending conceptual card).

- [ ] **Step 4: Commit** — `git add pipeline/conceptual_cards.yaml pipeline/tests/test_conceptual_gate.py && git commit -m "feat(pipeline): expand conceptual set to ~60 reference-sourced verified items"`

---

## Task 4: End-to-end build + docs + PR

**Files:**
- Modify: `pipeline/pipeline.md`, `pipeline/README.md`, `docs/codebase/INDEX.md`

- [ ] **Step 1: Full suite + end-to-end build**
```bash
. .venv/bin/activate
python -m pytest pipeline/tests -q                 # all PASS
time python pipeline/build_deck.py --seed 42        # writes .apkg, gate PASSED
ls -la pipeline/dist/gre-study-deck.apkg            # record size
```
Expected: total ≥ ~5,000 cards, `By format: flashcard=..., mcq=...`, 17/17 leaves, calc ≥ 50%, `Coverage gate PASSED`, exit 0. Record card count, generation+pack time, and `.apkg` size for the PR (these feed sub-project B).

- [ ] **Step 2: Update docs** — `pipeline/pipeline.md` (new scale + widened templates + capacity/scale tests + conceptual sourcing note), `pipeline/README.md` ("What gets built": ~5,000 cards, conceptual ~60 reference-sourced), `docs/codebase/INDEX.md` (bump the pipeline row's "Last verified"/scope note). Update the trailing `Last verified against:` line.

- [ ] **Step 3: Commit + open the fast-lane PR**
```bash
git add pipeline/pipeline.md pipeline/README.md docs/codebase/INDEX.md
git commit -m "docs(pipeline): document ~5000-card scale + conceptual expansion"
git push -u origin agent/deck-scale
gh pr create --base main --head agent/deck-scale --title "Deck scale-up: ~5,000 unique cards + expanded conceptual set" --body "<intent note + card count + .apkg size + test evidence; fast lane; no engine change>"
```

---

## Self-Review (plan vs. spec)

- **Spec coverage:** §1 W1 → Tasks 1–2; W2 → Task 3; §2 allocation → Task 2 counts; §3 capacity → Task 1 + the capacity test; §4 conceptual sourcing → Task 3 (rules + topics + `source`); §5 tests → Tasks 1–4 (capacity, scale, determinism, conceptual gate/count, firewall, e2e); §6 perf/footprint → Task 4 Step 1 (record size/time); §7 out-of-scope honored (no bundling/engine); §8 acceptance → Task 4. No gaps.
- **Placeholder scan:** template code + tests + record shape are inline; the conceptual authoring (Task 3) is bounded by the gate + count test + firewall + the concrete topic list and worked record.
- **Consistency:** `GENERATED_COUNTS` keys match `taxonomy` leaf names; `_card_identity` (from build_deck) reused for the distinctness test; MCQ `max_attempts` scaling matches the count bump; conceptual records match the existing gate schema.

## Execution Handoff

Implement via superpowers:subagent-driven-development (fresh subagent per task + review) or executing-plans (inline). Ship as a fast-lane PR. **Two execution options — which?** (1) Subagent-driven (recommended), (2) Inline.
