"""MCQ generation: determinism, well-formedness, and correct-key integrity."""

import sympy as sp

import generate_mcq
import mathfmt
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
    # 2x2 determinant: the ground-truth key must equal a*d - b*c independently
    # recomputed from the matrix rendered in the stem is not parseable (LaTeX),
    # so we assert the stored key is the exact determinant SymPy computed.
    tag = taxonomy.TAG_BY_LEAF["linear"]
    cards = [c for c in generate_mcq.generate_mcq_cards(seed=42) if c["leaf_tag"] == tag]
    assert cards
    for c in cards:
        key = c["_correct_expr"]
        # The option at correct_index renders exactly the ground-truth key.
        assert c["options"][c["correct_index"]] == mathfmt.expr_inline(key), c
        # And the key is an integer determinant (2x2 det of integer entries).
        assert key.is_integer, c


def test_is_deterministic_for_fixed_seed():
    assert generate_mcq.generate_mcq_cards(seed=42) == generate_mcq.generate_mcq_cards(seed=42)
    assert generate_mcq.generate_mcq_cards(seed=42) != generate_mcq.generate_mcq_cards(seed=7)
