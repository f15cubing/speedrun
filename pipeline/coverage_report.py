"""Coverage report + hard gate for the GRE study deck.

Computes, prints, and ASSERTS the invariants that make the deck defensible:

1. Every card carries **exactly one valid leaf tag** (``topic::<bucket>::<leaf>``).
2. At least ``MIN_LEAF_COVERAGE`` of the 17 taxonomy leaves are covered
   (>=9 leaves; the readiness give-up rule's coverage proxy).
3. At least ``MIN_CALCULUS_CARD_WEIGHT`` of the cards are calculus-tagged
   (reflecting the ~50% ETS calculus weight).

Run standalone (``python pipeline/coverage_report.py --seed 42``) it builds the
merged card set and exits non-zero on any violation. ``build_deck`` also calls
``assert_coverage`` after writing the ``.apkg``.
"""

from __future__ import annotations

import argparse
import sys

import taxonomy


def summarize(cards):
    """Return a dict of coverage statistics for a list of card dicts."""
    per_leaf = {tag: 0 for tag in taxonomy.LEAF_TAGS}
    invalid = []
    calc_cards = 0
    by_format = {}
    for index, card in enumerate(cards):
        fmt = card.get("format", "flashcard") if isinstance(card, dict) else "?"
        by_format[fmt] = by_format.get(fmt, 0) + 1
        tag = card.get("leaf_tag") if isinstance(card, dict) else None
        if not taxonomy.validate_leaf_tag(tag):
            invalid.append((index, tag))
            continue
        per_leaf[tag] += 1
        if taxonomy.bucket_of(tag) == taxonomy.CALCULUS_BUCKET:
            calc_cards += 1
    total = len(cards)
    covered = [tag for tag, n in per_leaf.items() if n > 0]
    return {
        "total": total,
        "per_leaf": per_leaf,
        "covered_leaves": covered,
        "num_covered": len(covered),
        "num_leaves": len(taxonomy.LEAF_TAGS),
        "leaf_coverage": (len(covered) / len(taxonomy.LEAF_TAGS)) if taxonomy.LEAF_TAGS else 0.0,
        "calc_cards": calc_cards,
        "calc_weight": (calc_cards / total) if total else 0.0,
        "by_format": by_format,
        "invalid": invalid,
    }


def format_report(summary):
    """Render a human-readable coverage report string."""
    lines = []
    lines.append("GRE Math study-deck coverage report")
    lines.append("=" * 38)
    lines.append("Total cards:      {}".format(summary["total"]))
    lines.append(
        "Leaves covered:   {}/{}  ({:.1f}%)  [gate >= {:.0f}%]".format(
            summary["num_covered"],
            summary["num_leaves"],
            100 * summary["leaf_coverage"],
            100 * taxonomy.MIN_LEAF_COVERAGE,
        )
    )
    lines.append(
        "Calculus weight:  {}/{}  ({:.1f}%)  [gate >= {:.0f}%]".format(
            summary["calc_cards"],
            summary["total"],
            100 * summary["calc_weight"],
            100 * taxonomy.MIN_CALCULUS_CARD_WEIGHT,
        )
    )
    lines.append(
        "By format:        " + ", ".join(
            "{}={}".format(k, summary["by_format"][k]) for k in sorted(summary["by_format"])
        )
    )
    lines.append("")
    lines.append("Per-leaf card counts:")
    for bucket in taxonomy.BUCKETS:
        lines.append(
            "  {} (exam weight ~{:.0f}%)".format(
                bucket, 100 * taxonomy.BUCKET_WEIGHTS[bucket]
            )
        )
        for leaf in taxonomy.LEAVES_BY_BUCKET[bucket]:
            tag = taxonomy.TAG_BY_LEAF[leaf]
            count = summary["per_leaf"][tag]
            marker = "" if count > 0 else "  <-- MISSING"
            lines.append("    {:<24} {:>3}{}".format(leaf, count, marker))
    if summary["invalid"]:
        lines.append("")
        lines.append("INVALID leaf tags (index, tag):")
        for index, tag in summary["invalid"][:20]:
            lines.append("    #{}: {!r}".format(index, tag))
    return "\n".join(lines)


def assert_coverage(cards):
    """Raise ``AssertionError`` if any coverage invariant is violated.

    Returns the summary dict on success.
    """
    summary = summarize(cards)
    errors = []
    if summary["total"] == 0:
        errors.append("no cards produced")
    if summary["invalid"]:
        errors.append(
            "{} card(s) do not carry exactly one valid leaf tag (e.g. {})".format(
                len(summary["invalid"]), summary["invalid"][:5]
            )
        )
    if summary["leaf_coverage"] < taxonomy.MIN_LEAF_COVERAGE:
        errors.append(
            "leaf coverage {:.1%} is below the required {:.0%}".format(
                summary["leaf_coverage"], taxonomy.MIN_LEAF_COVERAGE
            )
        )
    if summary["calc_weight"] < taxonomy.MIN_CALCULUS_CARD_WEIGHT:
        errors.append(
            "calculus card weight {:.1%} is below the required {:.0%}".format(
                summary["calc_weight"], taxonomy.MIN_CALCULUS_CARD_WEIGHT
            )
        )
    if errors:
        raise AssertionError(
            "Coverage gate FAILED:\n  - " + "\n  - ".join(errors)
        )
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print and assert GRE study-deck coverage."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for the generated cards (default: 42).",
    )
    args = parser.parse_args(argv)

    # Lazy import to avoid an import cycle (build_deck imports this module).
    from build_deck import assert_all_verified, load_all_cards

    assert_all_verified()
    cards = load_all_cards(seed=args.seed)
    summary = summarize(cards)
    print(format_report(summary))
    try:
        assert_coverage(cards)
    except AssertionError as exc:
        print("\n" + str(exc), file=sys.stderr)
        return 1
    print("\nCoverage gate PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
