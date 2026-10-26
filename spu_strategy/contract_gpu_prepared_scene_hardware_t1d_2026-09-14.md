# Engineering Contract: Wukong GPU Prepared-Scene Physical UART Integration (T1d)

**Date:** 2026-09-14  
**Contract ID:** `contract_gpu_prepared_scene_hardware_t1d_2026-09-14.md`  
**Revision:** 4 — incorporates third pre-execution review of 2026-09-15  
**Status:** **ACTIVE — Stage A COMPLETE; Stage B COMPLETE; Stage C HALT. Stage C requires a separate owner authorization and does not inherit Stage B authorization.**
**Target:** Wukong Artix-7 `xc7a100tfgg676-1` GPU/VGA configuration; 50 MHz `sys_clk`, 25 MHz `clk_pixel`  
**Configuration under test:** a new, uniquely named T1d hardware mode guaranteeing `PREPARED_SCENE=1`, `COST_STIMULUS=0`, and physical CH340 UART RX

### Revision 4 review-resolution ledger

| Review finding | Revision 4 disposition |
|---|---|
| Authorization deadlock | Replaced single authorization with separately signed Stages A, B, and C |
| Wrong VGAFIX XDC | Corrected target to `spu_a7_vga_fix.xdc`; legacy XDC is inspection-only |
| Contradictory truncation indices | Replaced byte indices with exact accepted-byte counts 1, 2, 33, and 63 |
| Undefined safety-property names | Replaced with scoped definitions over `receiving`, `payload_count`, `commit_pending`, and `activate_scene` |
| Vacuous cost-LFSR assertion | Removed from assertions; retained as elaborated-hierarchy/netlist absence inspection |
| Clock declaration overstatement | Requires constrained `sys_clk` and routed recognition/analysis of both clock domains |
| Unmeasurable physical latency | Sender must drain, wait 100 ms, then check presence; no latency claim |
| Missing B0 artifact mechanism | Added naming-only `A7_ARTIFACT_TAG=T1D_B0_S1` mechanism for canonical B0 |
| Incomplete symmetric reset semantics | Both assertion and deassertion transitions now require 65,536 mismatch edges plus three pixel stages |
| Ambiguous primitive scope | Halt condition narrowed to extra scene primitives |

## 0. Decision this contract exists to make

Determine whether one frozen, error-free controlled-link transaction can enter the Wukong through its onboard CH340 UART path, populate the already-selected prepared-scene state, become active only at `frame_start`, and produce the predetermined GPU image on real hardware.

The transaction is exactly 64 wire bytes:

```text
wire transaction = 0xA5 start byte || 63 payload bytes
payload          = 63 bytes = 504 bits
```

The 63-byte payload and 64-byte wire transaction are distinct frozen fixtures and must never be described interchangeably.

This is an integration and silicon-bring-up tranche. It does not redesign the scene format, GPU, rasterizer, memory system, ISA, or host protocol.

The result must be classified as exactly one of:

- **PASS:** the frozen controlled-link transaction is loaded and activated atomically on hardware, its output matches the frozen reference, all required verification passes, and the routed design meets both ratified clocks without timing exceptions.
- **FAIL:** a completed experiment demonstrates a specified functional, timing, CDC, reset, protocol, or hardware mismatch.
- **INCONCLUSIVE:** the experiment cannot be completed or interpreted because a prerequisite, tool, connection, observation method, or frozen reference is missing.

No result from synthesis alone may be called hardware proof.

## 1. Grounding and inherited decisions

This contract depends on, but does not reopen, the following project decisions and evidence:

1. `spu_strategy/contract_graphics_first_priority_2026-09-04.md` establishes graphics-first priority but does not authorize this implementation.
2. `spu_strategy/contract_gpu_pipeline_tranche_2026-09-06.md` remains a draft rev 5 and must not be treated as blanket authorization.
3. `spu_strategy/contract_gpu_uart_scene_loader_t1a_2026-09-11.md` defines a loader that consumes `0xA5` followed by a 63-byte/504-bit payload. T1a is complete in simulation and does not itself provide physical UART ingress or GPU integration.
4. `spu_strategy/contract_gpu_prepared_scene_t1b_2026-09-11.md` selects B1 atomic activation. That architecture is inherited unchanged.
5. T1c prepared-state banking is recorded as closed PASS in `docs/archive/bench_sessions/WUKONG_GPU_CHECKPOINT_2026-09-11.md`. This contract integrates that implementation; it does not replace it.
6. `spu_strategy/contract_wukong_gpu_prepared_cost_2026-09-13.md` and its completed PS0/PS1 evidence provide cost baselines. The stale prepared-cost terminal text in that contract and `docs/archive/bench_sessions/WUKONG_GPU_CHECKPOINT_2026-09-11.md` must both be reconciled during Stage A without rewriting the historical initial failure.
7. The existing `spu_a7_vga_top`/VGAFIX image is the known-good board, monitor, pinout, clock, sync, colour-channel, and harness test.
8. The canonical `spu_a7_gpu_vga_top` configuration with prepared scene disabled and cost stimulus disabled is the known hardcoded red/green two-triangle GPU test.
9. UART receive through the onboard CH340 on F3 is separately silicon-verified at 115200 8N1 by the 20/20-byte echo and zero-stray-byte negative control in `docs/hardware_evidence.md` Section 3.11.
10. `docs/BENCH_ELECTRICAL_SAFETY.md` Part 4 requires removal of the programmer after loading. It does not currently require monitor disconnection. The monitor-disconnect/reconnect rule used by T1d is therefore frozen locally in Section 9.1 of this contract and must not be misattributed to the safety document.

If inspection shows that any inherited interface differs from the description above, HALT and amend this contract before editing RTL.

## 2. Staged authorization and mandatory reconciliation

This contract has three independent authorization gates. Completion of one stage returns the tranche to **HALT** for evidence review. No authorization carries into the next stage.

### 2.1 Stage A — preparation and integration

Stage A may authorize only documentation, fixture/oracle creation, scoped RTL and build-flow integration, and the focused tests in Sections 7.2 items 1-10. It authorizes no repository-wide regression, synthesis/P&R build, packing, bitstream use, programming, or physical operation.

Stage A deliverables are:

- [ ] Add this contract under `spu_strategy/` and preserve its staged gates.
- [ ] Correct comments in `hardware/boards/artix7/spu_a7_vga_fix.xdc` and `hardware/boards/artix7/spu_a7_gpu_vga.xdc` without changing the already-correct constraints. Inspect legacy `hardware/boards/artix7/spu_a7_vga.xdc`; correct it only if the same stale comments exist there. Freeze the measured mapping exactly as:
  - J10-1 / D5: HSYNC
  - J10-2 / G5: BLUE
  - J10-3 / G7: GREEN
  - J10-4 / G8: RED
  - J10-7 / E5: VSYNC
- [ ] Reconcile the completed PS0/PS1 result in both `spu_strategy/contract_wukong_gpu_prepared_cost_2026-09-13.md` and the stale prepared-cost entry at `docs/archive/bench_sessions/WUKONG_GPU_CHECKPOINT_2026-09-11.md:78`, preserving the historical initial failure.
- [ ] Confirm that the repository contains the exact T1a, T1b/B1, and T1c artifacts referenced in Section 1.
- [ ] Create and freeze the Section 5 payload, wire transaction, decoded reference, diagnostic pixels, oracle, and hashes.
- [ ] Add `GPU_T1D_UART=1` as the B1 functional selector. It must elaborate `PREPARED_SCENE=1`, `COST_STIMULUS=0`, and physical UART RX enabled.
- [ ] Add `A7_ARTIFACT_TAG` as a naming-only mechanism. `A7_ARTIFACT_TAG=T1D_B0_S1` must change only output paths/names and must leave the canonical B0 elaboration unchanged. B1 uses `A7_ARTIFACT_TAG=T1D_B1_S1` together with `GPU_T1D_UART=1`.
- [ ] Ensure both tags produce unique T1d artifacts and cannot overwrite canonical GPUVGA or PS0/PS1 evidence.
- [ ] Implement the bounded same-domain UART/T1c integration and focused self-checking tests, without widening T1a or T1c.
- [ ] Record the exact inherited regression and B0/B1 commands proposed for Stage B, but do not run them.
- [ ] End on one clean commit and record its SHA, focused-test commands/results, fixture hashes, decoded reference, hierarchy, reset semantics, and all Stage B commands/timeouts.

Any Stage A scope expansion or failed focused test ends Stage A at HALT. Stage A evidence must be reviewed before Stage B authorization.

### 2.2 Stage B — build qualification

Stage B is build qualification only. It may be authorized only after Stage A
closes with a reviewed clean SHA and completed Stage B fields in Section 13. It
authorizes exactly one repository regression/gate and the matched B0/B1
synthesis/P&R jobs in Section 8.1, including timing/utilization reports,
bitstream generation, and bitstream provenance only where those frozen jobs
normally produce them. It authorizes no programming or other physical
operation.

Stage B must produce the regression result, matched resource/timing reports, unique artifacts, and eligible bitstream hashes. Completion, failure, timeout, or tool error returns the tranche to HALT for review before Stage C.

### 2.3 Stage C — hardware execution

Stage C is hardware execution only. It may be authorized only after Stage B
passes its contracted gates and Section 13 freezes the exact eligible hashes,
programming/recovery commands, sender command, serial-drain behavior, reset
procedure, observation procedure, and equipment identities.

Stage C authorizes only the Section 9 sequence:

1. VGAFIX colour bars and moving liveness marker.
2. Canonical `_T1D_B0_S1` hardcoded triangles.
3. Candidate `_T1D_B1_S1` default black/unarmed state.
4. Five controlled UART attempts using the one frozen wire transaction.

It authorizes no RTL, fixture, command, constraint, frequency, scene, or protocol change.

Review-observed repository state at `e62c7e3bc1704b4527b855e083b3e94e8b9b671d` was not eligible for Stage A closure or Stage B authorization: GPU cost-flow files were dirty, no T1d contract existed under `spu_strategy/`, and both prepared-cost records required reconciliation. Re-inspect rather than assuming this state remains current.

Failure of the existing VGAFIX or canonical GPUVGA image is outside this contract. Repair the harness, clock, constraints, or existing GPU path first.

## 3. Scope

### 3.1 In scope

- The existing onboard CH340 receive path through F3 (`LVCMOS33`, pull-up), using 115200 baud, 8N1, idle high, LSB first.
- The existing `spu_uart_rx`, proposed to run on `clk_pixel` at 25 MHz and feed T1a in that same domain, subject to owner ratification and timing inspection.
- One exact controlled-link transaction: `0xA5` followed by the frozen T1a 63-byte payload.
- Connection of a successfully completed T1a transaction to T1c's inactive prepared-state bank.
- B1/T1c pending-state and frame-boundary atomic activation.
- A board-top configuration with prepared scene enabled and cost stimulus structurally disabled.
- One frozen deterministic scene, exact packet bytes, decoded-state reference, and expected image evidence.
- Simulation of the frozen error-free UART transaction, reset behavior, incomplete-transaction non-activation, same-domain connectivity, and exact frame-boundary activation.
- Matched synthesis and place-and-route against the canonical and prepared-cost evidence.
- One bounded Wukong programming and scene-loading procedure.
- Evidence and documentation needed to classify the tranche.

### 3.2 Explicitly out of scope

- Any framebuffer, frame store, tile buffer, scanout memory, DDR/SDRAM controller, or memory arbitration work.
- Changes to rasterization, depth, shading, reciprocal, fragment, Quadray, coordinate-conversion, or display algorithms.
- More triangles, new scene fields, packet-format redesign, compression, generalized command streaming, DMA, or multiple queued scenes.
- Bidirectional UART, external UART adapters, RP2350/Pico transport, USB protocol changes, networking, host GUI, dynamic baud negotiation, or production transport design.
- CRC, checksum, length field, timeout, abort, packet rejection, dropped-byte recovery, resynchronization, or any other T1a protocol redesign.
- CPU/ISA integration, D4/E8/root-reflection work, geometric-LLM work, or any other SPU extension.
- PS1's LFSR/cost stimulus as a visible or programmable hardware image.
- Timing waivers, false-path declarations, or multicycle constraints added merely to obtain a passing report.
- Opportunistic cleanup unrelated to the concrete physical prepared-scene path.

### 3.3 Controlled-link limitation

T1d makes no transport-robustness claim. T1a has no checksum, length field, timeout, abort, payload validation, or rejection mechanism. After accepting `0xA5`, it waits until all 63 payload bytes arrive. Arbitrary payload bytes are valid, and a dropped byte can misalign later data.

Accordingly:

- T1d sends only one frozen error-free 64-byte transaction per controlled attempt.
- A truncated transaction is expected to remain incomplete until reset.
- No second transaction may follow a truncated or framing-failed attempt without resetting the candidate image.
- Invalid-packet and automatic-recovery tests are prohibited because those semantics do not exist.
- Adding recovery or integrity protection requires a separate T1a protocol contract.

An out-of-scope requirement is a new contract, not an amendment made during implementation.

## 4. Frozen physical and protocol parameters

Stage A must complete this table from the board schematic, constraints, T1a contract, and existing host tooling; the completed values are reviewed before Stage B authorization. Values must not be inferred from comments alone.

| Parameter | Ratified value | Evidence source |
|---|---:|---|
| FPGA board and device | Wukong / `xc7a100tfgg676-1` | `hardware/boards/artix7/spu_a7_gpu_vga_t1d.xdc` + board evidence |
| Physical UART path | Onboard CH340 | `docs/hardware_evidence.md` Section 3.11 |
| FPGA input pin for UART RX | F3 | constraints + hardware evidence Section 3.11 |
| FPGA I/O standard | LVCMOS33 with pull-up | constraints + hardware evidence Section 3.11 |
| UART receiver clock | `clk_pixel` at 25 MHz | board top + elaborated hierarchy `[STAGE A FREEZE]` |
| UART divisor | `BIT_CYCLES=217` | receiver elaboration `[STAGE A FREEZE]` |
| Calculated baud | approximately 115207.4 baud; +0.0064% versus 115200 | `25,000,000 / 217` |
| Byte/T1a clock domain | Same `clk_pixel` domain; no byte/pulse CDC | board top + elaborated hierarchy `[STAGE A FREEZE]` |
| Physical oscillator / `sys_clk` | 50 MHz | board constraint |
| GPU/video `clk_pixel` | 25 MHz | generated-clock design |
| VGA harness mapping | J10-1/G8 -> RED/DE-15-1; J10-2/G7 -> GREEN/DE-15-2; J10-3/G5 -> BLUE/DE-15-3; J10-4/D5 -> HSYNC/DE-15-13; J10-10/E5 -> VSYNC/DE-15-14; J10-7/G6 unused | measured FPGA-pad-to-DE-15 evidence + frozen XDC harness comments |
| Baud rate | 115200 | hardware evidence Section 3.11 |
| Serial framing | 8 data bits, no parity, 1 stop bit; idle high; LSB first | existing `spu_uart_rx` + evidence |
| Accepted baud/phase tolerance | **Not claimed.** Simulation sweeps only the frozen test points in Section 7.2 and does not establish a general tolerance envelope. | receiver design/test |
| Start byte | `0xA5` | T1a |
| Payload length | 63 bytes / 504 bits | T1a |
| Wire-transaction length | 64 bytes: `A5 || payload[0..62]` | T1a |
| Payload validation | None; every 63-byte payload is accepted | T1a |
| Checksum/CRC/length field | None | T1a |
| Inter-byte timeout/abort/recovery | None; incomplete transaction waits until reset | T1a |
| Behavior while activation is pending | Stage A must copy the exact B1/T1c `commit_pending` set/hold/clear rule and its hierarchy here before focused tests. | T1b/T1c |
| Reset effect | Clear both banks; select bank 0; clear pending/preparation state; leave prepared renderer unarmed | T1c RTL/tests |
| Default display after reset | Stable black with valid VGA sync | T1c architecture |
| Physical reset semantics | The debounced reset state changes in either direction only after the physical input continuously disagrees with the current debounced state for 65,536 qualifying `sys_clk` rising edges (approximately 1.31072 ms at 50 MHz). The new debounced assertion or deassertion state reaches the pixel-domain reset on the third `clk_pixel` rising edge that samples that new state. Assertion sampling is disabled during the mismatch interval and first two propagation edges; required state is evaluated immediately after the third pixel edge. | `hardware/boards/artix7/spu_a7_gpu_vga_top.v:35` + debounce RTL `[STAGE A FREEZE EXACT POLARITY]` |
| Reset assertion/deassertion polarity | `[STAGE A FREEZE EXACT SIGNAL POLARITY AND SYNCHRONIZER DIRECTION]` | board top + RTL |
| Activation event | The internal `spu_gpu_top` `frame_start` at `hardware/rtl/gpu/spu_gpu_top.v:170`; not the separate board-top timing pulse used by the canonical setup | T1c/GPU RTL |

T1d uses the onboard CH340. It introduces no external TX jumper, external UART adapter, or adapter power connection. Any future RP2350/Pico sender is a separate integration contract.

### 4.1 Exact `sys_clk` to `clk_pixel` timing model

The board wrapper has one external clock and one derived synchronous clock:

- `sys_clk` is the M21 oscillator input at 50 MHz, with a 20 ns period.
- `clk_div` initializes low and toggles on every rising `sys_clk` edge.
- `clk_pixel` is the output of `BUFG` driven by `clk_div`; its rising edges
  occur on every second `sys_clk` edge, so its cycle period is 40 ns / 25 MHz.
- The BUFG contributes implementation delay but does not change the exact
  divide-by-two edge relationship. No independent phase or duty-cycle claim
  is made beyond the routed clock report.
- All T1d UART, video timing, loader, prepared-state, and GPU logic is clocked
  by `clk_pixel`. The UART input pad is synchronized inside `spu_uart_rx`;
  there is no byte or pulse CDC between `sys_clk` and `clk_pixel`.
- The reset debounce is clocked by `sys_clk`; its debounced state crosses into
  the pixel domain through the three-stage `pix_rst_sync` chain.

The executable model is `software/tests/test_gpu_t1d_clock_model.py`. It checks
the divider edge sequence, 50-to-25 MHz ratio, 217-cycle UART divisor,
receiver clock-domain binding, reset synchronizer anchor, and the frozen VGA
pad mapping. This model is a structural/arithmetic contract check; it is not
a substitute for routed timing evidence.

## 5. Frozen scene and oracle

Stage A may create exactly one scene. It must be visually diagnostic and exercise the already-implemented prepared-state and depth behavior without extending the architecture.

During Stage A, create and commit the following immutable fixtures before using them in focused tests:

- `fixtures/[STAGE_A_FREEZE]_scene_payload_63b.bin` — exactly 63 payload bytes; contains no start byte.
- `fixtures/[STAGE_A_FREEZE]_scene_wire_64b.bin` — exactly `0xA5 || scene_payload_63b.bin`.
- `fixtures/[STAGE_A_FREEZE]_scene_wire_64b.hex` — human-reviewable byte-for-byte rendering of the complete wire transaction.
- `fixtures/[STAGE_A_FREEZE]_scene_decoded.json` or equivalent — expected decoded fields using the existing T1a field names.
- `fixtures/[STAGE_A_FREEZE]_scene_reference.*` — deterministic reference produced independently of the new physical UART wrapper where practical.

Record:

| Fixture | Size | SHA-256 | Producer |
|---|---:|---|---|
| Binary payload | 63 bytes | `[STAGE A FREEZE]` | `[tool + command]` |
| Binary wire transaction | 64 bytes; byte 0 must be `A5` | `[STAGE A FREEZE]` | `[tool + command]` |
| Wire hex rendering | 64 bytes | `[STAGE A FREEZE]` | `[tool + command]` |
| Decoded state | `[STAGE A FREEZE]` | `[STAGE A FREEZE]` | `[oracle + command]` |
| Reference raster/evidence | `[STAGE A FREEZE]` | `[STAGE A FREEZE]` | `[oracle + command]` |

The reference must include exact expected values at a frozen set of diagnostic pixels, including background, each primitive, and any overlap/depth location. If an existing independent software oracle can deterministically produce the whole active raster, also freeze a hash over its defined RGB pixel byte order. Sync and blanking must not be silently included in a pixel hash unless the format explicitly says so.

A monitor photograph is useful hardware evidence but is not the numerical oracle.

## 6. Required architecture

The intended dataflow is:

```text
onboard CH340 -> FPGA F3 RX pad
    -> existing spu_uart_rx on clk_pixel (25 MHz)
    -> synchronous scene_rx_byte + scene_rx_valid
    -> unchanged T1a start-byte + 63-byte payload loader
    -> inactive T1c prepared-state bank
    -> pending-valid state
    -> atomic bank activation at the ratified frame boundary
    -> existing prepared-state GPU pipeline
    -> existing VGA timing/output path
```

### 6.1 UART and CDC rules

- The asynchronous RX pad must not feed protocol/state logic directly.
- The selected minimal architecture runs existing `spu_uart_rx` and T1a on `clk_pixel` at 25 MHz. Owner ratification requires inspection that the receiver's baud divisor/sampling behavior is correct at that clock.
- There must be no byte/pulse CDC in the selected architecture. If inspection instead requires the UART receiver to run on 50 MHz `sys_clk`, HALT: a new explicit byte/pulse CDC design and verification amendment is required before implementation.
- No fabric-generated, gated, or ripple clock may be introduced.
- `sys_clk` must be explicitly constrained. Both `sys_clk` and the derived `clk_pixel` must be recognized and analyzed in the routed report.
- T1d makes no claim about recovery from framing error, a dropped byte, or a truncated transaction. Any such attempt must end in reset before another transaction is sent.

### 6.2 Transaction and activation rules

- Reset clears partial reception, pending activation, and transaction-valid state.
- Reset clears both banks, selects bank 0, clears pending/preparation state, and leaves the prepared renderer unarmed. The required reset/default display is stable black with valid VGA sync.
- Bytes may modify only staging or the inactive bank. They must never modify the active scene directly.
- An incomplete packet must never request activation.
- T1a has no rejection state. A transaction becomes complete after `0xA5` and exactly 63 following payload bytes.
- A complete transaction may create exactly one pending activation according to inherited B1/T1c semantics.
- Active-bank selection may change only on the clock edge satisfying the internal `spu_gpu_top` `frame_start`. The separate board-top timing pulse is not the activation signal and must have a distinct testbench name.
- A bank change on that `frame_start` edge is permitted. The selected bank must then remain stable until the next `frame_start` edge.
- The scene loader always writes the structurally opposite candidate bank (`hardware/rtl/gpu/spu_scene_loader.v:25`). T1d defines no source/destination alias mode and requires no alias test.
- Reset or error during a partial transaction must not expose partially written scene state.

### 6.3 Build-configuration rules

- Prepared-scene functionality must be enabled through the existing configuration mechanism.
- `COST_STIMULUS` must be explicitly zero/disabled.
- The LFSR cost stimulus must not drive `scene_rx_byte`, `scene_rx_valid`, scene state, or any output in the programmable image.
- The physical UART path must be traceable from the constraints pin through the receiver to the unchanged T1a interface.
- The new `GPU_T1D_UART=1` hardware-mode selector must guarantee `PREPARED_SCENE=1`, `COST_STIMULUS=0`, and physical CH340 RX. The current behavior in which `GPU_PREPARED_SCENE=1` forces cost stimulus is not eligible.
- `A7_ARTIFACT_TAG=T1D_B0_S1` is the naming-only mechanism for B0. It must not alter sources, parameters, constraints, defines, hierarchy, or elaboration relative to canonical GPUVGA.
- B1 uses `GPU_T1D_UART=1 A7_ARTIFACT_TAG=T1D_B1_S1`.
- Both T1d outputs must use the exact `_T1D_B0_S1` and `_T1D_B1_S1` artifact/directory prefixes and must not overwrite canonical GPUVGA, PS0, or PS1 artifacts.
- The existing canonical hardcoded GPU configuration must remain buildable and behaviorally unchanged.

## 7. Required verification

### 7.1 Static inspection

Before simulation, record:

- exact modules and ports at every edge of the Section 6 dataflow;
- every clock and reset domain;
- synchronizer or asynchronous-FIFO structure;
- active/inactive bank ownership;
- all writers of active-bank select, `commit_pending`, `activate_scene`, `receiving`, `payload_count`, `scene_rx_byte`, and `scene_rx_valid`;
- proof by elaborated hierarchy or synthesis netlist that the candidate image has no cost-stimulus driver.

Multiple unexpected writers, an undocumented clock crossing, or disagreement with B1/T1c is an immediate HALT.

### 7.2 Simulation matrix

At minimum, automated tests must cover:

1. Reset with no UART traffic: stable black output with valid VGA sync, both banks cleared, bank 0 selected, renderer unarmed, and no pending activation.
2. One exact frozen wire transaction: `0xA5` is consumed as the start byte and all 63 payload bytes/504 bits decode correctly.
3. UART waveform reception through `spu_uart_rx`, not merely direct byte/valid injection, for all 64 wire bytes.
4. UART start phase swept across the exact sampling-clock phase offsets `[STAGE A FREEZE OFFSETS]`.
5. No general baud-tolerance test or claim. The testbench uses the frozen 115200-baud waveform against the 25 MHz, `BIT_CYCLES=217` receiver.
6. Incomplete transactions stopped after exact accepted-byte counts: 1 byte (start only), 2 bytes (start plus one payload byte), 33 bytes (start plus 32 payload bytes), and 63 bytes (start plus 62 payload bytes, one byte short). Each case must produce no activation and remain incomplete until reset. Receiving all 64 bytes is the separate completion case.
7. Reset during reception at representative early, middle, and final-payload positions; afterward the Section 4 reset state is restored.
8. A complete controlled transaction finishing at multiple positions relative to `frame_start`.
9. Atomic transition: a bank change may occur on `frame_start`, and the selected bank then remains stable until the following `frame_start`; no mixed frame is permitted.
10. One exact transaction after reset for every attempt. Back-to-back, malformed, framing-error, dropped-byte, timeout, and recovery behavior are not tested or claimed.
11. Existing T1a, T1b/T1c, GPU, video-timing, depth, UART-RX, and board-top regressions.

Tests must use self-checking assertions or exact comparisons. Waveform inspection alone is insufficient.

### 7.3 Required safety properties

Encode as assertions where supported, otherwise as self-checking testbench invariants:

Stage A must bind the following definitions to the inspected hierarchy; these are testbench expressions, not claimed RTL signal names:

- `start_accept := scene_rx_valid && !receiving && (scene_rx_byte == 8'hA5)` sampled before the accepting edge.
- `final_payload_accept := scene_rx_valid && receiving && (payload_count == 6'd62)` sampled before the accepting edge. This is acceptance of payload byte 62, the 63rd payload byte and wire byte 63.
- `partial_window` begins immediately after `start_accept`, remains active while the actual loader `receiving` state awaits payload completion, and ends only on `final_payload_accept` or reset.
- The pending state is the actual T1c `commit_pending`; the activation event is the actual `activate_scene`; the activation boundary is the internal `spu_gpu_top` frame-start signal bound as `gpu_frame_start_internal`.

Required properties:

- From a clean reset, throughout `partial_window`, `commit_pending==0`, `activate_scene==0`, and `active_bank` and active-scene state remain unchanged.
- Before `final_payload_accept`, the current transaction cannot set `commit_pending` or assert `activate_scene`.
- If `active_bank` changes after an edge, the pre-edge values satisfied `activate_scene && gpu_frame_start_internal && commit_pending`: `active_bank != $past(active_bank) -> $past(activate_scene && gpu_frame_start_internal && commit_pending)`. Adapt syntax without changing the pre-edge meaning.
- After an activation edge, `active_bank` remains stable until the next internal `gpu_frame_start_internal` edge.
- For physical assertion and deassertion separately, the reset test models 65,536 continuous-mismatch `sys_clk` rising edges plus all three `clk_pixel` propagation edges. Sampling is disabled during that transition region. Immediately after the third pixel edge, the expected asserted or deasserted reset state must be present. After completed reset assertion, `commit_pending==0`, both banks are cleared, bank 0 is selected, and the renderer is unarmed.

Absence of the cost LFSR belongs only to the non-vacuous elaborated-hierarchy/netlist inspection in Section 7.1; no assertion may be written against logic that should not exist.

## 8. Matched synthesis and place-and-route

This section is executable only under Stage B authorization. Run canonical and candidate builds from the same Stage A clean commit, oss-cad-suite version, device database, shared clock/reset/VGA constraints, frequency targets, and seed. B1 necessarily adds the F3 UART RX constraint because B0 has no UART port; F3 must be the sole candidate-only constraint addition. Record exact detached-job commands rather than paraphrasing them.

Required builds:

1. **`_T1D_B0_S1` — canonical GPUVGA:** prepared scene disabled/unset; cost stimulus disabled; `A7_ARTIFACT_TAG=T1D_B0_S1` changes naming only.
2. **`_T1D_B1_S1` — prepared CH340 UART candidate:** `GPU_T1D_UART=1 A7_ARTIFACT_TAG=T1D_B1_S1` guarantees prepared scene enabled, physical F3 UART ingress enabled, cost stimulus disabled, and unique naming.

### 8.1 Frozen detached jobs and campaign budget

The commands below are the proposed Stage B commands. They are executable only
after the Stage B pre-execution review in Section 13.2a is resolved and the
owner changes the Stage B decision from `HALT` to `AUTHORIZE`. The detached
runner records the source commit and dirty-tree state; a dirty root worktree is
not an acceptable substitute for the frozen source checkout.

| Job | Exact command | Attempts | Per-job timeout | Required artifact prefix |
|---|---|---:|---:|---|
| Repository gate | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/stage_b_gate_01 --timeout 3600 --notify-desktop -- bash tools/verify_repo.sh` | 1 | `3600 s` | `_T1D_GATE_S1` |
| B0 canonical build | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/b0_s1_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 A7_ARTIFACT_TAG=T1D_B0_S1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all` | 1 | `7200 s` | `_T1D_B0_S1` |
| B1 candidate build | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/b1_s1_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 A7_ARTIFACT_TAG=T1D_B1_S1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all` | 1 | `7200 s` | `_T1D_B1_S1` |

**Cumulative Stage B wall-clock budget:** `18,000 s`
**Retry budget:** zero unless a new owner authorization names the exact failed job and correction.  
**Parallel builds:** prohibited unless the existing flow proves output directories and caches are isolated.

A timeout or infrastructure failure produces INCONCLUSIVE for that job. It does not authorize a changed command, seed, frequency, or second attempt.

For both builds record:

- git commit and dirty-tree status;
- complete build command and environment overrides;
- tool and chip-database versions;
- LUT, FF, distributed RAM, BRAM18/36, DSP48E1, clock-buffer, and I/O utilization;
- routed setup results for each reported domain;
- achieved/estimated Fmax for every declared clock;
- critical-path startpoint, endpoint, delay, and logic/routing split;
- timing warnings emitted by the frozen flow;
- bitstream SHA-256 if and only if the build is eligible for programming.

The candidate passes the timing evidence available from the pinned nextpnr-xilinx flow only if final routed setup/Fmax reporting establishes both of the following:

- `sys_clk` routed Fmax is at least 50 MHz.
- `clk_pixel` routed Fmax is at least 25 MHz.

The flow's current global `--freq 25` labelling is not sufficient evidence for the 50 MHz `sys_clk` requirement; both reported domains must be interpreted and recorded separately. `--timing-allow-fail` may be used diagnostically but cannot make a bitstream eligible for programming.

The existing pinned reports contain neither an explicit hold analysis nor an unconstrained-path count. T1d therefore makes no `clean hold` or `zero unexplained unconstrained paths` claim, and neither is a PASS gate. Adding either gate requires a separately frozen analysis command, tool version, interpretation rule, and expected output before authorization; it must not be inferred from silence in nextpnr output.

No resource or frequency advantage is claimed by this tranche. Deltas are reported as measurements.

## 9. Bounded hardware procedure

This section is executable only under Stage C authorization after reviewed Stage B success.

### 9.1 T1d-local programming safety rule

For every programming operation in this tranche:

1. Power and UART transmission must be idle.
2. Disconnect the monitor from the VGA harness before programming.
3. Load the exact frozen image.
4. Remove DirtyJTAG/programmer hardware as required by `docs/BENCH_ELECTRICAL_SAFETY.md` Part 4.
5. Only then reconnect the monitor.

The monitor-disconnection rule is contractual T1d procedure, not a quotation from the current safety document.

### 9.2 Frozen reset and observation rules

- **Warm-reset attempts:** stop host transmission; assert the physical board reset continuously for at least 10 ms; release it; wait at least 20 ms; verify stable VGA sync and the defined black/unarmed state; then send the wire fixture exactly once.
- **Cold-boot attempt:** use the Stage C-ratified power-off, power-on, and candidate reload command `[STAGE C FREEZE BOARD-SPECIFIC COLD-BOOT PROCEDURE]`. It must reload the identical candidate bitstream hash if configuration is not retained. After reload, apply Section 9.1, wait `[STAGE C FREEZE STARTUP INTERVAL]`, and verify black/unarmed state before sending.
- **Post-drain observation:** the frozen sender must block until the operating system reports the serial output drained using the Stage A-frozen drain operation (`tcdrain` or an exact reviewed equivalent). After drain returns, the host waits **100 ms**, then the operator records whether the expected image is present. This is a presence-at-observation result, not a measurement of UART completion-to-display latency.
- Each attempt begins from a newly established clean state. A host-port reopen, a delay, or another start byte is not a reset.

1. Record board identity, power source, onboard CH340 port identity, monitor, cable/harness revision, git commit, bitstream hash, and exact host-send command.
2. Apply Section 9.1 and program the known-good VGAFIX image; confirm stable sync, colours, and moving marker.
3. Apply Section 9.1 and program `_T1D_B0_S1`; confirm the hardcoded canonical scene.
4. Apply Section 9.1 and program `_T1D_B1_S1` with the CH340 UART idle.
5. Confirm stable VGA sync and the defined default display: black, with the prepared renderer unarmed.
6. Open the onboard CH340 at 115200 8N1. For attempt 1, send the frozen 64-byte wire fixture (`0xA5 || 63-byte payload`) exactly once with the ratified host command `[STAGE A FREEZE EXACT COMMAND AND DRAIN OPERATION]`; block until serial drain completes, wait 100 ms, then record whether the expected scene is present. Do not type, reconstruct, or send the payload-only fixture.
7. For attempts 2-4, perform the complete warm-reset procedure separately, send and drain the same fixture exactly once, wait 100 ms after drain, and record presence or absence at observation.
8. For attempt 5, perform the complete ratified cold-boot/reload procedure, verify the identical candidate bitstream hash and black/unarmed initial display, send and drain the same fixture exactly once, wait 100 ms after drain, and record presence or absence at observation.
9. Do not perform malformed, truncated, dropped-byte, framing-error, timeout, or invalid-packet hardware tests in T1d. T1a has no safe recovery contract for them.
10. Restore and re-check a known-good image if candidate behavior is unstable or ambiguous, applying Section 9.1.

Do not repeatedly reprogram, alter timing constraints, edit packet bytes, or change UART parameters during this run. Such a change starts a new reviewed experiment.

## 10. Pass criteria

The tranche is **PASS** only when all of the following are true:

- Stages A, B, and C were separately owner-authorized, executed only within scope, halted at their boundaries, and reviewed before the next authorization.
- Static inspection finds no unauthorized data source, clock crossing, bank writer, or scope expansion.
- Every required automated test and inherited regression passes.
- The candidate completes matched PnR with reported `sys_clk` setup/Fmax at least 50 MHz and reported `clk_pixel` setup/Fmax at least 25 MHz. No hold-cleanliness or unconstrained-path-count claim is made by the pinned flow.
- The exact frozen 64-byte controlled-link transaction loads successfully in all five bounded hardware attempts.
- After valid activation, the physical image agrees with the frozen scene description and diagnostic-pixel expectations to the extent observable on the hardware path.
- Simulation confirms that an incomplete transaction does not activate and remains incomplete until reset; no recovery beyond reset is claimed.
- Monitor lock remains stable and the canonical configuration remains unaffected.
- Evidence includes commands, hashes, reports, attempt log, and at least one clearly labelled photograph or capture of the loaded prepared scene.

Atomic frame-boundary activation is principally established by the self-checking integration test unless a hardware capture method already exists. A photograph alone cannot prove absence of a one-frame tear.

## 11. Halt conditions

HALT without widening the tranche if any of the following occurs:

- UART path, receiver clock, baud/framing, reset timing, wire bytes, payload bytes, or `frame_start` behavior cannot be established from authoritative project sources.
- The distinct 63-byte payload and 64-byte wire transaction, or expected decoded scene, cannot be frozen exactly.
- T1a or T1c must be redesigned rather than merely integrated.
- The receiver requires a new clocking architecture or an unreviewed CDC mechanism.
- An incomplete transaction requests activation before reset.
- Any active-bank change occurs away from `frame_start`, or the bank changes again before the next `frame_start`.
- Reported `sys_clk` setup/Fmax fails 50 MHz or reported `clk_pixel` setup/Fmax fails 25 MHz. Hold or unconstrained-path findings become HALT conditions only if a separately ratified analysis method is added before authorization.
- The candidate requires a framebuffer, memory-controller work, packet redesign, extra scene primitives, or unrelated GPU changes beyond the contracted UART input logic and buffering.
- The build includes `COST_STIMULUS=1`, LFSR scene traffic, or PS1's cost-only configuration.
- The canonical ladder fails before candidate programming.
- Hardware output is intermittent or cannot be distinguished from a harness/pinout problem.

Record a FAIL only when the contracted experiment produced interpretable negative evidence. Otherwise record INCONCLUSIVE and identify the missing prerequisite.

## 12. Required closeout evidence

On completion, update or add the appropriate repository evidence records with:

- final classification and one-paragraph decision;
- exact source commit and dirty-tree state;
- hashes of fixtures, reports, bitstreams, and reference artifacts;
- verification commands and pass counts;
- B0/B1 matched resource and timing table;
- onboard CH340/F3 configuration and clock-domain table;
- five-attempt loading log;
- frozen host-send command and separate hashes for the 63-byte payload and 64-byte wire transaction;
- photograph/capture labels that distinguish VGAFIX, canonical GPUVGA, and prepared UART images;
- deviations, limitations, and anything not proved on silicon.

Do not change T1a, T1b, or T1c historical outcomes. Link this T1d result as a new integration layer.

## 13. Staged owner authorization and evidence record

Every stage begins in HALT. A signature authorizes only the named stage and scope. Each stage terminates back at HALT regardless of outcome.

### 13.1 Stage A authorization — preparation and integration only

Complete before any Stage A repository mutation or focused test:

| Field | Ratified value |
|---|---|
| Starting repository HEAD | `e62c7e3bc1704b4527b855e083b3e94e8b9b671d` |
| Starting dirty-tree inventory and disposition | `docs/`, `hardware/boards/artix7/`, and prior prepared-cost evidence were already dirty; preserve unrelated changes and reconcile only the T1d/prepared-cost records in scope |
| Authorized Stage A scope | Section 2.1 only |
| FPGA part | `xc7a100tfgg676-1` |
| Functional selector to implement | `GPU_T1D_UART=1` |
| Naming-only selector to implement | `A7_ARTIFACT_TAG` |
| Required B1 elaboration | `PREPARED_SCENE=1`, `COST_STIMULUS=0`, physical F3 UART RX enabled |
| Stage A wall-clock/tool budget | Focused checks and elaboration only; no synthesis/P&R, repository gate, packing, programming, or hardware |
| Stage A terminal rule | HALT after deliverables, any failed focused test, scope expansion, or budget exhaustion |

**Stage A owner:** John Curley  
**Stage A decision:** `AUTHORIZE`  
**Stage A date:** `2026-09-19`  
**Stage A notes:** `Owner authorization received in session; Pico/RP2350 connection is explicitly out of scope.`

### 13.1a Stage A closeout record — 2026-09-20

Stage A completed on clean implementation commit
`a6c52fa003a1a47ee5ae953c4d2a1658e786f2cb`. The following bounded work was
performed and reviewed; Stage B and Stage C remain unauthorized:

- Added compile-time `GPU_T1D_UART` mode with `PREPARED_SCENE=1`,
  `COST_STIMULUS=0`, and `spu_uart_rx` at 25 MHz / 115200 baud.
- Added `A7_ARTIFACT_TAG` validation and dedicated T1d synthesis/XDC inputs.
- Replaced the loader-only arbitrary `SCENE_A` byte pattern with the existing
  red/green overlapping depth-crossing geometry, and froze its decoded fields,
  exact integer edge/depth oracle, and diagnostic pixels.
- Added the board-top reset/default-state and end-to-end transaction benches.
- Corrected the T1d Yosys manifest to include the HDMI support modules needed
  for hierarchy elaboration, and bound the generic `spu_gpu_top` elaboration to
  `DEVICE="A7"` before the final hierarchy pass. These are elaboration/build
  flow corrections only; no renderer RTL was changed.
- Reconciled the prepared-cost retry result and the stale checkpoint sentence;
  the original D/tool-flow failure remains preserved.
- Corrected the measured VGA mapping comments in the canonical, fixed, and
  legacy XDC files without changing constraints.

Focused results:

| Check | Result |
|---|---|
| `python3 software/tests/test_gpu_t1d_stage_a.py` | PASS: fixture packing, decoded fields, and six diagnostic pixels |
| UART loader waveform bench | PASS: all 64 bytes, accepted-byte boundaries 1/2/33/63, reset interruption, 0/10/20/30 ns start offsets |
| Board reset/default bench | PASS: 65,536-edge deassertion and reassertion windows plus three pixel stages; black/defined-sync/unarmed reset state |
| Board transaction bench | PASS: exact 504-bit candidate, no mid-frame bank change, activation at internal `spu_gpu_top.frame_start` sampling edge |
| T1d Yosys hierarchy-only elaboration | PASS; no synthesis/P&R/packing run |
| `bash -n hardware/boards/artix7/build_a7.sh` | PASS |

Static bindings for the Stage A integration are:

| Contract signal | RTL binding |
|---|---|
| `scene_rx_byte` / `scene_rx_valid` | `spu_a7_gpu_vga_top.t1d_uart_input.u_uart.data` / `.valid` |
| `receiving` | `spu_a7_gpu_vga_top.u_gpu.u_scene_loader.receiving` |
| `payload_count` | `spu_a7_gpu_vga_top.u_gpu.u_scene_loader.payload_count` |
| `active_bank` | `spu_a7_gpu_vga_top.u_gpu.u_scene_loader.active_bank` |
| `commit_pending` | `spu_a7_gpu_vga_top.u_gpu.scene_commit_pending` |
| `activate_scene` | `spu_a7_gpu_vga_top.u_gpu.activate_scene` |
| internal frame boundary | `spu_a7_gpu_vga_top.u_gpu.frame_start` |
| board-top timing pulse (not activation boundary) | `spu_a7_gpu_vga_top.frame_start` |

All listed state and pulses are in `clk_pixel`; `uart_rx` is the only
asynchronous pad and is synchronized by `spu_uart_rx.rx_s1`/`rx_s2`. The
loader writes only the structurally inactive bank. `commit_pending` is set on
accepted payload byte 62, held while the prepared controller captures both
depth results, and cleared only when `activate_scene` is sampled by the loader
at the internal GPU `frame_start` edge. `active_bank` is written only by that
loader activation branch. The T1d candidate has no cost-stimulus generate
branch. Static inspection of `build_a7.sh` shows `A7_ARTIFACT_TAG` affects
only validation, the `_T1D_B0_S1`/`_T1D_B1_S1` artifact suffix, and reporting;
the B0 path selects the unchanged canonical Yosys/XDC inputs.

No repository-wide regression, synthesis/P&R, packing, bitstream loading,
programming, or hardware operation was performed under Stage A. The stage
terminates at **HALT** pending owner review and separate Stage B authorization.

### 13.2 Stage A closeout and Stage B authorization

Stage A closeout evidence:

| Field | Actual evidence |
|---|---|
| Clean Stage A commit | `a6c52fa003a1a47ee5ae953c4d2a1658e786f2cb` |
| Reconciled prepared-cost records | `spu_strategy/contract_wukong_gpu_prepared_cost_2026-09-13.md`; `docs/archive/bench_sessions/WUKONG_GPU_CHECKPOINT_2026-09-11.md` |
| Corrected/inspected VGA XDC files | `spu_a7_vga_fix.xdc`, `spu_a7_gpu_vga.xdc`, and legacy `spu_a7_vga.xdc`; constraints unchanged |
| 63-byte payload path and SHA-256 | `fixtures/gpu_t1d_scene_payload_63b.bin` / `54f9e7d5386ebf12577a4fbda4b2a4f862f935c2d8705a238641ebd9d43aa3d4` |
| 64-byte wire path and SHA-256 | `fixtures/gpu_t1d_scene_wire_64b.bin` / `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| Wire hex rendering and SHA-256 | `fixtures/gpu_t1d_scene_wire_64b.hex` / `80750e10012410bac2d23c96653227cf29233ba90d0c3f1c3df3999af2b4a754` |
| Decoded reference and SHA-256 | `fixtures/gpu_t1d_scene_decoded.json` / `a7e992aa8523c4009bd015db8f3f231ee7f7eab742d17924f3dbc9d14f658874` |
| Raster/reference evidence and SHA-256 | `fixtures/gpu_t1d_scene_reference.json` / `7c48bdeffac97bba871e5c92663168900cb617f8586976e66f09077e11b7f138` |
| Diagnostic pixels | `(10,10)=(0,0,0)` background; `(100,300)=(15,0,0)` triangle 0; `(540,300)=(0,15,0)` triangle 1; `(200,100)=(15,0,0)` overlap/triangle 0 near; `(400,100)=(0,15,0)` overlap/triangle 1 near; `(320,100)=(15,0,0)` equal-depth tie to triangle 0; internal RGB nibbles |
| UART phase offsets | `0 ns`, `10 ns`, `20 ns`, `30 ns` start phases; receiver `BIT_CYCLES=217` at `25 MHz/115200` |
| Focused test commands/results | Fixture PASS; loader waveform PASS; board reset/default PASS; board transaction/frame activation PASS; hierarchy-only PASS; shell syntax PASS |
| Actual hierarchy bindings | `scene_rx_byte/valid=t1d_uart_input.u_uart.data/valid`; `receiving,payload_count,active_bank=u_gpu.u_scene_loader.*`; `commit_pending=u_gpu.scene_commit_pending`; `activate_scene=u_gpu.activate_scene`; internal boundary=`u_gpu.frame_start` |
| Exact B1/T1c `commit_pending` rule | Loader sets on final payload byte, ignores bytes while pending, and clears/toggles bank only when `activate_scene` is sampled at internal `frame_start`; prepared control requires both depth results and the same boundary |
| Reset polarity and symmetric synchronizer interpretation | `rst_n` active-low; `rst_n_db` changes after 65,536 continuous mismatch `sys_clk` edges; `pix_rst_n` propagates after three `clk_pixel` edges; both assertion and deassertion are exercised |
| B0 naming-only proof | `A7_ARTIFACT_TAG` appears only in `build_a7.sh` validation/suffix/reporting; B0 leaves canonical Yosys/XDC selection and source elaboration unchanged |
| Sender command and drain operation | Not authorized or frozen in Stage A; Stage C only |

Complete before Stage B begins:

| Stage B field | Ratified value |
|---|---|
| Frozen source commit | `8095690628d34c3188ba700b0d9a50a7a3147e23` |
| Repository regression/gate command and expected condition | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/stage_b_gate_01 --timeout 3600 --notify-desktop -- bash tools/verify_repo.sh` / exactly one terminal `COMPLETE` with zero failures |
| Repository-gate timeout | `3600 s` |
| B0 command | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/b0_s1_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 A7_ARTIFACT_TAG=T1D_B0_S1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all` |
| B0 timeout | `7200 s` |
| B1 command | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/b1_s1_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 A7_ARTIFACT_TAG=T1D_B1_S1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all` |
| B1 timeout | `7200 s` |
| Cumulative Stage B budget | `18,000 s`; one job at a time; each launch consumes its slot |
| Retry/parallel rule | zero retries; no parallel builds unless already proven isolated |

**Stage B owner:** John Curley  
**Stage B decision:** `COMPLETE`
**Stage B date:** `2026-09-20`
**Stage B notes:** `Repository gate, chipdb generation, matched B0/B1 synthesis/P&R, timing review, utilization capture, and bitstream provenance completed from clean commit d88ee61f. Stage C remains separately unauthorized.`

### 13.2a Stage B pre-execution review — 2026-09-20

The review was performed against HEAD `e27c391d0cb6d5bc68e1002b830213beb0ede2fc`.
No repository gate, synthesis/P&R, packing, programming, or hardware
operation was launched.

| Review question | Finding | Gate disposition |
|---|---|---|
| Repository gate from the frozen source | The requested source commit exists, but the current root worktree is dirty. The dirty set includes `hardware/boards/artix7/synth_a7_gpu_vga.ys`, which directly affects the proposed B0 canonical build, plus other user changes. `run_detached_job.sh` records the dirty state but does not create a clean checkout. | **HALT** until B0/B1 and the repository gate run from an isolated clean checkout/worktree at `e27c391...`. Do not discard the existing changes. |
| Board/device/top-level selection | The proposed builds select `100t` / `xc7a100tfgg676-1`, `GPUVGA`, and `spu_a7_gpu_vga_top`. B1 selects the T1d Yosys manifest and T1d XDC through `GPU_T1D_UART=1`; B0 remains the canonical GPUVGA path. | Pass, subject to the clean-source gate. |
| Clock/reset/UART assumptions | `M21` is the 50 MHz `sys_clk`; the fabric divider produces the 25 MHz pixel clock; `H7` is active-low reset with debounce and three pixel-domain synchronizer stages; B1 receives CH340 TXD on `F3` at 115200 8N1 with `BIT_CYCLES=217`. The UART pad is synchronized by the receiver. | Pass for execution. No general baud-tolerance claim is permitted. |
| VGA observation definition | Stage B has no physical observation. Stage C must later freeze the monitor/analyser, harness, capture method, and diagnostic-pixel interpretation. The current contract has not yet frozen those equipment-specific fields. | Not a Stage B gate; **Stage C remains unauthorized**. |
| PASS / FAIL / INCONCLUSIVE | PASS requires a successful repository gate, both matched builds, eligible artifacts, and independently recorded routed timing for the ratified clocks. FAIL requires a completed specified mismatch. TIMEOUT, unavailable terminal marker, missing artifact, source mismatch, or unresolvable tool failure is INCONCLUSIVE and consumes the attempt. | Pass as a classification rule. |
| Evidence freeze | Each job must retain `command.txt`, `git_commit`, `git_status.txt`, `tool_versions.txt`, logs, reports, result marker, artifact hashes, device/seed/frequency, utilization, timing/warnings, and the exact build outputs. | Pass as a recording rule. |
| Timing/warning interpretation | `build_a7.sh` passes one global `--freq 25`; the T1d XDC declares `sys_clk` but does not declare a generated `clk_pixel` constraint. A B1 success exit or a 25 MHz global label cannot by itself prove both 50 MHz `sys_clk` and 25 MHz `clk_pixel`. Warnings must be preserved; no waiver or timing exception is authorized. | **HALT** if the frozen flow cannot provide separately interpretable evidence for both required domains. |
| Physical connector mapping | Resolved to the measured FPGA-pad-to-DE-15 mapping: `E5` drives VSYNC and the harness uses J10-10/E5; J10-7/G6 is unused. The relevant XDC comments, T1d XDC, contract table, and `docs/SPIpinout.txt` now agree. | Pass. |
| Clean B0 hierarchy | The isolated clean `e27c391` checkout was tested without synthesis/P&R. T1d hierarchy passes, but canonical B0 fails because `synth_a7_gpu_vga.ys` does not read `spu_scene_loader.v`, `spu_scene_unpack.v`, or `spu_prepared_scene_control.v`, which `spu_gpu_top` structurally instantiates. | **HALT** until a minimal post-`e27c391` correction is committed and re-isolated. |

Required minimal corrections before Stage B authorization:

1. Provide an isolated clean checkout/worktree at `e27c391...` without
   deleting or reverting the user's current dirty changes.
2. ~~Resolve the J10 hole-number/E5 contradiction consistently in the contract
   and the relevant XDC comments; do not change the active FPGA pin assignment
   without new board evidence.~~ **Resolved:** freeze J10-10/E5 for VSYNC and
   J10-7/G6 unused, without changing the active FPGA pin assignment.
3. Confirm that the selected flow can report or otherwise deterministically
   interpret both required clock domains. If it cannot, revise the timing gate
   before authorizing an expensive build.
4. Add only the missing prepared-scene source reads to the canonical B0
   synthesis manifest, create a new reviewed commit based on `e27c391...`, and
   recreate the clean Stage B worktree from that commit. The T1d hierarchy
   manifest already passes.

Until those corrections are reviewed, Stage B remains `HALT`. The physical
ladder (reset, prepared transaction, frame activation, and VGA observation)
belongs to a later Stage C authorization and is not implied by this review.

### 13.2b Stage B review rerun — 2026-09-20

The three requested correction checks were rerun without launching Stage B:

| Correction check | Result |
|---|---|
| Clean execution environment | PASS: detached clean worktree at `build/stage_b_clean_e27c391`; `git status --porcelain` empty; HEAD exactly `e27c391d0cb6d5bc68e1002b830213beb0ede2fc` |
| VGA connector/pin freeze | PASS: active T1d XDC remains `vga_vsync -> E5`; J10-10/E5 is the frozen VSYNC harness connection; J10-7/G6 is unused; related XDC comments and `docs/SPIpinout.txt` agree |
| Exact clock model | PASS: `python3 software/tests/test_gpu_t1d_clock_model.py`; 20 ns `sys_clk`, divide-by-two 40 ns `clk_pixel`, 217-pixel-clock UART divisor, and source anchors all checked |
| Canonical B0 hierarchy from clean source | FAIL: `spu_a7_gpu_vga.ys` in `e27c391` omits the three prepared-scene modules structurally instantiated by `spu_gpu_top`; Yosys reports `spu_prepared_scene_control` unresolved |
| T1d candidate hierarchy from clean source | PASS: the T1d manifest reads the required modules and the exact hierarchy-only command exits 0 |

**Rerun decision:** `HALT`. The clean-environment, mapping, and clock-model
corrections are now documented and tested, but Stage B cannot be authorized
until the minimal canonical B0 manifest correction is committed after
`e27c391` and a new clean worktree is created from that correction commit.
No repository gate or synthesis/P&R job was launched.

### 13.2c Stage B review from corrected baseline — 2026-09-20

The manifest correction was committed as
`37cf684bcd8a146d9db4472e68ecca96021c8d5c` from `e27c391...`. Its only diff
is the three prepared-scene `read_verilog` lines in
`hardware/boards/artix7/synth_a7_gpu_vga.ys`.

| Review check | Result |
|---|---|
| Corrected clean worktree | PASS: `build/stage_b_clean_37cf684`; empty porcelain status; HEAD exactly `37cf684...` |
| Canonical B0 hierarchy | PASS: hierarchy-only Yosys check exits 0 |
| T1d candidate hierarchy | PASS: hierarchy-only Yosys check exits 0 |
| Shared prepared-scene source closure | PASS: both manifests contain `spu_scene_loader.v`, `spu_scene_unpack.v`, `spu_prepared_scene_control.v`, and the same `spu_a7_gpu_vga_top.v` top source |
| Detached-job execution provenance | **HALT:** `tools/run_detached_job.sh` and `docs/DETACHED_JOB_RUNNER.md` are not tracked in `37cf684`; they exist only as untracked files in the dirty root workspace. Launching from the dirty root would record the wrong repository state, while launching from the clean checkout cannot invoke the required runner. |

**Corrected-baseline decision:** `HALT`. The build source now elaborates
cleanly and the manifest/source-closure recurrence is closed. Stage B still
requires a separately authorized infrastructure decision: either add the
detached-runner infrastructure in a separate provenance commit, or ratify an
immutable external runner path and evidence procedure. The manifest correction
commit must not be amended with unrelated infrastructure or documentation.
Stage C remains prohibited.

### 13.2d Stage B review from runner baseline — 2026-09-20

The runner infrastructure was committed as
`8095690628d34c3188ba700b0d9a50a7a3147e23` from `37cf684...`. Its scope is
limited to `tools/run_detached_job.sh`,
`tools/run_detached_job_worker.sh`, `docs/DETACHED_JOB_RUNNER.md`, and the
runner self-check.

| Review check | Result |
|---|---|
| Clean runner worktree | PASS: `build/stage_b_clean_8095690`; empty porcelain status; HEAD exactly `8095690...` |
| Runner availability | PASS: launcher, worker, documentation, and self-check are present from the clean checkout |
| Runner self-check | PASS: shell syntax, success, failure, timeout, durable markers, result JSON, and notification failure handling |
| Canonical B0 hierarchy | PASS: hierarchy-only Yosys check exits 0 |
| T1d candidate hierarchy | PASS: hierarchy-only Yosys check exits 0 |
| Shared prepared-scene source closure | PASS: canonical and T1d manifests contain the same prepared-scene module closure and top source |
| Clock-model self-check provenance | **HALT:** `software/tests/test_gpu_t1d_clock_model.py` is not present in `8095690`; the earlier PASS was executed from the dirty workspace only. The runner baseline therefore cannot reproduce that review check. |

**Runner-baseline decision:** `HALT`. The approved detached execution
mechanism is now reproducible, but the timing-model test and its associated
review documentation require their own narrowly scoped provenance commit (or
an explicit owner decision that the timing model is an external review
artifact). No repository gate, synthesis/P&R, or hardware job was launched.

### 13.3 Stage B closeout and Stage C authorization

Stage B closeout evidence:

| Field | Actual evidence |
|---|---|
| Build source anchor | `d88ee61f3f930a93b903839c6dcae73174578adc`; clean detached worktree; empty recorded dirty status |
| Repository regression/gate result | `stage_b_gate_03`: `COMPLETE`, exit 0, `233 PASS / 0 FAIL`; stdout SHA-256 `473d34f973b3f6f0f3435187738244c287e440be945c6989fc393b5b92d30128`; result JSON SHA-256 `972df417ede7ad6579fd2449d20678b84f3b5f904f6fd6d1ce88e5ea35fb997e` |
| Chip database prerequisite | `chipdb_100t_01`: `COMPLETE`, exit 0; `build/chipdb/xc7a100tfgg676.bin`, 159,062,368 bytes; SHA-256 `9d79e339c19fc3b42a5c409c47e58175ee199c2852d9096ea31c226e34398543` |
| B0 result | `b0_s1_02`: `COMPLETE`, exit 0; result JSON SHA-256 `02d7337c42a7e3393327963bbd96bb5f2dfe6ff1b974fa3b9410b7f19d056cce` |
| B1 result | `b1_s1_01`: `COMPLETE`, exit 0; result JSON SHA-256 `65b2a1de8022022dd17dc594c7ed3ed640d9dbeacb57837017bf7f01fd93163c` |
| B0/B1 resource comparison | Post-route console metrics: B0/B1 LUT `7,891 / 13,048`; FF `2,419 / 3,833`; CARRY4 `387 / 403`; DSP48E1 `2 / 2`; BRAM18/36 `0 / 0`; BUFGCTRL `2 / 2`; SELMUX `550 / 984`. The B1 increase is recorded as the T1d UART/prepared-scene integration delta, not a performance claim. |
| Routed setup/Fmax evidence | B0: `$iopadmap$sys_clk` `352.24 MHz`, `clk_pixel` `47.27 MHz`; B1: `$iopadmap$sys_clk` `334.90 MHz`, `clk_pixel` `42.02 MHz`. All exceed the contracted `50 MHz sys_clk` and `25 MHz clk_pixel` thresholds where the pinned flow reports the two domains. The flow provides no independent hold or unconstrained-path count; neither is claimed. |
| B0 report hashes | Bitstream `5de505769d619ddf01fb8a8d6853fee650425a3e0be57214ca97b4db00c95fee`; JSON `5f25b9d81e8a13899f3ab678499a56b0d49723041971a916633f13d829b022ec`; routed JSON `4463daa5bd19e22a6d47c18daa6a71abb1934981022597d0db608d8cdb1d3a8b`; FASM `afae385994f0d44743e0bcef8ba9c435acb7af7c7a4ed432a681c4d6554250ab`; nextpnr log `7d589b4dd995453faa12786d1a4c49da17bf72a254bf61e7f33a400d568b2c6e`; metrics JSON `6e14435461029fc2c6ea187aa3041839baf9e6d25da8c27c0945251ae212239c` |
| B1 report hashes | Bitstream `9d135a4d60e791fa88c4010ea6875c29127603d0d413c1d323fb03a0b0476cc1`; JSON `db41fdb9e856b079583178860cf93bea55beb085064f4b0d57d3bd9fa2218a74`; routed JSON `e9ca4264b98a901e9062bb64464d3c104c5d2ade49c53fd4e99ccf6a259c7a6d`; FASM `bd670c6b113e12b659a5101f872770d12a6e941b75ad787e1478f588e56f0aa7`; nextpnr log `d4cb7f09356124880a3e1cbf17b67002f9d1ea8e98ab5ce9f71d65258fcb3561`; metrics JSON `4d9006080daf171e223acbf02d0768844be7903d076e16d7646461a0c7b61a1f` |

The B0 and B1 jobs both completed synthesis, place-and-route, and bitstream
packaging with the frozen device, seed, frequency, manifests, and chipdb. The
results are build-qualification evidence only. They do not establish that the
bitstreams have been loaded, that VGA is functioning on a board, or that the
UART transaction has been observed physically.

Complete before Stage C begins:

| Stage C field | Ratified value |
|---|---|
| VGAFIX bitstream hash/program command | `a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379` / `openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_VGAFIX.bit` (historical known-good evidence; re-detect required) |
| B0 bitstream hash/program command | `5de505769d619ddf01fb8a8d6853fee650425a3e0be57214ca97b4db00c95fee` / `openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA_T1D_B0_S1.bit` |
| B1 bitstream hash/program command | `9d135a4d60e791fa88c4010ea6875c29127603d0d413c1d323fb03a0b0476cc1` / `openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA_T1D_B1_S1.bit` |
| Known-good recovery image hash/command | VGAFIX hash/command above; use only after applying the programming safety rule |
| Board/power/CH340/monitor/harness identities | Board model is QMTech Wukong Artix-7 XC7A100T-FGG676 with 50 MHz oscillator; live board serial, DirtyJTAG identity, CH340 `/dev/ttyUSB*`, power source, monitor, and harness revision remain **HALT fields** |
| Host-send command and drain operation | **HALT:** no committed T1d sender currently freezes port selection, fixture hash checks, raw 115200 8N1 setup, one-shot 64-byte write, and `tcdrain` evidence |
| Warm-reset procedure | Section 9.2, ratified unchanged |
| Cold-boot/reload procedure and startup interval | **HALT:** board-specific power/reload procedure and startup interval not yet observed and frozen |
| Observation rule | serial drain; wait 100 ms; record image present/absent; no latency claim |
| Attempt count | exactly five: four warm-reset attempts and one cold-boot attempt |

**Stage C owner:** John Curley
**Stage C decision:** `HALT`
**Stage C date:** `2026-09-20`
**Stage C notes:** `Stage B is closed. Programming, reset smoke testing, UART transmission, frame activation, and rendered-image observation require a new explicit Stage C authorization and completion of the remaining equipment, sender, recovery, and observation fields above.`

### 13.3a Stage C pre-execution review — 2026-09-20

Stage C remains **HALT**. This review freezes the already-qualified B0/B1
artifacts and the historical VGAFIX recovery image without authorizing any
programming or physical operation.

| Review item | Result |
|---|---|
| Build artifacts | PASS: B0 and B1 hashes above are tied to clean Stage B source commit `d88ee61f`; no rebuild or artifact substitution is authorized |
| Programming mechanism | **Provisional only:** the historical Wukong command uses `openFPGALoader -c dirtyJtag --freq 1000000`; a live `--detect -v` result and programmer identity must be recorded before authorization |
| Board and power identity | **HALT:** no live board/power inventory was captured in this review |
| CH340 receive port | **HALT:** no `/dev/ttyUSB*` or `/dev/serial/by-id/*` device was present in the review environment; do not infer `/dev/ttyUSB0` from historical evidence |
| Exact sender | **HALT:** add or identify one committed sender command that opens the CH340 at 115200 8N1, verifies the frozen 64-byte fixture hash, writes it exactly once, calls `tcdrain`, and emits a durable raw transcript |
| Monitor/harness observation | **HALT:** identify the monitor, VGA cable/harness revision, and capture method; the frozen J10/DE-15 mapping does not identify the physical equipment |
| Reset/cold-boot timing | Warm-reset minimums are frozen in Section 9.2; the cold-boot reload command and startup interval remain unmeasured and must be frozen before execution |
| Attempt accounting | PASS as a rule: exactly five attempts, four warm-reset and one cold-boot; any procedure or artifact change returns the tranche to HALT |

**Decision:** `HALT`. Stage C is not authorized. No board has been programmed,
no UART transaction has been sent, and no physical VGA result exists.

### 13.3b Stage C execution result — 2026-09-20

The owner subsequently authorized the bounded physical execution after the
live JTAG/CH340 preflight. The first recovery and build-image ladder steps
were completed as specified. The second controlled UART attempt produced a
completed, drained transaction but the expected image was absent, so the
contracted FAIL condition was reached and the remaining attempts were not
run.

| Attempt | Raw evidence | Observation | Classification |
|---|---|---|---|
| VGAFIX recovery | Loader completed with `isc_done 1`, `init 1`, `done 1`; historical hash `a80b6d0c...`; visual colour bars and moving marker confirmed | Stable recovery image | PASS |
| B0 canonical ladder | Loader completed with `isc_done 1`, `init 1`, `done 1`; B0 bitstream hash `5de505769d...`; visual red/green two-triangle scene confirmed | Stable canonical scene | PASS |
| B1 default state | Loader completed with `isc_done 1`, `init 1`, `done 1`; B1 bitstream hash `9d135a4d...` | Stable black/unarmed default confirmed | PASS |
| Attempt 1 | `stage_c_attempt_01/transmit.json`, SHA-256 `2630422598d51b2b2636dd4835588a3e18762ae1fd47877005ff354786d9496c` | 64 bytes written, `tcdrain` completed, expected prepared scene confirmed | PASS |
| Attempt 2 | `stage_c_attempt_02/transmit.json`, SHA-256 `aef644d1071bfd7c32a8f4ed07da6151faa8db698dc97220d8f3287c8305487d`; raw observation SHA-256 `7d185a2038e4f0001559728e245908e87546f677657e82d475e63923553e3693` | 64 bytes written, `tcdrain` completed, operator reported scene blank and expected prepared scene absent | FAIL |

The two earlier sender-open failures wrote zero bytes and are infrastructure
precondition events, not controlled UART attempts. A duplicate identical
VGAFIX load occurred during the loader-session return anomaly; no UART data was
sent during that event, and it is retained as a procedure anomaly.

**Stage C execution decision:** `HALT` after the completed Attempt 2 FAIL.
Attempts 3-5 are prohibited under this run. No RTL, bitstream, fixture,
reset, UART, or observation change is authorized by this result.

### 13.4 Final closeout

| Field | Actual evidence |
|---|---|
| VGAFIX ladder result | PASS; loader done flags and visual colour bars/marker confirmed |
| B0 ladder result | PASS; loader done flags and visual canonical red/green scene confirmed |
| B1 default-state result | PASS; loader done flags and visual black/unarmed state confirmed |
| Controlled UART attempts | Attempt 1 PASS; Attempt 2 FAIL; attempts 3-5 not run after terminal FAIL |
| Raw UART evidence | `stage_c_attempt_01/transmit.json`; `stage_c_attempt_02/transmit.json`; `stage_c_attempt_02/observation.txt` |
| Photograph/capture evidence | None; visual observations were operator-confirmed, with no image capture |
| Final T1d classification | **FAIL** — completed Attempt 2 did not reproduce the expected prepared scene |
| Closeout commit | `[EXACT SHA — documentation closeout pending]` |
