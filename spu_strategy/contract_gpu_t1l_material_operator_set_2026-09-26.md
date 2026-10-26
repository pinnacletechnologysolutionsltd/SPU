# Engineering Contract: T1l Compile-Time Procedural Material Operator Set

**Date:** 2026-09-26  
**Contract ID:** `GPU-T1L-MATERIAL-OPS-2026-09-26`  
**Status:** `Q0/Q1/Q2 PASS; SEED-1 B1 FAIL; SEED-2 ORIGINAL UNAVAILABLE; RETRY TIMEOUT; CAMPAIGN EXHAUSTED`  
**Owner:** John Curley

## 1. Objective and scoped files

Add a compile-time material selector that demonstrates a small deterministic
procedural operator set using the already-qualified winner-selected T1i U/V
values. Keep the A/B/C fixtures, scene transport, geometry, depth winner,
interpolation, and registered output stages unchanged.

Expected target files:

* `hardware/rtl/gpu/spu_gpu_top.v`
* `hardware/boards/artix7/spu_a7_gpu_vga_top.v`
* `hardware/boards/artix7/build_a7.sh`
* `software/tests/test_gpu_t1l_material_ops.py`
* `spu_strategy/contract_gpu_t1l_material_operator_set_2026-09-26.md`
* `docs/hardware_evidence.md` after any physical observation

No new fixtures are needed. The operator selector applies to the frozen T1i
A/B/C scenes.

## 2. Frozen material semantics

Add a default-off compile-time selector `T1L_MATERIAL_OP=0..4`:

| Value | Operation | Predicate for a valid winner-selected fragment |
|---:|---|---|
| 0 | Disabled | Preserve existing T1i/T1j/T1k behavior exactly |
| 1 | Checker | `selected_u_q[12] XOR selected_v_q[12]` |
| 2 | Grid | `(selected_u_q[11:10] == 0) OR (selected_v_q[11:10] == 0)` |
| 3 | U stripes | `selected_u_q[12]` |
| 4 | V stripes | `selected_v_q[12]` |

For values 1–4, predicate true maps to white and false maps to black. Invalid
fragments map to black. `T1L_MATERIAL_OP=2` is bit-equivalent to the frozen
T1k grid rule because unsigned `selected_[uv]_q[11:0] < 1024` iff bits `[11:10]`
are zero. `T1L_MATERIAL_OP=1` reproduces the frozen T1j checker predicate.
Coordinate bit 12 for stripe phases is taken from the existing frozen T1j
checker bit selection; no runtime tuning or new scene values are introduced.
Implement values 1–4 as mutually exclusive `generate` branches so synthesis
elaborates exactly one material predicate and does not retain a runtime
operator-selection mux.

## 3. Profile and pipeline invariants

When `T1L_MATERIAL_OP` is 1–4, require:

* `PREPARED_SCENE=1`, `FOUR_PRIMITIVE_SCENE=1`, and `T1I_UV_SCENE=1`;
* `GPU_POST_WINNER_REG=1` and the `GPUVGA` board spin;
* T1h scalar, T1i diagnostic, T1j selector, and T1k selector modes disabled.

The material consumes only `selected_u_q`, `selected_v_q`, and
`selected_uv_valid_q`, after the existing shared depth winner. Keep this order:

```text
coverage / depth winner / U-V interpolation
  -> registered selected U/V + valid + sync/active
  -> selected compile-time material predicate
  -> final RGB selection
  -> GPU_POST_WINNER_REG
  -> display output
```

No texture memory, framebuffer, sampled image, multiplication, division,
per-pixel material ID, or runtime shading control is in scope. Preserve
one-pixel-per-clock throughput and all T1i/T1j/T1k profile behavior when the
new selector is zero.

## 4. Q0/Q1/Q2 gates

**Q0 source review:** Confirm the selector can be elaborated as one compile-time
operation without adding an unselected multi-operator runtime mux. Confirm all
four predicates use the registered winner-selected values and retain valid
gating. No RTL or fixture changes during Q0.

**Q0 result:** PASS. The existing `spu_gpu_top` already has one registered
winner-selected U/V/valid/sync/active stage followed by final RGB selection
and `GPU_POST_WINNER_REG`. Each T1l operation is a predicate over those
registered values, so exclusive generate branches preserve the current stage
boundaries and one-pixel-per-clock throughput. The established compile-time
guard pattern can enforce a clean exclusion boundary for the T1h/T1i
diagnostics and T1j/T1k selectors. No source or fixture was changed for this
review. The owner authorized Q1 implementation; synthesis remains unauthorized.

**Q1 implementation and reduced oracle:** Add parameter guards, selector
propagation, the four operators, and an independent oracle test. The oracle
must calculate coverage and depth winner independently, select the oracle
winner's U/V values, then compute the selected material predicate. Check all
four operators over A/B/C/A, invalid black, all four winning lanes, return-A
equality, reset, sync/active alignment, post-winner register alignment, and
selector-zero compatibility. Run at least the frozen 80x100 ROI (32,000
pixels) per operator.

**Q1 result: PASS.** `T1L_MATERIAL_OP=0..4` is propagated through
`spu_gpu_top`, the Artix GPU wrapper, and the legal Artix build profile. Values
1–4 elaborate as exclusive compile-time branches over the existing registered
winner-selected U/V/valid tuple. The independent oracle passed all four
operators over 80x100 A/B/C/A (128,000 comparisons total), including all four
winning lanes, invalid-black gating, both predicate classes, exact return-A,
reset, sync/active alignment, and post-winner-register alignment. Illegal
profiles and selector value 5 are rejected. Selector zero remains the default
path and the existing T1i regression passes unchanged.

Focused regressions PASS:

```text
python3 software/tests/test_gpu_t1l_material_ops.py       PASS (128,000 pixels)
python3 software/tests/test_gpu_t1i_uv.py                 PASS (32,000 pixels)
python3 software/tests/test_gpu_t1j_checker.py            PASS (32,000 pixels)
python3 software/tests/test_gpu_t1k_grid.py               PASS (32,000 pixels)
python3 software/tests/test_gpu_t1h_attribute.py           PASS (40,000 pixels; 715 edge samples)
python3 software/tests/test_gpu_t1g_pacing.py              PASS
python3 software/tests/test_gpu_t1i_depth_output.py        PASS
bash -n hardware/boards/artix7/build_a7.sh                 PASS
```

No synthesis, place-and-route, programming, or fixture changes were performed.

**Q2 production oracle:** For the proposed physical profile `T1L_MATERIAL_OP=3`
(U stripes), run the independent oracle over all 640x480 pixels for A/B/C/A
(1,228,800 comparisons). Check that B/C differ from A and final A is exactly
equal to initial A. Synthesis is not part of Q2.

**Q2 result: PASS.** The production U-stripe oracle completed with the sole
`COMPLETE` marker and exit status 0 in 261 seconds. It checked all 1,228,800
pixels over production 640x480 A/B/C/A timing, with B/C pattern changes and
exact return-A equality. Evidence is in
`build/gpu/t1l_q2_20260926/production_oracle/run_01`; the runner recorded source
revision `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`.

## 5. Verification commands

```bash
python3 software/tests/test_gpu_t1l_material_ops.py
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1j_checker.py
python3 software/tests/test_gpu_t1k_grid.py
python3 software/tests/test_gpu_t1h_attribute.py
python3 software/tests/test_gpu_t1g_pacing.py
python3 software/tests/test_gpu_t1i_depth_output.py
```

Run the full production oracle with the detached runner and a frozen 600-second
timeout:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1l_q2_20260926/production_oracle/run_01 \
  --timeout 600 --notify-desktop -- \
  python3 software/tests/test_gpu_t1l_material_ops.py --production
```

Keep the known full repository-gate debt recorded separately; do not silently
waive or reinterpret it.

## 6. B1/H1 boundary

The owner authorized one Artix B1 attempt with a 3600-second per-attempt
timeout and 3600-second cumulative campaign budget. Qualification requires
final routed `clk_pixel` Fmax >=25.00 MHz; script exit status or a detached
`COMPLETE` marker alone is insufficient. The attempt is consumed on success,
failure, timeout, or build-flow error. Below 25.00 MHz, classify B1 FAIL, retain
the candidate/reports, do not flash, and stop without correction or rebuild.
If B1 passes timing, only the exact resulting image is eligible for the bounded
visual A/B/C/A H1 check. Limit H1 to operator-observed stripe visibility and
return-A broad-pattern match; exact per-pixel correctness remains an oracle
claim.

**B1 result: FAIL.** The detached build completed with exit 0 in 963 seconds,
but the authoritative final routed report gives `clk_pixel` Fmax = 24.30 MHz,
below the 25.00 MHz threshold. The one authorized attempt is consumed. The
candidate bitstream and reports are retained at
`build/spu_a7_100t_GPUVGA_T1L_MATERIAL_OP_B1_S1.bit` and
`build/metrics/artix7_100t_GPUVGA_T1L_MATERIAL_OP_B1_S1.{md,json}`; detached
logs are at `build/gpu/t1l_b1_20260926/run_01`. The bitstream was not flashed.
H1 was not run. No timing correction or rebuild is authorized by the exhausted
budget. The owner subsequently authorized read-only timing forensics and then
froze the single seed-2 B1 retry recorded below.

**Read-only timing forensics:** The failed T1l critical path starts at the
video timing counter, traverses `frame_start`/`activate_scene`, depth setup,
the four-way depth comparison and winner selection, then ends at
`fragment_u[12]` entering the registered U/V stage. The routed path is reported
as 6.5 ns logic and 34.6 ns routing. The successful T1k reference route at
27.01 MHz likewise ended at a pre-registered fragment coordinate (`fragment_v[11]`)
and reported 7.1 ns logic and 30.0 ns routing. The T1l material predicate is
downstream of the U/V register and is not on this reported critical path. This
points to placement/routing variation in the existing upstream path rather
than identifying the U-stripe predicate as the logic bottleneck; it does not
establish a source-level correction. No RTL changes or further builds were
made during this audit.

**Seed-2 B1 budget:** One attempt, `A7_SEED=2`, 3600-second per-attempt
timeout, 3600-second cumulative limit, and final routed `clk_pixel` Fmax >=25.00
MHz. The attempt is consumed regardless of outcome. Below threshold, retain
the reports/candidate, do not flash, and stop without RTL changes or another
build. At or above threshold, only the exact seed-2 bitstream is eligible for
the scoped H1 A/B/C/A U-stripe visual check. The build uses artifact tag
`T1L_MATERIAL_OP_B1_S2` to preserve the seed-1 candidate and reports.

**Seed-2 result: UNAVAILABLE.** At the later review, the detached evidence
directory `build/gpu/t1l_b1_seed2_20260926/run_01` contained `LAUNCHED` but no
terminal marker (`COMPLETE`, `FAILED`, or `TIMEOUT`). Per the detached-runner
contract this result cannot be inferred from logs or elapsed time. The attempt
slot is consumed, no routed timing result is qualified, and H1 was not run.

**Seed-2 retry authorization:** The owner authorized one fresh seed-2 Artix
attempt with a 3600-second per-attempt timeout and 3600-second cumulative
limit. This is a new attempt slot. The build uses unique artifact tag
`T1L_MATERIAL_OP_B1_S2R1` to preserve artifacts from the markerless attempt.
The same final routed `clk_pixel` threshold of >=25.00 MHz applies. Failure or
timeout consumes the slot; below threshold, do not flash and stop. At or above
threshold, only this retry's exact bitstream is eligible for the bounded H1
check. No RTL or material semantic changes are authorized.

**Seed-2 retry result: TIMEOUT; campaign exhausted.** The detached runner
recorded its sole terminal marker `TIMEOUT`, exit 124, at the frozen 3600-second
limit in `build/gpu/t1l_b1_seed2_retry_20260927/run_01`. The run had completed
placement and reported an intermediate `clk_pixel` estimate of 20.61 MHz, below
25 MHz, but nextpnr was still in router2 iteration 42 when the timeout stopped
the job. This is not the final routed timing report and does not qualify B1.
No bitstream was emitted; only the retained nextpnr JSON and log are present.
The exact candidate was not flashed. The authorized retry slot is consumed;
no further timing correction, timeout extension, or build is authorized by
this campaign.

## 7. Stop conditions and exclusions

* If profile guards allow an illegal combination, HALT before implementation.
* If any reduced or production oracle fails, do not synthesize.
* If a future B1 route misses 25.00 MHz, classify B1 FAIL, do not flash, and
  stop within its frozen campaign budget.
* No changes to rasterization, depth, winner priority, U/V interpolation,
  scene activation, loader/UART behavior, fixtures, pacing, or the
  `GPU_POST_WINNER_REG` behavior are authorized.

## 8. Evidence claims

| Evidence dimension | T1l status |
|---|---|
| Structural validation | Q0 source review PASS; Q1 profile/elaboration guards PASS |
| Functional simulation | Q1 reduced oracle PASS; Q2 production U-stripe oracle PASS (1,228,800 pixels) |
| Synthesis / place-and-route | B1 FAIL; routed `clk_pixel` Fmax 24.30 MHz (<25.00 MHz) |
| Interface validation | Reuse existing T1i interface evidence; T1l-specific H1 not run |
| Silicon observation | NOT RUN |

## 9. Post-budget source-level pipeline review

**Status: REVIEW COMPLETE; RTL CHANGE AND BUILD NOT AUTHORIZED.** The
characterization material predicate is downstream of the registered selected
U/V tuple and is not on the failed route. The source path currently computes
four lane depth values, reduces them through the serial priority structure in
`spu_depth_compare4`, then uses the winner ID to select the corresponding
56-bit U/V values. The failed routed path ends at `fragment_u[12]` entering the
existing selected-U/V register, consistent with the report's activation/depth/
winner/U-V mux path.

A clean new register boundary before winner reduction must preserve a
same-pixel tuple for all four lanes: coverage, depth, U, V, and RGB, plus
hsync/vsync/active alignment. Carrying all fields is approximately 727 data and
control bits per pixel (`4 × (1 coverage + 3 × 56-bit attributes + 12-bit
RGB) + 3 video controls`), before any implementation-specific validity or
generation bits. Registering winner ID alone is not sufficient: the attribute
steppers advance at the pixel edge, so a delayed ID can select the next
pixel's U/V unless that pixel's lane values are also held.

The next useful step is a revised simulation-only pipeline contract for this
tuple boundary, including reset, first post-activation pixel, active/sync
alignment, one-pixel-per-clock throughput, and frozen A/B/C/A output-oracle
checks. Do not synthesize or route under the exhausted seed campaign. A future
Artix attempt requires a fresh owner-authorized budget after the simulation
gate passes.
