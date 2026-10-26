# GPU-W1B — T1d scene workbench

**Status:** Complete within tested software and source-snapshot scope
**Date:** 2026-10-17
**Baseline:** [W1-A inventory](contract_gpu_w1a_inventory_2026-10-17.md)
**Scope:** CLI orchestration of existing T1d APIs; no renderer, packet, RTL, ISA, or FPGA changes.

## 1. Source provenance (B0)

The working tree contains unrelated edits and untracked files, so its Git
`HEAD` alone does not identify the tested source. The T1d workbench source was
frozen with base commit
`963a685004b96e275e7e58ebefac98c6e1321597` and the deterministic 84-file
snapshot at:

```text
build/gpu_evaluation/gpu_w1/source_snapshot_02/gpu_w1_source_4cb616e35ae6ace727cfbd9b0cedf4c7630968e1e341bdcc16c7645e41fe2cca.tar
```

Archive SHA-256:
`4cb616e35ae6ace727cfbd9b0cedf4c7630968e1e341bdcc16c7645e41fe2cca`.
The adjacent JSON file records the archive digest, base commit, and SHA-256 for
every included file. The archive pins source identity; the base checkout plus
the archive is the reproduction baseline. The source tree is not represented
as a clean Git commit.

From the repository root, verify and overlay the snapshot on the base commit:

```bash
git clone --shared . /tmp/gpu-w1b-repro
git -C /tmp/gpu-w1b-repro checkout --detach 963a685004b96e275e7e58ebefac98c6e1321597
sha256sum build/gpu_evaluation/gpu_w1/source_snapshot_02/gpu_w1_source_4cb616e35ae6ace727cfbd9b0cedf4c7630968e1e341bdcc16c7645e41fe2cca.tar
cp build/gpu_evaluation/gpu_w1/source_snapshot_02/gpu_w1_source_4cb616e35ae6ace727cfbd9b0cedf4c7630968e1e341bdcc16c7645e41fe2cca.tar /tmp/gpu-w1b-source.tar
tar -xf /tmp/gpu-w1b-source.tar -C /tmp/gpu-w1b-repro
```

The resulting directory contains the exact source and fixture inputs; run the
verification commands below from that directory. The snapshot is a local
evidence artifact and must be retained with its JSON sidecar for later
reproduction.

## 2. Implemented commands (B1–B3)

```bash
python3 -m software.spu_gpu_eval.workbench list
python3 -m software.spu_gpu_eval.workbench render baseline --mode ideal --out build/gpu_evaluation/gpu_w1_baseline_ideal_01
python3 -m software.spu_gpu_eval.workbench render baseline --mode device --out build/gpu_evaluation/gpu_w1_baseline_device_01
python3 -m software.spu_gpu_eval.workbench inspect baseline --x 320 --y 0
python3 -m software.spu_gpu_eval.workbench inspect-packet build/gpu_evaluation/gpu_w1_baseline_ideal_01/scene_packet.bin
```

The catalogue is an explicit 11-scene allowlist with hash-pinned paths. The
renderer commands delegate to the existing ideal and finite-width device-model
preview APIs. They write separate output layouts and manifests that identify
the arithmetic path. Pixel inspection delegates to the S3 oracle and reports
coverage, covered triangles, winner, RGB, and depth equality separately.
Packet inspection delegates to the existing strict decoder: exactly 64 bytes,
start byte `0xA5`, and two T1d triangle records.

## 3. Acceptance fixture and failure behavior (B4)

At `(320,0)` the report must preserve this result:

| Field | Ideal | Device model | Comparison |
|---|---:|---:|---|
| Coverage | overlap | overlap | equal |
| Covered triangles | 0, 1 | 0, 1 | equal |
| Winner | 0 | 0 | equal |
| RGB | 15, 0, 0 | 15, 0, 0 | equal |
| Depth, triangle 0 | 2000 | 1999 | different |
| Depth, triangle 1 | 2000 | 1999 | different |

Unknown scene IDs, modified pinned scenes, invalid pixels, malformed packets,
and output collisions fail with a nonzero status. The commands do not change
the S1/S2/S3 interfaces or implement another rasterizer.

## 4. Focused verification (B5)

```bash
python3 software/tests/test_gpu_workbench_w1.py
python3 software/tests/test_gpu_scene_compiler_s1.py
python3 software/tests/test_gpu_device_model_s2.py
python3 software/tests/test_gpu_pixel_inspect_s3.py
python3 -m software.spu_gpu_eval.workbench list
python3 -m software.spu_gpu_eval.workbench inspect baseline --x 320 --y 0
```

The W1 test also renders twice through each existing path, checks deterministic
artifact bytes and manifests, verifies malformed packet and changed-scene
controls, and checks the depth-difference fixture. Final execution results are
recorded in the W1-B closeout. The shared repository gate is a separate step
and may run only after the S3 detached gate has one durable terminal marker.

## 5. Boundaries

The framebuffer viewer remains W1-C. No rasterization or packet semantics,
hardware, ISA, or FPGA deployment work is in scope. Results describe software
reference/model execution and do not establish FPGA pixel equality.

## 6. Execution record

**B0–B5:** Complete within the stated software scope.

- Source archive hash verified; overlay replayed on a fresh clone at the pinned
  base commit.
- `test_gpu_workbench_w1.py`: 7 tests passed, both in the working tree and
  from the clean snapshot.
- S1: 12 tests passed; S2: RTL/model parity checks passed; S3: 5 tests passed.
  All three also passed from the clean snapshot overlay.
- `list`, `inspect` at `(320,0)`, separate ideal/device renders, and
  `inspect-packet` succeeded. Packet hash was
  `aa2bad57fa5d3d2f777ef5e5405357ac0216a4aafb707d99241050c986ed69ee`.
- The acceptance pixel reports `depths_equal=false` while coverage, covered
  triangles, winner, and RGB agree.
- An initial test assertion expected the RGB frames to differ. That expectation
  was invalid because depth can differ without changing color; it was replaced
  with checks for distinct path outputs/manifests and the explicit depth
  comparison. The corrected W1 test passes.

**B6:** Both detached repository gates have exactly one durable terminal
marker, `COMPLETE`, with exit code 0. S3 evidence is in
`build/symbolic_family_store/s3_20261017_01`. The W1-B repository gate is in
`build/gpu_evaluation/gpu_w1/repo_gate_01`; it completed in 917 seconds with a
1800-second timeout. No physical replay or architecture change was part of
these results.

**Disposition:** W1-B is complete within the tested software and source
snapshot scope. This does not qualify FPGA pixel equality. W1-C remains a
separate tranche.
