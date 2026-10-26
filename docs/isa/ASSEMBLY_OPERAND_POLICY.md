# Assembly operand policy — frozen before implementation

Scope: canonical instruction assembly in standalone Python, embedded Python VM and C++ VM. Preserve each assembler's supported mnemonics and its valid literal word encodings. Surd VM execution, WF profile, RTL raw binary, arithmetic, transport and FPGA changes are excluded.

Validate original source before masking, packing or folding. Scalar indices are R0–R25; Quadray indices QR0–QR12. Require complete decimal index syntax (no negatives, trailing garbage or type substitution). Standalone bracket register spelling remains supported. QLOAD scalar base must be R0–R22 for four consecutive scalars.

Canonical argument kinds/counts are explicit. QSUB accepts exactly two or three QR operands; two operands mean QRd=QRd-QRs. ROT and SCALE2 preserve named self-source forms. QROT preserves its destination-only built-in rotor form. LD preserves one-register and one/two-immediate zero defaults. Standalone QLDI/LOAD2X partial component zero defaults remain supported; Python VM's named two-packed-half forms remain supported. C++ QLDI remains four-component only. ROTC preserves destination/source with default zero only where already supported.

ROTC source selector is 0–63: 0–35 implemented catalog, 36–63 faithfully encoded runtime fault cases. Reject64, negatives and high field bits; no implicit angle masking. IROTC accepts0–59 or64–123 (catalog index0–59 and conjugate bit); reserved catalog indices rejected in source; raw-word fault tests unchanged. Jump/call numeric destinations0–65535; labels remain supported. Numeric coefficient masking is a named legacy immediate representation behavior and is preserved in this scope; malformed noninteger operands are rejected. No new interpretation of encoded bits.

Reject excess/missing arguments and wrong register/immediate types before encoder special cases; malformed input aborts whole assembly instead of silently skipping an instruction. Validate standalone IR before folding so optimization cannot erase invalid source. VM-only extension grammar beyond canonical instructions remains a separate conformance boundary; reject out-of-range register tokens globally.

Software qualification: new cross-assembler negative tests, existing literal encoding/VM conformance, fold conformance and canonical control tests, Python VM suite, scoped assembler tests. No synthesis is required by this software-only scope. Source policy and before hashes are recorded here. Full software/RTL parity is not claimed.

## Focused validation

```bash
python3 software/tests/test_assembly_operands.py
python3 software/tests/test_isa_conformance.py
python3 software/tests/test_isa_fold_conformance.py
python3 software/tests/test_canonical_control.py
python3 software/tests/test_regen_asm.py
python3 software/spu_vm_test.py
```

These gates check source rejection, named legacy forms and retained canonical words; they are software evidence, not RTL wrapping, FPGA timing or full VM parity evidence. Surd instructions remain unsupported by both VMs; standalone emission is not VM execution.
