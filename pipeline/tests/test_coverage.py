"""Test 3: the coverage assertions hold on the built card set."""

import build_deck
import coverage_report
import taxonomy


def test_coverage_gate_passes():
    cards = build_deck.load_all_cards(seed=42)
    # assert_coverage raises AssertionError on any violation.
    summary = coverage_report.assert_coverage(cards)
    assert summary["num_covered"] >= 9
    assert summary["leaf_coverage"] >= taxonomy.MIN_LEAF_COVERAGE
    assert summary["calc_weight"] >= taxonomy.MIN_CALCULUS_CARD_WEIGHT
    assert not summary["invalid"]


def test_all_seventeen_leaves_are_covered():
    cards = build_deck.load_all_cards(seed=42)
    summary = coverage_report.summarize(cards)
    # We aim for ALL 17 leaves, not just the >=9 minimum.
    assert summary["num_covered"] == summary["num_leaves"] == 17
    missing = [tag for tag, n in summary["per_leaf"].items() if n == 0]
    assert missing == [], "uncovered leaves: {}".format(missing)


def test_summary_reports_per_format_counts():
    cards = build_deck.load_all_cards(seed=42)
    summary = coverage_report.summarize(cards)
    assert summary["by_format"]["mcq"] >= 16
    assert summary["by_format"]["flashcard"] >= 1


def test_calc_weight_still_passes_with_mcq():
    cards = build_deck.load_all_cards(seed=42)
    summary = coverage_report.assert_coverage(cards)
    assert summary["calc_weight"] >= taxonomy.MIN_CALCULUS_CARD_WEIGHT
