"""Put the scoring package on sys.path for pytest from the repo root."""
import os
import sys

SCORING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(SCORING_DIR)
for p in (REPO_ROOT, SCORING_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)
