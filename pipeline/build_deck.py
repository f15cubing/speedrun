"""Assemble the GRE Math study deck into a deterministic ``.apkg``.

Merges the seeded SymPy generator (``generate_deck``) with the hand-authored
conceptual cards (``conceptual_cards.yaml``), packs them via ``genanki`` with
**deterministic** model id, deck id, and per-note GUIDs (each GUID derives from a
hash of the card content, so reruns are byte-stable), and then runs the coverage
gate (``coverage_report.assert_coverage``) -- failing the build if it fails.

One command::

    python pipeline/build_deck.py --seed 42

writes ``pipeline/dist/gre-study-deck.apkg`` and prints the coverage summary.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import os
import sys

import genanki
import yaml

import coverage_report
import generate_deck
import generate_mcq
import taxonomy

HERE = os.path.dirname(os.path.abspath(__file__))
CONCEPTUAL_YAML = os.path.join(HERE, "conceptual_cards.yaml")
DIST_DIR = os.path.join(HERE, "dist")
OUTPUT_APKG = os.path.join(DIST_DIR, "gre-study-deck.apkg")

DECK_NAME = "GRE Math Subject Test::Study Deck"

# Fixed timestamp (2021-01-01 UTC) so genanki does not stamp wall-clock time into
# the package -- one more knob toward reproducible output.
FIXED_TIMESTAMP = 1609459200.0


def _stable_id(namespace):
    """Deterministic 31-bit positive id derived from a namespace string."""
    digest = hashlib.sha256(namespace.encode("utf-8")).hexdigest()
    return int(digest, 16) % (1 << 31)


MODEL_ID = _stable_id("gre-speedrun::model::basic-tagged::v1")
DECK_ID = _stable_id("gre-speedrun::deck::gre-study-deck::v1")

MODEL = genanki.Model(
    MODEL_ID,
    "GRE Math Basic (leaf-tagged)",
    fields=[
        {"name": "Front"},
        {"name": "Back"},
        {"name": "LeafTag"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": (
                '{{FrontSide}}<hr id="answer">{{Back}}'
                '<br><br><span style="color:#888;font-size:0.8em">{{LeafTag}}</span>'
            ),
        }
    ],
    css=(
        ".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
        "font-size:18px;line-height:1.5;color:#111;background:#fff;"
        "text-align:left;padding:16px;white-space:pre-wrap;}"
    ),
)


MCQ_MODEL_ID = _stable_id("gre-speedrun::model::mcq-tagged::v1")

MCQ_MODEL = genanki.Model(
    MCQ_MODEL_ID,
    "GRE Math MCQ (leaf-tagged)",
    fields=[
        {"name": "Question"},
        {"name": "OptionA"},
        {"name": "OptionB"},
        {"name": "OptionC"},
        {"name": "OptionD"},
        {"name": "OptionE"},
        {"name": "CorrectOption"},
        {"name": "Explanation"},
        {"name": "LeafTag"},
    ],
    templates=[
        {
            "name": "MCQ",
            "qfmt": (
                "{{Question}}<br><br>"
                "A. {{OptionA}}<br>B. {{OptionB}}<br>C. {{OptionC}}<br>"
                "D. {{OptionD}}<br>E. {{OptionE}}"
            ),
            "afmt": (
                '{{FrontSide}}<hr id="answer">'
                "Correct: {{CorrectOption}}<br><br>{{Explanation}}"
                '<br><br><span style="color:#888;font-size:0.8em">{{LeafTag}}</span>'
            ),
        }
    ],
    css=(
        ".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
        "font-size:18px;line-height:1.5;color:#111;background:#fff;"
        "text-align:left;padding:16px;white-space:pre-wrap;}"
    ),
)


def _to_html(text):
    """HTML-escape plain card text.

    Newlines are preserved by the model's ``white-space: pre-wrap`` CSS, so no
    raw HTML is injected into note fields (keeps genanki's invalid-tag check quiet).
    """
    return html.escape(text)


_VALID_STATUSES = ("draft", "verified")
_REQUIRED_WHEN_VERIFIED = ("verified_by", "verified_on", "source")


def _conceptual_entry_to_card(entry):
    """Convert a raw YAML entry to a card dict (flashcard or mcq)."""
    fmt = str(entry.get("format", "flashcard"))
    base = {"leaf_tag": str(entry["leaf_tag"]), "format": fmt}
    if fmt == "mcq":
        options = [str(o) for o in entry["options"]]
        base.update(
            {
                "question": str(entry["question"]),
                "options": options,
                "correct_index": int(entry["correct_index"]),
                "explanation": str(entry.get("explanation", "")),
            }
        )
    else:
        base.update({"front": str(entry["front"]), "back": str(entry["back"])})
    return base


def load_conceptual_cards(path=CONCEPTUAL_YAML, strict=False):
    """Load conceptual cards, enforcing the human-verification gate (PRD §12a).

    Returns built card dicts for ``status: verified`` entries only. ``draft``
    entries are skipped with a warning (or, when ``strict=True``, raise). A
    ``verified`` entry missing any of ``verified_by``/``verified_on``/``source``,
    or any unknown ``status``, always raises ``ValueError``.
    """
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    raw = data["cards"] if isinstance(data, dict) else data

    cards = []
    skipped = []
    for index, entry in enumerate(raw):
        status = str(entry.get("status", "")).strip()
        if status not in _VALID_STATUSES:
            raise ValueError(
                "conceptual card #{} ({!r}) has invalid status {!r}; "
                "expected one of {}".format(
                    index, entry.get("front") or entry.get("question"), status,
                    _VALID_STATUSES,
                )
            )
        if status == "draft":
            if strict:
                raise ValueError(
                    "conceptual card #{} is still a draft (strict mode)".format(index)
                )
            skipped.append(index)
            continue
        missing = [k for k in _REQUIRED_WHEN_VERIFIED if not str(entry.get(k, "")).strip()]
        if missing:
            raise ValueError(
                "verified conceptual card #{} is missing attribution: {}".format(
                    index, ", ".join(missing)
                )
            )
        cards.append(_conceptual_entry_to_card(entry))

    if skipped:
        print(
            "NOTE: skipped {} unverified (draft) conceptual card(s): {}".format(
                len(skipped), skipped
            )
        )
    return cards


def assert_all_verified(path=CONCEPTUAL_YAML):
    """Production gate: raise if any conceptual card is not verified+attributed."""
    # strict=True raises on the first draft; verified-but-unattributed also raises.
    load_conceptual_cards(path=path, strict=True)


def load_all_cards(seed=generate_deck.DEFAULT_SEED):
    """Return the merged, canonically ordered card list.

    Order is deterministic: generated computational flashcards (taxonomy order),
    then computational MCQ cards (taxonomy order), then conceptual cards
    (YAML order, verified only).
    """
    generated = generate_deck.generate_cards(seed=seed)
    mcq = generate_mcq.generate_mcq_cards(seed=seed)
    conceptual = load_conceptual_cards()
    return generated + mcq + conceptual


def _card_identity(card):
    """Stable identity string for a card, covering both formats."""
    if card.get("format") == "mcq":
        parts = [card["leaf_tag"], "mcq", card["question"]]
        parts.extend(card["options"])
        parts.append(str(card["correct_index"]))
        return "\x1f".join(parts)
    return "\x1f".join((card["leaf_tag"], card["front"], card["back"]))


def cards_content_hash(cards):
    """Stable SHA-256 over the ordered identity of every card (both formats)."""
    hasher = hashlib.sha256()
    for card in cards:
        hasher.update((_card_identity(card) + "\x1e").encode("utf-8"))
    return hasher.hexdigest()


def note_for(card):
    """Build a genanki Note (basic or MCQ) with a content-derived, stable GUID."""
    if card.get("format") == "mcq":
        return mcq_note_for(card)
    guid = genanki.guid_for(card["front"], card["back"], card["leaf_tag"])
    return genanki.Note(
        model=MODEL,
        fields=[_to_html(card["front"]), _to_html(card["back"]), card["leaf_tag"]],
        tags=[card["leaf_tag"]],
        guid=guid,
    )


def mcq_note_for(card):
    """Build a genanki Note for an MCQ card (GRE MCQ model)."""
    options = card["options"]
    correct_letter = "ABCDE"[card["correct_index"]]
    fields = (
        [_to_html(card["question"])]
        + [_to_html(opt) for opt in options]
        + [correct_letter, _to_html(card.get("explanation", "")), card["leaf_tag"]]
    )
    guid = genanki.guid_for(card["question"], *options, card["leaf_tag"])
    return genanki.Note(
        model=MCQ_MODEL,
        fields=fields,
        tags=[card["leaf_tag"]],
        guid=guid,
    )


def build(seed=generate_deck.DEFAULT_SEED, out_path=OUTPUT_APKG, verbose=True):
    """Build the ``.apkg`` and run the coverage gate.

    Returns ``(cards, summary)``. Raises ``AssertionError`` (via the coverage
    gate) if the produced deck violates a coverage invariant.
    """
    cards = load_all_cards(seed=seed)
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    for card in cards:
        deck.add_note(note_for(card))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    package = genanki.Package(deck)
    package.write_to_file(out_path, timestamp=FIXED_TIMESTAMP)

    summary = coverage_report.summarize(cards)
    if verbose:
        print(coverage_report.format_report(summary))
        print("")
        print("Deck id:       {}".format(DECK_ID))
        print("Model id:      {}".format(MODEL_ID))
        print("Content hash:  {}".format(cards_content_hash(cards)))
        print("Wrote:         {}".format(out_path))

    # After building, the coverage report is the hard gate.
    coverage_report.assert_coverage(cards)
    return cards, summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the deterministic GRE Math study deck (.apkg)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=generate_deck.DEFAULT_SEED,
        help="RNG seed for deterministic generation (default: 42).",
    )
    parser.add_argument(
        "--out",
        default=OUTPUT_APKG,
        help="Output .apkg path (default: pipeline/dist/gre-study-deck.apkg).",
    )
    args = parser.parse_args(argv)

    try:
        build(seed=args.seed, out_path=args.out, verbose=True)
    except AssertionError as exc:
        print("\nBUILD FAILED -- coverage gate:\n{}".format(exc), file=sys.stderr)
        return 1
    print("\nCoverage gate PASSED. Build complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
