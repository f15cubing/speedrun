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
