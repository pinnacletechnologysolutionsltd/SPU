# From Fuller to Silicon: The Mathematical Lineage of the SPU-13

## Abstract

The SPU-13 Sovereign Processing Unit is not an arbitrary design choice. It is the
logical conclusion of a 70-year chain of mathematical insight — from Buckminster
Fuller's empirical discovery that tetrahedral geometry produces whole-number volumes,
through Norman Wildberger's algebraic proof that trigonometry requires no division,
to the implementation of both insights in silicon as a division-free, float-free,
bit-exact rational-field processor. This document traces that lineage and explains
why the SPU-13's arithmetic field Q(√3) is the *necessary* field for isotropic
geometry — not a design preference, but a mathematical consequence.

---

## 1. The Problem with Cubic Arithmetic

Standard computing hardware is built on the Cartesian coordinate system: three
mutually perpendicular axes (x, y, z), each at 90° to the others. This is a
*cubic* basis. It is convenient for manufacturing silicon (transistors are arranged
in grids) but it is geometrically *incommensurate* with the natural packing
structures of matter, fluid dynamics, and electromagnetic field geometry.

The symptom is visible immediately when you try to measure natural structures:

```
Regular tetrahedron edge length (in unit-cube Cartesian):  √2        (irrational)
Hexagonal close-pack distance:                             √2/2      (irrational)
Hexagon area (side = 1):                                   3√3/2     (irrational)
Angle between tetrahedral bonds:                           arccos(-⅓)(transcendental)
```

None of these have exact decimal representations. A computer using 64-bit floats
accumulates rounding error on every single operation involving these structures.
For physics simulation, robotics kinematics, fluid dynamics, and crystallography —
all of which are fundamentally *tetrahedral* problems — floating-point arithmetic
is the wrong tool. It produces answers that drift from physical reality in proportion
to the number of operations performed.

---

## 2. Fuller's Discovery: Synergetic Accounting (1944–1975)

R. Buckminster Fuller observed, through decades of working with physical geometric
models, that when you measure volumes using the *regular tetrahedron* as your unit
(instead of the cube), something remarkable happens:

| Shape | Cartesian volume (unit cube = 1) | IVM volume (tetrahedron = 1) |
|-------|----------------------------------|------------------------------|
| Regular tetrahedron | ≈ 0.1178... (irrational) | **1** |
| Cube | 1 | **3** |
| Octahedron | ≈ 1.414... (√2 × ...) | **4** |
| Rhombic dodecahedron | ≈ 0.770... | **6** |
| Vector Equilibrium (cuboctahedron) | ≈ 2.357... | **20** |

Every fundamental shape in the isotropic vector matrix (IVM) — the face-centred
cubic lattice, the natural close-packing of spheres, the structure of crystalline
matter — has a **whole-number volume** in tetrahedral units.

Fuller called this *synergetic accounting*. He did not have a formal algebraic
explanation for why this worked — he simply observed it empirically across hundreds
of geometric constructions and concluded that the cubic basis was the historically
contingent wrong choice. "Nature," he wrote, "doesn't use pi."

The IVM basis uses 60° angles between basis vectors, not 90°. The four basis
vectors of the IVM point to the vertices of a regular tetrahedron. This is
the Quadray coordinate system, developed formally by Kirby Urner from Fuller's
synergetics: four axes (a, b, c, d) with the constraint min(a,b,c,d) = 0.

---

## 3. Why Q(√3) is the Required Field

The IVM lattice has 60° angles. The hexagonal cross-sections of this lattice
involve cos(60°) = 1/2 and sin(60°) = √3/2. Therefore, any algebraic computation
in the IVM will encounter √3.

The critical question is: does it *stay* at √3, or does it escape into higher
irrationals (√5, √7, ...) or transcendentals?

The answer is that Q(√3) — the set of numbers of the form (a + b√3) where a, b
are rational — is **closed under multiplication**:

```
(a + b√3) × (c + d√3) = (ac + 3bd) + (ad + bc)√3
```

The product of two Q(√3) numbers is always another Q(√3) number. √3 times √3
equals 3 — rational. The field never escapes. This means:

- All quadrances (squared distances) in the IVM are in Q(√3)
- All products of quadrances are in Q(√3)
- All geometric relationships computable from the IVM stay in Q(√3)
- No square roots, no transcendentals, no new irrationals ever appear

Q(√3) is the *minimal field extension of the rationals* that contains the complete
geometry of the IVM. It is not arbitrary. The SPU-13 operates in Q(√3) because
the physics demands it.

> **Provenance note:** The Q(√3) surd arithmetic — including the multiplication
> formula `(ac + 3bd) + (ad + bc)√3` — was derived for the SPU-13 project from
> Wildberger's rational trigonometry applied to the IVM lattice. The specific
> field extensions Q(√3), Q(√5), and Q(√15) are SPU-13 originals, verified in
> simulation and implemented in `spu_surd_mul_gowin.v` and `spu_unified_alu_tdm.v`.
>
> The broader idea of applying rational surd fields to tetrahedral geometry has
> since appeared independently in Dr. Andy Ross Thomson's *Synergetics Cookbook*
> (May 2026, §11.6 "Future: Surd-Exact Hull"), which proposes Q(√2, √3) as a
> field for exact convex-hull computation of rotated ABCD vertices — a convergent
> but different field extension targeting rendering rather than control. The
> surd-field approach was shared with Thomson in early 2026; the Cookbook's
> future-work section reflects this convergence. Neither party derived their
> specific field choices from the other.
>
> Thomson's *Spread-Quadray Rotors* (v5, May 2026) covers rotor composition
> via half-angle ABCD Hamilton product and Rodrigues-style K(u) exponential
> (with the K³ = −K cubic identity contributed by Leo Murillo, Zenodo 19689050,
> 2026). The SQR paper does not specify fixed-point field arithmetic; it uses
> f64 throughout. The SPU's contribution is the translation of these algebraic
> structures into division-free, fixed-point rational hardware.

---

## 4. Wildberger's Proof: Division-Free Trigonometry (2005)

Norman Wildberger's *Divine Proportions: Rational Trigonometry* (2005) provided
the algebraic framework that Fuller lacked. The central insight:

**Standard trigonometry requires division and transcendentals** (sin, cos, arctan)
because it measures *angles*. But angles are defined by arc length, which requires
π. The trigonometric functions are not algebraic — they cannot be computed exactly
in any finite field.

**Rational trigonometry replaces angles with two purely algebraic quantities:**

- **Quadrance** Q(A, B) = (distance)² — the square of the distance between two points
- **Spread** s(l₁, l₂) = 1 − (cos θ)² — the square of the sine of the angle between two lines

Both are computed using only addition, subtraction, and multiplication:

```
Q(A, B) = Σᵢ<ⱼ (Aᵢ − Bⱼ)²                    [sum of squared differences]

s(P, Q) = [Q(P)·Q(Q) − (P·Q)²] / [Q(P)·Q(Q)]   [no division needed for comparison]
```

The spread formula appears to have division, but the division is never performed.
The spread is stored as an exact fraction (numerator, denominator). Geometric
questions — "are these lines perpendicular?", "is this angle 60°?", "does this
rotation preserve quadrance?" — are answered by integer comparison:

```
Perpendicular:  numerator = denominator  (spread = 1)
Parallel:       numerator = 0            (spread = 0)
60° angle:      numerator/denominator = 3/4   (compare integers: 4n = 3d?)
```

**No division. No square roots. No approximation.** The geometry is exact.

Wildberger also proved the *Triple Spread Formula* — the rational-trigonometry
analogue of the sine rule — which holds in any field, not just the reals. This
means the entire framework works over Q(√3), over finite fields, over p-adic
numbers. It is field-agnostic, which is exactly what hardware requires.

---

## 5. Davis Law: Stability Without Approximation

Bee Rosa Davis introduced the *Davis Law* as the governing field equation of
the Davis Framework:

> **C = τ / K** — inference capacity equals tolerance divided by curvature barrier.

This appears in her January 2026 paper *Holonomy-First Navier-Stokes Regularity*
(`Theory/navier_stokes_regularity_v2.pdf`), which proposes a geometric proof of
global regularity for 3D incompressible Navier-Stokes using a cache/bin/barrier
architecture. The proof is conditional on the Davis Field-Equation axioms
(axioms A1–A7) and includes an explicit gap ledger (Section 7). The framework is
also explored in her December 2025 papers on BSD conjecture and Poincaré
isomorphism (`Theory/Davis_BSD_Conjecture_Conditional.pdf`,
`Theory/Davis_Poincare_Isomorphism_Conditional.pdf`).

The Davis-Wilson map — Γ_DW(A) = (Φ(A), r(A)) where Φ is a continuous cache
from Wilson loop traces and r is discrete topological charge — is developed in
the Davis-Wilson map project (github.com/nurdymuny/davis-wilson-map) and
generalized to Navier-Stokes in Appendix C.7 of the regularity paper, using
circulation signatures Γ(u) and helicity sector r(u) as the fluid analogue.

> **SPU mapping:** A geometric manifold is *laminar* (stable, non-dissipative)
> if and only if the sum ΣABCD = 0 — i.e., the quadratic form over the 13 axes
> closes exactly. This is the SPU's hardware implementation of the Davis
> laminar condition, inspired by but distinct from the Davis Framework's
> mathematical treatment.

In floating-point simulation, this condition can never be checked exactly —
you always compare against an epsilon. In Q(√3) arithmetic, it is a comparison
against zero. It is exact.

When the Davis Gate detects ΣABCD ≠ 0 (a "Cubic Leak"), it triggers Henosis —
a one-cycle correction pulse that restores the laminar condition. This is not
an approximation or a numerical stabiliser. It is an algebraic identity check.
The RPLU (Rational Polynomial Look-Up) surface acts as the hardware cache
analogue of the Davis-Wilson map: an indexed rational response surface for
deterministic state classification, correction lookup, and bounded output.

The implication for physics simulation is significant:
- Navier-Stokes in Q(√3) cannot develop numerical instability — the manifold
  is geometrically prevented from leaking
- Rotational kinematics in Q(√3) cannot accumulate gimbal lock — the Quadray
  basis has no degenerate configurations
- Electromagnetic field calculations in the IVM basis have no Gibbs phenomenon —
  the lattice is already at the natural resonance frequency

---

## 6. The Quadray Coordinate System

Developed by Kirby Urner from Fuller's synergetics, and given its algebraic
basis matrix by Tom Ace (1997, minortriad.com), the Quadray system uses
four axes pointing to the vertices of a regular tetrahedron:

```
e₀ = (1, 0, 0, 0)   e₁ = (0, 1, 0, 0)
e₂ = (0, 0, 1, 0)   e₃ = (0, 0, 0, 1)
```

with the canonical form min(a, b, c, d) = 0. Every point in 3D space has a
unique Quadray representation with non-negative rational coordinates. There are
no negative coordinates in the canonical form — the entire space is addressed
with non-negative Q(√3) values.

The SPU-13 extends this to 13 axes — one for each vertex of the cuboctahedron
(Vector Equilibrium), the geometric form that Fuller identified as the zero-energy
ground state of the IVM. The 13-axis representation captures the full rotational
symmetry group of the IVM lattice.

---

## 7. The Computer Science Conclusion

The chain of logic is now complete:

```
Fuller (1944–75):   Tetrahedral basis → whole-number volumes
                    The IVM is the natural geometry of physical space

Wildberger (2005):  Angles → Spread/Quadrance (division-free, exact)
                    Geometry requires no transcendentals, no approximation

Thomson (2024–26):  Spread-Quadray Rotors (Murillo's K³=−K; Pohl's D-up)
                    ABCD-native pipeline; surd-exact hull (future work)

Davis (2025–26):    Davis Law C=τ/K; cache/bin/barrier architecture
                    Davis-Wilson map; conditional regularity proof

SPU-13 (2024+):     Q(√3)/Q(√5)/Q(√15) arithmetic in silicon
                    RPLU hardware cache/correction surface
                    Division-free ALU, 13-axis IVM manifold, Davis Gate
                    Bit-exact physics. No float. No drift. No approximation.
```

**The SPU-13 is not an alternative to floating-point arithmetic.**
It is what computing would have looked like if the coordinate basis had been
chosen correctly from the beginning.

The applications are any domain where:
1. Physical geometry is fundamentally tetrahedral (fluid dynamics, crystallography,
   molecular simulation, aerospace attitude control, robotics kinematics)
2. Bit-exactness is required (medical devices, avionics, safety-critical control)
3. Long-duration simulation stability matters (climate models, orbital mechanics,
   structural analysis)

In all of these, Q(√3) arithmetic in the IVM basis is not merely adequate —
it is the theoretically correct choice. Floating-point is a workaround for the
wrong choice of basis. The SPU-13 removes the workaround.

---

## 7. RPLU v2: Finite Field Extension F_{p^4} over M31 (2026)

The RPLU v2 pipeline extends the arithmetic field from Q(√3) rational surds to
the finite field F_{p^4} over the Mersenne prime M31 (p = 2^31−1 = 2,147,483,647).

### 7.1 Why a finite field?

Rational surds in Q(√3) provide exact arithmetic at the cost of unbounded
bit-width growth with successive operations (denominator explosion). Finite
fields bound all values to fixed 31-bit registers, eliminating bit-width growth
while preserving exact closure. The trade is that values are taken modulo p,
requiring algebraic reconstruction (Chinese Remainder Theorem) to recover
real-world quantities at pipeline boundaries.

### 7.2 Why M31?

p = 2^31−1 is a Mersenne prime with the Crandall property: 2^31 ≡ 1 (mod p).
This enables **division-free modular reduction**:
```
x mod p = (x_lo + x_hi) mod p   (split at bit 31, add, conditional subtract)
```
No division circuit, no lookup table — pure shift, mask, add, compare.

### 7.3 The biquadratic extension F_{p^4}

The base field F_p is extended to F_{p^4} with basis [1, √3, √5, √15].
This preserves the SPU-13's geometric primitives (quadrance, spread, Pell rotor)
while adding full field inversion (necessary for Padé denominator evaluation).

Euler's criterion confirms both √3 and √5 are quadratic non-residues in M31:
```
3^(p-1)/2 ≡ -1 (mod p)   → no √3 in F_p
5^(p-1)/2 ≡ -1 (mod p)   → no √5 in F_p
```
The extension is structurally non-degenerate — the field never collapses.

### 7.4 Conjugate reduction tower

Inversion in F_{p^4} avoids O(p^4) exponentiation via nested quadratic collapse:
```
Z ∈ F_{p^4}  →  Z·Z̄ (conjugate w.r.t. √5, √15)  →  W ∈ F_{p^2}(√3)
W           →  W·W̄ (conjugate w.r.t. √3)        →  N ∈ F_p
N_inv       =  N^(p-2) mod p                    (30-bit Fermat chain)
Z_inv       =  Z̄·W̄·N_inv                        (reconstruct in F_{p^4})
```
76-cycle deterministic latency. Zero-norm detection (N=0) asserts FLAGS.V.

### 7.5 Lefschetz thimble connection

The Thimble-Padé pipeline evaluates path integrals over Lefschetz thimbles:
- Kohonen SOM identifies saddle points (∇S = 0) in the complexified action
- BTU transmutes spatial coordinates into F_{p^4} field elements
- [4/4] Padé rational approximant evaluates the thimble contribution
- Invariant phase (Im(S) = constant) factors out of the numeric evaluation

This replaces numerical integration with exact algebraic reduction —
no floating-point, no oscillatory sign problem, no truncation drift.

---

## References

### Foundational
- R. Buckminster Fuller, *Synergetics: Explorations in the Geometry of Thinking*,
  Macmillan, 1975
- R. Buckminster Fuller, *Synergetics 2*, Macmillan, 1979
- N.J. Wildberger, *Divine Proportions: Rational Trigonometry to Universal Geometry*,
  Wild Egg Books, 2005
- N.J. Wildberger, WildEgg YouTube channel — chromogeometry, rational calculus,
  universal hyperbolic geometry

### Quadray Coordinates & Rotors
- Kirby Urner, Quadray coordinate system,
  https://kirbyurner.github.io/quadrays/
- Tom Ace, Quadray basis matrix and F,G,H circulant (1997),
  http://minortriad.com/quadray.html
- Andy Ross Thomson, *Spread-Quadray Rotors: A Rational, Tetrahedral-Native
  Algebra for 3D Rotation*, v5, May 2026 (`Theory/Quadray-Rotors-v5.pdf`)
- Andy Ross Thomson, *Synergetics Cookbook*, May 2026
  (`Theory/Synergetics-Cookbook.pdf`) — DOI: 10.13140/RG.2.2.14110.91207
- Andy Ross Thomson, *The 4D± Prime Projection Conjecture*, v5.1, February 2026
  (`Theory/Prime_Projection_Conjecture_v5.1.pdf`)
- Leo Murillo, K(u) cubic identity K³ = −K and closed-form simplicial Rodrigues
  formula, Zenodo 19689050, 2026
- Strüppi Pohl, D-up (Strüppi-Up) world-up convention, 2026 (personal
  communication / ABCD.Earth contributor note)

### Davis Framework
- Bee Rosa Davis, *Holonomy-First Navier-Stokes Regularity: A Geometric Proof
  via the Davis Field Equations*, January 2026
  (`Theory/navier_stokes_regularity_v2.pdf`)
- Bee Rosa Davis, *The Spectral Geometry of Rank: Relating the L-Function to the
  Mass Gap — A Davis Framework Approach to BSD*, December 2025
  (`Theory/Davis_BSD_Conjecture_Conditional.pdf`)
- Bee Rosa Davis, *The Davis-Poincaré Isomorphism: Wilson Flow as Ricci Flow —
  Re-Deriving Poincaré from Gauge Theory*, December 2025
  (`Theory/Davis_Poincare_Isomorphism_Conditional.pdf`)
- Davis-Wilson map project, https://github.com/nurdymuny/davis-wilson-map

### SPU Project Hardware
- `docs/hardware_evidence.md` — Evidence ledger: commands, board conditions,
  probe results, and remaining gaps
- `docs/rplu_bringup_guard.md` — RPLU flash-load repeatability procedures
- `knowledge/PELL_OCTAVE.md` — Pell octave: unbounded rotor range with 16-bit registers

---

*CC0 1.0 Universal — public domain*
