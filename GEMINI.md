# SPU-13 Cluster Architecture & Workflow (Tang Primer 25K)

## Current System Architecture
- **Compute Engine:** GW5A-25A FPGA (Tang Primer 25K) running Dual SPU-13 + 8× SPU-4 satellites.
- **I/O Host:** RP2350 microcontroller (USB-A port) handling USB stack/peripherals (Keyboards, Mice, Sensors), bridged to FPGA via `uart_tx` (C3).
- **Bridge/Console:** BL616 MCU (USB-C port) providing JTAG programming and verified serial UART telemetry at 115,200 baud on Pin B11.
- **Clocking:** Raw 50 MHz crystal (PLLA bypassed in open-source synthesis flow).
- **Storage:** Tang_sdram_xsds v1.3 dual-chip SDRAM module (2x W9825G6KH-6, 64 MB total); SD card (optional) for asset streaming via `spu_sd_inhaler`.
- **Status:** **Core Math Verified.** SPU-13 ISA (ROTC, QSUB, DELTA) is bit-exact. ROTC TDM core testbench passes all 5 cases. Boot telemetry is active. Rational robotics and SOM/BMU oracles are software-verified with C++ parity.

## Hardware/Toolchain Known Issues
- **CPU/SSPI Config Pins (GW5A-25A):** The Tang Primer 25K raw 50 MHz clock on `E2` sits on special configuration-pin territory.
  - **Constraint:** Ensure `IO_PORT "sys_clk" PULL_MODE=NONE;` is set in the `.cst` file.

## Engineering Standards (RationalSurd Math)
- **Coefficient Encoding:** Never use raw signed decimal literals (e.g., `-64'sd1`) for `RationalSurd` assignments.
- **Standard Pattern:** Always use explicit bit-packing for constants:
  - Identity: `{32'd0, 32'd1}`
  - Negative Rational: `{32'd0, 32'hFFFFFFFF}`
  - Standard Surd: `{32'd1, 32'd0}`
- **Division Scaling:** All tetrahedral rotations must use bit-exact division logic (`div3`) to maintain compatibility with the SPU VM.

## Corrected ROTC 0–5 Angle Catalog (June 2026)
| ROTC angle | Name | F | G | H | Period | Inverse | RTL path |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | identity | 1 | 0 | 0 | 1 | 0 | TDM |
| 1 | thirds period-6 | 2/3 | 2/3 | -1/3 | 6 | 4 | TDM + /3 |
| 2 | P5 forward cycle | 0 | 1 | 0 | 3 | 5 | bypass_p5 |
| 3 | thirds period-2 | -1/3 | 2/3 | 2/3 | 2 | 3 | TDM + /3 |
| 4 | thirds period-6 inv | 2/3 | -1/3 | 2/3 | 6 | 1 | TDM + /3 |
| 5 | P5 inverse cycle | 0 | 0 | 1 | 3 | 2 | bypass_p5_inv |

All determinants = 1. All entries have verified inverse closure. VM table (`spu_vm.py:1258-1265`) and
RTL (`spu13_rotor_core_tdm.v`) are aligned. Run `python3 software/tests/test_rotc_vm_rtl_trace.py`
for trace equivalence.

## Rational Robotics & SOM Oracles
- **Robotics:** `software/lib/rational_robotics.py` — Pell forward/inverse closure, F/G/H circulant
  inverse, FK chains, arc closure. 56 test checks.
- **SOM/BMU:** `software/lib/rational_som.py` — weighted quadrance BMU, surd-field square path,
  stable tie-breaking, Nguyen cluster reduction, hex neighbors. 24 test checks.
- **C++ parity:** Both oracles have C++17 headers and test files in `software/common/`.
- **Knowledge:** `knowledge/RATIONAL_CURVES_SPEC.md`, `knowledge/NGUYEN_WEIGHT_PARTITIONING.md`,
  `knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md`.

## Verified Pinout Baseline (Tang Primer 25K)
- **Clock (`sys_clk`):** Pin `E2` (Raw 50 MHz crystal). `PULL_MODE=NONE` is mandatory.
- **LEDs (`led[0:2]`):** Pins `L6`, `E8`, `D7` (Active low).
- **Telemetry UART (`uart_tx_telemetry`):** Pin `B11` (115,200 baud).
- **Host UART (`uart_tx`):** Pin `C3`.
- **SPI Flash (PMOD J4 Bottom Row):** Pins `G10` (CS), `D10` (SCK), `C10` (MOSI/D1), `B10` (MISO/DO).

## Upcoming Development Goals
1. **ROTC Trace Equivalence:** VM-vs-RTL bit-exact verification for all 6 corrected ROTC angles.
2. **SOM BMU RTL:** Implement `spu_som_bmu.v` — weighted quadrance best-matching-unit stage, then `spu_cluster_reduce.v`.
3. **Peripheral Bridge:** Integrate RP2350 firmware for USB-A Host functionality.
4. **I2S Audio:** Move I2S output from RTL-complete to silicon testing.
5. **GPU Rasterizer:** Validate fragment pipeline in silicon.
