# Engineering Contract: GPU T1d Scene Compiler and CPU Preview S1

- **Date:** 2026-10-04
- **Contract ID:** `contract_gpu_scene_compiler_preview_s1_2026-10-04.md`
- **Status:** CLOSED — S1 software implementation and required repository gates passed; no GPU hardware acceptance is implied.
- **Spec Author:** Codex
- **Halt-and-Flag Implementer:** Codex, after drafting
- **Integration Auditor:** `software/tests/test_gpu_scene_compiler_s1.py`, repository gates

## 0. Pre-execution review commands

Run from the repository root:

```bash
git status --short
python3 --version
sha256sum fixtures/gpu_t1d_scene_wire_64b.bin fixtures/gpu_t1d_scene_reference.json
sha256sum hardware/rtl/gpu/spu_scene_loader.v hardware/rtl/gpu/spu_scene_unpack.v hardware/rtl/gpu/spu_scene_profile_unpack.v hardware/rtl/gpu/spu_edge_stepper.v hardware/rtl/gpu/spu_depth_math.v hardware/rtl/gpu/spu_reciprocal_core.v hardware/rtl/gpu/spu_attr_stepper.v hardware/rtl/gpu/spu_depth_compare.v
sed -n '1,280p' spu_strategy/GPU_EVALUATION_PROFILE_AUDIT_2026-10-03.md
cat build/gpu_evaluation/q0_profile_audit_20261004/profile_inventory_01.json
```

Halt if any frozen identity differs from Q0's inventory, if the packet mapping below does not reproduce the retained 64-byte fixture, or if an instruction asks for a hardware operation.

## 1. Objective and scoped files

Implement a dependency-free Python scene compiler and exact CPU preview for the existing T1d two-triangle profile. Accept editable integer vertices, unsigned 16-bit per-vertex depth, and RGB444 colors. Validate the complete scene before writing output. Compile the scene to the frozen `A5 || 63-byte payload` packet. Render 640×480 integer-coordinate samples from an independent exact-rational reference. Save deterministic packet, preview, decision, and source-identity artifacts under a new child of `build/gpu_evaluation/`.

Target files:

```text
software/spu_gpu_eval/__init__.py
software/spu_gpu_eval/scene.py
software/spu_gpu_eval/packet.py
software/spu_gpu_eval/reference.py
software/spu_gpu_eval/preview.py
software/spu_gpu_eval/cli.py
software/tests/test_gpu_scene_compiler_s1.py
examples/gpu/t1d_two_triangle.json
docs/gpu_scene_preview.md
```

Update `docs/index.md` with one link to the tutorial. Preserve all existing user changes. Do not modify RTL, board constraints, UART/JTAG tools, frozen fixtures, generated files, or historical evidence.

Dependencies: Python 3.10+ standard library only. Use integers and `fractions.Fraction`; do not use floating point. P6 PPM output uses RGB8 bytes obtained by expanding each four-bit channel `n` to `17*n`; no imaging package is required.

## 2. Frozen input and packet contract

The editable scene JSON schema is exactly:

```json
{
  "format": "spu_gpu_scene_v1",
  "profile": "t1d-two-triangle-v1",
  "width": 640,
  "height": 480,
  "triangles": [
    {"vertices": [[600, 0, 3600], [40, 0, 400], [120, 460, 700]], "rgb": [15, 0, 0]},
    {"vertices": [[600, 0, 400], [40, 0, 3600], [520, 460, 700]], "rgb": [0, 15, 0]}
  ]
}
```

Each vertex is `[x,y,z]` in canonical input order V0,V1,V2. Require exactly two triangles; exactly three integer vertices per triangle; `0<=x<=639`, `0<=y<=479`, `0<=z<=65535`; exactly three RGB integers in `0..15`; exact keys and format/profile values; non-boolean integers only; and nonzero signed twice-area. Require `width` and `height` to be non-boolean integers with `width == 640` and `height == 480`. Reject all other dimensions and all malformed or unsupported inputs before creating the output directory or any output file.

For each triangle, derive wire edges in slot order `V0→V1`, `V1→V2`, `V2→V0` using:

```text
a = yj - yi
b = xi - xj
c = -(a*xi + b*yi)
f(x,y) = a*x + b*y + c
```

If the three opposite-vertex evaluations are negative, negate all three `(a,b,c)` tuples. Require them all strictly positive after orientation normalization. This keeps hardware coverage at `f>=0` for either input winding. Never import or call `gpu_depth_v2_oracle.edge_coeffs` or `triangle_edges` in the packet compiler.

Wire depth fields pair with the opposite vertices of those edge slots:
`z0=z(V2)`, `z1=z(V0)`, `z2=z(V1)`. Do not reorder the input vertex array to obtain this mapping.

For each 252-bit record, append low-to-high fields in this exact order and width:

```text
a0:16s, b0:16s, c0:32s,
a1:16s, b1:16s, c1:32s,
a2:16s, b2:16s, c2:32s,
r:4u, g:4u, b:4u, z0:16u, z1:16u, z2:16u
```

Encode signed values as their 2's-complement bit pattern. Place record 0 in payload bits `0..251` and record 1 in bits `252..503`; serialize the 504-bit payload as 63 little-endian bytes. Prepend exactly byte `A5`. Reject any coefficient outside its signed field range. The baseline example must compile byte-for-byte to `fixtures/gpu_t1d_scene_wire_64b.bin`, length 64, SHA-256 `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`.

## 3. Exact reference and preview contract

`reference.py` independently derives coverage and barycentric depth from the input vertices using oriented integer areas. It must not import the packet edge-conversion function or consume serialized edge coefficients. Coverage samples are integer `(x,y)` points in the active rectangle, with closed boundaries and no half-pixel offset. Both triangles may cover a shared edge. For covered triangles, compute exact rational affine depth from input vertex `z`; smaller depth wins and an exact tie selects triangle 0.

The preview is ideal geometry/depth only. It must label its manifest `device_model=false` and `physical_observation=false`. Do not claim that the preview reproduces the reciprocal approximation, finite-width depth accumulator, loader activation, board RGB truncation, or current FPGA state. Keep ideal exact depth and hardware-semantic observations distinct.

For a valid scene, `python3 -m software.spu_gpu_eval.cli preview <scene.json> --out <new-directory>` writes exactly:

```text
scene_packet.bin       # 64-byte T1d transaction
preview.ppm            # P6, 640x480, max value 255, full RGB444-expanded color
pixel_decisions.json   # coverage, exact rational depth, winner and RGB at sample points
manifest.json          # sorted deterministic JSON, scene/compiler hashes and output hashes
```

The decision file must include the six coordinates and expectations in `fixtures/gpu_t1d_scene_reference.json`, plus `(320,0)` to expose inclusive shared-edge coverage and primitive-0 tie selection. Name the fixed values `baseline_fixture_expectation` and the computed values `actual_scene_decision`; identify the expectation scope as the frozen baseline fixture so edits are not presented as matching those values. The manifest must identify the profile/schema, the input JSON SHA-256, the reference fixture SHA-256, source hashes for all compiler/reference modules, source hashes for the eight frozen profile RTL files named in §0, repository HEAD, repository worktree state (`clean` or `dirty`), packet and preview hashes, and `device_model=false`. The profile source hashes must match Q0's `profile_inventory_01.json` at implementation preflight. Do not include timestamps or absolute paths in deterministic outputs. Refuse an existing output directory. Generate the files in a temporary sibling directory and atomically rename it to the requested output path only after every artifact is complete; remove the temporary directory on failure so failed runs leave no partial output.

## 4. Required implementation sequence

1. Run §0; record current HEAD, worktree status, matching eight-file profile source hashes, and compiler/reference module hashes in `manifest.json` for the S1 experiment.
2. Add the exact baseline JSON from §2. Do not edit the binary fixture.
3. Implement strict validation in `scene.py`; validation must finish before output creation.
4. Implement packet-only edge derivation and the slot/depth permutation in `packet.py`.
5. Implement independent exact coverage/depth in `reference.py`; compare reference decisions with fixture expectations without reading packet edge fields.
6. Implement deterministic PPM, decision JSON, and manifest output in `preview.py` and `cli.py`.
7. Add the user tutorial with the exact command below and the limits in §3.
8. Add falsifiable unit/CLI tests in `software/tests/test_gpu_scene_compiler_s1.py`. Keep new single-purpose modules 50–150 lines where practicable; split responsibility instead of growing one large file.

## 5. Acceptance commands and vectors

Run from the repository root. Use a fresh output path; do not overwrite prior evidence.

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/s1_t1d_scene_20261004/run_01
python3 software/tests/test_gpu_scene_compiler_s1.py
```

The test must falsifiably check:

1. Baseline packet equals the frozen fixture byte-for-byte and has the frozen SHA-256.
2. All six fixture sample pixels match coverage, winner, and RGB; `(320,0)` is covered by both triangles and selects triangle 0 on the exact depth tie.
3. Changing triangle 0 V2 from `(120,460,700)` to `(120,240,700)` changes the packet and changes `(100,300)` from red to black.
4. Collinear vertices, x=640, y=480, z=65536, RGB=16, boolean values in integer fields including `width` and `height`, `width` or `height` values other than 640 or 480, `640.0`/`480.0`, each missing required scene field, missing `vertices` or `rgb`, wrong keys, wrong profile, and wrong primitive count are rejected; no output directory or files are created for rejected input.
5. An approximation-sensitive geometry `(0,0),(639,1),(1,478)` has `abs(D)=305441`, normalization right shift 3, and nonzero discarded low bits `1`. Record this metadata only; do not report a simulated device depth or winner from it.
6. PPM dimensions/header/payload length, deterministic hashes, and all manifest fields are correct.

The tutorial command is:

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/s1_t1d_scene_20261004/tutorial_run_01
```

Explain that the JSON is the manual edit point and that changing a vertex changes both the compiled packet and preview. The S1 tutorial is software-only and must not instruct the reader to send a packet to hardware.

## 6. Mandatory repository gates

After §5 passes, run these root gates in order and record every exit/result:

```bash
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py
```

Run the mandatory Artix-7 Padé synthesis using the detached runner because it exceeds 60 seconds:

```bash
tools/run_detached_job.sh --output build/gpu_evaluation/s1_t1d_scene_20261004/a7_pade_gate_01 --timeout 1800 --notify-desktop -- /usr/bin/bash -lc 'A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all'
```

After `LAUNCHED`, record the unit and evidence path and end the agent turn. Interpret a later result only when exactly one terminal marker exists. Do not call the Padé artifact a GPU build or silicon evidence. `TB_FILTER` triage is not applicable because S1 changes no RTL; the full repository gate exercises the existing GPU test suite.

## 7. Stop conditions

- Halt if the baseline packet does not match the frozen 64-byte fixture; propose a minimal mapping correction before editing.
- Halt if exact reference coverage or depth disagrees with the six frozen points; do not change fixture expectations or RTL.
- Halt if output validation can leave partial artifacts, if a tie is not deterministic, or if an input accepted by the validator exceeds a declared packet field range.
- Halt if any implementation requires floating point, a new dependency, a protocol change, RTL modification, UART/JTAG access, bitstream build/programming, or a claim about physical GPU acceptance.
- A Q0 profile audit PASS, software preview PASS, repository PASS, and physical GPU/display acceptance are separate results.

## 8. Execution record

Preflight confirmed the eight profile RTL source hashes match Q0's
`profile_inventory_01.json`; the retained packet fixture SHA-256 is
`aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`.

| Gate | Result | Evidence |
|---|---|---|
| Tutorial preview CLI | PASS, exit 0; emitted the four specified artifacts | [`run_02/`](../build/gpu_evaluation/s1_t1d_scene_20261004/run_02/) |
| S1 scene compiler suite | PASS, 6 tests | `python3 software/tests/test_gpu_scene_compiler_s1.py` |
| `git diff --check -- docs/index.md` | PASS, exit 0 | Command result recorded at closeout |
| New-file whitespace scan | PASS; no trailing whitespace | Command result recorded at closeout |
| `python3 tools/doc_audit.py --check links` | Exit 0; 24 regex candidates, matching the Q0 audit's existing inventory | New tutorial link target was manually confirmed |
| `bash tools/verify_repo.sh` | COMPLETE, exit 0; 238 pass, 0 fail | [`repo_gate_02/`](../build/gpu_evaluation/s1_t1d_scene_20261004/repo_gate_02/); exactly one `COMPLETE` marker |
| ROTC VM/RTL trace | PASS; 336 checks | `python3 software/tests/test_rotc_vm_rtl_trace.py` |
| IROTC VM trace | PASS; 9 passed, 0 failed | `python3 software/tests/test_irotc_vm_trace.py` |
| Rational robotics | PASS; 104 checks | `python3 software/tests/test_rational_robotics.py` |
| Rational SOM | PASS; 24 checks | `python3 software/tests/test_rational_som.py` |
| Lucas MAC oracle | PASS; 166,666 identity macros and 999,996 primitive operations | `python3 software/tests/test_lucas_mac_oracle.py` |
| Padé batch inversion | PASS; 25 checks | `python3 software/tests/test_pade_batch_inversion.py` |
| Artix-7 100T Padé synthesis | COMPLETE, exit 0; separate Padé target | [`a7_pade_gate_01/`](../build/gpu_evaluation/s1_t1d_scene_20261004/a7_pade_gate_01/); exactly one `COMPLETE` marker |

`TB_FILTER` triage was not applicable because S1 changes no RTL. No UART,
JTAG, FPGA programming, wiring, or power operation was performed. This closeout
establishes software and repository-gate results only; GPU hardware and display
acceptance remain separate.
