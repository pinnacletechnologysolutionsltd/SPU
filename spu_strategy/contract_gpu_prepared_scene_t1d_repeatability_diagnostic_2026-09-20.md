# Engineering Contract: T1d Physical Repeatability Diagnostic

**Date:** 2026-09-20
**Contract ID:** `GPU-T1D-REPEATABILITY-DIAGNOSTIC-2026-09-20`
**Revision:** 0
**Status:** `D2 AUTHORIZED — build qualification only; D3 HALT`
**Owner:** John Curley

## 1. Objective

Diagnose why the frozen T1d prepared-scene transaction produced the expected
scene on the first physical execution and produced a blank scene on the second
execution after the frozen warm-reset procedure.

This contract authorizes diagnosis planning only. It does not authorize a
behavioral fix, a new normal T1d bitstream, or another physical execution of
the existing B1 artifact.

The diagnostic boundary is:

```text
T1d Stage C FAIL
    -> instrument and discriminate hypotheses
    -> freeze root-cause classification
    -> separate correction contract
    -> requalify
    -> separate physical verification contract
```

## 2. Mandatory governance

The Halt-and-Flag Implementer shall inspect this contract before editing RTL,
tests, build scripts, or board procedures. If an observable cannot distinguish
two hypotheses, HALT and flag that deficiency before implementation.

The Integration Auditor shall run the repository gate only after the
diagnostic source closure and build command have been frozen by an approved
revision of this contract. A successful diagnostic build shall not amend the
existing B1 hardware evidence.

No command in this draft authorizes FPGA programming, UART transmission, or
monitor-based acceptance testing.

## 3. Immutable prior evidence

The following evidence is context and shall not be rewritten or reinterpreted
by the diagnostic work:

| Item | Frozen result |
|---|---|
| Stage B source anchor | `d88ee61f3f930a93b903839c6dcae73174578adc` |
| Repository gate | 233 passed, 0 failed |
| B0 bitstream | SHA-256 `5de505769d619ddf01fb8a8d6853fee650425a3e0be57214ca97b4db00c95fee` |
| B1 bitstream | SHA-256 `9d135a4d60e791fa88c4010ea6875c29127603d0d413c1d323fb03a0b0476cc1` |
| B1 build result | synthesis, place-and-route, timing, and bitstream generation completed |
| Stage C Attempt 1 | expected prepared scene observed; PASS |
| Stage C Attempt 2 | exact 64-byte transmit completed; scene blank; FAIL |
| Attempts 3–5 | prohibited after terminal FAIL; not run |
| Frozen wire fixture | SHA-256 `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee` |
| Sender provenance | `c8895e9`, `tools/send_gpu_t1d_scene.py` |
| Attempt 1 transcript | `stage_c_attempt_01/transmit.json`; SHA-256 `2630422598d51b2b2636dd4835588a3e18762ae1fd47877005ff354786d9496c` |
| Attempt 2 transcript | `stage_c_attempt_02/transmit.json`; SHA-256 `aef644d1071bfd7c32a8f4ed07da6151faa8db698dc97220d8f3287c8305487d` |
| Attempt 2 raw observation | SHA-256 `7d185a2038e4f0001559728e245908e87546f677657e82d475e63923553e3693` |

The earlier duplicate VGAFIX load and sender-open failures are procedural
anomalies recorded in the T1d execution contract. They are not evidence for a
root cause and shall not be silently removed.

## 4. Frozen hypotheses

The investigation shall begin without selecting a preferred explanation:

* **H1 — reset/re-arm state:** warm reset leaves a receiver, loader, scene
  staging area, or renderer state uncleared or not ready for the next frame.
* **H2 — UART synchronization/framing:** the second transaction loses start
  recognition, byte alignment, or accepted-byte count after reset.
* **H3 — loader transaction state:** the loader receives bytes but its
  transaction state, completion detection, or staging-to-active handoff is not
  rearmed correctly.
* **H4 — commit/activation timing:** the payload is valid, but commit or
  activation is missed, mistimed, or suppressed at the frame boundary.
* **H5 — renderer/post-commit state:** the payload commits and activates, but
  the rendering or VGA path remains blank or stale.

The diagnostic result may classify one hypothesis, several interacting
hypotheses, or the result `INCONCLUSIVE` if the instrumentation cannot support
a unique classification.

## 5. Scope and exclusions

### 5.1 In scope

* Diagnostic-only observability in simulation and, if required, a separately
  identified diagnostic bitstream.
* A deterministic reset → transaction → reset/re-arm → identical transaction
  simulation sequence.
* Relevant UART phase offsets and reset-to-transaction timing offsets.
* Received-byte count, payload signature, loader completion, commit, frame
  activation, and transaction sequence evidence.
* Fresh build qualification for any diagnostic RTL.
* A separately authorized, bounded physical diagnostic execution.

### 5.2 Out of scope

* Fixing RTL behavior during this diagnostic tranche.
* Changing the UART baud rate, framing, sender, payload, reset procedure, or
  observation procedure to obtain a passing picture.
* Changing normal T1d loader semantics or adding protocol commands.
* Reusing the B1 qualification for an instrumented design.
* Re-running the failed Stage C experiment with attempts 3–5.
* Adding CRC/resynchronization or general transport reliability features.

If diagnosis identifies a required behavioral change, stop and create a new
correction contract. Do not implement the correction under this contract.

## 6. Required observables

The diagnostic design shall make the following events or values observable in
simulation and, before any physical execution is authorized, through a frozen
diagnostic output path:

1. reset asserted, reset released, and receiver/loader ready;
2. start byte recognized;
3. each accepted payload byte count, including the final count;
4. UART framing or receive error, if present;
5. loader receiving state and transaction completion;
6. `scene_commit` request and acceptance;
7. frame-boundary activation of the prepared scene;
8. a deterministic signature of the accepted 63-byte payload;
9. a transaction sequence value that changes only after an accepted complete
   transaction;
10. the final diagnostic status retained long enough for observation.

The instrumentation must not alter the normal 64-byte wire fixture or require
the host to send a new protocol field. A diagnostic selector, if needed, shall
be compile-time-only and shall be absent from the normal B1 artifact.

### 6.1 Payload signature definition

Unless the pre-execution review finds a concrete RTL incompatibility, use the
following exact signature for the 63 payload bytes after the `A5` start byte:

```text
initial crc = 16'hFFFF
polynomial  = 16'h1021
input order = payload byte order, bit 7 first
update      = MSB-first CRC-16-CCITT
frozen T1d fixture result = 16'h7920
```

The signature is valid only after exactly 63 payload bytes have been accepted.
No signature from a partial transaction may be treated as a valid payload
signature.

For the frozen fixture `fixtures/gpu_t1d_scene_wire_64b.bin`, the complete
frozen reference is therefore:

```text
wire length       = 64 bytes
start byte        = 8'hA5
payload length    = 63 bytes
payload CRC-16    = 16'h7920
wire SHA-256      = aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee
```

### 6.2 Physical diagnostic output path

D0 freezes a dedicated diagnostic UART TX. It shall not share the suspected RX
implementation and shall not alter the VGA observation path.

```text
top-level port       = diag_tx
FPGA package pin     = G6
board header         = Wukong J10-7
I/O standard         = LVCMOS33
direction            = FPGA output to logic-analyzer input
idle level           = 1
capture               = fx2lafw/sigrok, logic channel D0, common ground
```

The existing board record identifies J10-7/G6 as unused by the VGA harness.
The operator shall connect only a 3.3 V-compatible analyzer input and ground;
no monitor-side VGA conductor, 5 V source, or CH340 UART conductor may be
connected to G6. The physical continuity and analyzer channel assignment must
be checked before any D3 execution and recorded with the raw capture.

The diagnostic XDC shall add exactly:

```tcl
set_property PACKAGE_PIN G6 [get_ports diag_tx]
set_property IOSTANDARD LVCMOS33 [get_ports diag_tx]
```

The diagnostic XDC is a new Stage B build input. It shall not modify the
normal T1d XDC or the normal B1 artifact.

## 6.3 D0 review findings — 2026-09-20

This section records the source and board findings that support the frozen D0
specification below. It does not authorize implementation.

### Existing diagnostic signal anchors

The current T1d source already contains these internal state anchors:

| Required observable | Existing source anchor |
|---|---|
| start recognition | `spu_scene_loader`: `rx_valid && rx_byte == START_BYTE` |
| accepted byte count | `spu_scene_loader.payload_count` |
| receive error | `spu_a7_gpu_vga_top.t1d_uart_input.u_uart.uart_frame_err` |
| loader receiving state | `spu_scene_loader.receiving` |
| loader completion | `spu_scene_loader.commit_pending` |
| active bank | `spu_scene_loader.active_bank` |
| commit/activation | `spu_gpu_top.activate_scene` and `frame_start` |
| prepared-control readiness | `spu_gpu_top.prepared_ready0`, `prepared_ready1`, `prepared_generation_matches` |
| reset readiness | `spu_a7_gpu_vga_top.rst_n_db`, `pix_rst_n` |

These are internal implementation signals, not yet a stable diagnostic
interface. D0 freezes which are retained, how their terminal values are
encoded, and how they are captured without changing the normal scene path.

### Current production source closure

The canonical T1d synthesis manifest is
`hardware/boards/artix7/synth_a7_gpu_vga_t1d.ys`. Its current prepared-scene
closure includes the UART receiver, video timing, raster/depth path,
`spu_scene_loader.v`, `spu_scene_unpack.v`,
`spu_prepared_scene_control.v`, `spu_gpu_top.v`, the VGA/HDMI support modules,
and `spu_a7_gpu_vga_top.v`. The frozen diagnostic closure is that production
closure plus:

* `hardware/rtl/peripherals/whisper/spu_t1d_diag_uart_tx.v`;
* `hardware/rtl/peripherals/whisper/spu_t1d_diag_record.v`;
* the `GPU_T1D_DIAG`-guarded additions in
  `hardware/boards/artix7/spu_a7_gpu_vga_top.v`;
* `hardware/boards/artix7/synth_a7_gpu_vga_t1d_diag.ys`;
* `hardware/boards/artix7/spu_a7_gpu_vga_t1d_diag.xdc`;
* `hardware/tests/common/spu_t1d_repeatability_diag_tb.v`;
* `software/tests/test_gpu_t1d_repeatability_diagnostic.py`;
* `tools/decode_gpu_t1d_diag_capture.py`.

The diagnostic selector must not compile the diagnostic additions into the
normal B0 or B1 source closure.

### Clock/reset review

The UART receiver and prepared-scene loader operate in `clk_pixel`, derived by
the registered divide-by-two from the 50 MHz `sys_clk`. The pixel-domain reset
is `pix_rst_n`, generated by the existing reset debounce and three-stage pixel
reset synchronizer. The diagnostic simulation must therefore observe all
transaction state in that one pixel clock domain and must explicitly include
reset release before each transaction.

### Physical output review

The current T1d top has no `uart_tx` or other diagnostic output. The reviewed
board records J10-7/FPGA pin G6 as unused by the VGA harness; J10 pins 7, 8,
and 9 are documented as unused by VGA. D0 freezes J10-7/G6 as the diagnostic
UART TX path, subject to the physical continuity and analyzer safety check
required before D3. It shall not be driven until D1/D2 are separately
authorized and complete.

### Build-flow review

`hardware/boards/artix7/build_a7.sh` currently accepts only the frozen T1d
artifact tags `T1D_B0_S1` and `T1D_B1_S1` and has no diagnostic selector or
diagnostic artifact tag. D0 therefore freezes the required build-flow
interface; implementing that interface is part of D1 and is not performed by
this review:

```text
compile selector     = GPU_T1D_DIAG=1
UART selector        = GPU_T1D_UART=1
artifact tag         = T1D_DIAG_S1
top                   = spu_a7_gpu_vga_top
manifest              = hardware/boards/artix7/synth_a7_gpu_vga_t1d_diag.ys
constraints           = hardware/boards/artix7/spu_a7_gpu_vga_t1d_diag.xdc
bitstream             = build/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
```

The exact future D2 command is:

```bash
tools/run_detached_job.sh \
  --output build/wukong_gpu_prepared_scene_t1d_repeatability_diag_20260920/d2_build_01 \
  --timeout 7200 \
  --notify-desktop \
  -- env A7_FREQ=25 A7_SEED=1 GPU_T1D_UART=1 GPU_T1D_DIAG=1 \
     A7_ARTIFACT_TAG=T1D_DIAG_S1 \
     bash -lc 'bash tools/verify_repo.sh && \
       python3 software/tests/test_gpu_t1d_repeatability_diagnostic.py \
         --fixture fixtures/gpu_t1d_scene_wire_64b.bin \
         --phase-offsets 0,1,2,3 --reset-offsets 0,1,2,3 && \
       bash hardware/boards/artix7/build_a7.sh 100t GPUVGA all'
```

The D1 build-flow edit shall reject `GPU_T1D_DIAG=1` unless the diagnostic
artifact tag is present, shall reject `T1D_DIAG_S1` without the diagnostic
selector, and shall preserve the existing B0/B1 tag rules. Until that edit is
implemented and reviewed, the command is a frozen specification, not an
authorized job.

## 6.4 Frozen telemetry record

The diagnostic TX emits one fixed 16-byte binary record per retained event.
Bytes are sent in increasing offset order, each byte is UART 8N1, and the
record ends with the terminal marker at offset 15.

| Offset | Field | Definition |
|---:|---|---|
| 0 | magic | `8'hD7` |
| 1 | version | `8'h01` |
| 2 | record type | `8'h01` READY; `8'h02` TRANSACTION |
| 3 | transaction sequence | Starts at 1 after each reset; increments on accepted `A5` start; reset clears it |
| 4 | flags | See below |
| 5 | accepted count | Payload bytes accepted, 0–63; start byte is excluded |
| 6 | payload CRC low | CRC-16/CCITT low byte |
| 7 | payload CRC high | CRC-16/CCITT high byte |
| 8 | active bank | Active bank value at terminal snapshot |
| 9 | terminal reason | See below |
| 10 | frame-wait low | Frame-starts observed after payload completion |
| 11 | frame-wait high | High byte of frame-wait count |
| 12 | ready state | `1` when reset/loader readiness is established |
| 13 | reserved | Must be `8'h00` in revision 1 |
| 14 | record CRC8 | MSB-first CRC-8, polynomial `8'h07`, initial value `8'h00`, over offsets 0–13 |
| 15 | terminal marker | `8'h7E` |

Flags at offset 4 are:

```text
bit 0  ready established
bit 1  start byte recognized
bit 2  UART frame error observed
bit 3  loader completed 63 payload bytes
bit 4  commit_pending observed
bit 5  scene activation observed
bit 6  payload CRC valid after exactly 63 accepted bytes
bit 7  reserved; must be zero
```

Terminal reasons at offset 9 are:

```text
8'h01  READY
8'h02  ACTIVATED at frame_start
8'h03  RX_IDLE_TIMEOUT after a recognized start
8'h04  UART_FRAME_ERROR
8'h05  COMMIT_TIMEOUT after complete payload
```

The READY record is emitted once after `pix_rst_n` becomes ready. A transaction
record is emitted only after a terminal reason is reached. A missing
transaction record during the bounded capture window is evidence of no
recognized start or no terminal event; it is not permission to repeat the
experiment. A partial transaction shall terminate with `RX_IDLE_TIMEOUT` after
the frozen idle threshold of 32 UART bit periods without an accepted byte.

The TX serializer shall be a separate TX-only module. It shall use
`clk_pixel`, `217` clock cycles per bit, 115200 baud, 8N1, idle high, and LSB
first within each byte. It shall snapshot a complete record before transmission
and shall expose `busy`/`ready` so a record cannot be overwritten mid-frame.
The diagnostic record producer shall hold a pending record until the serializer
accepts it.

Payload CRC state is reset to `16'hFFFF` when the `A5` start is recognized and
updated only for accepted payload bytes. The CRC-valid flag is set only when
the accepted count reaches 63. For the frozen valid fixture the expected
payload CRC is `16'h7920`.

## 6.5 Frozen capture procedure and reference records

The raw logic capture shall begin before reset release and shall run for 2000
ms at 24 MHz on analyzer channel D0 connected to J10-7/G6:

```bash
sigrok-cli \
  --driver fx2lafw \
  --config samplerate=24MHz \
  --channels D0 \
  --time 2000 \
  --output-format sr \
  --output-file build/<diagnostic-evidence>/g6_uart_capture.sr
```

The exact future decoder command is:

```bash
python3 tools/decode_gpu_t1d_diag_capture.py \
  --input build/<diagnostic-evidence>/g6_uart_capture.sr \
  --channel D0 \
  --baud 115200 \
  --output build/<diagnostic-evidence>/telemetry.json
```

The decoder shall retain the raw capture, decoded records, record offsets,
record CRC result, and any discarded bytes. No decoded record without a valid
16-byte structure, record CRC8, and `8'h7E` terminal marker is evidence.

For each healthy reset → identical transaction sequence, the exact reference
records are:

```text
READY:
D7 01 01 00 01 00 00 00 00 01 00 00 01 00 2F 7E

TRANSACTION, activated, payload CRC 16'h7920:
D7 01 02 01 7B 3F 20 79 01 02 00 00 01 00 7B 7E
```

The physical diagnostic procedure performs one baseline transaction and one
warm-reset repeat. Because reset clears the diagnostic sequence, each healthy
run is expected to produce the same READY and TRANSACTION records; the host
capture ordinal distinguishes baseline from repeat. A repeat that produces
only READY, a partial-count record, a wrong CRC, or a non-activation terminal
reason is classified with the decision table and preserved as raw evidence.

## 6.6 D0 completion review

The following D0 fields are now frozen:

* internal signal anchors and retention points;
* payload CRC algorithm and expected value `16'h7920`;
* independent diagnostic TX module and clock/divisor/framing;
* fixed 16-byte record layout, flags, terminal reasons, and CRC8;
* `diag_tx` → G6/J10-7 electrical path and XDC lines;
* compile-time selector, source filenames, artifact tag, and artifact name;
* exact simulation source files, command, phase-offset matrix, and assertions;
* exact detached D2 command;
* raw capture command, decoder command, capture duration, and reference records.

The exact future D1 simulation command is:

```bash
python3 software/tests/test_gpu_t1d_repeatability_diagnostic.py \
  --fixture fixtures/gpu_t1d_scene_wire_64b.bin \
  --phase-offsets 0,1,2,3 \
  --reset-offsets 0,1,2,3
```

The test shall compile `hardware/tests/common/spu_t1d_repeatability_diag_tb.v`
with the reviewed diagnostic source closure, execute the reset → transaction →
activation → reset → identical transaction → activation sequence, and fail if
either complete transaction differs from the frozen `16'h7920` reference or if
the first divergence is not reported. The phase values are pixel-clock cycles;
the test shall state the concrete conversion in its evidence output.

`D0 = REVIEWABLE COMPLETE / HALT`. This closes specification work only. The
owner authorization for D1 is recorded in §6.7; the existing T1d B1 artifact
remains prohibited for this investigation.

## 6.7 D1 closeout and D2 authorization — 2026-09-20

The owner-authorized D1 campaign completed successfully:

* detached result: `COMPLETE`, exit code `0`, duration `96 s`;
* evidence directory:
  `build/wukong_gpu_prepared_scene_t1d_repeatability_diag_20260920/d1_sim_01`;
* phase/reset cases: `(0,0)`, `(1,1)`, `(2,2)`, `(3,3)`;
* all four cases emitted the frozen READY and ACTIVATED records;
* all four cases matched payload CRC `16'h7920`, reset/re-arm behavior, and
  defined VGA outputs.

`D1 = PASS`. The simulation did not reproduce the physical blank-scene
failure. It is diagnostic evidence, not a reason to alter normal T1d RTL.

The owner now authorizes D2 only. D2 covers the repository gate, repeated
focused diagnostic simulation from the clean checkout, diagnostic synthesis,
place-and-route, timing/utilization/warning review, and artifact provenance.
The D2 campaign budget is one detached job with the frozen 7200-second
timeout. A failed, timed-out, or unavailable job consumes that slot; relaunch
requires renewed owner authorization.

The authorization does not cover any bitstream load, board connection, UART
transaction, logic-analyzer capture, or D3 physical diagnosis. D3 remains
`HALT` until separate authorization.

### 6.8 D2 preflight provenance record — 2026-09-21

The first full repository-gate attempt after D1 exposed an invocation defect,
not a DUT failure: the two existing T1d board benches were compiled without
`GPU_T1D_UART`, and the newly discovered diagnostic bench was compiled without
`GPU_T1D_DIAG`. That run is retained as:

* `precommit_gate_01`: `FAILED`, `231 PASS / 3 FAIL`, exit code `1`;
* the two board-bench failures were Verilator `uart_rx` pin-not-found errors;
* the diagnostic bench produced no verdict because its selector was absent.

The runner correction added per-bench compile defines for the three guarded
benches and propagated those defines to the Verilator fallback. The first
scoped rerun then exposed an independent harness limit: the diagnostic bench
legitimately exceeded the generic 15-second test timeout. That result is also
retained as:

* `triage_t1d_02`: `FAILED`, `3 PASS / 1 TIMEOUT`;

The runner correction then assigned only the diagnostic bench a bounded
60-second timeout; no DUT or diagnostic RTL semantics were changed. The clean
scoped rerun is:

* `triage_t1d_03`: `COMPLETE`, `68 PASS / 0 FAIL`, exit code `0`;
* `precommit_gate_02`: `COMPLETE`, `234 PASS / 0 FAIL`, exit code `0`.

The failed evidence directories remain preserved. These results qualify the
corrected repository invocation for the single authorized D2 campaign; they do
not qualify a diagnostic bitstream and do not authorize D3.

## 7. Diagnostic execution ladder

### D0 — pre-execution review

HALT until the following are explicitly frozen in a later approved revision:

* diagnostic RTL source closure and compile-time selector;
* exact observable signal names and retention behavior;
* physical diagnostic output path, pin mapping, and capture procedure;
* simulation command and expected assertions;
* diagnostic build command, artifact names, and evidence directory;
* bounded physical attempt count and timeout;
* PASS, FAIL, and INCONCLUSIVE rules.

### D1 — simulation discrimination

Run the diagnostic simulation before synthesis. It shall exercise, at minimum:

```text
reset
release and ready
transaction 1 using the frozen 64-byte fixture
frame activation 1
reset/re-arm
release and ready
the identical frozen 64-byte fixture
frame activation 2
```

Repeat the sequence with the approved UART and reset phase offsets. The test
shall assert that each accepted complete transaction has 63 payload bytes and
the expected signature, and shall report the first observable divergence
between transaction 1 and transaction 2.

The simulation shall cover at least the following offset classes, expressed in
the actual clock units of the testbench:

* reset release well before transmission;
* transmission beginning at the first eligible cycle after ready;
* transmission beginning near a pixel/frame boundary;
* transmission beginning near a system-clock/UART sampling boundary.

Any simulation failure must be classified before a diagnostic bitstream is
built.

### D2 — diagnostic build qualification

Treat the instrumented design as a new FPGA design. From a pristine checkout:

1. run `bash tools/verify_repo.sh`;
2. run the focused diagnostic simulation and preserve its complete output;
3. run canonical synthesis/place-and-route for the diagnostic top level;
4. inspect timing, utilization, warnings, unconstrained paths, and both clock
   domains;
5. freeze source commit, tool versions, command line, artifact paths, and
   SHA-256 hashes for the diagnostic bitstream and reports.

The exact detached command shall be written into the approved contract
revision only after the diagnostic artifact tag and build-flow support exist.
This draft intentionally authorizes no detached job.

### D3 — bounded physical diagnostic

Physical execution requires a later explicit authorization after D1 and D2
pass. The later authorization shall use:

* the diagnostic bitstream hash exactly as built;
* the same identified Wukong board and programming path;
* a frozen reset, sender, drain, and telemetry-capture procedure;
* the identical 64-byte fixture and 115200 8N1 sender settings;
* no more than two diagnostic transactions: one baseline and one
  reset/re-arm repeat;
* raw telemetry and operator observations recorded before interpretation.

No physical attempt may change the bitstream, payload, baud, reset timing,
sender, or observation rule. Missing or ambiguous telemetry is `INCONCLUSIVE`,
not permission to repeat indefinitely.

## 8. Decision table

| Observed evidence | Classification to investigate |
|---|---|
| No start recognition; count remains zero | H2 UART synchronization/framing |
| Start recognized; count stops below 63 or framing error asserted | H2 UART synchronization/framing |
| Count reaches 63 but signature is wrong | H2 or H3 receive/loader data path |
| Correct signature; no loader completion | H3 loader transaction state |
| Completion; no `scene_commit` | H3 loader handoff or H4 commit path |
| Commit; no frame activation | H4 commit/activation timing |
| Activation and correct signature; blank output | H5 renderer/post-commit/VGA path |
| First transaction complete; second fails after reset before any prior stage | H1 reset/re-arm state, with secondary H2/H3 checks |
| All diagnostic observables match but operator image differs | Observation/VGA path; do not infer renderer failure |
| Telemetry missing, contradictory, or truncated | `INCONCLUSIVE`; improve instrumentation under a new review |

The table is a classification aid, not proof that a single hypothesis is the
root cause. The final report shall cite the raw signal or telemetry evidence
for every classification.

## 9. Mandatory halt conditions

HALT immediately if any of the following occurs:

* a proposed edit changes normal T1d behavior rather than observing it;
* a proposed change alters baud, framing, payload, reset sequence, or sender;
* the diagnostic output path is not electrically and logically frozen;
* the diagnostic source closure differs from the reviewed closure;
* synthesis, place-and-route, timing, or bitstream provenance is incomplete;
* telemetry has fewer than the required terminal markers or cannot be tied to
  one exact artifact and transaction;
* the result depends only on a blank/non-blank monitor observation without
  diagnostic state evidence;
* a correction is discovered or implemented;
* the bounded physical attempt budget is exhausted.

Any halt caused by a discovered fix terminates this diagnostic contract and
requires a separate correction and requalification contract.

## 10. Acceptance criteria for this diagnostic contract

This contract may close only as one of:

* **ROOT CAUSE CLASSIFIED:** one or more hypotheses are supported by complete,
  repeatable diagnostic evidence and no competing hypothesis remains equally
  consistent;
* **INCONCLUSIVE:** the diagnostic execution completed but the observables do
  not distinguish the remaining hypotheses;
* **INFRASTRUCTURE FAIL:** the diagnostic build or execution could not be
  completed, with the failure evidence preserved.

`ROOT CAUSE CLASSIFIED` is not a hardware fix and is not a silicon-verified
claim. A fix, if desired, must be specified, implemented, requalified, and
physically verified under later contracts.

## 11. Required evidence package

The final diagnostic evidence directory shall contain, at minimum:

* the exact source commit and dirty-state record;
* the reviewed diagnostic source closure;
* repository-gate and focused-simulation outputs;
* synthesis/place-and-route reports and warning review;
* tool versions and exact build command;
* bitstream and report SHA-256 hashes;
* raw simulation traces or telemetry;
* raw physical observations, if D3 was authorized;
* a decision-table classification with evidence references;
* the terminal result and any next-contract identifier.

Until D0 is approved, Stage C remains `HALT` and the existing T1d B1 artifact
shall not be programmed again for this investigation.
