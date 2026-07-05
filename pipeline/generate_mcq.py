"""Seeded generator for exam-format MCQ cards (computational lane).

Reuses the pure problem-construction helpers from ``generate_deck`` and the
distractor engine to emit deterministic 5-option multiple-choice items for **all
11 computational leaves** (every leaf the flashcard generator templatizes). Each
builder returns ``(stem, correct_expr, wrong_exprs, explanation)``; the correct
answer and the operation-specific wrong answers are all SymPy, so every option is
computed (no hand-typed answers, no model calls). Output is byte-stable for a
fixed seed.

Each builder mirrors its flashcard counterpart's problem construction (recomputing
the correct answer with SymPy) and then adds operation-specific distractors, each
paired with the **named common error** it embodies for elaborated feedback.

These cards drive the Performance surface (PRD §7b/§8a); they review through the
same FSRS loop as flashcards (no engine change).
"""

from __future__ import annotations

import sympy as sp

import distractors
import mathfmt
import taxonomy
from generate_deck import DEFAULT_SEED, _C, _leaf_rng, _nonzero, _poly, x, y

# Cards per MCQ leaf. MCQ now spans **all 11 computational leaves** (mirroring the
# flashcard generator's coverage), raising MCQ to ~1/3 of the merged deck. The
# calculus-heavy counts keep the deck's calculus weight comfortably >= 50% (see
# coverage_report). Counts are **append-only per leaf**: raising a count only
# extends that leaf's deterministic RNG sequence, so the first N stems/uids -- and
# therefore existing MCQ GUIDs -- are unchanged.
MCQ_COUNTS = {
    # calculus
    "differential_single": 350,
    "integral_single": 350,
    "differential_multi": 350,
    "integral_multi": 250,
    "differential_equations": 250,
    "applications": 250,
    # algebra
    "elementary": 125,
    "linear": 125,
    "number_theory": 125,
    # additional
    "probability_stats": 125,
    "numerical": 125,
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


# --------------------------------------------------------------------------- #
# calculus builders (mirror generate_deck's problem construction)
# --------------------------------------------------------------------------- #
def _mcq_differential_multi(rng):
    # Partial derivative: same construction as generate_deck._gen_differential_multi.
    a = _nonzero(rng, -4, 4)
    b = _nonzero(rng, -4, 4)
    c = rng.randint(-4, 4)
    d = rng.randint(-4, 4)
    powx = rng.randint(1, 3)
    powy = rng.randint(1, 3)
    f = sp.expand(a * x ** powx * y ** powy + b * x ** 2 + c * y ** 2 + d * x * y)
    which = rng.choice(["x", "y"])
    var, other = (x, y) if which == "x" else (y, x)
    correct = sp.diff(f, var)
    # The tempting error is differentiating w.r.t. the other variable; the symbolic
    # answer means generic_variants top the options up to five.
    wrongs = [
        (sp.diff(f, other), "differentiated with respect to the wrong variable"),
    ]
    stem = (
        "Given " + mathfmt.inline("f(x, y) = " + mathfmt.tex(f))
        + "\n\ncompute the partial derivative "
        + mathfmt.inline("\\partial f/\\partial " + which) + "."
    )
    explanation = mathfmt.inline(
        "\\partial f/\\partial " + which + " = " + mathfmt.tex(correct)
    )
    return stem, correct, wrongs, explanation


def _mcq_integral_multi(rng):
    # Double-integral VALUE (a number): same construction as _gen_integral_multi.
    c1 = _nonzero(rng, 1, 6)
    c2 = rng.randint(0, 5)
    c3 = rng.randint(0, 5)
    px = rng.randint(0, 3)
    py = rng.randint(0, 3)
    g = sp.expand(c1 * x ** px * y ** py + c2 * x + c3 * y)
    a = rng.randint(1, 4)
    b = rng.randint(1, 4)
    correct = sp.integrate(sp.integrate(g, (x, 0, a)), (y, 0, b))
    # Numeric answer -> generic_variants suffice; one clean named error: integrating
    # over [0,b] x [0,a] (the limits of the two variables swapped).
    swapped = sp.integrate(sp.integrate(g, (x, 0, b)), (y, 0, a))
    wrongs = [(swapped, "swapped the two integration limits")]
    region = mathfmt.inline("R = [0, {}] \\times [0, {}]".format(a, b))
    integral = "\\iint_R " + mathfmt.tex(g) + "\\,dA"
    stem = (
        "Evaluate the double integral over " + region + ":\n\n"
        + mathfmt.inline(integral)
    )
    explanation = mathfmt.inline(integral + " = " + mathfmt.tex(correct))
    return stem, correct, wrongs, explanation


def _mcq_differential_equations(rng):
    # General solution: same families as _gen_differential_equations.
    kind = rng.choice(["separable_poly", "separable_poly", "exponential", "trig", "power"])
    if kind == "exponential":
        # y' = k y  ->  y = C e^{kx}. The arbitrary constant C makes generic_variants
        # unsafe (-C, 2C, ... are the SAME solution family), so supply four genuinely
        # wrong named distractors and never fall through to the generic top-up.
        k = _nonzero(rng, -9, 9)
        correct = _C * sp.exp(k * x)
        wrongs = [
            (_C * sp.exp(-k * x), "sign error in the exponent"),
            (sp.exp(k * x), "dropped the arbitrary constant C"),
            (_C + sp.exp(k * x), "added the constant instead of multiplying it"),
            (_C * x * sp.exp(k * x), "introduced a spurious factor of x"),
        ]
        stem = "Solve the differential equation (general solution):\n\n" + mathfmt.inline(
            "y'(x) = " + mathfmt.tex(k) + "\\,y(x)"
        )
        explanation = mathfmt.inline("y(x) = " + mathfmt.tex(correct))
        return stem, correct, wrongs, explanation
    if kind == "separable_poly":
        f = _poly(rng, x, 1, 4)
    elif kind == "trig":
        a = _nonzero(rng, -6, 6)
        k = rng.randint(2, 6)
        f = a * sp.sin(k * x)
    else:  # power
        n = rng.randint(2, 7)
        a = _nonzero(rng, -6, 6)
        f = a * x ** n
    # y' = f(x)  ->  y = antiderivative (+ C). Options omit the arbitrary constant
    # (so generic_variants stay valid, distinct wrong functions).
    correct = sp.integrate(f, x)
    wrongs = [
        (sp.diff(f, x), "differentiated instead of integrating"),
        (f, "left the right-hand side unintegrated"),
    ]
    stem = (
        "Solve the differential equation (give y(x); omit the arbitrary + C):\n\n"
        + mathfmt.inline("y'(x) = " + mathfmt.tex(f))
    )
    explanation = mathfmt.inline("y(x) = " + mathfmt.tex(correct) + " + C")
    return stem, correct, wrongs, explanation


def _mcq_applications(rng):
    # Branch exactly like _gen_applications.
    kind = rng.choice(["tangent_slope", "area", "average_value"])
    if kind == "tangent_slope":
        f = _poly(rng, x, 2, 4)
        a = rng.randint(-6, 6)
        correct = sp.diff(f, x).subs(x, a)
        wrongs = [(f.subs(x, a), "used f(a) instead of f'(a)")]
        stem = (
            "Find the slope of the tangent line to\n\n"
            + mathfmt.inline("f(x) = " + mathfmt.tex(f))
            + "\n\nat " + mathfmt.inline("x = " + mathfmt.tex(a)) + "."
        )
        explanation = "slope = " + mathfmt.inline(
            "f'(" + mathfmt.tex(a) + ") = " + mathfmt.tex(correct)
        )
        return stem, correct, wrongs, explanation
    if kind == "area":
        c1 = rng.randint(1, 6)
        c2 = rng.randint(1, 6)
        f = sp.expand(c1 * x ** 2 + c2)
        a = rng.randint(0, 3)
        b = a + rng.randint(1, 4)
        correct = sp.integrate(f, (x, a, b))
        antideriv = sp.integrate(f, x)
        wrongs = [
            (antideriv.subs(x, b), "evaluated the antiderivative only at the upper limit"),
            (f.subs(x, b) - f.subs(x, a), "subtracted function values instead of integrating"),
        ]
        stem = (
            "Find the area under\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
            + "\n\nfrom " + mathfmt.inline("x = " + mathfmt.tex(a))
            + " to " + mathfmt.inline("x = " + mathfmt.tex(b)) + "."
        )
        explanation = "area = " + mathfmt.expr_inline(correct)
        return stem, correct, wrongs, explanation
    # average_value
    c1 = rng.randint(1, 6)
    c2 = rng.randint(-6, 6)
    f = sp.expand(c1 * x + c2)
    a = rng.randint(0, 3)
    b = a + rng.randint(1, 5)
    integral = sp.integrate(f, (x, a, b))
    correct = integral / (b - a)
    wrongs = [(integral, "forgot to divide by the interval length")]
    stem = (
        "Find the average value of\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
        + "\n\non " + mathfmt.inline("[{}, {}]".format(a, b)) + "."
    )
    explanation = "average value = " + mathfmt.expr_inline(correct)
    return stem, correct, wrongs, explanation


# --------------------------------------------------------------------------- #
# algebra / additional builders
# --------------------------------------------------------------------------- #
def _mcq_elementary(rng):
    # Only solve-for-x linear equations, so the answer is a single scalar (no
    # set-valued quadratic roots). a*x + b = c  ->  x = (c - b)/a.
    a = _nonzero(rng, -6, 6)
    b = rng.randint(-9, 9)
    c = rng.randint(-9, 9)
    correct = sp.Rational(c - b, a)
    wrongs = [(sp.Rational(b - c, a), "sign error isolating x")]
    stem = "Solve for x:\n\n" + mathfmt.expr_inline(sp.Eq(a * x + b, c))
    explanation = mathfmt.inline("x = " + mathfmt.tex(correct))
    return stem, correct, wrongs, explanation


def _mcq_probability_stats(rng):
    # Branch exactly like _gen_probability_stats.
    kind = rng.choice(["choose", "mean", "prob"])
    if kind == "choose":
        n = rng.randint(5, 9)
        k = rng.randint(2, n - 1)
        correct = sp.binomial(n, k)
        wrongs = [(sp.ff(n, k), "computed a permutation instead of a combination")]
        stem = (
            "In how many ways can you choose " + mathfmt.inline(str(k)) + " items from "
            + mathfmt.inline(str(n)) + " (compute "
            + mathfmt.inline("\\binom{{{}}}{{{}}}".format(n, k)) + ")?"
        )
        explanation = mathfmt.inline(
            "\\binom{{{}}}{{{}}} = {}".format(n, k, mathfmt.tex(correct))
        )
        return stem, correct, wrongs, explanation
    if kind == "mean":
        data = [rng.randint(1, 12) for _ in range(rng.randint(4, 6))]
        total = sum(data)
        correct = sp.Rational(total, len(data))
        wrongs = [(sp.Integer(total), "reported the sum instead of the mean")]
        stem = "Compute the arithmetic mean of the data set:\n\n" + mathfmt.inline(
            "\\{" + ", ".join(str(v) for v in data) + "\\}"
        )
        explanation = "mean = " + mathfmt.expr_inline(correct)
        return stem, correct, wrongs, explanation
    total = rng.randint(6, 12)
    favorable = rng.randint(1, total - 1)
    correct = sp.Rational(favorable, total)
    wrongs = [
        (sp.Rational(total - favorable, total), "gave the complement"),
        (sp.Rational(favorable, total - favorable), "used odds instead of probability"),
    ]
    stem = (
        "A bag holds {} equally likely outcomes; {} of them are favorable. "
        "What is the probability of a favorable outcome?".format(total, favorable)
    )
    explanation = "P = " + mathfmt.expr_inline(correct)
    return stem, correct, wrongs, explanation


def _mcq_numerical(rng):
    # Branch exactly like _gen_numerical.
    kind = rng.choice(["newton", "trapezoid"])
    if kind == "newton":
        c = rng.randint(2, 30)
        x0 = rng.randint(2, 8)
        f = x ** 2 - c
        f0 = int(f.subs(x, x0))
        fp0 = int(sp.diff(f, x).subs(x, x0))
        correct = sp.Rational(x0 * fp0 - f0, fp0)
        wrongs = [
            (sp.Integer(x0 - f0), "forgot to divide by f'(x0)"),
            (sp.Rational(x0 * fp0 + f0, fp0), "wrong sign in the update"),
        ]
        stem = (
            "Perform one iteration of Newton's method for\n\n"
            + mathfmt.inline("f(x) = " + mathfmt.tex(f))
            + "\n\nstarting at " + mathfmt.inline("x_0 = " + mathfmt.tex(x0)) + ".  "
            + mathfmt.inline("x_1 = x_0 - f(x_0)/f'(x_0)")
        )
        explanation = mathfmt.inline("x_1 = " + mathfmt.tex(correct))
        return stem, correct, wrongs, explanation
    # trapezoidal rule (n=2): numeric answer, generic_variants suffice.
    f = _poly(rng, x, 1, 2, lo=0, hi=4)
    a = rng.randint(0, 2)
    b = a + 2
    mid = sp.Rational(a + b, 2)
    h = sp.Rational(b - a, 2)
    correct = sp.simplify(h * (f.subs(x, a) + 2 * f.subs(x, mid) + f.subs(x, b)) / 2)
    wrongs = []
    stem = (
        "Approximate the integral of\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
        + "\n\nfrom " + mathfmt.inline("x = " + mathfmt.tex(a))
        + " to " + mathfmt.inline("x = " + mathfmt.tex(b))
        + " using the trapezoidal rule with " + mathfmt.inline("n = 2") + " subintervals."
    )
    explanation = mathfmt.inline("T_2 = " + mathfmt.tex(correct))
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
    # calculus
    "differential_single": _mcq_differential_single,
    "integral_single": _mcq_integral_single,
    "differential_multi": _mcq_differential_multi,
    "integral_multi": _mcq_integral_multi,
    "differential_equations": _mcq_differential_equations,
    "applications": _mcq_applications,
    # algebra
    "elementary": _mcq_elementary,
    "linear": _mcq_linear,
    "number_theory": _mcq_number_theory,
    # additional
    "probability_stats": _mcq_probability_stats,
    "numerical": _mcq_numerical,
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
