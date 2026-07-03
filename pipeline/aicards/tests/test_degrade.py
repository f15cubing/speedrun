# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""AI-off degradation proof (PRD §9): no model / no network degrades gracefully.

The AI card pipeline is a BUILD-TIME content step, not a runtime dependency. With no
API key: (a) the live-model seam fails loudly; (b) run_pipeline_safe aborts cleanly
with ZERO unverified cards emitted; (c) the study/review deck + the scoring layer
still load and produce content because they never call a model.
"""

import os
import sys

import pytest

import orchestrator
from orchestrator import LlmBackend, NoLiveModelError

HERE = os.path.dirname(os.path.abspath(__file__))
AICARDS_DIR = os.path.dirname(HERE)
PIPELINE_DIR = os.path.dirname(AICARDS_DIR)
REPO_ROOT = os.path.dirname(PIPELINE_DIR)

LLM_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AI_CARDS_LLM_KEY")


@pytest.fixture
def no_api_keys(monkeypatch):
    for var in LLM_KEYS:
        monkeypatch.delenv(var, raising=False)
    yield


# --- (a) the seam fails loudly ---------------------------------------------
def test_live_backend_raises_without_key(no_api_keys):
    with pytest.raises(NoLiveModelError):
        LlmBackend().plan()


# --- (b) the pipeline degrades cleanly: zero unverified cards --------------
def test_run_pipeline_safe_aborts_cleanly_without_model(no_api_keys):
    result = orchestrator.run_pipeline_safe(LlmBackend())
    assert result.ok is False
    assert result.outcomes == []
    assert result.published == []          # ZERO cards emitted
    assert "0 unverified cards" in result.message
    assert "unavailable" in result.message.lower()


def test_run_pipeline_safe_still_works_with_the_stub(no_api_keys):
    # A working backend (the deterministic stub) still runs under the safe wrapper.
    from stub_model import StubBackend
    result = orchestrator.run_pipeline_safe(StubBackend(seed=42))
    assert result.ok is True
    assert len(result.published) == 35


# --- (c) study/review + scoring never depend on a model --------------------
def test_study_deck_content_loads_without_a_model(no_api_keys):
    # The verified conceptual deck (review content) loads with no key present and
    # calls no model — it is human-authored, build-time content.
    if PIPELINE_DIR not in sys.path:
        sys.path.insert(0, PIPELINE_DIR)
    import build_deck
    cards = build_deck.load_conceptual_cards()
    assert len(cards) > 0


def test_scoring_layer_imports_without_a_model(no_api_keys):
    # The scoring package (Memory/Performance/Readiness) has no AI/network import.
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    import importlib
    for mod in ("scoring.readiness", "scoring.performance", "scoring.scorecard"):
        importlib.import_module(mod)  # must not raise / must not need a model


def test_review_and_scoring_code_never_reference_a_live_model():
    # Static guard: the app-review/scoring surfaces must not import the AI generator
    # or any network/model client. (aicards is build-time only.)
    banned = ("import orchestrator", "LlmBackend", "import openai", "import anthropic",
              "import requests", "urllib.request")
    scanned = 0
    for base in (os.path.join(REPO_ROOT, "scoring"),):
        for name in os.listdir(base):
            if not name.endswith(".py"):
                continue
            scanned += 1
            with open(os.path.join(base, name), encoding="utf-8") as fh:
                src = fh.read()
            for token in banned:
                assert token not in src, "{} references {!r}".format(name, token)
    assert scanned > 0
