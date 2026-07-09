#!/usr/bin/env python3
"""Tests for the Cartesian bridge sensor/legacy boundary oracle.

Contract: docs/CARTESIAN_BRIDGE_SPEC.md. Exercises the §5 acceptance
checklist directly: round-trip error bound, saturation behavior, the
q=0 invariant, scalar/surd confusion detection, round-half-to-even at
an actual midpoint, and direct type compatibility with
rational_som.find_bmu (no adapter code).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.cartesian_bridge import (
    P_MAX,
    P_MIN,
    Q12_SCALE,
    dequantize_scalar,
    dequantize_surd,
    quantize_feature_vector,
    quantize_scalar,
)
from lib.rational_som import RationalSurd, find_bmu, tiny_hex_fixture

PASS = 0
FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {label}")


def test_round_trip_within_half_lsb():
    scale = Q12_SCALE
    for value in (0.0, 1.5, -1.5, 3.14159, -7.999, 6627 / scale):  # phi-ish
        result = quantize_scalar(value, scale)
        back = dequantize_scalar(result.value, scale)
        check(
            f"round-trip {value} within 1/(2*scale)",
            abs(back - value) <= 1.0 / (2 * scale) + 1e-12,
        )
        check(f"error field matches for {value}", abs(result.error - (back - value)) < 1e-12)


def test_saturation_never_silent_never_raises():
    scale = 1  # tiny scale so ordinary values saturate easily
    huge = quantize_scalar(1e9, scale)
    check("huge positive value saturates", huge.saturated is True)
    check("huge positive clamps to P_MAX", huge.value.p == P_MAX)

    tiny = quantize_scalar(-1e9, scale)
    check("huge negative value saturates", tiny.saturated is True)
    check("huge negative clamps to P_MIN", tiny.value.p == P_MIN)

    normal = quantize_scalar(5.0, Q12_SCALE)
    check("in-range value does not saturate", normal.saturated is False)


def test_q_zero_invariant():
    for value in (0.0, 100.0, -100.0, 0.0001):
        result = quantize_scalar(value, Q12_SCALE)
        check(f"q==0 for scalar quantize of {value}", result.value.q == 0)


def test_dequantize_scalar_rejects_nonzero_q():
    raised = False
    try:
        dequantize_scalar(RationalSurd(4, 1), Q12_SCALE)
    except ValueError:
        raised = True
    check("dequantize_scalar raises on q != 0", raised)


def test_dequantize_surd_evaluates_root_three():
    import math

    rs = RationalSurd(2 * Q12_SCALE, 1 * Q12_SCALE)  # 2 + 1*sqrt(3)
    got = dequantize_surd(rs, Q12_SCALE)
    want = 2.0 + math.sqrt(3)
    check("dequantize_surd evaluates P/scale + (Q/scale)*sqrt(3)", abs(got - want) < 1e-9)


def test_round_half_to_even_at_midpoint():
    # Choose scale=1 so value*scale lands exactly on a half-integer.
    # 2.5 -> banker's rounding -> 2 (round to even)
    r1 = quantize_scalar(2.5, 1)
    check("round-half-to-even: 2.5 -> 2", r1.value.p == 2)
    # 3.5 -> banker's rounding -> 4 (round to even)
    r2 = quantize_scalar(3.5, 1)
    check("round-half-to-even: 3.5 -> 4", r2.value.p == 4)


def test_feature_vector_feeds_find_bmu_directly():
    nodes, feature_weights = tiny_hex_fixture()
    # Raw "sensor" floats for a 4-channel feature vector.
    raw = [2.0, 1.0, 0.0, 0.0]
    results = quantize_feature_vector(raw, scale=1)
    features = [r.value for r in results]

    # No adapter — feed straight into the existing SOM oracle.
    bmu = find_bmu(features, nodes, feature_weights)
    check("quantized feature vector is valid input to find_bmu", bmu.valid)
    check("quantized feature vector produces same BMU as raw rs() features",
          bmu.best_node_id == 1)


def test_invalid_scale_rejected():
    for fn, arg in (
        (quantize_scalar, (1.0, 0)),
        (dequantize_scalar, (RationalSurd(0, 0), -1)),
        (dequantize_surd, (RationalSurd(0, 0), 0)),
    ):
        raised = False
        try:
            fn(*arg)
        except ValueError:
            raised = True
        check(f"{fn.__name__} rejects non-positive scale", raised)


def main():
    test_round_trip_within_half_lsb()
    test_saturation_never_silent_never_raises()
    test_q_zero_invariant()
    test_dequantize_scalar_rejects_nonzero_q()
    test_dequantize_surd_evaluates_root_three()
    test_round_half_to_even_at_midpoint()
    test_feature_vector_feeds_find_bmu_directly()
    test_invalid_scale_rejected()

    if FAIL:
        print(f"FAIL ({FAIL} failures, {PASS} passes)")
        return 1
    print(f"PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
