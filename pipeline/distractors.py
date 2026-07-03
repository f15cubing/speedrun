"""Deterministic MCQ option assembly + common-error distractors.

Given a correct SymPy answer and operation-specific wrong answers (also SymPy),
assemble exactly ``n_options`` stringified options with the correct answer at a
deterministic index. Wrong answers are validated to be defined, mutually distinct,
and != the key (symbolic equality). When the supplied wrongs are too few, generic
common-error transforms top them up; if still too few, ``InsufficientDistractors``
is raised so the caller can skip/redraw the instance.

No randomness beyond the supplied ``rng`` (used only to place/order options), so
output is byte-stable for a fixed seed. No AI, no network.
"""

from __future__ import annotations

import sympy as sp

import mathfmt

N_OPTIONS = 5


class InsufficientDistractors(Exception):
    """Raised when fewer than ``n_options - 1`` valid distractors can be formed."""


def _equal(a, b):
    """Symbolic equality that never raises (falls back to string compare)."""
    try:
        return sp.simplify(a - b) == 0
    except (TypeError, ValueError, sp.SympifyError, AttributeError):
        return str(a) == str(b)


def generic_variants(expr):
    """Operation-agnostic common-error variants, in a fixed deterministic order."""
    return [-expr, 2 * expr, expr + 1, expr - 1]


def make_options(rng, correct, wrong_exprs, n_options=N_OPTIONS):
    """Return ``(options, correct_index)``.

    ``correct`` and items of ``wrong_exprs`` are SymPy expressions. Options are
    rendered as **inline LaTeX** (``\\(...\\)`` via :mod:`mathfmt`) so MathJax
    typesets them. De-duplication and the "distinct from the key" check operate
    on the canonical SymPy string (``sympy.sstr``), never on the rendered LaTeX,
    so distractor integrity is independent of presentation.
    """
    needed = n_options - 1
    correct_canon = sp.sstr(correct)

    chosen_exprs = []
    seen = {correct_canon}
    for cand in list(wrong_exprs) + generic_variants(correct):
        if cand is None:
            continue
        if _equal(cand, correct):
            continue
        cand_canon = sp.sstr(cand)
        if cand_canon in seen:
            continue
        seen.add(cand_canon)
        chosen_exprs.append(cand)
        if len(chosen_exprs) == needed:
            break

    if len(chosen_exprs) < needed:
        raise InsufficientDistractors(
            "only {} distinct distractors for key {!r}".format(len(chosen_exprs), correct_canon)
        )

    exprs = list(chosen_exprs)
    correct_index = rng.randint(0, n_options - 1)
    exprs.insert(correct_index, correct)
    options = [mathfmt.expr_inline(e) for e in exprs]
    return options, correct_index
