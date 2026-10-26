# ISA-V02-H0-TRANSPORT-1 — Host-driven instruction transport, completion and status audit

**Status:** read-only source audit PASS; normative H0 protocol and any implementation repair **HOLD**. The single-outstanding protocol in §8 is **PROPOSED**, not implemented. No RTL, VM, opcode, test, tool or hardware change.
**Baseline identity:** `dev/next` at `836ca5b3a700cb162a49635e93af21ce0bfa638d` (clean). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280` (`b0632806621ed6fe44c9c72f4e0adbd8ee8df776`); analysis tools, tests and documentation were added in `dev/next`. Line numbers are at `836ca5b`.
**Method:** source reading only. Nothing was elaborated or simulated for this audit; no synthesis, timing or board activity. The Artix-7 top (`spu_a7_top.v`) was not elaborated. "Hypothesis" below means a reading of the source that no simulation has confirmed.
**Related:** `ISA_V02_STATE1_FINDINGS.md` (acknowledge-without-effect, `inst_done`), `ISA_V02_A31R2_FINDINGS.md` (stale result publication).

## 1. Path as built

`SPI 0xB1 → CRC-8 → one-cycle inst_valid strobe → [sidecar claim masks core] → acceptance → execution → completion pulse → 0xAE / 0xAC readback`

### 1.1 SPI `0xB1` framing (`hardware/rtl/peripherals/io/spu_spi_slave.v`)

- Command byte `0xB1`, then one 64-bit instruction, big-endian, then one CRC-8 byte (polynomial `0x07`) computed over the command byte followed by the 8 payload bytes (`S_RECV_INST` `:737`, `S_RECV_CRC` `:875`).
- Only a matching CRC produces `inst_word <= pending_data; inst_valid <= 1` (`:894-896`). The strobe lasts one clock: `inst_valid` is cleared by default every cycle (`:368`).
- There is **no instruction queue, no sequence number and no acknowledgement** from the FPGA to the host at the transport level. The SPI interface is master-driven and the `0xB1` frame returns no data.
- Mismatch: `crc_error_sticky <= 1`, instruction dropped (`:883`). A config chord (`0xA5`) whose header byte is not `0xA5` is also reported through `crc_error_sticky` (`:892`).
- CS deasserted before the eighth CRC bit: the frame is dropped with **no** sticky flag (`:877`, "CS dropped — skip CRC check"; likewise `S_RECV_INST`/`S_RECV_HDR`/`S_RECV_DATA` return to idle).
- Deadman: `DEADMAN_RELOAD = 50000` (about 1 ms at 50 MHz, `:243`); if SCK stalls in a receive state the machine returns to idle (`:391-393`) with no flag.
- Unknown command byte: one `0x00` response byte, no flag (`:684`).

### 1.2 Arbitration (`hardware/boards/artix7/spu_a7_top.v`)

`core_inst_valid = spi_inst_valid && !lucas_inst_claimed && !su3_inst_claimed && !rplu2_sidecar_inst_claimed` (`:427-428`). A sidecar's `inst_claimed` is combinational (`inst_valid && sidecar_op`), so a claimed opcode never reaches the core. Each sidecar has its own `inst_seen`-based acceptance; the Padé sidecar raises an `error` pulse and does not start when `busy` (`spu13_rplu2_pade_sidecar.v:442-444`).

### 1.3 Core acceptance (`hardware/rtl/core/spu13/spu13_core.v`)

- `eff_inst_valid` is `inst_valid` (or the sequencer, off in the Artix-7 top) AND `boot_ready` (`:707-708`); `inst_accept = eff_inst_valid && !inst_seen && !surd_busy` (`:710`). `inst_seen` sets on `inst_accept` and clears when `eff_inst_valid` falls (`:730-737`).
- Because the strobe is one cycle, an instruction is accepted only if `boot_ready` and `!surd_busy` hold in that cycle; otherwise it is lost without indication.
- `boot_ready = (boot_state == BOOT_READY_ST)` (`:664`); states RESET, HYDRATING, READY and a terminal FAULT (`:686`). FAULT and HYDRATING both read as `boot_ready = 0`; `core_boot_state_dbg` is declared and connected (`spu_a7_top.v:416`, `:818`) but not consumed.
- The only busy gate is `surd_busy` (Surd extension, off by default). The core has no general busy refusal.
- The core's own testbenches (`issue`) hold `inst_valid` until `inst_done`, and the boot-interlock comment in `spu13_core.v` (around `:640-654`) describes an `inst_valid`/`inst_done` handshake that "holds the sender". The SPI path does not hold the strobe.

### 1.4 In-flight priority chain: UNVERIFIED SOURCE HYPOTHESES

The instruction FSM is a priority `if / else if` chain (`spu13_core.v:1331-1662`) mixing in-flight handlers (`surd_retire_valid`, `rplu2_result_valid`, `qsub_active`, `rote_active`, `rote_done_tdm`, `irotc_active`, `scale2_active`, `hex_active`, `som_classify_valid`, `som_train_done`, `regen_done` and others) with new-instruction branches (`inst_accept && opcode == ...`). `inst_seen` is set by the wire `inst_accept`, independent of which branch executes. **Hypotheses, not demonstrated by simulation:**

1. **Swallow.** A strobe accepted in a cycle where an earlier-priority in-flight branch fires would be consumed (`inst_seen` set) without its own branch running: no execution, no `inst_done`, no error.
2. **Starve.** A new-instruction branch placed above an in-flight handler (for example `QLDI` at `:1373` above `rote_active` `:1427` and `rote_done_tdm` `:1432`) would take the cycle, potentially skipping the in-flight handler's step (for example the ROTC write-back), so that operation might never complete.
3. The core has no mechanism that stops the host from presenting overlapping strobes.

## 2. Completion and diagnostic signals

- `inst_done` is a one-cycle pulse from the core. In the Artix-7 top a composite `inst_done` wire exists (`:429`) with no further reference; `debug_core_done_seen` and `debug_core_commit_seen` are written (`:420-421`, `:511-513`) and never read. `core_boot_state_dbg` is unconsumed. The host therefore has **no direct completion signal**.
- The catch-all branch (`spu13_core.v:1662-1678`) pulses `inst_done` with no effect for opcodes the core does not implement (STATE-1), so `inst_done` alone is not evidence of execution.

## 3. SPI `0xAC` status (4 bytes; `spu_spi_slave.v:525-545`)

| Byte | Content (as built) |
|---|---|
| 0, 1 | `laminar_index` (the A7 top supplies a debug word, see below) |
| 2 | `{ratio_lat[2:0], ratio_valid_lat, fifo_full, turbulence, janus_lat, snaps_lat[0]}` (`:532`). `ratio_valid_lat` clears on read; `janus_lat` and `snaps_lat` are latched at CS assertion; `turbulence` is the live input at the time the response is built. |
| 3 | `{5'h0, boot_ready, crc_error_sticky, rplu_mode}` (`:533`). `crc_error_sticky` clears on this read (`:540`). Bits 7:3 are zero in the current layout. |

What the Artix-7 top supplies (`spu_a7_top.v:1068-1091`; `sidecar_status = (_L || _U || _R2_LIVE || _R2_PADE) ? 1 : !_CORE`):

| Field | Sidecar-status spins | Core spins |
|---|---|---|
| bytes 0-1 | `{sidecar_debug_status, last_spi_opcode}` | `core_rotc_debug_status` |
| byte 2 bit 0 (`snaps_lat[0]`) | `debug_sidecar_commit_seen` | `core_rotc_debug_status[0]` |
| byte 2 bit 1 (`janus_lat`) | `debug_sidecar_claim_seen` | `core_rotc_debug_status[1]` |
| byte 2 bit 2 (`turbulence`) | `debug_sidecar_error_seen` | `core_rotc_debug_status[2] || debug_rotc_commit_seen || axiomatic_fault || lucas_error || lucas_norm_violation || su3_error || rns_error || ecc_double_err` |
| byte 3 bit 0 (`rplu_mode`) | sidecar busy level (`lucas_busy || su3_busy || rplu2_sidecar_busy`) | `core_rotc_debug_status[3]` |
| byte 3 bit 2 (`boot_ready`) | `core_boot_ready`, tied to 0 when there is no core (`:879`) | `boot_ready` |

Lifetimes: `debug_sidecar_error_seen`, `claim_seen` and `commit_seen` clear when a new SPI instruction strobe arrives (`:488-496`) and set on the corresponding event (`:509`). `turbulence` for sidecar-status spins is that sticky value, not the one-cycle `sidecar_error` pulse.

## 4. SPI `0xAE` last QR commit (`:562-578`)

Response: `[valid, lane, A(8 bytes), B, C, D]`, 34 bytes. `valid` is `qr_valid_lat`, set by any `qr_commit_valid` and cleared **only by reset** (`:338`, `:406`); reading does not clear it (contrast `0xAF`, which clears `hex_valid_lat`). The latch updates only when `qr_commit_valid` is high (`:405-411`). There is no sequence number or freshness indication: a second commit with identical data, or a repeat of the previous result, looks the same to the host.

## 5. Cases: what the hardware does and what the host can observe

| Case | Hardware (source) | Host-observable | Unknown |
|---|---|---|---|
| Transport rejected, CRC mismatch | frame dropped, `crc_error_sticky` set | `0xAC` byte 3 bit 1, cleared by that read | |
| Transport rejected, CS drop or deadman | frame dropped silently | nothing | partial-frame state after the deadman |
| Transport rejected, unknown command | one `0x00` byte | a zero byte | |
| Boot not ready | strobe lost (`eff_inst_valid` requires `boot_ready`) | `boot_ready` bit on core spins; always 0 on coreless spins; FAULT indistinguishable from HYDRATING | whether firmware must always poll |
| Accepted | `inst_accept`, `inst_seen`, FSM dispatch | sidecar spins: last SPI opcode (recorded when the SPI strobe passes CRC, not proof of core acceptance); core spins: nothing | strobe-to-completion latency |
| Busy | `surd_busy` only (core); Padé sidecar `error` and drop | sidecar spins: busy level in byte 3 bit 0, error in byte 2 bit 2; core spins: ROTC busy bit only | the hypotheses in §1.4 |
| Completed successfully | `inst_done` pulse; `qr_commit_valid` for commit-producing instructions | `0xAE` (no freshness); sidecar `commit_seen` | no per-instruction completion record |
| Refused (A31) | ordinary pipeline and core bridge: stale result with valid indications (A31-R2); Padé sidecar: `error`, no commit | sidecar spins: `0xAC` byte 2 bit 2, sticky until the next SPI instruction; core spins: **nothing distinct** (`turbulence` has no Padé `flags_v` term) | Artix-7 top not elaborated |
| Unsupported | catch-all `inst_done` pulse, no effect | nothing distinct | |

## 6. Correction to the A31-R2 SPI statement

`ISA_V02_A31R2_FINDINGS.md` said the sidecar error "also feeds a sticky debug bit" in the Artix-7 top and that its SPI probe showed identical status reads before and after the refusal. Both statements stand, with this precision: in the Artix-7 top the sidecar error reaches `0xAC` byte 2 bit 2 (through `spi_status_turbulence = debug_sidecar_error_seen` on sidecar-status spins, `:1083-1088`). The earlier SPI probe used the existing SPI testbench's own wiring (`.turbulence(sidecar_error)`, the live one-cycle pulse), so it could not show that bit. Neither the probe nor this audit simulated the Artix-7 top; the mapping is a source reading. On core spins (the ordinary-pipeline and core-bridge defect) no status bit reflects the A31 refusal.

## 7. Verification questions

1. Do overlapping strobes swallow or starve in-flight handlers (§1.4)?
2. Is the Artix-7 top mapping in §3 observed at the SPI pins on `RPLU2PADE`, and absent on core spins?
3. Latency from strobe to completion for each supported instruction, and the minimum safe spacing.
4. Behavior of repeated identical instructions and of reset during an in-flight instruction.
5. Whether Lucas and SU3 sidecar busy and error behavior matches the Padé sidecar (not audited).

## 8. PROPOSED single-outstanding H0 protocol (not implemented)

Semantics only; no encoding is proposed or implied:

1. **One instruction outstanding.** The host submits the next instruction only after observing completion of the previous one (or a documented timeout), because the core has no general busy gate and §1.4 may apply.
2. **A host-readable completion indication per instruction**, separate from `0xAE`'s sticky valid, for example a completion count that advances once per completed instruction.
3. **A per-completion outcome** distinguishing at least a new valid result, a refusal and an unsupported instruction, instead of inferring from commit presence.
4. **Transport rejection remains distinct** (CRC sticky today), and silent drops (CS drop, deadman) need an indication or a host timeout rule.
5. **Boot not ready** is reported, with FAULT distinguishable from HYDRATING.
6. **Unsupported opcodes** either refuse or are rejected by the host before dispatch; the document must state which (an enforcement-boundary decision).

Existing spare bits (for example `0xAC` byte 3 bits 7:3, `0xAE` byte 0 bits 7:1) are a fact about the current layout, not an allocation. The A31 repair should be designed together with this contract; this document authorizes neither.

## Limitations

Source reading only. The Artix-7 top and the sidecars other than the Padé sidecar were not simulated or fully audited. No latency, timing or board evidence. `docs/hardware_evidence.md` was not consulted for transport entries in this pass. The O6 inventory is a non-exhaustive census. Conclusions apply to the identity above.
