# Engineering Contract: T1m Deterministic Fragment ALU

**Date:** 2026-09-27  
**Contract ID:** `GPU-T1M-FRAGMENT-ALU-2026-09-27`  
**Status:** `Q0 PASS; Q1 PASS; Q2 PASS; B1 PASS at 30.27 MHz; H1 PASS (operator-observed, visual-only)`  
**Owner:** John Curley

## 0. Commands

After Q0 approval, run the focused reduced-profile oracle with:

```bash
python3 software/tests/test_gpu_t1m_fragment_alu.py
```

After Q1 passes, run the production oracle through the detached runner with:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1m_fragment_alu_20260927/q2_production_oracle/run_01 \
  --timeout 600 --notify-desktop -- \
  python3 software/tests/test_gpu_t1m_fragment_alu.py --production
```

Do not synthesize, route, or program an FPGA under Q0–Q2. A fresh owner
authorization and frozen B1 budget are required after Q2 passes.

## 1. Objective and scope

Answer this question:

> Can the fragment stage evaluate a small deterministic Boolean material ALU
> over two U/V-derived predicate inputs while preserving one-pixel-per-clock
> throughput and the qualified raster/depth behavior?

The ALU is compile-time selected and has no runtime opcode, instruction
decoder, register file, loop, texture memory, framebuffer, or sampled texture.
The target is one selected operator per build, implemented after the already
registered winner-selected U/V tuple and before the existing final RGB/output
register.

## 2. Frozen inputs and pipeline

Reuse the existing T1l-qualified profile, fixtures, output registers, and
timing boundary:

```text
four-lane coverage/depth/U/V
  -> T1L_PIPELINE_PARTITION register
  -> depth winner and winner-selected U/V
  -> registered selected U/V + valid + sync/active
  -> T1m material ALU
  -> RGB mapping
  -> GPU_POST_WINNER_REG
  -> display
```

Frozen inputs:

* Scene fixtures: `fixtures/gpu_t1i_scene_{a,b,c}_wire_175b.hex`.
* Profile: prepared four-lane T1i U/V scenes, `T1L_PIPELINE_PARTITION=1`,
  and `GPU_POST_WINNER_REG=1`.
* Baseline image: `build/spu_a7_100t_GPUVGA_T1L_PIPELINE_PARTITION_B1_S1.bit`,
  SHA-256 `79c9de8fab4a9c40bbc3be845b0a4d2c124279b0704acd76d18aa85e52fe7040`.
* T1l physical closeout: broad return-A pattern repeatability PASS;
  physical U-stripe visibility/correspondence INCONCLUSIVE. This limitation
  remains separate from T1m's functional qualification.

## 3. Q0 semantics and profile review

Use the two frozen predicate inputs:

```text
pred_u = selected_u_q[12]
pred_v = selected_v_q[12]
```

Add a default-off `T1M_FRAGMENT_ALU=0|1` selector and a compile-time
`T1M_ALU_OP=0..5` selector. When the ALU is enabled, elaborate exactly one
operator branch:

| `T1M_ALU_OP` | Operation | Result |
|---:|---|---|
| 0 | `PASS_U` | `pred_u` |
| 1 | `PASS_V` | `pred_v` |
| 2 | `XOR` | `pred_u XOR pred_v` |
| 3 | `AND` | `pred_u AND pred_v` |
| 4 | `OR` | `pred_u OR pred_v` |
| 5 | `NOT_U` | `NOT pred_u` |

`NOT_U` defines the unary `NOT` entry from the proposed operation set as the
complement of the first input. Invalid fragments are gated after the
predicate operation and always render black.

For valid fragments, map result zero to blue (`RGB=12'h00F`) and result one
to yellow (`RGB=12'hFF0`). Map invalid fragments to black (`RGB=12'h000`).
This preserves a visible silhouette while exposing both ALU result classes.

Freeze these profile rules in Q0:

* `T1M_FRAGMENT_ALU=0` preserves T1l/T1i behavior exactly.
* `T1M_FRAGMENT_ALU=1` requires prepared four-lane T1i U/V scenes,
  `T1L_MATERIAL_OP=0`, `T1L_PIPELINE_PARTITION=1`, and
  `GPU_POST_WINNER_REG=1`.
* T1h scalar, T1i diagnostic, T1j, and T1k selectors must be disabled.
* `T1M_ALU_OP` outside 0–5 is rejected when the T1m ALU is enabled.
* The physical qualification profile uses `T1M_ALU_OP=2` (XOR), which
  composes both inputs and produces two visible result colors.

Source-review finding: the current T1l pipeline-partition guard permits
`T1L_PIPELINE_PARTITION=1` only with `T1L_MATERIAL_OP=3`. Q1 therefore needs a
guard-only extension permitting the T1m profile tuple above while retaining
the existing T1l checks unchanged. This changes compile-time legality only;
it must not alter the datapath or any existing legal profile. No RTL datapath
changes or fixture generation occur during Q0. Halt and amend this contract if
the RGB mapping cannot be placed before `GPU_POST_WINNER_REG` without changing
alignment.

## 4. Q1 reduced oracle and implementation

Authorized Q1 implementation is limited to:

* `hardware/rtl/gpu/spu_gpu_top.v` — default-off selector, profile guards,
  and six exclusive generate branches using only registered U/V and valid;
* `hardware/boards/artix7/spu_a7_gpu_vga_top.v` and
  `hardware/boards/artix7/build_a7.sh` — compile-time parameter propagation
  and legal-profile checks;
* `software/tests/test_gpu_t1i_uv.py` — shared testbench parameter and
  pixel/control-alignment support for the T1m profile;
* `software/tests/test_gpu_t1m_fragment_alu.py` — independent oracle and
  focused checks;
* this contract.

The independent oracle must derive coverage and depth winner first, select
the oracle winner's U/V values, evaluate the ALU result, apply valid gating,
and then apply the blue/yellow mapping. It must not use DUT-selected U/V or
DUT RGB as expected values.

Run A/B/C/A for each operation at the existing 80×100 reduced timing profile
(32,000 pixels per operation). Check:

* every covered output equals the independent winner/U/V/material oracle;
* invalid pixels are black even for `NOT_U`;
* both blue and yellow classes appear in valid coverage where predicted;
* all four primitive lanes win at least once;
* exact return-A pixel equality, reset, and scene activation behavior;
* hsync/vsync/active and `GPU_POST_WINNER_REG` alignment;
* selector-off behavior preserves T1l/T1i output exactly;
* illegal profile combinations are rejected.

Run the exact Q1 command in §0 and the focused legacy regressions:

```bash
python3 software/tests/test_gpu_t1l_material_ops.py
python3 software/tests/test_gpu_t1k_grid.py
python3 software/tests/test_gpu_t1j_checker.py
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1h_attribute.py
python3 software/tests/test_gpu_t1g_pacing.py
python3 software/tests/test_gpu_t1i_depth_output.py
bash -n hardware/boards/artix7/build_a7.sh
```

No fixture changes, synthesis, P&R, bitstream generation, or FPGA programming
are authorized in Q1.

**Q1 pass:** all operation/profile checks pass and selector-off behavior is
unchanged. Any oracle mismatch halts progression to Q2.

**Q1 result (2026-09-27): PASS.** The reduced independent A/B/C/A oracle
matched all 32,000 pixels for each of the six compile-time operations. Both
valid output colors, invalid-black gating, all four winner lanes, exact
return-A equality, reset, activation, and registered RGB/sync/active alignment
passed. Illegal T1m profiles were rejected. The seven focused T1l/T1k/T1j/T1i/
T1h/T1g/depth-output regressions and `bash -n` on the Artix build script also
passed. No synthesis, P&R, or hardware operation was run. Q2 remains pending;
its specified detached launch could not be used in the current environment
because the user systemd manager is unavailable. Q2 was therefore run in the
managed foreground fallback permitted when the detached-runner prerequisite
fails.

**Q2 result (2026-09-27): PASS.** The production XOR oracle matched all
1,228,800 pixels across the 640×480 A/B/C/A sequence, including invalid-black
gating, both valid colors, all four winner lanes, output/control alignment,
scene changes, and exact return-A equality. No synthesis, P&R, bitstream
generation, or programming was performed. A fresh bounded B1 budget still
requires the authorization recorded in §6.

## 5. Q2 production oracle

After Q1 passes, run the exact detached command in §0 for the physical profile
`T1M_ALU_OP=2` (XOR) over the complete 640×480 A/B/C/A stream (1,228,800
pixels). Check both output colors, invalid-black behavior, all four winning
lanes, sync/active alignment, scene changes for B/C, and exact return-A pixel
equality.

**Q2 pass:** all 1,228,800 pixels match the independent oracle and all
transition/alignment checks pass. Only then may the owner consider a fresh B1
budget. Q2 does not itself authorize hardware work.

## 6. B1/H1 — bounded build authorization

After Q2 passes, the owner authorized one bounded Artix-7 100T build attempt:
maximum one attempt, 3600-second wall-clock timeout, 3600-second cumulative
budget, and final routed `clk_pixel` Fmax >=25.00 MHz. The attempt is consumed
regardless of success, failure, timeout, or build-flow error. A successful
script exit or `COMPLETE` marker is insufficient without the final routed
timing report. Below threshold, retain reports/candidate and do not flash.
The exact profile is:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1m_fragment_alu_20260927/b1_s1_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_MATERIAL_OP=0 T1L_PIPELINE_PARTITION=1 \
      T1M_FRAGMENT_ALU=1 T1M_ALU_OP=2 GPU_POST_WINNER_REG=1 \
      A7_ARTIFACT_TAG=T1M_FRAGMENT_ALU_B1_S1 \
      bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

Launched via the detached runner as unit
`spu-b1_s1_01-20260927T074850Z-818964`; evidence directory:
`build/gpu/t1m_fragment_alu_20260927/b1_s1_01`. Interpret the run only after
exactly one `COMPLETE`, `FAILED`, or `TIMEOUT` marker is present.

**B1 result (2026-09-27): PASS.** The detached result is `COMPLETE`, exit 0,
within the 3600-second limit (2294 seconds). Final routed `clk_pixel` Fmax is
30.27 MHz against the 25.00 MHz threshold. The exact bitstream is
`build/spu_a7_100t_GPUVGA_T1M_FRAGMENT_ALU_B1_S1.bit`, SHA-256
`d3627d3f978a536e7e2f1980b45d9fabeb333d1662ca6f34b07a2691d554ef5f`.

The critical path report is in
`build/spu_a7_100t_GPUVGA_T1M_FRAGMENT_ALU_B1_S1.json.nextpnr.log`, lines
1384–1453. It starts at `partition_cov_q[0]` and ends at the register for
`partition_selected_v[12]`; the path passes through the four-lane depth
comparator/winner selection. Reported delay is 4.8 ns logic plus 28.2 ns
routing (33.0 ns total). The T1m ALU is downstream of this endpoint and is not
on the critical path. Against the T1l pipeline-partition baseline
(40.03 MHz), routed Fmax is 9.76 MHz lower. Resource deltas are +8 LUTs
(43,072 to 43,080) and +5 FFs (16,306 to 16,311); CARRY4 (1,208), SELMUX2_1
(2,841), and DSP48E1 (6) are unchanged. The exact image is eligible only for
the separately authorized bounded H1 visual check.

**H1 transport (2026-09-27):** The exact B1 image was loaded to Wukong SRAM
with `openFPGALoader -c dirtyJtag --freq 1000000`; detection identified
XC7A100 (`idcode 0x3631093`), and loading completed with `isc_done=1`,
`init=1`, and `done=1`. The frozen A/B/C/A sequence was transmitted on
`/dev/ttyUSB0` at 115200 8N1 using `tools/send_gpu_t1i_sequence.py`, with a
3-second scene dwell and frozen 20 ms minimum post-drain delay. All four
175-byte packets completed `tcdrain`; measured start-to-start gaps were
3011.501459 ms, 3011.453132 ms, and 3011.502617 ms. The transcript is
`build/gpu/t1m_fragment_alu_20260927/h1_abca.json`, SHA-256
`ef2be1833acaf6681c72ecd34c9ae828411c68efc4c5d60203b0d269458a0e0c`.
After the repeat below, the operator confirmed that the blue/yellow pattern
changed for B and C and returned to A. H1 is recorded as an operator-observed
visual result only; exact pixel correctness remains a simulation-oracle
claim.

A second A/B/C/A replay was sent at the owner's request with the same image,
fixtures, sender, pacing, and 3-second dwell. All four 175-byte writes drained;
start-to-start gaps were 3011.513228 ms, 3011.368875 ms, and 3011.495094 ms.
Its transcript is
`build/gpu/t1m_fragment_alu_20260927/h1_abca_repeat_01.json`, SHA-256
`0887a8f667c0eb70da595cf453a8353c6fe61ef59cb52819d54d051682e6c933`.
**H1 result: PASS (operator-observed, visual-only).** The operator confirmed
that the blue/yellow pattern changed for B and C and returned to the same broad
A pattern. No photo was supplied, so this does not establish per-pixel silicon
correspondence.

## 7. Invariants and stop conditions

No changes to raster equations, coverage, depth arithmetic/comparison,
winner priority, U/V setup/interpolation, scene activation, UART/loader,
fixtures, pacing, pipeline latency, or registered output alignment are in
scope. Preserve one-pixel-per-clock throughput.

Stop before implementation if any ALU operand cannot be sourced from the
registered winner-selected U/V tuple, if invalid gating can be bypassed, or
if profile guards alter existing T1l profiles. Stop before B1 if Q1 or Q2
fails. Do not add runtime opcodes, shader instructions, memories, loops,
register files, or texture operations.

Keep the prior repository-gate debt separate; T1m does not waive or rewrite
historical full-gate results.

## 8. Evidence dimensions

| Evidence dimension | Required T1m statement |
|---|---|
| Structural validation | Compile-time profile legality and one elaborated ALU operation |
| Functional simulation | Independent reduced and production oracle results, with exact pixel counts |
| Synthesis / place-and-route | Separate authorized B1 result with final routed Fmax and critical path |
| Interface validation | Existing scene transport and exact video alignment checks |
| Silicon observation | Only visible two-color material behavior and operator-observed transitions |
