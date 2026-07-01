# W2 — Desktop Dashboard (Memory Score + Coverage Map) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a read-only desktop dashboard that turns the merged `MasteryQuery` RPC into an honest Memory score (as a range) + a 17-leaf coverage map, with Readiness/Performance rendered as separated, non-blended placeholder slots.

**Architecture:** A pure, unit-tested Python view-model (`aqt/gre/dashboard_data.py`) computes memory %+Wilson CI, ETS 50/25/25 rollups, coverage %s, and the next-best topic from the RPC counts. A read-only `mediasrv` POST endpoint calls `mw.col.mastery_query(...)` and returns the view-model as JSON. A `QDialog` opens a SvelteKit route (`gre-dashboard/`) that fetches that JSON and renders it. The engine stays generic; GRE knowledge lives only in the view-model + a vendored taxonomy JSON.

**Tech Stack:** Python 3 (aqt), Flask (mediasrv), Qt (PyQt6 `QDialog`/`QAction`), SvelteKit/TypeScript (Vite), pytest.

## Global Constraints

- **Read-only, hard ceiling:** no mutations; the endpoint calls only the existing W1 read RPC and returns data; **never** emit `OpChanges`, never call `transact`/`transact_no_undo`. (PRD D1; `docs/codebase/qt.md`.)
- **Never blend the three scores.** Memory / Performance / Readiness are separate slots; no combined "overall" number. (PRD §7; `AGENTS.md`.)
- **No readiness number in W2.** Readiness shows only the "Insufficient evidence to score" gate state (never a number without the full evidence panel). (PRD §7 Honesty Rule.)
- **Memory is aggregate-calibrated, not personalized** — microcopy must say so; do not claim personal calibration. (PRD §7.)
- **Taxonomy = frozen 17 leaves / 3 buckets / weights 50/25/25**, verbatim from PRD Appendix A; never fabricate intra-bucket weights. (PRD §6.)
- **Lane = fast lane by risk** (Qt/TS-UI only, read-only; no `rslib`/`.proto`/`pylib` FFI/undo/store), executed with W1's fork-worktree + `.gitmodules`/gitlink-bump mechanics because files live in `f15cubing/anki`. Self-review against the fast-lane checklist; docs + submodule SHA bumped in the same PR. If a reviewer judges the submodule surface engine-risky, escalate to the engine lane.
- **Spec:** `docs/superpowers/specs/2026-06-30-w2-desktop-dashboard-design.md`. **Consumes W1:** `mw.col.mastery_query(topics) -> Sequence[TopicMastery{topic,total_cards,reviewed_count,mastered_count,avg_recall}]` (hierarchical tag match; single-field response unwrapped by codegen).

---

## File Structure

Inside the fork `anki/` (worktree):
- `qt/aqt/gre/__init__.py` — package marker.
- `qt/aqt/gre/taxonomy.json` — vendored 17-leaf taxonomy + buckets + weights (source: PRD Appendix A).
- `qt/aqt/gre/dashboard_data.py` — **pure** view-model (no `aqt` import): taxonomy loader, Wilson, headline, coverage, next-best, `build_view_model`.
- `qt/aqt/gre_dashboard.py` — `QDialog` + Tools-menu `QAction` (imports `aqt`).
- `qt/aqt/mediasrv.py` — **modify**: register `gre-dashboard` page + add the `gre_dashboard_data` read endpoint.
- `qt/aqt/main.py` — **modify** (one line): call the menu installer at init (or via `gui_hooks.main_window_did_init`).
- `ts/routes/gre-dashboard/+page.svelte` (+ `MemoryPanel.svelte`, `CoverageMap.svelte`, `ScoreSlot.svelte`) — presentation.
- `qt/tests/test_gre_dashboard_data.py` — pure unit tests for the view-model.
- `qt/tests/test_gre_dashboard_mediasrv.py` — endpoint registration + read-only + JSON-shape test.

Outer repo:
- `tests/test_taxonomy_sync.py` — asserts the vendored JSON matches `pipeline/taxonomy.py`.
- Docs: `docs/codebase/INDEX.md`, `docs/codebase/qt.md`, `docs/STATUS.md`, `docs/execution-plan.md`.

**Test-runner note:** `dashboard_data.py` is pure (stdlib only), so its tests run headless. Primary command from `anki/`: `./ninja check:pytest:qt` (if the exact target name differs, list with `./ninja -t targets all | grep pytest`). For a fast local loop on the pure module: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`. The outer sync test runs from the repo root with the repo `.venv`: `python -m pytest tests/test_taxonomy_sync.py -v`.

---

## Task 1: Vendored taxonomy + loader + drift guard

**Files:**
- Create: `anki/qt/aqt/gre/__init__.py`
- Create: `anki/qt/aqt/gre/taxonomy.json`
- Create: `anki/qt/aqt/gre/dashboard_data.py` (loader portion)
- Test: `anki/qt/tests/test_gre_dashboard_data.py` (loader tests)
- Test: `tests/test_taxonomy_sync.py` (outer repo)

**Interfaces:**
- Produces: `load_taxonomy() -> Taxonomy`; `Taxonomy.buckets: list[Bucket]` where `Bucket = {name:str, weight:float, leaves:list[str]}`; `leaf_tag(bucket,leaf)->str`; `bucket_tag(bucket)->str`; `all_leaf_tags()->list[str]`; `all_bucket_tags()->list[str]`; `query_topics()->list[str]` (= all leaf tags then all bucket tags, taxonomy order).

- [ ] **Step 1: Write the vendored taxonomy JSON**

Create `anki/qt/aqt/gre/taxonomy.json` (source: PRD Appendix A; identical data to `pipeline/taxonomy.py`):

```json
{
  "tag_prefix": "topic",
  "tag_sep": "::",
  "buckets": [
    { "name": "calculus", "weight": 0.50,
      "leaves": ["differential_single", "integral_single", "differential_multi",
                 "integral_multi", "differential_equations", "applications"] },
    { "name": "algebra", "weight": 0.25,
      "leaves": ["elementary", "linear", "abstract", "number_theory"] },
    { "name": "additional", "weight": 0.25,
      "leaves": ["real_analysis", "discrete", "topology", "geometry",
                 "complex", "probability_stats", "numerical"] }
  ]
}
```

- [ ] **Step 2: Create the package marker**

Create `anki/qt/aqt/gre/__init__.py` with the standard Anki copyright header:

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
```

- [ ] **Step 3: Write the failing loader test**

Create `anki/qt/tests/test_gre_dashboard_data.py`:

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from aqt.gre import dashboard_data as dd


def test_taxonomy_has_17_leaves_and_weights_sum_to_one():
    tax = dd.load_taxonomy()
    leaves = [leaf for b in tax.buckets for leaf in b.leaves]
    assert len(leaves) == 17
    assert abs(sum(b.weight for b in tax.buckets) - 1.0) < 1e-9
    assert [b.name for b in tax.buckets] == ["calculus", "algebra", "additional"]


def test_query_topics_lists_leaf_tags_then_bucket_tags():
    tax = dd.load_taxonomy()
    topics = dd.query_topics()
    assert topics[0] == "topic::calculus::differential_single"
    assert topics[16] == "topic::additional::numerical"
    assert topics[17:] == ["topic::calculus", "topic::algebra", "topic::additional"]
```

- [ ] **Step 4: Run it to verify it fails**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`
Expected: FAIL (`ModuleNotFoundError`/`AttributeError` — `dashboard_data`/`load_taxonomy` missing).

- [ ] **Step 5: Implement the loader in `dashboard_data.py`**

Create `anki/qt/aqt/gre/dashboard_data.py`:

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Pure view-model for the GRE desktop dashboard (W2).

No aqt/anki imports: it maps W1 MasteryQuery rows onto the frozen GRE taxonomy
and computes the Memory range (Wilson), 50/25/25 rollups, coverage, and the
next-best topic. Kept importable headless so it is unit-testable.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

_TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")


@dataclass(frozen=True)
class Bucket:
    name: str
    weight: float
    leaves: tuple[str, ...]


@dataclass(frozen=True)
class Taxonomy:
    tag_prefix: str
    tag_sep: str
    buckets: tuple[Bucket, ...]


def load_taxonomy() -> Taxonomy:
    raw = json.loads(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    buckets = tuple(
        Bucket(name=b["name"], weight=float(b["weight"]), leaves=tuple(b["leaves"]))
        for b in raw["buckets"]
    )
    return Taxonomy(tag_prefix=raw["tag_prefix"], tag_sep=raw["tag_sep"], buckets=buckets)


def leaf_tag(bucket: str, leaf: str, tax: Taxonomy | None = None) -> str:
    tax = tax or load_taxonomy()
    return tax.tag_sep.join((tax.tag_prefix, bucket, leaf))


def bucket_tag(bucket: str, tax: Taxonomy | None = None) -> str:
    tax = tax or load_taxonomy()
    return tax.tag_sep.join((tax.tag_prefix, bucket))


def all_leaf_tags(tax: Taxonomy | None = None) -> list[str]:
    tax = tax or load_taxonomy()
    return [leaf_tag(b.name, leaf, tax) for b in tax.buckets for leaf in b.leaves]


def all_bucket_tags(tax: Taxonomy | None = None) -> list[str]:
    tax = tax or load_taxonomy()
    return [bucket_tag(b.name, tax) for b in tax.buckets]


def query_topics(tax: Taxonomy | None = None) -> list[str]:
    tax = tax or load_taxonomy()
    return all_leaf_tags(tax) + all_bucket_tags(tax)
```

- [ ] **Step 6: Run the loader tests to verify they pass**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`
Expected: PASS (2 tests).

- [ ] **Step 7: Write the failing outer-repo sync test**

Create `tests/test_taxonomy_sync.py` (repo root):

```python
"""Guard: the dashboard's vendored taxonomy must equal pipeline/taxonomy.py."""
import json
from pathlib import Path

from pipeline import taxonomy as tx

VENDORED = Path(__file__).resolve().parents[1] / "anki/qt/aqt/gre/taxonomy.json"


def test_vendored_taxonomy_matches_pipeline():
    data = json.loads(VENDORED.read_text(encoding="utf-8"))
    assert tuple(b["name"] for b in data["buckets"]) == tx.BUCKETS
    for b in data["buckets"]:
        assert b["weight"] == tx.BUCKET_WEIGHTS[b["name"]]
        assert tuple(b["leaves"]) == tx.LEAVES_BY_BUCKET[b["name"]]
    # derived full leaf tags match, in order
    vendored_tags = [
        f'{data["tag_prefix"]}{data["tag_sep"]}{b["name"]}{data["tag_sep"]}{leaf}'
        for b in data["buckets"] for leaf in b["leaves"]
    ]
    assert tuple(vendored_tags) == tx.LEAF_TAGS
```

- [ ] **Step 8: Run the sync test to verify it passes**

Run (repo root, with `.venv` active): `python -m pytest tests/test_taxonomy_sync.py -v`
Expected: PASS. (If `pipeline` isn't importable, run `pip install -e .` is NOT needed — run from repo root so `pipeline/` is on the path; the repo `.venv` already has `pipeline/requirements.txt` installed.)

- [ ] **Step 9: Commit**

```bash
git add anki/qt/aqt/gre/__init__.py anki/qt/aqt/gre/taxonomy.json anki/qt/aqt/gre/dashboard_data.py anki/qt/tests/test_gre_dashboard_data.py
git commit -m "feat(gre): vendor W2 dashboard taxonomy + loader"
# outer repo (separate commit in the outer worktree):
git add tests/test_taxonomy_sync.py && git commit -m "test(gre): guard vendored taxonomy against pipeline drift"
```

---

## Task 2: Memory math — Wilson interval + 50/25/25 headline

**Files:**
- Modify: `anki/qt/aqt/gre/dashboard_data.py`
- Test: `anki/qt/tests/test_gre_dashboard_data.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `wilson_interval(mastered:int, reviewed:int, z:float=1.96) -> tuple[float,float,float]` returning `(point, low, high)` where `point = mastered/reviewed` (0.0 when `reviewed==0`); `headline(bucket_points:list[dict]) -> dict|None` where each input dict is `{"weight":float,"point":float,"reviewed":int}` and output is `{"point","low","high","buckets_reflected","buckets_total"}` or `None` when no bucket has reviews.

- [ ] **Step 1: Write the failing tests**

Append to `anki/qt/tests/test_gre_dashboard_data.py`:

```python
import pytest
from aqt.gre import dashboard_data as dd


def test_wilson_zero_reviews_is_all_zero():
    assert dd.wilson_interval(0, 0) == (0.0, 0.0, 0.0)


def test_wilson_known_value():
    point, low, high = dd.wilson_interval(8, 10)
    assert point == pytest.approx(0.8)
    assert low == pytest.approx(0.490, abs=0.01)
    assert high == pytest.approx(0.943, abs=0.01)


def test_wilson_bounds_are_clamped_to_unit_interval():
    for m, n in [(0, 5), (5, 5)]:
        _, low, high = dd.wilson_interval(m, n)
        assert 0.0 <= low <= high <= 1.0


def test_headline_none_when_no_reviews():
    assert dd.headline([{"weight": 0.5, "point": 0.0, "reviewed": 0}]) is None


def test_headline_reweights_when_a_bucket_has_no_reviews():
    out = dd.headline([
        {"weight": 0.50, "point": 0.8, "reviewed": 10},
        {"weight": 0.25, "point": 0.6, "reviewed": 5},
        {"weight": 0.25, "point": 0.0, "reviewed": 0},  # excluded + renormalized
    ])
    assert out["point"] == pytest.approx(0.7333, abs=0.001)
    assert out["buckets_reflected"] == 2
    assert out["buckets_total"] == 3
    assert 0.0 <= out["low"] <= out["point"] <= out["high"] <= 1.0
```

- [ ] **Step 2: Run to verify they fail**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`
Expected: FAIL (`wilson_interval`/`headline` missing).

- [ ] **Step 3: Implement the math**

Append to `anki/qt/aqt/gre/dashboard_data.py`:

```python
def wilson_interval(mastered: int, reviewed: int, z: float = 1.96) -> tuple[float, float, float]:
    """(point, low, high). point = raw proportion; [low,high] = Wilson score CI."""
    if reviewed <= 0:
        return (0.0, 0.0, 0.0)
    n = reviewed
    p = mastered / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def headline(bucket_points: list[dict], z: float = 1.96) -> dict | None:
    """ETS-weighted (50/25/25) headline over buckets that have reviews.

    Buckets with reviewed==0 are excluded and remaining weights renormalized.
    Interval via weighted normal error propagation over the pooled proportions.
    """
    present = [b for b in bucket_points if b["reviewed"] > 0]
    if not present:
        return None
    wsum = sum(b["weight"] for b in present)
    point = sum((b["weight"] / wsum) * b["point"] for b in present)
    var = 0.0
    for b in present:
        w = b["weight"] / wsum
        p = b["point"]
        var += w * w * p * (1 - p) / b["reviewed"]
    se = math.sqrt(var)
    return {
        "point": point,
        "low": max(0.0, point - z * se),
        "high": min(1.0, point + z * se),
        "buckets_reflected": len(present),
        "buckets_total": len(bucket_points),
    }
```

- [ ] **Step 4: Run to verify they pass**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`
Expected: PASS (all Task 1 + Task 2 tests).

- [ ] **Step 5: Commit**

```bash
git add anki/qt/aqt/gre/dashboard_data.py anki/qt/tests/test_gre_dashboard_data.py
git commit -m "feat(gre): Wilson interval + 50/25/25 memory headline"
```

---

## Task 3: Coverage, next-best topic, and `build_view_model`

**Files:**
- Modify: `anki/qt/aqt/gre/dashboard_data.py`
- Test: `anki/qt/tests/test_gre_dashboard_data.py`

**Interfaces:**
- Consumes: `load_taxonomy`, `query_topics`, `wilson_interval`, `headline`.
- Produces: `build_view_model(rows_by_tag: dict[str, Row], *, generated_at: str) -> dict`, where `Row` is any object with int attrs `total_cards`, `reviewed_count`, `mastered_count` and float `avg_recall` (duck-typed; W1's `TopicMastery` satisfies it). Output matches the spec §3 view-model shape. Also `next_best_topic(rows_by_tag, tax) -> str | None`.

- [ ] **Step 1: Write the failing tests**

Append to `anki/qt/tests/test_gre_dashboard_data.py`:

```python
from dataclasses import dataclass as _dc


@_dc
class FakeRow:
    total_cards: int = 0
    reviewed_count: int = 0
    mastered_count: int = 0
    avg_recall: float = 0.0


def _rows(**overrides):
    """All 20 topics zeroed, then apply overrides by tag."""
    rows = {t: FakeRow() for t in dd.query_topics()}
    rows.update(overrides)
    return rows


def test_empty_collection_suppresses_headline_and_gates_readiness():
    vm = dd.build_view_model(_rows(), generated_at="t")
    assert vm["memory"]["headline"] is None
    assert vm["coverage"]["deck_pct"] == 0.0
    assert vm["coverage"]["studied_pct"] == 0.0
    assert vm["readiness"]["state"] == "insufficient_evidence"
    assert vm["performance"]["state"] == "not_available"


def test_coverage_counts_deck_and_studied():
    vm = dd.build_view_model(_rows(**{
        "topic::calculus::integral_single": FakeRow(total_cards=5, reviewed_count=3, mastered_count=2, avg_recall=0.7),
        "topic::algebra::linear": FakeRow(total_cards=4, reviewed_count=0, mastered_count=0),
    }), generated_at="t")
    assert vm["coverage"]["deck_pct"] == pytest.approx(2 / 17)
    assert vm["coverage"]["studied_pct"] == pytest.approx(1 / 17)


def test_next_best_topic_prefers_highest_weight_uncovered_leaf():
    # nothing studied -> highest-weight bucket (calculus) first leaf, taxonomy order
    assert dd.next_best_topic(_rows(), dd.load_taxonomy()) == "topic::calculus::differential_single"


def test_headline_uses_bucket_rows_rolled_up_by_rpc():
    vm = dd.build_view_model(_rows(**{
        "topic::calculus": FakeRow(total_cards=100, reviewed_count=10, mastered_count=8, avg_recall=0.82),
        "topic::algebra": FakeRow(total_cards=40, reviewed_count=5, mastered_count=3, avg_recall=0.6),
    }), generated_at="t")
    assert vm["memory"]["headline"]["point"] == pytest.approx(0.7333, abs=0.001)
    assert vm["memory"]["headline"]["buckets_reflected"] == 2
```

- [ ] **Step 2: Run to verify they fail**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`
Expected: FAIL (`build_view_model`/`next_best_topic` missing).

- [ ] **Step 3: Implement coverage + next-best + build_view_model**

Append to `anki/qt/aqt/gre/dashboard_data.py`:

```python
def _memory_cell(row) -> dict:
    point, low, high = wilson_interval(row.mastered_count, row.reviewed_count)
    return {
        "point": point, "low": low, "high": high,
        "reviewed": row.reviewed_count, "total": row.total_cards,
        "mean_r": row.avg_recall,
    }


def next_best_topic(rows_by_tag: dict, tax: Taxonomy) -> str | None:
    leaves = [(b, leaf, leaf_tag(b.name, leaf, tax)) for b in tax.buckets for leaf in b.leaves]
    # 1) highest exam-weight uncovered leaf; ties -> taxonomy order
    uncovered = [(b, tag) for (b, _leaf, tag) in leaves if rows_by_tag[tag].reviewed_count == 0]
    if uncovered:
        uncovered.sort(key=lambda bt: -bt[0].weight)  # stable -> preserves taxonomy order in ties
        return uncovered[0][1]
    # 2) all studied -> lowest memory lower-bound; ties -> taxonomy order
    best_tag, best_low = None, 2.0
    for (_b, _leaf, tag) in leaves:
        _, low, _ = wilson_interval(rows_by_tag[tag].mastered_count, rows_by_tag[tag].reviewed_count)
        if low < best_low:
            best_low, best_tag = low, tag
    return best_tag


def build_view_model(rows_by_tag: dict, *, generated_at: str) -> dict:
    tax = load_taxonomy()
    # buckets
    bucket_vms, bucket_points = [], []
    for b in tax.buckets:
        row = rows_by_tag[bucket_tag(b.name, tax)]
        cell = _memory_cell(row)
        bucket_points.append({"weight": b.weight, "point": cell["point"], "reviewed": row.reviewed_count})
        bucket_vms.append({"bucket": b.name, "weight": b.weight, **cell})
    # leaves + coverage
    leaf_vms, deck, studied = [], 0, 0
    for b in tax.buckets:
        for leaf in b.leaves:
            tag = leaf_tag(b.name, leaf, tax)
            row = rows_by_tag[tag]
            if row.total_cards > 0:
                deck += 1
            if row.reviewed_count > 0:
                studied += 1
            leaf_vms.append({
                "tag": tag, "bucket": b.name, "leaf": leaf,
                "has_cards": row.total_cards > 0,
                "studied": row.reviewed_count > 0,
                "memory": _memory_cell(row) if row.reviewed_count > 0 else None,
            })
    n_leaves = len(leaf_vms)
    studied_pct = studied / n_leaves if n_leaves else 0.0
    reasons = []
    if studied_pct < 0.50:
        reasons.append("<50% studied coverage")
    total_reviewed = sum(rows_by_tag[bucket_tag(b.name, tax)].reviewed_count for b in tax.buckets)
    if total_reviewed < 200:
        reasons.append("<200 graded reviews")
    return {
        "generated_at": generated_at,
        "memory": {"headline": headline(bucket_points), "buckets": bucket_vms},
        "coverage": {
            "deck_pct": deck / n_leaves if n_leaves else 0.0,
            "studied_pct": studied_pct,
            "leaves": leaf_vms,
        },
        "readiness": {
            "state": "insufficient_evidence",
            "studied_pct": studied_pct,
            "next_best_topic": next_best_topic(rows_by_tag, tax),
            "reasons": reasons,
        },
        "performance": {"state": "not_available", "note": "Arrives Thursday (MCQ surface)."},
    }
```

- [ ] **Step 4: Run to verify they pass**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_data.py -v`
Expected: PASS (all view-model tests).

- [ ] **Step 5: Commit**

```bash
git add anki/qt/aqt/gre/dashboard_data.py anki/qt/tests/test_gre_dashboard_data.py
git commit -m "feat(gre): coverage, next-best topic, and build_view_model"
```

---

## Task 4: Read-only mediasrv endpoint + page registration

**Files:**
- Modify: `anki/qt/aqt/mediasrv.py`
- Test: `anki/qt/tests/test_gre_dashboard_mediasrv.py`

**Interfaces:**
- Consumes: `dashboard_data.query_topics`, `dashboard_data.build_view_model`; `aqt.mw.col.mastery_query`.
- Produces: POST endpoint `greDashboardData` (path `/_anki/greDashboardData`) returning `application/json`; `gre-dashboard` recognized by `is_sveltekit_page`.

- [ ] **Step 1: Write the failing test**

Create `anki/qt/tests/test_gre_dashboard_mediasrv.py`:

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import json
import types

import aqt.mediasrv as m
from aqt.gre import dashboard_data as dd


def test_page_and_endpoint_are_registered():
    assert m.is_sveltekit_page("gre-dashboard")
    assert "greDashboardData" in m.post_handlers


def test_endpoint_returns_view_model_and_is_read_only(monkeypatch):
    from dataclasses import dataclass

    @dataclass
    class Row:
        topic: str
        total_cards: int = 0
        reviewed_count: int = 0
        mastered_count: int = 0
        avg_recall: float = 0.0

    calls = {"mastery": 0}

    class FakeCol:
        def mastery_query(self, topics):
            calls["mastery"] += 1
            return [Row(topic=t, total_cards=1) for t in topics]

        # Fail loudly if the endpoint tries to mutate.
        def transact(self, *a, **k):  # pragma: no cover
            raise AssertionError("read endpoint must not mutate")

    monkeypatch.setattr(m, "aqt", types.SimpleNamespace(mw=types.SimpleNamespace(col=FakeCol())))
    out = m.gre_dashboard_data()
    vm = json.loads(out.decode("utf-8"))
    assert calls["mastery"] == 1
    assert set(vm.keys()) == {"generated_at", "memory", "coverage", "readiness", "performance"}
    assert len(vm["coverage"]["leaves"]) == 17
```

- [ ] **Step 2: Run to verify it fails**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_mediasrv.py -v`
Expected: FAIL (`gre-dashboard` not a page; `greDashboardData` not in `post_handlers`).

- [ ] **Step 3: Register the page**

In `anki/qt/aqt/mediasrv.py`, add `"gre-dashboard"` to the list returned by `is_sveltekit_page` (the list currently ending with `"image-occlusion"`):

```python
        "image-occlusion",
        "gre-dashboard",
    ]
```

- [ ] **Step 4: Add the read-only handler and register it**

In `anki/qt/aqt/mediasrv.py`, add the handler next to the other collection handlers (e.g. after `save_custom_colours`), then add it to `post_handler_list`:

```python
def gre_dashboard_data() -> bytes:
    # Read-only: calls the W1 MasteryQuery read RPC and returns a computed
    # view-model as JSON. No mutation, no OpChanges (see dashboard_data).
    import json
    from datetime import datetime, timezone

    from aqt.gre import dashboard_data as dd

    topics = dd.query_topics()
    rows = aqt.mw.col.mastery_query(topics)
    rows_by_tag = {r.topic: r for r in rows}
    vm = dd.build_view_model(
        rows_by_tag, generated_at=datetime.now(timezone.utc).isoformat()
    )
    return json.dumps(vm).encode("utf-8")
```

Add to `post_handler_list`:

```python
    save_custom_colours,
    gre_dashboard_data,
]
```

- [ ] **Step 5: Run to verify it passes**

Run: `out/pyenv/bin/python -m pytest qt/tests/test_gre_dashboard_mediasrv.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add anki/qt/aqt/mediasrv.py anki/qt/tests/test_gre_dashboard_mediasrv.py
git commit -m "feat(gre): read-only greDashboardData endpoint + route registration"
```

---

## Task 5: QDialog + Tools-menu action

**Files:**
- Create: `anki/qt/aqt/gre_dashboard.py`
- Modify: `anki/qt/aqt/main.py` (one line to install the menu action)

**Interfaces:**
- Consumes: `aqt.mw`, `AnkiWebView.load_sveltekit_page`.
- Produces: `show_gre_dashboard(mw)`; `setup_gre_dashboard_menu(mw)` (adds a `QAction` to the Tools menu).

- [ ] **Step 1: Implement the dialog + menu installer**

Create `anki/qt/aqt/gre_dashboard.py`:

```python
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from __future__ import annotations

import aqt
import aqt.main
from aqt.qt import (
    QAction,
    QDialog,
    QVBoxLayout,
    Qt,
    qconnect,
)
from aqt.utils import add_close_shortcut, disable_help_button, restoreGeom, saveGeom
from aqt.webview import AnkiWebView


class GreDashboard(QDialog):
    def __init__(self, mw: aqt.main.AnkiQt) -> None:
        QDialog.__init__(self, mw, Qt.WindowType.Window)
        mw.garbage_collect_on_dialog_finish(self)
        self.mw = mw
        self.name = "greDashboard"
        disable_help_button(self)
        self.web = AnkiWebView(kind=None)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        self.setLayout(layout)
        self.setMinimumSize(900, 700)
        restoreGeom(self, self.name, default_size=(1000, 800))
        add_close_shortcut(self)
        self.web.load_sveltekit_page("gre-dashboard")
        self.show()
        self.activateWindow()

    def reject(self) -> None:
        self.web.cleanup()
        self.web = None  # type: ignore
        saveGeom(self, self.name)
        QDialog.reject(self)


def show_gre_dashboard(mw: aqt.main.AnkiQt) -> None:
    GreDashboard(mw)


def setup_gre_dashboard_menu(mw: aqt.main.AnkiQt) -> None:
    action = QAction("GRE readiness dashboard", mw)
    qconnect(action.triggered, lambda: show_gre_dashboard(mw))
    mw.form.menuTools.addAction(action)
```

- [ ] **Step 2: Install the menu action at startup**

In `anki/qt/aqt/main.py`, register via the init hook (search for where other `gui_hooks` are used or the `setupMenus`/`__init__` completes). Add near the other imports/init a call:

```python
from aqt.gre_dashboard import setup_gre_dashboard_menu
gui_hooks.main_window_did_init.append(lambda: setup_gre_dashboard_menu(aqt.mw))
```

Place this at module import time in `main.py` (top-level, after `gui_hooks` is imported) so the action is added once the main window exists.

- [ ] **Step 3: Smoke-check the import**

Run: `out/pyenv/bin/python -c "import aqt.gre_dashboard as g; assert hasattr(g,'setup_gre_dashboard_menu')"`
Expected: no error (exit 0). (Full GUI open is verified manually in Task 7.)

- [ ] **Step 4: Commit**

```bash
git add anki/qt/aqt/gre_dashboard.py anki/qt/aqt/main.py
git commit -m "feat(gre): Tools-menu action opening the dashboard dialog"
```

---

## Task 6: SvelteKit route (presentation)

**Files:**
- Create: `anki/ts/routes/gre-dashboard/+page.svelte`
- Create: `anki/ts/routes/gre-dashboard/MemoryPanel.svelte`
- Create: `anki/ts/routes/gre-dashboard/CoverageMap.svelte`
- Create: `anki/ts/routes/gre-dashboard/ScoreSlot.svelte`

**Interfaces:**
- Consumes: `fetch('/_anki/greDashboardData', {method:"POST", ...})` → the JSON view-model from Task 4.
- Produces: the rendered dashboard.

- [ ] **Step 1: Implement the page (fetch + layout)**

Create `anki/ts/routes/gre-dashboard/+page.svelte`:

```svelte
<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { onMount } from "svelte";
    import MemoryPanel from "./MemoryPanel.svelte";
    import CoverageMap from "./CoverageMap.svelte";
    import ScoreSlot from "./ScoreSlot.svelte";

    let vm: any = $state(null);
    let error: string | null = $state(null);

    onMount(async () => {
        try {
            const resp = await fetch("/_anki/greDashboardData", {
                method: "POST",
                headers: { "Content-Type": "application/binary" },
                body: new Uint8Array(),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            vm = await resp.json();
        } catch (e) {
            error = String(e);
        }
    });
</script>

<div class="gre-dashboard">
    <h1>GRE readiness</h1>
    {#if error}
        <div class="err">Couldn't load dashboard: {error}</div>
    {:else if !vm}
        <div>Loading…</div>
    {:else}
        <MemoryPanel memory={vm.memory} generatedAt={vm.generated_at} />
        <div class="slots">
            <ScoreSlot
                title="Performance"
                body={vm.performance.note}
                state={vm.performance.state} />
            <ScoreSlot
                title="Readiness"
                body={`Insufficient evidence to score — studied ${Math.round(
                    vm.readiness.studied_pct * 100,
                )}% of topics. Best next: ${vm.readiness.next_best_topic ?? "—"}.`}
                state={vm.readiness.state} />
        </div>
        <CoverageMap coverage={vm.coverage} />
    {/if}
</div>

<style>
    .gre-dashboard { padding: 1rem 1.5rem; max-width: 1000px; margin: 0 auto; }
    .slots { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
    .err { color: var(--fg-critical, #c00); }
</style>
```

- [ ] **Step 2: Implement `MemoryPanel.svelte`**

Create `anki/ts/routes/gre-dashboard/MemoryPanel.svelte`:

```svelte
<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    let { memory, generatedAt }: { memory: any; generatedAt: string } = $props();
    const pct = (x: number) => `${Math.round(x * 100)}%`;
    const h = $derived(memory.headline);
</script>

<section class="memory">
    <h2>Memory</h2>
    {#if !h}
        <p class="muted">No graded reviews yet — insufficient evidence for a memory score.</p>
    {:else}
        <p class="headline">
            You can reliably recall <strong>~{pct(h.point)}</strong> of what you've studied
            <span class="range">(95% CI {pct(h.low)}–{pct(h.high)})</span>
        </p>
        {#if h.buckets_reflected < h.buckets_total}
            <p class="muted">Headline reflects {h.buckets_reflected}/{h.buckets_total} buckets.</p>
        {/if}
        <ul class="buckets">
            {#each memory.buckets as b}
                <li>
                    <span class="name">{b.bucket}</span>
                    <span class="w">({pct(b.weight)} of exam)</span>
                    {#if b.reviewed > 0}
                        {pct(b.point)} <span class="range">({pct(b.low)}–{pct(b.high)})</span>
                        · mean R {b.mean_r.toFixed(2)} · n={b.reviewed}
                    {:else}
                        <span class="muted">not studied yet</span>
                    {/if}
                </li>
            {/each}
        </ul>
    {/if}
    <p class="muted note">
        Aggregate-calibrated (population FSRS defaults), not personalized. Updated {generatedAt}.
    </p>
</section>

<style>
    .memory { border: 1px solid var(--border, #ccc); border-radius: 8px; padding: 1rem; }
    .headline { font-size: 1.1rem; }
    .range { color: var(--fg-subtle, #666); }
    .muted { color: var(--fg-subtle, #888); }
    .buckets { list-style: none; padding: 0; }
    .buckets li { padding: 0.25rem 0; }
    .note { font-size: 0.85rem; margin-top: 0.75rem; }
</style>
```

- [ ] **Step 3: Implement `CoverageMap.svelte`**

Create `anki/ts/routes/gre-dashboard/CoverageMap.svelte`:

```svelte
<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    let { coverage }: { coverage: any } = $props();
    const pct = (x: number) => `${Math.round(x * 100)}%`;
    const byBucket = $derived.by(() => {
        const groups: Record<string, any[]> = {};
        for (const leaf of coverage.leaves) {
            (groups[leaf.bucket] ??= []).push(leaf);
        }
        return groups;
    });
</script>

<section class="coverage">
    <h2>Coverage map</h2>
    <p class="muted">Deck coverage {pct(coverage.deck_pct)} · studied coverage {pct(coverage.studied_pct)}</p>
    {#each Object.entries(byBucket) as [bucket, leaves]}
        <h3>{bucket}</h3>
        <div class="grid">
            {#each leaves as leaf}
                <div class="cell" class:uncovered={!leaf.has_cards} class:studied={leaf.studied}>
                    <span class="leaf">{leaf.leaf}</span>
                    {#if leaf.studied && leaf.memory}
                        <span class="mem">{pct(leaf.memory.point)} ({pct(leaf.memory.low)}–{pct(leaf.memory.high)})</span>
                    {:else if leaf.has_cards}
                        <span class="muted">not studied</span>
                    {:else}
                        <span class="muted">no cards</span>
                    {/if}
                </div>
            {/each}
        </div>
    {/each}
</section>

<style>
    .coverage { margin-top: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.5rem; }
    .cell { border: 1px solid var(--border, #ccc); border-radius: 6px; padding: 0.5rem; display: flex; flex-direction: column; }
    .cell.studied { border-color: var(--accent, #4c8bf5); }
    .cell.uncovered { opacity: 0.55; }
    .leaf { font-weight: 600; }
    .mem { color: var(--fg-subtle, #555); }
    .muted { color: var(--fg-subtle, #888); }
</style>
```

- [ ] **Step 4: Implement `ScoreSlot.svelte`**

Create `anki/ts/routes/gre-dashboard/ScoreSlot.svelte`:

```svelte
<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    let { title, body, state }: { title: string; body: string; state: string } = $props();
</script>

<section class="slot {state}">
    <h2>{title}</h2>
    <p>{body}</p>
</section>

<style>
    .slot { border: 1px dashed var(--border, #ccc); border-radius: 8px; padding: 1rem; }
    .slot h2 { margin-top: 0; }
</style>
```

- [ ] **Step 5: Type-check + build the frontend**

Run (from `anki/`): `./ninja check:svelte`
Expected: PASS (no svelte-check/type errors in the new route). If the target name differs, list with `./ninja -t targets all | grep svelte`.

- [ ] **Step 6: Commit**

```bash
git add anki/ts/routes/gre-dashboard/
git commit -m "feat(gre): SvelteKit dashboard route (memory panel, coverage map, slots)"
```

---

## Task 7: Docs, integrated check, manual verification

**Files:**
- Modify: `docs/codebase/INDEX.md`, `docs/codebase/qt.md`, `docs/STATUS.md`, `docs/execution-plan.md` (outer repo)

- [ ] **Step 1: Update codebase docs**

- `docs/codebase/INDEX.md`: move the "3-score dashboard + coverage map" row from **Planned** to **Built**, code paths `anki/qt/aqt/gre/`, `anki/qt/aqt/gre_dashboard.py`, `anki/ts/routes/gre-dashboard/`, `anki/qt/aqt/mediasrv.py`; bump `Last verified` SHA to the new fork commit.
- `docs/codebase/qt.md`: in the "Where the 3-score dashboard + coverage map attach" section, mark it **implemented (W2)** with the exact files + the `greDashboardData` endpoint + `is_sveltekit_page("gre-dashboard")`; bump `Last verified against`.

- [ ] **Step 2: Run the integrated check (source of truth for green)**

Run (from `anki/`): `./ninja check:pytest:qt check:svelte`
Expected: PASS. For the full gate before shipping: `./ninja check` (slower). Use `verification-before-completion` before claiming green.

- [ ] **Step 3: Run the outer taxonomy sync test**

Run (repo root): `python -m pytest tests/test_taxonomy_sync.py -v`
Expected: PASS.

- [ ] **Step 4: Manual playtest**

From `anki/` in the fork worktree: `./run`. Build/import the seeded deck (`pipeline/build_deck.py --seed 42`), enable FSRS, study a few cards, then **Tools ▸ GRE readiness dashboard**. Confirm: memory headline range renders, per-bucket + per-leaf ranges show, coverage %s update after reviews, Readiness shows "Insufficient evidence" + next-best topic, Performance shows the Thursday placeholder. No errors in the console; opening the dashboard does not create an undo entry (Edit menu shows no new "Undo").

- [ ] **Step 5: Update STATUS + execution-plan and commit**

- `docs/STATUS.md`: add a Done line for W2 (PR number after opening), clear In flight, mark W3 next.
- `docs/execution-plan.md`: check the Wednesday boxes for "Memory score displayed as a range" and "Coverage map on the dashboard".

```bash
git add docs/codebase/INDEX.md docs/codebase/qt.md docs/STATUS.md docs/execution-plan.md
git commit -m "docs(gre): mark W2 desktop dashboard built; bump SHA"
```

---

## Self-Review

**1. Spec coverage:**
- §1 architecture / §2 files → Tasks 1–6 (taxonomy+loader, math, view-model, endpoint, dialog/menu, route).
- §3 data flow (one call, 20 topics, `QueryOp`/read-only) → Task 4 (`query_topics` = 17 leaves + 3 buckets; direct read on the request thread per the `graphs` precedent; no `OpChanges`). *Note: the spec named `QueryOp`; the concrete mediasrv fetch pattern is a direct read call in the handler — same read-only guarantee, matched to how `graphs`/`congrats_info` fetch. Reflected in Task 4.*
- §4 memory math (Wilson + 50/25/25 + n=0 renorm) → Task 2. §5 coverage → Task 3. §6 three slots + next-best rule → Task 3 + Task 6. §7 empty/error states → Task 3 (empty) + Task 6 (fetch error). §8 tests → Tasks 1–4 + Task 7 manual. §9 acceptance → Task 7.
- **Taxonomy sync** (spec decision) → Task 1.

**2. Placeholder scan:** No TBD/TODO; every code step contains full code; test steps contain real assertions and commands.

**3. Type consistency:** `wilson_interval` returns `(point, low, high)` everywhere; `headline` input `{"weight","point","reviewed"}` and output keys are used identically in Task 3 and `MemoryPanel.svelte`; `build_view_model` output keys (`memory/coverage/readiness/performance`, `headline`, `buckets`, `leaves`, `next_best_topic`) match the Svelte consumers and the mediasrv test; row duck-type (`total_cards/reviewed_count/mastered_count/avg_recall/topic`) matches W1's `TopicMastery`.

---

## Execution Handoff

Two execution options:
1. **Subagent-Driven (recommended)** — a fresh subagent per task, two-stage review between tasks.
2. **Inline Execution** — batch execution in this session with checkpoints.
