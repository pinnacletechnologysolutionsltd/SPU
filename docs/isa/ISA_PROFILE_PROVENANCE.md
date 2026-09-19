# ISA Profile Provenance

**Audit date:** 2026-09-19
**Audit contract:** `spu_strategy/contract_isa_reconciliation_2026-09-19.md`

This document resolves the repository's conflicting opcode tables by
provenance. It does not claim that every implementation is complete or that
every historical bitstream is reproducible.

## Profile decision

| Profile | Ownership | Encoding family | Intended status |
|---|---|---|---|
| **ISA-A** | **SPU-13 current architecture** | 64-bit word with 8-bit opcode and the `knowledge/isa_reference.md` field family | Current reference profile for the canonical assembler, Python VM, IROTC/ROTC software traces, and SPU-13 evidence |
| **ISA-B** | Wheeler–Feynman / next-generation adapter profile | Different 64-bit layout with 5-bit register fields and the `spu_isa_defines.vh` opcode family | Experimental or profile-specific; not a replacement for ISA-A |
| **ISA-C** | C++ implementation surface | Mostly ISA-A opcode values, incomplete feature set | Partial implementation of ISA-A; not authoritative |

“Current architecture” here means the ratified SPU-13 software/hardware
integration represented by the IROTC-bearing documents and evidence. It does
not mean that every RTL module in the repository has converged on ISA-A.

## Provenance table

| Surface | Profile | First/last known use | Hardware evidence | Paired tool/oracle | Claimed architecture |
|---|---|---|---|---|---|
| `docs/knowledge/isa_reference.md` | ISA-A | Added 2026-05-26; corrected through 2026-08-24 | Indirectly linked by the canonical VM/RTL trace wording and ROTC/IROTC contracts | `software/tools/spu13_asm.py`, `software/spu_vm.py`, ROTC/IROTC tests | SPU-13 current reference |
| `software/spu_vm.py` | ISA-A | Initial VM lineage 2026-04-03; IROTC added in `b052c3e` on 2026-07-10 | Software/trace oracle; not itself silicon evidence | `spu13_asm.py`, generated IROTC catalog, Python tests | SPU-13 reference VM |
| `software/tools/spu13_asm.py` | ISA-A plus ISA-B option | End-to-end `.lith` pipeline by 2026-05-22; WF table added with next-generation work | Generates source programs; individual output must be traced per evidence entry | Python VM and `.sas`/`.lith` programs | ISA-A default; ISA-B only with `--arch wf` |
| `software/vm/spu_vm.cpp` | ISA-C / partial ISA-A | Added `fc64f47` on 2026-04-04; parity updates in `2822bb5` | No direct silicon attribution established | C++ self-contained assembler/VM | Partial fast simulator |
| `hardware/rtl/arch/spu_isa_defines.vh` | ISA-B | Introduced with next-generation decoder work `41027af` on 2026-06-22 | No evidence found tying this table to the ROTC/IROTC silicon entries | ISA-B decoder/core family | Experimental adapter profile |
| `hardware/rtl/core/spu13/spu13_core.v` and `spu13_irotc_engine.v` | ISA-A integration for IROTC path | IROTC integration from 2026-07-10 onward | Direct: `docs/hardware_evidence.md` §§3.2k and 3.2k.1 | IROTC oracle, `IROTC_SPEC.md`, probe wrappers | SPU-13 current hardware path |

## Hardware evidence chain

### ROTC

`docs/hardware_evidence.md` §3.2g records the Tang 25K probe as validating
“all six ROTC angles on the canonical VM/RTL trace vector.” The recorded
simulation and build commands are:

```bash
iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_rotc_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_rotc_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_rotc_probe.v \
  hardware/rtl/core/spu13/spu13_rotor_core_tdm.v \
  hardware/rtl/common/prim/surd_multiplier.v

bash build_25k_spu13_rotc_probe.sh
```

The probe is therefore evidence for the ISA-A ROTC trace path, with the
documented limitation that the historical Tang build is no longer reproducible
on the current fabric.

### IROTC

`docs/hardware_evidence.md` §3.2k records the standalone IROTC probe:

```bash
bash build_25k_spu13_irotc_probe.sh
openFPGALoader -b tangprimer25k \
  build/tang_primer_25k_spu13_irotc_probe.fs
```

It identifies `spu13_irotc_engine.v`, the v0.2 `IROTC_SPEC.md` typestate
contract, exact Z[φ] oracle-derived constants, and the `IROTC:P E=00` result.
Section §3.2k.1 extends the same path through the SPI-dispatched instructions
`LOAD2X`, `IROTC`, and `SCALE2`, with six passing cases and a recorded
bitstream hash.

These entries establish direct hardware provenance for the ISA-A IROTC
semantics and its associated RTL integration. They do **not** establish that
the ISA-B opcode table was used by those probes.

### Provenance limitations

- The §3.2k and §3.2k.1 source anchors are candidates or failed rebuilds in
  the evidence ledger; the flashed bitstreams remain historical evidence.
- The SPI command words in §3.2k.1 are transport transactions and must not be
  conflated with 64-bit VM instruction encodings without a direct decoder
  trace.
- Some broad RTL files and historical cores use ISA-B-style constants. Their
  presence does not change ISA-A ownership of the current SPU-13 profile.

## Required follow-on work

1. Add explicit profile names to the ISA-B decoder/build targets.
2. Fix and test ISA-A assembler/VM/C++ opcode drift before calling the C++ VM
   feature-parity complete.
3. Generate cross-implementation conformance fixtures from one ratified ISA-A
   schema only after operand widths and instruction semantics are frozen.
