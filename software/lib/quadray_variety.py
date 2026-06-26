"""Exact M31 Quadray variety oracle.

This module models the division-free SQR constraint used by the RPLU
pipeline sidecar:

    Q(A,B,C,D) - kappa == 0 mod M31

where Q is the six pairwise squared component differences already used by
software/common/include/spu_quadray.h.
"""

from __future__ import annotations

from typing import Sequence, Tuple


P_M31 = (1 << 31) - 1
Jet2 = Tuple[int, int, int]


def m31(x: int) -> int:
    return x % P_M31


def m31_add(a: int, b: int) -> int:
    return (a + b) % P_M31


def m31_sub(a: int, b: int) -> int:
    return (a - b) % P_M31


def m31_mul(a: int, b: int) -> int:
    return (a * b) % P_M31


def quadray_quadrance(coords: Sequence[int]) -> int:
    """Return sum_{i<j} (coords[i] - coords[j])^2 in M31."""
    if len(coords) != 4:
        raise ValueError("Quadray coordinates must have exactly four lanes")

    total = 0
    for i in range(4):
        for j in range(i + 1, 4):
            diff = m31_sub(coords[i], coords[j])
            total = m31_add(total, m31_mul(diff, diff))
    return total


def quadray_delta(coords: Sequence[int], target_kappa: int) -> int:
    return m31_sub(quadray_quadrance(coords), target_kappa)


def quadray_coherent(coords: Sequence[int], target_kappa: int) -> bool:
    return quadray_delta(coords, target_kappa) == 0


def jet2(a0: int, a1: int = 0, a2: int = 0) -> Jet2:
    return (m31(a0), m31(a1), m31(a2))


def jet2_add(a: Jet2, b: Jet2) -> Jet2:
    return (
        m31_add(a[0], b[0]),
        m31_add(a[1], b[1]),
        m31_add(a[2], b[2]),
    )


def jet2_sub(a: Jet2, b: Jet2) -> Jet2:
    return (
        m31_sub(a[0], b[0]),
        m31_sub(a[1], b[1]),
        m31_sub(a[2], b[2]),
    )


def jet2_mul(a: Jet2, b: Jet2) -> Jet2:
    """Cauchy product in M31[eps]/(eps^3)."""
    c0 = m31_mul(a[0], b[0])
    c1 = m31_add(m31_mul(a[0], b[1]), m31_mul(a[1], b[0]))
    c2 = m31_add(
        m31_add(m31_mul(a[0], b[2]), m31_mul(a[1], b[1])),
        m31_mul(a[2], b[0]),
    )
    return (c0, c1, c2)


def quadray_jet_delta(
    a: Jet2,
    b: Jet2,
    c: Jet2,
    d: Jet2,
    target_kappa: int,
) -> Jet2:
    """Return the n=2 jet residual of the Quadray variety."""
    coords = (a, b, c, d)
    total = jet2(0)
    for i in range(4):
        for j in range(i + 1, 4):
            diff = jet2_sub(coords[i], coords[j])
            total = jet2_add(total, jet2_mul(diff, diff))
    return jet2_sub(total, jet2(target_kappa))
