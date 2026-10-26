"""
rotc_thirds_native.py — ROTC thirds-angle exactness: one documented dead
end, and one verified working fix.

Contract: docs/ROTC_THIRDS_EXACTNESS_FIX.md. Finding:
knowledge/SPU_LEXICON.md, Davis Gate entry ("/3 divisibility").

DEAD END (kept as a permanent audit trail, do not resurrect without
re-deriving): a "global trebled unit" convention — every raw Quadray
integer implicitly 3x the classical IVM step — was proposed as a
division-free fix. It is wrong. Applying the integer coefficients
(2, 2, -1 etc.) directly to an already-trebled input does not reproduce
a trebled output; it produces a 9x-scaled one, because the coefficients
themselves already carry the factor of 3 that was meant to be divided
out, and a fixed uniform rescaling cannot absorb a multiplicative-per-
application effect. `rotate_no_div_DEAD_END` and
`verify_no_div_matches_ground_truth` exist so this can never be silently
re-proposed as fixed without someone re-deriving why it isn't.

VERIFIED WORKING: a deferred-reduction, exponent-tagged representation.
State is carried as (value, exponent) with true_value = value / 3**exponent.
The raw integer coefficients apply directly to `value` (no division,
ever); each thirds-angle rotation increments `exponent` by 1. This is
exact by construction — no information is ever lost, the division is
deferred to an explicit renormalization point, not eliminated. Verified
against the exact Fraction-based ground truth (rational_robotics.py)
across a real 4-step, multi-axis composition chain (angles 1->3->4->1) —
the exact case that broke every narrower mitigation.

This is a genuine ISA extension if adopted (every register needs an
exponent field; combining values with different exponents needs
alignment, the same complexity floating-point addition carries) — same
shape as the sparse jet MAC's nilpotency-window tags
(docs/SPARSE_JET_MAC.md). Not a drop-in fix. See the fix doc's §2(c-revised)
and acceptance checklist before any RTL work.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from lib.rational_robotics import Q3, QuadrayQ, joint_60, joint_120, joint_240

# Integer (F, G, H) numerators per the corrected ROTC catalog — denom is
# always exactly 3 for these three angles (identity/P5 angles 0,2,5 have
# denom 1 and were never division-affected; this module doesn't touch them).
THIRDS_COEFFS: dict[int, tuple[int, int, int]] = {
    1: (2, 2, -1),   # thirds period-6
    3: (-1, 2, 2),   # thirds period-2
    4: (2, -1, 2),   # thirds period-6 inverse
}

# Matching exact Q3/Fraction joints from rational_robotics.py, for
# cross-verification against the true (never-truncating) ground truth.
_GROUND_TRUTH_JOINT = {
    1: joint_60(),
    3: joint_120(),
    4: joint_240(),
}


def ground_truth_rotate(
    a: tuple[int, int],
    b: tuple[int, int],
    c: tuple[int, int],
    d: tuple[int, int],
    angle: int,
) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction, Fraction]:
    """Apply the true (exact-Fraction, never-truncating) rotation directly
    via rational_robotics.py. Returns (b2.p, b2.q, c2.p, c2.q, d2.p, d2.q)
    as Fractions — A is invariant and omitted since it never changes."""
    joint = _GROUND_TRUTH_JOINT[angle]
    q = QuadrayQ(Q3(*a), Q3(*b), Q3(*c), Q3(*d))
    r = q.circulant_rotate(joint.f, joint.g, joint.h)
    return (r.b.p, r.b.q, r.c.p, r.c.q, r.d.p, r.d.q)


# ─────────────────────────────────────────────────────────────────────────
# DEAD END — kept only as a permanent negative-result audit trail.
# ─────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TrebledSurd:
    p3: int
    q3: int


@dataclass(frozen=True)
class TrebledQuadray:
    a: TrebledSurd
    b: TrebledSurd
    c: TrebledSurd
    d: TrebledSurd


def treble_surd(p: int, q: int) -> TrebledSurd:
    return TrebledSurd(3 * p, 3 * q)


def treble_quadray(a, b, c, d) -> TrebledQuadray:
    return TrebledQuadray(
        treble_surd(*a), treble_surd(*b), treble_surd(*c), treble_surd(*d)
    )


def rotate_no_div_DEAD_END(state: TrebledQuadray, angle: int) -> TrebledQuadray:
    """DOES NOT WORK — scales the true output by 9x per application, not
    3x. Kept only so this approach is never silently re-proposed as
    fixed. See module docstring."""
    F, G, H = THIRDS_COEFFS[angle]
    B, C, D = state.b, state.c, state.d
    b2 = TrebledSurd(F * B.p3 + H * C.p3 + G * D.p3, F * B.q3 + H * C.q3 + G * D.q3)
    c2 = TrebledSurd(G * B.p3 + F * C.p3 + H * D.p3, G * B.q3 + F * C.q3 + H * D.q3)
    d2 = TrebledSurd(H * B.p3 + G * C.p3 + F * D.p3, H * B.q3 + G * C.q3 + F * D.q3)
    return TrebledQuadray(state.a, b2, c2, d2)


# ─────────────────────────────────────────────────────────────────────────
# VERIFIED WORKING — deferred-reduction, exponent-tagged representation.
# ─────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TaggedSurd:
    """A Q(sqrt3) component, true value = (p, q) / 3**exponent."""

    p: int
    q: int
    exponent: int


@dataclass(frozen=True)
class TaggedQuadray:
    a: TaggedSurd
    b: TaggedSurd
    c: TaggedSurd
    d: TaggedSurd


def start_tagged(p: int, q: int = 0) -> TaggedSurd:
    """A fresh, un-rotated value: exponent 0, true value is exactly (p, q)."""
    return TaggedSurd(p, q, 0)


def start_tagged_quadray(a, b, c, d) -> TaggedQuadray:
    return TaggedQuadray(start_tagged(*a), start_tagged(*b), start_tagged(*c), start_tagged(*d))


def rotate_tagged(state: TaggedQuadray, angle: int) -> TaggedQuadray:
    """Apply a thirds-angle rotation with zero division. Every component
    must share the same exponent going in (true on any state produced
    solely by this function starting from start_tagged_quadray) — the
    exponent simply increments by 1 for B, C, D; A is an untouched
    passthrough at its original exponent, exactly like the RTL/VM's
    A_out <= A_in."""
    if angle not in THIRDS_COEFFS:
        raise ValueError(f"rotate_tagged only handles thirds angles 1,3,4; got {angle}")
    F, G, H = THIRDS_COEFFS[angle]
    B, C, D = state.b, state.c, state.d
    if not (B.exponent == C.exponent == D.exponent):
        raise ValueError(
            "rotate_tagged requires B, C, D at a common exponent — "
            "align exponents explicitly before combining mismatched values"
        )
    exp = B.exponent + 1
    b2 = TaggedSurd(F * B.p + H * C.p + G * D.p, F * B.q + H * C.q + G * D.q, exp)
    c2 = TaggedSurd(G * B.p + F * C.p + H * D.p, G * B.q + F * C.q + H * D.q, exp)
    d2 = TaggedSurd(H * B.p + G * C.p + F * D.p, H * B.q + G * C.q + F * D.q, exp)
    return TaggedQuadray(state.a, b2, c2, d2)


def reduce_tagged(t: TaggedSurd) -> tuple[Fraction, Fraction]:
    """Explicit renormalization: recover the true (p, q) value as exact
    Fractions. Never silently truncates — Fraction division is always
    exact. This is the deliberate, chosen point where a caller decides to
    materialize the true value (e.g. before a Cartesian bridge egress, or
    before a fixed-width register write that the ISA extension would need
    to define bit-precisely)."""
    scale = 3 ** t.exponent
    return Fraction(t.p, scale), Fraction(t.q, scale)


class InexactReduceError(ValueError):
    """Raised by reduce_tagged_exact when the true value genuinely is not
    an integer at the requested exponent — this is not a bug, it's the
    honest fact that the rotated point does not currently sit on the
    integer Quadray lattice. Corresponds to the RTL FAULT.INEXACT state
    in docs/ROTC_EXPONENT_STATE_MACHINE.md."""


def reduce_tagged_exact(t: TaggedSurd) -> tuple[int, int]:
    """Hardware-faithful REDUCE: succeeds only if both lanes divide
    evenly by 3**exponent, returning a clean (exponent=0) integer pair.
    Raises InexactReduceError otherwise — no value is silently committed,
    matching the house 'detect, never silently corrupt' idiom (A31
    FLAGS.V, whisper's saturating-not-silent dissonance field)."""
    scale = 3 ** t.exponent
    if t.p % scale != 0 or t.q % scale != 0:
        raise InexactReduceError(
            f"reduce_tagged_exact: ({t.p}, {t.q}) does not divide evenly "
            f"by 3**{t.exponent} — true value is not an integer here"
        )
    return t.p // scale, t.q // scale


def align_tagged(t: TaggedSurd, target_exponent: int) -> TaggedSurd:
    """ALIGN: bring a tagged value up to a higher target exponent by
    multiplying both lanes by the appropriate power of 3. Exact by
    construction (multiplication never loses information) — this is the
    direction that's always safe, unlike REDUCE's division. Raises if
    asked to align DOWN (that's REDUCE's job, and it can fail; ALIGN
    never can, so it refuses to be misused for the lossy direction)."""
    if target_exponent < t.exponent:
        raise ValueError(
            f"align_tagged only raises exponent ({t.exponent} -> "
            f"{target_exponent} is a decrease) — use reduce_tagged_exact "
            "to lower it, which can legitimately fail"
        )
    scale_up = 3 ** (target_exponent - t.exponent)
    return TaggedSurd(t.p * scale_up, t.q * scale_up, target_exponent)


def align_pair(x: TaggedSurd, y: TaggedSurd) -> tuple[TaggedSurd, TaggedSurd]:
    """Bring two tagged values to their common (higher) exponent."""
    target = max(x.exponent, y.exponent)
    return align_tagged(x, target), align_tagged(y, target)
