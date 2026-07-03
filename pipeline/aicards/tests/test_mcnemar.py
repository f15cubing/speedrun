# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Tests for the pure-stdlib exact McNemar test + paired bootstrap CI."""

import pytest

import mcnemar


def test_no_discordant_pairs_gives_p_one():
    r = mcnemar.mcnemar_exact(0, 0)
    assert r.p_value == 1.0
    assert r.b == 0 and r.c == 0


def test_symmetric_discordant_gives_p_one():
    # b == c: perfectly symmetric -> cannot reject H0.
    assert mcnemar.mcnemar_exact(7, 7).p_value == 1.0


def test_sign_test_eight_zero():
    # b=8, c=0: two-sided exact = 2 * 0.5^8 = 1/128.
    r = mcnemar.mcnemar_exact(8, 0)
    assert r.p_value == pytest.approx(2 * 0.5 ** 8)
    assert r.p_value == pytest.approx(0.0078125)


def test_known_value_ten_one():
    # b=10, c=1, n=11: two-sided = 2*(C(11,0)+C(11,1))*0.5^11 = 2*12/2048.
    r = mcnemar.mcnemar_exact(10, 1)
    assert r.p_value == pytest.approx(2 * 12 / 2048)
    assert r.p_value == pytest.approx(0.01171875)


def test_large_discordant_is_highly_significant():
    r = mcnemar.mcnemar_exact(30, 4)
    assert r.p_value < 1e-4
    assert r.favored == "A"  # b (A-wins) > c


def test_direction_favors_b_or_c():
    assert mcnemar.mcnemar_exact(3, 12).favored == "B"
    assert mcnemar.mcnemar_exact(12, 3).favored == "A"
    assert mcnemar.mcnemar_exact(5, 5).favored == "tie"


def test_p_value_never_exceeds_one():
    for b in range(0, 15):
        for c in range(0, 15):
            assert 0.0 <= mcnemar.mcnemar_exact(b, c).p_value <= 1.0


def test_table_from_paired_labels():
    # Pairs of (A_usable, B_usable).
    pairs = [(1, 1), (1, 0), (1, 0), (0, 1), (0, 0)]
    a, b, c, d = mcnemar.discordant_table(pairs)
    assert (a, b, c, d) == (1, 2, 1, 1)


def test_paired_bootstrap_ci_is_deterministic_and_brackets_diff():
    # A usable on 8/10, B usable on 3/10; difference favors A.
    a_flags = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
    b_flags = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    lo1, hi1 = mcnemar.paired_bootstrap_ci(a_flags, b_flags, seed=42)
    lo2, hi2 = mcnemar.paired_bootstrap_ci(a_flags, b_flags, seed=42)
    assert (lo1, hi1) == (lo2, hi2)          # deterministic
    assert lo1 <= 0.5 <= hi1                  # observed diff = 0.5 inside CI
    assert lo1 > 0                            # CI excludes 0 -> A better
