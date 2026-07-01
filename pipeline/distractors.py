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
    rendered with ``sympy.sstr`` (matching the deck's ``generate_deck._s``).
    """
    needed = n_options - 1
    correct_str = sp.sstr(correct)

    chosen_strs = []
    seen = {correct_str}
    for cand in list(wrong_exprs) + generic_variants(correct):
        if cand is None:
            continue
        if _equal(cand, correct):
            continue
        cand_str = sp.sstr(cand)
        if cand_str in seen:
            continue
        seen.add(cand_str)
        chosen_strs.append(cand_str)
        if len(chosen_strs) == needed:
            break

    if len(chosen_strs) < needed:
        raise InsufficientDistractors(
            "only {} distinct distractors for key {!r}".format(len(chosen_strs), correct_str)
        )

    options = list(chosen_strs)
    correct_index = rng.randint(0, n_options - 1)
    options.insert(correct_index, correct_str)
    return options, correct_index
