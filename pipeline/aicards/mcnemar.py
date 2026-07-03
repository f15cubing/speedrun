# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Exact McNemar test + paired bootstrap CI — pure stdlib (no scipy/numpy).

McNemar's test compares two paired binary classifiers (here: the AI-pipeline arm vs
the baseline arm, "usable card produced?" on the same items). It looks only at the
**discordant** pairs — items where the two arms disagree:

    b = A usable, B not   (A wins)
    c = A not,   B usable  (B wins)

Under H0 (the arms are equally good) each discordant pair is a fair coin, so b ~
Binomial(b+c, 0.5). The **exact two-sided p-value** is the binomial tail doubled:

    p = min(1, 2 * sum_{i=0}^{min(b,c)} C(n, i) * 0.5^n),  n = b + c

`math.comb` (stdlib, Py>=3.8) gives exact integer binomial coefficients, so this is
exact — no normal approximation, no continuity correction, no external deps.
"""

from __future__ import annotations

import random
from collections import namedtuple
from math import comb

McNemarResult = namedtuple(
    "McNemarResult", ["b", "c", "n", "p_value", "favored", "statistic"]
)


def mcnemar_exact(b: int, c: int) -> McNemarResult:
    """Exact two-sided McNemar test from the two discordant counts."""
    b = int(b)
    c = int(c)
    n = b + c
    if n == 0:
        return McNemarResult(b, c, 0, 1.0, "tie", 0.0)
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    p_value = min(1.0, 2.0 * tail)
    favored = "A" if b > c else ("B" if c > b else "tie")
    # Continuity-corrected chi-square statistic, reported for reference only.
    statistic = (abs(b - c) - 1) ** 2 / n if n > 0 else 0.0
    return McNemarResult(b, c, n, p_value, favored, statistic)


def discordant_table(pairs):
    """From an iterable of ``(a_usable, b_usable)`` 0/1 pairs, return ``(a,b,c,d)``.

    a = both usable · b = A only (A wins) · c = B only (B wins) · d = neither.
    """
    a = b = c = d = 0
    for av, bv in pairs:
        av, bv = int(bool(av)), int(bool(bv))
        if av and bv:
            a += 1
        elif av and not bv:
            b += 1
        elif bv and not av:
            c += 1
        else:
            d += 1
    return a, b, c, d


def mcnemar_from_pairs(pairs) -> McNemarResult:
    _, b, c, _ = discordant_table(pairs)
    return mcnemar_exact(b, c)


def paired_bootstrap_ci(a_flags, b_flags, seed=42, iters=5000, alpha=0.10):
    """Deterministic paired bootstrap CI for the usable-rate difference (A - B).

    Resamples the paired items with replacement (same indices for both arms, so the
    pairing is preserved). Returns the ``(1-alpha)`` percentile interval for
    ``mean(A) - mean(B)``. Seeded → byte-stable (PRD §11).
    """
    a_flags = [float(v) for v in a_flags]
    b_flags = [float(v) for v in b_flags]
    n = len(a_flags)
    if n == 0 or n != len(b_flags):
        return (0.0, 0.0)
    rng = random.Random("mcnemar-boot:{}".format(seed))
    diffs = []
    for _ in range(iters):
        sa = sb = 0.0
        for _ in range(n):
            j = rng.randrange(n)
            sa += a_flags[j]
            sb += b_flags[j]
        diffs.append((sa - sb) / n)
    diffs.sort()
    lo_i = int((alpha / 2.0) * iters)
    hi_i = min(iters - 1, int((1.0 - alpha / 2.0) * iters))
    return (diffs[lo_i], diffs[hi_i])
