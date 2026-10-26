# AOR-1 Phase A — final ratification amendment

**Date:** 2026-10-12

**Status:** PROPOSED FOR REVIEW. No implementation, numerical experiment,
RTL, opcode allocation, synthesis, routing or board operation is authorized.

Review commands:

```bash
sed -n '1,240p' spu_strategy/contract_spu13_aor1_phase_a_ratification_amendment_2026-10-12.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_spu13_aor1_phase_a_ratification_amendment_2026-10-12.md
```

This amendment supplements the [Phase A draft](contract_spu13_aor1_phase_a_2026-10-11.md)
and [review](../docs/AOR1_PHASE_A_DRAFT_REVIEW_2026-10-11.md). It proposes the
remaining executable semantics for owner ratification; it does not ratify itself.
The audit count is the root engineering contract's prescribed documentation
invocation, not a newly measured regression count. Preserve earlier drafts.

## 1. Domains and limits

Represent z=(a+b sqrt(3))U^k, U=2+sqrt(3), without rational denominators.
The bounded model stores signed64 a,b and signed32 k. Norm output is signed128.
Both multiplication coefficients use exact signed130 temporaries; the radical
needs only signed129, and the residual norm needs signed129. No truncation occurs.

| Resource | Proposed ceiling |
|---|---:|
| Oracle retained coefficient magnitude bits | 1,000,000 each |
| Oracle temporary magnitude bits | 2,000,128 each |
| Bounded arithmetic/expansion temporary signed width | 130 |
| Bounded expansion loop iterations | 128 |
| Per-case charged abstract operations, separately per model | 100,000 |

Magnitude bits means abs(x).bit_length(), with zero consuming zero bits.
Signed130 means -2^129 <= x < 2^129; it is not a 130-magnitude-bit allowance.
Bounded expansion may retain working coefficients wider than signed64, provided
all remain signed130. Only the committed expansion coefficients must be signed64.
These temporary values are internal, not additional architectural registers.

## 2. Charged primitives and fixed definitions

| Primitive | Definition of one charged operation |
|---|---|
| SURD_MUL | (a,b),(c,e) -> (ac+3be,ae+bc); all four scalar products, constant scaling and sums included |
| SURD_ADD/SUB | Componentwise pair sum/difference; both components included |
| SURD_CONJ | (a,b) -> (a,-b); AOR conjugation also checks and negates k within this charge |
| SURD_NORM | a*a-3*b*b; products, scaling and subtraction included |
| PELL_STEP | (p,q) -> (2p+3q,p+2q); one forward recurrence, both components included |
| PRECHECK | One named Boolean predicate from the frozen schedule below |

Input validation is uncharged and separately bounded: inspect at most two source
triples, one destination triple and one increment. Require exact built-in integers
(exclude bool), exact tuple lengths and supported operation names. Do not coerce
strings, iterate arbitrary objects or construct powers while validating. Bounded
coefficient/exponent/increment ranges are checked before arithmetic; increment
is signed32. Oracle coefficient bit ceilings are checked before coefficient work.

A precheck includes its documented fixed-size metadata calculations and comparisons.
It cannot hide coefficient multiplication, recurrence, expansion, or another
charged primitive. Public operation wrappers are not extra charged primitives.
Comparative implementations use identical schedules. An independent recurrence
oracle reports its own explicit recurrence schedule and cost, separately.

Before evaluating a primitive or its resource guards, add its charge to
`attempted_units`. If the new total exceeds 100,000, record the rejected attempt,
perform none of that primitive's work, and stop with RESOURCE_LIMIT (or
EXPANSION_RESOURCE_LIMIT within expansion). Thus the exhaustion event can record
100,001 attempted units, but at most 100,000 admitted units. There is no further
attempt after exhaustion. A guard rejection after admission retains the charge.
Neither failure commits the destination. This distinguishes charged attempts
from admitted work without silently granting an extra operation.

## 3. Frozen schedules and precedence

After input validation, reject unsupported operation names and operand domains
before charged work. ADD/SUB are supported pair operations: for otherwise valid
inputs, exponent mismatch is determined only by the charged equal-exponent
PRECHECK. It returns UNSUPPORTED_OPERATION after consuming one unit; no pair
arithmetic follows. General exponent alignment remains unsupported in Phase A.

- STEP: one exponent-range PRECHECK computes k+n in widened signed33 metadata;
  valid zero residual bypasses exponent arithmetic and returns canonical zero
  with zero charged units, including a valid nonzero stored exponent.
- MUL: one exponent-range PRECHECK computes k1+k2, then SURD_MUL, then one
  coefficient-range PRECHECK. Exponent failure precedes a zero-result shortcut.
- CONJ: SURD_CONJ checks exponent negation before coefficient negation. Exponent
  minimum failure takes precedence over simultaneous coefficient minimum failure.
- NORM: SURD_NORM, then one signed128-output-range PRECHECK.
- Equal-exponent ADD/SUB: one equal-exponent PRECHECK, the pair primitive,
  then one coefficient-range PRECHECK. A mismatch is unsupported.

Each admitted coefficient primitive evaluates one temporary-safety PRECHECK before
coefficient arithmetic, and the oracle additionally evaluates one retained-size
PRECHECK after its result. These are separate charges. Budget exhaustion or a
resource-guard failure prevents evaluation of subsequent schedule entries.
Zero-producing successful tuple operations return (0,0,0). General nonzero
factorization is not canonicalized; (13,0,0) is the required conjugate-product row.

Statuses are INVALID_INPUT, UNSUPPORTED_OPERATION, EXPONENT_OVERFLOW,
MANTISSA_OVERFLOW, NORM_OVERFLOW, RESOURCE_LIMIT, EXPANSION_OVERFLOW,
EXPANSION_RESOURCE_LIMIT and OK. Validate first, then execute the frozen schedule.
An unevaluated later numerical fault does not override an earlier resource failure.
Every failure preserves all destination fields; only complete success commits.

## 4. Pre-allocation guards

For a coefficient product with magnitude bit lengths A,B, abs(x*y)<2^(A+B)
when both are nonzero. Zero products have bound zero. Scaling by three adds two
bound bits; summing two nonzero bounded terms adds one bit above their maximum.
Take the maximum bound across every internal product, scaled product and sum.
The temporary-safety predicate requires this conservative bound to fit the
applicable ceiling before allocation. The bounded signed ceiling uses at most
129 magnitude-bound bits; signed64-input SURD_MUL and SURD_NORM may instead use
the proven signed130/signed129 bounds above, avoiding conservative false rejection.
Addition and recurrence use analogous explicit sum/scaling bounds. Negation uses
its source magnitude bound. No logarithms, floating-point estimates or expanded
integer powers are used by these guards.

The oracle checks actual retained magnitude bits after admitted arithmetic.
Rejected conservative guards establish resource exhaustion, not final overflow.
A bounded working-value range check concerns temporary resources; it cannot be
reported as destination overflow merely because a later cancellation was skipped.

## 5. Expansion schedule and permitted proofs

Use binary exponentiation with exponent magnitude held in widened metadata:
start r=(1,0), p=(2,sign(k)), n=abs(k). For each n>0 iteration, charge one
iteration-limit PRECHECK before entry. If n is odd, perform SURD_MUL(r,p).
Then shift n right once; if n remains nonzero, perform SURD_MUL(p,p).
Each multiplication includes the charged temporary-safety and oracle retained-size
checks in section 3. Finish with SURD_MUL(m,r), then one final-output-range PRECHECK.
Zero residual (a=b=0), including any valid nonzero k, is an explicit
zero-expansion fast path: after validation return (0,0,0), with zero charged
units, no loop and no coefficient allocation. Zero-residual input need not already
have k=0; successful output always does. Invalid fields still fail validation.
For a nonzero residual, k=0 evaluates only the final-output-range PRECHECK on m. Control-bit tests and metadata shifts are
uncharged fixed work inside the bounded loop, not arbitrary coefficient arithmetic.

For the initial model, the only accepted numerical overflow proof is an exact
final pair computed within all budgets, with at least one coefficient outside
signed64. No early exponent/magnitude heuristic is approved. Exact k=0 output
checking is the corresponding trivial case. This deliberately permits resource
failure for a result that a more sophisticated algorithm could prove overflows.
Any future early proof needs a separate reviewed derivation accounting for residual
coefficients, sign and cancellation, plus independent negative controls.

A temporary-size guard, retained-oracle-size guard, iteration cap or operation
budget failure during expansion returns EXPANSION_RESOURCE_LIMIT. Wall-clock
watchdogs are external campaign outcomes and never arithmetic statuses.

## 6. Required review fixtures and comparison

Before execution authorization, freeze literal expected rows and independent
checker commands for: exactly-at-budget admission; budget+1 rejection without
arithmetic; admitted-but-guard-rejected charging; malformed input; signed minima;
zero/exponent precedence; full-width products; norm overflow; expansion cancellation;
iteration limits; and resource rejection without a numerical overflow claim.
Test (5,2,1000)*(5,-2,-1000) -> (13,0,0) without expansion.
The illustrative U^-1000 residual is valid in the oracle but not a signed64
mantissa input; include cancellation fixtures that actually fit the bounded domain.

Compare against an ordinary Surd mantissa plus signed exponent counter with the
same numerical domains, schedules, resource checks and atomic failure semantics.
Do not infer instruction-count or hardware benefits from software tuple naming.
Independent oracle kernels must not reuse bounded arithmetic as their sole check.

## 7. Ratification and execution remain separate

Owner ratification must bind this amendment, the parent draft, exact source scope,
operation/fixture schedules and their hashes. A later execution packet supplies
commands, required gates, attempt counts, per-attempt timeouts and cumulative budget.
No AOR implementation or experiment is launched by this document. Artix-7 routing,
observer adoption and the unapplied aligned-decode candidate retain their own gates.

## 8. Review bindings and competing historical proposal

The [literal fixtures](aor1_phase_a_literal_fixtures_2026-10-12.md) specify expected
results and charging without claiming executed checks. The separate
[execution packet draft](contract_spu13_aor1_phase_a_execution_draft_2026-10-12.md)
remains unratified. The build review identity binds current proposal hashes.

The earlier [scalar accounting proposal](contract_spu13_aor1_accounting_review_2026-10-12.md)
has incompatible charges, temporary caps and a monotone proof walk. It is preserved
as an alternative historical proposal, not an additional source of Phase A rules.
If this amendment is ratified, its abstract primitive charges, bit caps and
exact-final-pair-only overflow policy take precedence. No policy has been adopted
by documentation preparation alone.
