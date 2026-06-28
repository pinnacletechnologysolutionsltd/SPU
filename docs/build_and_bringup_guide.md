# SPU-13 Build & Bring-Up Guide

Date: 2026-06-18.  Covers all four active board targets and the unified build flow.

## 1. Toolchain Setup

Detailed OS-specific setup lives in [`docs/toolchain_setup.md`](toolchain_setup.md).

### 1.1 OSS CAD Suite (Gowin, ECP5, iCE40)
Install the pre-built suite from https://github.com/YosysHQ/oss-cad-suite-build.
On Arch, extract to `/opt/oss-cad-suite/` and add to PATH:
```bash
export PATH="/opt/oss-cad-suite/bin:$PATH"
```

Provides: `yosys`, `nextpnr-ecp5`, `nextpnr-ice40`, `nextpnr-himbaechel` (Gowin),
`gowin_pack`, `ecppack`, `icepack`, `verilator`, `iverilog`.

### 1.2 Artix-7 OpenXC7 Toolchain
Canonical local install prefix:
```bash
$HOME/.local/openxc7
```

The repo expects this prefix to contain:
- `bin/nextpnr-xilinx`
- `bin/bbasm`
- `bin/xc7frames2bit`
- `lib/python/bbaexport.py`
- `share/nextpnr/prjxray-db`
- `lib/external/nextpnr-xilinx-meta`
- `lib/constids.inc`

Use the repo environment helpers instead of setting global `PYTHONPATH`:
```bash
# bash/zsh, current session only
source tools/env_openxc7.sh

# fish, current session only
source tools/env_openxc7.fish
```

For a non-default install prefix:
```bash
OPENXC7_ROOT=/opt/openxc7 source tools/env_openxc7.sh
```

Fish equivalent:
```fish
set -gx OPENXC7_ROOT /opt/openxc7
source tools/env_openxc7.fish
```

Generate the Artix-7 100T chip database once:
```bash
tools/generate_a7_chipdb.sh 100t
# Output: build/chipdb/xc7a100tfgg676.bin (~152 MB)
```

The Artix-7 build script also auto-loads `tools/env_openxc7.sh` or
`$OPENXC7_ROOT/export.sh` if the tools are not already on `PATH`.

Do not make `PYTHONPATH` universal in fish. If a permanent setup is desired,
make only `OPENXC7_ROOT` and the executable path permanent:
```fish
set -Ux OPENXC7_ROOT $HOME/.local/openxc7
fish_add_path $HOME/.local/openxc7/bin
```

**Artix-7 pipeline:**
```
yosys synth_xilinx → JSON → nextpnr-xilinx --chipdb xc7a100tfgg676.bin → FASM → fasm2frames → xc7frames2bit → .bit
```

### 1.3 RP2040/RP2350 Toolchain
```bash
git clone https://github.com/raspberrypi/pico-sdk.git ~/.pico/pico-sdk
```
Arch: `sudo pacman -S arm-none-eabi-gcc arm-none-eabi-newlib cmake`

## 2. Board Targets

Current hardware priority: the replacement Tang Primer 25K is the first
incoming FPGA board. Use `docs/tang25k_replacement_bringup_plan.md` as the
execution checklist. The Wukong Artix-7 flow is prepared, but hardware bring-up
is parked until that board arrives.

| Board | Chip | LUTs | DSP | Build Command | Status |
|---|---|---|---|---|---|
| Tang Primer 25K | GW5A-25K | 23K | 56 | `bash build_25k_spu13_math_probe.sh` | Bitstream ready ✅ |
| ECP5 25F (Colorlight) | LFE5U-25F | 24K | 56 | `yosys hardware/boards/ecp5_25f/synth_ecp5_math.ys` | Synthesized ✅ |
| QMTech A7-100T Wukong | XC7A100T FGG676 | 101K | 240 | `A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t robotics all` | Pinned P&R + bitstream ✅ at 2 MHz; 4 MHz misses timing |
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
source tools/env_openxc7.sh
tools/generate_a7_chipdb.sh 100t
bash hardware/boards/artix7/build_a7.sh 100t robotics synth

# Schematic-derived Wukong pins; board-usable bitstream.
A7_FREQ=2 \
  bash hardware/boards/artix7/build_a7.sh 100t robotics pnr
A7_FREQ=2 \
  bash hardware/boards/artix7/build_a7.sh 100t robotics pack
```

### 3.4 Artix-7 — Full Spin
```bash
bash hardware/boards/artix7/build_a7.sh 100t full
```

## 4. RP2040/RP2350 Southbridge

### 4.1 Build Firmware
```bash
cd hardware/rp2350
mkdir -p build && cd build
cmake -DPICO_SDK_PATH=$HOME/.pico/pico-sdk -DPICO_BOARD=pico ..
make
# Output: rp2350_spu_interface.uf2, rp2350_uart_injector.uf2, rp2350_spu_diag.uf2
```

### 4.2 Wiring (6 dupont wires)
```
QMTech 100T PMOD          RP2040/RP2350 Pico
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
| 0xAC | Read | 4-byte status: laminar index, flags, RPLU mode |
| 0xAD | Read | 9-byte scale table and overflow flags |
| 0xAE | Read | 34-byte last-QLDI commit: valid, lane, then A/B/C/D as four big-endian 64-bit words |
| 0xAF | Read | 5-byte sticky HEX result: valid, signed q16, signed r16; read clears valid |
| 0xB0 | Read | 64-byte sentinel telemetry burst |
| 0xA5 | Write | RPLU config record: 8-byte HEADER + 8-byte DATA |
| 0xB1 | Write | 8-byte instruction word (inst_valid pulsed) |

## 5. FPGA Bring-Up Sequence

### 5.1 Tang Primer 25K (Math Probe)
Use `docs/tang25k_replacement_bringup_plan.md` for the full replacement-board
sequence. First load SRAM only, without `-f`:

1. Build: `bash build_25k_spu13_math_probe.sh`
2. SRAM-load bitstream: `openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_math_probe.fs`
3. Connect UART at 115200 baud
4. Reset board → robotics FK closure program runs
5. Verify 5 closure proofs on UART output:
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

### 5.3 QMTech XC7A100T Wukong (Robotics First)
Prepared but parked until Wukong hardware arrives.

1. Verify JTAG chain: `openFPGALoader -c dirtyJtag --detect`
2. Build the pinned robotics bitstream: `A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t robotics all`
3. SRAM-load via DirtyJTAG: `A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t robotics flash`
4. Flash `rp2350_spu_interface.uf2` to the RP2040/RP2350 southbridge
5. Wire RP2040/RP2350 → FPGA SPI pins (see §4.2)
6. Insert SD card with `.sas` programs, manifests, configs, and table packs
7. RP2040/RP2350 boots, mounts SD, loads RPLU tables, hydrates manifold
8. Send `QLDI QR0, 0x0201, 0x0000` over SPI
9. Watch UART: `H: 0001 0000` → Davis Gate confirms laminar

Only write the Wukong configuration flash after the SRAM-loaded bitstream has
passed JTAG, reset, UART, and southbridge smoke tests.

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
