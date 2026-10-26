# Surd/REGEN preparation and launch-gate review

Date: 2026-10-10. Status: preparation PASS; isolated package frozen; integrated mapping/routing separately authorized.
Authority: [preparation contract](../../spu_strategy/contract_surd_regen_preparation_2026-10-10.md).

The owner authorized preparation and launch-gate repairs with synthesis as a
separate approval. No new integrated mapping/routing job has been launched.
The proposed next budget is one attempt, 7,200 seconds cumulative, at 25 MHz;
The owner subsequently authorized this prepared campaign; the bound approval
record below governs execution.

| Item | Result / scope |
|---|---|
| VM reconciliation | Current spu_vm.py equals the ISA repair after hash. Preserve it without a merge or overwrite. The ISA job retains its own isolated worktree. |
| Hardware snapshot | Copy retained preparation_10 hardware byte-for-byte, including five W64 Surd multiplier lanes and retirement/status logic. Newer live core changes are excluded from this hardware candidate. |
| REGEN policy | Retain exactly bk_qr0_meas_a/b and bk_qr1_meas_a/b as the selected DSP products. Seven other products retain the soft policy. No production RTL edits. |
| Source/dependency isolation | 456 package files and 520 external tool/library identities frozen with SHA-256. The new guard checks this package rather than coupling the build to unrelated live checkout edits. |
| Include handling | Qualified frontend generator emits validated unquoted -Ipath options and individually quoted source filenames; preparation and future build share it. Both frontend/hierarchy checks passed. |
| Failed-source launch control | Positive callback control passes; corrupted source and dependency controls reject before the callback. The same checked_call guards the actual detached launcher. |
| Separate approval | Real integrated launcher rejects when mapping_approval.json is absent. It also requires durable preparation acceptance bound to this manifest, terminal reference evidence and an unused output directory. |
| Mapped checks | Reuse exact retained mapped artifacts, passed 708 full-width 84-bit product checks, 256 sequential checks under each of two initialization seeds and corrupted-expectation controls. No fresh mapping is claimed from these checks. |
| Pending reference | integrated_build_04_attempt_02 has no terminal marker at inspection; result unavailable. Preserve it without cancellation or relaunch. |
| Capacity/timing | 234/240 DSPs remains projected for the proposed candidate. Integrated fit and timing remain unresolved. No physical or exhaustive equivalence claim. |

Review package: [preparation_11 manifest](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/manifest.json),
[VM reconciliation](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/vm_reconciliation.json),
[source guard](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/source_gate.py),
[negative controls](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/test_source_gate.py),
and [integrated launcher](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/scripts/launch_integrated.py).

Preparation completed once under the detached runner: exactly one COMPLETE
marker, exit 0, 67 seconds against a 900-second limit. Evidence:
[runner result](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/preparation_checks_01/result.json)
and [acceptance report](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/preparation_checks_01/preparation_results.json).
The acceptance report binds manifest SHA-256
`4f6f533936e40d8c29315c37ab86293c7ea52f17dc0f0bd48c8c4a6e60c8818b`;
the manifest hash was verified again when recording this result.
After a consistent preparation PASS, review the concrete manifest and then
record separate synthesis approval before invoking the integrated launcher.
Do not renew the old campaign or infer approval from an elapsed deadline.

## Integrated attempt approval

The owner authorized the prepared integrated mapping/routing campaign.
[Bound approval](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/mapping_approval.json)
freezes one attempt, 7,200 seconds wall-clock and cumulative, with 25 MHz
acceptance. The reference attempt now has exactly one TIMEOUT marker, exit
124; it leaves fit unresolved and does not prove that the candidate cannot fit.
No reference relaunch or board operation is authorized.

The prepared worker requires legal routing, exactly one timed sys_clk domain,
PASS at 25 MHz, no required unconstrained domain, nonempty routed artifacts
and explicit SDF coverage. No timing-allow-fail override is used. Five Surd
arithmetic lanes and retirement semantics are frozen; REGEN changes remain
limited to the four selected products. 234/240 DSPs remains projected until
the new mapping is measured; integrated fit/timing remain unresolved.

## Integrated terminal review — 2026-10-11

The [prepared attempt](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/result.json)
ended with exactly one TIMEOUT marker, exit 124, at the 7,200-second limit.
This supersedes the pre-launch/pending statuses above without altering the
frozen package or its historical evidence. No restart is authorized.
[Synthesis comparison](../../build/spu_surd_register/main_cpu_integration_20261007/selective_regen/preparation_11/integrated_mapping_01/synthesis_resource_comparison.json)
and packing confirm 234 DSP48E1s (154 disabled plus 80 incremental Surd),
including the 24 selected REGEN DSPs. Packed LUT-slot occupancy is 81%.
The log stops during main analytical placement. Legal routing, complete required
timing coverage and PASS at 25 MHz are unavailable; fit remains unresolved.
Synthesis/packing confirms resource usage but does not establish accepted fit.
Speedup, energy and board performance remain unmeasured.
