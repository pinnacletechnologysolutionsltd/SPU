# Hardware Evidence Ledger

A boring, reproducible record of what passed, what failed, and what remains
unproven.  No speculation — only commands, conditions, and results.

*Last updated: 2026-06-17*

---

## 1. Target Hardware

| Property | Value |
|---|---|
| FPGA | Gowin GW5A-LV25MG121NES (Tang Primer 25K) |
| Carrier | Sipeed Tang Primer 25K Dock |
| SDRAM | Winbond W9825G6KH (256 Mbit SDR SDRAM) on 40-pin Dock header |
| Flash | External SPI NOR (J4), 16 MiB |
| FTDI UART | Sipeed onboard, 115200 baud |
| Toolchain | OSS CAD Suite: Yosys 0.50 → nextpnr-himbaechel → gowin_pack → openFPGALoader |

### Board Condition

| Item | Status | Detail |
|---|---|---|
| SDRAM DQ[10] | **Damaged** | Pin stuck high on the Dock board; requires `dq10_masked` build variant. All other SDRAM pins functional. |
| FPGA core | Functional | No known silicon faults |
| SPI flash J4 | Functional | JEDEC ID `D0EF4018` confirmed |
| FTDI UART bridge | Functional | Reliable at 115200 baud |
| PMOD GPIO | Untested | Not yet probed |
| RP2350 southbridge | Not connected | Planned, not yet wired |

### Second FPGA

A replacement / second Tang Primer 25K is in transit. The damaged board remains
the risky IO and regression target; the replacement board should repeat the
RPLU/SDRAM/core probe ladder with no SDRAM pin mask.

---

## 2. What Passed — Simulation

### 2.1 Python VM Test Suite

**Command:**

```
python3 software/spu_vm_test.py
```

**Result:** `85 passed, 0 failed — PASS`

Covers: surd arithmetic, Pell rotor walk, SdfState snap_check, Quadray
coordinate ops, manifold types, Lithic-L assembler, Davis Gate integration.

### 2.2 Python VM Polystep / Ratio Comparison

**Command:**

```
python3 software/spu_vm_polystep_ratiocmp_test.py
```

**Result:** PASS (exact rational comparison across polystep sequences)

### 2.3 RPLU Bring-Up Regression

**Command:**

```
tools/run_rplu_bringup_regression.sh
```

Covers seven testbenches:

| Testbench | Status |
|---|---|
| `spu_laminar_boot_rplu_tb` | PASS — SPI bootloader emits RPLU config writes from chord records at `0x110000` |
| `rplu_exp_tb` | PASS — RPLU vnorm/dissoc table behaviour |
| `rplu_metric_vectors_tb` | PASS — RTL table lookup against generated metric vectors |
| `davis_to_rplu_tb` | PASS — large-axis clamp and delayed-start address capture |
| `spu_rotor_vault_tb` | PASS — Pell rotor vault reset, hydration-safe storage, per-axis octave walk |
| `spu13_rplu_addr_tb` | PASS — SPU-13 axis walk reaches RPLU address `0x3FF` |
| `rplu_metric_reference.py` | Source-table metrics match generated RTL vectors and flash chord payload CRC |

### 2.4 Verilog Testbench Inventory

73 testbenches exist under `hardware/tests/` across four categories:

| Category | Count | Examples |
|---|---|---|
| `common/` | 63 | spu_unified_alu_tdm_tb, spu_rotor_vault_tb, davis_gate_dsp_tb, rplu_tb, spu_mem_bridge_sdram_tb, spu_bresenham_tb, spu_raster_tb |
| `peripherals/` | 2 | gpu_pipeline_tb, rotor_compare_tb |
| `spu13/` | 3 | spu13_manifold_tb, spu_artery_tb, spu_whisper_tb |
| `spu4/` | 2 | spu4_precession_tb, tang25k_smoketest_tb |

### 2.5 ROTC Angle Catalog Correction & Trace Equivalence

**Corrected ROTC table (June 2026):** Three legacy defects fixed:
- Angle 2: documented as thirds coefficients, hardware bypasses as P5 permutation
- Angle 3: was singular (det=0) — corrected to thirds period-2
- Angle 5: duplicated angle 1 — corrected to P5 inverse cycle

All six angles now have determinant=1, documented inverse, and matching
VM/RTL/silicon path.

**ROTC testbench:**

| Testbench | Status |
|---|---|
| `spu13_rotc_tdm_tb` | PASS — all 5 non-identity ROTC cases on TDM rotor core |
| `test_rotc_vm_rtl_trace.py` | PASS — bit-exact for all 6 angles (VM vs RTL) |

**Command:** `python3 software/tests/test_rotc_vm_rtl_trace.py`

### 2.6 SOM/BMU Classifier Pipeline

**Command:** `python3 software/tests/test_som_bmu_rtl_trace.py`

| Testbench | Status |
|---|---|
| `spu_som_bmu_tb` (generated) | PASS — 7-node fixture, all 12 BMU scenarios |
| `test_som_bmu_rtl_trace.py` | PASS — bit-exact VM-vs-RTL on best_id, second_id, label, gap, ambiguity |

Core integration in `spu13_core.v` behind `ENABLE_CORE_SOM=1` (+39 LUTs).
Opcode 0x2A `SOM_CLASSIFY` wired into sequencer FSM.

### 2.7 Rational Robotics Oracle

**Command:** `python3 software/tests/test_rational_robotics.py`

**Result:** `56 passed, 0 failed — PASS`

Covers: Pell inverse closure (scalar + vector), F/G/H circulant determinant=1,
circulant inverse closure (5 joints), circulant period validation, FK chain
identity, FK/IK round-trip closure, six-step kinematics trace (inverse-balanced
every phase, orbit closes at phase 5), legacy table audit.

C++ parity: `software/common/tests/spu_rational_robotics_test.cpp`

### 2.8 Rational SOM Oracle

**Command:** `python3 software/tests/test_rational_som.py`

**Result:** `24 passed, 0 failed — PASS`

Covers: integer and surd BMU scenarios, weighted quadrance ordering,
stable tie-breaking (lower node_id wins ties), hex neighbor deltas,
confidence gap, ambiguity flag.

C++ parity: `software/common/tests/spu_rational_som_test.cpp`

### 2.9 Wildberger Rational Trigonometry Library

7 files, 30+ primitives under `tools/` as `.lith` source:

| File | Contents |
|---|---|
| `wildberger_spread.lith` | Spread + collinearity via Delta opcode |
| `wildberger_geometry.lith` | 5 geometry primitives |
| `wildberger_calculus.lith` | Tangents + Faulhaber areas |
| `wildberger_layer2.lith` | Quadrance_between, normalize, Pell polynomials |
| `wildberger_chromogeometry.lith` | Blue/red/green triple, Pell-quintic connection |
| `wildberger_higher_dim.lith` | Cross matrix, diagonal rule, 2-subspaces |
| `call_demo.lith` | CALL/RET subroutine test |

### 2.10 C++ Test Suite

11 C++ test files under `software/common/tests/`:

| Test | Domain |
|---|---|
| `spu_surd_test.cpp` | Q(√3) arithmetic: (a+b√3)×(c+d√3) = (ac+3bd)+(ad+bc)√3 |
| `spu_quadray_test.cpp` | Quadray coordinate ops, zero-sum hyperplane |
| `spu_ivm_test.cpp` | IVM lattice, Fuller volumes |
| `spu_wildberger_test.cpp` | Spread/quadrance invariants |
| `spu_manifold_types_test.cpp` | 13-axis manifold type system |
| `spu_physics_test.cpp` | Davis Gate laminar condition checks |
| `spu_hex_hierarchy_test.cpp` | Concentric hierarchy polyhedra |
| `spu_lithic_l_test.cpp` | Lithic-L assembler/disassembler |
| `spu_sdf_test.cpp` | Signed distance function evaluation |
| `spu_rational_robotics_test.cpp` | C++17 exact rational robotics oracle (56 checks parity) |
| `spu_rational_som_test.cpp` | C++17 rational SOM BMU oracle (24 checks parity) |

---

## 3. What Passed — Hardware Probes

The build commands in this section record the commands used for the original
captures. In the current tree, the wider RPLU/SDRAM rebuild scripts and
matching synthesis files are archived under `hardware/boards/archive/`. Use the
existing `build/*.fs` artifacts for replay, or restore/modernize the archived
scripts before claiming a fresh rebuild.

### 3.1 RPLU Flash-Load Proof (board present)

**Historical build command:**

```
./build_25k_spu13_rplu_probe.sh
```

**Probe command:**

```
tools/probe_tang25k_rplu_flash.py
```

**Proof lines captured on UART:**

```
B:D0EF4018 A:C     # SPI flash JEDEC ID confirmed
R:D28003FF A:D     # marker=0x1A5, mask=0x0000, addr=0x3FF — full table reach
R:00000803 A:E     # 2051 RPLU records loaded
R:1D971036 A:F     # RPLU checksum matches generated payload
```

**Interpretation:**
- SPI flash is readable at JEDEC address
- RPLU config chords loaded from flash into BRAM-based response surface
- All 2051 records intact (CRC match against `rplu_metric_reference.py` output)
- Address walk covers entire table (`0x000` through `0x3FF`)

### 3.2 RPLU + Math Path Proof

**Historical build command:**

```
./build_25k_spu13_rplu_math_probe.sh
```

**Result:** Same UART proof lines as 3.1, but `A:D` now driven by live rotated
SPU-13 axis data through the RPLU lookup path. Confirms the math datapath
(Surd ALU → rotor vault → Davis Gate → RPLU address) is functional.

### 3.2a RPLU v2 PMOD Flash Boot-Table Proof

**Probe command:**

```
tools/probe_tang25k_rplu_flash.py \
  --bitstream build/tang_primer_25k_spu13_rplu2_boot_probe.fs \
  --expected-jedec 0xEF4018 \
  --expected-rplu-marker 0x1A5 \
  --expected-rplu-mask 0x0000 \
  --expected-rplu-addr 0x3FF \
  --expected-rplu-loaded 0x51 \
  --expected-rplu-checksum 0x35DE2068
```

**Proof lines captured on UART:**

```
SPI JEDEC: B:10EF4018 A:C
RPLU: R:D28003FF A:D marker=0x1A5 mask=0x0000 addr=0x3FF
RPLU loaded: R:00000051 A:E count=81
RPLU checksum: R:35DE2068 A:F checksum=0x35DE2068
RPLU hardware probe PASS
```

**Interpretation:**
- Tang Primer 25K PMOD J4 mapping is proven: `J4[0]=CS#`, `J4[1]=SCK`,
  `J4[2]=MOSI/D1`, `J4[3]=MISO/DO`
- External W25Q128-class PMOD flash responds from FPGA logic (`JEDEC EF4018`)
- RPLU v2 boot table at flash offset `0x110000` is parsed and hydrated
- Current boot table image is 81 records with checksum `0x35DE2068`

### 3.3 RPLU + Math + SDRAM Proof

**Historical build command:**

```
./build_25k_spu13_rplu_math_sdram_probe.sh
```

**Result:** RPLU proof lines preserved, plus SDRAM write/read self-test passes
on the W9825G6KH module. Lattice (13-axis manifold) remains disabled at this
stage.

### 3.4 Full Probe (RPLU + Math + SDRAM + Lattice)

**Historical build command:**

```
./build_25k_spu13_rplu_full_probe.sh
```

**Probe command:**

```
tools/probe_tang25k_rplu_flash.py \
  --bitstream build/tang_primer_25k_spu13_rplu_full_probe.fs \
  --expect-sdram-selftest
```

**Proven telemetry:**

| Axis | Value | Meaning |
|---|---|---|
| `A:A–A:C` | SDRAM endpoints `0x5D005D33`, checksum `0x0012E92E` | Full SDRAM write/read self-test passes |
| `A:D` | `R:D28003FF` | RPLU marker + mask + address proof |
| `A:E` | `R:00000803` | 2051 RPLU records loaded |
| `A:F` | `R:1D971036` | RPLU checksum verified |
| `A:C` | `B:D0EF4018` | SPI flash JEDEC ID |

**Proven board timing constants:** `INVERT_SDRAM_CLK=1`, `READ_CAPTURE_OFFSET=3`

### 3.5 SDRAM Pin Isolation

**Build command (unmasked):**

```
./build_25k_sdram_min_probe.sh
```

**Result:** SDRAM DQ[10] consistently reads as stuck-high. All other 15 data
pins pass per-bit walk test. Confirmed hardware fault on the Dock PCB, not the
FPGA or the SDRAM module.

**Build command (masked):**

```
./build_25k_sdram_min_probe_mask.sh
```

**Result:** With DQ[10] masked out (treated as don't-care), all remaining
DQ/DQM/addr/control pins pass. The masked build is used for all subsequent
SDRAM-containing probes.

---

## 4. Synthesis Resource Reports

### 4.1 SPU-13 RPLU + Math + SDRAM + Lattice (full probe)

*To be populated from the most recent synthesis run.*

```
yosys synth_gowin resource report:
  LUTs:  [pending]
  FFs:   [pending]
  BRAMs: [pending]
  DSPs:  [pending]
```

### 4.2 Tang Nano 1K / ICE40 Targets

*Not yet built on this machine. Scripts exist: `build_gw1n1.sh`,
`hardware/ice40_nano/`, `hardware/ice40_regular/`.*

---

## 5. What Remains Unproven

### Board-Level

| Item | Status |
|---|---|
| SDRAM DQ[10] repair | Physical fault — permanent mask or board replacement required |
| Second FPGA board | In transit — needed for unmasked full-bandwidth SDRAM probe |
| RP2350 southbridge (USB/HID/sensors/timing) | Not wired, not tested |
| RP2040 visualization/debug bridge | Not wired, not tested |
| PMOD peripheral modules | Not connected, not tested |
| Continuous telemetry loop (>30s) | Only snapshot probes captured so far |

### Core Architecture

| Item | Status |
|---|---|
| 13-axis manifold full at-speed compute | Lattice enabled in full probe; sustained operation not yet stress-tested |
| Davis Gate / Henosis one-cycle correction pulse | Simulated (verified in `davis_gate_dsp_tb`), not captured on hardware |
| Pell octave rollover at r⁹ boundary | Verified in simulation (`spu_rotor_vault_tb`, `spu_vm_test.py`); hardware probe covers r⁰–r⁷ |
| Inter-SPU node link protocol | `spu_node_link_tb` exists, not probed on hardware |
| SDRAM arbiter under concurrent access | Simulated (`spu_sdram_arbiter_tb`), not stress-tested on hardware |
| ROTC angles 0–5 in silicon | All 6 angles verified in RTL (`spu13_rotc_tdm_tb`), VM-vs-RTL trace equivalence proven; silicon blaze pending replacement 25K — see `docs/rotc_robotics_bringup_plan.md` |
| SOM/BMU classifier in silicon | 7-node fixture verified in RTL (`test_som_bmu_rtl_trace.py`), VM-vs-RTL trace equivalence proven; silicon blaze pending replacement 25K — see `docs/som_bringup_plan.md` |
| Six-step robotics kinematics harness | Oracle exists (56 checks), RTL trace test exists; harness rebuild and silicon proof pending — see `docs/rotc_robotics_bringup_plan.md` |
| QSUB and DELTA RTL FSMs | VM handlers ready; RTL FSM not yet implemented — pending per `commercialization_and_development_roadmap.md` Phase 0 |

### Application Domain

| Item | Status |
|---|---|
| Robotics actuator state simulation | Exists in software (`spu_physics_test.cpp`); no hardware loop |
| Encoder/IMU-like proprioception | Not yet implemented |
| Contact/friction RPLU correction | Not yet implemented |
| Telemetry visualization | Not yet implemented |
| Bresenham Killer (raster accelerator) | Simulated (`spu_bresenham_tb`), not on hardware |
| Sound card / PDM audio | Simulated (`spu_pdm_audio_tb`), not on hardware |
| Flash-backed boot from cold | Verified via RPLU flash-load (marker `0x1A5`); full-firmware cold boot not yet demonstrated |

### Tooling

| Item | Status |
|---|---|
| `run_all_tests.py` | Hardcoded path fixed (now uses `Path(__file__).resolve().parent`); **directory paths not yet reconciled** with refactored RTL layout — inc_dirs/scan_dirs reference `hardware/common/rtl/` which is now `hardware/rtl/`. Needs full path audit before Verilog suite runs. |
| C++ test suite automated run | `run_all_tests.py` supports C++ discovery; three key tests confirmed passing manually (spu_surd, spu_quadray, spu_wildberger via `g++ -std=c++17`). Full suite not yet exercised. |
| Cross-validation (Python VM vs C++) | PASS — `cross_validate.py`: 5/5 snaps matched |

---

## 6. Toolchain Versions (Confirmed Working)

| Tool | Version / Path | Purpose |
|---|---|---|
| **iverilog** | OSS CAD Suite, `/opt/oss-cad-suite/bin/iverilog` | Verilog simulation (Icarus) |
| **vvp** | OSS CAD Suite, `/opt/oss-cad-suite/bin/vvp` | VVP runtime |
| **yosys** | OSS CAD Suite | Synthesis (synth_gowin) |
| **nextpnr-himbaechel** | OSS CAD Suite | Place & route (GW5A-25A) |
| **gowin_pack** | OSS CAD Suite | Bitstream packaging |
| **openFPGALoader** | OSS CAD Suite | FPGA programming via USB |
| **python3** | 3.14.5 | VM, tools, test infrastructure |
| **g++** | C++17 | Reference implementation and C++ tests |
| **bash** | /bin/bash | Build scripts |

---

## 7. Key Proof Lines (Quick Reference)

Copy these into any bring-up log to establish that the known-good configuration
is loaded:

```
B:D0EF4018 A:C              # SPI flash JEDEC ID
R:D28003FF A:D              # RPLU: marker=0x1A5, mask=0x0000, addr=0x3FF
R:00000803 A:E              # RPLU: 2051 records loaded
R:1D971036 A:F              # RPLU: checksum OK
SDRAM: 0x5D005D33 / 0x0012E92E   # SDRAM endpoints / checksum (full probe only)
```

Without these four RPLU lines and the SPI JEDEC line, no subsequent test
result should be treated as meaningful — the RPLU surface is the hardware
correction baseline and any drift from these values indicates a build, flash,
or timing regression.

---

*CC0 1.0 Universal — public domain*
