"""MCQ generation: determinism, well-formedness, and correct-key integrity.

Read-only tests share the session-scoped ``mcq_cards`` fixture (one build); the
determinism test builds fresh on purpose.
"""

import sympy as sp

import generate_mcq
import mathfmt
import taxonomy


def _by_leaf(cards):
    out = {}
    for c in cards:
        out.setdefault(c["leaf_tag"], []).append(c)
    return out


def test_generates_expected_leaves_and_counts(mcq_cards):
    assert mcq_cards, "no MCQ cards produced"
    by_leaf = {}
    for c in mcq_cards:
        by_leaf[c["leaf_tag"]] = by_leaf.get(c["leaf_tag"], 0) + 1
    for leaf, n in generate_mcq.MCQ_COUNTS.items():
        assert by_leaf[taxonomy.TAG_BY_LEAF[leaf]] == n


def test_mcq_now_spans_all_eleven_computational_leaves(mcq_cards):
    # MCQ used to cover only 4 leaves; it now mirrors the flashcard generator's
    # 11 computational leaves. Every leaf the flashcard generator templatizes has MCQ.
    import generate_deck

    covered = {c["leaf_tag"] for c in mcq_cards}
    for leaf in generate_mcq.MCQ_COUNTS:
        assert taxonomy.TAG_BY_LEAF[leaf] in covered
    assert set(generate_mcq.MCQ_COUNTS) == set(generate_deck.GENERATED_COUNTS)
    assert len(generate_mcq.MCQ_COUNTS) == 11
    assert sum(generate_mcq.MCQ_COUNTS.values()) == 2425


def test_every_mcq_is_wellformed(mcq_cards):
    for c in mcq_cards:
        assert c["format"] == "mcq"
        assert taxonomy.validate_leaf_tag(c["leaf_tag"])
        assert len(c["options"]) == 5
        assert len(set(c["options"])) == 5, c
        assert 0 <= c["correct_index"] < 5


def test_correct_option_is_the_ground_truth_key_for_every_leaf(mcq_cards):
    # The option at correct_index must render exactly the SymPy ground-truth key —
    # for ALL 11 leaves, not just the determinant leaf. This is the
    # "correct-by-construction, distractors provably != key" guarantee.
    for c in mcq_cards:
        key = c["_correct_expr"]
        assert c["options"][c["correct_index"]] == mathfmt.expr_inline(key), c


def test_correct_option_is_the_real_answer_for_linear(mcq_cards):
    tag = taxonomy.TAG_BY_LEAF["linear"]
    cards = [c for c in mcq_cards if c["leaf_tag"] == tag]
    assert cards
    for c in cards:
        key = c["_correct_expr"]
        assert c["options"][c["correct_index"]] == mathfmt.expr_inline(key), c
        assert key.is_integer, c


def test_elementary_answers_are_single_scalars(mcq_cards):
    # elementary emits ONLY solve-for-x linear equations, so each key is a single
    # rational scalar (never a set-valued quadratic root pair).
    tag = taxonomy.TAG_BY_LEAF["elementary"]
    cards = [c for c in mcq_cards if c["leaf_tag"] == tag]
    assert cards
    for c in cards:
        assert c["_correct_expr"].is_rational, c
        assert "Solve for x" in c["question"]


def test_is_deterministic_for_fixed_seed(mcq_cards):
    # Build fresh and compare to the once-built session fixture (independent
    # invocations) — a genuine determinism check — plus seed-sensitivity.
    assert generate_mcq.generate_mcq_cards(seed=42) == mcq_cards
    assert generate_mcq.generate_mcq_cards(seed=7) != mcq_cards


def test_raising_a_leaf_count_is_append_only(monkeypatch):
    # The per-leaf RNG namespace + dedup loop is APPEND-ONLY: raising a leaf's
    # MCQ_COUNTS extends its deterministic sequence, keeping the first N stems/uids
    # (hence note GUIDs) identical. This is why bumping differential_single/
    # integral_single from 125 -> 350 does not perturb any existing MCQ note.
    tag = taxonomy.TAG_BY_LEAF["differential_single"]

    def leaf_cards(count):
        monkeypatch.setitem(generate_mcq.MCQ_COUNTS, "differential_single", count)
        monkeypatch.setattr(generate_mcq, "_MCQ_LEAVES_IN_ORDER", ("differential_single",))
        return generate_mcq.generate_mcq_cards(seed=42)

    small = leaf_cards(50)
    big = leaf_cards(350)
    assert len(small) == 50 and len(big) == 350

    def ident(c):
        return (c["uid"], c["question"], tuple(c["options"]), c["correct_index"])

    assert [ident(c) for c in small] == [ident(c) for c in big[:50]]
    # uids are the append-only per-leaf ordinals 0..N-1.
    assert [c["uid"] for c in big] == ["{}::mcq::{}".format(tag, i) for i in range(350)]


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


def test_each_original_leaf_has_named_error_feedback(mcq_cards):
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
    by_leaf = _by_leaf(mcq_cards)
    for leaf, labels in expected.items():
        sample = by_leaf[taxonomy.TAG_BY_LEAF[leaf]][0]
        assert "Common errors to avoid:" in sample["explanation"], sample
        for label in labels:
            assert label in sample["explanation"], (leaf, label)
    lin = by_leaf[taxonomy.TAG_BY_LEAF["linear"]][0]
    assert "\\det" in lin["explanation"]


def test_new_leaves_expose_named_errors(mcq_cards):
    # Branchy leaves draw a kind per card, so a given named error appears in *some*
    # card of the leaf (not necessarily the first). Assert coverage across the leaf.
    expected = {
        "differential_multi": [
            "differentiated with respect to the wrong variable",
        ],
        "integral_multi": [
            "swapped the two integration limits",
        ],
        "differential_equations": [
            "differentiated instead of integrating",
            "left the right-hand side unintegrated",
            "sign error in the exponent",
            "dropped the arbitrary constant C",
        ],
        "applications": [
            "used f(a) instead of f'(a)",
            "evaluated the antiderivative only at the upper limit",
            "subtracted function values instead of integrating",
            "forgot to divide by the interval length",
        ],
        "elementary": [
            "sign error isolating x",
        ],
        "probability_stats": [
            "computed a permutation instead of a combination",
            "reported the sum instead of the mean",
            "gave the complement",
            "used odds instead of probability",
        ],
        "numerical": [
            "forgot to divide by f'(x0)",
            "wrong sign in the update",
        ],
    }
    by_leaf = _by_leaf(mcq_cards)
    for leaf, labels in expected.items():
        blob = "\n".join(c["explanation"] for c in by_leaf[taxonomy.TAG_BY_LEAF[leaf]])
        for label in labels:
            assert label in blob, (leaf, label)
