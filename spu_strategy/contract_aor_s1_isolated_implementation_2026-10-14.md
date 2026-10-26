# Engineering contract: isolated AOR-S1 implementation and qualification

```bash
cat spu_strategy/contract_aor_s1_isolated_implementation_2026-10-14.md
python3 -m json.tool spu_strategy/aor_s1_qualification_supplement_2026-10-14.json
python3 -m json.tool spu_strategy/aor_s1_executable_mutation_plan_2026-10-14.json
python3 -m json.tool spu_strategy/aor_s1_implementation_execution_plan_2026-10-14.json
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_aor_s1_isolated_implementation_2026-10-14.md spu_strategy/aor_s1_qualification_supplement_2026-10-14.json spu_strategy/aor_s1_executable_mutation_plan_2026-10-14.json spu_strategy/aor_s1_implementation_execution_plan_2026-10-14.json
```

Date: 2026-10-14. Status: AUTHORIZED IMPLEMENTATION AND THREE CONTRACTED STAGES.
The owner's later instruction, `Authorized, 3 attempts. Repairs and diagnosis
authorized.`, authorizes this contract's implementation and staged budget.
Retain [the allocation record](../build/aor_s1/implementation_qualification_20261014/authorization_01/owner_authorization.json).
One slot per stage, fixed1800/3600/7200-second limits and12600-second cumulative
budget apply. No board programming or ISA change is in scope. The earlier
[ratification](AOR_S1_FINAL_RATIFICATION_2026-10-14.md) remains decision history;
the later execution instruction supplies the additional authority.

Roles: spec author prepares this packet; implementer conducts halt-and-flag
preflight after separate authorization; independent auditor checks oracle,
checker, source identities and evidence before promotion. The prior separate-agent
fixture review is not acceptance of an unimplemented candidate or checker.

## 1. Freeze the inputs and scope

Use the ratified [schedule/status/codec amendment](contract_aor_s1_schedule_reconciliation_2026-10-14.md),
original finite-profile, comparator proof and operation schedules. The amendment
supersedes their generic resource names and ambiguous fourth multiplication only.
Do not change numerical limits, domains, half-open interval, raw-exponent-first
rule, exact-zero exception, alias semantics or failure order during implementation.

Verify the SHA256 identities in the [proposed execution plan](aor_s1_implementation_execution_plan_2026-10-14.json)
before coding and before every authorized launch. Retain original reviewed inputs
and evidence. The original 83-operation, five-kernel, 11-comparator and 13-alias
packets remain byte-identical. Reject duplicate fixture IDs across packets.

Load eight additional witnesses from the separate
[supplement](aor_s1_qualification_supplement_2026-10-14.json): three sign outcomes,
false equality, successful norm, and budgets 20/21/22 immediately surrounding
checked 1a. Proposed operation coverage is 83+8=91. Supplemental inclusion is
not a new independent qualification result.

Create only these isolated candidate files after authorization:

```text
software/research/aor_s1/__init__.py
software/research/aor_s1/budget.py
software/research/aor_s1/validation.py
software/research/aor_s1/comparator.py
software/research/aor_s1/normalize.py
software/research/aor_s1/arithmetic.py
software/research/aor_s1/execute.py
```

Create independent verification files after authorization:

```text
software/research/aor_s1_verification/__init__.py
software/research/aor_s1_verification/codec.py
software/research/aor_s1_verification/oracle.py
software/research/aor_s1_verification/obligations.py
software/research/aor_s1_verification/mutations.py
software/research/aor_s1_verification/qualification.py
software/research/aor_s1_verification/schedule.py
software/research/aor_s1_verification/schedule_arithmetic.py
software/tests/test_aor_s1.py
tools/qualify_aor_s1.py
tools/verify_aor_s1_repo_gates.sh
```

Keep single-purpose implementation modules at 50–150 lines where substantive;
package markers may be shorter. The two schedule replay modules are a recorded
repair split, separating validation/control from arithmetic ledger replay while
meeting the Lithic size limits. Flag a required scope split before adding an
unlisted module. Do not edit existing AOR-1, VM, assembler, ISA, RTL, board,
generated files or shared test-runner code. Run the new tests explicitly.

## 2. Implement the ratified finite profile literally

Use exact integers: stored a,b signed64, k/increment signed32; coefficient
temporaries signed136, comparator/norm workspace signed280, published norm
signed128; at most64 general adjustments or one certified local adjustment.
Default logical budget4096; diagnostic settings are declared exact integers in
0..4096. Reject malformed configuration as a harness/infrastructure error before
candidate execution; do not invent a charged candidate arithmetic status for it.

Expose `execute(operation, arguments, destination, budget=4096)` and return an
immutable outcome containing `status`, `result`, `destination`, `charged_units`,
`adjustments`, `events`, `next_action` and separate `primitive_counts`.
Inputs are immutable tuples. Do not mutate callers. `result` is None on refusal,
a descriptor for successful mutating operations, or a scalar for norm/sign/equality.
For read-only success and every refusal, return the original destination.
For mutating success, change destination only at the charged atomic commit action.
Destination is trusted existing state supplied by the harness, not another
arithmetic operand. Do not add unreviewed destination-validation charges.
Distinguish false/zero scalar success from absent output by status, not truthiness.

Charge before each action; do not charge arithmetic/check pairs as an indivisible
block. Record the ordered action/value ledger and the unexecuted next action on
WORK_LIMIT. Count the action detecting a failure. Record failed width checks
without narrowing/wrapping first. Record completed adjustments separately from
charged partial adjustment actions.

Implement the seven ratified adjustment steps with original private a,b reads:
exponent/check, 2a/check, 3b/check, first coefficient/check, 1a/check, 2b/check,
second coefficient/check. Keep all intermediate values private. Preserve the
fourteen logical units, including checked identity multiplication.
Never report that convention as mathematical necessity or measured hardware work.

Implement the exact comparator and expression bounds from the reviewed proof.
Record internal kernel operation vectors separately from logical units. Do not
charge comparator-internal signs twice. Permit wide diagnostic inputs only at
an explicitly internal normalizer entry point; the public API still rejects
out-of-storage-width fields. A second requested local adjustment is an implementation
defect, not an ordinary refusal status. Fail qualification on that defect.

## 3. Preserve verification independence

Candidate files must not import verifier arithmetic or fixtures. Oracle and
obligations code must not import candidate arithmetic, comparator, reducer,
validation, counters or reviewer witness code. The qualification adapter alone
may invoke both sides. Shared Python standard-library facilities are permitted;
shared generated expected answers or arithmetic helpers are not.

Use the ratified JSON-to-immutable-tuple codec without field coercion. Preserve
Boolean/decimal/string/null distinctions and malformed shapes. Test direct list
rejection at the public candidate API separately from JSON tuple adaptation.
Parsing/codec overhead is outside candidate logical charges and must be counted
in any later end-to-end workload study.

Use independent exact Pell expansion/value identities for supported semantic
witnesses and a separately derived exact ordering algorithm, such as rational
root isolation with integer square roots. Do not reuse the candidate sign-square
kernel as the oracle's ordering implementation. Enforce the existing oracle
ceilings: 1,000,000 coefficient magnitude bits and 100,000 exact pair products
per case. Check bounds during work, not after oversized materialization.

Use norm-one and zero-annihilation identities where expansion is unnecessary;
declare those proof paths in the result. Large-exponent refusal cases use frozen
first-failure expectations and input/state checks; never force unnecessary
expansion to turn oracle exhaustion into a candidate verdict. Any checker-limit
outcome on a required witness is infrastructure unavailability, not inequality,
numerical overflow or a qualifying pass.

Check literal statuses, results and charges against the independent fixture
packet; replay action legality, width/allowance checks, charge-before-action and
atomic publication independently of the candidate counter. Preserve the reviewed
83-row input identity and disclose that the eight supplemental expectations come
from the reviewer's recommendations. Independent auditor acceptance remains a
separate prerequisite; the prior author's helper is not that auditor.

For alias cases, load the actual source/destination values from pre_state, invoke
the candidate using the same immutable source tuple for aliased destinations,
and publish its returned destination into the observed map. Compare all registers
and input snapshots with the frozen post_state. A returned partial destination
must change the observation and fail the check. This harness tests API publication,
not hardware register ownership, reset or concurrent access.

## 4. Execute falsifiable mutation controls after authorization

Implement the [26-control plan](aor_s1_executable_mutation_plan_2026-10-14.json):
11 candidate controls, four oracle controls and 11 checker meta-controls.
For each, retain the clean same-fixture result, the actual changed observation,
mutation source/adapter identity and exact rejection labels. Require the clean
baseline to pass and the corrupted observation to differ. The checker must not
receive a mutation ID or injected-fault flag as evidence that an answer is wrong.

Inject dropped3bd at the private product arithmetic boundary before normalization;
do not substitute an unrelated canned wrong answer for that arithmetic mutation.
Use isolated private predicate/result replacements for endpoint, sign, exponent,
equality, charge, partial destination, extra adjustment and norm-publication faults.
Omit terminal Scan actions/charges on the wide kernel witness for its control.
Restore the clean candidate between controls; do not add public production fault
switches or change unrelated arithmetic code.

Allow multiple independent checker rejection labels where a corruption violates
multiple obligations. Require the plan's named label to be present; do not require
it to be the first checker finding. Candidate first-failure ordering remains a
separate invariant. This avoids forcing a misleading single label when dropped3bd
also changes the rebalance exponent or work count.

For four oracle controls, change sign, false equality, norm and product answers
while retaining frozen literal obligations and an unmodified candidate. Require
the independent obligations checker to reject each changed oracle answer.
For every checker meta-control, suppress the required named predicate/label on
its paired known corruption. The outer qualification assertion must detect the
missing label even if other rejection labels remain; record
META_REJECT_CHECKER_MISSED_REQUIRED_LABEL. A checker accepting its injected fault,
an unchanged mutant, an unreachable mutation or an always-rejecting checker fails
qualification. Never report planned controls as observed rejection evidence.

## 5. Freeze future commands and proposed budgets

The following commands are now authorized under the recorded three-stage budget.
Require source review and freeze before software launch, preceding evidence review
before each later launch, and CPU resource coordination before the Padé gate.
Use fresh output directories; no automatic retries, timeout extensions or substitute
methods. Any launch consumes that stage's one slot regardless of its result.

| Stage | Maximum attempts | Timeout | Proposed budget |
|---|---:|---:|---:|
| software_01: tests, fixtures, oracle/checker and mutations | 1 | 1800s | 1800s |
| repo_01: mandatory repository/trace/math gates | 1 | 3600s | 3600s |
| pade_01: mandatory Artix-7 Padé synthesis/route gate | 1 | 7200s | 7200s |
| Total | 3 | Per-stage limits above | 12600s |

Software qualification, after preflight and source freeze:

```bash
tools/run_detached_job.sh --output build/aor_s1/implementation_qualification_20261014/software_01 --timeout 1800 --notify-desktop -- python3 tools/qualify_aor_s1.py --fixtures spu_strategy/aor_s1_literal_fixtures_2026-10-14.json --supplement spu_strategy/aor_s1_qualification_supplement_2026-10-14.json --kernels spu_strategy/aor_s1_kernel_fixtures_2026-10-14.json --controls spu_strategy/aor_s1_comparator_alias_controls_2026-10-14.json --mutations spu_strategy/aor_s1_executable_mutation_plan_2026-10-14.json --output build/aor_s1/implementation_qualification_20261014/software_01/results
```

Require that qualifier to run `python3 software/tests/test_aor_s1.py` and then
all frozen fixture groups and controls, retaining command results separately.
Write a software PASS marker only after every predicate below succeeds.

Implement the future repository gate script as these commands in exact order,
with nonzero exit stopping the stage; do not skip tests or alter shared runners:

```bash
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
```

No new RTL subsystem exists for TB_FILTER triage; the explicit new software tests
are its focused check. Retain the full gates required for arithmetic-kernel changes.

```bash
tools/run_detached_job.sh --output build/aor_s1/implementation_qualification_20261014/repo_01 --timeout 3600 --notify-desktop -- bash tools/verify_aor_s1_repo_gates.sh
```

The required synthesis gate is explicitly included in the owner's three-stage
allocation; it still requires preceding gate review and CPU resource coordination.
No future software-only approval may authorize a different FPGA job implicitly:

```bash
tools/run_detached_job.sh --output build/aor_s1/implementation_qualification_20261014/pade_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

End the agent turn after each LAUNCHED. A later invocation may interpret a stage
only with exactly one COMPLETE, FAILED or TIMEOUT marker. TIMEOUT is infrastructure,
not an arithmetic failure. Run stages sequentially, only after preceding evidence
review and their separate authorization. Budget exhaustion requires a new owner
decision; it cannot justify another attempt or longer timeout.

## 6. Acceptance and stop conditions

Require all91 operation, five kernel, 11 comparator and 13 alias witnesses to match;
all26 mutation controls to meet their clean/corrupted/rejection obligations; input
snapshots and oracle/checker import separation to remain intact; and source/tool
identities, commands, outcomes, first counterexamples and limitations to be retained.
Check direct candidate tuple/list behavior, unchanged malformed values and successful
zero/false scalar publication in the focused API tests.

Retain expected and observed values/counts, action traces and scalar widths.
Recheck sources before/after execution; mixed-source results cannot qualify.
Record logical/kernel counts independently of host timings. Make no compactness,
speedup, hardware resource or silicon claim from this finite software result.

Require every authorized required stage COMPLETE and inspect its acceptance
records before overall qualification. If only the focused stage passes, report
FOCUSED_SOFTWARE_PASS / REPOSITORY_OR_SYNTHESIS_GATES_PENDING, not full qualification.
Exit zero alone does not establish complete timing coverage or hardware behavior.
For the Padé regression gate, retain device/constraints, utilization, all required
clock reports and timing coverage; verify the declared 25 MHz target and applicable
clock constraints before accepting that gate. This evaluates the existing Padé
build, not AOR hardware, and grants no AOR timing/resource or board-functional claim.

Halt and flag contradictory semantics, a mismatching fixture, premature writes,
unchecked width, unsound equality, unresolved required oracle witness, accepted
injected fault or changed frozen inputs. Do not silently amend a fixture, expand
the domain, widen temporaries or consume another attempt. Scope changes and repairs
need a concrete minimal correction reviewed under the root engineering contract.
