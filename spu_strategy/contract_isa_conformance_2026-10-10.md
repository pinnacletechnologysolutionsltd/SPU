# Engineering Contract: scoped canonical ISA conformance
Date: 2026-10-10. Status: COMPLETE for the scoped repair and listed gates.
Roles: Codex drafts, implements and audits. Frozen preparation retains ACTIVE.
Evidence: build/isa_conformance/qualification_01/result.json, exactly one
COMPLETE marker, exit 0. No unresolved policy repair or silicon claim is implied.

```bash
git diff -- software/tools/spu13_asm.py software/spu_vm.py software/vm/spu_vm.cpp hardware/rtl/core/spu13/spu13_core.v
python3 software/tests/test_isa_conformance.py
python3 software/tests/test_isa_fold_conformance.py
python3 software/tests/test_canonical_control.py
TB_FILTER=spu13_core python3 run_all_tests.py
python3 software/tests/test_spu13_core_surd.py --verification-only --output-dir build/isa_conformance/qualification_01/surd
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
python3 tools/doc_audit.py --actual-pass 238
bash tools/verify_repo.sh
A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

1. Preserve the incoming dirty tree. Edit only the three software surfaces,
   active core dispatch, canonical reference, new scoped tests and audit record.
   Migrate software/programs/pell_orbit_demo.sas and its examples/02 copy using
   the initial constants already stated by those demos; verify (9,5) and (7,4).
2. Encode QREAD and MIN4 operands in the standalone assembler. Reject third
   operands on canonical in-place ADD/SUB/MUL before folding, in all assemblers.
3. Add four-component QLDI and explicit DELTA steps to the Python inline
   assembler; retain its existing packed-half QLDI form.
4. Add canonical C++ HALT. Reject unsupported source mnemonics and raw VM
   opcodes explicitly. C++ ROTC outside 0..5 stops with an unsupported diagnostic;
   no destination or PC commit occurs. Do not allocate a hardware fault encoding.
5. Invalidate both scalar outputs of HEX/SPREAD in folding, including register
   25 wrap. Stop folding ROT because an LD cannot retain Pell metadata. Update
   JINV propagation after a folded result.
6. Add one HEX read-settle state. Preserve the existing 16-bit telemetry order
   (B-D,A-D); document it as a core telemetry subset, not scalar-register parity.
7. Replace lane modulo expressions with a bounded compare/subtract function.
   Preserve the existing full-byte modulo-13 behavior and QSUB low-nibble input.
8. Keep WF, SPI/GPU protocols, arithmetic rounding/overflow, status allocation,
   reset/load semantics and core fetch/stack architecture outside repair scope.
   Record their conflicts or unsupported capabilities explicitly.
9. Compare literal expected words and independent state expectations. Cover
   assembler rejection, folded outputs, C++ HALT and live RTL alternating HEX
   sources. Retain Surd directed preservation/alias/engine-fault qualification.
10. Launch all long gates once through tools/run_detached_job.sh, with a 7200s
    external timeout, durable per-command logs and no automatic retry. End the
    turn after LAUNCHED. Record failed gates without overwriting prior evidence.

Stop on a contradictory invariant, failing focused assertion or required policy
change. Do not infer arithmetic parity, integrated timing or silicon results
from source agreement or passing software tests. No hardware flashing or commit.
