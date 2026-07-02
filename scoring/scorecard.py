# scoring/scorecard.py
"""Assemble the synced gre_scorecard JSON payload (spec §6)."""
from __future__ import annotations


def build(memory, performance, readiness, *, source, updated_at) -> dict:
    return {
        "version": 1,
        "updated_at": updated_at,
        "source": source,
        "memory": memory,
        "performance": performance,
        "readiness": readiness,
    }
