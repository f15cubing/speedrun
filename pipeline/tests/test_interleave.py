"""Tests for the interleaving ordering core (pure, FSRS-cooperative re-sort)."""

import interleave


def _blocked(clusters_per_group=3, groups=("A", "B", "C", "D")):
    """A blocked queue AAABBB... as [(id, leaf), ...] in FSRS priority order."""
    q = []
    n = 0
    for g in groups:
        for _ in range(clusters_per_group):
            q.append(("c%d" % n, "topic::x::%s" % g))
            n += 1
    return q


def _ids(order):
    return [cid for cid, _leaf in order]


# --- invariants ---


def test_interleave_preserves_the_multiset():
    q = _blocked()
    out = interleave.interleave_order(q)
    assert sorted(_ids(out)) == sorted(_ids(q))  # nothing added/dropped/duplicated
    assert len(out) == len(q)


def test_interleave_is_deterministic():
    q = _blocked()
    a = interleave.interleave_order(q)
    b = interleave.interleave_order(q)
    assert _ids(a) == _ids(b)


# --- the two reported metrics ---


def test_adjacency_dispersion_metric():
    blocked = [("1", "L::A"), ("2", "L::A"), ("3", "L::B"), ("4", "L::B")]
    alt = [("1", "L::A"), ("2", "L::B"), ("3", "L::A"), ("4", "L::B")]
    assert interleave.adjacency_dispersion(blocked) == 1 / 3  # one A->B transition of 3
    assert interleave.adjacency_dispersion(alt) == 1.0
    assert interleave.adjacency_dispersion(alt[:1]) == 0.0  # singleton


def test_displacement_metric_counts_only_forward_drift():
    original = [("a", "L::X"), ("b", "L::Y"), ("c", "L::Z")]
    # b moved from index 1 -> 2 (forward drift 1); a pulled forward (no penalty)
    reordered = [("b", "L::Y"), ("a", "L::X"), ("c", "L::Z")]
    mean_d, max_d = interleave.displacement(original, reordered)
    assert max_d == 1  # only 'a' drifts forward (index 0 -> 1); 'b' pulled earlier
    assert mean_d == 1 / 3


# --- the core behaviour ---


def test_interleaving_raises_dispersion_over_blocked():
    q = _blocked()  # AAABBBCCCDDD
    res = interleave.interleave(q)
    assert res.adjacency_dispersion > res.blocked_dispersion
    assert res.adjacency_dispersion > 0.8  # near-perfect alternation is achievable here
    assert not res.used_fallback


def test_displacement_bound_prevents_starvation():
    # No card may drift more than W slots later than its FSRS position, so the most
    # urgent card (index 0) always appears within the first W+1 positions.
    q = _blocked()
    w = 3
    res = interleave.interleave(q, w=w)
    assert res.displacement_max <= w
    top_id = _ids(q)[0]
    assert _ids(res.order).index(top_id) <= w


# --- graceful fallbacks ---


def test_homogeneous_queue_falls_back_to_fsrs_order():
    q = [("c%d" % i, "topic::x::A") for i in range(6)]  # one cluster only
    res = interleave.interleave(q)
    assert res.used_fallback is True
    assert _ids(res.order) == _ids(q)  # unchanged
    assert res.adjacency_dispersion == 0.0


def test_tiny_queue_is_unchanged():
    for q in ([], [("a", "L::A")], [("a", "L::A"), ("b", "L::B")]):
        res = interleave.interleave(q)
        assert _ids(res.order) == _ids(q)
        assert res.used_fallback is True


# --- cluster mapping ---


def test_cluster_of_defaults_to_leaf_and_honours_overrides():
    assert interleave.cluster_of("topic::calculus::integral_single") == (
        "topic::calculus::integral_single"
    )
    override = {"topic::calculus::integral_single": "calc", "topic::calculus::differential_single": "calc"}
    assert interleave.cluster_of("topic::calculus::integral_single", override) == "calc"
    # grouped leaves are treated as ONE cluster (kept apart, not interleaved)
    q = [
        ("a", "topic::calculus::integral_single"),
        ("b", "topic::calculus::differential_single"),
    ]
    assert interleave.adjacency_dispersion(q, override) == 0.0  # same cluster now
