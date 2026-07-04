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


# --- elaborated-feedback distractor rationales (PRD §8a) ---


def test_error_labels_filters_like_make_options():
    correct = sp.Integer(4)
    labeled = [
        (sp.Integer(5), "a"),        # kept
        (sp.Integer(4), "dup-key"),  # == correct -> dropped
        (sp.Integer(5), "dup"),      # duplicate expr -> dropped
        (None, "none"),              # None -> dropped
        (sp.Integer(6), "b"),        # kept
    ]
    assert generate_mcq.error_labels(correct, labeled) == ["a", "b"]


def test_with_error_feedback_appends_and_noops():
    assert generate_mcq.with_error_feedback("ans", []) == "ans"
    assert generate_mcq.with_error_feedback("ans", ["x", "y"]) == (
        "ans\n\nCommon errors to avoid: x; y."
    )


def test_each_computational_leaf_has_named_error_feedback():
    expected = {
        "differential_single": [
            "integrating instead of differentiating",
            "taking the second derivative instead of the first",
        ],
        "integral_single": [
            "differentiating instead of integrating",
            "leaving the integrand unintegrated",
        ],
        "linear": [
            "adding the diagonal products instead of subtracting",
            "multiplying the wrong pairs of entries",
        ],
        "number_theory": [
            "computing the LCM instead of the GCD",
            "taking the smaller number instead of the GCD",
        ],
    }
    by_leaf = {}
    for c in generate_mcq.generate_mcq_cards(seed=42):
        by_leaf.setdefault(c["leaf_tag"], []).append(c)
    for leaf, labels in expected.items():
        sample = by_leaf[taxonomy.TAG_BY_LEAF[leaf]][0]
        assert "Common errors to avoid:" in sample["explanation"], sample
        for label in labels:
            assert label in sample["explanation"], (leaf, label)
    # the correct working (original explanation) is still present
    lin = by_leaf[taxonomy.TAG_BY_LEAF["linear"]][0]
    assert "\\det" in lin["explanation"]
