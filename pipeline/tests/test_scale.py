"""The deck scales to thousands of unique cards, calc >= 50%, deterministic.

Read-only tests share the session-scoped ``all_cards`` fixture.
"""
import build_deck
import coverage_report
import generate_mcq


def test_deck_has_target_scale(all_cards):
    # Flashcards (unchanged) + MCQ now across all 11 computational leaves + conceptual.
    assert len(all_cards) >= 7000


def test_mcq_is_about_a_third_of_the_deck(all_cards):
    mcq = sum(1 for c in all_cards if c.get("format") == "mcq")
    share = mcq / len(all_cards)
    # Target: MCQ ~1/3 of the deck (up from ~9% when only 4 leaves had MCQ).
    assert 0.30 <= share <= 0.36, (mcq, len(all_cards), share)


def test_all_stems_distinct(all_cards):
    keys = [build_deck._card_identity(c) for c in all_cards]
    assert len(keys) == len(set(keys)), "duplicate card identity"


def test_calc_weight_and_coverage_hold_at_scale(all_cards):
    s = coverage_report.assert_coverage(all_cards)
    assert s["calc_weight"] >= 0.50
    assert s["num_covered"] == 17


def test_scale_is_deterministic(all_cards):
    # Independent fresh build must equal the once-built session deck.
    assert build_deck.load_all_cards(seed=42) == all_cards
