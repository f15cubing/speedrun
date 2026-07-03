# SPDX-License-Identifier: AGPL-3.0-or-later
# Part of the GRE Math Speedrun fork of Anki (see repo LICENSE; credit: Anki / ankitects).
"""Verification for AI-generated cards (PRD §9).

Two independent worlds:

* **Computational cards** are *proved* by re-derivation with SymPy — a decisive,
  deterministic gate that is independent of whatever produced the card. Two methods
  are provided so the gold-set gate can use genuinely different raters:
  - :func:`verify_computational` — symbolic CAS (``simplify`` / derivative-equivalence);
  - :func:`numeric_check` — an independent numeric probe (sample-point evaluation),
    which does not trust the symbolic simplifier.
  A wrong computational answer cannot pass either.

* **Conceptual cards** cannot be re-derived, only *entailment-checked* against their
  source quote with an NLI **proxy** (lexical token containment — a stand-in for a
  real NLI model, labelled honestly). Passing entailment is necessary but NOT
  sufficient, so conceptual cards are **always** routed to mandatory human review
  (:func:`needs_human_review`) and never auto-verified.
"""

from __future__ import annotations

import random
from collections import namedtuple

import sympy as sp

import cards as _cards
from retriever import tokenize

VerifyResult = namedtuple("VerifyResult", ["ok", "detail"])

# Fixed seed so the numeric probe's sample points are byte-stable (PRD §11).
_PROBE_SEED = 20260703
_PROBE_POINTS = 7
_PROBE_TOL = 1e-6

# Entailment (NLI-proxy) threshold: fraction of a claim's content tokens that must
# be present in the source quote for the claim to count as "supported".
ENTAILMENT_THRESHOLD = 0.7


def _symbolically_equal(a, b) -> bool:
    """Robust symbolic equality that never raises."""
    try:
        return sp.simplify(sp.sympify(a) - sp.sympify(b)) == 0
    except (TypeError, ValueError, AttributeError, sp.SympifyError):
        return str(a) == str(b)


def recompute(check: dict):
    """Independently compute the correct answer for a computational ``check``."""
    op = check["op"]
    if op == "diff":
        return sp.diff(check["f"], check["var"])
    if op == "deriv_at":
        return sp.diff(check["f"], check["var"]).subs(check["var"], check["at"])
    if op == "defint":
        return sp.integrate(check["f"], (check["var"], check["lo"], check["hi"]))
    if op == "average":
        length = check["hi"] - check["lo"]
        return sp.integrate(check["f"], (check["var"], check["lo"], check["hi"])) / length
    if op == "antideriv":
        return sp.integrate(check["f"], check["var"])
    if op == "gcd":
        return sp.Integer(sp.igcd(int(check["m"]), int(check["n"])))
    if op == "mod":
        return sp.Integer(int(check["m"]) % int(check["n"]))
    if op == "binomial":
        return sp.Integer(sp.binomial(int(check["n"]), int(check["k"])))
    raise ValueError("unknown verification op {!r}".format(op))


def verify_computational(check: dict, claimed) -> VerifyResult:
    """Symbolic CAS gate: is ``claimed`` a provably correct answer for ``check``?"""
    op = check["op"]
    try:
        if op == "antideriv":
            # An antiderivative is correct iff its derivative is the integrand
            # (any constant of integration is acceptable).
            deriv = sp.diff(claimed, check["var"])
            ok = _symbolically_equal(deriv, check["f"])
            return VerifyResult(ok, "d/dx(claimed) {} integrand".format("==" if ok else "!="))
        correct = recompute(check)
        ok = _symbolically_equal(claimed, correct)
        return VerifyResult(ok, "claimed {} recomputed {}".format("==" if ok else "!=", correct))
    except Exception as exc:  # a bad card must fail closed, never crash the run
        return VerifyResult(False, "cas error: {}".format(exc))


def numeric_check(check: dict, claimed, n_points: int = _PROBE_POINTS,
                  tol: float = _PROBE_TOL) -> VerifyResult:
    """Independent numeric probe (Rater B): evaluate at fixed sample points.

    Deliberately avoids the symbolic simplifier — it lambdifies both sides and
    compares floating-point values at deterministic sample points. For scalar
    results it compares the numbers directly; for function-valued results
    (``diff``/``antideriv``) it compares at several points.
    """
    op = check["op"]
    try:
        if op in ("gcd", "mod", "binomial"):
            return VerifyResult(int(claimed) == int(recompute(check)), "integer compare")
        if op in ("deriv_at", "defint", "average"):
            correct = float(recompute(check))
            got = float(claimed)
            ok = abs(got - correct) <= tol * (1.0 + abs(correct))
            return VerifyResult(ok, "scalar {:.6g} vs {:.6g}".format(got, correct))

        var = check["var"]
        if op == "diff":
            lhs, rhs = claimed, sp.diff(check["f"], var)
        elif op == "antideriv":
            lhs, rhs = sp.diff(claimed, var), check["f"]
        else:
            lhs, rhs = claimed, recompute(check)

        f_lhs = sp.lambdify(var, lhs, "math")
        f_rhs = sp.lambdify(var, rhs, "math")
        rng = random.Random(_PROBE_SEED)
        agree = 0
        total = 0
        for _ in range(n_points):
            pt = rng.uniform(0.3, 2.7)  # away from 0 (1/x, ln) and small (exp overflow)
            try:
                a = f_lhs(pt)
                b = f_rhs(pt)
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            total += 1
            if abs(a - b) <= tol * (1.0 + abs(b)):
                agree += 1
        ok = total > 0 and agree == total
        return VerifyResult(ok, "{}/{} sample points agree".format(agree, total))
    except Exception as exc:
        return VerifyResult(False, "numeric error: {}".format(exc))


def entailment_score(claim: str, quote: str) -> float:
    """NLI **proxy**: fraction of the claim's content tokens present in the quote.

    This is a lexical stand-in for a real entailment model, labelled honestly as a
    proxy. It is only ever used as a *necessary* filter; conceptual cards still go
    to human review regardless of the score.
    """
    claim_tokens = tokenize(claim)
    if not claim_tokens:
        return 0.0
    quote_tokens = set(tokenize(quote))
    hits = sum(1 for t in claim_tokens if t in quote_tokens)
    return hits / len(claim_tokens)


def entails(claim: str, quote: str, threshold: float = ENTAILMENT_THRESHOLD) -> bool:
    return entailment_score(claim, quote) >= threshold


def needs_human_review(card) -> bool:
    """Conceptual cards always require human adjudication; computational do not."""
    return getattr(card, "kind", None) == _cards.CONCEPTUAL
