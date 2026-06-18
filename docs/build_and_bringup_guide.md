# SPU-13 Build & Bring-Up Guide

Date: 2026-06-18.  Covers all four active board targets and the unified build flow.

## 1. Toolchain Setup

### 1.1 OSS CAD Suite (Gowin, ECP5, iCE40)
Install the pre-built suite from https://github.com/YosysHQ/oss-cad-suite-build.
On Arch, extract to `/opt/oss-cad-suite/` and add to PATH:
```bash
export PATH="/opt/oss-cad-suite/bin:$PATH"
```

Provides: `yosys`, `nextpnr-ecp5`, `nextpnr-ice40`, `nextpnr-himbaechel` (Gowin),
`gowin_pack`, `ecppack`, `icepack`, `verilator`, `iverilog`.

### 1.2 Artix-7 Open-Source Toolchain (Manual Build)
Requires `boost`, `boost-libs`, `eigen`, `cmake`, `gcc`.

```bash
# Dependencies
sudo pacman -S boost boost-libs eigen cmake

# Clone and build nextpnr-xilinx
git clone https://github.com/openXC7/nextpnr-xilinx.git
cd nextpnr-xilinx
mkdir build && cd build
cmake -DARCH=xilinx -DCMAKE_CXX_FLAGS="-I/usr/include/eigen3" ..
make -j$(nproc)
sudo make install  # or set CMAKE_INSTALL_PREFIX

# Clone and build Project X-Ray
git clone https://github.com/f4pga/prjxray.git
cd prjxray && mkdir build && cd build && cmake .. && make

# Generate chip database for xc7a100t
cd nextpnr-xilinx
XRAY_DIR=/path/to/prjxray PRJXRAY_DB_DIR=/path/to/prjxray-db \
  python3 xilinx/python/bbaexport.py --device xc7a100tcsg324-1 --bba xilinx/xc7a100t.bba
bbasm --l xilinx/xc7a100t.bba xilinx/xc7a100t.bin
# Result: ~152 MB xc7a100t.bin chip database
```

**Artix-7 pipeline:**
```
yosys synth_xilinx → JSON → nextpnr-xilinx --chipdb xc7a100t.bin → routed JSON → xc7frames2bit → .bit
```

### 1.3 RP2040/RP2350 Toolchain
```bash
git clone https://github.com/raspberrypi/pico-sdk.git ~/.pico/pico-sdk
```
Arch: `sudo pacman -S arm-none-eabi-gcc arm-none-eabi-newlib cmake`

## 2. Board Targets

| Board | Chip | LUTs | DSP | Build Command | Status |
|---|---|---|---|---|---|
| Tang Primer 25K | GW5A-25K | 23K | 56 | `bash build_25k_spu13_math_probe.sh` | Bitstream ready ✅ |
| ECP5 25F (Colorlight) | LFE5U-25F | 24K | 56 | `yosys hardware/boards/ecp5_25f/synth_ecp5_math.ys` | Synthesized ✅ |
| QMTech A7-100T Wukong | XC7A100T | 101K | 240 | `yosys hardware/boards/artix7/synth_a7_math.ys` | Synthesized ✅ |
| iCESugar Pro | iCE40UP5K | 5K | 0 | TBD (sensor spin) | Target defined |

### 2.1 Spins (Artix-7 family)

| Spin | Modules | Min Board | Command |
|---|---|---|---|
| `FULL` | MATH + SOM + GPU + RPLU + I2S + Gatekeeper | 100T | `bash hardware/boards/artix7/build_a7.sh 100t full` |
| `MULTIMEDIA` | MATH + GPU + RPLU + I2S + Gatekeeper | 100T | `bash hardware/boards/artix7/build_a7.sh 100t multimedia` |
| `INTELLIGENCE` | SOM + RPLU + Gatekeeper | 35T | `bash hardware/boards/artix7/build_a7.sh 35t intelligence` |
| `ROBOTICS` | MATH + Gatekeeper | 35T | `bash hardware/boards/artix7/build_a7.sh 35t robotics` |
| `SENSOR` | MATH only | 35T / iCE40 | Minimum viable build |
| `CUSTOM` | Manual ENABLE_* | Any | Override any flag |

### 2.2 Prim Layer
One RTL, three hardware backends.  Swapped at synthesis time:

| File | Target | Multiplier | BRAM |
|---|---|---|---|
| `spu_gowin_prim.v` | Gowin GW5A/GW2A | MULT27X36 / MULT18X18 | SDPB |
| `spu_ecp5_prim.v` | Lattice ECP5 | Behavioral → MULT18X18D | Behavioral → DP16KD |
| `spu_xilinx_prim.v` | Xilinx Artix-7 | Behavioral → DSP48E1 | Behavioral → RAMB18E1 |

The prim files define the same three modules: `spu_gowin_mult32`, `spu_gowin_multiplier`, `spu_gowin_bram`.
The synthesis script reads the appropriate prim file for the target device.

## 3. Synthesis Commands (Quick Reference)

### 3.1 Gowin 25K — Math Probe
```bash
bash build_25k_spu13_math_probe.sh
# Output: build/tang_primer_25k_spu13_math_probe.fs (~5.7 MB)
```

### 3.2 ECP5 25F — Math Probe
```bash
yosys hardware/boards/ecp5_25f/synth_ecp5_math.ys
# JSON: build/ecp5_math.json
# P&R: nextpnr-ecp5 --25k --json build/ecp5_math.json ...
# Pack: ecppack ...
```

### 3.3 Artix-7 100T — Math Probe
```bash
yosys hardware/boards/artix7/synth_a7_math.ys
# JSON: build/a7_math.json
# P&R: nextpnr-xilinx --chipdb xc7a100t.bin --xdc board.xdc --json build/a7_math.json ...
# Bitstream: xc7frames2bit ...
```

### 3.4 Artix-7 — Full Spin
```bash
bash hardware/boards/artix7/build_a7.sh 100t full
```

## 4. RP2040 Southbridge

### 4.1 Build Firmware
```bash
cd hardware/rp2350
mkdir -p build && cd build
cmake -DPICO_SDK_PATH=$HOME/.pico/pico-sdk -DPICO_BOARD=pico ..
make
# Output: rp2350_spu_interface.uf2 (~40 KB), rp2350_uart_injector.uf2 (~61 KB)
```

### 4.2 Wiring (6 dupont wires)
```
QMTech 100T PMOD          RP2040 Pico
─────────────────         ────────────
SPI CS           ───────  GP17 (SPI0 CS)
SPI SCK          ───────  GP18 (SPI0 SCK)
SPI MOSI         ───────  GP19 (SPI0 TX)
SPI MISO         ───────  GP16 (SPI0 RX)
FPGA UART TX     ───────  GP5  (UART1 RX)  [optional]
GND              ───────  GND
```

### 4.3 SPI Protocol (Mode 0, 2 MHz)
| CMD | Direction | Function |
|---|---|---|
| 0xA0 | Read | 32-byte manifold snapshot |
| 0xAC | Read | Status: label, ambiguous, fault_type, fault_count |
| 0xB0 | Write | 8-byte instruction word (inst_valid pulsed) |
| 0xC0 | Write | Save manifold to SDRAM |
| 0xC1 | Write | Load manifold from SDRAM |

## 5. FPGA Bring-Up Sequence

### 5.1 Tang Primer 25K (Math Probe)
1. Flash bitstream: `openFPGALoader -b tangprimer25k -f build/tang_primer_25k_spu13_math_probe.fs`
2. Connect UART at 115200 baud
3. Reset board → robotics FK closure program runs
4. Verify 5 closure proofs on UART output:
   ```
   H: FFFE 0002  → cross check
   H: 0001 0003  → self-inverse
   ...
   ```

### 5.2 Tang Primer 25K (RP2040 Southbridge)
1. Flash `rp2350_uart_injector.uf2` to RP2040
2. Wire RP2040 UART → FPGA UART RX (Pin B3)
3. Insert SD card with `.sas` programs
4. RP2040 streams instructions to FPGA
5. FPGA UART TX → RP2040 UART RX → host terminal

### 5.3 QMTech XC7A100T Wukong (Full Stack)
1. Build bitstream: `bash hardware/boards/artix7/build_a7.sh 100t full`
2. Flash via JTAG: `openFPGALoader -b arty_a7 build/spu_a7_100t_FULL.bit`
3. Flash `rp2350_spu_interface.uf2` to RP2040 Pico
4. Wire RP2040 → FPGA SPI pins (see §4.2)
5. Insert SD card with `.sas` programs and CSV tables
6. Power on — FPGA auto-configures from SPI flash
7. RP2040 boots, mounts SD, loads RPLU tables, hydrates manifold
8. Send `QLDI QR0, 0x0201, 0x0000` over SPI
9. Watch UART: `H: 0001 0000` → Davis Gate confirms laminar

## 6. Verification Matrix

| Test | VM | RTL (iverilog) | RTL (Verilator) | Silicon |
|---|---|---|---|---|
| QLDI (quadray load) | ✅ | ✅ | ✅ | ✅ 25K |
| ROTC (all 6 angles) | ✅ | ✅ | ✅ | ⬜ |
| HEX (coordinate output) | ✅ | ✅ | ✅ | ✅ 25K |
| SOM_CLASSIFY (BMU) | ✅ | ✅ | ✅ | ⬜ |
| SOM_TRAIN (weight update) | ✅ | ✅ RTL ready | ⬜ | ⬜ |
| Gatekeeper (RCA₀/WKL₀) | ✅ | ✅ | ✅ | ⬜ |
| Robotics FK closure | ✅ | ✅ | ✅ in ROM | ⬜ |
| Neighborhood training | ✅ | ⬜ | ⬜ | ⬜ |
| RPLU correction | ✅ | ✅ RTL ready | ⬜ | ⬜ |
| GPU rasterization | ✅ | ✅ | ✅ | ⬜ |
| SDRAM persist | ✅ | ✅ RTL ready | ⬜ | ⬜ |

Legend: ✅ verified | ⬜ pending hardware or toolchain

## 7. File Inventory (2026-06-18)

| Area | Files | Lines | Notes |
|---|---|---|---|
| RTL (Verilog) | 225 | 24,002 | `hardware/rtl/` |
| Testbenches | 103 | 11,698 | `hardware/tests/` |
| Software (Python/C++) | 90 | 19,657 | VM, oracles, proofs |
| .sas programs | 27 | — | Mathematics, robotics, SOM |
| RP2040 firmware | 5 | 3,477 | Southbridge + tools |
| Knowledge specs | 15 | — | ISA, math, RPLU, SOM |
| Docs | 12 + this | — | Bring-up plans, strategy |

Active boards: 4 (`artix7/`, `ecp5_25f/`, `tang_primer_25k/`, `icesugar/`).
Archived boards: 7 (+23 build scripts) in `hardware/boards/archive/`.

## 8. Key Paths

```
Synthesis YS files:
  hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_math_probe.ys
  hardware/boards/ecp5_25f/synth_ecp5_math.ys
  hardware/boards/artix7/synth_a7_math.ys   (math probe)
  hardware/boards/artix7/synth_a7.ys         (spin-based main build)
  hardware/boards/artix7/build_a7.sh         (unified build script)

Primitives:
  hardware/rtl/common/prim/spu_gowin_prim.v
  hardware/rtl/common/prim/spu_ecp5_prim.v
  hardware/rtl/common/prim/spu_xilinx_prim.v

Programs:
  software/programs/robotics_fk_closure.sas   — 27-word FK proof
  software/programs/som_classify_demo.sas     — 6 test vectors
  software/programs/som_train_demo.sas        — 4-epoch training loop

Proofs (software/tests/):
  test_rational_robotics.py     — 104 checks (FK, inverse, Pell)
  test_rational_som.py          — 24 checks (BMU, tie-breaking)
  test_som_training.py          — VM↔Oracle equivalence
  som_train_demo.py             — 3×3 hex map training
  som_neighborhood_demo.py      — Ring-1 updates
  gpu_quadray_demo.py           — Quadray rasterization
  rplu_trajectory_demo.py       — RPLU correction loop
```
