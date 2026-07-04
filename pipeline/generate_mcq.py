"""Seeded generator for exam-format MCQ cards (computational lane).

Reuses the pure problem-construction helpers from ``generate_deck`` and the
distractor engine to emit deterministic 5-option multiple-choice items for a
representative set of computational leaves. Each builder returns
``(stem, correct_expr, wrong_exprs, explanation)``; the correct answer and the
operation-specific wrong answers are all SymPy, so every option is computed (no
hand-typed answers, no model calls). Output is byte-stable for a fixed seed.

These cards drive the Performance surface (PRD §7b/§8a); they review through the
same FSRS loop as flashcards (no engine change).
"""

from __future__ import annotations

import sympy as sp

import distractors
import mathfmt
import taxonomy
from generate_deck import DEFAULT_SEED, _leaf_rng, _nonzero, _poly, x

# Cards per MCQ leaf. Two calculus + two algebra leaves keeps the merged deck's
# calculus weight comfortably >= 50% (see coverage_report).
MCQ_COUNTS = {
    "differential_single": 125,
    "integral_single": 125,
    "linear": 125,
    "number_theory": 125,
}


def _mcq_differential_single(rng):
    f = _poly(rng, x, 2, 4)
    correct = sp.diff(f, x)
    # Each wrong answer is paired with the named common error it embodies, so the
    # card can give elaborated feedback ("why that tempting option is wrong").
    wrongs = [
        (sp.integrate(f, x), "integrating instead of differentiating"),
        (sp.diff(sp.diff(f, x), x), "taking the second derivative instead of the first"),
    ]
    stem = "Differentiate with respect to x:\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
    explanation = mathfmt.inline("f'(x) = " + mathfmt.tex(correct))
    return stem, correct, wrongs, explanation


def _mcq_integral_single(rng):
    f = _poly(rng, x, 1, 3)
    correct = sp.integrate(f, x)         # antiderivative; options omit + C
    wrongs = [
        (sp.diff(f, x), "differentiating instead of integrating"),
        (f, "leaving the integrand unintegrated"),
    ]
    stem = (
        "Evaluate the indefinite integral (give the antiderivative, omit + C):"
        "\n\n" + mathfmt.inline("\\displaystyle\\int \\left(" + mathfmt.tex(f) + "\\right)\\,dx")
    )
    explanation = mathfmt.inline("F(x) = " + mathfmt.tex(correct) + " + C")
    return stem, correct, wrongs, explanation


def _mcq_linear(rng):
    a = _nonzero(rng, -6, 6)
    b = rng.randint(-6, 6)
    c = rng.randint(-6, 6)
    d = _nonzero(rng, -6, 6)
    correct = sp.Integer(a * d - b * c)
    wrongs = [
        (sp.Integer(a * d + b * c), "adding the diagonal products instead of subtracting"),
        (sp.Integer(a * b - c * d), "multiplying the wrong pairs of entries"),
    ]
    stem = "Compute the determinant of the matrix:\n\n" + mathfmt.expr_block(
        sp.Matrix([[a, b], [c, d]])
    )
    explanation = mathfmt.inline(
        "\\det = ({})({}) - ({})({}) = {}".format(
            mathfmt.tex(a), mathfmt.tex(d), mathfmt.tex(b), mathfmt.tex(c), mathfmt.tex(correct)
        )
    )
    return stem, correct, wrongs, explanation


def _mcq_number_theory(rng):
    a = rng.randint(12, 120)
    b = rng.randint(12, 120)
    g = sp.igcd(a, b)
    correct = sp.Integer(g)
    wrongs = [
        (sp.Integer(a * b // g), "computing the LCM instead of the GCD"),
        (sp.Integer(min(a, b)), "taking the smaller number instead of the GCD"),
    ]
    stem = "Compute the greatest common divisor:\n\n" + mathfmt.inline(
        "\\gcd({}, {})".format(a, b)
    )
    explanation = mathfmt.inline("\\gcd({}, {}) = {}".format(a, b, mathfmt.tex(correct)))
    return stem, correct, wrongs, explanation


def error_labels(correct, wrongs_labeled):
    """Labels for the named distractors that survive the option-assembly filter.

    Mirrors :func:`distractors.make_options`'s "distinct + != key" rule so we only
    surface an error whose distractor actually appears among the options.
    """
    seen = {sp.sstr(correct)}
    labels = []
    for expr, label in wrongs_labeled:
        if expr is None or distractors._equal(expr, correct):
            continue
        canon = sp.sstr(expr)
        if canon in seen:
            continue
        seen.add(canon)
        labels.append(label)
    return labels


def with_error_feedback(explanation, labels):
    """Append the elaborated 'common errors to avoid' feedback to an explanation."""
    if not labels:
        return explanation
    return explanation + "\n\nCommon errors to avoid: " + "; ".join(labels) + "."


_MCQ_BUILDERS = {
    "differential_single": _mcq_differential_single,
    "integral_single": _mcq_integral_single,
    "linear": _mcq_linear,
    "number_theory": _mcq_number_theory,
}

# Emit in canonical taxonomy order so the card list is stable.
_MCQ_LEAVES_IN_ORDER = tuple(
    leaf.leaf for leaf in taxonomy.LEAVES if leaf.leaf in MCQ_COUNTS
)


def generate_mcq_cards(seed=DEFAULT_SEED):
    """Return the ordered list of computational MCQ card dicts (deterministic)."""
    cards = []
    for leaf in _MCQ_LEAVES_IN_ORDER:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        builder = _MCQ_BUILDERS[leaf]
        count = MCQ_COUNTS[leaf]
        # Distinct RNG namespace from the flashcard generator (":mcq" suffix) so
        # adding MCQ never perturbs the existing flashcard determinism.
        rng = _leaf_rng(seed, tag + "::mcq")
        seen = set()
        attempts = 0
        max_attempts = max(400, count * 400)
        while len(seen) < count:
            attempts += 1
            if attempts > max_attempts:
                raise RuntimeError(
                    "could not generate {} MCQ cards for {}".format(count, leaf)
                )
            stem, correct, wrongs_labeled, explanation = builder(rng)
            if stem in seen:
                continue
            wrong_exprs = [expr for expr, _label in wrongs_labeled]
            try:
                options, correct_index = distractors.make_options(rng, correct, wrong_exprs)
            except distractors.InsufficientDistractors:
                continue
            # Elaborated feedback: name the common errors the (surviving) distractors
            # embody, so a wrong tap teaches *why* it was tempting (PRD §8a; test-
            # enhanced learning with explanatory feedback).
            explanation = with_error_feedback(
                explanation, error_labels(correct, wrongs_labeled)
            )
            cards.append(
                {
                    "leaf_tag": tag,
                    "format": "mcq",
                    "question": stem,
                    "options": options,
                    "correct_index": correct_index,
                    "explanation": explanation,
                    # Stable, rendering-independent note identity (per-leaf ordinal
                    # in the deterministic sequence) so re-rendering keeps the GUID.
                    "uid": "{}::mcq::{}".format(tag, len(seen)),
                    # Ground-truth key for the correctness test; never written to
                    # the note (mcq_note_for/_card_identity ignore extra keys).
                    "_correct_expr": correct,
                }
            )
            seen.add(stem)
    return cards


def _main():
    cards = generate_mcq_cards()
    print("generated {} MCQ cards".format(len(cards)))
    for card in cards[:2]:
        print("\n--- {} ---".format(card["leaf_tag"]))
        print(card["question"])
        for i, opt in enumerate(card["options"]):
            mark = " (correct)" if i == card["correct_index"] else ""
            print("  {}. {}{}".format("ABCDE"[i], opt, mark))


if __name__ == "__main__":
    _main()
