"""Make the ``pipeline/`` modules importable when pytest collects from the repo root."""

import os
import sys

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)
