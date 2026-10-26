# GC-FIELD-0: A4 lattice, Z[φ] coefficients, fivefold plane

2026-10-23. Software-only mathematical audit; exact int/Fraction arithmetic; no floats.
Reproduce: `python3 research/gc_field0/verify_gc_field0.py` (29 checks, all PASS at write time).
No performance, width, timing or area claim. No ISA/RTL/CPU/GPU/simulator/Golden-Core/QCG-0/CI change.
Physical integration is unresolved pending separate width, parity, timing and area evidence.

## Classification

"Value" is the algebraic object; "encoding" is the integer coefficients that represent it.

| Operation | Value domain | Encoding / retained state | Minimal domain |
|---|---|---|---|
| A4 root lattice, 4D quadrance, inner product | Z | 5 integers (sum 0) or 4 simple-root coords; Gram = integer Cartan matrix | integer |
| Order-5 cyclic coordinate shift | lattice automorphism | integer 4×4 in simple-root basis (verified order exactly 5) | integer permutation |
| Fixed multiplication by φ | Z[φ] | pair (a,b) ↦ (b, a+b): swap and add. Equivalently the integer 4×4 matrix T = I + C + C⁻¹ on A4 (T² = T + I verified, acts as φ on the plane) | integer |
| General Z[φ] product | Z[φ] | (a,b)(c,d) = (ac+bd, ad+bc+bd); equals (p+q, r−p) with p=ac, q=bd, r=(a+b)(c+d). Verified equal | integer coefficient products; no division |
| Conjugation (√5 → −√5) | Z[φ] | (a,b) ↦ (a+b, −b), ring automorphism (verified) | integer |
| Norm | Z | a²+ab−b²; multiplicative; φ is a unit of norm −1 | integer |
| Inverse of a non-unit | Q(√5) | needs denominator N(x); e.g. 2 has norm 4 | rational, not Z[φ] |
| φ-basis ↔ √5-basis | Q(√5) | a+bφ = (2a+b)/2 + (b/2)√5; x+y√5 = (x−y) + 2yφ. Z[φ] = half-integer pairs with matching parity (b odd ⇔ half-integers); Z[√5] is the index-2 subgroup (b even). Round trip and product agreement verified | denominator 2 and a parity constraint in the √5 basis |
| Planar quadrance |z₁|² of a lifted point | ½Z[φ] | 2|z₁|² = (2Σv² − S₁) + (S₁ − S₂)φ, S₁ = 2Σvⱼvⱼ₊₁, S₂ = 2Σvⱼvⱼ₊₂ (cyclic). Verified against independent Z[ω] arithmetic | Q(√5), irrational in general |
| Planar Cartesian coordinates | Q(ζ₅) real/imag parts | y ∈ sin72°·Z[φ] | outside Q(√5) |

## Key results

- **Intrinsic vs projected quadrance (trace identity).** For v in A4 with 2|z₁|² = a + bφ,
  the 4D quadrance equals (2a + b)/5 = (2/5)·Tr(|z₁|²), the trace of the planar quadrance down to Q. Verified on
  every sum-zero vector with entries in [−2,2]. The rational metric is the Galois trace of the irrational one.
- **φ-scaling is an integer matrix on the lifted lattice** but it is not a 4D isometry or similarity (quadrance
  ratio varies); it scales the plane by φ and the conjugate plane by φ′ = −1/φ. The projected quadrance scales by
  exactly φ² (verified).
- **Selectivity of symmetries.** The integer automorphisms of the A4 lattice number exactly 240 (S₅ × ±1, by
  exhaustive search over images of simple roots). Only 20 (D₅ × ±1) preserve the planar quadrance; 220 preserve the 4D
  quadrance but change the planar one.

## Negative results (preserved)

- Planar quadrance of a root, e.g. (1,−1,0,0,0): intrinsic 4D quadrance 2, planar value has a nonzero φ part.
  The A₂ trick does not transfer: cos72° = (√5−1)/4 is irrational, so the planar metric is irrational in every basis.
- Planar Cartesian y needs sin72°; its square (5+√5)/8 has norm 5/16, not a rational square, so sin72° ∉ Q(√5).
  The (5+√5)/8 value is derived by hand, not checked by the script; the norm arithmetic is.
- No integer 2×2 matrix with entries in [−6,6] has order 5. This is a bounded search; the general reason is that
  an order-5 rational matrix needs the degree-4 cyclotomic polynomial, so rank ≥ 4.
- Lattice-preserving maps that are planar isometries are only D₅ × ±1: the lifted lattice admits no 60° or 90° planar rotation.
- Non-units have no inverse in Z[φ].

## Limits

Test set: sum-zero vectors with entries in [−2,2] (and norm ≤ 4 for the automorphism comparison); Z[φ] grid [−4,4]².
No claim about which of these operations a datapath should implement. Open: width and overflow behavior of
integer encodings, parity handling at a φ/√5 boundary, and whether the 4D lift is worth its extra storage.
Those need separate evidence.
