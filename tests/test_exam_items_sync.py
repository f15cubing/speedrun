"""Guard: the vendored exam items must equal the authored eval bank.

Exam Mode ships a copy of the eval items inside the app
(`anki/qt/aqt/gre/exam_items.json`) because the app cannot read the outer
`eval/bank/items.yaml` at runtime. This asserts the copy can't drift from the
source (same pattern as `test_taxonomy_sync.py`).
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VENDORED = ROOT / "anki/qt/aqt/gre/exam_items.json"
SOURCE = ROOT / "eval/bank/items.yaml"

FIELDS = (
    "id", "leaf_tag", "question", "options", "correct_index",
    "explanation", "difficulty", "partition",
)


def _project(items):
    return [{k: it[k] for k in FIELDS} for it in items]


def test_vendored_exam_items_match_bank():
    src = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))["items"]
    vendored = json.loads(VENDORED.read_text(encoding="utf-8"))["items"]
    assert _project(vendored) == _project(src)
