"""Assemble the GRE Math study deck into a deterministic ``.apkg``.

Merges the seeded SymPy generator (``generate_deck``) with the hand-authored
conceptual cards (``conceptual_cards.yaml``), packs them via ``genanki`` with
**deterministic** model id, deck id, and per-note GUIDs. Each GUID derives from a
card's **stable, rendering-independent ``uid``** (per-leaf/format ordinal in the
deterministic sequence), so reruns are byte-stable AND re-rendering the deck
(e.g. ASCII -> LaTeX) keeps GUIDs stable — the version-gated auto-importer then
updates cards in place instead of duplicating them. Finally it runs the coverage
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
            # Interactive graded MCQ. Five tappable A-E options; tapping locks the
            # choice, marks it green/red, highlights the correct option, and reveals
            # the explanation. It does NOT auto-advance -- the learner grades
            # explicitly, and the grade is bound to Anki's FSRS ease enum via the
            # reviewer's own bridge commands (pycmd("ans") -> answer state, then
            # pycmd("ease<N>")), exactly what the built-in answer buttons call:
            #   correct -> Hard(2) / Good(3) / Easy(4);   wrong -> Again(1) only.
            # A wrong answer is a lapse: a single "Continue" grades Again, never a
            # rating. Where pycmd is unavailable (e.g. AnkiDroid) the custom rating
            # row is hidden and the built-in Again/Hard/Good/Easy buttons remain the
            # grader (feedback + explanation still show). Vanilla ES5-safe JS so the
            # same template works in the desktop qt webview and AnkiDroid's.
            "qfmt": (
                '<div class="mcq-q">{{Question}}</div>'
                '<div class="mcq-opts">'
                '<button class="mcq-opt" data-i="0">A. {{OptionA}}</button>'
                '<button class="mcq-opt" data-i="1">B. {{OptionB}}</button>'
                '<button class="mcq-opt" data-i="2">C. {{OptionC}}</button>'
                '<button class="mcq-opt" data-i="3">D. {{OptionD}}</button>'
                '<button class="mcq-opt" data-i="4">E. {{OptionE}}</button>'
                "</div>"
                '<span id="mcq-correct" style="display:none">{{CorrectOption}}</span>'
                '<div id="mcq-explain" class="mcq-explain" style="display:none">{{Explanation}}</div>'
                '<div id="mcq-actions" class="mcq-actions"></div>'
                "<script>(function(){"
                "var root=document.getElementById('mcq-correct');"
                "if(!root){return;}"
                "var correct='ABCDE'.indexOf((root.textContent||'').trim());"
                "var opts=document.querySelectorAll('.mcq-opt');"
                "var exp=document.getElementById('mcq-explain');"
                "var actions=document.getElementById('mcq-actions');"
                "var canGrade=(typeof pycmd==='function');"
                "function typeset(){try{if(window.MathJax&&MathJax.typeset){MathJax.typeset();}}catch(e){}}"
                # grade() feeds the scheduler with the *existing* FSRS grade enum:
                # ans flips the reviewer to answer state (set synchronously), then
                # ease<N> answers the card -- the same path as the built-in buttons.
                "function grade(ease){if(typeof pycmd==='function'){pycmd('ans');pycmd('ease'+ease);}}"
                "function rateBtn(label,ease,cls){var b=document.createElement('button');"
                "b.className='mcq-rate '+cls;b.setAttribute('data-ease',ease);b.textContent=label;"
                "b.addEventListener('click',function(){grade(ease);});return b;}"
                "var answered=false;"
                "function answer(i){"
                "if(answered){return;}"
                "answered=true;"
                "var right=(i===correct);"
                "for(var j=0;j<opts.length;j++){"
                "opts[j].disabled=true;"
                "if(j===correct){opts[j].className+=' correct';}"
                "else if(j===i){opts[j].className+=' wrong';}"
                "}"
                "if(exp){exp.style.display='block';}"
                # No auto-advance: reveal only. The learner then rates (correct) or
                # presses Continue (wrong, auto-Again) to move on.
                "if(actions&&canGrade){var v=document.createElement('div');"
                "v.className='mcq-verdict';"
                "if(right){v.textContent='Correct - how hard was it?';"
                "actions.appendChild(v);"
                "actions.appendChild(rateBtn('Hard',2,'hard'));"
                "actions.appendChild(rateBtn('Good',3,'good'));"
                "actions.appendChild(rateBtn('Easy',4,'easy'));}"
                "else{v.textContent='Not quite - read the explanation, then continue.';"
                "actions.appendChild(v);"
                "actions.appendChild(rateBtn('Continue',1,'again'));}"
                "actions.style.display='flex';}"
                "typeset();"
                "}"
                "for(var k=0;k<opts.length;k++){(function(btn){"
                "btn.addEventListener('click',function(){answer(parseInt(btn.getAttribute('data-i'),10));});"
                "})(opts[k]);}"
                "typeset();"
                "})();</script>"
            ),
            "afmt": (
                '{{FrontSide}}<hr id="answer">'
                '<div class="mcq-key">Correct: {{CorrectOption}}</div>'
                '<div class="mcq-explain">{{Explanation}}</div>'
                '<div class="mcq-leaf">{{LeafTag}}</div>'
                "<script>(function(){try{if(window.MathJax&&MathJax.typeset){MathJax.typeset();}}catch(e){}})();</script>"
            ),
        }
    ],
    css=(
        ".card{font-family:-apple-system,Segoe UI,Roboto,sans-serif;"
        "font-size:18px;line-height:1.5;color:#111;background:#fff;"
        "text-align:left;padding:16px;white-space:pre-wrap;}"
        ".mcq-q{margin-bottom:14px;}"
        ".mcq-opts{display:flex;flex-direction:column;gap:8px;}"
        ".mcq-opt{display:block;width:100%;text-align:left;"
        "min-height:44px;padding:10px 14px;font-size:17px;line-height:1.4;"
        "border:1px solid #cbd5e0;border-radius:8px;background:#f7fafc;color:#111;"
        "cursor:pointer;white-space:pre-wrap;}"
        ".mcq-opt:hover:not(:disabled){background:#edf2f7;}"
        ".mcq-opt:disabled{cursor:default;}"
        ".mcq-opt.correct{background:#c6f6d5;border-color:#38a169;font-weight:600;}"
        ".mcq-opt.wrong{background:#fed7d7;border-color:#e53e3e;}"
        ".mcq-explain{margin-top:14px;}"
        ".mcq-key{margin-top:4px;font-weight:600;}"
        ".mcq-leaf{margin-top:14px;color:#888;font-size:0.8em;}"
        ".mcq-actions{display:none;flex-wrap:wrap;gap:8px;align-items:center;"
        "margin-top:16px;}"
        ".mcq-verdict{flex-basis:100%;font-weight:600;margin-bottom:2px;}"
        ".mcq-rate{min-height:40px;padding:8px 18px;font-size:16px;border-radius:8px;"
        "border:1px solid #cbd5e0;background:#edf2f7;color:#111;cursor:pointer;}"
        ".mcq-rate:hover{background:#e2e8f0;}"
        ".mcq-rate.easy{border-color:#38a169;}"
        ".mcq-rate.good{border-color:#3182ce;}"
        ".mcq-rate.hard{border-color:#dd6b20;}"
        ".mcq-rate.again{border-color:#e53e3e;}"
        ".night-mode .card{color:#e2e8f0;background:#1a202c;}"
        ".night-mode .mcq-opt{background:#2d3748;border-color:#4a5568;color:#e2e8f0;}"
        ".night-mode .mcq-opt:hover:not(:disabled){background:#374151;}"
        ".night-mode .mcq-opt.correct{background:#22543d;border-color:#38a169;}"
        ".night-mode .mcq-opt.wrong{background:#742a2a;border-color:#e53e3e;}"
        ".night-mode .mcq-rate{background:#2d3748;border-color:#4a5568;color:#e2e8f0;}"
        ".night-mode .mcq-rate:hover{background:#374151;}"
    ),
)


def _rewrite_apkg_deterministically(path):
    """Re-zip the .apkg with fixed entry metadata so the file is byte-reproducible.

    genanki stamps each zip entry's ``date_time`` with the wall-clock build time,
    so two builds of identical content produce different archive bytes (breaking
    ``make deck-asset-check`` and re-runnability). The embedded ``collection.anki2``
    and ``media`` payloads are already deterministic; here we only normalize the
    zip container — sorted members, a fixed 1980-01-01 timestamp, fixed perms, and
    deflate — which yields identical bytes for identical content and imports the
    same as any other .apkg.
    """
    import zipfile as _zip

    with _zip.ZipFile(path) as zf:
        members = sorted(zf.namelist())
        payloads = {name: zf.read(name) for name in members}

    tmp = path + ".tmp"
    with _zip.ZipFile(tmp, "w", _zip.ZIP_DEFLATED) as zf:
        for name in members:
            info = _zip.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = _zip.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, payloads[name])
    os.replace(tmp, path)


def _to_html(text):
    """HTML-escape plain card text (which now embeds delimited LaTeX).

    Newlines are preserved by the model's ``white-space: pre-wrap`` CSS, so no
    raw HTML is injected into note fields (keeps genanki's invalid-tag check quiet).

    LaTeX/MathJax round-trip: escaping is **safe** for math. The MathJax
    delimiters ``\\(`` / ``\\[`` and LaTeX control sequences use backslashes and
    braces, which ``html.escape`` leaves untouched. The only characters it
    changes are ``&`` (matrix ``&`` alignment -> ``&amp;``) and ``<``/``>``
    (e.g. ``a < b`` -> ``a &lt; b``); the browser decodes those entities back to
    ``&``/``<`` in the text node **before** MathJax scans it, so MathJax typesets
    the intended LaTeX. See ``tests/test_latex_escaping.py``.
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
    # Per-(leaf, format) ordinal over ALL raw entries (draft or not), so a stable
    # note identity survives re-rendering AND a draft later becoming verified.
    uid_counters = {}
    for index, entry in enumerate(raw):
        leaf = str(entry["leaf_tag"])
        fmt = str(entry.get("format", "flashcard"))
        uid_key = (leaf, fmt)
        ordinal = uid_counters.get(uid_key, 0)
        uid_counters[uid_key] = ordinal + 1
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
        card = _conceptual_entry_to_card(entry)
        # ``c``-prefixed ordinal keeps conceptual uids disjoint from the generated
        # cards' numeric ordinals for the same leaf/format.
        card["uid"] = "{}::{}::c{}".format(leaf, fmt, ordinal)
        cards.append(card)

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


def _guid_for(card, *content_fallback):
    """Stable note GUID.

    Prefer the card's rendering-independent ``uid`` so re-rendering the deck
    (e.g. ASCII -> LaTeX) keeps GUIDs stable and the auto-importer updates cards
    in place instead of duplicating them. Ad-hoc cards without a ``uid`` (e.g. in
    unit tests) fall back to their content.
    """
    uid = card.get("uid")
    if uid:
        return genanki.guid_for(uid)
    return genanki.guid_for(*content_fallback)


def note_for(card):
    """Build a genanki Note (basic or MCQ) with a stable, uid-derived GUID."""
    if card.get("format") == "mcq":
        return mcq_note_for(card)
    guid = _guid_for(card, card["front"], card["back"], card["leaf_tag"])
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
    guid = _guid_for(card, card["question"], *options, card["leaf_tag"])
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
    _rewrite_apkg_deterministically(out_path)

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
