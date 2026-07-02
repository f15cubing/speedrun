"""Computational eval-item generation: determinism, well-formedness, correct key."""
import sympy as sp

import generate_eval
import loader
import taxonomy


def test_p0_items_are_wellformed_and_valid():
    items = generate_eval.gen_p0_items(seed=42)
    assert len(items) >= 12
    for it in items:
        assert it["partition"] == "p0"
        assert taxonomy.validate_leaf_tag(it["leaf_tag"])
        assert len(it["options"]) == 5 and len(set(it["options"])) == 5
        assert 0 <= it["correct_index"] < 5
        assert 1 <= it["difficulty"] <= 5


def test_p3_pairs_are_grouped_and_same_key():
    items = generate_eval.gen_p3_pairs(seed=42)
    groups = {}
    for it in items:
        assert it["partition"] == "p3"
        groups.setdefault(it["paraphrase_group"], []).append(it)
    assert groups
    for members in groups.values():
        assert len(members) == 2
        keys = {m["options"][m["correct_index"]] for m in members}
        assert len(keys) == 1  # same-key paraphrase


def test_generation_is_deterministic():
    assert generate_eval.gen_p0_items(seed=42) == generate_eval.gen_p0_items(seed=42)
    assert generate_eval.gen_p3_pairs(seed=42) == generate_eval.gen_p3_pairs(seed=42)


def test_generated_items_pass_the_loader(tmp_path):
    # Freeze then load: generated computational items must satisfy the validator.
    text = generate_eval.emit_yaml(
        generate_eval.gen_p0_items(seed=42) + generate_eval.gen_p3_pairs(seed=42)
    )
    p = tmp_path / "items.yaml"
    p.write_text(text, encoding="utf-8")
    items = loader.load_eval_items(path=str(p))
    assert len(items) == len(generate_eval.gen_p0_items(seed=42)) + len(
        generate_eval.gen_p3_pairs(seed=42)
    )
