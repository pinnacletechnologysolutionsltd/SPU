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

## Proposed implementation qualification

Freeze the edit set and exact commands first. Required focused checks include
assembler words, CALL return-PC/stack behavior, nested calls, RET failure policy,
QREAD noncollision, COND rejection, explicit legacy source handling and C++/Python
agreement. Such arithmetic/shared execution changes retain the repository's
full regression/math/trace/Padé gates. No campaign or new encoding is launched
by this record. Historical passes do not establish repaired control behavior.
