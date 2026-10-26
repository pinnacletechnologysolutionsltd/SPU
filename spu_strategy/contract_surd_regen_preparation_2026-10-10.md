# Surd/REGEN preparation and launch-gate repair

```bash
python3 -B build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/test_source_gate.py
python3 -B build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/source_gate.py
tools/run_detached_job.sh --output build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/preparation_checks_01 --timeout 900 --unit spu-surd-regen-preparation11-01 --notify-desktop -- bash build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/run_preparation.sh /home/user/Projects/hardware/SPU/build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/preparation_checks_01
```

Date: 2026-10-10. Status: ACTIVE; preparation authorized, synthesis separately
held. Spec author, implementer and auditor: Codex. Keep production files and
all prior evidence unchanged. Use a new preparation package; no mutation of
preparation_10, the pending reference job or the ISA qualification snapshot.

## Scope and source decisions

1. Preserve current spu_vm.py byte-for-byte: it equals the ISA semantics
   repair's after hash. Freeze the ISA snapshot's software and dependencies
   alongside the retained preparation_10 hardware. Record this reconciliation.
2. Preserve the retained five-lane W64 Surd products, normalization, bank,
   status/retirement and frozen core. Newer live core edits are not silently
   merged into this hardware candidate. Do not change production REGEN RTL.
3. Retain only the four selected signed42x42 ->84 REGEN products in the DSP
   policy; seven other products retain their existing soft mapping. Reuse the
   exact retained mapped candidate and test artifacts with hashes. Do not infer
   fresh mapping equivalence from frontend success alone.
4. Emit validated whitespace-free Yosys -Ipath options unquoted and source
   filenames individually quoted. Share the same frontend generator between
   preparation and the proposed integrated build. Validate enabled/disabled
   hierarchy without synth_xilinx or nextpnr during preparation.
5. Verify snapshot/tool/library/dependency hashes BEFORE invoking the detached
   launch callback, and again inside the worker. Reject corruption and missing
   input. Exercise positive callback control and source/dependency corruption
   controls; failed checks must not reach the callback.
6. Give the new integrated launcher a separate manifest-bound approval gate.
   Require durable preparation COMPLETE, explicit acceptance, completed pending
   reference attempt, and a fresh output directory. Do not copy authorization
   from the older package. Preserve all previously consumed attempts.

## Authorized validation

Run one preparation job, 900 seconds maximum, no automatic retry. It performs
two frontend/hierarchy checks, 708 retained full84 mapped-product checks,
256 mapped sequential checks on each of two initialization seeds, corrupted
expectation controls, the legacy reference check and the reused ISA software
operand/semantics checks. These are directed compiled known-input checks;
four-state or exhaustive equivalence is not established. Freeze external tool
and library identities; verify them before and after execution.

The prior mapped qualification has exactly one COMPLETE marker and exit0.
Prior integrated attempt04/02 has no terminal marker at preparation inspection;
its result is unavailable. Do not infer completion or relaunch it. The ISA
qualification proceeds independently on its already frozen worktree.

## Separate integrated mapping proposal

After interpreting a single durable preparation COMPLETE and reviewing the
package, obtain separate synthesis approval bound to manifest.json. Proposed
new budget: exactly one attempt, 7,200 seconds per attempt and cumulative,
XC7A100T, seed1, 25MHz /40ns. No retry, deadline extension or seed/target sweep.

The prepared launcher is:

```bash
python3 -B build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/launch_integrated.py
```

It must reject while mapping_approval.json is absent. Approval is not created
by this preparation contract. Each accepted launch consumes the sole slot.
Require disabled/enabled mapping, four-product DSP audits, five-lane Surd80-DSP
audit, complete clock coverage and strict legal-route/SDF/timing acceptance.
234/240 DSPs remains projected for this proposed candidate; integrated fit and
timing remain unresolved. Do not flash hardware or make silicon claims.

Production RTL, arithmetic kernels and build flows are not modified. The
frozen-package checks above qualify preparation; they do not replace full
arithmetic/RTL qualification or authorize additional mandatory build campaigns.
End the turn after LAUNCHED and interpret the result in a later invocation,
as required by AGENTS.md §4.2.
