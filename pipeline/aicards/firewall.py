# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Firewall / leakage guards for the AI card pipeline (PRD §9/§11/§12).

The hard ceiling: the held-out **gold-set** and **eval bank** answers must never
enter generation, and no official **ETS** item may be used anywhere. This module
provides re-runnable, committed checks (they key off the committed canary GUID and
static source scans, never the gitignored held-out data), so they pass on a fresh
clone with no access-controlled files present:

* the source corpus and everything fed to generation carry **no canary** (the
  sentinel that marks held-out items) and **no ETS/GRE markers**;
* every generated card is grounded to a **source-corpus passage id** (``svc-*``),
  never a gold-set id (``gNNN``);
* the generation code **never references** the held-out store paths.
"""

from __future__ import annotations

import os
import re

import corpus

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))  # pipeline/aicards -> pipeline -> repo
CANARY_MANIFEST = os.path.join(REPO_ROOT, "eval", "goldset", "canary-manifest.md")

_GUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_CANARY_PREFIX = "CANARY-GRE-SPEEDRUN"

# Contamination markers. Case-sensitive acronyms so we do not match "sets"/"targets".
_ETS_MARKERS = ("Educational Testing Service", "GR3768")
_ACRONYM_RE = re.compile(r"\b(ETS|GRE)\b")
_OCW_MARKER = "ocw.mit.edu"

# Held-out store path fragments the *generation* code must never reference.
_HELDOUT_MARKERS = ("goldset/data", "pairs.jsonl", "eval/bank", "eval\\bank")

# Only the modules that participate in GENERATION are scanned (gate/firewall are
# eval-side and legitimately mention the gold-set by name).
GENERATION_MODULES = (
    "corpus.py", "retriever.py", "provenance.py", "verify.py",
    "cards.py", "stub_model.py", "orchestrator.py",
)


def read_canary_guid(path: str = CANARY_MANIFEST) -> str:
    """Parse the project canary GUID from the committed manifest."""
    with open(path, "r", encoding="utf-8") as handle:
        m = _GUID_RE.search(handle.read())
    if not m:
        raise ValueError("no canary GUID found in {}".format(path))
    return m.group(0)


def canary_hits(text: str, guid: str) -> int:
    """Count canary occurrences (the GUID itself or the sentinel prefix)."""
    return text.count(guid) + text.count(_CANARY_PREFIX)


def _ets_hits(text: str):
    hits = [m for m in _ETS_MARKERS if m in text]
    hits += _ACRONYM_RE.findall(text)
    return hits


def scan_corpus() -> dict:
    text = corpus.corpus_text()
    guid = read_canary_guid()
    return {
        "canary_free": canary_hits(text, guid) == 0,
        "ets_free": _ets_hits(text) == [],
        "ocw_url_free": _OCW_MARKER not in text,
    }


def generation_input_text(backend) -> str:
    """Everything fed INTO generation: the corpus + the retrieval queries."""
    parts = [corpus.corpus_text()]
    parts.extend(req.query for req in backend.plan())
    return "\n".join(parts)


def scan_generation_inputs(backend) -> dict:
    text = generation_input_text(backend)
    guid = read_canary_guid()
    return {
        "canary_free": canary_hits(text, guid) == 0,
        "ets_free": _ets_hits(text) == [],
        "ocw_url_free": _OCW_MARKER not in text,
    }


def _outcome_text(outcomes) -> str:
    parts = []
    for o in outcomes:
        parts.append(o.card.front or "")
        parts.append(o.card.back or "")
        if o.card.provenance:
            parts.append(o.card.provenance.quote or "")
    return "\n".join(parts)


def scan_outputs(outcomes) -> dict:
    text = _outcome_text(outcomes)
    guid = read_canary_guid()
    return {
        "canary_free": canary_hits(text, guid) == 0,
        "ets_free": _ets_hits(text) == [],
    }


def generation_modules_referencing_heldout():
    """Return generation module filenames that reference the held-out store."""
    offenders = []
    for name in GENERATION_MODULES:
        path = os.path.join(HERE, name)
        with open(path, "r", encoding="utf-8") as handle:
            src = handle.read()
        if any(marker in src for marker in _HELDOUT_MARKERS):
            offenders.append(name)
    return offenders


def run_firewall(backend, outcomes) -> dict:
    """Aggregate all firewall checks into one pass/fail report."""
    corpus_scan = scan_corpus()
    input_scan = scan_generation_inputs(backend)
    output_scan = scan_outputs(outcomes)
    heldout_refs = generation_modules_referencing_heldout()
    goldset_id = re.compile(r"^g\d{3}$")
    bad_anchors = [
        o.card.card_id for o in outcomes
        if goldset_id.match(o.card.provenance.anchor) or not o.card.provenance.anchor.startswith("svc-")
    ]
    checks = {
        "corpus_canary_free": corpus_scan["canary_free"],
        "corpus_ets_free": corpus_scan["ets_free"],
        "corpus_ocw_url_free": corpus_scan["ocw_url_free"],
        "inputs_canary_free": input_scan["canary_free"],
        "inputs_ets_free": input_scan["ets_free"],
        "outputs_canary_free": output_scan["canary_free"],
        "anchors_all_from_corpus": bad_anchors == [],
        "generation_never_reads_heldout": heldout_refs == [],
    }
    return {"passed": all(checks.values()), "checks": checks,
            "heldout_refs": heldout_refs, "bad_anchors": bad_anchors}
