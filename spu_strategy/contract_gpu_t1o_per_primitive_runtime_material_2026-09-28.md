# Engineering Contract: T1o Per-Primitive Runtime Material Selection

**Date:** 2026-09-28  
**Contract ID:** `GPU-T1O-PER-PRIMITIVE-RUNTIME-MATERIAL-2026-09-28`  
**Status:** `Q0 PASS; Q1 PASS; RENEWED REPOSITORY GATE PASS; Q2 PASS; SYNTHESIS PASS; P&R PASS; B1 PACK PASS; H1 TRANSITION/RETURN PASS (VISUAL-ONLY)`  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `tools/verify_repo.sh` plus owner evidence review

## 0. Commands and authorization boundary

Run these Q0 read-only checks from the repository root:

```bash
sed -n '1,180p' hardware/rtl/gpu/spu_scene_loader.v
sed -n '220,420p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '900,1070p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '1,260p' hardware/rtl/gpu/spu_prepared_scene_control4.v
rg -n "T1N_RUNTIME_MATERIAL|SCENE_BITS|PAYLOAD_BYTES|winner_id|selected_u|selected_v" \
  hardware/rtl/gpu hardware/boards/artix7 software/tests
python3 -c 'from pathlib import Path; w=bytes.fromhex(Path("fixtures/gpu_t1i_scene_a_wire_175b.hex").read_text()); p=w[1:]+bytes((5,4,3,2)); s=int.from_bytes(p,"little"); print(len(w)-1,len(p),len(p)+1,len(p)*8,[((s>>(1392+8*i))&255) for i in range(4)])'
git diff --check
```

Stop after Q0. Do not modify RTL, board files, tests, fixtures, or generators.
Do not run simulation, synthesis, place-and-route, FPGA programming, or UART
transport under this authorization.

### Q1 owner authorization

On 2026-09-28, the owner authorized Q1 implementation within §8, including
the later scope amendment for `hardware/boards/artix7/synth_a7_gpu_vga.ys`.
Focused simulations and static checks in §9 are authorized. Fixture
regeneration, synthesis, place-and-route, bitstream generation, FPGA
programming, hardware packet transmission, and the repository-wide gate are
not authorized. The repository-wide gate requires a separately frozen timeout
and budget.

## 1. Objective

Answer this question:

> Can each prepared primitive carry its own runtime material opcode, committed
> atomically with scene state, with the depth winner selecting the matching
> opcode for each fragment?

T1o extends the T1n runtime material mechanism from one scene-wide opcode to
one opcode for each of four prepared primitives. Preserve the existing
coverage, depth, winner priority, U/V interpolation, six-operation Boolean
material ALU, RGB mapping, output register, frame activation, and UART framing.

Exclude per-pixel opcode storage, instruction streams, material programs,
register files, texture memory, sampled textures, runtime parameters, loops,
branches in the fragment path, and a shader ISA.

## 2. Q0 source-review result

Q0 passes with one required loader change reserved for Q1.

* T1i occupies 1,392 bits and 174 payload bytes.
* Four appended opcode bytes produce 1,424 scene bits, 178 payload bytes, and
  179 wire bytes including the existing `A5` start byte.
* `spu_scene_loader.payload_count` is eight bits and represents counts through
  177 without widening.
* The loader currently validates only the final payload byte. T1o requires
  validation of all four trailing bytes. Q1 must add a trailing-byte invalid
  accumulator; checking only byte 177 is prohibited.
* `partition_winner_id` already selects `partition_selected_u` and
  `partition_selected_v` immediately before the existing selected-U/V
  register boundary.
* The per-primitive opcode mux can use that same `partition_winner_id` and be
  captured on the same edge as `selected_u_q` and `selected_v_q`. Q0 does not
  authorize a new pipeline stage.
* `activate_scene` already qualifies the atomic raw-bank and prepared-state
  activation at `frame_start`. The opcode tuple must use the same event.
* Diagnostic payload count visibility is seven bits. T1o must remain mutually
  exclusive with T1d/T1i diagnostic profiles; no diagnostic-width change is
  in scope.

## 3. Frozen profile and packet format

Add this default-off selector only in a separately authorized Q1:

```text
T1O_PER_PRIMITIVE_MATERIAL=0|1, default 0
```

When enabled, require all of these values:

```text
PREPARED_SCENE=1
FOUR_PRIMITIVE_SCENE=1
T1I_UV_SCENE=1
T1L_PIPELINE_PARTITION=1
GPU_POST_WINNER_REG=1
T1N_RUNTIME_MATERIAL=0
T1M_FRAGMENT_ALU=0
T1L_MATERIAL_OP=0
```

Reject coexistence with T1h scalar modes, T1i diagnostics, T1j, T1k, T1l
static material selection, T1m, T1n, or any T1d diagnostic build.

Freeze this T1o layout:

| Scene bits | Payload byte | Wire byte | Meaning |
|---:|---:|---:|---|
| `0:1391` | `0:173` | `1:174` | Existing four T1i records, unchanged |
| `1392:1399` | `174` | `175` | `material_op[0]` |
| `1400:1407` | `175` | `176` | `material_op[1]` |
| `1408:1415` | `176` | `177` | `material_op[2]` |
| `1416:1423` | `177` | `178` | `material_op[3]` |

`wire[0]` remains `8'hA5`. Bytes remain little-endian by scene bit position.
Set `SCENE_BITS=1424` and `PAYLOAD_BYTES=178` only when T1o is enabled.
Preserve every legacy profile length and bit position when T1o is disabled.

## 4. Frozen opcode semantics

Use the T1n encodings unchanged:

| Byte | Operation | Result from winner-selected U/V |
|---:|---|---|
| `0x00` | `PASS_U` | `selected_u_q[12]` |
| `0x01` | `PASS_V` | `selected_v_q[12]` |
| `0x02` | `XOR` | `selected_u_q[12] XOR selected_v_q[12]` |
| `0x03` | `AND` | `selected_u_q[12] AND selected_v_q[12]` |
| `0x04` | `OR` | `selected_u_q[12] OR selected_v_q[12]` |
| `0x05` | `NOT_U` | `NOT selected_u_q[12]` |
| `0x06..0xFF` | invalid | Reject the complete candidate packet |

Map valid result zero to blue (`RGB=12'h00F`) and result one to yellow
(`RGB=12'hFF0`). Map invalid fragments to black. Do not change ALU truth
tables, predicate bits, or color mapping.

## 5. Winner selection and pipeline alignment

Treat the four opcodes as one tuple:

```text
candidate_material_ops[31:0] = candidate_scene[1392 +: 32]
active_material_ops[7:0]     = primitive 0 opcode
active_material_ops[15:8]    = primitive 1 opcode
active_material_ops[23:16]   = primitive 2 opcode
active_material_ops[31:24]   = primitive 3 opcode
```

On `activate_scene`, commit the complete candidate tuple with the raw scene,
prepared geometry, prepared U/V state, and generation. Before that event,
candidate opcode bytes must not affect any displayed fragment.

Select the opcode with the exact `partition_winner_id` used to select
`partition_selected_u` and `partition_selected_v`. Capture the selected opcode
on the same edge as `selected_u_q`, `selected_v_q`, selected valid, and video
controls. On the activation edge, select from `candidate_material_ops`; on all
other edges, select from `active_material_ops`.

Do not recompute a winner, delay a separate winner ID, or add a pipeline stage.
Invalid fragments remain black regardless of the selected opcode.

## 6. Invalid-packet rejection and recovery

In Q1, extend `spu_scene_loader` with an explicit trailing-byte validation
count. Preserve `VALIDATE_FINAL_BYTE` behavior for T1n or replace it only with
bit-equivalent behavior proven by the T1n regression.

For T1o, validate payload bytes 174, 175, 176, and 177. Accumulate an invalid
flag when any received opcode byte exceeds `8'h05`. At payload completion:

* never assert `commit_pending` if the accumulated flag or final byte is
  invalid;
* clear receive/count/invalid state;
* leave active bank, active opcode tuple, active generation, and displayed
  output unchanged;
* accept a new `A5` transaction on the next eligible cycle;
* allow the next complete valid packet to overwrite the inactive bank and
  activate normally.

Do not infer packet length at runtime. Do not add ACK, ready, FIFO, queueing,
or UART protocol changes.

## 7. Frozen Q1 oracle discriminator

Use the existing production A geometry/U/V fixture and append this primary
opcode tuple:

| Primitive | Opcode |
|---:|---|
| 0 | `NOT_U` (`0x05`) |
| 1 | `OR` (`0x04`) |
| 2 | `AND` (`0x03`) |
| 3 | `XOR` (`0x02`) |

Q0 oracle inspection of the 640x480 A fixture found:

* winner counts: lane 0 = 773, lane 1 = 742, lane 2 = 488, lane 3 = 438;
* 115 adjacent valid-pixel winner boundaries inside the frame;
* every assigned operation differs from each other assigned operation on at
  least 38 pixels won by that lane.

The Q1 oracle must recompute these properties independently before it
uses the fixture. Halt if any count changes or any comparison becomes vacuous.

The Q1 reduced suite must also exercise all six legal encodings, every
primitive index, candidate isolation, activation-edge alignment, no
partial-frame tuple change, exact return-state equality, invalid opcode in
each of the four byte positions, unchanged active output after rejection, and
valid recovery after every rejection.

Derive expected coverage, depth winner, winner ID, winner U/V, winner opcode,
Boolean result, RGB, and video-control alignment independently of DUT RGB and
DUT-selected values.

## 8. Authorized Q1 scope

Limit Q1 changes to:

* `hardware/rtl/gpu/spu_scene_loader.v` — four-byte tail validation and
  recovery;
* `hardware/rtl/gpu/spu_material_op_select4.v` — new single-purpose Lithic
  tuple commit, winner mux, and selected-op register;
* `hardware/rtl/gpu/spu_gpu_top.v` — default-off T1o profile and module hookup;
* `hardware/boards/artix7/spu_a7_gpu_vga_top.v` — selector propagation;
* `hardware/boards/artix7/synth_a7_gpu_vga.ys` — read the new selector module;
* `hardware/boards/artix7/build_a7.sh` — profile legality and Q1 tag;
* `software/tests/test_gpu_t1i_uv.py` — shared T1o timing/profile support;
* `software/tests/test_gpu_t1o_per_primitive_material.py` — independent oracle,
  invalid-tail checks, and illegal-profile checks;
* this contract — append measured results only.

Keep the new RTL module between 50 and 150 lines. Do not regenerate or edit
existing T1i fixtures. Construct T1o packets in the test from frozen T1i bytes
plus the four explicit opcode bytes.

## 9. Q1 verification commands

Do not run these commands under Q0:

```bash
python3 software/tests/test_gpu_t1o_per_primitive_material.py
python3 software/tests/test_gpu_t1n_runtime_material.py
python3 software/tests/test_gpu_t1m_fragment_alu.py
python3 software/tests/test_gpu_t1l_material_ops.py
python3 software/tests/test_gpu_t1k_grid.py
python3 software/tests/test_gpu_t1j_checker.py
python3 software/tests/test_gpu_t1i_uv.py
python3 software/tests/test_gpu_t1h_attribute.py
python3 software/tests/test_gpu_t1g_pacing.py
python3 software/tests/test_gpu_top_integration.py
bash -n hardware/boards/artix7/build_a7.sh
git diff --check
```

After the focused commands pass, run the mandatory repository gate through a
new detached evidence directory and a separately authorized frozen timeout:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_<date>/repo_gate/run_01 \
  --timeout <owner-authorized-seconds> --notify-desktop -- \
  bash tools/verify_repo.sh
```

Do not synthesize, route, generate a bitstream, program an FPGA, or send a
hardware packet in Q1. Q2/B1/H1 each require a separate owner decision after
the preceding evidence is complete.

## 10. Repository gate and Q2 authorization

On 2026-09-28, the owner authorized one repository-gate attempt with a
1,800-second wall-clock timeout and 1,800-second cumulative budget. The
attempt is consumed on pass, failure, timeout, interruption, or infrastructure
failure. Interpret only the detached runner's terminal evidence. Run exactly:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_20260928/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Q2 may launch only if that repository gate records `COMPLETE` with exit code
zero. A gate failure or timeout halts T1o without consuming the conditional Q2
attempt.

**Repository gate result (2026-09-28): FAIL.** The detached runner recorded
`FAILED`, exit code 1, after 870 seconds in
`build/gpu/t1o_per_primitive_material_20260928/repo_gate/run_01`. The single
authorized attempt is consumed. Of 173 Verilog tests, 172 passed and the known
`spu_t1d_board_transaction_tb.v` test timed out. All 12 C++ tests and every
reported Python, oracle, parser, product, trace, and GPU integration suite
passed. The gate reported 236 total passes and two aggregate failures: the
Verilog timeout and the resulting verification-gate failure. Q2 was not
launched and its conditional attempt was not consumed. No retry or Q2 run is
authorized by this result.

**T1d timeout triage:** The isolated board transaction simulation completed
with its existing `PASS` verdict in 20.6 seconds, exceeding the repository
runner's generic 15-second test limit. `run_all_tests.py` now gives only this
test a 60-second limit. Python syntax and `git diff --check` passed after the
change. The consumed repository gate was not rerun; its recorded failure and
the conditional Q2 boundary remain in force pending a renewed frozen gate
attempt budget.

**Renewed repository gate authorization:** The owner froze one new attempt,
1,800 seconds per attempt, and a 1,800-second cumulative budget. The attempt
is consumed on pass, failure, timeout, interruption, or infrastructure
failure. Use the unchanged `bash tools/verify_repo.sh` gate with the sole
test-specific 60-second T1d limit and a fresh evidence directory:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_20260928/repo_gate/run_02 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Interpret only its terminal evidence. If it fails or times out, halt without
Q2 or another implicit retry. If it passes, the previously frozen single Q2
attempt remains authorized with its unchanged production opcode sequence.

**Renewed repository gate result (2026-09-28): PASS.** The detached runner
recorded `COMPLETE`, exit code 0, in 876 seconds in
`build/gpu/t1o_per_primitive_material_20260928/repo_gate/run_02`. All 173
Verilog tests passed, including `spu_t1d_board_transaction_tb.v`; the gate
reported 237 total passes, zero failures, and zero Verilog timeouts. The
renewed one-attempt budget is consumed. The frozen Q2 production oracle may
now launch.

After a gate pass, the owner authorized one detached Q2 production-oracle
attempt with a 1,800-second wall-clock timeout and 1,800-second cumulative
budget. Use production Scene A geometry/U/V for every frame and these opcode
tuples:

```text
A        [5,4,3,2]
B        [0,5,4,3]
C        [1,0,5,4]
return A [5,4,3,2]
```

The independent oracle must compare all 1,228,800 pixels at 640x480 through
coverage, depth winner, winner U/V, winner opcode, Boolean result, RGB, and
video-control alignment. Initial and return A must match exactly. Run exactly:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_20260928/q2_production_oracle/run_01 \
  --timeout 1800 --notify-desktop -- \
  python3 software/tests/test_gpu_t1o_per_primitive_material.py --production
```

The Q2 attempt is consumed on pass, failure, timeout, interruption, or
infrastructure failure. Any non-pass result halts T1o. Q2 does not authorize
synthesis, place-and-route, B1, bitstream generation, FPGA programming, or
hardware transmission.

**Q2 result (2026-09-28): PASS.** The detached runner recorded `COMPLETE`, exit
code 0, in 356 seconds in
`build/gpu/t1o_per_primitive_material_20260928/q2_production_oracle/run_01`.
The independent oracle matched all 1,228,800 production pixels for the frozen
A/B/C/A opcode tuples over Scene A geometry/U/V, including winner selection,
RGB and control alignment, and exact return-A equality. The single Q2
attempt is consumed.

**Synthesis preflight:** The user requested synthesis after Q2. The existing
T1o Q1 profile tag accepts the intended Artix-7 100T, seed-1, 25 MHz
registered four-primitive GPUVGA configuration. The synthesis JSON path
`build/spu_a7_100t_GPUVGA_T1O_PER_PRIMITIVE_MATERIAL_Q1.json` and evidence
directory `build/gpu/t1o_per_primitive_material_20260928/synth_seed1/run_01`
were fresh at preflight. The shell syntax and diff checks passed. The owner
authorized one synthesis attempt with a 3,600-second per-attempt timeout and
3,600-second cumulative budget. The attempt is consumed on pass, failure,
timeout, interruption, or infrastructure failure. Run exactly:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_20260928/synth_seed1/run_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
      T1O_PER_PRIMITIVE_MATERIAL=1 \
      A7_ARTIFACT_TAG=T1O_PER_PRIMITIVE_MATERIAL_Q1 \
  bash hardware/boards/artix7/build_a7.sh 100t gpuvga synth
```

This command runs Yosys synthesis only. It does not invoke place-and-route,
packing, bitstream generation, programming, or UART transport.

**Synthesis attempt 1 result (2026-09-28): FAIL at hierarchy.** The detached
runner recorded `FAILED`, exit code 1, after one second in
`build/gpu/t1o_per_primitive_material_20260928/synth_seed1/run_01`. The build
selected `hardware/boards/artix7/synth_a7_gpu_vga_t1d.ys` because
`GPU_T1D_UART=1`. That manifest omits
`hardware/rtl/gpu/spu_material_op_select4.v`, so Yosys reported the module
missing from the design. The Q1 scope had added the module only to the
non-UART `synth_a7_gpu_vga.ys` manifest. No synthesis JSON was produced. The
authorized one-attempt synthesis budget is consumed.

**Halt-and-Flag correction proposal:** Add one `read_verilog -sv` entry for
`spu_material_op_select4.v` to the T1d UART manifest, verify the manifest
reaches Yosys hierarchy, then request a new owner-frozen synthesis budget.
This is a source-manifest correction; it does not change RTL behavior, packet
semantics, or the Q1/Q2 simulation evidence. No correction or retry is
authorized by the consumed attempt.

**Manifest correction and renewed synthesis authorization:** The owner
authorized exactly one added `read_verilog -sv` entry for
`hardware/rtl/gpu/spu_material_op_select4.v` in
`hardware/boards/artix7/synth_a7_gpu_vga_t1d.ys`, followed by one synthesis
attempt with a 3,600-second per-attempt timeout and 3,600-second cumulative
budget. The attempt is consumed on success, failure, timeout, interruption,
or infrastructure error. `bash -n`, `git diff --check`, and a Yosys
`hierarchy -check` under the frozen profile passed before launch; the hierarchy
log confirms `spu_material_op_select4` is in the selected design. Use the same
profile and seed-1 command as above with a fresh evidence path:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_20260928/synth_seed1/run_02 \
  --timeout 3600 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
      T1O_PER_PRIMITIVE_MATERIAL=1 \
      A7_ARTIFACT_TAG=T1O_PER_PRIMITIVE_MATERIAL_Q1 \
  bash hardware/boards/artix7/build_a7.sh 100t gpuvga synth
```

If this retry fails, halt without another correction or attempt. A pass
authorizes evidence recording only; place-and-route, packing, bitstream
generation, programming, and UART hardware transmission remain outside scope.

**Synthesis attempt 2 result (2026-09-28): PASS.** The detached runner recorded
`COMPLETE`, exit code 0, in 22 seconds in
`build/gpu/t1o_per_primitive_material_20260928/synth_seed1/run_02`. Yosys
resolved the complete hierarchy, including one `spu_material_op_select4`
instance in the GPU path, and wrote
`build/spu_a7_100t_GPUVGA_T1O_PER_PRIMITIVE_MATERIAL_Q1.json` (30,073,027
bytes; SHA-256
`96915215cd0e7b6d53c6beb2476545f40bd590d47c66576ad571c93f62ab4ffa`).
The final `stat -top` reports 57,286 cells including submodules, 6 DSP48E1,
and an estimated 19,584 logic cells for `spu_a7_gpu_vga_top`. These are
synthesis counts, not placed-resource use or routed timing. The renewed
one-attempt budget is consumed. Stop before place-and-route and all hardware
steps.

**Place-and-route authorization and result:** The owner froze one attempt, a 3,600-second
per-attempt timeout, and a 3,600-second cumulative budget. The attempt is
consumed on success, failure, timeout, interruption, or infrastructure error.
The pass threshold is routed Fmax of at least 25.00 MHz. The Artix-7 100T chip
database and T1d UART XDC exist, the
source JSON has the recorded SHA-256, and the route output paths are fresh.
The existing build script's `pnr` step runs nextpnr with seed 1 and a 25 MHz
target, then collects routed metrics; it does not pack a bitstream. The exact
command prepared for a single attempt is:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1o_per_primitive_material_20260928/pnr_seed1/run_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
      T1O_PER_PRIMITIVE_MATERIAL=1 \
      A7_ARTIFACT_TAG=T1O_PER_PRIMITIVE_MATERIAL_Q1 \
  bash hardware/boards/artix7/build_a7.sh 100t gpuvga pnr
```

The detached run recorded `COMPLETE`, exit code 0, and a 646-second duration
in `build/gpu/t1o_per_primitive_material_20260928/pnr_seed1/run_01`.
The post-route metrics in
`build/metrics/artix7_100t_GPUVGA_T1O_PER_PRIMITIVE_MATERIAL_Q1.json`
report 35.42 MHz for `clk_pixel` and 195.05 MHz for `sys_clk`; both pass the
frozen 25.00 MHz threshold. Reported use is 43,301 SLICE_LUTX, 16,416
SLICE_FFX, 1,208 CARRY4, and 6 DSP48E1. The one-attempt budget is consumed.
Packing, bitstream generation, programming, and UART hardware transmission
remain outside this route authorization.

**Owner-authorized B1 pack and H1 transport (2026-09-28):** The pack-only
detached run at `build/gpu/t1o_per_primitive_material_20260928/pack_seed1/run_01`
recorded `COMPLETE`, exit 0, in 284 seconds. It produced
`build/spu_a7_100t_GPUVGA_T1O_PER_PRIMITIVE_MATERIAL_Q1.bit` (3,825,950 bytes;
SHA-256 `9cd34b81b30a6048e231d77add649c6adab835b14fe08d1ab99d9c03ff9b0016`).
The exact bitstream was loaded into FPGA SRAM with
`openFPGALoader -c dirtyJtag --freq 1000000`; the programmer reached 100% and
reported `ISC_DONE=1` and `DONE=1`. Programming log:
`build/gpu/t1o_per_primitive_material_20260928/h1/program_01_escalated.log`.

`tools/send_gpu_t1o_sequence.py` sent the fixed production Scene A geometry/U/V
with opcode tuples `[5,4,3,2]`, `[0,5,4,3]`, `[1,0,5,4]`, and return
`[5,4,3,2]` through the CH340 UART at 115200 8N1. Each 179-byte transaction
completed `tcdrain`; start-to-start gaps were 5011.436138, 5011.617771, and
5011.598304 ms. The initial and return-A packet hashes match exactly.
Transcript: `build/gpu/t1o_per_primitive_material_20260928/h1/sequence_01.json`,
SHA-256 `26e634a777f2dc0c155dae70c384f02b1ecc2cbcdb00cb4199152ce356529a5b`.
The owner confirmed that the displayed image changed through the sequence and
returned to the initial pattern. This is an operator-observed visual transition
and return, with fixed geometry/U/V and changing opcode tuples. No physical
pixel capture was made, so exact winner/opcode/pixel correspondence remains
supported by the simulation oracle rather than measured on hardware.

## 11. Evidence claims

Q1 focused evidence is stored in
`build/gpu/t1o_per_primitive_material_20260928/focused_q1/run_01`.
The detached runner recorded `COMPLETE`, exit code 0, and a 258-second
duration on 2026-09-28.

| Evidence dimension | Result |
|---|---|
| Structural validation | PASS: 1,424 scene bits, 178 payload bytes, 179 wire bytes, four-byte tail validation, common winner mux, same-edge U/V/opcode registration, and default-off board propagation |
| T1o functional simulation | PASS: frozen discriminator, all six legal operations at every primitive index, winner-selected opcode/RGB, atomic A/B/C/A transitions, invalid opcode at every tail position, unchanged active state, and valid recovery |
| Focused legacy regressions | PASS: T1n, T1m, T1l, T1k, T1j, T1i, T1h, T1g, and GPU top integration |
| Static checks | PASS: `bash -n hardware/boards/artix7/build_a7.sh` and `git diff --check` |
| Synthesis | PASS: Yosys hierarchy and JSON; 57,286 cells, 6 DSP48E1, top LC estimate 19,584 |
| Place-and-route | PASS: seed 1, post-route `clk_pixel` 35.42 MHz and `sys_clk` 195.05 MHz against 25.00 MHz target; 43,301 SLICE_LUTX, 16,416 SLICE_FFX, 1,208 CARRY4, 6 DSP48E1 |
| B1 pack | PASS: exact routed image packed into a 3,825,950-byte bitstream |
| H1 transport | PASS: FPGA SRAM load reported DONE; four 179-byte fixed-scene material packets drained; exact return-A packet equality |
| H1 visual | PASS (operator-observed, visual-only): image changed through fixed-scene opcode sequence and returned to initial pattern; no physical pixel comparison |
| Production Q2 oracle | PASS: 1,228,800 pixels; exit 0 after 356 seconds |
| Repository-wide gate | Renewed gate PASS: exit 0 after 876 seconds; 237 total passes, zero failures; prior failed attempt retained as separate evidence |

## 12. Stop conditions

Halt Q1 and report the minimal correction if any condition occurs:

* any opcode byte cannot be validated before `commit_pending` is asserted;
* the inactive packet cannot recover after an invalid opcode without changing
  valid T1n behavior;
* opcode selection uses a winner ID different from winner-selected U/V;
* activation requires a partial-frame opcode change;
* a new pipeline stage is required for functional alignment;
* any legacy profile length, packet layout, or legal behavior changes when
  T1o is disabled;
* the primary overlap oracle loses a winning lane, winner boundary, or
  non-vacuous assigned-op distinction;
* any focused regression fails.

Do not silently revise the packet, opcode tuple, stage count, invalid recovery,
or evidence boundary. Amend this contract and obtain owner authorization.
