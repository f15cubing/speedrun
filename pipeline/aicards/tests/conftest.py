# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Put ``pipeline/aicards/`` and ``pipeline/`` on sys.path for the AI-cards tests.

Mirrors ``pipeline/tests/conftest.py``: the AI-card modules use flat imports
(``import corpus``, ``import verify``, …) and also reuse the sibling pipeline
modules (``import taxonomy``, ``import distractors``, ``import mathfmt``).
"""

import os
import sys

AICARDS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.dirname(AICARDS_DIR)
for _p in (AICARDS_DIR, PIPELINE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
