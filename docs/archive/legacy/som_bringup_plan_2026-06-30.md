# SOM/BMU Classifier Bring-Up Plan

Date: 2026-06-30

This plan covers bringing the Self-Organizing Map / Best-Matching-Unit classifier
from RTL simulation through to silicon on the Tang Primer 25K. The currently
Tang-proven path is the serial seven-node `spu_som_bmu.v` classifier plus
`spu_cluster_reduce.v`; the parallel `spu_som_node_array.v` path remains an RTL
track for later RPLU2 integration.

## What's Already Proven

| Layer | Status | Evidence |
|---|---|---|
| Rational SOM oracle (Python) | PASS — 24 checks | `software/tests/test_rational_som.py` |
| Rational SOM oracle (C++) | PASS — parity with Python | `software/common/tests/spu_rational_som_test.cpp` |
| Serial BMU scan (`spu_som_bmu.v`) | PASS — 7-node fixture | `test_som_bmu_rtl_trace.py` |
| Tang 25K SOM/BMU silicon probe | PASS — UART `SOM:P T:2 B:6 E:00` | `build_25k_spu13_som_bmu_probe.sh` |
| **Parallel SOM node** (`spu_som_node.v`) | PASS — 4 checks (quadrance + training) | `spu_som_node_tb.v` |
| **Parallel SOM array** (`spu_som_node_array.v`) | Compiles — WTA tree verified | `spu_som_node_array.v` |
| **BTU collision resolver** | PASS — 7 scenarios (single/dual/triple/zero) | `btu_collision_tb.v` |
| VM-vs-RTL trace equivalence | PASS — bit-exact on 2 built-in fixture scenarios | `test_som_bmu_rtl_trace.py` |
| Core integration (`spu13_core.v`) | Synthesises behind `ENABLE_CORE_SOM=1` | `spu13_core.v:1114-1198` |
| Opcode 0x2A `SOM` / 0x2B `SOM_TRAIN` | Wired into sequencer FSM | `spu13_core.v:1178-1192` |

## Architecture — RPLU v2 Parallel Array

```
QR regfile lane[s]
    │
    │ 4 RationalSurd features (288 bits, 4×{P18,Q18})
    ▼
┌─────────────────────────────────────────────────────┐
│  spu_som_node_array (MAX_NODES=7, NUM_FEATURES=4)  │
│  ┌──────────┐ ┌──────────┐       ┌──────────┐      │
│  │ node[0]  │ │ node[1]  │  ...  │ node[6]  │      │
│  │ 3-stage  │ │ 3-stage  │       │ 3-stage  │      │
│  │ quadrance│ │ quadrance│       │ quadrance│      │
│  └────┬─────┘ └────┬─────┘       └────┬─────┘      │
│       └─────────────┴─────────────────┘             │
│                     │                               │
│          Winner-Take-All Comparator Tree             │
│          BMU + 2nd-best + confidence gap             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              cluster_label, ambiguity flag
                       │
                       ▼
              BTU → A₃₁ coordinates
                       │
                       ▼
              rplu_thimble_pade (Padé approximant)
                       │
                       ▼
              hex_q/hex_r → UART telemetry
```

### Seven-Node Hex Fixture (Hardcoded in `spu_som_bmu.v`)

| Node | (q,r) | Label | Weight w0 | Weight w1 | Weight w2 | Weight w3 |
|---:|---|---:|---:|---:|---:|---:|
| 0 | (0,0) | 0 | 0 | 0 | 0 | 0 |
| 1 | (1,0) | 1 | 2 | 0 | 0 | 0 |
| 2 | (1,-1) | 1 | 0 | 2 | 0 | 0 |
| 3 | (0,-1) | 2 | 0 | 0 | 2 | 0 |
| 4 | (-1,0) | 2 | -2 | 0 | 0 | 0 |
| 5 | (-1,1) | 3 | 0 | -2 | 0 | 0 |
| 6 | (0,1) | 3 | 0 | 0 | -2 | 1+1√3 |

Cluster labels 0–3 map to RPLU material classes: 0=carbon, 1=iron, 2=aluminum, 3=titanium.

## Phase 0: Simulation Replay (Now — No FPGA Required)

Goal: produce deterministic visual artifacts and golden trace files from existing
simulations before touching any synthesis scripts.

### 0.1 Run Oracle Tests

```sh
python3 software/tests/test_rational_som.py
# Expected: 24 passed, 0 failed

python3 software/tests/test_som_bmu_rtl_trace.py
# Expected: SOM BMU RTL TRACE: PASS
```

### 0.2 Generate Golden Trace Files

Run the RTL trace test with dump enabled to produce a VCD under `build/`:

```sh
python3 software/tests/test_som_bmu_rtl_trace.py --dump build/som_bmu_golden.vcd
```

This trace exercises the two built-in seven-node fixture scenarios shared with
the silicon probe. Additional edge cases, including tie-breaking and skipped
invalid nodes, remain covered by the software oracle tests.

### 0.3 Host Visual Renderer (Phase 0 of `docs/archive/legacy/visual_som_devboard_plan.md`)

Before the FPGA is ready, build a desktop renderer that consumes the SOM BMU
frame (telemetry ABI v0 frame_type 0x01) and renders the hex map:

1. Read the golden trace scenarios.
2. Produce a static HTML/SVG or Python `matplotlib` hex map rendering.
3. Encode each node as: cell hue = cluster/material class, brightness = recent
   activity, outline = BMU, split outline = second-best, hatch = ambiguous.

Keep renderer scripts in `tools/`, not under `build/`. Golden images go in
`build/` only.

### 0.4 Expand the Node Fixture (Optional)

The 7-node fixture is a minimal proof. Before silicon, consider expanding to a
larger Nguyen-style hex lattice. The fixture lives in `spu_som_bmu.v` lines
59–99. Expansion requires:

1. Update `MAX_NODES` parameter.
2. Add new `assign node_valid[N] / node_id[N] / node_label[N] / node_w[N]` blocks.
3. Regenerate the golden trace with `test_som_bmu_rtl_trace.py`.
4. Update the software oracle fixture in `rational_som.py` to match.

Keep the 7-node fixture as the default; larger fixtures go behind a parameter or
a separate synth variant.

## Phase 1: Synthesis Integration (Now — Dry Run)

Goal: confirm that the full SPU-13 + SOM pipeline synthesises and passes P&R on
the 25K before the replacement board arrives.

### 1.1 Create SOM-Enabled Synthesis Script

The existing `build_25k_spu13_math_probe.sh` already reads
`synth_gowin_25k_spu13_math_probe.ys`, which includes `spu_som_bmu.v` and
`spu_cluster_reduce.v` but keeps `ENABLE_CORE_SOM=0`. Create a variant that
enables it:

```sh
cp hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_math_probe.ys \
   hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_probe.ys
```

Change the chparam line:

```tcl
chparam -set ENABLE_SDRAM 0 \
        -set ENABLE_CORE_RPLU 0 \
        -set ENABLE_CORE_LATTICE 0 \
        -set ENABLE_CORE_MATH 1 \
        -set ENABLE_CORE_SOM 1 \
        spu13_tang25k_top
```

Create the build script:

```sh
# build_25k_spu13_som_probe.sh

#!/usr/bin/env bash
set -e
mkdir -p build
export PATH=$PATH:/opt/oss-cad-suite/bin

echo "--- 1. Yosys Synthesis (SPU-13 SOM probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu13_som_probe.json \
    --write build/spu13_som_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --cpu_as_gpio \
    build/spu13_som_probe_pnr.json \
    -o build/tang_primer_25k_spu13_som_probe.fs

echo ""
echo "=== SPU-13 SOM Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_som_probe.fs"
```

### 1.2 Dry-Run Synthesis

```sh
bash build_25k_spu13_som_probe.sh
```

Record the resource report from Yosys output:

```
LUTs:  [record here]
FFs:   [record here]
BRAMs: [record here]
DSPs:  [record here]
```

The expected overhead from `ENABLE_CORE_SOM=1` is +39 LUTs, +~50 FFs. If the
math probe already pushes near LUT limits, the SOM variant may need to drop
the math path (rotor core) to fit — the first SOM-in-silicon image can be
math-disabled and just prove the BMU scan + UART telemetry.

### 1.3 LUT-Reduction Fallback: SOM-Only Probe

If the full math+SOM probe doesn't route, create a minimal SOM-only variant:

```tcl
chparam -set ENABLE_SDRAM 0 \
        -set ENABLE_CORE_RPLU 0 \
        -set ENABLE_CORE_LATTICE 0 \
        -set ENABLE_CORE_MATH 0 \
        -set ENABLE_CORE_SOM 1 \
        spu13_tang25k_top
```

This image proves the SOM pipeline, UART telemetry, and hex output without the
rotor/ALU datapath. Re-enable the math path only when that combined image is
the explicit target.

## Phase 2: SOM Silicon Blaze

Goal: run `SOM_CLASSIFY` on hardware and capture deterministic UART telemetry.

2026-06-30 status: complete for the dedicated Tang SOM/BMU probe. The route
reports 13,189 LUT4 / 959 DFF / 1,130 ALU, 0 BRAM, 0 DSP, and 84.75 MHz
post-route max frequency at the 12 MHz target. SRAM load repeatedly reports:

```text
SOM:P T:2 B:6 E:00
```

This is a primitive BMU/classifier proof. SOM training, larger BRAM-backed
maps, material-bank gating, and visual telemetry frames remain future phases.

### 2.1 Load the Bitstream

```sh
openFPGALoader -b tangprimer25k \
    build/tang_primer_25k_spu13_som_bmu_probe.fs
```

### 2.2 Boot Sequence

The sequencer ROM must emit a `SOM_CLASSIFY` instruction after QR hydration:

```asm
; Minimal SOM blaze program
QLDI  R0, 0x0000, 0x0000    ; QR[0].A = (0, 0)
QLDI  R0, 0x0001, 0x0000    ; QR[0].B = (1, 0)  — push to feature vector lane
SOM_CLASSIFY  R0, R0         ; classify QR[0] through SOM map
; Expected: hex_q = label, hex_r[0] = ambiguous flag
```

### 2.3 UART Telemetry Proof Lines

Expected UART output from the dedicated SOM/BMU probe:

```
SOM:P T:2 B:6 E:00
```

`T:2` means both built-in fixture oracle scenarios were checked. `B:6` means
the final scenario selected node 6, the surd/titanium fixture. `E:00` means no
BMU or cluster-reduce mismatch was detected.

### 2.4 Per-Scenario Silicon Check

| Feature Vector (canonical) | Expected BMU | Expected Label | Expected Ambiguous |
|---|---|---|---|
| (0, 0, 0, 0) | Node 0 | 0 (carbon) | 0 |
| (2, 0, 0, 0) | Node 1 | 1 (iron) | 0 |
| (0, 2, 0, 0) | Node 2 | 1 (iron) | 0 |
| (0, 0, 2, 0) | Node 3 | 2 (aluminum) | 0 |
| (-2, 0, 0, 0) | Node 4 | 2 (aluminum) | 0 |
| (0, -2, 0, 0) | Node 5 | 3 (titanium) | 0 |
| (0, 0, -2, 1+1√3) | Node 6 | 3 (titanium) | 0 |
| (1, 1, 1, 1) | Node 1 | 1 (iron) | 0 |
| (0, 0, 0, 2) | (tie-break) | deterministic | check tie-breaking |

The dedicated silicon probe covers the two scenarios used by
`test_som_bmu_rtl_trace.py`: `(2,1,0,0)` and `(0,0,-2,2+1√3)`. The broader
table remains the next expansion target for a BRAM-backed or sequencer-driven
probe.

### 2.5 Known Limitations on Damaged 25K

If the damaged 25K is still the only board available when SOM silicon testing
begins:

- SDRAM is unavailable — no large SOM map hydration from flash.
- The 7-node hardcoded fixture is the max that fits in LUT-only ROM.
- UART telemetry uses the existing one-pulse hex_valid pattern (must be cleared
  each cycle).
- LUT utilization near ceiling — may need the SOM-only (math-disabled) variant.

## Phase 3: SOM + RPLU Material Gating

Goal: prove the SOM label → RPLU material_id path that gates which RPLU table
bank is active.

### 3.1 Enable Both SOM and RPLU

Build the combined SOM+RPLU probe:

```tcl
chparam -set ENABLE_CORE_MATH 1 \
        -set ENABLE_CORE_RPLU 1 \
        -set ENABLE_CORE_SOM  1 \
        spu13_tang25k_top
```

### 3.2 Test the Gating

```asm
QLDI  R0, 0x0002, 0x0000    ; features that push to iron cluster (label=1)
SOM_CLASSIFY  R0, R0         ; classify → som_material_id = 1 (iron)
; RPLU reads som_material_id via rplu_material_id wire (spu13_core.v:868)
; Verify RPLU uses iron table bank, not carbon
```

Expected telemetry:

```
H:0001 0000    # SOM label = 1 (iron)
R:XXXXXXXX A:D # RPLU address driven by iron material table, not carbon
```

### 3.3 Four-Material Sweep

Exercise all four cluster labels and confirm each gates the correct RPLU
material bank. This bridges the SOM classifier to the RPLU correction surface.

## Phase 4: Nguyen Cluster Scaling (Post Silicon Blaze)

Once the 7-node fixture passes in silicon:

### 4.1 Expand to Larger Hex Lattice

The fixture is hardcoded in `spu_som_bmu.v`. For a 19-node or 37-node hex lattice,
the fixture must move to BRAM or a flash-loaded table. Options:

| Approach | Cost | Complexity | Fit on 25K |
|---|---|---|---|
| LUT ROM (current) | 0 BRAM | Low | Up to ~12 nodes |
| BRAM-initialised fixture | 1 BRAM | Medium | 100+ nodes |
| Flash-loaded (RPLU-style) | 1 BRAM + flash region | Higher | 100+ nodes, persistent |

### 4.2 Nguyen Weight → BRAM Tiering

See `knowledge/NGUYEN_WEIGHT_PARTITIONING.md` and
`knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md` for the laminar weight
partitioning strategy. Once BRAM-backed SOM maps are available, implement:

- Cold cluster: rarely-active nodes in flash, paged on demand.
- Warm cluster: recent BMUs in streaming BRAM registers.
- Hot cluster: current BMU and nearest-neighbor ring in dedicated flip-flops.

## Phase 5: Integration with the Telemetry ABI

### 5.1 SOM BMU Frame (type 0x01)

The visual telemetry ABI (defined in `docs/archive/legacy/visual_som_devboard_plan.md`) includes
frame type `0x01` for SOM BMU data:

```
byte  0      magic 0x53
byte  1      magic 0x56
byte  2      version 0
byte  3      frame_type = 0x01
byte  4..7   sequence
byte  8..11  cycle_count
byte 12..13  flags
byte 14..15  payload_len
byte 16..17  best_node_id
byte 18..19  second_node_id
byte 20..21  cluster_label
byte 22      material_id
byte 23..26  best_q (32-bit surd)
byte 27..30  confidence_gap (32-bit surd)
byte 31      flags: [0]=has_second, [1]=ambiguous
last 4       crc32
```

### 5.2 UART Adapter (Phase 1 of Visual Plan)

During bring-up, encode frames as ASCII-safe hex over the existing 115200 baud
UART path. Extend `tools/visualizer.py` to parse frame type 0x01 and render the
hex map.

## Proof Checklist

- [x] Phase 0.1: Oracle tests pass (24 + RTL trace)
- [ ] Phase 0.2: Golden VCD trace generated
- [ ] Phase 0.3: Host visual renderer renders hex map from trace
- [x] Phase 1.1: SOM/BMU synthesis script created
- [x] Phase 1.2: Dry-run synthesis passes with resource report
- [x] Phase 2.1: Bitstream loads on Tang 25K
- [x] Phase 2.3: UART telemetry shows `SOM:P T:2 B:6 E:00`
- [x] Phase 2.4: Two built-in fixture scenarios match golden trace in silicon
- [ ] Phase 3.2: SOM label gates correct RPLU material bank
- [ ] Phase 3.3: Four-material sweep passes
- [ ] Phase 5.1: SOM BMU frame emitted over UART
- [ ] Phase 5.2: Visual renderer consumes live frame

## References

- SOM BMU RTL: `hardware/rtl/core/spu13/spu_som_bmu.v`
- Cluster reduce RTL: `hardware/rtl/core/spu13/spu_cluster_reduce.v`
- Core integration: `hardware/rtl/core/spu13/spu13_core.v` lines 1107–1198
- Software oracle: `software/lib/rational_som.py`
- Oracle tests: `software/tests/test_rational_som.py`
- RTL trace test: `software/tests/test_som_bmu_rtl_trace.py`
- C++ oracle: `software/common/include/spu_rational_som.h`
- Nguyen partitioning: `knowledge/NGUYEN_WEIGHT_PARTITIONING.md`
- SOM Nguyen notes: `knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md`
- Visual devboard plan: `docs/archive/legacy/visual_som_devboard_plan.md`
- RP MCU bring-up: `docs/rp_mcu_bringup_plan.md`
