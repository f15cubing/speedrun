"""Guard: the dashboard's vendored taxonomy must equal pipeline/taxonomy.py."""
import json
from pathlib import Path

from pipeline import taxonomy as tx

VENDORED = Path(__file__).resolve().parents[1] / "anki/qt/aqt/gre/taxonomy.json"


def test_vendored_taxonomy_matches_pipeline():
    data = json.loads(VENDORED.read_text(encoding="utf-8"))
    assert tuple(b["name"] for b in data["buckets"]) == tx.BUCKETS
    for b in data["buckets"]:
        assert b["weight"] == tx.BUCKET_WEIGHTS[b["name"]]
        assert tuple(b["leaves"]) == tx.LEAVES_BY_BUCKET[b["name"]]
    # derived full leaf tags match, in order
    vendored_tags = [
        f'{data["tag_prefix"]}{data["tag_sep"]}{b["name"]}{data["tag_sep"]}{leaf}'
        for b in data["buckets"] for leaf in b["leaves"]
    ]
    assert tuple(vendored_tags) == tx.LEAF_TAGS
