# Engineering Contract: T1k U/V Grid Material Operator

**Date:** 2026-09-26  
**Contract ID:** `GPU-T1K-UV-GRID-2026-09-26`  
**Status:** `T1k CLOSED: Q0/Q1 PASS; POST-REFACTOR B1 PASS (27.01 MHz); H1 PASS (OPERATOR-OBSERVED A/B/C/A RETURN)`
**Owner:** John Curley

## 1. Objective

Add one deterministic two-axis grid material operator that combines U and V
coordinate tests with Boolean OR. Preserve the T1j pipeline and prove the new
color function against an independent oracle before requesting hardware work.

The grid output is white on periodic U or V border bands and black elsewhere.
It uses only winner-selected U/V and the existing U/V-valid signal. It adds no
texture storage, framebuffer, sampled image, multiplication, or division.

## 2. Q0 frozen semantics

Use the existing registered 56-bit, signed `selected_u_q` and `selected_v_q`
from the T1j material-input stage. For each valid fragment, define:

```text
u_phase = selected_u_q[11:0]
v_phase = selected_v_q[11:0]
u_border = u_phase < 12'd1024
v_border = v_phase < 12'd1024
grid = u_border OR v_border

if !selected_uv_valid_q:
    RGB = 12'h000
else if grid:
    RGB = 12'hFFF
else:
    RGB = 12'h000
```

The low 12 bits define a 4096-coordinate period on each axis; the first
1024 coordinates of each period form its border band. These constants are
frozen for T1k and are not runtime or build-time tuning values. The T1j
checker rule remains unchanged in its own profile.

An independent-oracle candidate scan over the frozen A/B/C scenes' 80x100
geometry region reports:

| Scene | Covered | White grid | Black interior |
|---|---:|---:|---:|
| A | 2441 | 1046 | 1395 |
| B | 924 | 360 | 564 |
| C | 2441 | 922 | 1519 |

Both colors occur in all scenes. Independent recomputation corrects the
candidate color-pattern difference counts to 1346 pixels for A/B and 1464 for
A/C over this 80x100 region. These counts are scene-distinction summaries,
not substitutes for per-pixel oracle checks.

## 3. Q0 source review

The existing T1j path already registers depth-winner-selected U, V, validity,
hsync, vsync, and active together. It evaluates the checker from that
registered tuple and then sends final RGB plus aligned video controls through
`GPU_POST_WINNER_REG`. T1k shall preserve those stage boundaries and
one-pixel-per-clock throughput:

```text
coverage/depth winner/U-V interpolation
  -> registered selected U/V + valid + sync/active
  -> T1k grid comparisons and OR
  -> final RGB mux
  -> GPU_POST_WINNER_REG
  -> VGA/HDMI
```

No scene, loader, UART, pacing, fixture, coverage, depth, winner, interpolation,
or activation change is needed. The apparent gaps in the T1j black/white photo
were resolved as a visualization artifact: black covered checker cells blended
into the black background. The two-visible-color diagnostic preserved the full
triangle silhouette. The earlier detached red artifact remains a separate
unresolved observation; T1k makes no claim to fix it.

**Q0 result: PASS for the frozen operator semantics and source boundary.** The
owner's 2026-09-26 direction authorizes Q1 as simulation-first within the
boundary below. Synthesis, bitstream build, and hardware programming are not
included.

## 4. Proposed Q1 implementation boundary

Add a default-off `T1K_GRID_SHADE=0|1` compile-time selector.
When enabled, require the prepared four-primitive T1i U/V profile, require
`GPU_POST_WINNER_REG=1`, and reject simultaneous T1j checker selection and all
diagnostic profiles. Reuse the T1j registered U/V/valid/control stage; place
the comparisons and OR after that stage and keep `GPU_POST_WINNER_REG` after
final RGB. With the selector off, preserve T1i and T1j behavior exactly.

Add a T1k independent oracle/test that computes coverage, depth winner, and
winner-selected U/V independently before evaluating the frozen grid rule. It
must check invalid black, both colors, all four winning lanes, A/B/C changes,
exact return-A equality, reset state, one-cycle sync/active alignment, and the
existing output-register alignment. The production qualification target is
all 640x480 pixels for A/B/C/A (1,228,800 pixel comparisons).

## 5. Proposed verification commands

```bash
python3 software/tests/test_gpu_t1k_grid.py
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1j_checker.py
python3 software/tests/test_gpu_t1h_attribute.py
python3 software/tests/test_gpu_t1g_pacing.py
python3 software/tests/test_gpu_t1i_depth_output.py
```

After the reduced oracle passes, run the production A/B/C/A oracle through the
detached runner with a frozen 600-second limit. Do not change the checker
constants to improve routed timing. If T1k misses the 25 MHz Artix target,
record the timing result and revise the pipeline contract before another
hardware build. No T1k FPGA build or flash budget is requested by this Q0
contract.

## 6. Separate qualification debt

* T1j H1 passed as an operator-observed bounded checker demonstration; exact
  physical pixel correctness remains simulation/oracle evidence.
* T1j apparent clipping is resolved as a visualization artifact by the
  two-visible-color diagnostic: black covered fragments blended into the
  black background in the prior image. The separate small red artifact remains
  open.
* The full repository gate previously failed with 236 passes and 2 reported
  failures due T1j-only hierarchical taps in `test_gpu_t1i_uv.py`. A
  compile-time testbench guard was added and the focused T1i test now passes
  32,000 pixels. The full gate has not been rerun; keep this debt separate
  from T1k simulation work and reconcile it before a public release/tag.
* The first detached production oracle run completed with exit 1 after 256 s
  because its host checker incorrectly expected the reduced-ROI change counts
  `[2671, 2486]` as fixed production counts. It reported actual differences
  `[1346, 1464]` and no pixel/oracle mismatch. The incorrect assertion was
  removed. A corrected detached run completed with exit 0 in 254 s and passed
  all 1,228,800 production A/B/C/A pixel comparisons:
  `build/gpu/t1k_q1_20260926/production_oracle_retry/`. T1k Q1 is closed.

## 7. T1k qualification result

`python3 software/tests/test_gpu_t1k_grid.py` passed the reduced 80x100
A/B/C/A oracle (32,000 pixels). The corrected production-timing run passed
1,228,800 pixels. The T1i, T1j, T1h, T1g, and T1i depth-output regressions also
passed after the shared testbench changes. The T1j visibility diagnostic's
production oracle passed independently. T1k initially had simulation/oracle
qualification only; the subsequent authorized post-refactor B1 and H1 results
are recorded in Sections 8–9.

## 8. B1 build results

The Artix-7 build profile is wired through the board top and build script as
`T1K_GRID_SHADE=1`, with `GPU_POST_WINNER_REG=1`, the prepared four-primitive
T1i U/V scene, and artifact tag `T1K_UV_GRID_B1_S1`. Other T1h/T1i diagnostics
and both T1j selectors are disabled. The default-off path remains unchanged
when T1k is not selected. `bash -n hardware/boards/artix7/build_a7.sh` and
`git diff --check` passed before the build.

The initial owner-authorized one-attempt budget (3600 seconds per attempt,
3600 seconds cumulative; threshold 25.00 MHz) produced 24.08 MHz and B1 FAIL.
That candidate was not programmed. The owner then separately authorized one
post-refactor attempt with the same timeout and threshold, conditional on a
passing full production oracle.

The post-refactor production oracle passed all 1,228,800 A/B/C/A pixels in 270
seconds: `build/gpu/t1k_post_refactor_20260926/production_oracle/run_01/`.
The single authorized post-refactor Artix build completed in 850 seconds with
exit code 0. Its final routed result is **27.01 MHz (PASS at 25.00 MHz)**; an
earlier placement/routing result in the same run was 23.75 MHz and is
superseded by the final route. The routed report is
`build/metrics/artix7_100t_GPUVGA_T1K_UV_GRID_B1_S1.md` and the detached evidence
is `build/gpu/t1k_post_refactor_b1_20260926/run_01/`.

The exact bitstream is
`build/spu_a7_100t_GPUVGA_T1K_UV_GRID_B1_S1.bit`, SHA-256
`925782d94f2cb914c271fd4861df1f22adbf175f3b4bb11b663f043c1168b7d2`. It was
SRAM-loaded through DirtyJTAG; the programmer reported 100% and
`isc_done=1`, `init=1`, `done=1`.

## 9. Timing isolation findings and source correction

The final T1k nextpnr critical path is **not** in the T1k grid comparisons or
the selected-U/V material mux. The reported `clk_pixel` path starts at
`u_gpu.u_t1i_u.u_attribute_dispatch4.active_unit[2]`, crosses the wide
per-lane operand selection into `spu_depth_math`, traverses the dot-product,
absolute-value and reciprocal normalization logic, and ends at
`u_math.u_recip.mant_full[0]`. It totals 41.5 ns (5.9 ns logic, 35.7 ns
routing). The active-unit net alone contributes 7.3 ns, indicating that
selection fanout/placement is a substantial part of this path.

The timing-passing T1j visibility route instead reported a 38.5 ns path from
edge coverage through depth comparison and the `raster_primitive_id` selection
into the U interpolation result register (6.7 ns logic, 31.9 ns routing). Its
Fmax was 25.94 MHz; T1k's final routed Fmax was 24.08 MHz. The two builds have
the same reported device resource profile except T1k adds 2 LUTs and 2 FFs
(39,336 LUTs / 15,354 FFs versus 39,334 / 15,352). This points to a small
placement/routing perturbation exposing a different pre-existing setup path;
it does not establish that the grid comparator is the cause of the frequency
loss.

**Behavior-preserving source correction implemented:** `spu_depth_dispatch4`
now stages the selected lane's complete `a/b/c/z` operand tuple at the same
dispatch edge that selects the output lane, then feeds the shared math engine
from that tuple register. The tuple selection keeps lane priority and explicitly
uses current input-bus values when that same lane asserts `depth_setup` on the
dispatch edge, preserving the previous same-cycle overwrite behavior. The math
start/complete sequence, output routing, and arithmetic are unchanged. This
moves active-unit selection off the long arithmetic path without changing
scene activation or the pixel pipeline.

Focused regressions passed after the refactor:

* T1k grid, T1i U/V, and T1h scalar setup/activation checks.
* T1j checker and checker-visibility oracles.
* T1g frame pacing characterization; preparation remains 95 cycles and all
  first-frame checks pass.
* T1i output diagnostics, depth-dispatch parity, and depth-math parity.

The T1k 80x100 A/B/C/A oracle passed 32,000 pixels. The T1i U/V oracle passed
32,000 pixels; T1h checked 40,000 pixels plus 715 focused edge samples. After
the refactor, the full production T1k oracle also passed 1,228,800 pixels and
the authorized B1 build passed timing at 27.01 MHz. The frozen A/B/C/A UART
sequence was sent over `/dev/ttyUSB0`; all four 175-byte writes drained and
scene-start gaps were 3011.36–3011.59 ms. Transcript:
`build/gpu/t1k_post_refactor_h1_20260926/uart_sequence.json`. H1 visual
observation: the operator reports that the grids changed and appeared as
“perfect diamond shaped chequers.” Photo `IMG_1768.jpeg` shows the bright
diamond/grid form against black (SHA-256
`a9881b5b3d419cd03d40df50a0e2dbdc7ab96dec39c2b8cf46e0e70adadf56f3`).
The operator confirms final A matched initial A. No detached artifact or
phantom vertex is apparent in the photo.
