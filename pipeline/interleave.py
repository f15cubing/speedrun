"""FSRS-cooperative interleaving: re-sequence a due queue for confusable-type dispersion.

This is a **pure presentation-layer reordering** (PRD §8, D5; design spec
`docs/superpowers/specs/2026-06-30-content-generation-and-timed-ui-design.md` §6). It
**never** touches FSRS scheduling, the collection/undo/store, or the held-out eval bank:
given a due queue already in FSRS priority order it returns a permutation of the *same*
cards that maximises **adjacency dispersion** (consecutive cards drawn from different
confusable clusters) subject to a **displacement bound** so urgent (high-priority) cards
never starve.

It reports the two provable metrics the spec asks for:

* **adjacency dispersion** — fraction of consecutive pairs from different clusters, and
* **FSRS displacement** — how far cards drift (mean / max) from their FSRS slots,

plus the load-bearing **invariant** that the reordered multiset equals the input
multiset (nothing is added, dropped, or duplicated; FSRS scheduling fields are untouched
because we only reorder *presentation*).

The ablation's **blocked** arm is :func:`blocked_order` (identity = FSRS order). Wiring
this into the desktop reviewer + an interleaved↔blocked toggle + the ablation run itself
are **documented follow-ups**; this module is the tested ordering core.

Evidence basis
--------------
Interleaving *confusable* problem types improves discrimination and transfer — the exact
"pick the strategy before executing" demand a GRE item makes: Rohrer, Dedrick, Hartwig &
Cheung (2020, *J. Educ. Psychol.*), classroom **d≈0.83**; Brunmair & Richter (2019,
*Psychol. Bull.*) meta-analysis, **g≈0.34** for mathematics. The honest **incremental**
effect over an *already spaced* app is smaller — **dz≈0.2–0.35** (PRD D5) — so this ships
as a pre-registered estimation pilot, not a confirmatory claim.
"""

from __future__ import annotations

from dataclasses import dataclass

# Default tuning. K = how many recently-shown clusters to avoid repeating; W = the
# displacement bound (a card may land at most W slots later than its FSRS position, so
# an urgent card can never be starved by the dispersion preference).
DEFAULT_K = 1
DEFAULT_W = 3

# Optional leaf-tag -> cluster-id overrides. **Default: each leaf is its own cluster.**
# For the GRE taxonomy that is the right default: the confusable types the research
# targets are the within-bucket leaves themselves (e.g. differentiation vs integration),
# so dispersing at the leaf level *is* confusable-type interleaving. Populate this only
# to deliberately treat several leaves as a single type (they would then be kept apart
# rather than interleaved).
CONFUSABLE_CLUSTERS: dict[str, str] = {}


def cluster_of(leaf: str, clusters: dict[str, str] | None = None) -> str:
    """Cluster id for a leaf tag (defaults to the leaf tag itself)."""
    clusters = CONFUSABLE_CLUSTERS if clusters is None else clusters
    return clusters.get(leaf, leaf)


def _cluster_seq(order, clusters):
    return [cluster_of(leaf, clusters) for _cid, leaf in order]


def adjacency_dispersion(order, clusters: dict[str, str] | None = None) -> float:
    """Fraction of consecutive pairs drawn from different clusters (0..1).

    A perfectly blocked order (``AAABBB``) → ~0; a perfectly alternating order
    (``ABAB``) → 1. Sequences shorter than two items return ``0.0``.
    """
    seq = _cluster_seq(order, clusters)
    if len(seq) < 2:
        return 0.0
    different = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
    return different / (len(seq) - 1)


def displacement(original, reordered) -> tuple[float, int]:
    """``(mean, max)`` forward displacement of cards from their FSRS positions.

    A card's displacement is ``max(0, emitted_index - fsrs_index)`` — how many slots
    *later* than its FSRS priority slot it ended up (the starvation direction). Pulling
    a card *earlier* is interleaving's mechanism and is not penalised. Empty → ``(0.0, 0)``.
    """
    fsrs_index = {cid: i for i, (cid, _leaf) in enumerate(original)}
    shifts = [max(0, new_i - fsrs_index[cid]) for new_i, (cid, _leaf) in enumerate(reordered)]
    if not shifts:
        return (0.0, 0)
    return (sum(shifts) / len(shifts), max(shifts))


def blocked_order(queue):
    """The ablation's blocked / baseline arm: FSRS order, unchanged."""
    return list(queue)


def interleave_order(queue, *, k: int = DEFAULT_K, w: int = DEFAULT_W, clusters=None):
    """Return a dispersion-maximising permutation of ``queue`` (same multiset).

    ``queue`` is ``[(card_id, leaf_tag), ...]`` in FSRS priority order (index 0 = most
    urgent). Greedy per step: emit the highest-priority remaining card whose cluster is
    not among the last ``k`` emitted; but any card that has reached its displacement
    deadline (``fsrs_index + w``) is **force-emitted first**, so no card drifts more than
    ``w`` slots and urgent cards never starve. On a tiny queue (≤2) it returns the input
    unchanged.
    """
    q = list(queue)
    n = len(q)
    if n <= 2:
        return q
    remaining = list(range(n))  # indices into q, kept in FSRS priority order
    present = set(remaining)
    recent: list[str] = []  # clusters of the last emitted cards
    out = []
    for t in range(n):
        # 1) Starvation guard: the card whose deadline (fsrs_index + w == t) has arrived
        #    must be emitted now to respect the displacement bound.
        deadline_idx = t - w
        pick = None
        if deadline_idx >= 0 and deadline_idx in present:
            pick = deadline_idx
        else:
            # 2) Prefer the highest-priority remaining card outside the recent clusters.
            recent_clusters = set(recent[-k:]) if k > 0 else set()
            for idx in remaining:
                if cluster_of(q[idx][1], clusters) not in recent_clusters:
                    pick = idx
                    break
            # 3) Fallback: nothing satisfies the cluster rule → highest-priority remaining.
            if pick is None:
                pick = remaining[0]
        out.append(q[pick])
        present.discard(pick)
        remaining.remove(pick)
        recent.append(cluster_of(q[pick][1], clusters))
    return out


@dataclass
class InterleaveResult:
    """The interleaved order plus the spec's reported metrics."""

    order: list
    adjacency_dispersion: float
    blocked_dispersion: float
    displacement_mean: float
    displacement_max: int
    used_fallback: bool


def interleave(queue, *, k: int = DEFAULT_K, w: int = DEFAULT_W, clusters=None) -> InterleaveResult:
    """Interleave ``queue`` and return the order + adjacency/displacement metrics.

    ``used_fallback`` is True when dispersion is impossible (a homogeneous queue — a
    single cluster — or a queue too small to reorder); in that case the order equals the
    FSRS order and ``adjacency_dispersion == blocked_dispersion``.
    """
    base = list(queue)
    distinct_clusters = {cluster_of(leaf, clusters) for _cid, leaf in base}
    used_fallback = len(distinct_clusters) <= 1 or len(base) <= 2
    order = interleave_order(base, k=k, w=w, clusters=clusters)
    mean_d, max_d = displacement(base, order)
    return InterleaveResult(
        order=order,
        adjacency_dispersion=adjacency_dispersion(order, clusters),
        blocked_dispersion=adjacency_dispersion(base, clusters),
        displacement_mean=mean_d,
        displacement_max=max_d,
        used_fallback=used_fallback,
    )
