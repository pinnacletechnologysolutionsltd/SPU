# Colorlight i9 Evaluation Board — Setup Summary

**Date:** 2026-07-06
**Status:** Board target created; pinout documented; RPLU2 synthesis, P&R, and
bitstream packaging pass. Physical hardware smoke is still pending.

## Active Files

```text
hardware/boards/colorlight_i9/
├── build_colorlight_i9_rplu2.sh        # Current RPLU2 synthesis/P&R/bitstream target
├── build_colorlight_i9_minimal.sh      # Older minimal smoke wrapper
├── colorlight_i9.lpf                   # Current LPF constraints
├── spu_colorlight_i9_rplu2_top.v       # Current RPLU2 resource/timing probe
├── spu_colorlight_i9_top.v             # Older board top wrapper
├── README_COLORLIGHT_I9.md
├── COLORLIGHT_I9_PINOUT.md
└── INDEX.md
```

## Build Commands

```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh synth
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh pnr
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh bitstream
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh all
```

The script uses `nextpnr-ecp5 --45k --package CABGA381`, constrains the 25 MHz
clock on `clk_25m`, and sets `HOME=build/yosyshq_home` so the OSS CAD Suite
wrapper does not try to write under a read-only user config directory.

`ecppack` on this OSS CAD Suite version uses `--bit`, not `--output`; the build
script has been corrected for that.

## Measured RPLU2 Probe Result

Measured on 2026-07-06:

| Metric | Result |
|---|---:|
| Logic LUT4 | 3,477 |
| Carry LUT4 | 3,404 |
| Total LUT4 before packing | 6,881 / 43,848 (15%) |
| TRELLIS_COMB after packing | 7,271 / 43,848 (16%) |
| TRELLIS_FF | 1,967 / 43,848 (4%) |
| DP16KD BRAM | 0 / 108 |
| MULT18X18D DSP | 72 / 72 (100%) |
| Core clock timing | 44.05 MHz max, PASS at 25 MHz |
| Packaged bitstream | `build/spu_colorlight_i9_rplu2_top.bit` (297 KiB) |

The build fits and routes. DSP saturation means the i9 is suitable for a lean
RPLU2/ECP5 portability proof, not the full concurrent SPU-13 sidecar suite.

## Constraint Status

Current constrained probe signals:

| Signal | FPGA ball | Notes |
|---|---|---|
| `clk_25m` | P3 | 25 MHz oscillator |
| `led` | L2 | D2 status LED, active low |
| `spi_cs` | C18 | Available SODIMM GPIO |
| `spi_sck` | V1 | Available SODIMM GPIO |
| `spi_mosi` | K18 | Available SODIMM GPIO |
| `spi_miso` | R1 | Available SODIMM GPIO |
| `flash_cs_n` | R2 | On-board flash CS |
| `flash_mosi` | W2 | On-board flash MOSI |
| `flash_miso` | V2 | On-board flash MISO |

`flash_clk` is intentionally left unconstrained for this P&R metric because the
documented U3/CCLK-style path is not exposed as a normal user I/O in the current
open-flow probe. Add a proper ECP5 configuration-clock/USRMCLK path before
claiming on-board flash access.

## Hardware Bring-Up Order

1. Verify the physical module revision against the community i9-v7.2 pinout.
2. Confirm the programming path and JTAG or flash method.
3. Flash the packaged bitstream.
4. Check the 25 MHz clock and D2 LED behavior.
5. Only after basic smoke passes, wire SPI readback and port the Artix-style
   southbridge result path.

## Current Boundary

This is build evidence, not board evidence. The i9 target is now ready for
hardware smoke when the module is available, but no Colorlight silicon result
has been recorded yet.
