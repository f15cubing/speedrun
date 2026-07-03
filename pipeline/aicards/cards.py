# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""The AI-generated card model.

A ``GeneratedCard`` carries the human-facing text (``front``/``back``), its
**non-nullable provenance** (a verbatim quote + source anchor), a machine-checkable
``check`` payload for computational cards (the SymPy ground truth used by the CAS
verifier and the raters), and generation metadata. Computational cards can be
*proved* correct (SymPy); conceptual cards can only be *entailment-checked* and are
therefore always routed to mandatory human review (PRD §9).

The ``check`` payload keeps the SymPy truth **separate from the rendered text**
(same pattern as the study-deck generators' test-only ``_expr`` key): correctness
is decided on expressions, never on marked-up strings a model wrote.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from provenance import Provenance

COMPUTATIONAL = "computational"
CONCEPTUAL = "conceptual"


@dataclass
class GeneratedCard:
    card_id: str
    leaf_tag: str
    kind: str  # COMPUTATIONAL | CONCEPTUAL
    front: str
    back: str
    provenance: Optional[Provenance] = None
    # Computational verification payload: {"op": ..., ...sympy args..., } + "claimed".
    check: Optional[dict] = field(default=None)
    gen: str = "ai"          # gen::ai — all cards here are AI-drafted
    status: str = "draft"    # draft until verified (computational: CAS; conceptual: human)
    tags: tuple = ()

    def anki_tags(self):
        """The tags an emitted note would carry: the leaf tag + gen provenance."""
        base = [self.leaf_tag, "gen::ai"]
        base.extend(self.tags)
        return tuple(base)
