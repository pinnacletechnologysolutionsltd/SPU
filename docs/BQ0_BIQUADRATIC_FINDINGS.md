# BQ-0: Q(√3,√5) software oracle — findings

Status: software-oracle PASS (simulation-only; no RTL, no silicon claim).
Source: `software/lib/biquad_q.py`; test: `software/tests/test_biquad_q.py`
(`python3 software/tests/test_biquad_q.py`; registered in `run_all_tests.py`).

## Bases
* Rational basis `[1, √3, √5, √15]` — internal storage, `Fraction` coefficients.
* Golden basis `[1, √3, φ, √3φ]`, φ=(1+√5)/2. R→G: `(a−c, b−d, 2c, 2d)`;
  G→R: `(A+C/2, B+D/2, C/2, D/2)`. Round-trips exactly (20,000 seeded cases).

## Integral-ring distinction
The golden basis spans the full ring of integers ℤ[√3]⊗ℤ[φ] (discriminants 12
and 5 are coprime). `{1,√3,√5,√15}` spans an index-4 sublattice, so it misses
φ and √3φ. `is_integral()` tests golden coordinates being integers.

## Norm and inverse (characteristic 0)
* `N(x)` = product of the four conjugates; rational, multiplicative, and
  `N(x)=0` iff `x=0`: there are no zero divisors.
* `inv(x)` = product of the three non-identity conjugates / `N(x)`; exact.
  Only units (|N|=1, e.g. φ, 2+√3) have integral inverses; e.g. `inv(√5)` has
  denominator 5 (N=25). Division is not closed over the integers.
* Fixtures: N(1+√3+√5)=−11, N(√5)=25, N(1+√3)=4, N(2+√3)=1.

## Contrast with A₃₁
A₃₁ = F_p[x,y]/(x²−3,y²−5), p=M₃₁, is a split algebra: 3 and 5 are non-residues
but 15 is a residue, so it has zero divisors and non-invertible nonzero
elements, trapped by `FLAGS.V`. The characteristic-zero field here has none.
Do not reuse either invertibility contract for the other. A₃₁ is unchanged.

## Not done
No fixed-width/overflow semantics, ISA, RTL, or Golden Core integration. A
scratchpad measurement (not in the fixture) put a 64-bit-input product
coefficient near 131 bits.
