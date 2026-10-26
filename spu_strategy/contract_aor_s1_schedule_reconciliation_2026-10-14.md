# AOR-S1 schedule and status reconciliation

```bash
cat spu_strategy/contract_aor_s1_schedule_reconciliation_2026-10-14.md
python3 -m json.tool spu_strategy/aor_s1_literal_fixtures_2026-10-14.json
python3 -m json.tool spu_strategy/aor_s1_kernel_fixtures_2026-10-14.json
python3 -m json.tool spu_strategy/aor_s1_comparator_alias_controls_2026-10-14.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_aor_s1_schedule_reconciliation_2026-10-14.md spu_strategy/AOR_S1_FIXTURE_REVIEW_2026-10-14.md spu_strategy/AOR_S1_REVIEW_PACKET_2026-10-14.md spu_strategy/aor_s1_literal_fixtures_2026-10-14.json docs/PARALLEL_TRANCHES_2026-10-14.md
```

Date: 2026-10-14. Status: RATIFIED SPECIFICATION AMENDMENT.
The owner explicitly ratified this amendment after the separate-agent review
passed all submitted mathematics, ordered charges and outcomes. The checked 1a
action, 14-unit adjustment, status precedence and input rules are ratified.
See the [final decision](AOR_S1_FINAL_RATIFICATION_2026-10-14.md).
Candidate implementation remains HOLD; qualification, ISA changes and FPGA work
are not authorized. Only separate implementation/qualification contract
preparation is authorized. No execution budget is allocated by ratification.
Roles: spec author records the correction; independent reviewer audits counts
and consistency; implementer waits for separate authorization.

## Pre-execution finding and scope

The [operation schedule](AOR_S1_OPERATION_SCHEDULES_2026-10-13.md) charges four
constant multiplications and two additions/subtractions per unit adjustment:
12 coefficient units plus 2 exponent units. The
[width proof](AOR_S1_COMPARATOR_WIDTH_PROOF_2026-10-13.md) lists only 2a, 3b
and 2b: three multiplications and two additions/subtractions. Direct execution
of those formulas would cost 12 total units rather than the scheduled 14.
The ratified sequence below resolves that ambiguity after independent fixture
review. The prior draft and
its preparation evidence remain retained in
`build/parallel_tranches_20261014/schedule_reconciliation_review_01/sources/`.

Keep original documents, prior results and the current proposed numerical
profile intact. This correction is the ratified amendment for the subjects it
addresses; broader qualification and candidate authorization remain separate.

## Minimal correction preserving existing counts

Use an explicit checked identity multiplication as the fourth multiplication.
After allowance validation, charge and execute these actions in exactly this order:

| Step | Action | Logical units |
|---|---|---:|
| 1 | Compute k-1 for U, or k+1 for U^-1; check signed32 | 2 |
| 2 | Compute 2a; check signed136 | 2 |
| 3 | Compute 3b; check signed136 | 2 |
| 4 | Compute 2a+3b for U, or 2a-3b for U^-1; check signed136 | 2 |
| 5 | Compute 1a; check signed136 | 2 |
| 6 | Compute 2b; check signed136 | 2 |
| 7 | Compute 1a+2b for U, or 2b-1a for U^-1; check signed136 | 2 |

All coefficient actions read the original private a,b of that adjustment, never
the newly calculated first coefficient. Both coefficients and the exponent
remain private until complete operation success. Charge before each individual
arithmetic or check, rather than charging an inseparable two-unit block.
The identity multiplication is a declared logical action; a host optimizer may
remove its machine instruction without removing its logical charge or check.
Logical units remain distinct from host instructions or future FPGA costs.
The checked identity multiplication is a contractual accounting convention,
not evidence that four multiplications are mathematically necessary. Any future
benchmark must disclose it and give compared representations equivalent treatment;
never label its two logical units as measured hardware work.

Multiplication by 1 preserves the operand and its bound. This introduces no new
larger width requirement, but still requires the stated width check in the
schedule. General signed136 intermediates may refuse at earlier actions. The
local rebalance theorem, balance interval, exponent-first rule and final storage
checks are unchanged. Success remains 14 units per adjustment, upper Scan2,
lower Scan1 and final successful Scan2; proposed fixture totals remain unchanged.

Removing the fourth charge instead would require a different explicit amendment
and recounting every adjustment-bearing fixture. Do not silently do that as an
implementation optimization.

## Ratified resource-status precedence

Ratification makes the finite-profile amendment's specific names supersede
generic RESOURCE_LIMIT wording in the original fragment draft for this S1 profile.

| Status | Trigger |
|---|---|
| WORK_LIMIT | Next action has no available logical unit, or another adjustment is requested beyond the allowance |
| TEMPORARY_LIMIT | A charged temporary-width check fails before publication |
| EXPONENT_OVERFLOW | A charged computed exponent signed32 check fails |
| MANTISSA_OVERFLOW | A charged final a or b signed64 publication check fails |
| NORM_OVERFLOW | A charged norm signed128 publication check fails |
| INVALID_ENCODING | Charged operation identity/type check rejects the operation |
| INVALID_INPUT | Charged arity, descriptor shape/type/stored-width or increment type/width check fails |
| NONCANONICAL_INPUT | Required canonical-operand check fails |
| INVALID_DOMAIN | Unit inverse reaches the charged zero-domain check |
| UNSUPPORTED_OPERATION | Unit inverse norm-one check or same-k equality check rejects the domain |

First failure follows execution order; WORK_LIMIT can occur before a later input
or domain defect. Do not translate resource refusal into mathematical inequality,
overflow or a successful partial result. No RESOURCE_LIMIT alias would be emitted
by this profile. Checker expansion exhaustion remains an infrastructure outcome,
distinct from candidate statuses. A violated certified one-adjustment invariant
is an implementation defect, not an ordinary arithmetic refusal.

## Ratified input and fixture codec

The operation identity is an exact string in the finite set `canonicalize`,
`step`, `conjugate`, `multiply`, `same_k_sum`, `norm`, `sign`, `equality`,
`unit_inverse`. Other strings and nonstrings fail INVALID_ENCODING at action 1.
This is software vocabulary, not an ISA opcode assignment. Sign and norm admit
raw valid descriptors; other operation domains follow the original schedule.

The candidate's descriptor input is an immutable tuple of three exact Python
integers. Booleans, decimal values, strings and nulls fail field-type checks.
An outer immutable argument tuple has the operation's exact arity. Within the
fixture adapter only, JSON arrays in descriptor positions are converted to
tuples, preserving wrong lengths; other container/value types remain unchanged.
Do not convert Boolean, decimal or string fields to integers. The adapter is
outside candidate arithmetic charging; parse/adapter cost belongs to any later
end-to-end workload comparison. Shape and argument checks remain charged inside
the candidate. Direct candidate lists are not tuples and fail its shape check.

The opcode action checks identity/type; the arity action checks the outer
argument tuple shape and length. It executes before any descriptor inspection.
Step has one descriptor plus one integer increment; binary operations have two
descriptors; all other operations have one descriptor. Validate every descriptor
in argument order before canonical/domain checks, and validate the increment
after descriptor validation. Diagnostic budgets are declared fixture settings,
including zero, not silently coerced call arguments.

## Review exit and subsequent work

The 83 operation rows, five kernel rows, 11 comparator rows, 13 alias rows and
11 planned mutations are review inputs, not qualification. Shape/type/range,
all-validation-before-domain and low-budget first-failure proposals now have
explicit witnesses. The independent review passed all 83 operation rows,
five kernel rows, 11 comparators and 13 alias maps without numerical correction.
Separate-agent review does not imply independent human sign-off or candidate
qualification. The owner accepted that review for final amendment ratification.
Executable checker/oracle review and implementation authorization remain pending.

After ratification, draft a separate isolated implementation/qualification
contract identifying candidate files, independent oracle/checker files, required
gates, commands and frozen attempt/time budgets. Candidate, oracle and checker
must remain separate; an oracle accepting its injected fault fails qualification.
This proposal does not allocate that execution or change CPU, GPU, E8 or SGN work.
