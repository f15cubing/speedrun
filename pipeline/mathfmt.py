"""The single math-formatting contract for the GRE pipeline.

**Math truth is a SymPy expression; LaTeX is its rendering; MathJax is the one
renderer.** Every surface that displays math (flashcards, MCQ options/stems,
explanations, the eval bank) renders through this module, so there is exactly one
place that decides how a SymPy expression becomes on-screen mathematics.

Output is delimited LaTeX using Anki's / MathJax's conventions:

- inline math  ->  ``\\( ... \\)``
- display math ->  ``\\[ ... \\]``

Anki's desktop reviewer and AnkiDroid both load MathJax on every card and typeset
these delimiters automatically (no ``[latex]`` image toolchain, so it works
offline on a clean device). ``sympy.latex`` is deterministic for a fixed input,
so the pipeline's byte-stable-output guarantee is preserved.
"""

from __future__ import annotations

import sympy as sp

INLINE_OPEN = "\\("
INLINE_CLOSE = "\\)"
BLOCK_OPEN = "\\["
BLOCK_CLOSE = "\\]"


def tex(expr) -> str:
    """Render a SymPy expression to a raw LaTeX string (no delimiters).

    Use this when composing a math span by hand (e.g. ``"f(x) = " + tex(f)``),
    then wrap the whole span with :func:`inline` / :func:`block`.
    """
    return sp.latex(expr)


def inline(latex_str: str) -> str:
    """Wrap an already-LaTeX string in inline ``\\( ... \\)`` delimiters."""
    return INLINE_OPEN + latex_str + INLINE_CLOSE


def block(latex_str: str) -> str:
    """Wrap an already-LaTeX string in display ``\\[ ... \\]`` delimiters."""
    return BLOCK_OPEN + latex_str + BLOCK_CLOSE


def expr_inline(expr) -> str:
    """Render a SymPy expression as inline math: ``\\(<latex>\\)``."""
    return inline(tex(expr))


def expr_block(expr) -> str:
    """Render a SymPy expression as display math: ``\\[<latex>\\]``."""
    return block(tex(expr))
