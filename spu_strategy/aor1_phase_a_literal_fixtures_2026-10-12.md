# AOR-1 Phase A literal boundary fixtures

**Status:** PROPOSED, EXPECTED VALUES ONLY, NOT EXECUTED. Date: 2026-10-12.

```bash
sed -n '1,240p' spu_strategy/aor1_phase_a_literal_fixtures_2026-10-12.md
```

Apply the [reviewed amendment](contract_spu13_aor1_phase_a_ratification_amendment_2026-10-12.md).
These manually derived rows are checker inputs, not an implementation or oracle
qualification. A separate independent checker must verify them before promotion.
Do not change expected rows automatically to agree with a model.

## Notation and bounded-model expectations

L=-9223372036854775808; H=9223372036854775807.
Kmin=-2147483648; Kmax=2147483647. D=(17,-19,23) is the initial tuple destination.
Each ordinary row starts with zero used units, a 100,000-unit budget and D.
On a failure, D remains exactly unchanged and no commit event occurs.
A norm operation has a separate scalar destination initially 17; failure preserves
that scalar. Norm does not overwrite a tuple with an invented encoding.
Charges below are the bounded model's; oracle retained-size checks add their own
explicit charges and are not silently pooled with this ledger.

| ID | Operation and inputs | Expected result/status | Attempted/admitted units |
|---|---|---|---:|
| F01 | MUL (5,2,1000), (5,-2,-1000) | OK (13,0,0) | 4/4 |
| F02 | MUL (1,0,1000), (1,0,-1000) | OK (1,0,0) | 4/4 |
| F03 | ADD (5,2,7), (3,-1,7) | OK (8,1,7) | 4/4 |
| F04 | SUB (5,2,7), (3,-1,7) | OK (2,3,7) | 4/4 |
| F05 | ADD (5,2,7), (3,-1,8) | UNSUPPORTED_OPERATION; preserve D | 1/1 |
| F06 | SUB (5,2,7), (3,-1,8) | UNSUPPORTED_OPERATION; preserve D | 1/1 |
| F07 | EXPAND (0,0,1000) | OK (0,0,0) | 0/0 |
| F08 | EXPAND (0,0,Kmin) | OK (0,0,0) | 0/0 |
| F09 | STEP (0,0,Kmax), increment 1 | OK (0,0,0) | 0/0 |
| F10 | EXPAND (0,0,Kmax+1) | INVALID_INPUT; preserve D | 0/0 |
| F11 | STEP (1,0,Kmax), increment 1 | EXPONENT_OVERFLOW; preserve D | 1/1 |
| F12 | MUL (0,0,Kmax), (1,0,1) | EXPONENT_OVERFLOW; preserve D | 1/1 |
| F13 | MUL (0,0,7), (1,0,8) | OK (0,0,0) | 4/4 |
| F14 | MUL (L,L,0), (L,L,0) | MANTISSA_OVERFLOW; preserve D | 4/4 |
| F15 | CONJ (0,L,Kmin) | EXPONENT_OVERFLOW; preserve D | 1/1 |
| F16 | CONJ (0,L,0) | MANTISSA_OVERFLOW; preserve D | 2/2 |
| F17 | NORM (5,2,1000) | OK scalar 13 | 3/3 |
| F18 | NORM (0,L,0) | NORM_OVERFLOW; scalar destination stays 17 | 3/3 |
| F19 | EXPAND (2,-1,1) | OK (1,0,0) | 6/6 |
| F20 | EXPAND (1,0,1) | OK (2,1,0) | 6/6 |
| F21 | EXPAND (1,0,-1) | OK (2,-1,0) | 6/6 |
| F22 | EXPAND (H,0,1) | EXPANSION_OVERFLOW; preserve D | 6/6 |
| F23 | EXPAND (5,2,0) | OK (5,2,0) | 1/1 |
| F24 | MUL (True,0,0), (1,0,0) | INVALID_INPUT; preserve D | 0/0 |
| F25 | Unknown operation name, otherwise valid tuples | UNSUPPORTED_OPERATION; preserve D | 0/0 |

F01: 5*5+3*2*(-2)=13 and 5*(-2)+2*5=0; exponent sum is zero.
F03/F04 use componentwise sums/differences only; no exponent alignment is performed.
F14: exact raw coefficients are 2^128 and 2^127, proving signed130 arithmetic
is required before signed64 rejection. No intermediate truncation is permitted.
F18: exact norm is -3*2^126, smaller than signed128 minimum -2^127.
F19: 2*2+3*(-1)*1=1 and 2*1+(-1)*2=0; an exponent-only rejection is incorrect.
F22: exact final coefficients are 2H and H; final real coefficient exceeds H.
Each k=+/-1 expansion charges: iteration predicate; accumulator multiplication
and temporary predicate; residual multiplication and temporary predicate; final
output predicate. No unused final square occurs. The result tuple resets k to 0.

CONJ admits its one primitive charge, checks exponent negation first, then admits
its temporary predicate and attempts coefficient negation. This fixes F15/F16
precedence and accounting independently of how code is organized.

## Instrumented boundary fixtures, not public API overrides

These rows seed private test state; production per-case limits remain unchanged.
Expose seed state only in a test harness, never as an alternate arithmetic mode.

| ID | Seed and next attempted action | Required result |
|---|---|---|
| B01 | attempted=admitted=99,999; true PRECHECK | 100,000/100,000; predicate evaluated once |
| B02 | attempted=admitted=100,000; true PRECHECK | RESOURCE_LIMIT; 100,001/100,000; predicate never evaluated |
| B03 | zero ledger; SURD_MUL on internal pairs (2^100,0),(2^100,0) | primitive and temporary predicate both charged (2/2); resource refusal before multiplication; no numerical overflow claim |
| B04 | ledger=99,999; same internal multiplication as B03 | primitive admitted as 100,000; guard attempted as 100,001 and not evaluated; no coefficient arithmetic |
| B05 | expansion loop already entered 128 times; n still positive | next iteration predicate charged once; EXPANSION_RESOURCE_LIMIT; loop body not entered |
| B06 | EXPAND context; ledger=100,000; next primitive requested | EXPANSION_RESOURCE_LIMIT; attempted=100,001, admitted=100,000; no evaluation |
| B07 | zero ledger; internal SURD_ADD (2^128,0),(-2^128,0), in EXPAND context | primitive and temporary predicate charged (2/2); EXPANSION_RESOURCE_LIMIT before coefficient addition; preserve D |

B03/B04 deliberately use signed130 internal working pairs, not invalid signed64
public operands. Conservative product bound is 202 magnitude bits, above the
129-bit bound allowance. They test the guard itself without allocating the product.
B05 requires private state injection: a valid signed32 exponent needs at most 32
binary-exponentiation iterations, so the 128-iteration refusal is unreachable from
ordinary valid inputs. Do not describe its coverage as a natural workload result.

B07 separates sufficient bounds from necessary ones. Both real operands fit
signed130 and have magnitude bit length 129. The conservative sum bound is
max(129,129)+1=130, above the permitted 129 magnitude-bound bits, so the guard
rejects it. Independently, the exact pair sum is (0,0), which fits signed64.
Thus this refusal cannot establish numerical overflow. This is an internal
working-value fixture, not a public signed64 input; no product-width shortcut
applies to addition. The ordinary signed64 ADD fixture F03 remains unchanged.
The identity x+(-x)=0 supplies a separate literal check of the cancellation result.
B07 explicitly injects the temporary guard for an internal SURD_ADD into a
private harness with expansion failure context. Its schedule is: admit/charge
SURD_ADD (one unit), admit/charge its temporary-safety PRECHECK (one unit), reject
that predicate, perform no coefficient addition, and preserve D. Context selects
EXPANSION_RESOURCE_LIMIT; the corresponding ordinary-operation context would
select RESOURCE_LIMIT. This harness injection does not add SURD_ADD to the frozen
binary-expansion algorithm, which uses SURD_MUL, or expose signed130 public inputs.
Two separate deliberately faulty variants, one reporting MANTISSA_OVERFLOW and
one reporting EXPANSION_OVERFLOW for B07, must each be rejected with nonzero exit.
Their outer qualification result must not hide either defective checker's exit.

## Negative controls and independent qualification still pending

Require deliberately faulty variants to be rejected: free mismatch predicate,
charged zero-expansion fast path, uncharged guard rejection, budget+1 evaluation,
truncated F14 accumulator, exponent-only overflow, wrong norm, wrong conjugation,
and committing a failed destination. Record each defective checker's nonzero exit
separately from a passing outer qualification runner. No controls have run here.
