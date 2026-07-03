"""LaTeX survives the note-field HTML escaping so MathJax typesets it correctly.

``build_deck._to_html`` HTML-escapes every field. The regression risk is that a
matrix (LaTeX ``&`` column alignment) or an inequality (``<``) gets mangled. It
does not: escaping only rewrites ``&``/``<``/``>`` into entities that the browser
decodes back in the text node before MathJax reads it. These tests prove the
round-trip (``html.unescape`` of the stored field == the original LaTeX) and that
the MathJax delimiters + control sequences are preserved verbatim.
"""

import html

import sympy as sp

import build_deck
import mathfmt


def test_matrix_latex_survives_html_escape_roundtrip():
    mat = sp.Matrix([[1, 2], [3, 4]])
    front = "Compute the determinant of the matrix:\n\n" + mathfmt.expr_block(mat)
    card = {
        "front": front,
        "back": mathfmt.inline("\\det = -2"),
        "leaf_tag": "topic::algebra::linear",
    }
    note = build_deck.note_for(card)
    field = note.fields[0]
    # The ampersand IS escaped in storage (so genanki sees no raw markup) ...
    assert "&amp;" in field
    # ... but decodes back to the exact LaTeX MathJax will typeset.
    assert html.unescape(field) == front
    assert "\\begin{matrix}" in html.unescape(field)
    # MathJax delimiters + row-break backslashes are untouched by escaping.
    assert "\\[" in field and "\\]" in field
    assert "\\\\" in field  # matrix row separator survives


def test_inequality_lt_survives_html_escape_roundtrip():
    front = mathfmt.inline("a < b")
    card = {"front": front, "back": mathfmt.inline("x = 1"), "leaf_tag": "topic::algebra::elementary"}
    note = build_deck.note_for(card)
    field = note.fields[0]
    assert "&lt;" in field
    assert html.unescape(field) == front
    # Inline delimiters preserved.
    assert field.startswith("\\(") and field.endswith("\\)")
