# ISA-V02-STATE-1 — Architectural state across the specification, VMs and SPU-13 RTL

**Status:** read-only source characterization PASS; normative architectural-state contract **HOLD**. The C0 and H0 profiles below are **PROPOSED**, not implemented contracts. No VM, assembler, opcode, RTL, test, tool, generated-inventory or hardware change.
**Baseline identity:** `dev/next` at `c2f7b36074c8163b7f2294e8be5ba3bcfde35673` (clean). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280` (`b0632806621ed6fe44c9c72f4e0adbd8ee8df776`); analysis tools and tests were added in `dev/next`. Line numbers are at `c2f7b36`.
**Method:** source reading only (`grep`/`sed`). Nothing was elaborated, simulated, synthesized or run on a board. Matching opcode numbers are not treated as evidence of equivalent behavior.
**Sources:** `knowledge/isa_reference.md`; `docs/isa/ISA_SOFTWARE_SEMANTICS_2026-10-10.md` and `ISA_CONFORMANCE_2026-10-10.md` (frozen earlier records, cited, not re-derived); `software/spu_vm.py`; `software/vm/spu_vm.cpp`; `hardware/rtl/core/spu13/spu13_core.v`; `hardware/rtl/top/spu_ve_qr_init.v`; `hardware/rtl/peripherals/io/spu_spi_slave.v`; `hardware/boards/artix7/spu_a7_top.v`; `docs/BOOT_SEQUENCE_FSM.md`.

## 1. State inventory

| State element | Spec | Python VM | C++ VM | SPU-13 RTL core | Artix-7 top |
|---|---|---|---|---|---|
| Scalar `R0–R25` (`a`, `b`, Pell step) | yes | yes (`NUM_REGS=26`, `spu_vm.py:1217`) | yes (`:482`) | **none**: no scalar execution (conformance record) | none |
| Quadray `QR0–QR12` | yes | yes | yes | yes, 13 lanes, ECC regfile (`spu_quadray_regfile_ecc`) | through the core |
| QR reset state | not specified | all zero (`__init__`) | all zero | after `boot_done`: QR0 identity, QR1–12 the 12 cuboctahedron vertices (`spu_ve_qr_init.v`) | through the core |
| QR component encoding | `a + b√3` | integer pair `RationalSurd` | integer pair | 64-bit lane; `QLDI` writes a sign-extended imm8 to `[31:0]`, `[63:32]=0` (`spu13_core.v:1376-1392`); VE hydration writes `0x1000` (Q12) per unit (`spu_ve_qr_init.v:36-41`) | through the core |
| φ-plane tag per QR | IROTC spec | `qr_doubled` | none | `qr_tags` | through the core |
| Surd bank `S0–S7`, `SSTAT` | yes (`ENABLE_SURD_CPU`) | none | none | yes, default off (`:13`) | off in named spins |
| PC | `JMP`/`CALL` encodings only | `pc` | `pc` | **none**; the instruction is supplied from outside | none |
| Call stack | `CALL`/`RET` encodings only | list | vector | **none** | none |
| Retired-step count | not stated | `step_count` | `step_count` | none | none |
| Halt and fault | not stated | `halted`, `fault_kind` | `halted`, `fault_kind` | none | none |
| Boot state | `docs/BOOT_SEQUENCE_FSM.md` | none | none | `boot_state` RESET/HYDRATING/READY/FAULT, `boot_ready` (`:664`) | `boot_ready` readable in the SPI status byte |
| Diagnostics | FLAGS (unimplemented; see SNAP-1) | `snap_failures`, Davis gasket, SDF | `snap_failures` | `rotc_debug_status`, `ecc_single_err`/`ecc_double_err`, `is_janus_point` | `rotc_debug_status` over SPI; `ecc_*` and the composite `inst_done` have no further reference in `spu_a7_top.v` |

Further state exists in only some profiles (REGEN block counter in the Python VM and RTL; SOM weights; RPLU configuration; Python-only Davis gasket and SDF). It is not part of a minimum contract.

## 2. Instruction encoding and host ingress

- **Word layout.** `[63:56]` opcode, `[55:48]` R1, `[47:40]` R2, `[39:24]` P1_A, `[23:8]` P1_B (`isa_reference.md`). Both VMs decode these fields, sign-extend the 16-bit P1_A and P1_B, and ignore `[7:0]` (`spu_vm.py:1325-1334`; `spu_vm.cpp:521-532`). The spec requires `[7:0]` zero only for the Surd extension.
- **`QLDI` fields** agree across the VMs and the RTL (`A=[39:32]`, `B=[31:24]`, `C=[23:16]`, `D=[15:8]`). Quadray register indices wrap modulo 13 in all three (the RTL `qr_lane` function).
- **VM ingress.** A program list; `load()` sets PC to 0 and clears `halted`, `fault_kind` and `step_count` while retaining the register banks, stack and `snap_failures` (frozen record).
- **RTL ingress.** The core takes `inst_valid`/`inst_word` and produces an `inst_done` pulse. Acceptance is `inst_accept = eff_inst_valid && !inst_seen && !surd_busy` (`:710`), where `eff_inst_valid` requires `boot_ready` (`:707-708`); `inst_seen` re-arms when valid drops (`:730-737`). On the Artix-7 top the only source is SPI command `0xB1` (`spu_spi_slave.v`): a 64-bit big-endian word with CRC, delivered as a one-cycle `inst_valid` strobe; a CRC failure sets a sticky error instead (`crc_error_sticky`). The `ENABLE_SEQUENCER` ROM-playback path is off in the Artix-7 top. Instructions presented before `boot_ready` are not accepted and produce no indication other than the readable `boot_ready` status.

## 3. PC, fetch and retirement

- **VMs.** A PC at or beyond the program end halts without a `fault_kind` (`spu_vm.py:1354-1356`; `spu_vm.cpp:584-587`). `JMP`/`CALL` targets are `P1_A & 0xFFFF`; `RET` on an empty stack halts. `HALT` sets `halted`, advances the PC and counts as retired. The step budget halts silently in Python (`:2496`) and sets `step_limit_reached` (process exit 3) in C++ (`:1052`). Python raises before committing for the refusals examined (unsupported opcode, invalid scalar register, bad ROTC angle, degenerate SPREAD) but has no snapshot-restore; C++ `step()` snapshots registers, QRs, stack, PC, `step_count` and `snap_failures` and restores them on a fault (`:565-581`). The software record states that unsupported and overflow faults do not retire.
- **RTL.** There is no PC, fetch or retirement count. Completion is a one-cycle `inst_done` pulse set in the per-opcode branches (`spu13_core.v`, `inst_done_r`) and in the catch-all described next.

## 4. Unsupported-opcode behavior

- **VMs.** An opcode outside the table, or one with no implementation, faults: Python sets `halted` and `fault_kind = "UNSUPPORTED"` and raises (`spu_vm.py:1360-1364`); C++ throws `VmFault("UNSUPPORTED", ...)` (`spu_vm.cpp:1041-1043`) and restores state.
- **RTL.** The final branch of the instruction FSM (`spu13_core.v:1662-1678`) sets `inst_done_r <= 1` for any accepted opcode that is not: a Surd opcode, `0x1D`, `0x1C`, `0x16`, `0x1B`, `0x1E`, the IROTC set when `ENABLE_IROTC`, NSA when the extension bundle is on, `0x2A` when the RPLU2 pipeline is on, or `0x2A`/`0x2B` when `ENABLE_CORE_SOM`. (Earlier branches handle REGEN, JSCR and a few others.) The comment in the code says "Unknown/QLOG — consume immediately".
- **Consequences visible in source.** `inst_done` is pulsed with no state change for (a) opcodes with no RTL support, among them `LD`, `ADD`, `SUB`, `MUL`, `ROT`, `LOG`, `JMP`, `HALT`, `SNAP`, `QADD`, `QROT`, `QNORM`, `QLOAD`, `QLOG`, `QREAD`, `SPREAD`, `EQUIL`, `IDNT`, `JINV`, `ANNE`, `MIN4`, `CALL`, `RET` and `NOP`; and (b) opcodes whose feature parameter is off (for example IROTC without `ENABLE_IROTC`, SOM without `ENABLE_CORE_SOM`, NSA without the extension flag). The `0xE0` handler also acts in an independent block (`:1899-1907`) while this branch acknowledges the same opcode. The existing conformance record also notes that a ROTC with math disabled can hang (not re-derived here).
- **Hazard.** A host that treats `inst_done` as successful execution cannot distinguish an executed instruction from an acknowledged no-op. No profile in the repository specifies a hardware refusal; the software profile specifies `UNSUPPORTED`. The two behaviors are not interchangeable and should not be described under one name.

## 5. QR reset state and representation

- The VMs construct all QRs as zero. The RTL, after `boot_done`, loads QR0 and QR1–12 through `spu_ve_qr_init` (VE vertices, permutations of `(-1,0,0,1)`), and instructions are held until the walk finishes (`qrf_hydrated`, `spu13_core.v:776`; boot FSM gating `:707`).
- VE hydration uses `1 = 0x00001000` ("Q12 scaled", `spu_ve_qr_init.v:36-41`), while `QLDI` loads unscaled integers (`spu13_core.v:1376-1392`). Whether Q12-scaled and unscaled values may coexist in one register file, and how downstream operations interpret the scale, was not established.
- The lane layout is inferred, not verified: `QLDI` and the VE constants put the value in the low half, while a comment in `spu_ve_qr_init.v` says `{P[31:0], Q[31:0]}`.
- Consequently the VM state "QR = exact coefficient pair" and the RTL state "QR = 64-bit lane, hydrated, partly Q12-scaled" are different state models; matching `QLDI` field positions does not make them one.

## 6. Background mutation and diagnostics

- **Python VM.** After every executed instruction, including `HALT`, the Fibonacci dispatch and Davis gasket hook runs (`spu_vm.py:2469-2495`). At φ13/φ21 gates it can call `henosis_recover`, which halves QR components in place and resets the φ-plane tags (`:2482-2490`). C++ has no such hook. Observed in QROT-1: a cycle-14 pulse zeroed `QR0` after a `QROT`. This is state mutation not caused by the instruction being executed.
- **Diagnostics.** `snap_failures`, `fault_kind` and VM stdout/exit codes (VMs); `rotc_debug_status`, boot state, `is_janus_point` and ECC flags (RTL). SNAP-1 records that these are not an architectural FLAGS register.

## 7. Unverified

- **Backpressure and multi-cycle behavior.** `inst_accept` is blocked only by `inst_seen` and `surd_busy`. What happens if a second `inst_valid` strobe arrives while a multi-cycle instruction (for example ROTC, IROTC) is in progress was not traced, so two submitted instructions are not shown to produce two ordered executions.
- That `inst_done` corresponds to a committed result for every accepted opcode. The ack-without-effect branch shows it does not.
- The 64-bit lane format beyond `QLDI` and the hydration constants (§5).
- The consumers of `ecc_single_err`/`ecc_double_err` (none in `spu_a7_top.v`).
- The reset/readiness behavior of non-Artix-7 tops.

## 8. PROPOSED profiles (not implemented contracts)

**C0, software execution profile.** A sequential machine: `R0–R25`, `QR0–QR12`, PC, call stack, a retired-step count, `halted` and `fault_kind`. Out-of-program fetch halts with an empty `fault_kind`. `HALT` retires once. Faults are atomic and do not retire; the fault set includes `UNSUPPORTED`, `INVALID_REGISTER`, `OVERFLOW` and per-instruction refusals. `snap_failures` is diagnostic only; the Python gasket, SDF and henosis hooks are a named extension profile, not part of C0. This builds on `ISA_SOFTWARE_SEMANTICS_2026-10-10.md`.

**H0, host-driven hardware execution profile (accelerator profile).** `QR0–QR12` with tags, an explicit boot FSM, and single-instruction ingress with an `inst_done` pulse, accepting only when READY. It implements a verified subset of operations. It has no scalar file, PC, call stack or fault state. It must specify: the QR reset state and scale (§5); the treatment of every opcode outside the subset (acknowledged no-op as today, or a refusal, which needs a design decision and is not made here); acceptance, busy and ordering behavior (§7); and the status interfaces as implementation diagnostics. **H0 is not a complete implementation of C0**, and matching opcode numbers does not imply equivalence.

## 9. Architectural execution versus host transport

The SPI link (`0xB1` word, CRC, strobe), the sidecar claim arbitration and the readable status byte are host transport. They determine whether a word reaches the core, and are not the execution contract of an instruction. Faults at the transport layer (CRC error sticky; instructions presented before READY) are distinct from architectural refusals and are currently the only refusal-like signals on the Artix-7 path.

## 10. Proposed release stages (proposal only)

A **Reference Machine** (a software execution model with defined architectural state, C0) and an **FPGA Execution Engine** (a documented subset executed through host commands, H0). Which stage a given artifact belongs to should be stated with that artifact.

## 11. Unresolved issues found while documenting

1. The ack-without-effect default and its feature-parameter variants (§4) have no documented intent; whether it is deliberate is not stated in any file read.
2. `inst_done` has no documented meaning beyond the pulse.
3. `HALT`, `JMP`, `CALL`, `RET` and `SNAP` are acknowledged no-ops in RTL, so a host-driven stream cannot express control flow.
4. The comment and the constants in `spu_ve_qr_init.v` disagree about lane order (§5).
5. The composite `inst_done` wire and the ECC flags in `spu_a7_top.v` are unconsumed there.

## Limitations

Source reading only; no RTL simulation, synthesis, board qualification, timing analysis or silicon claim. `docs/hardware_evidence.md` was not consulted for state or retirement entries. SPU-4 has its own state model and is out of scope. The O6 inventory is a non-exhaustive census (see `ISA_V02_O6_FINDINGS.md`). Conclusions apply to the identity above.
