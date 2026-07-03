"""Note GUIDs are stable across re-rendering (so the auto-importer never dupes).

Every card carries a rendering-independent ``uid``; the note GUID derives from it.
That means changing how a card is *rendered* (e.g. ASCII -> LaTeX) does not change
its GUID, so the version-gated bundled-deck importer updates cards in place. These
tests pin that contract: uids exist and are unique, the GUID is a pure function of
the uid, and mutating the rendered fields does not move the GUID.
"""

import genanki

import build_deck


def test_every_card_has_a_uid():
    for card in build_deck.load_all_cards(seed=42):
        assert card.get("uid"), card


def test_uids_are_unique_across_the_deck():
    cards = build_deck.load_all_cards(seed=42)
    uids = [c["uid"] for c in cards]
    assert len(uids) == len(set(uids)), "duplicate uid(s) in the deck"


def test_note_guid_is_derived_from_uid():
    for card in build_deck.load_all_cards(seed=42)[:50]:
        note = build_deck.note_for(card)
        assert note.guid == genanki.guid_for(card["uid"]), card["uid"]


def test_guid_is_stable_when_rendering_changes():
    # A flashcard whose front/back are re-rendered keeps its GUID (uid unchanged).
    flash = {
        "leaf_tag": "topic::calculus::differential_single",
        "front": r"\(f(x) = x^{2}\)",
        "back": r"\(f'(x) = 2 x\)",
        "uid": "topic::calculus::differential_single::flashcard::0",
    }
    g1 = build_deck.note_for(flash).guid
    flash_rerendered = dict(flash, front="f(x) = x**2", back="f'(x) = 2*x")
    g2 = build_deck.note_for(flash_rerendered).guid
    assert g1 == g2

    # An MCQ likewise keeps its GUID when options are re-rendered.
    mcq = {
        "leaf_tag": "topic::algebra::linear",
        "format": "mcq",
        "question": r"\(\det \left[\begin{matrix}1 & 2\\3 & 4\end{matrix}\right]\)?",
        "options": [r"\(-2\)", r"\(2\)", r"\(0\)", r"\(1\)", r"\(-1\)"],
        "correct_index": 0,
        "explanation": r"\(\det = -2\)",
        "uid": "topic::algebra::linear::mcq::0",
    }
    m1 = build_deck.note_for(mcq).guid
    mcq_rerendered = dict(mcq, options=["-2", "2", "0", "1", "-1"], question="det [[1,2],[3,4]]?")
    m2 = build_deck.note_for(mcq_rerendered).guid
    assert m1 == m2
