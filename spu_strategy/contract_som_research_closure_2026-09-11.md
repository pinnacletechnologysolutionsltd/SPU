# Engineering Contract: SPU-4 SOM Research Closure

**Date:** 2026-09-11  
**Contract ID:** `contract_som_research_closure_2026-09-11.md`  
**Status:** ACTIVE — owner authorized in session on 2026-09-11  

**Roles:**
- **Spec Author:** Owner and Codex
- **Halt-and-Flag Implementer:** Codex
- **Integration Auditor:** `bash tools/verify_repo.sh`

## 1. Objective

Close the SPU-4 SOM/INA226 research programme in a durable, defensible state.
Preserve the established evidence without further diagnosis, hardware work,
observer development, synthesis, repair, or benchmarking.

## 2. Authorized writes

- This contract.
- `build/spu4_ina226_benchmark/som_research_closure_20260911/` evidence.
- The SOM sections of `docs/TAKEOVER_CHECKPOINT.md`.
- A short next-programme GPU checkpoint, limited to existing evidence and one
  smallest next question.

No RTL, constraints, model, generated file, or hardware-evidence claim may be
changed by this tranche.

## 3. Commands

Execute exactly:

```bash
sha256sum \
  build/spu4_ina226_benchmark/bench25_global/probe.fs \
  build/spu4_ina226_benchmark/bench25_completion_arm/probe.fs

tools/run_detached_job.sh \
  --output build/spu4_ina226_benchmark/som_research_closure_20260911/repo_verify_01 \
  --timeout 3600 \
  --notify-desktop \
  -- bash tools/verify_repo.sh
```

Do not execute an FPGA synthesis command. The owner's closure scope explicitly
prohibits a new synthesis campaign and supersedes that general completion gate
for this evidence-only tranche.

## 4. Required terminal record

Record all of the following without causal embellishment:

1. Artifact A SHA-256
   `6b7022f236813695931464e2be946724a0d1775c1633f30c5540d861f3f8e8f6`
   remains the known-good reference and returns node 2 / `03C58E94` for the
   frozen scaled query.
2. Artifact B SHA-256
   `7a57be49d6164d838cd9ba49b9e13a1feb64f250312378a425bf237622dc448b`
   remains the divergent artifact and returned node 0 / `42FF6EEB` for that
   same query with verified J4 identity.
3. The earlier raw-vector result node 3 / `04433EA4` exactly matched the oracle
   for the bytes actually transmitted. That fixture mismatch is resolved and
   is not evidence explaining the A/B divergence.
4. The broad-observer validity attempt and four-run formal campaign did not
   establish non-perturbation, equivalence, non-equivalence, or mechanism.
5. Static analysis selected raw `som_best_node[1]` as a useful D3/D4 boundary,
   but did not localize cause.
6. D7 is the Dock's active-high DONE path; the observer drove
   `D7 = ~som_best_node[1]`. The earlier active-low three-LED interpretation
   was incorrect.
7. The D7 electrical tranche was partially executed but invalid: its only
   query did not reproduce B, the post-query electrical observation was not
   taken after the mandatory stop, and final J4 readback mismatched the initial
   capture. It produced no P1/P2 localization.
8. Application advantage was not demonstrated and comparative offload work is
   incomplete.

## 5. Final classification

If the artifact hashes remain exact and the repository gate reaches one
durable `COMPLETE` marker, classify:

> **SOM research tranche: CLOSED. Application advantage not demonstrated.
> Hardware offload comparison incomplete because artifact B has an unresolved
> same-input parity divergence. Artifact A retains exact oracle agreement on
> the frozen reference case. Further Tang-specific diagnosis is not warranted
> at current priority.**

If either artifact hash differs, or the repository gate terminates as `FAILED`
or `TIMEOUT`, preserve that outcome and close as **E — CLOSURE GATE
INCOMPLETE**. Do not repair, relaunch, or extend the timeout.

## 6. Stop conditions

Stop immediately after the final classification and checkpoint are written.
Do not launch synthesis, formal work, hardware work, another observer, repair,
RP benchmarking, or a second verification attempt. Any future SOM work
requires a new owner-authorized contract.
