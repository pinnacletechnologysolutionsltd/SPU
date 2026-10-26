# PSS-1 ratification preparation amendment

**Status:** HOLD FOR RATIFICATION — documentation and scenario plan only.  
**Date:** 2026-10-12.  
**Parent:** [PSS-1 draft](contract_pade_service_state_pss1_2026-10-12.md).

## 1. Current commands

```bash
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_pade_service_state_pss1_ratification_2026-10-12.md docs/README.md
```

Inspect the prepared inputs:

```bash
cat build/pade_service_state_pss1/ratification_preparation_20261012/attempt_01/source_identity.json
cat build/pade_service_state_pss1/ratification_preparation_20261012/attempt_01/scenario_plan.json
cat build/pade_service_state_pss1/ratification_preparation_20261012/attempt_01/execution_plan.json
```

These files prepare review; they neither ratify the lifecycle nor authorize code
or execution. Preserve the parent draft and its original source manifest.

## 2. Frozen source confirmation

The preparation rechecked every identity from the original review manifest.
All matched. In particular:

| Source | SHA-256 |
|---|---|
| `hardware/rtl/gpu/rplu_thimble_pade.v` | `dd8f4dfbc447d9b476e66213be62fc6cd914a277f45a2ab8e3b5dfb3fabdab5a` |
| `hardware/rtl/core/spu13/spu13_rplu2_pade_sidecar.v` | `4303de8030350068e13d5ffae2a69e2f4389f2670755c3deea11f550023f27c5` |

This establishes source identity for the audit, not independent executable RTL
verification. Freeze a separate implementation snapshot before any run. A changed
source must trigger review rather than silently adopting a new lifecycle.

## 3. Consumer result validity

For the current owned request, a consumer may publish a fresh numerical result
only on a sampled completion with `done=1` and `flags_v=0`, while that request is
outstanding and has not been cancelled. Completion without singular status is
necessary; ownership and non-cancellation are also necessary.

`done=1, flags_v=1` completes the request as a fault. It must not publish the
retained result bits as a new answer. Retained bits may belong to a previous
successful request, or may be unspecified before the first success.

After a successful completion the consumer may retain its own valid result
record, associated with that completed request. It must not infer a subsequent
request's validity from those bits or from idle status. Reset cancels ownership;
it is not an arithmetic completion. No new RTL signal or acknowledgement input
is introduced by this rule.

Add an explicit negative control: change a singular completion's consumer
publication from false to true, leaving the result bits unchanged. The checker
must reject it for RESULT_VALIDITY. This extends N06 beyond physical result-write
checking; absence of a write alone is insufficient to prove safe consumption.
Add the consumer publication event and owning request ID to mandatory trace
observations. Missing publication evidence is UNVERIFIED, not PASS.

## 4. Enumerated scenario plan

The packet enumerates 24 positive cases, 12 negative mutations and four
unsupported-domain classification cases for each of two parameter profiles:
80 planned profile executions. Positive-case expected admission, completion and
write counts are literal. Unit success requires nine multiplier transactions;
singularity requires eight. Success → singular → success requires 26.

Reset cases prime a known successful result, abort one active evaluation, reset
or drain the external engines, then admit a fresh success: three admissions,
two completions, two writes and one abort. Reset wins when asserted on a
response/completion sampling edge. Aborted partial work is recorded separately
and must not be counted as a completed evaluation.

The response-handoff reset case means the direct sampling boundary in profile 0
and the registered handoff boundary in profile 1. It does not invent a pipeline
register in profile 0. Negative timing controls must use each profile's own
expected edge convention.

Freeze 4,096 sampled cycles maximum per profile execution; no random generation.
This is an experiment bound, not a hardware latency promise. Exact cycle-level
stimulus, delay schedules, payload provenance and expected frame fixtures remain
to be prepared after implementation authorization and hashed before launch.
The scenario list is frozen for review; executable traces are not yet frozen.

## 5. Stale-response interpretation

Externally assigned ownership IDs and reset epochs exist only in the checker.
Correct rejection of a labelled stale response establishes the checker and
owner obligations; it does not establish intrinsic RTL stale-response detection.
An untagged stale response that looks like an expected response may be accepted
by the current evaluator. Any final report must state this limitation beside
reset/drain results, not only in an exclusions appendix.

Standalone software acceptance is conditional on the owner ensuring reset or
drain of outstanding engines before service reuse. Sidecar arbitration and CPU
retirement require separate integration evidence; they are not implied here.

## 6. Execution gate

Retain the proposed budget: one attempt, 900 seconds maximum and cumulative,
no retry. This allocation is NOT AUTHORIZED. The proposed command is
`python3 software/tests/test_pade_service_state_pss1.py`; its file does not yet
exist. Therefore the execution packet is explicitly NOT EXECUTABLE.

Required order: lifecycle ratification; separate isolated implementation/checker
authorization; prepare and freeze exact traces, code, tools and launch guards;
review negative-control evidence; separate execution-budget authorization;
launch via the detached runner when expected duration exceeds 60 seconds.
Full tranche qualification has a separate budget and required gates.

No Artix-7 source, candidate, job, attempt ledger or timeout is changed by this
amendment. RTL, ISA, synthesis, routing and board work remain outside PSS-1
preparation. The parent lifecycle gate remains HOLD.
