# Engineering Contract: T1p Per-Primitive Runtime Predicate Bits

**Date:** 2026-09-28  
**Contract ID:** `GPU-T1P-PER-PRIMITIVE-PREDICATE-BITS-2026-09-28`  
**Status:** `Q0 PASS; Q1 FOCUSED PASS; Q1 REPOSITORY GATE PASS; Q2 PRODUCTION ORACLE PASS; B1 ROUTE/PACK PASS; SRAM LOAD PASS; H1 UART TRANSPORT PASS; SCALED H1 VISUAL PASS (OPERATOR-OBSERVED); H1 RENEWED REPOSITORY GATE PASS`  
**Owner:** John Curley  
**Spec Author:** Codex  
**Halt-and-Flag Implementer:** Codex  
**Integration Auditor:** `tools/verify_repo.sh` plus owner evidence review

## 0. Q0 commands and boundary

Run from the repository root:

```bash
sed -n '1,125p' hardware/rtl/gpu/spu_scene_loader.v
sed -n '225,360p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '945,1110p' hardware/rtl/gpu/spu_gpu_top.v
sed -n '1,120p' hardware/rtl/gpu/spu_material_op_select4.v
sed -n '1,120p' hardware/rtl/gpu/spu_scene_profile_unpack.v
sed -n '1,115p' software/tests/test_gpu_t1o_per_primitive_material.py
git diff --check
```

Q0 is source review and oracle-discriminator selection only. Do not edit RTL,
fixtures, loader behavior, build profiles, or tests under this draft. Q1,
repository-gate retries, synthesis, place-and-route, bitstream generation,
FPGA programming, and UART hardware transmission require separate owner
authorization.

## 1. Objective

Answer this question:

> Can each depth-winning primitive select its own U and V predicate bit,
> atomically with its runtime material opcode, while preserving the existing
> six Boolean operations and pixel/control alignment?

T1o fixes both predicates at `selected_u_q[12]` and `selected_v_q[12]`.
T1p proposes one runtime parameter byte for each primitive. The low nibble
selects U bit `0..15`; the high nibble selects V bit `0..15`. The existing
winner-selected opcode then acts on those two predicates. All 256 parameter
byte values are legal; the six opcode encodings and invalid-opcode rule stay
unchanged.

Exclude texture memory, color parameters, per-pixel parameters, instruction
streams, shader programs, register files, loops, and new Boolean operations.

## 2. Proposed packet and activation contract

Preserve the T1i four-primitive geometry/U/V bytes and T1o opcode bytes:

| Scene bits | Payload bytes | Wire bytes | Meaning |
|---:|---:|---:|---|
| `0:1391` | `0:173` | `1:174` | Existing T1i geometry/U/V |
| `1392:1423` | `174:177` | `175:178` | T1o material opcodes, primitives 0..3 |
| `1424:1455` | `178:181` | `179:182` | T1p predicate selector bytes, primitives 0..3 |

The proposed T1p profile is 1,456 scene bits, 182 payload bytes, and 183
wire bytes including `A5`. The current eight-bit payload counter reaches
byte 181. Existing packet lengths and layouts must stay exact when T1p is
disabled. Q0 must confirm the profile guard and active/candidate bank rules
before this layout becomes frozen.

Commit the complete opcode and selector tuples with geometry/U/V at the
existing `activate_scene` event. On the activation edge, the displayed
fragment must use the winning primitive's candidate tuple; later fragments
use the active tuple. Select both opcode and U/V bit indices with the exact
`partition_winner_id` that selects the winner U/V values. Capture the selected
opcode and both indices on the same edge as selected U/V, valid, and video
controls. Keep `GPU_POST_WINNER_REG` and the current output cycle.

The Boolean inputs become `selected_u_q[u_bit_q]` and
`selected_v_q[v_bit_q]`. Preserve the six T1o truth tables, blue/yellow RGB
mapping, black invalid fragments, depth priority, and frame-start activation.
Validate opcodes in the explicit four-byte payload window `174..177` only.
Accumulate any invalid opcode across that window. Packet completion remains at
byte `181`; there, reject the entire candidate if any opcode was invalid.
Selector bytes `178..181` are never range-validated: all 256 values remain
legal. Rejection leaves the active scene, opcode tuple, selector tuple, and
generation unchanged and permits a fresh valid transaction afterward.
Preserve T1n final-byte validation and T1o trailing-four-byte validation
bit-for-bit when T1p is disabled.

## 3. Q0 halt-and-flag review

Confirm all of the following before freezing Q1:

1. The proposed byte order maps to primitive indices 0..3 after the loader's
   shift-based assembly and retains T1o opcode validation at bytes 174..177.
2. The current selected U/V widths include bits 0..15 at the registered ALU
   input; verify signed indexing does not change bit meaning.
3. The selected parameter tuple can be captured beside the opcode and U/V
   without an added stage or an activation-edge generation mismatch.
4. The two variable bit-select muxes are a bounded combinational addition;
   Q1 may test their routed cost, but must not hide a timing failure with a new
   stage under this contract.
5. The production Scene A oracle has overlapping winners whose selected bit
   pairs produce non-vacuous differences for a proposed A/B/C/A tuple set.
   Freeze exact tuples and per-lane distinction counts before Q1 begins.

If any check fails, halt Q0 and propose the smallest correction. Do not
silently change the packet layout, timing, or predicate semantics.

**Q0 check 1 finding, corrected by owner decision:** The existing loader's
`VALIDATE_TRAILING_BYTES=4` validates the final four payload positions using
`payload_count >= PAYLOAD_BYTES - 4`. At the proposed T1p length of 182 bytes,
that checks selector bytes 178..181 against `8'h05` and leaves opcode bytes
174..177 unchecked. All 256 selector byte values must be legal, so the
current loader configuration contradicts the proposed packet contract.
Increasing the trailing count to eight would also reject legal selectors.

**Frozen Q0 correction:** Keep the proposed byte order and validate only the
explicit opcode window 174..177. Accumulate invalid state until packet
completion at byte 181; reject the complete candidate without changing active
state, then allow a fresh valid transaction. Preserve T1n/T1o validation when
T1p is disabled. The owner authorized this contract correction and Q0 checks
2..5 only. The loader change belongs to a separately authorized Q1.
After 182 received payload bytes, the loader's shift assembly places byte
`i` at scene bits `[8*i +: 8]`: selector bytes 178..181 therefore map to
bits 1424..1455 and primitives 0..3 in order. The eight-bit count covers
indices through 181. The existing T1o profile guards are specific to its
178-byte profile; Q1 must add a separate, default-off T1p profile guard and
leave T1o's packet length and validation path unchanged.

**Q0 check 2 — PASS (source review):** `selected_u_q` and `selected_v_q` are
both signed 56-bit registers. Nibble values 0..15 index physical bits within
those registers. Signedness does not change the meaning of an indexed bit.
The six existing operations currently read bit 12, which the proposed A
selector reproduces exactly.

**Q0 check 3 — PASS (architecture review):** `partition_winner_id` already
selects both winner U/V values and the T1o opcode. The selected opcode and
winner U/V are registered on the same `clk_pixel` edge. The proposed two
selected indices can use that same winner and edge, selecting candidate
bytes on `activate_scene` and active bytes otherwise. `activate_scene` is
qualified by `commit_pending`, matching prepared generations, and
`frame_start`; the loader, prepared state, opcode tuple, and scene-generation
bit advance on that edge. Q1 must prove the new selector tuple follows this
architecture in simulation; Q0 makes no implemented-alignment claim.

**Q0 check 4 — PASS as a bounded timing-risk review:** A four-bit U index and
four-bit V index each imply up to a 16:1 bit select from the registered U/V
values. The four-lane selector-byte winner mux also feeds the existing
winner-to-register edge. T1o's seed-1 post-route pixel-clock Fmax was
35.42 MHz against a 25.00 MHz target, but that result does not predict T1p
timing. Q1 must retain the current pipeline and measure T1p route timing
separately before any hardware qualification.

**Q0 check 5 — PASS (independent production Scene A oracle):** Keep the frozen
T1i production Scene A geometry/U/V fixture fixed in all four frames. Hold
the material opcode tuple at `[2,2,2,2]` (`XOR`) so both U and V selector
nibbles affect every winning lane; focused Q1 cases must separately exercise
the full six-operation opcode set. Freeze selector bytes in primitive order:

| Frame | Selector bytes 0..3 | U bit indices 0..3 | V bit indices 0..3 |
|---|---|---|---|
| A | `[CC, CC, CC, CC]` | `[12,12,12,12]` | `[12,12,12,12]` |
| B | `[89, 8E, AA, D9]` | `[9,14,10,9]` | `[8,8,10,13]` |
| C | `[BD, D8, 8E, F8]` | `[13,8,14,8]` | `[11,13,8,15]` |
| Return A | `[CC, CC, CC, CC]` | `[12,12,12,12]` | `[12,12,12,12]` |

Each lane wins in the production frame, and the fixed geometry has 115
in-frame winner boundaries. Counts below compare the XOR predicate result
only on pixels actually won by that lane:

| Winning lane | Won pixels | A→B differing | B→C differing | C→A differing | Minimum |
|---:|---:|---:|---:|---:|---:|
| 0 | 773 | 383 | 386 | 425 | 383 |
| 1 | 742 | 392 | 373 | 383 | 373 |
| 2 | 488 | 271 | 259 | 246 | 246 |
| 3 | 438 | 223 | 243 | 224 | 223 |

Across the full frame, A→B, B→C, and C→A differ on 1,269, 1,261, and
1,278 winning pixels respectively. Holding the other selector nibble at
its A value, both the U-only and V-only changes are non-vacuous for every
lane in B and C; the smallest such count is 215. Return A repeats the exact
initial selector tuple. These counts come from the existing independent
coverage/depth/U/V oracle applied to the frozen production Scene A fixture;
no RTL simulation or test file was changed during Q0.

## 4. Owner-authorized Q1 scope and evidence gates

An authorized Q1 should test the four selector bytes at every primitive
index, including selectors 0 and 15; fixed-geometry A/B/C/A parameter
changes; overlapping winner boundaries; opcode/parameter pairing; atomic
activation; invalid-opcode rejection and recovery; and bit-for-bit T1o and
legacy behavior when T1p is disabled. Derive expected pixels independently
through coverage, depth winner, winner U/V, winner opcode, selected U/V bit
indices, Boolean operation, RGB, and output alignment. Require exact
return-A equality.

Run the focused T1o through T1i regressions before the repository gate. Any
repository gate, production oracle, synthesis, route, or hardware campaign
must have a separate owner-frozen attempt count and wall-clock budget. Route
qualification must again name a pixel-clock threshold before launch.

Q1 implemented the explicit opcode window in `spu_scene_loader.v`, the
51-line `spu_material_predicate_select4.v` register/mux, default-off T1p
selection and variable bit picks in `spu_gpu_top.v`, board parameter and
build-profile propagation, both GPU VGA source manifests, shared testbench
support, and the independent reduced oracle in
`software/tests/test_gpu_t1p_predicate_bits.py`. No fixture was edited.

The new reduced oracle passed locally over 96,000 pixels across three
four-frame cases: the frozen XOR selector discriminator; endpoint selector
bytes `00` and `FF` at every primitive; and mixed opcode/selector cases
covering all six operations at every lane. Each run checks candidate
isolation, same-edge registered U/V/opcode/selector/control alignment,
invalid opcode rejection at each of bytes 174..177 after a legal `FF`
selector tail, valid recovery, and exact return A. Illegal-profile
elaboration checks passed. The board's legal T1p profile reached its
deliberate unknown-step boundary without launching synthesis.

Run the remaining Q1 focused gate through a fresh detached evidence
directory:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1p_predicate_bits_20260928/focused_q1/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/run_gpu_t1p_q1.sh
```

Stop after this focused gate. Repository-wide verification, production
oracle, synthesis, route, bitstream, FPGA programming, and hardware
transmission remain unauthorized.

**Q1 focused result (2026-09-28): PASS.** The detached runner recorded
`COMPLETE`, exit code 0, in 287 seconds at
`build/gpu/t1p_predicate_bits_20260928/focused_q1/run_01`. The T1p reduced
independent oracle passed 96,000 pixels across four winning lanes, all six
operations and selector endpoint bytes at every lane, same-edge alignment,
atomic A/B/C/A activation, four invalid-opcode rejection/recovery cases,
and exact return A. Focused T1o, T1n, T1m, T1l, T1k, T1j checker and
visibility, T1i U/V, and GPU top integration regressions passed. Shell
syntax, Python compile, and `git diff --check` passed. No repository-wide
gate, production-resolution T1p run, synthesis, route, bitstream, or
hardware step was launched.

## 5. Evidence classification

| Claim | Q0 status |
|---|---|
| Structural review | Q0 PASS: explicit opcode validation window 174..177 frozen; signed 56-bit U/V bits 0..15 accessible; same-edge tuple architecture identified |
| Production discriminator | Q0 PASS: fixed XOR opcodes, A/B/C/A selector tuples above; minimum per-lane pairwise distinction 223 winning pixels |
| Functional simulation | Q1 focused PASS: 96,000 T1p reduced-oracle pixels and T1o→T1i/GPU integration regressions |
| Repository gate | NOT RUN for T1p |
| Synthesis and place-and-route | NOT RUN |
| Interface validation | NOT RUN |
| Silicon observation | NOT RUN |

T1o's simulation, routed build, and operator-observed visual response are
recorded in `docs/hardware_evidence.md` §3.23. They do not establish T1p
parameter behavior.

## 6. Qualification preflight and proposed bounded sequence

**Preflight (2026-09-28):** Q1's detached evidence has exactly one `COMPLETE`
marker, exit 0, duration 287 seconds. Root scratch-file hygiene,
`bash -n hardware/boards/artix7/build_a7.sh`, `bash -n
tools/run_detached_job.sh`, and `git diff --check` passed. Both GPU VGA
synthesis manifests read `spu_material_predicate_select4.v`; the T1p seed-1
profile guard is present. The user systemd manager is available. Fresh
`repo_gate/run_01` and `q2_production_oracle/run_01` evidence paths are absent.
No qualification job has launched.

The T1p oracle currently runs only 80×100 reduced frames. A Q2
`--production` mode is required after a passing repository gate. It must
keep production Scene A geometry/U/V fixed, opcode tuple `[2,2,2,2]`, and
the Q0 selector A/B/C/return-A tuples above; configure the existing testbench
for 640×480 active pixels and the standard VGA porches; compare exactly
1,228,800 fragments through the independent winner/U/V/opcode/selector/RGB
oracle; require every lane to win, non-vacuous B/C differences, and exact
return-A equality. The reduced default behavior must remain unchanged.

**Owner-authorized gate freeze:** one detached attempt,
1,800 seconds per attempt and cumulative, consumed on pass, failure,
timeout, interruption, or infrastructure error. Run the mandatory gate first:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1p_predicate_bits_20260928/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Interpret only the terminal marker and `result.json`. If the gate does not
pass, halt without Q2 or a retry. If it passes, add and statically check the
T1p test-only `--production` mode before the separately budgeted Q2 run.

**Repository-gate result (2026-09-28): PASS.** Exactly one terminal marker,
`COMPLETE`, and `result.json` report exit 0 after 864 seconds at
`build/gpu/t1p_predicate_bits_20260928/repo_gate/run_01`. The gate reported
237 total passes and zero failures. The sole gate attempt is consumed; the
conditional one-attempt Q2 budget is now eligible.

**Owner-authorized conditional Q2 freeze:** one detached
attempt, 1,800 seconds per attempt and cumulative, consumed on any outcome.
After a passing gate and Q2 test preflight, run:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1p_predicate_bits_20260928/q2_production_oracle/run_01 \
  --timeout 1800 --notify-desktop -- \
  python3 software/tests/test_gpu_t1p_predicate_bits.py --production
```

**Q2 test-only preflight (2026-09-29):** Added `--production` to the independent
T1p oracle without changing its reduced default, RTL, packet, fixture, or
build profile. The mode selects only frozen XOR A/B/C/return-A selector tuples,
sets 640×480 active timing, expects 307,200 comparisons in each of four
frames, and requires every lane, the invalid-opcode rejection markers,
non-vacuous B/C differences, and exact return-A RGB equality. Python compile,
`--help`, frozen layout/discriminator checks, and `git diff --check` passed.
The fresh Q2 evidence path is absent. No Q2 attempt has yet launched.

**Q2 production result (2026-09-29): PASS.** The one authorized detached
attempt at `build/gpu/t1p_predicate_bits_20260928/q2_production_oracle/run_01`
has exactly one terminal marker, `COMPLETE`. Its `result.json` reports exit 0
after 319 seconds. The independent oracle checked 1,228,800 pixels across
four 640×480 frames with frozen XOR A/B/C/return-A selector tuples and exact
return-A equality. This is functional simulation evidence, not a routed GPU
build or silicon observation. The Q2 attempt budget is consumed.

If Q2 fails or times out, retain its evidence and halt. Synthesis,
place-and-route, bitstream generation, FPGA programming, and UART transport
remain separate steps. Their attempts, budgets, exact profile, and routed
25.00 MHz `clk_pixel` pass threshold must be frozen before launch.

## 7. Owner-authorized B1 Artix-7 build freeze (2026-09-29)

Q2 passed. The owner authorized the GPU build. Freeze one seed-1 Artix-7
100T `gpuvga all` attempt (synthesis, route, and pack), 1,800 seconds per
attempt and 1,800 seconds cumulative. The attempt is consumed on any outcome;
do not retry, alter the seed, extend the timeout, or substitute a profile
without renewed owner authorization. Require a routed `clk_pixel` Fmax of
at least **25.00 MHz** and a clean 25 MHz system-clock route. A build exit 0
alone does not replace the post-route metrics check.

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1p_predicate_bits_20260928/build_seed1/run_01 \
  --timeout 1800 --notify-desktop -- \
  env A7_SEED=1 A7_FREQ=25 GPU_T1D_UART=1 \
    FOUR_PRIMITIVE_SCENE=1 T1I_UV_SCENE=1 \
    T1L_PIPELINE_PARTITION=1 GPU_POST_WINNER_REG=1 \
    T1O_PER_PRIMITIVE_MATERIAL=0 T1P_PER_PRIMITIVE_PREDICATES=1 \
    A7_ARTIFACT_TAG=T1P_PER_PRIMITIVE_PREDICATES_Q1 \
    bash hardware/boards/artix7/build_a7.sh 100t gpuvga all
```

Preflight: `bash -n` for the build script and `git diff --check` passed;
the T1p JSON, bitstream, and build evidence directory were absent. The
T1p profile guard requires prepared four-lane T1i, pipeline partition,
post-winner register, runtime UART, and disables competing material modes.
The expected output base is
`build/spu_a7_100t_GPUVGA_T1P_PER_PRIMITIVE_PREDICATES_Q1`.
Interpret only a durable `COMPLETE`, `FAILED`, or `TIMEOUT` marker with
`result.json` in a later session. Programming and UART transport are not
part of this build authorization.

**B1 build result (2026-09-29): PASS.** The sole detached attempt at
`build/gpu/t1p_predicate_bits_20260928/build_seed1/run_01` has exactly one
terminal marker, `COMPLETE`. `result.json` records exit 0 in 1,378 seconds.
The seed-1 Artix-7 100T `gpuvga all` command completed synthesis, route, and
pack. Post-route metrics at
`build/metrics/artix7_100t_GPUVGA_T1P_PER_PRIMITIVE_PREDICATES_Q1.json`
report `clk_pixel` **31.23 MHz** against the frozen **25.00 MHz** threshold
and `sys_clk` **166.09 MHz** against 25.00 MHz, both PASS. The routed design
uses 43,648 SLICE_LUTX, 16,670 SLICE_FFX, and 6 DSP48E1. The packed
`build/spu_a7_100t_GPUVGA_T1P_PER_PRIMITIVE_PREDICATES_Q1.bit` has SHA-256
`fe351b04a9f2d2e8b00fe49b9f84c20231f2d905d9c6dcc746c0b7f0347798e9`.
This establishes build and timing only; no T1p programming, UART transport,
or displayed behavior has been measured.

## 8. Owner-authorized SRAM load (2026-09-29)

The owner separately authorized loading T1p into FPGA SRAM. The input
bitstream SHA-256 matched the B1 record above. Read-only DirtyJTAG detection
reported one Xilinx Artix-7 100T (`xc7a100`, IDCODE `0x3631093`). The first
programmer invocation was sandbox-blocked (`libusb init failed`) before it
could load the device; its log is
`build/gpu/t1p_predicate_bits_20260928/h1/program_01.log`.

The approved retry ran the exact command

```bash
openFPGALoader -c dirtyJtag --freq 1000000 \
  build/spu_a7_100t_GPUVGA_T1P_PER_PRIMITIVE_PREDICATES_Q1.bit
```

It exited 0, reached `Load SRAM 100.00%`, and reported `isc_done 1`,
`init 1`, and `done 1`. Its durable transcript is
`build/gpu/t1p_predicate_bits_20260928/h1/program_02_escalated.log`
(SHA-256 `f7bcd298e32574bd55c7c893c6d68bfa6ba7369071a097be12217589c819c439`).
This establishes FPGA SRAM programming of the named artifact only. No T1p
UART packet, scene transition, displayed response, or physical pixel match
has been measured. Persistent configuration flash was not written.

## 9. Owner-authorized bounded H1 UART scene transport

The T1p SRAM load passed, and the CH340 UART is present at
`/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0`. The owner separately
authorized one A/B/C/return-A sequence:

```bash
python3 tools/send_gpu_t1p_sequence.py --dry-run
python3 tools/send_gpu_t1p_sequence.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --dwell-seconds 5 \
  --transcript build/gpu/t1p_predicate_bits_20260928/h1/sequence_01.json
```

The sender pins the 175-byte production Scene A fixture and the loaded
bitstream by SHA-256. It appends XOR opcode bytes `[2,2,2,2]` at wire
positions 175..178 and selector bytes at wire positions 179..182. The four
183-byte packets use selector tuples A `[CC,CC,CC,CC]`, B
`[89,8E,AA,D9]`, C `[BD,D8,8E,F8]`, and exact return A. At 115200 8N1, the
sender requires each full write and `tcdrain`, then waits five seconds before
the next packet. The transcript refuses overwrite and records packet hashes,
byte counts, drain completion, and timings. Do not repeat or vary the
sequence without renewed owner authorization.

**Static preflight (2026-09-29): PASS.** `py_compile`, `--dry-run`, and
`git diff --check` passed. Dry-run packet SHA-256 values are A/return A
`e265339b10a827d1264c5268513c0eebec1dfaa4c3c17462d4e322f196971081`,
B `eadf42c57c7808569b520a4c56ddceb74124d8526cf0f52c1a98bf9bda4d773c`,
and C `1887ef0d11b49c7dfc61fe51e9beaf0554bbc2c297dd4c33429436cc10a4723b`.
Wire transport can establish packet delivery to the UART device, not exact
per-pixel FPGA behavior. Record any display change only from an actual
operator observation.

**H1 transport result (2026-09-29): PASS.** The first sandboxed attempt could
not open the CH340 device and sent no bytes. The approved retry exited 0 and
recorded four complete 183-byte writes and `tcdrain` completions in
`build/gpu/t1p_predicate_bits_20260928/h1/sequence_01.json` (SHA-256
`4cd7e65e0019cb6a37e8cfff5e499914b02c1373f3e05a1b69f93484b3e304f3`).
The start-to-start gaps were 5012.521, 5012.414, and 5011.737 ms. Initial
and return-A packet hashes match exactly. An independent transcript audit
checked four ordered packets, all byte counts, selector tuples, XOR opcode
bytes, drain markers, timing gaps, and exact return-A equality. This proves
host-to-CH340 transport of the frozen sequence. FPGA packet acceptance,
display response, and physical pixel equality were not established by that
transport record.

**Owner-authorized repeat (2026-09-29): TRANSPORT PASS; VISUAL UNRESOLVED.**
The repeat used the same sender, port, 115200 8N1 framing, packet bytes, and
five-second dwell. `build/gpu/t1p_predicate_bits_20260928/h1/sequence_02.json`
(SHA-256 `3471a5d2842efad57611a943b1c9c29f0888af6ba3d95109849686272179b569`)
records four complete 183-byte writes and drain completions, with
start-to-start gaps of 5012.268, 5011.765, and 5011.580 ms. Its A, B, C,
and return-A packet hashes match the first sequence exactly. The operator
reported a small upper-left patch on VGA but **no visible change** during the
repeat. Therefore no A/B/C/return-A visual transition or FPGA packet
acceptance is established.

The independent scene oracle gives 2,441 valid pixels within x=10..70,
y=10..90 of the 640×480 frame (0.795% of the frame). The expected A→B,
B→C, and C→A differences are 1,269, 1,261, and 1,278 pixels respectively,
each about 0.4% of the full frame but roughly half of the rendered patch.
This small screen footprint limits unaided observation; it does not explain
away the negative operator report. Halt further repeat transmissions under
this contract. A new visual diagnostic should first specify a larger,
oracle-checked discriminator or a close-up time-resolved capture and its
bounded hardware attempt budget.

Post-transport integration preflight: `py_compile` for the sender and
`git diff --check` passed. One repository-gate attempt was frozen at 1,800
seconds per attempt and cumulative; no retry or timeout increase is
authorized. The attempt was launched at the evidence path below:

```bash
tools/run_detached_job.sh \
  --output build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_01 \
  --timeout 1800 --notify-desktop -- \
  bash tools/verify_repo.sh
```

Interpret only a durable terminal marker and `result.json` in a later
session. This repository gate does not replace the UART transcript audit.

**First H1 repository-gate result (2026-09-29): FAILED, exit 1.** The durable
`FAILED` marker and `result.json` at the initial gate path record 1,004
seconds. Root hygiene and changed-markdown citation checks passed;
`spu_t1d_repeatability_diag_tb.v` hit its 60-second per-test limit. Two
isolated default-phase simulations then passed in 55.506 and 50.722 seconds.
The test-specific cap was raised to 90 seconds to provide measured headroom.

**Renewed H1 repository-gate result (2026-09-29): COMPLETE, exit 0.** The
single renewed attempt at
`build/gpu/t1p_predicate_bits_20260928/h1/repo_gate/run_02/` completed in
937 seconds. T1d repeatability passed; the suite reported 237 passes and zero
failures. The post-transport repository integration gate is closed.

## 10. Owner-authorized scaled visibility diagnostic

The owner authorized one larger oracle-checked visual diagnostic after the
negative repeat observation. Use the loaded T1p bitstream without reprogramming.
`tools/send_gpu_t1p_large_diagnostic.py` derives a 175-byte scene wire from
the frozen T1i Scene A fixture by multiplying only each signed 32-bit edge
constant by four. It leaves edge slopes, depth samples, UV samples, XOR
opcodes, and A/B/C/return-A selectors unchanged. The program pins the source
fixture and bitstream SHA-256 values, rejects edge overflow, checks packet
length and exact return A, and runs the independent 640×480 software oracle
before opening the UART.

**Frozen preflight (2026-09-29): PASS.** `py_compile`, dry run, and
`git diff --check` passed. The derived 175-byte wire SHA-256 is
`1b6b066639da98f914f3e8512150656631dd7a55e18b6a1f65b9b7f222ca66df`.
The oracle found 38,561 valid pixels, lane counts `[11964,11723,7635,7239]`,
bounds x=40..280 and y=40..360. Expected A→B, B→C, C→A differences are
`[19918,19805,20165]` pixels. Packet SHA-256 values are A/return A
`7fde74d72eb47e5f18a82239e15e4275c3785e7609dc2bb7a3d8013fe311676a`,
B `6c5d5eb11e230ca92c8b912f834824bd57b5661450bc2c618e1cf2d003005eab`,
and C `ae1a840b1cbbbe1f3988682b94b262be8a3cd6873b9079111920389daa4c42a8`.

Freeze one hardware transmission attempt, one A/B/C/return-A sequence,
five seconds between packets, and a 60-second external timeout. The attempt
is consumed only if the UART opens and at least one byte is written. Do not
repeat or vary it under this authorization. Run:

```bash
timeout 60s python3 tools/send_gpu_t1p_large_diagnostic.py --send \
  --port /dev/serial/by-id/usb-1a86_USB_Serial-if00-port0 \
  --transcript build/gpu/t1p_predicate_bits_20260928/h1/scaled_visibility_01.json
```

The transcript proves host-to-CH340 transport if complete. Accept a visual
transition only from an operator observation or capture; do not infer FPGA
acceptance from `tcdrain` or the software oracle.

**Scaled diagnostic result (2026-09-29): TRANSPORT PASS; VISUAL PASS.** The
sandboxed invocation could not open the device and sent no bytes. The approved
retry exited 0; `build/gpu/t1p_predicate_bits_20260928/h1/scaled_visibility_01.json`
(SHA-256 `83df320ff8045dded24c3655bb99250a49493823aa5781cce2c8467866bb113a`)
records four complete 183-byte writes and drain completions, with packet
start gaps of 5011.502, 5012.988, and 5013.298 ms. An independent audit
reconstructed all packet hashes from the recorded derived wire, confirmed
the byte counts and drain markers, checked the gaps, and proved exact
return-A packet equality. The operator reported visual changes during the
sequence. Initial answers about the final image conflicted, so a direct
clarification asked whether it matched the first **enlarged A** or the
preceding C. The operator answered that it matched the first enlarged A.
This closes the bounded enlarged-scene A/B/C/return-A visual gate as
**PASS (operator-observed, visual-only)**. It does not establish an exact
physical pixel comparison. No further UART transmission is authorized by
this bounded attempt.

Targeted 115200-baud receive simulation with the exact scaled 183-byte
packets passed in `software/tests/test_gpu_t1p_scaled_uart_loader.py`:
732 bytes received without framing errors; each inactive bank matched its
packet; all four frame-boundary activations completed; the final active bank
equaled the initial enlarged A payload. This is testbench evidence; the
separate visual observation supports only broad physical transitions and
return, not exact physical pixel equality.
