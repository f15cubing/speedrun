<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Original single-variable-calculus reference chapter for the GRE Math Speedrun fork.

PROVENANCE / FIREWALL NOTE (read before editing):
  * This file is the RAG *source chapter* the AI card pipeline retrieves over and
    quotes from (pipeline/aicards/). Every generated card's non-nullable provenance
    quote must appear VERBATIM in one of the passages below, anchored to its id.
  * It is ORIGINAL prose written for this repo. It is NOT copied from MIT
    OpenCourseWare, ETS, or any other source. It shares only the *subject*
    (single-variable calculus) with the held-out MIT-OCW gold-set
    (eval/goldset/) — train and test share the topic, never the items (PRD §12).
  * Contains NO ETS/GRE exam items and NO gold-set canary strings (firewall,
    PRD §9/§11). The firewall test asserts this.
  * Facts are standard mathematics stated in original wording. Keep every rule a
    single, self-contained, quotable sentence so a card can anchor to it.
-->

# Single-Variable Calculus — Reference Chapter

A compact, self-contained reference for the differential and integral calculus of
one real variable. Each section states rules as short, quotable sentences.

## Limits and continuity

A function f has limit L as x approaches c when f(x) can be made arbitrarily close
to L by taking x sufficiently close to c but not equal to c.

A function f is continuous at a point c when the limit of f(x) as x approaches c
exists and equals f(c).

The epsilon-delta definition states that the limit of f(x) as x approaches c is L
when for every positive epsilon there is a positive delta such that the distance
from f(x) to L is less than epsilon whenever the distance from x to c is less than
delta.

Every function that is differentiable at a point is also continuous at that point,
but a continuous function need not be differentiable.

## The derivative

The derivative of a function f at a point x is the limit of the difference quotient
(f(x + h) minus f(x)) divided by h as h approaches zero, when that limit exists.

The derivative measures the instantaneous rate of change of f and equals the slope
of the tangent line to the graph of f at the point of tangency.

### Power rule

The power rule states that the derivative of x raised to the power n is n times x
raised to the power n minus one.

The derivative of any constant function is zero.

### Constant multiple, sum, and difference rules

The constant multiple rule states that the derivative of a constant times a
function is that constant times the derivative of the function.

The sum rule states that the derivative of a sum of functions is the sum of their
derivatives, and the same holds for differences term by term.

### Product and quotient rules

The product rule states that the derivative of a product f times g equals f prime
times g plus f times g prime.

The quotient rule states that the derivative of f divided by g equals g times f
prime minus f times g prime, all divided by g squared.

### Chain rule

The chain rule states that the derivative of a composition f of g at x equals f
prime evaluated at g of x, times g prime of x.

A common error is to omit the inner factor g prime of x when differentiating a
composition; the chain rule requires multiplying by that inner derivative.

### Derivatives of elementary functions

The derivative of the sine function is the cosine function, and the derivative of
the cosine function is the negative of the sine function.

The derivative of the natural exponential function is the natural exponential
function itself.

The derivative of the natural logarithm of x is one divided by x for positive x.

## Applications of the derivative

The slope of the line tangent to the graph of f at the point where x equals a is
the value of the derivative f prime evaluated at a.

A differentiable function is increasing on an interval where its derivative is
positive and decreasing on an interval where its derivative is negative.

A critical point of f is a point in its domain where the derivative is zero or
undefined, and interior extrema can occur only at critical points.

The Mean Value Theorem states that if f is continuous on a closed interval and
differentiable on its interior, then there is an interior point where the
derivative equals the average rate of change over the interval.

## Antiderivatives and the indefinite integral

An antiderivative of a function f is a function whose derivative is f, and the
indefinite integral of f denotes the family of all such antiderivatives.

Because the derivative of a constant is zero, every indefinite integral includes an
arbitrary constant of integration, written plus C.

A frequent error is to drop the constant of integration; an indefinite integral is
incomplete without the plus C term.

### Integral of a power

The power rule for integration states that the integral of x raised to the power n,
for n not equal to negative one, is x raised to the power n plus one, divided by n
plus one, plus a constant of integration.

The integral of one divided by x is the natural logarithm of the absolute value of
x, plus a constant of integration.

### Integrals of elementary functions

The integral of the natural exponential function is the natural exponential
function itself, plus a constant of integration.

The integral of the cosine function is the sine function plus a constant, and the
integral of the sine function is the negative cosine function plus a constant.

The integral of a constant times a function equals that constant times the integral
of the function, and integrals distribute over sums term by term.

## The definite integral

The definite integral of a nonnegative function over an interval equals the area
between the graph of the function and the horizontal axis over that interval.

The Fundamental Theorem of Calculus states that the definite integral of f from a to
b equals F of b minus F of a, where F is any antiderivative of f.

The average value of a continuous function f over the interval from a to b is the
definite integral of f from a to b, divided by the length b minus a.

## Sequences and series

A sequence converges to a limit L when its terms become and remain arbitrarily
close to L as the index grows without bound.

A geometric series with common ratio r converges if and only if the absolute value
of r is less than one, and then its sum is the first term divided by one minus r.

The harmonic series, the sum of the reciprocals of the positive integers, diverges
even though its terms tend to zero.

A sequence is called a Cauchy sequence when its terms eventually all lie within any
prescribed positive distance of one another, and in the real numbers every Cauchy
sequence converges.
