"""Independent bit-exact oracle for a multiply-only fixed-point reciprocal
core: normalize -> LUT initial estimate -> one Newton-Raphson refinement.

Scoping prototype for the SPU-13 GPU rasterizer's depth/texture
interpolation reciprocal (barycentric denominator = twice triangle area).
See spu_strategy/contract_gpu_reciprocal_scoping_2026-08-25.md.

This models exactly what the RTL will do: no `/` operator anywhere in
reciprocal_core() or build_lut() at runtime scale. The LUT is generated
here with a Python float divide, which is a build-time/generation-time
convenience (same pattern as tools/generate_pade_44.py) -- it produces a
constant table, not a runtime division.

Normalization (barrel-shifting an arbitrary-width denominator so its
leading 1 lands at a fixed bit position) is an exact bit operation with
no rounding error, so it is deliberately NOT part of what this oracle
characterizes -- only the core mantissa-domain reciprocal (normalize ->
LUT -> NR -> result) needs error characterization, and because the core
operates on a fixed-width mantissa regardless of the original
denominator's magnitude, its worst-case error can be swept EXHAUSTIVELY
(every mantissa value), not sampled.
"""

MANTISSA_BITS = 16   # normalized denominator width: d in [2**15, 2**16)
LUT_INDEX_BITS = 8    # top bits of the mantissa (below the implicit leading 1)
OUT_FRAC_BITS = 15    # output Q1.15-ish: result scaled by 2**OUT_FRAC_BITS


def build_lut(table_bits=LUT_INDEX_BITS, mant_bits=MANTISSA_BITS, out_frac=OUT_FRAC_BITS):
    """Generation-time ROM: for each table index, the reciprocal of the
    bucket's midpoint mantissa, rounded to an out_frac-bit fixed-point
    integer. Uses a float divide to BUILD the constant table only."""
    lead = 1 << (mant_bits - 1)
    shift = mant_bits - 1 - table_bits
    bucket_width = 1 << shift
    lut = []
    for idx in range(1 << table_bits):
        base = lead + (idx << shift)
        d_mid = base + bucket_width // 2
        v_mid = d_mid / float(1 << mant_bits)
        r_mid = 1.0 / v_mid
        lut.append(round(r_mid * (1 << out_frac)))
    return lut


_LUT = build_lut()


def reciprocal_core(d, table_bits=LUT_INDEX_BITS, mant_bits=MANTISSA_BITS,
                     out_frac=OUT_FRAC_BITS, lut=None):
    """d: normalized mantissa, 2**(mant_bits-1) <= d < 2**mant_bits.
    Returns an integer approximation of (2**mant_bits / d) * 2**out_frac,
    i.e. 1/v in Q(out_frac) where v = d / 2**mant_bits, using only
    multiply/subtract/shift -- no division."""
    if lut is None:
        lut = _LUT
    assert (1 << (mant_bits - 1)) <= d < (1 << mant_bits)

    shift = mant_bits - 1 - table_bits
    idx = (d - (1 << (mant_bits - 1))) >> shift
    y0 = lut[idx]                              # scale 2**out_frac

    # Newton-Raphson: y1 = y0 * (2 - v*y0), all multiply/subtract, fixed point.
    prod = d * y0                              # scale 2**(mant_bits+out_frac)
    two_fx = 2 << (mant_bits + out_frac)
    err = two_fx - prod                        # scale 2**(mant_bits+out_frac)
    y1_full = y0 * err                         # scale 2**(mant_bits+2*out_frac)
    y1 = y1_full >> (mant_bits + out_frac)      # back down to scale 2**out_frac
    return y1


def exact_scaled(d, mant_bits=MANTISSA_BITS, out_frac=OUT_FRAC_BITS):
    """Ground truth: (2**mant_bits / d) * 2**out_frac as an exact rational,
    for error measurement only -- never used in the RTL-modeled path."""
    from fractions import Fraction
    return Fraction(1 << (mant_bits + out_frac), d)


def characterize(table_bits=LUT_INDEX_BITS, mant_bits=MANTISSA_BITS,
                  out_frac=OUT_FRAC_BITS):
    """Exhaustive sweep of every normalized mantissa value. Returns
    (max_abs_error_ulp, max_rel_error, worst_d)."""
    lut = build_lut(table_bits, mant_bits, out_frac)
    max_abs_ulp = 0
    max_rel = 0.0
    worst_d = None
    for d in range(1 << (mant_bits - 1), 1 << mant_bits):
        got = reciprocal_core(d, table_bits, mant_bits, out_frac, lut)
        exact = exact_scaled(d, mant_bits, out_frac)
        abs_err = abs(got - exact)
        rel_err = float(abs_err / exact)
        if abs_err > max_abs_ulp:
            max_abs_ulp = abs_err
            worst_d = d
        if rel_err > max_rel:
            max_rel = rel_err
    return max_abs_ulp, max_rel, worst_d


if __name__ == "__main__":
    max_abs, max_rel, worst_d = characterize()
    print(f"MANTISSA_BITS={MANTISSA_BITS} LUT_INDEX_BITS={LUT_INDEX_BITS} "
          f"OUT_FRAC_BITS={OUT_FRAC_BITS}")
    print(f"Exhaustive sweep over {1 << (MANTISSA_BITS - 1)} mantissa values.")
    print(f"Max abs error: {float(max_abs):.2f} ULP (output scale 2**{OUT_FRAC_BITS})")
    print(f"Max rel error: {max_rel:.3e}  (worst d={worst_d})")
    import math
    correct_bits = -math.log2(max_rel) if max_rel else OUT_FRAC_BITS
    print(f"Effective correct bits: ~{correct_bits:.1f}")
