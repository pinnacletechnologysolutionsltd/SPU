# AOR-1 Phase A software execution packet — preparation draft

**Status:** PROPOSED; ratification and implementation/execution authorization pending.
**Date:** 2026-10-12. No job has launched from this packet.

Review commands:

```bash
sed -n '1,240p' spu_strategy/contract_spu13_aor1_phase_a_ratification_amendment_2026-10-12.md
sed -n '1,240p' spu_strategy/aor1_phase_a_literal_fixtures_2026-10-12.md
sed -n '1,200p' spu_strategy/contract_spu13_aor1_phase_a_execution_draft_2026-10-12.md
```

## Sources and implementation boundary

Bind the [amendment](contract_spu13_aor1_phase_a_ratification_amendment_2026-10-12.md),
[parent draft](contract_spu13_aor1_phase_a_2026-10-11.md),
[literal fixtures](aor1_phase_a_literal_fixtures_2026-10-12.md) and review identity
before ratification. The older scalar-accounting proposal is preserved, excluded
from the selected execution semantics. Ratification is a separate owner decision.

Proposed new files only, each split into single-purpose modules as necessary:

- software/research/aor1/oracle.py: independent arbitrary-precision recurrence oracle.
- software/research/aor1/bounded.py: checked tuple operations and binary expansion.
- software/research/aor1/baseline.py: Surd mantissa plus exponent bookkeeping.
- software/research/aor1/accounting.py: bounded-model charge and resource ledger.
- software/tests/test_aor1_phase_a.py: independent literal/schedule/negative checks.
- tools/bench_aor1_phase_a.py: fixed cohorts and host measurements.
- build/aor1/phase_a_execution_<unique-id>/: frozen runner, manifests and evidence.

These paths are proposed, not existing implementations or runnable commands.
No current VM, ISA, arithmetic RTL, CPU/GPU interfaces or registers may change.
The oracle and checker must not reuse bounded arithmetic as their sole reference.
The baseline must retain equivalent checks and destination preservation. Report
host timings, memory and storage separately from abstract operation counts.

## Proposed campaigns — no execution authority

| Campaign | Attempts | Hard limit | Included stages |
|---|---:|---:|---|
| Software qualification and comparison | 1 | 1,800 seconds | Compile/import; literal and independent checks; negative controls; fixed cohorts and paired host measurement |
| Required repository verification | 1 | 5,400 seconds | Repository, scoped triage, ROTC/IROTC, four math checks and fresh Artix-7 Padé build |

Proposed cumulative maximum is 7,200 seconds. No retries, routing, board operation
or adoption into architectural state. The mandatory Padé gate checks repository
regression only; it is not AOR synthesis or an extension of Artix-7 routing work.
Dependent jobs are sequential, and the second requires the first's durable PASS.

Required regression commands, to be frozen with executable source identities:

```bash
bash tools/verify_repo.sh
TB_FILTER=aor1 python3 run_all_tests.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

Do not assume scoped RTL triage discovers software tests: invoke the proposed
software test script explicitly in the focused campaign. The final script and
benchmark CLI commands cannot be frozen until implementation is separately
approved and reviewed; placeholders do not authorize a launch.

Before launch, freeze cohort inputs, literal expected values, full command argv,
subordinate stage list, source/tool hashes and new evidence directories. Use the
repository detached runner and exactly one consistent terminal marker per job.
Record consumed attempts even for failed preparation after launch. End the agent
turn after LAUNCHED and interpret only in a later session.

Include one million compact forward steps, inverse composition, mixed mantissas,
conjugation/norm, bounded expansion and unsupported different-exponent addition.
Do not materialize U^1,000,000 merely to validate a compact counter. Oracle
resource refusal is evidence of its limits, not proof the bounded answer is wrong.
Pair only identical operations/domains. No CPU instruction-count, hardware
resource, speedup or energy claims arise from these software cohorts.

## Ratification record template

A completed record must identify the owner instruction and bind all contract,
fixture, source-scope and execution-manifest hashes. Current review_identity.json
is a PROPOSED preparation record, not that ratification. Implementation authorization
and campaign authorization must be recorded distinctly. Changes to frozen semantics
or execution bounds require a reviewed amendment before running affected work.
