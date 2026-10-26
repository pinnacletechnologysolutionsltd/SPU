# Engineering Contract: T1q Four-Bit Truth-Table Material, Q0 Scope

**Date:** 2026-09-29  
**Contract ID:** `GPU-T1Q-TRUTH-TABLE-MATERIAL-Q0-2026-09-29`  
**Status:** `Q1 RTL, SOFTWARE ORACLE, AND FOCUSED COMPATIBILITY CHECKS PASS; HARDWARE/REPO GATES PENDING`
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `tools/verify_repo.sh` plus owner evidence review

## 0. Execute Q0 source review only

Run from the repository root:

```bash
sed -n '235,375p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '985,1135p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '1,120p' hardware/rtl/gpu/spu_scene_loader.v
sed -n '1,100p' hardware/rtl/gpu/spu_material_op_select4.v
sed -n '1,100p' hardware/rtl/gpu/spu_material_predicate_select4.v
sed -n '1,110p' software/tests/test_gpu_t1p_predicate_bits.py
git diff --check
```

Q0 authorizes this contract and read-only source/oracle review only. Do not
edit T1p RTL, loader, fixture, board profile, sender, or evidence; do not
launch simulation, synthesis, repository-gate retry, FPGA programming, or UART
transmission under this contract. T1q Q1 may start only after a renewed T1p
integration gate records `COMPLETE`, exit 0, and the T1d timeout diagnosis
has been recorded separately. Freeze the T1q Q1 attempt count and wall-clock
budget before launching any gate expected to exceed 60 seconds.

## 1. Objective and packet meaning

Make the two selected T1p predicates the inputs to a four-bit Boolean truth
table for each winning primitive. Keep the same 182-byte payload and 183-byte
wire length, geometry/U/V fields, four predicate-selector bytes, two-bank
commit, winner selection, output cycle, and black invalid-fragment behavior.
Use a separate default-off `T1Q_TRUTH_TABLE_MATERIAL` profile, mutually
exclusive with T1p and earlier material modes. T1p packet bytes retain their
existing opcode interpretation when T1q is disabled.

| Payload bytes | Scene bits | T1q meaning |
|---:|---:|---|
| `0..173` | `0..1391` | Existing T1i geometry/U/V |
| `174..177` | `1392..1423` | Primitive 0..3 truth tables, one byte each |
| `178..181` | `1424..1455` | Primitive 0..3 U/V predicate selectors |

Require the high nibble of each truth-table byte to be zero. All low-nibble
values `0..15` are legal; selector bytes remain unrestricted. Define
`i = {pred_u, pred_v}` and output `table[i]`: bit 0 is `f(0,0)`, bit 1 is
`f(0,1)`, bit 2 is `f(1,0)`, and bit 3 is `f(1,1)`. Thus constant zero is
`0`, constant one `F`, U `C`, V `A`, XOR `6`, AND `8`, OR `E`, and NOT U `3`.
Constant one colors only valid winning fragments; uncovered or invalid
fragments remain black. Retain the T1p blue/yellow mapping for false/true.

Do not add texture memory, a shader instruction stream, per-pixel parameters,
new color storage, or a new pipeline stage.

## 2. Halt-and-flag review findings

1. **Packet compatibility hazard:** Reinterpreting values `0..5` as LUTs
   changes every legacy T1p opcode meaning. Require a distinct elaboration
   profile and reject simultaneous T1p/T1q enables. Keep the T1p path and
   existing packets bit-for-bit when T1q is disabled.
2. **Validation hazard:** The T1p loader validates payload bytes `174..177`
   against `8'h05`. T1q requires the same explicit window against `8'h0F`.
   Keep selector bytes `178..181` outside that window. Accumulate an invalid
   high nibble, reject the entire candidate at byte 181, leave the active
   bank and generation unchanged, then accept a fresh valid packet.
3. **Activation-edge hazard:** `spu_material_op_select4` and
   `spu_material_predicate_select4` already select candidate tuples on the
   activation edge and active tuples on subsequent edges using the same
   `partition_winner_id`. The T1q table byte and selector byte must follow
   that pairing on the same registered U/V and video-control edge. An added
   register or a mismatch at frame-start is outside this contract.
4. **Timing hazard:** T1q replaces the six-way operation case with a
   four-input indexed LUT after two variable predicate bit selects. Do not
   infer timing from T1p's routed 31.23 MHz pixel-clock result; route the
   T1q profile at the frozen 25 MHz target before hardware qualification.
5. **Oracle hazard:** A single XOR scene cannot distinguish all 16 LUTs.
   Q1 must exercise all four `(pred_u,pred_v)` combinations for each lane,
   all 16 tables, both selector endpoint indices, winner boundaries,
   constant-one masking, invalid high-nibble rejection/recovery, and exact
   A/B/C/return-A restoration. Verify the production fixture has enough
   predicate-pair coverage before freezing its discriminator; otherwise use
   an independently specified reduced scene.

No source contradiction remains for the scoped architecture. The renewed T1p
integration gate completed with exit 0 after the isolated T1d diagnosis was
recorded (two isolated PASS samples at 55.506s and 50.722s; test cap raised
from 60s to 90s). Q1 implementation is authorized and underway. No T1q
simulation, route, hardware programming, or UART evidence is implied by this
status update.

## 3. Proposed Q1 implementation boundary after prerequisite passes

1. Add `T1Q_TRUTH_TABLE_MATERIAL`, default 0, to
   `hardware/rtl/gpu/spu_gpu_top.v` and
   `hardware/boards/artix7/spu_a7_gpu_vga_top.v`. Enforce exclusive profile
   guards, preserve the T1p scene layout, and parameterize only the explicit
   byte-window maximum to `8'h0F` for T1q.
2. Reuse the four-lane candidate/active selection structure, registering the
   winning T1q table byte beside its selector and U/V sample. Select
   `table[{pred_u,pred_v}]` from the low nibble. Preserve existing T1p and
   older branches without semantic changes.
3. Add an independent Python truth-table oracle and focused Verilog checks
   in `software/tests/test_gpu_t1q_truth_table.py`; register it in
   `run_all_tests.py`. Add a scoped runner only if the focused command set
   exceeds 60 seconds. Keep each new module or script within the 50–150 line
   Lithic range where practical.
4. Add an exact, default-off T1q Artix-7 build profile only after the focused
   software oracle and backward-compatibility checks pass.

## 4. Required future gates and evidence boundary

Run the following only in an owner-authorized Q1 campaign after the T1p
integration prerequisite. Record exact commands, source state, terminal
markers, exit codes, and artifacts. Do not infer one evidence dimension from
another.

### 4.1 Frozen detached attempts

The focused T1q RTL/oracle test, unchanged T1p and T1o compatibility tests,
required ROTC/IROTC and exact-arithmetic tests, `bash -n`, and `git diff
--check` completed before these launches. Freeze each long-running gate as a
single attempt with a 1,800-second timeout and a 1,800-second cumulative
campaign budget:

| Gate | Maximum attempts | Per-attempt timeout | Cumulative budget |
|---|---:|---:|---:|
| T1q Artix-7 GPUVGA route, seed 1 | 1 | 1,800 s | 1,800 s |
| Repository regression/hygiene gate | 1 | 1,800 s | 1,800 s |
| Mandatory Artix-7 100T Padé build | 1 | 1,800 s | 1,800 s |

Each launch consumes its sole slot regardless of terminal result. No timeout
extension or relaunch is included in this freeze.

```bash
python3 software/tests/test_gpu_t1q_truth_table.py
python3 software/tests/test_gpu_t1p_predicate_bits.py
python3 software/tests/test_gpu_t1o_per_primitive_material.py
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
git diff --check
```

For repository-wide verification, launch its frozen single detached attempt:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1q_truth_table_20260929/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Stop after `LAUNCHED`; interpret only a durable
`COMPLETE`, `FAILED`, or `TIMEOUT` marker with `result.json`. A separate
owner-frozen build campaign must run the exact T1q Artix-7 profile and record
pixel-clock timing against 25 MHz before any FPGA or visual claim. Mark all
unrun dimensions `NOT RUN`.

The mandatory Artix-7 100T Padé synthesis check has its own frozen detached
attempt before Q1 completion:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1q_truth_table_20260929/pade_synthesis/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

The frozen T1q route attempt is:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1q_truth_table_20260929/build_seed1/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 \
    FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
    T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
    T1O_PER_PRIMITIVE_MATERIAL=0 T1P_PER_PRIMITIVE_PREDICATES=0 \
    T1Q_TRUTH_TABLE_MATERIAL=1 A7_ARTIFACT_TAG=T1Q_TRUTH_TABLE_MATERIAL_Q1 \
    bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
```

## 5. Stop conditions

Halt on any T1p/T1q packet alias, unvalidated table high nibble, selector
validation, activation-edge mismatch, backward-compatibility difference,
vacuous truth-table test, failed semantic assertion, or route below the
frozen clock threshold. Report the smallest correction before changing the
architecture or spending another gate attempt.
