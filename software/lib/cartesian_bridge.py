"""
cartesian_bridge.py — sensor/legacy boundary oracle.

Contract: docs/CARTESIAN_BRIDGE_SPEC.md. Converts real-world float sensor
readings into RationalSurd (Q(sqrt(3)) exact values, Q=0 for plain scalar
channels) on ingest, and back to plain floats for legacy/display
consumption on egress. This is the one place in the pipeline where
"exact" means "deterministic and bounded," not "lossless" — see the
contract doc before changing any rounding/saturation behavior here.

No floating point in the exact pipeline itself; floats only ever appear
at the two edges (raw sensor input, legacy display output).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from lib.rational_som import RationalSurd

P_MIN = -32768
P_MAX = 32767

# Named scale presets matching existing SPU conventions (SQR rotor Q12).
Q12_SCALE = 4096


@dataclass(frozen=True)
class QuantizeResult:
    """Result of quantizing one float sensor reading."""

    value: RationalSurd
    saturated: bool
    error: float  # exact rounding residual: dequantize(value) - original


def quantize_scalar(value: float, scale: int) -> QuantizeResult:
    """Quantize a plain scalar sensor reading to a RationalSurd (q=0).

    Round-half-to-even (Python's native round()), clamped to the
    hardware's signed 16-bit P bound. Never raises on out-of-range input
    — saturates and reports it, per the contract's "never silent, never
    crash" rule (a sensor spike is exactly when the monitor must keep
    running).
    """
    if scale <= 0:
        raise ValueError("scale must be a positive integer")

    raw = round(value * scale)
    saturated = False
    if raw > P_MAX:
        raw = P_MAX
        saturated = True
    elif raw < P_MIN:
        raw = P_MIN
        saturated = True

    rs = RationalSurd(raw, 0)
    error = (raw / scale) - value
    return QuantizeResult(value=rs, saturated=saturated, error=error)


def dequantize_scalar(rs: RationalSurd, scale: int) -> float:
    """Egress for a plain scalar value. Requires q == 0 — a nonzero surd
    component here is a caller bug (scalar/surd confusion), not data to
    silently coerce."""
    if scale <= 0:
        raise ValueError("scale must be a positive integer")
    if rs.q != 0:
        raise ValueError(
            f"dequantize_scalar called on a non-scalar RationalSurd "
            f"(q={rs.q} != 0) — use dequantize_surd for general values"
        )
    return rs.p / scale


def dequantize_surd(rs: RationalSurd, scale: int) -> float:
    """General egress: evaluates P/scale + (Q/scale)*sqrt(3) as a float.

    Display/legacy consumption only — this value must never be fed back
    into the exact pipeline. sqrt(3) is irrational; this is precisely
    the boundary where exactness ends by design.
    """
    if scale <= 0:
        raise ValueError("scale must be a positive integer")
    return (rs.p / scale) + (rs.q / scale) * math.sqrt(3)


def quantize_feature_vector(
    values: Sequence[float], scale: int
) -> list[QuantizeResult]:
    """Per-channel convenience: quantize a full sensor feature vector.

    The .value list of the result feeds rational_som.find_bmu()
    directly — no adapter needed, since quantize_scalar already produces
    the Sequence[RationalSurd] shape find_bmu expects.
    """
    return [quantize_scalar(v, scale) for v in values]
