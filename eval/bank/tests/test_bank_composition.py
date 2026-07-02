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


def test_firewall_holds():
    loader.assert_firewall()  # no overlap with the study deck
