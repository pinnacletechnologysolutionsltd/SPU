# Engineering Contract: GPU T1r Q1 Focused-Gate Recovery

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-PALETTE-PAIR-Q1-RECOVERY-2026-10-01`  
**Status:** DRAFT — implementation and fresh focused-gate execution NOT AUTHORIZED  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `run_all_tests.py` focused filter and owner evidence review

## 0. Purpose and prior evidence boundary

This contract recovers only the T1r Q1 focused functional gate after the campaign in [the original Q1 contract](contract_gpu_t1r_palette_pair_q1_2026-10-01.md) halted. It does not authorize hardware access, repository verification, synthesis, place-and-route, or further RTL/design changes.

Record the prior campaign exactly as follows:

| Check | Prior outcome | Interpretation |
|---|---|---|
| Direct T1r Python/RTL oracle | PASS | Diagnostic evidence on the corrected source state; repeat once under this contract |
| Filtered Verilog triage | TIMEOUT, exit 124 at 600 s | Infrastructure-inconclusive; consumes the original invocation |
| T1q compatibility | PASS | Prior evidence only; repeat once under this contract |
| T1p compatibility, first invocation | FAIL at pixel `(10,10)` | Consumed the original invocation |
| T1p compatibility, post-failure correction rerun | PASS | Diagnostic only; it does not replace the consumed invocation |
| T1o compatibility | PASS | Prior evidence only; repeat once under this contract |

The post-failure selector correction is retained. The current truth-predicate condition is `(T1P_MATERIAL || T1Q_TABLE)`, preserving T1p selectors while enabling T1q/T1r selectors. The old filtered triage had empty captured stdout/stderr and no usable phase timing; do not infer a test failure or successful progress from that timeout.

## 1. Frozen base identity

The frozen repository base is commit `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`. The working tree is dirty; the following SHA-256 values identify the current T1r implementation and focused-gate inputs. Before any fresh invocation, recompute this manifest and halt if any listed value differs.

```text
cf0adc42370b1add78d121a880f57ea934254fbc9f59c76d36d4280b465ac700  hardware/rtl/gpu/spu_gpu_top.v
fcf82cb555be46701e7db408a90e6f5603da6bb70a4e55e1154a707d4ef9cbcc  hardware/rtl/gpu/spu_video_timing.v
f3a8221f0df166353e8edeb9dc561d562188694c5cc648b949a103c442012fd8  hardware/rtl/gpu/spu_scene_loader.v
8801576124865a597b231a3e73fde828ce06b18af320d2bd75fbcbb1ea593cdc  hardware/rtl/gpu/spu_scene_unpack.v
96c02f34d0ef40f148d23e7a4a8b08d10110a87784b7742e60ebe5aa2b4b5ccc  hardware/rtl/gpu/spu_scene_profile_unpack.v
84fa69cd6927053f8ab87094ef14d3f57b0d31abc1168402ff9fe6e19baf057b  hardware/rtl/gpu/spu_prepared_scene_control.v
cc2e6007894987d3064d5791c91b827de2f977740a86a544785ef02358de1567  hardware/rtl/gpu/spu_prepared_scene_control4.v
f4c2698f960528e5eb7563e94a5d4c1d4bee7fe54401c73db45e428b41e04dd0  hardware/rtl/gpu/spu_dual_raster.v
386414cc2d301a942a542d22f353daae292379b87e794a75b9533473ac1877b6  hardware/rtl/gpu/spu_quad_raster.v
4e7674635363fd317f337a3ee1f7aec419f2d737459dabb3bfd4e5983d8f13bf  hardware/rtl/gpu/spu_raster_unit.v
cd6d2d7bd6b73fde5d848e806b8a6a4be911c5760ecf63bea84497902560ee9d  hardware/rtl/gpu/spu_edge_stepper.v
d4d9affab7257fc7d0d8d1d4a625899917d322c5b96c89955f2bb4b7c9a56d19  hardware/rtl/gpu/spu_depth_dispatch.v
35bff6da2bbb7092a59d206bed6683563bc292284783bc8fbbd274bb5d610641  hardware/rtl/gpu/spu_depth_dispatch4.v
ca7e0c21793a173adb51452f15df2e2851b8bbdd27315aa7d9e056814ed1c732  hardware/rtl/gpu/spu_prepared_scalar_attribute4.v
0fadfdc7b6a0ba2b64a820097c3b7edfe4835a52b5087da6d9dcb1e151a0341f  hardware/rtl/gpu/spu_material_op_select4.v
115c9685c544f8a37f3ee4ae3dedac8202b2a8f6463fb7178cac7efadddae19c  hardware/rtl/gpu/spu_material_predicate_select4.v
1921d2c0fc4a74843502267b86e632aa8af06fadf32361bcc3a4b84145786c49  hardware/rtl/gpu/spu_pixel_output_register.v
e86d84244e1c2352ef86b6188d63be820a4a81c34ad23864f696cf1e9f3492bd  hardware/rtl/gpu/spu_depth_math.v
9f49e386f4bf04b200097c4bb3c82f1af42ef3decebafae081dd49d1a4749306  hardware/rtl/gpu/spu_reciprocal_core.v
6f95ae24f276af6437ce9d91152e6babec314a1de2e8a669697530cbae764bf5  hardware/rtl/gpu/spu_shared_mult35.v
7e6daa88abd61ba5587b3e98ad9d127d88b6fefbd259d1f784b2ddf0eb218b74  hardware/rtl/gpu/spu_attr_stepper.v
4e21fe4700544dc747856eb55cf326472e8424ce20578141f32669ab165ba95a  hardware/rtl/gpu/spu_depth_compare.v
5ffb83c57abdb6a802e14550b2bb87fb986f75f1f43db5f6cb2d535cbcc3a46c  hardware/rtl/gpu/spu_depth_compare4.v
1e511f84762d66b65bbd592d4278a4c2e4240c5c9360a75b326be25ea582068b  hardware/rtl/hal/hal_vga.v
45f1ebbf71124f25d6fda0ff27f88e8d06e2ab32c03543bc6feb804fe3213634  hardware/rtl/hal/hal_hdmi.v
8fc2a34e29449ffc7499e10c276862f835c1e90f4d73e393f1050ae893e6e367  hardware/rtl/hal/hal_hdmi_tmds.v
3aad06dbbab9866c6443d446746666acba8f7b15c7d68a055fdfe990856936ab  hardware/rtl/hal/hal_hdmi_serdes_a7.v
cb92ec158f1ada5b934897070e5299da59f1f67c2bc2691890cfbca5a8568784  hardware/rtl/gpu/spu_material_palette_select4.v
e7d6e074b6e5f7a18053ac971d89c1114d20844beeb18542376ba6147a2c9e68  hardware/tests/common/spu_gpu_t1r_palette_pair_tb.v
811f5bb6c397aaf456ee72ad3fad7a7eea3da112c4482321fbe8993087cfa069  software/tests/test_gpu_t1r_palette_pair.py
1d0123347049130975d6271769fba2ba8fb34f7fbda5d62fe426735a86f7001d  software/tests/test_gpu_t1i_uv.py
079a14b7fa4565c86e82311d571ab1b70099e96e598eededa7e8bffa5a0f4143  fixtures/gpu_t1i_scene_a_wire_175b.hex
49feed1cd12813b0aca21716ad44e2f9fd228104c32a2d45cdca503ad26391d1  software/tests/test_gpu_t1p_predicate_bits.py
75d5e78cac868ac47eec1d68953c2923e5a50a1c24affc8bd1dea0e662fae7bf  software/tests/test_gpu_t1q_truth_table.py
86a20efc71000598977607eba922aa0627f66241578c1cb9561286fc5482ed5e  software/tests/test_gpu_t1o_per_primitive_material.py
c1d4223738a4a6e660b16a58ebdc5a593d0c563e864b8aee0706e622d3c1f927  run_all_tests.py (pre-recovery source-filter implementation)
```

The reviewed source-filter correction below is the only implementation change allowed by this recovery contract. After that correction, record the resulting `run_all_tests.py` SHA-256 in the campaign evidence directory before executing any test. Do not alter any RTL, oracle, fixture, compatibility test, packet, profile, timing, or build source.

## 2. Halt-and-flag finding and bounded correction

The existing T1r `TB_FILTER` path starts with the broad `hardware/rtl` prefix in its allowed-directory test. That prefix admits unrelated RTL files before the later GPU exclusion and T1r dependency append. The direct T1r Python oracle instead compiles its explicit `test_gpu_t1i_uv.RTL_FILES` list plus `spu_material_palette_select4.v`. The old filtered run timed out with empty captured logs, so the broad source collection is an unresolved runtime cost.

Before tests, update only the `TB_FILTER=spu_gpu_t1r_palette_pair_tb` source selection in `run_all_tests.py` so `src_unique` is replaced with exactly these source files, in this order:

```text
hardware/rtl/gpu/spu_gpu_top.v
hardware/rtl/gpu/spu_video_timing.v
hardware/rtl/gpu/spu_scene_loader.v
hardware/rtl/gpu/spu_scene_unpack.v
hardware/rtl/gpu/spu_scene_profile_unpack.v
hardware/rtl/gpu/spu_prepared_scene_control.v
hardware/rtl/gpu/spu_prepared_scene_control4.v
hardware/rtl/gpu/spu_dual_raster.v
hardware/rtl/gpu/spu_quad_raster.v
hardware/rtl/gpu/spu_raster_unit.v
hardware/rtl/gpu/spu_edge_stepper.v
hardware/rtl/gpu/spu_depth_dispatch.v
hardware/rtl/gpu/spu_depth_dispatch4.v
hardware/rtl/gpu/spu_prepared_scalar_attribute4.v
hardware/rtl/gpu/spu_material_op_select4.v
hardware/rtl/gpu/spu_material_predicate_select4.v
hardware/rtl/gpu/spu_pixel_output_register.v
hardware/rtl/gpu/spu_depth_math.v
hardware/rtl/gpu/spu_reciprocal_core.v
hardware/rtl/gpu/spu_shared_mult35.v
hardware/rtl/gpu/spu_attr_stepper.v
hardware/rtl/gpu/spu_depth_compare.v
hardware/rtl/gpu/spu_depth_compare4.v
hardware/rtl/hal/hal_vga.v
hardware/rtl/hal/hal_hdmi.v
hardware/rtl/hal/hal_hdmi_tmds.v
hardware/rtl/hal/hal_hdmi_serdes_a7.v
hardware/rtl/gpu/spu_material_palette_select4.v
```

Do not change source selection for any other `TB_FILTER` value. Confirm the list matches the T1r test's declared RTL inputs and that no other testbench matches `spu_gpu_t1r_palette_pair_tb`. Save the filtered-runner diff and post-correction SHA-256 in `build/gpu/t1r_palette_pair_20261001/recovery_01/` before starting the campaign.

## 3. Fresh focused-gate campaign

Authorize one invocation of each exact command below, in order. Each invocation has a 300-second maximum; cumulative campaign budget is 1,500 seconds. The corrected filtered source set matches the direct T1r oracle's explicit RTL set. The direct oracle completed within one second in the prior focused session; 300 seconds provides bounded compile and execution headroom while the old 600-second broad-source timeout remains recorded as inconclusive.

```bash
python3 software/tests/test_gpu_t1r_palette_pair.py
TB_FILTER=spu_gpu_t1r_palette_pair_tb python3 run_all_tests.py
python3 software/tests/test_gpu_t1q_truth_table.py
python3 software/tests/test_gpu_t1p_predicate_bits.py
python3 software/tests/test_gpu_t1o_per_primitive_material.py
```

Record the exact command, start/end time, exit status, stdout/stderr, and source hashes for each invocation. An invocation expected to exceed 60 seconds must use `tools/run_detached_job.sh` with a unique new child of `build/`, `--timeout 300`, and `--notify-desktop`; after `LAUNCHED`, record its unit and evidence path and end the turn. Interpret only its durable terminal marker and `result.json`.

Stop immediately on any nonzero exit, assertion failure, timeout, missing result, source-hash mismatch, or unexpected additional testbench. Do not retry, increase a timeout, substitute a command, or proceed to later tests after a failed or unavailable invocation. A failure or unavailable result consumes its slot.

## 4. Acceptance and downstream boundary

The recovery focused gate passes only when all five fresh invocations complete successfully on the frozen source state and the filtered Verilog run reports exactly one selected testbench and a passing result. A timeout is infrastructure-inconclusive and does not pass.

This contract does not authorize the repository gate, mandatory Padé synthesis, T1r synthesis/place-and-route, FPGA programming, UART traffic, or visual observation. If and only if this focused campaign passes, report its evidence and request a separate owner decision to unlock the still-unconsumed repository → Padé synthesis → T1r route gates. Preserve the single-attempt, 1,800-second budgets and exact commands in the original Q1 contract unless a later owner-approved contract changes them.

| Evidence claim | Recovery starting state |
|---|---|
| T1r implementation source identity | Frozen by §1; runner correction hash pending |
| Fresh direct T1r oracle | NOT RUN under this recovery contract |
| Fresh filtered Verilog triage | NOT RUN under this recovery contract |
| Fresh T1q/T1p/T1o compatibility | NOT RUN under this recovery contract |
| Repository gate | NOT RUN; not authorized here |
| Synthesis/place-and-route | NOT RUN; not authorized here |
| Hardware/interface/silicon evidence | NOT RUN; not authorized here |
