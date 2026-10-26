# SPU-13 Architectural Contract: Algebraic Octave Representation (AOR-1)

**Contract ID:** `contract_spu13_algebraic_octave_aor1_2026-10-11.md`

**Status:** PROPOSED — review only; implementation not authorized.

**Date:** 2026-10-11

Read the bounded research draft before any implementation decision:

```bash
sed -n '1,200p' spu_strategy/contract_spu13_aor1_phase_a_2026-10-11.md
```

This command reads a proposal; it does not authorize execution of Phase A.

## Authority and purpose

Define an optional exact symbolic-scale facility without changing existing Surd
registers, ISA encodings, CPU/GPU behavior, or the active Artix-7 timing campaign.
No software implementation, RTL, architectural state allocation, synthesis,
routing or board experiment is authorized. Software objects versus architectural
registers remain an open decision.

Separate a residual mantissa from an integer power of the Pell unit. Preserve
exact composition, reversibility and norm within explicitly supported domains.
Compact storage does not imply bounded expanded coordinates, unlimited range,
or a discrete physical universe.

## Mathematical representation

Let U = 2 + sqrt(3), U^-1 = 2 - sqrt(3), and z = m U^k.
For m = a + b sqrt(3), N(m) = a^2 - 3b^2, N(U) = 1, and N(z) = N(m).

The architectural coefficient domain and physical packing remain undecided.
The initial Phase A domain is explicitly a,b,k in Z, with no rational denominator.
Its mathematical oracle is arbitrary precision; its bounded profile is distinct.

Composition: (m1 U^k1)(m2 U^k2) = (m1 m2) U^(k1+k2).
Residual multiplication is (ac+3bd, ad+bc), with exact checked arithmetic.
Both residual and exponent checks must succeed before destination commit.

Conjugation: conjugate(m U^k) = conjugate(m) U^-k.
For nonzero m, inversion requires representability of m^-1; conjugation is an
inverse only for norm-one values. General inverse support is not allocated.

## Special values and equivalence

| Meaning | Tuple (a,b,k) |
|---|---|
| Canonical zero | (0,0,0) |
| Preferred identity | (1,0,0) |
| Pell unit | (1,0,1) |
| Inverse Pell unit | (1,0,-1) |

Operations yielding zero return canonical zero. Zero stepping returns canonical
zero rather than incrementing its exponent. Malformed-input validation still
applies. Preferred identity is not a general identity canonicalization algorithm.

(1,0,1) and (2,1,0) denote the same value. Representation equality and value
equality are distinct. General canonicalization and comparison are deferred.

## Semantic operations — no opcodes assigned

| Name | Meaning |
|---|---|
| AOR_LOAD | Validate and construct an exact residual/exponent tuple |
| AOR_STEP | Checked exponent increment/decrement; special-case zero |
| AOR_MUL | Checked residual product and exponent sum, atomic commit |
| AOR_CONJ | Negate residual b and exponent, both checked |
| AOR_NORM | Exact residual norm with a declared result domain |
| AOR_EXPAND | Materialize ordinary coefficients only on exact success |
| AOR_IS_UNIT | Test mathematical norm equals one |
| AOR_STATUS | Expose completion/failure under a future interface contract |

Stepping and multiplication do not require coefficient expansion. Expansion
overflow preserves destination. Resource exhaustion is distinct from proven
numerical overflow. General addition/subtraction across exponents is deferred;
lossy scale alignment must never be called exact arithmetic.

## Failure and invariants

Proposed categories: SUCCESS, MANTISSA_OVERFLOW, EXPONENT_OVERFLOW,
EXPANSION_OVERFLOW, EXPANSION_RESOURCE_LIMIT, UNSUPPORTED_OPERATION,
INVALID_ENCODING. Norm-result overflow classification remains to be frozen.
No FLAGS bits, status numbers or retirement behavior are allocated.

Failed mutations preserve the entire destination. No partial writes, exponent
wrapping, saturation, coefficient truncation or floating-point substitution.

| Invariant | Required scope |
|---|---|
| I1 | N(U^k)=1 mathematically for every supported exponent |
| I2 | N(z1 z2)=N(z1)N(z2) |
| I3 | Step by n then -n restores representation for valid normalized inputs when both succeed |
| I4 | U^n U^-n is mathematical identity; mantissa-one workload also returns (1,0,0) |
| I5 | Associativity of values; bounded intermediate failures are reported |
| I6 | Every failure preserves destination |
| I7 | Successful expansion matches an independent arbitrary-precision oracle |
| I8 | Existing ISA and Surd behavior remain unchanged |

General equivalent factorizations need not canonicalize under I4. Normalized
input in Phase A means canonical zero or a valid nonzero tuple, not a general
unit-factor reduction algorithm.

## Research phases and promotion gates

1. Phase A: independent mathematical oracle, bounded software model and negative
   controls after a reviewed and separately authorized implementation contract.
2. Phase B: compare bounded exact coefficients, symbolic Pell exponents,
   arbitrary-precision expansion, floating point and applicable approximations.
   Separate symbolic manipulation from materialization; record storage,
   operations, time and exactness without inferring hardware performance.
3. Phase C: propose the smallest useful RTL subset only after Phase A acceptance.
   Candidate operations are LOAD, STEP, MUL, NORM and EXPAND; scope is not frozen.
4. Phase D: separately authorize synthesis, legal routing, timing and silicon
   measurement. Never infer these from software or functional simulation.

Initial workloads: 10, 34 and 1,000 positive steps; 1,000 positive followed by
1,000 inverse steps; mixed signs; unit multiplication; conjugation; checked
expansion; exponent boundaries; and corrupted expected results.

Promotion requires an independent oracle, explicit domains/equivalence rules,
bounded operation/failure specifications, falsifiable qualification evidence,
reviewed ISA/state decisions and preservation of existing behavior. None of
these implementation or physical qualification claims is established here.

Excluded: altered Surd widths/layout, ISA, ROTC/QROT/QNORM/REGEN/GPU semantics,
retirement/reset, arbitrary exact real arithmetic, arbitrary Lorentz coverage,
infinite range, CPU/GPU concurrency and unapproved hardware campaigns.

The unit-exponent counter alone may suffice for the Pell subgroup. Hardware
adoption requires useful mixed-mantissa workloads beyond software bookkeeping.
