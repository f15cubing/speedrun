"""The human-verification gate on conceptual cards (PRD §12a)."""

import textwrap

import pytest

import build_deck


def _write(tmp_path, body):
    p = tmp_path / "cards.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(p)


def test_only_verified_cards_are_loaded(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q1"
            back: "A1"
            status: verified
            verified_by: "fc"
            verified_on: "2026-06-30"
            source: "original"
          - leaf_tag: "topic::algebra::abstract"
            front: "Q2 (draft)"
            back: "A2"
            status: draft
            verified_by: ""
            verified_on: ""
            source: "original"
        """,
    )
    cards = build_deck.load_conceptual_cards(path=path)
    fronts = [c["front"] for c in cards]
    assert fronts == ["Q1"]  # the draft is skipped


def test_verified_without_attribution_hard_fails(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q"
            back: "A"
            status: verified
            verified_by: ""
            verified_on: "2026-06-30"
            source: "original"
        """,
    )
    with pytest.raises(ValueError):
        build_deck.load_conceptual_cards(path=path)


def test_unknown_status_hard_fails(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q"
            back: "A"
            status: approved
            verified_by: "fc"
            verified_on: "2026-06-30"
            source: "original"
        """,
    )
    with pytest.raises(ValueError):
        build_deck.load_conceptual_cards(path=path)


def test_strict_mode_fails_on_any_draft(tmp_path):
    path = _write(
        tmp_path,
        """
        cards:
          - leaf_tag: "topic::algebra::abstract"
            front: "Q"
            back: "A"
            status: draft
            verified_by: ""
            verified_on: ""
            source: "original"
        """,
    )
    with pytest.raises(ValueError):
        build_deck.load_conceptual_cards(path=path, strict=True)


def test_production_yaml_is_fully_verified():
    # The committed production file must contain zero drafts.
    build_deck.assert_all_verified()
