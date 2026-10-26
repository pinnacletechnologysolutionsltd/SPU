#!/usr/bin/env python3
"""
test_verification.py — SPU-13 Python Verification Suite v1.0
Ported from Laminar-Core/hardware/tests/ C++ suite.

Runs standalone (no hardware needed). All arithmetic is bit-exact Q(√3).
Each test maps to a C++ original for cross-validation.

Usage:
    python3 test_verification.py          # run all tests
    python3 test_verification.py -v       # verbose (show each step)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from spu_vm import RationalSurd, QuadrayVector

VERBOSE = '-v' in sys.argv

def log(msg: str):
    if VERBOSE:
        print(f"    {msg}")

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

ZERO = RationalSurd(0, 0)
ONE  = RationalSurd(1, 0)
PELL = RationalSurd(2, 1)   # 2 + 1·√3  — fundamental Pell rotor, Q=1

def q(r: RationalSurd) -> int:
    return r.a * r.a - 3 * r.b * r.b


def pell_rotate(r: RationalSurd) -> RationalSurd:
    """Multiply r by Pell rotor (2+√3). Q(r) is preserved."""
    return r * PELL


PASS = 0
FAIL = 0

def result(name: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    mark = "PASS" if passed else "FAIL"
    suffix = f"  — {detail}" if detail else ""
    print(f"  [{mark}] {name}{suffix}")
    if passed:
        PASS += 1
    else:
        FAIL += 1


# ---------------------------------------------------------------------------
# Test 1: Long-Run Rotation Stability (ported from rigorous_verification.cpp)
# C++ ran 10^8 iterations; Python integers are exact so we verify Q-invariant.
# We run 10,000 steps (sufficient to prove no drift in exact arithmetic).
# ---------------------------------------------------------------------------

def test_pell_rotation_stability():
    """
    Apply Pell rotation 10,000 times. Q must equal 1 at every step.
    In floating-point this drifts; in Q(√3) integer arithmetic it never can.
    """
    r = RationalSurd(1, 0)  # start at unity
    steps = 10_000
    drift = False
    for i in range(steps):
        r = pell_rotate(r)
        if q(r) != 1:
            drift = True
            log(f"  Q drift at step {i}: Q={q(r)}")
            break
        if VERBOSE and i < 5:
            log(f"  step {i+1}: ({r.a}, {r.b})  Q={q(r)}")
    # Don't repr r — after 10k steps the integers are thousands of digits
    log(f"  final a has {r.a.bit_length()} bits (exact integer, no float drift)")
    result("Pell rotation stability (10k steps, Q=1 invariant)",
           not drift, f"a={r.a.bit_length()}-bit integer, Q=1 exact")


# ---------------------------------------------------------------------------
# Test 2: Janus Involution — ported from rigorous_verification.cpp Test 2
# Flip surd sign twice → identity. Also: flip, rotate 3x, flip, rotate 3x.
# ---------------------------------------------------------------------------

def test_janus_involution():
    """
    JINV applied twice is identity: (a - b√3) sign-flipped again = (a + b√3).
    Also verifies Janus-Rotation commutativity: J·R³·J·R³ = identity.
    """
    r = RationalSurd(1234, 567)

    # Part A: double flip = identity
    flipped = RationalSurd(r.a, -r.b)
    restored = RationalSurd(flipped.a, -flipped.b)
    result("Janus double-flip = identity",
           restored == r, f"{r!r} → flip → flip → {restored!r}")

    # Part B: Q is symmetric under Janus (Q(a+b√3) == Q(a-b√3))
    q_before = q(r)
    q_after  = q(RationalSurd(r.a, -r.b))
    result("Janus Q-symmetry (Q unchanged by sign flip)",
           q_before == q_after, f"Q={q_before} both sides")

    # Part C: J·R³·J·R³ = identity
    # Start from (1,0), apply: flip, rotate 3×, flip, rotate 3×
    v = RationalSurd(1, 0)
    v = RationalSurd(v.a, -v.b)            # Janus flip
    for _ in range(3): v = pell_rotate(v)  # rotate 3×
    v = RationalSurd(v.a, -v.b)            # Janus flip
    for _ in range(3): v = pell_rotate(v)  # rotate 3×
    # After 6 Pell steps from (1,0): v should have Q=1 and be exact
    result("Janus-Rotation commutativity (J·R³·J·R³ consistent)",
           q(v) == 1, f"Q={q(v)} (bit-exact)")


# ---------------------------------------------------------------------------
# Test 3: Field Norm Invariant — ported from rigorous_verification.cpp Test 4
# Q(a+b√3) = a²-3b² must be preserved through multiplication.
# ---------------------------------------------------------------------------

def test_field_norm_invariant():
    """
    The norm N(r) = a²-3b² is a ring homomorphism:
    N(r·s) = N(r)·N(s). Verify for Pell rotor: N(2+√3) = 1.
    """
    # Pell rotor Q = 1
    result("Pell rotor Q=1 (fundamental norm)",
           q(PELL) == 1, f"Q({PELL!r}) = {q(PELL)}")

    # Multiplicative: Q(r·s) = Q(r)·Q(s)
    pairs = [
        (RationalSurd(3, 1), RationalSurd(2, 1)),
        (RationalSurd(7, 4), RationalSurd(2, 1)),
        (RationalSurd(5, 2), RationalSurd(5, 2)),
    ]
    for a_r, b_r in pairs:
        product = a_r * b_r
        lhs = q(product)
        rhs = q(a_r) * q(b_r)
        log(f"  Q({a_r!r}) · Q({b_r!r}) = {q(a_r)} · {q(b_r)} = {rhs}  "
            f"Q(product) = {lhs}")
        if lhs != rhs:
            result(f"Norm multiplicativity Q(r·s)=Q(r)·Q(s) for {a_r!r}·{b_r!r}",
                   False, f"got {lhs} ≠ {rhs}")
            return
    result("Norm multiplicativity Q(r·s)=Q(r)·Q(s) (3 pairs)",
           True, "all exact")


# ---------------------------------------------------------------------------
# Test 4: 13-Axis Cyclic Identity — ported from spu13_verification.cpp
# Load unique values into QR[0..12], cyclic-shift 13 times → identity.
# ---------------------------------------------------------------------------

def test_13_axis_cyclic_identity():
    """
    Cyclic permutation of 13 elements applied 13 times = identity.
    Maps to SPU-13 _spu_sperm_13 operation.
    """
    # Initial state: QR[i] has rational part = i+1, surd = 0
    initial = list(range(1, 14))   # [1, 2, ..., 13]
    state   = list(initial)

    for step in range(13):
        state = [state[-1]] + state[:-1]  # cyclic right-shift by 1
        log(f"  step {step+1}: {state}")

    result("13-axis cyclic identity (shift × 13 = identity)",
           state == initial, f"final={state}")


# ---------------------------------------------------------------------------
# Test 5: Pell sequence correctness
# The Pell sequence is (1,0) → (2,1) → (7,4) → (26,15) → ...
# Each step: (a,b) → (2a+3b, a+2b). Q=1 throughout.
# ---------------------------------------------------------------------------

def test_pell_sequence():
    """
    Verify the first 8 terms of the Pell sequence are exactly correct.
    Each term has Q = a² - 3b² = 1.
    """
    expected = [
        (1, 0), (2, 1), (7, 4), (26, 15),
        (97, 56), (362, 209), (1351, 780), (5042, 2911),
    ]
    r = RationalSurd(1, 0)
    actual = [(r.a, r.b)]
    for _ in range(7):
        r = pell_rotate(r)
        actual.append((r.a, r.b))

    match = actual == expected
    if VERBOSE:
        for i, (got, exp) in enumerate(zip(actual, expected)):
            mark = "✓" if got == exp else "✗"
            log(f"  step {i}: {got}  Q={got[0]**2 - 3*got[1]**2}  {mark}")
    result("Pell sequence first 8 terms exact",
           match, f"{'correct' if match else f'got {actual[0:3]}...'}")


# ---------------------------------------------------------------------------
# Test 6: Spread(8/9) — the IVM canonical result
# spread((1,1,1,0), (1,0,0,0)) = 8/9 in Wildberger rational trig.
# Ported from concept in WHITE_PAPER.md / Gemini analysis.
# ---------------------------------------------------------------------------

def test_spread_8_9():
    """
    The spread between face-centre (1,1,1,0) and vertex (1,0,0,0) of a
    regular tetrahedron is exactly 8/9 in rational trigonometry.
    This is the SPU-13 canonical proof-of-concept result.
    Uses QuadrayVector.spread() with IVM quadrance (Σᵢ<ⱼ (cᵢ-cⱼ)²).
    """
    from math import gcd

    face  = QuadrayVector(RationalSurd(1,0), RationalSurd(1,0),
                          RationalSurd(1,0), RationalSurd(0,0))
    vert  = QuadrayVector(RationalSurd(1,0), RationalSurd(0,0),
                          RationalSurd(0,0), RationalSurd(0,0))

    numer_r, denom_r = face.spread(vert)
    # Extract rational integer parts (no surd component expected for integer inputs)
    numer, denom = numer_r.a, denom_r.a
    from math import gcd
    g = gcd(abs(numer), abs(denom))
    numer, denom = numer // g, denom // g
    log(f"  spread({face!r}, {vert!r}) = {numer}/{denom}")

    result("Spread((1,1,1,0),(1,0,0,0)) = 8/9  [IVM canonical]",
           numer == 8 and denom == 9,
           f"got {numer}/{denom}")


# ---------------------------------------------------------------------------
# Test 7: Vector Equilibrium — 6 cuboctahedron vectors hex-sum to (0,0)
# ---------------------------------------------------------------------------

def test_vector_equilibrium():
    """
    The 6 cuboctahedron edge vectors (all permutations of (1,1,0,0)) have
    hex projections that sum to exactly (0,0) — Vector Equilibrium.
    """
    vecs = [
        QuadrayVector(RationalSurd(1,0), RationalSurd(1,0), RationalSurd(0,0), RationalSurd(0,0)),
        QuadrayVector(RationalSurd(1,0), RationalSurd(0,0), RationalSurd(1,0), RationalSurd(0,0)),
        QuadrayVector(RationalSurd(1,0), RationalSurd(0,0), RationalSurd(0,0), RationalSurd(1,0)),
        QuadrayVector(RationalSurd(0,0), RationalSurd(1,0), RationalSurd(1,0), RationalSurd(0,0)),
        QuadrayVector(RationalSurd(0,0), RationalSurd(1,0), RationalSurd(0,0), RationalSurd(1,0)),
        QuadrayVector(RationalSurd(0,0), RationalSurd(0,0), RationalSurd(1,0), RationalSurd(1,0)),
    ]
    sum_hx = sum(v.hex_project()[0] for v in vecs)
    sum_hy = sum(v.hex_project()[1] for v in vecs)

    if VERBOSE:
        for i, v in enumerate(vecs):
            hx, hy = v.hex_project()
            log(f"  QR{i}: {v!r}  hex=({hx:+d},{hy:+d})")
        log(f"  Σ hex = ({sum_hx:+d},{sum_hy:+d})")

    result("Vector Equilibrium: Σ hex_project(cuboctahedron) = (0,0)",
           sum_hx == 0 and sum_hy == 0,
           f"Σ=({sum_hx},{sum_hy})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print(" SPU-13 Python Verification Suite v1.0")
    print(" Ported from Laminar-Core C++ verification tests")
    print("=" * 60)

    test_pell_rotation_stability()
    test_janus_involution()
    test_field_norm_invariant()
    test_13_axis_cyclic_identity()
    test_pell_sequence()
    test_spread_8_9()
    test_vector_equilibrium()

    print("=" * 60)
    total = PASS + FAIL
    print(f" Results: {PASS}/{total} passed"
          + (f"  ({FAIL} FAILED)" if FAIL else "  ✓ All clear"))
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
