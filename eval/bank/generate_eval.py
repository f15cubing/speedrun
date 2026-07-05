"""Deterministic SymPy generators for computational eval items (P0 + P3 pairs).

Reuses pipeline/distractors + generate_deck helpers so keys and distractors are
correct-by-construction. Output is meant to be FROZEN into eval/bank/items.yaml
(the committed corpus is the source of truth; this module is the authoring aid).

All displayed math is delimited LaTeX (via pipeline/mathfmt) so the exam webview
and any regenerated bank typeset correctly. Design note: _det_problem returns the
raw SymPy problem alongside the stem so P3 framings can be assembled directly from
it — no brittle text extraction, and no str.format on LaTeX (whose braces would
collide with format fields).
"""
from __future__ import annotations

import sympy as sp
import yaml

import distractors
import mathfmt
import taxonomy
from generate_deck import _leaf_rng, _nonzero, x

_ATTR = {
    "src": "original",
    "gen": "human",
    "status": "verified",
    "verified_by": "fc",
    "verified_on": "2026-07-02",
}


def _record(rec_id, leaf_tag, question, options, correct_index, explanation,
            difficulty, partition, paraphrase_group=None, base_ref=None):
    rec = {
        "id": rec_id,
        "leaf_tag": leaf_tag,
        "format": "mcq",
        "question": question,
        "options": options,
        "correct_index": correct_index,
        "explanation": explanation,
        "difficulty": difficulty,
        "partition": partition,
        "paraphrase_group": paraphrase_group,
        "base_ref": base_ref,
    }
    rec.update(_ATTR)
    return rec


# P0 held-out: (leaf, difficulty, count). Calculus-weighted so calc share >= 50%.
_P0_SPEC = [
    ("integral_single", 2, 4),
    ("differential_single", 2, 4),
    ("linear", 3, 2),
    ("number_theory", 3, 2),
]


def _det_problem(leaf, rng):
    """Return (question, correct_expr, wrong_exprs, explanation, params).

    ``params`` carries the raw SymPy problem so callers can format alternative
    surface framings (P3) without parsing the question string.
    """
    if leaf == "integral_single":
        a = _nonzero(rng, 2, 6)
        b = _nonzero(rng, 1, 6)
        f = a * x + b
        correct = sp.integrate(f, x)
        return (
            "Give the antiderivative (omit + C):  "
            + mathfmt.inline("\\int \\left(" + mathfmt.tex(f) + "\\right)\\,dx"),
            correct,
            [sp.diff(f, x), f],
            mathfmt.inline("F(x) = " + mathfmt.tex(correct) + " + C"),
            {"f_expr": f},
        )
    if leaf == "differential_single":
        a = _nonzero(rng, 2, 6)
        n = rng.randint(2, 4)
        f = a * x**n
        correct = sp.diff(f, x)
        return (
            "Differentiate:  " + mathfmt.inline("f(x) = " + mathfmt.tex(f)),
            correct,
            [sp.integrate(f, x), sp.diff(correct, x)],
            mathfmt.inline("f'(x) = " + mathfmt.tex(correct)),
            {"f_expr": f},
        )
    if leaf == "linear":
        a = _nonzero(rng, -6, 6)
        b = rng.randint(-6, 6)
        c = rng.randint(-6, 6)
        d = _nonzero(rng, -6, 6)
        correct = sp.Integer(a * d - b * c)
        mat = sp.Matrix([[a, b], [c, d]])
        return (
            "Determinant of " + mathfmt.expr_inline(mat) + "?",
            correct,
            [sp.Integer(a * d + b * c), sp.Integer(a * b - c * d)],
            mathfmt.inline("\\det = " + mathfmt.tex(correct)),
            {"mat": mat},
        )
    if leaf == "number_theory":
        a = rng.randint(12, 90)
        b = rng.randint(12, 90)
        g = sp.igcd(a, b)
        return (
            "Compute " + mathfmt.inline("\\gcd({}, {})".format(a, b)) + ".",
            sp.Integer(g),
            [sp.Integer(a * b // g), sp.Integer(min(a, b))],
            mathfmt.inline("\\gcd = " + mathfmt.tex(sp.Integer(g))),
            {"a": a, "b": b},
        )
    raise ValueError("no generator for leaf " + leaf)


def gen_p0_items(seed=42):
    items = []
    n = 0
    for leaf, difficulty, count in _P0_SPEC:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        rng = _leaf_rng(seed, tag + "::eval::p0")
        seen = set()
        generated = 0
        while generated < count:
            q, correct, wrongs, expl, _params = _det_problem(leaf, rng)
            if q in seen:
                continue
            try:
                options, ci = distractors.make_options(rng, correct, wrongs)
            except distractors.InsufficientDistractors:
                continue
            seen.add(q)
            n += 1
            generated += 1
            items.append(_record(
                "eval-p0-{:04d}".format(n), tag, q, options, ci,
                expl, difficulty, "p0",
            ))
    return items


# P3 reword pairs: (leaf, difficulty, n_groups). Each group = 2 same-key rewordings.
_P3_SPEC = [
    ("integral_single", 2, 3),
    ("differential_single", 2, 3),
    ("linear", 3, 2),
]

# Two surface framings per leaf that keep the SAME instance/key (true paraphrase).
# Frames are functions (not str.format templates) because the stems contain LaTeX
# braces, which str.format would misinterpret.
_P3_FRAMES = {
    "integral_single": [
        lambda p: "Find the antiderivative (omit + C):  "
        + mathfmt.inline("\\int \\left(" + mathfmt.tex(p["f_expr"]) + "\\right)\\,dx"),
        lambda p: "A velocity is "
        + mathfmt.inline("v(t) = " + mathfmt.tex(p["f_expr"]))
        + ". Which is a position function " + mathfmt.inline("s(t)")
        + " (up to a constant)?",
    ],
    "differential_single": [
        lambda p: "Differentiate:  " + mathfmt.inline("f(x) = " + mathfmt.tex(p["f_expr"])),
        lambda p: "Find the slope function " + mathfmt.inline("f'(x)")
        + " for " + mathfmt.inline("f(x) = " + mathfmt.tex(p["f_expr"])) + ".",
    ],
    "linear": [
        lambda p: "Determinant of " + mathfmt.expr_inline(p["mat"]) + "?",
        lambda p: "For " + mathfmt.inline("M = " + mathfmt.tex(p["mat"]))
        + ", compute " + mathfmt.inline("\\det(M)") + ".",
    ],
}


def gen_p3_pairs(seed=42):
    items = []
    gi = 0
    for leaf, difficulty, n_groups in _P3_SPEC:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        rng = _leaf_rng(seed, tag + "::eval::p3")
        made = 0
        seen = set()
        while made < n_groups:
            _q, correct, wrongs, expl, params = _det_problem(leaf, rng)
            sig = sp.sstr(correct)
            if sig in seen:
                continue
            try:
                options, ci = distractors.make_options(rng, correct, wrongs)
            except distractors.InsufficientDistractors:
                continue
            seen.add(sig)
            gi += 1
            made += 1
            group = "pg-{:04d}".format(gi)
            base_ref = "{} :: {}".format(tag, expl)
            frames = _P3_FRAMES[leaf]
            texts = [frame(params) for frame in frames]
            for r, text in enumerate(texts, start=1):
                items.append(_record(
                    "eval-p3-{}-r{}".format(group, r), tag, text, options, ci,
                    expl, difficulty, "p3",
                    paraphrase_group=group, base_ref=base_ref,
                ))
    return items


# --------------------------------------------------------------------------- #
# Demo items — enlarge the p0 held-out pool so Exam Mode can build the official
# full-length (66-item) form under the 50/25/25 blueprint.
#
# These are deterministic and correct-by-construction (SymPy keys), authored in
# a HIGH-COEFFICIENT / distinct-phrasing regime disjoint from the study deck so
# `loader.assert_firewall` holds. They are labelled `gen: generated`,
# `demo: True`, and id-prefixed `eval-p0-gen-*` so the scoring layer can exclude
# them from real calibration folds. NOT a live-model run — same AI-off posture.
# --------------------------------------------------------------------------- #
_DEMO_ATTR = {
    "src": "generated",
    "gen": "generated",
    "status": "verified",
    "verified_by": "sympy-cas",
    "verified_on": "2026-07-05",
}

# (leaf, difficulty, count). Totals: calculus 27 / algebra 11 / additional 9 ->
# final p0 pool 35 / 18 / 18, clearing the 33 / 17 / 16 a full form needs.
_DEMO_SPEC = [
    ("integral_single", 2, 14),
    ("differential_single", 2, 13),
    ("linear", 3, 6),
    ("number_theory", 3, 5),
    ("discrete", 3, 3),
    ("geometry", 2, 3),
    ("probability_stats", 3, 3),
]


def _demo_record(rec_id, leaf_tag, question, options, correct_index,
                 explanation, difficulty):
    rec = {
        "id": rec_id,
        "leaf_tag": leaf_tag,
        "format": "mcq",
        "question": question,
        "options": options,
        "correct_index": correct_index,
        "explanation": explanation,
        "difficulty": difficulty,
        "partition": "p0",
        "paraphrase_group": None,
        "base_ref": None,
    }
    rec.update(_DEMO_ATTR)
    rec["demo"] = True
    return rec


def _coprime_pair(rng, lo, hi):
    """Two distinct coprime integers in ``[lo, hi]`` (for a non-trivial gcd)."""
    while True:
        m = rng.randint(lo, hi)
        n = rng.randint(lo, hi)
        if m != n and sp.igcd(m, n) == 1:
            return m, n


def _permutations(n, k):
    p = 1
    for i in range(k):
        p *= n - i
    return p


def _demo_problem(leaf, rng):
    """Return ``(question, correct_expr, wrong_exprs, explanation)``.

    High-coefficient / distinct-phrasing regime, disjoint from the study deck so
    the firewall holds; keys are SymPy-exact (correct-by-construction).
    """
    if leaf == "integral_single":
        a = rng.randint(7, 25)
        b = rng.randint(7, 25)
        f = a * x + b
        correct = sp.integrate(f, x)
        return (
            "Give the antiderivative (omit + C):  "
            + mathfmt.inline("\\int \\left(" + mathfmt.tex(f) + "\\right)\\,dx"),
            correct,
            [sp.diff(f, x), f],
            mathfmt.inline("F(x) = " + mathfmt.tex(correct) + " + C"),
        )
    if leaf == "differential_single":
        a = rng.randint(7, 25)
        n = rng.randint(2, 4)
        f = a * x**n
        correct = sp.diff(f, x)
        return (
            "Differentiate:  " + mathfmt.inline("f(x) = " + mathfmt.tex(f)),
            correct,
            [sp.integrate(f, x), sp.diff(correct, x)],
            mathfmt.inline("f'(x) = " + mathfmt.tex(correct)),
        )
    if leaf == "linear":
        a, b = rng.randint(10, 20), rng.randint(10, 20)
        c, d = rng.randint(10, 20), rng.randint(10, 20)
        correct = sp.Integer(a * d - b * c)
        mat = sp.Matrix([[a, b], [c, d]])
        return (
            "Determinant of " + mathfmt.expr_inline(mat) + "?",
            correct,
            [sp.Integer(a * d + b * c), sp.Integer(a * b - c * d)],
            mathfmt.inline("\\det = " + mathfmt.tex(correct)),
        )
    if leaf == "number_theory":
        g = rng.randint(6, 15)
        m, n = _coprime_pair(rng, 2, 9)
        a, b = g * m, g * n
        correct = sp.Integer(g)
        return (
            "Compute " + mathfmt.inline("\\gcd({}, {})".format(a, b)) + ".",
            correct,
            [sp.Integer(a * b // g), sp.Integer(min(a, b)), sp.Integer(g * 2)],
            mathfmt.inline("\\gcd = " + mathfmt.tex(correct)),
        )
    if leaf == "discrete":
        n = rng.randint(6, 12)
        k = rng.randint(2, 4)
        correct = sp.binomial(n, k)
        return (
            "How many ways can {} objects be chosen from {} when order does "
            "not matter?".format(k, n),
            correct,
            [sp.Integer(_permutations(n, k)), sp.Integer(n**k),
             sp.binomial(n, k - 1)],
            mathfmt.inline("\\binom{%d}{%d} = %s" % (n, k, mathfmt.tex(correct))),
        )
    if leaf == "geometry":
        r = rng.randint(3, 12)
        correct = sp.pi * r**2
        return (
            "What is the area of a circle of radius "
            + mathfmt.inline(str(r)) + "?",
            correct,
            [2 * sp.pi * r, sp.pi * r, sp.pi * r**2 / 2],
            mathfmt.inline("A = \\pi r^2 = " + mathfmt.tex(correct)),
        )
    if leaf == "probability_stats":
        red = rng.randint(2, 6)
        blue = rng.randint(2, 6)
        correct = sp.Rational(red, red + blue)
        return (
            "A jar holds {} red and {} blue marbles. If one is drawn at "
            "random, what is ".format(red, blue)
            + mathfmt.inline("P(\\text{red})") + "?",
            correct,
            [sp.Rational(blue, red + blue), sp.Rational(red, blue),
             sp.Rational(red + blue, red)],
            mathfmt.inline("P = " + mathfmt.tex(correct)),
        )
    raise ValueError("no demo generator for leaf " + leaf)


def gen_demo_p0_items(seed=42):
    """Deterministic demo p0 items that unlock the full-length mock."""
    items = []
    n = 0
    for leaf, difficulty, count in _DEMO_SPEC:
        tag = taxonomy.TAG_BY_LEAF[leaf]
        rng = _leaf_rng(seed, tag + "::eval::p0-demo")
        seen = set()
        generated = 0
        attempts = 0
        while generated < count:
            attempts += 1
            if attempts > 5000:
                raise RuntimeError("demo generation stuck for leaf " + leaf)
            q, correct, wrongs, expl = _demo_problem(leaf, rng)
            if q in seen:
                continue
            try:
                options, ci = distractors.make_options(rng, correct, wrongs)
            except distractors.InsufficientDistractors:
                continue
            seen.add(q)
            n += 1
            generated += 1
            items.append(_demo_record(
                "eval-p0-gen-{:04d}".format(n), tag, q, options, ci,
                expl, difficulty,
            ))
    return items


def emit_yaml(items):
    return yaml.safe_dump({"items": items}, sort_keys=False, allow_unicode=True)


def emit_items(items):
    """Dump a bare item list (no ``items:`` key) for appending to the corpus."""
    return yaml.safe_dump(items, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    print(emit_yaml(gen_p0_items() + gen_p3_pairs()))
