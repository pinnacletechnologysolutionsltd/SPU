#!/usr/bin/env python3
"""Lucas Phinary MAC — Python Behavioral Oracle

Copyright 2026 John Curley

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
Models the Lucas Phinary co-processor arithmetic over ℤ[φ] / L_p
where L_p is a Lucas prime modulus.  This oracle generates golden
test vectors for Verilog testbench comparison.

Core operations:
  PSCALE  — multiply by φ     (single shift-add, no DSP)
  PCHIRAL — φ-conjugation     (a + bφ → (a+b) − bφ)
  PWAVE   — φ-phase accumulate (running φ-exponent sum)
  PMUL    — full φ-multiply    (general a·b in ℤ[φ])
  PINV    — Lucas inverse      (extended Euclidean over ℤ[φ])
  PHSLK   — phase coherence    (n1*d2 == n2*d1, no denominator inverse)

The zero-drift proof:
  Apply φ-multiplication repeatedly to a seed value.  After the
  Lucas period (related to the multiplicative order of φ mod L_p),
  the value must return to the exact starting bit-pattern.

Usage:
  python3 software/tests/test_lucas_mac_oracle.py
  python3 software/tests/test_lucas_mac_oracle.py --emit-verilog
"""

import math
from typing import Tuple


# ── Lucas primes ──────────────────────────────────────────────────────────

LUCAS_PRIMES = {
    5:  11,
    7:  29,
    11: 199,
    13: 521,
    17: 3571,
    19: 9349,
}

DEFAULT_MODULUS = 521  # L_13


# ── ℤ[φ] arithmetic ──────────────────────────────────────────────────────

def phi_mul(a: int, b: int, mod: int = DEFAULT_MODULUS) -> Tuple[int, int]:
    """PSCALE: multiply a + bφ by φ.  φ·(a + bφ) = b + (a+b)φ."""
    return (b % mod, (a + b) % mod)


def phi_conj(a: int, b: int, mod: int = DEFAULT_MODULUS) -> Tuple[int, int]:
    """PCHIRAL: φ-conjugation.  conj(a + bφ) = (a+b) − bφ."""
    return ((a + b) % mod, (-b) % mod)


def phi_add(a1: int, b1: int, a2: int, b2: int,
            mod: int = DEFAULT_MODULUS) -> Tuple[int, int]:
    """Add two ℤ[φ] elements."""
    return ((a1 + a2) % mod, (b1 + b2) % mod)


def phi_mul_full(a1: int, b1: int, a2: int, b2: int,
                 mod: int = DEFAULT_MODULUS) -> Tuple[int, int]:
    """PMUL: full multiply in ℤ[φ].
    (a1 + b1φ)(a2 + b2φ) = (a1a2 + b1b2) + (a1b2 + a2b1 + b1b2)φ
    using φ² = φ + 1.
    """
    ar = (a1 * a2 + b1 * b2) % mod
    br = (a1 * b2 + a2 * b1 + b1 * b2) % mod
    return (ar, br)


def phi_pow(exp: int, mod: int = DEFAULT_MODULUS) -> Tuple[int, int]:
    """Compute φ^exp in ℤ[φ]/L_p by repeated squaring."""
    # φ^0 = 1 = 1 + 0φ
    result = (1, 0)
    base = (0, 1)  # φ = 0 + 1φ

    while exp > 0:
        if exp & 1:
            result = phi_mul_full(result[0], result[1],
                                  base[0], base[1], mod)
        base = phi_mul_full(base[0], base[1],
                            base[0], base[1], mod)
        exp >>= 1

    return result


def phi_order(mod: int = DEFAULT_MODULUS) -> int:
    """Compute the multiplicative order of φ in ℤ[φ]/L_p.
    The order is the smallest n > 0 such that φ^n ≡ ±1 mod L_p.
    """
    # Search for the period
    val = (0, 1)  # φ^1
    for n in range(1, mod * mod + 1):
        if val == (1, 0) or val == (mod - 1, 0):
            return n
        val = phi_mul(val[0], val[1], mod)
    return -1  # should not happen for Lucas primes


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    """Extended Euclidean algorithm over integers."""
    if b == 0:
        return (a, 1, 0)
    g, x, y = egcd(b, a % b)
    return (g, y, x - (a // b) * y)


def mod_inv(x: int, mod: int) -> int:
    """Modular inverse over integers."""
    g, a, _ = egcd(x % mod, mod)
    if g != 1:
        raise ValueError(f"{x} has no inverse mod {mod}")
    return a % mod


def phi_norm(a: int, b: int, mod: int = DEFAULT_MODULUS) -> int:
    """Norm of a + bφ in ℤ[φ].  N(a+bφ) = a² + ab − b²."""
    return (a * a + a * b - b * b) % mod


def phi_inv(a: int, b: int, mod: int = DEFAULT_MODULUS) -> Tuple[int, int]:
    """PINV: invert a + bφ in ℤ[φ]/L_p.
    (a + bφ)⁻¹ = (a + b − bφ) / N(a+bφ)
    """
    n = phi_norm(a, b, mod)
    if n == 0:
        raise ValueError(f"({a}+{b}φ) is a zero-divisor mod {mod}")
    n_inv = mod_inv(n, mod)
    # conj(a+bφ) = (a+b) − bφ
    ca = (a + b) % mod
    cb = (-b) % mod
    return ((ca * n_inv) % mod, (cb * n_inv) % mod)


def pinv_scalar_cycle_count(norm: int, mod: int = DEFAULT_MODULUS):
    """Model RTL PINV scalar inverse busy-phase cycles for one norm.

    Counts the setup cycle, binary-GCD loop cycles, and final result cycle.
    The caller issue/accept cycle is excluded.
    """
    norm %= mod
    if norm == 0:
        return None

    u = norm
    v = mod
    x1 = 1
    x2 = 0
    cycles = 1  # pinv_st=0 setup

    while True:
        cycles += 1
        if u == 1 or v == 1:
            break
        if (u & 1) == 0:
            u >>= 1
            x1 = (x1 >> 1) if ((x1 & 1) == 0) else ((x1 + mod) >> 1)
        elif (v & 1) == 0:
            v >>= 1
            x2 = (x2 >> 1) if ((x2 & 1) == 0) else ((x2 + mod) >> 1)
        elif u >= v:
            u -= v
            x1 = (x1 - x2) if x1 >= x2 else (x1 + mod - x2)
        else:
            v -= u
            x2 = (x2 - x1) if x2 >= x1 else (x2 + mod - x1)

    return cycles + 1  # pinv_st=2 result


def pinv_latency_profile(mod: int = DEFAULT_MODULUS):
    """Exhaustively profile RTL-style PINV cycles for all a+bφ elements."""
    counts = []
    zero_divisors = 0
    norm_cycles = {}

    for a in range(mod):
        for b in range(mod):
            n = phi_norm(a, b, mod)
            if n == 0:
                zero_divisors += 1
                continue
            c = norm_cycles.setdefault(n, pinv_scalar_cycle_count(n, mod))
            counts.append(c)

    return {
        "zero_divisors": zero_divisors,
        "nonzero_elements": len(counts),
        "unique_norms": len(norm_cycles),
        "min_cycles": min(counts),
        "max_cycles": max(counts),
        "avg_cycles": sum(counts) / len(counts),
    }


def phi_phslk(n1: Tuple[int, int], d1: Tuple[int, int],
              n2: Tuple[int, int], d2: Tuple[int, int],
              mod: int = DEFAULT_MODULUS):
    """PHSLK: rational phase coherence by cross multiplication.

    Checks n1*d2 == n2*d1 over Z[phi]/L_p and reports whether either
    denominator is a zero divisor. No modular inverse is computed.
    """
    left = phi_mul_full(n1[0], n1[1], d2[0], d2[1], mod)
    right = phi_mul_full(n2[0], n2[1], d1[0], d1[1], mod)
    zero_divisor = (phi_norm(d1[0], d1[1], mod) == 0 or
                    phi_norm(d2[0], d2[1], mod) == 0)
    return left == right, zero_divisor, left, right


def anyon_capture_predicate(observed_n: Tuple[int, int],
                            observed_d: Tuple[int, int],
                            template_n: Tuple[int, int],
                            template_d: Tuple[int, int],
                            mod: int = DEFAULT_MODULUS):
    """Interpret PHSLK as a rational anyon-capture predicate.

    The arithmetic is exactly PHSLK. "Capture" is a domain-level validity rule:
    the observed rational phase must cohere with the template phase, and
    neither denominator may be a zero divisor.
    """
    coherent, zero_divisor, left, right = phi_phslk(
        observed_n, observed_d, template_n, template_d, mod)
    return coherent and not zero_divisor, coherent, zero_divisor, left, right


# ── Zero-Drift Test ───────────────────────────────────────────────────────

def zero_drift_test(mod: int = DEFAULT_MODULUS,
                    seed: Tuple[int, int] = (3, 5),
                    steps: int = 1000000):
    """Run the zero-drift closure test.

    Apply φ-multiplication repeatedly to the seed value.
    After one full Lucas period, the value must return to seed exactly.
    Verify at every period boundary.
    """
    period = phi_order(mod)
    print(f"Lucas modulus L_p = {mod}")
    print(f"φ period mod {mod} = {period}")
    print(f"Seed = {seed[0]} + {seed[1]}φ")
    print()

    a, b = seed
    errors = 0
    periods_checked = 0

    for step in range(1, steps + 1):
        a, b = phi_mul(a, b, mod)

        if step % period == 0:
            periods_checked += 1
            if (a, b) != seed:
                print(f"  DRIFT at step {step}: got ({a}+{b}φ), expected {seed}")
                errors += 1
                break

        if step % 100000 == 0:
            print(f"  ... {step} steps, {periods_checked} periods checked, "
                  f"current = ({a}+{b}φ)")

    print()
    if errors == 0:
        print(f"ZERO-DRIFT: PASS — {periods_checked} full periods, "
              f"bit-exact closure every time")
    else:
        print(f"ZERO-DRIFT: FAIL — {errors} drift events")
    return errors == 0


def composite_zero_drift_test(mod: int = DEFAULT_MODULUS,
                              seed: Tuple[int, int] = (3, 5),
                              primitive_ops: int = 1000000):
    """Run a mixed-opcode exact-closure test.

    Each macro applies an identity sequence built from PSCALE, PMUL, and PINV:
      x <- PSCALE(x)
      x <- x * PINV(phi)
      x <- x * g
      x <- x * PINV(g)

    "Zero drift" for a mixed pipeline means every algebraic identity boundary
    returns to the exact seed bit pattern; no residual is allowed to accumulate.
    """
    phi = (0, 1)
    generators = [
        (3, 5), (2, 7), (8, 13), (21, 34),
        (55, 89), (1, 1), (5, 2), (13, 21),
    ]
    ops_per_macro = 6  # PSCALE, PINV(phi), PMUL, PINV(g), PMUL, PMUL
    macros = primitive_ops // ops_per_macro
    if macros <= 0:
        raise ValueError("primitive_ops must cover at least one macro")

    print("Composite zero-drift: mixed PSCALE/PMUL/PINV identity macros")
    print(f"Seed = {seed[0]} + {seed[1]}φ")
    print(f"Primitive ops target = {primitive_ops}, macros = {macros}")

    a, b = seed
    errors = 0
    executed_ops = 0

    for macro_idx in range(1, macros + 1):
        g = generators[(macro_idx - 1) % len(generators)]

        # PSCALE by phi.
        a, b = phi_mul(a, b, mod)
        executed_ops += 1

        # PINV(phi), then PMUL by phi^-1.
        inv_phi = phi_inv(phi[0], phi[1], mod)
        executed_ops += 1
        a, b = phi_mul_full(a, b, inv_phi[0], inv_phi[1], mod)
        executed_ops += 1

        # PMUL by g, then PINV(g), then PMUL by g^-1.
        a, b = phi_mul_full(a, b, g[0], g[1], mod)
        executed_ops += 1
        inv_g = phi_inv(g[0], g[1], mod)
        executed_ops += 1
        a, b = phi_mul_full(a, b, inv_g[0], inv_g[1], mod)
        executed_ops += 1

        if (a, b) != seed:
            print(f"  DRIFT at macro {macro_idx}: got ({a}+{b}φ), expected {seed}")
            errors += 1
            break

        if macro_idx % 25000 == 0:
            print(f"  ... {macro_idx} macros, {executed_ops} primitive ops, "
                  f"state = ({a}+{b}φ)")

    print()
    if errors == 0:
        print(f"COMPOSITE ZERO-DRIFT: PASS — {macros} identity macros, "
              f"{executed_ops} mixed primitive ops")
    else:
        print(f"COMPOSITE ZERO-DRIFT: FAIL — {errors} drift events")
    return errors == 0


# ── Jitterbug Interpolation Test ──────────────────────────────────────────

def jitterbug_test(mod: int = DEFAULT_MODULUS):
    """Simulate the Jitterbug transformation as φ-linear interpolation.

    The Jitterbug collapses a Vector Equilibrium into an Octahedron.
    In ℤ[φ], this is a simple mix() between two φ-weighted endpoints.
    """
    # Start: VE vertex (1 + φ)
    # End:   Octahedron vertex (2φ)
    start = (1, 1)   # 1 + φ
    end = (0, 2)     # 2φ

    print(f"Jitterbug: VE → Octahedron via φ-interpolation")
    print(f"  Start = {start[0]} + {start[1]}φ")
    print(f"  End   = {end[0]} + {end[1]}φ")

    # Interpolate in 8 steps using φ-weighted mix
    # mix(t) = start + t·(end - start)  where t = k·φ/8
    for k in range(9):
        # t = k/8 in ℤ[φ] rational form
        # For exact geometry: interpolate with rational weights
        frac_a = k
        frac_b = 8 - k
        # Weighted blend: (frac_b * start + frac_a * end) / 8
        sa = (frac_b * start[0] + frac_a * end[0]) % mod
        sb = (frac_b * start[1] + frac_a * end[1]) % mod
        # Divide by 8 (mod L_p)
        inv8 = mod_inv(8, mod)
        sa = (sa * inv8) % mod
        sb = (sb * inv8) % mod
        print(f"  k={k}: ({sa}+{sb}φ)")

    print("JITTERBUG: exact rational interpolation — no transcendental ops")
    print()


# ── Verilog test vector generation ────────────────────────────────────────

def emit_verilog_testbench(mod: int = DEFAULT_MODULUS):
    """Emit a Verilog testbench header with golden test vectors."""
    period = phi_order(mod)
    seed_a, seed_b = 3, 5

    print("// Auto-generated Lucas MAC golden trace")
    print(f"// Modulus: L_p = {mod}")
    print(f"// φ period: {period}")
    print()

    # Phase 1: PSCALE — single φ-multiplication
    print("// ── PSCALE test vectors ──")
    test_vecs = [(0, 0), (1, 0), (0, 1), (3, 5), (mod-1, mod-1)]
    for a, b in test_vecs:
        ra, rb = phi_mul(a, b, mod)
        print(f"// φ·({a}+{b}φ) = ({ra}+{rb}φ)")

    print()
    print("// ── PCHIRAL test vectors ──")
    for a, b in test_vecs:
        ra, rb = phi_conj(a, b, mod)
        print(f"// conj({a}+{b}φ) = ({ra}+{rb}φ)")

    print()
    print("// ── PINV test vectors ──")
    for a, b in [(1, 0), (3, 5), (0, 1)]:
        try:
            ra, rb = phi_inv(a, b, mod)
            print(f"// ({a}+{b}φ)⁻¹ = ({ra}+{rb}φ)")
        except ValueError as e:
            print(f"// ({a}+{b}φ)⁻¹ = SINGULAR ({e})")

    print()
    print("// ── PHSLK test vectors ──")
    phslk_vecs = [
        ((3, 5), (2, 7), (6, 10), (4, 14), "coherent scaled fraction"),
        ((3, 5), (2, 7), (6, 11), (4, 14), "mismatch"),
        ((3, 5), (1, 100), (6, 10), (4, 14), "zero-divisor denominator"),
    ]
    for n1, d1, n2, d2, label in phslk_vecs:
        coherent, zero_divisor, left, right = phi_phslk(n1, d1, n2, d2, mod)
        print(f"// {label}: n1*d2={left}, n2*d1={right}, "
              f"coherent={int(coherent)}, zero_divisor={int(zero_divisor)}")

    print()
    print("// ── Zero-drift trace (first 3 periods) ──")
    a, b = seed_a, seed_b
    trace = [(a, b)]
    for _ in range(3 * period):
        a, b = phi_mul(a, b, mod)
        trace.append((a, b))
    for i, (a, b) in enumerate(trace):
        marker = " ← PERIOD CLOSURE" if (i > 0 and i % period == 0) else ""
        print(f"// [{i:4d}] ({a:4d}+{b:4d}φ){marker}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    import sys

    if '--emit-verilog' in sys.argv:
        emit_verilog_testbench()
        return

    mod = DEFAULT_MODULUS
    print("=== Lucas Phinary MAC Oracle ===")
    print(f"Modulus L_p = {mod}")
    print(f"φ period = {phi_order(mod)}")
    print()

    # Quick sanity checks
    print("PSCALE: φ·(3+5φ) =", phi_mul(3, 5, mod))
    print("PCHIRAL: conj(3+5φ) =", phi_conj(3, 5, mod))
    print("PMUL: (3+5φ)(2+7φ) =", phi_mul_full(3, 5, 2, 7, mod))
    print("PINV: (3+5φ)⁻¹ =", phi_inv(3, 5, mod))
    coherent, zero_divisor, left, right = phi_phslk(
        (3, 5), (2, 7), (6, 10), (4, 14), mod)
    print("PHSLK: (3+5φ)/(2+7φ) == (6+10φ)/(4+14φ) ->",
          coherent, "zero_divisor=", zero_divisor,
          "left=", left, "right=", right)

    mismatch, mismatch_zd, _, _ = phi_phslk(
        (3, 5), (2, 7), (6, 11), (4, 14), mod)
    zd_coherent, zd_flag, _, _ = phi_phslk(
        (3, 5), (1, 100), (6, 10), (4, 14), mod)
    assert coherent and not zero_divisor
    assert not mismatch and not mismatch_zd
    assert not zd_coherent and zd_flag

    capture, cap_coherent, cap_zd, _, _ = anyon_capture_predicate(
        (3, 5), (2, 7), (6, 10), (4, 14), mod)
    capture_mismatch, _, _, _, _ = anyon_capture_predicate(
        (3, 5), (2, 7), (6, 11), (4, 14), mod)
    capture_singular, singular_coherent, singular_zd, _, _ = (
        anyon_capture_predicate((3, 5), (1, 100), (6, 10), (4, 14), mod))
    print("ANYON_CAPTURE: observed/template rational phase ->",
          capture, "coherent=", cap_coherent, "zero_divisor=", cap_zd)
    assert capture and cap_coherent and not cap_zd
    assert not capture_mismatch
    assert not capture_singular and not singular_coherent and singular_zd

    # Verify: (3+5φ) · (3+5φ)⁻¹ should be (1,0)
    inv = phi_inv(3, 5, mod)
    prod = phi_mul_full(3, 5, inv[0], inv[1], mod)
    print(f"Self-check: (3+5φ)·(3+5φ)⁻¹ = {prod}  {'✓' if prod == (1,0) else '✗'}")
    print()

    profile = pinv_latency_profile(mod)
    print("PINV latency profile:")
    print(f"  nonzero elements={profile['nonzero_elements']}, "
          f"zero_divisors={profile['zero_divisors']}, "
          f"unique_norms={profile['unique_norms']}")
    print(f"  busy-phase cycles min/max/avg="
          f"{profile['min_cycles']}/{profile['max_cycles']}/"
          f"{profile['avg_cycles']:.2f}")
    assert profile["max_cycles"] == 23
    print()

    jitterbug_test(mod)
    zero_drift_test(mod)
    composite_zero_drift_test(mod)


if __name__ == '__main__':
    main()
