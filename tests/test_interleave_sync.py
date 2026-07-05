"""Guard: the vendored interleaving algorithm must not drift from its source.

The "how this differs from FSRS" page runs the interleaving algorithm inside the app,
so a copy is vendored (`anki/qt/aqt/gre/interleave.py`) because the app can't import the
outer `pipeline/` at runtime (same reason `exam_items.json` is vendored). The vendored
copy carries a short license/vendoring header and is kept ruff-formatted for the app's
lint gate, so we compare **logic, not bytes**: the two modules must parse to the same
AST (formatting/quote-style/wrapping differences are ignored; any change to the actual
algorithm fails this test). Re-vendor from `pipeline/interleave.py` if it trips.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/interleave.py"
VENDORED = ROOT / "anki/qt/aqt/gre/interleave.py"


def _ast(path: Path) -> str:
    return ast.dump(ast.parse(path.read_text(encoding="utf-8")))


def test_vendored_interleave_matches_source():
    assert _ast(VENDORED) == _ast(SOURCE), (
        "anki/qt/aqt/gre/interleave.py drifted from pipeline/interleave.py — re-vendor it"
    )
    header = VENDORED.read_text(encoding="utf-8")
    assert "Vendored verbatim from pipeline/interleave.py" in header
    assert "GNU AGPL" in header
