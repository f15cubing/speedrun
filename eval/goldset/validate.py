#!/usr/bin/env python3
"""Validate the AI gold-set (eval/goldset/data/pairs.jsonl).

Loads the GITIGNORED held-out data file and asserts that every record:
  * has all required fields (id, question, answer, source, leaf_tag,
    second_solver_check, canary), with no unknown top-level fields;
  * carries a VALID taxonomy leaf tag (one of the 17 leaves in schema.json);
  * has a complete source anchor (course + problem_set + problem_no + an
    ocw.mit.edu url);
  * has a non-empty second_solver_check note;
  * carries a per-item canary matching the project sentinel pattern.

Also checks ids are unique and well-formed, then prints the total count and the
per-leaf distribution. Exits non-zero on ANY violation (including a missing or
empty data file), so it can gate CI / the Friday eval run.

Dependency-free (stdlib only); runs on python 3.9+.

Usage:  python eval/goldset/validate.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "schema.json")
DATA_PATH = os.path.join(HERE, "data", "pairs.jsonl")

REQUIRED_TOP = ("id", "question", "answer", "source", "leaf_tag",
                "second_solver_check", "canary")
REQUIRED_SOURCE = ("course", "problem_set", "problem_no", "url")
ID_RE = re.compile(r"^g[0-9]{3}$")


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    props = schema["properties"]
    leaf_tags = set(props["leaf_tag"]["enum"])
    canary_re = re.compile(props["canary"]["pattern"])
    url_re = re.compile(props["source"]["properties"]["url"]["pattern"])
    return leaf_tags, canary_re, url_re


def validate():
    leaf_tags, canary_re, url_re = load_schema()

    if not os.path.exists(DATA_PATH):
        print("FAIL: data file not found: %s" % DATA_PATH, file=sys.stderr)
        print("      (the gold-set Q&A data is access-controlled / gitignored; "
              "regenerate it per eval/goldset/README.md before validating)",
              file=sys.stderr)
        return 1

    errors = []
    seen_ids = set()
    leaf_counts = {}
    total = 0

    with open(DATA_PATH, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            total += 1
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append("line %d: invalid JSON (%s)" % (lineno, exc))
                continue

            tag = "line %d" % lineno
            if isinstance(rec, dict) and ID_RE.match(str(rec.get("id", ""))):
                tag = "%s (%s)" % (rec["id"], tag)

            if not isinstance(rec, dict):
                errors.append("%s: record is not a JSON object" % tag)
                continue

            for field in REQUIRED_TOP:
                if field not in rec:
                    errors.append("%s: missing required field '%s'" % (tag, field))
            for field in rec:
                if field not in REQUIRED_TOP:
                    errors.append("%s: unexpected top-level field '%s'" % (tag, field))

            rid = rec.get("id", "")
            if not ID_RE.match(str(rid)):
                errors.append("%s: id must match ^g[0-9]{3}$ (got %r)" % (tag, rid))
            elif rid in seen_ids:
                errors.append("%s: duplicate id %r" % (tag, rid))
            else:
                seen_ids.add(rid)

            if not str(rec.get("question", "")).strip():
                errors.append("%s: empty question" % tag)
            if not str(rec.get("answer", "")).strip():
                errors.append("%s: empty answer" % tag)

            src = rec.get("source")
            if not isinstance(src, dict):
                errors.append("%s: source must be an object" % tag)
            else:
                for field in REQUIRED_SOURCE:
                    if not str(src.get(field, "")).strip():
                        errors.append("%s: source missing '%s'" % (tag, field))
                url = str(src.get("url", ""))
                if url and not url_re.match(url):
                    errors.append("%s: source url is not an ocw.mit.edu URL (%r)" % (tag, url))

            leaf = rec.get("leaf_tag", "")
            if leaf not in leaf_tags:
                errors.append("%s: invalid leaf_tag %r (not one of the 17 taxonomy leaves)" % (tag, leaf))
            else:
                leaf_counts[leaf] = leaf_counts.get(leaf, 0) + 1

            if not str(rec.get("second_solver_check", "")).strip():
                errors.append("%s: empty second_solver_check" % tag)

            canary = str(rec.get("canary", ""))
            if not canary_re.match(canary):
                errors.append("%s: canary does not match project sentinel pattern (%r)" % (tag, canary))
            elif rid and ID_RE.match(str(rid)) and not canary.endswith("-item-%s" % rid[1:]):
                errors.append("%s: canary item suffix does not match id (%r)" % (tag, canary))

    if total == 0:
        errors.append("data file is empty (expected gold-set records)")

    # ---- report ----
    print("AI gold-set validation: %s" % DATA_PATH)
    print("records: %d" % total)
    print("per-leaf distribution:")
    for leaf in sorted(leaf_counts):
        print("  %3d  %s" % (leaf_counts[leaf], leaf))
    calc = sum(v for k, v in leaf_counts.items() if k.startswith("topic::calculus::"))
    if total:
        print("calculus weight: %d/%d (%.0f%%)" % (calc, total, 100.0 * calc / total))

    if errors:
        print("\nVALIDATION FAILED: %d violation(s):" % len(errors), file=sys.stderr)
        for e in errors:
            print("  - %s" % e, file=sys.stderr)
        return 1

    print("\nOK: all %d records valid." % total)
    return 0


if __name__ == "__main__":
    sys.exit(validate())
