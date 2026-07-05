"""Vendor the eval bank into Exam Mode's in-app copy.

Exam Mode ships inside the desktop app and cannot read the outer
`eval/bank/items.yaml` at runtime, so it reads a vendored projection at
`anki/qt/aqt/gre/exam_items.json`. This script regenerates that projection from
the corpus so the copy can never silently drift (guarded by
`tests/test_exam_items_sync.py`). Run it after changing `items.yaml`:

    python eval/bank/vendor_exam_items.py

Only the exam-facing fields are vendored (no provenance/attribution), matching
the drift-guard's projection exactly.
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
# `loader` lives here; it imports `taxonomy` from pipeline/ — put both on path
# so this runs standalone (`python eval/bank/vendor_exam_items.py`).
for _p in (_HERE, os.path.join(_ROOT, "pipeline")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import loader

# The exact fields (and order) the drift guard compares — see
# tests/test_exam_items_sync.py.
FIELDS = (
    "id", "leaf_tag", "question", "options", "correct_index",
    "explanation", "difficulty", "partition",
)

VENDORED = os.path.join(_ROOT, "anki", "qt", "aqt", "gre", "exam_items.json")


def project(items):
    return [{k: item[k] for k in FIELDS} for item in items]


def vendor(path=VENDORED):
    """Load + validate the corpus, then write the exam-facing projection."""
    items = loader.load_eval_items()  # validates the whole bank first
    payload = {"items": project(items)}
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=4, ensure_ascii=False))
        handle.write("\n")
    return len(items)


if __name__ == "__main__":
    n = vendor()
    print("vendored {} items -> {}".format(n, VENDORED))
