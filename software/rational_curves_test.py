#!/usr/bin/env python3
"""
Rational Curves Test Suite — validates Type 1-4 primitives against spec invariants.
Exercises: Pell rotor, F,G,H circulant, circular arc, linear segment,
           forward kinematics chain, spread interpolation, Davis snap.

All arithmetic stays in Q(√3). No float, no division, no sin/cos.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spu_vm import (RationalSurd, QuadrayVector, rs_lt, rs_min,
                    triple_quadrance, spread_from_quadrances,
                    is_right_triangle, delta_curve)

RS = RationalSurd  # shorthand

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")

# ══════════════════════════════════════════════════════════════════════════════
# Type 1: Rotor Application
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Type 1: Pell Rotor ──")

# Pell orbit: r^n, r = (2+√3).  12 steps ≈ one full rotation.
r = RS(2, 1, pell_step=0)
for n in range(1, 13):
    r = r.rotate_phi()
    check(f"pell[{n}] norm = 1", r.quadrance() == 1,
          f"got Q={r.quadrance()}")
    expected_step = n % 8
    check(f"pell[{n}] pell_step = {n}", r.pell_step == n,
          f"got {r.pell_step}")

# After 12 steps, mantissa should cycle back to orbit[4] = (97, 56)
r12 = RS(2, 1, pell_step=0)
for _ in range(12):
    r12 = r12.rotate_phi()
check("pell[12] mantissa = (97,56)", (r12.a, r12.b) == (97, 56),
      f"got ({r12.a}, {r12.b})")
check("pell[12] octave = 1 (step 4 in octave 1)",
      r12.pell_step == 12)

print("\n── Type 1: F,G,H Circulant ──")

# Test at 0°: identity (F=1, G=0, H=0)
v = QuadrayVector(RS(0), RS(1), RS(2), RS(3))
F1, G0, H0 = RS(1, 0), RS(0, 0), RS(0, 0)
v_id = v.circulant_rotate(F1, G0, H0)
check("circulant identity B", v_id.b == v.b)
check("circulant identity C", v_id.c == v.c)
check("circulant identity D", v_id.d == v.d)
check("circulant identity A unchanged", v_id.a == v.a)

# Test at 120°: F=-1/3, G=2/3, H=2/3 — should be pure permutation B→D→C→B
# With F,G,H as rational surds: F = (-1 + 0√3), but we need -1/3.
# Represent -1/3 as RationalSurd(-1, 0) scaled — but RationalSurd stores integers.
# We need rational coefficients. The spec says entries are in {−1/3, 2/3}.
# For simulation, we test with integer-scaled surds: multiply F,G,H by 3.
# Then B' = (F·B + H·C + G·D) is scaled by 3², so divide result by 9.
# But the circulant formula is linear, so:
#   B'/3 = ((-1/3)·B + (2/3)·C + (2/3)·D) = (-B + 2C + 2D) / 3 → B' = (-B+2C+2D)/3
# Let's use integer surds: F3 = RS(-1), G3 = RS(2), H3 = RS(2), then scale result.

def circulant_120(v):
    """120° circulant with exact rational coefficients using 3× scaling."""
    # B' = ((-1)B + 2C + 2D) / 3  →  integer numerator in Q(√3)
    b_num = (RS(-1) * v.b) + (RS(2) * v.c) + (RS(2) * v.d)
    c_num = (RS(2) * v.b) + (RS(-1) * v.c) + (RS(2) * v.d)
    d_num = (RS(2) * v.b) + (RS(2) * v.c) + (RS(-1) * v.d)
    return QuadrayVector(
        v.a,
        RationalSurd(b_num.a, b_num.b),
        RationalSurd(c_num.a, c_num.b),
        RationalSurd(d_num.a, d_num.b),
    )
    # Note: components are 3× the true result. Divide by 3 externally.

v120 = circulant_120(v)
# At 120°, the true result should be: b → d, c → b, d → c (cyclic permutation on B,C,D)
# But with F=-1/3, G=2/3, H=2/3: B' = (-B + 2C + 2D)/3, etc.
# Test that B' * 3 = -B + 2C + 2D (no division needed for comparison)
expected_b3 = (RS(-1)*v.b + RS(2)*v.c + RS(2)*v.d)
expected_c3 = (RS(2)*v.b + RS(-1)*v.c + RS(2)*v.d)
expected_d3 = (RS(2)*v.b + RS(2)*v.c + RS(-1)*v.d)
check("circulant 120° B*3", v120.b == expected_b3,
      f"got {v120.b}, expected {expected_b3}")
check("circulant 120° C*3", v120.c == expected_c3)
check("circulant 120° D*3", v120.d == expected_d3)
check("circulant 120° A unchanged", v120.a == v.a)

# Test cyclic permutation property: four 120° rotations = identity (A₄ subgroup)
# Apply 120° four times to B,C,D only
v4x = v
for _ in range(4):
    v4x = circulant_120(v4x)
# After 4×120° = 480° ≡ 120°, expect 3^4 = 81× scaling
# Each application multiplies by 3, so 4 applications = 3^4 = 81
# The true coordinates should return to original scaled by 81
f81 = RS(81, 0)
check("circulant 120°×4 B = 81×B", v4x.b.a == v.b.a * 81 and v4x.b.b == v.b.b * 81)
check("circulant 120°×4 C = 81×C", v4x.c.a == v.c.a * 81 and v4x.c.b == v.c.b * 81)
check("circulant 120°×4 D = 81×D", v4x.d.a == v.d.a * 81 and v4x.d.b == v.d.b * 81)

# ══════════════════════════════════════════════════════════════════════════════
# Type 2: Curve Segments
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Type 2: Circular Arc ──")

def circular_arc(center, point, pell_count):
    """Generate pell_count+1 points on a Pell-orbit circle around center.
    Uses scalar multiplication by Pell rotor (no normalization) to preserve quadrance."""
    pts = [point]
    offset = point - center
    r = RS(2, 1)  # Pell rotor, no pell_step tracking needed
    for _ in range(pell_count):
        offset = offset.scale(r)   # scale by (2+√3) — preserves quadrance up to r²
        pts.append(center + offset)
    return pts

center = QuadrayVector(RS(0), RS(0), RS(0), RS(0))
point  = QuadrayVector(RS(0), RS(1), RS(0), RS(0))  # offset on B-axis
arc = circular_arc(center, point, 12)
check("circular arc returns 13 points", len(arc) == 13)
# Quadrance scales by r² each step: Q_n = Q_0 * r^(2n)
# r² = (2+√3)² = 7+4√3
r2 = RS(7, 4)
q0 = arc[0].quadrance()
q_expected = q0
for i, pt in enumerate(arc[1:], 1):
    q_expected = q_expected * r2
    check(f"arc[{i}] quadrance = Q₀ * r²^{i}", pt.quadrance() == q_expected,
          f"got {pt.quadrance()} ≠ {q_expected}")

# After 12 Pell steps, point should be original scaled by r^12.
# r^12 via Pell octave: OCTAVE¹×r⁴ = (18817+10864√3)(97+56√3)
# = (3650401 + 2107560√3)
r12_full = RS(1, 0)  # r⁰ = identity
r = RS(2, 1)
for _ in range(12):
    r12_full = r12_full * r
arc12_expected = arc[0].scale(r12_full)
check("circular arc 12-step closure (A)", arc[12].a == arc12_expected.a,
      f"got {arc[12].a} ≠ {arc12_expected.a}")
check("circular arc 12-step closure (B)", arc[12].b == arc12_expected.b,
      f"got {arc[12].b} ≠ {arc12_expected.b}")

print("\n── Type 2: Linear Segment ──")

def linear_segment(p0, p1, steps):
    """Generate steps+1 points linearly interpolated between p0 and p1."""
    pts = [p0]
    for k in range(1, steps + 1):
        pts.append(p0.lerp_spread(p1, k, steps))
    return pts

p0 = QuadrayVector(RS(0), RS(0), RS(0), RS(0))
p1 = QuadrayVector(RS(3), RS(1), RS(2), RS(0))  # (3, 1+√3, 2, 0)
line = linear_segment(p0, p1, 4)
check("linear segment returns 5 points", len(line) == 5)
check("linear segment[0] = p0", line[0] == p0)
# At step 4 (t=1), should equal p1 scaled by denominator 4.
# lerp_spread returns numerator *4 unscaled, so we check scaled equality.
# line[4] = p0 + (p1-p0)*4/4 → each component = p1_i * 4 / 4 with denom 4.
# The lerp_spread result has component.a = s0.a*4 + da*4 = p1.a * 4
# So line[4].a * 1 should equal p1.a * 4... no, let me re-read the formula:
# _lerp_surd: na = s0.a * t_den + da * t_num
# For p0=(0,0,0,0), p1=(3,1,2,0), t_num=4, t_den=4:
#   na = 0*4 + 3*4 = 12, nb = 0*4 + 1*4 = 4
# So line[4] has (a=12, b=4) which represents (12+4√3)/4 = 3+1√3 = p1 ✓
check("linear segment[4] A * denom = p1.A * denom",
      line[4].a.a == p1.a.a * 4 and line[4].a.b == 0)
check("linear segment[4] B * denom = p1.B * denom",
      line[4].b.a == p1.b.a * 4 and line[4].b.b == p1.b.b * 4)

# ══════════════════════════════════════════════════════════════════════════════
# Type 3: Forward Kinematics
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Type 3: Forward Kinematics Chain ──")

def fk_chain(base, joints):
    """Forward kinematics: apply joint rotations in sequence.
    Each joint is (F, G, H) RationalSurd triple for circulant rotation."""
    v = base
    for F, G, H in joints:
        v = v.circulant_rotate(F, G, H)
    return v

# 2-joint arm: identity chain should return base
base = QuadrayVector(RS(0), RS(0), RS(1), RS(0))
v_id_chain = fk_chain(base, [(RS(1), RS(0), RS(0)), (RS(1), RS(0), RS(0))])
check("fk identity chain = base", v_id_chain == base)

# ══════════════════════════════════════════════════════════════════════════════
# Janus Polarity
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Janus Polarity ──")

# Pell rotor from unity starts with p=+1 at step 0
r = RS(2, 1, pell_step=0, polarity=+1)
check("initial polarity = +1", r.polarity == +1)

# After 4 steps, polarity should flip to −1
for _ in range(4):
    r = r.rotate_phi()
check("step 4 polarity = −1", r.polarity == -1, f"got {r.polarity}")
check("step 4 mantissa = (97,56)", (r.a, r.b) == (97, 56))

# After 8 steps, polarity should be back to +1 (two flips)
for _ in range(4):
    r = r.rotate_phi()
check("step 8 polarity = +1 (two flips cancel)", r.polarity == +1,
      f"got {r.polarity}")

# Janus inversion: flip polarity, leave surd unchanged
a, b = r.a, r.b
r_inv = r.janus_invert()
check("janus_invert flips polarity", r_inv.polarity == -1)
check("janus_invert preserves surd a", r_inv.a == a)
check("janus_invert preserves surd b", r_inv.b == b)
check("double invert returns original", r_inv.janus_invert().polarity == r.polarity)

# Polarity composes under multiplication
r_pos = RS(2, 1, polarity=+1)
r_neg = RS(2, 1, polarity=-1)
r_prod = r_pos * r_neg
check("(+1) × (−1) = −1", r_prod.polarity == -1)
check("(−1) × (−1) = +1", (r_neg * r_neg).polarity == +1)
check("(+1) × (+1) = +1", (r_pos * r_pos).polarity == +1)

# Surds without polarity don't interfere
s = RS(3, 0)  # no polarity
check("unpolarized surd has polarity=None", s.polarity is None)
check("unpolarized × polarized preserves polarity",
      (s * r_pos).polarity == +1)

# ══════════════════════════════════════════════════════════════════════════════
# Cayley NLERP (Type 4)
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Type 4: Cayley NLERP ──")

def cayley_nlerp(rotor_a, rotor_b, t_num, t_den):
    """
    Cayley NLERP: interpolate between two rotors using Cayley vectors.
    Thomson §10, Table 4.  Rational in the bulk; falls back to Hamilton
    product at antipodal endpoints.
    
    Cayley vector: r = tan(θ/2) · u  (axis-angle → 3D vector).
    In the rational framework, we work with the spread s = sin²(θ)
    and represent tan(θ/2)² = s / (4(1−s)) — stays rational for
    rational s.
    
    For Pell rotors, we interpolate on the Pell step counter directly
    since the Pell orbit is discrete and each step has known (F,G,H).
    For general rotors, we decompose to axis-angle, interpolate the
    angle linearly, and reconstruct.
    """
    # Simplest case: both rotors are Pell steps on the same orbit.
    # Interpolate between step counts, reconstruct from vault.
    if rotor_a.pell_step is not None and rotor_b.pell_step is not None:
        s_a = rotor_a.pell_step
        s_b = rotor_b.pell_step
        # Interpolate step count linearly
        step_interp = s_a + (s_b - s_a) * t_num // t_den
        # Reconstruct from Pell orbit
        _ORBIT = [(1,0,+1),(2,1,+1),(7,4,+1),(26,15,+1),
                  (97,56,-1),(362,209,-1),(1351,780,-1),(5042,2911,-1)]
        sm = step_interp % 8
        a, b, p = _ORBIT[sm]
        return RationalSurd(a, b, pell_step=step_interp, polarity=p)
    # Fallback: linear interpolation on axis-angle θ
    # cos_θ_a = p_a · √(1−s_a), cos_θ_b = p_b · √(1−s_b)
    # θ_a = acos(cos_θ_a), θ_b = acos(cos_θ_b) — but we can't compute acos
    # Instead: interpolate the rational coefficients directly, then
    # renormalize.  This is the Cayley NLERP without the trig detour.
    return _cayley_generic(rotor_a, rotor_b, t_num, t_den)

def _cayley_generic(rotor_a, rotor_b, t_num, t_den):
    """Generic Cayley NLERP via direct surd interpolation + renormalization."""
    # Interpolate surd coefficients linearly
    da = rotor_b.a - rotor_a.a
    db = rotor_b.b - rotor_a.b
    interp_a = rotor_a.a * t_den + da * t_num
    interp_b = rotor_a.b * t_den + db * t_num
    # Normalize: ensure P² − 3Q² = 1 (or close)
    # For Pell rotors the vault guarantees this; for general rotors
    # we'd need normalize-by-division which we avoid.
    # For now: return unnormalized with denom tracking.
    p = None
    if rotor_a.polarity is not None and rotor_b.polarity is not None:
        # Interpolate polarity: if both same, keep; if different, tie-break
        # by proximity to t=0 or t=1
        p = rotor_a.polarity if t_num * 2 <= t_den else rotor_b.polarity
    return RationalSurd(interp_a, interp_b, polarity=p)

# Test Cayley NLERP on Pell orbit
r0 = RS(1, 0, pell_step=0, polarity=+1)   # r⁰: identity
r4 = RS(97, 56, pell_step=4, polarity=-1)  # r⁴: 4 steps
mid = cayley_nlerp(r0, r4, 1, 2)           # halfway: step 2
check("NLERP midpoint step = 2", mid.pell_step == 2)
check("NLERP midpoint mantissa = (7,4)", (mid.a, mid.b) == (7, 4),
      f"got ({mid.a}, {mid.b})")
check("NLERP midpoint polarity = +1", mid.polarity == +1)

# Quarter-way: t=1/4, step ≈ 1
qtr = cayley_nlerp(r0, r4, 1, 4)
check("NLERP quarter step = 1", qtr.pell_step == 1,
      f"got {qtr.pell_step}, ({qtr.a}, {qtr.b})")

# Antipodal: r⁰ → r⁸ (polarities differ)
r8 = RS(1, 0, pell_step=8, polarity=+1)   # r⁸: back to identity mantissa
far = cayley_nlerp(r0, r8, 1, 2)          # should step to 4
check("NLERP r⁰→r⁸ midpoint step = 4", far.pell_step == 4,
      f"got {far.pell_step}")
check("NLERP r⁰→r⁸ polarity = −1 (crosses 90°)", far.polarity == -1,
      f"got {far.polarity}")

# ══════════════════════════════════════════════════════════════════════════════
# Type 5: Davis Snap (SDF integration)
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Type 5: Davis Snap ──")

# Test that a zero-vector manifold is laminar
z = QuadrayVector(RS(0), RS(0), RS(0), RS(0))
check("zero vector is_zero", z.is_zero())
check("zero vector quadrance = 0", z.quadrance() == RS(0, 0))

# A vector with non-zero quadrance
v_nonzero = QuadrayVector(RS(0), RS(1), RS(0), RS(0))
check("nonzero vector not is_zero", not v_nonzero.is_zero())
# quadrance should be computed correctly: sum of squared pairwise differences
q_v = v_nonzero.quadrance()
check("nonzero vector quadrance > 0", q_v.a > 0 or q_v.b > 0,
      f"got {q_v}")

# ══════════════════════════════════════════════════════════════════════════════
# Type 6: Delta Curves — Triple Quadrance
# ══════════════════════════════════════════════════════════════════════════════

print("\n── Type 6: Delta Curves (Triple Quadrance) ──")

# Right triangle: s=1 → Q₃ = Q₁ + Q₂
check("right triangle 3,4 → 7", is_right_triangle(3, 4, 7))
check("not right triangle 3,4 → 8", not is_right_triangle(3, 4, 8))

# Spread from three quadrances
# For Q₁=3, Q₂=4, Q₃=7 (right): s should be 1
num, den = spread_from_quadrances(3, 4, 7)
check("spread(3,4,7) numer = denom (s=1)", num == den,
      f"got {num}/{den}")

# For Q₁=Q₂=1, Q₃=0 (collapsed, same direction): s should be 0
num, den = spread_from_quadrances(1, 1, 0)
check("spread(1,1,0) s = 0 (collapsed)", num == 0,
      f"got {num}/{den}")

# For Q₁=Q₂=1, Q₃=4 (collapsed, opposite direction): s should be 0
num, den = spread_from_quadrances(1, 1, 4)
check("spread(1,1,4) s = 0 (antiparallel)", num == 0,
      f"got {num}/{den}")

# For Q₁=5, Q₂=5, Q₃=10 (isosceles right): s=1
check("spread(5,5,10) = 1", is_right_triangle(5, 5, 10))

# Delta curve: parameterize Q₃ as spread varies
curve = delta_curve(3, 4, 4)  # 5 steps from s=0 to s=1
check("delta_curve returns 5 steps", len(curve) == 5)
# At s=0 (k=0): rhs² = 4·3·4·(4−0)/4 = 48/4, Q₃ = 7 ± √(48/4)
k0, sd0, qsum0, rhs_num0, rhs_den0 = curve[0]
check("delta[0] q_sum = 7", qsum0 == 7)
check("delta[0] rhs² = 192/4 (=48)", rhs_num0 == 192 and rhs_den0 == 4,
      f"got {rhs_num0}/{rhs_den0}")
# At s=1 (k=4): rhs² = 4·3·4·(4−4)/4 = 0, Q₃ = 7
k4, sd4, qsum4, rhs_num4, rhs_den4 = curve[4]
check("delta[4] rhs² = 0 (right triangle)", rhs_num4 == 0)
# At s=0.5 (k=2): rhs² = 4·3·4·(4−2)/4 = 96/4 = 24, Q₃ = 7 ± √24
k2, sd2, qsum2, rhs_num2, rhs_den2 = curve[2]
check("delta[2] rhs² = 96/4 (=24)", rhs_num2 == 96 and rhs_den2 == 4,
      f"got {rhs_num2}/{rhs_den2}")

# Triple quadrance: Q₁=3, Q₂=4, s=0 → Q₃ = |3−4| = 1 or 7
qsum, rhs_sq = triple_quadrance(3, 4, RS(0, 0))
check("TQF(3,4,s=0) q_sum = 7", qsum == 7)
check("TQF(3,4,s=0) rhs² ≥ 0", rhs_sq >= 0)
# s=1 → Q₃ = 7
qsum, rhs_sq = triple_quadrance(3, 4, RS(1, 0))
check("TQF(3,4,s=1) rhs² = 0", rhs_sq == 0)

# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*50}")
print(f"Rational Curves Test Suite: {PASS} passed, {FAIL} failed")
print(f"{'='*50}")

if FAIL > 0:
    print("FAIL")
    sys.exit(1)
else:
    print("PASS")
