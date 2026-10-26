# Engineering Contract: T1n Runtime Material Opcode

**Date:** 2026-09-27  
**Contract ID:** `GPU-T1N-RUNTIME-MATERIAL-OPCODE-2026-09-27`  
**Status:** `Q0 PASS; Q1 PASS; Q2 PASS; guard correction PASS; B1 PASS (43.68 MHz); H1 opcode-isolation PASS; broad photo/oracle shape agreement PASS (visual-only)`  
**Owner:** John Curley

## 0. Q0 decision

Q0 is an architectural and source-review phase only. It freezes the scene
record extension, opcode semantics, activation rule, and invalid-packet
handling. No RTL, testbench, fixture, synthesis, bitstream, or hardware changes
are authorized by Q0.

**Q0 result: PASS.** The current T1i payload has no reserved bits. T1n will
append one scene-wide opcode byte after the four existing T1i records. Existing
T1i/T1m scene layouts and wire lengths remain unchanged when T1n is disabled.
Q1 remains unauthorized pending owner approval.

## 1. Objective and boundary

Answer this question:

> Can one runtime-selected Boolean material operation be committed atomically
> with a prepared four-primitive scene and used by fragments from that active
> scene, without changing rasterization, depth, U/V interpolation, or the
> existing output pipeline?

T1n extends the existing T1m material operation set with a scene-wide runtime
selector. It does not add an instruction stream, shader program, per-primitive
or per-pixel opcode, register file, loop, texture memory, framebuffer, or
sampled texture path. The opcode is selected once per scene and applies to all
valid fragments of that active scene.

## 2. Frozen opcode and scene semantics

The one-byte `material_op` field has these encodings:

| Byte | Opcode | Result from registered winner-selected U/V predicates |
|---:|---|---|
| `0x00` | `PASS_U` | `selected_u_q[12]` |
| `0x01` | `PASS_V` | `selected_v_q[12]` |
| `0x02` | `XOR` | `selected_u_q[12] XOR selected_v_q[12]` |
| `0x03` | `AND` | `selected_u_q[12] AND selected_v_q[12]` |
| `0x04` | `OR` | `selected_u_q[12] OR selected_v_q[12]` |
| `0x05` | `NOT_U` | `NOT selected_u_q[12]` |
| `0x06..0xFF` | Invalid | Reject the completed candidate packet; never activate it |

Invalid fragments always render black. Valid fragments map result zero to blue
(`RGB=12'h00F`) and result one to yellow (`RGB=12'hFF0`), matching T1m so the
geometry silhouette remains visible.

For the Q1 transition oracle, preserve the existing A/B/C geometry and U/V
records and append these opcode bytes:

| Scene | Opcode | Return sequence |
|---|---|---|
| A | `PASS_U` (`0x00`) | Initial and final A use the identical packet |
| B | `PASS_V` (`0x01`) | Sent after A |
| C | `XOR` (`0x02`) | Sent after B |

The expected pixel result is always calculated from the independent oracle's
depth winner and that winner's U/V values, followed by the scene's opcode.
Q1 must confirm the frozen scenes produce distinguishing predicted output
patterns before implementation qualification proceeds. If an assignment does
not distinguish as intended, halt and request a contract amendment; do not
silently change opcodes or fixtures.

## 3. Frozen packet format and profile

Source review established that the current T1i record is 348 bits per lane:
252 geometry bits followed by six 16-bit U/V samples. Four records occupy all
1,392 T1i scene bits; there is no reserved field to reuse.

T1n therefore appends the opcode as a full byte:

```text
bits   [0:1391]  existing four T1i records, unchanged
bits [1392:1399]  scene-wide material_op byte
```

Bytes remain little-endian by scene bit position: the opcode is payload byte
174. The T1n transaction is exactly **175 payload bytes**, preceded by the
existing `A5` start byte, for **176 wire bytes total**. The existing T1i
transaction remains 174 payload bytes / 175 wire bytes. No runtime length
inference or UART framing change is introduced.

Q1 shall add a default-off compile-time selector:

```text
T1N_RUNTIME_MATERIAL=0|1, default 0
```

When enabled, it requires the prepared four-primitive T1i U/V profile,
`T1L_PIPELINE_PARTITION=1`, and `GPU_POST_WINNER_REG=1`. T1h scalar modes,
T1i diagnostic modes, T1j, T1k, T1l static-material selection, and T1m
compile-time ALU selection must be disabled. The existing T1l pipeline
partition legality check may be extended only to admit this exact T1n profile
tuple; existing legal profiles and behavior must remain unchanged.

With `T1N_RUNTIME_MATERIAL=0`, scene sizes, payload completion counts, fixtures,
and elaborated behavior for all legacy profiles remain unchanged.

## 4. Candidate/active state and atomic activation

The opcode is part of the same candidate and active scene generation as the
geometry and prepared U/V state:

```text
candidate_scene[1392 +: 8] -> candidate_material_op
active_scene[1392 +: 8]    -> active_material_op
```

The existing loader bank switch and prepared-scene activation remain the only
commit mechanism. `active_material_op` changes only on the same qualified
`activate_scene` event that activates geometry and prepared derived state:
the first `frame_start` after all four generation-matched preparation results
are ready. Fragment shading consumes only `active_material_op`; the candidate
opcode must have no effect on current active pixels.

The opcode must be sampled/aligned with the registered winner-selected U/V,
valid, and sync/active pipeline at the existing boundary. It must not create a
new pipeline stage or change one-pixel-per-clock throughput. The existing
`GPU_POST_WINNER_REG` remains after the final material color decision and
continues to delay RGB and video controls together.

The activation event occurs at the existing `frame_start` definition
(`vx==0 && vy==0`); Q0 does not claim a particular absolute frame number or
assume this event is in blanking. Q1 must test the exact edge relationship and
show that the first complete new-scene frame uses one coherent tuple:

```text
geometry + prepared U/V state + active_material_op + generation
```

There may be no partial-frame opcode change or pixel combining the outgoing
scene's U/V with the incoming scene's opcode.

## 5. Invalid-opcode rejection and recovery

The current loader raises `commit_pending` when an exact-length payload
completes and ignores incoming bytes until activation clears that flag. T1n
must not leave an invalid packet permanently pending. On receipt of the final
payload byte, if the appended opcode is outside `0x00..0x05`, the T1n loader
must reject the candidate before asserting `commit_pending`, clear its
receive/count state, and leave the active bank and active opcode unchanged.
The receiver must then accept a fresh `A5` transaction. A subsequent valid
packet overwrites the complete inactive bank before it can be committed.

No ACK, ready pin, UART protocol change, or altered host pacing is added. The
existing sender delay remains required after valid packets. Invalid-packet
recovery is verified through simulation-visible state and successful
subsequent valid activation.

## 6. Q1 scope and verification

Q1 was authorized on 2026-09-27. Implementation is limited to GPU scene
profile/loader integration and compile-time build-profile propagation for the
appended byte and active opcode, plus focused test/oracle code. It does not
change raster coverage, depth comparison/winner priority, U/V arithmetic,
activation timing, valid-scene loader semantics, existing fixtures, pacing, or
output-register behavior.

The independent reduced oracle shall run A→B→C→A and derive, independently of
DUT outputs:

1. coverage for all four lanes;
2. depth winner and winner identity;
3. that winner's interpolated U/V;
4. active scene opcode and Boolean result;
5. invalid-black gating, RGB, and video-control alignment.

It shall exercise all six valid opcode encodings and verify candidate
isolation, atomic generation-consistent activation, no partial-frame opcode
changes, initial-A/final-A equality, all four lanes winning, invalid-opcode
rejection, unchanged active output during rejection, and successful valid
recovery after an invalid packet. The invalid check must use the incoming final
`rx_byte` value at packet completion; the just-written nonblocking scene-bank
value is not yet visible in that same clock edge. Selector-off behavior must
match the existing T1m/T1l/T1i profiles exactly. Q1 must run the focused T1m,
T1l, T1k, T1j, T1i, T1h, and T1g regressions. No synthesis, P&R, fixture
generation, or FPGA programming is authorized in Q1.

Implemented files:

* `hardware/rtl/gpu/spu_scene_loader.v` — optional final-byte opcode
  validation. Invalid final bytes clear receive state without asserting
  `commit_pending` or switching the active bank.
* `hardware/rtl/gpu/spu_gpu_top.v` — default-off T1n profile, 1,400-bit scene
  and 175-byte payload, active opcode and generation state, and opcode capture
  alongside registered winner-selected U/V/valid/video controls.
* `hardware/boards/artix7/spu_a7_gpu_vga_top.v` and
  `hardware/boards/artix7/build_a7.sh` — profile propagation and legality
  checks.
* `software/tests/test_gpu_t1i_uv.py` — shared testbench support for the
  appended byte, per-pixel opcode/generation assertions, candidate isolation,
  and invalid packet checks.
* `software/tests/test_gpu_t1n_runtime_material.py` — independent reduced
  oracle and illegal-profile checks.
* `software/tests/test_gpu_top_integration.py` — include the existing four-way
  depth comparator dependency, which the full repository gate exposed as
  missing from this test's compile file list.

**T1n reduced oracle result: PASS.** The frozen A/B/C/A sequence
(`PASS_U`/`PASS_V`/`XOR`/`PASS_U`) and separate A/B/C/A trials for all six legal
opcodes matched 224,000 reduced-profile output pixels total. The oracle
independently derived coverage, depth winner, winner U/V, opcode result, and
RGB. Opcode and generation aligned with U/V on every checked pixel, including
the frame-start boundary samples; invalid fragments were black; every lane
won; return A matched initial A. An invalid opcode was rejected without
changing the active scene/opcode, loader active-bank selection, active
generation, or prepared-scene candidate generation, and the following valid
return-A packet activated successfully. The five illegal-profile checks also
rejected as expected. No synthesis or hardware operation was run.

**Q1 focused regression result: PASS.** The detached run completed with exit
status 0 in 238 seconds. T1n, T1m, T1l, T1k, T1j, T1i, T1h, and T1g focused
tests passed, as did `bash -n hardware/boards/artix7/build_a7.sh`. Evidence is
in `build/gpu/t1n_runtime_material_20260927/q1_focused_regressions/run_01`.
Q1 is closed. The owner-authorized conditional Q2 production oracle is now
the active gate; synthesis and hardware remain unauthorized.

Q2 command:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1n_runtime_material_20260927/q2_production_oracle/run_01 \
  --timeout 1800 --notify-desktop -- \
  python3 software/tests/test_gpu_t1n_runtime_material.py --production
```

Q2 compares all 1,228,800 640×480 A/B/C/A pixels under the frozen scene
opcode assignment. B1 is not authorized by Q2; a separate owner decision is
required after the production oracle passes.

**Q2 result (2026-09-27): PASS.** The independent oracle matched all
1,228,800 production pixels for frozen `A(PASS_U) → B(PASS_V) → C(XOR) →
A(PASS_U)`, including invalid-black behavior, all four winner lanes, opcode
and generation alignment, and exact return-A equality. The managed foreground
fallback completed with exit status 0 because the user systemd manager was
unavailable. Evidence is in
`build/gpu/t1n_runtime_material_20260927/q2_production_oracle/foreground_fallback_02/`.

The first Q2 invocation is recorded separately in
`foreground_fallback_01/`: the test harness's internal 60-second `vvp`
timeout expired before it produced an oracle verdict. The production-only
harness timeout was raised to 1,500 seconds; no RTL, scene, opcode, or oracle
semantics changed between attempts. The completed retry produced the Q2 PASS
above. No synthesis, P&R, bitstream generation, or FPGA programming was run.

**Repository gate result: NOT GREEN.** `bash tools/verify_repo.sh` completed
with exit status 1: 235 tests passed and three checks failed. The initial
root-hygiene check found `tmp_spu_t1d_board_transaction_tb.vvp`; the Verilog
suite also timed out in the known `spu_t1d_board_transaction_tb.v` and failed
its first `test_gpu_top_integration.py` compile because that test omitted
`spu_depth_compare4.v`. The missing test dependency was added and the isolated
integration test then passed (115,198 checked pixels, zero mismatches). The
full gate was not rerun; repository-wide qualification remains open. The
temporary root file was absent after the gate completed. This gate debt does
not alter the focused Q1 or production Q2 oracle results.

## 9. B1 bounded Artix build

The owner initially authorized one B1 attempt after Q2 passed. That first
attempt was consumed by a build-flow rejection before synthesis. The owner
subsequently authorized one narrow build-flow correction and one retry: one
Artix-7 100T attempt, one 3,600-second timeout, and a 3,600-second cumulative
limit. Qualification requires final routed `clk_pixel` Fmax >=25.00 MHz. The
retry is consumed regardless of result. A successful shell exit or
`COMPLETE` marker alone is insufficient; the final routed timing report is
authoritative. If timing is below threshold, retain the reports, do not flash,
and stop. If it passes, the exact bitstream becomes eligible for a separately
authorized H1 visual check; B1 does not authorize programming the board.

Frozen B1 command:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1n_runtime_material_20260927/b1_seed1/run_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_MATERIAL_OP=0 T1L_PIPELINE_PARTITION=1 \
      T1M_FRAGMENT_ALU=0 T1M_ALU_OP=0 T1N_RUNTIME_MATERIAL=1 \
      GPU_POST_WINNER_REG=1 \
      A7_ARTIFACT_TAG=T1N_RUNTIME_MATERIAL_B1_S1 \
      bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

The T1n B1 artifact tag is intended only for the frozen T1n profile and seed 1.

**B1 attempt 1 result (2026-09-27): FAIL — build-flow rejection.** The first authorized
attempt launched as unit `spu-run_01-20260927T102306Z-860110` and produced the
terminal marker `FAILED`, exit 1, duration 0 seconds. The build script stopped
at its artifact-tag validation with `Invalid A7_ARTIFACT_TAG:
T1N_RUNTIME_MATERIAL_B1_S1`. No synthesis, route, timing report, or bitstream
was produced. This is not a timing verdict. Evidence is in
`build/gpu/t1n_runtime_material_20260927/b1_seed1/run_01/`. The initial budget
is exhausted. After renewed owner authorization, source inspection found the
T1n tag in later profile/bitstream allowlists but missing from the central
artifact-tag validation case. The sole correction adds that tag to the central
case and enforces seed 1 and the frozen registered T1n profile; no RTL or
datapath behavior changed. One retry is authorized under a renewed 3,600-second
budget.

Retry command and fresh evidence directory:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1n_runtime_material_20260927/b1_seed1_retry/run_01 \
  --timeout 3600 --notify-desktop -- \
  env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 FOUR_PRIMITIVE_SCENE=1 \
      T1I_UV_SCENE=1 T1L_MATERIAL_OP=0 T1L_PIPELINE_PARTITION=1 \
      T1M_FRAGMENT_ALU=0 T1M_ALU_OP=0 T1N_RUNTIME_MATERIAL=1 \
      GPU_POST_WINNER_REG=1 \
      A7_ARTIFACT_TAG=T1N_RUNTIME_MATERIAL_B1_S1 \
      bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all
```

**B1 retry launched (2026-09-27):** unit
`spu-run_01-20260927T103115Z-861532`; evidence directory
`build/gpu/t1n_runtime_material_20260927/b1_seed1_retry/run_01/`. It produced
exactly one terminal marker, `FAILED`, exit 1, duration 0 seconds. The script
rejected the T1n artifact at the T1I U/V profile guard because that guard's
registered-output branch accepts only the earlier T1i post-winner diagnostic
tag. No synthesis, route, timing report, or bitstream was produced. This is a
second build-flow failure, not a timing verdict. The renewed retry budget is
exhausted; no further build or source correction is authorized under it.

**Guard-only correction tranche (2026-09-28): PASS.** The T1i artifact-tag
guard now admits `T1N_RUNTIME_MATERIAL_B1_S1` only as an additional legal tag
for the registered T1n profile. No RTL, packet, material, activation,
interpolation, or pipeline files changed in this tranche. `bash -n` and
`git diff --check` passed. Profile-only invocations stopped at the deliberate
unknown-step boundary before synthesis: legal T1i/T1l/T1m/T1n profiles passed
their guards; representative invalid registered T1i tag, wrong T1l seed,
wrong T1m opcode, and T1n/static-material coexistence cases were rejected.

The owner authorized a fresh B1 budget after those checks: one Artix-7 100T
attempt, a 3,600-second timeout, and a 3,600-second cumulative limit, with the
same final routed `clk_pixel` threshold of >=25.00 MHz. A guard rejection is
build-flow FAIL; a completed route below threshold is timing FAIL. Neither
case authorizes flashing. A timing PASS makes the exact bitstream eligible
only for a separately authorized H1 visual check.

The third attempt uses the frozen command and profile above with this fresh
evidence directory:

```text
build/gpu/t1n_runtime_material_20260927/b1_seed1_guardfix/run_01/
```

**B1 attempt 3 launched (2026-09-28):** unit
`spu-run_01-20260927T110509Z-871098`; evidence directory
`build/gpu/t1n_runtime_material_20260927/b1_seed1_guardfix/run_01/`.
It produced exactly one terminal marker, `COMPLETE`, exit 0, in 970 seconds.
The final routed timing report records `clk_pixel` Fmax **43.68 MHz**, passing
the 25.00 MHz gate. The bitstream is
`build/spu_a7_100t_GPUVGA_T1N_RUNTIME_MATERIAL_B1_S1.bit`, SHA-256
`7b3bf1ada1b471d34bb3db76fc2964b954a84b816119fe533d58fa49246f85bc`.
Detailed post-route evidence is in
`build/metrics/artix7_100t_GPUVGA_T1N_RUNTIME_MATERIAL_B1_S1.json` and the
detached run directory above. B1 is PASS. The exact image is eligible for a
separately authorized H1 visual check; it has not been programmed.

The single-attempt budget is consumed. No additional source correction or
build is authorized by this budget.

**SRAM programming (2026-09-28): PASS.** After owner authorization, the exact
T1n bitstream above was loaded with
`openFPGALoader -c dirtyJtag --freq 1000000
build/spu_a7_100t_GPUVGA_T1N_RUNTIME_MATERIAL_B1_S1.bit`. The programmer
completed at 100% and reported `ISC_DONE=1` and `DONE=1`. This records image
loading only; no visual behavior has yet been reported, so H1 remains pending.

**H1 transport (2026-09-28): PASS.** The frozen
runtime-opcode sequence `A(PASS_U) -> B(PASS_V) -> C(XOR) -> A(PASS_U)` was
replayed over the stable CH340 by-id UART at 115200 8N1 using
`tools/send_gpu_t1n_sequence.py`. Each transaction contained the frozen
175-byte T1i wire fixture followed by its one-byte T1n opcode, for 176 wire
bytes total. All four writes completed `tcdrain`; start-to-start gaps were
5011.503685 ms, 5011.601794 ms, and 5011.538406 ms. The final active scene is
A. Transcript:
`build/gpu/t1n_runtime_material_20260927/h1/sequence_02.json`, SHA-256
`d5408941358dd2d3e7c6447328384bb2ea907627d5f81f8e4f2880a45438bebc`.

**H1 result: transition PASS (operator-observed, visual-only); checkerboard
fidelity INCONCLUSIVE.** The operator confirmed that the displayed image
changed through the bounded sequence and returned to A. The operator also
reported that the checkerboards were distorted. No photo or captured pixel
stream was supplied. This establishes visible runtime scene/opcode response
and return behavior only. It does not establish correct physical opcode
decoding, exact per-pixel material output, or clean checkerboard geometry;
those exact results remain simulation-oracle claims. The distortion is
retained as an observed limitation and is not, by itself, evidence for a
raster or material RTL correction.

**H1 non-vacuity correction:** The A/B/C/A replay changes geometry and U/V
records together with the opcode. Its visible transitions therefore establish
scene/packet response but cannot isolate physical opcode response. A follow-up
replay held the complete 175-byte A fixture constant and changed only the final
opcode byte: `PASS_U -> PASS_V -> XOR -> PASS_U`. All four 176-byte writes
completed `tcdrain`; start-to-start gaps were 5011.656113 ms, 5011.684550 ms,
and 5011.766513 ms. Transcript:
`build/gpu/t1n_runtime_material_20260927/h1/opcode_isolation_01.json`, SHA-256
`403232b4cfc63517eb6d91e7e03e662111bf4d1f20033ef943b76dd5cc9b6320`.
The operator confirmed three visibly different material patterns for
`PASS_U`, `PASS_V`, and `XOR`, followed by return to the first `PASS_U`
pattern. **H1 opcode-isolation result: PASS (operator-observed, visual-only).**
This establishes physical response to the isolated runtime opcode byte and
return behavior. Exact pixel correspondence remains a simulation-oracle claim,
and the reported checkerboard distortion required the photo/oracle comparison
below. The final `PASS_U` return state is photographed in
`docs/bench_captures/t1n_h1_2026-09-28/IMG_1774.jpeg`, SHA-256
`5d27b215fc810b102aa09b0a931e606ec2e374bafa48ea2f348aac94807e0780`.
The photo shows a blue/yellow triangular pattern against black. It records the
final displayed state only and does not independently establish the preceding
opcode transitions or per-pixel correspondence.

The same fixed A scene was then sent once with only the opcode changed to
`PASS_V`. Transport transcript:
`build/gpu/t1n_runtime_material_20260927/h1/photo_pass_v_01.json`, SHA-256
`444a4f8d04235260ffd870d8e45b2aef46013a3097674f5d822644f1203383db`.
The resulting state is photographed in
`docs/bench_captures/t1n_h1_2026-09-28/IMG_1775.jpeg`, SHA-256
`ca35f268d835939485466c7cb3fc846d7a96a69b213aee10bc15e0fdd72ba065`.
It shows a visibly different blue/yellow partition within the comparable
triangle silhouette and screen position. A subsequent one-packet `XOR` write
completed; its transcript is
`build/gpu/t1n_runtime_material_20260927/h1/photo_xor_01.json`, SHA-256
`6e8fa8e71eaed1fba1dd3662e2cc064312c0ff199a3dc3e6d33b9f4fd8c2150c`.
The matching state is photographed in
`docs/bench_captures/t1n_h1_2026-09-28/IMG_1776.jpeg`, SHA-256
`3cbab9b04abab6a79c92270ec1c6e11768c99c85e706c1d34fdf3dff4d762489`.
It shows a third visibly distinct blue/yellow partition with the same overall
triangular scene. The board was then returned to fixed-scene `PASS_U`; the
write completed `tcdrain` and is recorded in
`build/gpu/t1n_runtime_material_20260927/h1/photo_return_pass_u_01.json`,
SHA-256
`5e118815bf787aae327bbbf94cdce4f551599f32f8a6838649190c994d425392`.
Together, the three photos directly document visually distinct physical output
for the three isolated opcode values. They do not establish exact pixel-level
agreement with the oracle.

**Photo/oracle shape comparison: PASS (visual-only).** Independent 640x480
oracle renders for the identical A fixture and each opcode are archived beside
the photos:

* `oracle_fixed_a_pass_u.png`, SHA-256
  `8dc38d82628121a057a6910871af674cda0d3b6840dbc94bac6b2ea3302f2200`;
* `oracle_fixed_a_pass_v.png`, SHA-256
  `27771b8bc78d8d538132a3fcfad0e4d406e6049a30190ba926535e8bbc3fd903`;
* `oracle_fixed_a_xor.png`, SHA-256
  `109278920c52f69d897b69597d2b92512544625856ce45d91570600a75530923`.

All are under `docs/bench_captures/t1n_h1_2026-09-28/`. Each photo has the
same broad blue/yellow region topology as its corresponding oracle render,
allowing for camera perspective, crop, and display photography. The initially
reported “distorted checkerboards” are the expected coarse regions produced by
testing interpolated U/V bit 12; this fixed-scene sequence does not implement a
regular square-grid material. This resolves the distortion concern at the
broad visual-shape level. It does not establish exact physical pixel equality.

## 7. Q0 source-review findings and stop conditions

Reviewed source:

* `hardware/rtl/gpu/spu_gpu_top.v` — current profile sizes, loader hookup,
  activation signal, T1m operator path, and post-winner output register.
* `hardware/rtl/gpu/spu_scene_loader.v` — exact-length byte receive, bank
  selection, and `commit_pending` busy behavior.
* `hardware/rtl/gpu/spu_scene_profile_unpack.v` — complete T1i record field
  use and byte/bit layout.
* `hardware/rtl/gpu/spu_prepared_scene_control4.v` — generation-matched
  four-lane preparation and frame-start activation rule.

Q0 stops before implementation. Halt Q1 if the appended-byte encoding cannot
preserve all legacy profile behavior, if invalid-packet rejection cannot
recover without changing valid-packet semantics, or if the opcode cannot be
aligned atomically with the existing registered U/V and video-control path.
Any such finding requires a contract amendment before RTL work.

## 8. Evidence debt

The historical repository-wide gate timeout/failure remains separate and is
not waived by T1n. T1m's simulation, routed timing, and operator-observed
hardware results retain their existing evidence classifications; T1n makes no
additional silicon claim until its own authorized B1/H1 sequence is complete.
