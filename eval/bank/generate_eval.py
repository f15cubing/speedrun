"""Deterministic SymPy generators for computational eval items (P0 + P3 pairs).

Reuses pipeline/distractors + generate_deck helpers so keys and distractors are
correct-by-construction. Output is meant to be FROZEN into eval/bank/items.yaml
(the committed corpus is the source of truth; this module is the authoring aid).

Design note: _det_problem returns raw params alongside the stem so P3 framings
can be assembled directly from those params — no brittle text extraction needed.
"""
from __future__ import annotations

import yaml

import distractors
import taxonomy
from generate_deck import _leaf_rng, _nonzero, _s, x

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

    ``params`` is a dict of raw values used in the stem so callers can format
    alternative surface framings without parsing the question string.
    """
    import sympy as sp
    if leaf == "integral_single":
        a = _nonzero(rng, 2, 6)
        b = _nonzero(rng, 1, 6)
        f = a * x + b
        correct = sp.integrate(f, x)
        fstr = _s(f)
        return (
            "Give the antiderivative (omit + C):  \u222b ({}) dx".format(fstr),
            correct,
            [sp.diff(f, x), f],
            "F(x) = {} + C".format(_s(correct)),
            {"f": fstr},
        )
    if leaf == "differential_single":
        a = _nonzero(rng, 2, 6)
        n = rng.randint(2, 4)
        f = a * x**n
        correct = sp.diff(f, x)
        fstr = _s(f)
        return (
            "Differentiate:  f(x) = {}".format(fstr),
            correct,
            [sp.integrate(f, x), sp.diff(correct, x)],
            "f'(x) = {}".format(_s(correct)),
            {"f": fstr},
        )
    if leaf == "linear":
        a = _nonzero(rng, -6, 6)
        b = rng.randint(-6, 6)
        c = rng.randint(-6, 6)
        d = _nonzero(rng, -6, 6)
        correct = sp.Integer(a * d - b * c)
        return (
            "Determinant of [[{}, {}], [{}, {}]]?".format(a, b, c, d),
            correct,
            [sp.Integer(a * d + b * c), sp.Integer(a * b - c * d)],
            "det = {}".format(_s(correct)),
            {"a": a, "b": b, "c": c, "d": d},
        )
    if leaf == "number_theory":
        a = rng.randint(12, 90)
        b = rng.randint(12, 90)
        g = sp.igcd(a, b)
        return (
            "Compute gcd({}, {}).".format(a, b),
            sp.Integer(g),
            [sp.Integer(a * b // g), sp.Integer(min(a, b))],
            "gcd = {}".format(g),
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
_P3_FRAMES = {
    "integral_single": [
        "Find the antiderivative (omit + C):  \u222b ({f}) dx",
        "A velocity is v(t) = {f}. Which is a position function s(t) (up to a constant)?",
    ],
    "differential_single": [
        "Differentiate:  f(x) = {f}",
        "Find the slope function f'(x) for f(x) = {f}.",
    ],
    "linear": [
        "Determinant of [[{a}, {b}], [{c}, {d}]]?",
        "For M = [[{a}, {b}], [{c}, {d}]], compute det(M).",
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
            sig = _s(correct)
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
            texts = [frame.format(**params) for frame in frames]
            for r, text in enumerate(texts, start=1):
                items.append(_record(
                    "eval-p3-{}-r{}".format(group, r), tag, text, options, ci,
                    expl, difficulty, "p3",
                    paraphrase_group=group, base_ref=base_ref,
                ))
    return items


def emit_yaml(items):
    return yaml.safe_dump({"items": items}, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    print(emit_yaml(gen_p0_items() + gen_p3_pairs()))
