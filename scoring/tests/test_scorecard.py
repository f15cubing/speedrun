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
