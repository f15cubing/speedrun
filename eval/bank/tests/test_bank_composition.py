"""The committed eval bank meets composition + firewall targets."""
import loader


def test_committed_bank_loads_and_is_verified():
    items = loader.load_eval_items()
    assert all(i["status"] == "verified" for i in items)


def test_partition_targets():
    s = loader.summarize(loader.load_eval_items())
    assert s["by_partition"].get("p0", 0) >= 20
    assert s["by_partition"].get("p3", 0) >= 56
    # P3 rewordings come in groups of exactly 2:
    assert s["by_partition"]["p3"] == 2 * s["paraphrase_groups"]


def test_calc_weight_reasonable():
    s = loader.summarize(loader.load_eval_items())
    assert s["calc_weight"] >= 0.30  # calc well represented (P0+P3 combined)


def test_p0_supports_full_length_exam_blueprint():
    # p0 must hold >= 33 calc / 17 algebra / 16 additional so Exam Mode can build
    # the official 66-item 50/25/25 form (see anki/qt/aqt/gre/exam.py).
    b = loader.summarize(loader.load_eval_items(partition="p0"))["by_bucket"]
    assert b.get("calculus", 0) >= 33
    assert b.get("algebra", 0) >= 17
    assert b.get("additional", 0) >= 16


def test_firewall_holds():
    loader.assert_firewall()  # no overlap with the study deck
