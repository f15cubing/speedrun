"""Load + validate the authored eval bank (eval/bank/items.yaml).

Pure Python (no Anki/engine deps). Enforces the record schema, the human
verification gate, MCQ well-formedness, difficulty range, partition validity,
and P3 paraphrase-group integrity. `assert_firewall` guards against overlap
with the study deck (the rigorous leakage scan is a separate pipeline).
"""
from __future__ import annotations

import os
import re

import yaml

import taxonomy

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS_YAML = os.path.join(HERE, "items.yaml")

PARTITIONS = ("p0", "p1", "p2", "p3")
_REQUIRED = ("id", "leaf_tag", "format", "question", "options", "correct_index",
             "explanation", "difficulty", "partition", "src", "gen", "status",
             "verified_by", "verified_on")
_ATTRIBUTION = ("verified_by", "verified_on", "src")
N_OPTIONS = 5


def _fail(msg):
    raise ValueError("eval-bank: " + msg)


def _validate_item(index, item):
    for key in _REQUIRED:
        if key not in item:
            _fail("item #{} missing field {!r}".format(index, key))
    if str(item["status"]).strip() != "verified":
        _fail("item {!r} is not verified (status={!r})".format(item["id"], item["status"]))
    for key in _ATTRIBUTION:
        if not str(item.get(key, "")).strip():
            _fail("item {!r} missing attribution {!r}".format(item["id"], key))
    if item["format"] != "mcq":
        _fail("item {!r} has unsupported format {!r}".format(item["id"], item["format"]))
    if not taxonomy.validate_leaf_tag(item["leaf_tag"]):
        _fail("item {!r} has invalid leaf tag {!r}".format(item["id"], item["leaf_tag"]))
    opts = item["options"]
    if not isinstance(opts, list) or len(opts) != N_OPTIONS:
        _fail("item {!r} must have {} options".format(item["id"], N_OPTIONS))
    if len(set(str(o) for o in opts)) != N_OPTIONS:
        _fail("item {!r} has duplicate options".format(item["id"]))
    ci = item["correct_index"]
    if not isinstance(ci, int) or not (0 <= ci < N_OPTIONS):
        _fail("item {!r} has bad correct_index {!r}".format(item["id"], ci))
    if not (isinstance(item["difficulty"], int) and 1 <= item["difficulty"] <= 5):
        _fail("item {!r} difficulty must be int 1..5".format(item["id"]))
    if item["partition"] not in PARTITIONS:
        _fail("item {!r} bad partition {!r}".format(item["id"], item["partition"]))
    if item["partition"] == "p3":
        if not str(item.get("paraphrase_group") or "").strip():
            _fail("p3 item {!r} needs paraphrase_group".format(item["id"]))
        if not str(item.get("base_ref") or "").strip():
            _fail("p3 item {!r} needs base_ref".format(item["id"]))


def _validate_p3_groups(items):
    groups = {}
    for item in items:
        if item["partition"] != "p3":
            continue
        groups.setdefault(item["paraphrase_group"], []).append(item)
    for gid, members in groups.items():
        if len(members) != 2:
            _fail("paraphrase_group {!r} must have exactly 2 rewordings (has {})".format(
                gid, len(members)))
        keys = {str(m["options"][m["correct_index"]]) for m in members}
        refs = {m["base_ref"] for m in members}
        if len(keys) != 1:
            _fail("paraphrase_group {!r} rewordings have different keys {}".format(gid, keys))
        if len(refs) != 1:
            _fail("paraphrase_group {!r} rewordings have different base_ref {}".format(gid, refs))


def load_eval_items(path=ITEMS_YAML, partition=None):
    """Load + validate the frozen eval bank; optionally filter by partition."""
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    raw = data["items"] if isinstance(data, dict) else (data or [])
    for index, item in enumerate(raw):
        _validate_item(index, item)
    _validate_p3_groups(raw)
    if partition is not None:
        if partition not in PARTITIONS:
            _fail("unknown partition filter {!r}".format(partition))
        return [i for i in raw if i["partition"] == partition]
    return list(raw)


def summarize(items):
    """Return counts by partition / bucket / difficulty + paraphrase-group count."""
    by_partition, by_bucket, by_difficulty = {}, {}, {}
    groups = set()
    for item in items:
        by_partition[item["partition"]] = by_partition.get(item["partition"], 0) + 1
        bucket = taxonomy.bucket_of(item["leaf_tag"])
        by_bucket[bucket] = by_bucket.get(bucket, 0) + 1
        d = item["difficulty"]
        by_difficulty[d] = by_difficulty.get(d, 0) + 1
        if item["partition"] == "p3":
            groups.add(item["paraphrase_group"])
    total = len(items)
    calc = by_bucket.get(taxonomy.CALCULUS_BUCKET, 0)
    return {
        "total": total,
        "by_partition": by_partition,
        "by_bucket": by_bucket,
        "by_difficulty": by_difficulty,
        "paraphrase_groups": len(groups),
        "calc_weight": (calc / total) if total else 0.0,
    }


def _normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def assert_firewall(items=None, seed=42):
    """Raise if any eval item's (stem, answer) collides with a study-deck card."""
    if items is None:
        items = load_eval_items()
    from build_deck import load_all_cards  # lazy: pipeline is a code dep

    study = set()
    for card in load_all_cards(seed=seed):
        if card.get("format") == "mcq":
            study.add((_normalize(card["question"]),
                       _normalize(card["options"][card["correct_index"]])))
        else:
            study.add((_normalize(card["front"]), _normalize(card["back"])))
    for item in items:
        key = (_normalize(item["question"]),
               _normalize(item["options"][item["correct_index"]]))
        if key in study:
            _fail("item {!r} collides with a study-deck card (firewall)".format(item["id"]))
