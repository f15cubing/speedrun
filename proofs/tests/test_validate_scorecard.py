# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Tests for the gre_scorecard honesty-contract validator (pure; no engine/scoring imports)."""

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from proofs import validate_scorecard as vs  # noqa: E402

_FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name):
    with open(os.path.join(_FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


# --- the two valid shapes (gated + fully-shown) ---


def test_valid_gated_fixture_passes():
    assert vs.validate(_load("scorecard_gated.json")) == []


def test_valid_shown_fixture_passes():
    assert vs.validate(_load("scorecard_shown.json")) == []


# --- the honesty ceilings ---


def test_bare_readiness_number_is_rejected():
    card = _load("scorecard_shown.json")
    card["readiness"]["shown"] = False  # a number present but not shown = bare
    assert any("bare number" in e for e in vs.validate(card))


def test_readiness_number_without_full_panel_is_rejected():
    card = _load("scorecard_shown.json")
    del card["readiness"]["coverage_pct"]  # drop one required panel field
    assert any("evidence panel" in e for e in vs.validate(card))


def test_blended_total_is_rejected():
    for bad in ("overall", "total", "combined"):
        card = _load("scorecard_gated.json")
        card[bad] = 0.6
        assert any("blended" in e for e in vs.validate(card)), bad


def test_estimate_without_range_is_rejected():
    card = _load("scorecard_gated.json")
    card["memory"] = {"estimate": 0.6, "low": None, "high": None, "coverage_pct": 0.4}
    assert any("without a range" in e for e in vs.validate(card))


def test_gated_without_reasons_or_next_is_rejected():
    card = _load("scorecard_gated.json")
    card["readiness"]["reasons"] = []
    assert any("no reasons" in e for e in vs.validate(card))
    card = _load("scorecard_gated.json")
    card["readiness"]["best_next_topic"] = ""
    assert any("best_next_topic" in e for e in vs.validate(card))


def test_missing_score_separation_is_rejected():
    card = _load("scorecard_gated.json")
    del card["performance"]
    assert any("performance" in e for e in vs.validate(card))


def test_assert_valid_raises_on_violation():
    card = _load("scorecard_gated.json")
    card["overall"] = 1
    try:
        vs.assert_valid(card)
        assert False, "expected AssertionError"
    except AssertionError as exc:
        assert "honesty violations" in str(exc)


def test_validate_does_not_mutate_input():
    card = _load("scorecard_shown.json")
    before = copy.deepcopy(card)
    vs.validate(card)
    assert card == before
