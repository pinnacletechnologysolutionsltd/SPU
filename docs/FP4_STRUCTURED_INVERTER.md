# Structured A31 inverter candidate

Status: split formal gate passed; seven of eight consumer builds pass;
production default **off**.

> **Default history — read this before quoting anything below.** The selector
> was switched **on** on 2026-08-01 (`5399b4c`) on the strength of the
> twenty-seed matrix in this document, and switched back **off** on 2026-08-03
> (`b48b6f6`'s follow-up) because **v2 is wrong on silicon**. This document was
> never updated for the first change, so its "default unchanged" line was
> stale for two days and is now correct again only by coincidence.
>
> The silicon fault: `RPLU2PADE`'s `seven_over_three` case returns
> `0x0CA45881` against an oracle of `0x55555557` on a v2 build, and the correct
> value on a v1 build from identical source — 41 consecutive
> `RPLU2PADE_J11: PASS`. See `hardware_evidence.md` §3.2m.
>
> **None of the measurements in this document are withdrawn.** They remain
> accurate about area, Fmax and cycle count. What they do not cover is
> functional correctness after synthesis, which is the axis v2 fails on: v1 and
> v2 agree in *simulation* on every vector, including the small-scalar family
> added in `66217ed` and all five Padé cases at both parameter values. So this
> is behaviourally-correct RTL that miscompiles, and the twenty-seed matrix was
> never designed to catch that.
>
> **Restoring the default requires explaining the synthesis divergence**, not
> re-running these benchmarks. They already pass.

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
constructing the timing graph for logic inside `u_spi`.
No `--ignore-loops` result is used.

**Correction (2026-07-28) — that rejection is not a `spu_spi_slave` defect.**
An earlier revision of this section attributed it to "the unrelated
`spu_spi_slave` LUT network." Investigation established otherwise:
`spu_spi_slave.v` is entirely synchronous (three `always @(posedge clk ...)`
blocks, four `assign`s reading only registered signals, every output port an
`output reg`), so it has zero combinational input-to-output paths; and a DFS
cycle detector over its synthesized netlist found 3,543 combinational cells
with **no cycle**. The failure is nextpnr 0.8.2's, in the
*"incomplete specification of timing ports"* branch of its generic error
string. Two causes were separated:

- The **one-node** rejection at `746d376` was a genuine RTL defect — an
  undriven `core_boot_ready` reaching `u_spi` on all five `_CORE=0` spins,
  fixed in `05d1709`. That source point then routes at 43.20 MHz.
- The **230-node** rejection on the preserved July netlist is a nextpnr
  0.8.2 limitation. Upstream nextpnr 0.10's Himbächel XC7 backend builds the
  timing graph on the identical netlist with **zero** unschedulable nodes and
  analyses both clock domains separately (`clk_fast` 23.74 MHz,
  `clk_100mhz` 119.76 MHz) — something 0.8.2 cannot do, having one global
  `--freq` and an XDC parser that honours no timing commands at all.

Use of the `FP4EVIDENCE` harness for physical measurement is therefore a
justified consequence of a toolchain limitation, not a shortcut — but it does
mean these numbers characterise the inverter in isolation rather than inside
the production design.

The predeclared five-seed parallel matrix completed on 2026-07-28. Per-seed
resource results are:

| Seed | v1 LUT | v2 LUT | Ratio | v1 FF | v2 FF | Ratio | v1 DSP | v2 DSP | Ratio |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 17 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 41 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 53 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 67 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |
| 79 | 9,421 | 10,121 | 1.074302 | 1,274 | 1,177 | 0.923862 | 72 | 72 | 1.000000 |

Timing and derived unit-completion time use the measured 83-cycle historical
v1 latency and 74-cycle v2 latency:

| Seed | v1 Fmax | v2 Fmax | Ratio | v1, 83 clocks | v2, 74 clocks | Time ratio | Per-seed gate |
|---:|---:|---:|---:|---:|---:|---:|---|
| 17 | 75.02 MHz | 70.51 MHz | 0.939883 | 1.106372 us | 1.049497 us | 0.948593 | PASS |
| 41 | 77.16 MHz | 69.60 MHz | 0.902022 | 1.075687 us | 1.063218 us | 0.988409 | PASS |
| 53 | 70.48 MHz | 68.44 MHz | 0.971056 | 1.177639 us | 1.081239 us | 0.918141 | PASS |
| 67 | 59.65 MHz | 77.58 MHz | 1.300587 | 1.391450 us | 0.953854 us | 0.685511 | PASS |
| 79 | 64.11 MHz | 78.24 MHz | 1.220402 | 1.294650 us | 0.945808 us | 0.730551 | PASS |

The seven-clock singular path is unchanged. Its per-seed v1/v2 wall-clock
times are respectively 0.093308/0.099277, 0.090721/0.100575,
0.099319/0.102279, 0.117351/0.090229, and 0.109187/0.089468 us for seeds
17/41/53/67/79.

The required aggregate statistics, with no dropped or added seeds, are:

| Metric | v1 mean | v1 median | v1 min | v1 max | v2 mean | v2 median | v2 min | v2 max | Ratio mean | Ratio median | Ratio min | Ratio max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LUT | 9,421 | 9,421 | 9,421 | 9,421 | 10,121 | 10,121 | 10,121 | 10,121 | 1.074302 | **1.074302** | 1.074302 | 1.074302 |
| FF | 1,274 | 1,274 | 1,274 | 1,274 | 1,177 | 1,177 | 1,177 | 1,177 | 0.923862 | 0.923862 | 0.923862 | 0.923862 |
| DSP48E1 | 72 | 72 | 72 | 72 | 72 | 72 | 72 | 72 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| Fmax (MHz) | 69.284 | 70.480 | 59.650 | 77.160 | 72.874 | 70.510 | 68.440 | 78.240 | 1.066790 | **0.971056** | 0.902022 | 1.300587 |
| Unit time (us) | 1.209160 | 1.177639 | 1.075687 | 1.391450 | 1.018723 | 1.049497 | 0.945808 | 1.081239 | 0.854241 | 0.918141 | 0.685511 | 0.988409 |

The matrix passes both aggregation rules: median LUT ratio 1.074302 is at or
below 1.08, median Fmax ratio 0.971056 is at or above 0.90, and **5/5** seeds
individually pass both gates (the requirement was at least 4/5).

> **This five-seed matrix is superseded as the headline.** It remains the record
> of the predeclared gate and its verdict, both of which still stand, but the
> sample was widened to twenty seeds on 2026-07-31 — see "Widened to twenty
> seeds" below. **Quote the twenty-seed median (0.964448), not 0.971056**, and do
> not describe the seed split as 2-fast/3-slow: that reading did not survive the
> larger sample.

All five seeds are now source-matched: every one synthesizes to a bit-identical
netlist, so LUT, FF and DSP have zero variance across the matrix and the only
per-seed variable is placement. Seed 17 was re-run on matched source on
2026-07-30; see calibration note 3.

### Calibration — what this result does and does not say

The pass is real and measured against rules fixed before the runs. Three
qualifications belong with it, so it is not quoted more strongly later than
the data supports:

1. **"5/5 PASS" does not mean faster. At the median it is slower.** The Fmax
   gate was `>= 0.90x` — *not much worse* — not `>= 1.00x`, and the median
   ratio is **0.971056**, i.e. **~3% slower**. **Three of five seeds are slower
   in Fmax**: seed 41 (77.16 -> 69.60 MHz, 0.902022), seed 17
   (75.02 -> 70.51 MHz, 0.939883) and seed 53 (70.48 -> 68.44 MHz, 0.971056).
   Two are substantially faster: seed 79 (1.220402) and seed 67 (1.300587).
   Seed 41 cleared the gate by 0.2%. Any phrasing of this result as a clock
   speed *win* is unsupported; the defensible claim is that v2 is not much
   worse in Fmax while retiring the work in fewer cycles.
2. **The wall-clock gain is a range, and it comes from the cycle count, not
   the clock.** Per-seed unit-time ratios are 0.948593, 0.988409, 0.918141,
   0.685511 and 0.730551 — i.e. between **1.2% and 31.4% faster** depending on
   placement. The mean, 0.854241 (~14.6%), is the fairest single figure; the
   median is 0.918141 (~8.2%). The gain survives the negative Fmax median only
   because v2 completes a unit in 74 clocks against v1's 83; on a same-clock
   comparison v2 would be behind at three of five seeds.
3. **Seed 17 was unmatched, and correcting it moved the headline across 1.0.**
   Resolved 2026-07-30. This note is kept rather than deleted, because the
   correction is the most important calibration in this document.

   The four 2026-07-28 seeds gave identical LUT counts (v1 9,421 / v2 10,121)
   — expected, since nextpnr's seed drives placement, not synthesis. Seed 17,
   run 2026-07-26, differed (9,415 / 10,120), indicating a different source or
   flow state, and it supplied the reported median. It was re-synthesized and
   re-placed on current source on 2026-07-30. Both arms now reproduce the
   other four seeds' synthesis hashes **bit-identically**
   (`feb7b8cd...945372` for v1, `d8be0759...4a6adce` for v2), which is the
   evidence that the source is matched — not the LUT count agreeing.

   The measured effect was large and adverse:

   | | unmatched 2026-07-26 | matched 2026-07-30 |
   |---|---:|---:|
   | seed 17 v1 Fmax | 66.51 MHz | 75.02 MHz |
   | seed 17 v2 Fmax | 76.63 MHz | 70.51 MHz |
   | seed 17 Fmax ratio | 1.152158 | **0.939883** |
   | **matrix median Fmax ratio** | **1.152158** | **0.971056** |

   Seed 17 went from the best-looking seed to the second worst, and the matrix
   median crossed from 1.15 (a 15% apparent gain) to 0.97 (a 3% loss). **Every
   previously published "median ~15% faster" statement about this result is
   false and must not be requoted.** The predeclared gate still passes — 0.971
   is above 0.90 and 5/5 seeds pass individually, in fact an improvement on
   4/5 — but it passes as *not much worse*, which is what the gate always
   measured. Seed 17 is no longer the median, so the headline no longer depends
   on any single seed.

   The 2026-07-26 artifacts were preserved before the re-run, because
   `build_a7.sh` names its output from the variant and seed alone and `build/`
   is gitignored with no second copy. All 13 files — `FI0B0`, `FI1B0`, `FI0B1`
   complete, plus a synthesis-only `FI1B1` — are under
   `build/evidence_archive/` with a `_UNMATCHED_2026-07-26` infix, verified
   byte-identical by SHA-256. The `seed 17` entries in the hash block below now
   carry the **matched** values, identical to the other four seeds; the
   superseded unmatched hashes
   (`eeb33958...6f5c8b0b` for v1, `7e066bd0...ff65d443e3` for v2) are recorded
   in `build/evidence_archive/README.md`, so the correction above stays
   checkable from either side.

### Widened to twenty seeds — the 2-fast/3-slow split was an n=5 artifact

Measured 2026-07-31 against a predeclared seed list
(`37, 43, 47, 59, 61, 71, 73, 83, 89, 97, 101, 103, 107, 109, 113`), all fifteen
routed in both arms on the **frozen** netlists — copied to new seed names and
`pnr` only, never re-synthesized, so the matched-source property that seed 17
broke could not recur. 30/30 runs returned exit 0 with zero overuse; no seed was
dropped. Independently audited: all 40 Fmax values re-extracted from the raw
`.nextpnr.log` files and every derived statistic recomputed, with no mismatch.

| Metric | 5 seeds | **20 seeds** |
|---|---:|---:|
| Fmax ratio mean | 1.066790 | **1.007939** |
| Fmax ratio median | 0.971056 | **0.964448** |
| Fmax ratio range | 0.902–1.301 | **0.683598–1.300587** |
| Unit-time ratio mean | 0.854241 | **0.902037** |
| Unit-time ratio median | 0.918141 | **0.924475** |

**There is no bimodality.** The only adjacent gap reaching the predeclared 0.10
threshold is 0.212139, between seed 59 (0.683598) and seed 89 (0.895737), and it
divides the sample 1/19 rather than into two groups each holding 25%. The
correct description is **dispersion, not two populations**, and the original
"seeds 67/79 gain while 17/41/53 lose" reading does not survive more data.

The median sits inside [0.95, 1.05], so the predeclared summary applies: **v2 is
Fmax-neutral at the median with high placement variance.** "Neutral" is the
gate's word for that interval — the median is a ~3.6% loss, not zero.

**Mechanism: routing delay, not logic.** Ratio versus v1-minus-v2 critical-path
routing advantage gives Pearson **r = 0.906** (independently recomputed:
0.9061); against route-iteration count it is only r = 0.144. Twenty of twenty v2
runs and eighteen of twenty v1 runs are critical inside the parallel M31
multiplier, on FF-to-FF paths through LUT/CARRY4 arithmetic. On those runs logic
delay stays in a narrow band (v1 3.9–4.9 ns, v2 3.6–4.9 ns) while routing spans
7.9–12.2 ns and 7.9–15.7 ns respectively. The two exceptions are v1 seeds 53 and
67, which move to a `mult_start`-to-clock-enable control path; they do not form a
population — 53 is near the median and 67 is the maximum.

### Two calibrations that must travel with the twenty-seed result

4. **The mean and the median tell opposite stories, and the mean is the
   misleading one.** Fmax mean 1.007939 reads as a small win; median 0.964448 is
   a small loss. The gap is right-skew from three large gains (1.300, 1.220,
   1.177) pulling the mean up. **Twelve of twenty seeds have a slower v2 clock.**
   Quote the median, or quote both — the mean alone overstates the result in
   exactly the way the retracted "~15% faster" claim did.

5. **The wall-clock case is strong but carries a real tail.** v2 is faster in
   unit time on **19 of 20** seeds — mean 9.8%, median 7.6% — and that gain comes
   from completing a unit in 74 clocks against 83, not from the clock. But **seed
   59 is 30.4% slower** (unit-time ratio 1.304226), caused by a 15.7 ns routing
   critical path in its v2 placement. One seed in twenty landing ~30% worse is a
   placement-lottery exposure, not measurement noise. It would present as an
   unexplained regression after an unrelated rebuild, so anyone adopting v2
   should expect it as a known failure mode rather than diagnose it fresh.

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
parallel v1, seed 17: feb7b8cdc743ba4e180ff480256a82be1adb360763c60b4f096b70aeab945372
parallel v2, seed 17: d8be0759ac4a5a446f5f4d5253634338a91551a822a74dbb4f32d1c4e4a6adce
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
