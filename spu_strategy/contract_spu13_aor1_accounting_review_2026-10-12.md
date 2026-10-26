# AOR-1 Phase A accounting and expansion-precheck review proposal

**Date:** 2026-10-12

**Status:** PROPOSED — exact candidate rules for review; no implementation/execution authorization.

Read the amended Phase A contract and the review disposition:

```bash
sed -n '1,220p' spu_strategy/contract_spu13_aor1_phase_a_2026-10-11.md
sed -n '1,200p' docs/AOR1_PHASE_A_DRAFT_REVIEW_2026-10-11.md
```

## Agreed limits and proposed details

Owner-approved direction: integer signed64 residual, signed32 stored exponent,
sufficiently wide exact temporaries, signed128 norm output or explicit overflow,
oracle expanded coefficient limit 1,000,000 bits each, oracle budget 100,000
counted operations per case, bounded expansion maximum 128 squaring-loop
iterations and signed64 output. Resource limits are distinct from numeric
overflow. Wall-clock watchdogs are external infrastructure outcomes.

The following accounting, temporary caps, precheck schedule and failure details
are proposed for ratification. They are not an implementation contract yet.

## Exact accounting units

Define B(x)=max(1, bit_length(abs(x))). This measures magnitude bits, not signed
storage bits. Each exact scalar integer addition, subtraction, multiplication,
negation or right-shift costs one unit, including operations on exponents and
constant multiplication. Reserve a unit before the operation. A rejected
operation does not execute or consume a unit. Assignments, branching, comparison,
bit inspection and bit-length queries cost zero units in this abstract ledger.
This ledger is reproducible arithmetic accounting, not a runtime/energy model.

| Operation/schedule | Arithmetic units |
|---|---|
| Residual pair multiply | 4 variable products + multiply-by-3 + 2 adds = 7 |
| Residual norm | 2 squares + multiply-by-3 + subtraction = 4 |
| Exponent sum / step | 1 add |
| Conjugation | 2 negations (b and k) |
| Forward unit recurrence | 3 constant products + 2 adds = 5 |
| Recurrence remaining-count decrement | 1 subtraction |
| Squaring-loop exponent halve | 1 right-shift |

Reset counters per case. Oracle and bounded reference have separate ledgers;
do not pool them. Propose the same 100,000-unit cap for bounded expansion.
Different independent algorithms may consume different counts: semantic results
must agree when both succeed, but their resource-limit thresholds need not match.
Use a separate schedule checker for contract accounting; never reuse the bounded
arithmetic kernel as the sole expected-value oracle.

## Guard arithmetic before allocation

Propose oracle temporary cap 1,000,000 magnitude bits and bounded expansion
temporary cap 4,096 magnitude bits per scalar integer. Oracle final expanded
outputs retain the separate 1,000,000-bit limit. These temporary caps are new
review choices, not inferred from the owner's output limits.

Before a product require B(x)+B(y)<=cap. Before add/subtract require
max(B(x),B(y))+1<=cap. Negation and right-shift require the operand fits the cap.
For literal zero operands, the documented zero shortcut may return exact zero
without constructing a product, but still charges the scheduled arithmetic unit.
Conservative bounds can reject an operation whose actual result would fit; that
is a resource refusal, not a numerical overflow proof. No oversized intermediate
is allocated to find out whether cancellation would have occurred.

## Bounded expansion schedule and exact prechecks

1. Validate tuple, operation and operand domains. Propose exact integer operands
   (excluding Boolean) and a signed32 step increment; validate before zero rules.
   No binary instruction encoding is introduced.
2. Check applicable exponent arithmetic. For multiplication propose this check
   precedes zero-product normalization. Zero STEP returns canonical zero after
   validation without adding an exponent. These choices require explicit approval.
3. For EXPAND, zero returns (0,0); k=0 returns the already validated residual.
4. For other expansions, use a bounded proof walk of at most 64 recurrence steps,
   charged separately from the squaring-loop iteration counter but against the
   same arithmetic ledger. Transform to c=a,d=b for k>=0, or c=a,d=-b for k<0;
   reserve/charge the latter negation. Let r=abs(k), charging a negation if needed.
5. At each proof-walk boundary, if c and d have the same weak sign and either
   final-coordinate candidate (c,d for k>=0; c,-d for k<0) is outside signed64,
   return EXPANSION_OVERFLOW. Account for sign restoration without an uncounted
   arithmetic operation. In this sign region recurrence c'=2c+3d,d'=c+2d keeps
   both signs and cannot decrease their magnitudes. Therefore every remaining
   forward step stays outside the relevant asymmetric signed64 range.
6. Otherwise, if r=0, determine signed64 fit using the sign-aware intervals. On
   success restore d for negative original k with a reserved, charged negation
   before commit; on failure report proven EXPANSION_OVERFLOW. If proof-walk
   steps remain, apply the recurrence and
   decrement r with the guards and accounting above. Never call an oversized
   opposite-sign intermediate a proof of final overflow.
7. If the proof walk reaches its cap without deciding, perform exponentiation by
   squaring on its remaining transformed residual and U^r. Each loop condition
   with r>0 starts one counted iteration; reserve it before execution. If odd,
   multiply accumulator by power (7 units); halve r (1 unit); if r remains
   nonzero square power (7 units). Avoid the unused final square. Initialize the
   accumulator to the walked residual and power to (2,1).
8. Enforce every scalar bit guard, arithmetic-unit cap and 128-loop limit before
   executing the affected operation. Restore d's sign for original negative k
   with a charged negation, validate final signed64 widths, then commit atomically.

An exact overflow proof already completed within budget takes precedence. If a
guard or budget stops undecided expansion, report EXPANSION_RESOURCE_LIMIT.
No exponent-only cutoff or elapsed-time inference is a numerical overflow proof.
The proof walk is an exact monotonicity argument, not a claim that all overflowing
inputs will be detected within 64 steps. Independent recurrence/fixtures must
test sign transitions, residual cancellation and negative-exponent restoration.

For a precheck sign-restoration test, compare d to the inverted interval
[-(2^63-1),2^63] when original k<0; do not construct -d solely for that comparison.
The interval endpoints are fixed constants. Remaining subtraction/negation
counts follow the table; predicates themselves are free abstract ledger steps.

## Required additional tests and fair baseline

- (5,2,1000) times (5,-2,-1000) returns (13,0,0); norm is 13, not one.
- (2,-1,1) expands to (1,0); opposite-sign cancellation defeats naive size tests.
- b=-2^63 and k=-2^31 exercise independent conjugation failures.
- a=0,b=-2^63 has norm -3*2^126: exact temporary calculation, signed128 output fault.
- Proof success immediately before budget exhaustion versus refusal before proof.
- Exact signed64 endpoints and output-coordinate sign reversal for negative k.
- Counters, bit guards and zero shortcuts falsified by injected off-by-one faults.

Baseline: ordinary signed64 Surd mantissa plus signed32 exponent software
bookkeeping, with identical domain, operation subset, atomicity and failure rules.
Do not compare a checked AOR object with an unchecked baseline. Include validation,
allocation, representation handling and expansion work in costs. Report storage,
operation vectors and host timings separately for compact versus materialized
workloads. No hardware instruction benefit follows from algebraic equivalence.

Outstanding status proposal: NORM_OVERFLOW for norm output, distinct from mantissa
product overflow; unsupported domains remain distinct from malformed types.
Ratify these names and the schedule before authorizing any Phase A execution.
