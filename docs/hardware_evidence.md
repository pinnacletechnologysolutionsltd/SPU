# Hardware Evidence Ledger

A boring, reproducible record of what passed, what failed, and what remains
unproven.  No speculation — only commands, conditions, and results.

*Last updated: 2026-08-15*

Current regression headline: `python3 run_all_tests.py` reports
`Total PASS: 193`, `Total FAIL: 0` (re-run 2026-08-15). Note that this headline
covers **simulation only** — a board target can be entirely unbuildable while
this number stays green, which is what happened to the Tang SOM sidecar for
four weeks. Board-build coverage is `tools/board_build_check.py`; per-entry
source anchoring for the silicon results below is §3.6. ROTC is gated through angles 0-35
(0-5 silicon-verified; 6-35 testbench/trace-equivalence verified). IROTC uses
the v0.2 phi-plane typestate contract; Tang 25K silicon scope is the §3.2k
engine probe vectors (idx 16, idx 36 main catalog, and fault matrix), with the
full 60 x 2 catalog surface testbench-verified.

---

## 1. Target Hardware

| Property | Value |
|---|---|
| FPGA | Gowin GW5A-LV25MG121NES (Tang Primer 25K) |
| Carrier | Sipeed Tang Primer 25K Dock |
| SDRAM | Winbond W9825G6KH (256 Mbit SDR SDRAM) on 40-pin Dock header |
| Flash | External SPI NOR (J4), 16 MiB |
| FTDI UART | Sipeed onboard, 115200 baud |
| Toolchain | OSS CAD Suite: Yosys 0.63+87 → nextpnr-himbaechel 0.9-99 → gowin_pack → openFPGALoader v1.1.0 |

### Board Condition

| Item | Status | Detail |
|---|---|---|
| SDRAM DQ[10] | **Damaged** | Fault confirmed on the external SDRAM module (Winbond W9825G6KH) itself, not the FPGA or Dock PCB — see AGENTS.md; requires `dq10_masked` build variant. All other SDRAM pins functional. |
| FPGA core | Functional | No known silicon faults |
| SPI flash J4 | Functional | JEDEC ID `D0EF4018` confirmed |
| FTDI UART bridge | Functional | Reliable at 115200 baud |
| PMOD GPIO | Untested | Not yet probed |
| RP2350 southbridge | Functional | SPI & SD hydration link verified in silicon (June 28 and June 30, 2026) |

### Second FPGA

**Stale entry, unconfirmed as of 2026-07-16** — a replacement/second Tang
Primer 25K was reported in transit as of this doc's last real update
(2026-07-11-era); no later entry in this ledger or in AGENTS.md/
CURRENT_STATUS.md confirms arrival or an unmasked SDRAM re-run. Treat this
as an open question to verify, not a live status, until someone confirms
one way or the other.

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

### 3.2e.6 Wukong J11 Standalone SU3 Full-Oracle Proof

**Date:** 2026-08-07 NZT

**Scope:** QMTech Wukong Artix-7 100T standalone `SU3` spin — the dedicated
multiplier instance, not the shared one proven in §3.2e.5. This section exists
because the standalone spin had never been logged here: the 2026-08-03
eight-spin sweep gave it only a liveness-and-dispatch probe
(`00 EA 32 01`, opcode latched, sidecar claimed), and
`SESSION_HANDOVER_2026-08-04.md` carried "SU3's full oracle" as open bench
work. This run closes that item.

**Build/load:**

```bash
usbreset 1209:c0ca && sleep 1
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_SU3.bit
picotool load -f hardware/rp2350/build/rp2350_su3_j11_smoke.uf2
picotool reboot -f
```

No rebuild: the bitstream is the artifact already on disk from 2026-08-03,
SHA-256
`a8b9f661892fd0520afa5e685e40757d3edadcde97c206ba086f1c2018b77d96`.
Smoke firmware `rp2350_su3_j11_smoke.uf2`, SHA-256
`d2dabc0b6d7639de63a42136bf14d68a965a118d08a36d89dab2df5a81ffde91`.

SRAM load completed with `Load SRAM 100%`, `isc_done 1`, `isc_ena 0`,
`init 1`, and `done 1`.

**Link configuration, as reported by the firmware itself:**

```text
pins miso=GP0 cs=GP1 sck=GP2 mosi=GP3 spi_baud=25000
SPI: 25000 Hz requested, 25000 Hz achieved
timing cs_setup=1000us turnaround=1000us crc_hold=1000us recovery=1000us
status_checks=1 word_delay=250us result_wait=1500ms
```

**Proof lines** (run 3 of 13, verbatim; status lines elided):

```text
=== Wukong J11 SU3 smoke run 3 ===
case elem=0 lane=0
  qr valid=1 lane=0 A=0x7FFE271F7FFC43EF B=0x7FFF6B677FFED36F C=0x00021510000446A0 D=0x0000A30000014F30 PASS
case elem=1 lane=1
  qr valid=1 lane=1 A=0x7FFDA5EF7FFB3FBB B=0x7FFF41F77FFE7FF3 C=0x0002AE0400057E04 D=0x0000D3240001B14C PASS
case elem=2 lane=2
  qr valid=1 lane=2 A=0x7FFD24BF7FFA3B87 B=0x7FFF18877FFE2C77 C=0x000346F80006B568 D=0x0001034800021368 PASS
case elem=3 lane=3
  qr valid=1 lane=3 A=0x7FFDC7077FFB830B B=0x7FFF4BFF7FFE9463 C=0x00028DC400053A24 D=0x0000CA2400019E2C PASS
case elem=4 lane=4
  qr valid=1 lane=4 A=0x7FFD2A6B7FFA47FF B=0x7FFF196B7FFE2E9F C=0x00034B480006BAA8 D=0x00010678000218A8 PASS
case elem=5 lane=5
  qr valid=1 lane=5 A=0x7FFC8DCF7FF90CF3 B=0x7FFEE6D77FFDC8DB C=0x000408CC00083B2C D=0x000142CC00029324 PASS
case elem=6 lane=6
  qr valid=1 lane=6 A=0x7FFD66EF7FFAC227 B=0x7FFF2C977FFE5557 C=0x0003067800062DA8 D=0x0000F1480001ED28 PASS
case elem=7 lane=7
  qr valid=1 lane=7 A=0x7FFCAEE77FF95043 B=0x7FFEF0DF7FFDDD4B C=0x0003E88C0007F74C D=0x000139CC00028004 PASS
case elem=8 lane=8
  qr valid=1 lane=8 A=0x7FFBF6DF7FF7DE5F B=0x7FFEB5277FFD653F C=0x0004CAA00009C0F0 D=0x00018250000312E0 PASS
SU3_J11: PASS
```

**Aggregate over one continuous 280-second capture**
(`build/su3_reproof/run_a_defaultclk.log`):

| Quantity | Value |
|---|---|
| Runs started | 13 |
| Runs completed | 12 (the 13th was truncated by the capture window) |
| `SU3_J11: PASS` | 12 |
| `SU3_J11: FAIL` | 0 |
| Per-element `PASS` lines | 120 |
| Any line containing `FAIL` | 0 |
| Distinct QR quadruples across lanes 0-8 | 9 (all elements distinct) |

**Interpretation:**

- The standalone `SU3` spin computes the full nine-element dense 3×3 product
  in `A31[i]` on silicon and commits every element exactly, matching the
  Python oracle's `dense_expected` constants. It is no longer a
  liveness-probe-only spin.
- Twelve consecutive complete runs with zero failures. No intermittency was
  observed at this link configuration, despite the spin's post-route
  `clk_fast` of 45.51 MHz being under the 50 MHz target
  (`SESSION_HANDOVER_2026-08-04.md`).
- **Three corrections to `SU3_COPROCESSOR_PAPER` follow from this run.** Its
  Table 3 hex values are confirmed correct and are now silicon-verified. But
  the paper describes the link as *"100 kHz with 20 us guard delays"*, whereas
  the committed firmware reports **25 kHz with 1000 us guards** — and
  `git log -S` shows those four guard defines have been 1000 us since
  `a71635c`, the commit that introduced the paper, with no build-time override
  anywhere. The paper also maps elements 0/4/8 to lanes 2/5/8, where the
  current firmware uses an identity mapping, element *n* to lane *n*, across
  all nine.
- The paper's Limitations claim about 5 us guards was tested directly; see the
  guard-delay sweep below.

**Guard-delay sweep, 2026-08-07 NZT.** The committed firmware fixes both the
SPI rate and the four guard delays as `#ifndef` defaults, so the paper's
configuration was rebuilt by temporarily overriding them and restoring the
source from git afterwards. Same bitstream throughout
(`a8b9f661892fd052...`), each variant flashed with `picotool` and captured to
`build/su3_reproof/`:

| Configuration | Firmware | Runs | `SU3_J11: PASS` | `FAIL` | `valid=0` |
|---|---|---:|---:|---:|---:|
| 25 kHz / 1000 us | as committed | 12 | 12 | 0 | 0 |
| 100 kHz / 20 us | rebuilt | 27 | 27 | 0 | 0 |
| 100 kHz / 5 us | rebuilt | 44 | 44 | 0 | 0 |

83 complete runs, no failed element, no invalid QR read at any setting.

- **The 5 us intermittency does not reproduce.** The paper's Limitations
  section reports that a 5 us guard probe produced an intermittent invalid QR
  read, concluding that "20 us is the current practical margin". 44 consecutive
  clean runs at 5 us — against the paper's own 13-run capture — do not support
  that margin claim on current silicon.
- **A likely reconciliation, not a refutation.** This bitstream postdates the
  reset root-cause fix (`b48b6f6` pulls `rst_n` up in every XDC that
  constrains it; `0eec6f4` conditions the reset pin and stops cascading BUFG
  into BUFG). An unconditioned reset pad is a credible cause of intermittent
  invalid reads at tight guard timings. The July observation was plausibly
  real and has since been designed out. Testing that would require reloading a
  pre-fix bitstream, which has not been done.
- Recommended paper wording: retain the observation as a dated, historical
  finding against the pre-reset-fix image, and drop the standing claim that
  20 us is a required margin. Do not restate it as a current limitation
  without a fresh reproduction.

### 3.2e.7 Wukong J11 LUCAS 200-Step Zero-Drift Silicon Proof

**Date:** 2026-08-09 NZT.

**Scope:** the 200-step φ-scaling feedback loop on the `LUCAS` spin, with each
step's hardware result fed back as the next step's operand, compared against
exact-integer ground truth and against the same recurrence in IEEE-754.

**Why this entry exists.** `docs/LUCAS_QUICKSTART.md` §5 has shown a transcript
asserting *"silicon: bit-exact against ground truth for all 200 steps"* since
2026-07-17, while the ledger carried no 200-step entry at all — §3.2e.2 covers
the four sidecar ops on 2026-07-03, before the J11 remap. The claim was
therefore **unbacked** when audited on 2026-08-08, in the same shape as the SU3
gap closed on 08-07. This run backs it.

**Build & load:**

```
usbreset 1209:c0ca
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_LUCAS.bit
# isc_done 1  init 1  done 1  ;  console `status` -> raw=5A 00 10 00, ratio_valid=1

.venv/bin/python3 tools/lucas_demo.py --port /dev/serial/by-id/... --steps 200
```

Bitstream `build/spu_a7_100t_LUCAS.bit`, 3,825,919 bytes, SHA-256
`07cb3d7e2c77726120a0cfca96b461cf56d7f256c53c9008d46142d66302c07c` — the
post-reset-fix image built 2026-08-03, unchanged. RP2350 diagnostic console at
125 kHz SPI.

**Result: PASS, 10/10 runs, zero failures.** Raw captures in
`build/lucas_200step/run{1..10}.log`. Representative run:

```text
Act 1: the four Z[phi]/L_521 sidecar ops (silicon-proven vectors)
  PINV    (3+5*phi)^-1           -> 513 +   5 phi   expected 513 +   5 phi   [ok]

Act 2: 200-step phi-scaling loop -- silicon vs exact vs float64
  step      1: silicon =   0 +   1 phi   [exact]   (~1 bits unreduced)
  step     10: silicon =  34 +  55 phi   [exact]   (~6 bits unreduced)
  step     50: silicon =   2 + 520 phi   [exact]   (~34 bits unreduced)
  step     79: float64 diverged -- double now claims 0 + 0 phi, exact is 0 + 1 phi
  step    100: silicon =   5 + 518 phi   [exact]   (~69 bits unreduced)
  step    200: silicon =  34 + 500 phi   [exact]   (~138 bits unreduced)

  silicon: bit-exact against ground truth for all 200 steps.
  float64: lost the exact value at step 79 and never recovers.
PASS: silicon matched exact-integer ground truth on every check.
```

Across the ten runs: 10 × "bit-exact ... for all 200 steps", 10 × float64
divergence at step 79, and the step-200 value `34 + 500 phi` identical in every
run.

**On the positive control.** As with §3.2l.1 it is **internal**: the float64 arm
must diverge. If the double-precision recurrence ever tracked the exact one for
all 200 steps, the comparison would not be discriminating and the silicon
result would carry no information. It diverged at step 79 on all ten runs, at
the point the regression pins.

**Interpretation.** The `Z[φ]/L_521` MAC sustains 200 chained feedback steps on
silicon with no drift, against an operand that grows to ~138 unreduced bits,
while IEEE-754 doubles lose the exact residue at step 79 and never recover.
This is the claim `LUCAS_QUICKSTART.md` has been making; it is now evidenced.

**Limitation.** One bitstream, one board, one session — this establishes the
zero-drift behaviour, not a reliability rate across images or thermal
conditions. The separate software oracle carries the million-step proof
(`software/tests/test_lucas_mac_oracle.py`); this entry covers silicon only.

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

### 3.2f.1 Legacy openXC7 XDC timing limitation

**Date:** 2026-07-28 NZT. This is a tooling constraint, not a new hardware
claim. The repository baseline nextpnr-xilinx 0.8.2-73-gf681eb3a consumes
the Artix XDC's physical pin properties, but does not execute its timing
commands. Two independent negative probes established the boundary:

- adding a deliberately invalid timing command produced no warning or error;
- removing the only `create_clock` command produced an identical timing-graph
  result, including the same 230 unschedulable nodes in the preserved
  RPLU2PADE artifact.

The legacy flow therefore has only nextpnr's single global `--freq` input;
`create_clock`, `create_generated_clock`, false-path, and similar XDC timing
commands are documentation for this backend, not active constraints. Do not
claim that a legacy-openXC7 Fmax report covers clocks described only in XDC,
and do not attempt to repair a legacy timing failure by adding more inert XDC
commands. `docs/toolchain_setup.md` records the operational rule; the bounded
P&R evidence and preserved-artifact caveat are in
`spu_strategy/gtp_contract_nextpnr_clkfast_timing_2026-07-28.md`.

The same investigation separated three failure classes: a real undriven
core-less `boot_ready` endpoint (fixed independently), an artifact-sensitive
230-node timing-scheduler rejection, and a fresh-netlist DSP `CARRYCASCIN`
routing rejection. They are not interchangeable evidence for one cause.

**The 230-node rejection is FIXED — `spu_a7_top.v`, 2026-08-01.** The
`spu_spi_slave` instantiation omitted `tgr_transport_status`, leaving a 128-bit
input undriven; the resulting X/Z-fed decode cone is what nextpnr-xilinx 0.8.2
rejected. Tying it explicitly — `.tgr_transport_status(128'd0)`, TGR transport
being disabled on every `spu_a7_top` spin — takes the build from 230 nodes and
no FASM to **zero nodes, clean route, post-route Fmax 76.08 MHz**. Matched
unmodified control still fails at 230. `spu_spi_slave.v` was not edited and the
full command decode is unchanged. This is the same defect class as the earlier
undriven `core_boot_ready`, and it is the third instance of an omitted input
port on this module producing a misleading toolchain-level symptom.

**The fix's diff landed in commit `c932127`, whose message describes only the
CARRYCASCIN finding.** It was swept in by a `git add -A` during an overlapping
edit and is recorded here because the commit message will not lead anyone to it.

**Board acceptance of that fix FAILED, and the failure is not the toolchain.**
`build/spu_a7_100t_LUCAS_TGRTIE_S307.bit` (SHA-256 `09097c2a...671a358`)
SRAM-loads clean (`isc_done 1 / init 1 / done 1`) and then fails every case of
`rp2350_lucas_j11_smoke` at 2 MHz — the firmware and rate recorded passing on
2026-07-03. That is **identical to the failure of the Himbächel-routed LUCAS
bitstream**, produced by a different backend via a different fix. Two
independent build paths yielding the same silicon failure, while the
0.8.2-built `TENSEGRITYLINK` answers on the same wiring minutes either side,
points at LUCAS's current source rather than any backend.

Ruled out by direct comparison: the SPI pin constraints are byte-identical
between `spu_a7_100t.xdc` and `spu_a7_tensegrity_link.xdc` (J4/G4/B4/B5), as is
the `rst_n` pin (H7, LVCMOS33). The open candidate is that the LUCAS spin's
SPI-to-sidecar-to-QR integration inside `spu_a7_top.v` has no simulation
coverage — the existing LUCAS benches exercise the MAC and the sidecar, not the
`0xB1` chord to `0xAE` QR chain through the board top — so a wiring regression
there since 2026-07-03 would pass the full regression and appear only on the
bench.

**The silicon fault is not LUCAS-specific — it tracks `spu_a7_top` itself
(2026-08-01).** `SU3` was rebuilt from current source with the
`tgr_transport_status` fix: P&R clean (`overused=0 archfail=0`, `clk_fast` max
58.30 MHz), packed to a fresh bitstream, SRAM-loaded with `done 1`. It then
failed `rp2350_su3_j11_smoke` at 25 kHz on every element — `checked write
failed`, status `00 00 00 00`. A different sidecar, a different build, the same
all-zero symptom.

| Board top | Spins tested | Silicon |
|---|---|---|
| `spu_a7_top` | LUCAS (2 builds, 2 backends), SU3 | **all fail** |
| standalone tops | `TENSEGRITYLINK`, `SOMSIDECAR` | **work** |

**`ROBOTICS` answered that question the same day: it fails too.** Rebuilt from
current source (routing `overused=0 archfail=0`, `clk_fast` max 4.12 MHz against
the 781.25 kHz it actually runs at), packed, SRAM-loaded with `done 1`, then
`rp2350_spu_arithmetic_test` returned **`ARITHMETIC_BLAZE: FAIL`, 0/13**, every
`rotc_commit valid=0` and every status `00 00 00 00`.

`ROBOTICS` is `_CORE = 1`, so the fault is **not** confined to the coreless
path. Final tally:

| Board top | Spins tested | `_CORE` | Silicon |
|---|---|---|---|
| `spu_a7_top` | LUCAS (2 builds, 2 backends), SU3 | 0 | **fail** |
| `spu_a7_top` | ROBOTICS | 1 | **fail** |
| standalone tops | `TENSEGRITYLINK`, `SOMSIDECAR` | — | **work** |

Four bitstreams across three spins, both `_CORE` settings, two backends, three
of them freshly built from current source with correct pins — all produce the
same all-zero symptom. Every spin with its own board top works. **The
discriminator is `spu_a7_top` itself**, and no narrower.

What this rules out, each by direct evidence rather than inference:

- **the toolchain** — two backends produce the same failure, and 0.8.2 builds
  working bitstreams from other tops;
- **the pin mapping** — SPI constraints are byte-identical between
  `spu_a7_100t.xdc` and `spu_a7_tensegrity_link.xdc`;
- **BUFG placement** — the failing LUCAS build and the working `TENSEGRITYLINK`
  both land the clock buffer on `BUFGCTRL_X0Y0`;
- **the behavioural RTL wiring** — `spu13_a7_lucas_spi_integration_tb.v`
  (`c69a7d5`) drives real SPI `0xB1`/`0xAE` through an actual
  `spu_a7_top #(.SPIN("LUCAS"))` and passes all four vectors exactly;
- **an undriven sibling of `tgr_transport_status`** — the SU3 build log reports
  zero undriven-net warnings;
- **MISO gating** — `spi_miso` is driven directly by `u_spi` with no
  spin-conditional logic.

The bisection space is **10 commits** to `spu_a7_top.v` since the 2026-07-03
LUCAS J11 proof. The residual candidates are things RTL simulation does not
model: synthesis/implementation divergence, physical clock or reset behaviour
(the sim's BUFG is `assign O = I;`), or the FASM/frames path.

**`CARRYCASCIN` is a backend defect, not an SPU defect — established
2026-08-01 by netlist inspection.** The handover listed it as "the honest next
lead on the production top", which implied a design-side bug to chase. It is
not one, and the RTL needs no change.

No SPU source instantiates `DSP48E1`; `spu13_m31_multiplier.v` uses behavioural
`*` operators and `synth_xilinx` infers the blocks. In every synthesized netlist
on disk, **`CARRYCASCIN` appears only as a port declaration inside the Yosys
blackbox library modules (`DSP48E`, `DSP48E1`, `DSP48E2`) and is connected by
zero instantiated cells**:

| netlist | DSP48E1 cells | cells with `CARRYCASCIN` connected |
|---|---:|---:|
| `RPLU2PADE` (the design that failed routing) | 72 | **0** |
| `FP4EVIDENCE_FI1B0_S17` (routes cleanly) | 72 | **0** |
| `RPLU2CORE` | 0 | 0 |

So the pin is left unconnected by synthesis, in the design that fails *and* in
one that succeeds. The "tied-low `CARRYCASCIN` sink" that nextpnr reports is
therefore **materialised by nextpnr itself** — its packer drives unconnected DSP
inputs from the global constant network, and the router then cannot reach
`CARRYCASCIN`, which on DSP48E1 is a dedicated cascade input with no general
routing path (it is drivable only by the `CARRYCASCOUT` of the DSP directly
below). That is also why the failing site moves with placement
(`DSP48_X0Y71`, `X0Y79`, `X1Y74`) and why some placements route fine.

Yosys does tie *other* unused cascade inputs to constant 0 — in
`FP4EVIDENCE_FI1B0_S17`, `BCIN` is tied on all 72 cells and `ACIN`/`PCIN` on 36
each, with the other 36 genuinely cascaded — and those route without incident.
The defect is specific to how the backend handles the one pin it cannot reach.

Consequences:

- **Do not look for an RTL or synthesis fix.** There is nothing in the source or
  the netlist to correct.
- The A7 legacy backend therefore carries **two independent defects** — this and
  the 230-node timing-graph rejection — and the Himbächel alternative is not
  viable either (it fails gate 3 on silicon and aborts on `TENSEGRITYLINK`; see
  `spu_strategy/bench_findings_a7_build_blocker_2026-08-01.md`).
- The only design-side lever is to stop inferring DSPs for the shared M31
  multiplier, trading area and timing to avoid the pin entirely. That is a real
  cost and should not be spent before the 230-node blocker is understood, since
  it does not address that one.

### 3.2g ROTC 0-5 Silicon Probe

> **The result below stands; the build is no longer reproducible on Tang.**
> `rotc_probe` was retired as a Tang 25K target on 2026-08-16 (§3.6g): it
> synthesises to 33,456 LUT4 today against the 23,040 the device has. The
> footprint recorded in this entry — **13,352 LUT4** — is what it measured when
> it ran, so the spin has grown **2.5×** since, unnoticed, in a design nobody
> rebuilt.
>
> Nothing in this entry is withdrawn. The 2026-06-30 run happened, on hardware,
> and the UART proof below is what the board emitted. What is lost is only the
> ability to rebuild that bitstream on this fabric. ROTC also carries A7
> ROBOTICS silicon coverage, so the capability is not evidenced solely here.
> Treat the build command below as a historical record, not a procedure.

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

### 3.2g.1 SOM/BMU Classifier Silicon Probe

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

### 3.2g.2 SOM BRAM Hydration Silicon Probe

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

### 3.2g.3 Writable SOM Sidecar SPI/UART Silicon Proof

**Date:** 2026-07-16 NZT

**Scope:** renewed Tang Primer 25K board proof of the standalone writable SOM
sidecar after repairing `spu_spi_cfg.v` command acceptance, changing result
readback to a two-byte SPI transaction, latching valid/busy/label status, and
replacing the old ordering shortcut with the exact fixed-schedule
Q(√3) comparator. The RP2350 diagnostic firmware drove SPI0 at 250 kHz on
GP0 MISO, GP1 CS, GP2 SCK, and GP3 MOSI. The Tang J4 mapping was G10 CS,
D10 SCK, B10 MOSI, and C10 MISO with a common ground.

The first loaded image proved all three SPI classifications but exposed a
board-top telemetry mapping error: `uart_tx_telemetry` was constrained to B11,
the internal FPGA/BL616 link, rather than the visible dock CDC UART. The top
now mirrors the result stream onto `uart_tx` at C3 while retaining B11 for
compatibility. The corrected image was rebuilt, SRAM-loaded, and rerun without
changing the SOM or SPI datapath.

**Hydrated weights and classification vectors:**

| Case | Non-zero node weight | Input feature | SPI result | C3 UART byte |
|---|---|---|---|---|
| 0 | node 0, feature 0 = 2 | feature 0 = 2 | label 0, raw `0x80` | `0x00` |
| 1 | node 4, feature 2 = 7 | feature 2 = 7 | label 2, raw `0xA0` | `0x14` |
| 2 | node 6, feature 3 = 4 | feature 3 = 4 | label 3, raw `0xB0` | `0x1E` |

All unspecified node weights and input features were zero. In every case the
RP2350 console reported `done=1 busy=0`; the UART byte independently packed
`{3'b000, label[1:0], best_node[2:0]}` and matched the SPI winner.

**Build and bench commands:**

```
TB_FILTER=spu13_tang25k_som_sidecar_top python3 run_all_tests.py
bash build_25k_spu13_som_sidecar.sh
openFPGALoader -b tangprimer25k \
  build/tang_primer_25k_spu13_som_sidecar.fs
```

The RP2350 console used `somwrite`, `featwrite`, `classify`, and `result`.
C3 telemetry was captured at 115200 8N1 from `/dev/ttyUSB1` as `00 14 1e`.

**Result:** PASS. The filtered regression reported 33 total checks and zero
failures. The rebuilt Tang image uses 12,786/23,040 LUT4 (55%), 1,574 DFF,
1,190 ALU, 8/56 BSRAM, and 0 DSP. Route closed at 77.61 MHz against the
12 MHz target. Packed bitstream SHA-256:
`8c6b6f8e2cc10f0668761ccb4e178b71499af5ef7c204b8cd47728ecd81c8e0b`.

This closes the standalone sidecar's real SPI write/classify/readback path and
the visible UART result path. It does not by itself close the v1 product gate
for a checked-in trained map, versioned rich result frame, adversarial
negative-surd corpus, interrupted hydration handling, or Artix-7 cross-vendor
equivalence.

### 3.2g.4 Reproducible Iris SOM Corpus Silicon Proof

**Date:** 2026-07-17 NZT

**Scope:** one-command board proof using a checked, deterministically trained
seven-node/four-feature Iris SOM map. The artifact includes the training
recipe, prototype coefficients, semantic node labels, four exact feature
weights, dataset checksum, and canonical map checksum. The host regenerates
the map before use, validates all signed 18-bit `Q(sqrt(3))` pairs, uploads
exactly 28 prototypes through the RP2350 console, streams all 150 samples, and
requires every FPGA BMU node to equal the exact software oracle.

**Command:**

```
python3 tools/iris_som_demo.py --hardware
```

**Result:**

```
Oracle confusion matrix
                 predicted
true             set  ver  vir
setosa            50    0    0
versicolor         0   48    2
virginica          0    1   49
accuracy: 147/150 (98.0%)
...
IRIS_SOM_V1: PASS (150/150 FPGA winners bit-exact to oracle)
```

The FPGA confusion matrix was identical. Semantic classification uses the
artifact's node labels on the host; the current compact hardware response still
contains the sidecar's fixed legacy raw-label LUT and is checked only as
independent SPI/UART link telemetry.

**Mismatch found and closed:** the first corpus run matched samples 1-100 but
failed sample 101 (`6300,3300,6000,2500`): FPGA node 2 versus oracle node 1.
The board top described its metric as uniform but packed
`{F3,F2,F1,F0}={1,1,1,2}`. With that unintended feature-0 weight, exact
recalculation selects node 2, reproducing silicon. The corrected top packs
`{1,1,1,1}`. A dedicated RTL regression uses an input whose winner changes
from node 0 to node 2 if feature 0 is doubled, preventing recurrence.

**Artifact identity:**

- map: `software/models/iris_som_v1.json`
- map SHA-256:
  `3373e851c29450e37fca76281f9ea4dbbdf1b94b34cf1b7bd74f6d83fe8eaa15`
- dataset: `software/tests/data/iris.csv`
- dataset SHA-256:
  `6f608b71a7317216319b4d27b4d9bc84e6abd734eda7872b71a458569e2656c0`

**Corrected build:** 12,865/23,040 LUT4 (55%), 1,576 DFF, 1,192 ALU,
8/56 BSRAM, 0 DSP. Route closes at 79.38 MHz against the board's real 50 MHz
clock. Packed bitstream SHA-256:
`946574dc25ad7aada168f9f06af101cd0df747230c0fea0ca9dae0ad5d9e7c3c`.

This closes the reproducible-map and Tang full-corpus portions of SOM v1.
The rich versioned result frame, interrupted/partial hydration contract, and
Artix-7 replay remain open before the complete v1 exit gate.

### 3.2g.5 SOM1 Full Decision-Evidence Silicon Proof

**Date:** 2026-07-17 NZT

**Scope:** renewed Tang Primer 25K silicon proof of the complete versioned
`SOM1` observation-to-decision path. This run used the same checked Iris map
and corpus as §3.2g.4, but replaced the legacy winner-only evidence boundary
with the 52-byte CRC-protected frame and hydrated all seven semantic labels in
addition to the 28 prototype values.

**Bench:** Tang Primer 25K dock plus RP2350/Pico 2. The RP2350 diagnostic
firmware drove SPI0 at 250 kHz with GP0 MISO, GP1 CS#, GP2 SCK, and GP3 MOSI.
Tang J4 was J4-1/G10 CS#, J4-2/D10 SCK, J4-3/B10 MOSI, J4-4/C10 MISO, and
J4-5/common ground. The Tang dock debugger exposed UART on `/dev/ttyUSB1`; the
RP2350 console was `/dev/ttyACM0`.

**Artifact identity:**

- bitstream SHA-256:
  `8753c4924ed6952c049a038a80cbe3bfb8b930e038842631665108af4ad1ff92`
- RP2350 UF2 SHA-256:
  `51a0f26940464d82d11b392d9a363f218e0a343fa33658c296686dc001f63de1`
- canonical map SHA-256 recorded by the artifact:
  `3373e851c29450e37fca76281f9ea4dbbdf1b94b34cf1b7bd74f6d83fe8eaa15`
- checked JSON file SHA-256:
  `1288c03dc7f68a8e165906a30921d9b055d58f6799d4759c484baaaf68f19b8e`
- dataset SHA-256:
  `6f608b71a7317216319b4d27b4d9bc84e6abd734eda7872b71a458569e2656c0`

**Load and run:**

```bash
openFPGALoader -b tangprimer25k \
  build/tang_primer_25k_spu13_som_sidecar.fs
picotool load -f build/rp2350_som/rp2350_spu_diag.uf2
python3 tools/iris_som_demo.py --hardware \
  --console-port /dev/ttyACM0 --uart-port /dev/ttyUSB1
```

**Result:**

```text
Uploading iris-som-v1 to /dev/ttyACM0...
  map upload: 35/35 writes
  corpus: 150/150 exact SOM1 evidence matches
Hardware corpus elapsed: 16.9s
FPGA confusion matrix
                 predicted
true             set  ver  vir
setosa            50    0    0
versicolor         0   48    2
virginica          0    1   49
accuracy: 147/150 (98.0%)
IRIS_SOM_V1: PASS (150/150 FPGA winners bit-exact to oracle)
```

For every sample, the host parser validated magic, version, length, reserved
bytes, and CRC-32. It then required the hardware winner, runner-up, semantic
label, best quadrance, second quadrance, exact confidence gap, ambiguity bit,
valid/busy/runner-up/map-valid flags, and zero error code to match the exact
software oracle. The hydrated map generation was nonzero and stable for the
whole corpus; result generations were consecutive. The legacy compact SPI
result and independent C3 UART byte were also checked on every sample.

The renewed image uses 14,068/23,040 LUT4 (61%), 3,251 DFF (14%), and 8/56
BSRAM (14%), with 0 DSP. Route closes at 75.79 MHz against the real 50 MHz
clock. This closes Tang silicon evidence for the full `SOM1` frame and
map-owned semantic-label path. The 147/150 figure is model accuracy; the
hardware implementation equivalence result is 150/150. Artix-7 full-sidecar
replay and physical sensor acquisition remain separate open evidence items.

### 3.2g.6 Cross-Vendor SOM1 Replay on Wukong Artix-7

**Date:** 2026-07-17 NZT

**Scope:** Wukong Artix-7 100T silicon proof of the complete writable
SOM-SIDECAR used in §3.2g.5, rather than the older fixed-fixture SOMPROBE.
The Artix wrapper instantiates the same SPI receiver, map and semantic-label
storage, fixed-schedule exact BMU, SOM1 encoder, and UART telemetry RTL as the
Tang image. Only board pins and synthesis plumbing differ.

**Bench:** RP2350 SPI0 at 250 kHz, wired to the undamaged Wukong J11 bottom
row: GP1/J11-7/J4 CS#, GP2/J11-8/G4 SCK, GP3/J11-9/B4 MOSI,
GP0/J11-10/B5 MISO, and J11-11/common ground. The RP2350 console was
`/dev/ttyACM6`; E3 UART telemetry was captured through `/dev/ttyUSB0`.
Before the product run, the independent J11 electrical-loopback image passed
all 16 patterns in four consecutive runs at 500 kHz.

**Build and load:**

```bash
bash hardware/boards/artix7/build_a7.sh 100t somsidecar synth
bash hardware/boards/artix7/build_a7.sh 100t somsidecar pnr
PRJXRAY_ROOT=$HOME/toolchains/prjxray \
OPENXC7_PYTHON=$HOME/.local/venvs/prjxray/bin/python \
  bash hardware/boards/artix7/build_a7.sh 100t somsidecar pack
openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_SOMSIDECAR.bit
picotool load -f build/rp2350_som/rp2350_spu_diag.uf2
python3 tools/iris_som_demo.py --hardware \
  --console-port /dev/ttyACM6 --uart-port /dev/ttyUSB0
```

**Artifact identity:**

- Artix bitstream SHA-256:
  `f22a34e78437583efcb6a5a0bafb800c9df6a0803ee8614e8184b170cf5bf180`
- RP2350 UF2 SHA-256:
  `51a0f26940464d82d11b392d9a363f218e0a343fa33658c296686dc001f63de1`
- map and dataset identities are unchanged from §3.2g.5.

**Result:** the 35-record map/label upload completed, followed by 150/150
exact SOM1 evidence matches in 16.3 seconds. The FPGA confusion matrix was
`[[50,0,0],[0,48,2],[0,1,49]]`, or 147/150 semantic accuracy, and the final
line was:

```text
IRIS_SOM_V1: PASS (150/150 FPGA winners bit-exact to oracle)
```

Every frame passed the same magic/version/length/reserved/CRC checks and exact
winner, runner-up, label, quadrance, gap, ambiguity, status, map-generation,
and result-generation comparisons as the Tang corpus. The independent UART
byte and compact SPI result also agreed for every sample. Because both board
runs match the same complete exact oracle record, this closes the cross-vendor
replay-equivalence claim for the SOM1 ABI.

The routed Artix image uses 8,013/126,800 SLICE_LUTX (6%), 3,098/126,800
SLICE_FFX (2%), 44/240 DSP48E1 (18%), and 4/270 RAMB18E1 (1%). Route closes
at 65.63 MHz against the 50 MHz constraint. During porting, a legacy
`tx_count % CLKS_PER_BIT` UART expression was found to synthesize as a 213 ns
divider chain; replacing it with an equivalent baud down-counter preserved
the 434-cycle bit interval and removed the non-product timing path.

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

> **SUPERSEDED — and the bench re-run is DONE. See §3.2j.2 (2026-08-16) for
> the current SPU-4 silicon result, which re-anchors both T7.4 and the width
> fix at 10/10 loads with a 4/4 positive control. This entry's measurements
> stay as the record of what ran on 2026-07-08 and must not be edited.**
>
> **SUPERSEDED 2026-08-15 — needed a bench re-run before it could be cited.**
> T7.4 exported `dissonance[7:0]` from `spu4_standalone_top` and extended this
> probe's UART line from 36 to 41 characters to carry it. The bitstream below
> and its golden line both describe the pre-T7.4 design. `R=FF` is the correct
> settled value — the QROT fixture's residual is 0x3FF and saturates — and the
> field is `R`, not `E`, because `E=` already means an error code on other
> probes. The hash and line recorded in this
> entry are left untouched because they record what actually ran on the board
> on 2026-07-08. Re-run the probe, observe the 41-char line, then write a new
> entry — do not edit this one's measurements.
> Decision and cost table: `docs/SPU4_FAULT_REPORTING_CONTRACT.md`.
>
> **Baseline moved a second time, 2026-08-16.** The `dissonance` residual
> width was fixed (17 → 19 bits, §3.2j.1 below) and the duplicated expression
> extracted into `spu4_dissonance.v`. The tree now builds
> `0061b02f17a0f945110ad0aed269556568eb1412875268a3679baeb1cb56d67c`
> at **982 LUT4 / 462 ALU / 336 DFF, 161.11 MHz** (CORRECTED 2026-08-17: was
> recorded as 160.38 MHz, nextpnr's post-placement estimate; 161.11 MHz is the
> final post-route figure), reproduced 2×
> (was `cbd6f83a…` at 979 / 460 / 336 under T7.4 alone).
> **The golden line is unchanged** — the QROT fixture's 0x3FF saturates under
> both widths — so the pending bench re-run validates both changes at once.
> The two moves were batched deliberately for that reason: doing the width fix
> after the bench session would have cost a second one.

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

#### 3.2j.1 The `dissonance` residual read laminar under maximum fault (fixed 2026-08-16)

Found while closing T7.4 on 2026-08-15, documented then, fixed now. **This is
a simulation and synthesis result. No board was involved**; the 2026-07-08
silicon in §3.2j ran the defective version.

`dissonance[7:0] = min(|A+B+C+D|, 255)` summed four sign-extended 16-bit
addends in a **17-bit** context. Four 16-bit signed values span ±131072, so
the sum wrapped modulo 131072 *before* the saturation test could see it:

| Vector | True residual | Old reading | Correct |
|---|---|---|---|
| `A=B=C=D=0x8000` | **−131072** (maximum reachable) | **`0x00` — perfectly laminar** | `0xFF` |
| `A=B=C=D=0x7FFF` | 131068 | `0x04` — near-laminar | `0xFF` |

A saturating fault signal that reads *clean* under the largest possible fault
is worse than no signal, because it is trusted. The failure is silent and in
the unsafe direction.

**Fix.** Width raised to 19 bits. 18 bits *hold* the ±131072 range, but the
absolute-value step negates, and negating −131072 in 18-bit signed wraps back
to itself — so 19 is the correct width, not 18.

**The expression was also deduplicated.** It existed as a copied block in both
`spu4_core.v` and `spu4_standalone_top.v`, kept in step only by a comment
saying they must not diverge. They had already diverged once (T7.4 found the
wrapper had no `dissonance` port at all), and this bug then had to be fixed in
two places. It is now one module, `hardware/rtl/core/spu4/spu4_dissonance.v`,
instantiated by both — the constraint is structural rather than a comment.

**Coverage:** `hardware/tests/spu4/spu4_dissonance_width_tb.v`, 2016 checks
against an independent 32-bit reference model. Verified non-vacuous by
replaying it against a reconstruction of the old 17-bit expression, which
fails on exactly the two vectors above.

**A note on what caught it.** That replay also passed **all 2000 random
vectors** in the same file. `$random` essentially never produces four
same-sign extremes, which is the only region where the wrap is observable.
The targeted corner vectors found this; the randomised sweep would not have,
at any iteration count worth running.

**Cost:** +3 LUT4, +2 ALU, 0 DFF (979 → 982, 460 → 462), Fmax 161.11 MHz
(CORRECTED 2026-08-17: was recorded as 160.38 MHz, nextpnr's post-placement
estimate; 161.11 MHz is the final post-route figure).
Regression 193 → 194 PASS.

#### 3.2j.2 SPU-4 probe re-anchored — T7.4 and the width fix, in silicon

**Date:** 2026-08-16 NZT. Supersedes §3.2j as the current SPU-4 silicon result.
§3.2j's own measurements are untouched; they record what ran on 2026-07-08.

**Scope:** re-anchors *two* changes in one session, which is why the width fix
was taken before this run rather than after — T7.4's `dissonance` export
(§3.2j) and the 19-bit residual widening (§3.2j.1). The golden line is
unchanged by the second, so one bench run validates both.

**Procedure:** `docs/BENCH_PROCEDURE_2026-08-3_2j_SPU4_REANCHOR.md`,
pre-registered before the rig was energised.

**Build & load:**

```bash
bash build_25k_spu4_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_probe.fs
```

Bitstream SHA-256:
`0061b02f17a0f945110ad0aed269556568eb1412875268a3679baeb1cb56d67c`
(982 LUT4 / 462 ALU / 336 DFF, 161.11 MHz against 12 MHz — CORRECTED
2026-08-17, was recorded as 160.38 MHz, nextpnr's post-placement estimate;
161.11 MHz is the final post-route figure; reproduced 3× before
the session and hash-verified again at the bench).

**UART proof — 10/10 loads, 250 lines, every line identical:**

```
SPU4:P A=0000 B=0155 C=0155 D=0155 R=FF
```

41 bytes including CRLF, verified with `cat -A`. The bitstream was reloaded
between every run, so what is sampled is the configure-and-start path, not one
configuration observed ten times.

**Positive control — 4/4 loads, the previous bitstream:**

```
SPU4:P A=0000 B=0155 C=0155 D=0155
```

36 bytes, **no `R=` field**. `9599f5e4…22664`, rebuilt from commit `511f3f3`
and reproducing the 2026-07-08 hash bit-exactly. Run 3× before the trials and
**once more after them**, so the capture path is shown to discriminate the two
images at both ends of the session. This is the control that matters here: the
risk was never the RTL but "did the new image actually load", and a control
that merely proves the bench works cannot distinguish that.

**`R=FF` is correct, not a fault.** The QROT fixture settles at A=0,
B=C=D=0x155, a residual of 0x3FF that saturates. `R=00` would be the
suspicious reading — that is also what a stripped or stuck-at-zero port emits.

**Capture path differs from §3.2j and is recorded as such.** July used the
bare dock's BL616 USB-CDC. This session used a **Sipeed USB Debugger
(FTDI FT2232, `0403:6010`)**, JTAG on interface 0 and the C3 UART on
interface 1 (`/dev/serial/by-id/usb-SIPEED_USB_Debugger_2025030317-if01-port0`),
115200 8N1. No `ttyACM` device was present. `blinky_uart` was loaded first as a
bench-path sanity image and returned `BLINK`, which is what established that
interface 1 carries C3 before any result was interpreted.

**Method note — a stale-buffer artifact, and why all ten runs were repeated.**
The first attempt's run 01 mixed a truncated control line with the golden line,
because the serial buffer still held bytes from the previously-loaded image.
Runs 02–10 looked clean only because they followed the *same* image, so the
stale bytes were indistinguishable from fresh ones. That is a capture artifact,
not a device failure — the same one `tools/bench_metrics/power_log.py` already
flushes for. Rather than discard one run, the capture method was corrected to
drain the buffer after loading and **all ten trials were re-run**. **Raw captures are committed** at
`docs/bench_captures/2026-08-16-spu4-reanchor/` — ten trial logs, four
control logs, and the superseded first attempt under
`attempt1_stale_buffer/`. They are in the repository rather than in the
gitignored `build/` tree specifically so they survive a clean and remain
auditable later.

**What this establishes.** The SPU-4 standalone probe executes the documented
QROT path on Tang 25K silicon and reports the saturating Quadray residual on a
pin, at the current HEAD bitstream. T7.4's product-wording claim and §3.2j.1's
width fix are both now silicon-backed rather than simulation-backed.

**What it does not establish.** One board, one session — a behaviour, not a
reliability rate. It says nothing about other fabrics, and nothing about the
161.11 MHz figure (CORRECTED 2026-08-17, was 160.38 MHz — see §3.2j.2's cost
line), which is a P&R result and not exercised by a 12 MHz run. It
also gives no evidence for `spu4_customer_wrapper`, which is a different
bitstream (§4a of `docs/SPU4_ABI.md`).

#### 3.2j.3 SPU-4 ABI v1.0 in silicon — the bounded-latency gate closed on hardware

**Date:** 2026-08-16 NZT, same bench session as §3.2j.2, run as a separate
block after that result was sealed.

**Scope:** first silicon for `spu4_customer_wrapper`, the SPU-4 ABI v1.0
contract layer. Until this run the ABI had been verified only in simulation.

**Build & load:**

```bash
bash build_25k_spu4_abi_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_abi_probe.fs
```

Bitstream SHA-256:
`1e70739d68477869c47e673407ebd599c350ce058ac1c1ba2b7a77edd647a81a`
(1,044 LUT4 / 500 ALU / 381 DFF, 211.60 MHz against 12 MHz — CORRECTED
2026-08-17, was recorded as 160.26 MHz, nextpnr's post-placement estimate;
211.60 MHz is the final post-route figure, confirmed by rebuilding this
commit; reproduced 2×).

**UART proof — 10/10 loads, 250 complete lines, every one identical:**

```
ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7
```

44 bytes including CRLF, verified with `cat -A`. Reloaded between every run.

**`L=0B7` is the measured latency: 183 clocks.** This is the result that
matters commercially. `docs/SPU4_PRODUCT_CLAIMS.md` carried bounded latency as
an **OPEN** product gate, and simulation had measured 180–183 over 124
operations against a contract bound of 200. Hardware returns **183** — inside
the bound and at the top of the simulated range. The gate is now closed with
silicon rather than a simulation figure.

**`S=0A`** decodes as `done` and `saturated` set, `busy`, `henosis` and
`start_ignored` clear. `start_ignored` clear is the useful one: it confirms the
probe drove the handshake correctly, so the latency figure describes one
accepted operation rather than a contended one. `henosis` clear is an
observation, not a prediction — the testbench deliberately reports that bit
rather than asserting a guess.

**Capture artifact, stated because it looks like a failure and is not.** Seven
of the ten captures contain a **truncated final line** — `timeout` cutting the
stream mid-transmission, e.g. `ABI:P B=` on run 09. Every *complete* line in
every run is the golden line, and dropping the trailing fragment gives 10/10.
An initial hypothesis that the fragment was the *leading* line was tested
against the data and refuted; it is the trailing one. §3.2j.2's captures were
checked for the same artifact and have none (0/10), so that entry is
unaffected.

**What this establishes.** The frozen ABI executes on Tang 25K silicon through
its real `start`/`busy`/`done` handshake, returns the reference QROT result,
reports the saturating residual, and meets its published latency bound.

**What it does not.** One board, one session — a behaviour, not a reliability
rate. It exercises one operand fixture, so it does not probe the ABI's full
input range, and it says nothing about the 211.60 MHz P&R figure (CORRECTED
2026-08-17, was 160.26 MHz — see the bitstream note above), which a
12 MHz run cannot test.

#### 3.2j.4 Three further probes brought up, one genuinely mute

Same session, exploratory block. None of these had ever been run on a board.

| Probe | Result | Line |
|---|---|---|
| `satellite_aggregator_probe` | **PASS** | `SAGG:P W:2 I:9 E:00` |
| `whisper_v1_probe` | **PASS** | `WHSP:P F:1 E:00  PASS` |
| `rotc_tagged_probe` | **MUTE** | no output |

`rotc_tagged_probe`'s silence is a **genuine finding, not a bench fault**. It
was checked immediately against `blinky_uart`, which returned 14 lines on the
same path seconds later. The spin builds, reproduces bit-exactly
(`5fa8b4b8…`), and closes timing at 120.03 MHz against 12 MHz (CORRECTED
2026-08-17: the 120–135 MHz range previously recorded here was nextpnr's
final post-route figure and its post-placement estimate, unlabeled; 120.03 MHz
is the final one) — it simply emits nothing. That is a real bring-up item: it has been recorded as "built,
awaiting board run" since 2026-07-09, and the board run now says the image is
silent.

Single runs, exploratory. `SAGG` and `WHSP` need N≥10 with a control before
either is cited as evidence.

#### 3.2j.5 Bench operational finding — the FTDI UART channel wedges

**The Sipeed USB Debugger's channel B stops delivering UART after repeated
MPSSE use on channel A**, which is what a long sequence of `openFPGALoader`
invocations does. Observed after roughly twenty loads in one session:
`blinky_uart`, working minutes earlier, went silent; JTAG stayed healthy
(`idcode 0x1281b`, loads reporting DONE), the device stayed enumerated, and no
process held the port.

**Unplugging and replugging the USB cable restores it.** Confirmed: both
interfaces re-enumerated and `blinky_uart` returned `BLINK` immediately.

**Operational rules this earns:**

- **Re-enumerate after a long load sequence.** Do not interpret silence as an
  RTL result until this is ruled out.
- **Keep a known-good image as the discriminator.** `blinky_uart` at 140 LUT4
  is the cheapest one. Four probes read as failures in this session before
  `blinky` showed the path itself was dead; the same check later proved
  `rotc_tagged_probe`'s silence was real. The check is what separates the two
  cases, and without it both look identical.
- A replug power-cycles the board, so SRAM configuration is lost — reload
  before capturing.

#### 3.2j.6 SPU-4 ABI v1.1 `id` port in silicon — first read-back of the identity word

**Date:** 2026-08-17 NZT.

**Scope:** first silicon for `id`, the read-only identity port appended to
`spu4_customer_wrapper` in ABI v1.1 (`docs/SPU4_ABI.md` §2a). `id` was wired
into `spu13_tang25k_spu4_abi_probe`'s UART line as a new `I=` field for this
run; the probe's golden line previously ended at `L=`.

**Build & load:**

```bash
bash build_25k_spu4_abi_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_abi_probe.fs
```

Bitstream SHA-256:
`23ba4a3f5326d0943f32c63a011dc5f6ee6c32aba7608c40bb7f73d03dad8365`,
built from commit `daabf25` — rebuilt after that commit and reproduces the
flashed hash bit-exactly.

**Post-P&R resource cost, measured 2026-08-17** (closes the open item left by
§3.2j.3, which did not have `id` yet): **1,066 LUT4 / 23,040 = 4.6%, 500 ALU,
381 DFF.** Rebuilding §3.2j.3's pre-`id` commit for comparison gives **1,044
LUT4, 500 ALU, 381 DFF** — so `id` costs **+22 LUT4, and zero new ALU/DFF**,
consistent with `id` being a synthesis-time constant net rather than clocked
state. Full table and the reasoning behind the LUT4 attribution:
`docs/SPU4_ABI.md` §5.1.

**Fmax finding, corrected 2026-08-17:** getting the comparison above required
rebuilding §3.2j.3's exact commit, which surfaced that nextpnr prints *two*
`Max frequency` lines per run — a post-placement estimate, then (after a full
`Critical path report`) the final post-route figure — and **this repo had
been citing the estimate, not the final number, for §3.2j.3's Fmax.** The
same rebuild's actual final post-route Fmax was **211.60 MHz**, not the
previously recorded `160.26 MHz`. This build's own two figures are 183.52 MHz
(estimate) / **142.25 MHz (final, correctly the one cited above and in
SPU4_ABI.md)**. A same-day repo-wide audit (see the nextpnr Fmax
estimate-vs-final finding) found and fixed four more instances of the same
mistake; §3.2j.3, this document's other citations, `SPU4_ABI.md`, and
`board_build_manifest.json` are all corrected. Full detail:
`docs/SPU4_ABI.md` §5.1.

**UART proof — 10/10 loads, one capture per load, all identical:**

```
ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7 I=1110
```

Raw log: `docs/bench_captures/2026-08-17-spu4-abi-v1.1-id/raw_runs.log`.
Captured via `/dev/ttyUSB1` at 115200 8N1, reloaded between every run.

**`I=1110` matches `docs/SPU4_ABI.md` §2a exactly**: `ABI_MAJOR=1`,
`ABI_MINOR=1`, `WRAPPER_ID=1` (QROT-only Euclidean ALU wrapper), reserved
nibble `0`. `B`/`C`/`D`/`R`/`S`/`L` are unchanged from §3.2j.3 and confirm
this run is the same wrapper behaviour with one port added, not a different
build.

**What this establishes.** `id` is not just a simulated constant — the
elaborated netlist on real Tang 25K silicon reads back the exact bitfield the
doc promises, across 10 independent SRAM loads. This is the discovery
mechanism itself proven end-to-end: a party holding only this bitstream could
read `id` off the UART (or, on an ASIC, off the equivalent pins) and learn
which ABI version and wrapper variant they have, without trusting paperwork.

**What it does not.** One board, one session, one fixture — same scope
caveat as §3.2j.3. It does not exercise a second `WRAPPER_ID` value (none
exists yet) or prove anything about a future custom-ASIC spin; it proves the
mechanism works for the one variant that exists today.

#### 3.2j.7 SPU-4 edge-node SOM in silicon — step 4 of the edge-node programme closed

**Date:** 2026-08-17 NZT.

**Scope:** first silicon for `spu4_som_edge_wrapper` and the fixed
`spu4_som_edge.v` (see the same-day quadrance-sum generalization fix,
commit `efc7466`) — the SPU-4 edge SOM product, a different sub-product
from the ABI/Euclidean-ALU wrapper covered by the rest of §3.2j. Closes
step 4 (board probe → silicon) of the edge-node programme; step 3 (the
oracle-checked full-chain testbench) landed simulation-only earlier the
same day.

**Build & load:**

```bash
bash build_25k_spu4_som_edge_probe.sh
python3 tools/gen_spu4_som_boot_image.py --profile oracle_fixture \
    --output tools/build/spu4_som_boot_image.bin
tools/rp2040_flash_pmod.py --port <tty> write tools/build/spu4_som_boot_image.bin \
    --offset 0x120000
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_som_edge_probe.fs
```

Bitstream SHA-256:
`4cd15ae59f2b132c2608679ba6ad22ed39807e3777217572ecec14e60e242734`.

**Post-P&R resource cost, measured 2026-08-17:** 14,653 LUT4 / 23,040 =
63%, 1,072 ALU / 17,280 = 6%, 1,069 DFF / 23,040 = 4%. Fmax: nextpnr
printed the usual two `Max frequency` lines (35.67 MHz post-placement
estimate, then the final post-route figure) — the final figure is
**42.15 MHz**, comfortably clearing the 12 MHz `--freq` target.

**UART proof — stable, repeating, re-verified after reload:**

```
SOM:P N=1 Q=00001900 S=06 L=007 I=1020
```

`N=1`/`Q=00001900` (6400) is the oracle-computed answer for the fixture's
"far from all nodes, mixed sign" query
(`software/lib/spu4_som_edge_oracle.py`) — deliberately the one query
whose correct verdict depends on feature index 3, i.e. the exact
regression case for the dropped-feature bug fixed the same day. `S=06`
decodes to hydrated=1, done=1, busy=0, start_ignored=0. `L=007` matches
the simulation testbench's latency exactly. `I=1020` matches
`ABI_MAJOR=1 ABI_MINOR=0 WRAPPER_ID=2` per `docs/SPU4_ABI.md` §2a.

**What this establishes.** The full product chain — external SPI flash →
`spu4_som_flash_loader` → `spu4_som_edge` → `spu4_som_edge_wrapper`'s
handshake → UART report — works end to end on real silicon, on the one
query that a synthesis-vs-simulation mismatch in that day's RTL fix could
plausibly have broken. Bit-exact agreement with the software oracle, not
just "a plausible-looking number."

**What it does not.** One board, one session, one fixture, same caveat
class as the rest of §3.2j. Real (non-synthetic) trained weights still
don't exist — this proves the mechanism, not a trained classifier.

**Operational findings from this session (worth more than the RTL result
itself, time-wise):**

- **A stuck Sipeed dock debugger looks identical to a bench result you can't
  trust, not to an obvious hardware fault.** Symptom: the UART line reads
  *something* — a real, well-formed, previously-golden line from a
  completely different bitstream, sometimes repeating, sometimes a single
  non-repeating leftover byte sequence — while the board is actually frozen
  (clock not running). The tell is the LED: a design's heartbeat LED
  (`led[0]` in both SOM probes here) should be visibly blinking; steady/frozen
  means the board is stuck regardless of what the UART appears to say.
  **Check the LED before trusting any UART read that looks "wrong but
  plausible."**
- **Recovery: short the Tang 25K Dock's `3V3`/`TDO` test points** (bottom
  side, upper-left corner) while powering on / connecting the debug USB
  cable, wait for it to enumerate as a Bouffalo `/dev/ttyACMx` CDC device
  (vendor ID `349b`, confirming it's genuinely the BL616 in DFU mode, not
  guessed), release the short, then power-cycle normally. Source: Sipeed's
  own wiki (`wiki.sipeed.com/hardware/en/tang/common-doc/update_debugger.html`),
  not the generic/unverified pin names a first search pass turned up.
- **`openFPGALoader -b tangprimer25k <file>` reports success (`Load SRAM
  100%`, `Done DONE`) even when the load does not take live effect until
  the next power cycle.** Observed repeatedly and consistently this
  session — reading immediately after a "successful" load kept showing the
  *previous* bitstream's output, and only a subsequent power cycle brought
  up the newly-loaded design. Budget a power cycle into every load-and-check
  cycle on this board rather than trusting the load command's own success
  report.
- **A dedicated debug probe that bypasses the product wrapper and reads raw
  hydrated weight registers directly (`spu13_tang25k_spu4_som_edge_debug_probe.v`,
  kept in-tree) is what actually separated "RTL bug" from "the J4 flash
  chip was never wired to the Tang board at all, only to the RP2040
  programmer"** — an all-`FFFF` readback (the floating-MISO pull-up
  pattern, per `tang_primer_25k.cst`'s `PULL_MODE=UP` on that pin) pointed
  straight at the physical wiring rather than the quadrance-sum fix.

#### 3.2j.8 First trained-weight silicon result — interactive probe + fixed-probe reconfirmation

**Date:** 2026-08-19 NZT.

**Scope:** first time `spu4_som_edge_wrapper` classified against genuinely
*trained* weights (`tools/spu4_som_edge_trainer.py` output, not a synthetic
profile) on real silicon, via the interactive probe
(`spu13_tang25k_spu4_som_edge_interactive_probe.v`, §2 of the 2026-08-18
handover — this is that probe's first board session). Immediately followed
by a full swap back to `oracle_fixture` weights and the fixed probe to
reconfirm §3.2j.7 still holds on the same physical wiring after a flash
chip reseat.

**Build & load (interactive probe, trained weights):**

```bash
python3 tools/spu4_som_edge_trainer.py --csv software/tests/data/synthetic_current_v1.csv \
    --output tools/build/spu4_som_edge_synthetic_weights.json \
    --report tools/build/spu4_som_edge_synthetic_report.json
python3 tools/gen_spu4_som_boot_image.py --weights tools/build/spu4_som_edge_synthetic_weights.json \
    --output tools/build/spu4_som_edge_synthetic_boot_image.bin
tools/rp2040_flash_pmod.py --port /dev/ttyACM0 write tools/build/spu4_som_edge_synthetic_boot_image.bin \
    --offset 0x120000
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_som_edge_interactive_probe.fs
python3 tools/spu4_som_edge_demo.py --port /dev/ttyUSB1 \
    --weights tools/build/spu4_som_edge_synthetic_weights.json
```

Bitstream SHA-256:
`03ab3d3fb0315710b4101f0b1f308cb6d0d72ee5c8d13ee87f8de304c63aa384`.
nextpnr final Fmax **44.32 MHz** (the second of the two printed "Max
frequency" lines — see §3.6/nextpnr-fmax memory), file size 5.9 MB, from
the 2026-08-18 build session; utilization not re-measured this session.

**Demo output — 5/5, all matched the independent oracle:**

```
exact match: node 0              HW: node=0 Q=0      ORACLE: node=0 Q=0      [OK]
exact match: node 1              HW: node=1 Q=0      ORACLE: node=1 Q=0      [OK]
exact match: node 2              HW: node=2 Q=0      ORACLE: node=2 Q=0      [OK]
exact match: node 3              HW: node=3 Q=0      ORACLE: node=3 Q=0      [OK]
midpoint of node 0 and node 1    HW: node=3 Q=82056  ORACLE: node=3 Q=82056  [OK]
PASS: every hardware classification matched the software oracle exactly.
```

`tools/spu4_som_edge_demo.py` previously only supported the three synthetic
profiles (`oracle_fixture`/`demo`/`zero`) via `--profile`; it did not know
how to compare against arbitrary trained weights, so this session added a
`--weights` flag (reusing `gen_spu4_som_boot_image.load_weights`, the same
loader the boot-image generator already trusted) rather than writing a
separate one-off script.

**Then the swap-back — flash chip unseated, wired to the RP2040 PMOD,
reflashed `oracle_fixture`, reseated in `J4`, fixed-probe bitstream
reloaded:**

```bash
python3 tools/gen_spu4_som_boot_image.py --profile oracle_fixture \
    --output tools/build/spu4_som_edge_oracle_fixture_boot_image.bin
tools/rp2040_flash_pmod.py --port /dev/ttyACM0 write tools/build/spu4_som_edge_oracle_fixture_boot_image.bin \
    --offset 0x120000
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_som_edge_probe.fs
python3 tools/spu4_som_edge_smoketest.py --port /dev/ttyUSB1
```

Fixed-probe bitstream SHA-256 (re-verified, unchanged from §3.2j.7):
`4cd15ae59f2b132c2608679ba6ad22ed39807e3777217572ecec14e60e242734`.

**Smoke-test output:**

```
SOM:P N=1 Q=00001900 S=06 L=007 I=1020
PASS: real silicon classified the fixed fixture correctly.
```

Bit-exact match to §3.2j.7's original result, on the same board after the
flash chip was physically removed and reseated — a genuine reseat/wiring
check, not just a re-run of the same session.

**Environment note:** this machine's system Python (3.14) has no
`pyserial` and no pip/venv; both serial-dependent scripts were run via
`/opt/oss-cad-suite/py3bin/python3` (the OSS CAD Suite's bundled
Python 3.11, which does have `pyserial`) instead. `tools/rp2040_flash_pmod.py`
worked under the system Python unmodified — worth checking why if this
becomes a recurring friction point.

**What this establishes.** The full chain — trainer output → boot-image
generator → external SPI flash → `spu4_som_flash_loader` →
`spu4_som_edge` → wrapper handshake → UART — is correct end to end on real
silicon using weights that came from actual training, not a hand-picked
constant, for the first time. The fixed-probe reconfirmation additionally
proves the physical flash-reseat procedure itself doesn't disturb a known-
good result.

**What it does not.** Training data is still the synthetic fixture
(`synthetic_current_v1.csv`), not real INA226 captures — Track A (parts
ordered 2026-08-18) is still the gate for a result that says anything about
a real bearing/motor. Also: §3.2j.7 flagged that `openFPGALoader` can
report success while a load doesn't take live effect until a power cycle;
this session did not independently re-verify the LED-blink check for
either load, though both results were internally consistent with the
weights actually flashed (a stale load would have produced the *other*
probe's answer instead of a clean match), which is reasonably strong
circumstantial evidence against it happening here, not a substitute for
checking directly next time.

### 3.2k IROTC Icosahedral Rotation Engine Silicon Probe

**Date:** 2026-07-10 NZT — **first icosahedral (A₅) rotation silicon.**

**Build & flash:**

```
bash build_25k_spu13_irotc_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_irotc_probe.fs
```

Bitstream SHA-256:
`4aedc90143e4e9c5bceb5bf3c25046a737b4b70d10a5e9b97126db248619bb24`.
Capture path: bare dock, BL616 USB-CDC on pin C3 at 115200 baud (the
§3.2g/§3.2j re-baselined path).

**UART proof (repeating status line):**

```
IROTC:P E=00
```

**What executed:** the self-checking FSM drives the term-serial IROTC
engine (`spu13_irotc_engine.v`, fixed 13-cycle slot, signed exact Z[φ],
0 DSP) through five phases in fabric: (1) catalog index 16 — period-3
rotation — on a doubled Z[φ] input, both output pairs bit-checked against
oracle-derived constants; (2) index 36 — period-5, a genuinely
icosahedral rotation whose matrix requires φ-arithmetic (no A₄/octahedral
alias exists); (3-5) the dispatch-fault matrix: BADIDX (idx 60),
UNTAGGED, and CATMIX (conjugate-catalog request on MAIN-locked data),
each required to raise the exact fault code and nothing else. The
verdict line repeats every 0.2 s (§3.2g pattern). Golden constants were
independently re-derived from the exact-Fraction oracle before commit;
the engine's 540-entry code ROM is pinned to the derivation by oracle
check 23 on every suite run.

**Interpretation:** first hardware evidence for the icosahedral catalog
(ROTC paper §11 trajectory A₄→S₄→A₅) and for the theorem-licensed
typestate guard (IROTC_SPEC.md v0.2): the doubling theorem's `>>>1`
executed unguarded in fabric on licensed data, and all three dispatch
refusals fired on unlicensed data. Silicon scope is the probe's vector
set (indices 16 and 36, main catalog, plus the three faults); the full
60-index × both-catalog surface is testbench-verified
(`spu13_irotc_engine_tb.v`, 120 oracle golden cases, 12-clock latency
pinned per case). Not yet in silicon at this probe: conjugate-catalog
rotations, LOAD2X/SCALE2 as instructions, tag storage in
`spu13_core.v`, sidecar/SPI dispatch — closed by §3.2k.1 below.

### 3.2k.1 IROTC SPI Core-Integration + Conjugate-Catalog Silicon Proof

**Date:** 2026-07-12 — closes every gap §3.2k left open: LOAD2X/IROTC/
SCALE2 as real instructions dispatched over the SPI link, the 13×2-bit
tag file, and — the headline — the **conjugate catalog** (dual
icosahedron) executing in fabric for the first time.

**Build & flash:**

```
bash build_25k_spu13_irotc_spi.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_irotc_spi.fs
```

Bitstream SHA-256:
`ca54c1dcdd1b358f786dab9a1094192c94402e86800bcd5cb6301ca0844c072a`.
Resources: BSRAM 1/56, LUT4 49%, worst Fmax 47.2 MHz @ 12 MHz
constraint (engine ROM converted case-mux→BSRAM this session,
73acd91, to close the routing livelock that had blocked this bitstream
— 6.9k→3.0k cells). SRAM-loaded, not flashed (`openFPGALoader` without
`-f`), so the RPLU2 boot tables at flash 0x110000 stay untouched.
`boot_done` is tied `1'b1` in this spin (no flash boot master, no
chord streaming) — `boot_ready` (status byte 3, mask 0x04) comes up
as soon as the internal 13-cycle VE hydration walk completes, no SD
card involved.

**Capture path:** RP2350 Pico 2, `rp2350_spu_irotc_test` firmware,
spi0 on GP0-3 (MISO=GP0, CS=GP1, SCK=GP2, MOSI=GP3; built with
`-DSPU_RP2350_ZERO_HEADER_SPI=ON`) wired to the Tang 25K PMOD J4
flash-compatible header (CS#=G10, SCK=D10, MOSI=B10, MISO=C10),
common ground, USB CDC at 115200 baud.

**Six-case link-level proof, all PASS:**

```
[1/6] LOAD2X QR1 = 2*(0,3,-6,9)                                 PASS
[2/6] IROTC QR2 <- QR1 idx36 main                                PASS
[3/6] IROTC QR3 <- QR1 idx36 CONJUGATE                           PASS  <- conjugate-catalog silicon
[4/6] CATMIX conj-on-MAIN faults, no commit (still QR3)          PASS  <- CATMIX poison, no commit
[5/6] SCALE2 QR5 = 2*QR2 (recondition)                           PASS
[6/6] IROTC QR6 <- QR5 conj idx3 (post-SCALE2 switch)            PASS
=== Results: 6/6 PASSED ===
ARITHMETIC_BLAZE: PASS
```

Case [3] (`D603010064000000`) committed lane 3 = A=(3,-6) B=(-3,-9)
C=(-12,15) D=(12,0) — the dual-icosahedron rotation of idx36 applied
to the same doubled input as case [2]'s main-catalog result, bit-exact
against `test_icosahedral_catalog.py`. Case [4] issued a CONJ-tagged
IROTC against QR2 (MAIN-tagged from case [2]) — the CATMIX guard
fired and the QR commit correctly held at lane 3 (case [3]'s value),
proving the 13×2-bit tag file enforces the typestate contract over the
SPI link, not just in the bare-engine TB. Case [6] proves SCALE2's
FRESH re-conditioning legally re-opens the catalog choice (conjugate
idx3 after a main-catalog idx36 chain).

**Interpretation:** IROTC is now silicon-proven end-to-end — engine,
tag file, dispatch FSM, and SPI transport — including the conjugate
catalog and CATMIX refusal that §3.2k left as testbench-only. Full
60-index × both-catalog surface remains testbench-verified
(`spu13_irotc_engine_tb.v`, `spu13_spi_core_irotc_tb.v`); this probe's
silicon scope is the six-case vector set above (idx36 main+conjugate,
idx3 conjugate, LOAD2X, SCALE2, one CATMIX fault).

### 3.2l Wukong Tensegrity Admission-Guard Silicon Probe

**Date:** 2026-07-14. The first-tranche standalone Artix probe was
SRAM-loaded through the inline-100-ohm-protected RP2040 DirtyJTAG path. The
operator confirmed the probe working after load. Its acceptance contract is:

```
TGR:P V:5 E:00
```

The five completed fixtures are TGR1 IDs 0, 1, 2, 3, and 5: canonical
balanced, topology fault, shared-endpoint strut collision, collapsed cable,
and MAIN/CONJ grid mismatch. The wrapper compares every state/fault pair
before emitting the verdict; `V:5` is a completed-fixture count, not vector
ID 5. Build figures were 2,013 `SLICE_LUTX`, 526 `SLICE_FFX`, 0 BRAM, 0 DSP,
and 72.51 MHz against the 50 MHz board clock.

**Second-tranche attempt:** the first V:6 image (SHA-256
`c178462f9fdcb11533467b74fb3425dc083c307e2016b7355e14eb7779cd9b54`) was
loaded and repeatedly reported:

```
TGR:F V:4 E:84
```

This proves fixtures 0-3 completed and fixture 4 returned a state/fault
mismatch; it is not intersection silicon evidence. That route closed at only
51.89 MHz, leaving 0.7 ns modeled slack. The synthesized Xilinx-cell model of
the intersection engine passed all eight cases, while post-route inspection
found two independent near-critical combinational paths: distributed
edge/node-table predicates and a 108-bit subtraction feeding its decision in
the same cycle. Both are now pipelined. The replacement image uses 13,876
`SLICE_LUTX`, 3,509 `SLICE_FFX`, 72 DSP48E1, 0 BRAM and closes at 57.27 MHz
while constrained to 55 MHz. SHA-256:
`07748c85a3a212c9128641824792d962a3547b5435cf6e3d6dc4aaab0f3f6c0d`.
Its repeat board result is recorded below; it encodes the actual state/fault
pair as `E:1SSSSFFF` rather than the first image's generic `84`.

**Repeat result:** the 57.27 MHz replacement (SHA-256
`07748c85a3a212c9128641824792d962a3547b5435cf6e3d6dc4aaab0f3f6c0d`)
still failed fixture 4:

```
TGR:F V:4 E:90
```

`0x90 = {1, state=2, fault=0}` decodes to `BALANCED/F_NONE`: counts and the
first four verdicts were correct, but no intersection contact was latched.
The next image moves the entire table loader, guard scanner, and intersection
engine to a divided-BUFG 25 MHz domain; UART remains at the board's 50 MHz.
OpenXC7 still conservatively timed the guard clock against 50 MHz and closed
at 59.16 MHz (UART/sys clock 111.15 MHz), giving more than 2x margin at the
actual guard cadence. Resources: 13,895 `SLICE_LUTX`, 3,515 `SLICE_FFX`, 72
DSP48E1, 0 BRAM. Failure lines now append `A:xx`, the number of strut-pair
intersection attempts, so another miss separates pair scanning from predicate
arithmetic without a diagnostic rebuild. Current packed bitstream SHA-256:
`d72412f1cfbd82b2a7c8d4ded597382c4272531628711f8b24ac53212ac344d8`.

**Successful repeat:** the divided-clock image produced the repeating board
verdict:

```
TGR:P V:6 E:00
```

This closes silicon evidence for all six fixtures carried by the V:6 image:
canonical balanced plus topology, strut collision, cable slack, exact
antipodal strut intersection, and grid mismatch faults. The failure sequence
also establishes the operating boundary: the exact guard is reliable at the
25 MHz divided cadence, while the two attempted 50 MHz images produced a
fixture-4 false negative despite nominal OpenXC7 closure.

**Final admission tranche (silicon PASS):** the V:7 wrapper adds
TGR1 ID 6 and the exact type-uniform Z[phi] equilibrium guard. It accumulates
one cable/GAP and one strut force row per node/axis, derives the shared density
ratio from a nonzero pivot, checks every row by exact cross multiplication,
and applies exact sign tests; the canonical `2:-3` ratio is not hard-coded.
The direct guard TB additionally passes a phi-scaled canonical fixture, and
the wrapper TB observes all seven state/fault pairs before accepting:

```
TGR:P V:7 E:00
```

Focused regression: `TB_FILTER=tensegrity python3 run_all_tests.py` = 37 PASS,
0 FAIL. XC7A100T synthesis/P&R/pack are clean. Resources are 22,520
`SLICE_LUTX` (17%), 6,373 `SLICE_FFX` (5%), 108 DSP48E1 (45%), and 0 BRAM.
Post-route Fmax is 106.72 MHz for the 50 MHz system/UART domain and 42.93 MHz
for the divided 25 MHz guard domain. The node table is explicitly implemented
as registers: allowing a third replicated asynchronous RAM32M read port made
nextpnr's timing graph incomplete. Packed bitstream:
`build/spu_a7_100t_TENSEGRITYPROBE.bit`, 3,825,929 bytes, SHA-256
`7859d0e7d78218fcf49d5b4cd091332f0f0b5d5c3641edbc8b0380caba592d3f`.
After DirtyJTAG SRAM load on 2026-07-14, the operator returned the exact UART
verdict `TGR:P V:7 E:00`. This closes silicon evidence for all seven frozen
TGR1 admission fixtures, including ID 6's type-uniform equilibrium fault.

**Scope boundary:** V:7 is the silicon-proven bounded admission scope.
Intersection silicon scope is the antipodal origin-crossing fixture; the full
crossing/overlap/T-junction matrix remains RTL-verified. Equilibrium silicon
scope is the canonical pass plus ID 6's perturbed-coordinate rejection under
the type-uniform density contract. The oracle's broader nonuniform per-edge
nullspace fallback and active rotation/actuation control remain outside the
hardware claim.

**Karatsuba-candidate-as-default silicon confirmation, 2026-07-24.** The
above proof used the four-product reference multiplier. Following the
Z[phi] Karatsuba three-product candidate's Phase 0-5 completion
(`docs/ZPHI_KARATSUBA_INTEGRATION_PLAN.md` — formal proof, transaction-
semantics hardening at production widths, default-off selector plumbing,
dual-mode integration regression, matched three-seed P&R, then the
production-default switch itself), this closes Phase 6's standalone half:
silicon confirmation of the candidate multiplier as the actual shipped
default, not just simulation/formal/P&R evidence.

Build: clean commit `8aaaeaa` (current `origin/master` at build time),
`ZPHI_KARATSUBA=1 A7_SEED=2 A7_FREQ=25`, seed deliberately distinct from
the Phase 4 matched matrix's 1/7/13 so this build could not collide with
or overwrite that evidence. `synth`/`pnr`/`pack` all clean: router
converged to zero overuse, timing PASS on both clocks (`guard_clk`
43.47 MHz, `sys_clk` 70.86 MHz, both against the 25 MHz target), no
unconstrained or incomplete-timing warnings. Packed bitstream:
`build/spu_a7_100t_TENSEGRITYPROBE_ZK1_S2.bit`, 3,825,936 bytes, SHA-256
`07c979daf0da76697c615527620eb2b96c85433438862368db43645550dd4cad`.

DirtyJTAG SRAM load completed cleanly (`isc_done 1`, `init 1`, `done 1`).
UART readback over 15 seconds returned exactly `TGR:P V:7 E:00`, repeated
200 times with zero variance and no other output — the same seven-fixture
admission verdict as the reference-multiplier proof above, now produced
by the candidate. This closes the standalone-`TENSEGRITYPROBE` half of
Phase 6. The `TENSEGRITYLINK` half (full transactional admission,
mechanical-negative, corrupt-payload rollback, and recovery, per the
integration plan) **is CLOSED as of 2026-08-09 — see §3.2l.1** (10/10
runs on bitstream `40373ab8…`).

*Superseded text, kept for the record:* this entry previously said that
half "remains open, gated on the power-ready interlock". Both halves of
that were stale. The interlock stopped gating anything on 2026-08-04
(reaffirmed 08-07) — the 100 ohm series resistors on all four SPI lines
plus power-sequencing discipline cover that damage class — so the work
was runnable for five days before anyone noticed. The blocker was
recorded here while its removal was recorded in the roadmap and BOM,
with nothing connecting the two. When retiring a gate, search for what
cites it.

**Transactional table-link build evidence (not silicon evidence):** the
follow-on `TENSEGRITYLINK` spin connects optional southbridge commands B2/B3
to `spu13_tensegrity_sidecar.v`. Its raw 1,016-byte store is inferred as
exactly one RAMB18E1 and split into active/staging banks. A B2 transaction is
made visible only after transport CRC-8, TGR1 CRC-32, structural parsing, and
full guard replay complete; every rejection path preserves the prior active
vector and verdict. The sidecar module bench proves valid commit, CS abort,
payload-CRC rejection, and a second mechanically failing but representationally
valid commit. The SPI integration bench proves exact B2 framing, B3 response,
bad-CRC diagnostics, deadman-timeout abort, and rollback through the real
slave. A boundary regression holds B3 across the guard's one-cycle done pulse,
proves the prior status remains coherent, then releases and commits the
remembered result. The focused suite is
37 PASS / 0 FAIL; the host parser is 33/33 and the protocol oracle is 9/9.
XC7A100T synthesis is clean at 12,909 estimated logic cells, 108 DSP48E1, and
one RAMB18E1. The reproducible seed-1 route closes with zero overuse at
24,675 `SLICE_LUTX`, 7,655 `SLICE_FFX`, 40.16 MHz guard-domain Fmax, and
318.78 MHz system-domain Fmax against a 25 MHz constraint. The packed
3,825,928-byte bitstream is
`build/spu_a7_100t_TENSEGRITYLINK.bit`, SHA-256
`a515381a8b90ceba836da83c7fe80bf719033717d72458cfb8297d7753d63463`.
**Partial board evidence, 2026-07-16:** after reseating the remapped J11
connector, the standalone electrical loopback returned repeated 16/16 exact
passes. The RP2350 then initialized the SD card and sent the 468-byte canonical
TGR1 table through B2; B3 reported `received=expected=468`, proving the live
SPI/SD/transport/length-accounting path. Reduced images using the same sidecar
and parser each terminate correctly: intersection-only committed vector 100,
and equilibrium-only committed vectors 100 and 101, as
`state=2 fault=0 flags=0x08 nodes=12 edges=30`.

The original full combined image does **not** terminate on that same canonical
table. It remains at `state=0 fault=0 vector=0 flags=0x04`, with no active
nodes/edges and `received=expected=468`; an immediate post-reset retry and a
second combined build with a lower guard-domain constraint behave identically.
This localizes the open issue to the combined intersection+equilibrium
implementation, after successful transport/parser replay, but does not yet
distinguish the exact internal wait state. Therefore B2/B3 have partial silicon
evidence, while complete atomic admission and invalid-table rollback through
the combined guard remain unproven. The agreed next step is componentization
with explicit stage handshakes/watchdogs and eventual shared Z[phi] arithmetic,
not further blind place-and-route seed searches.

**Term-serial combined revision, 2026-07-18 (build + live status evidence):**
the verifier now exposes a coarse B3 service stage and a one-million-cycle
rollback-safe watchdog. Intersection and equilibrium use separate four-cycle,
captured-input Z[phi] multiplication services instead of four parallel integer
products each. Full regression is 170/170 (129/129 Verilog), including a new
direct signed multiplier/latency bench and a forced intersection-timeout proof
that returns loader error 10, stage `0x85`, preserves the active transaction,
and then recovers.

The monolithic diagnostic route was stopped at iteration 38 with 392 conflicts.
The term-serial image routes cleanly at iteration 41 with 25,120 SLICE_LUTX
(19%), 8,972 SLICE_FFX (7%), 66 DSP48E1 (27%), one RAMB18E1, guard Fmax
42.23 MHz, and system Fmax 336.25 MHz. Packed bitstream:
`build/spu_a7_100t_TENSEGRITYLINK.bit`, SHA-256
`478e206c65fa5f18c44e7604ca27139e5d65f551ac91a170d8beb78baa4c7c57`.

DirtyJTAG SRAM load completed with `done=1`; the rebuilt RP2350 firmware then
returned:

```text
OK tgrstatus version=1 state=0 fault=0 stage=0 vector=0 \
  flags=0x00 error=0 nodes=0 edges=0 received=0 expected=0
```

This is silicon evidence for the refactored image, J11 link, and new B3 stage
field only. The canonical combined verdict could not be run in that session:
`sdinit` returned `ERR no SD card`, and `sdprobe` showed GP12 MISO floating.
Do not promote the complete atomic verifier to silicon-proven until the SD
module is reconnected and the canonical/fault/rollback sequence completes.

**Complete TENSEGRITYLINK closure, 2026-07-19:** the SD path was restored and
the parser-bounded term-serial image completed the full transaction on the
Wukong Artix-7.  The image routed at 25,563 SLICE_LUTX (20%), 8,980
SLICE_FFX (7%), 66 DSP48E1 (27%), and one RAMB18E1; guard Fmax was 41.54 MHz
at the 25 MHz operating cadence.  The packed bitstream is
`build/spu_a7_100t_TENSEGRITYLINK.bit`, SHA-256
`30381825ed444d92a5474740c0219c84fff449e05ba575d45dcbb409459a1de5`.

The following admission, mechanical-negative, corrupt-payload rollback, and
recovery sequence was reproduced bit-for-bit on three consecutive runs:

```text
state=2 fault=0 stage=8 vector=0 flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468
state=8 fault=5 stage=8 vector=6 flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468
state=8 fault=5 stage=0 vector=6 flags=0x09 error=7 nodes=12 edges=30 received=468 expected=468
state=2 fault=0 stage=8 vector=0 flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468
```

The corrupt-payload case used the bench-only `tgrloadbadcrc` command: firmware
flipped the final TGR1 payload byte in RAM and then generated a valid SPI
transport CRC-8, so loader error 7 proves the FPGA's independent payload
CRC-32 rejection and preservation of the active vector-6 verdict.  The full
B2/B3 transactional transport and combined intersection+equilibrium admission
guard are therefore silicon-proven.  The parser telemetry/watchdog changed
placement as well as observability, so the precise cause of the older stage-1
stall was not isolated; this closure claim is tied to the bitstream hash
above.  The remaining tensegrity frontier is the active proposal/actuation
controller, not table transport or bounded admission.

### 3.2l.1 TENSEGRITYLINK Four-Act Proof on the Karatsuba Candidate

**Date:** 2026-08-09 NZT.

**Scope:** the `TENSEGRITYLINK` half that §3.2l left open. That entry proved the
four acts on 2026-07-19 with the **four-product reference** multiplier
(bitstream `30381825…`), and `c1fe58f` made the **three-product Karatsuba
candidate** the production default four days later, on 2026-07-23. The shipped
configuration therefore had no transactional-half evidence until this run.
Closes criterion 5 of `docs/ZPHI_KARATSUBA_SWAP_CRITERIA.md`; criteria 1-4 were
met by the 2026-08-08 P&R sweep and the 2026-08-09 formal/regression re-run.

**Build & load:**

```
ZPHI_KARATSUBA=1 A7_SEED=1 bash hardware/boards/artix7/build_a7.sh 100t tensegritylink pack
usbreset 1209:c0ca
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_TENSEGRITYLINK_ZK1_S1.bit
# isc_done 1  init 1  done 1

cmake -S hardware/rp2350 -B build/rp2350_tgr -DPICO_BOARD=pico2 \
  -DSPU_RP2350_ZERO_HEADER_SPI=ON -DSPU_SD_BAUD_HZ=1000000
cmake --build build/rp2350_tgr --target rp2350_spu_diag -j4
```

Packed from the routed artifact of the 2026-08-08 sweep, so the routed design
is bit-identical to the measured one. `A7_SEED=1` is the build default — this
evidences what an ordinary build ships, not a selected seed. Post-route guard
Fmax 46.63 MHz against the 25 MHz constraint.

Bitstream `build/spu_a7_100t_TENSEGRITYLINK_ZK1_S1.bit`, 3,825,935 bytes,
SHA-256 `40373ab866aa4cdc8a5b563a4f378436e99989b3220d3e73e7f1a7e2f2fe5e0b`.

**Result: PASS, 10/10 complete four-act runs, zero deviations.** Driven over
the RP2350 diagnostic console; full raw capture in
`build/tgr_four_act/campaign.log`. Run 1 verbatim:

```text
> tgrload TGR/00_canonical_balanced.tgr 0
OK tgrload bytes=468 vector=0
OK tgrstatus version=1 state=2 fault=0 stage=8 vector=0 flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468
> tgrload TGR/06_fault_not_in_equilibrium.tgr 6
OK tgrload bytes=468 vector=6
OK tgrstatus version=1 state=8 fault=5 stage=8 vector=6 flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468
> tgrloadbadcrc TGR/06_fault_not_in_equilibrium.tgr 6
OK tgrloadbadcrc bytes=468 vector=6
OK tgrstatus version=1 state=8 fault=5 stage=0 vector=6 flags=0x09 error=7 nodes=12 edges=30 received=468 expected=468
> tgrload TGR/00_canonical_balanced.tgr 0
OK tgrload bytes=468 vector=0
OK tgrstatus version=1 state=2 fault=0 stage=8 vector=0 flags=0x08 error=0 nodes=12 edges=30 received=468 expected=468
```

Across the 40 status reads: 20 × `state=2 fault=0` (admission and recovery),
20 × `state=8 fault=5` (mechanical negative, and its preservation under
rejection), 10 × `error=7` (payload-CRC rejection). Every field was compared
per act by the driver, not eyeballed.

**On the positive control.** The bench-evidence standard requires one. Here it
is **internal**: acts 2 and 3 are the control. If act 2 stopped returning
`state=8 fault=5`, or act 3 stopped returning `error=7`, the rig would not be
discriminating and a run of clean passes would carry no information. Both fired
on all ten runs. This differs from the Padé campaign, where the control had to
be a separate known-bad bitstream, because there the failure signal was absent
by construction.

**Interpretation.** The candidate multiplier sustains the full B2/B3
transactional path: atomic admission of a valid table, commit of a genuine
mechanical-negative verdict, independent TGR1 CRC-32 rejection of a corrupted
payload carrying a *valid* transport CRC-8 with the prior verdict preserved,
and recovery on canonical reload. Combined with §3.2l's 2026-07-24 standalone
`TENSEGRITYPROBE` confirmation, the Karatsuba candidate as shipped default now
has both halves proven in silicon.

**Limitations, stated rather than omitted.**

- The SD fixtures were **not** hash-verified against their repository
  references; the card reader would not enumerate. Verification is partial but
  strong by another route: the card's file header matches the repo fixture
  byte-for-byte including the embedded CRC-32 (`e750a663`), the size matches at
  468 bytes, and the FPGA independently validates that payload CRC-32 on every
  load — which is precisely the mechanism act 3 exercises. A substituted table
  would have to collide on both the CRC field and the byte count.
- SD ran at 1 MHz rather than the committed 8 MHz default. At 8 MHz on jumper
  wiring, `sdinit` passed at its 400 kHz init rate while reads returned
  `FR_DISK_ERR`. This concerns the RP2350's own microSD bus and is unrelated to
  the J11 link or the FPGA.
- During bring-up a 3V3 bare microSD adapter was briefly powered at 5 V. The
  card survived and read correctly afterwards, but the excursion is recorded
  because it also placed 5 V on a non-5V-tolerant RP2350 GPIO through the
  card's DO line.

### 3.2m Wukong `spu_a7_top` Outage — Root Cause and Silicon Re-Proof

**Date:** 2026-08-02 → 2026-08-03.

**Scope:** every `spu_a7_top` spin rebuilt after the 2026-07-13 J11 remap
returned all zeros over SPI — `LUCAS` (two builds, two backends), `SU3`, and
`ROBOTICS` — while the standalone tops `TENSEGRITYLINK` and `SOMSIDECAR` kept
answering on the same board, wiring and firmware. The failure had been
localised in the 2026-08-01 handover to "between chord-accept and QR-commit."
**That localisation was wrong**; the fault was upstream of the SPI slave
entirely.

**How it was found.** The `0xAC` status frame already carried the answer. On a
sidecar spin (`spu_a7_top.v:980`) it decodes as:

| Byte | Content |
|---|---|
| 0 | `0x5A` literal (`sidecar_status_hi`) |
| 1 | `debug_last_spi_opcode`, latched on `spi_inst_valid` |
| 2 | `{su3_state[2:0], ratio_valid, fifo_full, error_seen, claim_seen, commit_seen}` |
| 3 | `{5'h0, boot_ready, crc_error_sticky, busy}` |

Byte 0 is hard-wired and byte 2 bit 4 is a hard-wired `1'b1`, so **a live
slave on this spin can never return `00 00 00 00`**. The board returned exactly
that for `0xAC`, `0xA0`, `0xAE`, `0xAF` and the scale read — the response path
had never run. Golden frames were established in simulation first
(`spu13_a7_lucas_spi_integration_tb.v`): idle `5A 00 10 00`, live
`5A <opcode> 13 00`.

**Ruled out by direct comparison** against `TENSEGRITYLINK`'s artifacts:
SPI package pins (J4/G4/B4/B5), IOB sites (`spi_miso` at `IOB_X1Y120` in both),
every SPI IOB's FASM features (byte-identical), the clock input pin (M21), the
`rst_n` IOB configuration, and the MISO driver (a real FF at
`SLICE_X80Y130/B5FF` in the failing build).

**Two defects, both in `spu_a7_top.v`, fixed in `0eec6f4`:**

1. **The reset pin — the operative fault.** `spu_a7_top` fed the raw `rst_n`
   pad straight into every async reset. `rst_n` (H7) carries no `PULLTYPE` in
   any XDC. The silicon-proven standalone tops two-flop synchronise it and hold
   reset until it reads high for 256 consecutive clocks
   (`spu_a7_tensegrity_link_top.v:18-27`); `spu_a7_top` did not. The
   reset-free heartbeat counter kept toggling throughout, which is why the
   board read as half-alive.
2. **A BUFG cascade.** With `A7_CLK_DIV_LOG2 = 0` the raw branch instantiated a
   BUFG fed from the BUFG `clkbufmap` already places on the clock port.
   nextpnr-xilinx 0.8.2 accepted it and emitted
   `BUFGCTRL15_I0 <- CK_MUXED30 <- CK_IN_R0` — a right-edge clock **input**
   track that nothing in the design drives, i.e. an undriven `clk_fast`.
   Verified in `build/spu_a7_100t_LUCAS.json.pnr.fasm`, archived at
   `build/evidence_archive/bufg_cascade_2026-08-02/`. Fixing this alone did not
   restore function; it is a real defect that would have surfaced next.

**Silicon re-proof.** `build/spu_a7_100t_LUCAS.bit`, SHA-256
`41df24aa145c192d6b2dff223443802684c84fbcd3ba90e54e9c5dda315e88d3`, SRAM-loaded
over RP2040 DirtyJTAG (`isc_done 1 / init 1 / done 1`), driven from
`rp2350_spu_diag` at 250 kHz over J11:

```
status                    -> raw=5A 00 10 00      (live, idle)
chord D0200C0500000000    -> qr valid=1 lane=2  A=0x0000000800000005   raw=5A D0 13 00
chord D1C00C0500000000    -> qr valid=1 lane=12 A=0x0000020400000008   raw=5A D1 13 00
chord D2300C0500807000    -> qr valid=1 lane=3  A=0x0000004200000029   raw=5A D2 13 00
chord D3400C0500000000    -> qr valid=1 lane=4  A=0x0000000500000201   raw=5A D3 13 00
```

All four match the `rp2350_lucas_j11_smoke.c:44` oracle, and every status frame
matches the simulated golden value byte for byte. **This is the first working
`spu_a7_top` bitstream since the J11 remap.**

> **That artifact no longer exists.** It was overwritten later the same day by
> a rebuild into the same canonical name — the exact hazard recorded below
> under "never invoke `build_a7.sh` against an existing artifact name."
> Synthesis is not bit-reproducible here, so it cannot be re-derived, and the
> hash above is no longer verifiable against anything on disk.
>
> The replacement, built from the same committed source plus the `rst_n`
> `PULLUP` constraint, is
> `07cb3d7e2c77726120a0cfca96b461cf56d7f256c53c9008d46142d66302c07c`. It was
> re-verified on silicon — idle `5A 00 10 00`, PSCALE `lane=2
> A=0x0000000800000005`, PINV `lane=4 A=0x0000000500000201`, status frames
> `5A D0 13 00` and `5A D3 13 00` — and archived with a manifest at
> `build/evidence_archive/lucas_pullup_2026-08-03/`. **Quote that hash, not the
> one above.** The behavioural claim is unaffected and rebuildable from
> `0eec6f4`; only the original artifact is gone.

**Neither defect produces a diagnostic** at synthesis, place-and-route or pack,
and neither is observable in simulation — `sim_xilinx_bufg.v` is
`assign O = I;`, and simulation drives a clean reset. Standing rules: never
instantiate a BUFG whose input is another BUFG's output, and never feed a raw
pad into an async reset on this board.

**Calibration on nextpnr's reported Fmax:** the 2026-07-03 LUCAS build that
passed on silicon reports `clk_fast` max **4.79 MHz**; the 2026-08-01 build
that failed reports **68.71 MHz**. Both ran the same board clock. These numbers
are not evidence a design will or will not work.

**Full spin sweep, 2026-08-03.** Every `spu_a7_top` spin rebuilt from fixed
source and bench-tested in the same session, on the same wiring, each with its
own firmware at 25 kHz (LUCAS and SU3 from the `rp2350_spu_diag` console at
250 kHz — both coreless, so `clk_fast` is 50 MHz and that is ratio 200):

| Spin | Bitstream SHA-256 (first 16) | Result |
|---|---|---|
| LUCAS | `41df24aa145c192d` (lost; superseded by `07cb3d7e2c777261`) | PASS — 4/4 oracle vectors |
| SU3 | `a8b9f661892fd052` | live — `00 EA 32 01`, opcode latched, sidecar claimed |
| ROBOTICS | `fa1e3c7c4fa9589c` | PASS — `13/13 PASSED`, `ARITHMETIC_BLAZE: PASS` |
| SU3SHARE | `dd061f5a6acfa246` | PASS — `SU3_J11: PASS`, 9 lanes |
| RPLUCFG | `82a87d1190657a2c` | PASS — `RPLU2_J11: PASS`, count=149, checksum `0xBA708FD4` |
| RPLU2CORE | `94741644e56c8063` | PASS — transport, `RPLU2CORE_QR`, `RPLU2CORE_QSUB` |
| RPLU2PADE | `626e2260e86e1043` | **4/5** — `seven_over_three` fails, see below |
| IROTC | `f0ff82f3232f5ff0` | PASS — `6/6 PASSED` |

SU3 received a liveness-and-dispatch probe rather than its full oracle;
SU3SHARE exercises the same sidecar and passes all 9 lanes.

**RPLU2PADE `seven_over_three` — the FP4 structured inverter, in synthesis
only.** The default build returns `A=0x000000000CA45881` where the oracle is
`0x55555557` (7·3⁻¹ mod M31). The other four cases, including `wide_constants`
(12345/6789), are exact, so the evaluator, config transport and readback all
work; this is not the reset or clock fault.

A same-day A/B settles it. `spu_a7_100t_RPLU2PADE_FI0B0_S1.bit`
(`225459d24cf058c5…`), identical source built with `FP4_STRUCTURED=0`, passes
**all five cases** with `seven_over_three` = `0x55555557` — `RPLU2PADE_J11:
PASS` on 41 consecutive runs. The default v2 build fails that case just as
consistently.

**The inverter's logic is exonerated; its v2 synthesis path is implicated.**
Both implementations are correct in simulation, and the coverage that was
missing has since been added: the frozen corpus went 25 → 31 vectors with the
small-scalar family 3, 5, 6, 7, 9, 11 (regenerated from `software/lib/a31_field.py`,
which was not modified), and `spu13_spi_rplu2_pade_tb.v` now covers all five
firmware cases under `USE_STRUCTURED_INVERTER` 0 **and** 1 — both pass,
`seven_over_three` included, with a hierarchical assertion proving the
parameter reaches the DUT. So this is a behaviourally-correct design that is
wrong once synthesised, i.e. synthesis or timing on the v2 path, not arithmetic.

`5399b4c` flipped v2 default-on on 2026-08-01; §3.2f records this case passing
on 2026-07-05. The regression window matches the flip exactly.

**Operational consequence:** `FP4_STRUCTURED=0` is the known-good setting for
`RPLU2PADE` on silicon today. The v2 default is not safe for this spin until
the synthesis divergence is understood.

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
pins pass per-bit walk test. Confirmed hardware fault on the external SDRAM
module (Winbond W9825G6KH) itself, not the FPGA or the Dock PCB — see
AGENTS.md's SDRAM entry (this section previously had the fault backwards).

**Build command (masked):**

```
./build_25k_sdram_min_probe_mask.sh
```

**Result:** With DQ[10] masked out (treated as don't-care), all remaining
DQ/DQM/addr/control pins pass. The masked build is used for all subsequent
SDRAM-containing probes.

---

### 3.6 Source Anchors and Reproduction Status

*Added 2026-08-15 (T9).*

Every entry above records the SHA-256 of the bitstream that was flashed. Until
now none recorded **which source tree produced it**, and several recorded no
build command either. A hash with no source anchor proves only that some file
existed — it cannot be regenerated, so it cannot be checked.

This section closes what can be closed and states plainly what cannot.

**How to read the anchor column.** Only one entry has a *confirmed* anchor: a
commit from which the recorded bitstream has actually been rebuilt bit-for-bit.
The rest carry a **candidate** commit — the repository HEAD on the entry's
recorded date. A candidate is a starting point for a reproduction attempt, not
a record. Two known weaknesses:

- Builds were often made from a dirty tree, so the true input may be a
  candidate plus uncommitted edits — and a hash quoted in a commit message is
  not proof of what that commit builds. This is not hypothetical; see the
  worked case in §3.6b.
- Where the repo had commit gaps, several entries collapse onto one candidate.
  §3.2g.1, §3.2e.4 and §3.2e.5 all resolve to `502c962` despite spanning
  2026-06-30 to 2026-07-05, so the candidate carries almost no information.

| § | Date | Flashed bitstream | Build command | Source anchor | Rebuild status |
|---|---|---|---|---|---|
| 3.2e.4 | 07-04 | `71319fbb…` | `A7_FREQ=2 A7_CLK_DIV_LOG2=6 build_a7.sh 100t rplu2core` | `502c962` cand. (gap) | UNMEASURED |
| 3.2e.5 | 07-05 | `4dff1a6e…` | `A7_FREQ=2 A7_CLK_DIV_LOG2=6 build_a7.sh 100t su3share` | `502c962` cand. (gap) | UNMEASURED |
| 3.2e.6 | 08-07 | `a8b9f661…` | **absent** | `616bc44` cand. | UNMEASURED |
| 3.2e.7 | 08-09 | `07cb3d7e…` | **absent** | `0e0a4a3` cand. | UNMEASURED |
| 3.2g.1 | 06-30 | `0385b641…` | `build_25k_spu13_som_bmu_probe.sh` | `502c962` cand. (gap) | **DIFFERS** — builds `a3df02d5…`; **5** commits touch its 4 sources, cause not isolated |
| 3.2g.2 | 07-06 | `6177aa67…` | `build_25k_spu13_som_hydrate_probe.sh` | **`a8b5bdc` or later, CONFIRMED** (not the `a71635c` candidate — see §3.6c) | **REPRODUCES** at current HEAD |
| 3.2g.3 | 07-16 | `8c6b6f8e…` | `build_25k_spu13_som_sidecar.sh` | `35105c3` cand. | DIFFERS — builds `a7d3459e…`; see §3.6b |
| 3.2g.4 | 07-17 | `946574dc…` | **absent** | `df6cffd` cand. | UNMEASURED |
| 3.2g.5 | 07-17 | `8753c492…` | `build_25k_spu13_som_sidecar.sh` | **`f4e271e` CONFIRMED** | **REPRODUCES** from `f4e271e` (2026-08-14) |
| 3.2g.6 | 07-17 | `f22a34e7…` | `build_a7.sh 100t somsidecar` | `df6cffd` cand. | DIFFERS — see §3.6a |
| 3.2j | 07-08 | `9599f5e4…` | `build_25k_spu4_probe.sh` | **`511f3f3` CONFIRMED** — rebuilt 2026-08-16 and reproduces the flashed hash bit-exactly | **SUPERSEDED by §3.2j.2.** Historical record of the 07-08 run; used 2026-08-16 as the positive control, 4/4 |
| 3.2j.2 | **08-16** | `0061b02f…` | `build_25k_spu4_probe.sh` | `2adebf6` | **CURRENT** — 10/10 loads, 250 identical lines, 4/4 positive control. Re-anchors T7.4 and the width fix together |
| 3.2j.3 | 08-16 | `1e70739d…` | `build_25k_spu4_abi_probe.sh` | **absent** | UNMEASURED — first ABI silicon, predates this table row |
| 3.2j.6 | **08-17** | `23ba4a3f…` | `build_25k_spu4_abi_probe.sh` | **`daabf25` CONFIRMED** — rebuilt post-commit, reproduces the flashed hash bit-exactly | **CURRENT** — 10/10 loads, `id` field matches SPU4_ABI.md 2a on every load |
| 3.2k | 07-10 | `4aedc901…` | `build_25k_spu13_irotc_probe.sh` | `d1244e0` cand. | **DIFFERS, cause explained** — builds `6ac1e8ab…`; `73acd91` (07-12) moved the IROTC code ROM to BSRAM after this proof, see §3.6d |
| 3.2k.1 | 07-12 | `ca54c1dc…` | `build_25k_spu13_irotc_spi.sh` | `6f6ec43` cand. | **BUILD_FAILED — not reproducible from any tested tree**, see §3.6f |
| 3.2l | 07-14 | `d72412f1…` | **absent** | `62dd6c3` cand. | UNMEASURED |
| 3.2l.1 | 08-09 | `40373ab8…` | `ZPHI_KARATSUBA=1 A7_SEED=1 build_a7.sh 100t tensegritylink` | `0e0a4a3` cand. | UNMEASURED |
| 3.2m | 08-03 | 8 spins, see entry | `build_a7.sh 100t <spin>` per spin | `7e6ac4a` cand. | UNMEASURED — and **not anchorable as written**, see below |

**Two entries need more than an anchor.**

- **§3.2m** is a sweep of eight `spu_a7_top` spins, each with its own bitstream,
  and it records them as **16 hex characters, not full SHA-256**. Sixteen hex
  characters is a fine label but a weak identifier, and it cannot be compared
  against a `sha256sum` without truncating the fresh value to match — which
  silently weakens the comparison. The entry also notes the LUCAS bitstream
  `41df24aa145c192d` is **lost**. Future sweeps should record full hashes; the
  existing ones stay as they are, since shortening happened at capture time and
  the full values are unrecoverable.
- **§3.2e.6 and §3.2e.7** carry full hashes and no build command at all. Both
  are Wukong J11 spins from August; the spin name is recoverable from the entry
  text, but the env prefix (`A7_FREQ`, `A7_SEED`, `ZPHI_KARATSUBA`) is not, and
  on this project those change the output. Treat their anchors as unrecoverable
  until someone reproduces them by search.

**Standing rule.** A historical bitstream hash in this document records what was
flashed to a board. It is never to be overwritten with a fresh build hash —
that would assert hardware testing that did not happen. Where a rebuild
disagrees, the disagreement is recorded in the rebuild-status column and the
flashed hash stays untouched. `hardware/boards/board_build_manifest.json` is
the separate record of what this tree builds today; the two files are never
copied between.

#### 3.6a A7 SOM sidecar rebuilt after the `BAUD_COUNTER` change (2026-08-15)

`bc06156` added a `BAUD_COUNTER` parameter to a module `spu_a7_som_sidecar_top`
consumes, and was verified only through yosys. §3.2g.6 could therefore not be
trusted until a full place-and-route and pack run passed. It now has:

```bash
PRJXRAY_ROOT=$HOME/toolchains/prjxray \
OPENXC7_PYTHON=$HOME/.local/venvs/prjxray/bin/python \
  bash hardware/boards/artix7/build_a7.sh 100t somsidecar all
```

Result: synth, P&R and bitstream generation all complete, exit 0. Routing
converged with zero overused wires at iteration 4, and the post-routing clock
report is 80.18 MHz against the 50 MHz constraint (PASS).

| Metric | §3.2g.6 (07-17) | Rebuild (08-15) |
|---|---|---|
| SLICE_LUTX | 8,013 | 8,161 |
| SLICE_FFX | 3,098 | 3,131 |
| DSP48E1 | 44 | 44 |
| RAMB18E1 | 4 | 4 |
| Routed fmax | 65.63 MHz | 80.18 MHz |

**Scope of this result — build only.** It establishes that the `BAUD_COUNTER`
change does not break the Artix-7 sidecar, which was the open risk. It does
**not** re-prove §3.2g.6 in silicon: the rebuild produces
`bf4c1614a0311fa91565ec68df8bc6b1a89dbc899015a17ffa163811aacf3023`, which
differs from the flashed `f22a34e7…`, and it has not been loaded to a board or
run against the Iris corpus. §3.2g.6's silicon claim continues to rest on the
July run.

#### 3.6b Worked case — a commit message anchored to a hash its own tree does not build

Recorded because it is the clearest example of why a hash needs a source anchor,
and because it resolves a loose end left open on 2026-08-14.

`bc06156`'s message states: *"Sidecar now builds at 14,126 LUT4 (61%) … Anchor
bitstream SHA-256 `af0c5e4c…`"*. The manifest recorded two commits later at
`3c9e92d` instead gives `a7d3459e…`. Both cannot be right. What was measured:

1. `build_25k_spu13_som_sidecar.sh` is **bit-deterministic** on this design —
   `a7d3459e…` has now been produced on three separate runs (two on 08-14, one
   on 08-15), including on the large near-utilisation-limit build where
   determinism was least certain.
2. The sidecar's full input set is the six sources in
   `synth_gowin_25k_spu13_som_sidecar.ys`, the `-I hardware/rtl/arch` include
   dir, the `.cst`, the `.ys` and the build script.
   `git diff --name-only bc06156..HEAD --` over exactly that set is **empty**.

A deterministic build over an unchanged input set has one output. So `bc06156`'s
committed tree builds `a7d3459e…`, and `af0c5e4c…` was produced from a working
tree that was never committed. **`af0c5e4c…` is not reproducible and should not
be used as an anchor.** The correct anchor for the post-fix sidecar is
`a7d3459e…` at `bc06156` or later.

Nothing about the fix in `bc06156` is affected — the LUT figures and the
vendor-specific `BAUD_COUNTER` reasoning stand. Only the quoted hash is wrong.
The general lesson is the one this section exists for: a hash captured mid-work
records a tree that may never be committed, so anchor hashes should be taken
from a clean tree, after the commit, or not quoted at all.

#### 3.6c A date-derived anchor that is provably wrong, and what corrects it

§3.2g.2 is recorded as **2026-07-06**, which gives the candidate `a71635c`. But
`a8b5bdc` (**2026-07-07**) modifies `spu_som_weight_bram.v`, one of the probe's
two sources, and the current tree still reproduces the flashed `6177aa67…`.
Since no commit after `a8b5bdc` touches either source, every tree from
`a8b5bdc` to HEAD builds the same bitstream — and `a71635c`, which predates the
source change, cannot.

So the true anchor is **`a8b5bdc` or later, which is after the date the entry
records**. Either the bench date and the build date differ, or the image was
rebuilt; the record does not say which.

Two things follow, and they generalise past this entry:

1. **A date-derived candidate can be wrong, not merely imprecise.** Every
   candidate in the table above should be read as a hypothesis.
2. **Reproduction is what upgrades an anchor**, and it upgrades it to a
   *range* — "`a8b5bdc` or later" — rather than a point. That range is a
   stronger statement than a single unverified commit, because it was measured.

#### 3.6d §3.2k DIFFERS — cause identified, and it is benign

`73acd91` (2026-07-12) rewrote the IROTC engine's 540-entry code ROM from a
combinational case function into an initialized memory mapped to one BSRAM,
after finding that the old form synthesized into deep `MUX2_LUT8..5` chains and
routing-livelocked the SPI spin. The engine dropped from ~6.9k to ~3.0k cells.

§3.2k's silicon proof is dated **07-10**, before that rewrite, so its bitstream
could not match a current build and the DIFFERS is fully expected. The rewrite
preserves behaviour: ROM values are bit-identical and mechanically derived from
the verified table, the fixed 13-cycle slot is unchanged, and the engine TB's
per-case 12-clock latency assertion passes on all 120 golden cases alongside
the chain, fault matrix, probe, core-opcode and SPI-level testbenches.

**Treat this as closed-explained, not open.** The July silicon result stands for
the pre-BSRAM engine; the current source is a different implementation of the
same behaviour, verified in simulation but not separately re-proven on silicon
for this probe.

#### 3.6e What hash-reproduction can and cannot anchor

Sorting the measured targets by how many sources they pull in against how much
those sources have since changed makes the pattern plain:

| Target | Sources | Commits since anchor | Result |
|---|---|---|---|
| `spu4_probe` (3.2j) | 7 | 0 | REPRODUCES |
| `som_hydrate_probe` (3.2g.2) | 2 | 1 | REPRODUCES |
| `som_bmu_probe` (3.2g.1) | 4 | 5 | DIFFERS |
| `irotc_probe` (3.2k) | 2 | 1 | DIFFERS |
| `irotc_spi` (3.2k.1) | **51** | **21** | see entry |

Hash-reproduction is a workable anchor for **narrow probes** — few sources,
little churn, so a mismatch is a real signal worth investigating. It is
structurally unusable for **full-core spins**: `irotc_spi` compiles 51 sources,
effectively the whole SPU-13 core, so it absorbs every core commit and diverges
permanently after any core work. A DIFFERS there carries almost no information.

**Consequence for `board_build_manifest.json`.** Adding full-core spins to the
manifest would produce a check that fails constantly for uninformative reasons,
which is how checks get ignored. For those spins the honest anchor is the
commit, and re-verification means re-running the bench, not re-hashing. The
manifest should stay biased toward narrow probes, where a hash mismatch means
something changed that nobody intended.

#### 3.6f §3.2k.1 is BUILD_FAILED — the Tang 25K no longer builds this spin

Measured 2026-08-15. §3.2k.1 was previously recorded as UNMEASURED on the
belief that the 2026-08-14 attempt had merely been slow, killed at 90 minutes
because of `--placed-svg` / `--routed-svg` / `--detailed-timing-report`. **That
explanation is refuted.** All three flags were removed and the build still does
not complete.

Two trees were measured, and neither produces a bitstream:

| Tree | Cells | Placement | Routing |
|---|---|---|---|
| HEAD (`f9754a6`) | 23,081 | succeeds | **livelock** — 317k iterations / 8.5 h, plateaus at ~58,011 of 71,950 arcs unrouted |
| Anchor `6f6ec43` | 22,997 | **fails legalisation** | never reached |

The router does not stall so much as thrash: it resolved 7,728 arcs in the
first 40k iterations and about 141 in the last 37k, while per-iteration cost
rose roughly 80× (2.31 → 183 s per 1000 iterations). At the terminal rate the
remaining arcs would take on the order of 26 days, still degrading.

**Nothing is near a resource limit** in either tree — 52% LUT4, 37% DFF, 15%
MUX2_LUT5, 1/56 BSRAM, 14% IOB. The placer's `design is probably at utilisation
limit` text is misleading here; this is a legalisation failure on a design with
ample room, the same class as the pre-BSRAM livelock `73acd91` describes, and
the ~58k plateau closely matches the ~58.9k that commit records.

**What this rules out.**

- *A regressing commit.* The two trees differ by 84 cells (0.37%) yet fail in
  **different phases**, and HEAD places where the anchor does not. The 21
  commits since the anchor did not cause this.
- *`5399b4c`, the prime suspect.* It flipped `USE_STRUCTURED_INVERTER` to
  default-on, and its own message notes the default governs "other tops" — but
  synthesising this spin with the parameter at 1 and at 0 gives **identical**
  cell counts (23,081 both ways). The structured inverter is unreachable from
  this spin's top and is pruned. Exonerated.
- *Design growth.* 0.37% is not a capacity story.

**What it leaves.** The spin sits at the edge of what the Gowin placer and
router can handle for this design, and its outcome is unstable to perturbations
far smaller than any intentional change. §3.2k.1's 2026-07-12 bitstream is
therefore **not reproducible from its own sources on this toolchain**, and the
entry cannot be re-anchored by rebuilding.

One alternative is not excluded: that the toolchain moved since July in a way
that affects this design specifically. The 2026-08-14 toolchain check covered
the SOM sidecar, not this spin. Against that, the narrow `irotc_probe` (§3.2k)
still builds today, so Gowin support is not globally broken.

**Recommendation: stop treating `irotc_spi` as a Tang 25K target.** This is
consistent with what this document already says — the 25K's role is "closed as
a split-probe regression target" and "full concurrent integration belongs on an
Artix-7 200T / Kintex-class board." A 51-source full-core spin is exactly what
that boundary excludes. The 2026-07-12 silicon result stands as a historical
observation; it should not be presented as a currently reproducible build.

#### 3.6g Five Tang 25K spins have outgrown the GW5A-25A — a capacity boundary, not a bug

Measured 2026-08-15/16, after the board-build check widened from 5 to 21
targets (`42c65e9`) and exposed seven failing spins. **Six of the seven are
size failures** — five over the fabric's capacity outright, and
`six_step_probe` at 96% failing to route through congestion. Only `irotc_spi`
fails with room to spare (§3.6f), and it is the one genuine anomaly.

| Target | LUT4 used / 23,040 | Verdict |
|---|---|---|
| `series_stream_probe` | **70,390 = 305%** | over capacity |
| `southbridge` | **61,439 = 267%** | over capacity |
| `rotc_probe` | 33,456 = 145% | over capacity |
| `som_southbridge` | 29,437 = 127% | over capacity |
| `som_probe` | 23,891 = 103% | over capacity |
| `six_step_probe` | 22,212 = **96% — it fits** | **routing**, not capacity; see below |
| `irotc_spi` | 12,136 = 52% | **routing pathology**, see §3.6f |

**The placer's error message names a symptom, not a cause.** `rotc_probe` and
`southbridge` both fail naming a `MUX2_LUT*` cell, which resembles the
"Gowin mux blow-up… unexplained" that `bc06156` describes. It is not that.
The named cell is whichever one the placer gave up on while the design sat far
over capacity. `southbridge` is the decisive case: it fails on **`MUX2_LUT8`,
the one resource with headroom** —

```
LUT4:      61439/23040  266%
MUX2_LUT5: 23546/11520  204%
MUX2_LUT6:  9864/ 5760  171%
MUX2_LUT7:  4199/ 2880  145%
MUX2_LUT8:  1644/ 2880   57%   <- the cell named in the error
```

`series_stream_probe` confirms the same point from the opposite direction. Its
mux resources are **uncontended** — MUX2_LUT5/6/7/8 at 64% / 37% / 29% / 8% —
and its error correspondingly names **LUT4 itself** ("no BELs remaining"), not a
mux. The `MUX2_LUT*` name appears only when the muxes happen to be over
capacity too. It is a report of where the placer stopped, not of what ran out.

Likewise `design is probably at utilisation limit` is literally true for
`som_probe` at 103% and actively misleading for `irotc_spi` at 52%. **Measure
the utilisation; do not read the message as a diagnosis.**

**`six_step_probe` is not a capacity failure at all.** Measured 2026-08-16, it
is the one target in the group that comfortably fits, and the 1200 s timeout
recorded on 08-15 concealed that:

| Phase | Result |
|---|---|
| Synthesis | 22,212 / 23,040 LUT4 = **96%**; DFF 6%, ALU 9%, MUX2_LUT5 54% |
| Placement | **succeeds** — HeAP 483.8 s, then annealing |
| Post-placement timing | **PASS — 25.77 MHz** against the 12 MHz constraint |
| Routing | 109,475 arcs; degrading, see below |

Its router shows the same signature §3.6f documents for `irotc_spi` — cost per
iteration rising while progress falls:

| Iteration window | Arcs resolved | Rate | Seconds / 1000 iter |
|---|---|---|---|
| 82k → 98k | 3,505 | 5.83 arcs/s | 37.6 |
| 98k → 108k | 1,797 | 3.19 arcs/s | 56.4 |
| 108k → 115k | 1,200 | 2.64 arcs/s | 65.0 |
| 115k → 126k | 1,963 | 2.46 arcs/s | 72.4 |

Monotone in both directions across four windows: the arc-resolution rate more
than halved while per-iteration cost roughly doubled. At iteration 126k,
**67,337 of 109,475 arcs were still unrouted after 49 minutes of routing** —
that is, 62% of the design remained unrouted having consumed six times the
whole build's nominal budget.

**This is an extrapolation, not an observed failure:** at the last measured
and still-falling rate the remainder needs on the order of 7–8 hours. The run
was left going; if it converges, this paragraph is what needs correcting.

**Correction — it is not a second `irotc_spi`.** I first wrote this up as
making routing "a population of two, not one", which overstated it. Comparing
against the footprint recorded in `docs/build_and_bringup_guide.md` for the
run that was proven in silicon:

| | Proven run | 2026-08-16 | Change |
|---|---|---|---|
| LUT4 | 13,576 (59%) | **22,212 (96%)** | **+63%** |
| ALU | 1,024 | 1,600 | +56% |
| DFF | 1,518 | 1,518 | **unchanged** |

DFF identical to the digit while combinational logic grew by half. So
`six_step_probe` is a **congestion** failure: the design grew until the fabric
was 96% full, and routing a nearly-full device is expected to be hard. That is
an ordinary consequence of growth, not an anomaly.

`irotc_spi` remains the genuinely anomalous one — it fails to route at **52%**,
with ample room. **Routing-with-room is still a population of one.** The two
share a symptom, not a cause, and this is the same trap §3.6g is otherwise
about: reading a shared error for a shared diagnosis. Do not merge them.

**Both routing levers were tried and both fail.** Measured, not assumed.

*A longer timeout does not rescue it.* Watched to iteration 140k over 68
minutes: 65,740 of 109,475 arcs still unrouted, and the arc-resolution rate
fell monotonically 5.83 → 3.19 → 2.64 → 2.46 → **1.39** arcs/s. That is decay
toward the `irotc_spi` terminal state, not slow convergence. Extrapolating the
last measured rate gives ~13 h and rising. The run was stopped; raising
`timeout_seconds` is not a fix.

*An alternate router and seed do not rescue it either.* `--router router2
--seed 7` reached routing iteration 2 with **25,087 wires overused** out of
~275k (iteration 1: 25,991 overused, 44,412 total overuse) — the same
congestion signature as the default router, reached sooner. Stopped there.
Placement quality is the lever a different router pulls, and at 96% occupancy
there is no slack for it to exploit.

**Therefore trimming is the only remaining route** to a buildable Tang
`six_step_probe`. Seeds and routers are covered ground; do not spend on them
again.

#### DECIDED 2026-08-16 — `six_step_probe` is quarantined, not retired

It is the one spin sitting on the capacity boundary, which makes it the early
warning for exactly the growth that cost five spins their Tang targets. Two
obvious dispositions are both wrong:

- **Retire it** → discards the only canary. The next design to cross the line
  gets found the way these five were: years late, at 305%.
- **Keep gating it on buildability** → it fails every run, and a permanently
  red check is one everybody learns to ignore. That is how the four-week SOM
  sidecar outage survived.

So the gate changed instead of the target. `six_step_probe` now uses
`"check": "utilisation"` in `board_build_manifest.json`: synthesise, pack,
compare LUT4 occupancy against a ceiling, and **skip placement and routing
entirely**. Recorded baseline **22,212 / 23,040 = 96.4%**, ceiling 100%.

**Why occupancy is the better quantity.** Neither `sha` nor `builds` can give
early warning, because both need a build that completes, and a design over
capacity never completes — they report the failure only once it is total, and
take hours to do it. Occupancy moves gradually, is deterministic (no placer or
router seed noise), and `nextpnr --pack-only` reports it in **about two
seconds**. Growth below the ceiling is printed and recorded but does not fail,
so it surfaces in a manifest diff during review rather than as noise.

Had this gate existed, all five retirements would have tripped it at 101%
rather than being discovered at 103–305%. The manifest now runs 13 `sha`,
2 `builds` and 1 `utilisation`; the two remaining `builds` entries
(`rplu2_arith_probe`, `math_probe`) build fine today, so converting them is an
optimisation rather than a fix.

The spin still does not build, and that is accepted: its 2026-06-30 Tang
silicon result stands as history, and six-step also has A7 ROBOTICS coverage,
so nothing currently depends on producing a Tang bitstream from it.

**None of this is new breakage.** No board top was rebuilt between its original
spin and `239bf4c`, so these have been failing for unknown periods — the same
way the Tang SOM sidecar was silently unbuildable for four weeks. This is a
backlog becoming visible.

`som_southbridge` additionally had a real, separate fault in front of the
capacity one: `spu13_axiomatic_gatekeeper` was instantiated in `spu13_core`
but absent from this spin's `.ys` file list, a synthesis regression from
`7b80a59` (08-13). Fixed in `2315d77`. That fix was necessary but only exposed
the 127% underneath it.

**For the five capacity failures, this was a scope decision, not a debugging
task.** They crossed the 25K's capacity line with nothing watching.

#### DECIDED 2026-08-16 — all five are retired as Tang 25K targets

John's call. **Retired by decision, not by defect.** Nothing here is broken
RTL; these designs are correct and simply larger than a GW5A-25A.

| Retired target | LUT4 | Notes |
|---|---|---|
| `series_stream_probe` | 305% | Cause known, remedy known — see below |
| `southbridge` | 267% | Already recorded as not fitting on 2026-07-11, at 25.5k |
| `rotc_probe` | 145% | **Did fit once** — real Tang silicon at 13,352 LUT4, §3.2g |
| `som_southbridge` | 127% | |
| `som_probe` | 103% | Closest to fitting; best trim candidate if wanted back |

**What retirement means here.** They are removed from
`hardware/boards/board_build_manifest.json`, so they no longer run in the
board-build check. A target that cannot fit cannot be a regression signal — it
fails every run, and a check that always fails trains people to ignore it.
Their scripts and RTL are **kept and unmodified**; each script now carries a
`RETIRED` header stating its number and this rationale.

**Re-entry condition:** trim under 23,040 LUT4, rebuild, re-add to the
manifest. Nothing else is required, and none of this is irreversible.

**What is not lost.**

- **ROTC** keeps its silicon evidence. §3.2g records a genuine Tang run at
  13,352 LUT4 with UART proof `ROTC:P A:5 E:00`; that happened and stands.
  ROTC additionally has A7 ROBOTICS coverage. What is gone is only the ability
  to *reproduce* that bitstream on this fabric — see the note in §3.2g.
- **SOM on Tang survives.** `som_sidecar`, `som_bmu_probe` and
  `som_hydrate_probe` all still build and remain in the manifest. Only the
  larger `som_probe` and `som_southbridge` spins are retired, so the SOM
  product track keeps its Tang regression coverage.
- **`series_stream_probe` has a known fix path.** `docs/SPIN_CATALOG.md`
  already carried the diagnosis — a combinational M31 multiplier — and the
  remedy: a sequential variant or a Gowin DSP wrapper. Its 305% was recorded
  there before this sweep measured it independently. It is retired as a *Tang*
  target, not abandoned as a design.

**`rotc_probe` is the one worth pausing on.** It fit at 13,352 LUT4 (58%) when
it was proven in silicon, and stands at 33,456 today — **2.5× growth** in a
spin nobody rebuilt. `southbridge` tells the same story twice over: known not
to fit at 25.5k on 2026-07-11, now at 61,439. This is the cost of the
board-build gap that `239bf4c` closed, measured after the fact.

The boundary this enforces is the one this document already draws: the 25K is
"closed as a split-probe regression target", and full concurrent integration
"belongs on an Artix-7 200T / Kintex-class board."
This is the boundary this document already draws — the 25K is a split-probe
regression board, and full concurrent integration "belongs on an Artix-7 200T /
Kintex-class board."

`spu4_probe` builds and is bit-reproducible, so T7 — the declared primary
direction — is not blocked by any of this.

---

### 3.7 GPU depth-v2 + reciprocal — first silicon (2026-08-25)

**Date:** 2026-08-25 NZT.

**Scope:** first silicon for the depth-v2 affine-interpolated-depth
pipeline (`spu_depth_dispatch.v` → `spu_depth_math.v` →
`spu_reciprocal_core.v` → `spu_shared_mult35.v` → `spu_attr_stepper.v`),
scoped and implemented same-session per the GPU rasterizer thread (see
`spu_strategy/contract_gpu_depth_v2_shared_multiplier_arch_2026-08-25.md`,
gitignored planning layer). All five modules were testbench-verified
against `software/lib/gpu_depth_v2_oracle.py` and synthesis-measured
(41.8% Tang 25K, integrated) before this — this entry is the first time
any of it ran on real hardware.

**Build & load:**

```bash
bash build_25k_spu13_depth_v2_silicon_probe.sh
openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_depth_v2_silicon_probe.fs
```

Bitstream SHA-256:
`70babbad19589b1a552654974842c5415b43729bb52de60de430339b71d390aa`.

**Fixture:** the "small, screen-corner" triangle already used across
the depth-v2 oracle/RTL parity tests — v0=(10,10) z0=0, v1=(600,30)
z1=65535, v2=(300,460) z2=32768. The probe pulses `depth_setup0` once
(exercising the full setup arithmetic: 9 dot-product multiplies,
`D=c0+c1+c2`, the reciprocal core's normalize/LUT/Newton-Raphson, 3
final-scale multiplies), then steps `spu_attr_stepper` 200 rows + 300
columns from the origin to pixel (300,200) — a point independently
confirmed inside this triangle — and self-checks `A_z0/B_z0/C_z0/
frac_bits0` and the resulting per-pixel depth against oracle-derived
constants hardcoded at build time.

**UART proof — stable, repeating:**

```
DEPTH2:P D=00007EB7
```

`D=00007EB7` = 32439 decimal, the oracle's exact expected interpolated
depth at (300,200) for this triangle — bit-exact match, not a
tolerance/rounding check. `P` requires **all five** hardcoded
expected values (`A_z0`, `B_z0`, `C_z0`, `frac_bits0`, and the final
per-pixel depth) to match simultaneously; any single mismatch reports
`F` instead.

**What this establishes.** The full depth-v2 arithmetic chain — dot
products, the denominator-from-existing-coefficients shortcut, the
multiply-only reciprocal (leading-one detector, 256-entry ROM, one
Newton-Raphson iteration), the shared 40×17 multiplier, and 500 cycles
of per-pixel incremental accumulation — works end to end on real Tang
25K silicon, on a fixture an independent Python oracle also computed.
**What this does NOT establish:** perspective-correct texture mapping
(explicitly out of scope, needs a genuinely per-pixel reciprocal, not
this setup-time one); real multi-triangle-per-frame throughput (this
probe runs the setup once, not repeatedly); or a second triangle
unit / the pending-queue dispatch logic under real timing (only unit 0
was exercised here — `spu_depth_dispatch`'s queue behavior is
testbench-verified only, per `test_gpu_depth_dispatch_rtl_parity.py`).

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

*Not yet built on this machine, and not close to it: `hardware/ice40_nano/`
and `hardware/ice40_regular/` exist as directories but their `build.py`
files are empty stubs, not working scripts. No `build_gw1n1.sh` or
`build_25k.sh` exist anywhere in the repo (verified 2026-07-16) — the Tang
25K build path is the many `build_25k_spu13_*_probe.sh` scripts
documented elsewhere in this ledger and in AGENTS.md.*

---

## 5. What Remains Unproven

### Board-Level

| Item | Status |
|---|---|
| SDRAM DQ[10] repair | Physical fault in the external SDRAM module — permanent mask or module replacement required (FPGA board itself is healthy) |
| Second FPGA board | Stale entry, unconfirmed as of 2026-07-16 — reported in transit as of this doc's 2026-07-11-era update; no later confirmation of arrival found |
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
| ROTC angles 0–5 in silicon | **Verified in Silicon** on Tang 25K with UART `ROTC:P A:5 E:00`; covers canonical trace for all 6 angles plus period closure for angles 1-5. Uses TDM core (`spu13_rotor_core_tdm.v`) with silent `div3` — see Davis Gate entry in `knowledge/SPU_LEXICON.md` for the /3 exactness caveat. |
| ROTC tagged (deferred-reduction) core | TB-verified (8/8, `spu13_rotor_core_tagged_tb.v`); probe `spu13_tang25k_rotc_tagged_probe.v` **still awaiting a board run after five weeks** (built 2026-07-09). **Rebuilt and manifest-covered 2026-08-16**: 570/23,040 LUT4 = 2.5%, `u_rotc.clk` closes 120.03 MHz against 12 MHz (CORRECTED 2026-08-17: the 120.03–135.37 MHz range previously recorded here was nextpnr's final post-route figure and its post-placement estimate, unlabeled; 120.03 MHz is the final one), bitstream `5fa8b4b8…`, reproduced 2×. It was one of four targets the 08-15 sweep left uncovered. Nothing blocks the board run. Golden-vector re-verification contract: ROTATE must produce 3× TDM golden at exp=1; REDUCE must recover TDM golden at exp=0. **Fixed 2026-07-09:** REDUCE's `reduce_val64` loaded lane values via zero-extension instead of sign-extension — every negative lane value (routine in this representation) either false-faulted INEXACT or missed a real exact division; `-9` at exp=1 is the regression case (Test 8). |
| SOM/BMU classifier in silicon | **Verified in Silicon** on Tang 25K with UART `SOM:P T:2 B:6 E:00`; covers 2 weighted BMU oracle scenarios and cluster reduction for the 7-node fixture |
| Writable SOM sidecar over RP2350 SPI | **Verified in Silicon** on Tang 25K: hydrated winners returned SPI `80 A0 B0` and matching C3 UART `00 14 1E`; exact fixed-434-cycle HEAD datapath, §3.2g.3 |
| Reproducible Iris SOM edge classifier | **Verified in Silicon** on Tang 25K and Wukong Artix-7: checked seven-node map plus labels, 35/35 writes, 150/150 complete SOM1 evidence records equal the exact oracle on each vendor, 147/150 semantic labels (98.0%), §§3.2g.5–3.2g.6 |
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
| `run_all_tests.py` | Full automated regression exercised on 2026-07-11: `Total PASS: 151`, `Total FAIL: 0`. |
| C++ test suite automated run | Covered by `run_all_tests.py` full regression. |
| Cross-validation (Python VM vs C++) | PASS — `cross_validate.py`: 5/5 snaps matched |

---

## 6. Toolchain Versions (Confirmed Working)

| Tool | Version / Path | Purpose |
|---|---|---|
| **iverilog** | OSS CAD Suite, `/opt/oss-cad-suite/bin/iverilog` | Verilog simulation (Icarus) |
| **vvp** | OSS CAD Suite, `/opt/oss-cad-suite/bin/vvp` | VVP runtime |
| **yosys** | `Yosys 0.63+87 (git sha1 2f1cdc2df, clang++ 18.1.8 -fPIC -O3)` | Synthesis (synth_gowin / synth_xilinx) |
| **nextpnr-himbaechel** | `nextpnr-0.9-99-g4ace8952` | Place & route (GW5A-25A) |
| **nextpnr-xilinx** | `0.8.2-73-gf681eb3a`, `~/.local/openxc7` | Place & route (xc7a100t) |
| **gowin_pack** | OSS CAD Suite | Bitstream packaging (Gowin) |
| **prjxray / fasm** | `~/toolchains/prjxray`, venv `~/.local/venvs/prjxray` | Bitstream packaging (Xilinx) |
| **openFPGALoader** | `v1.1.0` | FPGA programming via USB |
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

---

### 3.8 First video output — 640x480 VGA on a monitor (2026-09-04)

**Date:** 2026-09-04 NZT.
**Board:** QMTech Wukong Artix-7 XC7A100T-FGG676, 50 MHz oscillator.
**Claim:** the SPU display path produces a correct, standards-conformant
640x480@60 VGA signal that a physical monitor locks to and displays.

This is the **first video output of any kind** from this project on any board.

**Source anchor** (both, deliberately — §3.6 notes most historical entries
carry a bitstream hash but no commit and often no build command):

```
commit    bf00be0  a7: VGAFIX -- the measured J10 pin mapping, and first pixels
bitstream build/spu_a7_100t_VGAFIX.bit
          3,825,920 bytes
          SHA-256 a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379
build     bash hardware/boards/artix7/build_a7.sh 100t vgafix all
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_VGAFIX.bit
          -> isc_done 1  init 1  done 1
```

**Design.** `spu_a7_video_top`-class VGA spin: 50 MHz divided by two for a
25 MHz pixel clock (no MMCM, no PLL), `spu_video_timing`, `spu_video_pattern`
(eight colour bars plus a vertically scrolling marker), `hal_vga`. Output is
1 bit per channel through an external three-resistor DAC. `clk_pixel` closes
at 170.97 MHz against the 25 MHz requirement; 246 LUTs, 54 FFs.

**Instrumented measurements** (fx2lafw on J10, 2 s captures):

| quantity | measured | expected | error |
|---|---|---|---|
| HSYNC frequency | 31248.25 Hz | 31250 | **0.006%** |
| HSYNC duty | 88.01% | 88.00% | exact |
| implied pixel clock | 24.9986 MHz | 25.0000 | 0.006% |
| implied frame rate | 59.520 Hz | 59.524 | 0.007% |
| GREEN | 1.00 runs/line | bars 0-3 contiguous | — |
| RED | 2.00 runs/line | bars 0,1 + 4,5 | — |
| BLUE | 3.64 runs/line | bars 0,2,4,6 x 480/525 | — |
| R/G/B duty | 36.4 / 36.4 / 36.7% | 36.6% | — |

The 88.01% duty is the VESA 640x480@60 sync pulse exactly (96 low of 800),
so this is standards-conformant timing rather than merely a square wave at
about the right rate. The colour run counts fall directly out of the bar
layout, and the 40% -> 36.6% scaling from vertical blanking appears
independently in all three channels.

**Visual confirmation.** Eight vertical colour bars in the correct order
(white, yellow, cyan, green, magenta, red, blue, black) with the marker line
scrolling vertically, on a physical VGA monitor. The scrolling marker is the
liveness control: static bars cannot distinguish a running pipeline from a
frozen one.

**Pin mapping was MEASURED, not read.** The QMTech README and the LiteX
`qmtech_wukong` platform file list J10 in opposite orders and neither states
which is physical. Three bitstream variants built on inferred mappings all
failed. `J10IDENT` (every J10 pin driven at a distinct frequency) probed at
the VGA plug gave:

```
VGA pin 13 (HSYNC) <- FPGA D5    6103.0 Hz, 0.0% error
VGA pin 14 (VSYNC) <- FPGA E5     381.5 Hz, 0.0% error
```

J10's top row follows the LiteX order; its bottom row does not. Each earlier
variant had exactly one half right.

**What this does NOT establish.**

- **Nothing about HDMI/DVI.** That path cannot currently be built at all —
  nextpnr-xilinx cannot place differential outputs (openXC7 issue #66, open
  and unimplemented). `spu_a7_video_top` and `hal_hdmi_serdes_a7.v` exist and
  synthesise, but have never been placed, packed or loaded.
- **Nothing about the GPU.** This is a test-pattern generator. The rasterizer,
  depth-v2 and reciprocal blocks are not in this bitstream.
- **Colour depth is 1 bit per channel** (8 colours). The 4-bit ladder is
  unbuilt.
- **Single observation.** One monitor, one session. Not an N>=10 result and
  not offered as one.
