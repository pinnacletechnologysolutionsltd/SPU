# CPU Surd verification update

```bash
python3 software/tests/test_spu13_core_surd.py --verification-only --output-dir build/spu_surd_register/cpu_verification_update_20261007/verification_02
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- hardware/tests/spu13/spu13_core_surd_tb.v hardware/tests/spu13/spu13_core_surd_tasks.vh hardware/tests/spu13/spu13_core_surd_guards.vh software/experiments/surd_cpu_verification_cases.py software/tests/test_spu13_core_surd.py spu_strategy/contract_surd_cpu_verification_update_2026-10-07.md
```

Date: 2026-10-07. Scope authorized by the owner's CPU verification follow-up:
test fixtures and directed driver only. Spec author, implementer, and auditor:
Codex. Frozen arithmetic interface, production RTL, ISA, and accepted historical
evidence remain unchanged. This update does not authorize synthesis, routing,
physical hardware, archive pruning, or a repeat of a frozen campaign.

## Scoped files and checks

Modify the existing CPU testbench/tasks and its Python test entry point.
Add `spu13_core_surd_guards.vh` and `surd_cpu_verification_cases.py`.

1. Snapshot every 192-bit bank entry and all eight initialized bits before
   issue. On retirement compare the entire bank against the snapshot, allowing
   only the expected successful destination write and initialized-bit update.
   Failed retirements must leave all tuples and validity bits unchanged.
2. Initialize seven distinct poison destinations and leave S7 uninitialized in
   new cases. Exercise destination=right and destination=both sources for ADD,
   SUB, and MUL. Cover raw-fit commits, rescue commits and unrescued overflow
   where mathematically possible. All-sources-equal SUB always produces fitting
   raw zero with the original positive denominator; no rescue/overflow case is
   possible under that interface. Require the observed rescue-request count to
   match the declared fit/rescue path, and read back all seven initialized tuples.
3. At a real successful normalizer terminal handshake, inject either `n_fault=1`
   or `n_valid=0`, in alignment, scheduled SNORM, and multiply rescue phases.
   Use simulation-only force/release. Require ENGINE_FAULT status 3, exactly
   one retirement, zero writes, and full bank/validity preservation. Release
   at the next falling edge, after the arithmetic unit consumes the completion.
4. Check four idle cycles after failure/alias retirement for stale completion,
   writes or lack of readiness. Read status and preserved tuples. Reissue the
   same arithmetic successfully after each injection without reset; check exact
   result and status through the unchanged stream oracle.
5. Require 17 alias cases and six engine-failure injections in the test runner's
   coverage record. Record failed-retirement snapshot checks separately. The
   default directed and retained-kernel execution now includes these cases;
   `--verification-only` excludes the historical random-vector and kernel suites.

## Evidence and stop conditions

Record `compile.log`, `runtime.log`, `program.txt`, `results.json`, source list,
and a new source snapshot manifest under the new evidence directory. Output
directories refuse overwrite. Halt on a failed assertion or coverage mismatch;
do not change production arithmetic to obtain a pass.

`directed_01` is a retained failed compile: the new guard incorrectly referred
to another task's local phase variable. Corrected the guard to inspect the
existing hierarchical phase wire. `directed_02` was interrupted when the full
directed run exceeded the intended foreground scope; it supplies no PASS.
`verification_01` passed the new subset (39 failed retirements, 17 aliases,
six injections). `verification_02` includes the corrected rescued right-alias
SUB case and the final report's explicit verification-only scope.

The scoped `TB_FILTER=spu13_core_surd_tb python3 run_all_tests.py` invocation
passed its one RTL smoke test, then continued into unrelated C++/software tests.
It was interrupted, exit 130; do not claim a completed scoped regression from
that invocation. `TB_FILTER` is not a whole-run scope limiter in this runner.

These checks supply directed RTL simulation evidence only. They do not inject
an actual quotient remainder fault inside the normalizer or prove every fault
source; they verify CPU handling of terminal engine failure signals. Full bank
preservation is observed at retirement and during the guard interval, not a
formal proof for all inputs or arbitrary durations. Full regression, retained
kernel replay, synthesis and routing were not rerun for this test-only update.
Any required broader deterministic gate must use a new frozen, owner-authorized
budget and the detached runner; historical campaign slots are not reusable.

T1I remains offline preparation. T1H H1 stays HOLD and T1G rollback remains
preserved. The integer baseline specification and article remain unreviewed
by the owner; they are not approval authority for this test update.
