#!/usr/bin/env python3
"""Tests for ROTC thirds-angle exactness fixes (root-cause research).

Contract: docs/ROTC_THIRDS_EXACTNESS_FIX.md.

Two things are tested here, deliberately:
1. That the "global trebled unit" idea is dead — it must NOT match
   ground truth, proving the negative result stays caught if anyone
   ever touches rotate_no_div_DEAD_END again.
2. That the exponent-tagged deferred-reduction representation IS exact,
   across the original counterexample, a broad sweep, explicit zero-sum
   cases, surd components, and — the case that broke every narrower
   mitigation — a multi-axis composition chain.
"""

import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.rotc_thirds_native import (
    THIRDS_COEFFS,
    InexactReduceError,
    align_pair,
    align_tagged,
    ground_truth_rotate,
    reduce_tagged,
    reduce_tagged_exact,
    rotate_no_div_DEAD_END,
    rotate_tagged,
    start_tagged,
    start_tagged_quadray,
    treble_quadray,
)

PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def test_dead_end_confirmed_dead():
    """rotate_no_div_DEAD_END must NOT match ground truth — if this ever
    starts passing, something has changed and the module's claim is
    stale; investigate before trusting either."""
    a, b, c, d = (1, 0), (1, 0), (1, 0), (-3, 0)
    trebled = treble_quadray(a, b, c, d)
    rotated = rotate_no_div_DEAD_END(trebled, 1)
    # Correct-if-trebled would require rotated.b.p3 == 3 * true_b_prime.
    # True b' = -5/3, so 3*b' = -5. Confirm the dead end gives something
    # else (it gives -15 = 9*b', not -5 = 3*b').
    check("dead end does NOT give the correctly-trebled value (-5)",
          rotated.b.p3 != -5)
    check("dead end reproduces its documented failure mode (9x scaling)",
          rotated.b.p3 == 9 * (Fraction(-5, 3)))


def test_tagged_original_counterexample():
    a, b, c, d = (1, 0), (1, 0), (1, 0), (-3, 0)
    state = start_tagged_quadray(a, b, c, d)
    for angle in (1, 3, 4):
        rotated = rotate_tagged(state, angle)
        got_b = reduce_tagged(rotated.b)
        got_c = reduce_tagged(rotated.c)
        got_d = reduce_tagged(rotated.d)
        gt = ground_truth_rotate(a, b, c, d, angle)
        check(f"tagged counterexample exact, angle {angle} (b)", got_b == (gt[0], gt[1]))
        check(f"tagged counterexample exact, angle {angle} (c)", got_c == (gt[2], gt[3]))
        check(f"tagged counterexample exact, angle {angle} (d)", got_d == (gt[4], gt[5]))


def test_broad_sweep_no_zero_sum_restriction():
    count = 0
    mismatches = 0
    for angle in THIRDS_COEFFS:
        for av in range(-3, 4):
            for bv in range(-3, 4):
                for cv in range(-3, 4):
                    for dv in range(-3, 4):
                        a, b, c, d = (av, 0), (bv, 0), (cv, 0), (dv, 0)
                        state = start_tagged_quadray(a, b, c, d)
                        rotated = rotate_tagged(state, angle)
                        got = (
                            reduce_tagged(rotated.b),
                            reduce_tagged(rotated.c),
                            reduce_tagged(rotated.d),
                        )
                        gt = ground_truth_rotate(a, b, c, d, angle)
                        want = ((gt[0], gt[1]), (gt[2], gt[3]), (gt[4], gt[5]))
                        count += 1
                        if got != want:
                            mismatches += 1
                            if mismatches <= 5:
                                check(
                                    f"sweep mismatch angle={angle} "
                                    f"a={av} b={bv} c={cv} d={dv}",
                                    False,
                                )
    check(f"broad sweep: all {count} cases exact (0 mismatches)", mismatches == 0)


def test_zero_sum_cases_including_negatives():
    zero_sum_cases = [
        (1, 1, 1, -3),
        (0, 0, 0, 0),
        (5, -2, -1, -2),
        (-7, 3, 2, 2),
        (10, 10, 10, -30),
        (-1, -1, -1, 3),
    ]
    for av, bv, cv, dv in zero_sum_cases:
        check(f"zero-sum check {(av, bv, cv, dv)}", av + bv + cv + dv == 0)
        a, b, c, d = (av, 0), (bv, 0), (cv, 0), (dv, 0)
        for angle in THIRDS_COEFFS:
            state = start_tagged_quadray(a, b, c, d)
            rotated = rotate_tagged(state, angle)
            got = (
                reduce_tagged(rotated.b),
                reduce_tagged(rotated.c),
                reduce_tagged(rotated.d),
            )
            gt = ground_truth_rotate(a, b, c, d, angle)
            want = ((gt[0], gt[1]), (gt[2], gt[3]), (gt[4], gt[5]))
            check(f"zero-sum exact {(av, bv, cv, dv)} angle {angle}", got == want)


def test_surd_components_nonzero_q():
    cases = [
        ((1, 2), (2, -1), (3, 0), (-6, -1)),
        ((0, 0), (1, 1), (-1, 1), (0, -2)),
        ((2, -3), (-1, 2), (0, 1), (-1, 0)),
    ]
    for a, b, c, d in cases:
        for angle in THIRDS_COEFFS:
            state = start_tagged_quadray(a, b, c, d)
            rotated = rotate_tagged(state, angle)
            got = (
                reduce_tagged(rotated.b),
                reduce_tagged(rotated.c),
                reduce_tagged(rotated.d),
            )
            gt = ground_truth_rotate(a, b, c, d, angle)
            want = ((gt[0], gt[1]), (gt[2], gt[3]), (gt[4], gt[5]))
            check(f"surd-component exact {(a, b, c, d)} angle {angle}", got == want)


def test_multiaxis_composition_chain():
    """The case that broke the narrow per-axis-residue mitigation AND the
    dead-end trebling idea: rotate about one axis, then rotate the
    RESULT through a different angle, repeatedly, and confirm the
    tagged representation stays exact throughout."""
    a, b, c, d = (1, 0), (1, 0), (1, 0), (-3, 0)
    state = start_tagged_quadray(a, b, c, d)
    chain = [1, 3, 4, 1]

    ga, gb, gc, gd = a, b, c, d
    for angle in chain:
        state = rotate_tagged(state, angle)
        res = ground_truth_rotate(ga, gb, gc, gd, angle)
        gb, gc, gd = (res[0], res[1]), (res[2], res[3]), (res[4], res[5])

        got_b = reduce_tagged(state.b)
        got_c = reduce_tagged(state.c)
        got_d = reduce_tagged(state.d)
        check(f"composition chain exact after angle {angle} (b)", got_b == gb)
        check(f"composition chain exact after angle {angle} (c)", got_c == gc)
        check(f"composition chain exact after angle {angle} (d)", got_d == gd)

    check("A invariant throughout composition chain",
          reduce_tagged(state.a) == (Fraction(a[0]), Fraction(a[1])))


def test_reduce_tagged_exact_success_and_fault():
    # angle-1 rotation of A=1,B=1,C=1,D=-3 gives true b'=-5/3 -- genuinely
    # not an integer, so REDUCE at exponent 1 must fault, not truncate.
    a, b, c, d = (1, 0), (1, 0), (1, 0), (-3, 0)
    state = start_tagged_quadray(a, b, c, d)
    rotated = rotate_tagged(state, 1)

    raised = False
    try:
        reduce_tagged_exact(rotated.b)
    except InexactReduceError:
        raised = True
    check("reduce_tagged_exact faults on genuinely non-integer true value", raised)

    # A whole angle-1 period is 6 -- rotating 6 times returns to the
    # original point, where the true value IS an integer again (the
    # guaranteed-safe reduction point from the state-machine contract).
    state2 = start_tagged_quadray(a, b, c, d)
    for _ in range(6):
        state2 = rotate_tagged(state2, 1)
    b_exact = reduce_tagged_exact(state2.b)
    c_exact = reduce_tagged_exact(state2.c)
    d_exact = reduce_tagged_exact(state2.d)
    check("REDUCE succeeds at period-6 closure (b)", b_exact == b)
    check("REDUCE succeeds at period-6 closure (c)", c_exact == c)
    check("REDUCE succeeds at period-6 closure (d)", d_exact == d)


def test_align_is_exact_and_matches_ground_truth():
    # Build two values with DIFFERENT rotation histories (different
    # exponents), align them to a common exponent, and confirm the
    # aligned values still reduce to the correct true values.
    from lib.rotc_thirds_native import TaggedSurd

    low = start_tagged(5, -2)          # exponent 0
    high_seed = start_tagged(5, -2)
    high = TaggedSurd(high_seed.p * 27, high_seed.q * 27, 3)  # same true value, exponent 3

    aligned_low = align_tagged(low, 3)
    check("align_tagged raises exponent correctly", aligned_low.exponent == 3)
    check("align_tagged preserves true value (p)",
          Fraction(aligned_low.p, 3 ** aligned_low.exponent) == Fraction(5))
    check("align_tagged preserves true value (q)",
          Fraction(aligned_low.q, 3 ** aligned_low.exponent) == Fraction(-2))
    check("aligned value matches independently-scaled equivalent",
          (aligned_low.p, aligned_low.q) == (high.p, high.q))

    x, y = align_pair(low, high_seed)
    check("align_pair brings both to the same exponent", x.exponent == y.exponent)


def test_align_never_lowers_exponent():
    from lib.rotc_thirds_native import TaggedSurd
    t = TaggedSurd(9, 0, 2)
    raised = False
    try:
        align_tagged(t, 1)
    except ValueError:
        raised = True
    check("align_tagged refuses to lower the exponent", raised)


def test_mismatched_exponent_rejected():
    from lib.rotc_thirds_native import TaggedQuadray, TaggedSurd

    bad_state = TaggedQuadray(
        TaggedSurd(1, 0, 0), TaggedSurd(1, 0, 0), TaggedSurd(1, 0, 1), TaggedSurd(1, 0, 0)
    )
    raised = False
    try:
        rotate_tagged(bad_state, 1)
    except ValueError:
        raised = True
    check("rotate_tagged rejects mismatched exponents", raised)


def main():
    test_dead_end_confirmed_dead()
    test_tagged_original_counterexample()
    test_broad_sweep_no_zero_sum_restriction()
    test_zero_sum_cases_including_negatives()
    test_surd_components_nonzero_q()
    test_multiaxis_composition_chain()
    test_reduce_tagged_exact_success_and_fault()
    test_align_is_exact_and_matches_ground_truth()
    test_align_never_lowers_exponent()
    test_mismatched_exponent_rejected()

    if FAIL:
        print(f"FAIL ({FAIL} failures, {PASS} passes)")
        return 1
    print(f"PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
