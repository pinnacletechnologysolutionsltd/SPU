# Contract: T1d visual observation without logic-analyzer telemetry

**Date:** 2026-09-21
**Contract ID:** `GPU-T1D-VISUAL-OBSERVATION-2026-09-21`
**Status:** `PASS — operator-observed visual-only; original D3 remains HALT`

## 1. Purpose

Provide a separate, explicitly visual-only observation path for the already
qualified T1d diagnostic image while the FX2 logic-analyzer capture path is
unavailable.

This contract does not close or replace the original D3 requirement for D0
telemetry. A visual result cannot prove UART byte acceptance, payload CRC,
loader completion, or frame-boundary activation.

## 2. Frozen inputs

```text
bitstream = build/d3_physical_diag_20260921/spu_a7_100t_GPUVGA_T1D_DIAG_S1.bit
sha256    = 52d45da0743c326f1700b4efa7fa0187523ea6e456948f274e2cc276ccd7b914
UART      = existing frozen 64-byte fixture, 115200 8N1
VGA       = existing frozen board pinout, cable, monitor, and timing
reference = fixtures/gpu_t1d_scene_reference.json
reference_sha256 = 7c48bdeffac97bba871e5c92663168900cb617f8586976e66f09077e11b7f138
```

No RTL, bitstream, reset sequence, UART fixture, baud, VGA channel mapping,
or original D3 acceptance criterion may change. The logic-analyzer probes are
not connected under this contract.

The predetermined image is the active 640x480 raster in RGB order, using the
frozen integer/rational depth oracle. The visual acceptance anchors are:

```text
(10,10)   background       = (0,0,0)
(100,300) triangle 0       = (15,0,0)
(540,300) triangle 1       = (0,15,0)
(200,100) overlap, tri 0   = (15,0,0)
(400,100) overlap, tri 1   = (0,15,0)
(320,100) equal-depth tie  = (15,0,0)
```

These points anchor the visual comparison; they do not replace the original
telemetry observables.

## 3. Required visual record

Before any UART transmission, record the board identity, bitstream provenance,
monitor/cable identity, ambient lighting, and a baseline image after reset.
Then perform the existing frozen transaction once and record the resulting
image with the same camera/device, lens, position, focus, monitor input mode,
resolution, refresh mode, cable, and lighting. Disable automatic exposure,
white balance, focus, HDR, and other image-processing changes where possible.
Repeat the frozen warm-reset sequence and transaction once with that unchanged
setup. Preserve the raw images and SHA-256 values.

## 4. Classification

* **VISUAL PASS:** both transactions produce the predetermined expected image
  and the monitor remains locked; this is visual evidence only.
* **VISUAL FAIL:** a transaction produces a blank, stale, malformed, or
  inconsistent image.
* **INCONCLUSIVE:** monitor lock, camera framing, board state, or transaction
  provenance cannot be established.

Any visual failure remains ambiguous between UART ingress, loader state,
activation timing, and rendering/output behavior. It does not authorize a
second retry or a claim about the original D3 telemetry criteria.

## 5. Execution record — 2026-09-21

The visual-only procedure completed as an operator-observed PASS:

* the initial frozen transaction produced the expected dual-triangle image;
* the physical warm-reset sequence returned the board to the black/unarmed
  state;
* the repeat frozen transaction produced the same expected dual-triangle
  image;
* both transactions used the provenance-pinned sender from commit `c8895e9`
  with sender blob SHA-256
  `7310a1a9f505a215a26082f1928963a96054a1e4552b96d0dba72a777fd110a1`;
* the two host-side transaction records report 64 bytes written and completed
  `tcdrain`.

Evidence records:

```text
build/d3_visual_observation_20260921/uart_recovery_amendment_01/preflight.json
build/d3_visual_observation_20260921/uart_recovery_amendment_01/transcript.json
build/d3_visual_observation_20260921/visual_repeat_02/repeat_record.json
build/d3_visual_observation_20260921/visual_repeat_02/transcript.json
```

This is operator-observed visual evidence. No camera raw-image files or
image SHA-256 values were produced. The result does not establish UART byte
acceptance, payload CRC, loader completion, frame-boundary activation, or any
other D3 telemetry observable.

## 6. Halt conditions

HALT on any need to reprogram the FPGA, alter the UART fixture or timing,
change VGA wiring, reconnect the logic analyzer, modify RTL/bitstream, or
interpret a visual result as internal UART/loader evidence. The original D3
remains halted until a separately authorized capture method satisfies its
48,000,000-sample telemetry requirement.
