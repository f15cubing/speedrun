"""Test 2: deterministic build -- same seed yields an identical ordered card list."""

import build_deck
import generate_deck


def test_same_seed_identical_card_list():
    first = build_deck.load_all_cards(seed=42)
    second = build_deck.load_all_cards(seed=42)
    assert first == second
    assert build_deck.cards_content_hash(first) == build_deck.cards_content_hash(second)


def test_generator_is_repeatable():
    a = generate_deck.generate_cards(seed=42)
    b = generate_deck.generate_cards(seed=42)
    assert a == b


def test_different_seed_changes_some_cards():
    # Not a hard requirement, but a different seed should reshuffle the generated
    # problems -- guards against the seed being ignored entirely.
    base = generate_deck.generate_cards(seed=42)
    other = generate_deck.generate_cards(seed=7)
    assert len(base) == len(other)
    assert base != other
