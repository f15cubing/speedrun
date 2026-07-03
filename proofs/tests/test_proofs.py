# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Unit tests for the Block-D proof helpers (pure stdlib; no engine/yaml needed).

Run: PYTHONPATH=. python3 -m pytest proofs/tests -q
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from proofs import bench_mastery, calibration, paraphrase  # noqa: E402


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
