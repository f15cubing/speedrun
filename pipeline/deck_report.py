"""Study-deck quality report + hard integrity gate (complements ``coverage_report``).

`coverage_report` proves the deck *covers* the taxonomy; this proves each card is
*well-formed*. It computes, prints, and ASSERTS deck-wide quality invariants:

1. **MCQ integrity** — every MCQ has exactly 5 **distinct** options, a valid
   ``correct_index``, and (when the ground-truth ``_correct_expr`` is present) the option
   at ``correct_index`` renders exactly that key. This is the "distractors provably ≠ key,
   correct-by-construction" guarantee (PRD §12/§12a) checked across the *whole* deck, not
   just per-generator unit tests.
2. **Required fields** — no empty stem/answer/explanation.

Readability *lengths* (stem/option) are **reported** for transparency but not gated (they
are stylistic, and conceptual cards vary). Run standalone
(``python pipeline/run_deck_report.py --seed 42 --strict``) it exits non-zero on any
integrity/required-field violation. Pure: reads the study deck only — never the held-out
eval bank, the scoring layer, or the engine.
"""

from __future__ import annotations

import mathfmt
import taxonomy

N_OPTIONS = 5


def card_uid(card) -> str:
    return card.get("uid") or card.get("question") or card.get("front") or "?"


def audit_mcq(card) -> list[str]:
    """Integrity violations for one MCQ card (empty list == clean)."""
    issues = []
    opts = card.get("options") or []
    if len(opts) != N_OPTIONS:
        issues.append("expected {} options, got {}".format(N_OPTIONS, len(opts)))
    if len(set(str(o) for o in opts)) != len(opts):
        issues.append("duplicate options")
    ci = card.get("correct_index")
    if not isinstance(ci, int) or not (0 <= ci < len(opts)):
        issues.append("correct_index {!r} out of range".format(ci))
    elif "_correct_expr" in card:
        expected = mathfmt.expr_inline(card["_correct_expr"])
        if opts[ci] != expected:
            issues.append(
                "key mismatch: option[{}]={!r} != rendered key {!r}".format(
                    ci, opts[ci], expected
                )
            )
    return issues


def required_fields(card) -> list[str]:
    """Violations for empty mandatory fields (empty list == clean)."""
    issues = []
    if card.get("format") == "mcq":
        for field in ("question", "explanation"):
            if not str(card.get(field, "")).strip():
                issues.append("empty {}".format(field))
    else:
        for field in ("front", "back"):
            if not str(card.get(field, "")).strip():
                issues.append("empty {}".format(field))
    return issues


def audit_card(card) -> list[str]:
    issues = list(required_fields(card))
    if card.get("format") == "mcq":
        issues += audit_mcq(card)
    return issues


def _lengths(cards):
    stem = [len(str(c.get("question") or c.get("front") or "")) for c in cards]
    opt = [len(str(o)) for c in cards for o in (c.get("options") or [])]
    return {
        "stem_max": max(stem) if stem else 0,
        "stem_mean": round(sum(stem) / len(stem), 1) if stem else 0.0,
        "option_max": max(opt) if opt else 0,
    }


def summarize_quality(cards) -> dict:
    """Deck-wide quality summary + the list of failing cards."""
    mcq = [c for c in cards if c.get("format") == "mcq"]
    failures = []
    for card in cards:
        issues = audit_card(card)
        if issues:
            failures.append(
                {"uid": card_uid(card), "format": card.get("format"), "issues": issues}
            )
    by_leaf_format: dict[str, dict[str, int]] = {}
    for card in cards:
        tag = card.get("leaf_tag")
        if taxonomy.validate_leaf_tag(tag):
            slot = by_leaf_format.setdefault(tag, {})
            fmt = card.get("format", "flashcard")
            slot[fmt] = slot.get(fmt, 0) + 1
    return {
        "total": len(cards),
        "mcq_total": len(mcq),
        "flashcard_total": len(cards) - len(mcq),
        "mcq_integrity_ok": all(not audit_mcq(c) for c in mcq),
        "num_failures": len(failures),
        "failures": failures,
        "lengths": _lengths(cards),
        "leaves_with_mcq": sum(1 for v in by_leaf_format.values() if v.get("mcq")),
    }


def assert_deck_quality(cards) -> dict:
    """Raise ``AssertionError`` on any integrity/required-field violation; else return summary."""
    summary = summarize_quality(cards)
    if summary["failures"]:
        raise AssertionError(
            "Deck quality gate FAILED: {} card(s) with issues, e.g.\n  {}".format(
                summary["num_failures"],
                "\n  ".join(str(f) for f in summary["failures"][:5]),
            )
        )
    return summary


def format_report(summary) -> str:
    lines = [
        "GRE Math study-deck quality report",
        "=" * 38,
        "Total cards:        {}  (mcq {}, flashcard {})".format(
            summary["total"], summary["mcq_total"], summary["flashcard_total"]
        ),
        "MCQ integrity:      {}".format("OK" if summary["mcq_integrity_ok"] else "FAILED"),
        "Leaves with MCQ:    {}".format(summary["leaves_with_mcq"]),
        "Stem length:        max {}, mean {}".format(
            summary["lengths"]["stem_max"], summary["lengths"]["stem_mean"]
        ),
        "Option length:      max {}".format(summary["lengths"]["option_max"]),
        "Quality violations: {}".format(summary["num_failures"]),
    ]
    for f in summary["failures"][:20]:
        lines.append("  - {} ({}): {}".format(f["uid"], f["format"], "; ".join(f["issues"])))
    return "\n".join(lines) + "\n"
