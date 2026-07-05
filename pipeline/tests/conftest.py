"""Make the ``pipeline/`` modules importable when pytest collects from the repo root.

Also exposes **session-scoped** fixtures for the expensive deterministic builds. The
seeded deck is byte-stable (proven by ``test_determinism`` / ``test_stable_guids``,
which build fresh), so every *read-only* test can share a single build instead of each
paying the ~45s SymPy generation cost — this keeps the suite fast now that MCQ spans all
11 computational leaves (~7.3k cards). **Do not mutate** the objects these fixtures return.
"""

import os
import sys

import pytest

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)


@pytest.fixture(scope="session")
def all_cards():
    """The full merged study deck (flashcards + MCQ + conceptual) at seed 42."""
    import build_deck

    return build_deck.load_all_cards(seed=42)


@pytest.fixture(scope="session")
def mcq_cards():
    """The computational MCQ card list at seed 42."""
    import generate_mcq

    return generate_mcq.generate_mcq_cards(seed=42)


@pytest.fixture(scope="session")
def flashcards():
    """The generated flashcard list at seed 42."""
    import generate_deck

    return generate_deck.generate_cards(seed=42)
