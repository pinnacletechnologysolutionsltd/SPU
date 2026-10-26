# AOR-S1 proposed charged operation schedules

**Status:** PROPOSED; literal counts hand-derived, independent review pending.

```bash
sed -n '1,240p' spu_strategy/AOR_S1_OPERATION_SCHEDULES_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
```

This refines the [finite-profile amendment](contract_aor_s1_finite_profile_amendment_2026-10-13.md).
No model, checker or qualification execution is authorized by this document.
The [comparator proof](AOR_S1_COMPARATOR_WIDTH_PROOF_2026-10-13.md) fixes the
internal comparator kernel; its primitive vectors are distinct from logical units.

## Shared schedule macros

Every listed logical action costs1. Charge before execution: if no unit remains,
fail WORK_LIMIT without executing the action. A charged action that discovers a
mathematical/input error still consumes its unit. No global error search follows.
Shape and opcode checks refine the previous operation-argument validation category.

| Macro | Ordered actions and charges |
|---|---|
| V | Opcode check1; argument-count check1; for each descriptor: shape1, then type1+stored-width1 for a, b, k. Unary9, binary16 |
| Increment validation | Type1 then signed32 width1, after descriptor validation |
| C | Zero test1; if zero, canonical-zero tuple test1. Otherwise lower compare1 then upper compare1, rejecting at the first failed balance test. Valid nonzero3, valid zero2 |
| Z | Zero test1 per operand, left to right; binary executes both tests |
| E | Exponent addition/negation1, then signed32 check1 |
| Scalar arithmetic | Arithmetic1 followed immediately by temporary-width check1 |
| Scan | Lower compare1; if below, skip upper and request U adjustment; otherwise upper compare1 and request U^-1 adjustment if at least upper endpoint |
| Adjustment | Check allowance without consuming a logical unit; E2; four scalar constant multiplies and two adds/subtracts, each arithmetic+width check:12; total14 |
| F | Final a signed64 check1; b signed64 check1; k signed32 check1; atomic tuple commit1; total4 |
| N | a*a, b*b, 3*(b*b), first minus third, each arithmetic+signed280 check; total8 |

Unknown opcode stops at V's first action, INVALID_ENCODING. Wrong arity or
descriptor shape/type is INVALID_INPUT. Out-of-storage-range input fields are
INVALID_INPUT. C rejection is NONCANONICAL_INPUT. Comparator internal signs
are included in the boundary primitive and are not charged a second time.
Standalone SIGN charges one sign primitive. No hidden extra sign/zero tests
are permitted in the logical schedule; internal implementation work is recorded
separately. Operand traversal stops on the first error.

General Scan repeats after each adjustment. Even when an allowance is fully
consumed, Scan may establish success without another adjustment. A requested
adjustment beyond the allowance returns WORK_LIMIT before exponent arithmetic.
Local Scan uses the same order, followed by one final Scan after adjustment;
any request for a second adjustment is a checker-visible implementation defect.

## Supported operations and successful path totals

| Operation | Ordered schedule | No-adjustment nonzero total |
|---|---|---|
| Canonicalize | V, Z, general Scan/Adjustment loop, F | 16 |
| Step | V, increment validation, C, Z, E, F | 21 |
| Conjugate | V, C, Z, E, b negation+width, local Scan/Adjustment, F | 23 |
| Multiply | V, C(left), C(right), Z(left), Z(right), E, seven scalar actions in amendment order, local Scan/Adjustment, F | 46 |
| Same-k sum | V, C(left), C(right), equal-k test1, two scalar sums+width, Z(result), general Scan/Adjustment, F | 34 |
| Norm | V, N, signed128 publication check1; return scalar | 18 |
| Sign | V, sign primitive1; return scalar | 10 |
| Equality | V, C(left), C(right), tuple comparison1; return boolean | 23 |

Canonicalize, norm and sign admit raw valid descriptors. Other operations require
canonical operands; inverse is specified below. For mutating operations, zero
skips E, coefficient arithmetic and Scan and uses F. Same-k sum recognizes zero
only after exact coefficient addition. Same-k test failure is UNSUPPORTED_OPERATION.
Unequal-exponent sums are not aligned implicitly. Every read-only return is
published only on success; it does not charge a tuple commit.

Unit inverse: V, C, zero test1 (zero fails INVALID_DOMAIN), N, norm-one test1
(nonunit fails UNSUPPORTED_OPERATION), then E, b negation+width, local Scan/
Adjustment, F. Successful nonzero no-adjustment total32. A boundary adjustment
and rescan adds16. A general nonunit inverse is not separately materialized.

For general normalization with L lower adjustments and H upper adjustments,
Scan/Adjustment total is `15L+16H+2` on success. Canonicalize totals
`16+15L+16H`; nonzero same-k sum totals `34+15L+16H`.
Maximum64 adjustments give at most1,058 units for nonzero same-k sum, below4,096,
before considering earlier temporary/exponent refusal. This counts logical
primitives, not constant-time arbitrary-precision arithmetic.

Equality costs at most23 units for valid canonical operands, including all
validation; zero operands can cost less. Thus the default4,096 budget admits
decisive equality. Lower diagnostic budgets explicitly test first-failure behavior.

## Literal outcome seeds

All mutating failures preserve destination `(7,-2,11)`. Inputs and sources are
immutable; alias tests use the same outcome with destination aliased to a source.
Counts below include the action that detects an error, except WORK_LIMIT, where
the next uncharged action does not run. These seeds are not a complete fixture packet.

| Operation and input | Expected result/status | Charged units |
|---|---|---|
| Canonicalize `(5,2,0)` | `(4,-1,1)` | 32 |
| Canonicalize `(5,-2,0)` | `(4,1,-1)` | 31 |
| Canonicalize `(1,1,0)` | `(-1,1,1)` | 32 |
| Conjugate `(-1,1,1)` | `(1,-1,0)` | 39 |
| Multiply `(1,0,1000)`, `(1,0,-1000)` | `(1,0,0)` | 46 |
| Step `(0,0,0)`, increment2147483647 | `(0,0,0)` | 18 |
| Step `(1,0,2147483647)`, increment1 | EXPONENT_OVERFLOW | 17 |
| Conjugate `(1,0,-2147483648)` | EXPONENT_OVERFLOW | 15 |
| Canonicalize `(1,1,2147483647)` | EXPONENT_OVERFLOW during adjustment | 14 |
| Same case, diagnostic budget13 | WORK_LIMIT before exponent check | 13 |
| Norm `(0,-9223372036854775808,0)` | NORM_OVERFLOW | 18 |
| Equality of that descriptor with itself | true | 23 |
| Same-k sum `(1,0,0)`, `(-1,0,0)` | `(0,0,0)` | 32 |
| Step `(1,0,0)`, increment0, budget21 | `(1,0,0)` | 21 |
| Same case, budget20 | WORK_LIMIT before commit | 20 |
| Step `(true,0,0)`, increment0, budget3 | WORK_LIMIT before a type check | 3 |
| Same malformed case, budget4 | INVALID_INPUT | 4 |

The norm/equality seed's mantissa is balanced: embedding magnitudes are equal.
Norm output overflow must not contaminate the equality-domain decision.
The malformed-input seeds explicitly show that WORK_LIMIT can precede a later
input error in a reduced-budget diagnostic profile.

## Outstanding fixture review

Expand these seeds into independently inspected machine-readable fixtures for
every zero/domain/adjustment path, multiplication direction, overlapping final
overflow and unsupported-domain outcome. Include 64-adjustment terminal-check
diagnostics, temporary-width boundary primitives and all required negative controls.
Freeze exact counts independently of candidate counters. These pending items,
including the hand-derived schedules above, keep ratification and execution HOLD.
