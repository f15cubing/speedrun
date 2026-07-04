# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""Pre-registered ablation analysis for interleaving (PRD D5, Appendix B).

Given the **within-subject** arm scores — interleaved ON vs blocked OFF, on the delayed
(≥1 wk) test of novel mixed-topic items — this computes the paired effect + a **90% CI**
(paired bootstrap; stdlib, seeded) and runs the pre-registered **TOST equivalence** against
the ±SESOI (**dz 0.3**, converted to raw score units via the observed paired SD), then
emits the **honest-null verdict template**.

This is the *analysis* half of the D5 deliverable — the *ordering* machinery is
`pipeline/interleave.py`; the pre-registration is PRD Appendix B (locked 2026-06-30). Per
Appendix B the deliverable is **the design + the analysis machinery + an honest inconclusive
result**: a pre-registered null scores; a post-hoc hypothesis does not. With team-size *n*
this is powered only for large effects, so it is an **estimation/feasibility pilot**,
reported honestly — never spun as a confirmatory finding.

Pure stdlib + deterministic. It analyses *provided* arm scores; it does **not** touch the
three learner scores, the scoring definitions, the held-out eval bank, or the engine.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass

SESOI_DZ = 0.3          # pre-registered smallest effect size of interest (Appendix B)
CI_LEVEL = 0.90         # pre-registered 90% CI (two one-sided 5% tests → TOST)
BOOTSTRAP_ITERS = 10000


def paired_diffs(interleaved, blocked) -> list[float]:
    """Per-subject (interleaved - blocked) differences; arms must be equal length."""
    if len(interleaved) != len(blocked):
        raise ValueError("within-subject arms must have equal length")
    if not interleaved:
        raise ValueError("no subjects")
    return [float(a) - float(b) for a, b in zip(interleaved, blocked)]


def _mean(xs) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _sd(xs) -> float:
    """Sample SD (n-1)."""
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def cohen_dz(diffs) -> float:
    """Standardized paired effect: mean(diff) / sd(diff). 0 when SD is 0."""
    sd = _sd(diffs)
    return (_mean(diffs) / sd) if sd > 0 else 0.0


def bootstrap_ci(diffs, *, level=CI_LEVEL, iters=BOOTSTRAP_ITERS, seed=42):
    """Percentile bootstrap CI on the mean paired difference (deterministic for a seed)."""
    n = len(diffs)
    if n == 0:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = []
    for _ in range(iters):
        means.append(_mean([diffs[rng.randrange(n)] for _ in range(n)]))
    means.sort()
    alpha = (1.0 - level) / 2.0
    lo = means[int(round(alpha * (iters - 1)))]
    hi = means[int(round((1.0 - alpha) * (iters - 1)))]
    return (lo, hi)


def tost_verdict(ci_low, ci_high, sesoi_raw) -> str:
    """Pre-registered CI + TOST decision:

    * ``equivalent``         — the whole CI lies within (-SESOI, +SESOI) (checked first: a
      trivially small effect is reported as equivalence even if it excludes 0);
    * ``meaningful_effect``  — CI excludes 0 **and** a bound reaches/exceeds the SESOI;
    * ``directional_effect`` — CI excludes 0 but *straddles* the SESOI (statistically
      non-zero, magnitude uncertain — could be trivial or meaningful);
    * ``inconclusive``       — CI spans 0 **and** extends beyond a SESOI bound.
    """
    excludes_zero = (ci_low > 0) or (ci_high < 0)
    within_bounds = (ci_low > -sesoi_raw) and (ci_high < sesoi_raw)
    if within_bounds:
        return "equivalent"
    if excludes_zero:
        beyond = (ci_low >= sesoi_raw) or (ci_high <= -sesoi_raw)
        return "meaningful_effect" if beyond else "directional_effect"
    return "inconclusive"


def min_detectable_dz(n: int) -> float:
    """Crude smallest dz detectable at ~80% power, one-sided paired t (honest power note)."""
    if n <= 1:
        return float("inf")
    return round((1.6448536269 + 0.8416212336) / math.sqrt(n), 3)


@dataclass
class AblationResult:
    n: int
    mean_diff: float
    dz: float
    ci_low: float
    ci_high: float
    sesoi_dz: float
    sesoi_raw: float
    verdict: str
    min_detectable_dz: float


def analyze(interleaved, blocked, *, sesoi_dz=SESOI_DZ, level=CI_LEVEL,
            iters=BOOTSTRAP_ITERS, seed=42) -> AblationResult:
    diffs = paired_diffs(interleaved, blocked)
    sd = _sd(diffs)
    ci_low, ci_high = bootstrap_ci(diffs, level=level, iters=iters, seed=seed)
    sesoi_raw = sesoi_dz * sd  # standardized SESOI → raw score units at the observed SD
    return AblationResult(
        n=len(diffs),
        mean_diff=round(_mean(diffs), 4),
        dz=round(cohen_dz(diffs), 4),
        ci_low=round(ci_low, 4),
        ci_high=round(ci_high, 4),
        sesoi_dz=sesoi_dz,
        sesoi_raw=round(sesoi_raw, 4),
        verdict=tost_verdict(ci_low, ci_high, sesoi_raw),
        min_detectable_dz=min_detectable_dz(len(diffs)),
    )


_VERDICT_TEXT = {
    "equivalent": "statistically EQUIVALENT to zero within the pre-registered SESOI",
    "meaningful_effect": "a MEANINGFUL effect (90% CI excludes 0 and reaches the SESOI)",
    "directional_effect": "a directional effect (90% CI excludes 0 but straddles the SESOI; magnitude uncertain)",
    "inconclusive": "INCONCLUSIVE — the CI spans 0 and also extends beyond the SESOI",
}


def honest_null_template(r: AblationResult) -> str:
    direction = "higher" if r.mean_diff >= 0 else "lower"
    return (
        "Pre-registered ablation: interleaved (ON) vs blocked (OFF), delayed novel "
        "mixed-topic test (PRD Appendix B, H1, one-sided).\n"
        "  Effect: interleaved scored {md:+.2f} raw points {dir} than blocked "
        "(Cohen's dz = {dz:+.2f}); 90% CI [{lo:+.2f}, {hi:+.2f}].\n"
        "  SESOI = dz {sdz} (= {sraw:.2f} raw pts at the observed paired SD). "
        "TOST/CI verdict: {vt}.\n"
        "  n = {n}: this pilot detects only dz >= ~{mdd} at 80% power (detecting dz=0.3 "
        "needs ~90 learners), so it is an ESTIMATION/FEASIBILITY pilot, not a confirmatory "
        "trial. A pre-registered result -- including a null or inconclusive one -- is "
        "reported as-is; no post-hoc reframing.".format(
            md=r.mean_diff, dir=direction, dz=r.dz, lo=r.ci_low, hi=r.ci_high,
            sdz=r.sesoi_dz, sraw=r.sesoi_raw, vt=_VERDICT_TEXT[r.verdict],
            n=r.n, mdd=r.min_detectable_dz,
        )
    )


def demo_dataset(seed: int = 42, n: int = 5):
    """A SYNTHETIC team-size pilot dataset (clearly not real data) to exercise the
    machinery and produce the honest inconclusive result the deliverable calls for."""
    rng = random.Random(seed)
    # small true benefit (~1.5 raw pts) swamped by between-subject noise at tiny n
    interleaved, blocked = [], []
    for _ in range(n):
        base = rng.uniform(40, 70)          # subject ability
        blocked.append(round(base + rng.gauss(0, 6), 2))
        interleaved.append(round(base + 1.5 + rng.gauss(0, 6), 2))
    return interleaved, blocked


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pre-registered interleaving ablation analysis.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=5, help="synthetic pilot size (demo)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    interleaved, blocked = demo_dataset(seed=args.seed, n=args.n)
    result = analyze(interleaved, blocked, seed=args.seed)
    text = honest_null_template(result)
    print("[SYNTHETIC pilot data — machinery demonstration, not a real study]\n")
    print(text)

    if args.out:
        import os
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        payload = asdict(result)
        payload["note"] = "SYNTHETIC pilot data; machinery demonstration (PRD D5/App. B)"
        payload["honest_null_report"] = text
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
