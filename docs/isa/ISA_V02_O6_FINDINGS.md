# ISA-V02-O6 — Source Inventory and Consistency Findings

**Date:** 2026-10-26 · **Status:** findings for review; no opcode, RTL, VM or ISA document changed.
**Inventory:** [`isa_v02_o6_inventory.json`](isa_v02_o6_inventory.json) (frozen, source-derived)
**Regenerate:** `python3 tools/isa_inventory.py --out docs/isa/isa_v02_o6_inventory.json`
**Test:** `python3 software/tests/test_isa_inventory.py` (fails if the inventory or the known CONFLICT set changes)

Sources read: `knowledge/isa_reference.md`, `software/spu_vm.py`, `software/tools/spu13_asm.py` (+ `surd_cpu_encoding.py`), `software/vm/spu_vm.cpp`, `spu13_core.v` and five opcode-bearing sidecars, `spu_isa_defines.vh`, `ISA_IMPLEMENTATION_MATRIX.md`. Duplicates are preserved (AST/line scan, not dict load). ISA-B/WF is a separate namespace; 27 of its values numerically overlap ISA-A and no conflict is asserted.

## Findings by class (live counts: 3 / 7 / 19 / 0 / 20)

### Confirmed encoding conflict (3 records, 1 underlying issue)
`POLY_STEP`: spec `0x60` (`isa_reference.md:178`); Python VM defines both `0x60` and `0xE0` in one dict literal, so `0xE0` silently wins (`spu_vm.py`); `spu13_core.v:1903` decodes `0xE0`. Spec disagrees with the VM and the core RTL.
**Proposed resolution (owner decision):** declare `0xE0` canonical (VM and RTL agree) and amend the spec row, or move both to `0x60`. Either way remove the duplicate dict key. Not done here.

### Missing in a claimed profile (7)
The assembler header says its table "must stay in sync with spu_vm.py". The assembler lacks `SOM 0x2A`, `SOM_TRAIN 0x2B`, `PHADD 0x30`, `PHCFG 0x31`, `RATIO_CMP 0x61` and both `POLY_STEP` values. The matrix already records the SOM assembler gap. **Resolution:** either add them or weaken the header claim to a stated subset.
No matrix row (105 mnemonic×column cells checked) contradicts the sources.

### Documented profile extension (19; not defects)
In the spec, not in some software implementation, no contract claiming otherwise: C++ VM lacks `REGEN`, `MIN4`, `SOM`, `SOM_TRAIN`, `PHADD`, `PHCFG`, `POLY_STEP`, `RATIO_CMP`, `IROTC`, `LOAD2X`, `SCALE2`; neither Python VM nor C++ VM has the Surd extension `0x70–0x77` (the assembler does). Correction to my earlier note: the assembler *does* include 0x70–0x77 via `**SURD_OPCODES`.

### Undocumented implementation (0 strictly)
Every VM/assembler/C++ opcode is in the spec. The RTL-only cases below are classified as unresolved ownership.

### Unresolved profile ownership (20)
- `spu13_core.v`: `0x48`, `0x4C`, `0x4D` (JSCR/NSA decode); `SPU13_ARCHITECTURE.md:208` calls them "feature-specific", no encoding or semantics are documented.
- Sidecars with no spec entry: Lucas `0xD0–0xD5`, Neuro `0xE1–0xE3`, SU3 `0xE8–0xEB`.
- **Candidate overlaps** (same value, different name, optional modules): `0x2A` = `SOM` (spec/VM/core) vs `RPLU2_START` (two RPLU2 sidecars); `0xE0` = `POLY_STEP` (VM/core) vs `NEURO_CFG` (Neuro sidecar). Whether these modules can coexist in one build is not established here.
- ISA-B/WF namespace note.

## Architectural state (see `state` in the JSON)
- Scalar `R0–R25` (both VMs), `QR0–QR12` (spec), Surd `S0–S7` (spec, `ENABLE_SURD_CPU`).
- **Spec FLAGS (6 bits) read via `SNAP` — UNRESOLVED in both VMs:** their `SNAP` is a Davis-gate scan with no FLAGS word.
- Faults: VMs `UNSUPPORTED`, `INVALID_REGISTER`, `DEGENERATE_METRIC`, `OVERFLOW`; Python exceptions for ROTC/IROTC; spec `SSTAT` codes `OK=0..BAD_ENCODING=4`.
- Per-opcode fault precedence and refusal post-state, RTL register organisation, and the fetch/PC/stack transition table: **UNRESOLVED**.

## Recorded qualification blockers (no work done on them)
1. **QROT operand class.** Spec (`isa_reference.md:112`): `QROT Rd, Rs, n`, `R[d]=R[s]×(2+√3)ⁿ` (scalar form). Both VMs (`spu_vm.py:1622`, `spu_vm.cpp:822`) and the assembler treat it as `QROT QRn`, one in-place rotor step on a Quadray register with no exponent; the Python VM also marks the register `PHI_UNTAGGED`. Spec and implementation describe different operations.
2. **A31 inverse has no opcode.** `FLAGS.V` is documented, but no ISA-A table encodes an A31 inverse. The inverter (`spu13_fp4_inverter.v`) raises `flags_v` and `done` on zero norm and does not write `inv0..3`, so the outputs hold stale values; whether the RPLU/Padé consumer gates them is not established.
3. **A31 zero-divisor coverage (HOLD).** The inverter tests one norm, `w0²−3·w1²`. A31 ≅ F_p² × F_p², so whether one check catches every non-invertible element needs a mathematical audit. Not opened, per O6 scope.
