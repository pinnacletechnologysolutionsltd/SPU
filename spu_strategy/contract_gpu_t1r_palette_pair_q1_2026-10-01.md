# Engineering Contract: GPU T1r Per-Primitive Palette-Pair Q1

**Date:** 2026-10-01  
**Contract ID:** `GPU-T1R-PALETTE-PAIR-Q1-2026-10-01`  
**Status:** DRAFT — Q1 implementation and verification NOT AUTHORIZED  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `tools/verify_repo.sh` plus owner evidence review

## 0. Execution boundary

This contract freezes a proposed Q1 implementation and verification campaign. It does not authorize code edits, test execution, builds, FPGA programming, UART transmission, or visual claims. Start only after the owner changes this contract to `ACTIVE` or gives equivalent explicit authorization.

Run all commands from the repository root. Before edits, inspect the frozen T1r Q0 findings and run the implementer's halt-and-flag review. If the source no longer matches Q0, halt and revise this contract before implementation.

## 1. Objective and exact packet layout

Implement the design frozen in [T1r Q0](contract_gpu_t1r_palette_pair_q0_2026-10-01.md): the existing T1q four-bit Boolean material result followed by a per-winning-primitive RGB palette pair. Keep all existing T1q fields and semantics unchanged. T1r is a distinct, default-off profile that enables T1q truth-table and predicate-selector behavior internally; do not require simultaneous T1q profile enablement.

The T1r payload is exactly 186 bytes; the `A5`-prefixed wire frame is exactly 187 bytes.

| Payload byte | Scene bits | Meaning |
|---:|---:|---|
| 0..173 | 0..1391 | Existing T1q geometry and U/V data |
| 174..177 | 1392..1423 | Primitive 0..3 truth tables; each byte must be `0x00..0x0F` |
| 178..181 | 1424..1455 | Primitive 0..3 predicate selectors; unrestricted bytes |
| 182..185 | 1456..1487 | Primitive 0..3 palette-pair bytes |

For each palette byte, bits `[2:0]` encode outcome-0 RGB with `R=bit0`, `G=bit1`, `B=bit2`; bits `[5:3]` encode outcome-1 in the same order; bits `[7:6]` must be zero. Thus palette value `0x1C` maps false to RGB `001` and true to RGB `110`. Expand each one-bit RGB channel to the existing four-bit channel bus by replication. Invalid fragments remain black.

The scene-bank byte mapping remains `scene[8*i +: 8]`. Four palette bytes therefore occupy `candidate_scene[1456 +: 32]` and `active_scene[1456 +: 32]`, ordered lane 0 in `[7:0]` through lane 3 in `[31:24]`.

## 2. Frozen design choices and implementer review

1. **Profile:** Add `T1R_PALETTE_PAIR_MATERIAL`, default `0`, as a separate compile-time profile. T1r selects T1q truth-table evaluation internally. Reject conflicting T1P/T1Q/T1R and earlier material profiles using explicit elaboration guards and build-script checks. The T1q build/profile remains byte-for-byte unchanged when T1r is disabled.
2. **Scene width and receiver:** T1r uses `SCENE_BITS=1488` and `PAYLOAD_BYTES=186`. The internal loader counter is already 8 bits and can represent payload indices 0..185. Widen the `diag_payload_count` declaration/connection from 7 bits to 8 bits in `spu_scene_loader.v`, `spu_gpu_top.v`, and `spu_a7_gpu_vga_top.v` so diagnostics do not truncate a T1r receive. Do not change the diagnostic record wire format unless a separate contract requires it.
3. **Validation parameters:** Add a second validation window to `spu_scene_loader` with disabled defaults:
   - `VALIDATE_WINDOW2_START = 0`
   - `VALIDATE_WINDOW2_BYTES = 0`
   - `WINDOW2_BYTE_MAX = 8'hFF`

   Preserve the existing first-window parameters and all existing trailing-byte behavior. For T1r set window 1 to start `174`, length `4`, max `8'h0F`; set window 2 to start `182`, length `4`, max `8'h3F`. An invalid byte in either window must latch candidate invalidity and prevent `commit_pending`, including an invalid byte at payload index 185. Invalid candidate data must not change active bank, active generation, or active rendering. Existing T1q continues to use only window 1 at `174/4/0x0F` and stays at 182 payload bytes.
4. **Selection and activation:** Add `spu_material_palette_select4.v`, a single-purpose four-lane selector that follows the existing material-op/selector pattern. Use `partition_winner_id`. On `activate_scene`, select from the candidate palette tuple on the same edge that candidate table/selector and winner-selected U/V are selected. On later pixels, select from the active tuple. Do not add a pipeline stage. Keep palette output gated by the registered valid-fragment signal.
5. **Diagnostic boundary:** The 8-bit diagnostic count is observation only. It does not establish packet acceptance, scene activation, or rendering. Do not change T1D UART diagnostic packet framing.
6. **No timing or scope expansion:** Do not change clock targets, timing constraints, rasterization, predicate generation, winner policy, T1q truth-table indexing, or the active-scene protocol.

If any review finds that preserving existing profile validation requires different parameter semantics, stop and flag the smallest correction before editing.

## 3. Frozen four-lane palette discriminator

Use these four distinct palette pairs in lane order. Both outcomes must be forced and checked for each lane by the oracle scene.

| Lane | Outcome 0 RGB | Outcome 1 RGB | Palette byte |
|---:|---:|---:|---:|
| 0 | `001` | `110` | `0x1C` |
| 1 | `010` | `101` | `0x2A` |
| 2 | `100` | `011` | `0x31` |
| 3 | `111` | `000` | `0x07` |

The complete palette suffix is bytes `1C 2A 31 07`. With `R=bit0`, `G=bit1`, and `B=bit2`, palette value `0x1C` maps false to RGB `001` and true to RGB `110`. Across the four lanes, all eight RGB codes are used, every pair is distinct, and every reserved bit is zero. Freeze the discriminator packet as follows: take payload bytes `0..173` from `fixtures/gpu_t1i_scene_a_wire_175b.hex`, append truth-table bytes `06 06 06 06`, selector bytes `00 00 00 00`, then the palette suffix `1C 2A 31 07`. The test must assert that this scene produces both XOR outcomes for every winning lane, all four winning lane IDs, overlapping coverage, and uncovered pixels; stop if any required case is absent. The fixed Python oracle and Verilog testbench must derive expected pixels from the selected lane, truth-table result, and this table; do not copy observed RTL outputs into expected values.

The discriminator scene must create visible winning samples from all four primitive IDs, force both truth-table results for each ID, include at least one pixel where primitives overlap so the depth winner is observable, and include uncovered pixels that must remain black. If the frozen fixture cannot produce these cases deterministically, halt and define a corrected scene in a revised contract before implementation.

## 4. Exact implementation scope and order

Target files:

- `hardware/rtl/gpu/spu_scene_loader.v`
- `hardware/rtl/gpu/spu_gpu_top.v`
- New `hardware/rtl/gpu/spu_material_palette_select4.v`
- `hardware/boards/artix7/spu_a7_gpu_vga_top.v`
- `hardware/boards/artix7/synth_a7_gpu_vga_t1d.ys`
- `hardware/boards/artix7/build_a7.sh`
- `run_all_tests.py`
- New `hardware/tests/common/spu_gpu_t1r_palette_pair_tb.v`
- New `software/tests/test_gpu_t1r_palette_pair.py`

Implement in this order:

1. Review scene-bank sizes, receiver counter and diagnostic widths, loader final-byte logic, scene unpack slices, current profile guards, and build profile/tag allowlists. Halt if they contradict §2.
2. Extend the loader with the independently bounded second validation window using disabled defaults. Preserve T1O trailing-byte and all T1q/T1p behavior.
3. Add the default-off T1r profile and 186-byte packet configuration. Add its board-wrapper parameter and exact build-script profile/tag allowlist.
4. Add `spu_material_palette_select4.v`, add it to the explicit GPUVGA synthesis source list, connect four-lane candidate/active palette selection on the existing winner/activation edge, and map the registered Boolean result to RGB. Keep invalid output black.
5. Widen diagnostic count wiring to 8 bits without changing serialized diagnostic framing.
6. Add the testbench and independent Python oracle. Register `test_gpu_t1r_palette_pair.py` in `run_all_tests.py`. Add a narrow `TB_FILTER=spu_gpu_t1r_palette_pair_tb` source allowlist for the required GPU RTL dependencies if the current filtered source rules omit `hardware/rtl/gpu`; do not broaden other filtered runs.
7. Run the focused and compatibility commands in §5. Do not start synthesis/route until all focused checks pass.
8. Run the repository and mandatory Padé gates in their separate frozen campaigns in §6. Then run the separately budgeted T1r route campaign. Stop after each detached launcher reports `LAUNCHED`; interpret only the durable terminal marker and its `result.json`.

Keep new RTL and Python modules single-purpose and within the repository's 50–150 line Lithic guidance where practical. Do not refactor unrelated profiles.

## 5. Focused functional and compatibility checks

Required tests and exact commands:

```bash
python3 software/tests/test_gpu_t1r_palette_pair.py
TB_FILTER=spu_gpu_t1r_palette_pair_tb python3 run_all_tests.py
python3 software/tests/test_gpu_t1q_truth_table.py
python3 software/tests/test_gpu_t1p_predicate_bits.py
python3 software/tests/test_gpu_t1o_per_primitive_material.py
```

`test_gpu_t1r_palette_pair.py` must compile/run `spu_gpu_t1r_palette_pair_tb.v` against the exact required GPU RTL sources and independently check the four-lane discriminator. `run_all_tests.py` registration is required for full repository verification; the filtered run must execute the named testbench with the GPU dependency sources available.

The testbench/oracle must falsify all of these:

1. Both output colors are correct for all four winning primitive IDs using the frozen palette suffix.
2. All 16 truth tables produce the expected output for `{pred_u,pred_v}` values `00`, `01`, `10`, and `11`.
3. Per-lane table, selector, palette, winner, and valid-fragment state remain aligned across adjacent pixels, overlap winner changes, and candidate activation.
4. Invalid fragments remain black regardless of palette values.
5. An invalid truth-table byte `0x10` and an invalid palette byte `0x40` each prevent candidate commit, including `0x40` at payload index 185 (palette lane 3, the final payload byte). After each rejection, a complete valid packet commits and becomes active.
6. T1q still accepts its exact 182-byte payload with its existing `0x0F` truth-table validation and blue/yellow mapping. T1q must ignore no bytes and consume no T1r suffix.
7. T1P/T1O compatibility commands pass unchanged.
8. Assertions are falsifiable and compare computed expected outputs; no output is asserted against a constant or untoggled input.
9. The T1r profile is default-off, accepts the registered T1r parameter combination, and rejects T1r combined with incompatible T1P/T1Q or earlier material profiles. T1q remains default-off and its prior registered configuration remains accepted.

The focused-test campaign has one allowed invocation for each listed command, a 600-second maximum per command, and a 3,000-second cumulative budget across the direct T1r oracle, filtered Verilog triage, and three compatibility commands. Any command expected to exceed 60 seconds must use the detached runner with a new `build/` child, `--timeout 600`, and `--notify-desktop`; record its exact command and evidence path. A failed focused or compatibility check stops the campaign. No retry is included.

## 6. Detached repository and synthesis/route budgets

Each row is a separate one-attempt campaign. A launched attempt consumes its slot for every outcome, including unavailable results. No relaunch, timeout extension, clock change, alternate seed, or substitute command is authorized.

| Gate | Maximum attempts | Per-attempt timeout | Cumulative campaign budget |
|---|---:|---:|---:|
| Repository hygiene/regression | 1 | 1,800 s | 1,800 s |
| Mandatory Artix-7 100T Padé synthesis | 1 | 1,800 s | 1,800 s |
| T1r Artix-7 100T GPUVGA synthesis/place/route, seed 1 | 1 | 1,800 s | 1,800 s |

Repository gate:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261001/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Mandatory Padé synthesis gate:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261001/pade_synthesis/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all
```

T1r route gate, after the repository and Padé gates pass:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1r_palette_pair_20261001/build_seed1/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 \
    FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
    T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
    T1O_PER_PRIMITIVE_MATERIAL=0 T1P_PER_PRIMITIVE_PREDICATES=0 \
    T1Q_TRUTH_TABLE_MATERIAL=0 T1R_PALETTE_PAIR_MATERIAL=1 \
    A7_ARTIFACT_TAG=T1R_PALETTE_PAIR_MATERIAL_Q1 \
    bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
```

Route success requires exactly one durable `COMPLETE` marker, exit 0, required bitstream and route artifacts, and routed pixel clock at least `25.00 MHz`. `FAILED`, `TIMEOUT`, missing marker, missing artifacts, or lower timing is not a pass. Do not program the FPGA or send UART packets under Q1; prepare a separate hardware contract after route evidence is reviewed.

The expected T1r bitstream is `build/spu_a7_100t_GPUVGA_T1R_PALETTE_PAIR_MATERIAL_Q1.bit`. Require that bitstream plus the route JSON, FASM, nextpnr log, and timing evidence under the detached job evidence directory before interpreting the route gate.

## 7. Other mandatory gates

After focused tests pass, execute these exact commands once:

```bash
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
git diff --check
```

The full `bash tools/verify_repo.sh` gate remains mandatory and separately budgeted in §6. Mark any gate not launched or without a durable terminal marker `NOT RUN` or `UNAVAILABLE`; do not infer its result from elapsed time or logs alone.

## 8. Evidence state, stop conditions, and claims

| Evidence claim | Q1 starting state |
|---|---|
| T1r structural validity | NOT RUN |
| T1r functional simulation | NOT RUN |
| T1r repository gate | NOT RUN |
| T1r synthesis/place-and-route | NOT RUN |
| T1r board interface validation | NOT RUN |
| T1r silicon observation | NOT RUN |

- Halt on packet aliasing, wrong payload length, either validation window accepting a reserved-bit violation, active-state mutation after rejected input, output mismatch, selector/palette/winner skew, or T1q/T1P/T1O regression.
- Halt on vacuous assertions, test failure, repository-gate failure, Padé-gate failure, route failure, missing terminal evidence, missing required artifacts, or route timing below 25.00 MHz.
- Do not claim T1r silicon verification without a separate hardware contract and a specific entry in `docs/hardware_evidence.md`.
- Do not change T1q packet semantics, board clock constraints, timing target, or route timeout under this contract.
- A consumed or unavailable attempt does not authorize a retry. Renewed owner authorization is required for any further attempt or hardware action.
