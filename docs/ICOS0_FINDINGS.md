# ICOS-0: icosian / E₈ software oracle — findings

Status: software PASS (simulation-only; no RTL, no silicon claim).
Oracle: `software/lib/icosian_e8.py` (exact `Fraction`s over ℤ[φ], independent of BQ-0, A₃₁, Lucas/Phinary).
Tests: `software/tests/test_icosian_e8.py` (fast, ~11 s, registered in `run_all_tests.py`) and
`software/tests/test_icosian_e8_full.py` (pure-oracle exhaustive research gate, ~47 s, not registered).

## Construction
* 120 unit icosians (binary icosahedral group): 8 values ±1,±i,±j,±k; 16 values (±1±i±j±k)/2;
  96 even permutations of (±φ,±1,±φ⁻¹,0)/2. Distinct, unit quaternionic norm, closed under all 14,400 products.
* Form: dot(x,y)=a+bφ (4-dim Euclidean dot over ℚ(√5)); **B(x,y)=2(a+b)** = 2·Tr(λ·dot), λ=(5+√5)/10
  totally positive, hence positive definite on the 8-dim ℤ-lattice.
* Roots: U ∪ φ⁻¹U — 240 distinct, B(r,r)=2.

## E₈ evidence
* Every root has inner-product profile {−2:1, −1:56, 0:126, 1:56, 2:1}.
* All 57,600 root reflections s_r(x)=x−B(x,r)r stay in the 240.
* HNF of the roots has rank 8; Gram on the basis is integral, even, det 1 ⇒ E₈ (unique even unimodular
  rank-8 lattice). φ·u=u+φ⁻¹u lies in the span, so it equals the ℤ[φ]-span of the units.
* Not done: no minimal-vector enumeration; the 240 count rests on the uniqueness argument.

## Width (numerators over 2; four ℤ[φ] coordinates = 8 integer lanes)
Observed: roots 2 bits; root reflections 2; pairwise root products 3 (43,200/57,600 land back in the roots);
unit-product chains 2 at any depth (finite group); 64-step reflection chains ≤3; unrestricted root-product
chains grow (depth 1/4/8/16/32/64 → 3/4/7/10/17/30 bits, ≈0.45 bit/step, 100 seeded chains per depth).
Proved: B=2(λ|x|²+λ′|σx|²) bounds each coordinate by √(n/2λ), √(n/2λ′) in the two embeddings, so
B(x,x)=n fixes a bit width (n=2 → 3 bits). This bound covers reflections (norm-preserving) only; it does
**not** bound unrestricted multiplication.

## Test equivalence
The fast fixture runs on exact integer 8-vectors with a cached Gram matrix, differentially checked
against the Fraction oracle on all 14,400 unit products and all 57,600 root inner products; same
assertions, same RNG sequence. Both tests produce identical growth numbers. A corrupted-product negative
control makes the fast fixture fail.

## Not authorized / not done
Fixed-width registers, ISA, RTL, synthesis, Golden Core integration; BQ-0 and A₃₁ unchanged.
