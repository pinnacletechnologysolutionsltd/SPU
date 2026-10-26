# Golden Core T1d scene comparison — Python and SIM-1

**Date:** 2026-10-17
**Status:** Bounded software comparison; no physical GPU observation
**Scenes:** Identity, proper BCD rotation, BC reflection

## Result

Each frozen Quadray scene was compiled to the existing 64-byte
`gpu.scene.t1d.two-triangle-v1` packet, rendered by the standalone SIM-1 C++
`spu-sim gpu render` command, and compared byte-for-byte with the Python
finite-width T1d device-model frame. All three complete RGB8 frames matched:
each is 921,600 bytes and the Python and C++ SHA-256 values are identical.
This establishes cross-implementation consistency for these inputs; the
matching results do not establish independent correctness or FPGA pixel
equality.

| View | Packet SHA-256 | Python and SIM-1 RGB8 SHA-256 | Result |
|---|---|---|---|
| Identity | `e2ef44e4087e7c8a2d1a67c3ef24abde1e2542d9b8f5a74c11753762dad43942` | `434e6b5525fcfc75ddb8e5888a1e6cda0c4e877c5d08518af90a5aa01ba90691` | Exact, 921,600 bytes |
| Proper BCD rotation | `8d829ce865a2053578e5369b437ec9b603023cbf624e6a6d573f112af7ee7b37` | `f8a6afbfeb929e5079b800893acf5fb15623c0e9a09807d61bac1d4d66baaad4` | Exact, 921,600 bytes |
| BC reflection | `c0c439c1955a43f86793fa439aa2d1617a4a671a8237850c5acde802f63b772d` | `ad7415db404a5189012b1dfcd30bd096317420d631f4555a7cf3b4459e162c7e` | Exact, 921,600 bytes |

The C++ executable used was `/home/user/Projects/hardware/spu-sim/build/release/spu-sim`, SHA-256
`39eb6c8858903a733011e26f0da4b62e88c1045e5c851c3d1982bf7f721c4e0f`.
The reciprocal ROM was `hardware/rtl/arch/gpu_reciprocal_lut_q15.mem`,
SHA-256 `a64327c1bc0c8c74a4fb8c849a922a1f8b3d6a6e2e3bb58951d11f2012bb5248`.
The machine-readable run record is
`build/gpu_evaluation/gc_tetra_20261017/sim1_cpp_frame_comparison.json`.
For a newcomer workflow that generates the packet, renders both paths,
compares the complete frame and saves a viewer-ready image, run
`python3 tools/run_gc_t1d_newcomer.py --out build/gpu_evaluation/<new-run-name>`.

The packaged newcomer command was rerun on 17 October using a fresh output
directory. Its generated identity packet produced matching 921,600-byte
frames with SHA-256
`434e6b5525fcfc75ddb8e5888a1e6cda0c4e877c5d08518af90a5aa01ba90691`.
The runner recorded SPU revision `4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`
as dirty and SIM-1 revision `013acd4230442e0e126640604c11176f274962ab` as
clean. The local evidence is at
`build/gpu_evaluation/newcomer_pins_20261017/cross_renderer_comparison.json`;
it demonstrates the workflow in the current development environment, not a
clean-checkout newcomer review. The SPU changes are not in that HEAD, and the
separate SIM-1 checkout has no configured remote. The review is pending until
both immutable source revisions are fetchable. The runner accepts
`--expected-spu-revision`, `--expected-sim1-revision`, and
`--require-clean-checkouts` for that review.

## Keep the implementations distinct

- **Python T1d:** host-CPU exact reference renderer and host-CPU finite-width
  device model; both support reproducible complete-frame output.
- **Standalone SIM-1 C++:** separate C++17 package at
  [`../spu-sim`](../../spu-sim/README.md); its accepted bounded T1d capability
  consumes the frozen two-triangle packet and returns RGB8 frame bytes. This
  comparison extends evidence to these three packets; it does not replace the
  accepted SIM-1 baseline fixture or broaden the profile contract.
- **Root-checkout legacy C++ VM:** `software/vm/spu_vm` accepts SAS or VM binary
  inputs and has no T1d packet/frame interface.
- **C++ Vulkan utility:** `software/gpu_vulkan/gpu_raster_compute.cpp` evaluates
  coverage for one triangle and returns covered-pixel coordinates. It does
  not implement T1d packet decoding, depth, primitive color, or complete RGB8
  frames.

The three Golden Core fixtures each contain the two labelled faces ABC and ADC
because the current T1d packet profile carries exactly two triangles. These are
software renderer results, not FPGA execution, physical pixel equality, or a
GPU compute-shader result. T1H H1 remains HOLD.

The host computer's GPU is not used to accelerate either simulator. “GPU” in
this comparison refers to the simulated SPU T1d rasterizer capability.

## Reproduction

From the SPU checkout, with the separately qualified SIM-1 checkout at
`../spu-sim`:

```bash
SIM=../spu-sim/build/release/spu-sim
ROM=../spu-sim/hardware/rtl/arch/gpu_reciprocal_lut_q15.mem
for view in identity rotate_bcd reflect_bc; do
  python3 -m software.spu_gpu_eval.cli device-preview \
    "examples/gpu/golden_core_tetra_views/${view}.json" \
    --out "build/gpu_evaluation/gc_tetra_20261017/${view}_device_rerun"
  "$SIM" gpu render \
    "build/gpu_evaluation/gc_tetra_20261017/${view}_device_rerun/scene_packet.bin" \
    --output "/tmp/gc_${view}.rgb8" --rom "$ROM"
  python3 -c 'from pathlib import Path; import sys; p=Path(sys.argv[1]).read_bytes(); h=bytes.fromhex("50360a363430203438300a3235350a"); assert p.startswith(h) and len(p)==921615; assert p[len(h):]==Path(sys.argv[2]).read_bytes(), "RGB8 frame mismatch"' \
    "build/gpu_evaluation/gc_tetra_20261017/${view}_device_rerun/device_preview.ppm" \
    "/tmp/gc_${view}.rgb8"
done
```

The `device-preview` output is PPM (`P6` header plus RGB8 body); SIM-1 writes
raw RGB8. The command checks that the complete 921,600-byte frame matches
after removing the 15-byte PPM header. Use new output names on reruns because
preview output directories are immutable.
