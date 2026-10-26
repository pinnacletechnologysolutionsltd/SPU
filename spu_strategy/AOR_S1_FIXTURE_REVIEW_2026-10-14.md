# AOR-S1 literal fixture review draft

Date: 2026-10-14. Preparation only; candidate implementation and qualification HOLD.

The [final owner decision](AOR_S1_FINAL_RATIFICATION_2026-10-14.md) ratifies the
correction after independent verification of submitted counts. Those counts are
reviewed mathematical expectations; candidate implementation and execution remain
HOLD. Eight recommended additions are proposed separately in the qualification
supplement, preserving all83 original rows.
The [separate-agent review](AOR_S1_INDEPENDENT_REVIEW_DISPOSITION_2026-10-14.md)
passes all submitted operation/kernel/comparator/alias expectations. Its scope
and uncovered sign/norm/equality/identity-budget paths remain explicit.

```bash
python3 -m json.tool spu_strategy/aor_s1_literal_fixtures_2026-10-14.json
python3 -m json.tool spu_strategy/aor_s1_kernel_fixtures_2026-10-14.json
python3 -m json.tool spu_strategy/aor_s1_comparator_alias_controls_2026-10-14.json
cat spu_strategy/AOR_S1_OPERATION_SCHEDULES_2026-10-13.md
cat spu_strategy/AOR_S1_COMPARATOR_WIDTH_PROOF_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/AOR_S1_FIXTURE_REVIEW_2026-10-14.md spu_strategy/aor_s1_literal_fixtures_2026-10-14.json docs/gpu_scene_preview.md docs/PARALLEL_TRANCHES_2026-10-14.md
```

The accompanying JSON is a hand-derived fixture proposal, not an executed
candidate comparison. Each count is the sum of named actions/macros from the
proposed schedule. No candidate reducer or counter generates these expectations.
The same preparer supplies these derivations; independent reviewer acceptance
remains pending. This is an initial subset, not a complete fixture packet.

## Literal derivations

For `(5,2)`, multiplication by U^-1 yields `(4,-1)` and k increases by one.
For `(5,-2)`, multiplication by U yields `(4,1)` and k decreases by one.
For `(1,1)`, multiplication by U^-1 yields `(-1,1)` at the inclusive lower
endpoint. Conjugation then reaches the excluded upper endpoint and returns
`(1,-1)` with the exponent adjustment. The mantissas `(1,0)` and `(-1,0)`
have equal embedding magnitudes and are balanced. Zero skips exponent arithmetic
after validation/domain checks. Equal-exponent opposite unit mantissas cancel.

For S=2^63, `(0,-S)` is balanced because its embedding magnitudes agree.
Its norm is `-3*S*S`, outside signed128; equality remains valid. Conjugation
produces coefficient b=S exactly in temporary storage, then fails the final
signed64 b check. Squaring `(S-1,0)` produces `(S-1)^2`, within temporary
storage and balanced, but outside final signed64 a storage.

The first-failure counts include the detecting action. A WORK_LIMIT record
consumes exactly its diagnostic budget and does not execute the next action.
Failure preserves poisoned destination `(7,-2,11)`. Alias obligations must be
expanded separately: a failed alias case preserves its actual source tuple,
not the poison tuple belonging to an unrelated destination.

## Reachability of the adjustment limit

The proposed 64-adjustment terminal-check fixture cannot be represented as an
ordinary valid stored input merely by assigning it a large exponent: k does
not affect the mantissa balance ratio.

For integer mantissa coefficients with magnitudes at most 2^64 (covering raw
signed64 inputs and a same-k sum), each embedding magnitude is less than 2^66,
since 1+sqrt(3)<4. A nonzero integer norm has absolute value at least 1, so
the ratio R=|x/x'| and its reciprocal are both less than 2^132. Each unit
adjustment changes R by U^2 or U^-2, with U^2>8. At most 45 adjustments
suffice to reach the half-open balance interval if no bounded refusal occurs
earlier. Local product/conjugation paths already have a one-adjustment bound.

Thus a successful public operation cannot exercise adjustment 64 under this
profile. Preserve the production ceiling, but specify a separate wider internal
kernel fixture or a reduced diagnostic allowance to exercise exhaustion/final
Scan behavior. Such a fixture must declare its different preconditions and must
not be counted as public-profile arithmetic qualification. This is a fixture
reachability finding, not a request to change the profile.

The [kernel fixture proposal](aor_s1_kernel_fixtures_2026-10-14.json) supplies
four literal wider-input cases. An independent Pell recurrence constructs U^64,
U^-64, U^65 and U^-65 mantissas. They fit signed136 and exceed signed64.
The two 64-power cases reach `(1,0,+/-64)` on the final permitted adjustment.
The two 65-power cases still require an adjustment after 64 and must refuse.

| Kernel input at k=0 | Result/status | Scan/adjustment-only units |
|---|---|---:|
| U^64 | `(1,0,64)` | 1026 |
| U^-64 | `(1,0,-64)` | 962 |
| U^65 | WORK_LIMIT, no published result | 1026 |
| U^-65 | WORK_LIMIT, no published result | 961 |

Upper iterations cost 2 comparisons plus 14 adjustment units. Lower iterations
cost 1 comparison plus 14 adjustment units. A successful final Scan costs 2;
an exhausted lower request costs 1 and stops before adjustment arithmetic.
These counts exclude public validation, dispatch, final storage and commit.
The public API must reject these oversized input mantissas; a future direct
kernel test must declare that boundary rather than bypass public validation
silently. No normalizer implementation or kernel qualification runs here.

A fifth kernel diagnostic uses a=b=2^135-1 at the excluded upper endpoint.
The first U^-1 adjustment computes 2a, exceeding signed136. After Scan2,
exponent arithmetic/check2 and multiply/check2, it must refuse TEMPORARY_LIMIT
at 6 kernel units, without completing an adjustment or publishing state.

## Expanded operation, comparator and state proposals

The operation draft now contains 83 rows, including 50 subsequent malformed
input and precedence proposals. Three successful adjustment paths have
explicit distributive derivations:

| Operation | Raw mantissa | Canonical result | Charged units |
|---|---|---|---:|
| `(-1,1,0) * (4,-1,0)` | `(-7,5)` | `(1,3,-1)` after lower adjustment | 61 |
| `(4,1,0) * (1,2,0)` | `(10,9)` | `(-7,8,1)` after upper adjustment | 62 |
| `(4,0,0) + (3,4,0)` | `(7,4)` | `(1,0,2)` after two upper adjustments | 66 |

The two products have negative norms -26 and -143, respectively. The sum's
raw mantissa is U^2: intermediate `(2,1)` is still at an excluded upper
ratio, so a second adjustment is required. Other added rows distinguish
noncanonical zero and unequal-k rejection before any coefficient/exponent
arithmetic on large operands.

The [comparator/alias/control proposal](aor_s1_comparator_alias_controls_2026-10-14.json)
contains 11 literal comparator cases covering all four embedding-sign pairs,
both signed endpoints, below/above balance and signed64 minimum. Lower and
upper expressions retain exact `[1,sqrt(3)]` coefficients and expected signs.
Thirteen register-state alias cases specify complete pre/post maps, preserving
the actual source value on failure and changing only the destination on success.
These maps describe values; they do not qualify a runtime ownership implementation.

The short [preparation witnesses](../build/parallel_tranches_20261014/aor_literal_review_01/review_result.json)
check successful literal values by bounded exact Pell expansion, comparator
signs by rational isolation `5/3 < sqrt(3) < 7/4`, and alias-map consistency.
A zero-product witness uses the zero-annihilation identity instead of expanding
its other operand's large exponent. The first review-helper run stopped at its
expansion bound before making that distinction; the correction and original
failure are recorded in `preparation_history.json`. The expansion bound remains
abs(k)<=1000. Failure statuses, work counts and mutations are not executed.
The same author prepared the packet and witnesses; no independent sign-off
or candidate qualification follows from these checks.

Eleven named negative controls prescribe a mutation site, witness and required
rejection label. They cover endpoint/sign mistakes, dropped 3bd, exponent,
equality, charge, early commit, local-adjustment count, norm publication and
terminal Scan charges. The checker is NOT IMPLEMENTED; no injected fault has
yet been executed or rejected. These labels are obligations, not test results.

## Review discrepancies and remaining obligations

**Resolved adjustment-count contradiction:** the original schedule charges four constant
multiplications but the width proof lists only three. The separate
[minimal correction](contract_aor_s1_schedule_reconciliation_2026-10-14.md)
proposes an explicit checked 1a action to preserve all drafted adjustment counts.
The owner ratified that correction after independent review. Original
schedule/proof documents remain unchanged; candidate implementation still needs
separate authorization.

The same proposal resolves generic versus specific resource statuses and freezes
the immutable-tuple/JSON-codec boundary. Added malformed cases cover a/b/k Boolean,
decimal, null and string values; both out-of-range boundaries for each field;
wrong descriptor shapes; unknown/nonstring operation identity; missing/extra and
noncontainer arguments; right-operand validation; invalid increments; canonical
checks after complete validation; and zero/width-check budget boundaries.
These are literal expected outcomes, not executed candidate rejections.

The original fragment draft uses generic RESOURCE_LIMIT whereas the later
amendment distinguishes TEMPORARY_LIMIT and WORK_LIMIT. Final ratification now
explicitly supersedes the generic names for this profile.

Literal proposals now cover the listed comparator, product, sum, temporary,
alias, malformed-input and rejection-label families. Submitted-fixture independent
review now passes and schedule/status/codec ratification is recorded. Supplemental
coverage execution, executable checker/oracle identities and actual injected-fault
rejection evidence remain pending. Keep candidate
implementation HOLD until its pre-implementation review gates are satisfied;
qualification needs a separately frozen execution contract and budget.
