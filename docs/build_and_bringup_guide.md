# SPU-13 Build & Bring-Up Guide

Date: 2026-07-06. Covers the current board targets and the unified build flow.
For the shortest current status summary, read `docs/CURRENT_STATUS.md` first.

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

Current hardware priority: the Tang Primer 25K is active for subsystem
regression via split-build probes. The Wukong Artix-7 100T is the target for
silicon evidence, sidecar proofs, and constrained integration. Full concurrent
RPLU2 + Lucas MAC + sidecar integration is an Artix-7 200T / Kintex-class
funding target. Use the bring-up checklists in `docs/` for execution. For
semantic boundaries and claim levels, see
`docs/SPU13_IDENTITY_AND_BOUNDARIES.md`.

| Board | Chip | LUTs | DSP | Build Command | Status |
|---|---|---|---|---|---|
| Tang Primer 25K | GW5A-25K | 23K | 56 | See split-build table below | regression ladder closed ✅ |
| QMTech A7-100T Wukong | XC7A100T FGG676 | 101K | 240 | `bash hardware/boards/artix7/build_a7.sh 100t <spin> all` | JTAG/J11 verified; LUCAS, SU3, ROBOTICS, SU3SHARE, RPLU2CORE, and RPLU2PADE smoke pass ✅ |
| Colorlight i9 | LFE5U-45F class | 43.8K reported | 72 | `bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh all` | Open-flow RPLU2 synth/P&R/bitstream pass; hardware smoke pending |
| ECP5 custom evaluator | LFE5U-45F/85F class | 43.8K/83.6K reported | 72/156 | `bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh all` | 85F placeholder flow passes; EE/funding-dependent PCB not fab-ready |
| Kintex-7 K7-480T PCIe | XC7K480T | 400K+ class | 1920 | TBD | Later full-integration target |

### 2.1 ECP5 Open-Flow Builds

Colorlight i9 RPLU2 resource/timing probe:

```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh all
```

Current measured result: 6,881 / 43,848 LUT4 before packing, 1,967 FF,
72 / 72 MULT18X18D, 0 / 108 DP16KD, and 44.05 MHz max core clock while passing
the 25 MHz constraint. This is build evidence only until physical i9 smoke is
recorded.

ECP5-85F curated placeholder:

```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh all
```

Current measured result: 293 / 83,640 LUT4 before packing, 97 FF,
0 / 156 MULT18X18D, 0 / 208 DP16KD, and 273.00 MHz max generated internal
clock while passing the 50 MHz constraint. This validates the curated
source/LPF/toolchain path, not a functional RPLU2 85F image.

### 2.2 Tang 25K Split Builds

The full concurrent SPU-13 image is not the 25K strategy. Earlier full
southbridge attempts reached very high utilization and poor integration margin;
independent probes now split the architecture into testable subsystems:

| Probe | MATH | RPLU_V2 | LUTs | Build Command | Proves |
|---|---|---|---|---|---|
| `southbridge_spi_probe` | 0 | 0 | 1,861 LUT4 | `bash build_25k_southbridge_spi_probe.sh` | SPI electrical/protocol smoke without core |
| `southbridge_link` | 0 | 0 | 4,054 LUT4 | `bash build_25k_spu13_southbridge_link.sh` | SPI link validation with dormant core attached |
| `math_probe` | 1 | 0 | ~4,000 | `bash build_25k_spu13_math_probe.sh` | ROTC, Davis, rotor |
| `rplu2_arith_probe` | 0 | 1 | 9,211 LUT4 | `bash build_25k_spu13_rplu2_arith_probe.sh` | QLDI, QSUB, RPLU2 config, CRC-8 writes, ECC regfile |
| `lucas_mac_probe` | 0 | 0 | 696 LUT4 | `bash build_25k_spu13_lucas_mac_probe.sh` | PSCALE/PCHIRAL fast paths, PSCALE zero-drift |
| `rotc_probe` | 0 | 0 | 13,352 LUT4 | `bash build_25k_spu13_rotc_probe.sh` | Corrected ROTC 0-5 trace and period closure |
| `six_step_probe` | 0 | 0 | 13,576 LUT4 | `bash build_25k_spu13_six_step_probe.sh` | Period-6 six-step robotics closure and inverse recovery |
| `som_bmu_probe` | 0 | 0 | 15,325 LUT4 + 4 BSRAM | `bash build_25k_spu13_som_bmu_probe.sh` | BRAM-backed weighted SOM/BMU classification and cluster reduction |
| `som_hydrate_probe` | 0 | 0 | 583 LUT4 + 8 BSRAM | `bash build_25k_spu13_som_hydrate_probe.sh` | SOM BRAM write/readback and per-feature byte-enable hydration |
| `neuro_guard_probe` | 0 | 0 | 5,016 LUT4 | `bash build_25k_spu13_neuro_guard_probe.sh` | Fixed-epoch neuro guard, Lucas norm admission, fallback |
| `neuro_sidecar_probe` | 0 | 0 | 4,013 LUT4 | `bash build_25k_spu13_neuro_sidecar_probe.sh` | SPI-visible neuro adapter opcodes, readback, overflow fallback |

The two southbridge probes were re-routed and hardware-verified on 2026-06-30
after deadman-timer and CRC-8 write-receive hardening. Expected telemetry is
`status raw=25 A5 00 00` for the SPI-only probe, `status raw=13 A5 00 00` for
the core-attached probe, and `cfgtele count=16 checksum=0x3A0AB5E9` after
`sdhydrate` on both.

The `rplu2_arith_probe` was rebuilt and hardware-verified on 2026-06-30. It
routes at 9,211 LUT4 / 7,926 DFF and includes the ECC-wrapped quadray register
file (Hamming (72,64) SECDED), CRC-8-verified SPI writes, and a 128-cycle
deadman timer on the SPI receive state machine. It proves the corrected 149-record
consume table (`rplu2_sum=0x0AA480E7`, `rplu2_status=0xC02E0001`) plus six RP2350
arithmetic commit checks: QLDI positive, QLDI signed, QSUB positive, QSUB
negative, and QSUB self-zero.

The `lucas_mac_probe` routes at 696 LUT4 / 216 DFF / 416 ALU with no BRAM and
no DSP. It is a Tang `FAST_ONLY=1` silicon proof for PSCALE, PCHIRAL, and a
100-period PSCALE zero-drift marathon. Hardware-verified UART after SRAM load
is `LUCAS:P`; PMUL and PINV are now Wukong-J11 verified through the RP2350 SPI
sidecar.

The `rotc_probe` routes at 13,352 LUT4 / 1,036 DFF / 1,044 ALU with no BRAM
and no DSP. It self-checks the corrected ROTC catalog on the canonical VM/RTL
trace vector and repeats period-closure loops for all non-identity angles.
Hardware-verified UART after SRAM load is `ROTC:P A:5 E:00`.

The `six_step_probe` routes at 13,576 LUT4 / 1,518 DFF / 1,024 ALU with no BRAM
and no DSP. It self-checks the period-6 rational robotics harness: six forward
ROTC angle-1 phases, angle-4 inverse recovery after every phase, early-closure
rejection, and exact closure on phase 5. Hardware-verified UART after SRAM load
is `KIN:P P:5 E:00`.

The `som_bmu_probe` routes at 15,325 LUT4 / 1,009 DFF / 1,268 ALU with 4 BSRAM
and no DSP. It self-checks two weighted seven-node SOM/BMU oracle scenarios and
the cluster-reduce label/ambiguity path using the BRAM-backed node-weight store.
Hardware-verified UART after SRAM load is `SOM:P T:2 B:6 E:00`.

The `som_hydrate_probe` routes at 583 LUT4 / 165 DFF / 200 ALU with 8 BSRAM
and no DSP. It self-checks the writeable SOM node-weight store: initial node-0
readback, node-0 feature hydration, and node-6 per-feature byte-enable
preservation. Hardware-verified UART after SRAM load is `HYD:P T:3 B:6 E:00`.

The `neuro_guard_probe` routes at 5,016 LUT4 / 358 DFF with
`synth_gowin -noalu`, no BRAM, no DSP, and no ALU carry cells. It is a
standalone Tang bitstream for the fixed-epoch neuro sidecar: accept,
reject/fallback, carry-bit threshold crossing, and saturated-counter fallback.
Hardware-verified UART after SRAM load is
`N:P T:4 P:003/003 K:009 C:007/008 E:00`.

The `neuro_sidecar_probe` routes at 4,013 LUT4 / 380 DFF with no BRAM, no DSP,
and no ALU carry cells. It self-drives the SPI-visible adapter opcodes
`0xE0`/`0xE1`/`0xE2`/`0xE3` for config, start, spike injection, and QR
readback. Hardware-verified UART after SRAM load is `N:P T:3 E:00`.

Tang bring-up closeout, 2026-07-01: the Sipeed FTDI2232 bridge enumerates under
`openFPGALoader --scan-usb`, all closed-regression `.fs` images listed above are
present in `build/`, and a 40-second UART soak on `six_step_probe` stayed on
`KIN:P P:5 E:00`.

### 2.2 Spins (Artix-7 family)

| Spin | Modules | Min Board | Command |
|---|---|---|---|
| `FULL` | MATH + SOM + GPU + RPLU2 + I2S + Gatekeeper | 100T | `bash hardware/boards/artix7/build_a7.sh 100t full` |
| `MULTIMEDIA` | MATH + GPU + RPLU2 + I2S + Gatekeeper | 100T | `bash hardware/boards/artix7/build_a7.sh 100t multimedia` |
| `INTELLIGENCE` | SOM + RPLU2 + Gatekeeper | 35T | `bash hardware/boards/artix7/build_a7.sh 35t intelligence` |
| `ROBOTICS` | MATH + Gatekeeper | 35T | `bash hardware/boards/artix7/build_a7.sh 35t robotics` |
| `LUCAS` | SPI-visible Lucas MAC sidecar, no core math/RPLU2 | 35T | `bash hardware/boards/artix7/build_a7.sh 100t lucas synth` |
| `NEURO_SAFE` (planned) | Fixed-epoch neuro sidecar + Lucas norm guard | 35T after Tang probe | Tang adapter proof: `build_25k_spu13_neuro_sidecar_probe.sh` |
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

### 3.2 ECP5 Curated Minimal Flow
```bash
bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh synth
```

This is a curated-source parse/synthesis check for the custom ECP5 evaluator
placeholder. For the next practical ECP5 target, use the Colorlight i9 command
in Section 3.5.

### 3.3 Artix-7 100T — LUCAS Bring-Up Bitstream
```bash
source tools/env_openxc7.sh
tools/generate_a7_chipdb.sh 100t
bash hardware/boards/artix7/build_a7.sh 100t lucas synth

# Schematic-derived Wukong pins; board-usable bitstream.
A7_FREQ=2 \
  bash hardware/boards/artix7/build_a7.sh 100t lucas pnr

# If fasm2frames is not installed as an executable, provide Project X-Ray.
PRJXRAY_ROOT=/path/to/prjxray \
OPENXC7_PYTHON=/path/to/prjxray-venv/bin/python \
A7_FREQ=2 \
  bash hardware/boards/artix7/build_a7.sh 100t lucas pack
```

Current measured result: the Wukong V02 J11-PMOD constraints route the hardened
`LUCAS` spin at `A7_FREQ=2`; the final routed max frequency is 4.41 MHz. The
spin uses 120/240 DSP48E1 slices after enabling the MAC PINV watchdog and
PMUL/PINV norm checks. The packed image is `build/spu_a7_100t_LUCAS.bit`.
Treat it as a bench SRAM-load artifact for JTAG/reset/UART/SPI proof, not as
final timing closure.

### 3.4 Artix-7 — Full Spin
```bash
bash hardware/boards/artix7/build_a7.sh 100t full
```

### 3.5 Colorlight i9 — Next ECP5 Synthesis Target
```bash
bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh synth
```

This is the next planned ECP5 check. It should be treated as a synthesis audit
first, not a board proof. Expected follow-up order is:

1. Fix any Verilog/Yosys issues exposed by `synth`.
2. Run `pnr` with the verified 25 MHz i9 constraints.
3. Only after P&R succeeds, generate a bitstream and plan hardware flashing.
4. Add SPI/J11-style southbridge readback later; the current i9 RPLU2 top is a
   resource/timing probe, not a functional RP2350 smoke image.

## 4. RP2350 Southbridge

### 4.1 Build Firmware
```bash
cd hardware/rp2350
mkdir -p build && cd build
cmake -DPICO_SDK_PATH=$HOME/.pico/pico-sdk -DPICO_BOARD=pico ..
make
# Output: rp2350_spu_interface.uf2, rp2350_uart_injector.uf2, rp2350_spu_diag.uf2
```

### 4.2 Wukong J11 SPI Wiring
```
QMTech Wukong J11 PMOD / FPGA  RP2350-Zero/Pico SPI master
────────────────────────       ────────────────────────────
J11-1 / H4 / spi_cs_n    ────  GP1 (software CS#)
J11-2 / F4 / spi_sck     ────  GP2 (SPI0 SCK)
J11-3 / A4 / spi_mosi    ────  GP3 (SPI0 TX)
J11-4 / A5 / spi_miso    ────  GP0 (SPI0 RX)
J11-5 or J11-11 / GND    ────  GND
J11-6 or J11-12 / 3V3    ────  target reference only
E3 / uart_tx             ────  GP5 (UART1 RX) [optional]
GND                      ────  GND
```

The Wukong V02 schematic also has a separate 20x2 expansion header named J12.
The SPU Artix constraints use J11 for the RP2350 southbridge so the connection
lands on the physical PMOD-style connector.

### 4.3 Wukong J11 LUCAS Smoke Test
After loading `build/spu_a7_100t_LUCAS.bit` with DirtyJTAG:

```bash
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_LUCAS.bit
```

The expected SRAM-load footer is `isc_done 1`, `init 1`, `done 1`. With the
RP2350 `rp2350_lucas_j11_smoke` firmware on `/dev/ttyACM2`, the 2026-07-03
J11 bench proof repeatedly produced:

```text
status -> raw=00 FF 00 00
chord D0200C0500000000 -> qr lane=2  A=0x0000000800000005
chord D1C00C0500000000 -> qr lane=12 A=0x0000020400000008
chord D2300C0500807000 -> qr lane=3  A=0x0000004200000029
chord D3400C0500000000 -> qr lane=4  A=0x0000000500000201
status after each opcode -> raw=00 FF 00 00
LUCAS_J11: PASS
```

This verifies PSCALE, PCHIRAL, PMUL, and PINV over the physical Wukong J11
PMOD wiring through the external RP2350 SPI path.

For diagnostic firmware that defaults to GP16-GP19, build with
`-DSPU_RP2350_ZERO_HEADER_SPI=ON` to select the GP0-GP3 header mapping.

### 4.3a Wukong J11 RPLUCFG Transport Smoke
The `RPLUCFG` Artix spin is a coreless SPI/telemetry proof for long RPLU2
runtime config bursts. It exists to separate J11 transport from main-core timing
closure.

```bash
bash hardware/boards/artix7/build_a7.sh 100t rplucfg all
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_RPLUCFG.bit
picotool load -f build/rp2350_arithmetic/rp2350_rplu2_j11_smoke.uf2
```

Current 2026-07-04 bench result: the image routes timing-clean
(`clk_fast` max 83.17 MHz, PASS at 50 MHz), SRAM-loads with `done 1`, and the
RP2350 bit-banged GP0-GP3 smoke receives the full 149-record consume profile:

```text
bus=bitbang
after cfgtele count=149 last_sel=6 last_addr=0 last_data=0x0000000000000003
rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001
rplu2_num0=0x00000002 rplu2_delta=0x00000000
rplu2_row1=0x00000001 rplu2_kappa=0x00000003
RPLU2_J11: PASS
```

Do not use the RP2350 hardware-SPI path for long Artix RPLU2 config bursts yet.
On the same wiring it deterministically missed records (`count=52`, `61`, `71`,
or `59` depending on guards/instrumentation), while bit-banged mode repeatedly
passes. Treat bit-banged GP0-GP3 as the current known-good Wukong transport path.

### 4.3b Wukong J11 RPLU2CORE Main-Core Smoke
The `RPLU2CORE` Artix spin keeps the RPLU2 config/QR path active while leaving
the full RPLU2 pipeline disabled. Use it for the first core-enabled Wukong proof.

```bash
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t rplu2core synth
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t rplu2core pnr
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t rplu2core pack
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_RPLU2CORE.bit
```

Current 2026-07-04 bench result: after routing `clk_fast` through BUFG, the
image routes at the 2 MHz bring-up target (`clk_fast` max 4.39 MHz),
SRAM-loads with `done 1`, hydrates the 149-record consume profile, and passes
QR plus QSUB readback over J11 bit-banged SPI:

```text
RPLU2_J11: PASS
RPLU2CORE_QR: PASS
qsub lane=3 A=9 B=18 C=27 D=36
RPLU2CORE_QSUB: PASS
```

### 4.3c Wukong J11 SU3SHARE Shared-Multiplier Smoke
The `SU3SHARE` Artix spin keeps the main core and RPLU2 config/QR path present
while the SU3 sidecar borrows one top-level shared `spu13_m31_multiplier`.

```bash
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t su3share synth
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t su3share pnr
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t su3share pack
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_SU3SHARE.bit
```

Current 2026-07-06 restart revalidation: the image routes at the 2 MHz bring-up target
(`clk_fast` max 3.67 MHz), uses 64 DSP48E1 cells total for the shared M31 path,
SRAM-loads with `done 1`, and has SHA-256
`0f886350d43966303aa1c74c38265dd8ee3b8554b71eb531589027db780681cf`.

Run the SU3 smoke first:

```bash
picotool load -f build/rp2350_arithmetic/rp2350_su3_j11_smoke.uf2
```

Expected result:

```text
SU3_J11: PASS
```

Current 2026-07-06 SU3 smoke firmware SHA-256:
`a6d8f0541fd2cce3a930173b0ee43ba071c92826fc5dc81540674c1e0a9da87d`.
It checks all 9 dense-product result elements, using QR lanes 0 through 8.

Then load the RPLU2 smoke firmware against the same FPGA image:

```bash
picotool load -f build/rp2350_arithmetic/rp2350_rplu2_j11_smoke.uf2
```

Expected result:

```text
RPLU2_J11: PASS
RPLU2CORE_QR: PASS
RPLU2CORE_QSUB: PASS
```

### 4.4 SPI Protocol (Mode 0, 2 MHz)
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

### 5.1 Tang Primer 25K (Split-Build Subsystem Probes)

The 25K uses independent probes (see Section 2.1). The regression ladder is
closed; retest in this order when checking a board or after RTL/toolchain edits:

1. **SPI-only smoke:** `bash build_25k_southbridge_spi_probe.sh` → load → verify RP2350↔FPGA SPI
2. **Core-attached SPI link:** `bash build_25k_spu13_southbridge_link.sh` → load → verify SPI with the real integration shell
3. **Math probe:** `bash build_25k_spu13_math_probe.sh` → load → verify ROTC/Davis/rotor
4. **RPLU2 arithmetic:** `bash build_25k_spu13_rplu2_arith_probe.sh` → load → verify QLDI/QSUB/RPLU2 config
5. **ROTC 0-5:** `bash build_25k_spu13_rotc_probe.sh` → load → verify `ROTC:P A:5 E:00`
6. **Six-step robotics:** `bash build_25k_spu13_six_step_probe.sh` → load → verify `KIN:P P:5 E:00`
7. **SOM/BMU:** `bash build_25k_spu13_som_bmu_probe.sh` → load → verify `SOM:P T:2 B:6 E:00`
8. **Lucas MAC:** `bash build_25k_spu13_lucas_mac_probe.sh` → load → verify `LUCAS:P`
9. **Neuro guard:** `bash build_25k_spu13_neuro_guard_probe.sh` → load → verify fixed-epoch accept/reject/fallback telemetry
10. **Neuro SPI adapter:** `bash build_25k_spu13_neuro_sidecar_probe.sh` → load → verify `N:P T:3 E:00`

First load SRAM only, without `-f`:
```sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_<probe>.fs
```

See `docs/archive/tang25k/tang25k_replacement_bringup_plan.md` for detailed sequences.

### 5.2 Tang Primer 25K (RP2350 Southbridge)
1. Flash `rp2350_uart_injector.uf2` to RP2040
2. Wire RP2040 UART → FPGA UART RX (Pin B3)
3. Insert SD card with `.sas` programs
4. RP2040 streams instructions to FPGA
5. FPGA UART TX → RP2040 UART RX → host terminal

### 5.3 QMTech XC7A100T Wukong (JTAG + LUCAS First)
Active on the bench for silicon proofs.

1. Build and flash RP2040 DirtyJTAG with the low-pin preset:
   ```bash
   cmake -S tools/rp2040_tooling/repos/pico-dirtyJtag \
     -B build/pico_dirtyjtag_zero \
     -G Ninja \
     '-DCMAKE_C_FLAGS=-mcpu=cortex-m0plus -mthumb -DBOARD_TYPE=BOARD_RP2040_ZERO'
   cmake --build build/pico_dirtyjtag_zero --target dirtyJtag -j
   picotool info -a build/pico_dirtyjtag_zero/dirtyJtag.uf2
   ```
   The UF2 must report `0:TDI`, `1:TMS`, `2:TCK`, and `3:TDO` in its fixed-pin
   information. If it reports `16:TDI`, `17:TDO`, `18:TCK`, and `19:TMS`, it is
   the upstream Pico-default pinout and will not match the GP0-GP3 bench wiring.
2. Wire the RP2040 JTAG pod to the Wukong JTAG header:
   ```text
   RP2040 GP2  -> Wukong TCK
   RP2040 GP1  -> Wukong TMS
   RP2040 GP0  -> Wukong TDI
   RP2040 GP3  <- Wukong TDO
   RP2040 GP4  -> Wukong reset, optional
   RP2040 GND  -> Wukong GND
   ```
   On the QMTech Wukong V02 schematic, J1 is `1=3V3 reference`, `2=TCK`,
   `3=TDO`, `4=TDI`, `5=TMS`, and `6` has no visible net label in the schematic
   crop. Do not use J1-3 as ground; it is TDO. Use a confirmed Wukong GND point
   for the RP2040 ground lead, and do not back-power the board through J1-1.
   Power Wukong from its normal input, then measure J1-1 only as the target
   3.3 V reference. Before first SRAM load, set any Wukong configuration-mode
   jumpers or DIP switches to the board's JTAG/safe mode per silkscreen so a bad
   SPI-flash image cannot keep the FPGA in a configuration retry loop.
3. Verify USB/JTAG enumeration: `openFPGALoader --scan-usb`
4. Verify the JTAG chain with the actual Wukong cable before loading any bitstream.
   Current bench result, 2026-07-02: corrected low-pin UF2 flashed and J1 wiring
   fixed. `openFPGALoader -c dirtyJtag --freq 1000000 --detect -v` reports
   IDCODE `0x03631093`, manufacturer Xilinx, family Artix A7 100T, model
   `xc7a100`, IR length 6.
5. Build the pinned LUCAS bitstream: `A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t lucas all`
6. SRAM-load `build/spu_a7_100t_LUCAS.bit` only after the Wukong JTAG path is
   identified. Select the explicit cable/profile reported by `openFPGALoader`;
   do not write configuration flash during first bring-up.
   Current bench result, 2026-07-02 before the J11 SPI remap:
   `openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_LUCAS.bit`
   reaches `Load SRAM 100%` and reports `done 1`.
   Current bench result, 2026-07-03: the replacement image is routed to the
   J11 PMOD SPI pins, SRAM-loads with `done 1`, and passes RP2350 smoke
   PSCALE/PCHIRAL/PMUL/PINV commands over J11.
7. After JTAG/reset/UART smoke passes, flash `rp2350_spu_interface.uf2` or a
   focused smoke image to the RP2350 southbridge.
8. Wire RP2350 -> FPGA SPI pins (see §4.2).
9. Insert SD card with `.sas` programs, manifests, configs, and table packs.
10. RP2350 boots, mounts SD, loads RPLU tables, hydrates manifold.
11. For the main-core smoke, load `build/spu_a7_100t_ROBOTICS.bit`, then flash
    `build/rp2350_arithmetic/rp2350_spu_arithmetic_test.uf2`.
12. Capture USB CDC. The current Wukong acceptance line is
    `ARITHMETIC_BLAZE: PASS` after `13/13` QLDI/QSUB/ROTC checks.

Only write the Wukong configuration flash after the SRAM-loaded bitstream has
passed JTAG, reset, UART, and southbridge smoke tests.

## 6. Verification Matrix

| Test | VM | RTL (iverilog) | RTL (Verilator) | Silicon |
|---|---|---|---|---|
| QLDI (quadray load) | ✅ | ✅ | ✅ | ✅ 25K + A7 |
| QSUB (quadray subtract) | ✅ | ✅ | ⬜ | ✅ 25K + A7 |
| ROTC (all 6 angles) | ✅ | ✅ | ✅ | ✅ 25K + A7 |
| HEX (coordinate output) | ✅ | ✅ | ✅ | ✅ 25K |
| SOM_CLASSIFY (BMU) | ✅ | ✅ | ✅ | ✅ 25K |
| SOM_TRAIN (weight update) | ✅ | ✅ RTL ready | ⬜ | ⬜ |
| Gatekeeper (RCA₀/WKL₀) | ✅ | ✅ | ✅ | ⬜ |
| Six-step robotics kinematics | ✅ | ✅ | ✅ | ✅ 25K |
| Robotics FK closure | ✅ | ✅ | ✅ in ROM | ⬜ |
| Neighborhood training | ✅ | ⬜ | ⬜ | ⬜ |
| RPLU correction | ✅ | ✅ RTL ready | ⬜ | ⬜ |
| GPU rasterization | ✅ | ✅ | ✅ | ⬜ |
| SDRAM persist | ✅ | ✅ RTL ready | ⬜ | ⬜ |

Legend: ✅ verified | ⬜ pending hardware or toolchain

## 7. File Inventory

Historical snapshot only. Use `rg --files`, `git status`, and
`docs/CURRENT_STATUS.md` for current counts and proof status.

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
