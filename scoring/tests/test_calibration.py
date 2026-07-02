# scoring/tests/test_calibration.py
import json

from scoring.calibration import append_log, brier, ece, reliability_bins


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


def test_append_log_appends_jsonl(tmp_path):
    path = str(tmp_path / "cal.jsonl")
    append_log(path, {"a": 1, "shown": True})
    append_log(path, {"a": 2, "shown": False})
    lines = open(path).read().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["a"] == 1 and json.loads(lines[1])["shown"] is False
