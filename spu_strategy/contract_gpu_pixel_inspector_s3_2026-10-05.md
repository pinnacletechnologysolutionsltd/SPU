# Engineering Contract: T1d Pixel Inspector S3

- **Date:** 2026-10-05
- **Contract ID:** `contract_gpu_pixel_inspector_s3_2026-10-05.md`
- **Status:** ACTIVE — pre-execution review passed after correcting report-output and manifest-hash requirements.
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Codex, after §0 review
- **Integration Auditor:** `software/tests/test_gpu_pixel_inspect_s3.py` and repository gates

## 0. Pre-execution review

Run from the repository root:

```bash
git status --short
sed -n '1,180p' spu_strategy/GPU_EVALUATION_ROADMAP_2026-10-03.md
sed -n '1,180p' software/spu_gpu_eval/scene.py
sed -n '1,140p' software/spu_gpu_eval/packet.py
sed -n '1,150p' software/spu_gpu_eval/reference.py
sed -n '1,120p' software/spu_gpu_eval/device_model.py
sed -n '1,100p' software/spu_gpu_eval/cli.py
python3 -c 'import json; p=json.load(open("fixtures/gpu_t1d_scene_reference.json")); print(p["diagnostic_pixels"])'
```

Halt if `reference.pixel_decision` and `device_model.pixel_decision` do not
return deterministic decisions for one `(x,y)` coordinate, if either decision
does not include coverage, covered primitives, depth data, winner, and RGB, or
if the baseline scene does not produce overlap/tie/primitive-0/red at `(320,0)`.
Preserve the dirty worktree and do not stage or overwrite unrelated changes.

## 1. Objective and scoped files

Add a CLI command that inspects one active pixel in a valid S1 scene. It compiles
the existing packet, prepares the S2 functional device model, and emits one
deterministic JSON report containing the independent ideal decision beside the
finite-width device-model decision. Do not render the full frame.

Target files:

```text
software/spu_gpu_eval/device_inspect.py
software/spu_gpu_eval/cli.py
software/tests/test_gpu_pixel_inspect_s3.py
docs/gpu_scene_preview.md
spu_strategy/contract_gpu_pixel_inspector_s3_2026-10-05.md
```

Use Python 3.10+ standard library only. Use the existing scene parser, packet
compiler, ideal reference, and device model. Do not duplicate geometry,
arithmetic, or packet encoding. Do not modify RTL, board files, generated files,
frozen fixtures, S1/S2 artifacts, historical evidence, or hardware tools.

## 2. Command and report contract

Add this command:

```bash
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

`--x` and `--y` are required base-10 integers. Accept only `0<=x<640` and
`0<=y<480`. Read and validate the complete scene before writing stdout. Compile
the packet with `software.spu_gpu_eval.packet.compile_packet`, prepare it with
`software.spu_gpu_eval.device_model.prepare_scene`, compute
`reference.pixel_decision(scene,x,y)` and
`device_model.pixel_decision(prepared,x,y)`, and emit exactly one JSON object
plus a newline to stdout. Do not create scene or report artifacts on disk.

Emit sorted compact JSON with these top-level keys and meanings:

```json
{
  "format": "spu_gpu_pixel_inspection_s3_v1",
  "profile": "t1d-two-triangle-v1",
  "x": 320,
  "y": 0,
  "input_scene_sha256": "64 lowercase hexadecimal characters",
  "scene_packet_sha256": "64 lowercase hexadecimal characters",
  "ideal_reference": {},
  "device_decision": {},
  "decision_match": {
    "coverage": true,
    "covered_by": true,
    "winner": true,
    "rgb": true
  },
  "evidence": {
    "device_model": true,
    "physical_observation": false,
    "cycle_timing_model": false
  }
}
```

`ideal_reference` and `device_decision` contain the complete dictionaries
returned by the existing pixel-decision functions. `decision_match` compares
only `coverage`, `covered_by`, `winner`, and `rgb`; do not compare ideal rational
depths with approximate finite-width device depths. Hash the exact scene input
bytes and compiled packet bytes with SHA-256. Use the profile identifier from
`software.spu_gpu_eval.scene.PROFILE`. Do not include timestamps, absolute
paths, host identity, repository state, or hardware observations.

On input, read, or coordinate errors, print no JSON to stdout, print a concise
error to stderr, and return exit code 2. A successful command returns 0.

## 3. Implementation order

1. Run §0 and complete the Halt-and-Flag review before changing implementation
   files.
2. Add `inspect_pixel(raw_scene_bytes, x, y)` in `device_inspect.py` using only
   the existing parser, compiler, reference and device-model APIs.
3. Add the `inspect` subcommand in `cli.py`; preserve existing `preview` and
   `device-preview` interfaces and scene results. Their packet, image, and
   decision artifacts remain byte-identical; newly generated manifests record
   the changed `cli.py` source hash.
4. Add falsifiable tests for the baseline overlap/tie at `(320,0)`, background at
   `(0,0)`, a triangle-only covered pixel from the frozen diagnostics, exact scene
   and packet hashes, all four decision comparisons, deterministic JSON, invalid
   coordinates, malformed scene input, exit codes, and absence of report artifacts.
5. Add the exact command and report interpretation to `docs/gpu_scene_preview.md`.

## 4. Acceptance commands

Run from the repository root:

```bash
python3 software/tests/test_gpu_pixel_inspect_s3.py
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 0 --y 0
git diff --check -- software/spu_gpu_eval/cli.py software/spu_gpu_eval/device_inspect.py software/tests/test_gpu_pixel_inspect_s3.py docs/gpu_scene_preview.md spu_strategy/contract_gpu_pixel_inspector_s3_2026-10-05.md
```

Then run the mandatory gates in root `AGENTS.md` order: repository verifier;
ROTC and IROTC traces; rational robotics and SOM; Lucas MAC oracle; Padé batch
inversion; detached Artix-7 100T Padé synthesis. S3 changes no RTL, so `TB_FILTER`
triage is not applicable. Use a new output child of
`build/gpu_evaluation/s3_pixel_inspector_20261005/` for the detached synthesis.
After `LAUNCHED`, record its unit and evidence path and end the agent turn.

## 5. Stop conditions

- Stop if the two decision APIs disagree with their existing S1/S2 tests.
- Stop if the report needs a second geometry or arithmetic implementation.
- Stop if report JSON depends on timestamps, paths, host identity, or dict order.
- Stop if invalid input writes stdout JSON or creates a report artifact.
- Stop before UART, JTAG, programming, wiring, power, or physical GPU claims.
- Do not claim cycle accuracy, shader execution, or complete SPU emulation.
