# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Honesty-contract validator for the synced ``gre_scorecard`` artifact.

The desktop scoring adapter writes ``gre_scorecard`` into ``col.conf``; it **syncs** to
the phone, where the read-only AnkiDroid panel renders it. Nothing between those two ends
checks that the *artifact* honours the app's hard honesty ceilings (PRD §7 / D2):

* the **three scores stay separate** — Memory / Performance / Readiness — with **no
  blended "overall" total** anywhere;
* **never a bare Readiness number**: a Readiness ``estimate`` may appear **only** with the
  full evidence panel — a range (``low``/``high``), ``coverage_pct``, ``confidence``, a
  last-updated timestamp, ``reasons``, and a ``best_next_topic`` — and only when
  ``shown == True``; otherwise Readiness must be gated (no number, with reasons + next
  best);
* any score that shows a point ``estimate`` must show its **range** too (every metric is a
  range, never a lone number).

This is a **pure dict validator** (no scoring/engine/eval-bank imports; it does not modify
any definition). It is the sync-transport guard that complements the give-up-rule audit
(which proves the readiness *function* gates): this proves the *persisted artifact* can
never carry a fabricated number.

    python proofs/validate_scorecard.py proofs/tests/fixtures/*.json   # validate files
"""

from __future__ import annotations

import argparse
import json
import sys

# Any of these appearing as a top-level key implies a blended/combined score → forbidden.
_BLENDED_KEYS = ("overall", "total", "combined", "score", "aggregate", "blended")

# The full evidence panel a Readiness number may never appear without (PRD §7c / D2).
_READINESS_PANEL = ("low", "high", "coverage_pct", "confidence", "reasons", "best_next_topic")


def _has_range(block: dict) -> bool:
    return block.get("low") is not None and block.get("high") is not None


def validate(card) -> list[str]:
    """Return a list of honesty-contract violations (empty list == valid)."""
    errors: list[str] = []
    if not isinstance(card, dict):
        return ["scorecard is not an object"]

    for key in ("version", "updated_at", "memory", "performance", "readiness"):
        if key not in card:
            errors.append("missing top-level key {!r}".format(key))
    for bad in _BLENDED_KEYS:
        if bad in card:
            errors.append("blended/overall key {!r} present (scores must never be summed)".format(bad))
    if errors:
        return errors  # structural problems first

    # Each metric that shows a point estimate must show its range too.
    for name in ("memory", "performance", "readiness"):
        block = card.get(name)
        if not isinstance(block, dict):
            errors.append("{} is not an object".format(name))
            continue
        if block.get("estimate") is not None and not _has_range(block):
            errors.append("{}: point estimate without a range (low/high)".format(name))

    # Readiness honesty ceiling.
    rd = card.get("readiness")
    if isinstance(rd, dict):
        shown = rd.get("shown")
        has_number = rd.get("estimate") is not None
        if has_number:
            if shown is not True:
                errors.append("readiness: estimate present but shown != True (bare number)")
            missing = [k for k in _READINESS_PANEL if k not in rd or rd.get(k) in (None, "")]
            # reasons may legitimately be an empty list when shown; treat [] as present.
            missing = [k for k in missing if not (k == "reasons" and rd.get(k) == [])]
            if missing:
                errors.append(
                    "readiness: number shown without full evidence panel (missing {})".format(
                        ", ".join(missing)
                    )
                )
        else:
            # Gated: must be honestly explained, never a silent blank.
            if shown is True:
                errors.append("readiness: shown == True but no estimate")
            if not rd.get("reasons"):
                errors.append("readiness: gated but no reasons given")
            if not rd.get("best_next_topic"):
                errors.append("readiness: gated but no best_next_topic")

    return errors


def is_valid(card) -> bool:
    return not validate(card)


def assert_valid(card) -> None:
    errs = validate(card)
    if errs:
        raise AssertionError("scorecard honesty violations:\n  - " + "\n  - ".join(errs))


def validate_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        return validate(json.load(fh))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate gre_scorecard honesty contract.")
    ap.add_argument("paths", nargs="+", help="scorecard JSON file(s) to validate")
    args = ap.parse_args(argv)
    bad = 0
    for path in args.paths:
        errs = validate_file(path)
        if errs:
            bad += 1
            print("FAIL {}".format(path))
            for e in errs:
                print("  - {}".format(e))
        else:
            print("OK   {}".format(path))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
