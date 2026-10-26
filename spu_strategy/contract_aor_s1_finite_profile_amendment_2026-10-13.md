# AOR-S1 finite-profile and failure-sequence amendment

**Status:** PROPOSED FOR REVIEW — no implementation or qualification authorized.  
**Applies to:** [S1 product-fragment draft](contract_aor_s1_product_fragment_2026-10-13.md).

## Review commands

```bash
sed -n '1,220p' spu_strategy/contract_aor_s1_finite_profile_amendment_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_aor_s1_finite_profile_amendment_2026-10-13.md spu_strategy/contract_aor_s1_product_fragment_2026-10-13.md
```

This amendment proposes concrete limits for ratification. It does not change
the completed AOR-1 profile or allocate the small oracle qualification attempt.
S3 remains preparation-only. Hardware and Artix-7 inputs are unchanged.

## Proposed numerical profile

| Quantity | Limit |
|---|---|
| Stored a,b | signed64 |
| Stored k; step increment n | signed32 |
| Exponent temporary | signed64; check signed32 before use and commit |
| Arithmetic coefficient temporaries | signed136 |
| Exact sign/ratio-comparison and norm temporaries | signed280 |
| Published norm | signed128, or `NORM_OVERFLOW` |
| General normalization | at most 64 unit adjustments per operation |
| Certified local rebalance | at most one unit adjustment |
| Logical work budget | 4,096 charged units per operation, including validation |
| Oracle expanded coefficient | at most 1,000,000 magnitude bits each |
| Oracle expansion work | at most 100,000 exact pair multiplications per case |

All signed widths include the sign bit. Every temporary is computed exactly,
checked against its declared width, and never wrapped or narrowed first.
Temporary-width exhaustion is `TEMPORARY_LIMIT`; work/adjustment exhaustion is
`WORK_LIMIT`. Neither proves final numerical overflow. Oracle limits are
checker infrastructure outcomes, never candidate arithmetic statuses.

The signed136 choice leaves margin above the fixed stored-input product bound:
`|ac+3bd| <= 2^128`, `|ad+bc| <= 2^127`. A single unit adjustment has first
coefficient magnitude at most `7*2^127` and second at most `2^129`.
These fit signed136 without signed128 overflow. Squaring signed136 values and
forming `a*a-3*b*b` fits signed280. Comparison-only expressions use signed280;
an implementation must document and verify their intermediate bounds before
qualification. These are software safety limits, not proposed RTL widths.

## Accounting units and schedule

Charge the following logical actions **before** performing them:

| Action | Charge |
|---|---|
| Validate one descriptor field or operation argument | 1 |
| Scalar coefficient multiplication, including by 2 or 3 | 1 |
| Scalar coefficient addition/subtraction/negation | 1 |
| Exponent addition or negation | 1 |
| Exact embedding sign decision | 1 |
| Exact lower- or upper-ratio boundary comparison | 1 |
| Check one scalar width | 1 |
| Test one zero, norm-one or tuple-equality condition | 1 |
| Atomic tuple commit | 1 |

Sign and boundary comparisons are semantic primitives with separately specified
exact kernels; their internal arithmetic is not charged again to this logical
budget. Record their internal primitive-operation vectors separately. Logical
units are an abstract reproducible resource bound, not equal hardware costs.
The frozen implementation schedule must list each logical action in order,
including short-circuit paths. Independent checkers replay that schedule; they
must not derive expected charges from candidate counters.

A unit adjustment additionally consumes one adjustment allowance and charges
its coefficient arithmetic, exponent update and width checks. General
normalization tests lower boundary first, then upper boundary; it adjusts toward
the interval and repeats. At 64 adjustments, it may still perform the final
boundary check: success if balanced, `WORK_LIMIT` if another adjustment is needed.
Local rebalance uses the same comparisons but never a second adjustment.
Canonical equality must have a reviewed worst-case schedule below 4,096 units;
valid canonical descriptors cannot return unresolved under this default profile.

## First-failure sequence

Report the first failure in this evaluation sequence. Do not search for all
possible errors or promise a global ranking independent of evaluation order.

1. Validate operation identity, descriptor shape and exact integer types;
   reject booleans. Validate fields in argument order, a then b then k, and
   validate signed32 step increments. Fail `INVALID_INPUT` or `INVALID_ENCODING`.
2. Check operation domain: required canonical operands, nonzero inverse,
   norm-one inverse and equal-exponent addition. Fail `NONCANONICAL_INPUT`,
   `INVALID_DOMAIN` or `UNSUPPORTED_OPERATION` as applicable.
3. Take the explicit zero path before exponent arithmetic: step, conjugation,
   canonicalization and multiplication yielding zero return `(0,0,0)`.
   Inputs still require validation and operation-specific domain checks.
4. Compute and check raw exponent arithmetic. Fail `EXPONENT_OVERFLOW` before
   coefficient multiplication. Later canonical rescue does not override this.
5. Compute exact coefficient results within temporary/work limits. Use left-
   to-right formula order: ac, bd, 3bd, ac+3bd, ad, bc, ad+bc for multiplication.
6. Rebalance within the certified local or general adjustment limit. Check each
   new exponent against signed32 before its associated coefficient adjustment.
   Keep all state private; fail on the first exceeded limit or invalid invariant.
7. Check final a then b against signed64; fail `MANTISSA_OVERFLOW`. For norm,
   check signed128 publication and fail `NORM_OVERFLOW`. Commit atomically only
   after all applicable checks succeed.

Resource charging and temporary checks occur at the action where required;
they may fail during validation or domain checks. Norm overflow is not a domain
failure for equality or multiplication. An invariant violation in a certified
one-adjustment path is an implementation defect, not a normal refusal outcome.

## Required precedence and limit fixtures

Freeze literal outcomes for malformed-plus-unsupported, unsupported-plus-
exponent-overflow, exponent-plus-mantissa-overflow, zero with would-overflow
exponent arithmetic, and post-rebalance exponent overflow. Include conjugation
at signed32 minimum and boundary mantissas at signed64 minimum.

Test exact budget exhaustion before an action and success exactly at the budget;
test a final successful boundary check after the last allowed adjustment.
Reduced-budget diagnostic profiles must be named separately; they cannot replace
the default profile or make canonical equality indecisive in its supported domain.
Every refusal preserves poisoned destination tuples and aliased operands.

## Remaining review and execution gates

The [expression width proof](AOR_S1_COMPARATOR_WIDTH_PROOF_2026-10-13.md) and
[operation schedules with literal seeds](AOR_S1_OPERATION_SCHEDULES_2026-10-13.md)
are proposed review artifacts. Their existence is not independent validation;
the complete machine-readable fixture packet remains pending.

Ratify these proposed numbers and statuses, inspect exact comparator kernels and
freeze the logical schedules and literal fixtures. Then authorize isolated
implementation separately. Freeze independent oracle/checker identities and
negative controls before allocating one small qualification experiment with
explicit wall-clock and cumulative limits. No qualification has run for this
amendment, and no S3 execution follows automatically from its acceptance.
