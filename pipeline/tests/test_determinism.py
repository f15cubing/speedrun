"""Test 2: deterministic build -- same seed yields an identical ordered card list.

The dedicated determinism gate: each test builds fresh and compares to the once-
built session fixture (two independent invocations), so caching never hides a
non-determinism regression.
"""

import build_deck
import generate_deck


def test_same_seed_identical_card_list(all_cards):
    fresh = build_deck.load_all_cards(seed=42)
    assert all_cards == fresh
    assert build_deck.cards_content_hash(all_cards) == build_deck.cards_content_hash(fresh)


def test_generator_is_repeatable(flashcards):
    fresh = generate_deck.generate_cards(seed=42)
    assert flashcards == fresh


def test_different_seed_changes_some_cards(flashcards):
    # Not a hard requirement, but a different seed should reshuffle the generated
    # problems -- guards against the seed being ignored entirely.
    other = generate_deck.generate_cards(seed=7)
    assert len(flashcards) == len(other)
    assert flashcards != other
