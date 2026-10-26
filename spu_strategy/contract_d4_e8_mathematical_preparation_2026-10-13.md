# D4/E8 isolated mathematical campaign preparation

```bash
python3 -m software.research.lattice_symmetry.preparation --help
python3 software/tests/test_lattice_symmetry_preparation.py
python3 -m json.tool build/d4_e8_math_20261013/preparation_01/checks_03/math_preparation.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/lattice_symmetry software/tests/test_lattice_symmetry_preparation.py spu_strategy/contract_d4_e8_mathematical_preparation_2026-10-13.md docs/D4_E8_MATHEMATICAL_PREPARATION_2026-10-13.md docs/README.md
```

Date: 2026-10-13. Status: PREPARATION CHECKS ONLY; qualification NOT RUN.
Authority: owner explicitly requests independent software oracles, mathematical
checks and workload preparation. No substantial campaign budget is authorized.
Roles: specification, halt-and-flag implementation and evidence audit performed
sequentially. This supersedes documentation-only scope for this new increment,
not existing D4, AOR, SGN or CPU evidence/authority.

## Scope and immutable boundaries

New code: `software/research/lattice_symmetry/`; new focused tests:
`software/tests/test_lattice_symmetry_preparation.py`. New contract and report.
Sources are Lithic modules, at most150 lines each. Preserve CPU, RTL, ISA,
build flows, existing oracle implementations and qualified snapshots.
Evidence lives only under `build/d4_e8_math_20261013/preparation_01/`.
No FPGA synthesis, placement, routing, bitstreams, board access or integration.
Full repository qualification is not claimed; no hardware gate is executed.

## Implementation and independent reference

| Module | Boundary |
|---|---|
| roots | Explicit D4/D8 integer support-pair roots and E8 half-coordinate signs, stored doubled |
| reference | Separate rational norm-shell search and lattice predicate; no candidate/mapping imports |
| linear | Fraction-based elimination, matrix application and composition |
| checker | Counts, norms, membership, rank, root-set agreement and finite reflection properties |
| mapping | Rank-aware Quadray/scalar and rational-Surd software encodings |
| fixtures | Named simple roots, deterministic words/vectors and strict input validation |
| accounting / comparators / surd_arm | Prepared logical cost counters and four equivalent small-comparison arms |
| controls / preparation | Named rejection diagnostics and short preparation evidence |

Physical coordinates are x=X/2. D4 has integer x with even coordinate sum.
E8 has all integral or all half-integral x with even coordinate sum. Candidate
X is uniformly even, or uniformly odd for E8, and sum(X) is divisible by4.
All roots have physical squared length2 and doubled squared length8.

Explicit construction: D4 contains +/-e_i +/-e_j (i<j),24 roots. E8 contains
112 such integer roots in eight dimensions plus128 half-coordinate sign
vectors with an even number of minus signs. The independent oracle searches
the small integer/half-integer norm shell, not the candidate's port/root list.
Conventions agree with [Sage type D](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/type_D.html)
and [type E](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/type_E.html).
Sage is a source reference, not a runtime dependency or a local verification result.

Use exact s_alpha(x)=x-2(x dot alpha)/(alpha dot alpha)*alpha. In doubled
coordinates use X'=X-((X dot A)/4)*A, checking lattice membership, root norm
and divisibility before quotient. Runtime division here is host exact integer/
rational arithmetic; no synthesizable RTL algorithm is proposed.

Check24×24 and240×240 candidate root/reflection pairs for closure and
involution. Independently compare rational formula and dense matrix on16
specified pairs per system. This is not exhaustive matrix-oracle agreement.
Exact rank is4/8. Allowed physical inner products are{-2,-1,0,1,2}; retain
complete ordered-pair distributions. Simple generators must belong to the
root set, be independent, and generate the full root orbit.

## Mathematical proof obligations and mapping limits

Norm-shell completeness: integer norm2 coordinates must lie in{-1,0,1};
half-integer coordinates cannot have magnitude3/2 because one square exceeds2.
The sign/parity construction therefore exhausts the declared roots.

For lattice X and root A, prove X dot A divisible by4 from uniform parity,
sum(X)=0 mod4, and the even number of negative signs of an odd root. For an
even root only two +/-2 entries occur. A reflection preserves uniform parity
and sum mod4 because sum(A) is divisible by4. With c=(X dot A)/4 and A dot A=8,
the norm difference is -2c(X dot A)+8c*c=0; the second reflection uses -c.
These are reviewed algebraic arguments plus finite checks, not formal proofs.

One constrained Quadray block has three independent coordinates; two have six.
D4's four coordinates need an extra scalar or a different independent encoding.
The implemented D4 bridge retains x3, parity-shifts x0 to produce an FCC triple,
then uses a zero-sum inverse lift. It is reversible, not a linear isometry.

For E8 doubled X, encode each four-coordinate block as q_i=4X_i-t,
t=sum(block). Then sum(q)=0 and X_i=(q_i+t)/4. Two q blocks plus two retained
t scalars have rank8; discard t and rank falls to6. Charge all ten stored
coefficients, dependencies, scaling and inverse-divisibility checks. This is
an eight-dimensional software encoding, not two Quadray processing elements
implementing native E8 or a compactness advantage. Round trips are checked on roots.

Rational coordinates embed in explicit-denominator Surds through B=0. Packing
eight rationals into four pairs a+b*sqrt(3) is also a Q-linear encoding, but
it does not identify E8's Euclidean norm with the field norm a*a-3*b*b.
Preserve the pulled-back metric and define transformed coefficient operations
before claiming a general Surd/E8 action. Pell boosts and Weyl reflections
remain different families; no AOR-S1 exponent-to-symmetry map is established.

## Deterministic comparative workload preparation

Prepare120 cases: systems D4/E8; words of length0,1,2,8,32,128; five vectors
each; forward words and each word followed by its reversed inverse. Inputs
include zero, opposite roots, a root sum and a17-fold root. Generator IDs are
literal and words cycle in ascending ID order. Apply left to right; compose
matrices on the left. No random fixture selection or post-result remapping.

Arms: immediate doubled coordinates; exact rational matrices; retained ordinary
generator words with full charged evaluation; explicit-denominator Surd bridge.
The bridge is standalone software, not AOR-S1 or CPU instruction execution.
Only four cases based on two-generator words and their inverse pairs ran. Larger
cases are written to the fixture plan, NOT RUN. No learned or physical claim.

For substantial comparison, add the conventional even-signed-permutation D4
descriptor baseline and separate table setup from amortized repeated-vector
evaluation. A new compressed descriptor is an investigation, not an existing arm.
Use matched final materialized vectors and descriptor-only endpoints separately.

## Accounting and negative controls

Record semantic scalar add/subtract/multiply, exact quotient/remainder checks,
word appends, GCD calls, Fraction normalization calls and coordinate conversions.
For direct coordinate words of length L in n dimensions, count2nL multiplies,
nL additions,nL subtractions,L exact quotients andL remainder checks. Independent
formula checks and literal witnesses must agree with candidate counters.

Fraction semantic counts and modeled schoolbook integer counts are distinct
views, not quantities to add together. Model unreduced products, cross-products
and cancellation numerators/denominators for intermediate growth. Record signed
integer width, normalized numerator/denominator width and modeled raw widths.
CPython's internal cancellation/GCD steps are not measured by these counters.

Logical integer storage uses minimum two's-complement width; rational storage
adds a signed numerator and positive denominator bit length. Include generator
tables, accumulated matrices, live old/new arrays and word tokens. Word storage
includes a32-bit count and2/3-bit generator IDs for D4/E8. These are logical
array observations, not complete live-memory/serialization budgets: object
headers, lengths for other structures, pointers, allocator and GCD workspace
remain excluded. Report those exclusions, not a hardware storage estimate.

Materialization charges every deferred reflection for words and the final
matrix/vector application for matrices; Surd normalization charges GCD calls
and exact coefficient quotients. Current counters are preparation kernels;
all validation, root loads, allocation and conversion primitives require a
fully frozen instrumented schedule before a substantial cost comparison.

Retain named controls for missing/duplicate roots, wrong norm/parity/type,
rank-six mislabeled E8, wrong scaling, invalid lattice inputs, lost block
divisibility, reversed matrix composition, noninvolution and invalid generator
IDs. Missing observations, escaped controls or disagreement stop checks.
Resource-limit and partial-write controls must be added when a finite profile
is specified; the current pure unbounded functions do not implement CPU writes.

## Next implementation plan and execution HOLD

1. Review mathematical constructions, metrics and source hashes independently.
2. Freeze full cost schedules, storage schema, comparison domains and resource
   refusal limits; add D4 signed-permutation and descriptor baselines.
3. Implement an isolated qualification driver preserving all original evidence,
   named first counterexamples and before/after source identities.
4. Freeze the exact detached command, maximum attempts, per-attempt timeout and
   cumulative budget, then obtain separate explicit owner authorization.
5. Run only that authorized software campaign; audit durable terminal results
   before any promotion. No executable campaign launcher or budget exists now.

Preparation data is not qualified D0–D3 campaign evidence. AOR-S1 integration,
general compactness, finite-width refusal semantics and useful workload benefit
remain unresolved. Prioritize Surd CPU backend repair without changing its
sources, physical attempts or budget. SGN Phase B stays deferred.
