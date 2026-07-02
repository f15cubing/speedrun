"""Schema, verification gate, and P3 integrity for the eval-bank loader."""
import textwrap

import pytest

import loader


def _write(tmp_path, body):
    p = tmp_path / "items.yaml"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return str(p)


_GOOD_P0 = """
items:
  - id: "eval-p0-0001"
    leaf_tag: "topic::calculus::integral_single"
    format: mcq
    question: "Antiderivative of 6x + 4 (omit + C)?"
    options: ["3*x**2 + 4*x", "6", "3*x**2 + 4", "6*x**2 + 4*x", "3*x + 4"]
    correct_index: 0
    explanation: "3x^2 + 4x"
    difficulty: 2
    partition: p0
    paraphrase_group: null
    base_ref: null
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
"""


def test_loads_valid_p0(tmp_path):
    items = loader.load_eval_items(path=_write(tmp_path, _GOOD_P0))
    assert len(items) == 1
    assert items[0]["partition"] == "p0"


def test_draft_is_rejected(tmp_path):
    body = _GOOD_P0.replace("status: verified", "status: draft")
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_verified_without_attribution_rejected(tmp_path):
    body = _GOOD_P0.replace('verified_by: "fc"', 'verified_by: ""')
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_bad_difficulty_rejected(tmp_path):
    body = _GOOD_P0.replace("difficulty: 2", "difficulty: 9")
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_bad_partition_rejected(tmp_path):
    body = _GOOD_P0.replace("partition: p0", "partition: pX")
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_malformed_mcq_rejected(tmp_path):
    # only 4 options
    body = _GOOD_P0.replace(
        '["3*x**2 + 4*x", "6", "3*x**2 + 4", "6*x**2 + 4*x", "3*x + 4"]',
        '["3*x**2 + 4*x", "6", "3*x**2 + 4", "6*x**2 + 4*x"]',
    )
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


_P3_GROUP = """
items:
  - id: "eval-p3-pg1-r1"
    leaf_tag: "topic::algebra::linear"
    format: mcq
    question: "Wording one?"
    options: ["7", "1", "2", "3", "4"]
    correct_index: 0
    explanation: "7"
    difficulty: 3
    partition: p3
    paraphrase_group: "pg-1"
    base_ref: "topic::algebra::linear :: det of [[3,1],[2,3]]"
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
  - id: "eval-p3-pg1-r2"
    leaf_tag: "topic::algebra::linear"
    format: mcq
    question: "Wording two?"
    options: ["7", "5", "6", "8", "9"]
    correct_index: 0
    explanation: "7"
    difficulty: 3
    partition: p3
    paraphrase_group: "pg-1"
    base_ref: "topic::algebra::linear :: det of [[3,1],[2,3]]"
    src: "original"
    gen: human
    status: verified
    verified_by: "fc"
    verified_on: "2026-07-02"
"""


def test_valid_p3_group_loads(tmp_path):
    items = loader.load_eval_items(path=_write(tmp_path, _P3_GROUP))
    assert len(items) == 2


def test_p3_group_needs_exactly_two_rewordings(tmp_path):
    # drop the second rewording -> group of 1
    body = _P3_GROUP.split("  - id: \"eval-p3-pg1-r2\"")[0]
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_p3_group_key_mismatch_rejected(tmp_path):
    # second rewording's correct option (index 0) is "70" not "7"
    body = _P3_GROUP.replace('["7", "5", "6", "8", "9"]', '["70", "5", "6", "8", "9"]')
    with pytest.raises(ValueError):
        loader.load_eval_items(path=_write(tmp_path, body))


def test_partition_filter(tmp_path):
    items = loader.load_eval_items(path=_write(tmp_path, _P3_GROUP), partition="p0")
    assert items == []
