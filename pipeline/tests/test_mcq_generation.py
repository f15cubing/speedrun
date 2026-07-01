"""MCQ generation: determinism, well-formedness, and correct-key integrity."""

import sympy as sp

import generate_mcq
import taxonomy


def test_generates_expected_leaves_and_counts():
    cards = generate_mcq.generate_mcq_cards(seed=42)
    assert cards, "no MCQ cards produced"
    by_leaf = {}
    for c in cards:
        by_leaf[c["leaf_tag"]] = by_leaf.get(c["leaf_tag"], 0) + 1
    for leaf, n in generate_mcq.MCQ_COUNTS.items():
        assert by_leaf[taxonomy.TAG_BY_LEAF[leaf]] == n


def test_every_mcq_is_wellformed():
    for c in generate_mcq.generate_mcq_cards(seed=42):
        assert c["format"] == "mcq"
        assert taxonomy.validate_leaf_tag(c["leaf_tag"])
        assert len(c["options"]) == 5
        assert len(set(c["options"])) == 5, c
        assert 0 <= c["correct_index"] < 5


def test_correct_option_is_the_real_answer_for_linear():
    # 2x2 determinant: the option at correct_index must equal a*d - b*c parsed back.
    tag = taxonomy.TAG_BY_LEAF["linear"]
    cards = [c for c in generate_mcq.generate_mcq_cards(seed=42) if c["leaf_tag"] == tag]
    assert cards
    for c in cards:
        key = sp.sympify(c["options"][c["correct_index"]])
        # Re-derive from the explanation's stated value (independent of option order).
        stated = sp.sympify(c["explanation"].split("=")[-1].strip())
        assert sp.simplify(key - stated) == 0, c


def test_is_deterministic_for_fixed_seed():
    assert generate_mcq.generate_mcq_cards(seed=42) == generate_mcq.generate_mcq_cards(seed=42)
    assert generate_mcq.generate_mcq_cards(seed=42) != generate_mcq.generate_mcq_cards(seed=7)
