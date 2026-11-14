# SPU v0.3 RTL-0C plan: physical bring-up on the Wukong Artix-7

**Status: COMPLETE — physical demonstration objective achieved 2026-11-12.** Gates C0–C4 PASS; C5 accepted;
one SRAM session (load 1 of 3, route attempt 1 of 2) passed all 95 steps; recorded as
[`docs/hardware_evidence.md`](../hardware_evidence.md) §3.53, a single-session silicon observation on one board.
LUTAR-1 (a LUT drives the reset synchronizer's asynchronous clear) is an owner-accepted residual risk. Plan
revision 2: D1–D8 approved 2026-11-12 with four refinements (R1–R4, marked below). No flash write, frozen-ISA
change or Gen-1 change was made.

**Specification:** the frozen [v0.3 contract](SPU_V03_CONTRACT_CANDIDATE.md) and the host protocol recorded in
the [RTL-0B plan](SPU_V03_RTL0B_PLAN.md) §3 and §7.

**Builds on:** RTL-0B, gates B1–B6 PASS, and the synchronizer attribute correction (`98c85afd`; RTL-0B plan
§8.3: out-of-context setup +6.986 ns, hold +0.056 ns). That evidence is simulation and out-of-context routed
timing. **No v0.3 hardware has run on an FPGA.**

## 1. Objective and boundaries

**Objective.** Load a simple SPUI program through the board's physical UART, execute it on the v0.3 core, and
read back a 213-byte result record that equals the independent oracle byte for byte.

**In scope:** one board top around the unchanged `psurd_sys_top`; pin and clock constraints; a board-level
simulation; a board-level route and bitstream; a host client; one bounded physical session; a ledger entry
drafted for owner review.

**Not in scope:**
- any change to the frozen v0.3 ISA, to frozen Gen-1 modules, or to the RF-B register bank;
- any change to `psurd_sys_top` or the modules below it (a defect found here is a HALT, §9);
- configuration flash (SRAM load only), LEDs, external headers, any second board;
- baud-rate, voltage, temperature or signal-integrity margin testing;
- a public push.

## 2. Board facts and what each rests on

Every row is re-checked in gate C0 before anything is built. "Ledger" is
[`docs/hardware_evidence.md`](../hardware_evidence.md).

| Item | Value | Source | State |
|---|---|---|---|
| Board | QMTECH Wukong, owner-identified V3 | Ledger §3.46 (V03 schematic hash) | Owner-identified |
| Device | XC7A100T-1FGG676C; JTAG idcode `0x3631093` | Ledger §3.40, §3.46 | Idcode observed; speed grade from the seller listing, **not physically verified** |
| Clock | 50 MHz oscillator on M21, LVCMOS33, 20.000 ns | `spu_a7_surd_cpu_base.xdc`; ledger §3.40 onward | Used by the Gen-1 runs; frequency not instrumented |
| CPU clock | 25 MHz: divide-by-two fabric flop into a BUFG | `spu_a7_surd_cpu_base_top.v` | Topology used in ledger §3.40–§3.52 |
| Reset | KEY0 on H7, **active low**, no external pull (PULLUP set in the constraint) | Same file; ledger §3.42, §3.48, §3.52 | KEY0 restart observed for Gen-1 |
| UART host → FPGA | F3, LVCMOS33, PULLUP | `spu_a7_uart_loopback.xdc`; ledger §3.11 | Observed |
| UART FPGA → host | E3, LVCMOS33 | Same; ledger §3.46 | Observed |
| USB bridge | CH340 (`1a86:7523`), 115,200 8N1 | Ledger §3.11, §3.46 | Observed |
| Configuration bank | `CFGBVS VCCO`, `CONFIG_VOLTAGE 3.3` | `research/h0_board_uart_1a/board.xdc` | As used in §3.46 |
| LEDs | **Not used.** Documented I/O anomaly on this unit | `spu_a7_100t.xdc` | Closed, not fixed |
| Programming | `openFPGALoader -c dirtyJtag --freq 1000000 <bit>` (SRAM) | Ledger §3.46 | Observed |

Ledger §3.46 is a single-session observation of experimental H0 research RTL. It supports the pin, bridge and
programming rows above. It is **not** evidence for the v0.3 design.

## 3. Architecture

One new module, `hardware/boards/artix7/psurd_board_top.v`, and nothing else in RTL.

| Part | Content |
|---|---|
| Clock | `sys_clk` (50 MHz) → divide-by-two flop → BUFG → `cpu_clk` (25 MHz), as `spu_a7_surd_cpu_base_top.v` |
| Reset | Raw `rst_n` pad → two-flop synchronizer → 255-cycle release counter (50 MHz) → asynchronous-assert, synchronous-release pair in the 25 MHz domain → `psurd_sys_top.rst` (active high) |
| System | `psurd_sys_top` with its defaults: 25 MHz, 115,200 baud, 17,360-cycle inter-byte limit. **No parameter override** |
| Pins | `sys_clk` M21, `rst_n` H7, `uart_rx` F3, `uart_tx` E3. `busy`, `image_valid`, `record_valid` are left unconnected |

**Effect of reset (to be shown in C2 and P8):** image-valid, load-open, run state and run id return to their
reset values, so STATUS reads flags `00`, IDLE, cause `FF`, run id 0. Memory contents may persist but are not
reachable: START is refused until a new image is loaded and RESULT is refused until a new run completes.

**Constraints** (`psurd_board.xdc`): the pin table above; `create_clock` 20.000 ns on `sys_clk`;
`create_generated_clock` divide-by-two for `cpu_clk` at the divider flop; `CFGBVS` and `CONFIG_VOLTAGE`.
Asynchronous inputs (`uart_rx`, `rst_n`) get an exception **only** to the first synchronizer stage, applied
after the exact pins are confirmed in synthesis. No I/O delays are invented.

## 4. Host client

`tools/psurd_uart_host.py` (D6): builds H0-UART-1B v2 frames, performs stop-and-wait with a host-side response
timeout, and exposes `status`, `load <image.spui>`, `start <budget>`, `result`, and a `session` mode that runs
a frozen JSON script and writes every byte sent and received with timestamps. Raw termios, no new dependency.
Expected records are **never** computed by this tool: the session checker compares against files produced
beforehand by `psurd_oracle.py` and by `spu_vm`.

## 5. Gates before any board contact

| Gate | Content | Pass criterion |
|---|---|---|
| C0 preflight | Re-check every §2 row against the schematic, the cited constraint files and ledger entries; confirm tool versions (Vivado 2026.1, openFPGALoader, DirtyJTAG probe id); confirm `98c85afd` or later is the source revision | A signed-off table; any disagreement is a HALT |
| C1 host client | Unit tests of the client against the RTL-0B reference model over a pseudo-terminal, including a lost response, a short response and a bad response checksum | All pass; added to the required regression only with owner approval (D6) |
| C2 board simulation (**behavioural**, R1) | `psurd_board_top` with a 50 MHz clock and the real 217 cycles/bit: reset behaviour (held, released, re-asserted mid-run and mid-frame, a pulse shorter than the release count), then the B4 quick set driven through the board top | Records equal the oracle; reset cases match §3; planted mutants (reset polarity, release counter removed, wrong divider) are detected. Simulation says nothing about metastability or synchronizer structure |
| C3 synthesis and route | Vivado non-project flow on `psurd_board_top` with `psurd_board.xdc`, default directives, detached job | 0 routing errors; setup, hold, recovery and removal all positive; 0 unconstrained internal endpoints; no latches or black boxes; LUTRAM 256, RAMB36 + RAMB18, DSP 112; **structural checks (R1), fail-closed in the flow:** the raw `rst_n` pad fans out only to the first reset-synchronizer flop; every asynchronous clear/preset pin is driven from the approved reset flops through buffers or inverters only; `uart_rx` fans out only to `rx_s1`, whose only load is `rx_s2`, both `ASYNC_REG` and both on `cpu_clk`; `cpu_clk` is 40.000 ns and reaches every v0.3 flop |
| C4 bitstream | `write_bitstream` as a separate detached job from the C3 checkpoint | Bitstream and checkpoint hashes recorded. **Pin check (R4), from the routed checkpoint before `write_bitstream`:** exactly four placed ports, at M21, H7, F3, E3, all LVCMOS33, with E3 the only output; `BITSTREAM.CONFIG.UNUSEDPIN` is `PULLNONE` (unused pins high-impedance); the job fails if any of these differs |
| C5 session freeze | The physical session script (§6), the expected-record files and the stop rules (§9) are committed before the run. **Host timing is frozen with it (R2):** serial settings, the delay between the SRAM load and the first byte, the per-response timeout, the STATUS polling interval and the maximum poll count, each with its derivation | Owner acceptance of the frozen package. Until then no SRAM load |

**Hold timing is a fresh item in C3.** The RTL-0B figures (+0.032 ns and +0.056 ns across two placements of the
same logic) are not carried forward as a margin. If C3 hold or removal slack is not positive, the plan stops
for review; it does not add ad-hoc delay or retry with other directives without authorization.

## 6. Physical acceptance tests (one frozen session)

All expected values come from `psurd_oracle.py`, cross-checked with `spu_vm`, and are written to files before
the session. Every step records the raw bytes.

| Step | Action | Pass criterion |
|---|---|---|
| P0 | Preflight: bitstream hash, JTAG detect, serial port free, no analyser or pod attached | idcode `0x3631093`; hash equals C4 |
| P1 | One SRAM load | Loader exit 0, `done 1` |
| P2 | STATUS; RESULT; START | STATUS OK with flags `00`, IDLE, cause `FF`, run id 0; RESULT REFUSED 10; START REFUSED 8 |
| P3 | Load program 1 (`SLIK 0,7; HALT`) | Every load frame OK; STATUS shows image-valid = 1 |
| P4 | START, poll, RESULT | 213 bytes, record CRC valid, equal to the oracle and to `spu_vm` byte for byte |
| P5 | Exact arithmetic: the six Program A cases and Program B with K = 33 and 34 (near-cancelling sign tests), each loaded and run | Each record equals the oracle |
| P6 | Repetition: START five times on one image; then a different program without reconfiguration | Five identical records; run id increments by one per accepted START; the second program's record equals the oracle |
| P7 | Failure handling: an image with a wrong CRC; a header with revision `0x02`; START with B = 0; a long run (`BR AL 0`, large budget) with STATUS, START, LOAD_BEGIN and RESULT sent during it; a frame with a bad checksum; a truncated frame | REFUSED 4 and REFUSED 2 with image-valid = 0, START then REFUSED 8, the earlier record still readable; REFUSED 9; BUSY for START, LOAD_BEGIN and RESULT with STATUS reporting RUNNING, then a BUDGET record equal to the oracle; BAD_FRAME; TIMEOUT; a valid STATUS accepted after each error |
| P8 | Reset recovery: one KEY0 press by the owner, then STATUS, RESULT, START, then program 1 again | STATUS as in P2; RESULT and START refused; the reloaded program's record equals P4 |

**P7 budget (R3).** The long run must outlast the four commands sent during it. The budget is derived, not
chosen: (bytes of those four frames and their responses at 115,200 baud, from the protocol) + (the frozen host
timeouts and inter-command delays of R2), times a stated safety factor, divided by the cycles per `BR AL 0`
iteration measured in the C2 simulation at 25 MHz. The derivation and the resulting value are part of C5. The
session also sends a final STATUS during the run, so that a run that ended early is detected, not assumed.

**What a PASS would and would not establish.** It would be a single-session silicon observation of one
bitstream on one board. It would not qualify the UART interface, timing margin, electrical behaviour, the
device grade or behaviour across reloads, resets beyond the one in P8, temperature or supply.

## 7. Programming procedure and safety

1. The board boots an unidentified design from flash. Nothing is attached to KEY0, J11 or any header for this
   session; the only connections are USB power, the DirtyJTAG probe and the CH340 USB-UART.
2. Exactly one `openFPGALoader -c dirtyJtag --freq 1000000 <bit>` per load attempt. **No flash option is ever
   passed**; a power cycle returns the board to its flash design.
3. The bitstream assigns four pins, all LVCMOS33 on pins already used at 3.3 V in the ledger. No pin is driven
   except E3.
4. Load attempts are a bounded campaign (D7). A consumed attempt is consumed whether it passes, fails or the
   session is abandoned.
5. Evidence goes to `build/psurd-rtl0c/<step>/` with a hash manifest. A ledger entry (§3.53) is drafted as a
   review copy; no "silicon" wording is used anywhere until the owner accepts that entry.

## 8. Decisions (all approved 2026-11-12)

| # | Decision | Approved choice |
|---|---|---|
| D1 | Clocking | Divide-by-two flop into a BUFG, as the Gen-1 board top. No MMCM/PLL in the first image |
| D2 | Reset | KEY0 active low through the Gen-1 conditioning chain into `psurd_sys_top.rst`; no power-on reset generator beyond it |
| D3 | Pins and standards | M21, H7, F3, E3, all LVCMOS33; no LEDs; status outputs unconnected |
| D4 | Tool flow | Vivado 2026.1 non-project route, then a separate `write_bitstream` job, both detached; default directives only |
| D5 | Configuration | SRAM load only through DirtyJTAG at 1 MHz; no flash |
| D6 | Host client | New `tools/psurd_uart_host.py` with tests; add the tests to the required regression |
| D7 | Campaign budget | One bitstream; at most three SRAM load attempts; one frozen session per load; C3 route at most two attempts, 7200 s each |
| D8 | Reset in P8 | Owner presses KEY0 by hand (owner-reported), as in ledger §3.46. The instrumented Pico 2 pulse setup is not attached for this first session |

**Refinements attached to the approval.** R1: behavioural reset tests (C2) are reported separately from
structural synchronizer verification (C3). R2: host timeouts, polling intervals and startup delays are frozen
in C5. R3: the P7 budget is derived from UART transmission and simulated execution timing. R4: the
bitstream's pin assignments and unused-pin behaviour are verified explicitly (C4).

## 9. Stop rules

- A disagreement in C0, a C2 failure that points at `psurd_sys_top` or below, or non-positive C3 timing is a
  **HALT for review**, not a prompt to change frozen or qualified RTL.
- In the physical session, the first failed step ends the session. Later steps are not attempted "for
  information" unless the frozen script says so.
- No response at P2 is a result (recorded as FAIL at P2), not a reason to reload, change baud or edit the
  script. Diagnosis is a separately authorized step.
- Budget exhaustion is a terminal result (AGENTS.md §4.2).

## 10. Risks

- **Hold and removal margin.** Thin in every out-of-context route so far; the board top adds a generated clock
  and a reset synchronizer. C3 measures it afresh.
- **First silicon use of this reset release into v0.3 logic.** The 25 MHz release synchronizer has Gen-1
  observations only (ledger §3.42, §3.48, §3.52).
- **Asynchronous UART receive.** The synchronizer is now marked `ASYNC_REG`; that supports placement and
  analysis and does not guarantee reception. Only nominal-rate traffic from one bridge is tested.
- **Device grade not physically verified.** Timing is analysed for speed grade -1, the slowest.
- **Host-side lost-response ambiguity.** The protocol has no sequence number; the client treats a missing
  response as a failure and never retries a START or a load frame silently.
