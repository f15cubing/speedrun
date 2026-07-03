# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Paraphrase robustness proof (Block D).

The eval bank's P3 partition holds paraphrase GROUPS: two rewordings of the same
question with the SAME key (`eval/bank/`). This is the go/no-go probe for whether
"Performance" is genuinely tracking skill or just echoing "Memory" of a specific
surface form (design spec §2): if a simulated cohort's accuracy is stable across
rewordings, the signal is paraphrase-robust; a large within-group gap is the
honest failure flag.

We simulate a cohort answering both rewordings of each group (a 1PL/Rasch draw on
the authored difficulty — the model never sees the latent ability), then report:
- accuracy on rewording R1 ("original") vs R2 ("reworded"), each with a Wilson CI,
- the mean absolute within-group accuracy gap (paraphrase sensitivity).

HONESTY LABEL: simulated cohort (machinery check); real per-student paraphrase
validity is unestablished at n\u22481. Descriptive, not inferential.

Deterministic (fixed seed). Pure stdlib + the eval-bank loader.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random

_DIFF_MID = 3.0
_DIFF_SCALE = 1.414
_Z95 = 1.959963984540054


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def wilson(k: int, n: int, z: float = _Z95):
    """(point, low, high) Wilson score interval for k successes of n."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def load_p3_groups():
    import loader  # from eval/bank (on PYTHONPATH)

    items = loader.load_eval_items(partition="p3")
    groups = {}
    for it in items:
        groups.setdefault(it["paraphrase_group"], []).append(it)
    # each group has exactly 2 rewordings (loader enforces this)
    return {g: sorted(v, key=lambda x: x["id"]) for g, v in groups.items() if len(v) == 2}


def run(seed: int, cohort: int) -> dict:
    groups = load_p3_groups()
    rng = random.Random(seed)
    # A shared latent ability per simulated student across all groups.
    abilities = [rng.gauss(0.0, 1.0) for _ in range(cohort)]

    r1_k = r2_k = 0
    total = cohort * len(groups)
    per_group_gaps = []
    for _g, (r1, r2) in groups.items():
        b1 = (float(r1["difficulty"]) - _DIFF_MID) / _DIFF_SCALE
        b2 = (float(r2["difficulty"]) - _DIFF_MID) / _DIFF_SCALE
        g1 = g2 = 0
        for theta in abilities:
            if rng.random() < _sigmoid(theta - b1):
                g1 += 1
            if rng.random() < _sigmoid(theta - b2):
                g2 += 1
        r1_k += g1
        r2_k += g2
        per_group_gaps.append(abs(g1 - g2) / cohort)

    p1, lo1, hi1 = wilson(r1_k, total)
    p2, lo2, hi2 = wilson(r2_k, total)
    mean_gap = sum(per_group_gaps) / len(per_group_gaps) if per_group_gaps else 0.0
    return {
        "note": ("simulated cohort (machinery check); real per-student paraphrase "
                 "validity unestablished at n\u22481; descriptive"),
        "seed": seed,
        "cohort": cohort,
        "groups": len(groups),
        "rewording_1": {"acc": round(p1, 4), "low": round(lo1, 4), "high": round(hi1, 4), "n": total},
        "rewording_2": {"acc": round(p2, 4), "low": round(lo2, 4), "high": round(hi2, 4), "n": total},
        "accuracy_gap": round(abs(p1 - p2), 4),
        "mean_within_group_abs_gap": round(mean_gap, 4),
        "paraphrase_robust": bool(abs(p1 - p2) <= 0.05),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--cohort", type=int, default=500)
    ap.add_argument("--out", default="docs/evidence/proofs/paraphrase.json")
    args = ap.parse_args(argv)

    result = run(args.seed, args.cohort)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, sort_keys=True, indent=2)
    r1, r2 = result["rewording_1"], result["rewording_2"]
    print(f"paraphrase ({result['groups']} groups, cohort {result['cohort']}):")
    print(f"  rewording 1: {r1['acc']:.3f} [{r1['low']:.3f}, {r1['high']:.3f}]")
    print(f"  rewording 2: {r2['acc']:.3f} [{r2['low']:.3f}, {r2['high']:.3f}]")
    print(f"  accuracy gap={result['accuracy_gap']:.3f}  "
          f"mean within-group |gap|={result['mean_within_group_abs_gap']:.3f}  "
          f"robust={result['paraphrase_robust']}")
    print(f"  note: {result['note']}")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
