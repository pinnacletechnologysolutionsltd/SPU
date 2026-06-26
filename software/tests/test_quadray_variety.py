#!/usr/bin/env python3
"""Tests for the exact M31 Quadray variety oracle."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.quadray_variety import (  # noqa: E402
    P_M31,
    jet2,
    quadray_coherent,
    quadray_delta,
    quadray_jet_delta,
    quadray_quadrance,
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


def check_eq(label, got, want):
    check(f"{label}: got {got!r}, want {want!r}", got == want)


def test_dynamic_shape_load_sequence():
    """Simulates firmware writing a target kappa to the BTU config bus (sel=6)."""

    # Dynamic shape load: firmware picks a target kappa that matches
    # a known Quadray coordinate set — the variety sidecar should
    # report coherent (delta == 0).
    coords_on_variety = (500, 250, 120, 80)
    target_kappa = quadray_quadrance(coords_on_variety)
    check(f"on-variety delta zero at kappa={target_kappa}",
          quadray_delta(coords_on_variety, target_kappa) == 0)
    check("on-variety coherent",
          quadray_coherent(coords_on_variety, target_kappa))

    # Re-probe with a different kappa — same coords should now be
    # off-variety (non-zero delta, not coherent).
    wrong_kappa = target_kappa - 1 if target_kappa > 0 else target_kappa + 1
    check(f"off-variety delta non-zero at kappa={wrong_kappa}",
          quadray_delta(coords_on_variety, wrong_kappa) != 0)
    check("off-variety not coherent",
          not quadray_coherent(coords_on_variety, wrong_kappa))

    # Zero coords at non-zero kappa: must be off-variety (delta = -kappa mod M31)
    check_eq("origin at non-zero kappa delta wraps",
             quadray_delta((0, 0, 0, 0), 143250), P_M31 - 143250)

    # Firmware re-loads kappa to 0 — origin should be coherent again
    check("origin re-coherent at kappa=0",
          quadray_coherent((0, 0, 0, 0), 0))

    # Jet variety: a constant-velocity jet on-variety should stay on-variety
    a = jet2(100, 3, 1)
    b = jet2(50,  3, 1)
    c = jet2(25,  3, 1)
    d = jet2(15,  3, 1)
    k = quadray_quadrance([a[0], b[0], c[0], d[0]])
    jet_delta = quadray_jet_delta(a, b, c, d, k)
    check("jet on-variety has zero position residual", jet_delta[0] == 0)


def test_scalar_variety():
    check_eq("origin quadrance", quadray_quadrance((0, 0, 0, 0)), 0)
    check("origin coherent at kappa 0", quadray_coherent((0, 0, 0, 0), 0))

    check_eq("single axis quadrance", quadray_quadrance((1, 0, 0, 0)), 3)
    check("single axis coherent at kappa 3", quadray_coherent((1, 0, 0, 0), 3))

    check_eq("two-axis quadrance", quadray_quadrance((1, 1, 0, 0)), 4)
    check("two-axis coherent at kappa 4", quadray_coherent((1, 1, 0, 0), 4))

    check_eq("off-variety delta wraps", quadray_delta((1, 0, 0, 0), 4), P_M31 - 1)
    check_eq("negative residue squares exactly", quadray_quadrance((P_M31 - 1, 0, 0, 0)), 3)


def test_jet_variety():
    check_eq(
        "static jet on variety",
        quadray_jet_delta(jet2(1), jet2(0), jet2(0), jet2(0), 3),
        jet2(0),
    )

    check_eq(
        "axis velocity residual",
        quadray_jet_delta(jet2(1, 1), jet2(0), jet2(0), jet2(0), 3),
        jet2(0, 6, 3),
    )

    check_eq(
        "shared translation cancels",
        quadray_jet_delta(jet2(2, 5, 7), jet2(1, 5, 7), jet2(1, 5, 7), jet2(1, 5, 7), 3),
        jet2(0),
    )


def main():
    test_scalar_variety()
    test_jet_variety()
    test_dynamic_shape_load_sequence()

    if FAIL:
        print(f"FAIL ({FAIL} failures, {PASS} passes)")
        return 1
    print(f"PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
