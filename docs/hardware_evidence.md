# Hardware Evidence Ledger

A boring, reproducible record of what passed, what failed, and what remains
unproven.  No speculation — only commands, conditions, and results.

*Updated: 2026-10-15; entries retain their individual experiment dates and scopes.*

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

## Evidence Claim Boundaries

Evidence claims are independent; do not treat them as an automatic progression
or infer a later result from an earlier one.

| Claim | Evidence required | Does not establish |
|---|---|---|
| Structural validation | Inspection or automated check of the intended hierarchy/topology, with the source revision and check recorded | Functional behavior or physical realizability |
| Functional simulation | Named testbench/oracle, exact tested scope, command, and pass/fail result | Synthesis, timing closure, correct board interfaces, or silicon behavior |
| Synthesis / P&R | Device, constraints, toolchain, resource results, and routed timing outcome | Correct external interface wiring or successful physical operation |
| Interface validation | Evidence for clocks, reset, UART/protocol, and pin mapping using the stated method | Functional correctness of all workloads |
| Silicon observation | Exact programmed artifact identity and observed result, with scope limited to what was observed | Per-pixel or mathematical correctness unless separately measured against an oracle |

Use this record for new entries; write `NOT RUN` where a dimension was not
checked rather than leaving it implicit:

```text
Claim:
Evidence dimension: structural | simulation | synthesis/P&R | interface | silicon
Source revision / dirty-tree identity:
Build/test command and configuration:
Device and toolchain, when applicable:
Artifact identity (including bitstream hash for FPGA runs):
Oracle and checked scope, when applicable:
Result and evidence artifact path:
Adjacent evidence dimensions not established:
```

Repeatability is also reported as separate results: same-device repeated-run
agreement, cross-build agreement, cross-device agreement, and exact agreement
with an independent mathematical oracle. Measure the time, throughput, energy,
memory, or resource cost for each guarantee claimed. None of these results
implies another.

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

**Annotation (2026-11-05; original entry preserved above).** This entry is an
inventory, not a test result: it records no command or output. The files are
under `software/programs/`, not `tools/`. `wildberger_geometry`, `wildberger_layer2`
and `wildberger_chromogeometry` contained scalar Pell lines (`IDNT R0`,
`QROT Rd, Rs, 1`) that the historical assembler silently encoded as Quadray
operations on QR0, so any earlier run of them did not execute the written
scalar Pell steps. Their sources were corrected and regenerated on 2026-11-05
(see `docs/isa/CANONICAL_CONTROL_RECONCILIATION.md`, legacy binary boundary).
On the historical public Python VM, CALL shared opcode 0x20 with COND and was
executed as COND, so `call_demo` could not have exercised CALL/RET there;
canonical CALL/RET is tested by `software/tests/test_canonical_control.py`.
None of this is silicon evidence.

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

Photograph: `docs/bench_captures/2026-09-04_first_video_vga_colour_bars.jpeg`
(image is rotated 180 degrees; the bar order reads correctly when inverted).
The photograph independently confirms a stable image with no tearing, shear or
roll; bars spanning the full active width; and clean secondary colours --
yellow, cyan and magenta are each unmixed, which means all three channels
reach the correct level through the 270 ohm DAC rather than merely being
present. The wavy pattern across the bars is camera moire against the LCD
pixel grid, not a signal artifact.

**Observed on this display, cause not established:** a slight halo on the
moving marker line. This is an axis-aligned line stepping one integer row per
frame, so it lands exactly on pixel boundaries and cannot be spatially
aliased -- the likelier causes are the LCD's analog sampling PLL, panel
response time, or ringing on an unterminated hand-wired harness (270 ohm
series into a 75 ohm input is a large impedance mismatch). Untested. See the
queued CRT control in `SESSION_HANDOVER_2026-09-04.md` §7.

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

### 3.9 First rasterized geometry — GPU triangle on a monitor (2026-09-05)

**Date:** 2026-09-05 NZT.
**Board:** QMTech Wukong Artix-7 XC7A100T-FGG676, 50 MHz oscillator.
**Claim:** `spu_gpu_top`'s coverage rasterizer produces correct, stable
geometry on silicon, displayed through the VGA path proven in §3.8.

This is the **first rasterized geometry** from this project on any display.
`spu_gpu_top` had never been instantiated by any top on any board before
today — every prior reference to it in the tree was a comment, and the ECP5
build listed the file without its top ever using it.

**Source anchor:**

```
commit    dfbefd3  gpu: re-anchor the edge accumulators every frame, and the
                   first spu_gpu_top testbench
bitstream build/spu_a7_100t_GPUVGA.bit
          3,825,920 bytes
          SHA-256 b6045458d149e0ad90d87dfa19c3f89b9a05dcb7613af8722d5ca82ce13e2e1e
build     bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
detect    openFPGALoader -c dirtyJtag --freq 1000000 --detect -v
          -> 1 device, idcode 0x3631093, xc7a100, irlength 6
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA.bit
          -> Load SRAM 100%, isc_done 1, isc_ena 0, init 1, done 1
```

**Design.** `spu_a7_gpu_vga_top` swaps `spu_video_pattern` for `spu_gpu_top`
and changes nothing else about the §3.8 display path: 50 MHz / 2 for a 25 MHz
pixel clock (no MMCM), same reset debounce, same `hal_vga`, same
three-resistor DAC, same MEASURED `spu_a7_vga_fix.xdc` mapping. Built with
`DEVICE("A7")` and `ENABLE_HDMI(0)` — the latter is required, since
`hal_hdmi` emits OBUFDS and nextpnr-xilinx cannot place differential output
(openXC7 issue #66). One hardcoded triangle, no host link: if the shape
appears the rasterizer works, and if it does not the fault cannot be in a
link that would otherwise need debugging at the same time.

Post-route: 7,890/126,800 SLICE_LUTX (6%), 2,417/126,800 SLICE_FFX (1%),
2/240 DSP48E1, `clk_pixel` 40.28 MHz against the 25 MHz requirement.

**Triangle.** V0(320,100) V1(150,380) V2(490,380) in screen coordinates, flat
red on black. Edge coefficients computed by hand; each edge evaluates to
+95200 at its opposite vertex, so the winding is consistent.

**Geometric verification.** Measured off the photograph against the design:

| quantity | predicted | measured | note |
|---|---:|---:|---|
| base width / screen width | 53% | ~55% | 340/640 |
| height / screen height | 58% | ~60% | 280/480 |
| apex centred over base | yes | yes | isoceles |

Handheld-photo precision, so this confirms the shape is *correct* rather than
merely *present* — the edge coefficients, stepper arithmetic and coverage
test all agree with the intended geometry.

**Aliasing, as designed.** `spu_edge_stepper`'s `inside_out` is a hard
`(f >= 0)` test with no coverage fraction, so the two slanted edges stair-step
symmetrically at the predicted ~0.607 px/row while the horizontal edge
(`A = 0`) is straight with no steps. A jagged horizontal edge would have
indicated a fault; it is clean. `software/tools/golden_primes.py` exists but
is referenced nowhere in `hardware/rtl/` — no smoothing of any kind is applied
in this design.

Photograph: `docs/bench_captures/2026-09-05_first_triangle_gpu_vga.jpeg`
(rotated 180 degrees, as §3.8's is; the apex points up when inverted). The
blue-purple field is LCD backlight bleed and camera white balance — the design
emits zero on all channels outside the triangle, and the background reads
black by eye. The concentric fringes inside the red area are camera moire
against the pixel grid: the interior is one bit of red fully on at every
covered pixel and is uniform by construction.

**Three RTL defects were fixed to reach this**, all in never-built code and
all found the same day (`dfbefd3`, and `9c5d4e0`/`65ec1ef` before it):

1. **Frame drift.** `step_y` derives from the horizontal wrap alone, firing on
   all 525 lines while only 480 are displayed, and nothing re-anchored the
   accumulators after `setup`. Measured on the pre-fix RTL with B=170, `f_row`
   at successive frame starts: -17520, 71730, 160980 — a constant 89250 =
   525*170 step per frame. A triangle set up once left the screen almost
   immediately. `spu_gpu_top` now re-pulses setup at (0,0).
2. **`spu_depth_dispatch` never reset its coefficient outputs.** On an FPGA
   they come up at 0; in simulation they are X, an X depth reaches
   `spu_depth_compare`, and every pixel on the screen goes X. This is why
   `spu_gpu_top` had never been simulated — it could not be.
3. **An un-set-up raster unit covered the whole screen.** Its accumulators
   reset to 0 and `inside` is `(f >= 0)`, so all three edges reported inside.
   Coverage is now gated by an `armed` latch.

Covered by `hardware/tests/common/spu_gpu_top_frame_anchor_tb.v`, the first
testbench ever to instantiate `spu_gpu_top`: three frames from a single setup
must be identical by lit-pixel count and position-weighted checksum. PASS at
lit=47781 against a geometric area of 0.5*340*280 = 47600 (0.4%); FAIL with
the re-anchor disabled.

**What this does NOT establish.**

- **Nothing 3D.** No transform, no projection, no perspective. The edge
  coefficients are 2D constants written by hand.
- **No depth test was exercised.** Unit 1 is disarmed and all three z values
  are 1000, so `spu_depth_compare` never decided a pixel on depth. The depth
  path ran; nothing depended on its result.
- **No shading.** One flat colour per triangle is all the RTL can express;
  there is no shader stage of any kind.
- **No host link.** The triangle is hardcoded in the top.
- **One triangle.** Says nothing about triangle residency, the architectural
  limit of a framebuffer-less streaming rasterizer.
- **Single observation**, one monitor, one session. Not an N>=10 result.

**Bench caveat, recorded because it will recur.** The display was initially
black and came up after the operator prodded the hand-wired harness. The
connection is therefore marginal, and this result was obtained on a bench that
responds to being touched. That is a fault in the harness, not in the design —
but a future session must not assume clean wiring, and a marginal lead will
eventually fail in a way that resembles an RTL bug. It is the same
flying-lead class that the harness adapter board in
`spu_strategy/contract_graphics_first_priority_2026-09-04.md` §7 addresses.
The result was not re-confirmed after a deliberate reseat or a power cycle.

---

### 3.10 First depth-resolved image — two triangles on a monitor (2026-09-06)

**Date:** 2026-09-06 NZT.
**Board:** QMTech Wukong Artix-7 XC7A100T-FGG676, 50 MHz oscillator.
**Claim:** `spu_depth_compare` selects between two overlapping triangles on a
per-pixel basis on silicon, using depth interpolated by `spu_attr_stepper`
from coefficients computed at setup by `spu_depth_math`.

§3.9 established coverage rasterization but explicitly recorded that **no
depth test was exercised** — unit 1 was disarmed and all three z values were
equal, so `unit0_wins` reduced to `cov0` and nothing depended on the depth
result. This entry closes that gap.

**Source anchor:**

```
commit    eb27177  gpu: two overlapping triangles resolved by depth, so a
                   bench trip tests depth
bitstream build/spu_a7_100t_GPUVGA.bit
          3,825,920 bytes
          SHA-256 ce5bdc70753fc88d1a6e91bc1e573dff2c40756f66e9d689f9880139285e25e2
build     bash hardware/boards/artix7/build_a7.sh 100t gpuvga all   (A7_FREQ=25)
detect    openFPGALoader -c dirtyJtag --freq 1000000 --detect -v
          -> 1 device, idcode 0x3631093, xc7a100, irlength 6
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_GPUVGA.bit
          -> Load SRAM 100%, isc_done 1, isc_ena 0, init 1, done 1
```

Post-route: 7,896/126,800 SLICE_LUTX (6%), 2,419/126,800 SLICE_FFX (1%),
2/240 DSP48E1, `clk_pixel` 41.36 MHz against the 25 MHz requirement. Display
path unchanged from §3.8/§3.9: 50 MHz / 2, no MMCM, same reset debounce, same
`hal_vga`, same three-resistor DAC on J10, same MEASURED `spu_a7_vga_fix.xdc`.

**Scene.** Two triangles sharing the top edge y=0 from x=40 to x=600:

| | tri0 (red) | tri1 (green) |
|---|---|---|
| V0 / V1 / V2 | (600,0) (40,0) (120,460) | (600,0) (40,0) (520,460) |
| depth at V0 / V1 / V2 | 3600 / 400 / 700 | 400 / 3600 / 700 |

tri0 is near on the left and far on the right; tri1 the reverse. Both
interpolate 400..3600 across the shared edge in opposite directions, so they
are equidistant at x = 320 — the exact horizontal centre of the screen.
**Nothing in the geometry places an edge there.** The boundary exists only
because depth is compared per pixel, which is what makes this a test of the
depth path rather than of the rasterizer.

**Prediction registered before the bitstream was built.** The frame was
rendered out of `spu_gpu_top` in simulation at full 640x480 and checked
against an independent oracle built from the geometry: 0 mismatches over
307,200 pixels. The render and the checklist are in
`docs/bench_captures/2026-09-06_predicted_two_triangle_scene.{png,md}`.

**Photographic measurement.** Photograph
`docs/bench_captures/2026-09-06_two_triangle_depth_vga.jpeg`, 2016x1512. The
monitor is physically inverted, as in §3.8 and §3.9, so design y=0 appears at
the bottom of the frame and red appears on the right. Red and green pixels
were classified by channel dominance and the boundary taken as the midpoint
between the green and red runs on each scanline.

| quantity | predicted | measured | error |
|---|---:|---:|---:|
| depth boundary, fraction of lit width | 0.5000 | 0.5058 (sd 0.0010, 24 scanlines) | 0.58% of screen width, ~3.7 px in 640 |
| boundary straightness | vertical | sd 0.08 photo px over design rows 50..235 | — |
| triangles separate at design y | 268.3 | 271.5 | 3.2 rows, 0.66% of screen height |

**The row-0 check, and why it is the point of this scene.** The depth-anchor
defect fixed the same day (`8c2d2cc`, completed in `07a50f1`) was **row-0
only** — `spu_attr_stepper` was anchored wherever the setup latency ended
rather than at (0,0), and `acc_row` re-seeding from the row wrap meant the
field self-corrected from row 1. Both triangles were therefore given a shared
top edge so that scanline 0 is inside the overlap and a residual fault would
be visible:

```
boundary x over design rows ~50..235 : mean 1018.5 photo px, sd 0.08
boundary x over design rows 0..19    : mean 1017.5 photo px, sd 0.11
difference                           : 1.0 photo px = 0.46 screen px
```

An unfixed anchor would have displaced scanline 0 by roughly 24 screen
pixels. The measured displacement is **0.46 px**, within the noise of the
classification. No notch, no colour flip, no displacement on the top line.

**What this does NOT establish.**

- **Two triangles, not a scene.** Says nothing about triangle residency or
  about a framebuffer-less streaming rasterizer's architectural limit.
- **Still no 3D, no projection, no transform.** The edge and depth
  coefficients are constants written by hand; the "depth" is an interpolated
  scalar, not a camera-space z from a projection matrix.
- **No shading, no texturing, no antialiasing.** One flat colour per triangle.
- **No host link.** The scene is hardcoded in the top.
- **The y-direction depth gradient is untested by this scene.** Both depth
  planes share the same y gradient, so their difference has no y term and the
  boundary is vertical. That was a deliberate trade for a prediction checkable
  by eye; it means an x-direction depth error would show and a y-direction one
  would not.
- **Single observation**, one monitor, one session. Not an N>=10 result, and
  **not re-confirmed after a deliberate reseat or power cycle** — the §3.9
  bench caveat below still stands and is still outstanding.
- **The bitstream hash is not reproducible.** Rebuilding from the same commit
  produces a different SHA-256: A7 `.bit` files carry a build timestamp in
  their header (measured 2026-09-06 — two builds from byte-identical source
  differed in exactly 3 bytes at offsets 122-125, all configuration data
  identical). The hash above identifies the artifact that was flashed; it
  cannot be regenerated by rebuilding.

**Bench caveat.** Unchanged from §3.9: the harness is hand-wired flying leads
and responds to being touched. On the load this entry measures, the display
came up without prodding, but one clean start is not evidence that the
connection is sound.

**SECOND OBSERVATION — §3.9's outstanding re-confirmation, now closed.** The
board was power-cycled (both USB devices re-enumerated: dirtyJtag bus 1
device 6 -> 9, CH340 5 -> 8, so the cycle is confirmed rather than asserted),
the harness was physically reseated, and the same bitstream was reloaded to
the same `done 1` signature. Configuration is SRAM-only, so the fabric was
genuinely unconfigured in between. The display came up **without prodding**.

Photograph `docs/bench_captures/2026-09-06_two_triangle_depth_vga_obs2.jpeg`,
measured by the same method:

| | boundary as fraction of lit width | scanlines |
|---|---:|---:|
| predicted | 0.5000 | — |
| observation 1, pre power-cycle | 0.5062 | 989 |
| observation 2, post power-cycle + reseat | 0.4986 | 939 |

The two observations bracket the prediction and differ from each other by
0.76% of screen width (4.85 px in 640), which is the difference between two
handheld camera positions, not a change in the design. **Two independent
observations, one of them across a confirmed power cycle and a reseat.**

**The grey shadow reported on the second load: measured, not the design.** The
operator reported a grey shadow beneath the colours. It cannot originate in
the design — one bit per channel through the three-resistor DAC, two flat
colours, and depth never routed to any output. Measurement of the dark region
in the second photograph:

- It is a **smooth gradient**, not a ghost. Luminance rises 37 -> 70 walking
  down the left dark wedge, and the horizontal gradient inside the dark region
  is mean 2.86 and p99 11.0 per pixel. A ghosted or reflected image produces
  localised step edges at the shape boundaries; there are none, and no
  displaced copy of the triangles appears anywhere under a 4x contrast stretch.
- **The black level did not change across the power cycle.** Dark-region mean
  luminance is 33.4 in observation 1 and 36.8 in observation 2, against
  ambient references of 121.8 and 128.6 — the small rise tracks the brighter
  room, not the signal. A degraded return path would have lifted the black
  level markedly and uniformly; it did not.

**Conclusion: LCD backlight bleed and ambient reflection, amplified by a
brighter room and an off-axis view of a tilted panel.** §3.8 and §3.9 recorded
the same panel behaviour ("the background reads black by eye"). This is a
**leading explanation supported by measurement, not a demonstrated cause** —
the discriminating test of loading a different image
(`build/spu_a7_100t_VGAFIX.bit`, the §3.8 colour bars) would settle it and has
not been run.

---

### 3.11 UART receive on F3 — first use of the inbound direction (2026-09-06)

**Date:** 2026-09-06 NZT.
**Board:** QMTech Wukong Artix-7 XC7A100T-FGG676, 50 MHz oscillator.
**Claim:** the FPGA receives UART bytes on pin F3 and echoes them, at 115200
8N1, through the onboard USB-serial bridge.

`spu_a7_100t.xdc` has recorded for months that the bridge's TXD line "is
available on F3, but `spu_a7_top` currently exposes TX only". **This is the
first use of the receive direction on this board.** It is gate step 1 of the
GPU tranche's T1 (`spu_strategy/contract_gpu_pipeline_tranche_2026-09-06.md`),
which requires the link proven in isolation before a triangle loader is
attached to it.

**Source anchor:**

```
commit    757e998  gpu: T1 gate step 1 -- UART RX on F3
bitstream build/spu_a7_100t_UARTLOOP.bit
          3,825,922 bytes
          SHA-256 01b559f46dcc517d9fafba08e63ae44a40a1e43e0e2394e62cf2901a272e3b99
build     A7_FREQ=50 bash hardware/boards/artix7/build_a7.sh 100t uartloop all
load      openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_UARTLOOP.bit
          -> Load SRAM 100%, isc_done 1, isc_ena 0, init 1, done 1
port      /dev/ttyUSB0 at 115200 8N1, raw
```

Post-route: 472/126,800 SLICE_LUTX (0%), 126 SLICE_FFX (0%), `sys_clk`
230.52 MHz against the 50 MHz requirement. Nine cells placed by constraints,
F3 among them.

**Measurements.**

| check | result |
|---|---|
| banner `UARTLOOP:READY` observed with no input | yes, repeating ~1 Hz |
| echo rate, 20 pseudo-random bytes (seed 20260906) | **20 / 20** |
| non-banner bytes emitted in a 3 s quiet window | **0** (3 banners, 0 stray) |

The negative control is the one that matters: a probe emitting bytes
spontaneously would report a receive path that does not exist. Zero stray
bytes means the echo is caused by the input. The 20 probes are random rather
than chosen, and include non-ASCII values, so a terminal-side artifact cannot
account for them.

**The banner is the positive control, not an LED — deliberately.** This same
file records `led_out[3:0]` (V17/W21/Y21/V26) on this unit as a stable,
reproducible I/O anomaly, "closed, not fixed", with the standing instruction
not to trust those pins for a new claim. Liveness is carried on E3, which is
already silicon-proven for that duty.

**A documentation error corrected by this result.** `spu_a7_100t.xdc` and the
bring-up guide describe the onboard bridge as a **CP2102N**. On this unit it
is a **CH340** (USB `1a86:7523`, `/dev/ttyUSB0`); no Silicon Labs device
(`10c4:*`) enumerates at all. The chip name was wrong, not the pin mapping —
E3 and F3 are correct as documented. This cost a diagnostic detour: the
absence of a CP2102N was read as a missing connection, and a Mini-USB cable
was connected in response, when the bridge had been present the whole time.

**What this does NOT establish.**

- **Echo only.** A byte in is a byte out. No framing errors were induced, no
  sustained throughput was measured, and no flow control exists.
- **No triangle loader**, no command decoding, no shadow bank — those are the
  rest of T1 and none of them is built.
- **Single session.** 20/20 within one session is a rate, not a
  reproducibility claim across power cycles or reflashes.
- **`frame_err` from `spu_uart_rx` is not surfaced** anywhere in this probe,
  so a marginal baud match would show as a wrong echoed byte rather than an
  explicit error.

## 2026-09-08 — RP2350 four-node INA226 kernel preflight (performance-only)

Scope: owner-authorised replay of deterministically reconstructed failed INA226
four-node models; no application/promotion gate changed. Not an FPGA comparison
or a complete sensor-stream benchmark.

Device: Pico2 RP2350 A2, chipid `<redacted; see docs/PUBLICATION_REDACTIONS.md>`, identified through BOOTSEL.
Firmware: `hardware/rp2350/spu4_benchmark/baseline.c`, Cortex-M33 Release/-O3,
GCC 16.2.0 / Pico SDK 2.2.0, configured 150 MHz, SRAM execution at 0x20000000.
ELF SHA256 `324d1427d07446c791421d874c440fc213416b914f786e08a30e957a4dd12bbd`.
Full original flash backed up and verified; no flash rewritten and no external
GPIO configured/driven by the benchmark firmware.

Observed: three same-boot batches, each 120/120 exact features/scaling/winner/
distance/label matches. SysTick cycle intervals, min/median/p99/max per batch:
preprocessing 2412/2436/2440/2440; classifier 111/111/111/111; prepared-window
processing through label lookup 2527/2551/2555/2555. All three batches identical.
One-cycle back-to-back read overhead is retained. Each 120-case batch including
setup/checking takes 2262 us by the firmware timer; USB printing happens afterward.

Raw: [MCU preflight JSON](bench_captures/2026-09-08_spu4_rp2350_kernel_preflight.json),
SHA256 `9b8296b5d505ccbd7bb7a7f072125406b97e36d1844bb0f52cc2b327824a734a`.
Methods/limitations: [benchmark record](SPU4_INA226_BENCHMARK_2026-09-08.md).
The 0.740 us classifier interval uses configured 150 MHz, not an independently
calibrated oscillator measurement. Excludes acquisition, model/window copying,
stream scheduling, transport and session vote. No background-load, cold-start,
worst-case latency, energy, throughput or comparative architecture claim.

## 2026-09-09 — Tang bench25 completion-arm probe: physical parity halt

Scope: one owner-authorised probe-consumer correction preventing a stale
level-held `done` from completing the next accepted query. Classifier RTL,
wrapper, model, fixtures, clocking and UART semantics were frozen.

Pre-hardware evidence: both consumer simulation profiles passed 50/50 checks;
the registered repository gate passed 227/227. Fresh Tang P&R passed 25 MHz
with 35.02 MHz routed Fmax, +11.45 ns setup slack, no hold/min violation and
zero timing errors. Build evidence is in
`build/spu4_ina226_benchmark/bench25_completion_arm/`; packed image SHA-256 is
`7a57be49d6164d838cd9ba49b9e13a1feb64f250312378a425bf237622dc448b`.

Physical observation: SRAM load succeeded; fresh UART boot output contained
hydration `SOM:H ... S=04 ...`. The first frozen fold-0 request returned one
valid fresh-completion line with `L=006`, establishing that the stale `L=000`
symptom did not recur on that query. However, its node/distance was node 3 /
71,515,812 versus expected node 2 / 63,278,740. The required exact-parity gate
therefore failed and the run stopped before a second query or any performance
measurement.

This is **not** evidence of benchmark performance or architectural advantage.
It is a physically observed consumer-latency repair accompanied by an
unresolved classifier-parity failure. Raw captures:
`bench_captures/2026-09-09_spu4_completion_arm_boot.json` and
`bench_captures/2026-09-09_spu4_completion_arm_fold0_acceptance.json`.

## 2026-09-21 — T1d visual-only prepared-scene observation

This is a separate operator-observed hardware result. It does not close the
original D3 telemetry requirement and must not be used as internal UART,
payload-CRC, loader, or activation evidence.

Frozen artifact:

```text
bitstream = build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
bitstream_sha256 = 52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914
sender_commit = c8895e9
sender_blob_sha256 = 7310a1a9f505a215a26082f1928963a96054a1e4552b96d0dba72a777fd110a1
fixture_sha256 = aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee
uart = 115200 8N1, frozen 64-byte transaction
```

The initial transaction produced the expected dual-triangle image. After the
frozen warm-reset sequence and operator confirmation of the black/unarmed
state, the repeat transaction produced the same expected dual-triangle image.
Both host transactions wrote 64 bytes and completed `tcdrain`; the CH340
preflight remained stable with no recorded host events.

Evidence:

* `build/d3_visual_observation_20260921/uart_recovery_amendment_01/preflight.json`
* `build/d3_visual_observation_20260921/uart_recovery_amendment_01/transcript.json`
* `build/d3_visual_observation_20260921/visual_repeat_02/repeat_record.json`
* `build/d3_visual_observation_20260921/visual_repeat_02/transcript.json`
* `spu_strategy/contract_gpu_t1d_visual_observation_2026-09-21.md`

Classification: **PASS (operator-observed, visual-only)**. No camera raw-image
files or image SHA-256 values were produced. Original D3 remains **HALTED**
with `INFRASTRUCTURE FAIL — FX2 sustained-stream limitation`.

## 2026-09-23 — T1g bounded temporal scene replacement

**Scope:** Physical A→B→C scene replacement on the Wukong Artix-7 100T using
the T1g prepared-scene candidate/active banks and the frozen Q1 host pacing.

**Bitstream:**

```text
source snapshot commit = a64d87c7ae0d96b44d8178c20f2421376a975ac0
artifact = build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
SHA-256 = e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5
load = openFPGALoader -c dirtyJtag --freq 1000000 \
       build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit
result = Load SRAM 100%, isc_done 1, init 1, done 1
```

After a board power cycle, the FPGA was detected as XC7A100 (`idcode
0x3631093`) and the bitstream loaded successfully. The host then sent the
frozen 127-byte A, B, and C fixtures in order at 115200 8N1, with a 20 ms
post-drain delay, 3-second scene dwell, and a 31.1 ms minimum start-to-start
bound. The recorded gaps were 3006.081843 ms and 3005.912119 ms. All writes
completed `tcdrain`; transcript:
`build/t1f_clean_qualification_20260922/build/t1g_h1_20260923/uart_sequence_attempt_03.json`.

**Operator observation:** both scene changes were visible on the monitor; the
operator reported that the prior yellow shimmer was absent in this run. During
troubleshooting, the analyzer was found on the wrong PMOD; earlier captures
from that connection are excluded. Correcting the PMOD connection restored
the VGA display.

**Classification:** **PASS (operator-observed, visual-only)** for the bounded
A→B→C hardware demonstration. This is not a captured-pixel proof of every
transition frame. The no-mixed-scene pixelwise result remains the simulation
Q2 evidence recorded in the T1g contract. No general streaming or arbitrary
back-to-back delivery claim is made.

### 3.13 — T1h scalar threshold visualization (2026-09-23)

**Scope:** Physical demonstration that the prepared four-primitive scene
loader, selected scalar, and scalar-to-display diagnostic change together for
the frozen A/B/C scenes. The diagnostic renders the selected scalar's
`[14:11]` bits to grayscale; the one-bit-per-channel VGA board output makes
the visible levels black and white at the scalar bit-14 threshold (16384).

**Source and image:**

```text
source HEAD at build = 8ea3bc2abeaff97dac5b01ed558ee96008788340
source tree = dirty; exact build-time status is recorded in
  build/t1h_gpu_attributes_20260923/b1_scalar_diag_01/git_status.txt
artifact = build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit
SHA-256 = ec600abe73e847f0846bff5429813cc6913a343b235e215cab5298ebb5d126dd
load = openFPGALoader -c dirtyJtag --freq 1000000 \
       build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit
result = Load SRAM 100%, isc_done 1, init 1, done 1
```

The host sent the frozen A/B/C/A transactions at 115200 8N1. Every
151-byte write completed `tcdrain`; the host waited three seconds between
scenes, exceeding the frozen 20 ms post-drain minimum. Recorded start-to-start
gaps were 3008.766143 ms, 3008.735051 ms, and 3008.739499 ms. Transmit
evidence:

* `build/t1h_gpu_attributes_20260923/h1_abca_sequence.json`
* `build/t1h_gpu_attributes_20260923/h1_scene_a.json`
* `build/t1h_gpu_attributes_20260923/h1_scene_b.json`
* `build/t1h_gpu_attributes_20260923/h1_scene_c.json`
* `build/t1h_gpu_attributes_20260923/h1_ac_toggle.json`
* sender: `tools/send_gpu_t1h_sequence.py`, SHA-256
  `11b8ba229536d2ad454cf1f15615522d8f5f23174f1ceaad155183c1068e50de`

**Operator observation:** the monitor showed the black/white scalar pattern
change for B and C, then return to A. The operator reported that the A/C
eight-pixel translation was visible. A purple shimmer appeared along the left
vertex edge; it followed the vertex line pattern and remained confined to the
geometry edge. The diagnostic RTL drives R/G/B from the same scalar bit, so
purple is not an intentional scalar color. Its physical/display cause remains
unresolved. The operator supplied one monitor photo; it shows the expected
bright-right/dark-left threshold split and the purple vertex-edge line. This
is a visual record, not a raw VGA frame capture:
`build/t1h_gpu_attributes_20260923/h1_scalar_threshold_photo.jpeg`
(SHA-256 `a0afe136711a6acd02cd91c000b9c394663f6fbebb161b5dba7a3f06a07c757d`).

**Classification:** **HOLD — edge artifact audit**. The operator-observed
pattern change supports physical scalar threshold visualization and bounded
A/B/C/A scene replacement, but H1 is not accepted while the geometry-aligned
purple edge remains unexplained. This does not establish captured-pixel
equality or full scalar numeric accuracy on hardware; the independent
integer-oracle result remains simulation evidence, not a captured hardware
frame.

**Focused simulation audit (2026-09-23):** the T1h regression checks 715
samples in the lower-vertex neighborhood across A/A/B/C/A. All twelve edge
accumulators per sample match independent edge equations; coverage masks,
depth winner, selected scalar, diagnostic RGB, and final VGA RGB match their
oracles. Pixels outside coverage produce black at the final VGA outputs in
these samples. This rules out a coverage leak or invalid-scalar RGB leak in
the sampled RTL simulation region; it does not identify the physical purple
edge cause. H1 remains on hold. Run with
`python3 software/tests/test_gpu_t1h_attribute.py`.

**Depth-winner seam analysis (2026-09-23):** Scene A's four primitive edge
sets are identical, so all four triangles overlap exactly. The integer oracle
finds 117 pixels where multiple covered lanes share the nearest depth. At
`(39,41)`, lane 2 wins; at `(40,41)`, lanes 2 and 3 tie at depth 58 and the
fixed lower-ID rule selects lane 2; at `(41,41)`, lane 3 wins. At `(40,40)`
all four depths tie and lane 0 wins. The new second-A-frame pass shows the
same winner and scalar at every sampled pixel in both consecutive A frames.
This supports a stable depth-winner boundary at the black/white transition,
not temporal z-fighting in the tested RTL simulation. It is a plausible source
of the high-contrast physical fringe, but the purple appearance is unresolved.

A follow-up FX2 logic-analyzer attempt requested 1,000,000 samples at 48 MHz
on J10 RGB and hsync but returned only 10,240 samples (about 0.213 ms, or
6.7 scan lines). D0–D2 remained black and D3 showed hsync pulses, so the
capture was from a blank portion of the frame and did not include the triangle
edge. The capture is retained at
`build/t1h_gpu_attributes_20260923/rgb_pin_capture_01/vga_rgb_hsync.sr`
(SHA-256 `41f35997cbf7882d467643bf6df3f87d6aebaf500ba03b1f379bab3a257177bb`).
It is inconclusive and does not change the H1 HOLD classification.

### 3.14 — T1i interpolated U/V physical diagnostic (2026-09-24)

**Scope:** Physical observability of the T1i winner-selected U/V values through
the compile-time binary diagnostic. The display maps `U[14]` to red,
`V[14]` to green, and blue to zero; expected covered classes are black, red,
green, and yellow. This is a diagnostic pattern observation, not exact
per-pixel U/V correctness on silicon.

**Build:** Source commit at build was
`8ea3bc2abeaff97dac5b01ed558ee96008788340`; the tree was dirty and the exact
status is recorded in
`build/gpu_t1i_hw_uv_diag_20260924_b1_01/git_status.txt`. Artifact:
`build/spu_a7_100t_GPUVGA_T1I_UV_DIAG_B1_S1.bit`, SHA-256
`ccfa2b883a5ee1e30da52afdfa7b122a4a288e64b1730ecc59df788d1ad5b92e`. The
detached build result is `COMPLETE` (exit 0). Routed `clk_pixel` timing was
35.23 MHz against 25 MHz; utilization was 31% LUT, 12% flip-flop, 7% CARRY4,
2% DSP48E1, and zero block RAM. Full synthesis and routing logs are retained
under `build/gpu_t1i_hw_uv_diag_20260924_b1_01/` and the adjacent named
nextpnr artifact.

The board was detected as XC7A100 (`idcode 0x3631093`). The diagnostic image
was loaded using
`openFPGALoader -c dirtyJtag --freq 1000000`; the result was `Load SRAM 100%`,
`isc_done 1`, `init 1`, and `done 1`. The frozen T1i A/B/C/A 175-byte packets
were sent at 115200 8N1 through `/dev/ttyUSB0`. Each write completed
`tcdrain`; the 3-second-dwell start-to-start gaps were 3011.583114 ms,
3011.703550 ms, and 3011.457002 ms. Sender and transcript:

* `tools/send_gpu_t1i_sequence.py`, SHA-256
  `c227b38053cea29ea6c109aa91e986d0cad4c207284a6b5d561f030fc7455d74`
* `build/gpu_t1i_hw_uv_diag_20260924_b1_01/h1_abca.json`, SHA-256
  `e4f24c71c1748eaa55dd6a0ee8f25435ff81dd586310df35f1cf4eb055d93e60`

**Operator photo:** `build/gpu_t1i_hw_uv_diag_20260924_b1_01/IMG_1743.jpeg`,
SHA-256 `e31a002fc5f77d2876505e31c5e61bf2f202e07d227f27815024ff93985b1f51`.
It shows broad red/green regions and yellow edge pixels, along with a detached
red fragment and dotted green line above the main shape. The operator reports
that ghosting lines remain.

**Classification:** **HOLD — ghosting visible.** The photo establishes that
the broad diagnostic colors are physically visible, but the ghosting prevents
accepting H1 as a clean physical demonstration. The image does not establish
whether the pattern changed for B and C and returned to A, and it is not a
captured-pixel oracle. The ghosting cause is not identified; no interpolation
or coverage correction is justified by this evidence. T1i remains
simulation-qualified for exact U/V interpolation. Its prior Q3 full-repository
gate result remains FAILED on the unrelated T1D timeout and was not rerun.

### 3.15 — Registered T1i U/V output divergence replay (2026-09-24)

**Scope:** Experimental physical discriminator for the previously observed
history-dependent broad color change. The image registers the winner-selected
56-bit U/V values and validity, then maps `U[14]` to red and `V[14]` to green;
sync and active are delayed by the same stage. This observation does not
establish exact per-pixel U/V correctness on silicon.

**Build:** The bounded detached Artix build completed successfully (exit 0,
1390 seconds) in
`build/gpu_t1i_uv_divergence_hw_20260924/build_01`. Artifact
`build/spu_a7_100t_GPUVGA_T1I_UV_REG_DIAG_B1_S1.bit`, SHA-256
`3bd663e65db659ddfa7dcc4b71082c1a490927ccf4d1994cf07d14f2aaeed376`.
The artifact was loaded to SRAM using
`openFPGALoader -c dirtyJtag --freq 1000000`; it reported `Load SRAM 100%`,
`isc_done 1`, `init 1`, and `done 1`.

The frozen 175-byte A -> B -> C -> A packets were sent at 115200 8N1 through
`/dev/ttyUSB0`; each write completed `tcdrain`. Per-scene transcripts are
`h1_scene_a_initial.json`, `h1_scene_b.json`, `h1_scene_c.json`, and
`h1_scene_a_return.json` in the build evidence directory. Scene B photo
`scene_b_operator_capture.jpeg` (source workspace name `IMG_1752.jpeg`),
SHA-256 `d761b93eee76ade1847a66b4c8d729df339ea51f8cc04372e2daeef491cdcc6d`;
Scene C photo `scene_c_operator_capture.jpeg` (source workspace name
`IMG_1754.jpeg`), SHA-256
`b4370196f7ab2c861f8cecde72c94fe068ac1a8578ae2d79225f73a6613144f6`.
Initial-A and return-A assessments were operator-reported without photos in
this record.

**Observation:** Initial A was reported red-left/green-right with a small red
artifact above. Scene B showed red and green regions with yellow overlap at
the left triangle and the red artifact above. Scene C showed a broad
yellow-left/green-right triangle with a red region above. On return A, the
operator reported that the broad red-left/green-right regions appeared to
match initial A; the small artifact remained visible.

**Classification:** The broad history-dependent color change seen on the
original combinational U/V diagnostic was not reproduced in this registered
U/V replay. Together with the identical committed U/V tuples/re-anchor state
and production-timing oracle results, this supports output settling/alignment
as a contributor to that broad color instability. This is operator-observed
evidence, not captured-pixel proof. The small detached red artifact remains
unresolved and is tracked separately; this run did not remove or explain it.
No interpolation, coverage, depth, or winner correction is justified. The
contingency second build from the divergence campaign was not used.

### 3.16 — T1i post-winner output register hardening (2026-09-24)

**Scope:** Physical observation of the compile-time `GPU_POST_WINNER_REG=1`
diagnostic profile after registering final RGB and aligned hsync/vsync/active.
The profile leaves coverage, depth, winner selection, U/V interpolation,
scene activation, and packet semantics unchanged. The display diagnostic
maps winner-selected U/V to red/green; it is not exact per-pixel silicon
verification.

**Simulation gate:** The detached 640x480 A/B/C/A production-timing replay
completed with exit 0 and exactly one `COMPLETE` marker at
`build/gpu_post_winner_output_register_20260924/prod_timing_run_01`. Its
32,000 ROI samples matched the independent U/V oracle.

**Build:** Source commit `8ea3bc2abeaff97dac5b01ed558ee96008788340`; the
dirty source snapshot is recorded in
`build/gpu_post_winner_output_register_20260924/build_01/git_status.txt`.
The detached Artix build completed in 1626 seconds with exit 0 in
`build/gpu_post_winner_output_register_20260924/build_01`. Artifact
`build/spu_a7_100t_GPUVGA_T1I_POST_WINNER_REG_DIAG_B1_S1.bit`, SHA-256
`f782a18ad2ee78928ddae05eb341094655815180fdd019ea3826a07610925640`.
It was loaded using `openFPGALoader -c dirtyJtag --freq 1000000`; load
reported 100%, `isc_done 1`, `init 1`, and `done 1`.

The frozen T1i A/B/C/A 175-byte packets were sent at 115200 8N1 through
`/dev/ttyUSB0`. Each write completed `tcdrain`; individual transcripts are
`h1_scene_a_initial.json`, `h1_scene_b.json`, `h1_scene_c.json`, and
`h1_scene_a_return.json` in the build evidence directory.

**Operator observation:** Initial A was a red-left/green-right triangle with
a small red artifact above. B was reported as matching `IMT_1748.jpeg`. C
was yellow-left/green-right with a red artifact above. Return A matched the
initial A broad red-left/green-right regions. The small red artifact remained
visible. No photos were supplied for this replay; observations are
operator-reported, not captured-pixel measurements.

For ordinary RGB sanity, the already-qualified T1g bitstream
`build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit`
(SHA-256
`e16dc6992c60de99d9d5f9d5a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`)
was loaded and its 127-byte T1f Scene A packet sent. The operator reported a
normal triangle with no phantom vertices. The existing image was reused; no
additional build was consumed.

**Classification:** **PASS (operator-observed, visual-only)** for the bounded
diagnostic A/B/C/A broad-region change and return-A match, plus ordinary T1g
RGB sanity. The broad history-dependent color shift was not reproduced with
the post-winner register. The detached red artifact remains unresolved and
outside this pass. No exact physical pixel correctness is claimed. The
second build slot remains unused.

### 3.17 — T1j procedural checker: timing-qualified build and H1 visual pass (2026-09-25/26)

**Simulation:** The production 640x480 A/B/C/A checker oracle passed all
1,228,800 frame-pixel comparisons. Exact per-pixel checker correctness remains
a simulation/oracle claim.

**Build:** Source commit `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`; the
build tree was dirty and the launch-time status is preserved in
`build/gpu/t1j_b1_timing_fix_20260925/run_01/git_status.txt`. The Artix-7 100T
route closes at 27.82 MHz for `clk_pixel`, above the 25 MHz constraint. The
detached job completed with exit 0 in 1239 seconds. Artifact
`build/spu_a7_100t_GPUVGA_T1J_PROC_CHECKER_B1_S1.bit`, SHA-256
`a2e7eaa2a5a4997d7e6ac416e82b6e07d72489c1ecbf08a84b00b638e3576526`.
Post-route metrics:
`build/metrics/artix7_100t_GPUVGA_T1J_PROC_CHECKER_B1_S1.md`.

**Programming and transport:** The board was detected as XC7A100
(`idcode 0x3631093`). The exact artifact loaded to SRAM and reported `Load
SRAM 100%`, `isc_done 1`, `init 1`, and `done 1`. Frozen T1i A/B/C/A packets
were sent at 115200 8N1 over `/dev/ttyUSB0`; all four 175-byte writes
completed `tcdrain`. The start-to-start gaps were 3011.43, 3011.49, and
3011.40 ms, exceeding the frozen 20 ms post-drain minimum. Transcript:
`build/gpu/t1j_h1_20260925/uart_sequence.json`.

**Operator observation:** The operator first reported “image unstable or
artifact visible,” then described “a series of broken triangles with edges
clipped.” The operator confirms that photo `IMG_1760.jpeg` shows final A and
that B/C visibly changed. In a follow-up on 2026-09-26, the operator
confirmed that the black/white checker cells themselves changed for B/C and
that final A matched initial A. Photo `IMG_1760.jpeg` (workspace name; SHA-256
`2b5b38765d4c14d68c77f673c7ecd90b1fdec661594acdeeb56d3b6199cb1a11`) shows
three pale triangle-shaped regions with apparent gaps. The photo alone does
not classify those gaps as clipping: black checker cells and uncovered
background both render black, so the checker can blend into the background.

**Classification:** **PASS (operator-observed, visual-only)** for the bounded
A/B/C/A checker demonstration: the cells changed for B and C, then final A
matched initial A. Exact per-pixel checker correctness remains a
simulation/oracle claim. Record the apparent silhouette gaps as unclassified;
black-cell/background aliasing is a plausible explanation. The next
discriminator is a two-visible-color checker mapping (checker zero blue,
checker one white, uncovered black) with raster, U/V, depth, winner, and
checker semantics unchanged. The earlier detached artifact remains a separate
unresolved observation. No raster RTL correction is justified by this result.

### 3.18 — T1j two-visible-color checker diagnostic: production oracle and routed build (2026-09-26)

**Purpose:** Distinguish covered black-checker cells from uncovered black
background. The diagnostic renders covered checker-zero pixels blue,
checker-one pixels white, and uncovered pixels black. Coverage, depth winner,
U/V interpolation, checker predicate, scene activation, and register stages
are unchanged.

**Simulation:** The independent production-timing A/B/C/A oracle passed
1,228,800 pixels. It checked the complete color tuple against independently
computed coverage, depth winner, and U/V; both checker colors were present in
each winning lane; return-A matched initial A; and video control alignment
passed. Evidence:
`build/gpu/t1j_checker_visibility_q1_20260926/production_oracle/`.

**Build:** The first authorized launch omitted profile environment variables
from the detached command and failed in one second; it produced no timing
result. After the owner authorized a renewed attempt, the profile variables
were passed through `env` after the runner's `--`. That build completed with
exit 0 in 987 seconds. Routed `clk_pixel` Fmax is **25.94 MHz** against the
25.00 MHz constraint. Full metrics:
`build/metrics/artix7_100t_GPUVGA_T1J_CHECKER_VIS_DIAG_B1_S1.md`.
The exact SRAM-loadable bitstream is
`build/spu_a7_100t_GPUVGA_T1J_CHECKER_VIS_DIAG_B1_S1.bit`, SHA-256
`5c7ea46db4eb3ec8080f45ad33fa6f113a10cd783b382a604654483ad50a0127`.

**Programming and transport:** The exact bitstream was loaded to the XC7A100
with `openFPGALoader -c dirtyJtag --freq 1000000`; it reported `Load SRAM
100%`, `isc_done 1`, `init 1`, and `done 1`. The frozen A/B/C/A transactions
were sent over `/dev/ttyUSB0` at 115200 8N1; all 175-byte writes completed
`tcdrain`, with start-to-start gaps of 3011.60, 3011.48, and 3011.52 ms.
Transcript: `build/gpu/t1j_checker_visibility_h1_20260926/uart_sequence.json`.

**Operator observation:** Photo `IMG_1767.jpeg` (SHA-256
`ae2da46bd6a321aaece3a5ea5b491060c4b6c7e62671ed393a6d26d9bd8f6e89`) shows
blue and white regions filling the triangle-shaped scene against black,
without the apparent gaps in the earlier black/white capture. No detached
colored fragment is apparent in this photo.

**Classification:** **B1 PASS; H1 PASS (operator-observed, visual-only).** The
two checker states are visibly distinct and their combined silhouette appears
filled against the black background. The apparent clipping in the earlier
black/white image is resolved as a visualization artifact: black covered
fragments were indistinguishable from the black background. The two-visible-
color diagnostic shows those regions as procedurally shaded cells rather than
clipped raster coverage. Exact physical pixel correctness remains a
simulation/oracle claim. The earlier small detached red artifact remains a
separate unresolved observation.

### 3.19 — T1k U/V grid: post-refactor routed build and H1 observation (2026-09-26)

**Simulation:** The post-refactor independent production-timing A/B/C/A grid
oracle passed all 1,228,800 pixels:
`build/gpu/t1k_post_refactor_20260926/production_oracle/run_01/`.

**Build:** The original T1k route failed at 24.08 MHz and was not programmed.
After the documented `spu_depth_dispatch4` operand-tuple staging refactor, the
owner-authorized build completed with exit 0 in 850 seconds. Final routed
`clk_pixel` Fmax is **27.01 MHz** against the 25.00 MHz threshold (the earlier
23.75 MHz route in the same build was superseded by the final route). Metrics:
`build/metrics/artix7_100t_GPUVGA_T1K_UV_GRID_B1_S1.md`. Exact bitstream:
`build/spu_a7_100t_GPUVGA_T1K_UV_GRID_B1_S1.bit`, SHA-256
`925782d94f2cb914c271fd4861df1f22adbf175f3b4bb11b663f043c1168b7d2`.

**Programming and transport:** The exact image was SRAM-loaded using
`openFPGALoader -c dirtyJtag --freq 1000000`; SRAM reached 100%, with
`isc_done=1`, `init=1`, and `done=1`. Frozen A/B/C/A fixtures were sent over
`/dev/ttyUSB0` at 115200 8N1. All 175-byte writes completed `tcdrain`; scene
start gaps were 3011.36–3011.59 ms. Transcript:
`build/gpu/t1k_post_refactor_h1_20260926/uart_sequence.json`.

**Operator observation:** The operator reports: “Grids changed, perfect
diamond shaped chequers.” Photo `IMG_1768.jpeg` (SHA-256
`a9881b5b3d419cd03d40df50a0e2dbdc7ab96dec39c2b8cf46e0e70adadf56f3`) shows a
high-contrast white diamond/grid pattern against black. Confirmation of
final-A return equality was operator-confirmed after the full sequence. No
detached artifact or phantom vertex is apparent in this image.

**Classification:** **B1 PASS (27.01 MHz); H1 grid visibility PASS,
operator-observed, visual-only; final-A matched initial A.** The increase
from the original 24.08 MHz route to 27.01 MHz after dispatch tuple staging is
consistent with the dispatch/setup path diagnosis, though route-to-route timing
alone does not prove sole causation. Exact physical pixel correctness remains a
simulation/oracle claim. No full repository-gate claim is made here.

### 3.20 — T1l U-stripe pipeline partition: production oracle, routed build, and bounded H1 (2026-09-27)

**Simulation:** The independent production-timing U-stripe oracle passed
1,228,800 A/B/C/A pixel comparisons, including exact return-A equality:
`build/gpu/t1l_pipeline_partition_20260927/production_oracle/run_01/`.

**Build:** The exact `T1L_MATERIAL_OP=3`,
`T1L_PIPELINE_PARTITION=1`, `GPU_POST_WINNER_REG=1` image completed the
Artix-7 100T route at **40.03 MHz** against the 25.00 MHz requirement. Metrics:
`build/metrics/artix7_100t_GPUVGA_T1L_PIPELINE_PARTITION_B1_S1.md`. Bitstream:
`build/spu_a7_100t_GPUVGA_T1L_PIPELINE_PARTITION_B1_S1.bit`, SHA-256
`79c9de8fab4a9c40bbc3be845b0a4d2c124279b0704acd76d18aa85e52fe7040`.

**Programming and transport:** The exact bitstream was SRAM-loaded to the
Wukong XC7A100; `openFPGALoader` reported `isc_done=1`, `init=1`, and `done=1`.
The frozen 175-byte A/B/C/A scene sequence was sent over `/dev/ttyUSB0` at
115200 8N1. All writes drained. Latest transcript:
`build/gpu/t1l_pipeline_partition_20260927/h1_repeat_sequence.json`.

**Operator/photo evidence:** Photos are archived under
`docs/bench_captures/t1l_h1_2026-09-27/`. `IMG_1769.jpeg` is initial A,
`IMG_1770.jpeg` is B, and `IMG_1771.jpeg` is return A. Scene C was observed
but not photographed. The operator reported C looked similar to initial A and
return A looked slightly different from initial A. The photo comparison shows
the same two broad white regions; the differences are consistent with camera
framing and brightness. The photos do not resolve the internal U-stripe bands
clearly enough to confirm their physical correspondence.

**Classification:** **B1 PASS; production oracle PASS. H1 PASS for broad
return-A pattern repeatability at operator/photo-comparison level; physical
U-stripe visibility/correspondence INCONCLUSIVE.** Exact A/B/C/A return
equality is a simulation-oracle result and is not claimed as per-pixel silicon
evidence. T1l is closed at this evidence boundary; no RTL change, packet
investigation, or further FPGA build/replay is justified by this result.

### 3.21 — T1m deterministic Boolean fragment ALU: production oracle, routed build, and bounded H1 (2026-09-27)

**Simulation:** The reduced independent oracle passed all six compile-time
operators over 32,000 A/B/C/A pixels per operator. The production XOR oracle
passed all 1,228,800 pixels, including invalid-black gating, both valid color
classes, all four depth-winner lanes, output/control alignment, scene changes,
and exact return-A equality. Focused T1l/T1k/T1j/T1i/T1h/T1g/depth-output
regressions also passed. The full repository gate was not completed; this is
not treated as T1m qualification evidence. Contract:
`spu_strategy/contract_gpu_t1m_fragment_alu_2026-09-27.md`.

**Build:** The exact prepared four-lane T1m XOR profile completed the
Artix-7 100T route at **30.27 MHz** for `clk_pixel`, above the 25.00 MHz
threshold. The detached job completed with exit 0 in 2294 seconds. Metrics:
`build/metrics/artix7_100t_GPUVGA_T1M_FRAGMENT_ALU_B1_S1.md`. Bitstream:
`build/spu_a7_100t_GPUVGA_T1M_FRAGMENT_ALU_B1_S1.bit`, SHA-256
`d3627d3f978a536e7e2f1980b45d9fabeb333d1662ca6f34b07a2691d554ef5f`.
The critical path runs from `partition_cov_q[0]` through the four-lane depth
comparator/winner selection to the `partition_selected_v[12]` register; it
reports 4.8 ns logic and 28.2 ns routing. The T1m ALU is downstream of that
path. Compared with T1l, the route is 9.76 MHz slower, with +8 LUTs and +5 FFs;
CARRY4, SELMUX2_1, and DSP48E1 counts are unchanged.

**Programming and transport:** The exact image was loaded to Wukong XC7A100
SRAM with `openFPGALoader -c dirtyJtag --freq 1000000`; it reported
`isc_done=1`, `init=1`, and `done=1`. The frozen 175-byte A/B/C/A fixtures
were sent over `/dev/ttyUSB0` at 115200 8N1 with 3-second dwell and the
20 ms minimum post-drain delay. All writes completed `tcdrain`; the observed
repeat-run start-to-start gaps were 3011.513228, 3011.368875, and 3011.495094
ms. Transcript:
`build/gpu/t1m_fragment_alu_20260927/h1_abca_repeat_01.json`, SHA-256
`0887a8f667c0eb70da595cf453a8353c6fe61ef59cb52819d54d051682e6c933`.

**Operator observation:** The operator reported that the blue/yellow pattern
changed for B and C and returned to A. No photo was supplied, so the record is
limited to this operator-observed broad visual behavior; exact pixel
correctness remains a simulation/oracle claim.

**Classification:** **B1 PASS; H1 PASS (operator-observed, visual-only).**
The bounded T1m material pattern was observed changing across A/B/C/A and
returning to A. No claim is made about per-pixel silicon correspondence.

### 3.22 — T1n runtime material opcode: oracle, routed build, and bounded H1 (2026-09-28)

**Simulation:** The reduced independent oracle exercised all six legal
runtime opcodes and matched 224,000 pixels. The production oracle matched all
1,228,800 pixels for `A(PASS_U) -> B(PASS_V) -> C(XOR) -> A(PASS_U)`, including
invalid-black gating, all four depth-winner lanes, opcode/generation alignment,
invalid-opcode rejection and recovery, and exact return-A equality. Contract:
`spu_strategy/contract_gpu_t1n_runtime_material_opcode_2026-09-27.md`.

**Build:** The exact prepared four-lane T1n profile completed the Artix-7 100T
route at **43.68 MHz** for `clk_pixel`, above the 25.00 MHz requirement. The
successful detached run completed with exit 0 in 970 seconds. Metrics:
`build/metrics/artix7_100t_GPUVGA_T1N_RUNTIME_MATERIAL_B1_S1.md`. Bitstream:
`build/spu_a7_100t_GPUVGA_T1N_RUNTIME_MATERIAL_B1_S1.bit`, SHA-256
`7b3bf1ada1b471d34bb3db76fc2964b954a84b816119fe533d58fa49246f85bc`.

**Programming and transport:** The exact image was loaded to Wukong XC7A100
SRAM with `openFPGALoader -c dirtyJtag --freq 1000000`; programming reached
100% and reported `ISC_DONE=1` and `DONE=1`. The frozen runtime-opcode sequence
was sent through the CH340 UART at 115200 8N1. Each transaction contained the
175-byte T1i fixture followed by its one-byte T1n opcode. All four 176-byte
writes completed `tcdrain`; start-to-start gaps were 5011.503685,
5011.601794, and 5011.538406 ms. Transcript:
`build/gpu/t1n_runtime_material_20260927/h1/sequence_02.json`, SHA-256
`d5408941358dd2d3e7c6447328384bb2ea907627d5f81f8e4f2880a45438bebc`.

**Operator observation:** The operator confirmed that the displayed image
changed through the sequence and returned to A, and reported that the
checkerboards were distorted. The final fixed-scene `PASS_U` return state is
shown in `docs/bench_captures/t1n_h1_2026-09-28/IMG_1774.jpeg`, SHA-256
`5d27b215fc810b102aa09b0a931e606ec2e374bafa48ea2f348aac94807e0780`.
The photo shows a blue/yellow triangular pattern against black. It records the
final state only and does not independently establish the preceding opcode
transitions or per-pixel correspondence.

The fixed A scene was then sent with only the opcode changed to `PASS_V`.
Transcript:
`build/gpu/t1n_runtime_material_20260927/h1/photo_pass_v_01.json`, SHA-256
`444a4f8d04235260ffd870d8e45b2aef46013a3097674f5d822644f1203383db`.
Photo `docs/bench_captures/t1n_h1_2026-09-28/IMG_1775.jpeg`, SHA-256
`ca35f268d835939485466c7cb3fc846d7a96a69b213aee10bc15e0fdd72ba065`,
shows a visibly different blue/yellow partition within a comparable triangle
silhouette and screen position. A subsequent fixed-scene `XOR` write completed
with transcript:
`build/gpu/t1n_runtime_material_20260927/h1/photo_xor_01.json`, SHA-256
`6e8fa8e71eaed1fba1dd3662e2cc064312c0ff199a3dc3e6d33b9f4fd8c2150c`.
Photo `docs/bench_captures/t1n_h1_2026-09-28/IMG_1776.jpeg`, SHA-256
`3cbab9b04abab6a79c92270ec1c6e11768c99c85e706c1d34fdf3dff4d762489`,
shows a third visibly distinct blue/yellow partition with the same overall
triangular scene. The board was then returned to fixed-scene `PASS_U`; that
write completed `tcdrain`. Transcript:
`build/gpu/t1n_runtime_material_20260927/h1/photo_return_pass_u_01.json`,
SHA-256
`5e118815bf787aae327bbbf94cdce4f551599f32f8a6838649190c994d425392`.
The three photos directly document visually distinct physical output for the
three isolated opcode values. They do not establish exact pixel-level oracle
agreement.

**Photo/oracle shape comparison:** Independent 640x480 renders for the exact
fixed A fixture and the three opcodes are archived beside the photos as
`oracle_fixed_a_pass_u.png`, `oracle_fixed_a_pass_v.png`, and
`oracle_fixed_a_xor.png`. Their SHA-256 values are, respectively,
`8dc38d82628121a057a6910871af674cda0d3b6840dbc94bac6b2ea3302f2200`,
`27771b8bc78d8d538132a3fcfad0e4d406e6049a30190ba926535e8bbc3fd903`,
and `109278920c52f69d897b69597d2b92512544625856ce45d91570600a75530923`.
Each photo has the same broad blue/yellow region topology as its corresponding
oracle render, allowing for camera perspective, crop, and display photography.
The reported “distorted checkerboards” are the expected coarse regions from
testing interpolated U/V bit 12; this sequence is not a regular square-grid
material. This is visual shape agreement, not exact pixel comparison.

**Non-vacuity follow-up:** The A/B/C/A replay changed geometry and U/V records
with the opcode, so its visible changes cannot isolate physical opcode
response. A follow-up held the complete A fixture constant and changed only
the final opcode byte: `PASS_U -> PASS_V -> XOR -> PASS_U`. All four writes
drained, with start-to-start gaps of 5011.656113, 5011.684550, and 5011.766513
ms. Transcript:
`build/gpu/t1n_runtime_material_20260927/h1/opcode_isolation_01.json`, SHA-256
`403232b4cfc63517eb6d91e7e03e662111bf4d1f20033ef943b76dd5cc9b6320`.
The operator confirmed three visibly different patterns for `PASS_U`,
`PASS_V`, and `XOR`, followed by return to the first `PASS_U` pattern.

**Classification:** **B1 PASS (43.68 MHz); H1 opcode-isolation PASS; broad
photo/oracle shape agreement PASS (visual-only).** The fixed-scene follow-up
establishes physical response to the isolated runtime opcode byte and return
behavior. The three photographed patterns agree with the oracle at the broad
region-topology level. Exact per-pixel physical equality remains unmeasured and
is still a simulation-oracle claim.

### 3.23 — T1o per-primitive runtime material: route, bitstream, and transport (2026-09-28)

**Simulation:** The independent production oracle matched 1,228,800 pixels
across the fixed Scene A geometry/U/V and the A/B/C/return-A opcode sequence.
The renewed repository gate passed. Contract:
`spu_strategy/contract_gpu_t1o_per_primitive_runtime_material_2026-09-28.md`.

**Build:** The seed-1 Artix-7 100T route passed the 25.00 MHz threshold at
35.42 MHz for `clk_pixel` and 195.05 MHz for `sys_clk`. Route evidence:
`build/gpu/t1o_per_primitive_material_20260928/pnr_seed1/run_01/` and
`build/metrics/artix7_100t_GPUVGA_T1O_PER_PRIMITIVE_MATERIAL_Q1.json`.
The separate pack run completed in 284 seconds and produced
`build/spu_a7_100t_GPUVGA_T1O_PER_PRIMITIVE_MATERIAL_Q1.bit` (3,825,950 bytes;
SHA-256 `9cd34b81b30a6048e231d77add649c6adab835b14fe08d1ab99d9c03ff9b0016`).

**Hardware transport:** The exact bitstream was loaded into FPGA SRAM over
DirtyJTAG at 1 MHz. `openFPGALoader` reached 100% and reported `ISC_DONE=1`
and `DONE=1`; log:
`build/gpu/t1o_per_primitive_material_20260928/h1/program_01_escalated.log`.
The CH340 UART sender transmitted the fixed production Scene A geometry/U/V
with opcode tuples `[5,4,3,2]`, `[0,5,4,3]`, `[1,0,5,4]`, and return
`[5,4,3,2]`. All four 179-byte writes completed `tcdrain`, at 115200 8N1,
with 5011.436138, 5011.617771, and 5011.598304 ms start-to-start gaps.
Initial and return-A packet hashes are identical. Transcript:
`build/gpu/t1o_per_primitive_material_20260928/h1/sequence_01.json`, SHA-256
`26e634a777f2dc0c155dae70c384f02b1ecc2cbcdb00cb4199152ce356529a5b`.

**Operator observation:** The owner confirmed that the displayed image changed
through the fixed-scene opcode sequence and returned to its initial pattern.
Geometry and U/V were held constant across all four packets; only the four
material opcode bytes changed. The observation establishes visible runtime
response and return behavior for this bounded sequence.

**Repeat run (2026-09-28):** The same bitstream hash above was checked again,
then `openFPGALoader -c dirtyJtag --freq 1000000` reloaded it into SRAM and
returned exit 0 with `ISC_DONE=1`, `INIT=1`, and `DONE=1`. The frozen sender
again drained four 179-byte A/B/C/return-A transactions at 115200 8N1.
The A and return-A packet hashes match. Transcript:
`build/gpu/t1o_per_primitive_material_20260928/h1/sequence_02.json` (SHA-256
`9705bc3d4f6823aa8100ceabfcff2d5baaddc4085cf941d74a2ddf295b506ab4`).
This repeat establishes programming and packet transport; no new visual or
physical pixel observation has yet been recorded for it.

**Second repeat (2026-09-28):** The identical SHA-256 bitstream was reloaded;
the programmer again returned exit 0 with `ISC_DONE=1`, `INIT=1`, and
`DONE=1`. All four frozen A/B/C/return-A UART packets drained, with exact
initial/return-A packet equality. Transcript:
`build/gpu/t1o_per_primitive_material_20260928/h1/sequence_03.json` (SHA-256
`bd0b30eb5624eeda51c05e3b9ff292c4b2290413de5e3ed423edd72b20fcb651`).
The owner observed that the display returned to identity after this run.
This confirms the visible return state for the second repeat; no physical
pixel-level comparison was made.

**Classification:** **B1 route and pack PASS; FPGA programming and UART
transport PASS; H1 transition/return PASS (operator-observed, visual-only).**
Exact per-pixel winner/opcode correspondence on hardware remains unmeasured;
that claim is supported by the independent simulation oracle.

### 3.24 — T1p per-primitive predicate bits: routed build and SRAM load (2026-09-29)

The T1p independent production oracle passed 1,228,800 simulated pixels
across frozen A/B/C/return-A selector tuples. The seed-1 Artix-7 100T
`gpuvga all` build completed synthesis, route, and pack; routed `clk_pixel`
was 31.23 MHz against the frozen 25.00 MHz threshold, and `sys_clk` was
166.09 MHz against 25.00 MHz. Build evidence:
`build/gpu/t1p_predicate_bits_20260928/build_seed1/run_01/`; metrics:
`build/metrics/artix7_100t_GPUVGA_T1P_PER_PRIMITIVE_PREDICATES_Q1.json`.
The packed bitstream SHA-256 is
`fe351b04a9f2d2e8b00fe49b9f84c20231f2d905d9c6dcc746c0b7f0347798e9`.

DirtyJTAG at 1 MHz loaded that bitstream into Artix-7 100T FPGA SRAM.
`openFPGALoader` exited 0 after `Load SRAM 100.00%` and reported
`isc_done 1`, `init 1`, and `done 1`. Transcript:
`build/gpu/t1p_predicate_bits_20260928/h1/program_02_escalated.log`
(SHA-256 `f7bcd298e32574bd55c7c893c6d68bfa6ba7369071a097be12217589c819c439`).
The first sandbox-blocked invocation did not access JTAG; its log is
`build/gpu/t1p_predicate_bits_20260928/h1/program_01.log`.

**UART transport (2026-09-29):** After a sandboxed attempt could not open the
CH340 device and sent no bytes, the approved retry wrote and drained four
frozen 183-byte A/B/C/return-A packets at 115200 8N1. The exact initial
and return-A packet SHA-256 values match. Start-to-start gaps were 5012.521,
5012.414, and 5011.737 ms. Transcript:
`build/gpu/t1p_predicate_bits_20260928/h1/sequence_01.json` (SHA-256
`4cd7e65e0019cb6a37e8cfff5e499914b02c1373f3e05a1b69f93484b3e304f3`).
This establishes host-to-CH340 packet transport, not FPGA acceptance or
displayed behavior.

The owner authorized a repeat with identical packets. Transcript
`build/gpu/t1p_predicate_bits_20260928/h1/sequence_02.json` (SHA-256
`3471a5d2842efad57611a943b1c9c29f0888af6ba3d95109849686272179b569`)
records four complete 183-byte writes and drain completions; gaps were
5012.268, 5011.765, and 5011.580 ms. The operator reported the small
upper-left patch but **no visible change** during A/B/C/return-A. The
independent oracle places 2,441 scene pixels inside x=10..70, y=10..90;
successive scene variants differ on 1,269, 1,261, and 1,278 pixels,
respectively. Thus the repeat confirms host transport but does not establish
FPGA packet acceptance or visual transitions. Further sends require a new
bounded visual diagnostic.

The owner then authorized one scaled visibility diagnostic using the same
T1p bitstream. The derived scene scaled the four triangle edge constants by
four and passed an independent 640×480 oracle: 38,561 valid pixels within
x=40..280, y=40..360; expected A→B, B→C, and C→A differences of 19,918,
19,805, and 20,165 pixels. The approved UART run transmitted four complete
183-byte packets with drain completions and exact return-A bytes. Transcript:
`build/gpu/t1p_predicate_bits_20260928/h1/scaled_visibility_01.json`
(SHA-256 `83df320ff8045dded24c3655bb99250a49493823aa5781cce2c8467866bb113a`).
The operator reported visual changes. Initial answers about the final image
conflicted, so a direct comparison asked whether it matched the first
enlarged A or preceding C. The operator confirmed that it matched the first
enlarged A. The bounded enlarged-scene A/B/C/return-A visual gate therefore
passed as an operator observation. No raw VGA capture or exact physical
pixel comparison was made.

The exact scaled packet sequence also passed a targeted T1p UART receiver and
scene-bank testbench, including final return-A activation; that is simulation
evidence and does not establish the physical return.

The first post-transport repository gate at
`build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_01/` ended `FAILED`
(exit 1, 1,004 seconds) after `spu_t1d_repeatability_diag_tb.v` exceeded its
60-second cap. Two isolated simulations passed in 55.506 and 50.722 seconds;
the test-specific runner cap was raised to 90 seconds. The renewed one-attempt
gate at `build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/` ended
`COMPLETE` (exit 0, 937 seconds). T1d repeatability passed and the suite
reported 237 passes, zero failures. This closes H1 repository integration.
The diagnosis and budget are recorded in
`spu_strategy/contract_gpu_t1p_t1d_timeout_triage_2026-09-29.md`.

**Classification:** B1 route/pack PASS; FPGA SRAM programming PASS; UART
transport PASS; enlarged-scene H1 transition/return PASS (operator-observed,
visual-only). Physical pixel correspondence is UNMEASURED.
Persistent configuration flash was not written. Contract:
`spu_strategy/contract_gpu_t1p_per_primitive_predicate_bits_2026-09-28.md`.

### 3.25 — T1q truth-table material: route, SRAM load, and UART transport (2026-09-30)

The T1q Q1 seed-1 Artix-7 100T build completed route and pack. The routed
pixel clock was 36.92 MHz against the 25.00 MHz threshold. The generated
bitstream SHA-256 is
`c2458086d6efcc323f70039dce87754ae6ff8bcf8012aed2e1404862332a728d`;
route evidence is `build/gpu/t1q_truth_table_20260929/build_seed1/run_02/`.
Its result duration includes host suspend; the active-runtime accounting
finding is documented in `docs/DETACHED_JOB_SUSPEND_ACCOUNTING_2026-09-30.md`.

DirtyJTAG at 1 MHz loaded the exact bitstream into FPGA SRAM. `openFPGALoader`
exited 0 after `Load SRAM 100.00%` and reported `isc_done 1`, `init 1`, and
`done 1`. Transcript:
`build/gpu/t1q_truth_table_20260930/hardware/program_01.log` (SHA-256
`da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`).
Persistent configuration flash was not written.

The frozen T1q sender wrote and drained four 183-byte packets to the CH340 at
115200 8N1. The sequence held the production geometry and selectors
`CCCCCCCC` fixed while sending table tuples A `00000000`, B `0F0F0F0F`, C
`06060606`, then return A `00000000`. The initial and return-A packet hashes
match. Transcript:
`build/gpu/t1q_truth_table_20260930/hardware/sequence_01.json` (SHA-256
`f5621af9dcc54f7e0db422de00a26346889fe31278aa0bca9a9eda7a3ce48d15`).
This establishes host-to-CH340 transport only. FPGA packet acceptance,
display response, visual transitions, and physical pixel correspondence are
`NOT MEASURED`.

An authorized single replay of the same sequence completed four more full
writes and drains. Transcript:
`build/gpu/t1q_truth_table_20260930/hardware/sequence_02.json` (SHA-256
`5ce5df993202bf4ddfac50ab9fea65bddba7cf1df422b637c97550e182d806e9`). The
operator reported stable monitor sync but no visible image during this replay.
This is a negative visual observation for this small production fixture;
packet acceptance and physical pixel behavior remain unmeasured. The replay contract is
`spu_strategy/contract_gpu_t1q_uart_replay_2026-09-30.md`.

**Classification:** T1q route/pack/timing PASS; FPGA SRAM programming PASS;
UART transport PASS; operator-reported stable sync with no visible image on
the replay.
FPGA packet acceptance and physical pixel behavior remain unmeasured.
Contract: `spu_strategy/contract_gpu_t1q_hardware_transport_2026-09-30.md`.

The owner then authorized one 4x-scaled T1q visibility attempt. The same Q1
bitstream was reloaded successfully; the derived geometry covered 38,561
oracle pixels in bounds x=40..280, y=40..360. The four scaled A/B/C/return-A
packets were transported and drained. Transcript:
`build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_01.json`
(SHA-256
`73a1d126586ef6c4e7f303e82b6a37ea94934ac4692986f7d72f444bb15301d0`). The
operator reported a blue triangle after the sequence. This is an
operator-observed T1q blue output. No pixel capture or physical pixel
comparison was made. Contract:
`spu_strategy/contract_gpu_t1q_scaled_visibility_2026-10-01.md`.

An owner-authorized unchanged replay also completed and passed transcript
audit for the four ordered packets. Transcript:
`build/gpu/t1q_truth_table_20261001/scaled_visibility/sequence_02.json`
(SHA-256
`5c2598430ad47079d61bf387a9fc2dd30ef1c0e762cfe599aa504ebfbe8c4bf9`). The
operator confirmed yellow B, XOR C, and return to blue A. This closes the
scaled A/B/C/return-A transition gate as operator-observed visual evidence.
It supports physical receipt and activation for this exact sequence but does
not prove byte-level receipt or exact per-pixel correspondence. Replay
contract: `spu_strategy/contract_gpu_t1q_scaled_visibility_replay_2026-10-01.md`.

### 3.26 — T1r SRAM programming recovery (2026-10-01)

After the first T1r programming attempt failed during JTAG initialization, one
owner-authorized recovery preflight found the RP2040 DirtyJTAG adapter and one
Xilinx Artix-7 100T device (`xc7a100`, IDCODE `0x03631093`, IR length 6). The
frozen T1r bitstream SHA-256 remained
`5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7`; sender
and fixture hashes and the scaled-scene packet/oracle dry-run also matched.
Preflight record:
`build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/preflight.txt`
(SHA-256
`dc009507fd7035e83d25d8d906b5cb4dc8685014dee99ccee3d25319f39f668b`).

The single recovery attempt loaded the exact bitstream into FPGA SRAM.
`openFPGALoader` exited 0 after `Load SRAM 100%` and reported `isc_done 1`,
`init 1`, and `done 1`. Log:
`build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/program_02.log`
(SHA-256
`da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`).
Persistent configuration flash was not written.

The conditional single UART command exited 1 before opening the port because
the frozen by-id path
`/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` was no longer present. The
sender transcript records zero transmissions:
`build/gpu/t1r_palette_pair_20261001/hardware_recovery_01/sequence_02.json`
(SHA-256
`3f111c7c0c8745e745cd8a96b3ddb860936229b97bbc84158304908c1d7cd0dc`). The
UART attempt is consumed; no reconnect or retry was made. T1r host-to-CH340
transport and scaled palette visibility remain unproven. FPGA packet
acceptance and physical pixel correspondence are unmeasured. Further UART or
hardware actions require a new contract and authorization.

Contract:
`spu_strategy/contract_gpu_t1r_programming_recovery_2026-10-01.md`.

### 3.27 — T1r UART path recovery (2026-10-01)

After the first conditional UART attempt failed before port open, one
owner-authorized read-only preflight found one CH340 (`1a86:7523`) and the
frozen by-id path resolving to `/dev/ttyUSB0`. The bitstream and sender hashes
and scaled packet/oracle dry-run matched. Preflight:
`build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01/preflight.txt`
(SHA-256
`535f726f1d9de7cbb8b9ecb8d85d1f987502de38220c0c13bf826c4a33563bd0`).

The single authorized resend then failed before opening the serial endpoint:
the same by-id path disappeared between preflight and sender open. The
transcript records zero transmissions:
`build/gpu/t1r_palette_pair_20261001/uart_path_recovery_01/sequence_03.json`
(SHA-256
`3f111c7c0c8745e745cd8a96b3ddb860936229b97bbc84158304908c1d7cd0dc`). No
retry, reconnect, or USB reset was performed. T1r host-to-CH340 transport and
scaled palette visibility remain unproven. Further hardware action requires
a new contract and authorization.

Contract: `spu_strategy/contract_gpu_t1r_uart_path_recovery_2026-10-01.md`.

### 3.28 — T1r passive USB/serial diagnosis (2026-10-01)

One authorized 45-second passive capture did not reproduce the CH340 path loss.
Before and after monitoring, the CH340 (`1a86:7523`, driver `ch341`) remained
at USB path `1-1.4` as `/dev/ttyUSB0`, with the same by-id link and matching
udev identity. The udev monitor recorded no events during the window; its
status 124 is the expected `timeout` completion. Artifacts and SHA-256 values
are in `build/gpu/t1r_palette_pair_20261001/usb_serial_diagnostic_01/manifest.sha256`.

The captured recent kernel log records a USB disconnect on port `1-1.1` at
`2026-10-01T23:29:32+13:00`, two seconds before the diagnostic's before
snapshot. The CH340 was on port `1-1.4`; this event does not establish a CH340
disconnect or explain the two sender-open failures. The earlier path loss was
not reproduced, and its cause remains unknown. No sender, serial-port open,
FPGA programming, reset, reconnect, or cable action occurred. T1r UART
transport and scaled visibility remain unproven. No further hardware action
is authorized by this diagnostic.

Contract: `spu_strategy/contract_gpu_t1r_usb_serial_diagnostic_2026-10-01.md`.

### 3.29 — T1r sandbox/host serial visibility comparison (2026-10-01)

A read-only comparison found different mount namespaces for the default
sandboxed command context and the approved host context. In the default
namespace `mnt:[4026533125]`, Python reported the frozen by-id link and
`/dev/ttyUSB0` absent. In the host namespace `mnt:[4026531832]`, Python saw
the by-id link resolving to `/dev/ttyUSB0`; `stat` identified a character
device (major 188, minor 0), and USB inventory showed CH340 `1a86:7523` at
`1-1.4`. No serial port was opened and no bytes were sent. The comparison
strongly supports sandbox device-namespace visibility as the explanation for
the prior `FileNotFoundError` results. It does not establish UART transport,
FPGA packet acceptance, or visible output.

Record: `build/gpu/t1r_palette_pair_20261001/execution_context_compare_01.txt`.
The correlated-monitor draft was superseded by this direct context
comparison. Any host-context sender attempt requires separate authorization.
The T1r host-context UART contract is
`spu_strategy/contract_gpu_t1r_host_namespace_uart_2026-10-01.md`.

### 3.30 — T1r power-off and successful SRAM reload (2026-10-02)

The operator confirmed the board had been turned off since the successful
SRAM load in §3.26. That volatile configuration is invalidated; the historical
programming result remains unchanged. The host-context UART contract halted
before sender launch. No UART bytes were sent under that contract.

The owner instructed a new bitstream load. The new contract scopes one SRAM
load of the same frozen T1r Q1 bitstream, SHA-256
`5df8ac43e5e6c10dc8a8a6b6a369ee2c44b7e73df9e11149f2b30e9f044523d7`,
with a 120-second limit and no UART transmission.

The first preflight halted on an unsupported `--version` metadata option,
before USB scan or JTAG detection. Its record is preserved. The corrected
preflight used the documented `-V` option and passed in host mount namespace
`4026531832`: loader v1.1.0, one DirtyJTAG `1209:c0ca`, serial
`CB81353DCE678119`, and one Xilinx `xc7a100`, IDCODE `0x03631093`, IR length
6. The frozen bitstream hash and original successful route evidence matched.
Preflight record:
`build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/preflight_02.txt`
(SHA-256
`8b3893e9691aa75b77d994e9646d506d1c29e310bf5fba8c1087a8a7cab344df`).

The single new SRAM load completed in 31 seconds, with exactly one terminal
marker, `COMPLETE`, and `result.json` exit code 0. The programmer reached
`Load SRAM: 100.00%` and reported `isc_done 1`, `init 1`, and `done 1`.
Programming evidence:
`build/gpu/t1r_palette_pair_20261002/power_cycle_reload_01/program_01/`,
systemd unit `spu-t1r-power-cycle-reload-20261002-01`. `stdout.log` SHA-256:
`da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`.
`stderr.log` is empty, SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

**Classification:** frozen T1r Q1 SRAM programming PASS; persistent flash
NOT RUN; UART NOT RUN. The attempt is consumed. FPGA packet acceptance and
scaled visibility remain unproven. The SRAM load remains volatile and requires
power/configuration continuity before any future sender launch.

After the reload, the operator reported: "Sync is visible but no image."
Record this as operator-observed sync with no visible image before any new
scene transmission. No A/B/C/return-A sequence has been sent since this load;
this observation does not establish scene reception or a failed scaled-scene
visibility test. No physical pixel capture or comparison was made.

Contract:
`spu_strategy/contract_gpu_t1r_power_cycle_sram_reload_2026-10-02.md`.

### 3.31 — T1r host UART sequence after reload; partial visual observation (2026-10-02)

The operator confirmed continued board power and observer readiness:
"Yes—still powered and ready now". The read-only host preflight passed in
mount namespace `4026531832`, with the expected CH341 endpoint
`/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` resolving to `/dev/ttyUSB0`.
Frozen bitstream, sender, and fixture hashes matched; the §3.30 reload had
exactly one successful terminal marker, and the scaled-scene oracle/packet
dry-run passed. `preflight.txt` SHA-256:
`2a6c75270e09affc4978be06420d7c4f62db6ef946e104177b76df4abe5cb3be`.

The single authorized 60-second-bounded sender command completed with exit
0 at `2026-10-01T20:45:20.596440Z`. The durable transcript records four
ordered A/B/C/return-A full 187-byte writes, four completed `tcdrain` calls,
the frozen packet hashes, and identical A/return-A packet bytes. Independent
transcript checks passed. Evidence directory:
`build/gpu/t1r_palette_pair_20261002/host_uart_01/`.
`sequence_01.json` SHA-256:
`50cbc9b6591122adca466cda904d9449bc1f6789d9fe3486178a459f9ec8aaf8`.
`sender.stdout.log` SHA-256:
`8bd972b2cf88e21002060c924009de4a8e7c223e11f56ad4676892d37d20a958`.
`sender.stderr.log` is empty, SHA-256:
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
`sender_launch.json` and `sender_result.json` preserve the exact command,
operator confirmation, host namespace, timestamps, and command exit status.

The operator subsequently reported: "Crosshatch patterns with interference."
This partial observation does not identify the four states separately, their
color transitions, or return-A equivalence. Full-display and close-up photos
were requested while preserving the powered return-A state.

The operator supplied `IMG_1790.jpeg`, preserved unchanged in the evidence
directory (640×480 photograph), SHA-256
`86b6e4a9924c741310755ed8a211753fdaf536f445c4c75f242a3f081e16ba9f`.
It shows repeated green-and-white diagonal blocks across the visible display
area, plus fine bands/fringes. Physical state attribution is not confirmed
beyond its submission after the request to photograph held return-A.
`photo_01.json` records the description and limits. An oracle-derived
`expected_return_A.png` shows a bounded downward triangle with flat red/green
upper regions and blue/white lower regions on black, covered bounds
x=40..280, y=40..360. The repeated pattern in the photograph is inconsistent
with expected return-A if this state attribution is confirmed. No cause is
assigned to the interference; a still photograph cannot distinguish hardware
or display behavior from camera artifacts. State-specific details remain
pending. No further hardware action was taken.

The operator then confirmed stationary diagonal blocks, visible vertical
blue lines, and constantly flickering visual "snow". The exact report is
preserved in `operator_observation_02.json` in the same evidence directory.
This establishes that display instability is visible to the operator;
camera artifacts alone cannot account for that reported live flicker.
The cause remains unresolved, and the four-state transitions remain
unreported. The historical route log reports final `clk_pixel` Fmax
35.73 MHz against a 25.00 MHz requirement. Passing that tool timing check
does not measure current electrical signal quality or establish the cause
of the observed snow. No new hardware action was taken.

The operator subsequently confirmed "Patterns changed" and requested a
photographic replay. This establishes broad changes during the first
sequence, without state-specific detail or return-A equivalence. One
separate replay is authorized under
`spu_strategy/contract_gpu_t1r_photo_replay_2026-10-02.md`;
the original invocation remains consumed, and its visual HOLD is unchanged.

**Classification:** host UART write/drain PASS; single sender invocation
consumed. Visual HOLD from the supplied photograph; four-state visibility
inconclusive from the partial operator report.
Host transport success does not establish FPGA
byte-level packet acceptance or exact physical pixel equality. No further
invocation is authorized under the original contract; the renewed replay
authorization is recorded separately above.

Contract:
`spu_strategy/contract_gpu_t1r_host_uart_after_reload_2026-10-02.md`.

### 3.32 — T1r photographic replay; host writes/drains PASS (2026-10-02)

The owner reported that patterns changed during the first sequence and
requested one photographic replay, then confirmed continued board power
and readiness for 15-second dwells. Read-only host preflight passed with
the same endpoint, namespace, frozen hashes, reload evidence, and oracle
packet dry-run. `preflight.txt` SHA-256:
`92ae1b6c690ccbabff4978fd58dd79d1d780770415a9d0b13c26f132e9bb6971`.

The single renewed 60-second-bounded invocation exited 0 at
`2026-10-01T21:02:04.673081Z`. Four ordered full A/B/C/return-A writes of
187 bytes each and four completed drains were recorded. Independent
transcript checks passed for all frozen packet hashes, packet bytes,
identical A/return-A bytes, and three 15-second dwell intervals.
Evidence directory:
`build/gpu/t1r_palette_pair_20261002/photo_replay_01/`.
`sequence_01.json` SHA-256:
`1d157de804b0f33a70d7f41f7bd327a3836c2c948dde7b4ae58f30f9d40051b7`.
`sender.stdout.log` SHA-256:
`8bd972b2cf88e21002060c924009de4a8e7c223e11f56ad4676892d37d20a958`.
`sender.stderr.log` is empty, SHA-256:
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
`sender_launch.json`, `sender_result.json`, `observer_ready.json`, and
`transcript_check.json` preserve command identity, operator confirmation,
timestamps, exit status, and independent checks.

The operator was cued to photograph each state. Supplied `A.jpeg`, `B.jpeg`,
`C.jpeg`, and `D.jpeg` are preserved unchanged in the evidence directory's
`photos/` child. `photos_manifest.sha256` and `photo_review_01.json` preserve
the exact file hashes, dimensions, camera timestamps, and decoded RGB hashes.
The three distinct photographs show broad color/pattern changes: A has
red/green/pale repeated blocks; B has cyan/magenta bands and dark blocks;
C has green/pale repeated blocks, fine colored lines, and a magenta region
at lower right. All retain repeated patterns across the active display
rather than the expected bounded triangle. Software-oracle reference images
`expected_A.png`, `expected_B.png`, and `expected_C.png` are preserved for
visual comparison; these are expected output, not physical evidence.

`A.jpeg` and `D.jpeg` have different file-byte hashes but identical decoded
RGB pixels and the same camera DateTime (`2026:10:02 10:01:23`). Their decoded
RGB SHA-256 is
`f1f1f5f40160628acc82641aa2daba9862e4950537920a5ce2825973feb8d690`.
They cannot independently establish return-A equivalence. Asked about state
attribution, the operator clarified: "Initial and return." Record A as
initial-A and D as return-A by operator attribution, preserved in
`operator_state_attribution.json`. This resolves the intended state labels;
the duplicate pixel data still prevents independent photographic return-A
verification. Under the supplied A/B/C labels, the three distinct photos
support broad display response during the sequence, without proving
byte-level FPGA acceptance.

The intended held final state is return-A. The prior stationary blocks,
blue lines, and flickering-snow HOLD in §3.31 is unresolved. No RTL, sender,
fixture, or bitstream changed, and no additional hardware action was taken.

**Classification:** replay host UART write/drain PASS; single renewed
invocation consumed. Replay visual HOLD: photographed output does not match
the expected bounded triangle. Four-state/return-A photographic verification
is inconclusive because A/D are duplicate image pixels. Pixel correspondence
and byte-level FPGA acceptance remain unproven; the fault cause is unresolved.
No additional sender, reload, reset, or changed bound is authorized.

Contract: `spu_strategy/contract_gpu_t1r_photo_replay_2026-10-02.md`.

### 3.33 — VGAFIX display control; programming/startup PASS, visual HOLD (2026-10-02)

After the reviewed contracts and snapshot-helper correction, the owner
explicitly authorized VGAFIX and confirmed unchanged board, monitor, VGA
harness, settings, and power configuration, with live-observer readiness.
The hardware phase is limited to one SRAM load, one read-only STAT query,
and one 30-second observation. Repository verification is a separately
authorized phase and has not started.

Frozen historical artifact: `build/spu_a7_100t_VGAFIX.bit`, 3825920 bytes,
SHA-256 `a80b6d0cde560f71c85dcd4a8896019ae21f9149a5eed6cf26e35b154b69e379`.
Historical source anchor and measured color-bar evidence remain §3.8;
no rebuild was performed for this hardware experiment.

Host preflight passed with every command exit 0, mount namespace
`mnt:[4026531832]`, loader v1.1.0, exactly one DirtyJTAG `1209:c0ca`
serial `CB81353DCE678119` at 1 MHz, and one Xilinx XC7A100T,
IDCODE `0x03631093`, IR length 6. Preflight log SHA-256:
`5b07ce97f861445dbc016357109aafffb86f1ff71038ec3030838fd31eb1df29`.

The single 120-second-bounded detached programming job completed in
31 seconds, `2026-10-02T00:49:34Z` to `00:50:05Z`. Exactly one terminal
marker `COMPLETE`, exit 0, 100% SRAM transfer, and `isc_done 1`, `init 1`,
`done 1` establish programming PASS. Unit:
`spu-t1r-vgafix-control-20261002-01`. Exact command:

```bash
openFPGALoader -c dirtyJtag --freq 1000000 build/spu_a7_100t_VGAFIX.bit
```

Programming stdout SHA-256:
`da4130eb31e500564a5b017544b128b144754cbc9fef33ce1238c3da42996605`;
result SHA-256:
`ceb6c77cc41caaa3d69db8ca129a4799de158f0de157e7262677848d6e0f5203`.
The volatile T1r configuration was replaced by VGAFIX. No persistent
flash, UART transmission, wiring change, reset, or power-cycle occurred.

The single authorized read-only query exited 0 in the approved host context:

```bash
timeout 20s openFPGALoader -c dirtyJtag --freq 1000000 --read-register STAT
```

Raw STAT `0x401079fc`: no CRC/ID error; DEC Error 0; INIT Complete,
EOS, GWE, Release Done, and Done all 1. Startup PASS. STAT stdout SHA-256:
`00b1a9b0058387fb04aac054b7ddb9671987e94dd096cbfccb72b6a35a6caf59`.
Programming and query stderr were empty. Original commands, timestamps,
exit statuses, raw decode, and all log hashes are preserved under
`build/gpu/t1r_vgafix_control_20261002/control_01/`, including
`programming_startup_check_01.json` and `startup_stat_01.*`.

After startup PASS the operator confirmed continued power, unchanged setup,
and readiness. The single 30-second observation was cued; its interval
ran from `2026-10-02T01:09:52.251083+00:00` to scheduled end
`01:10:22.251083+00:00`. Start/end records are
`observation_01/interval_start.json` and `interval_end.json`.
The interval is consumed; elapsed time does not establish a physical visual
pass. No hardware commands were issued during the interval. Operator report and original
photo/video remain pending. Expected bars are white/yellow/cyan/green/
magenta/red/blue/black, with a moving four-row red marker whose temporary
disappearance at counter rows 480..511 is intentional.

The owner subsequently requested another interval: "Can you run that again?
I didn't see it." Classify the first interval INCONCLUSIVE / missed by
the observer. The request authorizes one additional 30-second observation,
one full-display photo, and one 10-second video under `observation_02/`,
pending current power/setup continuity and readiness. This repeats only
the observation; the continuously running pattern needs no new command.
`observation_repeat_authorization_01.json` preserves the request and scope.

The owner answered "Ready." to the continuity/readiness question. The
repeat was cued at `2026-10-02T01:17:02.294916+00:00`, scheduled to end
at `01:17:32.294916+00:00`. During the interval the owner reported
"Nothing has changed." Preserve this exact report in
`observation_02/operator_report_01.json`. Clarification is pending whether
the earlier T1r crosshatch remains or expected bars are stable, and whether
the marker moves. The original deadline was preserved after the report
interrupted the wait; no hardware command or further interval was started.
The repeat slot is consumed; start/end records are preserved under
`observation_02/`. Photo/video remain pending.

The operator clarified: "Same diagonal/crosshatch pattern as T1r."
Record control visual HOLD on this live report: expected VGAFIX color bars
were not observed, and comparable crosshatch persists after clean startup
of the frozen non-GPU control image. Preserve the clarification in
`observation_02/operator_report_02.json`; `hardware_result_01.json` records
the independent dimensions. Original photo/video support is PENDING.
Current blue-line/snow persistence, marker liveness, physical pixel equality,
and electrical timing/quality were not established by that clarification.

**Classification:** programming/startup PASS; first observation INCONCLUSIVE;
repeat control visual HOLD by operator report. The shared display path and
configuration behavior remain unresolved, including FPGA output, electrical
harness, power, and monitor causes. No wiring or GPU arithmetic fault is
assigned. Hardware result is recorded; both hardware command slots and both
observation intervals are consumed. No command retry or recovery is authorized.
Repository closeout PENDING; separately authorized snapshot preparation may
now start, followed sequentially by the reviewed gates. No current repository
gate or synthesis pass is claimed.

The operator then reiterated "No change.", preserved in
`observation_02/operator_report_03.json`; control visual HOLD is unchanged.
The separately authorized repository snapshot attempt later had exactly one
terminal marker `FAILED`, exit 1 after 9 seconds, because its destination
manifest rejected external `.venv_plot/bin/python`. Chipdb copying,
regressions, and synthesis were NOT RUN. The snapshot slot is exhausted;
no retry was launched. Preserve the independent hardware result above and
leave repository closeout PENDING. Repository evidence:
`build/gpu/t1r_vgafix_control_verification_20261002/campaign_01/snapshot_01/`
and `snapshot_interpretation_01.json` in its parent. The companion contract
§7 records the stop and minimal proposed correction.

During the subsequently authorized diagnosis/redesign, the operator visually
confirmed the same Wukong board, J10 harness, and monitor as the DirtyJTAG target.
Record this as physical association by operator report, not measured continuity
or pin waveforms. The frozen VGAFIX hash remains unchanged. Current source bytes
for top/pattern/timing/HAL/synthesis match the historical anchor; retained routed
VGA pad assignments match G8/G7/G5/D5/E5, with artifact association limits recorded
in `spu_strategy/diagnosis_gpu_t1r_vgafix_and_snapshot_2026-10-02.md`.
No new hardware commands or measurements were performed. The snapshot exclusion
cause is established separately; corrected-helper temporary fixtures passed but
no new snapshot, full regression, or synthesis was launched. Control visual HOLD
and repository closeout PENDING remain independent.

The separately authorized recovery phase later completed all mandatory repository
gates for its exact frozen `campaign_02/checkout` snapshot: preparation COMPLETE
(9 seconds); full regression 238 PASS/0 FAIL, video triage 65 PASS/0 FAIL, both
trace and all four named math/oracle commands PASS (1558 seconds); isolated
Artix-7 100T RPLU2PADE synthesis/place-and-route/packing COMPLETE (412 seconds).
All three jobs had exactly one COMPLETE marker and exit 0. Final reported
`clk_fast` was 39.86 MHz and `$iopadmap$clk_100mhz` 307.41 MHz, both PASS at the
25 MHz constraint. Required outputs were nonempty and hashed; final independent
source/helper/build/chipdb guards passed. **Repository closeout PASS** is limited
to the frozen 2851-entry dirty-tree snapshot, HEAD
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`, manifest SHA-256
`1044941c30d6703afe34f6871f669d116e893ef1c411102796a6719928fe736d`.
Evidence: `build/gpu/t1r_vgafix_control_verification_20261002/campaign_02/`
contains `repository_closeout_01.json` and `pade_interpretation_01.json`;
`spu_strategy/contract_gpu_t1r_vgafix_repository_recovery_2026-10-02.md` §10
records scope and exhausted slots. Later primary result reports were not gate
inputs. Generated Padé outputs stayed isolated and were not programmed.
VGAFIX visual HOLD and the unresolved display diagnosis are unchanged;
post-load photo/video and RGB/sync measurements remain pending. This repository
verification supplies no new silicon or display-correctness claim.

Contract: `spu_strategy/contract_gpu_t1r_vgafix_display_control_2026-10-02.md`.

### 3.34 — VGAFIX CRC delivery: transfer COMPLETE, subsequent startup anomaly (2026-10-02)

**Classification:** HALT / PROGRAMMING-STARTUP ANOMALY. No display observation
was launched. Current active FPGA configuration is UNKNOWN; CRC delivery
validation is NOT ESTABLISHED. This result assigns no physical or RTL root cause.

The owner authorized the frozen CRC campaign with "Authorized." and confirmed
"Same setup, powered continuously, ready now" before preflight. The derived
3825920-byte image SHA-256 is
`534e88759e10aa66330fbeb10856635f93d7c5306c277de841a09587ccde49f9`.
It preserves the historical VGAFIX frame payload and every byte outside two
eight-byte packet replacements supplying CRC checks. Offline preparation
recorded 83 passing checks and reproduction from the frozen review packet.
Source configuration provenance remains the historical VGAFIX frame input;
this artifact was generated by packet transformation, without new synthesis.

Preflight PASS identified one DirtyJTAG `1209:c0ca`, serial
`CB81353DCE678119`, one XC7A100 IDCODE `0x03631093`, IR length 6, loader
v1.1.0, host mount namespace `mnt:[4026531832]`, and 1 MHz JTAG. Frozen input
checks passed before each hardware stage. The single detached SRAM attempt,
unit `spu-vgafix-crc-delivery-20261002-01`, has exactly one COMPLETE marker,
exit 0, duration 32 seconds, `2026-10-02T09:06:15Z`–`09:06:47Z`. Its stdout
reports 100% SRAM transfer and immediate IR `isc_done 1`, `init 1`, `done 1`.
Programming stderr is empty. This initial report does not override the later
failed startup prerequisite.

The single subsequent STAT command itself exited 0 with empty stderr, but
the frozen startup guard returned HALT at `2026-10-02T09:07:24.699893+00:00`.
Raw STAT was `0x40000018`: CRC/ID/DEC errors reported absent and EOS 1,
while INIT Complete, INIT B, GWE, Release Done and Done all reported 0.
The immediate IR and subsequent STAT results disagree. The available evidence
does not determine when or why the state changed; the absence of a reported
CRC error is insufficient to establish CRC acceptance or correct SRAM contents.

Preflight, launcher, SRAM and STAT slots are consumed. The observation was NOT
RUN because startup did not pass; no retry, restoration, reset, power-cycle,
UART, wiring change or additional query was performed. Stop this campaign.
Earlier VGAFIX visual HOLD remains a historical observation; no current display
behavior is attributed to a successfully running CRC control image. Repository
PASS remains limited to the preceding frozen verification snapshot.

Evidence: `build/gpu/vgafix_crc_delivery_20261002/hardware_01/`, especially
`hardware_result_01.json`, `program_01/result.json`, programming logs,
`startup_stat_01.*`, and `operator_preflight.json`. Original authorization,
readiness, exact commands, UTC timestamps and log hashes are preserved.
Frozen contract: `spu_strategy/contract_gpu_vgafix_crc_delivery_2026-10-02.md`;
its reviewed bytes are retained unchanged, with execution status recorded in
the hardware result rather than rewriting the authorized draft.

The subsequent owner-authorized **offline** CRC/loader audit reproduced all six
supplied CRC checkpoints in the candidate and two independent existing images;
three changed-data/checksum controls were rejected. Source-extracted STAT
serialization preserved three supplied values, with two negative controls
rejected. The inspected JTAG query sequence agrees with AMD UG470 Table 6-5,
including TAP-reset cleanup; SelectMAP's DESYNC requirement does not establish
a JTAG query defect. Offline driver-failure injection and exact installed-binary
disassembly establish that `Jtag::read_write` discards transport return codes
and can report success after a driver failure. No recorded driver diagnostic
or other evidence links that defect to this campaign's low STAT flags.

This audit ran **zero hardware operations** and preserved the frozen campaign
and raw observations. CRC delivery remains NOT ESTABLISHED, active configuration
UNKNOWN, earlier visual HOLD unchanged. Repository PASS remains limited to its
earlier frozen snapshot. Evidence:
`build/gpu/vgafix_crc_delivery_20261002/offline_audit_01/`; interpretation:
`spu_strategy/diagnosis_gpu_vgafix_crc_loader_audit_2026-10-02.md`.
No follow-on query, recovery, loader patch or hardware budget is authorized.

### 3.35 — T1d recovery: SRAM load reported complete, no VGA lock, checked startup status agrees (2026-10-05)

**Classification:** VISUAL HOLD; GPU hardware/display acceptance and physical
vertex A/B are NOT ESTABLISHED. No A or B packet was sent. One of the
prospectively authorized three recovery load/A/B attempts is consumed; two
remain, subject to diagnosis/correction and operator readiness.

The owner authorized iterative contract/helper and host-environment repairs,
read-only checks without consuming load attempts, and at most three physical
attempts. The amended scope freezes 300 seconds per attempt and a cumulative
reserved budget of 900 seconds. Earlier authorizations/failures remain recorded.
Attempt 1 uses `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/hardware_08/`.

The operator described the reset method as "I pulled the power plug and stuck
it back in," then explicitly clarified "Before the reload of course. I thought
I mentioned this." The power cycle was before this SRAM load. The earlier
black-screen-with-signal report is a pre-load observation; no physical user-reset
procedure or post-load power cycle is established by it.

The pinned historical image is
`build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit`, SHA-256
`52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914`.
Host USB/serial and programmer-access preflight passed. The single SRAM load
ran `2026-10-04T20:39:36Z`–`20:40:07Z`, exited 0, reported 100% progress
and immediate IR `isc_done 1`, `init 1`, `done 1`. The operator subsequently
reported "No signal lock," and later confirmed "Yes, no signal. Massive
regressions happening." This fails the required display baseline. Attempt 1
closed before any UART transmission. The loading report does not establish
live frame identity or display acceptance.

A separately recorded checked read-only status diagnostic first stopped before
STAT because its identity guard compared revision-less `0x03631093` with the
raw `0x13631093`. The retained loader source masks the top four bits for part
lookup. The corrected helper pins the normalized part and observed revision 1;
the original failed diagnostic remains in read_only_status_01. No wiring,
RTL, bitstream identity or A/B criteria changed. Offline corrected checks:
124 sequence checks, 4 entrypoint checks, 3 wrong-identity controls PASS.

The corrected read-only bracket completed at `2026-10-04T20:48:53Z`, exit 0:
IR before `0x35`, STAT `0x401079fc`, IR after `0x35`. DONE, INIT Complete,
INIT B, Release Done, GWE and EOS report 1; CRC/ID/DEC errors report 0.
The native transport journal records 79 checked bulk transfers with complete
returned counts. This supports IR/STAT shared-flag agreement and a responding
configuration interface. It does not establish SRAM frame identity, pixel-clock
liveness, VGA sync, a code regression or any specific physical cause. No reload
followed this query, and the operator still reports no monitor signal.

The host loader's underlying ELF SHA-256 remains
`2956f63e5afbedf0747ec880e3b17c316fef311f4710d6f71bc23abea7821ed9`, matching
the earlier transport audit. Its discarded-return-code defect is known; its
involvement in this attempt remains unmeasured. No CRC error alone does not
prove payload integrity. Passed software gates are reused only for their
unchanged relevant inputs; Padé synthesis is separate from GPU/display acceptance.

Evidence: hardware_08/command_results.json, programming.log and
recovery_diagnosis.json; read_only_status_01 and read_only_status_02 beneath
`build/gpu_evaluation/t1d_vertex_ab_2026-10-04/`, especially the corrected
status_result.json, managed_result.json, transport.jsonl and evidence_check.json.
Budget/authorization: recovery_2026-10-05.json. Active amendment:
`spu_strategy/contract_gpu_t1d_reload_after_operator_reset_2026-10-05.md`.

#### 3.35.1 — Existing-cable JTAG SAMPLE observations

Following the owner's request to diagnose the regression and readiness
"Powered, unchanged, ready now," one SAMPLE/BYPASS measurement completed
`2026-10-04T21:20:20.909832Z`–`21:20:26.639739Z`, exit 0. No reload, UART,
output override or wiring change occurred; no load-attempt slot consumed.
The native USB journal has 1259 checked bulk transfers, and every one of the
32 boundary captures verified the 989-bit register extent with a 16-bit
shifted marker. IR before/after remained `0x35`. Captures span 5.192409431 s.

Clock M21 input sampled both 0 and 1. Reset H7 and UART F3 input sampled 1
throughout. HSYNC D5 and VSYNC E5 pad input and output cells sampled 0 in
every capture. These are sparse observations, not sync or clock frequency
measurements. They locate an abnormal sync-level observation at the FPGA,
but do not establish its cause or the internal clock/reset state.
Red G8 and diagnostic G6 control cells sampled 1 despite the retained
always-driven output model; post-configuration interpretation is qualified
by the vendor BSDL annotation warning. This discrepancy alone does not prove
corrupted SRAM, a disabled physical driver or a programmer fault.

Offline comparison establishes that the loaded historical file retains its
September hash; the primary T1d file differs only in seven header date/time
bytes. Their complete 3825788-byte configuration payloads match. Independent
reconstruction from retained frames matches all 955864 FDRI words. Live SRAM
identity remains unmeasured. Retained reset pull-up and clock-buffer topology
are unchanged. No newly changed bitstream payload explains this failure.

Focused checks: 25 SAMPLE/alignment/fail-stop and 5 entrypoint/readiness
checks PASS with mocked USB. Model is vendor-authored XC7A100T FGG676 BSDL,
pinned to a public mirror Git blob with provenance retained; it is not
represented as a signed vendor download. Evidence beneath
`build/gpu_evaluation/t1d_vertex_ab_2026-10-04/`:
`read_only_pins_01/{pin_result.json,managed_result.json,transport.jsonl,evidence_check.json,provenance.json}`
and `regression_diagnosis_01/{bitstream_comparison.json,clock_reset_pin_audit.json}`.
GPU/display acceptance and physical vertex A/B remain NOT ESTABLISHED.

#### 3.35.2 — Stable selected I/O configuration mismatch

After renewed readiness "Powered, unchanged, ready now," the bounded
configuration readback completed `2026-10-04T22:30:45.607660Z`–
`22:30:50.121906Z`, exit 0, through the existing JTAG cable. No reload, shutdown,
frame writes or UART; no recovery load slot consumed. All 1091 native bulk
transfers had checked results/counts. IR before/after was `0x35`, STAT
before/after `0x401079fc`, CTL0 `0x501`. Pre-read STAT is retained separately
because the read procedure resets the CRC accumulator.

Two planned reads of FARs `0x1ca6` and `0x1ca7`, with a discarded dummy frame,
returned identical complete 303-word sequences. Both actual frame ECC values
independently recompute correctly. Of 76 projected static I/O drive/pull bits,
13 differ from the intended historical T1d image, affecting red G8, diagnostic
G6 and selected reset/UART pull-up bits. This is a stable configuration mismatch
under the recorded readback/alignment model. It correlates with prior SAMPLE
discrepancies and provides physical evidence beyond the loader's completion
report. It does not establish full live image identity, the mismatch mechanism,
a particular loader/firmware fault or GPU/display acceptance.

The two frames match none of 45 retained frame sets; there is no exact alternate
frame-address match in the historical T1d frames. This is a limited offline
candidate inventory. The no-shutdown configuration request is an explicit
CFG_IN/CFG_OUT translation of AMD's ICAP static-frame request; technical basis
and interface uncertainty are retained in active contract §10. No security
setting was changed and no captured registers/BRAM contents were compared.

Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/read_only_frames_01/`,
especially frame_result.json, transport.jsonl, evidence_check.json, expected_io.json,
retained_io_frame_comparison.json, all_retained_frame_candidates.json and
t1d_all_frame_alignment_comparison.json. One recovery load attempt consumed,
two remain; physical A/B has not run.

The existing loader's proven discarded-error defect is being repaired in a
separate local DirtyJTAG-only v1.1.0 source copy, with no system replacement or
hardware use. 25 focused source-extracted error/count/firmware controls PASS
with mocked transport. Build result is pending; no repaired-loader load or
causal attribution is claimed. Host repair evidence:
`build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_repair_01/`.

Host-only loader build LAUNCHED at `2026-10-04T22:46:19Z`, unit
`spu-loader_build_job_01-20261004T224619Z-132219`, evidence
`build/gpu_evaluation/t1d_vertex_ab_2026-10-04/loader_build_job_01`, external cap 600 seconds. Result PENDING in the launching turn; no repaired-loader hardware command run.

In a later invocation, that build has exactly one COMPLETE marker, exit 0,
duration 66 seconds, ending `2026-10-04T22:47:25Z`. Executable SHA-256:
`b7a184491a7e0c8dca9676473c2507d2c047821cc4cfb72db22831c071b66f46`.
Six actual-binary controls PASS with mocked libusb failures, including short
writes, incomplete/bad information responses and frequency-command failure.
No physical USB opened in these checks. Source controls remain 25 PASS.

Prospective recovery attempt 2 is prepared in hardware_09 with 20 mocked
recorder/preflight and 7 observation-gate checks PASS. Active contract §12
pins the repaired executable and unchanged bitstream/sender/packets. It adds
an immediate checked post-load static I/O comparison before the existing
black/locked and A/B visual gates. No attempt-2 load or UART has occurred at
this preparation checkpoint. Current operator readiness is still required;
one attempt used, two remain. The historical mismatch mechanism remains
unresolved; loader repair is not yet a demonstrated physical correction.

#### 3.35.3 — Recovery attempt 2: successful load and selected I/O match

Operator readiness reply: "Ready. Run it." to the powered/unchanged readiness
question. Corrected-loader preflight passed. One SRAM load ran
`2026-10-04T23:38:17.441646Z`–`23:38:48.987516Z`, command exit 0, with 63767
checked native USB transfers, 100.00% progress and ISC_DONE/INIT/DONE=1.
Recorder falsely rejected decimal progress; original false stop and previous
helper manifest are preserved in hardware_09. A narrow progress-parser repair
passed 23 offline recorder checks. Contract §12.1 permits reassessment of the
existing successful command within its unchanged deadline; no second load.

Post-load I/O readback completed `2026-10-04T23:39:49.156236Z`–
`23:39:53.461878Z`, exit 0. All 76 projected static I/O bits match, stable
across the two planned reads, with zero selected mismatches. Previously 13
selected bits differed. This demonstrates a matching selected I/O configuration
after the instrumented load; it does not establish the historical mismatch
mechanism, full live image identity or VGA/GPU acceptance. No scene A/B sent
at this checkpoint. Await current black/locked baseline observation.

Evidence: hardware_09/{preflight.json,program.log,command_results.json,
command_results_before_progress_correction.json,focused_checks.json} and
hardware_09/postload_io/{frame_result.json,managed_result.json,transport.jsonl},
under `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/`.
Attempt deadline remains `2026-10-04T23:43:17.441646Z`; two attempts consumed,
one remains. No automatic retry or deadline extension.

Operator subsequently reported: "Stable signal achieved, we're back!" This
establishes reported monitor lock after the selected I/O match. It does not
confirm a black/unarmed baseline or physical scene rendering. Attempt 2's
300-second window had expired before recording this observation; it is closed
as SIGNAL_RECOVERED_AB_NOT_RUN_DEADLINE_EXPIRED with A/B unsent.

The remaining authorized attempt is prepared in hardware_10 as UART A/B only,
with zero additional loads, reusing the successful load and matching selected
I/O evidence. Thirteen focused mocked campaign checks PASS; no hardware use.
Contract §13 requires current black/locked, powered/unchanged readiness before
A starts the final 300-second clock. No third attempt started at this checkpoint.
The historical mismatch mechanism and physical vertex A/B remain unestablished.

#### 3.35.4 — Final UART-only attempt: Scene A sent, observation pending

After current black/locked and powered/unchanged confirmation "Confirmed.",
Scene A was sent once at 2026-10-04T23:48:59.923841Z in hardware_10.
Host command exited 0; transcript records 64 bytes and completed tcdrain.
No FPGA load, reset or power cycle occurred. Eight offline transcript-adapter
checks and thirteen mocked recorder controls passed before launch. Sender
source and packets remained unchanged; only transcript destination was bound
to this attempt. Host write/drain does not establish FPGA receipt or rendering.
A's physical observation is pending; B has not been sent. All three authorized
attempt slots are now consumed. This final attempt's deadline is
2026-10-04T23:53:59.923841Z. Evidence: hardware_10/{command_results.json,
uart_a.json,adapter_checks.json,focused_checks.json,operator_readiness.json}
under build/gpu_evaluation/t1d_vertex_ab_2026-10-04/.

Operator reported "Expected red and green triangles; stable lock" for Scene A.
The report was recorded at 2026-10-04T23:49:33.432804Z, 33.316 seconds after
A completion. The 30-second recorder bound closed attempt 3 as VISUAL_HOLD_A;
B was refused before serial access. Thus A rendering and lock are positively
reported, but the original timed A/B acceptance gate did not pass. All original
slots are consumed, and B remains unsent. Contract §14 proposes one B-only
completion, with no reload or repeat A, pending renewed owner authorization.
Four offline controls verify the proposed 120-second B reporting bound applies
only when that completion is explicitly marked authorized; no physical command.

The operator corrected Scene A's report: "Green triangle is deformed/interlaced
into red triangle." Preserve the initial positive report and timing stop, but
classify the actual A observation VISUAL_HOLD_A_GREEN_DEFORMED_OR_INTERLACED.
Reported sync lock remains recovered; expected scene geometry is not accepted.
B remains unsent. The proposed B-only completion is withdrawn because it would
assume a passing A baseline contradicted by the corrected report. No reload or
further UART is authorized under the exhausted original campaign. Offline
packet/retained-design diagnosis and a requested display photo may proceed.

Offline packet comparison confirms Scene A is byte-identical to the historical
64-byte fixture and its recorded sender digest. Independent packet decoding
gives the intended red/green colors and edge/depth fields. The retained S2
device-arithmetic preview has zero RGB differences from the ideal preview over
307200 pixels; its manifest explicitly says cycle_timing_model=false. It cannot
clear runtime timing or physical output faults. Expected Scene A has a straight
centre color boundary with separated lower apexes, not alternating lines.
Evidence: rendering_diagnosis_01/{packet_and_preview_audit.json,expected_scene_a.png}
under build/gpu_evaluation/t1d_vertex_ab_2026-10-04/. Root cause remains unresolved;
host drain does not prove FPGA receipt, and selected I/O matching is not full
live configuration verification. Current display photo requested; no further
physical execution occurred.

Current operator photo IMG_1815.jpeg was received from the project root and
preserved byte-for-byte as rendering_diagnosis_01/scene_a_operator_IMG_1815.jpeg,
SHA-256 e06c0dd6152b0b87798ef86f0ec716717018bf0d02062f7212a81c8c11494464.
It shows a mostly complete red triangle, green as a narrow upper band, and
absence of the expected lower/right green triangle. It does not clearly
establish alternating-line interlacing. Camera sampling patterns cannot be
assigned to FPGA timing from this photograph alone.

Retained netlist connectivity confirms triangle 1 uses scene bits 252–503,
its B0 field uses bits 16–31 of that record, the two rasterizers share setup,
and green color is sourced from active triangle 1. All three packed edge
coefficient maps and the depth comparator are present as expected. This is
static synthesized-design inspection, not proof of live registers or logic.

A targeted offline hypothesis matches the collapsed coverage: triangle 1's
first edge should be (A,B,C)=(0,560,0). A negative B would eliminate its
coverage for every row y>0, leaving only the top row. Illustratively, flipping
packet byte 36 bit 3 changes only that B sign bit (560 to -32208), preserving
the entire red record and other green fields. This is an arithmetic diagnostic
example, not observed corruption; no modified packet was transmitted. The
expected host packet is correct. Coverage/color/setup or live configuration
must be distinguished from actual received data before assigning cause.
Evidence: rendering_diagnosis_01/{photo_and_edge_hypothesis.json,
retained_tri1_connectivity.json}. B remains unsent; no new hardware command.

#### 3.35.5 — Renewed B-only diagnostic sent; physical observation pending

Owner explicitly replied "Authorized." to the combined single B diagnostic
authorization and current powered/unchanged Scene A readiness question. Scope:
one B, zero loads/resets/repeat A, 10-second UART, 180-second phase, 120-second
display-report window. This is prospective authorization; the earlier three
attempts and the malformed A baseline remain recorded without reinterpretation.

At 2026-10-05T03:51:15.948611Z–03:51:16.129782Z, the B-only command exited 0.
Its transcript records 64 bytes written, completed tcdrain and frozen packet
SHA-256 156ab65f14559c350bc602d4a48ee441cc2b145bfaee1a7775cde067e395a61d.
No FPGA reload/reset or repeat A occurred. Five offline authorization and
transcript-scoping preparation controls passed; unchanged sender gates reused.
The single new packet allowance is consumed, no retry. Physical observation
is pending and no FPGA receipt/rendering or original A/B acceptance is claimed.

Evidence: hardware_11_b_diagnostic/{completion_authorization.json,
operator_readiness.json,command_results.json,uart_b.json,b.log,identity.stdout,
focused_checks.json}, under build/gpu_evaluation/t1d_vertex_ab_2026-10-04/.
Report deadline: 2026-10-05T03:53:16.129782Z; phase deadline: 03:54:15.948611Z.

#### 3.35.6 — B photograph: vertex response with changed green appearance

Owner reported "Image sent." The new root photo IMG_1816.jpeg was preserved
byte-for-byte as hardware_11_b_diagnostic/scene_b_operator_IMG_1816.jpeg,
SHA-256 e526883103c27502b40301b0d8f7d9fd74915bebbac396ee87e04d76d5d0b1ba.
Compared with the retained A photo, red's lower apex visibly moved upward
consistent with the requested y=460 to y=240 edit. The green lower/right
triangle is now visible, whereas A had mainly a narrow upper green band.
The B photograph shows red/green horizontal bands within the overlap; their
monitor-versus-camera origin has not yet been explicitly established.

The entire 252-bit green triangle record is identical between A and B, not
merely its vertex list. Thus the displayed green appearance changed despite
identical green input fields. This supports investigation of runtime received
data, raw/prepared bank state, first-scene initialization or configuration/
timing/output behavior. It does not identify which mechanism occurred. The
offline loader model predicts first A activates bank 1 and subsequent B bank 0
from zero reset; actual hardware bank identities remain unmeasured. A persistent
unchanged negative green B0 alone would not explain its recovery in B, so that
earlier illustrative single-bit hypothesis remains unconfirmed.

Photo file mtime was 2026-10-05T03:52:43.177434Z, within the requested report
window, but agent review occurred later; file mtime is not a measured operator
observation timestamp. Classify PHOTO_RED_VERTEX_RESPONSE_GREEN_CHANGED_BANDING,
with original A/B acceptance NOT ESTABLISHED. This is evidence of a physical
vertex response, not a correct-rendering or full GPU acceptance claim. The
one B diagnostic is closed and its sole packet allowance is consumed. No
reload, repeat A or further UART occurred. Monitor lock and visible banding
confirmation requested from the operator without changing the displayed scene.

Evidence: hardware_11_b_diagnostic/command_results.json and preserved photo;
rendering_diagnosis_01/{a_b_photo_and_bank_audit.json,expected_scene_b.png},
under build/gpu_evaluation/t1d_vertex_ab_2026-10-04/.

Operator explicitly confirmed B: "Stripes visible on monitor; stable lock."
The bands are therefore a reported display artifact, not merely a photographic
pattern. Classification is RED_VERTEX_RESPONSE_WITH_REAL_STRIPING_STABLE_LOCK.
Physical red vertex response is observed, but correct rendering/original A/B
acceptance remains unestablished. Candidate next diagnostic: identical A twice
with no reload, comparing results across the model-predicted alternate banks.
That diagnostic has not been authorized or executed; actual bank states remain
unmeasured and no further packet allowance remains in the B-only phase.

#### 3.35.7 — Renewed identical-packet campaign: first A sent

Owner authorized multiple attempts/repairs and selected "Up to two comparisons;
board powered, unchanged and ready." Frozen scope: two comparisons maximum,
two packets each, 360 seconds per comparison, 720 cumulative, 10-second UART,
120-second report windows; no reload/reset/wiring or bitstream change. Routine
helper/host repairs are permitted with focused checks and unchanged-input gate
reuse. Thirty-one offline campaign/binding controls PASS with mocked UART.

Comparison 1's first A command ran 2026-10-05T04:07:02.243298Z–
04:07:02.427799Z, exit 0. Transcript records 64 bytes and completed drain,
frozen A digest aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee.
Actual host serial preflight passed. No reload/reset or second identical packet
has occurred at this checkpoint. Display report pending. First comparison
deadline is 04:13:02.120633Z; first report window ends 04:09:02.427799Z.

Evidence: hardware_12_identical_pairs/{authorization.json,operator_readiness.json,
comparison_1.json,uart_1_a.json,identity_1_1.stdout,focused_checks.json}, under
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/. Earlier failures, authorizations
and consumed budgets remain unchanged. No correct-rendering acceptance claim.

Comparison 1 closed COMPARISON_WINDOW_EXPIRED_NO_CURRENT_PHOTO_OR_REPORT.
Owner reported "Okay, new image in the root folder." Agent checked at
2026-10-05T04:15:37Z, after the 04:13:02.120633Z comparison deadline. Both
workspace and host root contain only IMG_1815.jpeg and IMG_1816.jpeg; their
SHA-256 values are unchanged from the earlier A/B photos. No current repeat-A
image or usable display/lock report was available. This is an unavailable
observation, not an observed GPU rendering failure. First A write/drain remains
successful; the second identical A was not sent. One authorized comparison
remains. Filename/path clarification requested. No physical retry follows
until the image-delivery/reporting problem is diagnosed and current readiness
is established. Evidence: hardware_12_identical_pairs/comparison_1.json.

The operator resolved photo delivery: "My bad, it's in the folder now. I put
it into the software/ folder by mistake." IMG_1817.jpeg was then found in the
project root and preserved as hardware_12_identical_pairs/
repeat_a_1_operator_IMG_1817.jpeg. The repeat-A photo shows full-height red and
green confined to an upper band, broadly returning to the original A fault
after the shorter-red/large-green B display. This is late evidence and does
not reopen comparison 1 or its timed acceptance gate. First-scene-only
initialization is less consistent with this return; bank/state versus
geometry-dependent setup is still unresolved.

The remaining already-authorized comparison is selected as identical A twice,
with a recorded reason, so geometry/packet contents stay fixed while the model
predicts alternate banks. Contract §16.1 covers this prospective routine
amendment; the two-comparison/two-packet/six-minute budget remains unchanged.
Current readiness and prompt text reports are requested; no new UART sent at
this checkpoint. Evidence: comparison_1.json, comparison_2_reason.json and the
preserved photo in hardware_12_identical_pairs.

#### 3.35.8 — Remaining identical-A comparison: first packet sent

After renewed current readiness "Ready." to the powered/unchanged Scene A,
stable-lock question, comparison 2's first A command ran
2026-10-05T04:21:56.357290Z–04:21:56.547337Z, exit 0. Transcript records
64 bytes written and completed drain, identical frozen A packet digest.
Read-only serial/sysfs preflight passed; no reload/reset or packet changes.
Current display report is pending; comparison 2's second A is unsent.
Comparison deadline: 04:27:56.228527Z; first text-report deadline: 04:23:56.547337Z.

Both authorized comparisons are now allocated. One final packet remains inside
the open second comparison, only after its first timely stable-lock observation.
The first comparison's unused second packet was not executed or recycled.
Evidence: hardware_12_identical_pairs/{comparison_2.json,uart_3_a.json,
operator_readiness.json,identity_2_1.stdout}, under
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/. No rendering acceptance claim.

Comparison 2 first report: "Full-height red and green; overlap striped; stable
lock", recorded 2026-10-05T04:22:52.378968Z (55.832 seconds after command).
Both full-height triangles now appear for A, unlike the preceding identical
A's preserved photo with green confined to the top. The second identical A
command then ran 04:22:52.633598Z–04:22:52.819770Z, exit 0, 64-byte write and
completed drain. Both transcript digests are exactly the frozen A digest.
No reload/reset, changed packet or blind retry; the first timely stable-lock
report preceded this second authorized identical packet. Its display report
is pending, deadline 04:24:52.819770Z.

The identical-packet campaign now has no additional packet allowance. Actual
UART writes total three, because comparison 1's unused second slot was not
recycled. Both comparisons remain consumed, with comparison 2's observation
still open. Original A/B acceptance is unestablished; no hardware bank state
has been measured. Evidence: hardware_12_identical_pairs/comparison_2.json,
uart_3_a.json and uart_4_a.json.

Comparison 2 is now CLOSED: DIFFERENT_REPORTED_OUTPUTS_FOR_IDENTICAL_PACKET.
The second timely report, recorded 2026-10-05T04:23:54.320514Z (61.501
seconds after command), is "Full-height red; green only a top band or missing;
stable lock". Thus the two byte-identical A packets produced different reported
green output while both maintained stable signal lock. Both writes were 64
bytes with completed drain and the same frozen packet digest. No new load,
reset or wiring change occurred. All two comparison allowances are consumed;
no additional packet is permitted under this campaign.

Across five successive transmissions since the recovered load, the green
output alternates upper-band/large/upper-band/large/upper-band. The final two
are identical A and have timely operator reports, removing changed scene
geometry as an explanation for that pair. Alternating scene-bank/update state
is a leading hypothesis. Bank assignments 1/0/1/0/1 are a software-model
prediction assuming initial bank zero and successful commits, not hardware
measurements. UART delivery to FPGA registers, actual coefficients, full live
image identity and the exact fault remain unmeasured. Rendering acceptance
remains NOT_ESTABLISHED.

Offline audit of the retained synthesized spu_scene_loader (SHA-256
d59390661dac131151b03f70aee9c3a0cf02d26ba4cb6c94ded9ecad707f67a5)
found correct active/candidate bank selection in 22 complementary bit-pattern
cases, indexed byte writes in 504 seeded-state cases covering all 63 byte
positions and both banks, and activation toggling in eight cases. This uses
the historical indexed-write mapping; the initial audit's assumption of the
current shift-register implementation was rejected and its failure preserved.
The result is offline combinational evaluation only. It establishes neither
routed timing nor live hardware configuration/register behavior. No RTL,
bitstream or acceptance criteria changed.

Evidence: hardware_12_identical_pairs/comparison_2.json, uart_3_a.json,
uart_4_a.json; rendering_diagnosis_01/{retained_bank_logic_audit.json,
audit_retained_banks.py,retained_bank_audit_initial_assumption.json,
five_transmission_bank_hypothesis.json}; recovery_2026-10-05.json, under
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/. Next useful physical diagnostic
is actual bank/coefficient state readback, after concrete review and separately
bounded readiness/authorization; further blind packet retries are not implied.

#### 3.35.9 — JTAG capture localizes active-bank descriptor corruption

Owner authorized current bank/green-coefficient readback and then reported
"Powered, unchanged, ready now." Contract §17 prospectively permitted one
GCAPTURE and the frozen 60-frame read set; it did not reopen any UART/load
campaign. Seventeen offline TAP/serialization/decoder/stop checks and 32
readiness/projection checks PASS. No native USB was opened by those checks.
Projection uses retained synthesized/routed netlists and pinned local X-Ray
FF ZINI locations, verified against retained FASM/frame initialization data.

The one physical command ran 2026-10-05T04:52:28.123108Z–
04:53:59.494091Z, terminal COMPLETE, exit 0, within its frozen 150-second
limit. One capture, 60 addressed frame reads and 21877 checked native bulk
operations were recorded. Each read contains 202 words, including 101 dummy
words excluded from decoding. Adapter serial CB81353DCE678119 and raw FPGA
IDCODE 0x13631093 were checked. STAT before/after is 0x401079fc, CTL0=0x501,
COR0=0x2003fe5. All 2591 selected static FF-control bits match the retained
image. Operator afterward reports "Stable lock; same image". No UART, FPGA
load, shutdown, reset, GRESTORE, wiring or bitstream change occurred.

Using the ZINI-inverted capture interpretation, raw bank 0 matches all 504
frozen Scene A bits. Bank 1 differs by exactly one bit: scene bit 346, green
triangle edge 1 B bit 14. Its expected signed value -480 (0xfe20) is captured
as -16864 (0xbe20). The active-bank selector captures 1; receiving,
commit_pending, payload_count and prepared-control state are zero. The
opposite-polarity control matches neither packet (504/503 differing bits)
and yields inconsistent settled-state controls. These controls support the
retained placement/alignment and inverted-polarity interpretation; full live
image identity and capture timing remain unmeasured.

Offline byte inspection identifies zero-based packet offset 44 (one-based
wire byte 45, payload offset 43): expected 0x0f (00001111), reconstructed
captured bank 0x0b (00001011), XOR 0x04. This maps to UART data bit D2,
expected 1 / bank-state 0. Expected D0..D3 are all high, so D2 lies within
a high run; it is not itself an expected rising edge. These are packet/bank
values, not a measured UART waveform or receiver-output byte. Electrical
slew/noise and transport origin remain unestablished. The model supplied the
same corrupt descriptor predicts green Sb=-6641600, while the shared capture
is -274968271552; Sa/Sc also differ. The isolated B1 corruption therefore
does not account for the captured arithmetic divergence or clear the physical
datapath. Evidence: diagnosis_campaign_01/byte_44_review.json.

Fault register: u_gpu.u_scene_loader.$auto$ff.cc:337:slice$30225,
SLICE_X35Y197/A5FF. Capture location: FAR 0x20b1f, word 95, bit 5,
CLBLM_L_X22Y197.SLICEL_X1.A5FF.ZINI. This is a logical-state mismatch at a
mapped register, not proof of a defective physical flip-flop or its cause.

The captured green edge is F1=460*x-16864*y-18400. With the other two captured
edges, software coverage is nonempty only for y=0..15, accounting for the
observed upper-band green output. Both raw banks' red descriptors match A.
The previously model-predicted bank alternation now has one physical selector
snapshot (bank 1); earlier selector states were not measured.

All six captured prepared A/B/C depth coefficients differ from the pinned S2
arithmetic prediction, even when S2 receives the captured malformed bank-1
descriptor. Both fractional scales match 33. All six captured coefficients
are exact multiples of the oracle reciprocal 33346; the red/green A terms
correspond to unscaled values each 16384 below prediction. This supports
further inspection of dot-product/setup arithmetic, but does not establish
the faulty stage or a second independent hardware defect. Additional oracle
ROM dependency is recorded with SHA-256
a64327c1bc0c8c74a4fb8c849a922a1f8b3d6a6e2e3bb58951d11f2012bb5248;
numerical expected_depth.json was frozen before execution. The software
reconstruction captured_state_model.png produces full red and thin striped
green at the top. It is a reconstruction from the captured values, not a
cycle/signal timing model or an independent physical acceptance result.

Offline enumeration of the target register's direct D LUT verifies all 32
FASM truth-table entries against the retained synthesized LUT after pin
permutation. Its configured static FF mux/control bits match in this read.
The D/CE/reset LUT truth tables themselves lie mostly in other minors not
read by the capture, so live write-path logic/routing configuration remains
unverified. No RTL repair or bitstream rebuild follows on this evidence.

Root-cause diagnosis remains open: bank-1 descriptor state is malformed and
prepared arithmetic is inconsistent, while physical timing, the write-path
configuration and the corruption mechanism remain unresolved. Next useful
measurement is selected static configuration of that register's D, CE and
reset path, retaining the captured-state evidence. The single capture slot
is consumed; further physical commands require their own bounded scope.
Original A/B acceptance remains NOT_ESTABLISHED.

Evidence: bank_capture_01/{authorization.json,operator_readiness.json,
projection.json,runtime_hashes.json,focused_checks.json,entrypoint_checks.json,
managed_result.json,capture_result.json,transport.jsonl,transport_summary.json,
decoded_capture.json,diagnosis.json,fault_register_write_path.json,
expected_depth.json,captured_state_model.png,operator_after_capture.json},
under build/gpu_evaluation/t1d_vertex_ab_2026-10-04/. Primary capture semantics:
https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content
(UG470 v1.17 pp.103,108,132). ZINI inversion basis:
https://github.com/openXC7/nextpnr-xilinx/blob/master/xilinx/fasm.cc.

#### 3.35.10 — Two diagnostic attempts: static write path and shared arithmetic

Owner prospectively authorized "Okay, authorize diagnosis. 3 attempts."
Contract §18 freezes three read-only diagnostic attempts, 180 seconds each,
540 seconds cumulative reserved, native USB cap 160 seconds. No UART, load,
reset, wiring, RTL or bitstream change. Earlier consumed budgets remain closed.
Operator readiness "Powered, unchanged, ready now" recorded at
2026-10-05T05:13:34.732986Z covered both launches while fresh.

Attempt 1: 2026-10-05T05:13:35.277122Z–05:14:16.178658Z,
COMPLETE/exit 0. Thirteen FARs read in two planned passes; all 204 selected
malformed-bank-register D/CE/reset LUT and FF-control bits match. No unstable
selected bit; all full frames identical across passes. Twenty-three protocol,
projection and stop checks plus 18 launch/readiness controls PASS offline.
Selected immediate configuration corruption is not observed; full routing and
physical timing are outside that projection.

Attempt 2: 2026-10-05T05:17:52.969956Z–05:19:24.245768Z,
COMPLETE/exit 0. One GCAPTURE, 60 FARs read once; 2017 logical state bits,
55 groups, all 3324 selected static controls match. Seventeen protocol/decoder/
stop checks plus 18 launch/readiness controls PASS offline. Previous captured
bank/prepared groups are unchanged, including bank-1 scene bit 346 wrong and
active_bank=1. All 24 latched dispatcher edge/depth fields match captured raw
inputs, including the malformed green B1. Reciprocal 33346 and exponent 33
match the prediction. Shared captured Sa/Sb/Sc are -1488384,
-274968271552, -16193629184; captured green descriptors predict -1472000,
-6641600, 986240000. Six prepared coefficients remain incorrect. No finding
here identifies a defective physical FF, timing violation or toolchain cause.

Offline extension of attempt-2 raw read interpretation compares 145200 bits
against retained frames after excluding all database FF ZINI locations and
word-50 ECC: zero differences. This extension was not a predeclared acceptance
gate. Unread configuration and correctness of emitted logic remain unmeasured.
An initially suspected pin permutation discrepancy was rejected: temporary
LUT permutation SITEWIRE sink labels were mistaken for physical CLB input
pins. Using the physical source pins, target D LUT FASM matches all 32 truth
cases. Retained artifacts and the rejected interpretation are preserved.
Primary explanation: https://github.com/openXC7/nextpnr-xilinx/blob/main/xilinx/arch_place.cc
(fixupRouting); current upstream source is not claimed as the retained binary's
source revision. Analysis helper field-offset errors and preparation's retained
carry-port name error were corrected offline before any physical command.

A broader offline consistency audit compares 6324 retained scene-loader/shared
depth-math LUT cells, 298976 physical truth cases, with emitted FASM: zero
mismatches. It excludes carry/DSP behavior, routing, timing and RTL-to-netlist
equivalence; this is not a physical acceptance gate. Audit artifact:
diagnosis_campaign_01/retained_lut_truth_audit.json.

Both attempts reviewed. Two slots used, one remains; 360 seconds reserved.
Final attempt is prepared for previously unread upstream bank/counter and
Sa-bit-14 static configuration: 864 bits, 33 FARs, two planned passes;
23 protocol/projection/stop checks and 21 readiness/reservation controls PASS.
No physical result for that final attempt yet. Root cause remains open and
original A/B rendering acceptance remains NOT_ESTABLISHED.

Evidence: diagnosis_campaign_01/{authorization.json,campaign.json,
operator_readiness.json,lut_permutation_audit.json}; attempt_01/{projection.json,
runtime_hashes.json,focused_checks.json,entrypoint_checks.json,
managed_result.json,measurement_result.json,transport.jsonl};
attempt_02/{projection.json,runtime_hashes.json,focused_checks.json,
entrypoint_checks.json,managed_result.json,capture_result.json,
decoded_capture.json,analysis.json,transport.jsonl}; attempt_03/{projection.json,
focused_checks.json,entrypoint_checks.json}, under
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/.

#### 3.35.11 — Final diagnostic read is inconclusive; hardware budget exhausted

Attempt 3 under contract §18 ran 2026-10-05T05:46:39.208917Z–
05:48:23.373170Z, terminal COMPLETE/exit 0 within the 180-second cap.
Owner reply "Authorized." to the fresh powered/unchanged/readiness request
was interpreted as confirmation to proceed; the literal reply and interpretation
are recorded at 05:46:38.718447Z. Earlier readiness is preserved separately.
No GCAPTURE, FPGA load, UART or reset was commanded. Sixty-six frame reads,
23927 checked native bulk operations all returned successful USB status.
STAT before/after is 0x401079fc; IR startup brackets unchanged.

Command completion is not measurement PASS. Frozen comparison reports
STATIC_READBACK_UNSTABLE: all 864 projected bits match in pass 0, 845 match
in both passes, 19 differ, zero stable mismatches. Thirty-one whole data
frames are identical. In pass 1, FAR 0x20b9f returns 101 all-ones data words
and FAR 0x2141b returns 101 all-zero data words. Their pass-0 payloads are
mixed and match the selected configuration. All 19 projected differences are
inside those two constant responses (11 FF-mux control bits, eight LUT INIT
bits). They do not establish changing FPGA configuration or silicon damage.
Classify the measurement INCONCLUSIVE_READBACK_DATA_ANOMALY. Successful USB
transfers and startup controls do not by themselves validate frame contents.

Operator afterward reports "Image or signal changed," then clarifies:
"Display change is that the green is no longer overlayed but interlaced.
Green is once again truncated." This identifies a picture change; signal
lock and operator intervention are not explicitly reported in the clarification.
Truncated/interlaced green is qualitatively consistent with the prior captured
malformed green coverage and incorrect depth coefficients, but no new state
measurement confirms the current selector, coefficients or cause of the change.
Probe noninterference is not established; causality remains open. All three
authorized diagnostic slots are consumed, 540 seconds reserved. Hardware
activity stopped. No fourth read, UART retry, load or reset is implied.
The earlier raw-bank and depth captures remain recorded evidence under their
stated placement/polarity/validity limits, not a repaired GPU acceptance result.

The executed worker remains frozen. A prospective guard separately rejects
complete-length all-zero/all-one frames contradicted by pinned static controls,
logs the raw candidate and stops before another frame. Seventy-nine offline
replay/fault-injection checks PASS (64 original frames accepted, two bad frames
rejected). Six integrated recorded-command replay controls PASS; it stops at
the first anomalous frame before later commands. No native USB was opened and
no further physical attempt occurred. This repair does not establish why the
payloads were invalid or make physical readback noninterference a proven claim.

Owner's overflow hypothesis was reviewed offline against the retained netlist:
37-bit term magnitude path, 40-bit signed sums, 40x17 full 57-bit multiply,
56-bit coefficient outputs. Frozen A and captured dispatcher inputs have
largest term 993600000 and largest expected scaled coefficient
32887159040000; all products, partial sums and scaled outputs fit. Exact
calculations equal the finite-width Python oracle, which explicitly models
37/40/56-bit truncation. Conservative closed 640x480 screen-domain bounds
also fit. This is a fixed-point integer path without M31 modular reduction;
an automatic 64-bit widening is not supported as a fix for these observations.
Full arbitrary 32-bit c-port values remain outside the documented sizing
domain; physical transient operands, mapping/timing and readback faults remain
unresolved. No RTL/bitstream change was made. A/B acceptance NOT_ESTABLISHED.

Evidence: diagnosis_campaign_01/attempt_03/{managed_result.json,
measurement_result.json,analysis.json,transport.jsonl,operator_after_measurement.json};
diagnosis_campaign_01/{campaign.json,operator_readiness.json,
operator_readiness_before_attempt_03.json,depth_width_audit.json};
diagnosis_campaign_01/readback_guard_repair_01/{validate_frame.py,
integration.patch,prospective_config_sequence.py,focused_checks.json,
integration_checks.json,preparation.json}, under
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/.

#### 3.35.12 — Proposed reciprocal/SPI/Z guard diagnosis rejected offline

Owner proposed a reciprocal alignment/ROM fault, late SPI packet drift and a
Python subclass rejecting green Z values above 65535 after 16-bit masking.
Pre-implementation review flags an unreachable rejection condition: every
masked field lies in 0..65535. Offline replay feeds the exact recorded bank
fault, packet byte 44 XOR 0x04 (scene bit 346, green B1 -16864). The proposed
subclass reports packet_complete, sets commit_pending and activates that
corrupted bank; all three green depths remain 700/400/3600. No proposed patch
was applied to software/RTL, no native USB opened and no new hardware attempt.

The selected sender and FPGA wrapper use CH340 115200-baud 8N1 UART, not an
RP2350 SPI master. Total wire packet is 64 bytes: A5 plus 63 payload bytes.
Two 252-bit records share packet byte 32; green depth occupies bytes 58..63.
The recorded error is in B1 at byte 44. The retained loader uses indexed byte
insertion, while current source/model shift; their byte-position semantics
were checked in the earlier retained bank logic audit. A Python model change
cannot repair the configured FPGA or establish electrical packet integrity.

Historical reference daedef2 reciprocal RTL already implements left-shift for
negative normalization amounts, correct ROM slice mantissa[14:7], 33-bit
product/error, 49-bit Newton result and output slice [46:31]. Expected values
for denominator 257600 are shift 2, mantissa 64400, ROM index 247, y 33346 and
exp 33. Captured shared y/exp agree, while captured dot products are already
incorrect. That does not support a reciprocal-only root cause. Optimizing
unused Newton product bits outside [46:31] is not itself truncation of the
output. This review is source/evidence consistency, not a physical correctness
or readback-validity measurement.

Discard the unreachable Z guard. Detecting arbitrary in-range corruption
requires additional independent integrity evidence; a checksum would require
a defined sender/receiver protocol and separate reviewed implementation scope.
Root cause and GPU acceptance remain unestablished. Three-attempt hardware
budget remains exhausted; no new packet/read/load/reset authorized here.

Evidence: diagnosis_campaign_01/proposal_review_01/{review_proposal.py,
review.json,historical_reciprocal_core.v}, under
build/gpu_evaluation/t1d_vertex_ab_2026-10-04/; source
software/spu_gpu_eval/{device_packet.py,device_arithmetic.py,device_loader.py};
tools/send_gpu_t1d_vertex_ab.py; hardware/boards/artix7/spu_a7_gpu_vga_top.v.

#### 3.35.13 — Campaign 02 baseline passes, capture frame rejected (2026-10-05)

The owner authorized the prospective three-attempt bank/depth contract and
then replied "Ready and powered. Proceed." The executor treated that as
contextual confirmation of the preceding unchanged/stable-lock/same-image
request; only readiness and power were explicitly restated. Preserve the raw
reply and interpretation rather than asserting an independent current image
observation. No new configuration identity was programmed or inferred.

Attempt 1 reserved one 360-second slot. Its measurement ran
2026-10-05T07:27:06.551932Z–07:28:00.307008Z, terminal FAILED/exit 1.
The two static passes completed all 30 planned reads. After one GCAPTURE,
four snapshot frames passed projected static controls; the fifth candidate,
FAR 0x0B9F, returned 101 all-zero data words, contradicting 29 of 76 controls.
The prospective guard preserved the candidate after DESYNC and halted before
the next frame. No final status bracket was reached. USB cleanup ran; no
recovery, UART, FPGA load or reset was commanded.

Classification: INCONCLUSIVE_READBACK_DATA_ANOMALY. This is a concrete
measurement failure, not a fresh raw-bank/depth result or evidence that the
live configuration became zero. Partial state is not interpreted. Root cause,
operator-reported post-measurement image/lock and rendering acceptance remain
unestablished at recording. Campaign 02 has one used slot, two remaining and
360 seconds reserved; hardware stops pending a specific correction/reviewed
diagnostic amendment. Earlier campaign budgets and failures are unchanged.

Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/`
`{authorization.json,operator_readiness.json,campaign.json,focused_checks.json,
runtime_hashes.json,state_encoding_review.json}` and
`attempt_01/{reservation.json,read_capture.py.started.json,
read_capture.py.result.json,managed_result.json,capture_result.json,
transport.jsonl,analysis.json,failure_review.json}`. Governing scope:
`spu_strategy/contract_gpu_t1d_bank_depth_diagnosis_2026-10-05.md`.

Owner later reports "Stable lock; same image — observed now" at executor
receipt 2026-10-05T07:34:31Z. This is outside the after-capture window/deadline
and is preserved as LATE_OBSERVATION_ONLY in
`diagnosis_campaign_02/attempt_01/operator_after_failure.json`. It records a
later stable display, without satisfying the expired gate, establishing probe
noninterference, repairing readback or reopening the failed attempt.

#### 3.35.14 — Campaign 02 static32 subset matches (2026-10-05)

With explicit powered/unchanged/stable-lock/same-image readiness, attempt 2
reserves its slot at 2026-10-05T07:56:20.741536Z. Measurement runs
07:56:29.746791Z–07:56:50.388873Z, exit 0/COMPLETE. Two passes over FARs
0x0B1F, 0x0B9F, 0x20B9F and 0x2141B complete all eight reads. The 271 pinned
static controls match both passes; unstable/mismatched bits are zero and
the repeated full frames agree. IR before/after is 0x35, STAT is 0x401079fc.
No GCAPTURE, UART packet, FPGA load, reset or recovery is commanded.

Only FDRO receive chunks change from 64 to 32 bits; the ID-chain scan and
frequency request are retained. Local adapter source selects different paths
above four bytes, but installed firmware identity and DMA causality are not
established. This subset result does not validate full captured FF state,
raw-bank/depth contents or display acceptance.

Owner later reports "Same as before. Authorized." at receipt 07:59:42Z,
outside the 60-second report window. Preserve unchanged display context as
LATE_OBSERVATION_ONLY; lock/intervention were not independently restated.
The native measurement remains COMPLETE, but the managed attempt is FAILED
on its operator gate. No expired gate is reopened. Two slots used, one remains;
720 seconds cumulatively reserved. A final reduced guarded snapshot is
prepared separately; it has no physical result at this entry's recording.

Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/`
`static32/attempt_02/{reservation.json,adaptive_plan.json,adaptive_checks.json,
read_capture.py.result.json,capture_result.json,transport.jsonl,analysis.json,
operator_late.json,managed_result.json,review.json}`; campaign `campaign.json`,
`operator_readiness_before_attempt_02.json`, `runtime_hashes_after_attempt_02.json`.
Scope: `spu_strategy/contract_gpu_t1d_bank_depth_diagnosis_2026-10-05.md` §12.

#### 3.35.15 — Campaign 02 final 32-bit snapshot rejected (2026-10-05)

Owner answers "Confirmed." to the composite final readiness request. The
executor records contextual confirmation of power, unchanged configuration/
wiring, stable lock and same image; individual conditions were not restated.
Attempt 3 reserves the last slot at 2026-10-05T08:17:26.842978Z, deadline
08:23:26.842978Z. The measurement runs 08:17:34.844679Z–08:18:42.357197Z,
exit 1/FAILED, within its 180-second limit.

All eight static reads pass. After one GCAPTURE, eighteen selected snapshot
frames pass pinned controls. Candidate 19, FAR 0x2079F, returns 101 all-zero
data words, contradicting 50 of 107 selected static controls. The dummy frame
is also zero. The guard preserves the candidate after DESYNC and stops before
the next frame. IR captures around the rejected read remain 0x35; the final
STAT/IR bracket is not reached. USB release returns zero and close/exit run.
No recovery, UART packet, FPGA load or reset is commanded.

Classification: INCONCLUSIVE_READBACK_DATA_ANOMALY. The 32-bit FDRO chunk
change alone does not qualify full snapshot readback. Partial state is not
decoded as new bank/input/sum evidence. Neither UART noise, adapter DMA cause,
physical arithmetic correctness nor GPU root cause is established. A current
post-measurement display report has been requested but is unavailable at this
entry's recording; no noninterference or rendering acceptance is inferred.

Campaign 02 closes exhausted: three slots used, zero remaining, 1080 seconds
cumulatively reserved; hardware execution is disabled. The identical-A pair
is incomplete and no new packets were sent in this campaign. Earlier budgets,
failures and observations remain preserved.

Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/`
`snapshot32/attempt_03/{adaptive_plan.json,adaptive_checks.json,
prelaunch_review.json,reservation.json,read_capture.py.result.json,
capture_result.json,transport.jsonl,failure_analysis.json,managed_result.json,
review.json}`; campaign `campaign.json`, `operator_readiness.json`,
`operator_readiness_before_attempt_03.json`, `runtime_hashes_after_attempt_02.json`.
Contract: `spu_strategy/contract_gpu_t1d_bank_depth_diagnosis_2026-10-05.md` §12.1.

#### 3.35.16 — Offline audit of the rejected readback transaction (2026-10-05)

The retained journal's preceding good FAR 0x2071F and rejected FAR 0x2079F
requests exactly match the pinned 52-word sequence, differing only at FAR
word index 15. Each records 202 FDRO scans: 201 at 32 bits and the final 31
bits plus checked exit bit. Native return statuses, reply lengths, logged
shift inputs and reconstructed words agree. The failed transaction's 808
FDRO body bytes are already zero in USB IN replies before Python word
conversion; its full dummy/data frame is zero. The preceding data frame has
42 distinct words. CFG_OUT and subsequent CFG_IN IR captures are 0x35.

Eight offline checks reject altered request bits, reply bytes, return status,
length, exit position, width and word assembly. No device was opened. This
audit identifies where zeros enter the recorded host data path; it cannot
distinguish adapter execution, physical TDO, timing, FAR delivery or live
configuration mismatch. Earlier bank-bit and depth mismatches remain
unconfirmed leads. Neither successful static subsets nor 18 passing snapshot
frames qualify a complete snapshot or establish GPU faults.

Campaign 02 remains exhausted. The pending monitor observation has not been
supplied at this recording; preserve any later reply as additional context,
late if outside the window, without restoring validity or claiming causal
probe noninterference. A separate inactive four-read/two-address static test
is prepared and passes 53 offline checks; it has no new physical authorization
or result.

Evidence: campaign-02 `readback_transaction_review_01/{extract_transaction.py,
check_review.py,review.json,focused_checks.json,preceding_good.jsonl,
rejected.jsonl}` under `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/`;
retained journal SHA-256
`d71f7de029c0402c91d9badd0daa0fb5dad91ab4920ac3e75ea7c6cade790ff8`.
Prospective bundle: `build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/`.
Draft: `spu_strategy/contract_gpu_t1d_readback_transaction_qualification_2026-10-05.md`.

#### 3.35.17 — Static transaction qualification amended to three slots

Owner replies "Authorized, 3 attempts." at executor receipt
2026-10-05T09:11:50Z. Preserve the preceding single-attempt draft and amend
the prospective two-address static test to three attempts maximum: 120 seconds
each, 360 seconds cumulative reserved, 60-second subprocess and 45-second
native limits. Each retains four reads, 221 controls and no GCAPTURE, UART,
FPGA load/reset or recovery. Prior campaign-02 exhaustion remains unchanged.

Seventy offline checks pass, including separate attempt/source archives,
preservation of failed results, refusal of unreviewed/blind retries, reviewed
corrected retry and stopping after static qualification. Native USB opened:
zero; physical slots consumed: zero at recording. No new physical readback,
bank/depth or GPU diagnosis is established. Current readiness remains required.

Evidence: `build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/`
`{owner_authorization_received.json,manifest.json,focused_checks.json,
check_attempts.py}` and `before_three_attempt_amendment_01/`.
Scope: `spu_strategy/contract_gpu_t1d_readback_transaction_qualification_2026-10-05.md`.

#### 3.35.18 — Two-address static qualification matches; stop after PASS

Owner directly confirms powered/unchanged/stable-lock/same-image readiness at
2026-10-05T09:20:51Z. Qualification attempt 1 runs
09:20:51.639604Z–09:21:01.238404Z, COMPLETE/exit 0 (9.60 seconds).
Read order is 0x2071F, 0x2079F, 0x2071F, 0x2079F. All 221 pinned static
controls match both passes; unstable/mismatched bits are zero and repeated
full frames agree. Data has 42 distinct words at 0x2071F and 44 at 0x2079F.
Both status brackets complete: IR 0x35, STAT 0x401079fc before/after.
USB cleanup completes; no GCAPTURE, UART, FPGA load/reset or recovery is sent.

Classification: STATIC_TWO_ADDRESS_CONTROLS_MATCH. This confirms the selected
static reads work in this measurement, including the previously rejected
address. The all-zero result is not reproduced by this short static sequence.
It does not qualify full snapshots or isolate capture/history/timing/adapter
causes. Earlier bank-bit/depth mismatches remain unconfirmed diagnostic leads;
GPU root cause and display acceptance remain unestablished.

The immediate after-measurement report is unavailable at closeout and its
60-second window has expired. The phase gate and probe noninterference remain
unestablished; preserve later replies as context only. The measurement remains
COMPLETE. Stop after PASS with one used slot, two unused and 120 seconds
reserved within the authorized 360-second maximum; physical execution disabled.

The earlier campaign-02 monitor receives additional late context through the
new readiness reply at 09:20:51Z: current stable lock and same image are
reported. Preserve it in campaign-02 `operator_later_readiness_context.json`;
it is not an independently bound immediate after-failure comparison, does not
reopen the expired gate and does not establish causal noninterference.

Evidence: `build/gpu_evaluation/t1d_readback_qualification_20261005/draft_01/`
`attempt_01/{reservation.json,authorization.json,operator_readiness.json,
runtime_hashes.json,executed_sources/,transport.jsonl,result.json,analysis.json,
review.json}` and root `manifest.json`. Contract:
`spu_strategy/contract_gpu_t1d_readback_transaction_qualification_2026-10-05.md` §7.

Owner later replies "Image is identical to last." at executor receipt
2026-10-05T09:25:04Z, about 242.76 seconds after measurement completion and
outside both the 60-second report window and attempt deadline. Preserve it
as LATE_OBSERVATION_ONLY in qualification `attempt_01/operator_late.json`.
It records unchanged image context. An observation timestamp, current lock
and intervention were not separately supplied; do not manufacture them.
The expired phase gate remains unestablished. Static subset PASS, full-snapshot
uncertainty, one used/two unused slots and the physical stop remain unchanged.

#### 3.35.19 — Offline comparison: anomalies also occur in static readback

Compare four retained journals offline: campaign-01 attempt-03 static64,
campaign-02 attempt-01 snapshot64, campaign-02 attempt-03 snapshot32 and the
short two-address static32 qualification. All reconstructed requests match
the retained 52-word read sequence; each assembled 202-word frame agrees
with logged scan data. Native bulk error counts are zero in these journals.
No new adapter access, UART, load, reset or hardware attempt occurs.

The older 66-read static64 routine issues no GCAPTURE. Its first pass matches
all selected static controls. On its second pass, read 48 at 0x20B9F returns
101 all-ones data words (11/17 controls disagree); read 55 at 0x2141B returns
101 zero data words (8/16 disagree). The next different-address reads, 49 at
0x20BA0 and 56 at 0x2141C, have mixed data and matching controls. They occur in
the same connection without an adapter reopen. This historical worker lacked
the current guard; its continuation does not authorize proceeding after a
contradiction in any future test. Final startup/status brackets are healthy.

Campaign-02 snapshot64 rejects 0x0B9F at total read ordinal 35 (snapshot frame
5). The later snapshot32 run reads 0x0B9F correctly both before and after
GCAPTURE, then rejects 0x2079F at total ordinal 27 (snapshot frame 19).
The subsequent short static32 qualification reads 0x2079F correctly twice.
Failures therefore do not stay at one address or one ordinal/chunk width.
The retained static-only anomaly shows a new GCAPTURE command is not required
within the failing read routine; it does not prove prior capture state has no
effect. GCAPTURE alone, a fixed unreadable FAR or a permanently stuck adapter
is insufficient to explain all these observations.

Priority lead: intermittent validity of the configuration-data transaction or
its adapter/physical receive path. IR 0x35 and USB success do not establish
that the FPGA accepted FAR/RCFG/FDRO or that received frame data is valid.
Host requests and assembly are internally consistent; actual TCK/TDO, adapter
firmware build identity and FPGA request acceptance remain unmeasured. The
logs do not distinguish ordering/history, adapter execution, electrical timing
or configuration readout. Earlier bank/depth faults remain unconfirmed leads;
no physical arithmetic or UART cause is established.

Evidence: `build/gpu_evaluation/t1d_vertex_ab_2026-10-04/diagnosis_campaign_02/`
`offline_log_diagnosis_01/{summarize_history.py,analysis.json}`. The analysis
records all four journal SHA-256 values and per-frame request/assembly/control
comparisons. Existing campaigns and physical stops are unchanged.

The older 0x20B9F all-ones anomaly retains 101 zero dummy words followed by
101 all-ones data words. Its 64-bit USB reply crossing that boundary is
`00000000ffffffff`; preceding/following replies are respectively all zero/
all one, with the final 63-bit reply's unused bit correctly zero. Thus a
constant-high input across the entire transaction is insufficient to explain
this response. The pattern motivates checking configuration request/address
acceptance and data selection; it does not establish either as the cause.

The offline comparison originally counted both candidate and completed-read
events in the short qualification. Preserve that draft output separately,
then select one event kind per physical read: corrected totals are 66, 35,
27 and 4 frames. No original journal or hardware result changed. The final
analysis also pins its script hash and dummy/data details. No new tests or
physical qualification are claimed by this retained-log calculation.

#### 3.35.20 — Offline request review: FAR read source and address fingerprints

Review the frozen bitstream headers, recorded CTL0, retained static projections
and local adapter sources without opening native USB. Recorded CTL0 is 0x501:
FARSRC bit 7 is clear. AMD UG470 v1.17 table 5-27 specifies ECC error-frame
address output for FAR[23:0] in that setting. Reject a proposed direct FAR echo
guard before implementation. The bitstream's CTL0 write payloads are 0x501,
but their MASK values exclude bit 7; those payloads alone do not establish a
FARSRC write. A simple post-read address equality check also needs to account
for frame-address advancement. Reference:
[AMD UG470](https://docs.amd.com/api/khub/documents/FOs3lXmlcWxBhTIFxVKyGA/content),
tables 5-23, 5-27 and chapter 6. No MASK/CTL0 write is proposed for execution.

The recent 0x2071F/0x2079F static projection has 35 common positions with no
opposing expectations. Cross-checking the actual retained frames against the
other address's controls nevertheless yields 34 and 29 mismatches; swapping
those observed frames would be rejected. This does not invalidate the prior
selected-control PASS or establish an address fault.

Select a stronger explicit fingerprint pair offline: 0x217A1 and 0x217A2,
128 known static bits each, 56 opposing positions. Each address matches in
both retained campaign-01 passes. Both fingerprints include zeros and ones,
and discriminate each other at those 56 positions. Verify retained projection
input hashes against PNR/FASM/frames/device database. Prepare exact unchanged
52-word requests with only FAR values changed, and a four-read A,B,B,A design.
This remains DESIGN_ONLY_NOT_AUTHORIZED; four reads cannot exclude a failure
dependent on longer transaction history. The closed qualification's unused
slots remain unused. No worker activation or physical attempt occurs.

Local adapter source review finds no demonstrated cause matching the anomaly.
Polling/DMA selection and the extra consumed FIFO push are recorded; they do
not establish loaded firmware behavior. A CMD echo must precede FDRO arming,
and alone cannot prove FAR or FDRO acceptance. Do not interpose the existing
reset/sync register helper in a pending FDRO response. Root cause remains
NOT_ESTABLISHED; no new GPU state, UART noise or physical arithmetic claim.

Evidence: `build/gpu_evaluation/t1d_readback_qualification_20261005/`
`request_review_01/{review_request.py,review.json,protocol_review.md}`;
`before_cross_check/` preserves the initial offline output/source. The review
records source hashes, parsed packet writes, full opposing-bit details and
retained-frame comparisons. Corrected the local result key before first
output generation; no hardware access or attempt was consumed.

#### 3.35.21 — Prepared A,B,B,A worker and bounded draft; no hardware execution

Prepare prospective copies of retained checked helpers under
`build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/`. Worker read
order is exactly 0x217A1,0x217A2,0x217A2,0x217A1. Each completed candidate
must match all 128 pinned static bits for that address before another request.
Keep the 52-word request, 202-word response, 32-bit receive chunks, native raw
reply/status journal, retained DESYNC and immediate guard stop. No FAR echo or
new register command is added.

417 offline checks PASS; no native USB opened. Mutate every projected bit;
reject swapped, wrong-address stale, zero/one-filled frames at every sequence
position and truncated raw/frame replies. Assert preserved candidates, retained
cleanup and no subsequent request. Check identical 32/64-bit TAP traces and
data; activation/launch refusals, report binding/expiry, separate source archives,
guarded corrected retries and timeout slot accounting. A byte-identical stale
B reply is accepted in an explicit limitation fixture: static bytes cannot
prove freshness for the B,B step. Do not claim universal stale-reply rejection.

Seal 22 helpers/data/report files; verify retained projection source hashes
and that predecessor workers are unchanged. The sealed DRAFT worker refuses
launch with exit 1 before slot reservation/native access. Three attempts are
proposed, 120 seconds each/360 seconds cumulative, subprocess 60/native 45;
none is authorized or consumed. Native deadline expiry is recorded as TIMEOUT,
separately from a static mismatch. Stop after a passing sequence; failures need
diagnosis and a checked correction before retry, no blind repeat.

Contract: [T1d address fingerprint draft](../spu_strategy/contract_gpu_t1d_address_fingerprint_2026-10-05.md).
Preparation does not qualify any physical read, long snapshot, GPU arithmetic
or display result. Earlier failures, unconfirmed bank/depth leads and the closed
qualification's two unused slots remain preserved. Root cause NOT_ESTABLISHED.

#### 3.35.22 — Four static address fingerprint reads PASS; campaign closed

Owner authorizes and confirms current readiness with "Authorized and ready."
in response to the prepared combined question, receipt 2026-10-05T19:16:12Z.
Preserve raw approval and the contextual readiness interpretation. Activate
the three-slot 120-second/360-second budget in the address-fingerprint contract.
Attempt 1 runs 19:16:40.147985Z–19:16:49.731953Z, COMPLETE/exit 0, about
9.58 seconds. Physical read order is 0x217A1,0x217A2,0x217A2,0x217A1.

Each frame matches all 128 declared static bits for its requested address;
all 256 projected bits are stable over their repeated observations. Zero
static mismatches/unstable bits; repeated full data frames identical. Every
returned frame differs from the opposite fingerprint at exactly 56 positions.
Distinct data-word counts are 42 for A and 48 for B. Startup brackets remain
IR 0x35, STAT 0x401079fc; CTL0 0x501. Native bulk errors zero and USB cleanup
complete. All archived executed sources match the attempt's runtime seal.
No UART, GCAPTURE, reload, reset or recovery is sent.

Operator reports "Stable lock; same image; no intervention — observed now".
Record at 19:17:37.783229Z within the required window/deadline; the operator
phase gate passes. This records unchanged display context, not proof of causal
probe noninterference or display/rendering acceptance.

Classify STATIC_FOUR_READ_FINGERPRINT_SEQUENCE_MATCH. The observed static
fingerprints follow the requested address changes, repeat at B and return to A
in this four-read sequence. This qualifies these selected reads only; it does
not qualify a long snapshot, prove freshness of identical B bytes, identify
adapter firmware or resolve earlier bank/depth leads or the display fault.
Root cause NOT_ESTABLISHED.

Review closes physical execution after the PASS: one slot consumed, two unused,
120 seconds reserved within the approved 360 seconds. Do not spend unused slots
on repeats or a longer experiment under this closed contract. Evidence:
`build/gpu_evaluation/t1d_address_fingerprint_20261005/draft_01/attempt_01/`
`{reservation.json,authorization.json,operator_readiness.json,runtime_hashes.json,
executed_sources/,transport.jsonl,result.json,analysis.json,operator_after_read.json,
review.json}`; journal SHA-256
`2127be1ed3ff9bee785fef53503bcba275ea6d2e1729e7fd01296272b7d9eb62`.
Preserve the offline summary correction from len(integer) to integer counts;
it occurred before summary output creation and did not change hardware results.

#### 3.35.23 — Extended static readback draft prepared; no physical launch

After two owner replies "Authorized", proceed with preparation of a longer
diagnostic, keeping FPGA power/wiring/configuration unchanged. Preserve the
interpretation as preparation authorization; no new numerical physical budget
or current readiness is manufactured from those short replies. A server restart
interrupts preparation before the new bundle exists; recovery checks confirm
the prior campaign remains closed with two unused slots and no repeat occurs.

Prepare prospective copies under
`build/gpu_evaluation/t1d_readback_history_20261006/draft_01/`: 64 reads in one
connection, A,B,B,A repeated 16 times, same static fingerprints/32-bit receive
and per-candidate stop. Earlier failing ordinals were 27,35,48,55; extending
to 64 reaches beyond them but does not replicate their address order or prove
transaction history is causal. Keep capture/UART/load/reset/firmware changes
excluded. No new physical operation occurs during preparation.

Propose three attempts capped at 270 seconds each/810 seconds cumulative,
subprocess 210/native 180 seconds. Size bounds using predecessor frame
intervals about 2.2–2.5 seconds; this is an extrapolation, not measured 64-read
performance. Original qualification remains closed; no unused slot is reused.

Preliminary syntax, pure 64-read comparison and eight mocked activation checks
PASS, native USB opened zero. Correct overlapping literal timeout replacements
before full checking/sealing/activation, and bind fixture limits to the actual
draft manifest. Full offline fixtures cover complete 32/64-bit TAP trace parity,
malformed replies and stops at late ordinal positions, per-bit mutation, source
archives, accounting and operator gates. A byte-identical stale reply remains
unobservable. Use one detached offline check launch with a frozen 600-second
limit; terminal result, final review and runtime sealing remain pending.

Contract: [Extended readback history draft](../spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md).
Evidence: named draft bundle's prospective workers, `manifest.json`,
`provenance.json` and `preliminary_review.json`. Root cause remains
NOT_ESTABLISHED; neither a GPU diagnosis nor physical qualification is added.

#### 3.35.24 — Extended readback worker: 498 offline checks PASS and sealed

Interpret the extended draft's detached job only after finding exactly one
terminal marker: COMPLETE, exit 0. Unit
`spu-offline_check_01-20261005T193747Z-219529` runs
2026-10-05T19:37:47Z–19:41:56Z, 249 seconds under its 600-second frozen limit.
stdout records 498 checks PASS; stderr empty. Native USB opened false.
The full 64-read mock agrees across 32/64-bit receives in TAP edge trace,
word data and 532902 modeled clock edges; late-failure/timeout/refusal fixtures
and the identical-stale limitation are exercised. No physical qualification.

Check worker hashes against the pre-launch checkpoint and frozen projection
inputs: all match. Preserve previous workers and executed evidence unchanged.
Seal 22 helper/data/report files. The sealed draft refuses an unauthorized
launch before reservation/native access, exit 1 with Draft or inactive
qualification. No slot consumed, execution false, attempts_used 0.

The three-attempt 270-second/810-second physical budget remains proposed;
earlier preparation approval does not activate it. Current operator readiness
and the frozen budget approval are required before physical execution.
Evidence: `build/gpu_evaluation/t1d_readback_history_20261006/`
`offline_check_01/{COMPLETE,result.json,stdout.log,stderr.log,unit_name}` and
`draft_01/{focused_checks.json,runtime_hashes.json,preparation_review.json}`.
GPU root cause NOT_ESTABLISHED; no capture, UART, reload, reset or physical
read occurs in this preparation/review.

#### 3.35.25 — Extended static readback fails after 22 valid reads; retry held

Owner reply "Confirmed." is received at 2026-10-05T19:55:15Z in response to
the combined budget/readiness question. Activate three attempts capped at
270 seconds each/810 seconds cumulative, subprocess 210/native 180 seconds,
64 static reads max, no capture/UART/load/reset. Preserve raw authorization
and contextual readiness interpretation. A separate native USB identity and
claim/release/close check completes at 19:56:08.928503Z without bulk JTAG
commands or TAP clocks; it consumes no physical slot.

Attempt 1 runs 19:56:19.215522Z–19:57:14.842806Z, FAILED/exit 1, about
55.63 seconds. A,B,B,A repeated sequence validates 22 candidates, then rejects
candidate 23 at B=0x217A2: all 202 words are zero, including 101 pipeline words.
The requested fingerprint disagrees at 44/128 static positions; opposite A
disagrees at 84. No subsequent frame request or final STAT bracket occurs.
IR captures around the failed read are 0x35, native bulk errors zero, USB
release/close/exit complete. No UART, GCAPTURE, reload, reset or power cycle.
All 22 executed helper/data/report archives match the runtime seal.

Offline audit of adjacent reads 22 and 23 finds both request the same B address.
Both exact 52-word requests, all 281 outgoing native packets and logged TDI
scan/exit sequences are identical. Read 22 has 48 distinct data words; read 23
already has 808 all-zero FDRO body bytes in native USB responses before Python
conversion. Both candidates agree with their recorded scans. This reproduces
invalid static readback without an adjacent address switch; it does not identify
adapter execution, FPGA request acceptance, firmware behavior or physical TDO.

Preserve the initial offline summary that counted a following 5-bit CFG_IN IR
body byte a8. Final analysis correctly selects 202 FDRO bodies (31/32 bits),
808 zero bytes. No worker or hardware changes result from that summary correction.
Root cause remains NOT_ESTABLISHED. Earlier bank-bit/depth mismatches remain
unconfirmed diagnostic leads; no new GPU arithmetic or transport fault is claimed.

Owner reports "Stable lock; same image; no intervention — observed now";
observed at 19:59:43.268632Z, recorded at 19:59:43.347339Z. Preserve as
LATE_OBSERVATION_ONLY after the 60-second window; operator phase gate false.
The report supplies display context, not readback validity or probe noninterference.

Manifest AWAITING_REVIEW, physical execution false, one slot consumed/two
remaining, 270 seconds reserved of 810. Hold retry pending a specific correction,
focused validation and review/readiness gates; no correction is established.
Preserve authorization, failed attempt and source seals. Contract:
[Extended static readback history](../spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md).
Evidence: `build/gpu_evaluation/t1d_readback_history_20261006/`
`draft_01/attempt_01/{result.json,analysis.json,operator_after_read.json,diagnostic_review.json,transport.jsonl}`
and `transaction_review_01/{audit_pair.py,review.json,preceding_good.jsonl,rejected.jsonl}`.
Journal SHA-256:
`c8b83219ef341256285f73c19171dfaf52d17507f3dfa7b1b966563dfd601e9d`.

#### 3.35.26 — CMD checkpoint amendment approved; offline worker prepared

Owner replies "Approved and ready." to the explicit CMD checkpoint scope
question; record at 2026-10-05T20:19:17.087061Z in
`build/gpu_evaluation/t1d_readback_history_20261006/scope_amendment_authorization_01.json`.
The amendment adds a CMD read after RCFG and before FAR/FDRO, using only the
two remaining slots and existing physical bounds. It replaces the active
contract's CMD-read exclusion prospectively; no other scope/budget changes.
This corrects a missing command-state observation, not an established cause
of the all-zero reply. Root cause NOT_ESTABLISHED.

Prepare prospective worker copies in `cmd_checkpoint_worker_01/`; retain
active workers, seal, failed attempt and accounting unchanged. Transmit the
17-word preparation/CMD-read request, consume one 32-bit reply and require
its low five bits equal RCFG=4 before the 38-word FAR/FDRO continuation.
No reset/resync/DESYNC is inserted between checkpoint and continuation.
Keep 202-word frame reads, per-candidate static guards and ABBA repeated 16.
Successful amended classification is distinct from the original experiment.

Syntax and first-CMD-zero rejection preliminary checks PASS, no native USB
opened and no physical slot consumed. Prepare independent TAP continuation,
CMD mismatch/zero/one/truncation, static/transport and reservation/report checks
under one new detached offline validation capped at 600 seconds. Full result,
release review and amended runtime seal remain pending. This entry records
preparation only; no physical CMD checkpoint or GPU state is established.

Contract: [Extended readback history, approved amendment](../spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md).
Active manifest remains AWAITING_REVIEW/execution false, one slot used/two
remaining. Preserve the readiness statement; the bound 300-second freshness
rule still applies before later physical execution. No UART/capture/load/reset.

#### 3.35.27 — Amended offline validation: 601 PASS; existing campaign released

Exactly one terminal marker COMPLETE/exit 0 is present for detached unit
spu-cmd_offline_check_01-20261005T202207Z-227279, running
2026-10-05T20:22:07Z–20:25:42Z, 215 seconds under the 600-second limit.
stdout records 601 checks PASS, stderr empty, native USB opened false. Modeled
32/64-bit data and full TMS/TDI traces agree across 543270 edges. The added
CMD mismatch/truncation and continuation fixtures pass; no physical checkpoint
or GPU diagnosis is established by these offline results.

Prepared source hashes and projection provenance inputs match. Preserve prior
active sources/22-file seal in `draft_01/before_cmd_checkpoint_amendment_01/`
and leave attempt 1's executed archives untouched. Promote the tested helpers
into the existing campaign and seal 23 files; do not activate a second counter.

Owner reply "Authorized and ready." is bound to readiness recorded at
20:27:01.090304Z; preserve contextual interpretation of powered/unchanged setup
and stable lock/same image, not separately enumerated in the short reply.
The reviewer at 20:27:01.512200Z accepts the approved measurement-gap correction
evidence and releases attempt 2, state REVIEWED_NEXT_ATTEMPT/execution true.
One slot remains consumed/two available before launch; limits unchanged.
The physical fault is not repaired or localized by this source change.

Evidence: `build/gpu_evaluation/t1d_readback_history_20261006/`
`cmd_offline_check_01/`, `cmd_checkpoint_worker_01/` and
`draft_01/{amendment_release_01.json,runtime_hashes.json,attempt_01/review.json}`.
Host access/current readiness remain prerequisites to physical execution;
attempt 1 stays FAILED and its operator gate false. Root cause NOT_ESTABLISHED.

#### 3.35.28 — Attempt 2: all 64 CMD checkpoints and static reads PASS

Host access check 02 completes at 2026-10-05T20:27:55.753136Z without bulk
JTAG commands or TAP clocks. Authorized attempt 2 runs
20:28:02.602156Z–20:30:41.579267Z, COMPLETE/exit 0, 158.98 seconds within the
unchanged external 210/native 180/attempt 270-second bounds.

All 64 CMD checkpoint replies are raw 0x4 and pass the low-five-bit guard
before FAR/FDRO. All 64 static reads match their declared A/B fingerprints;
256 projected bits each have 32 observations, zero unstable/mismatched bits.
Full data frames repeat identically per address. IR brackets remain 0x35,
STAT brackets 0x401079fc, CTL0 0x501. Native bulk errors zero, release/close/
exit complete. All 23 executed archives match the runtime source seal.
No UART, GCAPTURE, reload, reset or power cycle is sent.

Classification STATIC_64_CMD_CHECKPOINT_CONTROLS_MATCH qualifies the selected
static controls under this amended sequence only. The changed request split,
USB calls and timing are not isolated by this PASS. Do not claim a physical
repair, complete snapshot validity, fresh identical replies, full live-image
identity, physical TDO or GPU fault diagnosis. Prior bank/depth leads remain
unconfirmed; attempt 1's original-sequence failure is preserved.

Request the post-read monitor observation immediately; deadline
20:31:41.579267Z for both observation and receipt. Report is pending at this
entry; do not infer stable display from pre-execution readiness. The passing
measurement requires closure: two slots consumed/540 seconds reserved of 810,
one slot left unused; no repeat or new snapshot campaign under that slot.

Evidence: `build/gpu_evaluation/t1d_readback_history_20261006/draft_01/attempt_02/`
`{reservation.json,runtime_hashes.json,executed_sources/,transport.jsonl,result.json,analysis.json}`.
Journal SHA-256:
`91bf1fbd8a03b301e83a10abf1d70c7a72958bb8213d42d70c04b37ed0259939`.
Contract: [Extended readback history](../spu_strategy/contract_gpu_t1d_readback_history_2026-10-06.md).

Closeout: no post-read monitor report is received within the 60-second window.
Preserve `attempt_02/operator_report_status.json`; operator gate unestablished.
The sealed reviewer records measurement_qualified true/operator_gate false
and closes the campaign, state STATIC_HISTORY_QUALIFIED/execution false.
Two slots consumed, one closed unused; no third repeat or new snapshot scope.
Preserve any later operator reply separately as late context. Physical static
PASS does not establish display acceptance or causal probe noninterference.

#### 3.35.29 — Snapshot draft review: uniform-frame guard gap; no hardware run

Prepare a separate snapshot-frame qualification draft after the closed static
campaign. Preserve its missing timely monitor report and closed unused slot;
neither display noninterference nor authorization for a new capture is inferred.
No physical budget is set or activated, no native USB access occurs, and no
hardware attempt is consumed.

Offline review verifies the retained 48-FAR/1667-bit reduced projection's
source hashes and guard coverage. FAR 0x2151F has seven controls all expecting
1; an all-one data frame would satisfy this guard. The other 47 captured FARs
have both expected values. This identifies a prospective rejection-test gap,
not an observed all-one physical read at that FAR.

HALT before implementation under AGENTS.md §2. Minimal proposed correction:
add a source-proven immutable expected-zero control at 0x2151F and require
both expected values in every captured FAR's guard. Preserve old projections;
do not invent an unlisted zero bit or use live FF values as static controls.
Freeze feature mapping/source hashes and validate uniform/per-bit rejection
before releasing a new worker. Static validity alone cannot prove capture
freshness, clock alignment, polarity or coherent runtime operands.

Contract: [Snapshot frame qualification draft](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/review_01/`
`{review_inputs.py,review.json}`; status HALTED_PRE_EXECUTION_REVIEW, physical
execution false. GPU and adapter root causes remain NOT_ESTABLISHED.

#### 3.35.30 — Authorized offline snapshot guard repair; 3165 checks PASS

Owner reply "Authorized repair." permits the identified static guard correction.
Create prospective projection/guard copies under
`build/gpu_evaluation/t1d_snapshot_qualification_20261006/repair_01/` while
preserving the original review, projections, workers and closed campaign.
No physical budget/authorization is inferred; no native USB or hardware slot.

Enabled frozen FASM feature CLBLL_L_X42Y186.SLICEL_X1.AFFMUX.O6 has database
encoding `30_04 !31_00 !31_01 !31_02`. Verified tilegrid base 0x21500 and offset
73 map !31_00 to FAR 0x2151F, data word 73, bit 0, expected zero. Frozen word
0x00308218 agrees, and all four feature encoding tokens are verified against
the frozen frames. This is a mux configuration control, not captured ZINI;
the selected location is absent from the runtime projection. Preserve source
hashes and full derivation in proof.json.

Append one expected-zero control to both prospective lists; projection static
guards become 2836 and full frame guards 2852. The latter covers 49 FARs,
including all 48 capture FARs plus a retained baseline FAR. Both expected values
are present at every guard FAR. Original controls and 1667-bit runtime mapping
remain unchanged. Prepare coverage preflight that rejects missing binary coverage,
duplicate/undeclared/ECC controls and malformed or boolean numeric fields;
no physical snapshot worker is implemented/released.

3165 focused checks PASS offline: reproduce old all-one acceptance at 0x2151F
and reject it after repair, accept frozen static controls, reject uniform zero/
one and malformed frame extents, mutate every selected control, remove each
FAR's zero coverage and check schema refusals. Hash-verify the retained frame
validator against attempt 2's executed source seal. Old projection/guards and
all runtime mapping fields are preserved. No new physical result is established.

Evidence: `repair_01/{derive_guard.py,proof.json,projection.json,frame_guards.json,
guard_coverage.py,check_repair.py,focused_checks.json}`; contract
[Snapshot frame qualification draft](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
The guard blocker is resolved for prospective use. Capture freshness/clock/
polarity, runtime operand association, GPU cause and display noninterference
remain unqualified; the predecessor's missing timely monitor report and closed
unused slot remain unchanged. New snapshot budgets/worker release remain unset.

#### 3.35.31 — Three new snapshot attempts authorized; worker preparation only

Owner reply "Authorized 3 tries, ready and powered." is retained verbatim with
receipt UTC in the new snapshot campaign's `owner_authorization_received_01.json`.
Interpret approval as the proposed snapshot qualification with at most one
GCAPTURE per attempt. Freeze three attempts, 270 seconds each, 810 cumulative,
210-second external and 180-second native limits, conservatively retaining the
prior caps; the short owner reply did not separately restate those numeric caps.
The closed static campaign and its unused slot are unchanged. No new hardware
attempt, native USB access, UART, capture or reload has occurred.

Prepare copied checked helpers under `draft_01/`, with A→B→B→A static controls,
one GCAPTURE, all 48 guarded capture FARs once, then A→B→B→A controls; 56 reads
with individual CMD checkpoints. Use repaired capture guards plus qualified
A/B controls: 3092 controls across 50 read FARs. Reject the first contradiction;
do not decode runtime fields. Require source coverage before access and preserve
raw replies, capture-command accounting and three-slot reservations. Read COR0;
reject unsupported capture settings without clock/security writes or RCAP.

Preliminary complete TAP model passes 56 reads, 56 checkpoints and one capture
command, with no native access. Complete rejection suite and helper release
remain pending under one new detached offline check capped at 600 seconds.
Bind operator readiness to a specific attempt, phase and observation UTC;
expired or misbound reports are refused. No current image report is inferred
from "ready and powered"; fresh bound readiness remains a later prerequisite.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/`
`owner_authorization_received_01.json`, `draft_01/{preliminary_full_model.json,
plan.json,frame_guards.json,provenance.json,manifest.json}`. Contract:
[Snapshot frame qualification §7](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
Execution remains disabled, slots used zero. Even a subsequent frame-control
PASS will leave capture freshness, runtime association, polarity, display
noninterference and GPU cause unestablished.

#### 3.35.32 — Snapshot worker: 3415 offline checks PASS; release reviewed

Detached unit spu-offline_check_01-20261006T015518Z-249085 has exactly one
COMPLETE terminal marker, exit 0, running 2026-10-06T01:55:18Z–01:58:20Z,
182 seconds within the 600-second cap. stdout reports 3415 checks PASS; stderr
empty. Full modeled sequence covers 56 frame reads, 48 capture FARs, one capture,
3092 controls and exact 32/64 TMS/TDI equivalence across 476280 clocks. The suite
uses no native USB and consumes no physical slot. Fault, refusal, cleanup,
reservation and operator-report fixtures pass. These are offline results only.

Review all frozen preparation/provenance inputs unchanged; seal 29 runtime
inputs: 23 helpers, five data/result files and the frozen disk bitstream. The
disk identity does not prove the complete currently loaded image. Host adapter
access preflight completes at 01:56:46.595711Z, including interface release and
close, with no bulk JTAG commands or TAP clocks. Activate under the recorded
three-attempt authorization; manifest ACTIVE_READY, zero used/three available,
810 seconds unreserved. Fresh attempt-bound setup/image readiness is required
before launch; none has been recorded after release at this entry.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/`
`offline_check_01/`, `host_access_check_01.{json,jsonl}` and
`draft_01/{focused_checks.json,source_review_01.json,release_review_01.json,
runtime_hashes.json,authorization.json,manifest.json}`. Contract:
[Snapshot frame qualification §8](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
No new physical snapshot, display acceptance or GPU diagnosis is established.
Prior bank/depth mismatches remain unconfirmed, and the readback root cause
remains NOT_ESTABLISHED.

#### 3.35.33 — Snapshot attempt 1: invalid IR after fourth static reply; no capture

Contextually bind owner reply "Ready," to the immediately preceding setup/image
readiness question; preserve the interpretation separately from the verbatim
short reply. Readiness records at 2026-10-06T02:03:45.728046Z. Attempt 1 runs
02:04:07.244077Z–02:04:23.002155Z, 15.76 seconds, FAILED/exit 1 within the caps.
One slot consumed/270 seconds reserved; two slots/540 seconds remain. Execution
is disabled pending diagnosed correction review; no blind retry is released.

All four CMD checkpoints return 0x4. Static A/B/B reads pass. The fourth A reply
returns 202 words, but CFG_IN for the closing DESYNC returns IR 0x3f, violating
mandatory low bits 01. The worker stops before DESYNC transmission and normal
fourth-frame validation. No GCAPTURE is attempted, no UART/reload/reset sent.
Reconstructed fourth words disagree with 54 A controls and 80 B controls;
no simple global bit offset within [-64,64] satisfies all A controls. Keep this
as an incomplete, rejected static transaction, not a captured runtime snapshot.

Failure is present in raw native f8 plus GETSIG 08 before Python decoding;
four focused offline replay checks pass. Prior identical outgoing IR scan
packets return 0x35. USB bulk errors zero; release/close/exit complete; all 29
executed archives match the runtime seal. This localizes the invalid return
within the measurement path but does not identify adapter execution, JTAG signal
delivery/sampling or target TAP cause. Loaded adapter firmware is unidentified;
candidate local firmware inspection cannot establish the actual executable.

Operator reports stable lock/same image/no intervention. The report records at
02:05:59.383211Z, after the 02:05:23.002155Z deadline; preserve late context only,
operator gate false. No precise earlier receipt or observation UTC was supplied.
It cannot repair the rejected read or prove causal probe noninterference.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_01/`
`{result.json,managed_terminal.json,transport.jsonl,executed_sources/,
fourth_frame_uncommitted.json,diagnosis_refinement_02.json,alignment_triage_01.json,
raw_ir_replay_check.json,operator_after_read.json}`. Preserve the initial
transaction-slicing assertion failure and earlier mistaken failure-position
analysis; the refinement places rejection after FDRO receive, before DESYNC.
Contract: [Snapshot frame qualification §9](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
GPU cause, bank/depth leads and UART electrical fault remain unestablished.

#### 3.35.34 — Authorized host transport correction; 390 offline checks PASS

Owner reply "Authorized." permits prospective host correction preparation and
one additional detached offline check capped at 600 seconds. Preserve the
existing three-slot campaign: one failed attempt consumed, two remaining,
physical time caps unchanged. Active worker/seal and failed executed archives
are untouched; execution remains false. No native or physical attempt occurs.

Prepare copied helpers/data under `transport_repair_01/`. Replace partial-byte
bulk shifts with whole-byte bulk shifts plus existing per-clock signal commands
for remainder/exit bits. Keep logical TMS/TDI, clock counts, bit order, pins,
frequency request and the complete capture/read/guard plan unchanged. Sync
journal command intent before write and raw replies before decoding, plus
capture/candidate/halt/close boundaries; flush every record. Reduce redundant
syncs of derived records without removing raw evidence. Neither change proves
the physical root cause or guarantees timing performance.

390 focused checks PASS, no native USB: every width 2..64 with/without exit,
returned data, exact TMS/TDI and clock equivalence, complete modeled 56-read
snapshot equivalence, whole-byte-only bulk packets, synthetic partial-return
fault rejection and journal durability/order checks. The injected fault is a
fixture, not observed adapter behavior. Complete amended regression, source
review and runtime promotion remain pending. Candidate adapter firmware source
is not proven to match the loaded executable. GPU cause remains unestablished.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/`
`owner_authorization_received_03.json` and
`transport_repair_01/{dirty_protocol.py,checked_usb.py,check_transport.py,
transport_focused_checks_01.json}`. Contract:
[Snapshot frame qualification §10](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
Do not use either remaining slot before full checks, reviewed correction release,
source seal, host access and fresh operator setup/image readiness.

#### 3.35.35 — Pairing audit passes; amended worker released; clock candidate offline

At owner direction independently decode request reply lengths and native
pairing from attempt 1's journal: 2533 calls and 1266 replies, no incomplete
transfers, unbound replies or decoder assignment mismatches. Five checks PASS,
including malformed pairing fixtures. Good B/failed A outbound prefixes differ
only in their intended FAR word. Equal-length stale/incorrect replies within
the adapter/FPGA remain possible; no physical transaction IDs were measured.

Transport repair detached job has exactly one COMPLETE marker, exit 0,
2026-10-06T02:18:27Z–02:19:23Z, 56 seconds within 600. Full amended suite records
3806 PASS, no native access, unchanged 56-read/48-FAR/3092-control model and
476280 logical clocks. Verify prepared sources/provenance unchanged, preserve
original active worker/seal and failed attempt archives, promote checked helpers
and seal 30 inputs. Existing reviewer releases next attempt at 02:22:52.211139Z,
REVIEWED_NEXT_ATTEMPT; one slot consumed/two remain, limits unchanged.
Native host access check 02 completes at 02:23:53.101587Z without bulk commands
or TAP clocks. Fresh setup/image readiness is still required before attempt 2.

Prepare an inactive 100 kHz request candidate for a conditional final-slot
comparison against attempt 2's same amended path at 1 MHz. Seven offline checks
PASS; modeled data, TMS/TDI and clock counts agree and only the frequency command
differs. Actual TCK is unmeasured. Preserve initial mock-packet formatter error
and corrected result. No clock candidate is promoted and no new physical slot
is consumed. A single PASS cannot establish timing causality or actual frequency.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/`
`transaction_audit_01/`, `transport_repair_offline_check_01/`,
`draft_01/{transport_amendment_release_01.json,runtime_hashes.json,
before_transport_repair_01/,attempt_01/review.json}`, `host_access_check_02.{json,jsonl}`,
and `lower_clock_candidate_01/{dirty_protocol.py,focused_checks.json}`. Contract:
[Snapshot frame qualification §§11–12](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).
No physical snapshot/GPU diagnosis is established. Root cause remains open.

#### 3.35.36 — Corrected snapshot attempt 2: all guarded reads pass; campaign closed

With fresh attempt-bound readiness, attempt 2 executes
2026-10-06T02:26:26.709021Z–02:27:25.403349Z, 58.69 seconds, COMPLETE/exit 0.
Use the amended whole-byte host shift path, durable raw request/reply records,
and unchanged 1 MHz frequency request. All 56 addressed frame reads pass all
56 CMD checkpoints; four ABBA controls before and after, one GCAPTURE and all 48
captured FARs complete. Every one of 3092 static controls matches. All executed
sources match the 30-input seal. USB/native cleanup completes; no UART, new load
or FPGA reset is sent.

Classify CAPTURE_FRAME_SET_STATIC_CONTROLS_MATCH and
STATIC_CONTROLS_QUALIFIED_RUNTIME_FRESHNESS_UNESTABLISHED. This qualifies the
static controls for this bounded frame set. It does not establish live capture
freshness, coherent runtime operands, causal display noninterference, or GPU
bank/depth cause. Do not decode captured runtime fields from this campaign.

The owner’s post-read report "Stable lock; same image; no intervention —
observed now" is recorded 2026-10-06T02:28:06.793223Z, within 60 seconds;
operator phase gate passes for that reported observation. Preserve its stated
limits; it is not proof that JTAG could not cause an unobserved transient.

Close after PASS: two attempts used/540 of 810 seconds reserved, one existing
slot closed unused. The 100 kHz candidate remains unpromoted because the
conditional failure signature did not occur in attempt 2. No timing causality
or actual TCK reduction is established. Any future work on capture freshness /
operand association requires its own reviewed scope before interpreting GPU
state. Attempt 1’s invalid IR/static return remains FAILED and preserved.

Evidence: `build/gpu_evaluation/t1d_snapshot_qualification_20261006/draft_01/attempt_02/`
`{result.json,managed_terminal.json,transport.jsonl,executed_sources/,
operator_readiness.json,operator_after_read.json,review.json}`. Journal SHA-256:
`c07aa5b5b87232d72cde8bda037ff6b3360cde9f55f73c42c02fc954cd0c5aa0`.
Contract: [Snapshot frame qualification §13](../spu_strategy/contract_gpu_t1d_snapshot_qualification_2026-10-06.md).

### 3.36 — T1G display and scene-update recovery replay (2026-10-06)

**Purpose:** Restore a previously demonstrated Wukong GPU display after the
September 6 static image replay produced no signal lock. No RTL or bitstream
was rebuilt. The earlier September 23 T1G image was loaded unchanged.

**Device and artifact:** QMTech Wukong XC7A100T-FGG676, IDCODE `0x3631093`.
Artifact
`build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit`,
SHA-256 `e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`.
Retained source checkout is commit
`a64d87c7ae0d96b44d8178c20f2421376a975ac0`. The SRAM load command was
`timeout 60s openFPGALoader -c dirtyJtag --freq 1000000 <artifact>`; it exited
0 and reported `isc_done=1`, `init=1`, `done=1`. No flash write occurred.

**Scene transport:** Six frozen 127-byte T1G packets (A, B, C, A, B, C) were
sent over the CH340 UART at 115200 8N1. Every host write completed and
`tcdrain` returned. Per-packet records are in
`build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_02/`:
`scene_a_uart.json`, `scene_b_uart.json`, `scene_c_uart.json`,
`scene_a_cycle_02_uart.json`, `scene_b_cycle_02_uart.json`, and
`scene_c_cycle_02_uart.json`. These establish host-side writes, not FPGA
receipt or activation.

**Operator observation:** After the T1G load and Scene A send, the operator
reported stable signal lock and red/green inverted triangles, red on the left
and green on the right. The asynchronous first visibility reply arrived after
the Scene A write, so it does not establish whether the image appeared before
that packet. In each cycle, the operator reported that B changed the image
from A and C changed it again from B, with stable lock. On the second cycle,
A matched the first A image; B and C again changed from their preceding
scenes. No photographs or captured pixels were supplied.

**Separate failed baseline replay:** The retained September 6 artifact
`build/spu_a7_100t_GPUVGA.bit` (SHA-256
`ce5bdc70753fc88d1a6e91bc1e573dff2c40756f66e9d689f9880139285e25e2`) also
loaded to SRAM successfully, but the operator reported a blank screen and no
signal lock. The contrast with T1G is observed; its cause is not established.

**Classification:** **PASS (operator-observed visual scene changes)** for
two A/B/C cycles on the retained T1G image. This establishes stable display
lock and repeated visible scene transitions as reported by the operator. It
does not establish exact A/B/C pixel identity, FPGA packet receipt, activation
telemetry, or why the September 6 artifact produced no lock. Recovery log:
`build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_02/`.

### 3.37 — T1G two-cycle visual acceptance retry (2026-10-07)

**Purpose:** Complete the frozen-image two-cycle A/B/C visual acceptance
sequence after attempt 06 stopped before its final C observation. No RTL,
fixture, or bitstream was changed.

**Device and artifact:** QMTech Wukong XC7A100T-FGG676, JTAG IDCODE
`0x3631093`. The SRAM-loaded T1G image was
`build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1G_B1_S1.bit`,
SHA-256
`e16dc6992c60de99d9f5d9a5cc10c3aff99a245b5f5da6035887f2c92cb68fa5`.
Loading exited 0 with `isc_done=1`, `init=1`, and `done=1`; configuration
flash was not written.

**Attempt disposition:** Attempt 06 remains **INCOMPLETE**: its cycle 2 C
visual observation is absent. Attempt 07 remains **INCOMPLETE**: the SRAM
load passed, but its post-load stable-lock response arrived after the
180-second observation gate, so no UART was opened and no scene was sent.
Attempt 08 passed. The unused attempt 09 was not run. The campaign stopped
after PASS.

**Attempt 08 transport:** The operator confirmed stable lock and a visible
image after loading and before UART opened. Six frozen 127-byte packets were
sent in order A/B/C/A/B/C at 115200 baud, 8N1. Each host write completed
127/127 bytes in one call, `tcdrain` completed, and the recorded 20 ms
post-drain delay completed. Start-to-start intervals exceeded the 31.1 ms
minimum, and each next packet began at least three seconds after the preceding
operator confirmation. One UART descriptor was held for the sequence. The
load began at `2026-10-07T01:19:21Z`; the shared deadline was
`2026-10-07T01:49:21Z`; the runner completed at `2026-10-07T01:22:46Z`.

**Operator observations:** Both cycles retained stable lock. A matched the
red-left/green-right inverted-triangle reference. B visibly changed from A.
C visibly changed from B and resembled A. Cycle 2 A matched the A reference;
no C-to-A visible transition was required. All six observations were recorded
before the shared deadline.

**Classification:** **PASS — bounded operator-observed scene switching on
the frozen T1G image.** This does not establish exact physical pixel equality,
FPGA UART packet receipt, CRC acceptance, activation telemetry, or general
throughput. Host writes and `tcdrain` are host-side evidence only.

Evidence: `build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/attempt_08/`
`{programming_01/result.json,t1g_demo_01/sequence.json,attempt_closeout_20261007.md}`.
The sequence JSON SHA-256 is
`e85b59946771f62794428119c0aa70d8d2e5d0a438f404962e45bc419fba2651`;
the loader result SHA-256 is
`2431e7507a931083c6cc98e395da6674de501c2c9d5a1e64ad123e598199711c`.
Campaign closeout:
`build/gpu_evaluation/gpu_wukong_baseline_recovery_20261006/campaign_closeout_20261007.md`.

### 3.38 — T1H scalar-diagnostic visual replay (2026-10-07)

**Scope:** Bounded operator-observed A/B/C/A scene switching on the retained
T1H scalar-diagnostic image. This replay records whether the previously
reported purple edge fringe is visible; it does not diagnose its cause or
close T1H H1.

**Authorization and image:** Owner-ratified contract
`spu_strategy/contract_gpu_t1h_visual_replay_2026-10-07.md`, SHA-256
`505ad3977fcf549cfc6d1802b6eacd238243a85b6fbf34da953c608767193c23`.
The frozen image
`build/spu_a7_100t_GPUVGA_T1H_DIAG_B1_S1.bit` has SHA-256
`ec600abe73e847f0846bff5429813cc6913a343b235e215cab5298ebb5d126dd`.
The loader detected Wukong IDCODE `0x3631093`, completed the SRAM load with
all DONE flags, and emitted exactly one `COMPLETE` terminal marker.

**Transport:** The PTY runner used the frozen 151-byte A/B/C/A fixtures at
115200 8N1. All four writes were complete and all four `tcdrain` calls
completed. Each transcript records the completed 20 ms post-drain delay.
The three start-to-start gaps were approximately 24.58 s, 19.92 s, and
18.70 s, exceeding the 31.1 ms minimum. Inter-scene dwell measurements were
at least 3.000 s. Before each send, the runner recorded at least 185 seconds
remaining for the five-second transaction bound and full 180-second
observation window. All four observations were recorded before the shared
30-minute deadline.

**Operator observations:** Stable lock and visible image were confirmed after
load. Scene A matched its reference; B visibly changed from A; C visibly
changed from B; final A returned to its reference. The operator reported the
purple fringe was not visible in this replay. The prior physical fringe
report and inconclusive, underfilled analyzer capture remain unchanged; its
cause is still unresolved. No analyzer capture was performed.

One runner startup without a PTY stopped at terminal preflight. It recorded
zero sends and no UART open. The accepted PTY replay used the same SRAM load
result and shared deadline; it did not reload or restart the deadline.

**Classification:** **PASS — bounded operator-observed scalar-threshold
scene switching on the frozen T1H image.** This does not establish exact
physical pixel equality, FPGA receipt, or the cause of the historical fringe.
**T1H H1 remains HOLD.** The conditional T1G recovery was not used; the
campaign stopped after PASS.

Evidence: `build/gpu_evaluation/t1h_visual_replay_20261007/campaign_01/`;
campaign closeout:
`build/gpu_evaluation/t1h_visual_replay_20261007/campaign_01/campaign_closeout.md`.
The load result SHA-256 is
`19f3a8e0e0d3b95f4a257a2b327651c99af1658c63e5ce10914cf1e15c099a0c`; the
accepted sequence manifest SHA-256 is
`f0318b9ecea97d63599389d2710eb7d70c54463251a960230361043bd412676e`.

### 3.39 — Packet 06 routed CPU integrity audit (2026-10-15)

**Classification:** **ROUTE INTEGRITY PASS; TIMING QUALIFICATION HOLD.** This
is an independent software audit of a nextpnr-routed artifact. It is not
silicon evidence, a vendor timing signoff, or proof that the design meets
25 MHz.

**Route identity:** Device `xc7a100tfgg676-1`; router `router2`; seed 1; 25 MHz
constraint. Tool `nextpnr-himbaechel v1.2-typestate-187-g4e51d2f`, executable
SHA-256
`818b49982d7710762a4a5db04fc21ac4605915ab12cb5c46c6b8ff35af96982c`;
frozen xc7a100t chip database SHA-256
`a74a2a817485f004269a82abd9957c885182ac16c95bca851de48ba46ad7040a`.
Source checkout commit `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`; its
launch-time dirty status, exact command, tool versions and terminal result are
retained in `build/spu_surd_register/backend_compatibility_20261012/candidate_route_diagnostic_compact_03/`.
The placed input has SHA-256
`2c227ddad44337a11bc7f1dfb2fae7045a5f5d47d4c124f26c688a91febd573e`.
The completed routed JSON has SHA-256
`c12df2808f72bce5a3eb22b4a83ebb69514a1d6fe26d5ec8d2184aa1ad22504f`;
the native route capture is retained beside it.

**Independent route audit:** The all-net audit completed with PASS. It audited
61,113 nets, 1,061,576 routing resources and all 192,229 physical sinks; every
physical sink branch was source-connected. All 51,197 cell bindings passed
preservation checks. No cross-net wire/PIP ownership conflicts were reported;
external boundary checks and post-route backend legalization passed. Retained
negative controls rejected altered LUT logic, disconnected logical inputs,
wrong net bindings, removed route branches and invalid constant-source forests.
The audit did not reroute or modify Packet 06. Evidence:
`build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_all_net_audit_20261015.json`,
SHA-256
`9454a1e321ce9c155525a4fc954cde725719ff5d8001d0d50b9a0c39a1f79d48`.

**Timing boundary:** The backend report gives 40.886 MHz against the 25 MHz
constraint. This remains an unqualified tool estimate: the backend timing data
does not have complete active-arc and corner coverage. The 20 absent CE
summaries were traced to 19 statically-high and one statically-low enable, so
no switching CE check applies to those endpoints. Synchronous SR setup/hold,
asynchronous recovery/removal and DSP timing coverage remain unqualified.
25 MHz operation is not established. Timing review:
`build/spu_surd_register/backend_compatibility_20261012/packet06_audit_reconciliation_01/packet06_master_qualification_20261015_rev05.json`.

### 3.40 — CPU-BOARD-4C-R1 first fixed-program Surd CPU run over UART (2026-10-30)

**Classification:** **SILICON OBSERVATION PASS (single run, fixed program).** One
volatile load of the autonomous Surd CPU image on one physical Wukong produced
one complete, CRC-valid UART record equal to the expected record. Independently
reviewed (PASS, single-run silicon observation with the limits below); not yet committed.

```text
Claim: this exact bitstream, loaded once into SRAM on this unit, executed the
  fixed 14-instruction Surd program and reported the expected result record. Attribution of the
  record to this load is subject to the attribution limit below.
Evidence dimension: silicon (single observation); interface (UART TX only, as observed)
Source revision / dirty-tree identity: isolated clone /home/john/.local/gate/spu-int3b-c3efc18,
  HEAD c3efc1878e5ae35601ec01a9e87e52ef032a7fc7 plus untracked experiment/ sources
  (CPU-INTEGRATE-4 27-entry manifest + CPU-BOARD-2R wrapper board_top.v
  f11f72f75ea4856b9f4f1494625f3dc505fc32d85c2358ea02569df177689c30); production RTL unchanged
Build/test command and configuration: Vivado 2026.1 synth, opt/place/route, write_bitstream
  (CPU-BOARD-3 Phase S/P, CPU-BOARD-4B; UNUSEDPIN=PULLNONE, COMPRESS=FALSE,
  USR_ACCESS=0x48E0E161, CFGBVS=VCCO, CONFIG_VOLTAGE=3.3); load and capture by
  build/cpu-board-4c-r1-preflight/run_4c_r1.py (sha256
  f2f5c3670367256571abe00e7f79409a5611babe1f08b06cfd7ceb18ceae5f71) with loader_run.py
  8ba17f1c0897b6f24ff5fe7a5ad6eba0a1bfe67e8e9b9c5c2251458616f0219c, capture.py
  a5205549465eff76cb1153ea53fbc9a7335b5f1e60fe414b6651f8a2988c06c0, parse_record.py
  9c5d48be364fdeb549cb78a817bbf09cf367bcf0c6a3ab95819c5dc57d57dcc5
Device and toolchain: board QMTECH Wukong, owner-identified revision V3 (V03 schematic
  Rev 3.0, sha256 bec53e6201c5c47a7059ce5b5af86e0f3a48535ebdf5643af7583171f7331aee);
  device XC7A100T-1FGG676C per the seller listing and owner acceptance, NOT physically
  verified (no marking read); JTAG idcode 0x3631093 (XC7A100T die; says nothing about
  grade). openFPGALoader v1.2.0 (OSS CAD Suite 20261027), DirtyJTAG CB81353DCE678119,
  CH340 /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0, Python 3.10.12, Linux 6.8.0-138
Artifact identity: cpu_board_2r_top.bit sha256
  442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea (3,826,011 bytes);
  .bin sha256 cc259988b32dcd890a25c8a1765c6a28e3fafa280bcaed1aa5073f552dbc156c;
  routed checkpoint sha256 48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8
Oracle and checked scope: expected record equals the bytes simulated from the RTL
  (CPU-BOARD-2 mode 0 testbench) and an independent zlib CRC-32 of bytes 0-28; expected
  value (1+2*sqrt3)^2/9 = (13+4*sqrt3)/9 as tuple (a,b,d) = (13,4,9). Checked scope: the
  one fixed program, one run.
Result and evidence artifact path: PASS; build/cpu-board-4c-r1-01/ (10-entry
  MANIFEST.sha256, sha256 4c033bca3e2baebbcfd1f6351516c9faaf56996e562b91a5cfc400f666006793)
Adjacent evidence dimensions not established: see below
```

**Procedure and result:** Capture was started first (115200 baud, 8N1, raw, no flow
control) and drained for 1 s (0 stale bytes); then exactly one command
`openFPGALoader -c dirtyJtag --freq 1000000 <bit>` (SRAM load, no flash options)
returned exit 0 after **31.363 s**, reporting `Load SRAM 100.00%`, `Done`,
`isc_done 1`, `init 1`, `done 1` (`loader_output.txt`, sha256
724bc75b554fab00ba2599fd697b305580930dbe5c2d30ffa296feab7f560365). The UART delivered
exactly 33 bytes during the load, before the loader returned (`raw_all.bin` sha256
182c3453f3279af508c04da36c7d3e78e2feb26cf9685ca97512d8a05a8165cf), in two USB chunks
31,320.07 and 31,320.53 ms after the load started (about 43 ms before the loader
returned):

```text
a5 01 01 3f 0e | 0d000000 00000000 04000000 00000000 09000000 00000000 | 422b6b75
magic/version a5 01, status 01 (successful HALT), result-valid mask 3f, PC 14,
slices [13,0,4,0,9,0] little-endian, CRC-32/ISO-HDLC 756b2b42 (zlib.crc32 of bytes 0-28)
```

No other byte, truncated frame, contradictory or repeated record appeared during the
30 s observation window. A read-only JTAG detect after the window found one device,
idcode 0x3631093 (`session.json` sha256
499fb2d0912fa6607b68f01814e571c1a091e240646e7a502ee09ef9cf82047b). Session length
62.5 s from capture start. Owner reports (not independently measured): the rails and
configuration straps were checked visually and by continuity, not measured, as recorded in
the owner rail/strap confirmation section of
`build/cpu-board-4-readiness/CPU_BOARD_4A_RECONCILIATION.md`; the owner's immediate
pre-run confirmation of normal power and cables was given interactively and is noted in
`RESULT_NOTE.md`, not preserved as a separate artifact. `owner_observations.txt` records
only that the DONE LED was on and the board looked normal before R1, so the LED did not
show the load itself.

**Attribution limit (freshness):** The UART record carries no execution epoch or session
identifier, and the board was already configured (DONE LED on) before R1, so attributing
the record to this load rests on procedure and timing, not on independent proof. What the
preserved evidence shows: capture was initialized before the load, a 1 s drain returned 0
bytes, no byte arrived during the first 31.32 s of loading, and the only record arrived
about 43 ms before the loader returned. That strongly associates the record with this
load, but it does not independently establish when configuration completed relative to
transmission, does not exclude an earlier record buffered in the CH340/USB/OS path after
the drain, and cannot exclude an unrecorded manual action; the session script recorded
no second load and no KEY0 press, which establishes only what the recorded workflow did.

**Prior attempt:** The first CPU-BOARD-4C Step A attempt (`build/cpu-board-4c-01/`)
remains a separate **HOLD**: the loader had not returned within its 30 s timeout, was
killed, and 0 UART bytes were captured. The payload needs at least 30.6 s at 1 MHz, so
the limit was too short; this is a hypothesis consistent with the 31.363 s load here,
not a tested root cause, and the board state after that interrupted load was not read.
This entry does not supersede or erase it.

**Adjacent evidence dimensions not established (NOT RUN or not covered):**
- Full ISA qualification: one fixed 14-instruction program (SLI, SLD, SMUL, SRD) ran once;
  no other opcodes, operands, overflow/refusal paths or repeated runs on hardware.
- Physical reset qualification: the KEY0 button, reset-pulse capture, bounce and re-run
  behaviour were NOT RUN (Step B was not authorized). The run began from the
  configuration-time reset-hold only.
- General timing/electrical qualification: routed timing is internal only (WNS +6.360 ns,
  WHS +0.060 ns, recovery +17.927 ns, removal +0.233 ns); `raw_rst_n` has no input delay and
  `uart_tx` no output delay; no rail measurement, clock/baud measurement or margin test.
  A single successful run does not establish operation across voltage, temperature or
  repeated power-ups.
- Device identity: speed/temperature grade and board revision remain owner-accepted,
  unverified assumptions; the 100T die is supported by the JTAG idcode only.
- Persistence: nothing was written to the SPI flash; the image is volatile.
- Execution epoch / freshness: no epoch or session ID in the record; attribution to the
  load is timing- and procedure-based (see the attribution limit above).
- Repeatability: one run on one unit; no repeated-run, cross-build or cross-device agreement.

### 3.41 — CPU-ROM-2B one-word ROM variant: operand variation over UART (run 2026-10-30; entry prepared 2026-10-31)

**Classification:** **SILICON OBSERVATION PASS (single run, one authorised ROM-word change).**
A fresh volatile load of the one-word variant image produced one complete, CRC-valid
UART record equal to the independently predicted record, with no change to the CPU RTL.
It is separate from, and does not reinterpret, section 3.40. Independently reviewed
(PASS, single-run silicon observation with the limits below); not yet committed.

```text
Claim: this exact bitstream (golden image with ROM word 0 changed), loaded once into SRAM
  on this unit, executed the fixed 14-instruction Surd program with operands (a,b,d) = (2,2,3)
  and reported the predicted raw result (16,8,9). Attribution of the record to this load is
  subject to the freshness limit below.
Evidence dimension: silicon (single observation); interface (UART TX only, as observed)
Source revision / dirty-tree identity: same sources as 3.40 (isolated clone
  /home/john/.local/gate/spu-int3b-c3efc18, HEAD c3efc1878e5ae35601ec01a9e87e52ef032a7fc7 plus
  untracked experiment/ sources; wrapper board_top.v
  f11f72f75ea4856b9f4f1494625f3dc505fc32d85c2358ea02569df177689c30); production RTL unchanged
Build/test command and configuration: golden routed checkpoint (sha256
  48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8) opened in Vivado 2026.1;
  RAMB36 INIT for ROM word 0 (low half 0x100 -> 0x200) edited in memory only; write_bitstream
  with the 3.40 properties (UNUSEDPIN=PULLNONE, COMPRESS=FALSE, USR_ACCESS=0x48E0E161) by
  build/cpu-rom-2a/prep/cand_bitgen.tcl (sha256 ec7af37bcbae5e3a9ccf9722e805b68cc950358c0d82d92f79043815baa0ebec).
  updatemem was NOT used (CPU-ROM-1: HOLD). Load and capture by
  build/cpu-rom-2b-preflight/run_2b.py (sha256 80a3b693980b3b4767ad7f2a2e24be09447950b85553cd0fb7c4c230a2efc4b7)
Device and toolchain: as 3.40 (QMTECH Wukong, owner-identified V3; XC7A100T-1FGG676C per seller
  listing and owner acceptance, NOT physically verified; JTAG idcode 0x3631093;
  openFPGALoader v1.2.0; DirtyJTAG CB81353DCE678119; CH340 by-id usb-1a86_USB_Serial-if00-port0)
Artifact identity: oneword.bit sha256
  a71284850c56c17f4bab5ddb8b5b95e021315c954d9a324503756e8c58d20cc9 (3,826,011 bytes);
  oneword.bin sha256 058dc3fbaa49050ca413da60f4a6612c467cabaffea412a677a48d93bdec12cf
  (3,825,788 bytes); golden .bit 442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea
  unchanged
Oracle and checked scope: exact oracle ((2+2*sqrt3)/3)^2: raw SMUL tuple (a^2+3b^2, 2ab, d^2) =
  (16,8,9), value (16+8*sqrt3)/9, the CPU commits fitting arithmetic unreduced (gcd 1 here);
  agreed with the RTL simulation of the CPU-BOARD-2R wrapper with the ROM word patched
  (build/cpu-rom-2a/out/sim/vectors.log). Checked scope: one program, one run.
Result and evidence artifact path: PASS; build/cpu-rom-2b-01/ (9-entry MANIFEST.sha256, sha256
  5f1f6b6fc7dd3ee3276a5fb637d14fad67ece16476f8714c91d964a34dcbc16b); image evidence
  build/cpu-rom-2a/out/ (83-entry MANIFEST.sha256, sha256
  b5fc1c4cbf40c8554e1aff30fe47d5eec477adb370633162a0bbf55b6d6707e1)
Adjacent evidence dimensions not established: see below
```

**Image identity and difference to golden (CPU-ROM-2A, offline):** The golden image
regenerated by the same script is bit-identical to the original `.bin`. The one-word image
differs from golden in exactly three 32-bit payload words: 917032 (xor 0x00010000) and
917038 (xor 0x00000001), which are the two ROM bits flipped (INIT bits 8 and 9, positions
measured with separate single-bit probe bitstreams), and the configuration CRC word 955926
(golden c9fec49a, candidate 57c5f93d). The candidate's first data CRC was recomputed
independently (CRC-32C over data and register address, `bitcrc.py`) and equals the stored
value and the value for the predicted payload; all 16 ROM words reconstructed from the
bitstream difference and from the in-memory INIT match the intended program (word 0 changed
only); bitstream DRC reported 0 errors; the image equals the CPU-ROM-1 reference
`ref_w0_0x200.bin`. A second, constant CRC write later in the stream (word 956044,
e3ad7ea5, identical in every image) is not modelled by `bitcrc.py`; the owner reports this
was understood and independently checked in Terra's review, and it is not re-derived here.
Operand payloads stay below 2^16 and logical ROM bits 24 and 29 (unconnected in this image)
are clear.

**Procedure and result:** Capture was started first (115200 baud, 8N1, raw, no flow
control) and drained for 1 s (0 stale bytes); the board had been running the golden image
(3.40). Exactly one `openFPGALoader -c dirtyJtag --freq 1000000 <oneword.bit>` (SRAM load,
no flash options) returned exit 0 after **31.359 s**: `Load SRAM 100.00%`, `Done`,
`isc_done 1`, `init 1`, `done 1` (`loader_output.txt` sha256
0f5d9b8278c2ad152915688debbe5968de02380f31af0bd1e9e0f351bf82394f). The UART delivered
exactly 33 bytes during the load, before the loader returned (`raw_all.bin` sha256
aec07df22d320512cf93ca3e0775b52e7513afbaa7435250c7a0e76339e633bc), in two USB chunks 31,307.49
and 31,310.27 ms after the load started (loader returned at 31,359 ms):

```text
a5 01 01 3f 0e | 10000000 00000000 08000000 00000000 09000000 00000000 | 71400c97
status 01 (successful HALT), mask 3f, PC 14, slices [16,0,8,0,9,0] little-endian,
CRC-32/ISO-HDLC 970c4071 (zlib.crc32 of bytes 0-28); golden record was 756b2b42
```

No other byte, truncated frame, contradictory valid record (a golden-image record would have
been flagged) or repeated record appeared in the 30 s window. A read-only JTAG detect after
the window found one device, idcode 0x3631093 (`session.json` sha256
1144ecc281ecde06c3a9723679497d31d127febbd2c6bba51a60d73b7bb3d405). Session 62.5 s from
capture start. The owner's immediate pre-run confirmation of normal power, cables and
rails/straps was given interactively and is noted in `RESULT_NOTE.md`; rails and straps were
not measured (3.40).

**Provenance of the harness:** `capture.py` (a5205549465eff76cb1153ea53fbc9a7335b5f1e60fe414b6651f8a2988c06c0)
and `loader_run.py` (8ba17f1c0897b6f24ff5fe7a5ad6eba0a1bfe67e8e9b9c5c2251458616f0219c) are
byte-identical to the 3.40 run. The session script differs: it waits for a non-empty
`READY` file (an empty-file race found in offline testing; the 3.40 script has the same
latent race, which was not observed to trigger in that run), and its
parser (`parse_record_2b.py`, sha256 ce1e7ee58a36c22f23ecf94131050ea5abcf152978956a4f8d2d4700be971dfb)
expects the one-word record. The repair removes the observed race; it does not by itself
exclude every possible partial-write race.

**Attribution limit (freshness):** As in 3.40, the record carries no execution epoch or
session identifier. Attribution to this load rests on procedure and timing: capture
initialized first, a 1 s drain returned 0 bytes, no byte arrived during the first 31.3 s of
loading, and the only record arrived about 52 ms before the loader returned and was a
different valid record from the golden one. This strongly associates it with this load but
does not independently establish when configuration completed relative to transmission, does
not exclude a record buffered in the CH340/USB/OS path after the drain, and cannot exclude an
unrecorded manual action.

**Adjacent evidence dimensions not established (NOT RUN or not covered):**
- Full ISA qualification: one program with one changed operand word (a: 1 to 2; denominator
  unchanged at 3); no other opcodes, no overflow/refusal path, no normalization (SNORM) path.
- Repeatability: one load of this variant on one unit; no repeated loads, other variants,
  cross-build or cross-device agreement.
- Runtime reset: the KEY0 button, reset-pulse capture and re-run behaviour were NOT RUN; the
  run began from the configuration-time reset-hold only.
- Timing/electrical: as 3.40 (internal routed timing only; no rail, clock or baud measurement;
  raw reset has no input delay and UART no output delay).
- Device identity: speed/temperature grade and board revision remain owner-accepted,
  unverified assumptions.
- Persistence: nothing was written to the SPI flash; the image is volatile.

### 3.42 — CPU-BOARD-4C Step B: single KEY0 restart of the resident one-word image (2026-10-31)

**Classification:** **SILICON OBSERVATION PASS (single press, scoped restart functionality).**
After a 10 s UART silence with no bytes, an owner-reported single KEY0 press on this unit
was followed by one complete, CRC-valid UART record equal to the expected record, which
supports a restart of the resident one-word image without reconfiguration. No press
timestamp was captured. A first attempt the same day is recorded separately as a **HOLD**.
This entry does not establish asynchronous reset safety. Entry prepared for review; not yet
reviewed or committed.

```text
Claim: with the CPU-ROM-2B one-word image resident in SRAM, an owner-reported single KEY0
  press (made on the PRESS NOW notification; no press timestamp was captured) was followed by
  the expected record (16,8,9) on UART, supporting a restart of the resident program; no
  reload, no flash, no second press.
Evidence dimension: silicon (single observation, restart functionality); interface (KEY0 to
  reset path and UART TX, as observed)
Source revision / dirty-tree identity: unchanged from 3.40/3.41 (isolated clone
  /home/john/.local/gate/spu-int3b-c3efc18, HEAD c3efc1878e5ae35601ec01a9e87e52ef032a7fc7 plus
  untracked experiment/ sources; wrapper board_top.v f11f72f75ea4856b9f4f1494625f3dc505fc32d85c2358ea02569df177689c30);
  repository documentation baseline 82719ce; production RTL unchanged
Build/test command and configuration: no build, no load: build/cpu-board-4c-keyb-r1-preflight/run_keyb.py
  (sha256 b77892174489f6d09ed7305d7217cc71c49e6e536dc7da6d421c13b521dcba2d; preflight_keyb.py
  0fa97e2933619dc1ef6f8b62f64a454a595143ba5e6670ee657cb8b0ab6ab9b5; test_offline_keyb.py
  8300109c1ea085c37612bb763fc4a1cf258e3f38c8999066b340bea9caa25d9d; capture.py
  a5205549465eff76cb1153ea53fbc9a7335b5f1e60fe414b6651f8a2988c06c0 and parse_record_2b.py
  ce1e7ee58a36c22f23ecf94131050ea5abcf152978956a4f8d2d4700be971dfb, byte-identical to 3.41)
Device and toolchain: as 3.40/3.41 (QMTECH Wukong, owner-identified V3; XC7A100T-1FGG676C per
  seller listing and owner acceptance, NOT physically verified; JTAG idcode 0x3631093;
  DirtyJTAG CB81353DCE678119; CH340 by-id usb-1a86_USB_Serial-if00-port0)
Artifact identity: resident image = oneword.bit sha256
  a71284850c56c17f4bab5ddb8b5b95e021315c954d9a324503756e8c58d20cc9 (loaded in 3.41; residency
  rests on the owner's statement of continuous power, host-side consistent, and on the record
  content; there is no readback)
Oracle and checked scope: expected record = the one-word record of 3.41 (raw (16,8,9), CRC-32
  970c4071); checked scope: one press, one record
Result and evidence artifact path: PASS; build/cpu-board-4c-keyb-r1-01/ (10-entry
  MANIFEST.sha256, sha256 c4fda2c0c973fa46a964af4e6f96beaf69a76391750900e1b47da3a35a286f6a)
Adjacent evidence dimensions not established: see below
```

**Procedure and result (retry R1):** Full preflight passed (frozen scripts, offline tests,
one DirtyJTAG and one CH340, port free, read-only JTAG detect idcode 0x3631093); the owner
gave an immediate go/no-go. Capture was started first (115200 baud, 8N1, raw, no flow
control) and drained for 1 s (0 bytes). A 10 s quiet interval followed with **0 bytes**. The
single notification "KEY0 TEST: PRESS KEY0 NOW" was issued 11.04 s after capture start; the
owner pressed KEY0 once for about half a second (owner-reported; no press or release marks
were made, so there is no press timestamp). The 30 s window closed at 41.05 s; one read-only
JTAG detect afterwards found idcode 0x3631093 (`session.json` sha256
82348754b63f48741d675923427b1530ffd85d3ad824dd63b78a2cd8f4a74d06). Session 41.5 s (limit
120 s). The UART delivered exactly 33 bytes (`raw_all.bin` sha256
aec07df22d320512cf93ca3e0775b52e7513afbaa7435250c7a0e76339e633bc; raw file and per-chunk
jsonl both total 33 bytes, `capture.jsonl` sha256
6bca566c557ab1ce910ace2d772ee487e3cb4b9de251519de600c0ecb54d41ba) in two USB chunks 1,521.8
and 1,524.6 ms after the end of the quiet interval (the notification was issued 0.8 ms after
that end, so about 1,521.0 and 1,523.8 ms after the notification; `RESULT_NOTE.md` in the
evidence directory gives the offsets relative to the notification, and `session.json` is
authoritative):

```text
a5 01 01 3f 0e | 10000000 00000000 08000000 00000000 09000000 00000000 | 71400c97
status 01, mask 3f, PC 14, slices [16,0,8,0,9,0], CRC-32 970c4071
```

No truncated, garbage, repeated or contradictory bytes appeared. The record is byte-identical
to the 3.41 record.

**First attempt (separate HOLD):** `build/cpu-board-4c-keyb-01/` (MANIFEST sha256
e890a2b10101db6a86dee6b65580b0650a700589d8b7539d8b55460b70380439). The owner pressed KEY0
during the quiet interval, before any press instruction; the same 33-byte record arrived
1,279.7 ms after the quiet interval started (`raw_all.bin` sha256 aec07df2...e633bc, identical
to the retry's). The first-attempt harness (`run_keyb.py` sha256
071c1993cbf40db12c57ab412220ad6aae111e765b05890151f95bc0ec45111a) evaluated the quiet
interval only after its full 10 s and had sent an early "DO NOT PRESS YET" notice; it reported
HOLD and a STOPPED notice about 10 s after the bytes arrived (session 11.5 s). It is **not**
Step B evidence and is not a PASS; it is nonetheless a first, uncontrolled KEY0 restart of
this board (the board was therefore restarted once before the retry). The retry harness
removed the early notice and aborts on the first stray byte (addendum
HOLD_NOTE_ADDENDUM_2026-10-31.md).

**Reset-path analysis and simulation supporting the interpretation (offline, not hardware
evidence):** `build/cpu-board-4c-stepb-prep/` (13-entry MANIFEST, sha256
0e1466b621b81a216930511a9f64ebaa913c09b48e7b4768dab39da62ba30cc8). From the routed
checkpoint (sha256 48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8):
`raw_rst_n` asynchronously sets the supervisor's `request_pending` and `reset_hold`
(12 asynchronous pins in total, all single-input drivers); the released `cpu_rst_n` reaches
6,480 of 6,752 flip-flops (mostly as synchronous resets); the 272 flip-flops outside the cone
are the supervisor (9) and the packetizer (263: 235 data registers loaded before use, 27
control registers cleared through the synchronized `ok`, `rs[1]`). Simulation of the
CPU-BOARD-2R wrapper (`sim/bounce_results.txt`, sha256
87c0b7625e4361c8a209f4bd1f5c20c34399155b19ea1aac19c89d6e409fc6f8): a clean press, a bounce
train, a late glitch and a 3 ns pulse each end with one fresh valid record about 107 us after
the last raw release. The hardware press here is a single sample of that behaviour.

**Adjacent evidence dimensions not established (NOT RUN or not covered):**
- Asynchronous reset safety: assertion and release across clock phases, metastability margin,
  glitch immunity and switch-bounce statistics were not measured; one successful restart does
  not establish them (routed removal +0.233 ns and recovery +17.927 ns are internal estimates;
  `raw_rst_n` has no input delay).
- Press timing: no hardware or host press timestamp was captured, so when the press occurred
  is not established; the record's arrival time (about 1.52 s after the notification) is
  recorded but does not by itself date the press.
- Presses during arithmetic execution or UART transmission, repeated presses, and power-up
  behaviour were NOT RUN.
- Execution epoch / freshness: the record carries no epoch; attribution rests on 0 bytes in
  the 10 s quiet interval, the drain, and the arrival after the notification, and cannot
  exclude an unrecorded action or a record buffered in the CH340/USB/OS path.
- Resident-image identity: inferred from continuous power (owner statement) and the record
  content, with no configuration readback.
- Device identity, timing and electrical qualification, and general ISA qualification: as in
  3.40 and 3.41.

### 3.43 — CPU-ROM-2C Variant B (denominator 25): operand variation over UART (2026-10-31)

**Classification:** **SILICON OBSERVATION PASS (single run, one authorised three-word ROM change).**
A fresh volatile load of the Variant B image produced one complete, CRC-valid UART record
equal to the independently predicted record, with no change to the CPU RTL. It is separate
from, and does not reinterpret, sections 3.40 to 3.42. Entry prepared for review; not yet
reviewed or committed.

```text
Claim: this exact bitstream (golden image with ROM words 0, 2 and 4 changed), loaded once into
  SRAM on this unit, executed the fixed 14-instruction Surd program with operands (a,b,d) =
  (2,1,5) and reported the predicted raw result (7,4,25), i.e. ((2+sqrt3)/5)^2 = (7+4*sqrt3)/25.
  Attribution of the record to this load is subject to the freshness limit below.
Evidence dimension: silicon (single observation); interface (UART TX only, as observed)
Source revision / dirty-tree identity: same sources as 3.40 to 3.42 (isolated clone
  /home/john/.local/gate/spu-int3b-c3efc18, HEAD c3efc1878e5ae35601ec01a9e87e52ef032a7fc7 plus
  untracked experiment/ sources; wrapper board_top.v
  f11f72f75ea4856b9f4f1494625f3dc505fc32d85c2358ea02569df177689c30); production RTL unchanged;
  repository documentation baseline fd936ef
Build/test command and configuration: golden routed checkpoint (sha256
  48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8) opened in Vivado 2026.1;
  RAMB36 INIT for the low halves of ROM words 0, 2 and 4 (0x100 -> 0x200, 0x200 -> 0x100,
  0x300 -> 0x500) edited in memory only; write_bitstream with the 3.40 properties
  (UNUSEDPIN=PULLNONE, COMPRESS=FALSE, USR_ACCESS=0x48E0E161) by
  build/cpu-rom-2a/prep/cand_bitgen.tcl (sha256
  ec7af37bcbae5e3a9ccf9722e805b68cc950358c0d82d92f79043815baa0ebec); updatemem was NOT used.
  Load and capture by build/cpu-rom-2c-preflight/run_2c.py (sha256
  4c3544466e74db7e9e4711235a8ecb3e55b23de8e6c683186c79dab0bba62437)
Device and toolchain: as 3.40 to 3.42 (QMTECH Wukong, owner-identified V3; XC7A100T-1FGG676C per
  seller listing and owner acceptance, NOT physically verified; JTAG idcode 0x3631093;
  openFPGALoader v1.2.0; DirtyJTAG CB81353DCE678119; CH340 by-id
  usb-1a86_USB_Serial-if00-port0)
Artifact identity: B.bit sha256 794c2e3800836fcb916c1c014cbd4de00061bd12d296dd0c71ffffadfa473016
  (3,826,011 bytes); B.bin sha256 d4436b009955e782bebd4da48099df4646a136e1307eda01e8bf9088dc84a94c
  (3,825,788 bytes); golden .bit 442a229e9d8dc76485dee9e757ff2b6fecd9eca5f5d0c4cf17530501e3b153ea
  unchanged
Oracle and checked scope: exact oracle ((2+sqrt3)/5)^2: raw SMUL tuple (a^2+3b^2, 2ab, d^2) =
  (7,4,25), already reduced (gcd 1); agreed with the RTL simulation of the CPU-BOARD-2R wrapper
  with the ROM words patched (build/cpu-rom-2a/out/sim/vectors.log). Checked scope: one
  program, one run.
Result and evidence artifact path: PASS; build/cpu-rom-2c-01/ (9-entry MANIFEST.sha256, sha256
  38537ec2bff506b00596d662e9d2df58a8b8e85425229dd3983ba21e45a0ccf8); image evidence
  build/cpu-rom-2a/out/ (83-entry MANIFEST.sha256, sha256
  b5fc1c4cbf40c8554e1aff30fe47d5eec477adb370633162a0bbf55b6d6707e1)
Adjacent evidence dimensions not established: see below
```

**Image identity and difference to golden (CPU-ROM-2A, offline):** The golden image
regenerated by the same script is bit-identical to the original `.bin`. The Variant B image
differs from golden in exactly four 32-bit payload words: 917032 (xor 0x00030000), 917033
(xor 0x00000004) and 917038 (xor 0x00000007), which are the six ROM bits flipped (INIT bits 8,
9, 72, 73, 137 and 138, positions measured with separate single-bit probe bitstreams), and the
configuration CRC word 955926 (golden c9fec49a, candidate e4a81bfb). The candidate's first data
CRC was recomputed independently (CRC-32C over data and register address, `bitcrc.py`) and
equals the stored value and the value for the predicted payload; all 16 ROM words reconstructed
from the bitstream difference and from the in-memory INIT match the intended program (words 0,
2 and 4 changed); bitstream DRC reported 0 errors. The frozen `bitcrc.py` does not model the
second configuration CRC write (word 956044, e3ad7ea5, identical in every image): it carries
its accumulator past the first check, and the ROM-2A analysis checked only the first result. A
review-only correction that resets the accumulator after each CRC check reproduces both stored
CRC values for the golden image and for the A, B and one-word candidates; this was reproduced
here with `build/cpu-rom-2c-crc2-check/bitcrc_reset_after_check.py` (output `ALL_BOTH_MATCH`;
MANIFEST sha256 3a1f11b6252c27970865d68e782d6388e54bf3054d9c4228165ca408a48688a4) and agrees
with the independent review. The correction was not made to the frozen tool and the ROM-2A
evidence was not changed. The operand payloads stay below 2^16 and logical ROM
bits 24 and 29 (unconnected in this image) are clear. Unlike the one-word variant, Variant B
also changes the denominator operand (3 to 5) and two numerator operands.

**Procedure and result:** Preflight passed (frozen scripts and offline tests, complete
`.bit`/`.bin` hashes and the 83-entry image manifest, one DirtyJTAG and one CH340, port free,
read-only JTAG detect idcode 0x3631093, earlier hardware evidence manifests unchanged) and the
owner gave an immediate go/no-go. Capture was started first (115200 baud, 8N1, raw, no flow
control) and drained for 1 s (0 stale bytes); the board had been running the one-word image
(3.41, restarted by KEY0 in 3.42's attempts). Exactly one `openFPGALoader -c dirtyJtag --freq
1000000 <B.bit>` (SRAM load, no flash options) returned exit 0 after **31.370 s**:
`Load SRAM 100.00%`, `Done`, `isc_done 1`, `init 1`, `done 1` (`loader_output.txt` sha256
67efdec815df3f6253d90b75c0ec58c70673128dec7c86a9a0171d0d2848fe5e). The UART delivered
exactly 33 bytes during the load, before the loader returned (`raw_all.bin` sha256
02d15cadb5b550f8c3e57d451414a63273d2a791e6e85aedae5d4e56ace2f261; raw file and per-chunk
jsonl both total 33 bytes, `capture.jsonl` sha256
86c378f849fe0b831c7f01bc6ffd984fda155a3958b25e5876058b1ce94dc667), in two USB chunks 31,329.60
and 31,332.42 ms after the load started (the loader returned at 31,370.1 ms, so about 40.5 and
37.7 ms earlier):

```text
a5 01 01 3f 0e | 07000000 00000000 04000000 00000000 19000000 00000000 | d8eae602
status 01, mask 3f, PC 14, slices [7,0,4,0,25,0] little-endian, CRC-32 02e6ead8
(one-word record was 970c4071, golden 756b2b42)
```

No other byte, truncated frame, contradictory valid record (a resident one-word or golden
record would have been flagged) or repeated record appeared in the 30 s window. A read-only
JTAG detect after the window found one device, idcode 0x3631093 (`session.json` sha256
4299f789d8c2f1f5153c90c74d152823e9de440b482f8fb10b6531912c5305b6). Session 62.5 s from capture
start. The owner's immediate pre-run go/no-go (normal power, cables, rails and straps, no
anomaly) was given interactively and is noted in `RESULT_NOTE.md`; rails and straps were not
measured (3.40).

**Provenance of the harness:** `capture.py` (a5205549465eff76cb1153ea53fbc9a7335b5f1e60fe414b6651f8a2988c06c0)
and `loader_run.py` (8ba17f1c0897b6f24ff5fe7a5ad6eba0a1bfe67e8e9b9c5c2251458616f0219c) are
byte-identical to 3.41. The session script is the 3.41 session script (including its non-empty
`READY` fix) with only the bitstream path, expected record and evidence directory changed; the
parser (`parse_record_2c.py`, sha256 9d39c82b969f079631db991276604c8e3c29e4ebb2540fecd160957b410b97e2)
expects the Variant B record.

**Attribution limit (freshness):** As in 3.40 and 3.41, the record carries no execution epoch
or session identifier. Attribution to this load rests on procedure and timing: capture
initialized first, a 1 s drain returned 0 bytes, no byte arrived during the first 31.3 s of
loading, and the only record arrived during loading, before the loader returned, and was a
different valid record from the one-word and golden records. This strongly associates it with
this load but does not independently establish when configuration completed relative to
transmission, does not exclude a record buffered in the CH340/USB/OS path after the drain, and
cannot exclude an unrecorded manual action.

**Adjacent evidence dimensions not established (NOT RUN or not covered):**
- Full ISA qualification: one program with changed operand words (a: 1 to 2, b: 2 to 1,
  d: 3 to 5); no other opcodes, no overflow/refusal path, no normalization (SNORM) path (the
  result is already reduced).
- Repeatability: no repeated load of Variant B and no cross-build or cross-device agreement;
  this variant was loaded once on one unit (other images are recorded in 3.40 to 3.42).
- Runtime reset: the KEY0 behaviour of this image was NOT RUN (3.42 concerns the one-word
  image); the run began from the configuration-time reset-hold only.
- Timing/electrical: as 3.40 (internal routed timing only; no rail, clock or baud measurement;
  raw reset has no input delay and UART no output delay).
- Device identity: speed/temperature grade and board revision remain owner-accepted,
  unverified assumptions.
- Persistence: nothing was written to the SPI flash; the image is volatile.

### 3.44 — J11-GPIO-1 Wukong J11 lower-row GPIO diagnostic (2026-10-31)

**Classification:** **PASS: four-channel GPIO operation at logic-analyser threshold, with a
supplementary owner-reported voltage observation on pin 7.** This is a standalone Wukong GPIO
diagnostic. **It is a GPIO observation, not an SPU CPU result**, and it neither supports nor
extends sections 3.40 to 3.43. Entry prepared for review; not yet reviewed or committed.

```text
Claim: a single diagnostic bitstream, loaded once into SRAM, drove four registered square waves
  on J11 pins 7-10 of this Wukong V3 at approximately 1, 2, 4 and 8 Hz, observed by a logic
  analyser in two independent 8 s captures; an owner-reported multimeter reading on pin 7 was
  an alternation between about 3.3 V and about 0 V.
Evidence dimension: silicon (single observation); interface (GPIO, as observed)
Source revision / dirty-tree identity: standalone design outside tracked sources (repository
  baseline c922a01); no SPU CPU RTL, constraints, checkpoint or bitstream involved
Build/test command and configuration: Vivado 2026.1 non-project batch
  (build/j11-gpio-1-build/build_j11.tcl, sha256 2b3cd243e106dfcd3f70ad0f789477fe4e9f3998cd4e4e0a75cf0632018cb24e):
  synth, opt, place, route, write_bitstream; part xc7a100tfgg676-1; UNUSEDPIN=PULLNONE,
  COMPRESS=FALSE, USR_ACCESS=0x4A110001, CFGBVS=VCCO, CONFIG_VOLTAGE=3.3. Design
  rtl/j11_gpio1_top.v (12 lines, sha256 a66f950194481226e8136c2281facf11c0471aa2616922316a5d33b5d5277f41)
  and j11_gpio1.xdc (sha256 d272ceebdc1fbe2a27b9bbde403fccc1ce2720b757567b86e5cb29e5ea8915d0)
Device and toolchain: board QMTECH Wukong, owner-identified V3 (V03 schematic Rev 3.0, sha256
  bec53e6201c5c47a7059ce5b5af86e0f3a48535ebdf5643af7583171f7331aee); device XC7A100T-1FGG676C
  per seller listing and owner acceptance, NOT physically verified (as 3.40); JTAG idcode
  0x3631093; openFPGALoader v1.2.0 with DirtyJTAG; analyser: Saleae-type 0925:3881 (fixed input
  threshold) via sigrok-cli 0.7.2 and libsigrok 0.5.2, driver fx2lafw
Artifact identity: j11_gpio1.bit sha256
  a4ddc66c6fb41e3b00d1726436af7ae08afbbe11d626821fd435c19b9ecc120f (3,826,008 bytes);
  j11_gpio1.bin sha256 06dd158206eb4317496198d9708f9a837ab72b770cfa578ba3d9054a1a06a1f5
Oracle and checked scope: the design's exact timing (50 MHz / 3,125,000 cycles = 16 Hz tick;
  channels 8, 4, 2, 1 Hz) simulated at full and scaled size, with four mutants detected
  (build/j11-gpio-1-prep/sim); checked scope: two 8 s captures of four pins
Result and evidence artifact path: PASS; build/j11-gpio-1-run-01/ (12-entry MANIFEST.sha256,
  sha256 3d185b382f63c2727cdce88cbfe63916d86ce8351f8122c66c07527fafdba998); build evidence
  build/j11-gpio-1-build/ (30-entry manifest, sha256
  2364d2524f933bf285ed80cb37f7f753fe58a9923bffb8c122c2e4949d8d4971); design and procedure
  build/j11-gpio-1-prep/ (13-entry manifest, sha256
  d516cc5d6810f9692ac4212bc5e58c6f0127bf2f9d3df1648ead5058295a733d)
Adjacent evidence dimensions not established: see below
```

**Pin mapping (V03 sheet 2, read from the schematic itself):** J11 is a 12-pin PMOD header.
Lower-row pins 7, 8, 9 and 10 are nets BANK35_J4, BANK35_G4, BANK35_B4 and BANK35_B5, i.e. FPGA
balls J4, G4, B4 and B5 in bank 35, whose VCCO is tied to 3V3; pins 5 and 11 are GND and pins 6
and 12 are 3V3. Each net appears only at the FPGA ball and at J11. The tool's pin report
(`routed_io.rpt`) shows all four as LVCMOS33, DRIVE 8, SLEW SLOW. Channel assignment: CH0 = pin
7 (J4) 1 Hz, CH1 = pin 8 (G4) 2 Hz, CH2 = pin 9 (B4) 4 Hz, CH3 = pin 10 (B5) 8 Hz.

**Build:** COMPLETE, exit 0, 135 s (detached unit spu-j11-gpio-1-build-01-20261031T043836Z-265029);
0 unrouted nets, bitstream DRC 0 errors, no critical warnings, timing met (WNS +15.942 ns, WHS
+0.245 ns), 7 LUT and 26 FF; each GPIO output is an OBUF driven directly by a flip-flop.

**Procedure and result:** With the RP2350 and everything else disconnected from J11 and the
analyser the only device on J11 (D0 to D3 on pins 7 to 10, ground on pin 11; owner statement),
the session ran a 3 s baseline capture (CPU-ROM-2C image running, pins undriven by the design:
all four channels constant high), then exactly one `openFPGALoader -c dirtyJtag --freq 1000000
<bit>` (SRAM load, no flash options), exit 0 after 31.365 s (`Load SRAM 100.00%`, `Done`,
`isc_done 1`, `init 1`, `done 1`; `loader_output.txt` sha256
6d61d3fd0952e1f609b4b12e083b769e178ee4efd41844e86c854eb6aed78d85). Two independent 8 s
captures at 100 kHz (`sigrok-cli -d fx2lafw`, channels D0 to D3, VCD) started about 2 s after
the load returned and about 5 s after the first capture ended
(`capture1.vcd` sha256 8adaa4c3e2903cae68e8825810ebb99b9b9394068ed4e4a4bfb84dcaec6ff2a8,
`capture2.vcd` sha256 ea00fc1275e664c7783c1ba8356bcfaeb89ec57cb9ebc15d37b3502e6a19f16a;
`session.json` sha256 5343894f5038c53a736a9a32c679237af0efcdbb376ce334975e961a3f8b6629).
Both captures gave the same verdict:

| Channel | Pin (ball) | Edges in 8 s (expected) | Frequency | Duty | Shortest pulse |
|---|---|---|---|---|---|
| CH0 | 7 (J4) | 16 (16) | 0.9999 Hz | 0.500 | 0.500 s |
| CH1 | 8 (G4) | 32 (32) | 1.9999 Hz | 0.500 | 0.250 s |
| CH2 | 9 (B4) | 64 (64) | 3.9998 Hz | 0.500 | 0.125 s |
| CH3 | 10 (B5) | 128 (128) | 7.9996 Hz | 0.500 | 0.0625 s |

The four channels form a 4-bit binary counter that increments every 62.5 ms (CH3 least
significant); the decoded code (8*CH0 + 4*CH1 + 2*CH2 + CH3, sampled mid-tick) incremented by
exactly 1 at each of 127 tick boundaries in both captures. Both logic states were seen on every
channel, no two channels were identical, and no pulse shorter than the expected half-period
(no glitch) and no stuck or floating channel appeared. A post-load read-only JTAG detect found
idcode 0x3631093. The analyser script (`analyze_capture.py` sha256
e68c2266d9ebac5db222044ee7536d604df7f80b22d51c3230e013ef84cfb37a) failed all seven defective
synthetic captures in its offline tests. The owner's immediate pre-run confirmation of the
wiring and board condition was given interactively and is noted in `RESULT_NOTE.md`
(sha256 72bfa64b35232ab4bf0f389a0d86d2ec26becc47d979cb6de2aa1adabc139c84, unchanged).

**Owner-reported multimeter observation (supplementary):** After the session, with the diagnostic
image still running, the owner reported "Alternate pulsing between 3.3 and 0.0v on the pin 7 of
J11 checked with a digital multimeter" (`OWNER_MULTIMETER_2026-10-31.md`, sha256
b45444ed6256e99edd21d3c678a6852918f147595f654e7d5c26deaaf11388d9). Limitations: meter model,
range, ground point and accuracy were not recorded; the values are rounded, owner-reported
readings with no stored measurement or timestamp; only pin 7 (the 1 Hz channel) was measured;
pins 8 to 10 were observed by the analyser only. No calibrated voltage accuracy is claimed.

**Adjacent evidence dimensions not established (NOT RUN or not covered):**
- Voltage levels beyond the single owner-reported reading: the analyser reports logic state at
  its fixed threshold only; no calibrated, stored or per-pin voltage measurement exists.
- Loaded drive capability, signal integrity, edge rates, noise margin and long-term stability:
  NOT RUN (unloaded probes, two 8 s captures).
- Pin state before configuration: the pre-load baseline (all high) reflects undriven pins under
  the analyser's input and board pull state, not a design-controlled level.
- Pin health of J11 pins 1 to 4 and 6, 12 (top row, power): NOT RUN; the top row is recorded
  elsewhere as damaged and was not used.
- SPU CPU behaviour: none; this load replaced the CPU-ROM-2C image in SRAM (volatile, flash
  untouched), and the CPU image has not been reloaded.
- Device identity, repeatability across loads or units, and timing/electrical qualification: not
  established (one load, one unit; speed grade and revision as in 3.40).

### 3.45 — J11-TOP-2 Wukong J11 upper-row output diagnostic (2026-11-01)

**Classification:** **PASS: four-channel digital output observation on J11 pins 1 to 4 at
logic-analyser threshold, through owner-reported 1 kΩ series resistors.** This is a standalone
Wukong GPIO diagnostic, **not an SPU CPU result**; it neither supports nor extends sections 3.40
to 3.43. It is a single-run output-function observation and **not** a qualification of the pins.
Entry prepared 2026-11-01 and committed with the owner's authorisation; reviewer comments on the
companion documentation patch were addressed before commit.

```text
Claim: a single diagnostic bitstream, loaded once into SRAM, drove four registered square waves
  on J11 pins 1-4 (balls H4, F4, A4, A5) of this Wukong V3 at approximately 1, 2, 4 and 8 Hz,
  observed by a logic analyser in two 8 s captures with owner-reported 1 kOhm series resistors in
  the analyser signal leads; the captures were clean (correct frequencies, 50 percent duty, a
  127-step counter sequence, no glitch, no stuck output) and a post-run JTAG detect succeeded.
Evidence dimension: silicon (single observation); interface (GPIO output, as observed)
Source revision / dirty-tree identity: standalone design outside tracked sources (repository
  baseline 5a278ce); no SPU CPU RTL, constraints, checkpoint or bitstream involved
Build/test command and configuration: Vivado 2026.1 non-project batch
  (build/j11-top-2-build/build_top2.tcl, sha256 c3366c685b2ec2fbddeca11de25b9f583bcc77ce2729a65bf8e452b1f2722e5b):
  synth, opt, place, route, write_bitstream; part xc7a100tfgg676-1; UNUSEDPIN=PULLNONE,
  COMPRESS=FALSE, USR_ACCESS=0x4A110003, CFGBVS=VCCO, CONFIG_VOLTAGE=3.3. Design
  rtl/j11_top2_top.v (12 lines, sha256 04dfb2321be54ab22446f1073a4dc4fd48b91d94cf284d7e0711126e2cb8121d)
  and j11_top2.xdc (sha256 08dcab25887263768b5f6bf18eed9347732068c28b32049c77b2daa9af5c4a1c)
Device and toolchain: board QMTECH Wukong, owner-identified V3 (V03 schematic Rev 3.0, sha256
  bec53e6201c5c47a7059ce5b5af86e0f3a48535ebdf5643af7583171f7331aee); device XC7A100T-1FGG676C
  per seller listing and owner acceptance, NOT physically verified (as 3.40); JTAG idcode
  0x3631093; openFPGALoader v1.2.0 with DirtyJTAG at 1 MHz; analyser: Saleae-type 0925:3881 (fixed
  input threshold) via sigrok-cli 0.7.2 and libsigrok 0.5.2, driver fx2lafw
Artifact identity: j11_top2.bit sha256
  d914b7a4067bc80e272a2d7b583e55ffd16e4741661de567488a95f42404dc42 (3,826,007 bytes);
  j11_top2.bin sha256 04112080d97cf7c57019d1ca3311fdabd4634df73eebef2cbb1c973590972853
Oracle and checked scope: the design is the J11-GPIO-1 counter (50 MHz / 3,125,000 cycles = 16 Hz
  tick; outputs 1, 2, 4, 8 Hz) on different ports; simulated at full and scaled size with four
  mutants detected (build/j11-top-2-prep/sim); checked scope: two 8 s captures of four pins
Result and evidence artifact path: PASS; build/j11-top-2-run-01/ (10-entry MANIFEST.sha256,
  sha256 b6142a9c46ed877f4b098ccb69e336c3353efa1cf084efae2e8048513c98bc16); build evidence
  build/j11-top-2-build/ (30-entry manifest, sha256
  de422915e8cc265897b2923d9091c11cd6fe3cefa4b5905f758ccda4af06f2d0); design and procedure
  build/j11-top-2-prep/ (14-entry manifest, sha256
  8b2cc3d7eae304d3b991ef63a62a4ac35143d378d68b1df85523774c6574ba65)
Adjacent evidence dimensions not established: see below
```

**Pin mapping (V03 sheet 2; balls and bank from Vivado 2026.1 package data):** J11 pins 1, 2, 3, 4
are nets BANK35_H4, F4, A4, A5, i.e. FPGA balls H4, F4, A4, A5 in bank 35, whose VCCO is tied to
3V3 (`routed_io.rpt`: VCCO_35 3.30 V). All four are outputs LVCMOS33, DRIVE 4 mA, SLEW SLOW, no
pull, each an OBUF driven directly by a flip-flop; the design has exactly four OBUFs and one IBUF
(the 50 MHz clock, M21), no OBUFT, IOBUF or differential buffer. Channel assignment: D0 = pin 1
(H4) 1 Hz, D1 = pin 2 (F4) 2 Hz, D2 = pin 3 (A4) 4 Hz, D3 = pin 4 (A5) 8 Hz; analyser ground on
pin 5. Balls and bank are those of the J11 top row of the same connector as 3.44's pins 7 to 10.

**Build:** COMPLETE, exit 0, 153 s (detached unit spu-j11-top-2-build-01-20261101T032616Z-290752);
40 of 40 routable nets routed, bitstream DRC 0 errors, no critical warnings, timing met (WNS
+15.942 ns, WHS +0.245 ns), 7 LUT and 26 FF; the analyser `J11_TOP2_BUILD_CHECK` printed PASS
(17 checks, no amendment needed).

**Procedure and result:** With the RP2350 and every other peripheral disconnected, the owner
stated that each analyser signal lead D0 to D3 was fitted in series with a 1 kΩ resistor (measured
0.9 to 1.1 kΩ per the procedure), to J11 pins 1 to 4, ground on pin 5, fitted with the board
unpowered and passively checked (no bridging, no reading below 100 Ω to GND or 3V3, nothing on
pins 6 to 12); **these wiring and resistor statements are owner-reported and were not verified
by instrument**. The session ran exactly one `openFPGALoader -c dirtyJtag --freq 1000000 <bit>`
(SRAM load, no flash options), exit 0 after 31.363 s (`Load SRAM 100.00%`, `Done`; `loader_output.txt`
sha256 f2d0220b9d3cd149ca24537447188debfff918005b5436b53921d107b1844c96), then two 8 s captures
at 100 kHz (`sigrok-cli -d fx2lafw`, channels D0 to D3, VCD) about 2 s and about 5 s later
(`capture1.vcd` sha256 3d9d065e5f92691a94873088dc7511fd0048900d74fc41bdf3130960a12b6b18,
`capture2.vcd` sha256 c3bb9c7efdc937d7ca649ffa54a47d20d2108727cba5e05dbccfc44bd4b9e1be;
`session.json` sha256 0429de6cec7316afa6a3fd343a6254af383ec047a8a956dfd310fd8d2c334388), 2026-11-01
07:52 UTC. Both captures gave the same verdict:

| Channel | Pin (ball) | Edges in 8 s (expected) | Frequency | Duty | Shortest pulse |
|---|---|---|---|---|---|
| D0 | 1 (H4) | 16 (16) | 0.9999 Hz | 0.500 | 0.500 s |
| D1 | 2 (F4) | 32 (32) | 1.9999 Hz | 0.500 | 0.250 s |
| D2 | 3 (A4) | 64 (64) | 3.9998 Hz | 0.500 | 0.125 s |
| D3 | 4 (A5) | 128 (128) | 7.9996 Hz | 0.500 | 0.0625 s |

The four channels form a 4-bit binary counter that increments every 62.5 ms (D3 least
significant); the decoded code (8*D0 + 4*D1 + 2*D2 + D3, sampled mid-tick) incremented by exactly
1 at each of 127 tick boundaries in both captures. Both logic states were seen on every channel,
no two channels were identical, and no pulse shorter than the expected half-period (no glitch) and
no stuck or floating channel appeared. A post-load read-only JTAG detect found idcode 0x3631093.
The analyser script (`analyze_capture.py`, J11-GPIO-1 logic with names only changed, sha256
db4d10f4c7f8ea64b1f33bea79b4e74cae236e3774f220cbadd2a565bd9cb1f6) failed all seven defective
synthetic captures in its offline tests. A POWER DOWN desktop notice was issued after the
captures (07:53:08 UTC); the time the board was powered down was not recorded.

**Context and attempts that are not results:** (1) J11-TOP-1 (an input-sampling design, built and
verified offline: build/j11-top-1-build/, manifest sha256
8ba9f14b3e30775549a50ec67ac44f5174e3c47e2440e82ab800029a0d057d8b) and its Stage A load
(build/j11-top-1-run-01/, REVISE) and (2) a GPIO-1 control load (build/j11-gpio-1-control-01/,
HOLD) both returned four constant-high channels. The owner then reported the analyser leads had
been on J11 pins 1 to 6 (the top row) instead of pins 7 to 10; both runs are therefore invalid as
tests (placement error), say nothing about the images or pins, and no output was driven on pins
1 to 4 in either (addenda in those directories). The J11-TOP-1 input-sampling experiment was not
completed. (3) A passive unpowered multimeter inspection of J11 pins 1 to 4 against the lower row
(build/j11-toprow-inspection-run/, manifest sha256
e448dc1eed9d7a2ed471e471c3b4d95923eab068700b8958d92f920201531b32) was rough and inconclusive:
no pin was consistent with the reference pins, the sheet had unit and missing-reading defects,
and meter diode-mode drops of about 1.15 V appeared on healthy and suspect pins alike.

**Relation to the historical record:** the repository records J11 pins 1 to 3 as damaged by an
RP2350 backfeed incident in July 2026 (RP2350 powered and driving the pins while the FPGA board
was unpowered; a meter reading of about 1.0 V noted at the time). This observation does not test
that incident's cause and does not establish that the pins are undamaged. It shows only that,
under the stated conditions, the four output buffers produced correct logic square waves once.
Section 3.44's statement that the top row was "recorded elsewhere as damaged and was not used" is
accurate for that entry and is not altered.
**Resulting top-row classification (J11 pins 1 to 4): BACKFEED-EXPOSED, HISTORICALLY JUDGED DAMAGED,
DIGITAL OUTPUT OBSERVED ONCE, REMAINING FUNCTIONS UNQUALIFIED; provisionally excluded from new SPU
interfaces.**

**Adjacent evidence dimensions not established (NOT RUN or not covered):**
- Voltage levels: the analyser reports logic state at its fixed threshold only; no voltage
  measurement was made on pins 1 to 4 (the optional meter reading was not taken).
- Drive strength: NOT RUN; DRIVE 4 mA behind 1 kΩ into a high-impedance analyser input; behaviour
  at higher drive, without the resistor, or under load is not established.
- Input-buffer function of pins 1 to 4: NOT RUN (J11-TOP-1 was not completed).
- Long-term reliability, repeatability across loads or units, signal integrity, edge rates,
  noise margin, thermal behaviour and supply current: NOT RUN (one load, one unit, two 8 s
  captures); no current, heat or supply measurement was made.
- Wiring and resistor values: owner-reported, not instrument-verified; the power-down time was
  not recorded.
- Pin 5 (GND) and pins 6, 12 (3V3) as used by the analyser ground: not separately qualified.
- SPU CPU behaviour: none; this load replaced whatever image was in SRAM (volatile, flash
  untouched), and the CPU image has not been reloaded.
- Device identity and timing/electrical qualification: not established (speed grade and revision
  as in 3.40).

### 3.46 — H0-BOARD-UART-3B first UART-loaded programmable H0 CPU run on Wukong (2026-11-03 UTC)

**Classification:** **PASS: single-session silicon observation.** One SRAM-configured
image of the experimental H0 programmable Gen-1 Surd CPU accepted two distinct 14-word programs
over the onboard CH340 USB-UART, executed both and returned the exact oracle results, without
reconfiguration between them; a KEY0 reset then invalidated the program and result state and the
UART recovered. This is one run of one bitstream on one board. It is **not** a qualification of
the UART interface, timing margin, electrical behaviour or the H0 design; the H0 path is
experimental research RTL (`research/`), not production RTL.

```text
Claim: bitstream h0_board_uart.bit (sha256 775f2a36...cdad28), loaded once into SRAM, received
  host-encoded protocol-v1 frames at 115200 8N1 on F3 and answered on E3. Program A (15 LOAD, VALIDATE,
  START) returned six slices (13,0,4,0,9,0) as run 1; program B, loaded in the same recorded
  session after the single SRAM configuration, returned (7,0,4,0,4,0) as run 2; every LOAD/VALIDATE/START/STATUS/RESULT
  reply had status 00. After one owner KEY0 press, STATUS reported image invalid, not complete,
  run 0; RESULT and START were refused (0x20); STATUS still answered.
Evidence dimension: silicon (single observation); interface (UART RX/TX, as observed)
Source revision / dirty-tree identity: dev/next d9a25d2 (H0-UART-1C-R1 integration) plus the
  untracked board package research/h0_board_uart_1a/ in build/h0-board-uart-1a-worktree,
  SOURCES.sha256 39f4cf8bfa3464719596a491d47073f0b1c2c4a58a5a30b1860731d006396807 (50/50 OK);
  frozen Gen-1 package PACKAGE_SHA256.txt 36/36 OK
Build/test command and configuration: H0-BOARD-UART-2 Vivado 2026.1 non-project synth/opt/place/
  route (job spu-job-01-20261103T204107Z-495095, COMPLETE 882 s; external 5 GiB-preflight
  waiver wrapper sha256 979ad98d...; owner-authorized) -> routed.dcp sha256 4098ab7f...e3124c6b;
  H0-BOARD-UART-3A write_bitstream (job spu-job-01-20261103T210904Z-500166, COMPLETE 128 s),
  UNUSEDPIN=PULLNONE; part xc7a100tfgg676-1; CLKS_PER_BIT 217 at nominal 25 MHz cpu_clk
Device and toolchain: board QMTECH Wukong, owner-identified V3 (V03 schematic sha256
  bec53e62...7331aee); device XC7A100T-1FGG676C per seller listing, NOT physically verified (as
  3.40); JTAG idcode 0x3631093 before and after; openFPGALoader v1.2.0 with DirtyJTAG
  CB81353DCE678119 at 1 MHz; CH340 1a86:7523 /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0;
  host Linux 6.8.0-138, Python 3.10.12, raw termios (no pyserial)
Artifact identity: h0_board_uart.bit sha256
  775f2a36b71788eebb4704ac8be07122bc344721dd69fc67aba44569f2cdad28 (3,826,000 bytes)
Oracle and checked scope: board_oracle / H0-ORACLE-1 expected slices A (13,0,4,0,9,0),
  B (7,0,4,0,4,0); host frames from committed research/h0_uart_1c/host_loader.py (sha256
  8a1092af...) via execute(); checked scope: two programs, one reset, one session
Result and evidence artifact path: PASS; build/h0-board-uart-3b/ (17-entry MANIFEST.sha256,
  sha256 8348fb763b334c5f9f86a21d1bf3ec52fb41c58d303401ffba8c289ba3e34024)
Adjacent evidence dimensions not established: see below
```

**Procedure and result.** Preflight 2026-11-03 21:17 UTC: bitstream hash matched, JTAG detect
found one device (idcode 0x3631093); `fuser` reported no process holding /dev/ttyUSB0,
/dev/ttyACM0 or /dev/ttyACM1, while the recorded process-pattern check
(`pgrep -fc 'hw_server|openFPGALoader|minicom|picocom'`) returned `conflicting_procs=2` and did
not identify those processes (`preflight/preflight.txt`); no logic analyser enumerated; the bitstream assigns only M21, H7, F3, E3 (no J11 pin; unused pins
high-impedance). Exactly one `openFPGALoader -c dirtyJtag --freq 1000000 <bit>` (SRAM, no flash
options): exit 0 after 31.4 s, `Done`, `isc_done 1 init 1 done 1` (`program/loader_output.txt`
sha256 f25f27da...). Session `run-01` (21:18:36 UTC, 0.92 s; 475 bytes sent, 341 received,
0 stale bytes drained before):

| Step | Replies | Observed |
|---|---|---|
| Initial STATUS | 00 | flags 0x00, run 0 |
| Program A: LOAD CRC + 14 words, VALIDATE, START | 15 x 00, 00, 00 | — |
| A: STATUS (poll), RESULT, STATUS | 00, 00, 00 | complete, run 1; slices **(13,0,4,0,9,0)** = oracle |
| Program B: LOAD CRC + 14 words, VALIDATE, START | 15 x 00, 00, 00 | no recorded openFPGALoader call between A and B |
| B: STATUS (poll), RESULT, STATUS | 00, 00, 00 | complete, run 2; slices **(7,0,4,0,4,0)** = oracle |

Bank selection: under the reviewed controller implementation, promoting program B places it in
the alternate bank; the bank in use is not reported over UART, so this placement was not directly
observed in the captured traffic. Continuity: the evidence contains one successful SRAM
programming command, one continuous recorded A/B UART session and STATUS run IDs progressing
from 1 to 2. These observations support execution of A and B without intervening
reconfiguration, but they do not independently exclude unrecorded external actions or prove
continuous image validity between the recorded STATUS replies.
The owner then pressed KEY0 once and reported power and DONE LEDs on and nothing unusual
(owner-reported, `owner_observations.txt`). Session `post-01` (21:19:44 UTC): STATUS 00 flags 0x00
run 0 (image invalid, no owner, not complete); RESULT refused 0x20 with no payload; START refused
0x20 (no valid image); final STATUS 00 flags 0x00 run 0. A post-session JTAG detect returned
idcode 0x3631093. Raw traffic: `run-01/traffic.jsonl` (sha256 d24ac0c6...), `post-01/traffic.jsonl`
(sha256 47c51c41...); decoded summaries `run-01/decoded.json`, `post-01/decoded.json`; harness
`session.py` (sha256 845681e6...).

**Relation to other evidence (reported separately).** Simulation: H0-UART-1C/1D focused suites
and the independent asynchronous-host bench (217 cycles/bit, ±2% baud) — RTL only. Implementation:
H0-BOARD-UART-2 retained 1,792/1,792 bank and 192/192 result bits with 192/192 result-to-TX paths,
reset structure UNSAFE=0 (1,287 endpoints), cpu_clk WNS +5.968 ns, WHS +0.015 ns, recovery
+17.164 ns, removal +0.387 ns — tool reports, not measurements. H0-PHYS-2 (program-A-specialized)
and H0-OPT-2 (synthesis-only) are not extended by this entry.

**Adjacent evidence dimensions not established:**
- Only two fixed programs, one session, one reset; no other programs, operands or repeat runs.
- No baud-error, clock or rail measurement; no signal-integrity, temperature or margin testing.
- Hold slack is +15 ps (tool estimate); asynchronous reset input timing not analysed.
- KEY0 press and LED states are owner-reported, not instrumented; the reset is inferred from
  the post-reset STATUS.
- No error-injection on the physical link (malformed frames, timeouts, drain) was performed.
- XOR frame check; lost-response ambiguity; run-ID wrap/reset; untagged-retirement caveat remain.
- No configuration-flash image; volatile SRAM only. Device grade not physically verified.
