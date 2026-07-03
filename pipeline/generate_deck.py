"""Seeded SymPy generator for the templatable GRE-Math leaves.

Produces parametrized *computational* drill cards for the leaves that templatize
cleanly. For every card SymPy is used to BOTH build the problem and compute the
answer, so the back is correct **by construction** (no hand-typed answers, no
model calls). Generation is fully deterministic: each leaf gets its own RNG
derived from ``(seed, leaf_tag)``, so the produced card list is byte-stable for a
given seed and independent of dict/iteration order.

All displayed math is **delimited LaTeX** (via :mod:`mathfmt`) so Anki's MathJax
typesets it on both desktop and Android. The *truth* of each card stays a SymPy
expression; LaTeX is only its rendering (see :mod:`mathfmt`).

Public interface
----------------
- ``GENERATED_COUNTS``  : leaf name -> number of cards generated.
- ``generate_cards(seed=42)`` : returns an ordered ``list`` of card dicts
  ``{"front", "back", "leaf_tag"}`` in canonical taxonomy/leaf order. Cards whose
  answer is re-checkable carry an extra ``"_expr"`` dict of ground-truth SymPy
  objects for the recomputation test; ``"_expr"`` is **never written to the note**.

Each generator returns ``(front, back, meta)`` where ``meta`` is a dict of
ground-truth SymPy objects (possibly empty) used only by tests.
"""

from __future__ import annotations

import hashlib
import random

import sympy as sp

import mathfmt
import taxonomy

# Symbols shared across generators. Using a fixed set keeps rendering stable.
x, y = sp.symbols("x y")
_C = sp.Symbol("C")

DEFAULT_SEED = 42

# Cards per templatable leaf. Calculus leaves dominate to keep the merged deck
# >=50% calculus by card count and reach ~5000 total unique cards.
GENERATED_COUNTS = {
    "differential_single": 700,
    "integral_single": 700,
    "differential_multi": 700,
    "integral_multi": 500,
    "differential_equations": 500,
    "applications": 500,
    "elementary": 250,
    "linear": 250,
    "number_theory": 250,
    "probability_stats": 250,
    "numerical": 250,
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _leaf_rng(seed, leaf_tag):
    """Deterministic, leaf-local RNG derived from ``(seed, leaf_tag)``."""
    digest = hashlib.sha256("{}:{}".format(seed, leaf_tag).encode("utf-8")).hexdigest()
    return random.Random(int(digest, 16))


def _nonzero(rng, lo, hi):
    while True:
        v = rng.randint(lo, hi)
        if v != 0:
            return v


def _poly(rng, var, min_deg=2, max_deg=4, lo=-5, hi=5):
    """Random polynomial in ``var`` with integer coefficients (leading != 0)."""
    deg = rng.randint(min_deg, max_deg)
    expr = sp.Integer(0)
    for power in range(deg, -1, -1):
        coeff = rng.randint(lo, hi)
        if power == deg and coeff == 0:
            coeff = rng.choice([-3, -2, 2, 3])
        expr += coeff * var ** power
    return sp.expand(expr)


# --------------------------------------------------------------------------- #
# calculus generators
# --------------------------------------------------------------------------- #
def _gen_differential_single(rng):
    kind = rng.choice(["poly", "poly", "trig", "exp", "polytrig"])
    if kind == "poly":
        f = _poly(rng, x, 2, 4)
    elif kind == "trig":
        a = _nonzero(rng, -4, 4)
        b = _nonzero(rng, -4, 4)
        k = rng.randint(2, 4)
        f = a * sp.sin(k * x) + b * sp.cos(k * x)
    elif kind == "exp":
        a = _nonzero(rng, -4, 4)
        k = rng.randint(2, 4)
        f = a * sp.exp(k * x) + _poly(rng, x, 1, 2)
    else:  # polytrig
        a = _nonzero(rng, -4, 4)
        k = rng.randint(2, 3)
        f = _poly(rng, x, 2, 3) + a * sp.sin(k * x)
    fp = sp.diff(f, x)
    front = "Differentiate with respect to x:\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
    back = mathfmt.inline("f'(x) = " + mathfmt.tex(fp))
    return front, back, {"f": f, "answer": fp}


def _gen_integral_single(rng):
    kind = rng.choice(["poly", "poly", "trig", "exp", "recip"])
    if kind == "poly":
        f = _poly(rng, x, 1, 4)
    elif kind == "trig":
        a = _nonzero(rng, -4, 4)
        k = rng.randint(2, 4)
        f = a * sp.sin(k * x) + _nonzero(rng, -4, 4) * sp.cos(k * x)
    elif kind == "exp":
        a = _nonzero(rng, -4, 4)
        k = rng.randint(2, 4)
        f = a * sp.exp(k * x)
    else:  # recip -> logarithm
        c = _nonzero(rng, 2, 6)
        f = sp.Integer(c) / x
    antideriv = sp.integrate(f, x)
    front = "Evaluate the indefinite integral:\n\n" + mathfmt.inline(
        "\\displaystyle\\int \\left(" + mathfmt.tex(f) + "\\right)\\,dx"
    )
    back = mathfmt.inline("F(x) = " + mathfmt.tex(antideriv) + " + C")
    return front, back, {"integrand": f, "antiderivative": antideriv}


def _gen_differential_multi(rng):
    a = _nonzero(rng, -4, 4)
    b = _nonzero(rng, -4, 4)
    c = rng.randint(-4, 4)
    d = rng.randint(-4, 4)
    powx = rng.randint(1, 3)
    powy = rng.randint(1, 3)
    f = sp.expand(a * x ** powx * y ** powy + b * x ** 2 + c * y ** 2 + d * x * y)
    which = rng.choice(["x", "y"])
    var = x if which == "x" else y
    deriv = sp.diff(f, var)
    front = (
        "Given " + mathfmt.inline("f(x, y) = " + mathfmt.tex(f))
        + "\n\ncompute the partial derivative "
        + mathfmt.inline("\\partial f/\\partial " + which) + "."
    )
    back = mathfmt.inline("\\partial f/\\partial " + which + " = " + mathfmt.tex(deriv))
    return front, back, {"f": f, "var": var, "answer": deriv}


def _gen_integral_multi(rng):
    c1 = _nonzero(rng, 1, 6)
    c2 = rng.randint(0, 5)
    c3 = rng.randint(0, 5)
    px = rng.randint(0, 3)
    py = rng.randint(0, 3)
    g = sp.expand(c1 * x ** px * y ** py + c2 * x + c3 * y)
    a = rng.randint(1, 4)
    b = rng.randint(1, 4)
    inner = sp.integrate(g, (x, 0, a))
    value = sp.integrate(inner, (y, 0, b))
    region = mathfmt.inline("R = [0, {}] \\times [0, {}]".format(a, b))
    integral = "\\iint_R " + mathfmt.tex(g) + "\\,dA"
    front = (
        "Evaluate the double integral over " + region + ":\n\n"
        + mathfmt.inline(integral)
    )
    back = mathfmt.inline(integral + " = " + mathfmt.tex(value))
    return front, back, {"g": g, "region": (a, b), "answer": value}


def _gen_differential_equations(rng):
    kind = rng.choice(["separable_poly", "separable_poly", "exponential", "trig", "power"])
    if kind == "exponential":
        k = _nonzero(rng, -9, 9)
        sol = _C * sp.exp(k * x)
        front = "Solve the differential equation (general solution):\n\n" + mathfmt.inline(
            "y'(x) = " + mathfmt.tex(k) + "\\,y(x)"
        )
        back = mathfmt.inline("y(x) = " + mathfmt.tex(sol))
        return front, back, {"answer": sol}
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
    sol = sp.integrate(f, x)
    front = "Solve the differential equation (general solution):\n\n" + mathfmt.inline(
        "y'(x) = " + mathfmt.tex(f)
    )
    back = mathfmt.inline("y(x) = " + mathfmt.tex(sol) + " + C")
    return front, back, {"rhs": f, "answer": sol}


def _gen_applications(rng):
    kind = rng.choice(["tangent_slope", "area", "average_value"])
    if kind == "tangent_slope":
        f = _poly(rng, x, 2, 4)
        a = rng.randint(-6, 6)
        slope = sp.diff(f, x).subs(x, a)
        front = (
            "Find the slope of the tangent line to\n\n"
            + mathfmt.inline("f(x) = " + mathfmt.tex(f))
            + "\n\nat " + mathfmt.inline("x = " + mathfmt.tex(a)) + "."
        )
        back = "slope = " + mathfmt.inline(
            "f'(" + mathfmt.tex(a) + ") = " + mathfmt.tex(slope)
        )
        return front, back, {"f": f, "at": a, "answer": slope}
    if kind == "area":
        c1 = rng.randint(1, 6); c2 = rng.randint(1, 6)
        f = sp.expand(c1 * x ** 2 + c2)
        a = rng.randint(0, 3); b = a + rng.randint(1, 4)
        area = sp.integrate(f, (x, a, b))
        front = (
            "Find the area under\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
            + "\n\nfrom " + mathfmt.inline("x = " + mathfmt.tex(a))
            + " to " + mathfmt.inline("x = " + mathfmt.tex(b)) + "."
        )
        back = "area = " + mathfmt.expr_inline(area)
        return front, back, {"f": f, "interval": (a, b), "answer": area}
    # average_value
    c1 = rng.randint(1, 6); c2 = rng.randint(-6, 6)
    f = sp.expand(c1 * x + c2)
    a = rng.randint(0, 3); b = a + rng.randint(1, 5)
    avg = sp.integrate(f, (x, a, b)) / (b - a)
    front = (
        "Find the average value of\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
        + "\n\non " + mathfmt.inline("[{}, {}]".format(a, b)) + "."
    )
    back = "average value = " + mathfmt.expr_inline(avg)
    return front, back, {"f": f, "interval": (a, b), "answer": avg}


# --------------------------------------------------------------------------- #
# algebra / additional generators
# --------------------------------------------------------------------------- #
def _gen_elementary(rng):
    kind = rng.choice(["linear_eq", "quadratic"])
    if kind == "linear_eq":
        a = _nonzero(rng, -6, 6)
        b = rng.randint(-9, 9)
        c = rng.randint(-9, 9)
        sol = sp.Rational(c - b, a)
        front = "Solve for x:\n\n" + mathfmt.expr_inline(sp.Eq(a * x + b, c))
        back = mathfmt.inline("x = " + mathfmt.tex(sol))
        return front, back, {"answer": sol}
    r1 = rng.randint(-6, 6)
    r2 = rng.randint(-6, 6)
    poly = sp.expand((x - r1) * (x - r2))
    roots = sorted({r1, r2})
    front = "Solve for x:\n\n" + mathfmt.expr_inline(sp.Eq(poly, 0))
    back = mathfmt.inline(
        "x = " + ", ".join(mathfmt.tex(sp.Integer(r)) for r in roots)
    )
    return front, back, {"roots": roots}


def _gen_linear(rng):
    kind = rng.choice(["det2", "det2", "det3"])
    if kind == "det3":
        mat = sp.Matrix(3, 3, lambda i, j: rng.randint(-4, 4))
        det = mat.det()
        front = "Compute the determinant of the matrix:\n\n" + mathfmt.expr_block(mat)
        back = mathfmt.inline("\\det = " + mathfmt.tex(det))
        return front, back, {"matrix": mat, "answer": det}
    a = rng.randint(-6, 6)
    b = rng.randint(-6, 6)
    c = rng.randint(-6, 6)
    d = rng.randint(-6, 6)
    mat = sp.Matrix([[a, b], [c, d]])
    det = a * d - b * c
    front = "Compute the determinant of the matrix:\n\n" + mathfmt.expr_block(mat)
    back = mathfmt.inline(
        "\\det = ({})({}) - ({})({}) = {}".format(
            mathfmt.tex(a), mathfmt.tex(d), mathfmt.tex(b), mathfmt.tex(c), mathfmt.tex(det)
        )
    )
    return front, back, {"matrix": mat, "answer": sp.Integer(det)}


def _gen_number_theory(rng):
    kind = rng.choice(["gcd", "mod", "divisors"])
    if kind == "gcd":
        a = rng.randint(12, 120)
        b = rng.randint(12, 120)
        g = sp.igcd(a, b)
        front = "Compute the greatest common divisor:\n\n" + mathfmt.inline(
            "\\gcd({}, {})".format(a, b)
        )
        back = mathfmt.inline("\\gcd({}, {}) = {}".format(a, b, g))
        return front, back, {"answer": sp.Integer(g)}
    if kind == "mod":
        a = rng.randint(20, 200)
        m = rng.randint(3, 12)
        front = "Compute the remainder:\n\n" + mathfmt.inline(
            "{} \\bmod {}".format(a, m)
        )
        back = mathfmt.inline("{} \\bmod {} = {}".format(a, m, a % m))
        return front, back, {"answer": sp.Integer(a % m)}
    n = rng.randint(12, 90)
    d = sp.divisor_count(n)
    front = "How many positive divisors does " + mathfmt.inline(str(n)) + " have?"
    back = mathfmt.inline("d({}) = {}".format(n, d))
    return front, back, {"answer": sp.Integer(d)}


def _gen_probability_stats(rng):
    kind = rng.choice(["choose", "mean", "prob"])
    if kind == "choose":
        n = rng.randint(5, 9)
        k = rng.randint(2, n - 1)
        val = sp.binomial(n, k)
        front = (
            "In how many ways can you choose " + mathfmt.inline(str(k)) + " items from "
            + mathfmt.inline(str(n)) + " (compute "
            + mathfmt.inline("\\binom{{{}}}{{{}}}".format(n, k)) + ")?"
        )
        back = mathfmt.inline("\\binom{{{}}}{{{}}} = {}".format(n, k, val))
        return front, back, {"answer": sp.Integer(val)}
    if kind == "mean":
        data = [rng.randint(1, 12) for _ in range(rng.randint(4, 6))]
        mean = sp.Rational(sum(data), len(data))
        front = "Compute the arithmetic mean of the data set:\n\n" + mathfmt.inline(
            "\\{" + ", ".join(str(v) for v in data) + "\\}"
        )
        back = "mean = " + mathfmt.expr_inline(mean) + " (\u2248 {:.4f})".format(float(mean))
        return front, back, {"answer": mean}
    total = rng.randint(6, 12)
    favorable = rng.randint(1, total - 1)
    p = sp.Rational(favorable, total)
    front = (
        "A bag holds {} equally likely outcomes; {} of them are favorable. "
        "What is the probability of a favorable outcome?".format(total, favorable)
    )
    back = "P = " + mathfmt.expr_inline(p) + " (\u2248 {:.4f})".format(float(p))
    return front, back, {"answer": p}


def _gen_numerical(rng):
    kind = rng.choice(["newton", "trapezoid"])
    if kind == "newton":
        # f(x) = x^2 - c so a real root exists; one Newton step from x0
        c = rng.randint(2, 30)
        x0 = rng.randint(2, 8)
        f = x ** 2 - c
        f0 = int(f.subs(x, x0))
        fp0 = int(sp.diff(f, x).subs(x, x0))
        x1 = sp.Rational(x0 * fp0 - f0, fp0)
        front = (
            "Perform one iteration of Newton's method for\n\n"
            + mathfmt.inline("f(x) = " + mathfmt.tex(f))
            + "\n\nstarting at " + mathfmt.inline("x_0 = " + mathfmt.tex(x0)) + ".  "
            + mathfmt.inline("x_1 = x_0 - f(x_0)/f'(x_0)")
        )
        back = "x_1 = " + mathfmt.expr_inline(x1) + " (\u2248 {:.4f})".format(float(x1))
        return front, back, {"answer": x1}
    # trapezoidal rule with n=2 on a polynomial; exact rational result
    f = _poly(rng, x, 1, 2, lo=0, hi=4)
    a = rng.randint(0, 2)
    b = a + 2
    mid = sp.Rational(a + b, 2)
    h = sp.Rational(b - a, 2)
    approx = sp.simplify(h * (f.subs(x, a) + 2 * f.subs(x, mid) + f.subs(x, b)) / 2)
    front = (
        "Approximate the integral of\n\n" + mathfmt.inline("f(x) = " + mathfmt.tex(f))
        + "\n\nfrom " + mathfmt.inline("x = " + mathfmt.tex(a))
        + " to " + mathfmt.inline("x = " + mathfmt.tex(b))
        + " using the trapezoidal rule with " + mathfmt.inline("n = 2") + " subintervals."
    )
    back = mathfmt.inline("T_2 = " + mathfmt.tex(approx))
    return front, back, {"answer": approx}


_GENERATORS = {
    "differential_single": _gen_differential_single,
    "integral_single": _gen_integral_single,
    "differential_multi": _gen_differential_multi,
    "integral_multi": _gen_integral_multi,
    "differential_equations": _gen_differential_equations,
    "applications": _gen_applications,
    "elementary": _gen_elementary,
    "linear": _gen_linear,
    "number_theory": _gen_number_theory,
    "probability_stats": _gen_probability_stats,
    "numerical": _gen_numerical,
}

# Generate in canonical taxonomy order (calculus first) for a stable card list.
_GENERATED_LEAVES_IN_ORDER = tuple(
    leaf.leaf for leaf in taxonomy.LEAVES if leaf.leaf in GENERATED_COUNTS
)


def generate_cards(seed=DEFAULT_SEED):
    """Return the ordered list of generated computational card dicts.

    Each card is ``{"front", "back", "leaf_tag"}`` (plus a test-only ``"_expr"``
    dict of ground-truth SymPy objects, never written to the note). Output is
    fully deterministic for a given ``seed``; duplicate fronts within a leaf are
    skipped so each leaf yields ``GENERATED_COUNTS[leaf]`` distinct cards.
    """
    cards = []
    for leaf in _GENERATED_LEAVES_IN_ORDER:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        count = GENERATED_COUNTS[leaf]
        generator = _GENERATORS[leaf]
        rng = _leaf_rng(seed, tag)
        seen = set()
        attempts = 0
        max_attempts = max(2000, count * 60)
        while len(seen) < count:
            attempts += 1
            if attempts > max_attempts:
                raise RuntimeError(
                    "could not generate {} unique cards for {}".format(count, leaf)
                )
            front, back, meta = generator(rng)
            if front in seen:
                continue
            seen.add(front)
            card = {"front": front, "back": back, "leaf_tag": tag}
            if meta:
                card["_expr"] = meta
            cards.append(card)
    return cards


def _main():
    cards = generate_cards()
    print("generated {} computational cards".format(len(cards)))
    for card in cards[:3]:
        print("\n--- {} ---".format(card["leaf_tag"]))
        print(card["front"])
        print("=>", card["back"])


if __name__ == "__main__":
    _main()
