# Sovereign Processor Unit — Southbridge SPI Protocol v1.1

**Document:** SPU Southbridge Serial Protocol
**Version:** 1.1 (2026-06-28)
**Hardware:** Tang Primer 25K (GW5A-25A FPGA, `spu_spi_slave.v`)
**Master:** RP2350 Microcontroller (SPI0 @ 2 MHz, Mode 0)
**Status:** RTL testbench PASS; Tang 25K/RP2350 `0xAC` status read verified

---

## Overview

The **Southbridge** is the compute engine side of the RP2350↔FPGA bridge. It implements a **SPI slave** that answers queries from the RP2350 master, streaming manifold state, telemetry, and accepting instruction/configuration writes.

### Key Characteristics
- **Synchronous:** All edges are sampled on the rising edge of the system clock (50 MHz)
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

The telemetry path is also proven on the full SPU-13 southbridge image. On
2026-06-29 NZT, `build_25k_spu13_southbridge.sh` completed synthesis,
place-and-route, and packaging for `build/tang_primer_25k_spu13_southbridge.fs`.
The routed design passes the 12 MHz constraint (`clk_core` 72.28 MHz max,
`clk_50m` 125.16 MHz max). After SRAM load, RP2350 diagnostics report
`status raw=13 A5 00 00`; `cfgtele` reports `magic=SPUC` with count 0 before
hydration; `sdhydrate` loads 16 records with 0 skipped; and final `cfgtele`
reports count 16, last record `sel=0 material=1 addr=2
data=0x0000000000010000`, checksum `0x3A0AB5E9`.

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

The FPGA implements a 7-state machine to handle command parsing and response delivery.

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
3         [7:1] Reserved (0)
          [0]   RPLU mode bank (0=Smooth, 1=Turbulent)
```

**Fields:**
- **Laminar Index:** Phase counter (increments at Fibonacci intervals: 8, 13, 21 cycles)
- **RPLU Ratio:** `-1`, `0`, or `+1` from RPLU comparator (sticky, auto-clears after 0xAC read)
- **FIFO Full:** Set if instruction queue is full
- **Turbulence:** Set if Davis Gate detected manifold leak (Cubic Leak)
- **Janus Point:** Set when manifold crosses dual-polarity boundary
- **Satellite Snap:** SPU-4 Sentinel lock indicator
- **RPLU Mode:** Current active RPLU bank (0 = default, 1 = alternate)

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

#### **0xB0 — Sentinel Telemetry** (64 bytes)
**Response:** SPU-4 Sentinel probe data (8 nodes × 8 bytes)

**Format:**
```
Byte Range  Content
──────────  ─────────────────────────────────────────
0–7         Sentinel node 0 telemetry (8 bytes)
8–15        Sentinel node 1 telemetry (8 bytes)
...
56–63       Sentinel node 7 telemetry (8 bytes)
```

- **Node 0 (bits 511:448)** = bytes 0–7
- **Node 1 (bits 447:384)** = bytes 8–15
- Each node carries satellite SNR, phase, status flags

---

### Write Commands (0xB1, 0xA5)

#### **0xB1 — Instruction Write** (Recv: 64 bits)
**Role:** Stream a single 64-bit SPU instruction/chord

**Sequence:**
1. RP2350 sends: `0xB1` (8 bits)
2. FPGA latches command
3. RP2350 sends: 64-bit instruction (MSB first)
4. FPGA asserts `inst_valid` for one cycle, loads `inst_word`
5. Instruction fed into sequencer for execution

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

#### **0xA5 — RPLU Config Write** (Recv: 128 bits)
**Role:** Program RPLU runtime configuration table

**Sequence:**
1. RP2350 sends: `0xA5` (8 bits)
2. FPGA switches to S_RECV_HDR
3. RP2350 sends: 64-bit HEADER
4. FPGA switches to S_RECV_DATA
5. RP2350 sends: 64-bit DATA
6. FPGA decodes HEADER, asserts `rplu_cfg_wr_en` (1 cycle)

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
63:0   Configuration data (F_{p^4} coefficients, routing table, etc.)
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

## Protocol Timing

### Slave Sampling & Drive Times

| Phase | Timing |
|:---:|:---|
| **Command** | 8 × SCK cycles |
| **Response load** | 1 × system clock (50 MHz) |
| **MISO setup** | < 50 ns (combinational) |
| **MISO hold** | 0 ns (already stable) |
| **Max freq** | ~5 MHz conservative (2 MHz recommended) |

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
- FPGA state machine remains in active state (S_CMD, S_RESP, S_RECV_*)
- **No timeout mechanism** (would require additional logic)
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

**Test Status:** PASS (spu_spi_slave_tb.v)

### Hardware Validation (Tang Primer 25K)
When southbridge bitstream is tested with RP2350:
1. Build and SRAM-load the Tang 25K southbridge bitstream.
2. Flash `rp2350_spu_diag.uf2` built for the selected SPI pin profile.
3. Test `0xAC` status and `0xA0` manifold reads before enabling writes.
4. Test `0xB1` instruction writes, then `0xA5` RPLU config writes.
5. Prove SD separately with `spu_sd_test.uf2`; only then use SD-backed
   hydration commands from the RP2350 diagnostic console.

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
