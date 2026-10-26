# QCG-0 P0 draft-contract independent review allowance

Date: 2026-10-23. Owner requested the independent reviewer take the draft through
its section 10 checklist, including rule-derived counts and W31 refusal stages.
This is review authority only; D-1 through D-5 remain owner decisions. No freeze,
candidate implementation, pilot or benchmark authorization is conveyed.

Reviewer: /root/qcg0_fixture_reviewer, independent of the contract author and
HEX-SOM acceptance context. Verify pins before review or calculation:

    21fb45af84d609c3c127010a10b0c2824aaac4772ab8d95a4abd9f5d8d2b8bfc  QCG0_P0_EXECUTION_CONTRACT.md
    eade4b5f0957c3679c94b67d8f4b1f6b6d005d65316a5337e6c8dfb9370b98dd  QCG0_PREREGISTRATION.md
    244e73004c51b3339465ac65eb0f97da5d5ae01d4d48b281f416de922f8a4bff  QCG0_PREREGISTRATION_REVISION_3_1.diff

Also verify the prior review artifacts and exact values referenced by section 0;
do not regenerate or reselect certified curves. Preserve all input files.

Class A bounded review calculations, only if needed: at most two invocations,
30 seconds each, 1 GiB per-process address space, 60 seconds cumulative external
ceiling; no child processes/network/devices/installations/services, 10 MiB new
outputs maximum. Exact rational scalars only, at most 4096 reduced bits and
16384 raw bits. Inspect scripts and verify callable executable prerequisites
before execution. Command pattern: /usr/bin/timeout --signal=KILL 30
/usr/bin/prlimit --as=1073741824:1073741824 -- /usr/bin/python3 -B -I <review-script>.
Record each invocation's exact argv/cwd, script/input hashes, limits, transcript,
exit and stdlib resource usage. Ordinary corrections may use only the remaining
slot; no automatic timeout retry or budget expansion.

Permitted calculations: independent small symbolic/rational ledger examples,
checking written helper procedures and deriving literal refusal expectations
where the draft uniquely defines them. No candidate engines, P0 harness, arm
benchmark or full tape campaign. If operation order/width/status rules do not
determine a unique expected stage, flag that defect; do not invent semantics or
implement a repaired contract to obtain a result. A blocked stage derivation
does not require spending a calculation slot.

Write new review scripts, logs, certificate, expectations and manifest only in
research/qcg_0/. Use new P0-contract-review names and refuse overwrite. Do not
modify the draft, pre-registration, certified/reference data, previous reviews
or other campaigns. Report PASS / REVISE / BLOCKED for every checklist item,
distinguishing missing owner decisions from mathematical/measurement defects.
No change to implementation or execution HOLD follows from this allowance.
