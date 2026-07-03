# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Non-nullable, verbatim-verified provenance for AI-generated cards (PRD §9).

Every generated fact must carry a **verbatim source quote + a source anchor**, and
both are **non-nullable**: a card whose provenance is missing, blank, or not found
verbatim in its anchored source passage is dropped by the pipeline (``abstain``),
*before* any downstream verification or scoring. This is provenance-by-schema —
abstention enforced by pipeline logic, not by asking the model nicely.

The check is intentionally strict and boring: the quote must appear as a contiguous
whitespace-normalised span of the anchored passage (``corpus.quote_in_passage``).
No fuzzy match, no "close enough". If the model did not lift a real span from a real
source location, the card does not exist.
"""

from __future__ import annotations

from dataclasses import dataclass

import corpus


class ProvenanceError(ValueError):
    """Raised when a card's provenance is missing, blank, or ungrounded."""


@dataclass(frozen=True)
class Provenance:
    """A verbatim source quote anchored to a corpus passage id.

    Both fields are required (the dataclass has no defaults), so a card literally
    cannot carry provenance without a quote *and* an anchor.
    """

    quote: str
    anchor: str


def check(prov, verifier=corpus.quote_in_passage) -> None:
    """Raise :class:`ProvenanceError` unless ``prov`` is present and grounded.

    ``verifier(anchor, quote) -> bool`` is injectable for testing; it defaults to
    the real corpus verbatim check.
    """
    if prov is None:
        raise ProvenanceError("provenance is missing (None): every fact needs a quote + anchor")
    quote = (getattr(prov, "quote", "") or "").strip()
    anchor = (getattr(prov, "anchor", "") or "").strip()
    if not quote:
        raise ProvenanceError("provenance quote is blank")
    if not anchor:
        raise ProvenanceError("provenance anchor is blank")
    if not verifier(anchor, quote):
        raise ProvenanceError(
            "provenance quote not found verbatim in source anchor {!r}".format(anchor)
        )


def is_valid(prov, verifier=corpus.quote_in_passage) -> bool:
    """Boolean form of :func:`check` (never raises)."""
    try:
        check(prov, verifier=verifier)
        return True
    except ProvenanceError:
        return False
