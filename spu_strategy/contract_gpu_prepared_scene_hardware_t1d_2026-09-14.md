# Engineering Contract: Wukong GPU Prepared-Scene Physical UART Integration (T1d)

**Date:** 2026-09-14  
**Contract ID:** `contract_gpu_prepared_scene_hardware_t1d_2026-09-14.md`  
**Revision:** 4 — incorporates third pre-execution review of 2026-09-15  
**Status:** **ACTIVE — Stage A COMPLETE; Stage B/C HALT. Stage B or C requires a separate owner authorization and does not inherit Stage A authorization.**
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

### 2.2 Stage B — frozen regression and matched builds

Stage B may be authorized only after Stage A closes with a reviewed clean SHA and completed Stage B fields in Section 13. It authorizes exactly one repository regression/gate and the matched B0/B1 synthesis/P&R jobs in Section 8.1, including packing and bitstream generation only where those frozen jobs normally produce them. It authorizes no programming or other physical operation.

Stage B must produce the regression result, matched resource/timing reports, unique artifacts, and eligible bitstream hashes. Completion, failure, timeout, or tool error returns the tranche to HALT for review before Stage C.

### 2.3 Stage C — physical ladder and controlled UART attempts

Stage C may be authorized only after Stage B passes its contracted gates and Section 13 freezes the exact eligible hashes, programming/recovery commands, sender command, serial-drain behavior, reset procedure, observation procedure, and equipment identities.

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
| FPGA board and device | Wukong / `xc7a100tfgg676-1` | `[STAGE A FREEZE schematic/XDC source]` |
| Physical UART path | Onboard CH340 | `docs/hardware_evidence.md` Section 3.11 |
| FPGA input pin for UART RX | F3 | constraints + hardware evidence Section 3.11 |
| FPGA I/O standard | LVCMOS33 with pull-up | constraints + hardware evidence Section 3.11 |
| UART receiver clock | `clk_pixel` at 25 MHz | board top + elaborated hierarchy `[STAGE A FREEZE]` |
| UART divisor | `BIT_CYCLES=217` | receiver elaboration `[STAGE A FREEZE]` |
| Calculated baud | approximately 115207.4 baud; +0.0064% versus 115200 | `25,000,000 / 217` |
| Byte/T1a clock domain | Same `clk_pixel` domain; no byte/pulse CDC | board top + elaborated hierarchy `[STAGE A FREEZE]` |
| Physical oscillator / `sys_clk` | 50 MHz | board constraint |
| GPU/video `clk_pixel` | 25 MHz | generated-clock design |
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

The exact commands must be filled after inspection of the repository's detached-job wrapper and new hardware-mode selector. This section is a ratification gate; descriptive equivalents are not acceptable.

| Job | Exact command | Attempts | Per-job timeout | Required artifact prefix |
|---|---|---:|---:|---|
| Repository gate | `[STAGE A FREEZE EXACT COMMAND]` | 1 | `[STAGE A FREEZE TIMEOUT]` | `_T1D_GATE_S1` |
| B0 canonical build | `[STAGE A FREEZE EXACT COMMAND WITH A7_ARTIFACT_TAG=T1D_B0_S1 AND NO FUNCTIONAL T1D SELECTOR]` | 1 | `[STAGE A FREEZE TIMEOUT]` | `_T1D_B0_S1` |
| B1 candidate build | `[STAGE A FREEZE EXACT COMMAND WITH GPU_T1D_UART=1 A7_ARTIFACT_TAG=T1D_B1_S1]` | 1 | `[STAGE A FREEZE TIMEOUT]` | `_T1D_B1_S1` |

**Cumulative Stage B wall-clock budget:** `[STAGE A FREEZE]`  
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
| Frozen source commit | `a6c52fa003a1a47ee5ae953c4d2a1658e786f2cb` |
| Repository regression/gate command and expected condition | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/stage_b_gate_01 --timeout 3600 --notify-desktop -- bash tools/verify_repo.sh` / exactly one terminal `COMPLETE` with zero failures |
| Repository-gate timeout | `3600 s` |
| B0 command | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/b0_s1_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 A7_ARTIFACT_TAG=T1D_B0_S1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all` |
| B0 timeout | `7200 s` |
| B1 command | `tools/run_detached_job.sh --output build/wukong_gpu_prepared_scene_t1d_20260920/b1_s1_01 --timeout 7200 --notify-desktop -- env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 A7_ARTIFACT_TAG=T1D_B1_S1 bash hardware/boards/artix7/build_a7.sh 100t gpuvga all` |
| B1 timeout | `7200 s` |
| Cumulative Stage B budget | `18,000 s`; one job at a time; each launch consumes its slot |
| Retry/parallel rule | zero retries; no parallel builds unless already proven isolated |

**Stage B owner:** John Curley  
**Stage B decision:** `HALT`
**Stage B date:** `2026-09-20`
**Stage B notes:** `Commands are frozen as the proposal for the next owner decision; no Stage B job was launched under Stage A.`

### 13.3 Stage B closeout and Stage C authorization

Stage B closeout evidence:

| Field | Actual evidence |
|---|---|
| Repository regression/gate result | `[RESULT AND LOG HASH]` |
| B0 result and report hashes | `[RESULT/HASHES]` |
| B1 result and report hashes | `[RESULT/HASHES]` |
| B0/B1 resource comparison | `[TABLE/REPORT]` |
| Setup/Fmax evidence for `sys_clk` and `clk_pixel` | `[EXACT REPORT VALUES]` |
| B0 eligible bitstream SHA-256 | `[SHA-256]` |
| B1 eligible bitstream SHA-256 | `[SHA-256]` |

Complete before Stage C begins:

| Stage C field | Ratified value |
|---|---|
| VGAFIX bitstream hash/program command | `[SHA-256]` / `[EXACT COMMAND]` |
| B0 bitstream hash/program command | `[SHA-256]` / `[EXACT COMMAND]` |
| B1 bitstream hash/program command | `[SHA-256]` / `[EXACT COMMAND]` |
| Known-good recovery image hash/command | `[SHA-256]` / `[EXACT COMMAND]` |
| Board/power/CH340/monitor/harness identities | `[EXACT INVENTORY]` |
| Host-send command and drain operation | `[EXACT COMMAND AND DRAIN EVIDENCE]` |
| Warm-reset procedure | Section 9.2, ratified unchanged |
| Cold-boot/reload procedure and startup interval | `[EXACT PROCEDURE/COMMAND/INTERVAL]` |
| Observation rule | serial drain; wait 100 ms; record image present/absent; no latency claim |
| Attempt count | exactly five: four warm-reset attempts and one cold-boot attempt |

**Stage C owner:** John Curley  
**Stage C decision:** `[HALT / AUTHORIZE / REJECT]`  
**Stage C date:** `[YYYY-MM-DD]`  
**Stage C notes:** `[optional]`

### 13.4 Final closeout

| Field | Actual evidence |
|---|---|
| VGAFIX ladder result | `[PASS / FAIL / INCONCLUSIVE]` |
| B0 ladder result | `[PASS / FAIL / INCONCLUSIVE]` |
| B1 default-state result | `[PASS / FAIL / INCONCLUSIVE]` |
| Five-attempt UART log | `[PATH/HASH]` |
| Photograph/capture evidence | `[PATHS/HASHES]` |
| Final T1d classification | `[PASS / FAIL / INCONCLUSIVE]` |
| Closeout commit | `[EXACT SHA]` |
