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


# --- graded answer flow (bound to the FSRS ease enum) ---


def _right_branch(qfmt):
    return qfmt.split("if(right){", 1)[1].split("else{", 1)[0]


def _wrong_branch(qfmt):
    return qfmt.split("else{", 1)[1]


def test_mcq_grade_uses_reviewer_ease_commands():
    # Grading feeds the scheduler through the reviewer's own bridge commands:
    # show-answer (enters "answer" state) then ease<N> — the exact path the
    # built-in answer buttons use, so ratings bind to the existing FSRS enum.
    qfmt = _mcq_qfmt()
    assert "function grade(ease){" in qfmt
    assert "pycmd('ans');pycmd('ease'+ease)" in qfmt


def test_mcq_grade_is_one_shot_per_card():
    # A fast double-click / second rating must not answer the same card twice.
    qfmt = _mcq_qfmt()
    assert "var graded=false" in qfmt
    grade_fn = qfmt.split("function grade(ease){", 1)[1]
    assert grade_fn.startswith("if(graded){return;}")  # early-out before any pycmd
    assert "graded=true" in grade_fn.split("pycmd('ans')", 1)[0]  # lock set first


def test_mcq_correct_path_shows_three_ratings_bound_to_ease():
    # Correct -> Hard(2) / Good(3) / Easy(4); never "Again".
    right = _right_branch(_mcq_qfmt())
    assert right.count("rateBtn(") == 3
    assert "rateBtn('Hard',2,'hard')" in right
    assert "rateBtn('Good',3,'good')" in right
    assert "rateBtn('Easy',4,'easy')" in right
    assert "rateBtn('Continue'" not in right  # no lapse option on a correct answer


def test_mcq_wrong_path_autogrades_again_with_single_continue():
    # Wrong -> a single Continue that grades Again(1) (a lapse); no rating choice.
    wrong = _wrong_branch(_mcq_qfmt())
    assert wrong.count("rateBtn(") == 1
    assert "rateBtn('Continue',1,'again')" in wrong
    for banned in ("'Hard',2", "'Good',3", "'Easy',4"):
        assert banned not in wrong


def test_mcq_does_not_auto_advance_on_selection():
    # Selecting an option calls answer() (reveal only), not grade(): the learner
    # must explicitly rate / continue, so there is time to read the explanation.
    qfmt = _mcq_qfmt()
    assert "answer(parseInt(btn.getAttribute('data-i'),10))" in qfmt
    # the tap handler reveals the explanation but does not itself grade
    answer_body = qfmt.split("function answer(i){", 1)[1].split("for(var k=0", 1)[0]
    assert "exp.style.display='block'" in answer_body
    assert "pycmd(" not in answer_body  # no grade/advance on mere selection


def test_mcq_grading_degrades_gracefully_without_pycmd():
    # Where the reviewer bridge is absent (e.g. AnkiDroid), the custom rating row
    # is gated off (canGrade) and the built-in ease buttons remain the grader.
    qfmt = _mcq_qfmt()
    assert "var canGrade=(typeof pycmd==='function')" in qfmt
    assert "if(actions&&canGrade){" in qfmt
