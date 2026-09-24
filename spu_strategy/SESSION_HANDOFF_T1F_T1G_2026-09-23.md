# Session Handoff: T1f Closed / T1g Starting

Date: 2026-09-23<br>
Repository HEAD at handoff: `8ea3bc2abeaff97dac5b01ed558ee96008788340`

## T1f status

T1f Family A is closed at its intended scope:

```text
I0 PASS — source/resource/timing preflight
I1 PASS — four-primitive implementation/profile tests
I2 PASS — top-level four-way oracle
I3 PASS WITH UNRELATED GATE DEBT
B1 PASS — Artix-7 build/provenance/timing
H1 PASS — operator-observed visual evidence
```

Evidence:

```text
spu_strategy/contract_gpu_t1f_family_a_four_primitive_2026-09-22.md
build/t1f_h1_20260923/h1_observation.md
build/t1f_h1_20260923/program_01.md
build/t1f_h1_20260923/uart_transcript.json
```

Qualified artifact:

```text
source commit: cd507cd0465b00bc827d88458c0013ff6cff5189
bitstream: build/t1f_clean_qualification_20260922/build/spu_a7_100t_GPUVGA_T1F_B1_S1.bit
bitstream SHA-256: 45fb9e4b22e13c1893df7f39d36a365c5f5d0db1d5e30443cbae9afcc30ba755
fixture decoded wire SHA-256: 78820c1f6da055a3c51eb9ec3709fe027cd1b0a2772093c6e8618a5c300dbe5f
sender SHA-256: 78e0e458a8e12d37a989c5ee33a5110933d70107839f90915f8e4ffa8732c95e
```

The physical result was a black background with the expected top-left
four-triangle scene and red/green/blue/yellow depth-winner regions,
including the red primitive-0 equal-depth tie. No analyzer telemetry was
used. T1d D3 remains separately classified as:
`INFRASTRUCTURE FAIL — FX2 sustained-stream limitation`.

## UART host-context lesson

The Codex Python process cannot see `/dev` even when shell/udev/sysfs can.
The repository detached runner was unavailable because the user systemd bus
was not available. The exact pinned sender succeeded once through a host-
visible `screen` context; no alternate sender or raw `dd` path was used.

The accepted bitstream is volatile SRAM configuration. A board power cycle
requires reprogramming before visual work.

## T1g status

Draft contract:

```text
spu_strategy/contract_gpu_t1g_temporal_scene_replacement_2026-09-23.md
```

Current status: `Q0 DRAFT — REVIEW`. No T1g RTL, fixture, build, FPGA, or
UART changes have been made.

### Q0 source findings

`hardware/rtl/gpu/spu_scene_loader.v` already provides:

```text
two banks: active_scene and candidate_scene
candidate invisible during receipt
complete payload sets commit_pending
active bank changes only on activate_raw_bank
all bytes are ignored while commit_pending is asserted
```

`hardware/rtl/gpu/spu_prepared_scene_control4.v` already requires:

```text
all four derived results from one candidate generation
commit_pending
frame_start
```

before activation. `spu_gpu_top.v` re-anchors coverage/depth state from the
activated scene at frame boundaries.

### T1g next work

Q0 must freeze three prepared-scene fixtures and their hashes:

```text
scene A -> scene B -> scene C
```

It must freeze representative pixels, activation-frame semantics, the
definition of a mixed/tear frame, and observability for active scene,
candidate scene, readiness, activation, and frame number.

Q1 must characterize the interval:

```text
final payload byte
 -> four depth results ready
 -> next eligible frame_start
 -> activation
 -> commit_pending clear
```

Report it in `clk_pixel` cycles, frame periods, and 115200-baud wall-clock
equivalent. Freeze a safe inter-scene host pacing interval. If useful pacing
requires ACK/ready, FIFO, queueing, or protocol changes, split that into a
separate transport tranche and HALT T1g qualification.

Do not modify RTL or run physical tests during Q0/Q1.

## Architectural truth

The current VGA GPU is a deterministic fixed-point triangle compositor:

```text
triangle records
 -> screen-space edge coverage
 -> affine signed depth
 -> depth winner
 -> VGA
```

It is not currently a native Quadray beam renderer and does not yet use
surds, exact rational fragment arithmetic, beam primitives, texture memory,
or programmable material operators.

## Later roadmap

After T1g:

```text
T1h affine interpolated material coordinates (u,v)
T1i fragment-coordinate path
T1j procedural checkerboard/stripes/gradients
T1k deterministic material operators
T1l bounded fragment-program stream
```

Keep T1f's 252-bit record and four-primitive profile unchanged. T1h needs a
separate profile or proven unused record capacity; do not silently alter the
T1f wire format.

## Worktree warning

The worktree contains many pre-existing unrelated modifications and
untracked artifacts. Preserve them. Do not reset, clean, or broadly reformat
the repository. The T1f/T1g files above are the relevant handoff artifacts.
