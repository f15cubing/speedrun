"""Test 1: every produced card has exactly one valid leaf tag.

Read-only tests share the session-scoped ``all_cards`` fixture.
"""

import build_deck
import taxonomy


def test_every_card_has_exactly_one_valid_leaf_tag(all_cards):
    assert all_cards, "no cards were produced"
    for card in all_cards:
        tag = card["leaf_tag"]
        assert taxonomy.validate_leaf_tag(tag), "invalid leaf tag: {!r}".format(tag)
        # "exactly one": a single whitespace-free token (Anki tags split on spaces).
        assert isinstance(tag, str)
        assert tag.split() == [tag], "leaf tag must be a single token: {!r}".format(tag)


def test_built_notes_carry_exactly_one_topic_tag(all_cards):
    for card in all_cards:
        note = build_deck.note_for(card)
        topic_tags = [t for t in note.tags if t.startswith(taxonomy.TAG_PREFIX + "::")]
        assert len(topic_tags) == 1, "note must have exactly one topic:: tag, got {!r}".format(
            note.tags
        )
        assert taxonomy.validate_leaf_tag(topic_tags[0])
