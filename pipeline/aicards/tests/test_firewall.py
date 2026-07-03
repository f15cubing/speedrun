# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Firewall / leakage tests (PRD §9/§11/§12): train and test never share items.

The held-out gold-set + eval bank answers must NEVER enter generation. These checks
key off the COMMITTED canary GUID (not the gitignored data), so they are fully
re-runnable on a fresh clone.
"""

import re

import firewall
import orchestrator
from stub_model import StubBackend

GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _outcomes():
    return orchestrator.run_pipeline(StubBackend(seed=42))


def test_project_canary_guid_is_parsed_from_committed_manifest():
    guid = firewall.read_canary_guid()
    assert GUID_RE.match(guid)


def test_source_corpus_contains_no_canary():
    assert firewall.canary_hits(firewall.corpus.corpus_text(), firewall.read_canary_guid()) == 0


def test_generation_inputs_are_clean():
    report = firewall.scan_generation_inputs(StubBackend(seed=42))
    assert report["canary_free"] is True
    assert report["ets_free"] is True
    assert report["ocw_url_free"] is True


def test_generated_outputs_carry_no_canary():
    assert firewall.scan_outputs(_outcomes())["canary_free"] is True


def test_corpus_has_no_ets_or_gre_markers():
    report = firewall.scan_corpus()
    assert report["ets_free"] is True


def test_every_provenance_anchor_is_a_corpus_passage_not_a_goldset_id():
    goldset_id = re.compile(r"^g\d{3}$")
    for o in _outcomes():
        anchor = o.card.provenance.anchor
        assert not goldset_id.match(anchor), "card grounded to a gold-set id!"
        assert anchor.startswith("svc-"), "anchor {!r} is not a source-corpus passage".format(anchor)


def test_generation_modules_never_reference_the_heldout_store():
    offenders = firewall.generation_modules_referencing_heldout()
    assert offenders == [], "generation code must not read the held-out store: {}".format(offenders)


def test_full_firewall_report_passes():
    report = firewall.run_firewall(StubBackend(seed=42), _outcomes())
    assert report["passed"] is True
