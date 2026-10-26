# SPU transport boundaries

Date: 2026-10-09. Documentation reconciliation; no transport or hardware change.

## Southbridge: SPI command plane

The live decoder is `hardware/rtl/peripherals/io/spu_spi_slave.v`, instantiated
by board tops. [SOUTHBRIDGE_SPI_PROTOCOL.md](SOUTHBRIDGE_SPI_PROTOCOL.md) owns
the exact per-command transaction. The command byte is separate from a CPU
opcode. The narrow `spu13_southbridge_token_parser.v` CRC helper is not the
live HEADER/DATA decoder and must not replace its specification.

| SPI command | Surface |
|---|---|
| 0xA0 / 0xAC / 0xAD | Manifold / status / scale-table reads |
| 0xAE / 0xAF / 0xB0 | QR commit / HEX / sentinel telemetry |
| 0xB1 | One big-endian 64-bit instruction word |
| 0xA5 | Configuration HEADER/DATA transaction, not GPU scene input |

RP2350 firmware supplies a board-specific SPI/USB/SD path. Its Tang 2 MHz SPI
setting is not portable to reduced-clock Artix images: the documented SCK to
fabric-clock bound applies. Active pin defines are authoritative for the
compiled firmware; stale header comments need separate reconciliation.
Reset/watchdog/full board-management capabilities must be attributed to actual
firmware and evidence, not assumed from the southbridge role.

## GPU: versioned UART scene transport

Scene packets use their own start byte, fixed profile lengths, little-endian
payload and loader commit rules. Reusing 0xA5 does not make them SPI config
transactions. Profile identity must come from the selected build/interface;
the start byte alone does not identify the payload format.

| Profile | Records | Bits per record | Payload bytes | Total bytes including A5 |
|---|---|---|---|---|
| T1d offline/device packet | 2 | 252 | 63 | 64 |
| T1G geometry | 4 | 252 | 126 | 127 |
| T1H scalar attributes | 4 | 300 | 150 | 151 |
| T1I UV attributes | 4 | 348 | 174 | 175 |

T1d source: `software/spu_gpu_eval/packet.py` and `device_packet.py`.
Four-record profile definitions: [T1I offline preparation](GPU_T1I_OFFLINE_PREPARATION_2026-10-07.md);
loader/profile sources: `spu_scene_loader.v`, `spu_scene_profile_unpack.v`.
Other profiles, including T1o, require their own manifest and are not assigned
these lengths by analogy. Completeness, validation and atomic scene commit are
loader/profile requirements; partial input cannot be treated as a full scene.

[GPU bring-up runbook](GPU_BRINGUP_RUNBOOK.md) owns hardware operating and
rollback rules. T1H H1 remains HOLD; T1G rollback remains preserved. Packet
implementation is not new silicon evidence or CPU/GPU concurrent-fit evidence.

## Future PCIe northbridge

PCIe will be a host-facing transport alongside RP2350, using the existing
canonical instruction format and distinct typed data/config/scene surfaces.
Before RTL, specify endpoint identity/version, byte order, lengths, buffer and
queue ownership, admission/backpressure, atomic completion/status, reset/CDC,
error recovery and trace identity. Instruction-memory transport does not imply
that the current core already has a complete program-fetch/PC/control-flow
implementation.

Card-specific link width/generation, DMA/MMIO/DDR support, routing and timing
are unqualified here. This document allocates no registers, BARs, opcodes or
queues and authorizes no PCIe build. SOM dispatch remains parked.
