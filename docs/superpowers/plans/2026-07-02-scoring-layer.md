# Scoring Layer (Performance + Readiness) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone pure-Python `scoring/` package that computes the two harder scores — **Performance** (P(correct) on a new item) and **Readiness** (projected GRE 200–990 as a range with a full evidence panel + give-up rule) — validate them on a hybrid simulated+real attempt set, write a **desktop-authoritative synced `col.conf` "score card,"** and render all three scores **read-only on the phone**.

**Architecture:** `scoring/` is dependency-light **pure stdlib** (no numpy/scipy — the anki pyenv has none): hand-rolled logistic regression + Platt scaling (gradient descent), Poisson-binomial via DP convolution, split-conformal from sorted residuals. It takes plain inputs (feature dicts, attempt rows) and returns plain data. A thin Qt adapter in `anki/qt/aqt/gre/` gathers live inputs (W1 mastery RPC, coverage, revlog), calls `scoring/`, and writes `col.set_config("gre_scorecard", …)`; W4 sync carries it to AnkiDroid, which renders a read-only 3-score panel.

**Tech Stack:** Python 3 stdlib (`math`, `random`, `statistics`, `json`, `csv`), pytest; the built anki pyenv (`anki/out/pyenv/bin/python` + `PYTHONPATH=anki/out/pylib`) for the adapter/integration; Kotlin (AnkiDroid) for the read-only panel; `col.conf` (synced) as transport.

## Global Constraints

- **No engine/collection-schema change → fast lane.** Nothing under `anki/rslib/`, no `.proto`, no FFI, no submodule pin bump. Score card uses the existing `col.set_config`/`col.get_config` API. The W1 mastery RPC stays read-only.
- **Pure stdlib for `scoring/`** — numpy/scipy/sklearn are NOT in the anki pyenv; do not add them. All math is hand-rolled + unit-tested.
- **Never blend the three scores** — Memory, Performance, Readiness always separate, each with a range. (PRD D2 / AGENTS.md ceiling.)
- **Never show Readiness without the full evidence panel** (estimate, range, %coverage, confidence, last-updated, reasons, best-next topic) + the give-up rule. A bare number is an automatic fail.
- **Give-up rule (D2), ALL must hold or no Readiness number:** ≥ **200** graded reviews · ≥ **50%** leaf coverage · conformal interval **width ≤ `READINESS_MAX_INTERVAL_WIDTH = 120`** scaled-score points (total width). The width constant is declared before any run and never tuned to force a number.
- **Firewall:** item difficulty is authored/imported (never estimated from the validated student); train/test never share items; study deck and eval bank never mix.
- **Honesty over flattery:** at n≈1 report wide intervals + "no track record yet"; calibration metrics labeled "validated on simulated data (machinery check); real predictive validity unestablished at n≈1."
- **Re-runnable:** fixed seeds, deterministic output, one command (`make score-eval`).
- **Spec:** `docs/superpowers/specs/2026-07-02-thursday-scoring-layer-design.md`.

## Environment / interfaces (verified against current `main`)

- **eval bank** (`eval/bank/loader.py`): `load_eval_items(path=ITEMS_YAML, partition=None) -> list[dict]`; each item dict has `id, leaf_tag, format, question, options, correct_index, explanation, difficulty (int 1–5), partition ("p0".."p3"), paraphrase_group, base_ref`. `summarize(items)`, `assert_firewall()`.
- **Mastery (W1)** — desktop: `col.mastery_query(topics: list[str]) -> Sequence[TopicMastery]` with fields `topic, total_cards, reviewed_count, mastered_count, avg_recall` (`anki/pylib/anki/collection.py`).
- **W2 dashboard** (`anki/qt/aqt/gre/dashboard_data.py`): already computes `studied_pct` + `reasons` (`<50% studied coverage`, `<200 graded reviews`) and per-leaf rows via the mastery query. The Readiness adapter extends this (adds the interval-width reason).
- **Config API:** `col.get_config(key, default=None)`, `col.set_config(key, val)` (`anki/pylib/anki/collection.py:910/916`).
- **Run recipe (desktop tests/adapter):** `PYTHONPATH=$FORK_ANKI/out/pylib $FORK_ANKI/out/pyenv/bin/python …` where `FORK_ANKI=/Users/felipecaicedo/Desktop/alpha/speedrun/anki`. The pure `scoring/` unit tests need only system `python3` (stdlib).
- **Worktree:** fast lane; the `scoring/` package + its tests are outer-repo Python (no submodule needed). The Qt adapter (Task 6) and AnkiDroid panel (Task 7) touch the `anki`/`Anki-Android` submodules — init them per `using-git-worktrees` at those tasks.

---

## File Structure

**New top-level `scoring/` package (pure stdlib):**
- `scoring/__init__.py`
- `scoring/logistic.py` — logistic regression + Platt scaling (gradient descent).
- `scoring/features.py` — assemble per-`(student,item)` feature vectors from mastery + difficulty + timing + coverage.
- `scoring/performance.py` — fit + `predict_proba(features) -> (p, lo, hi)` (bootstrap interval).
- `scoring/poisson_binomial.py` — DP convolution for the raw-correct distribution.
- `scoring/readiness.py` — raw-correct → ETS percentile → 200–990 + split-conformal + give-up gate.
- `scoring/calibration.py` — Brier, reliability bins, ECE; calibration-log append.
- `scoring/simulate.py` — hybrid harness (simulated students + real-attempt CSV loader).
- `scoring/scorecard.py` — assemble the `gre_scorecard` JSON payload.
- `scoring/eval_cli.py` — `make score-eval` entry: simulate → fit → validate → emit `out/metrics.json` + sample scorecard.
- `scoring/data/ets_percentiles.json` — vendored ETS percentile→scaled-score anchors (cited).
- `scoring/data/real_attempts.csv` — optional real self-answered anchor (header + any rows).
- `scoring/requirements.txt` — documents "stdlib only" + pytest pin.
- `scoring/scoring.md` — module doc.
- `scoring/tests/` — `test_logistic.py`, `test_features.py`, `test_performance.py`, `test_poisson_binomial.py`, `test_readiness.py`, `test_calibration.py`, `test_scorecard.py`, `test_eval_cli.py`.

**Modified:**
- root `Makefile` — add `score-eval`.
- `anki/qt/aqt/gre/` (Task 6) — adapter that calls `scoring/` + writes the score card + renders desktop slots.
- `Anki-Android/AnkiDroid/…` (Task 7) — read-only 3-score panel.
- `docs/codebase/INDEX.md`, `docs/STATUS.md` (Task 8).

---

## Task 1: Logistic regression + Platt scaling (`scoring/logistic.py`)

**Files:**
- Create: `scoring/__init__.py`, `scoring/logistic.py`, `scoring/tests/conftest.py`, `scoring/tests/test_logistic.py`

**Interfaces:**
- Produces:
  - `sigmoid(z: float) -> float`
  - `class LogisticModel` with `weights: list[float]`, `bias: float`; `fit(X: list[list[float]], y: list[int], *, lr=0.1, epochs=2000, l2=0.0, seed=0) -> None`; `predict_proba_one(x: list[float]) -> float`.
  - `platt_fit(scores: list[float], y: list[int]) -> tuple[float, float]` and `platt_apply(a: float, b: float, score: float) -> float` (1-D logistic calibration of raw scores).

- [ ] **Step 1: Write `scoring/tests/conftest.py`**

```python
"""Put the scoring package on sys.path for pytest from the repo root."""
import os
import sys

SCORING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(SCORING_DIR)
for p in (REPO_ROOT, SCORING_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)
```

- [ ] **Step 2: Write the failing test** (`scoring/tests/test_logistic.py`)

```python
"""Hand-rolled logistic regression + Platt scaling (pure stdlib)."""
import math

from scoring.logistic import LogisticModel, platt_apply, platt_fit, sigmoid


def test_sigmoid_basic():
    assert abs(sigmoid(0.0) - 0.5) < 1e-9
    assert sigmoid(50) > 0.999
    assert sigmoid(-50) < 0.001


def test_learns_separable_1d():
    # y = 1 when x > 0. Model should learn a positive weight + near-zero bias.
    X = [[-3.0], [-2.0], [-1.0], [1.0], [2.0], [3.0]]
    y = [0, 0, 0, 1, 1, 1]
    m = LogisticModel()
    m.fit(X, y, lr=0.5, epochs=5000, seed=0)
    assert m.predict_proba_one([2.0]) > 0.8
    assert m.predict_proba_one([-2.0]) < 0.2


def test_fit_is_deterministic():
    X = [[-1.0], [1.0], [2.0], [-2.0]]
    y = [0, 1, 1, 0]
    a = LogisticModel(); a.fit(X, y, seed=0)
    b = LogisticModel(); b.fit(X, y, seed=0)
    assert a.weights == b.weights and a.bias == b.bias


def test_platt_maps_scores_to_calibrated_probs():
    # Raw scores correlated with label; Platt should push positives high.
    scores = [-2.0, -1.0, 0.5, 1.5, 2.5]
    y = [0, 0, 1, 1, 1]
    a, b = platt_fit(scores, y)
    assert platt_apply(a, b, 2.5) > platt_apply(a, b, -2.0)
```

- [ ] **Step 3: Run to verify it fails** — `python3 -m pytest scoring/tests/test_logistic.py -q` → FAIL (`No module named 'scoring.logistic'`).

- [ ] **Step 4: Implement `scoring/logistic.py`**

```python
"""Logistic regression + Platt (sigmoid) calibration — pure stdlib.

No numpy: the anki pyenv has none, and re-runnability wants zero heavy deps.
Batch gradient descent with optional L2; deterministic under a fixed seed.
"""
from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


class LogisticModel:
    def __init__(self) -> None:
        self.weights: list[float] = []
        self.bias: float = 0.0

    def fit(self, X, y, *, lr: float = 0.1, epochs: int = 2000, l2: float = 0.0, seed: int = 0) -> None:
        if not X:
            raise ValueError("no training rows")
        n_features = len(X[0])
        rng = random.Random(seed)
        # Deterministic tiny init (seeded) — keeps fit() reproducible.
        self.weights = [rng.uniform(-0.01, 0.01) for _ in range(n_features)]
        self.bias = 0.0
        n = len(X)
        for _ in range(epochs):
            grad_w = [0.0] * n_features
            grad_b = 0.0
            for xi, yi in zip(X, y):
                z = self.bias + sum(w * x for w, x in zip(self.weights, xi))
                err = sigmoid(z) - yi
                for j in range(n_features):
                    grad_w[j] += err * xi[j]
                grad_b += err
            for j in range(n_features):
                self.weights[j] -= lr * (grad_w[j] / n + l2 * self.weights[j])
            self.bias -= lr * (grad_b / n)

    def predict_proba_one(self, x) -> float:
        z = self.bias + sum(w * xi for w, xi in zip(self.weights, x))
        return sigmoid(z)


def platt_fit(scores, y, *, lr: float = 0.1, epochs: int = 2000, seed: int = 0) -> tuple[float, float]:
    """1-D logistic calibration: fit p = sigmoid(a*score + b)."""
    model = LogisticModel()
    model.fit([[s] for s in scores], y, lr=lr, epochs=epochs, seed=seed)
    return model.weights[0], model.bias


def platt_apply(a: float, b: float, score: float) -> float:
    return sigmoid(a * score + b)
```

- [ ] **Step 5: Run to verify it passes** — `python3 -m pytest scoring/tests/test_logistic.py -q` → PASS (4 passed).

- [ ] **Step 6: Commit**

```bash
git add scoring/__init__.py scoring/logistic.py scoring/tests/conftest.py scoring/tests/test_logistic.py
git commit -m "feat(scoring): pure-stdlib logistic regression + Platt scaling"
```

---

## Task 2: Poisson-binomial distribution (`scoring/poisson_binomial.py`)

**Files:**
- Create: `scoring/poisson_binomial.py`, `scoring/tests/test_poisson_binomial.py`

**Interfaces:**
- Produces:
  - `pmf(probs: list[float]) -> list[float]` — P(k successes) for k in 0..len(probs), via DP convolution.
  - `expected_and_var(probs) -> tuple[float, float]`.

- [ ] **Step 1: Write the failing test**

```python
"""Poisson-binomial via DP convolution (pure stdlib)."""
from scoring.poisson_binomial import expected_and_var, pmf


def test_pmf_sums_to_one_and_length():
    p = pmf([0.2, 0.5, 0.9, 0.1])
    assert len(p) == 5  # 0..4 successes
    assert abs(sum(p) - 1.0) < 1e-12


def test_reduces_to_binomial_when_equal():
    # All p=0.5, n=3 -> pmf = [1,3,3,1]/8
    p = pmf([0.5, 0.5, 0.5])
    assert abs(p[0] - 0.125) < 1e-12
    assert abs(p[1] - 0.375) < 1e-12
    assert abs(p[3] - 0.125) < 1e-12


def test_expected_matches_sum_of_probs():
    probs = [0.1, 0.4, 0.7, 0.9]
    mean, var = expected_and_var(probs)
    assert abs(mean - sum(probs)) < 1e-12
    assert abs(var - sum(pi * (1 - pi) for pi in probs)) < 1e-12


def test_deterministic_edge_cases():
    assert pmf([]) == [1.0]
    assert pmf([1.0]) == [0.0, 1.0]
    assert pmf([0.0]) == [1.0, 0.0]
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m pytest scoring/tests/test_poisson_binomial.py -q` → FAIL (no module).

- [ ] **Step 3: Implement `scoring/poisson_binomial.py`**

```python
"""Poisson-binomial distribution (sum of independent non-identical Bernoullis).

pmf via O(n^2) DP convolution — exact, pure stdlib. Used to turn per-item
P(correct) into a raw-correct distribution for the Readiness projection.
"""
from __future__ import annotations


def pmf(probs) -> list[float]:
    dist = [1.0]  # P(0 successes) = 1 before adding any item
    for p in probs:
        p = max(0.0, min(1.0, float(p)))
        nxt = [0.0] * (len(dist) + 1)
        for k, dk in enumerate(dist):
            nxt[k] += dk * (1.0 - p)      # item wrong
            nxt[k + 1] += dk * p          # item right
        dist = nxt
    return dist


def expected_and_var(probs) -> tuple[float, float]:
    mean = sum(float(p) for p in probs)
    var = sum(float(p) * (1.0 - float(p)) for p in probs)
    return mean, var
```

- [ ] **Step 4: Run to verify it passes** — `python3 -m pytest scoring/tests/test_poisson_binomial.py -q` → PASS.

- [ ] **Step 5: Commit**

```bash
git add scoring/poisson_binomial.py scoring/tests/test_poisson_binomial.py
git commit -m "feat(scoring): exact Poisson-binomial pmf via DP convolution"
```

---

## Task 3: Feature assembly (`scoring/features.py`)

**Files:**
- Create: `scoring/features.py`, `scoring/tests/test_features.py`

**Interfaces:**
- Consumes: eval-bank item dicts (`leaf_tag`, `difficulty`); a per-leaf mastery map; per-attempt timing.
- Produces:
  - `FEATURE_ORDER = ("mastery_recall", "difficulty_z", "time_z", "coverage")` (stable order).
  - `build_features(item: dict, mastery_by_leaf: dict[str, float], coverage: float, time_z: float = 0.0) -> list[float]` — returns a vector in `FEATURE_ORDER`; `difficulty_z = (item["difficulty"] - 3) / 1.414` (centered on the 1–5 midpoint); `mastery_recall` defaults to 0.0 for an unseen leaf.
  - `zscore(values: list[float]) -> list[float]` (population z; returns zeros if std==0).

- [ ] **Step 1: Write the failing test**

```python
"""Per-(student,item) feature assembly."""
from scoring.features import FEATURE_ORDER, build_features, zscore


def test_feature_vector_order_and_values():
    item = {"leaf_tag": "topic::calculus::integral_single", "difficulty": 5}
    vec = build_features(item, {"topic::calculus::integral_single": 0.8}, coverage=0.6, time_z=1.0)
    assert len(vec) == len(FEATURE_ORDER)
    assert abs(vec[FEATURE_ORDER.index("mastery_recall")] - 0.8) < 1e-9
    assert abs(vec[FEATURE_ORDER.index("difficulty_z")] - (5 - 3) / 1.414) < 1e-6
    assert vec[FEATURE_ORDER.index("time_z")] == 1.0
    assert abs(vec[FEATURE_ORDER.index("coverage")] - 0.6) < 1e-9


def test_unseen_leaf_defaults_zero_mastery():
    item = {"leaf_tag": "topic::algebra::linear", "difficulty": 3}
    vec = build_features(item, {}, coverage=0.0)
    assert vec[FEATURE_ORDER.index("mastery_recall")] == 0.0


def test_zscore_zeroes_when_constant():
    assert zscore([2.0, 2.0, 2.0]) == [0.0, 0.0, 0.0]
    z = zscore([1.0, 2.0, 3.0])
    assert abs(sum(z)) < 1e-9  # mean-centered
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m pytest scoring/tests/test_features.py -q` → FAIL.

- [ ] **Step 3: Implement `scoring/features.py`**

```python
"""Feature assembly for the Performance model (pure stdlib).

Features (stable order): the item's leaf-topic mastery (mean FSRS recall from
the W1 mastery query), authored difficulty (z-ish, centered on the 1-5 mid),
response-time z-score, and topic coverage. Difficulty is imported/authored —
never estimated from the student being scored (firewall).
"""
from __future__ import annotations

import statistics

FEATURE_ORDER = ("mastery_recall", "difficulty_z", "time_z", "coverage")

_DIFF_MID = 3.0     # midpoint of the authored 1-5 scale
_DIFF_SCALE = 1.414  # ~sd of a uniform 1-5, keeps difficulty_z O(1)


def build_features(item, mastery_by_leaf, coverage, time_z=0.0) -> list[float]:
    mastery = float(mastery_by_leaf.get(item["leaf_tag"], 0.0))
    difficulty_z = (float(item["difficulty"]) - _DIFF_MID) / _DIFF_SCALE
    values = {
        "mastery_recall": mastery,
        "difficulty_z": difficulty_z,
        "time_z": float(time_z),
        "coverage": float(coverage),
    }
    return [values[name] for name in FEATURE_ORDER]


def zscore(values) -> list[float]:
    if not values:
        return []
    mean = statistics.fmean(values)
    if len(values) < 2:
        return [0.0 for _ in values]
    sd = statistics.pstdev(values)
    if sd == 0:
        return [0.0 for _ in values]
    return [(v - mean) / sd for v in values]
```

- [ ] **Step 4: Run to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add scoring/features.py scoring/tests/test_features.py
git commit -m "feat(scoring): feature assembly for the Performance model"
```

---

## Task 4: Hybrid attempt harness (`scoring/simulate.py`)

**Files:**
- Create: `scoring/simulate.py`, `scoring/data/real_attempts.csv`, `scoring/tests/test_simulate.py`

**Interfaces:**
- Consumes: eval-bank items (`load_eval_items`), `scoring.logistic.sigmoid`.
- Produces:
  - `Attempt = namedtuple("Attempt", "student_id item_id leaf_tag difficulty correct time_z")`.
  - `simulate_attempts(items: list[dict], n_students: int = 40, seed: int = 42) -> list[Attempt]` — per-student per-topic ability θ~N(0,1); outcome `~ Bernoulli(sigmoid(theta_leaf - b_z))` where `b_z = (difficulty-3)/1.414`. Deterministic.
  - `load_real_attempts(path="scoring/data/real_attempts.csv") -> list[Attempt]` — reads the optional CSV (returns [] if absent/empty).
  - `student_mastery(attempts, student_id) -> dict[str, float]` — per-leaf mean correctness for that student (a stand-in for the FSRS mastery feature in simulation).

- [ ] **Step 1: Write the failing test**

```python
"""Hybrid attempt harness: deterministic simulation + real-CSV loader."""
from scoring.simulate import Attempt, load_real_attempts, simulate_attempts, student_mastery

_ITEMS = [
    {"id": "i1", "leaf_tag": "topic::calculus::integral_single", "difficulty": 2},
    {"id": "i2", "leaf_tag": "topic::calculus::integral_single", "difficulty": 5},
    {"id": "i3", "leaf_tag": "topic::algebra::linear", "difficulty": 3},
]


def test_simulation_is_deterministic_and_shaped():
    a = simulate_attempts(_ITEMS, n_students=10, seed=42)
    b = simulate_attempts(_ITEMS, n_students=10, seed=42)
    assert a == b
    assert len(a) == 10 * len(_ITEMS)
    assert all(x.correct in (0, 1) for x in a)


def test_harder_items_are_answered_worse_on_average():
    a = simulate_attempts(_ITEMS, n_students=300, seed=1)
    easy = [x.correct for x in a if x.item_id == "i1"]
    hard = [x.correct for x in a if x.item_id == "i2"]
    assert sum(easy) / len(easy) > sum(hard) / len(hard)


def test_real_loader_missing_is_empty():
    assert load_real_attempts("scoring/data/does_not_exist.csv") == []


def test_student_mastery_is_per_leaf_mean():
    a = simulate_attempts(_ITEMS, n_students=50, seed=3)
    m = student_mastery(a, a[0].student_id)
    assert set(m) <= {"topic::calculus::integral_single", "topic::algebra::linear"}
    assert all(0.0 <= v <= 1.0 for v in m.values())
```

- [ ] **Step 2: Run to verify it fails** — FAIL (no module).

- [ ] **Step 3: Implement `scoring/simulate.py`** + write the CSV header file

```python
"""Hybrid attempt harness (pure stdlib).

Simulated students give the pipeline enough (features -> outcome) rows to fit
Platt, bootstrap intervals, and draw a real reliability curve. A small real
self-answered CSV is an honest sanity anchor. The model never sees the
generative theta/b — only the resulting outcomes + authored difficulty.
"""
from __future__ import annotations

import csv
import os
import random
from collections import namedtuple

from scoring.logistic import sigmoid

Attempt = namedtuple("Attempt", "student_id item_id leaf_tag difficulty correct time_z")

_DIFF_MID = 3.0
_DIFF_SCALE = 1.414


def simulate_attempts(items, n_students: int = 40, seed: int = 42):
    rng = random.Random(seed)
    leaves = sorted({it["leaf_tag"] for it in items})
    attempts = []
    for s in range(n_students):
        theta = {leaf: rng.gauss(0.0, 1.0) for leaf in leaves}
        for it in items:
            b_z = (float(it["difficulty"]) - _DIFF_MID) / _DIFF_SCALE
            p = sigmoid(theta[it["leaf_tag"]] - b_z)
            correct = 1 if rng.random() < p else 0
            time_z = rng.gauss(0.0, 1.0)
            attempts.append(Attempt(f"sim{s}", it["id"], it["leaf_tag"],
                                    int(it["difficulty"]), correct, round(time_z, 6)))
    return attempts


def load_real_attempts(path: str = "scoring/data/real_attempts.csv"):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("item_id"):
                continue
            out.append(Attempt(row["student_id"], row["item_id"], row["leaf_tag"],
                               int(row["difficulty"]), int(row["correct"]),
                               float(row.get("time_z", 0.0))))
    return out


def student_mastery(attempts, student_id):
    by_leaf: dict[str, list[int]] = {}
    for a in attempts:
        if a.student_id == student_id:
            by_leaf.setdefault(a.leaf_tag, []).append(a.correct)
    return {leaf: sum(v) / len(v) for leaf, v in by_leaf.items() if v}
```

`scoring/data/real_attempts.csv` (header only — fill by answering eval items):
```csv
student_id,item_id,leaf_tag,difficulty,correct,time_z
```

- [ ] **Step 4: Run to verify it passes** — PASS.

- [ ] **Step 5: Commit**

```bash
git add scoring/simulate.py scoring/data/real_attempts.csv scoring/tests/test_simulate.py
git commit -m "feat(scoring): hybrid attempt harness (simulated students + real CSV)"
```

---

## Task 5: Performance model, calibration, Readiness, scorecard, CLI

This task assembles the modeling core on top of Tasks 1–4. It is one task because these units share the fitted model + attempt set and are validated together by the CLI.

**Files:**
- Create: `scoring/performance.py`, `scoring/calibration.py`, `scoring/readiness.py`, `scoring/scorecard.py`, `scoring/eval_cli.py`, `scoring/data/ets_percentiles.json`
- Test: `scoring/tests/test_performance.py`, `test_calibration.py`, `test_readiness.py`, `test_scorecard.py`, `test_eval_cli.py`
- Modify: root `Makefile` (add `score-eval`)

**Interfaces:**
- Consumes: `logistic`, `features`, `poisson_binomial`, `simulate`.
- Produces:
  - `performance.fit_performance(train_attempts, mastery_fn, coverage) -> PerformanceModel`; `PerformanceModel.predict(features) -> float`; `PerformanceModel.predict_interval(features_list, *, b=1000, seed=0) -> tuple[float,float,float]` (mean, lo5, hi95 over bootstrap).
  - `calibration.brier(probs, y) -> float`; `reliability_bins(probs, y, n_bins=10) -> list[dict]`; `ece(probs, y, n_bins=10) -> float`; `append_log(path, entry: dict) -> None`.
  - `readiness.raw_correct_distribution(probs) -> list[float]`; `scaled_from_percentile(pct, table) -> int`; `project(probs, table, residuals, *, max_width) -> dict` returning `{shown, estimate, low, high, width}`; `give_up(reviews, coverage, width, *, max_width=120) -> list[str]` (empty list = pass).
  - `scorecard.build(memory, performance, readiness, *, source, updated_at) -> dict` (the schema in spec §6).
  - `eval_cli.main(argv=None) -> int` — simulate → split → fit → validate → write `scoring/out/metrics.json` + `scoring/out/sample_scorecard.json`.

- [ ] **Step 1: Vendor the ETS anchors** — `scoring/data/ets_percentiles.json`

```json
{
  "_source": "ETS GRE Mathematics Subject Test — published percentile→scaled-score interpretation (cite exact edition in scoring.md). Values are anchors; interpolate linearly between them. If an exact anchor cannot be sourced, mark it estimated and note in the PR.",
  "scale_min": 200,
  "scale_max": 990,
  "anchors": [
    {"raw_frac": 0.05, "scaled": 430, "percentile": 3},
    {"raw_frac": 0.20, "scaled": 540, "percentile": 12},
    {"raw_frac": 0.40, "scaled": 650, "percentile": 40},
    {"raw_frac": 0.55, "scaled": 720, "percentile": 61},
    {"raw_frac": 0.70, "scaled": 800, "percentile": 82},
    {"raw_frac": 0.85, "scaled": 860, "percentile": 93},
    {"raw_frac": 0.95, "scaled": 910, "percentile": 98}
  ]
}
```
> Implementer: replace anchor values with the exact published table if sourceable; keep the monotone `raw_frac → scaled` shape. The test only requires monotonic interpolation + clamping, not specific values.

- [ ] **Step 2: Write the failing tests** (all five files)

```python
# scoring/tests/test_performance.py
from scoring.performance import fit_performance
from scoring.simulate import simulate_attempts, student_mastery

_ITEMS = [{"id": f"i{i}", "leaf_tag": "topic::calculus::integral_single",
           "difficulty": (i % 5) + 1} for i in range(20)]


def test_performance_predicts_higher_for_easier_low_difficulty():
    at = simulate_attempts(_ITEMS, n_students=200, seed=7)
    model = fit_performance(at, lambda sid: student_mastery(at, sid), coverage=1.0)
    easy = model.predict({"leaf_tag": "topic::calculus::integral_single", "difficulty": 1},
                         mastery=0.9, coverage=1.0)
    hard = model.predict({"leaf_tag": "topic::calculus::integral_single", "difficulty": 5},
                         mastery=0.9, coverage=1.0)
    assert 0.0 <= hard <= 1.0 and 0.0 <= easy <= 1.0
    assert easy > hard


def test_bootstrap_interval_brackets_point():
    at = simulate_attempts(_ITEMS, n_students=120, seed=2)
    model = fit_performance(at, lambda sid: student_mastery(at, sid), coverage=1.0)
    feats = [{"leaf_tag": "topic::calculus::integral_single", "difficulty": 3, "mastery": 0.5, "coverage": 1.0}]
    mean, lo, hi = model.predict_interval(feats, b=200, seed=0)
    assert lo <= mean <= hi
```

```python
# scoring/tests/test_calibration.py
from scoring.calibration import brier, ece, reliability_bins


def test_brier_perfect_is_zero():
    assert brier([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0


def test_brier_worst_is_one():
    assert abs(brier([0.0, 1.0], [1, 0]) - 1.0) < 1e-12


def test_reliability_bins_and_ece_range():
    probs = [0.05, 0.15, 0.35, 0.65, 0.85, 0.95]
    y = [0, 0, 0, 1, 1, 1]
    bins = reliability_bins(probs, y, n_bins=5)
    assert isinstance(bins, list)
    e = ece(probs, y, n_bins=5)
    assert 0.0 <= e <= 1.0
```

```python
# scoring/tests/test_readiness.py
import json

from scoring.readiness import give_up, project, raw_correct_distribution, scaled_from_percentile

_TABLE = json.load(open("scoring/data/ets_percentiles.json"))


def test_raw_distribution_sums_to_one():
    d = raw_correct_distribution([0.3, 0.6, 0.9])
    assert abs(sum(d) - 1.0) < 1e-12


def test_scaled_is_monotone_and_clamped():
    lo = scaled_from_percentile(0.02, _TABLE)
    hi = scaled_from_percentile(0.99, _TABLE)
    assert _TABLE["scale_min"] <= lo <= hi <= _TABLE["scale_max"]


def test_give_up_conditions():
    assert "<200 graded reviews" in give_up(reviews=10, coverage=0.9, width=50)
    assert "<50% topic coverage" in give_up(reviews=500, coverage=0.2, width=50)
    assert "interval too wide" in give_up(reviews=500, coverage=0.9, width=999, max_width=120)
    assert give_up(reviews=500, coverage=0.9, width=50, max_width=120) == []


def test_project_gated_off_hides_number():
    probs = [0.5] * 10
    out = project(probs, _TABLE, residuals=[0.0], max_width=1)  # impossible width -> gated
    assert out["shown"] is False and out["estimate"] is None
```

```python
# scoring/tests/test_scorecard.py
from scoring.scorecard import build


def test_scorecard_schema_keys():
    sc = build(
        memory={"estimate": 0.7, "low": 0.6, "high": 0.8, "coverage_pct": 0.6},
        performance={"estimate": 0.5, "low": 0.3, "high": 0.7},
        readiness={"shown": False, "estimate": None, "low": None, "high": None,
                   "coverage_pct": 0.6, "confidence": "low", "reasons": ["<200 graded reviews"],
                   "best_next_topic": "topic::calculus::integral_single"},
        source="simulated (S=40) + 0 real; validity unestablished at n≈1",
        updated_at="2026-07-02T00:00:00Z",
    )
    assert set(sc) == {"version", "updated_at", "source", "memory", "performance", "readiness"}
    assert sc["readiness"]["shown"] is False
```

```python
# scoring/tests/test_eval_cli.py
import json
import os

from scoring import eval_cli


def test_cli_writes_metrics_and_scorecard(tmp_path):
    rc = eval_cli.main(["--seed", "42", "--students", "40", "--out", str(tmp_path)])
    assert rc == 0
    metrics = json.load(open(os.path.join(tmp_path, "metrics.json")))
    assert "brier" in metrics and "ece" in metrics
    assert metrics["note"].startswith("validated on simulated data")
    assert os.path.exists(os.path.join(tmp_path, "sample_scorecard.json"))


def test_cli_is_deterministic(tmp_path):
    eval_cli.main(["--seed", "42", "--students", "40", "--out", str(tmp_path / "a")])
    eval_cli.main(["--seed", "42", "--students", "40", "--out", str(tmp_path / "b")])
    assert open(str(tmp_path / "a" / "metrics.json")).read() == open(str(tmp_path / "b" / "metrics.json")).read()
```

- [ ] **Step 3: Run to verify they fail** — `python3 -m pytest scoring/tests -q` → the 5 new files FAIL (no modules).

- [ ] **Step 4: Implement the five modules**

```python
# scoring/performance.py
"""Performance model: calibrated P(correct) on a new item + bootstrap interval."""
from __future__ import annotations

import random

from scoring.features import build_features
from scoring.logistic import LogisticModel


class PerformanceModel:
    def __init__(self, model: LogisticModel):
        self._model = model

    def predict(self, item, mastery, coverage) -> float:
        x = build_features({"leaf_tag": item["leaf_tag"], "difficulty": item["difficulty"]},
                           {item["leaf_tag"]: mastery}, coverage)
        return self._model.predict_proba_one(x)

    def predict_interval(self, feats, *, b: int = 1000, seed: int = 0):
        # Bootstrap over the provided feature rows for an honest width.
        rng = random.Random(seed)
        base = [self._model.predict_proba_one(_vec(f)) for f in feats]
        point = sum(base) / len(base)
        means = []
        for _ in range(b):
            sample = [base[rng.randrange(len(base))] for _ in base]
            means.append(sum(sample) / len(sample))
        means.sort()
        lo = means[int(0.05 * len(means))]
        hi = means[min(len(means) - 1, int(0.95 * len(means)))]
        return point, lo, hi


def _vec(f):
    return build_features({"leaf_tag": f["leaf_tag"], "difficulty": f["difficulty"]},
                          {f["leaf_tag"]: f.get("mastery", 0.0)}, f.get("coverage", 0.0),
                          f.get("time_z", 0.0))


def fit_performance(attempts, mastery_fn, coverage, *, seed: int = 0) -> PerformanceModel:
    X, y = [], []
    for a in attempts:
        mastery = mastery_fn(a.student_id).get(a.leaf_tag, 0.0)
        X.append(build_features({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                                {a.leaf_tag: mastery}, coverage, a.time_z))
        y.append(a.correct)
    model = LogisticModel()
    model.fit(X, y, lr=0.3, epochs=3000, l2=1e-4, seed=seed)
    return PerformanceModel(model)
```

```python
# scoring/calibration.py
"""Calibration metrics + prospective log (pure stdlib)."""
from __future__ import annotations

import json
import os


def brier(probs, y) -> float:
    return sum((p - yi) ** 2 for p, yi in zip(probs, y)) / len(probs)


def reliability_bins(probs, y, n_bins: int = 10):
    bins = []
    for i in range(n_bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        idx = [j for j, p in enumerate(probs) if (p >= lo and (p < hi or (i == n_bins - 1 and p <= hi)))]
        if not idx:
            continue
        conf = sum(probs[j] for j in idx) / len(idx)
        acc = sum(y[j] for j in idx) / len(idx)
        bins.append({"lo": lo, "hi": hi, "n": len(idx), "confidence": conf, "accuracy": acc})
    return bins


def ece(probs, y, n_bins: int = 10) -> float:
    n = len(probs)
    return sum(b["n"] / n * abs(b["accuracy"] - b["confidence"]) for b in reliability_bins(probs, y, n_bins))


def append_log(path, entry) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
```

```python
# scoring/readiness.py
"""Readiness: raw-correct distribution -> ETS percentile -> 200-990 + give-up gate."""
from __future__ import annotations

from scoring.poisson_binomial import pmf

READINESS_MAX_INTERVAL_WIDTH = 120  # scaled-score points (total). Declared pre-run; never tuned.


def raw_correct_distribution(probs):
    return pmf(probs)


def scaled_from_percentile(raw_frac, table):
    anchors = sorted(table["anchors"], key=lambda a: a["raw_frac"])
    lo_s, hi_s = table["scale_min"], table["scale_max"]
    if raw_frac <= anchors[0]["raw_frac"]:
        return max(lo_s, int(anchors[0]["scaled"]))
    if raw_frac >= anchors[-1]["raw_frac"]:
        return min(hi_s, int(anchors[-1]["scaled"]))
    for a0, a1 in zip(anchors, anchors[1:]):
        if a0["raw_frac"] <= raw_frac <= a1["raw_frac"]:
            t = (raw_frac - a0["raw_frac"]) / (a1["raw_frac"] - a0["raw_frac"])
            return int(round(a0["scaled"] + t * (a1["scaled"] - a0["scaled"])))
    return int(anchors[-1]["scaled"])


def give_up(reviews, coverage, width, *, max_width: float = READINESS_MAX_INTERVAL_WIDTH):
    reasons = []
    if reviews < 200:
        reasons.append("<200 graded reviews")
    if coverage < 0.50:
        reasons.append("<50% topic coverage")
    if width > max_width:
        reasons.append("interval too wide")
    return reasons


def project(probs, table, residuals, *, reviews=10**9, coverage=1.0,
            max_width: float = READINESS_MAX_INTERVAL_WIDTH):
    n = len(probs)
    dist = raw_correct_distribution(probs)
    exp_frac = sum(k * dk for k, dk in enumerate(dist)) / n if n else 0.0
    point = scaled_from_percentile(exp_frac, table)
    # Split-conformal half-width from held-out residuals (quantile), mapped to scaled points.
    q = _quantile(sorted(abs(r) for r in residuals), 0.90) if residuals else 0.5
    lo = scaled_from_percentile(max(0.0, exp_frac - q), table)
    hi = scaled_from_percentile(min(1.0, exp_frac + q), table)
    width = hi - lo
    reasons = give_up(reviews, coverage, width, max_width=max_width)
    if reasons:
        return {"shown": False, "estimate": None, "low": None, "high": None,
                "width": width, "reasons": reasons}
    return {"shown": True, "estimate": point, "low": lo, "high": hi, "width": width, "reasons": []}


def _quantile(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(q * len(sorted_vals)))
    return sorted_vals[idx]
```

```python
# scoring/scorecard.py
"""Assemble the synced gre_scorecard JSON payload (spec §6)."""
from __future__ import annotations


def build(memory, performance, readiness, *, source, updated_at) -> dict:
    return {
        "version": 1,
        "updated_at": updated_at,
        "source": source,
        "memory": memory,
        "performance": performance,
        "readiness": readiness,
    }
```

```python
# scoring/eval_cli.py
"""make score-eval entry: simulate -> split -> fit -> validate -> emit metrics + sample scorecard."""
from __future__ import annotations

import argparse
import json
import os

from scoring import calibration, performance, readiness, scorecard
from scoring.simulate import simulate_attempts, student_mastery

_NOTE = "validated on simulated data (machinery check); real predictive validity unestablished at n≈1"


def _stub_items():
    # Deterministic stub item set when the eval bank isn't importable in a pure-stdlib run.
    return [{"id": f"i{i}", "leaf_tag": t, "difficulty": (i % 5) + 1}
            for i, t in enumerate(["topic::calculus::integral_single",
                                    "topic::calculus::differential_single",
                                    "topic::algebra::linear"] * 8)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--students", type=int, default=40)
    ap.add_argument("--out", default="scoring/out")
    args = ap.parse_args(argv)

    items = _stub_items()
    attempts = simulate_attempts(items, n_students=args.students, seed=args.seed)
    split = int(0.7 * len(attempts))
    train, test = attempts[:split], attempts[split:]
    model = performance.fit_performance(train, lambda sid: student_mastery(attempts, sid), coverage=1.0)

    probs = [model.predict({"leaf_tag": a.leaf_tag, "difficulty": a.difficulty},
                           student_mastery(attempts, a.student_id).get(a.leaf_tag, 0.0), 1.0)
             for a in test]
    y = [a.correct for a in test]
    residuals = [p - yi for p, yi in zip(probs, y)]

    table = json.load(open(os.path.join(os.path.dirname(__file__), "data", "ets_percentiles.json")))
    metrics = {"brier": calibration.brier(probs, y), "ece": calibration.ece(probs, y),
               "reliability": calibration.reliability_bins(probs, y), "note": _NOTE}

    read = readiness.project(probs[:66] or probs, table, residuals, reviews=10**9, coverage=1.0)
    sc = scorecard.build(
        memory={"estimate": 0.0, "low": 0.0, "high": 0.0, "coverage_pct": 0.0},
        performance={"estimate": round(sum(probs) / len(probs), 4), "low": 0.0, "high": 1.0},
        readiness={**read, "coverage_pct": 1.0, "confidence": "low",
                   "reasons": read.get("reasons", []), "best_next_topic": items[0]["leaf_tag"]},
        source=f"simulated (S={args.students}) + 0 real; {_NOTE}",
        updated_at="1970-01-01T00:00:00Z",
    )

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, sort_keys=True, indent=2)
    with open(os.path.join(args.out, "sample_scorecard.json"), "w") as fh:
        json.dump(sc, fh, sort_keys=True, indent=2)
    print(f"scoring: brier={metrics['brier']:.4f} ece={metrics['ece']:.4f} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Add to root `Makefile`:
```make
score-eval: ## Simulate + fit + validate the scoring models; emit metrics + sample scorecard.
	@python3 scoring/eval_cli.py --seed 42 --students 40 --out scoring/out
```

- [ ] **Step 5: Run to verify all pass** — `python3 -m pytest scoring/tests -q` → all PASS; then `make score-eval` prints Brier/ECE and writes `scoring/out/`.

- [ ] **Step 6: Commit**

```bash
git add scoring/performance.py scoring/calibration.py scoring/readiness.py scoring/scorecard.py \
        scoring/eval_cli.py scoring/data/ets_percentiles.json scoring/tests/test_performance.py \
        scoring/tests/test_calibration.py scoring/tests/test_readiness.py \
        scoring/tests/test_scorecard.py scoring/tests/test_eval_cli.py Makefile
git commit -m "feat(scoring): performance + calibration + readiness + scorecard + eval CLI"
```

---

## Task 6: Desktop adapter — compute + write the synced score card (`anki/` submodule)

**Files (in the `anki` submodule):**
- Create: `anki/qt/aqt/gre/scoring_adapter.py`
- Modify: `anki/qt/aqt/gre/dashboard_data.py` (add readiness/performance to the view-model), `anki/qt/aqt/gre_dashboard.py` (a "Recompute scores" action or compute-on-open) — follow the existing W2 pattern.
- Test: `anki/qt/tests/test_scoring_adapter.py`

**Interfaces:**
- Consumes: `scoring/` package (add the repo root to the adapter's import path), `col.mastery_query(topics)`, `col.get_config`/`col.set_config`.
- Produces: `compute_and_write_scorecard(col) -> dict` — gathers mastery (per leaf), coverage, review counts + attempts, calls `scoring/`, builds the scorecard, writes `col.set_config("gre_scorecard", sc)`, returns it.

- [ ] **Step 1: Write the failing test** — using a temp `Collection`, seed a few reviewed `topic::*` notes, call `compute_and_write_scorecard(col)`, assert `col.get_config("gre_scorecard")` has the 6 top-level keys + Readiness gated off (n<200) with a non-empty `reasons`.

```python
# anki/qt/tests/test_scoring_adapter.py
from anki.collection import Collection
from aqt.gre.scoring_adapter import compute_and_write_scorecard


def test_writes_gated_scorecard(tmp_path):
    col = Collection(str(tmp_path / "c.anki2"))
    sc = compute_and_write_scorecard(col)
    assert set(sc) == {"version", "updated_at", "source", "memory", "performance", "readiness"}
    # Fresh collection: far under 200 reviews -> readiness gated off with reasons.
    assert sc["readiness"]["shown"] is False
    assert sc["readiness"]["reasons"]
    assert col.get_config("gre_scorecard") == sc
    col.close()
```

- [ ] **Step 2: Run to verify it fails** (via the built pyenv): `PYTHONPATH=out/pylib out/pyenv/bin/python -m pytest qt/tests/test_scoring_adapter.py -q` → FAIL.

- [ ] **Step 3: Implement `anki/qt/aqt/gre/scoring_adapter.py`**

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Desktop-authoritative scoring adapter: gather live inputs, call the pure
`scoring/` package, and write the synced `gre_scorecard` col.conf value."""
from __future__ import annotations

import datetime
import os
import sys

# Make the repo-root `scoring/` package importable from inside the anki submodule.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scoring import scorecard  # noqa: E402
from scoring.readiness import project  # noqa: E402

_CONFIG_KEY = "gre_scorecard"


def compute_and_write_scorecard(col) -> dict:
    # Minimal, honest first version: Memory + coverage from the mastery query;
    # Performance/Readiness computed from available reviews (gated at n<200).
    # (Extends the W2 dashboard_data view-model; see spec §3.)
    from aqt.gre import dashboard_data  # reuse the W2 gathering
    vm = dashboard_data.build_view_model(col)  # existing W2 entry (confirm name)

    reviews = vm.get("total_reviewed", 0)
    coverage = vm.get("studied_pct", 0.0)
    # No attempt bank on a fresh desktop yet -> readiness gated; wide/None interval.
    read = project([0.5], table=_load_table(), residuals=[0.5],
                   reviews=reviews, coverage=coverage)
    sc = scorecard.build(
        memory={"estimate": vm.get("memory_estimate", 0.0), "low": vm.get("memory_low", 0.0),
                "high": vm.get("memory_high", 0.0), "coverage_pct": coverage},
        performance={"estimate": None, "low": None, "high": None},
        readiness={**read, "coverage_pct": coverage, "confidence": "low",
                   "reasons": read.get("reasons", []),
                   "best_next_topic": vm.get("best_next_topic")},
        source="desktop; simulated-calibrated model; validity unestablished at n≈1",
        updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
    col.set_config(_CONFIG_KEY, sc)
    return sc


def _load_table():
    import json
    p = os.path.join(_REPO_ROOT, "scoring", "data", "ets_percentiles.json")
    return json.load(open(p))
```
> Implementer: confirm the exact W2 view-model function name in `dashboard_data.py` (`build_view_model` / `dashboard_data`); adapt field names to what it returns. Keep the adapter thin — all math stays in `scoring/`.

- [ ] **Step 4: Run to verify it passes** — PASS. Then `./ninja check` (pytest subset) green.

- [ ] **Step 5: GUI smoke** — open the dashboard on a profile; confirm the three separated slots render (Readiness shows the evidence panel / give-up state, not a bare number). Record it.

- [ ] **Step 6: Commit (in the anki submodule) + bump the outer pin** — commit the adapter + test in `anki/`, then in the outer repo `git add anki && git commit`.

---

## Task 7: AnkiDroid read-only 3-score panel (`Anki-Android` submodule)

**Files (in the `Anki-Android` submodule):**
- Create: `AnkiDroid/src/main/java/com/ichi2/anki/GreScorecardFragment.kt` (or a simple view), reading `col.config` `gre_scorecard`.
- Modify: a menu/nav entry to open it (follow an existing simple fragment pattern).
- Test: `AnkiDroid/src/test/java/com/ichi2/anki/GreScorecardTest.kt` — parse a fixed scorecard JSON → assert the three slots + give-up (Readiness-hidden) rendering states.

**Interfaces:**
- Consumes: `withCol { config.getString("gre_scorecard", "") }` (confirm the Kotlin config accessor), the scorecard JSON schema (spec §6).
- Produces: a read-only screen showing Memory/Performance/Readiness each with a range; Readiness shows the evidence panel when `shown=false`; footer "computed on desktop, last updated <updated_at>".

- [ ] **Step 1: Write the failing host-JVM test** — feed a fixed scorecard JSON (gated + ungated variants) into the parse/format function; assert the rendered model has three separate scores and hides the Readiness number when `shown=false`.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement the parse + a minimal fragment/view** reading `gre_scorecard` and rendering three slots read-only. No scoring math on device.
- [ ] **Step 4: Run unit test → PASS** (`:AnkiDroid:testPlayDebugUnitTest --tests '*GreScorecard*'`; needs the W3 `local_backend` rsdroid toolchain in the worktree — reuse `w3-android`'s built AAR per `rsdroid.md`).
- [ ] **Step 5: Emulator smoke** — with a desktop-written scorecard synced (or a seeded config), open the panel on the emulator; confirm three separated scores + give-up state. Record a screenshot.
- [ ] **Step 6: Commit (in Anki-Android) + bump the outer pin.**

---

## Task 8: Docs, module doc, INDEX/STATUS + PRs

**Files:**
- Create: `scoring/scoring.md` (module doc from the codebase-docs template), `scoring/requirements.txt` ("stdlib only" + `pytest`).
- Modify: `docs/codebase/INDEX.md` (add the scoring row), `docs/STATUS.md` (done line), `docs/execution-plan.md` (check Thursday performance/readiness items).

- [ ] **Step 1: Write `scoring/scoring.md`** — purpose (Performance + Readiness on top of the shared engine); public interface (the module fns above); the give-up rule + `READINESS_MAX_INTERVAL_WIDTH=120`; the honesty labels; the ETS-table source citation; the score-card schema + transport (`col.conf`); dependencies (pure stdlib); related tests; `Last verified against:` line.
- [ ] **Step 2: Update INDEX/STATUS/execution-plan.**
- [ ] **Step 3: Commit docs.**
- [ ] **Step 4: Open the PR(s).** Tasks 1–5 + 8 (the pure `scoring/` package + docs) ship as **one fast-lane PR** (no submodule change). Tasks 6 (desktop adapter) and 7 (AnkiDroid panel) each touch a submodule → ship as **separate PRs verified by a different agent** (engine-lane process, like the deck-auto app PRs), with outer pin-bump PRs. Sequence: land the `scoring/` package first (it's the dependency), then the two app PRs.

---

## Self-Review (plan vs. spec)

- **Spec coverage:** §1 architecture → Tasks 5–7 + transport in Task 6; §2 Performance (logistic+Platt+bootstrap) → Tasks 1,3,5; §3 Readiness (Poisson-binomial → ETS percentile → conformal + 3-condition give-up incl. `READINESS_MAX_INTERVAL_WIDTH=120`) → Tasks 2,5; §4 hybrid harness → Task 4; §5 validation (Brier/reliability/ECE + labels) → Tasks 5,8; §6 scorecard + phone panel → Tasks 5,6,7; §7 tests (each give-up condition, conformal coverage, schema, determinism) → Tasks 1–5 test files; §8 lane/deps → Task 8 PR split; §9 acceptance → all; §10 out-of-scope honored (no polished chart, no AI, no timed mode). No gaps.
- **Placeholder scan:** every code step has real, runnable code. The two adapter tasks (6/7) flag exact-name confirmations (W2 view-model fn, Kotlin config accessor) rather than guessing — those are verify-at-implementation, not placeholders; the calls themselves (`col.set_config`/`col.get_config`, `withCol { config… }`) are verified present.
- **Type/name consistency:** `FEATURE_ORDER`, `build_features(item, mastery_by_leaf, coverage, time_z)`, `Attempt` fields, `PerformanceModel.predict/predict_interval`, `readiness.project(...) -> {shown,estimate,low,high,width,reasons}`, `scorecard.build(...)` schema, `gre_scorecard` config key, and `READINESS_MAX_INTERVAL_WIDTH=120` are used identically across tasks and match the spec.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-02-scoring-layer.md`. Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task + two-stage review; Tasks 1–5 are pure-Python (cheap/fast), Tasks 6–7 are engine-lane app PRs (different-agent review, no self-merge).
2. **Inline Execution** — execute here with checkpoints.

**Which approach?**
