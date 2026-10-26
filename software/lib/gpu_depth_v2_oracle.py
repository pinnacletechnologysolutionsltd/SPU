"""Independent bit-exact oracle for depth-v2: affine-interpolated per-pixel
depth, the minimal consumer proposed to pin down the reciprocal interface
in spu_strategy/contract_gpu_reciprocal_scoping_2026-08-25.md (see its
addendum 3b).

Pipeline modeled (matches the real ~25-bit denominator the RTL would see,
NOT the idealized already-16-bit-mantissa domain gpu_reciprocal_oracle.py
characterized in isolation):

  vertices + per-vertex depth
    -> edge coefficients (a,b,c), same convention spu_edge_stepper.v uses
    -> D = F0+F1+F2 (constant per triangle, twice signed area)
    -> full_reciprocal(D): normalize (real bit truncation, NOT exact --
       see finding below) -> LUT -> 1 NR iteration -> denormalize
    -> A_z,B_z,C_z: one multiply each against inv_D (setup-time only)
    -> per-pixel z: pure incremental accumulator, same shape as
       spu_edge_stepper.v's f/f_row (no per-pixel multiply or divide)

FINDING (corrects an overclaim in the reciprocal contract's §2 point 1):
"the shift is exact, no rounding" is true for denormalizing the RESULT,
but normalizing a wide D (up to ~25 bits, per the reciprocal contract's
domain evidence) down to a 16-bit mantissa for the LUT is a real
right-shift-and-truncate -- it discards D's low bits. That is an
additional error source on top of the core's own characterized ~15-bit
precision, not covered by the earlier 16-bit-mantissa-only sweep.
characterize_full_reciprocal() below quantifies it exhaustively.
"""

from fractions import Fraction
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gpu_reciprocal_oracle import reciprocal_core, MANTISSA_BITS, LUT_INDEX_BITS, OUT_FRAC_BITS


# ---------------------------------------------------------------------------
# Edge coefficients from vertices (spu_edge_stepper.v convention: a,b,c such
# that inside <=> a*x + b*y + c >= 0). Derivation kept local since no shared
# vertex->edge utility exists in the repo yet -- this is scoping, not a new
# generic module.
# ---------------------------------------------------------------------------

def edge_coeffs(p, q):
    """Edge function for the directed edge p->q: a*x + b*y + c, positive
    on the left of p->q. a = p.y-q.y, b = q.x-p.x, c = p.x*q.y - p.y*q.x."""
    px, py = p
    qx, qy = q
    a = py - qy
    b = qx - px
    c = px * qy - py * qx
    return a, b, c


def triangle_edges(v0, v1, v2):
    """edge0 opposite v0 (v1->v2), edge1 opposite v1 (v2->v0), edge2
    opposite v2 (v0->v1). Self-checks the sum-of-edges-is-constant
    identity at build time -- a real computed check, not an assumption."""
    e0 = edge_coeffs(v1, v2)
    e1 = edge_coeffs(v2, v0)
    e2 = edge_coeffs(v0, v1)

    def f(e, x, y):
        a, b, c = e
        return a * x + b * y + c

    shoelace2 = (v1[0] - v0[0]) * (v2[1] - v0[1]) - (v2[0] - v0[0]) * (v1[1] - v0[1])
    samples = [v0, v1, v2, (v0[0] + 3, v0[1] - 7), ((v0[0] + v1[0] + v2[0]) // 3,
                                                     (v0[1] + v1[1] + v2[1]) // 3)]
    for (x, y) in samples:
        total = f(e0, x, y) + f(e1, x, y) + f(e2, x, y)
        assert total == shoelace2, (
            f"sum-of-edges identity broken: got {total}, expected {shoelace2} "
            f"at ({x},{y}) -- HALT, convention error, not an oracle bug to paper over"
        )
    return e0, e1, e2, shoelace2


# ---------------------------------------------------------------------------
# Full reciprocal: normalize (real truncation) -> core -> denormalize.
# ---------------------------------------------------------------------------

def full_reciprocal(d, mant_bits=MANTISSA_BITS, table_bits=LUT_INDEX_BITS,
                     out_frac=OUT_FRAC_BITS):
    """d: positive integer of arbitrary width. Returns (y, exp) such that
    1/d ~= y / 2**exp, using only the characterized multiply-only core plus
    exact bit shifts. The normalize step truncates d's low bits when d is
    wider than mant_bits -- that truncation is real and is NOT covered by
    the core's own isolated characterization."""
    assert d > 0
    msb_pos = d.bit_length() - 1
    shift = msb_pos - (mant_bits - 1)          # >0 for d wider than mant_bits
    mant = d >> shift if shift >= 0 else d << (-shift)
    y = reciprocal_core(mant, table_bits, mant_bits, out_frac)
    exp = mant_bits + out_frac + shift
    return y, exp


def characterize_full_reciprocal(max_extra_shift=9, mant_bits=MANTISSA_BITS,
                                  table_bits=LUT_INDEX_BITS, out_frac=OUT_FRAC_BITS):
    """Exhaustive worst-case sweep: for every mantissa value (32768 of
    them, exhaustive) and every possible truncated-bit-count up to
    max_extra_shift (covering denominators up to mant_bits+max_extra_shift
    bits wide -- 16+9=25 bits, matching the reciprocal contract's domain
    evidence for a 640x480 screen), evaluate the WORST-CASE real d that
    would normalize to that mantissa (all truncated low bits = 1) against
    the exact reciprocal. This is a true worst-case bound via exhaustive
    search over the only degrees of freedom that matter, not a sampled
    guess."""
    results = {}
    for extra_shift in range(max_extra_shift + 1):
        max_rel = 0.0
        worst_d = None
        for mant in range(1 << (mant_bits - 1), 1 << mant_bits):
            y = reciprocal_core(mant, table_bits, mant_bits, out_frac)
            d_worst = (mant << extra_shift) + (1 << extra_shift) - 1
            exact = Fraction(1, d_worst)
            got = Fraction(y, 1 << (mant_bits + out_frac + extra_shift))
            rel = abs(got - exact) / exact
            if rel > max_rel:
                max_rel, worst_d = rel, d_worst
        results[extra_shift] = (max_rel, worst_d)
    return results


# ---------------------------------------------------------------------------
# depth-v2: affine-interpolated depth, setup-time reciprocal, per-pixel
# incremental accumulation (no per-pixel multiply/divide).
# ---------------------------------------------------------------------------

def depth_interp_setup(v0, v1, v2, z0, z1, z2, out_frac=OUT_FRAC_BITS):
    """Returns fixed-point (A_z, B_z, C_z, frac_bits) such that the
    per-pixel accumulator z_accum(x,y) = (A_z*x + B_z*y + C_z) >> frac_bits
    approximates the exact affine-interpolated depth, computed with a
    SINGLE reciprocal at setup (not per pixel)."""
    e0, e1, e2, D = triangle_edges(v0, v1, v2)
    assert D != 0, "degenerate triangle"
    sign = 1 if D > 0 else -1
    y_recip, exp = full_reciprocal(abs(D), out_frac=out_frac)

    a0, b0, c0 = e0
    a1, b1, c1 = e1
    a2, b2, c2 = e2
    Sa = a0 * z0 + a1 * z1 + a2 * z2
    Sb = b0 * z0 + b1 * z1 + b2 * z2
    Sc = c0 * z0 + c1 * z1 + c2 * z2

    # (Sa,Sb,Sc) * (1/D) ~= (Sa,Sb,Sc) * sign * y_recip / 2**exp
    A_z = Sa * sign * y_recip
    B_z = Sb * sign * y_recip
    C_z = Sc * sign * y_recip
    return A_z, B_z, C_z, exp


def simulate_depth_raster(v0, v1, v2, z0, z1, z2, out_frac=OUT_FRAC_BITS):
    """Scans the triangle's bounding box; at each pixel computes the
    fixed-point interpolated depth via pure incremental add (same shape as
    spu_edge_stepper.v: seed C_z at row start, += A_z per step_x, += B_z
    per step_y), compared against the exact rational affine interpolation.
    Returns max absolute depth error (in the same units as z0/z1/z2) and
    the (x,y) where it occurred."""
    e0, e1, e2, D = triangle_edges(v0, v1, v2)
    A_z, B_z, C_z, frac_bits = depth_interp_setup(v0, v1, v2, z0, z1, z2, out_frac)

    xs = [v0[0], v1[0], v2[0]]
    ys = [v0[1], v1[1], v2[1]]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    def inside(x, y):
        def f(e):
            a, b, c = e
            return a * x + b * y + c
        vals = [f(e0), f(e1), f(e2)]
        return all(v >= 0 for v in vals) or all(v <= 0 for v in vals)

    max_err = 0.0
    worst_xy = None
    row = C_z + A_z * x_min + B_z * y_min
    for y in range(y_min, y_max + 1):
        acc = row
        for x in range(x_min, x_max + 1):
            if inside(x, y):
                approx_z = acc >> frac_bits if acc >= 0 else -((-acc) >> frac_bits)
                exact_num = e0[0] * x + e0[1] * y + e0[2]
                exact_z = Fraction(
                    (e0[0] * x + e0[1] * y + e0[2]) * z0
                    + (e1[0] * x + e1[1] * y + e1[2]) * z1
                    + (e2[0] * x + e2[1] * y + e2[2]) * z2,
                    D,
                )
                err = abs(Fraction(approx_z) - exact_z)
                if err > max_err:
                    max_err = err
                    worst_xy = (x, y)
            acc += A_z
        row += B_z
    return float(max_err), worst_xy, frac_bits


if __name__ == "__main__":
    print("=== Full reciprocal worst-case (mantissa truncation + NR core) ===")
    results = characterize_full_reciprocal()
    for extra_shift, (max_rel, worst_d) in results.items():
        d_bits = MANTISSA_BITS + extra_shift
        import math
        bits = -math.log2(max_rel)
        print(f"  denominator width {d_bits:2d} bits (extra_shift={extra_shift}): "
              f"max_rel={max_rel:.3e}  ~{bits:.1f} correct bits")

    print()
    print("=== depth-v2 affine interpolation, representative triangles ===")
    cases = [
        ("small, screen-corner", (10, 10), (600, 30), (300, 460), 0, 65535, 32768),
        ("thin sliver", (10, 10), (630, 12), (320, 470), 1000, 60000, 30000),
        ("near-degenerate", (0, 0), (639, 1), (320, 479), 0, 65535, 40000),
    ]
    for name, v0, v1, v2, z0, z1, z2 in cases:
        err, worst_xy, frac_bits = simulate_depth_raster(v0, v1, v2, z0, z1, z2)
        print(f"  {name}: max depth error = {err:.4f} (16-bit depth units), "
              f"worst pixel {worst_xy}, frac_bits={frac_bits}")
