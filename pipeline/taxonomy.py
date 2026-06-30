"""Single source of truth for the GRE Math Subject Test topic taxonomy.

The taxonomy is taken verbatim from PRD Appendix A (the frozen ETS three-bucket
outline): Calculus ~50% / Algebra ~25% / Additional ~25%, with ETS's sub-bullets
as the 17 leaf nodes. Tag form is the hierarchical Anki tag ``topic::<bucket>::<leaf>``.

Every other module in ``pipeline/`` imports its leaves, buckets, weights, and the
``validate_leaf_tag`` / ``bucket_of`` helpers from here so there is exactly one place
the taxonomy is defined. The taxonomy is frozen at the leaf level — do not add,
rename, or re-bucket leaves without updating the PRD.
"""

from __future__ import annotations

from collections import namedtuple

# --- tag grammar -----------------------------------------------------------
TAG_PREFIX = "topic"
TAG_SEP = "::"

# --- buckets and their published ETS exam weights --------------------------
# These three numbers are the ONLY weights ETS publishes (PRD D4 / Appendix A).
# Do NOT invent sub-percentages within a bucket.
BUCKETS = ("calculus", "algebra", "additional")

BUCKET_WEIGHTS = {
    "calculus": 0.50,
    "algebra": 0.25,
    "additional": 0.25,
}

# Convenience alias matching the PRD wording ("bucket weights").
WEIGHTS = BUCKET_WEIGHTS

# --- the 17 leaves, verbatim from PRD Appendix A ---------------------------
LEAVES_BY_BUCKET = {
    "calculus": (
        "differential_single",
        "integral_single",
        "differential_multi",
        "integral_multi",
        "differential_equations",
        "applications",
    ),
    "algebra": (
        "elementary",
        "linear",
        "abstract",
        "number_theory",
    ),
    "additional": (
        "real_analysis",
        "discrete",
        "topology",
        "geometry",
        "complex",
        "probability_stats",
        "numerical",
    ),
}

Leaf = namedtuple("Leaf", ("bucket", "leaf", "tag"))


def _make_tag(bucket, leaf):
    return TAG_SEP.join((TAG_PREFIX, bucket, leaf))


# Full ordered list of every leaf, each carrying its bucket and full tag.
LEAVES = tuple(
    Leaf(bucket, leaf, _make_tag(bucket, leaf))
    for bucket in BUCKETS
    for leaf in LEAVES_BY_BUCKET[bucket]
)

# Derived lookups.
LEAF_TAGS = tuple(leaf.tag for leaf in LEAVES)
TAG_BY_LEAF = {leaf.leaf: leaf.tag for leaf in LEAVES}
_VALID_TAGS = frozenset(LEAF_TAGS)
_LEAF_TO_BUCKET = {leaf.leaf: leaf.bucket for leaf in LEAVES}

# --- coverage-gate thresholds (single source of truth) ---------------------
CALCULUS_BUCKET = "calculus"
# Readiness "give-up" rule proxy: cover at least half the taxonomy leaves.
MIN_LEAF_COVERAGE = 0.50
# Deck must reflect the ~50% calculus exam weight.
MIN_CALCULUS_CARD_WEIGHT = 0.50

# --- import-time sanity checks ---------------------------------------------
assert len(LEAVES) == 17, "taxonomy must have exactly 17 leaves (PRD Appendix A)"
assert len(_VALID_TAGS) == 17, "leaf tags must be unique"
assert set(BUCKET_WEIGHTS) == set(BUCKETS), "weights must cover every bucket"
assert abs(sum(BUCKET_WEIGHTS.values()) - 1.0) < 1e-9, "bucket weights must sum to 1.0"


def parse_leaf_tag(tag):
    """Return ``(bucket, leaf)`` if ``tag`` is a valid full leaf tag, else ``None``.

    A valid tag is exactly ``topic::<bucket>::<leaf>`` for a known bucket+leaf.
    """
    if not isinstance(tag, str):
        return None
    parts = tag.split(TAG_SEP)
    if len(parts) != 3:
        return None
    prefix, bucket, leaf = parts
    if prefix != TAG_PREFIX:
        return None
    if bucket not in LEAVES_BY_BUCKET:
        return None
    if leaf not in LEAVES_BY_BUCKET[bucket]:
        return None
    return (bucket, leaf)


def validate_leaf_tag(tag):
    """True iff ``tag`` is exactly one valid fully-qualified leaf tag.

    Strict membership against the frozen set of 17 tags, so a string holding two
    space-joined tags, an unknown leaf, or a non-string all return ``False``.
    """
    return tag in _VALID_TAGS


def bucket_of(leaf):
    """Return the bucket name for a leaf.

    Accepts either a bare leaf name (``"integral_single"``) or a full leaf tag
    (``"topic::calculus::integral_single"``). Raises ``ValueError`` if unknown.
    """
    if leaf in _LEAF_TO_BUCKET:
        return _LEAF_TO_BUCKET[leaf]
    parsed = parse_leaf_tag(leaf)
    if parsed is not None:
        return parsed[0]
    raise ValueError("Unknown leaf or leaf tag: {!r}".format(leaf))
