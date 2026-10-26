# H2 — Exact hex-lattice refinement enumeration

2026-10-20. Class A host-only experiment (AGENTS.md §4.3,
[execution policy](../../spu_strategy/RESEARCH_EXECUTION_POLICY.md)), selected by
the owner from hypothesis H2 of the
[knowledge archaeology review](../../docs/KNOWLEDGE_ARCHAEOLOGY_2026-10-20.md).
**Result: CONFIRMED within the tested patch and proved in general below.**
9 test groups passed, exit 0, 0.21 s wall time. One negative control was
mis-specified on the first run and corrected (see Limitations). There were no other failures.
No RTL, simulator, ISA or evidence change was made.

```bash
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/h2_hex/test_h2.py'
cd research/h2_hex && python3 -I -c "import sys; sys.path.insert(0,'.'); import experiment as X, json; print(json.dumps(X.run(6), default=str))"
```

Limits: 60 s wall time, 1 GiB address space, no network, no installation, no child processes
other than the shell wrapper. All arithmetic uses Python `Fraction` over Q(√3), with no floating point.

## Setup

L = Z[ω], ω = (−1+√−3)/2, unit edge. a+bω ↦ (a − b/2, (b/2)√3), so coordinates
lie in Q(√3). Patch: |a|, |b| ≤ 6 (169 points). Lattice membership (`from_cart`) is
read back from the Q(√3) parts of the coordinates. It does not use the multiplication code.

## Results (patch radius 6)

| Operator | Class | Index | scale² | Nonzero images on L |
|---|---|---:|---|---:|
| ×(1+ω) (unit, control) | lattice automorphism | 1 | 1 | 168/168 |
| ×(1−ω) | sublattice similarity (aperture 3) | 3 | 3 | 168/168 |
| ×2 | sublattice similarity (aperture 4) | 4 | 4 | 168/168 |
| ×(3+ω) | sublattice similarity (aperture 7) | 7 | 7 | 168/168 |
| Pell ×(2+√3) | algebraic dilation, not lattice | — | 7+4√3 | **0** |
| Pell ×(2−√3) | algebraic dilation, not lattice | — | 7−4√3 | **0** |
| Cayley rotation, t = 2−√3 | Euclidean rotation, not lattice | — | 1 | **0** |

Identities verified exactly:
- Each index computed from the integer matrix equals the norm N(z) = a² − ab + b². It also equals the number of residue classes of L/zL, counted independently from z̄·p mod N.
- Multiplication computed in Eisenstein coordinates matches the Cartesian matrix on all 169 points.
- The inverse z̄/N(z) is exact over Q(ω). On L it is defined exactly on zL: the points it maps back onto L are exactly the points of zL.
- Cayley t = 2−√3 gives cos = √3/2 and sin = 1/2, so the rotation is 30°. Its order is exactly 12. Its inverse is Cayley(−t).
- R30² = ×(1+ω), the 60° lattice unit.
- ×(1−ω) = √3·R(−30°) and ×(2+ω) = √3·R(+30°).
- Composing half-angle parameters: compose(t, t) = √3/3 = tan 30°, which yields R30². This differs from t² = u⁻², so **Pell powers are not the composition law of these rotations**.
- Pell: u·u⁻¹ = 1 exactly. Field norm N(uⁿ) = 1 for n = 1..8, so the Pell/AOR algebraic identity holds. The real scale² u²ⁿ has a nonzero √3 part for every n tested.
- No map Pell∘R30ᵏ (k = 0..11) preserves L.

Negative controls (all must and do behave as stated):
- Rational scale 2 is accepted as lattice-preserving.
- A mutant membership test that reads only the rational part of x and the √3 part of y classifies Pell as lattice-preserving. This shows the real check is what excludes Pell.
- A sign-flipped "rotation" does not close after 12 steps.
- Residue keys without the modulus overcount the index.

## Proofs (general, not reliant on the enumeration)

**P1 — Eisenstein similarities.** An orientation-preserving similarity S with S(L) ⊆ L
is v ↦ zv with z = S(1) ∈ L. An orientation-reversing one is v ↦ z·v̄, since conj(L) = L.
Its index is |det| = N(z). So the aperture-3, 4 and 7 refinements are exactly multiplication by
elements of norm 3, 4 and 7, and they are closed under composition (norms multiply).

**P2 — No Pell level preserves any hex lattice.** Suppose S is any affine similarity of
scale λ (any rotation, reflection or translation) with S(L) ⊆ L. Then S(1) − S(0) is a nonzero
lattice vector of quadrance λ². Every lattice quadrance is the integer a² − ab + b², so
λ² ∈ Z. For λ = uⁿ with n ≠ 0, λ² = u²ⁿ = a + b√3 with b ≠ 0: Pell coefficients satisfy
b₋ₖ = −bₖ and bₖ > 0 for k > 0. Hence λ² ∉ Q, a contradiction. The same argument gives
L ⊄ uⁿL, since that would need u⁻ⁿL ⊆ L. It also gives **uⁿL ∩ L = {0}**: if z = uⁿw with z, w ∈ L
both nonzero, then u²ⁿ = N(z)/N(w) ∈ Q. Sublattices of L inherit integer quadrances, so no
Pell level maps L into any sublattice either.

**P3 — R30 meets L only at the origin.** By P1's identity, R30 = (×(2+ω))/√3, so
R30(L) ⊆ L/√3 = (√3·L)/3. Points of L have x ∈ Q and y ∈ √3·Q. Points of √3·L have x ∈ √3·Q and
y ∈ Q. The two forms can only both hold at the origin. So R30(L) ∩ L = {0}: R30 maps L onto the
30°-rotated lattice, which is the aperture-3 relationship.

**Remaining assumptions.**
- The plane is the exact Euclidean plane, and "preserve" means the image lies in the lattice. Scaling the lattice does not matter, because all arguments use ratios of quadrances.
- P1 is the standard classification of lattice similarities of Z[ω], stated here rather than re-derived.
- Nothing is claimed about grids other than hexagonal ones, ownership rules for overlapping cells, or memory placement.

## Disposition

| Hypothesis | Result |
|---|---|
| Eisenstein multipliers 1−ω, 2 and 3+ω are exact refinements of index 3, 4 and 7 | **CONFIRMED** (proof P1 + enumeration) |
| Real Pell scaling preserves the hex lattice or any sublattice | **FALSIFIED** (proof P2; patch: 0 of 168 nonzero points) |
| Pell-scaled grids nest with the base grid | **FALSIFIED**: they share only the origin (P2) |
| t = 2−√3 generates an exact 12-fold Euclidean rotation in Q(√3) | **CONFIRMED** |
| That rotation is a lattice automorphism | **FALSIFIED**: only its square is (P3) |
| Pell powers compose these rotations | **FALSIFIED**: composition is tangent addition |

Claim boundary: these are lattice-geometry facts. They say nothing against
Pell/AOR **algebraic composition**: the field-norm identity N(uⁿ) = 1 holds, and
AOR-1 Phase A, Pell Octave and ROTC evidence are untouched and not reinterpreted.
They only assign roles. Use Z[ω] multipliers for grid refinement, the Cayley 30°
rotation for exact 12-fold orientation, and Pell/AOR for exact algebraic scale
labels whose grids do not nest. No GPU, memory-placement or hardware claim follows.

Limitations: one finite patch; a Python reference only, with no independent second
implementation. On the first run, the mutant-membership control was mis-specified: it ignored
only the √3 part of x, and Pell's image of ω is also rejected through y. The control was
corrected to read only the "expected" component of each coordinate. No experimental
assertion changed.
