# Content-Generation Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing `pipeline/` so it produces exam-format **MCQ** cards with **auto-generated, templated distractors** (computational lane) and enforces a **human-verification gate** on conceptual cards — feeding the Performance surface (PRD §7b/§8a/§12a) without any AI or any engine change.

**Architecture:** Pure-Python additions to the already-merged `pipeline/` package. A new `distractors.py` turns a correct SymPy answer + operation-specific wrong answers into validated 5-option sets; a new `generate_mcq.py` builds deterministic computational MCQ items; `conceptual_cards.yaml` gains a `status`/attribution block that the loader enforces; `build_deck.py` packs a second genanki note type ("GRE MCQ"); `coverage_report.py` reports per-format counts. Everything stays seeded and byte-stable.

**Tech Stack:** Python 3.9, `sympy==1.14.0`, `genanki==0.13.1`, `PyYAML==6.0.3`, `pytest==8.4.2` (all already pinned in `pipeline/requirements.txt`).

## Global Constraints

- **No AI / no model calls anywhere in this plan.** Content is templated (SymPy) or human-authored. (PRD §9, spec "Global constraints".)
- **No ETS items.** All content original; never import official ETS material. (PRD §11/§12.)
- **No engine / Rust change.** This is a content/data-model change *above* the engine; do not touch `anki/` or `Anki-Android/`. (PRD §8a, D1 ceiling.)
- **Exactly one leaf tag per card** — a valid `topic::<bucket>::<leaf>` from `taxonomy.py` (PRD Appendix A). Enforced by the coverage gate.
- **Re-runnable & deterministic** — fixed `--seed` (default 42) ⇒ identical ordered card list; content-derived genanki ids/GUIDs; fixed package timestamp. (PRD §11.)
- **Coverage gate stays hard** — ≥ 50% leaf coverage (we ship all 17) and ≥ 50% calculus card weight, or the build exits non-zero.
- **Two corpora stay firewalled** — this plan only touches the **study deck** corpus; do not pull from or write to `eval/goldset/`. (PRD §12.)
- **Ships via `shipping-changes`** — implement in a dedicated git worktree on branch `agent/pipeline-mcq-content`, open a real `gh` PR, and have a **different** agent verify it against `pr-checklist.md` (base gate only — no engine extra gate). Commit frequently to the branch; never to `main`.
- **Spec reference:** `docs/superpowers/specs/2026-06-30-content-generation-and-timed-ui-design.md` (§2–§4).

## Decision notes (carried from the spec, made concrete here)

- **MCQ computational coverage in THIS plan is a representative set** — `differential_single`, `integral_single` (expression answers) + `linear`, `number_theory` (integer answers) — enough to prove both distractor styles and feed Performance. Extending the same pattern to the remaining computational leaves is a documented follow-up (Task 7), not part of this plan.
- **Verification gate semantics:** `build_deck` (dev) **skips `draft` cards with a printed warning** and **hard-fails** only on a card that claims `status: verified` without attribution, or has an unknown `status`. A separate strict check (`assert_all_verified`, run by the coverage CLI / PR gate) **hard-fails on any `draft`** so unverified content can never reach a production build. This keeps day-to-day builds unblocked while guaranteeing the production gate. (Honors the user's status-field choice; flag to owner if stricter "fail on any draft everywhere" is preferred.)

---

## Task 1: Distractor engine (`pipeline/distractors.py`)

**Files:**
- Create: `pipeline/distractors.py`
- Test: `pipeline/tests/test_distractors.py`

**Interfaces:**
- Consumes: `sympy` only.
- Produces:
  - `class InsufficientDistractors(Exception)`
  - `make_options(rng, correct, wrong_exprs, n_options=5) -> (options: list[str], correct_index: int)` — `correct` and items of `wrong_exprs` are SymPy expressions; `rng` is a `random.Random`. Returns stringified options (via `sympy.sstr`) with the correct answer at a deterministic index; raises `InsufficientDistractors` if fewer than `n_options-1` distinct, defined wrongs ≠ key can be formed.
  - `generic_variants(expr) -> list` — ordered operation-agnostic error variants.

- [ ] **Step 1: Write the failing test**

```python
# pipeline/tests/test_distractors.py
"""Unit tests for the distractor engine (pipeline/distractors.py)."""

import random

import sympy as sp

import distractors

X = sp.Symbol("x")


def test_make_options_has_five_distinct_with_correct_at_index():
    rng = random.Random(0)
    correct = sp.sympify("x**2 + 3")
    wrongs = [sp.sympify("x**2 - 3"), sp.sympify("2*x"), sp.sympify("x**3 + 3")]
    options, idx = distractors.make_options(rng, correct, wrongs)
    assert len(options) == 5
    assert len(set(options)) == 5, options
    assert options[idx] == sp.sstr(correct)


def test_make_options_is_deterministic_for_fixed_seed():
    correct = sp.Integer(7)
    wrongs = [sp.Integer(13), sp.Integer(1)]
    a = distractors.make_options(random.Random(5), correct, wrongs)
    b = distractors.make_options(random.Random(5), correct, wrongs)
    assert a == b


def test_make_options_drops_wrongs_equal_to_key():
    rng = random.Random(0)
    correct = sp.sympify("x + 1")
    # First wrong equals the key (after simplify) and must be discarded.
    wrongs = [sp.sympify("1 + x"), sp.sympify("x - 1")]
    options, idx = distractors.make_options(rng, correct, wrongs)
    assert options.count(sp.sstr(correct)) == 1


def test_make_options_raises_when_too_few_distinct():
    rng = random.Random(0)
    correct = sp.Integer(0)
    # All variants collapse to 0 / duplicates -> cannot form 4 distinct wrongs.
    with __import__("pytest").raises(distractors.InsufficientDistractors):
        distractors.make_options(rng, correct, [sp.Integer(0)], n_options=12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_distractors.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'distractors'`.

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/distractors.py
"""Deterministic MCQ option assembly + common-error distractors.

Given a correct SymPy answer and operation-specific wrong answers (also SymPy),
assemble exactly ``n_options`` stringified options with the correct answer at a
deterministic index. Wrong answers are validated to be defined, mutually distinct,
and != the key (symbolic equality). When the supplied wrongs are too few, generic
common-error transforms top them up; if still too few, ``InsufficientDistractors``
is raised so the caller can skip/redraw the instance.

No randomness beyond the supplied ``rng`` (used only to place/order options), so
output is byte-stable for a fixed seed. No AI, no network.
"""

from __future__ import annotations

import sympy as sp

N_OPTIONS = 5


class InsufficientDistractors(Exception):
    """Raised when fewer than ``n_options - 1`` valid distractors can be formed."""


def _equal(a, b):
    """Symbolic equality that never raises (falls back to string compare)."""
    try:
        return sp.simplify(a - b) == 0
    except (TypeError, ValueError, sp.SympifyError, AttributeError):
        return str(a) == str(b)


def generic_variants(expr):
    """Operation-agnostic common-error variants, in a fixed deterministic order."""
    return [-expr, 2 * expr, expr + 1, expr - 1]


def make_options(rng, correct, wrong_exprs, n_options=N_OPTIONS):
    """Return ``(options, correct_index)``.

    ``correct`` and items of ``wrong_exprs`` are SymPy expressions. Options are
    rendered with ``sympy.sstr`` (matching the deck's ``generate_deck._s``).
    """
    needed = n_options - 1
    correct_str = sp.sstr(correct)

    chosen_strs = []
    seen = {correct_str}
    for cand in list(wrong_exprs) + generic_variants(correct):
        if cand is None:
            continue
        if _equal(cand, correct):
            continue
        cand_str = sp.sstr(cand)
        if cand_str in seen:
            continue
        seen.add(cand_str)
        chosen_strs.append(cand_str)
        if len(chosen_strs) == needed:
            break

    if len(chosen_strs) < needed:
        raise InsufficientDistractors(
            "only {} distinct distractors for key {!r}".format(len(chosen_strs), correct_str)
        )

    options = list(chosen_strs)
    correct_index = rng.randint(0, n_options - 1)
    options.insert(correct_index, correct_str)
    return options, correct_index
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_distractors.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/distractors.py pipeline/tests/test_distractors.py
git commit -m "feat(pipeline): deterministic MCQ distractor engine"
```

---

## Task 2: Computational MCQ generator (`pipeline/generate_mcq.py`)

**Files:**
- Create: `pipeline/generate_mcq.py`
- Test: `pipeline/tests/test_mcq_generation.py`

**Interfaces:**
- Consumes: `taxonomy`, `distractors.make_options` / `InsufficientDistractors`, and the pure helpers `_poly`, `_nonzero`, `_leaf_rng`, `_s`, `x` from `generate_deck`.
- Produces:
  - `MCQ_COUNTS: dict[str, int]` — leaf name → MCQ card count.
  - `generate_mcq_cards(seed=42) -> list[dict]` — each dict is
    `{"leaf_tag": str, "format": "mcq", "question": str, "options": list[str], "correct_index": int, "explanation": str}`, in canonical taxonomy/leaf order, deterministic for a fixed seed.

- [ ] **Step 1: Write the failing test**

```python
# pipeline/tests/test_mcq_generation.py
"""MCQ generation: determinism, well-formedness, and correct-key integrity."""

import sympy as sp

import generate_mcq
import taxonomy


def test_generates_expected_leaves_and_counts():
    cards = generate_mcq.generate_mcq_cards(seed=42)
    assert cards, "no MCQ cards produced"
    by_leaf = {}
    for c in cards:
        by_leaf[c["leaf_tag"]] = by_leaf.get(c["leaf_tag"], 0) + 1
    for leaf, n in generate_mcq.MCQ_COUNTS.items():
        assert by_leaf[taxonomy.TAG_BY_LEAF[leaf]] == n


def test_every_mcq_is_wellformed():
    for c in generate_mcq.generate_mcq_cards(seed=42):
        assert c["format"] == "mcq"
        assert taxonomy.validate_leaf_tag(c["leaf_tag"])
        assert len(c["options"]) == 5
        assert len(set(c["options"])) == 5, c
        assert 0 <= c["correct_index"] < 5


def test_correct_option_is_the_real_answer_for_linear():
    # 2x2 determinant: the option at correct_index must equal a*d - b*c parsed back.
    tag = taxonomy.TAG_BY_LEAF["linear"]
    cards = [c for c in generate_mcq.generate_mcq_cards(seed=42) if c["leaf_tag"] == tag]
    assert cards
    for c in cards:
        key = sp.sympify(c["options"][c["correct_index"]])
        # Re-derive from the explanation's stated value (independent of option order).
        stated = sp.sympify(c["explanation"].split("=")[-1].strip())
        assert sp.simplify(key - stated) == 0, c


def test_is_deterministic_for_fixed_seed():
    assert generate_mcq.generate_mcq_cards(seed=42) == generate_mcq.generate_mcq_cards(seed=42)
    assert generate_mcq.generate_mcq_cards(seed=42) != generate_mcq.generate_mcq_cards(seed=7)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_mcq_generation.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'generate_mcq'`.

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/generate_mcq.py
"""Seeded generator for exam-format MCQ cards (computational lane).

Reuses the pure problem-construction helpers from ``generate_deck`` and the
distractor engine to emit deterministic 5-option multiple-choice items for a
representative set of computational leaves. Each builder returns
``(stem, correct_expr, wrong_exprs, explanation)``; the correct answer and the
operation-specific wrong answers are all SymPy, so every option is computed (no
hand-typed answers, no model calls). Output is byte-stable for a fixed seed.

These cards drive the Performance surface (PRD §7b/§8a); they review through the
same FSRS loop as flashcards (no engine change).
"""

from __future__ import annotations

import sympy as sp

import distractors
import taxonomy
from generate_deck import DEFAULT_SEED, _leaf_rng, _nonzero, _poly, _s, x

# Cards per MCQ leaf. Two calculus + two algebra leaves keeps the merged deck's
# calculus weight comfortably >= 50% (see coverage_report).
MCQ_COUNTS = {
    "differential_single": 4,
    "integral_single": 4,
    "linear": 4,
    "number_theory": 4,
}


def _mcq_differential_single(rng):
    f = _poly(rng, x, 2, 4)
    correct = sp.diff(f, x)
    wrongs = [
        sp.integrate(f, x),              # swapped operation (integrated)
        sp.diff(sp.diff(f, x), x),       # differentiated twice
    ]
    stem = "Differentiate with respect to x:\n\nf(x) = {}".format(_s(f))
    explanation = "f'(x) = {}".format(_s(correct))
    return stem, correct, wrongs, explanation


def _mcq_integral_single(rng):
    f = _poly(rng, x, 1, 3)
    correct = sp.integrate(f, x)         # antiderivative; options omit + C
    wrongs = [
        sp.diff(f, x),                   # swapped operation (differentiated)
        f,                               # forgot to integrate
    ]
    stem = (
        "Evaluate the indefinite integral (give the antiderivative, omit + C):"
        "\n\n\u222b ({}) dx".format(_s(f))
    )
    explanation = "F(x) = {} + C".format(_s(correct))
    return stem, correct, wrongs, explanation


def _mcq_linear(rng):
    a = _nonzero(rng, -6, 6)
    b = rng.randint(-6, 6)
    c = rng.randint(-6, 6)
    d = _nonzero(rng, -6, 6)
    correct = sp.Integer(a * d - b * c)
    wrongs = [
        sp.Integer(a * d + b * c),       # added instead of subtracted
        sp.Integer(a * b - c * d),       # multiplied the wrong pairs
    ]
    stem = "Compute the determinant of the 2x2 matrix:\n\n[[{}, {}], [{}, {}]]".format(
        a, b, c, d
    )
    explanation = "det = ({})*({}) - ({})*({}) = {}".format(a, d, b, c, _s(correct))
    return stem, correct, wrongs, explanation


def _mcq_number_theory(rng):
    a = rng.randint(12, 120)
    b = rng.randint(12, 120)
    g = sp.igcd(a, b)
    correct = sp.Integer(g)
    wrongs = [
        sp.Integer(a * b // g),          # lcm instead of gcd
        sp.Integer(min(a, b)),           # picked the smaller input
    ]
    stem = "Compute the greatest common divisor:\n\ngcd({}, {})".format(a, b)
    explanation = "gcd({}, {}) = {}".format(a, b, _s(correct))
    return stem, correct, wrongs, explanation


_MCQ_BUILDERS = {
    "differential_single": _mcq_differential_single,
    "integral_single": _mcq_integral_single,
    "linear": _mcq_linear,
    "number_theory": _mcq_number_theory,
}

# Emit in canonical taxonomy order so the card list is stable.
_MCQ_LEAVES_IN_ORDER = tuple(
    leaf.leaf for leaf in taxonomy.LEAVES if leaf.leaf in MCQ_COUNTS
)


def generate_mcq_cards(seed=DEFAULT_SEED):
    """Return the ordered list of computational MCQ card dicts (deterministic)."""
    cards = []
    for leaf in _MCQ_LEAVES_IN_ORDER:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        builder = _MCQ_BUILDERS[leaf]
        count = MCQ_COUNTS[leaf]
        # Distinct RNG namespace from the flashcard generator (":mcq" suffix) so
        # adding MCQ never perturbs the existing flashcard determinism.
        rng = _leaf_rng(seed, tag + "::mcq")
        seen = set()
        attempts = 0
        max_attempts = max(400, count * 400)
        while len(seen) < count:
            attempts += 1
            if attempts > max_attempts:
                raise RuntimeError(
                    "could not generate {} MCQ cards for {}".format(count, leaf)
                )
            stem, correct, wrongs, explanation = builder(rng)
            if stem in seen:
                continue
            try:
                options, correct_index = distractors.make_options(rng, correct, wrongs)
            except distractors.InsufficientDistractors:
                continue
            seen.add(stem)
            cards.append(
                {
                    "leaf_tag": tag,
                    "format": "mcq",
                    "question": stem,
                    "options": options,
                    "correct_index": correct_index,
                    "explanation": explanation,
                }
            )
    return cards


def _main():
    cards = generate_mcq_cards()
    print("generated {} MCQ cards".format(len(cards)))
    for card in cards[:2]:
        print("\n--- {} ---".format(card["leaf_tag"]))
        print(card["question"])
        for i, opt in enumerate(card["options"]):
            mark = " (correct)" if i == card["correct_index"] else ""
            print("  {}. {}{}".format("ABCDE"[i], opt, mark))


if __name__ == "__main__":
    _main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_mcq_generation.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/generate_mcq.py pipeline/tests/test_mcq_generation.py
git commit -m "feat(pipeline): seeded computational MCQ generator with templated distractors"
```

---

## Task 3: Conceptual verification gate (extend YAML + loader)

**Files:**
- Modify: `pipeline/conceptual_cards.yaml` (add a verification block to every entry; add the file header note)
- Modify: `pipeline/build_deck.py` (`load_conceptual_cards`) + add `assert_all_verified`
- Test: `pipeline/tests/test_conceptual_gate.py`

**Interfaces:**
- Consumes: `yaml`, existing `CONCEPTUAL_YAML`.
- Produces:
  - `load_conceptual_cards(path=CONCEPTUAL_YAML, strict=False) -> list[dict]` — returns built card dicts for `status: verified` entries only; **skips** `draft` entries (prints a warning) unless `strict=True` (then raises); **always raises** on a `verified` entry missing `verified_by`/`verified_on`/`source`, or any unknown `status`.
  - `assert_all_verified(path=CONCEPTUAL_YAML)` — raises `AssertionError` if any entry is not `verified` (the production gate).

- [ ] **Step 1: Write the failing test**

```python
# pipeline/tests/test_conceptual_gate.py
"""The human-verification gate on conceptual cards (PRD §12a)."""

import textwrap

import pytest

import build_deck


def _write(tmp_path, body):
    p = tmp_path / "cards.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(p)


def test_only_verified_cards_are_loaded(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q1"
            back: "A1"
            status: verified
            verified_by: "fc"
            verified_on: "2026-06-30"
            source: "original"
          - leaf_tag: "topic::algebra::abstract"
            front: "Q2 (draft)"
            back: "A2"
            status: draft
            verified_by: ""
            verified_on: ""
            source: "original"
        """,
    )
    cards = build_deck.load_conceptual_cards(path=path)
    fronts = [c["front"] for c in cards]
    assert fronts == ["Q1"]  # the draft is skipped


def test_verified_without_attribution_hard_fails(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q"
            back: "A"
            status: verified
            verified_by: ""
            verified_on: "2026-06-30"
            source: "original"
        """,
    )
    with pytest.raises(ValueError):
        build_deck.load_conceptual_cards(path=path)


def test_unknown_status_hard_fails(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q"
            back: "A"
            status: approved
            verified_by: "fc"
            verified_on: "2026-06-30"
            source: "original"
        """,
    )
    with pytest.raises(ValueError):
        build_deck.load_conceptual_cards(path=path)


def test_strict_mode_fails_on_any_draft(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q"
            back: "A"
            status: draft
            verified_by: ""
            verified_on: ""
            source: "original"
        """,
    )
    with pytest.raises(ValueError):
        build_deck.load_conceptual_cards(path=path, strict=True)


def test_production_yaml_is_fully_verified():
    # The committed production file must contain zero drafts.
    build_deck.assert_all_verified()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_conceptual_gate.py -q`
Expected: FAIL — `load_conceptual_cards()` has no `strict`/`path` validation yet and `assert_all_verified` does not exist (`AttributeError`).

- [ ] **Step 3a: Replace `load_conceptual_cards` and add `assert_all_verified` in `pipeline/build_deck.py`**

Replace the existing `load_conceptual_cards` function (currently `pipeline/build_deck.py:87-101`) with:

```python
_VALID_STATUSES = ("draft", "verified")
_REQUIRED_WHEN_VERIFIED = ("verified_by", "verified_on", "source")


def _conceptual_entry_to_card(entry):
    """Convert a raw YAML entry to a card dict (flashcard or mcq)."""
    fmt = str(entry.get("format", "flashcard"))
    base = {"leaf_tag": str(entry["leaf_tag"]), "format": fmt}
    if fmt == "mcq":
        options = [str(o) for o in entry["options"]]
        base.update(
            {
                "question": str(entry["question"]),
                "options": options,
                "correct_index": int(entry["correct_index"]),
                "explanation": str(entry.get("explanation", "")),
            }
        )
    else:
        base.update({"front": str(entry["front"]), "back": str(entry["back"])})
    return base


def load_conceptual_cards(path=CONCEPTUAL_YAML, strict=False):
    """Load conceptual cards, enforcing the human-verification gate (PRD §12a).

    Returns built card dicts for ``status: verified`` entries only. ``draft``
    entries are skipped with a warning (or, when ``strict=True``, raise). A
    ``verified`` entry missing any of ``verified_by``/``verified_on``/``source``,
    or any unknown ``status``, always raises ``ValueError``.
    """
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    raw = data["cards"] if isinstance(data, dict) else data

    cards = []
    skipped = []
    for index, entry in enumerate(raw):
        status = str(entry.get("status", "")).strip()
        if status not in _VALID_STATUSES:
            raise ValueError(
                "conceptual card #{} ({!r}) has invalid status {!r}; "
                "expected one of {}".format(
                    index, entry.get("front") or entry.get("question"), status,
                    _VALID_STATUSES,
                )
            )
        if status == "draft":
            if strict:
                raise ValueError(
                    "conceptual card #{} is still a draft (strict mode)".format(index)
                )
            skipped.append(index)
            continue
        missing = [k for k in _REQUIRED_WHEN_VERIFIED if not str(entry.get(k, "")).strip()]
        if missing:
            raise ValueError(
                "verified conceptual card #{} is missing attribution: {}".format(
                    index, ", ".join(missing)
                )
            )
        cards.append(_conceptual_entry_to_card(entry))

    if skipped:
        print(
            "NOTE: skipped {} unverified (draft) conceptual card(s): {}".format(
                len(skipped), skipped
            )
        )
    return cards


def assert_all_verified(path=CONCEPTUAL_YAML):
    """Production gate: raise if any conceptual card is not verified+attributed."""
    # strict=True raises on the first draft; verified-but-unattributed also raises.
    load_conceptual_cards(path=path, strict=True)
```

- [ ] **Step 3b: Add the verification block to every entry in `pipeline/conceptual_cards.yaml`**

For **each** of the 18 existing entries, add these four keys (the entries are all original, author-written, correct):

```yaml
    status: verified
    verified_by: "fc"
    verified_on: "2026-06-30"
    source: "original (standard textbook fact)"
```

Worked example — the first entry becomes:

```yaml
  - leaf_tag: "topic::algebra::abstract"
    front: "State Lagrange's theorem for finite groups, and give one immediate corollary about element orders."
    back: "If G is a finite group and H is a subgroup of G, then |H| divides |G|. Corollary: the order of every element g divides |G| (since g generates a cyclic subgroup of that order)."
    status: verified
    verified_by: "fc"
    verified_on: "2026-06-30"
    source: "original (standard textbook fact)"
```

Also update the file's top comment to mention the gate:

```yaml
# Hand-authored conceptual GRE-Math cards for the leaves that do not templatize.
# Fully original, mathematically correct, GRE-appropriate. No AI/model calls.
#
# VERIFICATION GATE (PRD §12a): every card MUST carry status: verified with a
# non-empty verified_by / verified_on / source, or the build hard-fails. Drafts
# (status: draft) are skipped by the dev build and rejected by the production
# gate (assert_all_verified). A human verifier is the only path to "verified".
#
# Each card carries EXACTLY ONE valid leaf tag topic::<bucket>::<leaf>.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_conceptual_gate.py -q`
Expected: PASS (5 passed). Then run the full suite to confirm no regression: `python -m pytest pipeline/tests -q` → all PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/build_deck.py pipeline/conceptual_cards.yaml pipeline/tests/test_conceptual_gate.py
git commit -m "feat(pipeline): enforce human-verification gate on conceptual cards"
```

---

## Task 4: Conceptual MCQ records (YAML format: mcq)

**Files:**
- Modify: `pipeline/conceptual_cards.yaml` (append 2 verified conceptual MCQ cards)
- Test: `pipeline/tests/test_conceptual_gate.py` (add one case)

**Interfaces:**
- Consumes: `load_conceptual_cards` + `_conceptual_entry_to_card` from Task 3 (already handles `format: mcq`).
- Produces: conceptual cards with `format: mcq`, `options` (5), `correct_index`, `explanation`.

- [ ] **Step 1: Write the failing test**

Append to `pipeline/tests/test_conceptual_gate.py`:

```python
def test_conceptual_mcq_records_load_wellformed():
    cards = build_deck.load_conceptual_cards()
    mcq = [c for c in cards if c.get("format") == "mcq"]
    assert len(mcq) >= 2
    for c in mcq:
        assert len(c["options"]) == 5
        assert len(set(c["options"])) == 5
        assert 0 <= c["correct_index"] < 5
        assert c["explanation"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_conceptual_gate.py::test_conceptual_mcq_records_load_wellformed -q`
Expected: FAIL with `assert 0 >= 2` (no conceptual MCQ yet).

- [ ] **Step 3: Append two verified conceptual MCQ cards to `pipeline/conceptual_cards.yaml`**

```yaml
  # --- conceptual MCQ (format: mcq) --------------------------------------
  - leaf_tag: "topic::additional::real_analysis"
    format: mcq
    question: "Which statement about the harmonic series sum_{n>=1} 1/n is true?"
    options:
      - "It diverges."
      - "It converges to 1."
      - "It converges to e."
      - "It converges to a finite value greater than 2."
      - "It converges only in the Cesaro sense."
    correct_index: 0
    explanation: "The harmonic series diverges (compare with the integral of 1/x = ln x -> infinity)."
    status: verified
    verified_by: "fc"
    verified_on: "2026-06-30"
    source: "original (standard analysis fact)"
  - leaf_tag: "topic::additional::discrete"
    format: mcq
    question: "How many subsets does a set with n elements have?"
    options:
      - "2^n"
      - "n^2"
      - "n!"
      - "2n"
      - "n^n"
    correct_index: 0
    explanation: "Each element is independently in or out of a subset: 2 choices for each of n elements -> 2^n."
    status: verified
    verified_by: "fc"
    verified_on: "2026-06-30"
    source: "original (standard combinatorics fact)"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest pipeline/tests/test_conceptual_gate.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/conceptual_cards.yaml pipeline/tests/test_conceptual_gate.py
git commit -m "feat(pipeline): add verified conceptual MCQ records"
```

---

## Task 5: "GRE MCQ" note type + build integration

**Files:**
- Modify: `pipeline/build_deck.py` (add `MCQ_MODEL`, `mcq_note_for`, dispatch in `note_for`, merge MCQ in `load_all_cards`, generalize `cards_content_hash`)
- Test: `pipeline/tests/test_mcq_notetype.py`

**Interfaces:**
- Consumes: `generate_mcq.generate_mcq_cards`, `genanki`, the card dict shapes from Tasks 2 & 4.
- Produces:
  - `MCQ_MODEL_ID`, `MCQ_MODEL` (genanki Model, 9 fields).
  - `mcq_note_for(card) -> genanki.Note`.
  - Updated `note_for(card)` dispatching on `card.get("format")`.
  - Updated `load_all_cards(seed)` returning `generated_flashcards + mcq_cards + conceptual_cards`.
  - Updated `cards_content_hash(cards)` handling both formats.

- [ ] **Step 1: Write the failing test**

```python
# pipeline/tests/test_mcq_notetype.py
"""The GRE MCQ note type packs correctly and carries exactly one topic tag."""

import build_deck
import taxonomy


def test_mcq_cards_present_in_merged_list():
    cards = build_deck.load_all_cards(seed=42)
    mcq = [c for c in cards if c.get("format") == "mcq"]
    assert len(mcq) >= 16  # 4 leaves x 4 computational + conceptual MCQ


def test_mcq_note_has_nine_fields_and_one_topic_tag():
    cards = build_deck.load_all_cards(seed=42)
    mcq = next(c for c in cards if c.get("format") == "mcq")
    note = build_deck.note_for(mcq)
    assert len(note.fields) == 9
    topic_tags = [t for t in note.tags if t.startswith(taxonomy.TAG_PREFIX + "::")]
    assert len(topic_tags) == 1
    assert taxonomy.validate_leaf_tag(topic_tags[0])


def test_mcq_correct_option_field_matches_index():
    cards = build_deck.load_all_cards(seed=42)
    for c in [c for c in cards if c.get("format") == "mcq"]:
        note = build_deck.note_for(c)
        # Field order: Question, A, B, C, D, E, CorrectOption, Explanation, LeafTag
        assert note.fields[6] == "ABCDE"[c["correct_index"]]


def test_content_hash_is_stable_with_mcq():
    a = build_deck.load_all_cards(seed=42)
    b = build_deck.load_all_cards(seed=42)
    assert build_deck.cards_content_hash(a) == build_deck.cards_content_hash(b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_mcq_notetype.py -q`
Expected: FAIL — `load_all_cards` has no MCQ cards yet (`assert ... >= 16`) and `note_for` cannot build a 9-field note.

- [ ] **Step 3a: Add the MCQ model after the existing `MODEL = genanki.Model(...)` block in `pipeline/build_deck.py`**

```python
MCQ_MODEL_ID = _stable_id("gre-speedrun::model::mcq-tagged::v1")

MCQ_MODEL = genanki.Model(
    MCQ_MODEL_ID,
    "GRE Math MCQ (leaf-tagged)",
    fields=[
        {"name": "Question"},
        {"name": "OptionA"},
        {"name": "OptionB"},
        {"name": "OptionC"},
        {"name": "OptionD"},
        {"name": "OptionE"},
        {"name": "CorrectOption"},
        {"name": "Explanation"},
        {"name": "LeafTag"},
    ],
    templates=[
        {
            "name": "MCQ",
            "qfmt": (
                "{{Question}}<br><br>"
                "A. {{OptionA}}<br>B. {{OptionB}}<br>C. {{OptionC}}<br>"
                "D. {{OptionD}}<br>E. {{OptionE}}"
            ),
            "afmt": (
                '{{FrontSide}}<hr id="answer">'
                "Correct: {{CorrectOption}}<br><br>{{Explanation}}"
                '<br><br><span style="color:#888;font-size:0.8em">{{LeafTag}}</span>'
            ),
        }
    ],
    css=(
        ".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
        "font-size:18px;line-height:1.5;color:#111;background:#fff;"
        "text-align:left;padding:16px;white-space:pre-wrap;}"
    ),
)
```

- [ ] **Step 3b: Add `mcq_note_for` and dispatch in `note_for` (replace the existing `note_for`, `pipeline/build_deck.py:124-132`)**

```python
def note_for(card):
    """Build a genanki Note (basic or MCQ) with a content-derived, stable GUID."""
    if card.get("format") == "mcq":
        return mcq_note_for(card)
    guid = genanki.guid_for(card["front"], card["back"], card["leaf_tag"])
    return genanki.Note(
        model=MODEL,
        fields=[_to_html(card["front"]), _to_html(card["back"]), card["leaf_tag"]],
        tags=[card["leaf_tag"]],
        guid=guid,
    )


def mcq_note_for(card):
    """Build a genanki Note for an MCQ card (GRE MCQ model)."""
    options = card["options"]
    correct_letter = "ABCDE"[card["correct_index"]]
    fields = (
        [_to_html(card["question"])]
        + [_to_html(opt) for opt in options]
        + [correct_letter, _to_html(card.get("explanation", "")), card["leaf_tag"]]
    )
    guid = genanki.guid_for(card["question"], *options, card["leaf_tag"])
    return genanki.Note(
        model=MCQ_MODEL,
        fields=fields,
        tags=[card["leaf_tag"]],
        guid=guid,
    )
```

- [ ] **Step 3c: Merge MCQ into `load_all_cards` and generalize `cards_content_hash` (`pipeline/build_deck.py`)**

Add the import near the other module imports (after `import generate_deck`):

```python
import generate_mcq
```

Replace `load_all_cards` (`pipeline/build_deck.py:104-112`) with:

```python
def load_all_cards(seed=generate_deck.DEFAULT_SEED):
    """Return the merged, canonically ordered card list.

    Order is deterministic: generated computational flashcards (taxonomy order),
    then computational MCQ cards (taxonomy order), then conceptual cards
    (YAML order, verified only).
    """
    generated = generate_deck.generate_cards(seed=seed)
    mcq = generate_mcq.generate_mcq_cards(seed=seed)
    conceptual = load_conceptual_cards()
    return generated + mcq + conceptual
```

Replace `cards_content_hash` (`pipeline/build_deck.py:115-121`) with:

```python
def _card_identity(card):
    """Stable identity string for a card, covering both formats."""
    if card.get("format") == "mcq":
        parts = [card["leaf_tag"], "mcq", card["question"]]
        parts.extend(card["options"])
        parts.append(str(card["correct_index"]))
        return "\x1f".join(parts)
    return "\x1f".join((card["leaf_tag"], card["front"], card["back"]))


def cards_content_hash(cards):
    """Stable SHA-256 over the ordered identity of every card (both formats)."""
    hasher = hashlib.sha256()
    for card in cards:
        hasher.update((_card_identity(card) + "\x1e").encode("utf-8"))
    return hasher.hexdigest()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest pipeline/tests/test_mcq_notetype.py -q`
Expected: PASS (4 passed). Then full suite: `python -m pytest pipeline/tests -q` → all PASS (existing determinism/tagging tests still green because flashcard dicts are unchanged and MCQ notes carry exactly one topic tag).

- [ ] **Step 5: Commit**

```bash
git add pipeline/build_deck.py pipeline/tests/test_mcq_notetype.py
git commit -m "feat(pipeline): GRE MCQ note type + merge MCQ into deterministic build"
```

---

## Task 6: Per-format coverage reporting + end-to-end build + docs

**Files:**
- Modify: `pipeline/coverage_report.py` (`summarize` adds `by_format`; `format_report` prints it; CLI runs `assert_all_verified`)
- Modify: `pipeline/tests/test_coverage.py` (add per-format assertion + calc-weight-still-holds)
- Modify: `pipeline/pipeline.md`, `pipeline/README.md`, `docs/codebase/INDEX.md`

**Interfaces:**
- Consumes: the merged card list from `build_deck.load_all_cards`.
- Produces: `summary["by_format"] -> {"flashcard": int, "mcq": int}`; coverage CLI also asserts the production verification gate.

- [ ] **Step 1: Write the failing test**

Append to `pipeline/tests/test_coverage.py`:

```python
def test_summary_reports_per_format_counts():
    cards = build_deck.load_all_cards(seed=42)
    summary = coverage_report.summarize(cards)
    assert summary["by_format"]["mcq"] >= 16
    assert summary["by_format"]["flashcard"] >= 1


def test_calc_weight_still_passes_with_mcq():
    cards = build_deck.load_all_cards(seed=42)
    summary = coverage_report.assert_coverage(cards)
    assert summary["calc_weight"] >= taxonomy.MIN_CALCULUS_CARD_WEIGHT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest pipeline/tests/test_coverage.py::test_summary_reports_per_format_counts -q`
Expected: FAIL with `KeyError: 'by_format'`.

- [ ] **Step 3a: Add `by_format` to `summarize` in `pipeline/coverage_report.py`**

Inside `summarize`, after `calc_cards = 0` add `by_format = {}`, and inside the loop (after computing `tag`) count formats. Replace the loop body + return dict so it reads:

```python
def summarize(cards):
    """Return a dict of coverage statistics for a list of card dicts."""
    per_leaf = {tag: 0 for tag in taxonomy.LEAF_TAGS}
    invalid = []
    calc_cards = 0
    by_format = {}
    for index, card in enumerate(cards):
        fmt = card.get("format", "flashcard") if isinstance(card, dict) else "?"
        by_format[fmt] = by_format.get(fmt, 0) + 1
        tag = card.get("leaf_tag") if isinstance(card, dict) else None
        if not taxonomy.validate_leaf_tag(tag):
            invalid.append((index, tag))
            continue
        per_leaf[tag] += 1
        if taxonomy.bucket_of(tag) == taxonomy.CALCULUS_BUCKET:
            calc_cards += 1
    total = len(cards)
    covered = [tag for tag, n in per_leaf.items() if n > 0]
    return {
        "total": total,
        "per_leaf": per_leaf,
        "covered_leaves": covered,
        "num_covered": len(covered),
        "num_leaves": len(taxonomy.LEAF_TAGS),
        "leaf_coverage": (len(covered) / len(taxonomy.LEAF_TAGS)) if taxonomy.LEAF_TAGS else 0.0,
        "calc_cards": calc_cards,
        "calc_weight": (calc_cards / total) if total else 0.0,
        "by_format": by_format,
        "invalid": invalid,
    }
```

- [ ] **Step 3b: Print formats in `format_report`** — after the "Calculus weight" line block, add:

```python
    lines.append(
        "By format:        " + ", ".join(
            "{}={}".format(k, summary["by_format"][k]) for k in sorted(summary["by_format"])
        )
    )
```

- [ ] **Step 3c: Make the coverage CLI also assert the verification gate** — in `coverage_report.main`, after `cards = load_all_cards(seed=args.seed)` add:

```python
    from build_deck import assert_all_verified
    assert_all_verified()
```

- [ ] **Step 4: Run tests + the real end-to-end build**

Run (unit): `python -m pytest pipeline/tests -q`
Expected: all PASS.

Run (end-to-end, in the venv):
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r pipeline/requirements.txt
python pipeline/build_deck.py --seed 42
```
Expected: prints the coverage report including a `By format: flashcard=..., mcq=...` line, `Coverage gate PASSED. Build complete.`, exit 0, and writes `pipeline/dist/gre-study-deck.apkg`.

Run (determinism of the artifact path is covered by tests; verify gate CLI):
```bash
python pipeline/coverage_report.py --seed 42
```
Expected: report prints, `Coverage gate PASSED.`, exit 0.

- [ ] **Step 5a: Update `pipeline/pipeline.md`** — under "Public interface" add entries for `distractors.py`, `generate_mcq.py`, `MCQ_MODEL`/`mcq_note_for`, `assert_all_verified`, and the `status`/attribution YAML keys; under "Gotchas & invariants" add the verification gate + MCQ determinism (`tag + "::mcq"` RNG namespace) notes; under "Related tests" add the four new test files. Update the trailing `Last verified against:` line to the new branch HEAD after the final commit.

- [ ] **Step 5b: Update `pipeline/README.md`** — in the "Files" table add `distractors.py`, `generate_mcq.py`; in "What gets built" note that MCQ cards (new "GRE MCQ" note type) are generated for `differential_single`, `integral_single`, `linear`, `number_theory` plus conceptual MCQ, and that conceptual cards are gated by `status: verified`.

- [ ] **Step 5c: Update `docs/codebase/INDEX.md`** — bump the `Study-deck + tagging pipeline` row's "Last verified" to the new branch HEAD; move the "MCQ study surface (Performance)" row note to reference that the content-side (note type + generation) is now built in `pipeline/` (the in-app review template remains planned).

- [ ] **Step 6: Commit**

```bash
git add pipeline/coverage_report.py pipeline/tests/test_coverage.py pipeline/pipeline.md pipeline/README.md docs/codebase/INDEX.md
git commit -m "feat(pipeline): per-format coverage report + verification-gate CLI + docs"
```

---

## Task 7 (follow-up, documented — NOT implemented here)

Extend the MCQ computational lane to the remaining templatable leaves (`differential_multi`, `integral_multi`, `differential_equations`, `applications`, `elementary`, `probability_stats`, `numerical`) using the exact Task 2 pattern (a `_mcq_<leaf>` builder returning `(stem, correct_expr, wrong_exprs, explanation)` + an `MCQ_COUNTS` entry). Keep calculus weight ≥ 50% as MCQ counts grow. This is intentionally out of scope to keep this plan reviewable; open it as a separate PR.

---

## Self-Review

**1. Spec coverage (spec §2–§4):**
- §2 templated computational / "infinite" via build-time scale → existing generator + `MCQ_COUNTS` knob (Tasks 2, 7). ✓
- §3 conceptual verification gate (status fields, hard-fail, AI-forward-compatible) → Task 3 (`status`/attribution + `load_conceptual_cards`/`assert_all_verified`). ✓
- §4.1 MCQ note type/data model → Task 5 (`MCQ_MODEL`, 9 fields, same FSRS loop, one topic tag). ✓
- §4.2 computational distractors via common-error transforms (deterministic, ≠ key, dedupe, skip-if-<4) → Tasks 1 + 2. ✓
- §4.3 conceptual distractors human-authored → Task 4. ✓
- §5 timed UI, §6 interleaving → **deferred companion plans** (stated up front; need the desktop build + eval bank). ✓ (explicitly out of scope)
- §8 tests / §9 acceptance (deterministic one-command build, gate green, MCQ reviews via FSRS, docs+INDEX) → Tasks 5–6. ✓

**2. Placeholder scan:** No "TBD"/"add error handling"/"similar to Task N". The one uniform YAML edit (Task 3b) is shown with a worked before/after and the exact 4-key block; the gate test fails if any entry lacks it. Task 7 is explicitly a non-implemented follow-up, not a placeholder in the build. ✓

**3. Type consistency:** Card dict shapes are consistent across tasks — flashcards `{front, back, leaf_tag}`; MCQ `{leaf_tag, format:"mcq", question, options[5], correct_index, explanation}`. `make_options(rng, correct, wrong_exprs)` returns `(list[str], int)` and is consumed identically in Task 2. `note_for`/`mcq_note_for` field order (Question, A–E, CorrectOption, Explanation, LeafTag) matches `MCQ_MODEL` and the Task 5 test (`fields[6]` == correct letter). `load_conceptual_cards(path=, strict=)` signature matches all Task 3/4 call sites. `summarize(...)["by_format"]` matches Task 6 tests. ✓

---

## Execution Handoff

Implement in an isolated worktree (superpowers:using-git-worktrees) on branch `agent/pipeline-mcq-content`, then ship via the repo's `shipping-changes` skill (real `gh` PR, verified by a **different** agent against the base gate).

**Two execution options:**
1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration (superpowers:subagent-driven-development).
2. **Inline Execution** — execute tasks in this session with checkpoints (superpowers:executing-plans).
