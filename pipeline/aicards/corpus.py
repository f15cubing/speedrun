# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Load the RAG *source chapter* into anchored passages.

The AI card pipeline (``pipeline/aicards/``) retrieves over these passages and
every generated card must carry a **non-nullable verbatim quote + source anchor**
back to one of them (``provenance.py``). This module is the single source of truth
for what the corpus contains and whether a quote is genuinely present.

Parsing is deterministic: the Markdown chapter is split on level >= 2 headings
(``##`` / ``###``); each becomes one passage with a stable, readable anchor id
(``svc-<NN>-<slug>``). Quote matching is **whitespace-normalised verbatim** — the
quote must appear as a contiguous span of the passage after collapsing runs of
whitespace (so a single-line quote still matches text that is line-wrapped in the
file), never a fuzzy/semantic match.

No network, no model calls, no external deps (stdlib only).
"""

from __future__ import annotations

import os
import re
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES_DIR = os.path.join(HERE, "sources")
DEFAULT_CHAPTER = os.path.join(SOURCES_DIR, "single_variable_calculus.md")

Passage = namedtuple("Passage", ["id", "heading", "text"])

_HEADING_RE = re.compile(r"^(#{2,})\s+(.*\S)\s*$")
_COMMENT_OPEN = "<!--"
_COMMENT_CLOSE = "-->"
_WS_RE = re.compile(r"\s+")


def normalize_ws(text: str) -> str:
    """Collapse all runs of whitespace to single spaces and strip the ends."""
    return _WS_RE.sub(" ", text).strip()


def _slug(heading: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return slug or "section"


def _strip_comments(lines):
    """Drop HTML comment blocks (``<!-- ... -->``) so they are never quotable."""
    out = []
    in_comment = False
    for line in lines:
        stripped = line.strip()
        if not in_comment and stripped.startswith(_COMMENT_OPEN):
            # Single-line or multi-line comment start.
            if _COMMENT_CLOSE in stripped:
                continue
            in_comment = True
            continue
        if in_comment:
            if _COMMENT_CLOSE in stripped:
                in_comment = False
            continue
        out.append(line)
    return out


def parse_chapter(md_text: str):
    """Parse Markdown chapter text into an ordered list of :class:`Passage`.

    A passage starts at each level >= 2 heading and runs until the next such
    heading. The H1 title and any content before the first level-2 heading are
    ignored (not quotable grounding material).
    """
    lines = _strip_comments(md_text.splitlines())
    passages = []
    ordinal = 0
    cur_heading = None
    cur_lines: list[str] = []

    def _flush():
        nonlocal ordinal
        if cur_heading is None:
            return
        body = "\n".join(cur_lines).strip()
        if not body:
            return
        ordinal += 1
        pid = "svc-{:02d}-{}".format(ordinal, _slug(cur_heading))
        passages.append(Passage(id=pid, heading=cur_heading, text=body))

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            _flush()
            cur_heading = m.group(2).strip()
            cur_lines = []
        else:
            if cur_heading is not None:
                cur_lines.append(line)
    _flush()
    return passages


def load_corpus(path: str = DEFAULT_CHAPTER):
    """Load and parse the source chapter at ``path`` into passages."""
    with open(path, "r", encoding="utf-8") as handle:
        return parse_chapter(handle.read())


# Loaded once at import for the default chapter; the pipeline reuses this.
PASSAGES = load_corpus()
PASSAGE_BY_ID = {p.id: p for p in PASSAGES}


def quote_in_passage(anchor: str, quote: str) -> bool:
    """True iff ``quote`` appears verbatim (ws-normalised) in passage ``anchor``."""
    passage = PASSAGE_BY_ID.get(anchor)
    if passage is None:
        return False
    q = normalize_ws(quote)
    if not q:
        return False
    return q in normalize_ws(passage.text)


def passages_containing(quote: str):
    """Return every passage whose (ws-normalised) text contains ``quote``."""
    q = normalize_ws(quote)
    if not q:
        return []
    return [p for p in PASSAGES if q in normalize_ws(p.text)]


def corpus_text() -> str:
    """The full concatenated corpus text (for firewall / leakage scans)."""
    return "\n\n".join(p.text for p in PASSAGES)
