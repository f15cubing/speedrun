"""The GRE MCQ note type packs correctly and carries exactly one topic tag."""

import build_deck
import taxonomy


def test_mcq_cards_present_in_merged_list():
    cards = build_deck.load_all_cards(seed=42)
    mcq = [c for c in cards if c.get("format") == "mcq"]
    assert len(mcq) >= 16  # 4 leaves x 4 computational + conceptual MCQ


def test_mcq_note_has_nine_fields_and_one_topic_tag():
    cards = build_deck.load_all_cards(seed=42)
    mcq = next(c for c in cards if c.get("format") == "mcq")
    note = build_deck.note_for(mcq)
    assert len(note.fields) == 9
    topic_tags = [t for t in note.tags if t.startswith(taxonomy.TAG_PREFIX + "::")]
    assert len(topic_tags) == 1
    assert taxonomy.validate_leaf_tag(topic_tags[0])


def test_mcq_correct_option_field_matches_index():
    cards = build_deck.load_all_cards(seed=42)
    for c in [c for c in cards if c.get("format") == "mcq"]:
        note = build_deck.note_for(c)
        # Field order: Question, A, B, C, D, E, CorrectOption, Explanation, LeafTag
        assert note.fields[6] == "ABCDE"[c["correct_index"]]


def test_content_hash_is_stable_with_mcq():
    a = build_deck.load_all_cards(seed=42)
    b = build_deck.load_all_cards(seed=42)
    assert build_deck.cards_content_hash(a) == build_deck.cards_content_hash(b)
