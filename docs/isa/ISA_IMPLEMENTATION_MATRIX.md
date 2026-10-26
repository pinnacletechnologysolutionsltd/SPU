# ISA Implementation Matrix

**Original audit date:** 2026-09-19
**Reconciliation annotation:** 2026-10-09
**Status:** Historical snapshot with the affected control-flow findings updated.
Unchanged rows and evidence retain their original scope and date. See
[October 9 control reconciliation](CANONICAL_CONTROL_RECONCILIATION.md) and
[qualification diagnosis](SURD_QUALIFICATION_DIAGNOSIS.md). Executable
compatibility repairs and fresh qualification remain pending.
**Profile:** ISA-A unless noted otherwise
**Evidence vocabulary:** `implemented`, `partial`, `profile-specific`,
`evidence-only`, `absent`, `unresolved`

This is a bounded inventory, not a claim that every opcode has identical
semantics across Python, C++, and RTL.

| Feature / opcode family | ISA-A spec | Python VM | C++ VM | Assembler | RTL | Tests / evidence |
|---|---|---|---|---|---|---|
| Scalar `LD/ADD/SUB/MUL/ROT/LOG` | implemented | implemented | implemented | implemented | partial/unresolved by module | VM tests; hardware mapping not established |
| Control `JMP/SNAP/CALL/RET/HALT/NOP` | canonical CALL=0x20, RET=0x21 | partial: October 10 collision repair passes focused checks; full gates pending | partial: canonical control repaired; basic QREAD added; full gates pending | canonical control definitions repaired; COND rejected; focused checks only | no JMP/CALL/RET handler established in inspected main core; other modules profile-dependent | historical tests do not establish repaired control parity; October 9 reconciliation |
| `COND` | unallocated in canonical profile | rejected canonically after October 10 repair | source rejected after October 10 repair | canonical source rejected after October 10 repair | no canonical COND handler established | no new encoding; focused rejection checks pass, full gates pending |
| `REGEN (0x09)` | implemented | implemented | absent | implemented | implemented, testbench-only | `test_regen_emulator.py`, `spu13_regen_tb.v` |
| Quadray `QADD/QSUB/QROT/QNORM/QLOAD/QLOG` | implemented | implemented | partial/implemented subset | implemented | partial across SPU-13 cores | Quadray, QSUB/DELTA, and trace tests |
| `QLDI (0x1D)` / `DELTA (0x1E)` | implemented | implemented | implemented | implemented | implemented | `test_regen_*`, QSUB/DELTA RTL tests; silicon QSUB path noted |
| `ROTC (0x1C)` angles 0–35 | implemented with angle fault boundary | implemented with guarded range | implemented for table subset | implemented | implemented in multiple cores | VM/RTL trace; §3.2g silicon for 0–5 |
| `IROTC (0xD6)` | implemented in `IROTC_SPEC.md` | implemented with typestate guards | absent | implemented | implemented with typestate tags | `test_irotc_vm_trace.py`, poison tests, §3.2k/§3.2k.1 |
| `LOAD2X (0xD7)` / `SCALE2 (0xD8)` | implemented | implemented | absent | implemented | implemented in IROTC integration | IROTC SPI evidence and RTL tests |
| IROTC 60-index main/conjugate catalog | implemented | implemented via generated catalog | absent | catalog-aware emission | implemented engine | 120-case RTL oracle; selected silicon vectors |
| Geometry `SPREAD/HEX` | implemented | implemented | implemented | implemented | partial/unresolved by core | rational/geometry tests; no unified silicon attribution |
| VE/Janus `EQUIL/IDNT/JINV/ANNE` | implemented | implemented | implemented subset | implemented | partial | VM and RTL targeted tests |
| SOM `0x2A/0x2B` | implemented | implemented | absent/partial | ISA-A assembler has SOM gap | implemented in SPU-13 RTL | SOM BMU/training tests and silicon evidence |
| Legacy `POLY_STEP/RATIO_CMP` | documented legacy extensions | historical/partial | absent or legacy | historical | profile-specific | legacy tests only |
| ISA-B WF `LOAD/STORE/MOVI/QMUL/...` | separate profile | only with WF assembler table, no default VM parity | absent | profile-specific via `--arch wf` | separate decoder/constants family | isolated next-generation tests; no ISA-A evidence |

## Immediate gaps

1. **C++ parity is not complete.** `software/vm/spu_vm.cpp` follows several
   ISA-A opcode values, but it lacks IROTC/LOAD2X/SCALE2 and is not a complete
   implementation of the current Python VM.
2. **Control collision confirmed October 9.** Effective Python/assembler
   CALL=0x20 and RET=0x21 follow the canonical reference, but COND also remains
   0x20. Python dispatch reaches COND before CALL. C++ and Lithic-L constructors
   still use legacy CALL/RET values. COND is unallocated canonically; the
   [compatibility plan](CANONICAL_CONTROL_RECONCILIATION.md) identifies repairs
   that remain unimplemented.
3. **RTL namespace collision.** `hardware/rtl/arch/spu_isa_defines.vh` uses
   overlapping numeric values for a different profile. Includes and build
   targets must identify ISA-B explicitly.
4. **Evidence granularity varies.** ROTC and IROTC have direct board evidence,
   while many table rows are only VM, RTL, trace, or historical evidence.
5. **GPU and SPI remain separate surfaces.** Their transport protocols are
   documented in [transport boundaries](../TRANSPORT_BOUNDARIES.md); they are
   not automatically ISA-A instruction streams. This historical matrix is not
   a current complete inventory; the October 9 canonical-path audit is linked
   from the [architecture map](../../knowledge/SPU13_ARCHITECTURE.md).

## Matrix rule

Until a generated conformance schema exists, a feature may be advertised as
“supported” only with the implementation and test surface named in this
matrix. “Implemented” in the specification column does not imply Python,
C++, RTL, or silicon parity.

## October 10 implementation annotation

The control row now reflects focused software repairs. The September/October9
collision findings above are historical diagnoses; the repair code exists, but
full repository qualification remains pending. Unchanged rows retain their
original evidence scope. Core fetch/PC/stack was not added.
