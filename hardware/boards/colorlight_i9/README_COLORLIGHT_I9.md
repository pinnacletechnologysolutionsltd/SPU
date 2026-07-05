
# Historical Note

This file contains early Colorlight i9 planning assumptions. For current
measured status, use `docs/COLORLIGHT_I9_SETUP_SUMMARY.md`,
`docs/colorlight_i9_feasibility.md`, and
`docs/COLORLIGHT_I9_PINOUT_VERIFIED.md`. The current RPLU2 probe uses a 25 MHz
clock on `clk_25m`, `nextpnr-ecp5 --45k`, and routes with 72/72 DSPs used.

# Colorlight i9 Evaluation Board — SPU-13 Minimal Spin

## Overview

The **Colorlight i9** is a high-performance FPGA evaluation module featuring the **LFE5U-44F** (44K LUTs) in a cost-effective SODIMM form factor. This board hosts the SPU-13 minimal evaluation spin:

- **SPU-13 Cortex** — 13-axis manifold processor core
- **RPLU 2.0** — Rational Padé approximant engine over A₃₁ (Mersenne M31 arithmetic)
- **SOM/BMU pipeline** — Kohonen self-organizing map with winner-take-all classifier
- **Laminar boot controller** — 50 MHz → 12 MHz internal, zero-drift sequencing

**Not included (deferred for custom board):**
- Lucas Phinary MAC (specialist hardware, ~200 LUTs; useful for quantum control)
- SU(3) extensions (full 3×3 unitary matrices; not critical for evaluation)
- PIO parallel bus (Colorlight i9 SODIMM has limited breakout; SPI preferred)

---

## Board Specifications

| Aspect | Value |
|--------|-------|
| **FPGA** | LFE5U-44F (44K LUTs, 44 BRAM, 44K distributed RAM, 132 DSP48A1) |
| **Package** | caBGA-381 (17×17 mm, 0.8 mm pitch) |
| **Interface** | DDR2 SODIMM (200-pin edge connector) |
| **Clock** | 50 MHz crystal (LVCMOS33, external buffer) |
| **I/O Banks** | Bank 6, 7 (3.3V LVCMOS33, all signals) |
| **Power** | VCC (1.1V core), VCCAUX (2.5V), VCCIO (3.3V) — managed on-module |
| **Bitstream Storage** | On-board W25Q128 SPI flash |
| **Breakout** | Standard SODIMM connectors, GPIO headers for PMOD modules |

---

## Key Signals (SODIMM Pin Mapping)

All pins use **3.3V LVCMOS33** signaling (single-ended).

| Signal | SODIMM Pin | LFE5U-45 BGA | Type | Purpose |
|--------|------------|--------------|------|---------|
| `sys_clk` | 11 | A4 (PL11A) | Input | 50 MHz system clock |
| `rst_n` | 25 | B2 (PL23C) | Input (pull-up) | Active-low reset |
| `led[0]` | 27 | A2 (PL23A) | Output | LED 0 (active low) |
| `led[1]` | 29 | B1 (PL23B) | Output | LED 1 (active low) |
| `led[2]` | 31 | C2 (PL23D) | Output | LED 2 (active low) |
| `uart_tx` | 33 | D1 (PL26B) | Output | UART @ 115.2 kbaud |
| `spi_cs_n` | 35 | E2 (PL32D) | Input | SPI Chip Select (optional) |
| `spi_clk` | 37 | F2 (PL32C) | Input | SPI Clock (optional) |
| `spi_mosi` | 39 | E3 (PL20B) | Input | SPI Master-Out (optional) |
| `spi_miso` | 41 | F4 (PL20A) | Output | SPI Master-In (optional) |

**Notes:**
- **`sys_clk`** — Must use differential pair PL11A/PL11B for optimal jitter (<5 ps). Constraint file specifies PULL_MODE=NONE (external crystal buffer).
- **`rst_n`** — Active-low with internal pull-up on Colorlight i9 module. Asserted at power-up, cleared by external button or RP2350 control.
- **LEDs** — Active-low; pull to GND to illuminate. Typical values 2.2 kΩ series resistors on breakout board.
- **`uart_tx`** — Serial protocol @ 115.2 kbaud. Connect to RP2350 or USB-to-serial adapter. No external pull-up needed (open-drain output from ECP5).
- **SPI (optional)** — If using on-board flash alone, these pins can be tied to low or left floating. If connecting to RP2350 southbridge, route as standard SPI slave: CS#, SCK, MOSI (input), MISO (output).

---

## Build Instructions

### Prerequisites

Install the OSS CAD Suite (Yosys, nextpnr, Trellis):

```bash
# On Ubuntu/Debian:
sudo apt-get install fpga-toolchain
# or build from source:
#   https://github.com/YosysHQ/oss-cad-suite-build

# Verify installation:
yosys --version
nextpnr-ecp5 --help
ecppack --help
```

### Synthesis

```bash
cd /path/to/SPU
bash hardware/boards/colorlight_i9/build_colorlight_i9_minimal.sh synth
```

**Expected output:**
```
>>> Yosys Synthesis <<<
read_verilog: loaded 8 modules from curated source list
synth_ecp5: inferring BRAM, inferring DSP...
✓ Synthesis complete: build/spu_colorlight_i9_top.json
```

**Synthesis statistics (typical):**
- **Cells:** ~6,500–7,000 (SPU-13 ALU, RPLU SOM, Padé engine)
- **Area:** 14.8% of 44K LUTs (~6,500 LUTs / 44,416 available)
- **DSP usage:** ~30/132 (Padé multiply, SOM quadrance)

### Place & Route

```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_minimal.sh pnr
```

**Expected output:**
```
>>> Nextpnr Place-and-Route <<<
nextpnr-ecp5 --44k --freq 50 ...
WARN: Not all placements are legal.
(Nextpnr iterates; typically converges within 60–120 seconds)
✓ Place-and-route complete
```

**P&R Metrics:**
- **Timing met?** Yes (50 MHz → 12 MHz internal, ±margin)
- **Placement:** ~14.8% utilized (no congestion expected)
- **Routing:** Standard; no crossing bottlenecks

### Full Build

```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_minimal.sh all
```

**Outputs:**
- `build/spu_colorlight_i9_top.json` — Yosys synthesis output
- `build/spu_colorlight_i9_top_out.config` — nextpnr place-and-route textcfg
- `build/spu_colorlight_i9_top.bit` — Final bitstream (ready for flashing)

---

## Flashing to Colorlight i9

### Option A: Via openFPGALoader (Recommended)

```bash
# Requires JTAG header or FT2232H adapter connected to JTAG pins (TCK, TDI, TDO, TMS)
openFPGALoader -b colorlight_i9 build/spu_colorlight_i9_top.bit

# Bitstream loads into SRAM; reloads on power-up from on-board flash if pre-programmed
```

### Option B: Direct SPI Flash Programming

```bash
# Using RP2040 USB-to-SPI programmer (see hardware/rp2040_tooling/)
tools/rp2040_flash_pmod.py --port /dev/ttyACM0 id
# Should report: JEDEC: EF4018 (W25Q128JV)

tools/rp2040_flash_pmod.py --port /dev/ttyACM0 write build/spu_colorlight_i9_top.bit --offset 0x0
# Bitstream now persists; loads automatically on power-up
```

### Option C: Via Colorlight i9 Bootloader

Some Colorlight i9 boards include a USB bootloader. Consult the Colorlight documentation or community resources (wuxx/Colorlight-FPGA-Projects).

---

## Smoke Tests

### Test 1: LEDs + Boot Strobe

After flashing, verify LEDs toggle at predictable intervals:

```bash
# Expected: LEDs blink in sequence ~1 Hz (Fibonacci-timed Piranha Pulse)
# If LEDs do not respond, check:
#   1. Power supply (1.1V core, 3.3V I/O)
#   2. FPGA configuration (bitstream loaded?)
#   3. Pin connections (SODIMM connectors seated fully)
#   4. Reset timing (rst_n held low for ≥1 ms at power-up)
```

### Test 2: UART Telemetry

Connect UART TX pin to USB-to-serial adapter (e.g., FT232R, 115.2k baud):

```bash
# Expected output (per second):
# H: FFFE 0001  <- hex coordinate projection
# Q: 00010001   <- QR (Q rational surd unit) register readback
# T: boot_tick  <- Fibonacci interval counter
# ...

# If no output:
#   1. Check UART level-shifter (3.3V → RS232 if needed)
#   2. Verify `uart_tx` connected to pin 33 (SODIMM)
#   3. Check baud rate (115.2 kbaud, 8 bits, no parity)
```

### Test 3: SPU-13 Instruction Execution

Via SPI protocol (optional; requires RP2350 southbridge or similar):

```bash
# Send CMD 0xB1 (instruction write) with QLDI opcode (0x0C)
# Expected: QR register updates; UART reports new value
```

See `hardware/boards/colorlight_i9/SMOKE_TESTS.md` for full testbench suite.

---

## Timing & Resource Budgets

### Clock Domains

| Domain | Frequency | Source | Used By |
|--------|-----------|--------|---------|
| `sys_clk` | 50 MHz | External crystal | PLL, sequencer |
| `clk_12mhz` | 12 MHz | PLL ÷ 4 | SPU-13 core, ALU |
| `clk_6mhz` | 6 MHz | Fibonacci divider (8-cycle interval) | Instruction dispatch (8, 13, 21) |

### Critical Paths

| Path | Slack | Period | Notes |
|------|-------|--------|-------|
| SPU-13 ALU combinational | +150 ps | 83 ns (12 MHz) | TDM multiplier, rotor core |
| Padé engine (A₃₁ inverter) | +80 ps | 83 ns | 3-cycle pipelined |
| SOM quadrance pipeline | +120 ps | 83 ns | 3-stage parallel array |

**All paths meet timing.** Estimated margin: +80–150 ps. No timing violations expected.

### Resource Summary (LFE5U-44F)

| Resource | Used | Available | % |
|----------|------|-----------|-----|
| **LUTs** | 6,500 | 44,416 | 14.6% |
| **BRAM (18 kb)** | 4 | 44 | 9.1% |
| **DSP48A1** | 30 | 132 | 22.7% |
| **Distributed RAM** | 2 kB | 44 kB | 4.5% |

**Headroom:** 37.9K LUTs, 40 BRAM, 102 DSP available for future features (e.g., Lucas MAC, extended SOM, second core).

---

## Constraint File

Location: `hardware/boards/colorlight_i9/colorlight_i9.lpf`

The `.lpf` file (Lattice Preference File) maps HDL port names to FPGA pins. It specifies:
- Pin locations (LOC)
- I/O types (LVCMOS33)
- Pull modes (UP for reset, NONE for clock)
- Differential pair associations (clock)

**To update pinout:**
1. Obtain the actual Colorlight i9 schematic or pinout diagram.
2. Cross-reference with `FPGA-SC-02034-3-0-ECP5U-45-Pinout.csv` (master ECP5U-45 datasheet).
3. Edit `colorlight_i9.lpf` with correct SODIMM-to-BGA mappings.
4. Rerun P&R: `bash build_colorlight_i9_minimal.sh pnr`.

---

## Transition to Custom LFE5U-45F Board

When moving to a production custom PCB with a bare LFE5U-45F chip:

1. **Switch package:** Colorlight i9 uses caBGA-381; your custom board may choose caBGA-381, caBGA-256, or caBGA-554.
2. **Regenerate constraints:** Download the Lattice pinout CSV for your package, create a new `.lpf` file.
3. **Update build script:** Change device string and package in `build_*.sh`.
4. **Add power delivery:** Ensure robust VCC (1.1V), VCCAUX (2.5V), VCCIO (3.3V) rails with low-impedance planes.
5. **Route JTAG:** Break out TCK, TDI, TDO, TMS + GND + VCCIO for programming.
6. **Flash storage:** Include SPI flash (W25Q series) for bitstream persistence.

See `docs/colorlight_i9_feasibility.md` for detailed migration path.

---

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Synthesis fails with "duplicate module" | glob-based RTL discovery pulling both .v and .vh stubs | Use curated source list (build script already does this) |
| P&R hangs or fails with "cannot place" | Timing constraint too tight or routing congestion | Reduce frequency (--freq 40 instead of 50), allow more iterations |
| LEDs don't blink | FPGA not configured, or reset stuck low | Check power supply, assert rst_n briefly |
| No UART output | UART TX pin not connected, or baud mismatch | Verify pin 33 connection; check serial terminal (115.2k baud) |
| Bitstream flashing fails | JTAG connection bad, or adapter not recognized | Test with `openFPGALoader --list-boards`; ensure USB driver installed |

---

## References

- **Colorlight i9 Documentation:** https://github.com/wuxx/Colorlight-FPGA-Projects (community reverse-engineered schematics, constraint files)
- **LFE5U-45 Datasheet:** `FPGA_DS_02012_2_4_ECP5_ECP5G_Family_Data_Sheet-1022822.pdf`
- **ECP5U-45 Pinout CSV:** `FPGA-SC-02034-3-0-ECP5U-45-Pinout.csv`
- **ECP5 Hardware Checklist:** `FPGA-TN-02038-2-0-ECP5-and-ECP5-5G-Hardware-Checklist.pdf`
- **SPU-13 Architecture:** `docs/SPU-13-ARCHITECTURE.md` (coming soon)
- **Feasibility Study:** `docs/colorlight_i9_feasibility.md`

---

## Next Steps

1. **Verify pinout:** Obtain Colorlight i9 schematic; cross-check against `.lpf` file.
2. **Run smoke tests:** Flash bitstream; verify LEDs, UART, SPI (optional).
3. **Phase 1 integration:** Implement southbridge SPI protocol handler (4.5 h effort).
4. **Custom board design:** Use Colorlight i9 as reference; design bare LFE5U-45F carrier PCB.

---

**Status:** Historical planning note. Use the docs listed at the top for
current measured status.
