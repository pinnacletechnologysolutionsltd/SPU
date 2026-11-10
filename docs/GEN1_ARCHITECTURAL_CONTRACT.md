# Gen-1 Surd CPU: architectural contract of the frozen implementation

**Status: ACCEPTED 2026-11-09 (SPU-GEN1-CONTRACT-0)** as a document-consistency review by the owner. Source-line citations were
verified by the implementing agent; this is not a second independent RTL audit. Publication HOLD.

This document describes the machine that the frozen Gen-1 golden image **implements**. It is not the
processor originally intended, and it is not the experimental Surd ISA extension in
[`knowledge/isa_reference.md`](../knowledge/isa_reference.md). It introduces no architecture, encoding or
instruction. Where this document and another source disagree, the disagreement is listed in §12 and
left unresolved.

Every claim carries one authority level:

| Tag | Level | Meaning |
|---|---|---|
| **[I]** | Implemented | Read directly from the frozen RTL. Not by itself demonstrated by any test |
| **[V-sim]** | Verified in simulation | Demonstrated by an existing, accepted RTL simulation (named) |
| **[V-si]** | Silicon observation | Observed on the board in a named ledger entry, within that entry's stated limits. Not qualification |
| **[U]** | Unverified | Implemented [I], but no existing evidence demonstrates it |

"Gen-1 golden image" means only the configuration in §1. The **H0 experimental image**
([ledger §3.46](hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc),
[`H0_OVERVIEW.md`](H0_OVERVIEW.md)) is a different machine. It has runtime program banks, a host
protocol and its own evidence. Nothing here describes H0, and H0 evidence is never cited as Gen-1
evidence.

Source abbreviations (all paths relative to the repository root):

| Abbr. | File |
|---|---|
| FE | `hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_fetch_1b.v` (frontend, ROM) |
| BT | `hardware/boards/artix7/wukong_v3/cpu_v02/rtl/board_top.v` (top, UART packetizer) |
| SV | `hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_rst_1b_supervisor.v` (clock/reset) |
| IT | `hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_integrate_1_top.v` (integration, core parameters) |
| CO | `hardware/boards/artix7/wukong_v3/cpu_v02/rtl/spu13_core.v` (board-local core copy) |
| EX | `hardware/rtl/core/spu13/spu13_surd_exec.v` |
| LD | `hardware/rtl/core/spu13/spu13_surd_load.v` |
| BK | `hardware/rtl/core/spu13/spu13_surd_bank.v` |
| AR | `hardware/rtl/core/spu13/spu13_surd_arith.v` |
| PR | `hardware/rtl/math/surd_cpu_products.v` |
| NU | `hardware/rtl/math/surd_normalize_unit.v` (with `surd_binary_gcd3.v`, `surd_exact_quotient.v`) |
| XDC | `hardware/boards/artix7/wukong_v3/cpu_v02/constraints/cpu_board_3.xdc` |
| REG | Portable seven-case regression `hardware/tests/spu13/gen1_integration/` (GEN1-ISA-COVERAGE-2 / `599dbd0a`; readiness §3) |

## 1. Identity

| Item | Value |
|---|---|
| Package | `hardware/boards/artix7/wukong_v3/cpu_v02/` (frozen; `PACKAGE_SHA256.txt`) |
| Top | `cpu_board_2r_top` (BT:2) |
| Sources | `filelists/candidate_portable.f`: five package files, 17 unchanged `hardware/rtl` files, four headers ([SOURCE_MANIFEST](../hardware/boards/artix7/wukong_v3/cpu_v02/SOURCE_MANIFEST.md)) |
| Golden bitstream | `.bit` sha256 `442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea`; `.bin` `cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c` |
| Device / tool | `xc7a100tfgg676-1`, Vivado 2026.1 build 6511674; board Wukong V3 |
| Pins | `sys_clk` M21, `raw_rst_n` H7 (KEY0, pull-up), `uart_tx` E3; LVCMOS33 (XDC). No other I/O |
| Core configuration | `spu13_core` with `ENABLE_SURD_CPU=1`, and `ENABLE_SEQUENCER`, `RPLU`, `LATTICE`, `MATH`, `CORE_SOM`, `CORE_RPLU_V2*`, `REGEN`, `IROTC`, `TORUS` all 0 (IT:13) |

Any change to these sources or to the ROM contents produces a different machine, with no evidence carried over.

## 2. Machine overview [I]

A clock and reset supervisor (SV) drives one CPU clock domain. The frontend (FE) fetches 64-bit words
from a 16-word ROM, issues each accepted word to the core's Surd execution unit (EX), and waits for its
retirement. The Surd unit holds eight tuple registers (BK), a slice-staging loader (LD) and one
arithmetic engine (AR, PR, NU). The frontend latches readback words into a 192-bit result buffer. A
packetizer (BT) sends exactly one UART frame per reset: a success frame at HALT, or a fault frame at
FAULT. The UART frame is the only external observation.

## 3. Clocking, reset and boot

| # | Claim | Level | Source / evidence |
|---|---|---|---|
| 3.1 | `sys_clk` is constrained at 20 ns (50 MHz nominal). `cpu_clk` is a register toggled on every `sys_clk` edge, giving 25 MHz nominal; `test_pause` is tied 0 | [I] | XDC; SV:27–29; IT:11 |
| 3.2 | At configuration, `reset_hold=1` and `request_pending=1` (register initial values), so the power-up/configuration reset follows the same sequence as a KEY0 reset | [I] | SV:7 |
| 3.3 | `raw_rst_n` low **asynchronously** sets `request_pending` and `reset_hold`. After release, the pending request clears on the next `sys_clk` edge, and `reset_hold` stays high until `hold_count` reaches 7, about nine `sys_clk` edges in all | [I] | SV:13–25 |
| 3.4 | `cpu_rst_n` deasserts through a two-flop synchronizer on `cpu_clk`, cleared by `reset_hold` | [I] | SV:31–36 |
| 3.5 | During `cpu_rst_n` low, the frontend, Surd unit, bank, loader, arithmetic engine and packetizer reset synchronously or asynchronously as coded. The packetizer samples `cpu_rst_n` through a two-flop synchronizer and forces TX high | [I] | FE:38; EX:43; BK:15; LD:16; AR:48; BT:36 |
| 3.6 | Boot: with no QR file and no SOM, both hydration signals are constant 1, so the core boot FSM passes RESET → HYDRATING → READY. The frontend leaves BOOT on `boot_ready`. The watchdog boot-fault path is unreachable in this configuration | [I] | CO:913, 2222, 671–690; FE:41 |
| 3.7 | Recovery after a KEY0 press re-executes the program from PC 0 and emits one fresh frame | [V-si] | §3.42 (1 press), §3.48 (5 owner-reported presses), §3.52 (15/15 timed pulses); scoped, see §11 |
| 3.8 | Reset timing, metastability, a reset during UART transmission, and the "TX high within 3 clocks" response (BT:9–10 comment) | [U] | Not established (§3.52 limits; readiness §4) |

## 4. Program storage and loading

| # | Claim | Level | Source / evidence |
|---|---|---|---|
| 4.1 | The program is a 16 × 64-bit ROM (`ram_style="block"`) initialized in the RTL `initial` block, i.e. in the bitstream. Words 0–13 are the program; words 14 and 15 are 0 and never fetched | [I] | FE:11–21 |
| 4.2 | The golden ROM loads S0 = (1 + 2√3)/3 with six SLI and an SLD, squares it with SMUL, and reads back six slices. The expected result is (13 + 4√3)/9, raw slices (13,0,4,0,9,0) | [V-sim] [V-si] | FE:13–19; REG case G; §3.40, §3.47, §3.51 |
| 4.3 | The **only** program-loading mechanism is bitstream content: a different program requires a different bitstream. Recorded variants edited the RAMB36 INIT in the golden routed checkpoint before `write_bitstream`. `updatemem` was not used (CPU-ROM-1: HOLD) | [V-si] (method as recorded) | §3.41, §3.43, §3.49 |
| 4.4 | Configuration is volatile SRAM loading over JTAG (`openFPGALoader -c dirtyJtag`). Once configured, execution needs no host action; the host only receives UART | [V-si] | §3.40, §3.47; readiness §1 |
| 4.5 | Nonvolatile (flash) configuration of this image | [U] / not established | §3.50 (HOLD: unidentified flash image), §3.51; the `.bin` has never been programmed |
| 4.6 | Runtime program loading, program banks, host commands | **Not implemented** (H0 only) | FE has no write port |

## 5. Accepted instruction encodings [I]

Word layout (all instructions): `[63:56]` Op, `[55:48]` R1, `[47:40]` R2, `[39:24]` P1_A, `[23:8]` P1_B,
`[7:0]` must be 0. The frontend checks every fetched word against the patterns below (FE:26–28). **Any other
word faults the frontend at fetch, before issue** (FE:43). The core would also decode
0x74–0x77, S1–S7 and other forms (EX:8–21), but none of them can reach it through this frontend.

| Instruction | Accepted pattern (hex nibbles; `s` = slice 0–5, `p` = payload) | Fields |
|---|---|---|
| `SLI S0, s, u32` | `70 00 0s pppppppp 00` (Op 0x70, R1 = 0, R2 < 6, bits [39:8] = payload, [7:0] = 0) | slice index R2; 32-bit payload `[39:8]` (EX:36) |
| `SLD S0` | exactly `7100000000000000` | — |
| `SMUL S0, S0, S0` | exactly `7300000000000000` | destination R1 = 0, Sa = R2 = 0, Sb = `[31:24]` = 0 (EX:9) |
| `SRD S0, s` | `72 00 0s 0000000000` (R1 = 0, R2 < 6, bits [39:0] = 0) | source R1, slice R2 (EX:32, 64) |

Slices order the 192-bit tuple as 0 = a[31:0], 1 = a[63:32], 2 = b[31:0], 3 = b[63:32], 4 = d[31:0],
5 = d[63:32] (LD:19; BK:9). Encodings were verified as accepted on the golden program [V-sim]
[V-si]. One rejected encoding of each kind was exercised in simulation: SLI with `[7:0]` ≠ 0 (REG M1)
and SADD `7400000000000000` (REG M2) [V-sim]. Other rejected encodings are [U].

## 6. Architectural state [I]

| State | Reset value | Notes |
|---|---|---|
| Tuple registers S0–S7, 192 bits each | `{d=1, b=0, a=0}` with all eight marked **uninitialized** | BK:15–17. Only S0 is reachable in Gen-1 |
| Staging buffer (192 bits), `received[5:0]`, `held_target` | 0 | LD:16 |
| Surd `status` register | 0 | EX:45. Holds the last retirement's status. Not externally visible (SSTAT is not accepted) |
| Frontend `pc` (4 bits), `state`, `halted`, `fault` | 0, BOOT, 0, 0 | FE:38 |
| Result buffer (192 bits), `result_valid[5:0]` | 0 | FE:38 |

Tuple value: (a + b√3)/d with a, b signed 64-bit two's complement and d unsigned 64-bit. A **committed**
tuple always has d ≠ 0 (§7). Tuples are not required to be in canonical form (§7.3).

## 7. Instruction semantics

Status codes (EX): 0 OK, 1 INVALID, 2 OVERFLOW, 3 ENGINE_FAULT, 4 BAD_ENCODING. In Gen-1, **any**
nonzero retirement status faults the frontend (FE:30–31). The status value itself is never transmitted
(§9).

### 7.1 SLI S0, s, payload
Writes the payload into staging slice s and marks it received [I] (LD:18–20). Re-writing a slice
overwrites it. A slice for a different target while staging is non-empty would return INVALID (LD:12), but
that is unreachable in Gen-1, where the target is always S0. No tuple register changes [I].
Retires with status 0, without a write or read flag [I] (EX:60). Verified on the accepted program [V-sim] [V-si].

### 7.2 SLD S0
Commits the staged tuple to S0 and marks S0 initialized **iff** all six slices were received for the same
target and d ≠ 0 [I] (LD:13; EX:26–28, 61). Otherwise it retires INVALID (status 1) and S0 is unchanged
[I]. The staging buffer is cleared on **every** SLD, successful or not [I] (LD:17). The committed tuple is
exactly the staged bits, with no normalization [I].
- d = 0 → INVALID → fault at PC 6 [V-sim] (REG case I).
- Incomplete staging → INVALID [U] (not exercised).

### 7.3 SMUL S0, S0, S0
Operands are snapshotted at acceptance [I] (AR:55). If an operand is uninitialized → INVALID (EX:23, 55) [U]
(unreachable once SLD has succeeded; not exercised). An operand with d = 0 → INVALID (AR:56) [I]
(unreachable: committed tuples have d ≠ 0).

Raw product with (a,b,d)·(c,e,f), signed 64 × signed 64 (PR:27–36) [I]:

  A = a·c + 3·b·e, B = a·e + b·c, D = d·f (unsigned).

| Case | Behaviour | Level |
|---|---|---|
| A and B fit signed 64, and D fits unsigned 64 with D ≠ 0 | Commit the **raw, unreduced** (A,B,D), status 0 (AR:71–72) | [V-sim] REG G, N1; [V-si] §3.40, §3.41, §3.43, §3.47, §3.49 (all raw-fit) |
| Otherwise | Exact normalization: g = gcd(\|A\|,\|B\|,D) by binary GCD; A/g, B/g, D/g by exact quotient, with remainders checked zero (NU). Signs are carried on A and B; D stays positive | [I] |
| — normalized value fits | Commit the normalized tuple, status 0 (AR:79) | [V-sim] REG N2 |
| — normalized value does not fit | Status 2 OVERFLOW; S0 **unchanged** (EX:27, 50); fault at PC 7 | [V-sim] REG O |
| — engine fault (GCD/quotient fault, non-zero remainder, invalid result) | Status 3 ENGINE_FAULT; S0 unchanged (AR:77, 81) | [U] (no case reaches it) |
| A = B = 0 but D does not fit (reachable: a = b = 0 with d ≥ 2³²) | Normalizer maps zero to (0,0,1); commit, status 0 (NU:74–76) | [U] (not exercised) |
| A = B = 0 and D fits | Commits the raw (0,0,D), not (0,0,1) (raw-fit rule) | [U] (not exercised) |

The result is a correct exact value of x² over Q(√3) whenever it commits [I by construction of PR/NU;
V-sim on G, N1, N2]. **Canonical form is not guaranteed**: a raw-fit result commits unreduced (e.g. (13,4,9)
is canonical only by coincidence of the inputs).

### 7.4 SRD S0, s
If S0 is initialized: returns the 32-bit slice s, status 0, with the read flag set [I] (EX:62–64). The frontend
stores it at result slot s and sets `result_valid[s]` [I] (FE:33). If S0 is uninitialized → INVALID → fault [U]
(unreachable after a successful SLD). Verified on the accepted program [V-sim] [V-si].

## 8. Frontend sequencing, HALT and FAULT [I]

States BOOT → FETCH → FETCH_WAIT → ISSUE → (WAIT_RETIRE) → REARM → FETCH … (FE:10, 39–49).

- **Fetch check:** if the fetched word matches no §5 pattern → FAULT, with `pc` left at the offending word
  (FE:43). [V-sim] M1 (PC 1), M2 (PC 7).
- **Retirement check:** FAULT if the status is nonzero; or SRD retires without a read; or a non-SRD
  retires with a read; or the write flag differs from expectation (SLD and SMUL expect a write; SLI and SRD
  do not). `pc` is left at the faulting instruction (FE:29–31). [V-sim] O (PC 7, status 2), I (PC 6, status 1).
  The flag-mismatch branches are [U].
- **Unexpected retirement** (a retire outside ISSUE/WAIT_RETIRE) → FAULT and `halted` cleared (FE:39) [U].
- **HALT:** after word 13 retires, REARM sets `pc` = 14 and `halted` = 1. HALT and FAULT are terminal until
  reset (FE:46–48). [V-sim] [V-si] (PC 14 in every success frame).
- There is **no** branch, jump, call, return, loop or interrupt. Control flow is strictly PC 0 → 13 → HALT.

## 9. External observation: the UART frame

| # | Claim | Level | Source / evidence |
|---|---|---|---|
| 9.1 | One frame of exactly **33 bytes** per reset: a success frame when `halted` ∧ ¬`fault` ∧ mask = 0x3F; otherwise a fault frame as soon as `fault` rises. In every reachable execution **at most one frame total** is sent per reset (success or fault), and the line then stays idle-high. This is a property of the frontend, not the packetizer: the fault branch tests only `sent_f` and pre-empts a transmission in progress (BT:37). A fault after HALT is unreachable by inspection, because after HALT `inst_valid` = 0 and nothing can retire (FE:23, 39) | [I]; [V-si] success frames; one-frame-total [U] | BT:36–38; FE:23, 39; §3.40 (exactly 33 bytes, no other byte) |
| 9.2 | Serial format: 8N1, LSB first, bit period 217 `cpu_clk` cycles = 115,207 Bd nominal (+0.006 % vs 115,200). Twelve idle-high bit times precede the start bit; bytes are back-to-back after one stop bit | [I]; [V-si] reception at 115200 8N1 | BT:13, 39–51 |

Byte layout [I] (BT:24–32). Success layout: [V-sim] REG all cases; [V-si] §3.40 capture.

| Bytes | Content |
|---|---|
| 0 | `0xA5` (magic) |
| 1 | `0x01` (frame version) |
| 2 | `0x01` success, `0x02` fault |
| 3 | `result_valid` mask, bits [5:0] (`0x3F` on success) |
| 4 | `pc` (4 bits, zero-extended): **14** on success; the faulting instruction's index on fault |
| 5–28 | Result buffer, slices 0–5 in order, each 32-bit **little-endian**. A slice whose mask bit is clear is sent as zeros |
| 29–32 | CRC-32/ISO-HDLC (reflected poly 0xEDB88320, init 0xFFFFFFFF, final complement; = `zlib.crc32`) over bytes 0–28, **little-endian** |

Golden success frame [V-si] §3.40, [V-sim] REG G:
`a5 01 01 3f 0e | 0d000000 00000000 04000000 00000000 09000000 00000000 | 422b6b75`.

**Fault frame contents.** It carries the fault marker, the mask, the PC of the faulting word, and any
result slices already read back (zeros otherwise) [I]. It does **not** carry the status code, the fault
cause (fetch rejection vs retirement status) or the tuple contents. Fault frames are [V-sim] only
(REG O, I, M1, M2). **No Gen-1 fault frame has been observed on silicon.**

## 10. Explicit exclusions (not part of the Gen-1 machine)

- Registers S1–S7 (present in BK, unreachable).
- SADD, SSUB, SNORM, SSTAT (0x74–0x77): present in EX/AR, rejected by FE.
- Any scalar R-file, Quadray QR, ROTC, REGEN, IROTC, SOM, sequencer, GPU or telemetry function. All are
  disabled by parameter (IT:13).
- All control flow (JMP, CALL, RET, COND, QREAD and HALT as an instruction). HALT is a frontend state
  reached after PC 13, not an opcode.
- Runtime program loading, a host command interface, input from the host, and SPI. UART is TX-only.
- The status code as an external observation.
- (Not an exclusion, listed for clarity.) Nonvolatile flash boot is not qualified for the Gen-1 golden image; JTAG/SRAM
  configuration is the demonstrated boot mechanism (§4.4–4.5). Flash boot is a board-level startup mechanism, not a CPU
  architectural feature.

## 11. Qualification boundary (what existing evidence does and does not establish)

| Dimension | Established | Not established |
|---|---|---|
| Functional, RTL | Seven directed cases (G, N1, N2, O, I, M1, M2), exact frames, negative controls (REG) | Exhaustive encodings, all operand ranges, ENGINE_FAULT, uninitialized/incomplete paths, gate-level/netlist equivalence |
| Functional, silicon | Success frames for the golden program and three ROM variants, single runs: (13,4,9) §3.40; (16,8,9) §3.41; (7,4,25) §3.43; (7,4,9) §3.49; 3/3 reloads §3.47; after a power cycle §3.51 | Any fault frame; normalization on silicon; more than one unit; failure rates |
| Reset | Scoped recovery: §3.42, §3.48, 15/15 timed pulses §3.52 | Reset timing, metastability, reset during transmission |
| Timing | GEN1-STA-1 nominal routed STA PASS ([closure](GEN1_STA_1_CLOSURE_2026-11-07.md)) | Physical margin, I/O timing (`raw_rst_n`, `uart_tx` unconstrained delays) |
| Build | Payload reproduced bit-exactly (REPRO-1B; second host) | — |
| Boot | JTAG/SRAM configuration | Flash boot |

All silicon entries are single-unit observations, not qualification. See each ledger entry's own limits.

## 12. Discrepancies with other sources (recorded, not resolved)

| # | Source | Discrepancy |
|---|---|---|
| D1 | `hardware/rtl/arch/spu_isa_defines.vh` (0x70–0x76); `software/common/include/spu13_arch.h` (0x70–0x75); `software/tools/spu13_asm.py` mnemonics MFOLD/STAT/SCALE/QR | Name 0x70–0x73 as telemetry operations (MFOLD, STAT, SCALE, QR). The frozen core decodes any word with `[63:59]` = `01110` (0x70–0x77) as Surd when `ENABLE_SURD_CPU=1` (CO:718). The assembler accepts both mnemonic families for the same bytes |
| D2 | `spu_isa_defines.vh` | CALL = 0x66, RET = 0x67, versus the canonical CALL 0x20 / RET 0x21 in `isa_reference.md`. Irrelevant to Gen-1, which has no control flow, but listed because it shares the header |
| D3 | `knowledge/isa_reference.md`, Surd section | Labelled "experimental", it defines eight registers and eight opcodes. Gen-1 implements the four-pattern subset of §5 only |
| D4 | `knowledge/isa_reference.md`, Surd section | States "No CPU tuple-extension silicon evidence is claimed". Silicon observations now exist (§11). Stale relative to the ledger |
| D5 | `knowledge/isa_reference.md`, Surd section | Does not state that a failed SLD clears staging (LD:17), or that SLI to a second target during staging is INVALID (LD:12). The RTL is more specific; it is not contradictory |
| D6 | `docs/CAPABILITY_MATRIX.md` CPU row; `cpu_v02/README.md` | Readiness index §8 items 1–2: the README says "not yet rebuilt" (now reproduced), and the matrix row omits §3.42 and §3.47–3.52 |
| D7 | Python VM, C++ VM (`software/vm`), `spu-sim` | Implement none of §5–§9 ([ISA_CONFORMANCE_2026-10-10](isa/ISA_CONFORMANCE_2026-10-10.md): "Surd unsupported"). The executable software reference for these semantics is the REG oracle and `software/experiments/surd_cpu_stream.py` |

## 13. Notes for simulator conformance (Task B input, not a design)

- **Two interfaces.** The external interface is the 33-byte frame (§9), with no status code. A simulator may
  expose internal diagnostics (status code, fault cause, tuple contents) on a separate, labelled interface.
  It must not present them as hardware-observable.
- **Input is a 16-word ROM image** (or 14 words plus two zero words), selected explicitly under a Gen-1
  profile. Bytes 0x70–0x73 must not be interpreted under any other profile (D1).
- **Reference outputs** for conformance are the REG fixture `fixtures/expected_records.json` (sha256
  `3268eed2b374c5fdea7e3ac9ca78ac119fad059c8d1d0c98b4f8dfdefa01b832`) and the silicon frames in §11.
  The simulator should reproduce the raw-fit, non-canonical commit rule exactly (§7.3).
