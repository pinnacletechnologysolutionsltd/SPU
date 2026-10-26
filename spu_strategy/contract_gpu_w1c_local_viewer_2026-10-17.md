# GPU-W1C — Local T1d frame and pixel viewer

```bash
python3 -m software.spu_gpu_eval.workbench view --port 8765
```

**Status:** Implemented; focused verification complete
**Date:** 2026-10-17
**Dependency:** W1-B qualified source snapshot and CLI

## Objective

Provide a small browser viewer for the existing frozen T1d scenes. It displays
the ideal-reference and finite-width device-model frames side by side and
shows both W1-B pixel reports when the user clicks either frame.

## Required behavior

1. Bind the HTTP server to `127.0.0.1`; do not expose a configurable network
   interface.
2. Populate the selector from W1-B's hash-checked 11-scene catalogue.
3. On scene selection, obtain frames by calling the existing `write_preview`
   and `write_device_preview` APIs into a temporary child of
   `build/gpu_evaluation`. Display their existing PPM pixel payloads on two
   canvases; do not rasterize or recompute arithmetic in the viewer.
4. On either canvas click, call W1-B's `_inspect` report path. Show ideal and
   device-model coverage, covered triangles, depth, winner and RGB, plus the
   separate equality fields. State that this is software reference/model data,
   not physical observation.
5. Convert click coordinates from displayed canvas size to the fixed 640×480
   T1d pixel grid and reject clicks outside the active pixel rectangle.
6. Reject unknown scenes, unsupported modes, malformed requests and invalid
   pixel coordinates with a client error. Remove only the viewer's own
   temporary render directory on orderly shutdown.

## Verification

```bash
python3 software/tests/test_gpu_workbench_w1c.py
python3 software/tests/test_gpu_workbench_w1.py
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 software/tests/test_gpu_pixel_inspect_s3.py
```

The W1-C test must exercise the HTTP endpoints against frozen scenes, compare
returned RGB bytes with W1-B output files, check the `(320,0)` depth mismatch,
and cover invalid IDs, modes and coordinates. Source provenance for this viewer
must be recorded separately from the completed W1-B snapshot. W1-C does not
qualify FPGA pixel equality or authorize RTL/ISA changes.

## Implementation and execution record

The viewer is a static HTML canvas front end served by Python's standard
library HTTP server. The server binds only to `127.0.0.1`; browser canvas code
displays the RGB bytes returned from the existing W1-B PPM outputs. Python
calls W1-B's existing preview and inspection APIs. It adds no renderer or
arithmetic path. Parallel frame requests share one cached render pair.

The separately frozen source snapshot is based on
`963a685004b96e275e7e58ebefac98c6e1321597` and is stored at:

```text
build/gpu_evaluation/gpu_w1c/source_snapshot_01/gpu_w1_source_e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3.tar
```

SHA-256:
`e014f8c9f090e38e9b2a20b56bdb93b4128625e91ee65b122d50d5e48c1cc2d3`.
The 88-file archive and adjacent JSON manifest include the viewer, frozen
inputs, tests, and dependencies. The base commit plus this hash-pinned overlay
reproduced W1-C and the W1/S1/S2/S3 focused suites successfully.

Results: W1-C, 5 tests passed; W1, 7 passed; S1, 12 passed; S2 RTL/model
parity checks passed; S3, 5 passed. The same suites passed from the clean
snapshot checkout. The server and endpoint tests establish local interaction
and exact frame payload reuse; no human usability review or FPGA comparison is
claimed.
