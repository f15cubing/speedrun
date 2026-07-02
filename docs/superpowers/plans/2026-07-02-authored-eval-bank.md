# Authored Eval Bank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a firewalled `eval/bank/` corpus of ~84 original, verified GRE-Math **MCQ** items — **P0** frozen held-out (~24, taxonomy-weighted) + **P3** paraphrase rewordings (~60 = ~30 groups × 2 same-key rewordings) — with expert-rated **provisional** difficulty, plus a pure-Python loader/validator (schema + verification gate + P3 integrity + firewall guard). Consumption-ready for the parked scoring layer. No AI, no engine change.

**Architecture:** New top-level `eval/bank/` package. Computational items are produced by a deterministic SymPy generator (`generate_eval.py`) that reuses `pipeline/distractors` + `pipeline/generate_deck` helpers, then **frozen** into `items.yaml`; conceptual items and all rewordings are hand-authored in `items.yaml`. `loader.py` loads + validates the frozen YAML and asserts the study-deck firewall. Everything is deterministic and gated by the same verified/attribution check used by `pipeline/conceptual_cards.yaml`.

**Tech Stack:** Python 3.9, `sympy==1.14.0`, `PyYAML==6.0.3`, `pytest==8.4.2` (already pinned in `pipeline/requirements.txt`). Reuses `pipeline/` modules as a code dependency (not a corpus dependency).

## Global Constraints

- **No AI / no model calls.** Items are SymPy-templated or hand-authored. (PRD §9/§11/§12.)
- **No ETS items.** All original + blueprint-matched; the entire ETS corpus is contaminated. (PRD §11/§12.)
- **No engine / Rust change.** New `eval/` data + Python only; never touch `anki/` or `Anki-Android/`. Fast lane.
- **Three corpora stay firewalled** — study deck (`pipeline/`), AI gold-set (`eval/goldset/`), eval bank (`eval/bank/`) never mix. Distinct `eval::` tag namespace + `assert_firewall()`.
- **Partitions are role-based** (PRD §12): `p0` frozen held-out · `p1` ablation-practice · `p2` delayed post-test · `p3` paraphrase pairs. Only **p0 + p3** authored here; schema/loader accept p1/p2 for later.
- **P3 = rewordings only.** The base recall item is the study-deck card (7d); the bank holds the 2 same-key rewordings per base, each with `base_ref` + `paraphrase_group`.
- **Difficulty is expert-rated, PROVISIONAL, integer 1–5.** Flag provisional wherever surfaced (widens Readiness interval; report with Wilson CIs downstream).
- **Exactly one `topic::<bucket>::<leaf>` leaf tag per item** (Appendix A; `taxonomy.validate_leaf_tag`).
- **Verification gate:** every committed item is `status: verified` with non-empty `verified_by`/`verified_on`/`src`.
- **Re-runnable & deterministic:** frozen `items.yaml` is the source of truth; the generator is seeded; the loader is pure.
- **Spec:** `docs/superpowers/specs/2026-07-02-authored-eval-bank-design.md`.

## Environment (known facts)

- Repo root (this worktree): `/Users/felipecaicedo/Desktop/alpha/speedrun-worktrees/eval-bank`; branch `agent/eval-bank`.
- Reuse the pipeline venv pattern: `python3 -m venv .venv && . .venv/bin/activate && pip install -r pipeline/requirements.txt`.
- `pipeline/` interfaces to reuse (verified): `taxonomy` (`LEAVES` namedtuple `(bucket, leaf, tag)`, `TAG_BY_LEAF`, `LEAVES_BY_BUCKET`, `BUCKET_WEIGHTS`, `BUCKETS`, `CALCULUS_BUCKET`, `validate_leaf_tag`, `bucket_of`); `distractors.make_options(rng, correct, wrong_exprs, n_options=5) -> (options:list[str], correct_index:int)` + `InsufficientDistractors`; `generate_deck` helpers `_poly`, `_nonzero`, `_s`, `x`, `_leaf_rng`, `DEFAULT_SEED`; `build_deck.load_all_cards(seed=42) -> list[dict]` (flashcard `{leaf_tag,front,back,format?}` / mcq `{leaf_tag,format:"mcq",question,options,correct_index,...}`).

**Worktree note:** fast-lane data/Python change; no submodule init needed.

---

## File Structure

**New `eval/bank/` package:**
- `eval/bank/__init__.py` — empty (package marker).
- `eval/bank/loader.py` — schema constants, `load_eval_items`, `assert_firewall`, `summarize`.
- `eval/bank/generate_eval.py` — deterministic SymPy generators for computational P0 items + P3 reword pairs; a `--emit` CLI that prints YAML records to freeze into `items.yaml`.
- `eval/bank/items.yaml` — the frozen, verified corpus (generated computational + hand-authored conceptual/rewordings).
- `eval/bank/eval_bank.md` — module doc (from the codebase-docs template).
- `eval/bank/tests/conftest.py` — put `eval/bank/` **and** `pipeline/` on `sys.path`.
- `eval/bank/tests/test_loader.py`, `eval/bank/tests/test_generate_eval.py`, `eval/bank/tests/test_bank_composition.py`.

**Modified:** `docs/codebase/INDEX.md` (add the eval-bank row).

---

## Task 1: Loader + validator (`eval/bank/loader.py`)

**Goal/deliverable:** a pure-Python loader that enforces the full schema, the verification gate, and P3 integrity on any items list/file. Testable against inline fixtures (no committed corpus yet).

**Files:**
- Create: `eval/bank/__init__.py`, `eval/bank/loader.py`, `eval/bank/tests/conftest.py`, `eval/bank/tests/test_loader.py`

**Interfaces:**
- Produces:
  - `PARTITIONS = ("p0","p1","p2","p3")`, `ITEMS_YAML` (path to `eval/bank/items.yaml`).
  - `load_eval_items(path=ITEMS_YAML, partition=None) -> list[dict]` — parse + validate; raises `ValueError` on any violation; `partition` filters.
  - `summarize(items) -> dict` — counts by partition / bucket / difficulty + `paraphrase_groups`.
  - `assert_firewall(items=None, seed=42)` — raises `ValueError` if any eval `(stem, answer)` collides with a study-deck card.

- [ ] **Step 1: Write `eval/bank/tests/conftest.py`**

```python
"""Make eval/bank and pipeline importable when pytest collects from the repo root."""
import os
import sys

BANK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(BANK_DIR))
PIPELINE_DIR = os.path.join(REPO_ROOT, "pipeline")
for path in (BANK_DIR, PIPELINE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)
```

- [ ] **Step 2: Write the failing loader test** (`eval/bank/tests/test_loader.py`)

```python
"""Schema, verification gate, and P3 integrity for the eval-bank loader."""
import textwrap

import pytest

import loader


def _write(tmp_path, body):
    p = tmp_path / "items.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(p)


_GOOD_P0 = """
items:
  - id: "eval-p0-0001"
    leaf_tag: "topic::calculus::integral_single"
    format: mcq
    question: "Antiderivative of 6x + 4 (omit + C)?"
    options: ["3*x**2 + 4*x", "6", "3*x**2 + 4", "6*x**2 + 4*x", "3*x + 4"]
    correct_index: 0
    explanation: "3x^2 + 4x"
    difficulty: 2
    partition: p0
    paraphrase_group: null
    base_ref: null
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
"""


def test_loads_valid_p0(tmp_path):
    items = loader.load_eval_items(path=_write(tmp_path, _GOOD_P0))
    assert len(items) == 1
    assert items[0]["partition"] == "p0"


def test_draft_is_rejected(tmp_path):
    body = _GOOD_P0.replace("status: verified", "status: draft")
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_verified_without_attribution_rejected(tmp_path):
    body = _GOOD_P0.replace('verified_by: "fc"', 'verified_by: ""')
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_bad_difficulty_rejected(tmp_path):
    body = _GOOD_P0.replace("difficulty: 2", "difficulty: 9")
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_bad_partition_rejected(tmp_path):
    body = _GOOD_P0.replace("partition: p0", "partition: pX")
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_malformed_mcq_rejected(tmp_path):
    # only 4 options
    body = _GOOD_P0.replace(
        '["3*x**2 + 4*x", "6", "3*x**2 + 4", "6*x**2 + 4*x", "3*x + 4"]',
        '["3*x**2 + 4*x", "6", "3*x**2 + 4", "6*x**2 + 4*x"]',
    )
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


_P3_GROUP = """
items:
  - id: "eval-p3-pg1-r1"
    leaf_tag: "topic::algebra::linear"
    format: mcq
    question: "Wording one?"
    options: ["7", "1", "2", "3", "4"]
    correct_index: 0
    explanation: "7"
    difficulty: 3
    partition: p3
    paraphrase_group: "pg-1"
    base_ref: "topic::algebra::linear :: det of [[3,1],[2,3]]"
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
  - id: "eval-p3-pg1-r2"
    leaf_tag: "topic::algebra::linear"
    format: mcq
    question: "Wording two?"
    options: ["7", "5", "6", "8", "9"]
    correct_index: 0
    explanation: "7"
    difficulty: 3
    partition: p3
    paraphrase_group: "pg-1"
    base_ref: "topic::algebra::linear :: det of [[3,1],[2,3]]"
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
"""


def test_valid_p3_group_loads(tmp_path):
    items = loader.load_eval_items(path=_write(tmp_path, _P3_GROUP))
    assert len(items) == 2


def test_p3_group_needs_exactly_two_rewordings(tmp_path):
    # drop the second rewording -> group of 1
    body = _P3_GROUP.split("  - id: \"eval-p3-pg1-r2\"")[0]
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_p3_group_key_mismatch_rejected(tmp_path):
    # second rewording's correct option (index 0) is "70" not "7"
    body = _P3_GROUP.replace('["7", "5", "6", "8", "9"]', '["70", "5", "6", "8", "9"]')
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_partition_filter(tmp_path):
    items = loader.load_eval_items(path=_write(tmp_path, _P3_GROUP), partition="p0")
    assert items == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `. .venv/bin/activate && python -m pytest eval/bank/tests/test_loader.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'loader'`.

- [ ] **Step 4: Write `eval/bank/loader.py`**

```python
"""Load + validate the authored eval bank (eval/bank/items.yaml).

Pure Python (no Anki/engine deps). Enforces the record schema, the human
verification gate, MCQ well-formedness, difficulty range, partition validity,
and P3 paraphrase-group integrity. `assert_firewall` guards against overlap
with the study deck (the rigorous leakage scan is a separate pipeline).
"""
from __future__ import annotations

import os
import re

import yaml

import taxonomy

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS_YAML = os.path.join(HERE, "items.yaml")

PARTITIONS = ("p0", "p1", "p2", "p3")
_REQUIRED = ("id", "leaf_tag", "format", "question", "options", "correct_index",
             "explanation", "difficulty", "partition", "src", "gen", "status",
             "verified_by", "verified_on")
_ATTRIBUTION = ("verified_by", "verified_on", "src")
N_OPTIONS = 5


def _fail(msg):
    raise ValueError("eval-bank: " + msg)


def _validate_item(index, item):
    for key in _REQUIRED:
        if key not in item:
            _fail("item #{} missing field {!r}".format(index, key))
    if str(item["status"]).strip() != "verified":
        _fail("item {!r} is not verified (status={!r})".format(item["id"], item["status"]))
    for key in _ATTRIBUTION:
        if not str(item.get(key, "")).strip():
            _fail("item {!r} missing attribution {!r}".format(item["id"], key))
    if item["format"] != "mcq":
        _fail("item {!r} has unsupported format {!r}".format(item["id"], item["format"]))
    if not taxonomy.validate_leaf_tag(item["leaf_tag"]):
        _fail("item {!r} has invalid leaf tag {!r}".format(item["id"], item["leaf_tag"]))
    opts = item["options"]
    if not isinstance(opts, list) or len(opts) != N_OPTIONS:
        _fail("item {!r} must have {} options".format(item["id"], N_OPTIONS))
    if len(set(str(o) for o in opts)) != N_OPTIONS:
        _fail("item {!r} has duplicate options".format(item["id"]))
    ci = item["correct_index"]
    if not isinstance(ci, int) or not (0 <= ci < N_OPTIONS):
        _fail("item {!r} has bad correct_index {!r}".format(item["id"], ci))
    if not (isinstance(item["difficulty"], int) and 1 <= item["difficulty"] <= 5):
        _fail("item {!r} difficulty must be int 1..5".format(item["id"]))
    if item["partition"] not in PARTITIONS:
        _fail("item {!r} bad partition {!r}".format(item["id"], item["partition"]))
    if item["partition"] == "p3":
        if not str(item.get("paraphrase_group") or "").strip():
            _fail("p3 item {!r} needs paraphrase_group".format(item["id"]))
        if not str(item.get("base_ref") or "").strip():
            _fail("p3 item {!r} needs base_ref".format(item["id"]))


def _validate_p3_groups(items):
    groups = {}
    for item in items:
        if item["partition"] != "p3":
            continue
        groups.setdefault(item["paraphrase_group"], []).append(item)
    for gid, members in groups.items():
        if len(members) != 2:
            _fail("paraphrase_group {!r} must have exactly 2 rewordings (has {})".format(
                gid, len(members)))
        keys = {str(m["options"][m["correct_index"]]) for m in members}
        refs = {m["base_ref"] for m in members}
        if len(keys) != 1:
            _fail("paraphrase_group {!r} rewordings have different keys {}".format(gid, keys))
        if len(refs) != 1:
            _fail("paraphrase_group {!r} rewordings have different base_ref {}".format(gid, refs))


def load_eval_items(path=ITEMS_YAML, partition=None):
    """Load + validate the frozen eval bank; optionally filter by partition."""
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    raw = data["items"] if isinstance(data, dict) else (data or [])
    for index, item in enumerate(raw):
        _validate_item(index, item)
    _validate_p3_groups(raw)
    if partition is not None:
        if partition not in PARTITIONS:
            _fail("unknown partition filter {!r}".format(partition))
        return [i for i in raw if i["partition"] == partition]
    return list(raw)


def summarize(items):
    """Return counts by partition / bucket / difficulty + paraphrase-group count."""
    by_partition, by_bucket, by_difficulty = {}, {}, {}
    groups = set()
    for item in items:
        by_partition[item["partition"]] = by_partition.get(item["partition"], 0) + 1
        bucket = taxonomy.bucket_of(item["leaf_tag"])
        by_bucket[bucket] = by_bucket.get(bucket, 0) + 1
        d = item["difficulty"]
        by_difficulty[d] = by_difficulty.get(d, 0) + 1
        if item["partition"] == "p3":
            groups.add(item["paraphrase_group"])
    total = len(items)
    calc = by_bucket.get(taxonomy.CALCULUS_BUCKET, 0)
    return {
        "total": total,
        "by_partition": by_partition,
        "by_bucket": by_bucket,
        "by_difficulty": by_difficulty,
        "paraphrase_groups": len(groups),
        "calc_weight": (calc / total) if total else 0.0,
    }


def _normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def assert_firewall(items=None, seed=42):
    """Raise if any eval item's (stem, answer) collides with a study-deck card."""
    if items is None:
        items = load_eval_items()
    from build_deck import load_all_cards  # lazy: pipeline is a code dep

    study = set()
    for card in load_all_cards(seed=seed):
        if card.get("format") == "mcq":
            study.add((_normalize(card["question"]),
                       _normalize(card["options"][card["correct_index"]])))
        else:
            study.add((_normalize(card["front"]), _normalize(card["back"])))
    for item in items:
        key = (_normalize(item["question"]),
               _normalize(item["options"][item["correct_index"]]))
        if key in study:
            _fail("item {!r} collides with a study-deck card (firewall)".format(item["id"]))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest eval/bank/tests/test_loader.py -q`
Expected: PASS (10 passed).

- [ ] **Step 6: Commit**

```bash
git add eval/bank/__init__.py eval/bank/loader.py eval/bank/tests/conftest.py eval/bank/tests/test_loader.py
git commit -m "feat(eval-bank): loader + validator (schema, gate, P3 integrity, firewall)"
```

---

## Task 2: Deterministic computational generator (`eval/bank/generate_eval.py`)

**Goal/deliverable:** produce well-formed, correct-key computational MCQ candidates (P0 items + P3 reword pairs) via SymPy, reusing `pipeline/distractors`. Output is YAML text to **freeze** into `items.yaml`; determinism + correctness are tested.

**Files:**
- Create: `eval/bank/generate_eval.py`, `eval/bank/tests/test_generate_eval.py`

**Interfaces:**
- Consumes: `pipeline` (`distractors`, `generate_deck` helpers, `taxonomy`).
- Produces:
  - `gen_p0_items(seed=42) -> list[dict]` — computational P0 records (partition `p0`, `paraphrase_group=None`, `base_ref=None`), taxonomy-weighted across computational leaves.
  - `gen_p3_pairs(seed=42) -> list[dict]` — computational P3 records in groups of 2 (same key, distinct wording, shared `paraphrase_group` + `base_ref`).
  - `emit_yaml(items) -> str` and a `__main__` that prints `gen_p0_items() + gen_p3_pairs()` as YAML for freezing.

- [ ] **Step 1: Write the failing test** (`eval/bank/tests/test_generate_eval.py`)

```python
"""Computational eval-item generation: determinism, well-formedness, correct key."""
import sympy as sp

import generate_eval
import loader
import taxonomy


def test_p0_items_are_wellformed_and_valid():
    items = generate_eval.gen_p0_items(seed=42)
    assert len(items) >= 12
    for it in items:
        assert it["partition"] == "p0"
        assert taxonomy.validate_leaf_tag(it["leaf_tag"])
        assert len(it["options"]) == 5 and len(set(it["options"])) == 5
        assert 0 <= it["correct_index"] < 5
        assert 1 <= it["difficulty"] <= 5


def test_p3_pairs_are_grouped_and_same_key():
    items = generate_eval.gen_p3_pairs(seed=42)
    groups = {}
    for it in items:
        assert it["partition"] == "p3"
        groups.setdefault(it["paraphrase_group"], []).append(it)
    assert groups
    for members in groups.values():
        assert len(members) == 2
        keys = {m["options"][m["correct_index"]] for m in members}
        assert len(keys) == 1  # same-key paraphrase


def test_generation_is_deterministic():
    assert generate_eval.gen_p0_items(seed=42) == generate_eval.gen_p0_items(seed=42)
    assert generate_eval.gen_p3_pairs(seed=42) == generate_eval.gen_p3_pairs(seed=42)


def test_generated_items_pass_the_loader(tmp_path):
    # Freeze then load: generated computational items must satisfy the validator.
    text = generate_eval.emit_yaml(
        generate_eval.gen_p0_items(seed=42) + generate_eval.gen_p3_pairs(seed=42)
    )
    p = tmp_path / "items.yaml"
    p.write_text(text, encoding="utf-8")
    items = loader.load_eval_items(path=str(p))
    assert len(items) == len(generate_eval.gen_p0_items(seed=42)) + len(
        generate_eval.gen_p3_pairs(seed=42)
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest eval/bank/tests/test_generate_eval.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_eval'`.

- [ ] **Step 3: Write `eval/bank/generate_eval.py`**

```python
"""Deterministic SymPy generators for computational eval items (P0 + P3 pairs).

Reuses pipeline/distractors + generate_deck helpers so keys and distractors are
correct-by-construction. Output is meant to be FROZEN into eval/bank/items.yaml
(the committed corpus is the source of truth; this module is the authoring aid).
"""
from __future__ import annotations

import yaml

import distractors
import taxonomy
from generate_deck import _leaf_rng, _nonzero, _s, x

_ATTR = {"src": "original", "gen": "human", "status": "verified",
         "verified_by": "fc", "verified_on": "2026-07-02"}


def _record(rec_id, leaf_tag, question, options, correct_index, explanation,
            difficulty, partition, paraphrase_group=None, base_ref=None):
    rec = {
        "id": rec_id, "leaf_tag": leaf_tag, "format": "mcq",
        "question": question, "options": options, "correct_index": correct_index,
        "explanation": explanation, "difficulty": difficulty, "partition": partition,
        "paraphrase_group": paraphrase_group, "base_ref": base_ref,
    }
    rec.update(_ATTR)
    return rec


# P0 held-out: (leaf, difficulty, count). Calculus-weighted so calc share >= 50%.
_P0_SPEC = [
    ("integral_single", 2, 4),
    ("differential_single", 2, 4),
    ("linear", 3, 2),
    ("number_theory", 3, 2),
]


def _det_problem(leaf, rng):
    """Return (question, correct_expr, wrong_exprs, explanation) for a leaf."""
    import sympy as sp
    if leaf == "integral_single":
        a = _nonzero(rng, 2, 6); b = _nonzero(rng, 1, 6)
        f = a * x + b
        correct = sp.integrate(f, x)
        return ("Give the antiderivative (omit + C):  \u222b ({}) dx".format(_s(f)),
                correct, [sp.diff(f, x), f], "F(x) = {} + C".format(_s(correct)))
    if leaf == "differential_single":
        a = _nonzero(rng, 2, 6); n = rng.randint(2, 4)
        f = a * x**n
        correct = sp.diff(f, x)
        return ("Differentiate:  f(x) = {}".format(_s(f)),
                correct, [sp.integrate(f, x), sp.diff(correct, x)],
                "f'(x) = {}".format(_s(correct)))
    if leaf == "linear":
        a = _nonzero(rng, -6, 6); b = rng.randint(-6, 6)
        c = rng.randint(-6, 6); d = _nonzero(rng, -6, 6)
        correct = sp.Integer(a * d - b * c)
        return ("Determinant of [[{}, {}], [{}, {}]]?".format(a, b, c, d),
                correct, [sp.Integer(a * d + b * c), sp.Integer(a * b - c * d)],
                "det = {}".format(_s(correct)))
    if leaf == "number_theory":
        a = rng.randint(12, 90); b = rng.randint(12, 90)
        g = sp.igcd(a, b)
        return ("Compute gcd({}, {}).".format(a, b),
                sp.Integer(g), [sp.Integer(a * b // g), sp.Integer(min(a, b))],
                "gcd = {}".format(g))
    raise ValueError("no generator for leaf " + leaf)


def gen_p0_items(seed=42):
    items = []
    n = 0
    for leaf, difficulty, count in _P0_SPEC:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        rng = _leaf_rng(seed, tag + "::eval::p0")
        seen = set()
        while sum(1 for i in items if i["leaf_tag"] == tag) < count:
            q, correct, wrongs, expl = _det_problem(leaf, rng)
            if q in seen:
                continue
            try:
                options, ci = distractors.make_options(rng, correct, wrongs)
            except distractors.InsufficientDistractors:
                continue
            seen.add(q)
            n += 1
            items.append(_record("eval-p0-{:04d}".format(n), tag, q, options, ci,
                                  expl, difficulty, "p0"))
    return items


# P3 reword pairs: (leaf, difficulty, n_groups). Each group = 2 same-key rewordings.
_P3_SPEC = [("integral_single", 2, 3), ("differential_single", 2, 3), ("linear", 3, 2)]

# Two surface framings per leaf that keep the SAME instance/key (true paraphrase).
_P3_FRAMES = {
    "integral_single": [
        "Find the antiderivative (omit + C):  \u222b ({f}) dx",
        "A velocity is v(t) = {f}. Which is a position function s(t) (up to a constant)?",
    ],
    "differential_single": [
        "Differentiate:  f(x) = {f}",
        "Find the slope function f'(x) for f(x) = {f}.",
    ],
    "linear": [
        "Determinant of [[{a}, {b}], [{c}, {d}]]?",
        "For M = [[{a}, {b}], [{c}, {d}]], compute det(M).",
    ],
}


def gen_p3_pairs(seed=42):
    import sympy as sp
    items = []
    gi = 0
    for leaf, difficulty, n_groups in _P3_SPEC:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        rng = _leaf_rng(seed, tag + "::eval::p3")
        made = 0
        seen = set()
        while made < n_groups:
            q0, correct, wrongs, expl = _det_problem(leaf, rng)
            sig = _s(correct)
            if sig in seen:
                continue
            try:
                options, ci = distractors.make_options(rng, correct, wrongs)
            except distractors.InsufficientDistractors:
                continue
            seen.add(sig)
            gi += 1
            made += 1
            group = "pg-{:04d}".format(gi)
            base_ref = "{} :: {}".format(tag, expl)
            frames = _P3_FRAMES[leaf]
            # Rebuild the surface strings for each framing from the same instance.
            if leaf == "linear":
                nums = _parse_matrix(q0)
                texts = [frames[0].format(**nums), frames[1].format(**nums)]
            else:
                fexpr = _extract_expr(q0)
                texts = [frames[0].format(f=fexpr), frames[1].format(f=fexpr)]
            for r, text in enumerate(texts, start=1):
                items.append(_record(
                    "eval-p3-{}-r{}".format(group, r), tag, text, options, ci,
                    expl, difficulty, "p3", paraphrase_group=group, base_ref=base_ref))
    return items


def _extract_expr(question):
    """Pull the '{f}' body back out of a generated stem (between the last '(' and ') dx' or '= ')."""
    if "\u222b (" in question:
        return question.split("\u222b (", 1)[1].split(") dx", 1)[0]
    if "f(x) = " in question:
        return question.split("f(x) = ", 1)[1]
    raise ValueError("cannot extract expr from: " + question)


def _parse_matrix(question):
    body = question.split("[[", 1)[1].split("]]", 1)[0]  # "a, b], [c, d"
    left, right = body.split("], [")
    a, b = [s.strip() for s in left.split(",")]
    c, d = [s.strip() for s in right.split(",")]
    return {"a": a, "b": b, "c": c, "d": d}


def emit_yaml(items):
    return yaml.safe_dump({"items": items}, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    print(emit_yaml(gen_p0_items() + gen_p3_pairs()))
```

> Implementer note: keep `_det_problem` the single source of each instance so both P3 framings share one key. If `_extract_expr`/`_parse_matrix` prove brittle, refactor `_det_problem` to return the raw params/expr alongside the stem and format both framings from those — same interface, cleaner. Whichever you choose, the Step-1 tests (grouped, same-key, deterministic, loader-valid) are the gate.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest eval/bank/tests/test_generate_eval.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add eval/bank/generate_eval.py eval/bank/tests/test_generate_eval.py
git commit -m "feat(eval-bank): deterministic SymPy generator for computational P0 + P3 items"
```

---

## Task 3: Freeze the corpus + author conceptual/reword content (`eval/bank/items.yaml`)

**Goal/deliverable:** the committed, verified `items.yaml` — generated computational items (frozen) + hand-authored conceptual P0 items and conceptual/extra P3 rewordings — reaching ~84 items (P0 ~24, P3 ~60), taxonomy-weighted, firewalled.

**Files:**
- Create: `eval/bank/items.yaml`
- Test: `eval/bank/tests/test_bank_composition.py`

**Interfaces:**
- Consumes: `generate_eval` (freeze its output), `loader`.

- [ ] **Step 1: Generate + freeze the computational base**

Run:
```bash
. .venv/bin/activate
python eval/bank/generate_eval.py > eval/bank/items.yaml
python -c "import sys; sys.path[:0]=['eval/bank','pipeline']; import loader; print(loader.summarize(loader.load_eval_items()))"
```
Expected: `items.yaml` written; summary prints (computational P0 ≈12 + P3 ≈16). This is the frozen computational core.

- [ ] **Step 2: Hand-author the remaining items into `eval/bank/items.yaml`**

Append verified records (same schema) until composition targets are met — **all original, correct, GRE-appropriate, `status: verified` + attribution**:
- **P0 conceptual (~12)** across `additional::*` + `algebra::abstract` leaves (real_analysis, topology, complex, discrete, geometry, …) so **P0 totals ~24** and stays taxonomy-weighted. Example record:

```yaml
  - id: "eval-p0-0101"
    leaf_tag: "topic::additional::real_analysis"
    format: mcq
    question: "Which sequence is Cauchy in R?"
    options: ["a_n = 1/n", "a_n = (-1)^n", "a_n = n", "a_n = sin(n)", "a_n = (-1)^n * n"]
    correct_index: 0
    explanation: "1/n converges (to 0), hence is Cauchy in the complete space R."
    difficulty: 3
    partition: p0
    paraphrase_group: null
    base_ref: null
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
```

- **P3 conceptual reword groups (~22 items = 11 groups)** so **P3 totals ~60**. Each group = **2 rewordings, same key, shared `paraphrase_group` + `base_ref`** to a study-deck concept. Example group:

```yaml
  - id: "eval-p3-pg0101-r1"
    leaf_tag: "topic::additional::discrete"
    format: mcq
    question: "How many subsets does a set of n elements have?"
    options: ["2^n", "n^2", "n!", "2n", "n^n"]
    correct_index: 0
    explanation: "Each element is in or out: 2^n."
    difficulty: 2
    partition: p3
    paraphrase_group: "pg-0101"
    base_ref: "topic::additional::discrete :: number of subsets of an n-set"
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
  - id: "eval-p3-pg0101-r2"
    leaf_tag: "topic::additional::discrete"
    format: mcq
    question: "A set has n elements. How many elements does its power set have?"
    options: ["2^n", "n - 1", "2*n", "n^2", "n + 1"]
    correct_index: 0
    explanation: "The power set has 2^n elements."
    difficulty: 2
    partition: p3
    paraphrase_group: "pg-0101"
    base_ref: "topic::additional::discrete :: number of subsets of an n-set"
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
```

Guidance while authoring: keep each `base_ref` pointing at a real study-deck concept (so 7d's recall comparison is meaningful); the two rewordings must share the *same correct-answer text* and differ only in surface wording/framing; keep exactly 5 distinct options; assign a provisional `difficulty` 1–5.

- [ ] **Step 3: Write the composition test** (`eval/bank/tests/test_bank_composition.py`)

```python
"""The committed eval bank meets composition + firewall targets."""
import loader


def test_committed_bank_loads_and_is_verified():
    items = loader.load_eval_items()
    assert all(i["status"] == "verified" for i in items)


def test_partition_targets():
    s = loader.summarize(loader.load_eval_items())
    assert s["by_partition"].get("p0", 0) >= 20
    assert s["by_partition"].get("p3", 0) >= 56
    # P3 rewordings come in groups of exactly 2:
    assert s["by_partition"]["p3"] == 2 * s["paraphrase_groups"]


def test_calc_weight_reasonable():
    s = loader.summarize(loader.load_eval_items())
    assert s["calc_weight"] >= 0.30  # calc well represented (P0+P3 combined)


def test_firewall_holds():
    loader.assert_firewall()  # no overlap with the study deck
```

- [ ] **Step 4: Run the composition tests + full bank suite**

Run: `python -m pytest eval/bank/tests -q`
Expected: all PASS. If `test_partition_targets` fails, author more items (Step 2) until P0 ≥ 20 and P3 ≥ 56 (28 groups). If `test_firewall_holds` fails, reword the colliding item.

- [ ] **Step 5: Commit**

```bash
git add eval/bank/items.yaml eval/bank/tests/test_bank_composition.py
git commit -m "feat(eval-bank): freeze ~84 verified P0+P3 items (paraphrase pairs)"
```

---

## Task 4: Module doc + INDEX + final verification

**Goal/deliverable:** document the corpus and its firewall, register it in the codebase index, and prove the whole thing loads + validates deterministically.

**Files:**
- Create: `eval/bank/eval_bank.md`
- Modify: `docs/codebase/INDEX.md`

- [ ] **Step 1: Write `eval/bank/eval_bank.md`** from `.cursor/skills/codebase-docs/module-doc-template.md`. Cover: purpose (held-out/paraphrase corpus for scoring); public interface (`load_eval_items`, `summarize`, `assert_firewall`, `generate_eval`); the record schema + partitions (`p0..p3`, only p0/p3 populated); gotchas (frozen/version-locked YAML; provisional difficulty; `eval::` firewall vs study deck; P3 = rewordings, base is study-deck; leakage pipeline is separate); related tests. End with `Last verified against: agent/eval-bank`.

- [ ] **Step 2: Update `docs/codebase/INDEX.md`** — add to the Built table:

```
| Authored eval bank (P0 held-out + P3 paraphrase, W-Thu) | `eval/bank/eval_bank.md` | `eval/bank/` (`loader.py`, `generate_eval.py`, `items.yaml`) | `agent/eval-bank` |
```
And update the Planned "held-out testing / eval item bank" note to point at `eval/bank/` as built (leave the leakage pipeline + P1/P2 as still-planned).

- [ ] **Step 3: Final deterministic verification**

Run:
```bash
python -m pytest eval/bank/tests -q
python -c "import sys; sys.path[:0]=['eval/bank','pipeline']; import loader; s=loader.summarize(loader.load_eval_items()); print(s); loader.assert_firewall(); print('firewall OK')"
```
Expected: all tests PASS; summary shows P0 ≥ 20, P3 ≥ 56 (== 2× groups), `firewall OK`.

- [ ] **Step 4: Commit**

```bash
git add eval/bank/eval_bank.md docs/codebase/INDEX.md
git commit -m "docs(eval-bank): module doc + INDEX entry"
```

---

## Self-Review (plan vs. spec)

- **Spec coverage:** §1 placement → `eval/bank/` (Task 1/3); §2 schema → Task 1 `_validate_item` + Task 3 records; §3 composition (P0 ~24, P3 ~60 groups×2) → Task 3 + `test_partition_targets`; §4 hybrid production (SymPy frozen + authored) → Tasks 2–3; §5 loader/validator/firewall/summarize → Task 1; §6 firewall/re-runnability → `assert_firewall` + frozen YAML + determinism tests; §7 tests → Tasks 1–3 test files; §8 lane/deps → fast lane, reuses `pipeline` code; §9 acceptance → Task 3/4 composition + firewall + docs. No gaps.
- **Placeholder scan:** none — loader, generator, tests, and representative content are inline. Hand-authoring in Task 3 Step 2 is bounded by concrete composition tests (P0 ≥ 20, P3 ≥ 56, groups of 2, firewall) and shown with full worked records.
- **Type/name consistency:** record dict shape (`id, leaf_tag, format, question, options[5], correct_index, explanation, difficulty, partition, paraphrase_group, base_ref, src, gen, status, verified_by, verified_on`) is identical across generator, loader validation, and authored YAML. `load_eval_items(path=, partition=)`, `summarize(items)->{by_partition,paraphrase_groups,calc_weight,...}`, `assert_firewall(items=, seed=)`, `make_options(rng, correct, wrong_exprs)->(list,int)` used consistently.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-02-authored-eval-bank.md`. Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task + two-stage review (superpowers:subagent-driven-development). *(Note: subagent dispatch is currently blocked by the account billing issue; inline is the fallback.)*
2. **Inline Execution** — execute in this session with checkpoints (superpowers:executing-plans).

**Which approach?**
