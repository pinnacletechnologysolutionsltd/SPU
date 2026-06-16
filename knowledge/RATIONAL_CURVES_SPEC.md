# Rational Curves: SPU Kinematics & Trajectory Primitives

A specification for rational curve computation on the SPU-13 architecture.
Every operation stays in Q(√3). No float, no division, no sin/cos, no atan2.

*Version 1.0 — 2026-05-22*

---

## Hardware Substrate

The spec builds on two existing rotation primitives in silicon:

| Primitive | Module | What it does | Cost |
|---|---|---|---|
| **Pell rotor** | `spu_rotor_vault.v` | Scalar multiply by rⁿ = (2+√3)ⁿ via 8-entry vault + octave counter. Generates exact rational points on the unit circle in quadrance space. | 1 cycle per step |
| **F,G,H circulant** | `spu13_rotor_core.v` | Basis-axis rotation: B' = F·B + H·C + G·D (cyclic). 9 surd multiplies, zero sqrt, zero div. A is invariant. | 2 cycles (1 mul + 1 sum) |

**Invariants enforced by hardware:**
- Pell norm: P² − 3Q² = 1 for every vault entry (trivially true)
- Circulant determinant: F³ + G³ + H³ − 3FGH = 1 (formal assertion, `spu13_rotor_core.v:94`)
- Davis Gate: Σ quadrance over 13 axes = 0 ⇒ laminar (stable)
- Axis M-unit: basis axes satisfy ⟨e_X, e_X⟩_M = √3 by definition — no normalization needed
- **Janus polarity:** explicit Z₂ flag p ∈ {+1, −1} per rotor (Thomson SQR §9). Resolves
  spread sign ambiguity: cos θ = p·√(1−s). Composes under multiplication: p_ab = p_a × p_b.
  Pell steps 0–3 have p=+1; steps 4–7 have p=−1 (half-angle crosses 90° at step 4).

---

## Type 1: Rotor Application

### 1.0 Inverse Closure Requirement

Every rational robotics motion primitive must define and test its inverse. A
forward-only path can be algebraically valid but topologically unbalanced: the
manifold has moved away from its source state without a proof that the motion
can close exactly.

For Pell rotor motion:

```
r      = 2 + √3
r_inv  = 2 - √3
r × r_inv = 1
```

For F,G,H circulant rotation using the SPU convention:

```
B' = F·B + H·C + G·D
C' = G·B + F·C + H·D
D' = H·B + G·C + F·D
```

and determinant condition:

```
F³ + G³ + H³ − 3FGH = 1
```

the inverse coefficients are:

```
F_inv = F² − G·H
G_inv = H² − F·G
H_inv = G² − F·H
```

Example:

```
60°  = ( 2/3,  2/3, -1/3)
240° = ( 2/3, -1/3,  2/3) = inverse(60°)
```

Required test pattern for every robotics primitive:

```
start = state
end = apply_forward(start)
recovered = apply_inverse(end)
assert recovered == start
assert end != start        # unless the primitive is identity
SNAP
```

### 1.1 Pell Step (`ROT`)

```
pell_rotate(vertex: QuadrayVector, axis_id: int) -> QuadrayVector

Hardware: spu_rotor_vault.v — rot_en=1 on axis_id
```

Applies one Pell rotor step r = (2+√3) to the specified manifold axis.
The vertex on that axis is multiplied by the rotor from the 8-entry vault.
Octave counter increments when step wraps 7→0.

**Test invariant:** After n steps, the rotor mantissa is always from
orbit[n mod 8] and octave = n // 8. P² − 3Q² = 1 always.

### 1.2 Circulant Rotate (`ROTC`)

```
circulant_rotate(vertex: QuadrayVector, F: RationalSurd, G: RationalSurd, H: RationalSurd) -> QuadrayVector

Hardware: spu13_rotor_core.v
```

Applies the F,G,H circulant matrix to the B,C,D components of a Quadray vertex.
A is invariant (the rotation axis). The F,G,H coefficients must satisfy
F³ + G³ + H³ − 3FGH = 1.

**Corrected ROTC 0-5 catalog:**

The old angle names conflated distinct operators. The hardware P5 bypass is a
pure cyclic permutation `(F,G,H)=(0,1,0)`, while `(-1,2,2)/3` is a separate
determinant-1 period-2 circulant. The release table uses explicit closure
semantics instead of relying on angle labels.

| ROTC angle | Name | F | G | H | Period | Inverse |
|---:|---|---:|---:|---:|---:|---:|
| 0 | identity | 1 | 0 | 0 | 1 | 0 |
| 1 | thirds period-6 | 2/3 | 2/3 | -1/3 | 6 | 4 |
| 2 | P5 forward cycle | 0 | 1 | 0 | 3 | 5 |
| 3 | thirds period-2 | -1/3 | 2/3 | 2/3 | 2 | 3 |
| 4 | thirds period-6 inverse | 2/3 | -1/3 | 2/3 | 6 | 1 |
| 5 | P5 inverse cycle | 0 | 0 | 1 | 3 | 2 |

At ROTC angle 2, `bypass_p5` can trigger the pure bit-permutation with zero
multiplies:

```
B' = D
C' = B
D' = C
```

Angle 5 is the reverse cycle:

```
B' = C
C' = D
D' = B
```

Legacy table audit:

- angle 2 was documented with thirds coefficients while hardware bypassed it as
  P5 permutation;
- angle 3 used `(-1,-1,-1)/3`, which is singular (`det=0`);
- angle 5 duplicated angle 1 instead of providing an inverse/reverse operation.

---

## Type 2: Curve Segments

### 2.1 Circular Arc (`ARC`)

```
circular_arc(center: QuadrayVector, point: QuadrayVector,
             axis_id: int, pell_count: int) -> List[QuadrayVector]

Implementation: pell_rotate() repeated pell_count times on (point - center),
                then add center back.
```

Generates exact rational points on a circle in quadrance space. Each step
is a Pell rotor r = (2+√3) applied to the offset vector. After 12 steps
(r¹² ≈ one full rotation), the point returns to within Pell-step precision.

The circle is not a Euclidean circle — it's the Pell orbit, which is the
rational analogue. Quadrance to center is preserved: Q(point, center) is
invariant under Pell rotation because r has unit quadrance.

**Test:** 12 Pell steps on (0,1,0,0) with center (0,0,0,0) returns to
within 1 LSB of the start point.

### 2.2 Linear Segment (`LINE`)

```
linear_segment(p0: QuadrayVector, p1: QuadrayVector, steps: int) -> List[QuadrayVector]

Implementation: spread-based interpolation.
  s_total = spread(p0, p1)                              // rational in Q(√3)
  for k in 0..steps:
      t_num = k, t_den = steps                          // rational parameter
      p_k = lerp_spread(p0, p1, t_num, t_den)           // see Type 4
```

The interpolation parameter t = k/steps is rational, not floating-point.
At each step, the intermediate point is in Q(√3).

**Test:** `linear_segment(p0, p1, 1)` returns exactly `p1`. `linear_segment(p, p, n)` returns `[p]*n`.

### 2.3 Helical Segment (`HELIX`)

```
helical_segment(axis_vertex: QuadrayVector, offset: QuadrayVector,
                axis_id: int, pell_count: int, octave_walk: int) -> List[QuadrayVector]

Implementation: circular_arc on offset, plus linear translation along axis
                scaled by octave_walk per step.
```

Combines Pell rotation (in the plane perpendicular to axis) with linear
translation (along the axis direction). The octave_walk parameter controls
the pitch: each full octave (8 Pell steps) advances by one translation unit
along the axis.

**Test:** octave_walk=0 recovers circular_arc exactly.

---

## Type 3: Kinematic Chains

### 3.1 Forward Kinematics (`FK`)

```
fk_chain(base: QuadrayVector, joints: List[(axis_id, F,G,H)]) -> QuadrayVector

Implementation: compose F,G,H circulant rotations from base outward.
  v = base
  for (axis, F, G, H) in joints:
      v = circulant_rotate(v, F, G, H)   // apply joint rotation
  return v
```

Each joint is specified by its rotation axis (which ABCD vertex) and its
F,G,H coefficients. The chain composes n rotations into one final position.

The ABCD-native nature means no coordinate conversion between joints —
every intermediate is a QuadrayVector in Q(√3).

**Test:** Identity chain (F=1, G=0, H=0 at every joint) returns base.
Two-joint chain with 120° at D and 120° at D equals 240° at D (group
closure of A₄ subgroup).

### 3.2 Jacobian via Spreads (`JAC`)

```
jacobian_spread(chain: List[(axis_id, F,G,H)], joint_i: int) -> RationalSurd

Implementation: numerical derivative using spread, not angle.
  Perturb joint_i by one Pell step; measure spread of end-effector displacement.
  Return spread / Pell_step_spread as exact rational fraction.
```

The Jacobian relates joint velocity to end-effector velocity. In the
rational framework, "velocity" is replaced by spread rate — the rate of
change of quadrance. No atan2, no sin/cos, no division.

**Invariant:** Jacobian entries are always in Q(√3) because the forward
kinematics is in Q(√3) and the spread formula uses only field operations.

---

## Type 4: Interpolation

### 4.1 Spread Linear Interpolation (`SLERP`)

```
lerp_spread(p0: QuadrayVector, p1: QuadrayVector,
            t_num: int, t_den: int) -> QuadrayVector

Implementation:
  For each ABCD component i:
    p_i = p0[i] + (p1[i] - p0[i]) * t_num // t_den    // rational scaling
```

The parameter t = t_num/t_den is an exact rational. The result is in Q(√3)
because RationalSurd is closed under addition, subtraction, and rational
scaling (integer multiplication, integer division — but division here is
by t_den which is an integer, so result stays rational).

**Test:** `lerp_spread(p0, p1, 0, 1) = p0`, `lerp_spread(p0, p1, 1, 1) = p1`.

### 4.2 Cayley NLERP (`CNLERP`)

```
cayley_nlerp(rotor_a: (F,G,H), rotor_b: (F,G,H),
             t_num: int, t_den: int) -> (F,G,H)

Implementation (Thomson §10, Table 4):
  Convert each rotor to Cayley vector: r = tan(θ/2) · axis_direction
  Interpolate in Cayley space: r_t = lerp(r_a, r_b, t)
  Convert back to F,G,H coefficients.
  Fallback: if rotors are antipodal (t_num/t_den near 1/2 causing
  Cayley singularity), use Hamilton product composition instead.
```

Cayley NLERP is rational in the bulk — the Cayley vectors are rational
functions of the spread, and interpolation is linear. The only sqrt is
in the fallback at antipodal endpoints (Thomson §10: "only the antipodal
fallback uses one √"). For SPU, the fallback switches to the Hamilton
half-angle product which is bilinear and surd-free.

**Invariant:** Interpolated rotor satisfies F³+G³+H³−3FGH = 1 (the
circulant determinant condition).

---

## Type 5: Correction

### 5.1 Trajectory Error → RPLU (`CORR`)

```
rplu_trajectory_correct(commanded: QuadrayVector,
                        actual: QuadrayVector) -> QuadrayVector

Implementation:
  error = commanded - actual                        // QuadrayVector in Q(√3)
  error_quadrance = Σ component.quadrance()          // scalar in Q(√3)
  rplu_addr = hash_to_rplu(error_quadrance)          // index into RPLU table
  correction = rplu_lookup(rplu_addr)                // pre-computed correction
  return commanded + correction                      // corrected target
```

The RPLU table is loaded at boot from flash (see `docs/rplu_bringup_guard.md`).
For trajectory correction, the table maps quadrance error magnitudes to
correction vectors. The table is pre-computed from simulation: for each
error bin, the correction is the inverse of the average observed drift.

**Table sizing:** Given max error ε_max quadrance and bin width τ, table
size = ε_max / τ entries. For robotics, τ = 1 LSB (Q12 fixed-point) gives
∼ 4096 entries for a 12-bit error range — fits in one BRAM18 block.

### 5.2 Davis Snap Check (`SNAP`)

```
davis_snap(manifold: Manifold13) -> bool

Implementation:
  total = Σ manifold.qr[i].quadrance() for i in 0..12
  return total == 0                                 // bit-exact zero test
```

After each trajectory step, SNAP checks that the 13-axis manifold sum is
exactly zero. Non-zero ⇒ Cubic Leak ⇒ trigger Henosis (one-cycle correction).
This is the rational analogue of renormalization in quaternion pipelines,
but it's a binary pass/fail check, not an approximate fix.

---

## Type 6: Delta Curves — Triple Quadrance Relations

The rational-trigonometry analogue of the cosine rule and Pythagorean theorem.
All operations are integer multiplication/addition — no square roots, no division.

### 6.1 Triple Quadrance Formula (`TQF`)

```
triple_quadrance(Q1: int, Q2: int, spread_s3: tuple) -> (int, int)

Wildberger, Divine Proportions Ch.5.  For quadrances Q₁, Q₂ meeting
at spread s₃ (opposite Q₃):
    (Q₃ − Q₁ − Q₂)² = 4·Q₁·Q₂·(1−s₃)

Since s₃ = sin²θ, we have 1−s₃ = cos²θ, giving:
    (Q₃ − Q₁ − Q₂)² = 4·Q₁·Q₂·cos²θ

This is the exact rational form of c² = a² + b² − 2ab·cos θ.
We never take the square root — we compare squared values.
```

### 6.2 Right Triangle (Pythagorean Analogue)

```
is_right_triangle(Q1: int, Q2: int, Q3: int) -> bool

For spread s₃ = 1 (right angle at vertex opposite Q₃):
    (Q₃ − Q₁ − Q₂)² = 0
    ⇒ Q₃ = Q₁ + Q₂         (exact integer addition)

No square root, no approximation. In the IVM lattice, quadrances
are exact integers. The hypotenuse quadrance is the sum of the
leg quadrances — the Pythagorean theorem without Pythagoras.
```

### 6.3 Delta Parameterization (`DELTA`)

```
delta_curve(Q1: int, Q2: int, spread_steps: int) -> List[(int, int)]

Parameterize triangles with fixed side quadrances Q₁, Q₂ as spread
varies from 0 (collapsed, Q₃=|Q₁−Q₂|) to 1 (right, Q₃=Q₁+Q₂).
At each step k ∈ {0, …, spread_steps}:
    s₃ = k / spread_steps  (rational spread)
    rhs_sq = 4·Q₁·Q₂·(spread_steps−k) / spread_steps
    Q₃ = Q₁ + Q₂ ± √(rhs_sq)  ← compare squared, never sqrt

The ± resolves via polarity: p=+1 for acute (subtract √), p=−1
for obtuse (add √). Each curve is a discrete rational family of
triangles — the "delta" is the discriminant 4·Q₁·Q₂·(1−s₃).
```

### 6.4 Spread from Three Quadrances (`SPREAD3`)

```
spread_from_quadrances(Q1: int, Q2: int, Q3: int) -> (int, int)

Inverse: given three quadrances, compute spread at vertex opposite Q₃.
    numer = 4·Q₁·Q₂ − (Q₃ − Q₁ − Q₂)²
    denom = 4·Q₁·Q₂

Returns (numer, denom) — exact rational, never divided.
Invariant: 0 ≤ numer ≤ denom (spread ∈ [0,1]).
numer=0 → parallel; numer=denom → perpendicular.

**Use in SPU:** Given two link quadrances and end-effector quadrance
from FK, compute joint spread. Given joint spread and two link
quadrances, compute reachable workspace quadrance bounds.
```

---

## Assembly: A Simple Robot Arm

A 2-joint planar arm in ABCD space, demonstrating all five types:

```
# Setup
base   = QuadrayVector(RS(0), RS(1), RS(0), RS(0))    # origin on B-axis
joint0 = (axis_id=3, F=2/3, G=2/3, H=-1/3)            # D-axis, 60°
joint1 = (axis_id=1, F=2/3, G=-1/3, H=2/3)             # B-axis, 240°
chain  = [joint0, joint1]

# Forward kinematics
elbow  = fk_chain(base, [joint0])
wrist  = fk_chain(base, [joint0, joint1])

# Trajectory: circular arc from current wrist position
arc_pts = circular_arc(center=elbow, point=wrist, axis_id=3, pell_count=12)

# Correction after each arc step
for pt in arc_pts:
    corrected = rplu_trajectory_correct(commanded=pt, actual=pt)  # mock sensor
    stable = davis_snap(corrected)                                 # laminar check
    assert stable, "Cubic Leak detected — Henosis triggered"
```

---

## Implementation Targets

| Layer | File | What |
|---|---|---|
| Python Reference | `software/lib/rational_robotics.py` | Exact rational robotics oracle with inverse closure |
| Python Tests | `software/tests/test_rational_robotics.py` | Pell, circulant, FK, arc, and six-step trace closure tests |
| C++ Reference | `software/common/include/spu_rational_robotics.h` | C++17 exact rational robotics oracle |
| C++ Tests | `software/common/tests/spu_rational_robotics_test.cpp` | C++ parity for closure and six-step trace tests |
| Trace Tool | `tools/rational_robotics_trace.py` | Exact JSON output for six-step visualizer and RTL vectors |
| Python VM | `software/spu_vm.py` | Type 1–5 primitives as VM methods/instructions |
| C++ IVM Core | `software/common/include/spu_ivm.h` | Corresponding low-level C++17 primitives |
| Hardware (exists) | `spu_rotor_vault.v`, `spu13_rotor_core.v` | Type 1 in silicon |
| Hardware (new) | `spu_robotics_inverse.v` | Pell inverse and F/G/H inverse coefficient path |
| Hardware (new) | `spu_robotics_fk.v` | Forward/inverse chain execution |
| Hardware (new) | `spu_rplu_trajectory.v` | Type 5: dedicated RPLU port for trajectory error |
| Test suite | `software/programs/rational_curves_test.sas` | Lithic-L test program exercising all primitives |
| RPLU table gen | `tools/build_rplu_trajectory_table.py` | Pre-compute correction tables from simulation data |

### RTL Handoff Order

1. Mirror the software oracle exactly in an RTL testbench fixture.
2. Implement Pell inverse closure first: multiply by `(2,1)`, then `(2,-1)`,
   and assert exact recovery.
3. Implement F/G/H inverse coefficient generation for determinant-1 circulants.
4. Implement single-joint forward/inverse closure.
5. Implement short FK chain forward/inverse closure.
6. Mirror the six-step trace from `tools/rational_robotics_trace.py` in an RTL
   fixture: phases 0-4 must not close, phase 5 must close, and every phase must
   pass inverse-balance.
7. Only after closure is proven, add RPLU trajectory correction and real sensor
   error bins.

---

## Design Rules

1. **No float. No division. No transcendentals.** Every intermediate value is a RationalSurd.
2. **Bit-exact zero tests, not epsilon comparisons.** Davis Gate SNAP checks Σ == 0, not |Σ| < ε.
3. **RPLU is the only approximate component.** The RPLU table maps continuous errors to discrete corrections — this is the boundary between exact math and real-world sensor noise.
4. **Dispatch to the most rational primitive available.** Pell rotor for 60° multiples; F,G,H circulant for basis-axis arbitrary angles; Cayley NLERP for interpolation; fallback to Hamilton product only at the antipodal singularity.
5. **Hardware matches simulation bit-for-bit.** Every Python VM test vector must produce the same RationalSurd values that the Verilog testbench observes.

---

*CC0 1.0 Universal — public domain*
