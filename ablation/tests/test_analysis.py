# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Tests for the pre-registered ablation analysis machinery (pure stdlib)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ablation import analysis as ab  # noqa: E402


# --- paired differences ---


def test_paired_diffs_and_validation():
    assert ab.paired_diffs([3, 5], [1, 2]) == [2.0, 3.0]
    for bad in (([1, 2], [1]), ([], [])):
        try:
            ab.paired_diffs(*bad)
            assert False, "expected ValueError"
        except ValueError:
            pass


def test_cohen_dz_zero_when_constant():
    assert ab.cohen_dz([2.0, 2.0, 2.0]) == 0.0  # sd 0
    d = [1.0, 2.0, 3.0, 4.0]
    assert abs(ab.cohen_dz(d) - (ab._mean(d) / ab._sd(d))) < 1e-12


# --- bootstrap CI ---


def test_bootstrap_ci_constant_and_deterministic():
    assert ab.bootstrap_ci([2.0] * 5, iters=500) == (2.0, 2.0)  # no variance -> point CI
    a = ab.bootstrap_ci([1.0, 2.0, 3.0, 4.0, 5.0], seed=7, iters=2000)
    b = ab.bootstrap_ci([1.0, 2.0, 3.0, 4.0, 5.0], seed=7, iters=2000)
    assert a == b  # deterministic for a fixed seed
    assert a[0] <= 3.0 <= a[1]  # brackets the mean


# --- TOST / CI verdict ---


def test_tost_verdict_all_branches():
    s = 1.82
    assert ab.tost_verdict(-1.0, 1.0, s) == "equivalent"          # within +/- SESOI
    assert ab.tost_verdict(0.2, 1.0, s) == "equivalent"           # within SESOI even excluding 0
    assert ab.tost_verdict(2.0, 4.0, s) == "meaningful_effect"    # excludes 0, beyond SESOI
    assert ab.tost_verdict(0.5, 2.5, s) == "directional_effect"   # excludes 0, straddles SESOI
    assert ab.tost_verdict(-3.0, 5.0, s) == "inconclusive"        # spans 0, beyond SESOI


def test_min_detectable_dz_shrinks_with_n():
    assert ab.min_detectable_dz(5) > ab.min_detectable_dz(90)
    assert 1.0 < ab.min_detectable_dz(5) < 1.3  # team-size only powered for large effects


# --- end-to-end ---


def test_analyze_shape_and_determinism():
    inter, blk = ab.demo_dataset(seed=42, n=5)
    r1 = ab.analyze(inter, blk, seed=42)
    r2 = ab.analyze(inter, blk, seed=42)
    assert r1 == r2
    assert r1.n == 5
    assert r1.ci_low <= r1.mean_diff <= r1.ci_high
    assert r1.sesoi_raw >= 0.0


def test_demo_pilot_is_honestly_inconclusive():
    inter, blk = ab.demo_dataset(seed=42, n=5)
    r = ab.analyze(inter, blk, seed=42)
    assert r.verdict == "inconclusive"  # tiny-n pilot cannot rule in or out
    text = ab.honest_null_template(r)
    assert "pre-registered" in text.lower()
    assert "SESOI" in text
    assert "reported as-is" in text
