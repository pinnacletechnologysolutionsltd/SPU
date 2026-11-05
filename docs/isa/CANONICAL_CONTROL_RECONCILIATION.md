# Canonical control encoding reconciliation

Date: 2026-10-09. Scope: freeze the existing canonical boundary and identify
compatibility changes. Original October9 record was documentation-only. October10 software repairs
are implemented and pass focused checks; full qualification remains pending.
No core fetch/PC/stack implementation or FPGA integration build is included.
Authority: [canonical reference](../../knowledge/isa_reference.md).
The WF adapter remains a separate profile.

## Frozen boundary

| Operation | Canonical encoding | Semantics / allocation |
|---|---|---|
| JMP | 0x06 | Unconditional transfer, existing reference |
| CALL | 0x20 | Save return PC and transfer to P1_A address |
| RET | 0x21 | Return using the call stack |
| QREAD | 0x22 | QR copy; cannot also mean RET |
| COND | Unallocated | No valid canonical encoding; do not emit or decode 0x20 as COND |

No new opcode is allocated here. In particular, WF 0x23 means QDIV and is not
evidence for allocating canonical COND. An eventual COND extension requires
its own field, predicate, failure and implementation contract.

## Current behavior and required compatibility work

| Surface | Observed conflict | Required change before conformance |
|---|---|---|
| Python default assembler | COND 0x20 and repeated CALL 0x20/RET 0x21 definitions | Keep one canonical definition per mnemonic; reject canonical COND with a clear diagnostic |
| Python VM | Later dictionary entries override CALL/RET, leaving COND=CALL 0x20; COND dispatch precedes CALL | Remove ambiguous canonical COND handling; dispatch 0x20 to CALL and 0x21 to RET; retain QREAD 0x22 |
| C++ VM and its internal assembler | COND 0x20, CALL 0x21, RET 0x22 | Align canonical CALL/RET; distinguish old input explicitly; reconcile QREAD support rather than advertise unsupported parity |
| Lithic-L C++ constructors | L_COND 0x20,L_CALL 0x21,L_RET 0x22 | Align canonical constructors; canonical COND must not silently emit a CALL word |
| Compiler / existing sources | Existing COND statements may assume the old predicate | Inventory affected programs; explicit diagnostic or reviewed legacy mode; do not invent branchless lowering without a supported predicate/selection operation |
| Main core | No JMP/CALL/RET handler established in inspected core | Document capability gap; implementing fetch/PC/stack is separate architectural work |

October10 repairs align canonical Python/C++ CALL/RET, add the C++ basic
QREAD copy, reject COND source explicitly and delete the Lithic-L COND
constructor. C++ does not gain IROTC metadata/parity. Historical sources using
COND need explicit migration; no automatic legacy-binary translation exists.
The original sources/tests are preserved in the repair evidence package.
The actual old COND handlers use `quadrance()>0`, despite the assembler header
saying `==0`. A legacy profile must preserve actual semantics intentionally,
not infer them from that header.

Raw binaries are ambiguous:0x20/0x21/0x22 have incompatible meanings. Do not
translate by opcode alone or auto-detect a profile. Retain historical binaries
and hashes; reassemble known sources under a named profile. The repairs retain existing next-PC return addresses,16-bit P1_A targets,
out-of-program stopping and halt on empty RET. They introduce no additional
reserved-field policy and make no main-core control-flow implementation claim.
Boundary identity and focused commands are frozen in
`build/repo_audit/repairs_20261010_01/repair_boundary.json`.

## Legacy binary boundary (2026-11-05)

Recorded during the public-`master` reconciliation review
(`docs/PUBLIC_BRANCH_RECONCILIATION_REVIEW_2026-11-05.md`). Program images
(`software/programs/*.bin`) are raw big-endian 8-byte words with no header or
encoding identifier, so an image cannot state which encoding it expects.

| Historical tool (public `master`) | Non-canonical behaviour |
|---|---|
| C++ VM `software/vm/spu_vm.cpp` and the prebuilt executable `software/vm/spu_vm` (commit `2822bb5`) | COND 0x20, CALL 0x21, RET 0x22 |
| Python VM `software/spu_vm.py` | CALL and COND both 0x20; 0x20 executed as COND. Built-in assembler dropped QLDI C/D, DELTA steps and a third ADD operand, and skipped unknown mnemonics |
| Assembler `software/tools/spu13_asm.py` | Assembled COND as CALL 0x20; accepted and silently mis-encoded operand forms that the current validator refuses |

Images produced or interpreted by these tools are not supported by the
canonical toolchain and must not be executed by guessing a profile. A headerless
image is **unversioned**, not presumed legacy: in-repository images are
reproducible from their sources and `software/tests/test_program_images.py`
(release gate) requires every tracked image to equal canonical assembly of its
`.sas`. Distributable images and a loader (southbridge/H0) need an explicit
encoding identifier before use; that container format is not yet defined.

Repairs on 2026-11-05: `spu_compiler.py` now lowers the three-operand arc
addition as `QREAD` + in-place `QADD`; three Wildberger `.lith` sources replace
`IDNT R0` with `LD R0, 1, 0` and the scalar `QROT Rd, Rs, 1` lines with in-place
`ROT`; the four affected programs and the stale `isa_test.bin`/`ve_orbit.bin`
were regenerated. `laminar_vs_cubic.sas` remains a preserved legacy COND source;
no conditional branch exists in the canonical ISA.

C++ VM exit status: 0 clean completion; 1 usage, I/O, assembly or execution
rejection (a faulting instruction commits no state); 2 one or more SNAP
failures (takes precedence over the step budget); 3 `--steps` budget reached
before HALT with no SNAP failure. Checked by `software/tests/test_isa_conformance.py`
and `test_isa_software_semantics.py`.

## Proposed implementation qualification

Freeze the edit set and exact commands first. Required focused checks include
assembler words, CALL return-PC/stack behavior, nested calls, RET failure policy,
QREAD noncollision, COND rejection, explicit legacy source handling and C++/Python
agreement. Such arithmetic/shared execution changes retain the repository's
full regression/math/trace/Padé gates. No campaign or new encoding is launched
by this record. Historical passes do not establish repaired control behavior.
