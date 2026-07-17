# Hardware Evidence Ledger

A boring, reproducible record of what passed, what failed, and what remains
unproven.  No speculation — only commands, conditions, and results.

*Last updated: 2026-07-16*

Current regression headline: `python3 run_all_tests.py` reports
`Total PASS: 161`, `Total FAIL: 0`. ROTC is gated through angles 0-35
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
| Toolchain | OSS CAD Suite: Yosys 0.50 → nextpnr-himbaechel → gowin_pack → openFPGALoader |

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

### 3.2g.2 Writable SOM Sidecar SPI/UART Silicon Proof

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

### 3.2g.3 Reproducible Iris SOM Corpus Silicon Proof

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

### 3.2g.4 SOM1 Full Decision-Evidence Silicon Proof

**Date:** 2026-07-17 NZT

**Scope:** renewed Tang Primer 25K silicon proof of the complete versioned
`SOM1` observation-to-decision path. This run used the same checked Iris map
and corpus as §3.2g.3, but replaced the legacy winner-only evidence boundary
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
| ROTC tagged (deferred-reduction) core | TB-verified (8/8, `spu13_rotor_core_tagged_tb.v`); probe `spu13_tang25k_rotc_tagged_probe.v` built (2026-07-09), awaiting board run. Golden-vector re-verification contract: ROTATE must produce 3× TDM golden at exp=1; REDUCE must recover TDM golden at exp=0. **Fixed 2026-07-09:** REDUCE's `reduce_val64` loaded lane values via zero-extension instead of sign-extension — every negative lane value (routine in this representation) either false-faulted INEXACT or missed a real exact division; `-9` at exp=1 is the regression case (Test 8). |
| SOM/BMU classifier in silicon | **Verified in Silicon** on Tang 25K with UART `SOM:P T:2 B:6 E:00`; covers 2 weighted BMU oracle scenarios and cluster reduction for the 7-node fixture |
| Writable SOM sidecar over RP2350 SPI | **Verified in Silicon** on Tang 25K: hydrated winners returned SPI `80 A0 B0` and matching C3 UART `00 14 1E`; exact fixed-434-cycle HEAD datapath, §3.2g.2 |
| Reproducible Iris SOM edge classifier | **Verified in Silicon** on Tang 25K: checked seven-node map, 28/28 writes, 150/150 FPGA/oracle BMU winners, 147/150 semantic labels (98.0%), §3.2g.3 |
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
