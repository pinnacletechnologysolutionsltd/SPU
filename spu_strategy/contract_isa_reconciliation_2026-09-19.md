# Engineering Contract: ISA Profile Reconciliation
**Date:** 2026-09-19
**Contract ID:** `isa_reconciliation_2026-09-19`
**Status:** ACTIVE — provenance only; no opcode or RTL changes authorized

## 1. Objective and scope

Establish provenance and profile ownership for the incompatible instruction
maps currently present in the repository before publishing a repository map,
claiming VM parity, or generating a single-source ISA schema.

This tranche does not redesign the ISA, rename files, move experiments, delete
source, change RTL, or change assembler/VM behavior.

### Neutral profiles

| Profile | Current surfaces | Initial description |
|---|---|---|
| ISA-A | `knowledge/isa_reference.md`, `software/spu_vm.py`, `software/tools/spu13_asm.py`, `software/vm/spu_vm.cpp` | 64-bit SPU-13 reference/Python family, including ROTC and IROTC |
| ISA-B | `hardware/rtl/arch/spu_isa_defines.vh`, related decoder/core users | alternate 5-bit-register / Wheeler–Feynman-style hardware profile |
| ISA-C | any remaining opcode table not identical to A or B | profile to identify or split explicitly |

These labels are provisional. No profile is called canonical until the
provenance gates below close.

## 2. Provenance questions

Answer each question with a path, commit, test, bitstream/evidence section, or
an explicit `UNRESOLVED` record:

1. Which opcode table and instruction packing produced each bitstream with
   hardware evidence?
2. Which assembler/compiler generated the programs used by those tests?
3. Which VM/oracle produced the expected values or trace?
4. Which opcode format is consumed by current Wukong GPU, Tang, SPI, and
   southbridge integrations?
5. Which documents claim to define SPU-13, SPU-4, a legacy FPGA profile, or
   the experimental Wheeler–Feynman adapter?
6. Do the IROTC silicon entries use ISA-A transport/opcode words, or a
   separate SPI command protocol that must not be conflated with the VM ISA?
7. Does `software/vm/spu_vm.cpp` implement ISA-A, or only a historical subset?

## 3. Evidence anchors already observed

The following are leads, not final ownership decisions:

- `knowledge/isa_reference.md` explicitly calls itself the current canonical
  encoding and documents IROTC `0xD6`, ROTC `0x1C`, and the 64-bit field family.
- `software/tools/spu13_asm.py` and `software/spu_vm.py` share the ISA-A-style
  table and implement IROTC-related software behavior.
- `software/vm/spu_vm.cpp` uses the ISA-A values for ROTC and related Quadray
  operations but is visibly partial and must not be promoted by declaration.
- `hardware/rtl/arch/spu_isa_defines.vh` defines a different opcode/field
  family, including the experimental-looking `OPCODES_WF` table in the Python
  assembler.
- `docs/hardware_evidence.md` contains explicit silicon evidence for ROTC and
  IROTC. The exact command/source/opcode relationship must be traced from each
  cited subsection; IROTC silicon evidence alone does not prove that the VM
  instruction encoding was used.
- Git history identifies the IROTC VM implementation (`b052c3e`), the
  next-generation ISA/decoder work (`a460844`, `41027af`), and the older
  C++ parity work (`fc64f47`, `2822bb5`). These commits are evidence leads only.

## 4. Required deliverables

Create the following only after the provenance pass:

1. `docs/isa/ISA_PROFILE_PROVENANCE.md`
   - neutral A/B/C table;
   - evidence links and unresolved claims;
   - explicit profile ownership decision;
   - no unsupported “canonical” wording.
2. `docs/isa/ISA_IMPLEMENTATION_MATRIX.md`
   - opcode/feature rows;
   - Python, C++, RTL, assembler, and test coverage;
   - statuses `implemented`, `partial`, `profile-specific`, `evidence-only`,
     `absent`, or `unresolved`.
3. A follow-on contract for convergence or profile separation.

Do not create a generated ISA schema in this tranche. It is authorized only
after the profile decision and encoding tests are ratified.

## 5. Exact audit commands

Run from repository root and preserve stdout under the session workspace:

```bash
git log --all --format='%h %ad %s' --date=short \
  -- knowledge/isa_reference.md \
     hardware/rtl/arch/spu_isa_defines.vh \
     software/spu_vm.py \
     software/vm/spu_vm.cpp \
     software/tools/spu13_asm.py

git log --all --format='%H %ad %s' --date=iso-strict -- docs/hardware_evidence.md

git grep -n -E \
  'spu13_asm|spu_vm\.py|spu_vm\.cpp|spu_isa_defines|IROTC|ROTC' \
  -- hardware docs knowledge software spu_strategy

git log --all -S'IROTC' --format='%H %ad %s' --date=iso-strict -- \
  hardware software docs knowledge

git log --all -S'OPCODES_WF' --format='%H %ad %s' --date=iso-strict -- \
  software hardware docs knowledge
```

Inspect every cited hardware-evidence subsection and record:

```text
source commit:
top/module:
build command:
program/assembler:
wire or instruction format:
expected oracle:
bitstream hash:
result scope:
```

## 6. Verification and stop conditions

- [ ] No profile is promoted based solely on filename age or documentation
      wording.
- [ ] Silicon evidence is separated from RTL, trace, and software evidence.
- [ ] SPI transport command encodings are not called VM opcode encodings
      without direct proof.
- [ ] Any duplicate opcode mnemonic or conflicting numeric value is recorded.
- [ ] The existing repository gate result is interpreted before closing this
      contract.
- [ ] No Stage B T1d synthesis/P&R command is run under this contract.

HALT immediately if provenance cannot distinguish ISA-A from ISA-B for a
silicon result, if a cited artifact is missing, or if reconciling profiles
would require changing hardware behavior without a new owner-authorized
contract.

## 7. Roles

- **Spec Author:** John Curley / Copilot
- **Halt-and-Flag Implementer:** Copilot
- **Integration Auditor:** `tools/verify_repo.sh` plus reviewed evidence ledger
