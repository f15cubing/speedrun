# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Unit tests for the Block-D proof helpers (pure stdlib; no engine/yaml needed).

Run: PYTHONPATH=. python3 -m pytest proofs/tests -q
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from proofs import bench_mastery, calibration, giveup_audit, paraphrase  # noqa: E402
from scoring import readiness  # noqa: E402


def test_percentile_monotone_and_bounds():
    vals = [float(i) for i in range(1, 101)]  # 1..100
    p50 = bench_mastery._percentile(vals, 0.50)
    p95 = bench_mastery._percentile(vals, 0.95)
    assert vals[0] <= p50 <= p95 <= vals[-1]
    assert bench_mastery._percentile([], 0.5) == 0.0


def test_wilson_known_and_clamped():
    point, low, high = paraphrase.wilson(8, 10)
    assert abs(point - 0.8) < 1e-9
    assert 0.0 <= low <= point <= high <= 1.0
    assert paraphrase.wilson(0, 0) == (0.0, 0.0, 0.0)


def test_sigmoid_symmetry():
    assert abs(paraphrase._sigmoid(0.0) - 0.5) < 1e-12
    assert paraphrase._sigmoid(50) > 0.99
    assert paraphrase._sigmoid(-50) < 0.01


def test_calibration_run_is_deterministic():
    a = calibration.run(seed=42, students=120, n_bins=10)
    b = calibration.run(seed=42, students=120, n_bins=10)
    assert a["brier"] == b["brier"] and a["ece"] == b["ece"]
    assert 0.0 <= a["ece"] <= 1.0
    assert a["note"].startswith("validated on simulated data")


# --- give-up rule (D2) evidence audit ---


def test_giveup_gate_boundaries():
    # each condition trips just below its threshold and clears just at it
    assert readiness.give_up(199, 0.9, 10) == ["<200 graded reviews"]
    assert readiness.give_up(200, 0.9, 10) == []
    assert readiness.give_up(500, 0.49, 10) == ["<50% topic coverage"]
    assert readiness.give_up(500, 0.50, 10) == []
    assert readiness.give_up(500, 0.9, 121) == ["interval too wide"]
    assert readiness.give_up(500, 0.9, 120) == []


def test_giveup_audit_never_leaks_a_number_when_gated():
    # THE auto-fail ceiling: a gated scenario must emit no scaled-score anywhere.
    result = giveup_audit.run(seed=42)
    giveup_audit.assert_giveup_invariants(result)  # raises if any gated leaks a number
    assert result["summary"]["n_shown"] >= 1  # the sweep includes a cleared case
    assert result["summary"]["n_gated"] >= 3   # ...and all three gate conditions
    for s in result["scenarios"]:
        if not s["shown"]:
            assert s["estimate"] is None and s["low"] is None and s["high"] is None


def test_giveup_audit_is_deterministic():
    assert giveup_audit.run(seed=42) == giveup_audit.run(seed=42)
