# Hardware Evidence Ledger

A boring, reproducible record of what passed, what failed, and what remains
unproven.  No speculation — only commands, conditions, and results.

*Last updated: 2026-07-06*

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
| RP2350 southbridge | Functional | SPI & SD hydration link verified in silicon (June 28 and June 30, 2026) |

### Second FPGA

A replacement / second Tang Primer 25K is in transit. The damaged board remains
the risky IO and regression target; the replacement board should repeat the
RPLU/SDRAM/core probe ladder with no SDRAM pin mask.

### Open ECP5 Build Targets

These are routed build artifacts, not physical-board smoke tests.

| Target | Status | Detail |
|---|---|---|
| Colorlight i9 RPLU2 probe | Synthesis/P&R/bitstream pass | `spu_colorlight_i9_rplu2_top`: 6,881 / 43,848 LUT4 before packing, 1,967 FF, 72 / 72 MULT18X18D, 0 / 108 DP16KD, 44.05 MHz max core clock, PASS at 25 MHz. Bitstream: `build/spu_colorlight_i9_rplu2_top.bit` (297 KiB). |
| ECP5-85F placeholder | Synthesis/P&R/bitstream pass | `spu_ecp5_top`: 293 / 83,640 LUT4 before packing, 97 FF, 0 / 156 MULT18X18D, 0 / 208 DP16KD, 273.00 MHz max generated internal clock, PASS at 50 MHz. Bitstream: `build/spu_ecp5_top.bit` (278 KiB). |

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
| `spu13_tang25k_rotc_probe_tb` | PASS — Tang wrapper self-check for all 6 angles plus period closure |

**Command:** `python3 software/tests/test_rotc_vm_rtl_trace.py`

### 2.6 SOM/BMU Classifier Pipeline

**Command:** `python3 software/tests/test_som_bmu_rtl_trace.py`

| Testbench | Status |
|---|---|
| `spu13_som_bmu_tb` | PASS — 7-node fixture smoke, 3 BMU scenarios |
| `test_som_bmu_rtl_trace.py` | PASS — bit-exact VM-vs-RTL on 2 built-in fixture scenarios: best_id, second_id, label, gap, ambiguity |
| `spu13_tang25k_som_bmu_probe_tb` | PASS — Tang wrapper self-check for 2 oracle scenarios |

Core integration in `spu13_core.v` behind `ENABLE_CORE_SOM=1` (+39 LUTs).
Opcode 0x2A `SOM_CLASSIFY` wired into sequencer FSM.

### 2.7 Rational Robotics Oracle

**Command:** `python3 software/tests/test_rational_robotics.py`

**Result:** `PASS (104 checks)`

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

### 3.0 Wukong Artix-7 ROBOTICS Main-Core Smoke

**Bitstream loaded:**

```
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_ROBOTICS.bit
```

**Configuration result:** `Load SRAM 100%`, `isc_done 1`, `init 1`, `done 1`.

**RP2350 firmware:**

```
picotool load -f build/rp2350_arithmetic/rp2350_spu_arithmetic_test.uf2
```

**Capture result over Wukong J11:** `=== Results: 13/13 PASSED ===`,
`ARITHMETIC_BLAZE: PASS`.

**Coverage:** QLDI positive/signed loads, QSUB positive/negative/self-zero,
corrected ROTC angles 0-5, and ROTC angle-1 six-step closure through the main
`spu13_core` path.

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
R:00000095 A:E     # 149 RPLU v2 records loaded (legacy v1 was 2051 records)
R:3A0AB5E9 A:F     # RPLU checksum (matches 16-record subset or full 149-record table)
```

**Interpretation:**
- SPI flash is readable at JEDEC address
- RPLU config chords loaded from flash or SD card (via southbridge) into BRAM
- RPLU v2 default table contains 149 records (legacy v1 was 2051 records)
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
  --expected-rplu-loaded 0x95 \
  --expected-rplu-checksum 0x0AA480E2
```

**Proof lines captured on UART:**

```
SPI JEDEC: B:10EF4018 A:C
RPLU: R:D28003FF A:D marker=0x1A5 mask=0x0000 addr=0x3FF
RPLU loaded: R:00000095 A:E count=149
RPLU checksum: R:0AA480E2 A:F checksum=0x0AA480E2
RPLU hardware probe PASS
```

**Interpretation:**
- Tang Primer 25K PMOD J4 mapping is proven: `J4[0]=CS#`, `J4[1]=SCK`,
  `J4[2]=MOSI/D1`, `J4[3]=MISO/DO`
- External W25Q128-class PMOD flash responds from FPGA logic (`JEDEC EF4018`)
- RPLU v2 boot table at flash offset `0x110000` is parsed and hydrated
- Current default boot table image is 149 records with checksum `0x0AA480E2`
- Historical note: the obsolete 81-record image used checksum `0x35DE2068`;
  do not use it for current RPLU2 consumption tests.

### 3.2b RP2350 Southbridge Write + SD Hydration Proof

**Date:** 2026-06-30 NZT

**Fixes under test:**
- `hardware/rp_common/spu_link.c`: CRC-8 helper now compares the CRC MSB as a
  0/1 bit, and write transactions hold CS low for 1 us after the CRC byte.
- `hardware/rtl/peripherals/io/spu_spi_slave.v`: `0xA5` and `0xB1` write
  commands enter receive state immediately after the command byte, and the
  write deadman timeout allows RP firmware inter-byte gaps.

**Simulation command:**

```
TB_FILTER=spu_spi_slave python3 run_all_tests.py
```

**Result:** PASS, including delayed `0xA5` payload reception with
firmware-style gaps inside one held-CS transaction.

**SPI-only Tang probe:**

```
bash build_25k_southbridge_spi_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_southbridge_spi_probe.fs
```

**Routed footprint:** 1,861 LUT4, 840 DFF, 0 BRAM, 0 DSP. Timing passes at
12 MHz (`clk_50m` max 82.50 MHz).

**RP2350 diagnostic proof:**

```
status raw=25 A5 00 00
rplu 0 1 2 0x0000000000010000
cfgtele count=1 last_sel=0 last_material=1 last_addr=2
        last_data=0x0000000000010000 checksum=0x00000002
sdhydrate -> 16 records loaded, 0 skipped
cfgtele count=16 checksum=0x3A0AB5E9
```

**Core-attached Tang probe:**

```
bash build_25k_spu13_southbridge_link.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_southbridge_link.fs
```

**Routed footprint:** 4,054 LUT4, 3,091 DFF, 0 BRAM, 0 DSP. Timing passes at
12 MHz (`clk_50m` max 55.48 MHz, `clk_core` max 102.46 MHz).

**RP2350 diagnostic proof:**

```
status raw=13 A5 00 00
rplu 0 1 2 0x0000000000010000
cfgtele count=1 last_sel=0 last_material=1 last_addr=2
        last_data=0x0000000000010000 checksum=0x00000002
sdhydrate -> 16 records loaded, 0 skipped
cfgtele count=16 checksum=0x3A0AB5E9
```

### 3.2c RPLU2 Arithmetic Probe + Consume Table Proof

**Date:** 2026-06-30 NZT

**Fix under test:** `hardware/rtl/core/shared/spu_quadray_regfile_ecc.v`
now resets ECC parity arrays to constants. This avoids non-constant async
reset values during Gowin/Yosys FF legalization while preserving the QR reset
contents.

**Simulation commands:**

```
TB_FILTER=ecc_wrapper python3 run_all_tests.py
TB_FILTER=spu_hamming python3 run_all_tests.py
```

**Result:** PASS for the focused ECC wrapper and Hamming SECDED tests.

**Tang probe build:**

```
bash build_25k_spu13_rplu2_arith_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_rplu2_arith_probe.fs
```

**Routed footprint:** 9,211 LUT4, 7,926 DFF, 822 ALU, 0 BRAM, 0 DSP. Timing
passes at 12 MHz (`clk_50m` max 54.42 MHz, `clk_core` max 48.40 MHz).

**RP2350 southbridge consume-table proof:**

```
cfgtele magic=SPUC count=149 last_sel=6 last_material=0 last_addr=0
        last_data=0x0000000000000003 checksum=0xBA708FD4
        rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001
        rplu2_num0=0x00000002 rplu2_delta=0x00000000
        rplu2_row1=0x00000001 rplu2_kappa=0x00000003
```

**RP2350 arithmetic firmware proof:**

```
cmake --build build/rp2350_zero_header --target rp2350_spu_arithmetic_test -j
picotool load -f build/rp2350_zero_header/rp2350_spu_arithmetic_test.uf2
```

Captured result:

```
[1/6] QLDI QR0 = (3,0,0,0)                 PASS
[2/6] QLDI QR1 = (1,0,0,0)                 PASS
[3/6] QSUB QR2 = QR0 - QR1 = (2,0,0,0)     PASS
[4/6] QSUB QR3 = QR1 - QR0 = (-2,0,0,0)    PASS
[5/6] QLDI QR4 = (-5,-3,7,-1)              PASS
[6/6] QSUB QR5 = QR4 - QR4 = (0,0,0,0)     PASS

ARITHMETIC_BLAZE: PASS
```

### 3.2d Neuro Sidecar SPI Adapter Probe

**Date:** 2026-06-30 NZT

**Fixes under test:**
- `hardware/boards/tang_primer_25k/spu13_tang25k_neuro_sidecar_probe.v` now
  waits one additional clock before checking registered `NEURO_READ` QR
  readback. The first SRAM load of the old wrapper reported `N:F T:1 E:A2`;
  board-level simulation reproduced this as an early readback sample.
- The epoch-B overflow fixture now packs the `NEURO_CFG` weight and threshold
  into the adapter's 10-bit command fields. The old wrapper left the B neuron
  at zero config and could reject on norm before proving overflow.

**Simulation commands:**

```
iverilog -I hardware/rtl/arch \
  -o build/spu13_neuro_sidecar_adapter_tb.vvp \
  hardware/rtl/core/spu13/spu13_neuro_sidecar_adapter.v \
  hardware/rtl/core/spu13/spu13_neuro_epoch_sidecar.v \
  hardware/tests/spu13/spu13_neuro_sidecar_adapter_tb.v &&
vvp build/spu13_neuro_sidecar_adapter_tb.vvp

iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_neuro_sidecar_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_neuro_sidecar_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_neuro_sidecar_probe.v \
  hardware/rtl/core/spu13/spu13_neuro_sidecar_adapter.v \
  hardware/rtl/core/spu13/spu13_neuro_epoch_sidecar.v &&
vvp build/spu13_tang25k_neuro_sidecar_probe_tb.vvp
```

**Result:** PASS for both the reusable adapter testbench and the Tang probe
wrapper testbench.

**Tang probe build:**

```
bash build_25k_spu13_neuro_sidecar_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_neuro_sidecar_probe.fs
```

**Routed footprint:** 4,013 LUT4, 380 DFF, 0 ALU, 0 BRAM, 0 DSP. Timing passes
at 12 MHz (`u_epochA.clk` max 99.53 MHz).

**UART proof:**

```
N:P T:3 E:00
```

**Interpretation:**
- The Tang image self-drives all four SPI-visible neuro adapter opcodes:
  `0xE0 NEURO_CFG`, `0xE1 NEURO_START`, `0xE2 NEURO_SPIKE`, and
  `0xE3 NEURO_READ`.
- Epoch A accept/readback is proven: commit `(12,9)`, norm `171`, total
  token count `9`, QR readback lane `5`.
- Epoch A reject/fallback is proven: mismatched norm routes fallback `(7,8)`
  and exposes the rejected status bit.
- Epoch B overflow fallback is proven with a saturated 1-neuron counter.
- External RP2350-master transactions into these neuro opcodes remain a
  separate integration proof; this probe validates the adapter command path
  inside the Tang bitstream.

### 3.2e Lucas MAC Fast-Path Zero-Drift Probe

**Date:** 2026-06-30 NZT

**Fixes under test:**
- `hardware/boards/tang_primer_25k/spu13_tang25k_lucas_mac_probe.v` now
  emits complete repeated `LUCAS:<status>` UART lines. The original probe
  arithmetic reached PASS, but the line sender could advance past the message
  and keep transmitting carriage returns only.
- `hardware/tests/spu13/spu13_tang25k_lucas_mac_probe_tb.v` covers the Tang
  wrapper state machine: PASS state, final 2,600-step drift marathon, and LED
  status.

**Simulation commands:**

```
iverilog -I hardware/rtl/arch \
  -o build/lucas_mac_tb.vvp \
  hardware/rtl/core/spu13/spu13_lucas_mac.v \
  hardware/tests/spu13/spu13_lucas_mac_tb.v &&
vvp build/lucas_mac_tb.vvp

iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_lucas_mac_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_lucas_mac_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_lucas_mac_probe.v \
  hardware/rtl/core/spu13/spu13_lucas_mac.v &&
vvp build/spu13_tang25k_lucas_mac_probe_tb.vvp
```

**Result:** PASS for the reusable Lucas MAC testbench and the Tang probe
wrapper testbench.

**Tang probe build:**

```
bash build_25k_spu13_lucas_mac_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_lucas_mac_probe.fs
```

**Routed footprint:** 696 LUT4, 216 DFF, 416 ALU, 0 BRAM, 0 DSP. Timing passes
at 12 MHz (`clk` max 126.50 MHz).

**UART proof:**

```
LUCAS:P
```

**Interpretation:**
- The Tang image instantiates `spu13_lucas_mac` with `FAST_ONLY=1`.
- PSCALE sanity is proven in silicon: `phi * (3 + 5 phi) = 5 + 8 phi`.
- PCHIRAL sanity is proven in silicon: `conj(3 + 5 phi) = 8 + 516 phi`.
- A 100-period PSCALE zero-drift marathon is proven in silicon: 2,600
  successive PSCALE steps over `Z[phi]/L_521` return to the seed at each
  26-step period boundary.
- Full PINV and MAC-backed PMUL/PINV silicon proof remains an Artix-7 or future
  dedicated Tang probe task. This Tang probe must not be cited as full-MAC
  silicon coverage.

### 3.2e.1 Lucas PHSLK Phase-Coherence Probe

**Date:** 2026-07-02 NZT

**Scope:** dedicated Tang 25K self-checking bitstream for the Lucas `PHSLK`
opcode. This proves the rational phase-coherence predicate on fixed coherent,
mismatched, and zero-divisor-denominator cases, then keeps the PHSLK datapath
live by feeding LFSR-derived dynamic operands into an observable result stream.

**Simulation command:**

```
iverilog -I hardware/rtl/arch \
  -o build/spu13_tang25k_lucas_phslk_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_lucas_phslk_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_lucas_phslk_probe.v \
  hardware/rtl/core/spu13/spu13_lucas_mac.v &&
vvp build/spu13_tang25k_lucas_phslk_probe_tb.vvp
```

**Result:** PASS for the Tang PHSLK probe wrapper testbench.

**Tang probe build/load:**

```
bash build_25k_spu13_lucas_phslk_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_lucas_phslk_probe.fs
```

**Routed footprint:** 293 LUT4, 146 DFF, 182 ALU, 0 BRAM, 0 DSP. Post-route
timing reports `u_mac.clk` max 200.40 MHz with a 4.99 ns critical path.

**UART proof:**

```
PHSLK:P
```

**Interpretation:**
- The Tang image instantiates the Lucas MAC `PHSLK` opcode and verifies the
  coherence bit plus denominator zero-divisor flag in silicon.
- This is a PHSLK microprobe, not full Lucas PMUL/PINV silicon coverage and not
  the full Artix-7 SPI sidecar timing closure.
- The bench capture was taken after SRAM load on `/dev/ttyUSB2`; repeated
  `PHSLK:P` lines were observed.

### 3.2e.2 Wukong J11 LUCAS SPI Sidecar Proof

**Date:** 2026-07-03 NZT

**Scope:** QMTech Wukong Artix-7 100T SRAM-loaded over RP2040 DirtyJTAG, with
the RP2350 `rp2350_lucas_j11_smoke` firmware driving the external SPI sidecar
through the physical J11 PMOD connector. J11 maps `H4/F4/A4/A5` to
`spi_cs_n/spi_sck/spi_mosi/spi_miso`.

**Build/load:**

```
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t lucas synth
nextpnr-xilinx ... --freq 2
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t lucas pack
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_LUCAS.bit
```

The JTAG load completed with `Load SRAM 100%`, `isc_done 1`, `init 1`, and
`done 1`.

**SPI proof:**

```
status -> raw=00 FF 00 00
chord D0200C0500000000 -> qr lane=2  A=0x0000000800000005
chord D1C00C0500000000 -> qr lane=12 A=0x0000020400000008
chord D2300C0500807000 -> qr lane=3  A=0x0000004200000029
chord D3400C0500000000 -> qr lane=4  A=0x0000000500000201
status after each opcode -> raw=00 FF 00 00
LUCAS_J11: PASS
```

**Interpretation:**
- Wukong J11 physical wiring, J11 XDC mapping, RP2040 DirtyJTAG SRAM load, and
  RP2350 external SPI transactions are verified together.
- PSCALE and PCHIRAL are direct sidecar paths; PMUL and PINV are verified
  through the CE-paced SPI sidecar sequencer.
- This is bench SRAM-load coverage at the 2 MHz Artix bring-up target, not final
  50 MHz timing closure.

### 3.2e.3 Wukong J11 RPLUCFG 149-Record Transport Proof

**Date:** 2026-07-04 NZT

**Scope:** QMTech Wukong Artix-7 100T `RPLUCFG` coreless transport spin. This
proves long `0xA5` RPLU2 config delivery over the physical J11 PMOD path without
main-core timing as a confounder.

**Build/load:**

```
bash hardware/boards/artix7/build_a7.sh 100t rplucfg all
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_RPLUCFG.bit
```

The image routed timing-clean: `clk_fast` max 83.17 MHz, PASS at 50 MHz. JTAG
SRAM load completed with `Load SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`.

**RP2350 firmware:** `build/rp2350_arithmetic/rp2350_rplu2_j11_smoke.uf2`,
using bit-banged GP0-GP3 SPI on the same J11 wiring.

**Proof lines:**

```
bus=bitbang
after status raw=5A 00 10 00 crc_error=0
after cfgtele count=149 last_sel=6 last_material=0 last_addr=0
last_data=0x0000000000000003 checksum=0xBA708FD4
rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001
rplu2_num0=0x00000002 rplu2_delta=0x00000000
rplu2_row1=0x00000001 rplu2_kappa=0x00000003
RPLU2_J11: PASS
```

**Interpretation:**
- J11 physical mapping and the Artix `0xA5` config decoder are good for the
  full 149-record consume-profile stream.
- The RP2350 hardware-SPI path is not yet reliable for long Artix RPLU2 bursts:
  with the same wiring it missed records (`count=52`, `61`, `71`, or `59`
  depending on guards/instrumentation). The bit-banged path is the current
  known-good Wukong transport.
- This is a transport/telemetry proof. Core-enabled RPLU2 coverage is recorded
  in the next Wukong section.

### 3.2e.4 Wukong J11 RPLU2CORE Config + QR Arithmetic Proof

**Date:** 2026-07-04 NZT

**Scope:** QMTech Wukong Artix-7 100T `RPLU2CORE` spin, SRAM-loaded over
RP2040 DirtyJTAG, with the RP2350 `rp2350_rplu2_j11_smoke` firmware driving
bit-banged SPI over J11. This extends the `RPLUCFG` transport proof by enabling
the main SPU-13 core and RPLU2 config path, then checking QLDI/QSUB through QR
commit readback.

**Clocking fix under test:** `clk_fast` is now driven through a BUFG in
`hardware/boards/artix7/spu_a7_top.v`. Before this fix, the fabric-divided
clock caused hardware-only QR telemetry skew even though RTL simulation passed.

**Build/load:**

```
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t rplu2core synth
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t rplu2core pnr
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t rplu2core pack
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_RPLU2CORE.bit
```

The routed image reports `clk_fast` max 4.39 MHz and PASS at the 2 MHz bring-up
target. The packed bitstream SHA-256 was
`71319fbbda67cdd6f5a713938ef860d220bc43ba0dbfc995a6245093b87799db`.

**Proof lines:**

```
after cfgtele count=149 last_sel=6 last_data=0x0000000000000003
checksum=0xBA708FD4 rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001
RPLU2_J11: PASS
RPLU2CORE_QR: PASS
qsub_q1 lane=1 A=10 B=20 C=30 D=40
qsub_q2 lane=2 A=1 B=2 C=3 D=4
qsub lane=3 A=9 B=18 C=27 D=36
RPLU2CORE_QSUB: PASS
```

**Interpretation:**
- Wukong J11 bit-banged SPI, RPLU2 consume-profile hydration, core instruction
  ingress, QR commit telemetry, QLDI, QR regfile read/write, and QSUB are now
  verified together on Artix-7 silicon.
- This is still a conservative low-MHz bring-up image. It is enough for
  functional evidence and paper claims at the "bench-verified" level, but not a
  final 50 MHz integrated timing claim.
- The old full `RPLU2` attempt packed the design densely enough to stall during
  placement (`104819/126800` LUT cells and `204/240` DSP48E1, then terminated).
  The routeable `RPLU2CORE` spin is the correct near-term proof target.

### 3.2e.5 Wukong J11 SU3SHARE Shared Multiplier Proof

**Date:** 2026-07-05 NZT

**Scope:** QMTech Wukong Artix-7 100T `SU3SHARE` spin. This image proves that
the SU3 sidecar can use a top-level shared `spu13_m31_multiplier` while the main
core and RPLU2 config/QR path remain present in the same bitstream.

**Build/load:**

```bash
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t su3share synth
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t su3share pnr
A7_FREQ=2 A7_CLK_DIV_LOG2=6 bash hardware/boards/artix7/build_a7.sh 100t su3share pack
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_SU3SHARE.bit
```

The routed image reports 60,837/126,800 LUTX cells, 16,478/126,800 FFX cells,
and 64/240 DSP48E1 cells. Router convergence ended at `iter=85` with
`overused=0`, and post-route timing reports `clk_fast` max 3.67 MHz, PASS at
the 2 MHz bring-up target. The packed bitstream SHA-256 was
`4dff1a6e5fbbfc2f10afca0afd5ff08846727a6b0b3571eb76deb755aafb80ed`.

SRAM load completed with `Load SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`.

**Proof lines:**

```text
SU3_J11: PASS

after cfgtele count=149 last_sel=6 last_data=0x0000000000000003
checksum=0xBA708FD4 rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001
RPLU2_J11: PASS
RPLU2CORE_QR: PASS
qsub lane=3 A=9 B=18 C=27 D=36
RPLU2CORE_QSUB: PASS
```

**Restart revalidation, 2026-07-06 NZT:**

After a host reboot, the current local packed `SU3SHARE` bitstream SHA-256 was
`0f886350d43966303aa1c74c38265dd8ee3b8554b71eb531589027db780681cf`. The
same build artifacts still report 60,837 LUTX cells, 16,478 FFX cells, 64
DSP48E1 cells, `iter=85 overused=0`, and `clk_fast` max 3.67 MHz. DirtyJTAG
SRAM load completed with `Load SRAM 100%`, `isc_done 1`, `init 1`, and
`done 1`.

The RP2350 `rp2350_su3_j11_smoke.uf2` run reported:

```text
SU3_J11: PASS
```

The expanded RP2350 `rp2350_su3_j11_smoke.uf2` image, SHA-256
`a6d8f0541fd2cce3a930173b0ee43ba071c92826fc5dc81540674c1e0a9da87d`,
was then loaded against the same `SU3SHARE` FPGA image. It checks all nine
dense-product result elements and tags them onto QR lanes 0 through 8. Two
complete capture loops reported exact matches for every element and ended with:

```text
case elem=0 lane=0 ... PASS
case elem=1 lane=1 ... PASS
case elem=2 lane=2 ... PASS
case elem=3 lane=3 ... PASS
case elem=4 lane=4 ... PASS
case elem=5 lane=5 ... PASS
case elem=6 lane=6 ... PASS
case elem=7 lane=7 ... PASS
case elem=8 lane=8 ... PASS
SU3_J11: PASS
```

The RP2350 `rp2350_rplu2_j11_smoke.uf2` run then reported, on the same FPGA
image:

```text
after cfgtele count=149 last_sel=6 last_data=0x0000000000000003
checksum=0xBA708FD4 rplu2_sum=0x0AA480E7 rplu2_status=0xC02E0001
RPLU2_J11: PASS
RPLU2CORE_QR: PASS
qsub qr valid=1 lane=3 A=9 B=18 C=27 D=36
RPLU2CORE_QSUB: PASS
```

**Interpretation:**
- The shared multiplier plumbing is verified in RTL and silicon. SU3 no longer
  requires a private M31 multiplier in the integrated Artix image.
- The same `SU3SHARE` bitstream also preserves RPLU2 config hydration, QR commit
  readback, and QSUB regression over the Wukong J11 path.
- This proof keeps the live RPLU2 Padé evaluator disabled (`_R2_PIPELINE=0`).
  It validates shared topology and coexistence, not simultaneous live Padé/SU3
  arbitration.

### 3.2f Wukong J11 RPLU2PADE Padé Pipeline Proof

**Date:** 2026-07-05 NZT

**Scope:** QMTech Wukong Artix-7 100T `RPLU2PADE` spin. This image proves the
SPI-visible Thimble-Padé evaluator sidecar in silicon: [4/4] Padé rational
approximant, shared M31 multiplier, and the A31 conjugate reduction inverter,
over the Wukong J11 RP2350 SPI southbridge. SOM/BMU and BTU coexistence are
covered by separate RPLU2CORE/SU3SHARE proofs; this section is the live Padé
evaluator proof.

**Build command:**
```
source tools/env_openxc7.sh
PYTHONPATH=/tmp/prjxray/third_party/fasm:/tmp/prjxray:${PYTHONPATH:-} \
PRJXRAY_ROOT=/tmp/prjxray \
OPENXC7_PYTHON=/tmp/prjxray-venv/bin/python \
A7_FREQ=2 A7_CLK_DIV_LOG2=6 \
bash hardware/boards/artix7/build_a7.sh 100t rplu2pade
```

**Yosys check:** 0 problems reported.

**Routed resource usage after FP4 inverter modular-negation cleanup:**
- 20,277 / 126,800 `SLICE_LUTX` (15%)
- 6,678 / 126,800 `SLICE_FFX` (5%)
- 72 / 240 `DSP48E1` (30%)
- 0 BRAM

The cleanup replaced `(P - x) % P` forms in `spu13_fp4_inverter.v` with an
explicit `m31_neg(x)` helper. The generated Artix JSON no longer contains
`$mod`, `$div`, or `div_mod` signatures for this spin.

Router converged: overuse=0 by iteration 9.

**Post-route timing:** `clk_fast` max 36.54 MHz, passing at 2 MHz bring-up target.

**Bitstream load:**
```
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_RPLU2PADE.bit
```

**Configuration result:** `Load SRAM 100%`, `isc_done 1`, `init 1`, `done 1`.

**RP2350 firmware smoke:**
```
cmake --build build/rp2350_arithmetic --target rp2350_rplu2_pade_j11_smoke -j
picotool load -f build/rp2350_arithmetic/rp2350_rplu2_pade_j11_smoke.uf2
```

**Capture result:** `RPLU2PADE_J11: PASS`

**Detailed results (from UART trace):**
- Focused RTL regressions before hardware load:
  `spu13_fp4_inverter`, `rplu_thimble_pade`,
  `spu13_rplu2_pade_sidecar`, `spu13_spi_rplu2_pade`
- Five RP2350-driven Padé cases pass repeatedly:
  `2/1 -> 0x00000002`, `2/2 -> 0x00000001`,
  `5/2 -> 0x40000002`, `7/3 -> 0x55555557`,
  `12345/6789 -> 0x2FCB82AA`
- Status byte: `raw=7F 2A 13 00`
- Busy clear, no CRC error, no RNS error

**FSM hardening note:** The inverter and Padé FSM state registers now use
explicit `keep` / `fsm_encoding="none"` attributes. This preserves the
silicon-passing state encodings without depending on debug-port side effects.

### 3.2g ROTC 0-5 Silicon Probe

**Date:** 2026-06-30 NZT

**Scope:** dedicated Tang 25K self-checking bitstream for the corrected ROTC
catalog. This proves all six ROTC angles on the canonical VM/RTL trace vector
and proves repeated period closure for angles 1, 2, 3, 4, and 5.

**Simulation command:**

```
iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_rotc_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_rotc_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_rotc_probe.v \
  hardware/rtl/core/spu13/spu13_rotor_core_tdm.v \
  hardware/rtl/common/prim/surd_multiplier.v &&
vvp build/spu13_tang25k_rotc_probe_tb.vvp
```

**Result:** PASS for the Tang probe wrapper testbench.

**Tang probe build:**

```
bash build_25k_spu13_rotc_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_rotc_probe.fs
```

**Routed footprint:** 13,352 LUT4, 1,036 DFF, 1,044 ALU, 0 BRAM, 0 DSP. Timing
passes at 12 MHz (`u_rotc.clk` max 73.07 MHz).

**UART proof:**

```
ROTC:P A:5 E:00
```

**Interpretation:**
- `A:5` means the self-check advanced through the final corrected angle.
- `E:00` means no mismatch was detected across the canonical trace checks or
  the closure loops.
- The probe covers the hardware TDM path and P5/P5-inverse bypass paths in the
  same routed image.
- Six-step robotics kinematics remains a distinct silicon proof; this probe
  validates the ROTC primitive layer it depends on.

### 3.2g SOM/BMU Classifier Silicon Probe

**Date:** 2026-06-30 NZT; BRAM-backed refresh verified 2026-07-06 NZT

**Fixes under test:**
- `hardware/rtl/core/spu13/spu_som_weight_bram.v` provides four synchronous
  BRAM-backed feature slices for node weights, with the seven-node fixture
  initialized in RTL and `.mem` files staged for later hydration.
- The BRAM wrapper uses registered read data so Gowin maps the writeable store
  to block RAM when `train_we`/`wr_en` is active.
- `hardware/rtl/core/spu13/spu_som_bmu.v` primes the BRAM read address before
  scanning node 0, exposes training readback from the BRAM read port, and uses
  a scalable `train_addr` width tied to `MAX_NODES`.
- `hardware/rtl/core/spu13/spu_som_train.v` latches the last valid BMU result
  so training can start after the one-cycle `bmu_valid` pulse.
- `hardware/rtl/core/spu13/spu_som_bmu.v` now latches and applies the
  `feature_weights` vector during weighted quadrance calculation. The previous
  RTL matched labels for the smoke cases but did not implement the documented
  weighted BMU contract.
- `software/tests/test_som_bmu_rtl_trace.py` now samples the one-cycle
  `bmu_valid` pulse on the completion cycle and expects BMU result packing as
  `{p[31:0], q[31:0]}`. Feature-vector inputs remain packed as `{q,p}` to match
  the core QR narrowing path.

**Simulation commands:**

```
python3 software/tests/test_rational_som.py
python3 software/tests/test_som_bmu_rtl_trace.py

iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_som_bmu_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_som_bmu_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_som_bmu_probe.v \
  hardware/rtl/core/spu13/spu_som_weight_bram.v \
  hardware/rtl/core/spu13/spu_som_bmu.v \
  hardware/rtl/core/spu13/spu_cluster_reduce.v &&
vvp build/spu13_tang25k_som_bmu_probe_tb.vvp
```

**Result:** PASS for the Python oracle, VM-vs-RTL BMU trace, Tang probe wrapper
testbench, and full repository regression (`112/112 PASS` on 2026-07-06).

**Tang probe build:**

```
bash build_25k_spu13_som_bmu_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_som_bmu_probe.fs
```

**Routed footprint:** 15,325 LUT4, 1,009 DFF, 1,268 ALU, 4 BSRAM, 0 DSP. Timing
passes at 12 MHz (`u_bmu.clk` max 77.45 MHz). The 2026-07-06 bitstream SHA-256
is `0385b641a86530696116c13e8b81676e74ec9da091617268808a503f186a9854`.

**UART proof:**

```
SOM:P T:2 B:6 E:00
```

**Re-baseline (2026-07-08):** the same golden line was re-captured on the
bare dock (southbridge rig removed, BL616 USB-CDC on pin C3) after a BL616
debugger-firmware update and a full rebuild from current HEAD — repeating
`SOM:P T:2 B:6 E:00` stream confirmed. This re-validates the whole capture
path (openFPGALoader JTAG load, 50 MHz clock, C3 UART leg) on the updated
debugger firmware. Pin note for future bring-up: C3 is the dock's USB-CDC
UART (per Sipeed's own `TangPrimer-25K-example` UART constraints); B11/A11
`uart_tx_telemetry` is a separate FPGA↔BL616 link, not the CDC console.

**Interpretation:**
- `T:2` means both built-in fixture oracle scenarios were checked.
- `B:6` means the final scenario selected node 6, the surd/titanium fixture.
- `E:00` means no mismatch was detected across BMU fields or cluster-reduce
  outputs.
- This proves deterministic SOM/BMU classification in silicon for the
  BRAM-backed 7-node fixture. It does not prove external SPI hydration of larger
  maps, visual telemetry frames, or SOM→RPLU material-bank gating.

### 3.2g.1 SOM BRAM Hydration Silicon Probe

**Date:** 2026-07-06 NZT

**Scope:** dedicated Tang 25K self-checking bitstream for the writeable SOM
node-weight BRAM primitive. The probe instantiates `spu_som_weight_bram`
directly, checks the initialized node-0 value, writes node 0 feature 0 through
the BRAM write port, reads it back, then writes only feature 3 of node 6 and
verifies that features 0-2 were preserved by the byte-enable mask.

**Simulation/build commands:**

```
iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_som_hydrate_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_som_hydrate_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_som_hydrate_probe.v \
  hardware/rtl/core/spu13/spu_som_weight_bram.v &&
vvp build/spu13_tang25k_som_hydrate_probe_tb.vvp

bash build_25k_spu13_som_hydrate_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_som_hydrate_probe.fs
```

**Result:** PASS for the hydration probe testbench, SOM-focused regression
(`TB_FILTER=som python3 run_all_tests.py`, `24/24 PASS`), and full repository
regression (`112/112 PASS`).

**Routed footprint:** 583 LUT4, 165 DFF, 200 ALU, 8 BSRAM, 0 DSP. Timing passes
at 12 MHz (`u_bram.clk` max 196.50 MHz). Bitstream SHA-256:
`6177aa67722b3888e70b251959058357ca79e0bd0b4d52f5b41ae7e4aed5d891`.

**UART proof:**

```
HYD:P T:3 B:6 E:00
```

**Interpretation:**
- `T:3` means initial readback, node-0 write/readback, and node-6 byte-enable
  preservation all passed.
- `B:6` means the final checked node was node 6.
- The full writeable-BMU Tang image was attempted first but did not legally
  place at 20,304 LUT4 / 8 BSRAM (88% LUT). Tang therefore remains split into
  a classifier proof (`SOM:P`) and a storage-hydration proof (`HYD:P`); the
  next integration step is an RP2350-driven write path into this BRAM interface.

### 3.2h Six-Step Robotics Kinematics Silicon Probe

**Date:** 2026-07-01 NZT

**Scope:** dedicated Tang 25K self-checking bitstream for the period-6 rational
robotics orbit from `software/tests/test_rotc_six_step_rtl_trace.py`. The probe
applies corrected ROTC angle 1 through six forward phases, applies angle 4 as
the inverse recovery check for every phase, rejects early closure, and requires
exact root closure on phase 5.

**Simulation commands:**

```
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rotc_six_step_rtl_trace.py

iverilog -g2012 -I hardware/rtl/arch \
  -o build/spu13_tang25k_six_step_probe_tb.vvp \
  hardware/tests/spu13/spu13_tang25k_six_step_probe_tb.v \
  hardware/boards/tang_primer_25k/spu13_tang25k_six_step_probe.v \
  hardware/rtl/core/spu13/spu13_rotor_core_tdm.v \
  hardware/rtl/common/prim/surd_multiplier.v &&
vvp build/spu13_tang25k_six_step_probe_tb.vvp
```

**Result:** PASS for the 104-check robotics oracle, the six-step VM-vs-RTL trace,
and the Tang probe wrapper testbench.

**Tang probe build:**

```
bash build_25k_spu13_six_step_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_six_step_probe.fs
```

**Routed footprint:** 13,576 LUT4, 1,518 DFF, 1,024 ALU, 0 BRAM, 0 DSP. Timing
passes at 12 MHz (`u_rotc.clk` max 77.25 MHz).

**UART proof:**

```
KIN:P P:5 E:00
```

**Interpretation:**
- `P:5` means the self-check advanced through the final six-step phase.
- `E:00` means no mismatch was detected across commanded vectors, inverse
  recovery checks, early-closure guards, or the final closure check.
- This proves the period-6 six-step kinematics harness in silicon using the
  already-proven ROTC TDM datapath. It does not prove a full actuator control
  loop, encoder/proprioception feedback, RPLU trajectory correction, or a
  monolithic robotics application image.

### 3.2i Tang 25K Regression Closeout

**Date:** 2026-07-01 NZT

**Scope:** final non-destructive closeout for the Tang Primer 25K as a
subsystem regression board.

**USB/JTAG scan:**

```
openFPGALoader --scan-usb
```

**Result:** `SIPEED 2025030317 USB Debugger` appears as an FTDI2232 bridge.

**Bitstream artifact check:** the following SRAM-loadable `.fs` images are
present under `build/`: southbridge SPI smoke, core-attached southbridge link,
RPLU2 arithmetic, Lucas MAC, ROTC, six-step robotics, SOM/BMU, neuro guard, and
neuro sidecar adapter.

**40-second UART soak:**

```
timeout 40 bash -lc \
  "stty -F /dev/ttyUSB2 115200 cs8 -cstopb -parenb -ixon -ixoff raw -echo && \
   cat /dev/ttyUSB2"
```

**Result:** capture remained on repeated `KIN:P P:5 E:00` lines for the full
timeout window.

**Interpretation:** Tang 25K bring-up is closed for the regression/probe-board
role. Remaining full-concurrency, unmasked SDRAM, PINV, generalized
robotics, and actuator/sensor-loop items are feature or Artix-7 integration
work, not Tang board bring-up blockers.

### 3.2j SPU-4 Sentinel Standalone Silicon Probe

**Date:** 2026-07-08 NZT — **first SPU-4 silicon.**

**Build & flash:**

```
bash build_25k_spu4_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_probe.fs
```

Bitstream SHA-256:
`9599f5e420f46515d99b57d2b256489440341166941be3bc9992b0b827222664`.
Capture path: bare dock, BL616 USB-CDC on pin C3 at 115200 baud, updated
debugger firmware (path re-baselined the same day against the SOM/BMU
golden line, §3.2g).

**UART proof (repeating status line):**

```
SPU4:P A=0000 B=0155 C=0155 D=0155
```

**What executed:** the probe writes a two-instruction program (QROT + HALT)
into the SPU-4 sequencer, pulses `run`, waits for busy to settle, and
self-checks the register file outputs. Inputs B=C=D=0x0100 under circulant
coefficients F=0x0050, G=0x00B5, H=0x0050 rotate to B=C=D=0x0155
(0x50 + 0xB5 + 0x50 = 0x155 — the row-sum fixture). The proven pipeline is
sequencer → decoder → regfile → Euclidean ALU → serial multiplier, executing
from program memory on silicon.

**Interpretation:** first hardware evidence for the SPU-4 Sentinel core as a
program-executing machine (the Euclidean ALU alone was already
formally verified). Not yet covered: sentinel mode (Piranha-gated), boot
master, sovereign bus, cluster bridge.

**Probe rewrite note:** the first flash attempt the same day was mute. The
original probe top — never simulated at top level — had multi-driven
`tx_active`/`tx_byte`/`tx_bit` (message pump and bit engine in separate
always blocks: the UART could never transmit), a latched `run` that
restarted the program forever (busy never settled), and a busy-stable-low
check that could fire before execution began. All three were found in
simulation after the SOM/BMU golden line exonerated the bench path. The
UART engine now reuses the SOM probe's silicon-proven pattern; regression
is `hardware/tests/spu13/spu13_tang25k_spu4_probe_tb.v`, which decodes the
golden line byte-for-byte off `uart_tx`.

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
| `A:E` | `R:00000095` | 149 RPLU v2 records loaded (0x95 = 149) |
| `A:F` | `R:3A0AB5E9` | RPLU v2 checksum verified (varies by table profile) |
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
| RP2350 southbridge (SPI/SD hydration link) | **Verified in Silicon** (June 28, 2026) |
| RP2350 southbridge (USB/HID/sensors/timing) | Not wired, not tested |
| RP2040 visualization/debug bridge | Not wired, not tested |
| PMOD peripheral modules | Not connected, not tested |
| Continuous telemetry loop (>30s) | **Verified for final Tang closeout** — 40-second `six_step_probe` UART soak stayed on `KIN:P P:5 E:00`; other feature probes remain snapshot captures |

### Core Architecture

| Item | Status |
|---|---|
| 13-axis manifold full at-speed compute | Lattice enabled in full probe; sustained operation not yet stress-tested |
| Lucas MAC fast-path zero-drift bit-pattern probe | **Verified in Silicon** on Tang 25K with UART `LUCAS:P`; covers PSCALE/PCHIRAL and 100-period PSCALE zero-drift |
| Lucas PHSLK phase-coherence microprobe | **Verified in Silicon** on Tang 25K with UART `PHSLK:P`; covers coherent, mismatch, and zero-divisor denominator cases plus live dynamic operand loop |
| Lucas PMUL/PINV in silicon | **Verified in Silicon** on Wukong Artix-7 J11 via RP2350 SPI sidecar; PMUL `A=0x0000004200000029`, PINV `A=0x0000000500000201` |
| SPU-4 Sentinel standalone core | **Verified in Silicon** on Tang 25K with UART `SPU4:P A=0000 B=0155 C=0155 D=0155`; QROT program executed from sequencer program memory (§3.2j) |
| Davis Gate / Henosis one-cycle correction pulse | Simulated (verified in `davis_gate_dsp_tb`), not captured on hardware |
| Pell octave rollover at r⁹ boundary | Verified in simulation (`spu_rotor_vault_tb`, `spu_vm_test.py`); hardware probe covers r⁰–r⁷ |
| Inter-SPU node link protocol | `spu_node_link_tb` exists, not probed on hardware |
| SDRAM arbiter under concurrent access | Simulated (`spu_sdram_arbiter_tb`), not stress-tested on hardware |
| ROTC angles 0–5 in silicon | **Verified in Silicon** on Tang 25K with UART `ROTC:P A:5 E:00`; covers canonical trace for all 6 angles plus period closure for angles 1-5 |
| SOM/BMU classifier in silicon | **Verified in Silicon** on Tang 25K with UART `SOM:P T:2 B:6 E:00`; covers 2 weighted BMU oracle scenarios and cluster reduction for the 7-node fixture |
| Six-step robotics kinematics harness | **Verified in Silicon** on Tang 25K with UART `KIN:P P:5 E:00`; covers period-6 angle-1 six-step forward phases, angle-4 inverse recovery per phase, early-closure rejection, and exact phase-5 closure |
| External RP2350 neuro-sidecar opcodes | Tang adapter command path is self-driven silicon-verified; external master transactions through the shared shell are pending |
| QSUB and DELTA RTL FSMs | Implemented and RTL-verified in `spu13_core_qsub_delta_tb`; QSUB also silicon-verified through RP2350 arithmetic tests |

The unproven core-architecture items above are feature/integration gaps, not
Tang board bring-up blockers. The 25K role is closed as a split-probe regression
target; full concurrent integration belongs on an Artix-7 200T / Kintex-class
board.

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
R:00000095 A:E              # RPLU v2: 149 records loaded (0x95 = 149)
R:3A0AB5E9 A:F              # RPLU v2: checksum verified
SDRAM: 0x5D005D33 / 0x0012E92E   # SDRAM endpoints / checksum (full probe only)
```

Without these four RPLU lines and the SPI JEDEC line, no subsequent test
result should be treated as meaningful — the RPLU surface is the hardware
correction baseline and any drift from these values indicates a build, flash,
or timing regression.

---

*CC0 1.0 Universal — public domain*
