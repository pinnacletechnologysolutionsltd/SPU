# SPU-13 Cluster Architecture & Workflow (Tang Primer 25K)

## Current System Architecture
- **Compute Engine:** GW5A-25A FPGA (Tang Primer 25K) running Dual SPU-13 + 8× SPU-4 satellites.
- **I/O Host:** RP2350 microcontroller (USB-A port) handling USB stack/peripherals (Keyboards, Mice, Sensors), bridged to FPGA via `uart_tx` (C3).
- **Bridge/Console:** BL616 MCU (USB-C port) providing JTAG programming and verified serial UART telemetry at 115,200 baud on Pin B11.
- **Clocking:** Raw 50 MHz crystal (PLLA bypassed in open-source synthesis flow).
- **Storage:** Tang_sdram_xsds v1.3 dual-chip SDRAM module (2x W9825G6KH-6, 64 MB total); SD card (optional) for asset streaming via `spu_sd_inhaler`.
- **Status:** **Core Math Verified.** SPU-13 ISA (ROTC, QSUB, DELTA) is bit-exact. ROTC TDM core testbench passes all 5 cases. Boot telemetry is active. Rational robotics and SOM/BMU oracles are software-verified with C++ parity. RPLU v2 Thimble-Padé pipeline with A₃₁ arithmetic testbench-verified (17 new tests).

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

## RPLU v2 — Thimble-Padé Pipeline (June 2026)

The RPLU has been redesigned from Morse-potential lookup tables to a full A₃₁ rational arithmetic pipeline over the Mersenne prime M31 (p = 2^31 − 1).

### Arithmetic Foundation
- **Base field:** A₃₁ over M31 with basis [1, √3, √5, √15].
- **Multiplier:** 2-stage pipelined, 16 parallel 32×32 products, fast Mersenne reduction via 72-bit chunk split + conditional subtract. (`spu13_m31_multiplier.v`)
- **Scalar inverter:** Binary Extended Euclidean Algorithm over M31 — zero divisions, shifts + subtracts + conditional P-add. ~180 LUTs. (`spu13_m31_inverter.v`)
- **A₃₁ inverter (Conjugate Reduction Tower):** Nested quadratic collapse — Z·Z_conj → F_{p^2}(√3) → scalar norm N → Fermat N^(p-2) → reconstruct. ~76-cycle deterministic latency. Zero-norm detection asserts FLAGS.V. (`spu13_fp4_inverter.v`)

### RPLU Pipeline (4 stages)
| Stage | Module | Function |
|:---|:---|:---|
| Φ₁ | `spu_som_bmu.v` | Kohonen SOM → saddle point BMU |
| Φ₂ | `spu13_btu_core_top.v` | BTU spatial→A₃₁ transmutation (4-lane BRAM) |
| Φ₃ | `rplu_thimble_pade.v` | [4/4] Padé rational approximant via Horner + A₃₁ inverter |
| Φ₄ | output latch | Final thimble contribution |

### SOM Layer
- **Node:** Parallel 3-stage quadrance pipeline (subtract → square → accumulate). 36-bit widened training multiply. (`spu_som_node.v`)
- **Array:** 7-node parallel instantiation with combinational winner-take-all tree. BMU + second-best + confidence gap in fixed latency. (`spu_som_node_array.v`)

### Resource Estimate (vs. old RPLU)
| Resource | Old (Morse) | New (A₃₁) | Delta |
|:---|:---|:---|:---|
| LUTs | ~1,100 | ~3,300 | +3× |
| BRAMs | 6–8 | 8 | ~same |
| DSPs | 4 | 16 | +4× |
| Functional coverage | Morse approx only | Full SOM + BTU + Padé + field arithmetic | |

The 3× LUT / 4× DSP increase replaces 4 separate subsystems with one unified exact-rational pipeline.

## Upcoming Development Goals
1. **Synthesis target:** Tang 25K place-and-route for A₃₁ pipeline (+2,200 LUTs over baseline).
2. **PHSLK opcode integration:** PHSLK core (`spu13_phslk_core.v`) uses jet MAC + shared M31 multiplier for 3-lane coherence check (~12 cycles). PHSLK testbench PASS (spu13_phslk_core_tb). Full-stack PHSLK verified in `spu_full_stack_tb`.
3. **SOM opcode integration:** Wire `spu_som_node_array` behind SOM (0x2A) and SOM_TRAIN (0x2B) opcodes.
4. **Peripheral Bridge:** Integrate RP2350 firmware for USB-A Host functionality.
5. **I2S Audio:** Move I2S output from RTL-complete to silicon testing.
