"""The deck scales to ~5000 unique cards, calc >= 50%, deterministic."""
import build_deck
import coverage_report
import taxonomy


def test_deck_has_target_scale():
    cards = build_deck.load_all_cards(seed=42)
    assert len(cards) >= 5000


def test_all_stems_distinct():
    cards = build_deck.load_all_cards(seed=42)
    keys = [build_deck._card_identity(c) for c in cards]
    assert len(keys) == len(set(keys)), "duplicate card identity"


def test_calc_weight_and_coverage_hold_at_scale():
    cards = build_deck.load_all_cards(seed=42)
    s = coverage_report.assert_coverage(cards)
    assert s["calc_weight"] >= 0.50
    assert s["num_covered"] == 17


def test_scale_is_deterministic():
    assert build_deck.load_all_cards(seed=42) == build_deck.load_all_cards(seed=42)
