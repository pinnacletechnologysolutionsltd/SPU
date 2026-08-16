# Synergetic Processing Unit — Southbridge SPI Protocol v1.2

**Document:** SPU Southbridge Serial Protocol
**Version:** 1.2 (2026-07-14)
**Hardware:** Tang Primer 25K and Wukong Artix-7 (`spu_spi_slave.v`)
**Master:** RP2350 Microcontroller (SPI0, Mode 0). **SCK is spin-dependent —
`clk_fast / 6` is the measured ceiling, not a fixed 2 MHz.** See "Maximum SCK is
a ratio, not a fixed frequency" under Protocol Timing before choosing a baud.
**Status:** base RTL testbench PASS; Tang 25K/RP2350 `0xAC` status read
verified; optional B2/B3 TGR1 extension RTL/host verified. Artix-7 board work
proves J11/SD/B2/B3 and each exact guard engine separately, while the full
combined guard remains `verify_busy`; see the tensegrity handover.

---

## Version & Compatibility Promise

**This document defines Southbridge SPI protocol v1.** It is the wire
contract behind the homogeneity rule in
`knowledge/INTERCONNECT_ARCHITECTURE.md` §2: one protocol, one console
grammar, any board with a resident southbridge MCU (Tang 25K, Wukong A7
J11, and future T1-tier boards alike). Board differences are pin maps and
constraints files, never protocol forks.

**Base opcode set (8, frozen since v1.1):**

| Opcode | Name | Direction | Bytes |
|---|---|---|---|
| `0xA0` | Manifold Burst | read | 32 |
| `0xAC` | Status | read | 4 |
| `0xAD` | Scale Table | read | 9 |
| `0xAE` | QR Commit | read | 34 |
| `0xAF` | HEX Projection | read | 5 |
| `0xB0` | Opaque Telemetry Burst | read | 64 |
| `0xB1` | Instruction Write | write | 64 bits + 8-bit CRC |
| `0xA5` | RPLU Config Write | write | 128 bits + 8-bit CRC |

Earlier repo documents (`AGENTS.md`, `CLAUDE.md`) summarize this as a
"5-opcode contract" (`0xAC`, `0xA0`, `0xAE`, `0xB1`, `0xA5`) — that was
shorthand for the opcodes exercised in early bring-up, not the full set.
All 8 are RTL-testbench-verified (`spu_spi_slave_tb.v`); this table is
the count of record.

**Optional v1 extension opcodes (v1.2):**

| Opcode | Name | Direction | Bytes |
|---|---|---|---|
| `0xB2` | TGR1 Transactional Load | write | 6-byte prefix + 12–508-byte table + CRC-8 |
| `0xB3` | TGR1 Status | read | 16 |

These opcodes are implemented only when `spu_spi_slave.v` is built with
`ENABLE_TENSEGRITY=1`. A base-v1 bitstream retains the frozen unknown-command
response, so a host can probe `0xB3` without changing the original eight
commands.

The standalone Artix `TENSEGRITYLINK` appliance additionally sets
`TENSEGRITY_ONLY=1`, which prunes the legacy command datapaths at synthesis
time so this dense guard build can route. It intentionally exposes only B2,
B3, and the frozen unknown-command response. The parameter defaults to zero;
all integrated southbridge builds retain the complete base-v1 command set and
the optional opcodes do not alter any existing wire format.

**Compatibility rules (v1):**
1. An opcode's response format, once documented here, **never changes**
   for the same opcode value. A format change is a new opcode.
2. New functionality gets a new, previously-unused opcode byte. Existing
   opcode formats are never widened in place.
3. Unknown opcodes return a single `0x00` byte and re-arm to `S_IDLE`
   (see Error Handling) — this behavior is itself part of the v1
   contract, so host code can safely probe for opcode support.
4. Any host library or firmware written against this table is expected to
   work unmodified against any board that implements v1, per the
   Interconnect Architecture homogeneity rule. A board-specific fork of
   this protocol is a bug in the port, not a new "board variant."
5. **An opcode whose payload varies by build must be documented as opaque
   at the wire level AND must carry a self-describing magic in its first
   four bytes.** An opcode whose meaning silently depends on which
   bitstream answered it is a protocol defect regardless of how carefully
   each individual meaning is documented — a caller cannot tell them
   apart. Added 2026-08-16 while resolving `0xB0`, which is the only
   opaque-payload opcode in v1. Payload magics are registered in that
   opcode's section and must be allocated *before* a bitstream emits
   them.

A future incompatible v2 (if one is ever needed) gets its own document.
Compatible v1 extensions may allocate unused opcodes as above, while the
frozen base formats remain unchanged.

---

## Overview

The **Southbridge** is the compute engine side of the RP2350↔FPGA bridge. It implements a **SPI slave** that answers queries from the RP2350 master, streaming manifold state, telemetry, and accepting instruction/configuration writes.

### Key Characteristics
- **Synchronous:** All edges are sampled on the rising edge of the selected
  southbridge clock (50 MHz on the original Tang spin; 25 MHz on
  `TENSEGRITYLINK`)
- **Big-endian:** All multi-byte values streamed MSB first
- **Latched:** Entire manifold snapshot captured atomically at CS assertion
- **Sticky state:** HEX and RPLU ratio valid bits clear on read; QR commit remains latched until overwritten or reset
- **SPI Mode 0:** CPOL=0, CPHA=0 (sample on leading edge, shift on trailing edge)

### Southbridge Pinout (PMOD J4 Bottom Row -> RP2350 SPI0)

This is the header-friendly RP2350-Zero wiring used by
`hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst` and the
current `rp2350_spu_interface.c` build.

| Tang PMOD J4 / FPGA pin | FPGA signal | RP2350-Zero pin | RP2350 signal | Wire direction |
|:---:|:---|:---:|:---|:---|
| J4-1 / G10 | `spi_cs_n` | GP1 | CS# (software GPIO) | RP2350 -> FPGA |
| J4-2 / D10 | `spi_sck` | GP2 | SPI0 SCK | RP2350 -> FPGA |
| J4-3 / B10 | `spi_mosi` | GP3 | SPI0 MOSI/TX | RP2350 -> FPGA |
| J4-4 / C10 | `spi_miso` | GP0 | SPI0 MISO/RX | FPGA -> RP2350 |
| J4-5 | GND | GND | GND | common ground |
| J4-6 | 3V3 | 3V3 | 3.3 V rail | optional; see note below |

If the Tang and RP2350 are both USB-powered, do not jumper J4-6 to RP2350 3V3.
Use J4-5/GND as the common reference and leave the 3.3 V rails separate. Jumper
J4-6 only when one side is intentionally powering the other and back-powering
through USB or regulators has been ruled out.

For `rp2350_spu_diag` and `spu_link_test`, build with
`-DSPU_RP2350_ZERO_HEADER_SPI=ON` to match the GP0-3 wiring above. If that
option is not set, those diagnostic targets default to GP16 MISO, GP17 CS,
GP18 SCK, GP19 MOSI. `-DSPU_RP2350_ZERO_G25_SPI=ON` selects the alternate
RP2350-Zero edge mapping GP20 MISO, GP21 CS, GP22 SCK, GP23 MOSI.

**RP2350 SPI0 Configuration:**
```c
#define SPU_SPI_MISO_PIN 0
#define SPU_SPI_CS_PIN   1
#define SPU_SPI_SCK_PIN  2
#define SPU_SPI_MOSI_PIN 3

spi_init(spi0, 2 * 1000 * 1000);    // 2 MHz (conservative)
spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);
gpio_set_function(SPU_SPI_SCK_PIN,  GPIO_FUNC_SPI);
gpio_set_function(SPU_SPI_MOSI_PIN, GPIO_FUNC_SPI);
gpio_set_function(SPU_SPI_MISO_PIN, GPIO_FUNC_SPI);
gpio_init(SPU_SPI_CS_PIN);
gpio_set_dir(SPU_SPI_CS_PIN, GPIO_OUT);
gpio_put(SPU_SPI_CS_PIN, 1);         // CS idle-high
```

### microSD PMOD Pinout (RP2350 SPI-mode)

The current SD bring-up path is SPI-mode microSD on the RP2350, independent of
the FPGA J4 southbridge link. Defaults come from `hardware/rp_common/spu_sd.c`
and `hardware/rp2350/CMakeLists.txt`.

| microSD PMOD signal | RP2350 pin | Firmware define |
|:---|:---:|:---|
| SCK / CLK | GP10 | `SPU_SD_SCK_PIN` |
| MOSI / CMD | GP11 | `SPU_SD_MOSI_PIN` |
| MISO / DAT0 | GP12 | `SPU_SD_MISO_PIN` |
| CS# / DAT3 | GP13 | `SPU_SD_CS_PIN` |
| VCC | 3V3 | 3.3 V only |
| GND | GND | common ground |

The SD SPI instance is `spi1` by default and the post-init rate is 8 MHz. If a
PMOD adapter routes different pins, override `SPU_SD_*` at CMake configure
time. Keep pull-ups on CMD/DAT lines; at minimum ensure CS# idles high.

### SD PMOD Bring-up Status (2026-06-28)

The RP2350-Zero southbridge wiring to Tang J4 is proven with
`rp2350_spu_diag status`: the FPGA replies `raw=13 A5 00 00`, so the GP0-GP3
SPI0 link and Tang southbridge bitstream are alive.

After SD-side solder rework, the default SPI-mode SD map is also proven:
`sdprobe` reports `cs=GP13 sck=GP10 mosi=GP11 miso=GP12`, raw CMD0/CMD8 at
400 kHz return `cmd0_r1=0x01 cmd8_r1=0x01 r7=00 00 01 AA`, and `sdinit`
mounts the card successfully. The standalone `spu_sd_test.uf2` filesystem
smoke also passes: create/write `test.txt`, readback match, delete, halt code
0. With `/manifest.txt` selecting `/carbon_rplu.tbl`, `sdhydrate` loads 16
records with 0 skipped. The SPI-only FPGA telemetry probe
`build/tang_primer_25k_southbridge_spi_probe.fs` confirms the FPGA receives
those writes: `cfgtele` changes from count 0 to count 16, with last record
`sel=0 material=1 addr=2 data=0x0000000000010000`.

Southbridge write-path hardening was re-tested on 2026-06-30 NZT after two
firmware/RTL timing bugs were fixed: the RP CRC helper now compares the CRC MSB
as a bit, and `spu_spi_slave` no longer lets RP firmware inter-byte gaps or a
missed command trailing edge corrupt `0xA5` payload reception. The SPI-only
probe now routes at 1,861 LUT4 / 840 DFF and reports `status raw=25 A5 00 00`.
A manual `rplu 0 1 2 0x0000000000010000` advances `cfgtele` from count 0 to
count 1, and a clean SD hydration advances count 0 to 16 with checksum
`0x3A0AB5E9`.

The telemetry path is also proven on the full SPU-13 southbridge image. On
2026-06-29 NZT, `build_25k_spu13_southbridge.sh` completed synthesis,
place-and-route, and packaging for `build/tang_primer_25k_spu13_southbridge.fs`.
The routed design passes the 12 MHz constraint (`clk_core` 72.28 MHz max,
`clk_50m` 125.16 MHz max). After SRAM load, RP2350 diagnostics report
`status raw=13 A5 00 00`; `cfgtele` reports `magic=SPUC` with count 0 before
hydration; `sdhydrate` loads 16 records with 0 skipped; and final `cfgtele`
reports count 16, last record `sel=0 material=1 addr=2
data=0x0000000000010000`, checksum `0x3A0AB5E9`.

The split core-attached southbridge probe was rebuilt with the same write-path
fixes on 2026-06-30 NZT. `build_25k_spu13_southbridge_link.sh` routes at
4,054 LUT4 / 3,091 DFF and passes timing (`clk_50m` 55.48 MHz,
`clk_core` 102.46 MHz against the 12 MHz target). After SRAM load,
`rp2350_spu_diag` reports `status raw=13 A5 00 00`; manual `rplu` advances
`cfgtele` to count 1; and SD hydration advances count 0 to 16 with checksum
`0x3A0AB5E9`.

RPLU v2 consume-profile hydration is also proven over the RP2350 southbridge
path on the full SPU-13 image. The corrected 149-record profile from
`tools/gen_rplu2_tables.py --profile consume_probe` streams over command
`0xA5`; final `cfgtele` reports count 149, last record `sel=6 material=0
addr=0 data=0x0000000000000003`, legacy checksum `0xBA708FD4`,
`rplu2_sum=0x0AA480E7`, `rplu2_status=0xC02E0001`, `rplu2_num0=0x00000002`,
`rplu2_delta=0x00000000`, `rplu2_row1=0x00000001`, and
`rplu2_kappa=0x00000003`. The rebuilt image, including SPI `S_FILL` CS-abort
recovery, routes at `clk_50m` 133.55 MHz and `clk_core` 67.76 MHz against the
12 MHz target.

The pre-rework raw diagnostics were:

| CS# | SCK | MOSI/CMD | MISO/DAT0 | `sdprobe` MISO observation | `sdcmd` result |
|:---:|:---:|:---:|:---:|:---|:---|
| GP13 | GP10 | GP11 | GP12 | externally high/pulled up | CMD0/CMD8 `0xFF` |
| GP6 | GP10 | GP11 | GP9 | externally low/no pull-up | CMD0/CMD8 `0x00` |
| GP6 | GP10 | GP11 | GP12 | externally high/pulled up | CMD0/CMD8 `0xFF` |
| GP13 | GP10 | GP11 | GP9 | externally low/no pull-up | CMD0/CMD8 `0x00` |

Keep the default map (`GP13/GP10/GP11/GP12`) as the active wiring. If failures
return, check the physical SD pins first: VCC at the socket, common ground,
CLK continuity from GP10, CMD/MOSI from GP11, DAT3/CS from GP13, and DAT0/MISO
to GP12.

### Bench Electrical Checks

Before powering both boards together:

1. Confirm continuity: RP2350 GP1/GP2/GP3/GP0 reach J4-1/J4-2/J4-3/J4-4
   respectively, and RP2350 GND reaches J4-5.
2. Confirm no shorts between adjacent signal pins, signal-to-3V3, or
   signal-to-GND.
3. Confirm both logic domains are 3.3 V LVCMOS. Do not connect 5 V to any
   FPGA or RP2350 GPIO.
4. With firmware idle, CS# should be high, SCK low, and MOSI not fighting any
   other driver. MISO may be low when the FPGA bitstream is running because the
   slave drives idle low.
5. Add or enable a CS# pull-up if the FPGA can be configured while the RP2350 is
   reset or disconnected; the SPI slave should see CS# high unless selected.

---

## SPI Slave State Machine

The FPGA implements an 11-state machine. The original response and fixed-size
write path is unchanged; the optional TGR1 path adds prefix, payload, and CRC
receive states.

```
                     ┌─────────────────────────────┐
                     │         S_IDLE              │
                     │  Waiting for CS assertion   │
                     └──────────────┬──────────────┘
                                    │ cs_active
                                    ▼
                     ┌─────────────────────────────┐
                     │         S_CMD               │
                     │  Receiving 8-bit command    │
                     │  (8 SCK rises)              │
                     └──────────────┬──────────────┘
                                    │ bit_cnt==7 && sck_rise
                                    ▼
                     ┌─────────────────────────────┐
                     │         S_FILL              │
                     │  Load resp_buf & preset MSB │
                     │  (wait for cmd SCK fall)    │
                     └──────┬──────────────────────┘
                            │ sck_fall
                ┌───────────┼────────────────────────┐
                ▼           ▼                        ▼
        ┌─────────────┐ ┌────────────┐ ┌──────────────────┐
        │  S_RESP     │ │S_RECV_HDR  │ │  S_RECV_INST     │
        │ Tx response │ │ Rx 64-bit  │ │  Rx 64-bit       │
        │             │ │ HEADER     │ │  instruction     │
        └─────┬───────┘ └────┬───────┘ │  then RPLU DATA  │
              │              │         │  in S_RECV_DATA  │
              │              │         └──────┬───────────┘
              └──────────────┼────────────────┘
                             │ cs inactive
                             ▼
                     ┌─────────────────────────────┐
                     │         S_IDLE              │
                     └─────────────────────────────┘
```

**States:**
| State | Role | Exit Condition |
|:---:|:---|:---|
| `S_IDLE` | Idle, waiting for CS | CS asserted (cs_active ← CS#) |
| `S_CMD` | Receive 8-bit command byte | 8 bits received + sck_rise |
| `S_FILL` | Prepare response buffer | sck_fall (consume trailing cmd clock) or CS abort |
| `S_RESP` | Transmit response bytes | CS deasserted or all bytes sent |
| `S_RECV_HDR` | Receive 64-bit RPLU header | 64 bits received on sck_rise |
| `S_RECV_DATA` | Receive 64-bit RPLU data | 64 bits received + hdr check |
| `S_RECV_INST` | Receive 64-bit instruction | 64 bits received on sck_rise |
| `S_RECV_CRC` | Receive CRC-8 for B1/A5 | 8 bits received on sck_rise |
| `S_RECV_TGR_PREFIX` | Receive TGR1 length and vector ID | 48 bits received on sck_rise |
| `S_RECV_TGR_DATA` | Stream the length-delimited TGR1 payload | declared byte count received |
| `S_RECV_TGR_CRC` | Receive and decide TGR1 transport CRC-8 | 8 bits received on sck_rise |

---

## Command Reference

### Read Commands (0xA0 – 0xB0)

#### **0xA0 — Manifold Burst** (32 bytes)
**Response:** Four 13-surd RationalSurd values (axes 0–3)

**Format (big-endian):**
```
Byte  Content
────  ─────────────────────────────────────────
0–1   Axis 0, Rational part (P), int16 signed
2–3   Padding (0x0000)
4–5   Axis 0, Surd part (Q), int16 signed
6–7   Padding (0x0000)
8–15  [same for Axis 1]
16–23 [same for Axis 2]
24–31 [same for Axis 3]
```

**Interpretation:**
- Each axis is a **RationalSurd** with layout `{P:16, Q:16}` (upper 16 = P, lower 16 = Q)
- Mathematical value: `real_value = P + Q * sqrt(3)`
- Both P and Q are **signed 16-bit** integers
- Padding bytes are always `0x00` (reserved for future use)

**Example:**
```
RP2350 sends: 0xA0
FPGA returns: [Axis0_P_hi, Axis0_P_lo, 0x00, 0x00, Axis0_Q_hi, Axis0_Q_lo, ...]
```

---

#### **0xAC — Status** (4 bytes)
**Response:** System status flags and manifold index

**Format:**
```
Byte  Bits        Content
────  ────────    ───────────────────────────────────────
0–1           Laminar Index (big-endian uint16)
               Fibonacci sequencer position (0–∞)
2         [7:5] RPLU Ratio result (signed, sticky)
          [4]   RPLU Ratio valid (sticky, cleared on read)
          [3]   FIFO full (RP2350 instruction queue at limit)
          [2]   Turbulence (Davis Gate anomaly detected)
          [1]   Janus point (dual-polarity transition)
          [0]   Satellite snap lock (SPU-4 phase lock)
3         [7:3] Reserved (0)
          [2]   Boot FSM READY (see BOOT_SEQUENCE_FSM.md §3.6)
          [1]   CRC error (sticky, cleared on read)
          [0]   RPLU mode bank (0=Smooth, 1=Turbulent)
```

**Fields:**
- **Laminar Index:** Phase counter (increments at Fibonacci intervals: 8, 13, 21 cycles)
- **RPLU Ratio:** `-1`, `0`, or `+1` from RPLU comparator (sticky, auto-clears after 0xAC read)
- **FIFO Full:** Set if instruction queue is full
- **Turbulence:** Set if Davis Gate detected manifold leak (Cubic Leak)
- **Janus Point:** Set when manifold crosses dual-polarity boundary
- **Satellite Snap:** SPU-4 Sentinel lock indicator
- **RPLU Mode:** Current active RPLU bank (0 = default, 1 = alternate) — byte 3 bit 0
- **CRC Error:** Set if the last B1, A5, or B2 write had a CRC-8 mismatch —
  byte 3 bit 1, clears on 0xAC read

---

#### **0xAD — Scale Table** (9 bytes)
**Response:** M31 arithmetic scale factors and overflow flags

**Format:**
```
Byte  Content
────  ──────────────────────────────────────────
0–6   Scale table (52-bit ÷ 8 = 6.5 bytes)
7–8   Overflow flags (13-bit ÷ 8 = 1.625 bytes)
```

- **Bytes 0–6:** Scaling exponents for M31 normalization (Mersenne prime 2^31 − 1)
- **Bytes 7–8:** Overflow counters for each scale lane

---

#### **0xAE — QR Commit** (34 bytes)
**Response:** Last committed Quadray register write

**Format:**
```
Byte  Content
────  ───────────────────────────────────────────
0     Valid flag (bit 0 = 1 if valid, else 0)
1     QR lane index (4-bit, 0–13)
2–9   Component A (64-bit big-endian RationalSurd)
10–17 Component B (64-bit big-endian RationalSurd)
18–25 Component C (64-bit big-endian RationalSurd)
26–33 Component D (64-bit big-endian RationalSurd)
```

- **Valid:** Set after a QR commit and remains set until another commit overwrites the latched value or reset clears it
- **Lane:** Which QR lane was written (0–13 for spu13_core, 0–3 for spu4_core)
- **A/B/C/D:** Four 64-bit components of the committed Quadray

---

#### **0xAF — HEX Projection** (5 bytes)
**Response:** Last Hex coordinate projection result

**Format:**
```
Byte  Content
────  ────────────────────────────────────
0     Valid flag (bit 0 = 1 if valid, else 0)
1–2   Hex Q coordinate (signed int16, big-endian)
3–4   Hex R coordinate (signed int16, big-endian)
```

- **Valid:** Set if a HEX projection has occurred since last read
- **Q, R:** Axial hex coordinates (hexagonal grid system)
- Auto-clears after read

---

#### **0xB0 — Opaque Telemetry Burst** (64 bytes)

**RESOLVED 2026-08-16.** This entry previously documented `0xB0` as
"Sentinel Telemetry, 8 nodes x 8 bytes" and then flagged a discrepancy with
the firmware. The discrepancy was real, and the resolution is that **the
documentation was over-specified, not the RTL wrong.**

**Wire format: 64 opaque bytes. That is the whole wire contract.**

`spu_spi_slave.v` streams `sentinel_telemetry[511:0]` big-endian, byte 0 from
bits 511:504. It imposes no structure whatsoever on the payload. The 512-bit
port is driven by whichever top instantiated the slave, and different tops
legitimately carry different telemetry:

| Top | Drives the port with | Payload |
|---|---|---|
| `spu13_tang25k_fpga_top.v`, `southbridge_spi_top.v`, `spu_a7_top.v` | `southbridge_telemetry` | RPLU2 config/write telemetry, `SPUC` magic |
| `spu13_tang25k_fpga_smoke_top.v`, `spu_a7_tensegrity_link_top.v` | `512'd0` | all zeros |
| `spu_system.v` | 8x `debug_reg_r0` | the 8-node sentinel layout |

**The 8-node sentinel layout is not reachable on any current bitstream.**
`spu_system.v` is referenced only from `hardware/boards/tang_primer_25k/archive/`
scripts, by no live `.ys`, and by no testbench (verified 2026-08-16). The
layout this section used to lead with is the one nobody can build.

### Payload discrimination is mandatory

Because the wire format is opaque, **bytes 0-3 are a payload magic** and a
caller MUST check it before interpreting anything after it.

| Magic | Bytes 0-3 | Meaning | Status |
|---|---|---|---|
| `SPUC` | `53 50 55 43` | RPLU2 config/write telemetry: `count` (2B), last-write `sel`/`material`/`addr`/`data`, `checksum` (4B), and six RPLU2 telemetry words when `count == 149` or an RPLU2 status bit is set | **The only payload currently shipped.** Decoded by `cmd_cfgtele` in `hardware/rp_common/spu_diag.c`, and matches every bring-up log in this document |
| — | `00 00 00 00` | No telemetry wired. Reserved; never allocate a real payload to this value | Emitted by the smoke and tensegrity-link tops |
| *(none)* | — | 8-node sentinel layout | **Carries no magic and is therefore undiscriminable.** Not currently reachable. **Reviving it requires allocating and emitting a magic first** — that is a precondition, not a nicety |

**Any future payload on `0xB0` must declare a magic here before it is
emitted by any bitstream.** A payload without one cannot be told apart from
another, which is the defect this section resolves.

### Why this does not violate compatibility rule 1

Rule 1 says an opcode's response format never changes. It has not: `0xB0`
has always been 64 opaque bytes at the wire level, and still is. What changed
is this document, which previously described one particular *payload schema*
as if it were the wire format. Correcting an over-specified description is not
a format change, and no bitstream moves as a result of this edit.

The general principle, now rule 5 in the compatibility section: an opcode
whose payload varies by build must be documented as opaque **and** must carry
a self-describing magic. An opcode whose meaning silently depends on which
bitstream answered it is a protocol defect regardless of how well each
individual meaning is documented.

---

### Write Commands (0xB1, 0xA5, 0xB2)

#### **0xB1 — Instruction Write** (Recv: 64 bits + 8 CRC)
**Role:** Stream a single 64-bit SPU instruction/chord

**Sequence:**
1. RP2350 sends: `0xB1` (8 bits)
2. FPGA latches command
3. RP2350 sends: 64-bit instruction (MSB first)
4. FPGA asserts `inst_valid` for one cycle, loads `inst_word`
5. RP2350 sends: 8-bit CRC-8-CCITT (polynomial 0x07) over command byte + payload
6. FPGA transitions to S_RECV_CRC, compares CRC, sets `crc_error_sticky` on mismatch

**Instruction Format (64-bit):**
```
Bits   Field
────   ─────────────────────────────────────────
63:56  Opcode (e.g., 0x0A = QLDI, 0x2A = SOM)
55:48  Operand 1 (register lane, immediate, or flags)
47:0   Extended operand (depends on opcode)
```

**Example (QLDI opcode):**
```
RP2350 sends: 0xB1 0x0A ... (64 bits total)
→ Load immediate quadray into QR[0]
→ inst_word = 0x0A<48-bit immediate>
```

---

#### **0xA5 — RPLU Config Write** (Recv: 128 bits + 8 CRC)
**Role:** Program RPLU runtime configuration table

**Sequence:**
1. RP2350 sends: `0xA5` (8 bits)
2. FPGA switches to S_RECV_HDR
3. RP2350 sends: 64-bit HEADER
4. FPGA switches to S_RECV_DATA
5. RP2350 sends: 64-bit DATA
6. FPGA decodes HEADER, asserts `rplu_cfg_wr_en` (1 cycle)
7. RP2350 sends: 8-bit CRC-8-CCITT over command byte + payload
8. FPGA transitions to S_RECV_CRC, compares CRC, sets `crc_error_sticky` on mismatch

**HEADER Format (64-bit big-endian):**
```
Bits   Field
────   ───────────────────────────────────
63:56  Magic (0xA5 = valid header marker)
55:51  Reserved (must be 0)
50:48  RPLU selector (sel = table/profile ID, 0–7)
47:44  Material type (4-bit, 0–15)
43:34  Address within material (10-bit, 0–1023)
33:0   Reserved (must be 0)
```

**DATA Format (64-bit):**
```
Bits   Field
────   ─────────────────────────────────────────
63:0   Configuration data (A₃₁ coefficients, routing table, etc.)
```

**Output Signals (asserted for 1 cycle after DATA received):**
- `rplu_cfg_wr_en` ← 1
- `rplu_cfg_sel` ← HEADER[50:48]
- `rplu_cfg_material` ← {4'b0, HEADER[47:44]}
- `rplu_cfg_addr` ← HEADER[43:34]
- `rplu_cfg_data` ← DATA[63:0]

**Example (Loading RPLU v2 M31 multiplier config):**
```
RP2350 sends:
  0xA5                           # RPLU config command
  0xA5_03_50_3C_00000000         # HEADER: sel=3, material=5, addr=15
  0xDEADBEEFCAFEBABE             # DATA: Padé coefficient or BTU entry

FPGA responds:
  (MISO held low during receive phase)

After DATA received:
  rplu_cfg_wr_en   ← 1 (1-cycle pulse)
  rplu_cfg_sel     ← 3'd3
  rplu_cfg_material← 8'd5
  rplu_cfg_addr    ← 10'd15
  rplu_cfg_data    ← 64'hDEADBEEFCAFEBABE
```

---

#### **0xB2 — TGR1 Transactional Load** (Recv: 6-byte prefix + table + CRC)

This optional command streams one complete TGR1 table into the inactive
sidecar bank. All multi-byte fields are big-endian and the entire transaction
must remain under one CS# assertion:

```text
byte 0        command = 0xB2
bytes 1..2    TGR1 table length, uint16 (12..508)
bytes 3..6    caller vector ID, uint32
bytes 7..N    exactly `length` TGR1 bytes
byte N+1      CRC-8-CCITT over command + prefix + table
```

The TGR1 header contains its own CRC-32 over the table payload. The transport
CRC-8 protects framing; the payload CRC-32 protects the stored representation.
After a valid transport commit the sidecar parses the inactive BRAM bank,
replays its nodes and edges through the admission guard, and switches the
active bank only when verification reaches a coherent terminal verdict.
Malformed headers, length/count violations, invalid records, CRC failure, CS#
abort, and deadman timeout preserve the previous active bank and verdict.

The maximum is the bounded hardware profile: 12 nodes and 40 edges, or
`12 + 12*28 + 40*4 = 508` bytes. The canonical 12-node/30-edge table is 468
bytes and its complete B2 wire transaction is 476 bytes.

#### **0xB3 — TGR1 Status** (Response: 16 bytes)

The first eight bytes are the frozen TGR1 status record. The following eight
bytes are transport/loader diagnostics:

| Byte(s) | Field |
|---|---|
| 0 | TGR1 ABI version (`1`) |
| 1 | active balancer state |
| 2 | active terminal fault |
| 3 | verifier service stage; bit 7 marks watchdog timeout |
| 4–7 | active vector ID, uint32 |
| 8 | flags: bit 3 active-valid, bit 2 verify-busy, bit 1 RX-busy, bit 0 error-present |
| 9 | loader error |
| 10 | active node count |
| 11 | active edge count |
| 12–13 | bytes received in the last load, uint16 |
| 14–15 | bytes expected in the last load, uint16 |

Loader error values are: `0` none, `1` transport abort/CRC, `2` magic,
`3` version, `4` flags, `5` bounds, `6` length, `7` payload CRC-32,
`8` node record, `9` edge record, `10` guard-service watchdog timeout, and
`11` parser watchdog timeout. Guard service stages are: `0` idle, `2`
topology, `3` connectivity, `4` local member guards, `5` exact strut
intersection, `6` exact equilibrium, `7` decision, and `8` terminal result.
Parser substates occupy `0x11` through `0x1A`; their low nibble is the private
replay substate. A guard timeout leaves `0x80 | service`, while a parser
timeout leaves `0x90 | substate`, so the exact bounded failure survives after
verify-busy clears.
A nonzero diagnostic error describes
the rejected staging transaction; bytes 1–7 continue to report the last
committed active verdict.

---

## Protocol Timing

### Slave Sampling & Drive Times

| Phase | Timing |
|:---:|:---|
| **Command** | 8 × SCK cycles |
| **Response load** | 1 × selected southbridge clock |
| **MISO setup** | < 50 ns (combinational) |
| **MISO hold** | 0 ns (already stable) |
| **Max freq** | **`clk_fast / 6`** — a ratio, not a constant. See below. |

### Maximum SCK is a ratio, not a fixed frequency

`spu_spi_slave` treats SCK as *data*: it is sampled by the fabric clock through
a 3-deep shift register and edge-detected on `sck_r[2:1]`. The usable SCK
therefore scales with whatever `clk_fast` the spin actually runs at, and there
is no single safe frequency for the protocol as a whole.

**Measured bound: `SCK <= clk_fast / 6`.** Established by
`hardware/tests/common/spu_spi_slave_ratio_tb.v`, which sweeps the SCK:fabric
ratio against a known 0xAC response at four sub-clock phase offsets and requires
every offset to pass:

| Ratio `N` | Result |
|---|---|
| `>= 6` | PASS at all four phase offsets |
| `5` | FAIL at 2 of 4 phase offsets |
| `<= 4` | FAIL at all four phase offsets |

Ratio 5 passing at *some* phases is why an over-clocked link can look healthy on
the bench and then fail intermittently: the margin is phase-dependent. Use 6 as
the floor, and prefer more.

### Confirmed in silicon, 2026-08-01

The bound above was simulation-derived when written. It has now been measured on
the bench, and both halves of it reproduced.

**Setup.** Wukong `TENSEGRITYLINK` over the J11 southbridge link, driven by
`rp2350_spu_diag` rebuilt at each rate. Probe was `0xB3` `tgrstatus`, whose byte 0
is a constant `1` in RTL: `version=1` means the read path works, `0` means it
does not. Binary, no interpretation. Ratios below are against this spin's **real**
25 MHz slave clock (see the caution after the table), and use the rate
`spi_init()` actually achieved, not the rate requested.

| SCK achieved | ratio | result |
|---:|---:|---|
| 125 kHz – 1.97 MHz | ≥ 12.7 | PASS |
| 3.947 MHz | 6.33 | PASS |
| 4.167 MHz | 6.00 | PASS |
| 4.412 MHz | 5.67 | **FAIL, then PASS ×3 on a later session** |
| 5.000 MHz | 5.00 | **PASS, then FAIL ×3 on a later session** |
| 5.357 MHz | 4.67 | FAIL |
| 5.77 – 10.7 MHz | ≤ 4.33 | FAIL |

**Every observation at ratio ≥ 6 passed. Every rate below 6 was unreliable** —
stable within one configuration cycle, but inverting between them. 4.412 MHz and
5.000 MHz each flipped verdict across sessions while repeating 3/3 within one.

That is not noise and not a frequency threshold: it is the phase relationship
between SCK and the sampling clock, fixed at configuration and re-rolled on the
next load. It is the same effect
`hardware/tests/common/spu_spi_slave_ratio_tb.v` reports when it fails ratio 5 at
2 of 4 phase offsets — which is why that bench sweeps phase instead of testing a
single alignment, and why a single-phase test would have called ratio 5 safe.

**Practical consequence: never operate below ratio 6.** A link at ratio 5 can pass
an entire bench session convincingly and then fail after an unrelated reconfigure,
with nothing in between to explain it.

> The bound still accounts for the synchronizer and Mode-0 MISO turnaround only —
> not PMOD ribbon skew or connector loading. On this bench, with 100 Ω series
> resistors on all four signal lines, signal integrity did **not** bind before the
> synchronizer did: the failure arrived exactly where the ratio predicted. Treat
> `clk_fast / 6` as a ceiling to stay well under, not a target to hit.

> **Check which top a spin uses before applying the per-spin table below.**
> `TENSEGRITYLINK` does not instantiate `spu_a7_top.v` at all — it has its own top,
> `spu_a7_tensegrity_link_top.v`, which clocks `u_spi` from `guard_clk`, a
> divide-by-2 of the 50 MHz `sys_clk`. Its slave therefore runs at **25 MHz** with
> a **4.17 MHz** ceiling, and `A7_CLK_DIV_LOG2` never enters into it. Reasoning
> from `spu_a7_top.v`'s spin lists gave the wrong answer here and was corrected by
> the sweep.

### Per-spin ceiling on the Wukong Artix-7 100T

The Wukong board oscillator is **50 MHz**. (The port is named `clk_100mhz`; the
name is a misnomer. The XDC declares `-period 20.000`, `surd_uart_tx` is
instantiated with `CLK_HZ(50_000_000)`, the raw UART uses `BAUD_DIV = 434`
= 50 MHz/115200, and every host tool opens the port at 115200 — four
independent agreements.)

**Confirmed on hardware 2026-07-31** — see "Confirming the oscillator" below.
This resolves a 2× discrepancy: `AGENTS.md` recorded the 2026-07-14 Nyquist
finding as "2 MHz SPI against a **1.5625 MHz** `clk_fast`", which is 100 MHz/64
and so assumed a 100 MHz oscillator. The measured clock is 50 MHz, making the
divided `clk_fast` **781.25 kHz**, not 1.5625 MHz. Both readings always agreed
the link was over-clocked and agreed on the fix; they disagreed on the
core-spin ceiling by 2× (130 kHz vs 260 kHz). **130 kHz is correct.**

### Confirming the oscillator

The board's own UART is the instrument — no scope, counter, or logic analyzer
needed. `spu_a7_uart_probe_top.v` divides the raw board clock with
`BAUD_DIV = 434`, which yields 115200 baud **only** if that clock is 50 MHz
(a 100 MHz clock would put the line at 230400). So the baud at which its output
is legible *is* the oscillator measurement.

```sh
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_UARTPROBE.bit
python3 tools/uart_baud_probe.py            # defaults to /dev/ttyUSB0
```

Result on this unit:

```
=== 115200 baud: 24 bytes, 100.0% printable ===
  hex : 55 41 52 54 3a 50 0d 0a 55 41 52 54 3a 50 0d 0a ...
  text: UART:P..UART:P..UART:P..
```

Legible `UART:P` at 115200 → **50 MHz**. Garbage at 115200 that cleans up at
230400 would have meant 100 MHz and a 260 kHz core-spin ceiling.

> **Do not use `stty` followed by `cat` for this.** The termios setting is reset
> when `cat` opens the port, so every baud returns byte-identical data and the
> test silently produces the same wrong answer at every rate. The baud must be
> set and the read performed on the **same file descriptor** —
> `tools/uart_baud_probe.py` does this, and `probe_tang25k_rplu_flash.py`'s
> `configure_tty` is the existing in-repo precedent.

A second, independent witness exists if the UART is ever unavailable:
`heartbeat_ctr` (`spu_a7_top.v:154`) is a 27-bit free-running counter on the raw
board clock, and bit 26 is emitted as the `HB:` field of the `DIAG HB:` line
when built with `A7_UART_DIAG=1`. It toggles every 2²⁶ clocks — **1.342 s at
50 MHz, 0.671 s at 100 MHz** — so ten flips take ~13.4 s versus ~6.7 s, a
difference a stopwatch resolves easily. Note `led_out` is tied off on this
particular Wukong (`spu_a7_top.v:1153`, suspect I/O bank), so the LED route is
not a valid witness on this unit.

`A7_FREQ` is passed to `nextpnr --freq` as a **timing constraint only**. It does
not divide the clock. The physical `clk_fast` is set by `A7_CLK_DIV_LOG2` in
`spu_a7_top.v`:

| Spin class | `A7_CLK_DIV_LOG2` | actual `clk_fast` | **SCK ceiling** |
|---|---|---|---|
| Coreless (`LUCAS`, `SU3`, `RPLUCFG`, `RPLU2LIVE`, `RPLU2PADE`, `SOM*`, `TENSEGRITY*`) | 0 (raw) | 50 MHz | **8.3 MHz** |
| Core spins (all others, incl. `IROTC`) | 6 (`/64`) | 781.25 kHz | **130 kHz** |

The two classes differ by **64×**. A baud rate that is safe on a coreless spin
can be an order of magnitude over the limit on a core spin, which is exactly the
2026-07-14 Wukong bring-up failure: 2 MHz SCK against a divided fabric clock.

### `A7_FREQ=2` suppresses the timing check — it does not slow anything down

Nearly every documented Artix-7 build command passes `A7_FREQ=2`, while
`build_a7.sh:122-127` already defaults it to 50 for all spins except `IROTC`
(2) and the tensegrity pair (25). The consequence is worth stating plainly,
because the combination is easy to misread as a low-speed profile:

- For every coreless spin in the table above, `A7_CLK_DIV_LOG2 = 0`, so
  **`clk_fast` is the 50 MHz board clock on silicon** regardless of `A7_FREQ`.
- `--freq 2` therefore does not produce a 2 MHz design. It lowers the bar the
  router must clear, so nextpnr stops optimising early and reports
  `PASS at 2.00 MHz` for a design that will run at 50 MHz.
- These spins are consequently **unclosed at their real operating frequency**
  and work on margin. Measured on the two Padé builds: v1 routes at
  38.18 MHz and v2 at 29.64 MHz, both reported as `PASS at 2.00 MHz`, and the
  silicon pass/fail split follows that ordering (`SESSION_HANDOVER_2026-08-03.md`).

This applies to the **coreless** class only. Core spins run
`A7_CLK_DIV_LOG2 = 6`, so `clk_fast` is 781.25 kHz and `--freq 2` is an
*over*-constraint — correct, and stricter than the hardware needs. The
`A7_FREQ=2 A7_CLK_DIV_LOG2=6` commands documented for `rplu2core` and
`su3share` are sound as written and want no change. nextpnr constrains the
generated `clk_fast` by name, which is why the figure is comparable to the
divided clock rather than to the 50 MHz pad.

**Do not "fix" this by deleting `A7_FREQ=2` from the build commands.** A routed
timing *miss* is an `ERROR` in nextpnr, not a warning, and `build_a7.sh:20` runs
`set -euo pipefail`, so a build that fails to close produces no bitstream at all
— observed on `FP4EVIDENCE` seeds 23 and 29, which ended `0 warnings, 1 error`
at `--freq 50`.

Whether any given spin *would* close at 50 is untested and not predictable from
the numbers above: a build constrained at 2 MHz stops optimising as soon as it
clears 2 MHz, so its reported figure is a floor, not a measurement of what the
router could reach. The same `FP4EVIDENCE` design ranged from 21.85 MHz to
68.04 MHz at `--freq 50` across seeds. Raising a spin's constraint is therefore
a per-spin experiment — rebuild, check it closes, then re-test on silicon —
never a docs edit.

Caveat in the other direction: nextpnr's absolute numbers are demonstrably
pessimistic on this board — the 2026-07-03 LUCAS build reported `clk_fast` max
**4.79 MHz** and has passed on silicon at 50 MHz ever since. What the Padé
result makes suggestive is the *ordering* between two builds of the same design,
not the absolute figure.

Current firmware defaults measured against these ceilings:

| Firmware | baud | target spin class | ratio | verdict |
|---|---|---|---|---|
| `rp2350_lucas_j11_smoke.c` | 2 MHz | coreless | 25 | safe |
| `rp2350_su3_j11_smoke.c` | 25 kHz | coreless | 2000 | safe, **333× conservative** |
| `rp2350_rplu2_pade_j11_smoke.c` | 25 kHz | coreless | 2000 | safe, **333× conservative** |
| `rp2350_spu_irotc_test.c` | 25 kHz | core (`/64`) | 31 | safe |
| `rp2350_spu_diag.c` | 250 kHz | core (`/64`) | **3.1** | **OVER — below the ratio-6 floor** |
| `rp2350_spu_interface.c` | 2 MHz | either | 0.39 on core | **OVER on core spins** |

The 25 kHz defaults are bring-up conservatism carried over from the 07-14
Nyquist debugging, not measured limits. On coreless spins they leave two orders
of magnitude of headroom.

### Clock Synchronization
- All SCK edges are **metastability-hardened** with 2-stage synchronizers (`sck_r[2:0]`)
- CS# and MOSI also synchronized
- Minimizes jitter from async SPI edges

### CS# Assertion to Response

1. **CS# asserts** (falls from 1 → 0)
2. **cs_fall detected** → Manifold snapshot latched (all 4 axes + scale + sentinel)
3. **Next SCK rise** → cmd_byte[7] clocked in
4. **After 8 SCK rises** → cmd_byte complete; state → S_FILL
5. **Next SCK fall** → resp_buf filled, shift_out preset, MISO set to byte[7]
6. **Next SCK rise** → MISO bit 7 sampled, bit 6 preset
7. **Continue until resp_len bytes sent** → MISO = 0
8. **CS# deasserts** (rises from 0 → 1) → state → S_IDLE

At 2 MHz, the 8-bit command phase takes 4 us. After the command byte, the first
response bit is available on the next command-trailing SCK fall plus the FPGA
synchronizer latency.

---

## RP2350 Integration Example

### Read Manifold + Status

```c
#include "hardware/spi.h"
#include "hardware/gpio.h"

void read_manifold_and_status(void) {
    // Set CS# low
    gpio_put(SPU_SPI_CS_PIN, 0);

    // Send 0xA0 command
    uint8_t cmd = 0xA0;
    spi_write_blocking(spi0, &cmd, 1);

    // Read 32 bytes (4 axes × 8 bytes)
    uint8_t manifold[32];
    spi_read_blocking(spi0, 0x00, manifold, 32);

    // Parse: Axis 0 = {manifold[0:1] (P), manifold[4:5] (Q)}
    int16_t p0 = (manifold[0] << 8) | manifold[1];
    int16_t q0 = (manifold[4] << 8) | manifold[5];
    printf("Axis 0: P=%d, Q=%d\n", p0, q0);

    // Set CS# high (transaction complete)
    gpio_put(SPU_SPI_CS_PIN, 1);

    // Wait ~100 ns before next transaction
    busy_wait_us(1);

    // Next transaction: read status
    gpio_put(SPU_SPI_CS_PIN, 0);
    cmd = 0xAC;
    spi_write_blocking(spi0, &cmd, 1);

    uint8_t status[4];
    spi_read_blocking(spi0, 0x00, status, 4);

    uint16_t laminar = (status[0] << 8) | status[1];
    uint8_t flags = status[2];
    printf("Laminar: %u, Flags: 0x%02X\n", laminar, flags);

    gpio_put(SPU_SPI_CS_PIN, 1);
}
```

### Write RPLU Config

```c
void write_rplu_config(uint8_t sel, uint8_t material, uint16_t addr, uint64_t data) {
    gpio_put(SPU_SPI_CS_PIN, 0);  // CS# low

    // Command
    uint8_t cmd = 0xA5;
    spi_write_blocking(spi0, &cmd, 1);

    uint64_t header_word = ((uint64_t)0xA5 << 56) |
                           ((uint64_t)(sel & 0x7) << 48) |
                           ((uint64_t)(material & 0xF) << 44) |
                           ((uint64_t)(addr & 0x3FF) << 34);
    uint8_t header[8];
    for (int i = 0; i < 8; i++) {
        header[i] = (header_word >> (56 - i*8)) & 0xFF;
    }
    spi_write_blocking(spi0, header, 8);

    // DATA: 64-bit config value
    uint8_t data_bytes[8];
    for (int i = 0; i < 8; i++) {
        data_bytes[i] = (data >> (56 - i*8)) & 0xFF;
    }
    spi_write_blocking(spi0, data_bytes, 8);

    gpio_put(SPU_SPI_CS_PIN, 1);  // CS# high
    busy_wait_us(1);
}
```

---

## Error Handling

### Unexpected CS# Deassert
If CS# deasserts before command/response is complete:
- State machine returns to S_IDLE immediately
- Partial data is discarded
- Next CS# assertion starts fresh

**Recommended:** RP2350 firmware should validate response length matches expected command.

### Unknown Commands
If FPGA receives unrecognized opcode:
- Enters S_RESP with resp_buf[0] = 0x00, resp_len = 1
- Returns single zero byte
- Returns to S_IDLE

**Recommended:** Document all valid opcodes and validate on master side.

### Hung Transactions
If RP2350 stops clocking SCK while CS# is active:
- FPGA state machine remains in active state (S_CMD, S_RESP, S_RECV_*, S_RECV_CRC)
- **Deadman timer:** 128-cycle timeout (≈2.6 µs at 50 MHz or 5.1 µs at
  25 MHz) resets to S_IDLE if no SCK edge arrives; an in-flight B2 staging
  transaction is aborted
- RP2350 must assert CS# if transaction times out

**Recommended:** RP2350 firmware should implement SCK watchdog (~10 ms timeout).

---

## Testing & Validation

### Testbench Verification
All protocol paths verified in `hardware/tests/common/spu_spi_slave_tb.v`:
- ✓ Read commands: 0xA0, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0
- ✓ Write commands: 0xB1, 0xA5
- ✓ CS# deassert during transaction (rollback)
- ✓ 149-record RPLU write burst followed by status and sentinel reads
- ✓ Manifold snapshot latching
- ✓ Sticky state (QR/HEX valid bits)
- ✓ Timing margins at 2 MHz

Optional TGR1 paths are verified in
`hardware/tests/spu13/spu13_tensegrity_transport_tb.v`:
- ✓ Valid B2 load through the real SPI slave and exact 16-byte B3 response
- ✓ Bad transport CRC preserves the active bank/verdict and reports error 1
- ✓ Stalled B2 trips the 128-cycle deadman, aborts staging, and preserves the
  active bank/verdict
- ✓ B3 status remains coherent when a guard result completes during the read;
  commit is held and its one-cycle result is remembered until CS# deasserts
- ✓ Base eight-opcode testbench still passes with the extension disabled

**Test Status:** PASS (`spu_spi_slave_tb.v` and
`spu13_tensegrity_transport_tb.v`)

### Hardware Validation (Tang Primer 25K)
When southbridge bitstream is tested with RP2350:
1. Build and SRAM-load the Tang 25K southbridge bitstream.
2. Flash `rp2350_spu_diag.uf2` built for the selected SPI pin profile.
3. Test `0xAC` status and `0xA0` manifold reads before enabling writes.
4. Test `0xB1` instruction writes, then `0xA5` RPLU config writes.
5. Prove SD separately with `spu_sd_test.uf2`; only then use SD-backed
   hydration commands from the RP2350 diagnostic console.

For the Wukong `TENSEGRITYLINK` spin, use the remapped J11 bottom row recorded
in `spu_a7_tensegrity_link.xdc`: GP1/GP2/GP3/GP0 to J11 pins 7/8/9/10, common
ground, and 100-ohm series resistance on all four signals. Never leave the
RP2350 powered and driving while the FPGA board is unpowered. The diagnostic
console commands are `tgrload <path.tgr> [vector_id]` and `tgrstatus`.
`tgrloadbadcrc <path.tgr> [vector_id]` is a bench-only negative test: it
corrupts one payload byte in RP RAM while retaining a valid link CRC-8, so the
FPGA's independent TGR1 CRC-32 rejection can be observed.  On 2026-07-19 the
full combined image admitted the canonical table, committed the genuine
not-in-equilibrium fixture, preserved that active verdict after the corrupt
payload returned error 7, and recovered on canonical reload.  The complete
sequence passed three consecutive times over the remapped link.

---

## Appendix: Big-Endian Byte Ordering

All multi-byte fields in the SPI protocol are transmitted **MSB first** (big-endian).

**Example:** 32-bit value `0xDEADBEEF`
```
SPI transmission: 0xDE, 0xAD, 0xBE, 0xEF
(first byte sent has MSB)
```

**RationalSurd in 0xA0:**
```
If P=0x1234, Q=0x5678:
  resp_buf[0] = 0x12  (P high byte)
  resp_buf[1] = 0x34  (P low byte)
  resp_buf[4] = 0x56  (Q high byte)
  resp_buf[5] = 0x78  (Q low byte)
```

---

## References

- **RTL Module:** `hardware/rtl/peripherals/io/spu_spi_slave.v` (510 lines)
- **Testbench:** `hardware/tests/common/spu_spi_slave_tb.v` (PASS)
- **RP2350 Interface:** `hardware/rp2350/rp2350_spu_interface.c`
- **Board Config:** `hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst`

---

**Document End**
CC0 1.0 Universal — Public Domain
