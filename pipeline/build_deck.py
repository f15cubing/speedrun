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


def _to_html(text):
    """HTML-escape plain card text.

    Newlines are preserved by the model's ``white-space: pre-wrap`` CSS, so no
    raw HTML is injected into note fields (keeps genanki's invalid-tag check quiet).
    """
    return html.escape(text)


def load_conceptual_cards(path=CONCEPTUAL_YAML):
    """Load the hand-authored conceptual cards from YAML into card dicts."""
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    raw = data["cards"] if isinstance(data, dict) else data
    cards = []
    for entry in raw:
        cards.append(
            {
                "front": str(entry["front"]),
                "back": str(entry["back"]),
                "leaf_tag": str(entry["leaf_tag"]),
            }
        )
    return cards


def load_all_cards(seed=generate_deck.DEFAULT_SEED):
    """Return the merged, canonically ordered card list.

    Order is deterministic: generated computational cards (in taxonomy/leaf
    order) followed by conceptual cards (in YAML order).
    """
    generated = generate_deck.generate_cards(seed=seed)
    conceptual = load_conceptual_cards()
    return generated + conceptual


def cards_content_hash(cards):
    """Stable SHA-256 over the ordered (leaf_tag, front, back) of every card."""
    hasher = hashlib.sha256()
    for card in cards:
        payload = "\x1f".join((card["leaf_tag"], card["front"], card["back"]))
        hasher.update((payload + "\x1e").encode("utf-8"))
    return hasher.hexdigest()


def note_for(card):
    """Build a genanki Note with a content-derived, stable GUID and one tag."""
    guid = genanki.guid_for(card["front"], card["back"], card["leaf_tag"])
    return genanki.Note(
        model=MODEL,
        fields=[_to_html(card["front"]), _to_html(card["back"]), card["leaf_tag"]],
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
