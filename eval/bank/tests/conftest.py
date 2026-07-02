"""Make eval/bank and pipeline importable when pytest collects from the repo root."""
import os
import sys

BANK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(os.path.dirname(BANK_DIR))
PIPELINE_DIR = os.path.join(REPO_ROOT, "pipeline")
for path in (BANK_DIR, PIPELINE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)
