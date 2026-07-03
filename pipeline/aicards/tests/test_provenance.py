# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the non-nullable, verbatim-verified provenance schema."""

import pytest

import provenance
from provenance import Provenance, ProvenanceError

REAL_QUOTE = (
    "The power rule states that the derivative of x raised to the power n is n "
    "times x raised to the power n minus one."
)
REAL_ANCHOR = "svc-03-power-rule"


def test_valid_provenance_passes():
    prov = Provenance(quote=REAL_QUOTE, anchor=REAL_ANCHOR)
    assert provenance.is_valid(prov) is True
    provenance.check(prov)  # must not raise


def test_none_provenance_is_invalid():
    assert provenance.is_valid(None) is False
    with pytest.raises(ProvenanceError):
        provenance.check(None)


def test_empty_quote_is_invalid():
    prov = Provenance(quote="   ", anchor=REAL_ANCHOR)
    assert provenance.is_valid(prov) is False
    with pytest.raises(ProvenanceError):
        provenance.check(prov)


def test_empty_anchor_is_invalid():
    prov = Provenance(quote=REAL_QUOTE, anchor="")
    assert provenance.is_valid(prov) is False
    with pytest.raises(ProvenanceError):
        provenance.check(prov)


def test_quote_not_in_source_is_invalid():
    # A fabricated (hallucinated) quote is not present verbatim in the anchor.
    prov = Provenance(quote="The derivative of x is always seventeen.", anchor=REAL_ANCHOR)
    assert provenance.is_valid(prov) is False
    with pytest.raises(ProvenanceError):
        provenance.check(prov)


def test_wrong_anchor_is_invalid():
    # Real quote, but anchored to a passage that does not contain it.
    prov = Provenance(quote=REAL_QUOTE, anchor="svc-12-the-definite-integral")
    assert provenance.is_valid(prov) is False


def test_provenance_cannot_be_constructed_without_fields():
    # The schema is non-nullable at the type level too.
    with pytest.raises(TypeError):
        Provenance(quote=REAL_QUOTE)  # missing anchor
