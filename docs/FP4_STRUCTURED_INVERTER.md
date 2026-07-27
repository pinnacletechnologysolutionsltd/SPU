# Structured A31 inverter candidate

Status: split formal gate passed; seven of eight consumer builds pass;
production default unchanged.

This tranche replaces the inverter's seven general A31 transactions (112
logical M31 products) with four structure-specific requests totaling exactly
20 products:

| Request | Products | Result |
|---|---:|---|
| Stage A | 6 | `Z * conj_5(Z) -> (w0,w1,0,0)` |
| Stage B | 2 | `w0^2 - 3*w1^2 -> N` |
| Stage D1 | 8 | `Z_conj * (wc0,wc1,0,0) -> Temp` |
| Stage D2 scale | 4 | four independent `Temp[i] * N_inv` products |
| **Total** | **20** | **four structured requests** |

The general Padé multiplier remains required. The candidate shared-parallel
backend therefore expresses each request as a patterned ordinary A31
transaction and reuses both the existing 16-product bank and its combiner; it
does not add a narrow multiplier or a second combiner. Its `logical_products`
count is the unique algebraic schedule above, while the fixed physical bank
still evaluates the zero/repeated lanes in parallel. The sequential backend
executes only the declared number of schedule entries. Both candidates retain
mod-3 residue checking for every structured result.

## Formal resolution

This tranche uses contract resolution **(b), the split gate**. The new
operand-map and modular-combiner blocks are parameterized and proven against
an independently written full-product reference at field/product width pairs
3/6 and 4/8. The complete candidate will additionally be checked at true M31
width against committed v1, comparing values and `flags_v` at each
implementation's own `done`.

The gate passed on 2026-07-26:

```text
sby -f hardware/tests/spu13/spu13_fp4_structured_arithmetic_formal.sby
  width_3_6 PASS
  width_4_8_scale PASS

sby -f hardware/tests/spu13/spu13_fp4_inverter_structured_formal.sby
  engine_0 (smtbmc bitwuzla) returned pass; depth 90
```

The production-width BMC is compositional at the multiplier transaction
boundary. Two-cycle symbolic responses obey the request relations proven on
the new parameterized arithmetic at both reduced widths; the full-width
extrema testbench separately compares those requests against the real v1
multiplier. The BMC itself instantiates the committed v1 and candidate v2
controllers at their real 32-bit ports, traverses one complete 31-bit Fermat
chain, and proves request operands, sequencing, singular handling, and values
at each implementation's own `done`. The identical inline Fermat result is an
explicit scale-request cutpoint; it is not represented as a new arithmetic
implementation.

## Predeclared physical and latency gates

These thresholds were fixed before any candidate-enabled backend synthesis or
place-and-route run. Each physical comparison uses matched source commits,
tool versions, constraints, and a fresh artifact name. Seeds 1, 7, 13, and 2
remain unavailable for ad-hoc work.

| Backend | DSP gate | LUT gate | FF gate | Fmax gate | Unit latency | Singular latency |
|---|---:|---:|---:|---:|---:|---:|
| Shared parallel | candidate <= matched v1 | <= 1.08x v1 | <= 1.05x v1 | >= 0.90x v1 | <= 77 clocks | <= 7 clocks |
| Sequential | candidate <= matched v1 | <= 1.10x v1 | <= 1.10x v1 | >= 0.90x v1 | <= 160 clocks | <= 35 clocks |

Latency is rising-edge index difference from accepted `start` to `done`.
There must be no operand-dependent variance within either outcome class.
The shared-parallel gate measures released occupancy as well as end-to-end
latency; unchanged DSP count is expected because Padé retains the general
multiplier.

## Preserved findings outside this change

- Historical sequential integration is invalid because its shared-operand mux
  does not hold inverter operands over the sequential multiplier schedule.
  Candidate plumbing must fix that structurally; the v1 artifact is not
  rewritten.
- `spu13_batch_inverter.v` leaves its multiplier `rns_error` unconnected. This
  pre-existing gap remains recorded and is not silently folded into the
  structured-inverter change.

## Measured candidate results (2026-07-26)

The full-width 25-vector bench measures accepted-start-edge to done-edge
latency as follows.  Every vector in an outcome class produced the same value:

| Backend | Unit | Stage-B singular | Gate |
|---|---:|---:|---|
| Shared parallel | 74 | 7 | PASS (<=77 / <=7) |
| Sequential | 114 | 23 | PASS (<=160 / <=35) |

The request-level bench also injects independent faults into the parallel
result register and into both the sequential result register and its stored
wide accumulator after the registered residue shadow advances.  All three
faults assert `rns_error`; fault-free full and narrow requests keep it low.

Matched Artix-7 seed runs use the dedicated `FP4EVIDENCE` top, which contains
the inverter, its selected multiplier, a live operand generator, and a live
result reduction.  This is the physical subject of the tranche.  The normal
`RPLU2PADE` top was also attempted first, but both the unchanged v1/classic-ABC
netlist and an ABC9 retry are rejected before placement by nextpnr 0.8.2 while
constructing the timing graph for the unrelated `spu_spi_slave` LUT network.
No `--ignore-loops` result is used.

The predeclared five-seed parallel matrix completed on 2026-07-28. Per-seed
resource results are:

| Seed | v1 LUT | v2 LUT | Ratio | v1 FF | v2 FF | Ratio | v1 DSP | v2 DSP | Ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 17 | 9,415 | 10,120 | 1.074881 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 41 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 53 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 67 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 79 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |

Timing and derived unit-completion time use the measured 83-cycle historical
v1 latency and 74-cycle v2 latency:

| Seed | v1 Fmax | v2 Fmax | Ratio | v1, 83 clocks | v2, 74 clocks | Time ratio | Per-seed gate |
|---:|---:|---:|---:|---:|---:|---:|---|
| 17 | 66.51 MHz | 76.63 MHz | 1.152158 | 1.247933 us | 0.965679 us | 0.773823 | PASS |
| 41 | 77.16 MHz | 69.60 MHz | 0.902022 | 1.075687 us | 1.063218 us | 0.988409 | PASS |
| 53 | 70.48 MHz | 68.44 MHz | 0.971056 | 1.177639 us | 1.081239 us | 0.918141 | PASS |
| 67 | 59.65 MHz | 77.58 MHz | 1.300587 | 1.391450 us | 0.953854 us | 0.685511 | PASS |
| 79 | 64.11 MHz | 78.24 MHz | 1.220402 | 1.294650 us | 0.945808 us | 0.730551 | PASS |

The seven-clock singular path is unchanged. Its per-seed v1/v2 wall-clock
times are respectively 0.105247/0.091348, 0.090721/0.100575,
0.099319/0.102279, 0.117351/0.090229, and 0.109187/0.089468 us for seeds
17/41/53/67/79.

The required aggregate statistics, with no dropped or added seeds, are:

| Metric | v1 mean | v1 median | v1 min | v1 max | v2 mean | v2 median | v2 min | v2 max | Ratio mean | Ratio median | Ratio min | Ratio max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LUT | 9,419.8 | 9,421 | 9,415 | 9,421 | 10,120.8 | 10,121 | 10,120 | 10,121 | 1.074418 | **1.074302** | 1.074302 | 1.074881 |
| FF | 1,274 | 1,274 | 1,274 | 1,274 | 1,177 | 1,177 | 1,177 | 1,177 | 0.923862 | 0.923862 | 0.923862 | 0.923862 |
| DSP48E1 | 72 | 72 | 72 | 72 | 72 | 72 | 72 | 72 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Fmax (MHz) | 67.582 | 66.510 | 59.650 | 77.160 | 74.098 | 76.630 | 68.440 | 78.240 | 1.109245 | **1.152158** | 0.902022 | 1.300587 |
| Unit time (us) | 1.237472 | 1.247933 | 1.075687 | 1.391450 | 1.001960 | 0.965679 | 0.945808 | 1.081239 | 0.819287 | 0.773823 | 0.685511 | 0.988409 |

The matrix passes both aggregation rules: median LUT ratio 1.074302 is at or
below 1.08, median Fmax ratio 1.152158 is at or above 0.90, and **5/5** seeds
individually pass both gates (the requirement was at least 4/5).

The closed sequential negative remains:

| Backend | Metric | v1 | v2 | Ratio | Gate |
|---|---|---:|---:|---:|---|
| Sequential, seed 29 | packed LUT | 5,128 | 8,048 | 1.5694 | **FAIL** (<=1.10) |
| | FF | 1,405 | 1,515 | 1.0783 | PASS (<=1.10) |
| | DSP48E1 | 12 | 12 | 1.0000 | PASS |
| | post-route Fmax | 61.52 MHz | 21.85 MHz | 0.3552 | **FAIL** (>=0.90) |

The parallel backend clears every predeclared physical gate across the full
matrix. The sequential backend delivers the intended cycle reduction but
fails both LUT and Fmax
gates by a wide margin.  Therefore the production selector remains default-off
and this tranche does not advance to the default-switch claim-ladder rung.

Exact matched commands were:

```text
FP4_EVIDENCE=1 FP4_STRUCTURED=0 FP4_BACKEND_SEQUENTIAL=0 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=17 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence synth
FP4_EVIDENCE=1 FP4_STRUCTURED=0 FP4_BACKEND_SEQUENTIAL=0 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=17 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence pnr
FP4_EVIDENCE=1 FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=0 FP4_BACKEND_SEQUENTIAL=0 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=17 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence synth
FP4_EVIDENCE=1 FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=0 FP4_BACKEND_SEQUENTIAL=0 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=17 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence pnr
FP4_EVIDENCE=1 FP4_STRUCTURED=0 FP4_BACKEND_SEQUENTIAL=1 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=29 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence synth
FP4_EVIDENCE=1 FP4_STRUCTURED=0 FP4_BACKEND_SEQUENTIAL=1 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=29 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence pnr
FP4_EVIDENCE=1 FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=1 FP4_BACKEND_SEQUENTIAL=1 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=29 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence synth
FP4_EVIDENCE=1 FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=1 FP4_BACKEND_SEQUENTIAL=1 A7_SYNTH_ABC9=0 ZPHI_KARATSUBA=0 A7_FREQ=50 A7_SEED=29 bash hardware/boards/artix7/build_a7.sh 100t fp4evidence pnr
```

The final sequential candidate P&R command exits nonzero because 21.85 MHz
misses the requested 50 MHz constraint.  That failure is the gate result, not
an infrastructure failure.

The matched runs used Yosys 0.63+87 and nextpnr-xilinx 0.8.2-73-gf681eb3a.
Their synthesis JSON SHA-256 values are:

```text
parallel v1, seed 17: eeb339587b013d402f953037599688d96f412818cf2a69ba96d1245e6f5c8b0b
parallel v2, seed 17: 7e066bd0af46bdf3210abfd92d9aa09403455e8d5e117c1be25532ff65d443e3
parallel v1, seed 41: feb7b8cdc743ba4e180ff480256a82be1adb360763c60b4f096b70aeab945372
parallel v2, seed 41: d8be0759ac4a5a446f5f4d5253634338a91551a822a74dbb4f32d1c4e4a6adce
parallel v1, seed 53: feb7b8cdc743ba4e180ff480256a82be1adb360763c60b4f096b70aeab945372
parallel v2, seed 53: d8be0759ac4a5a446f5f4d5253634338a91551a822a74dbb4f32d1c4e4a6adce
parallel v1, seed 67: feb7b8cdc743ba4e180ff480256a82be1adb360763c60b4f096b70aeab945372
parallel v2, seed 67: d8be0759ac4a5a446f5f4d5253634338a91551a822a74dbb4f32d1c4e4a6adce
parallel v1, seed 79: feb7b8cdc743ba4e180ff480256a82be1adb360763c60b4f096b70aeab945372
parallel v2, seed 79: d8be0759ac4a5a446f5f4d5253634338a91551a822a74dbb4f32d1c4e4a6adce
sequential v1, seed 29: a6b03be3cbf39cdcd754021515fad6863be755de61c5d7ce24d3d4e335c70b5c
sequential v2, seed 29: c5592f7e2f3be21ec614c0c782ad6d0d3fb0aba1ec05f6dd89f276c26cac3f51
```

The repeated hashes across new seeds are expected: the seed is consumed by
nextpnr, while each matched v1 or v2 synthesis command and source are
identical. For each new seed `S` in `41 53 67 79`, the exact four commands
were the seed-17 commands above with `A7_SEED=S`; v1 used
`FP4_STRUCTURED=0`, and v2 used `FP4_STRUCTURED=1` with
`FP4_STRUCTURED_SEQUENTIAL=0`, with all other environment settings unchanged.

## Consumer build classification

These are the complete candidate-enabled command lines for all eight source
list references.  “Dead elaboration” means the source parses but the selected
top removes it from the active hierarchy; it is not counted as exercising v2.

| Source-list reference | Candidate-enabled command | Classification and evidence |
|---|---|---|
| `artix7/synth_a7.ys` | `FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=0 FP4_BACKEND_SEQUENTIAL=0 ZPHI_KARATSUBA=0 A7_FREQ=2 A7_SEED=31 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade synth` | **PASS**; exercises v2; synthesized hierarchy contains `spu13_fp4_inverter_structured` and `spu13_m31_multiplier_structured` |
| `artix7/synth_a7_seq.ys` | `FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=1 FP4_BACKEND_SEQUENTIAL=1 ZPHI_KARATSUBA=0 A7_FREQ=2 A7_SEED=31 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade synth` | **PASS**; exercises v2; synthesized hierarchy contains the structured controller and sequential multiplier |
| `tang_primer_25k/synth_gowin_25k_spu13_rplu_v2.ys` | `yosys -D SPU13_STRUCTURED_INVERTER -s hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_rplu_v2.ys` | **NON-TERMINATING**; exercises v2 and reaches final ABC9 `&verify`, but produced no verdict in 2:01:51 and was stopped (exit 130) |
| `tang_primer_25k/synth_gowin_25k_spu13_southbridge.ys` | `yosys -D SPU13_STRUCTURED_INVERTER -s hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_southbridge.ys` | **PASS**; dead elaboration; the southbridge top does not enable the RPLU2 pipeline |
| `tang_primer_25k/synth_gowin_25k_spu13_irotc_spi.ys` | `yosys -D SPU13_STRUCTURED_INVERTER -s hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_irotc_spi.ys` | **PASS**; dead elaboration; `CORE_ENABLE_MATH=0`, IROTC-only hierarchy |
| `tang_primer_25k/synth_gowin_25k_series_stream_probe.ys` | `yosys -D SPU13_STRUCTURED_INVERTER -s hardware/boards/tang_primer_25k/synth_gowin_25k_series_stream_probe.ys` | **PASS**; exercises v2; ABC9 equivalence and final `check` pass; the board top directly instantiates the selected inverter |
| `colorlight_i9/build_colorlight_i9_rplu2.sh` | `FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=0 bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh synth` | **PASS**; exercises v2; RPLU2 is active in the Colorlight top |
| `ecp5_85k/build_ecp5_85k.sh` | `FP4_STRUCTURED=1 FP4_STRUCTURED_SEQUENTIAL=0 bash hardware/boards/ecp5_85k/build_ecp5_85k.sh` | **PASS**; parse-only; the legacy `spu13_top` hierarchy has no candidate selector propagation |

The active Tang RPLU synthesis is not counted as a pass.  Its source-list
repair clears `hierarchy -check`, both structured modules are live, and ABC9
writes its final 7,812,430-byte `output.aig`; the subsequent equivalence
solver produced no verdict between 21:17:37 and 23:19:28 NZST.  It was then
stopped cleanly rather than weakening the command or claiming deep
elaboration as build closure.  The claim ladder therefore remains below
"integration-verified candidate."

## Regression and reproduction

The final committed RTL was exercised from a clean working tree with:

```text
python3 run_all_tests.py
```

It passed **177/177**, exit 0: 134 Verilog tests, 12 C++ tests, and 31
Python/product checks.  This supersedes the contract's 173-test baseline
because the tranche adds four discovered tests.  A first run from the fresh
local clone `/tmp/spu-fp4-fresh.6QaG1T/SPU`, made after the implementation and
evidence commits, independently passed the same **177/177**, exit 0.
