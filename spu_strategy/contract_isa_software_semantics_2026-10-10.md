# Scoped ISA software semantics repair

```bash
python3 -B software/tests/test_assembly_operands.py
python3 -B software/tests/test_isa_software_semantics.py
python3 -B software/tests/test_isa_conformance.py
python3 -B software/tests/test_isa_fold_conformance.py
python3 -B software/tests/test_canonical_control.py
python3 -B software/spu_vm_test.py
```

Date: 2026-10-10. Status: COMPLETE for the qualified frozen software snapshot; semantics retained.
Spec author, implementer and auditor: Codex. Preserve incoming dirty changes.
Reuse operand validation; do not modify its sources or duplicate its 209 checks.
Before hashes and snapshots: `build/isa_software_semantics/preparation_01/`.

## Frozen policies

1. Python retains unbounded integer coefficients. C++ retains signed32
   coefficients and Pell counters. C++ arithmetic computes add/sub/multiply,
   ordering and scalar norm in signed128 intermediates. Check every produced
   coefficient before narrowing. No saturation, wrapping or undefined signed
   overflow. C++ helper intermediate coefficient overflow is an OVERFLOW fault
   even when a later expression could cancel it; Python can execute that wider
   domain. Report this capability boundary separately from mismatches.
2. C++ faults preserve scalar/QR banks, Pell metadata, PC, retirement count,
   stack and SNAP counter; set halted and fault_kind, then throw to the caller.
   Compute all multi-destination results before commit. Successful HALT retires
   once and advances PC. Unsupported instructions/selectors do not retire.
   Directly indexed scalar raw operands outside 0..25 reject before access. Legacy raw QR wrapping
   and ordinary reserved bytes are unchanged; source validation remains strict.
3. ROT is destination-in-place, one step. Tracked Pell state uses the eight
   mantissas plus total step, not an unbounded coefficient pair. Python polarity
   and QR tags are extension metadata unsupported by C++. QROT applies one rotor
   per component then exact ordered-minimum normalization. ROT/QROT second source
   fields remain historical ignored fields, not newly interpreted operands.
4. ROTC uses integer coefficient representation and nearest division with ties
   away from zero in both VMs. C++ supports angles0..5; Python0..35. C++ uses
   signed128 circulant accumulators and checks after division. No C++ catalog
   expansion. Source range0..63 is encoding range, not execution support.
   RTL TDM truncation and tagged representation remain distinct, with rounding
   mismatch explicitly recorded; do not alter RTL to achieve VM agreement.
5. Software fault_kind is host diagnostic state, not a hardware FLAGS encoding.
   UNSUPPORTED, OVERFLOW and INVALID_REGISTER are distinct. Scalar SNAP is
   nonhalting: increment snap_failures once per failing scalar check; preserve
   registers and retire. Python additionally has SDF checks and periodic
   gasket/dispatch behavior unsupported by C++; tests must name these exclusions.
6. Cold software reset means fresh SPUCore construction. It clears registers,
   metadata, stack, PC, program, counters and software fault. load is a warm
   program reload: replace program, reset PC/steps/halted/fault, preserve scalar
   and QR banks, metadata, stack and snap_failures. Python extension reload
   behavior remains existing behavior. RTL reset/hydration is outside this scope.

## Scope and edge review

Modify C++ arithmetic/dispatch and Python fault preflight only. Add one small
checked-math header, test harness, independent integer oracle and focused test.
Do not change REGEN, Surd, WF, transport, RTL, opcodes, ordinary folding rules,
polynomial allocation or flash addressing. JINV polarity semantics and MIN4
domain remain distinct capabilities outside the shared tested arithmetic slice.
Tests seed signed32 extrema directly: immediate fields cannot express them.
Include cancellation with products exceeding signed64, negative thirds,
source/destination aliases, late-component overflow, fault followed by reload,
HALT, scalar SNAP and fresh construction. Test diagnostics with proof enabled
where repaired wide formatting is involved; no broad proof equivalence claim.

## Qualification

Run focused checks before the full tranche job. Freeze one qualification
attempt with 7,200-second wall-clock/cumulative budget, no automatic retry.
Use an isolated snapshot bound to after hashes so concurrent REGEN/Surd edits
cannot change this job's sources. Execute focused tests, scoped spu13_core
regression, full repository verification, ROTC/IROTC trace tests, rational
robotics/SOM, Lucas and Padé oracles, documentation audit and the mandatory
25MHz Artix100T Padé build. Padé synthesis is a repository gate, not qualification
of the changed software on hardware. Record a single terminal marker before
interpreting results. After LAUNCHED end the turn per AGENTS.md §4.2.

Stop on failing assertions or source drift; flag a minimal correction. Do not
relax frozen semantics or extend a consumed qualification budget silently.

## Recorded qualification

`build/isa_software_semantics/qualification_01` has exactly one COMPLETE marker,
exit 0 and duration 2,168/7,200 seconds. All 18 gates passed, including the
separate requested-25-MHz Artix-7 Padé build and both source-identity checks.
`qualification_review.json` binds gate results and tested source hashes.
Repository/scoped totals are 243/0 and 75/0. This closeout is confined to the
frozen software semantics snapshot and does not qualify concurrent changes or
the Surd/REGEN image.
