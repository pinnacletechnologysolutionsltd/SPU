# Parallel GPIO / PIO Transport: RP2350 <-> FPGA (Deferred)

*Status: Proposed. Deferred until a full-size Raspberry Pi Pico 2 is on the
 bench. Current bring-up continues with the known-good J11 SPI path.*

The current Wukong bring-up uses J11 as a 4-wire SPI link and is proven at
conservative 25-100 kHz smoke-test rates. RP2350 PIO can improve that in two
different ways:

1. **PIO/DMA SPI on the existing J11 wiring.** This keeps the FPGA pinout and
   protocol shape unchanged, but removes most MCU-side bit-banging/guard delay.
   It is the lowest-risk firmware upgrade.
2. **A custom parallel GPIO bus.** This uses PIO as an 8-bit strobed transport
   over J10 + J11, target ~10 MHz, and is the real high-throughput southbridge
   data plane.

SPI remains the debug/control fallback. The parallel bus is a performance path,
not a replacement for the known-good recovery path.

## Can This Be Done With Current Hardware?

Partially.

- **Existing RP2350-Zero -> Wukong J11 wiring:** yes for faster PIO/DMA-driven
  SPI on the same `CS/SCK/MOSI/MISO` pins. No FPGA hardware changes are needed.
- **Full 8-bit PIO parallel transport:** not with the current four-wire J11
  hookup. It needs at least 8 data pins plus `STROBE`, `READY`, and direction or
  read/write sideband pins.
- **Bench prototype:** possible after adding wires from RP2350 GPIO to Wukong
  J10/J11 and verifying the Wukong J10 pinout against the schematic. The current
  `spu_a7_100t.xdc` only assigns three J10 pins as I2S placeholders, so the full
  J10/J11 mapping still needs constraint work.
- **Recommended bench adapter:** a full-size Pico 2 is preferred over the
  RP2350-Zero because the standard headers make contiguous GPIO, ground return,
  probing, and strain relief practical.

Do not attempt the full parallel bus until the FPGA header pins, VCCO voltage,
and ground pins are confirmed with the board schematic and a meter. All signals
must be 3.3 V LVCMOS with a solid shared ground.

## Hardware Required

- **Full-size RP2350 Pico 2** — preferred bench southbridge because the standard
  headers make ribbon wiring, probing, strain relief, and ground return easier.
- **RP2350-Zero** — keep as the compact/debug adapter; it is less convenient for
  a wide bench bus because not every GPIO is header-friendly.
- **RP2350B** — not required for the first 8-bit transport. Revisit only if the
  bus grows to 16 bits, adds separate read/write data buses, or needs many
  sideband/debug pins.
- The existing J11 SPI path remains the debug/control fallback.

## Current Bottleneck

| Metric | Current SPI | PIO/DMA SPI | Parallel PIO target |
|---|---:|---:|---:|
| FPGA data pins | 1 in each direction | 1 in each direction | 8 half-duplex |
| Extra control pins | CS/SCK only | CS/SCK only | STROBE, READY, DIR/WE |
| Proven clock | 25-100 kHz | not yet tested | not yet tested |
| Practical first target | 1-2 MHz | 10-30 MHz | 5-10 MHz |
| Raw throughput before framing | 0.025-0.1 Mbps proven | 10-30 Mbps | 40-80 Mbps |
| 64-bit payload time | 640-2560 us proven | 2.1-6.4 us | 0.8-1.6 us |
| Main value | reliable bring-up | low-risk speedup | real data-plane bandwidth |

## Pin Assignment

### J10 (8 pins, currently unused) — data bus

| J10 pin | FPGA pin | Direction | Signal |
|---|---|---|---|
| 1 | TBD | RP2350 → FPGA | DATA[0] |
| 2 | TBD | RP2350 → FPGA | DATA[1] |
| 3 | TBD | RP2350 → FPGA | DATA[2] |
| 4 | TBD | RP2350 → FPGA | DATA[3] |
| 5 | TBD | RP2350 → FPGA | DATA[4] |
| 6 | TBD | RP2350 → FPGA | DATA[5] |
| 7 | TBD | RP2350 → FPGA | DATA[6] |
| 8 | TBD | RP2350 → FPGA | DATA[7] |

### J11 remaining pins (currently has CS/SCK/MOSI/MISO on pins 1-4)

| J11 pin | Signal | Direction |
|---|---|---|
| 5 | STROBE | RP2350 → FPGA |
| 6 | READY | FPGA → RP2350 |
| 7 | DIRECTION | RP2350 → FPGA (1=write, 0=read) |
| 8 | (spare) | — |

## Protocol

The first implementation should be **write-first half-duplex**. Most southbridge
traffic is RP2350-to-FPGA instruction/config/table streaming, so spending pins
on separate read and write data buses is not justified until the profiler shows
readback pressure.

### FPGA Write (RP2350 sends instruction/data)

```
1. RP2350 sets DIRECTION=1, places data on DATA[7:0]
2. RP2350 asserts STROBE for 1 cycle
3. FPGA captures on STROBE rising edge
4. FPGA asserts READY when processed
5. RP2350 deasserts STROBE, waits for READY=0
6. Repeat for next byte
```

### FPGA Read (RP2350 reads back result)

```
1. RP2350 sets DIRECTION=0
2. FPGA drives DATA[7:0] with result
3. RP2350 asserts STROBE to clock in data
4. FPGA advances to next byte, drives DATA
5. Repeat for all result bytes
```

### Frame Format

Keep frames self-checking so link faults are visible during bring-up:

| Byte(s) | Field |
|---:|---|
| 0 | Sync `0xA7` |
| 1 | Command/opcode |
| 2 | Sequence number |
| 3 | Payload length in bytes |
| 4..N | Payload |
| N+1 | CRC-8 over command, sequence, length, and payload |

The existing SPI opcodes (`0xA0`, `0xA5`, `0xAC`, `0xAE`, `0xB1`) should be
reused so the transport layer changes without changing the SPU command model.

## FPGA Module

New module: `spu_parallel_slave.v` (~150 lines)

- 16-byte FIFO for incoming instructions
- Captures 8-bit words on STROBE, packs into 64-bit instruction words
- Drives READY and DATA during readback
- Output: same `inst_valid/inst_word/inst_done` interface as the existing SPI slave
- CRC-8 checker and sequence counter for bring-up observability
- Optional loopback mode before connecting the SPU core

## RP2350 PIO

New PIO program: `spu_parallel_tx.pio` (~30 instructions)

- State machine 0: parallel write (FPGA direction)
- State machine 1: parallel read (FPGA direction)
- Runs from PIO clock divider for ~10 MHz timing
- ~200 ns transaction overhead vs 20 µs SPI guard
- DMA feeds/empties PIO FIFOs so USB CDC jitter does not directly stall the
  FPGA-side byte timing.

PIO pin assignment should use contiguous GPIO for `DATA[7:0]` if possible. Put
`STROBE`, `READY`, and `DIR/WE` on nearby pins to keep the PIO program simple
and make ribbon routing inspectable.

## Integration

- Both SPI and parallel paths coexist on different headers
- `spu_a7_top.v` muxes `inst_valid/inst_word` from either source
- SPI remains as debug fallback
- No RTL changes to `spu13_core.v` or any pipeline module

## Evaluation Board Requirements

The ECP5 evaluator should build this in from day one:

- RP2350-to-FPGA 8-bit half-duplex PIO bus with contiguous MCU GPIO.
- Dedicated SPI fallback path on separate pins.
- Interleaved ground pins or nearby ground returns on every cable/header group.
- 22-47 ohm optional series resistors near the driving side for `DATA[7:0]` and
  `STROBE`.
- Test pads for `STROBE`, `READY`, `DIR/WE`, `CS`, `SCK`, and two data lanes.
- FPGA-side FIFO/CRC status exposed through both SPI and parallel readback.
- Keep the RP2350A/Pico 2 class for the first 8-bit evaluator. Move to RP2350B
  only if the board needs a 16-bit bus, separate read/write buses, or many extra
  debug/peripheral pins.

## Status

Deferred. Immediate next step is a PIO/DMA SPI firmware experiment on the
existing J11 wiring. Full parallel transport needs pin assignment in
`spu_a7_100t.xdc`, and the physical J10/J11 mapping must be checked against the
Wukong schematic before any RTL is written. FPGA module and PIO program still
need implementation. Estimated effort after hardware is on the bench: 4-6 hours
for the first loopback/streaming prototype.
