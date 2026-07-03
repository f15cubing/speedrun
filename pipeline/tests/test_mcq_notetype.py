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


def _mcq_qfmt():
    return build_deck.MCQ_MODEL.templates[0]["qfmt"]


def _mcq_afmt():
    return build_deck.MCQ_MODEL.templates[0]["afmt"]


def test_mcq_front_renders_five_tappable_options():
    qfmt = _mcq_qfmt()
    # each option field is wired to a tappable button carrying its index
    for i, letter in enumerate("ABCDE"):
        assert "{{Option%s}}" % letter in qfmt
        assert 'data-i="%d"' % i in qfmt
    assert qfmt.count('class="mcq-opt"') == 5


def test_mcq_front_hides_correct_letter_behind_a_hook_not_in_the_prompt():
    qfmt = _mcq_qfmt()
    # the correct letter is present only inside the hidden hook the JS reads,
    # so the visible prompt never announces the answer before a tap
    assert 'id="mcq-correct"' in qfmt
    assert ">{{CorrectOption}}<" in qfmt  # wrapped by the hidden hook element


def test_mcq_front_has_interaction_js_and_explanation_reveal():
    qfmt = _mcq_qfmt()
    assert "addEventListener" in qfmt        # tap handler
    assert "answered" in qfmt                # locks after first answer
    assert "{{Explanation}}" in qfmt         # revealed on tap
    assert "MathJax" in qfmt                 # re-typesets revealed LaTeX


def test_mcq_back_reveals_key_and_explanation():
    afmt = _mcq_afmt()
    assert "{{FrontSide}}" in afmt
    assert "{{CorrectOption}}" in afmt
    assert "{{Explanation}}" in afmt


def test_mcq_css_has_correct_and_wrong_states():
    css = build_deck.MCQ_MODEL.css
    assert ".mcq-opt" in css
    assert ".correct" in css and ".wrong" in css
