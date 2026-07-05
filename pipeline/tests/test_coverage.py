"""Test 3: the coverage assertions hold on the built card set.

Read-only tests share the session-scoped ``all_cards`` fixture.
"""

import coverage_report
import generate_mcq
import taxonomy


def test_coverage_gate_passes(all_cards):
    # assert_coverage raises AssertionError on any violation.
    summary = coverage_report.assert_coverage(all_cards)
    assert summary["num_covered"] >= 9
    assert summary["leaf_coverage"] >= taxonomy.MIN_LEAF_COVERAGE
    assert summary["calc_weight"] >= taxonomy.MIN_CALCULUS_CARD_WEIGHT
    assert not summary["invalid"]


def test_all_seventeen_leaves_are_covered(all_cards):
    summary = coverage_report.summarize(all_cards)
    # We aim for ALL 17 leaves, not just the >=9 minimum.
    assert summary["num_covered"] == summary["num_leaves"] == 17
    missing = [tag for tag, n in summary["per_leaf"].items() if n == 0]
    assert missing == [], "uncovered leaves: {}".format(missing)


def test_summary_reports_per_format_counts(all_cards):
    summary = coverage_report.summarize(all_cards)
    # MCQ now spans all 11 computational leaves (2425) plus conceptual MCQ.
    assert summary["by_format"]["mcq"] >= sum(generate_mcq.MCQ_COUNTS.values())
    assert summary["by_format"]["flashcard"] >= 1


def test_calc_weight_still_passes_with_mcq(all_cards):
    summary = coverage_report.assert_coverage(all_cards)
    assert summary["calc_weight"] >= taxonomy.MIN_CALCULUS_CARD_WEIGHT
