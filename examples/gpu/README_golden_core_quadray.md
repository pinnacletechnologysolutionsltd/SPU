# Golden Core Quadray GPU demonstration

Open `baby_quadray_covariance.html` locally for the interactive coordinate and weighted-cycle demonstration. It uses integer Quadray controls, exact `Q(sqrt(3))` pair arithmetic for the four-cycle, and SVG only for the display.

The four-coordinate point convention follows the recovered material in Andy Thomson, [*Synergetics Cookbook*](../../Synergetics-Cookbook.pdf), v0.19 (2026-08-06, CC BY-NC-SA 4.0), and the earlier Quadray/IVM construction discussed there. The exact view matrix and finite-pixel conversion below are new, explicit demonstration choices; they are not claims about the cookbook's renderer or the FPGA rasterizer. The source PDF remains unchanged.

## Representation and transforms

A point `q=(A,B,C,D)` is unchanged by adding a common scalar. The reference chooses its unique zero-sum representative

```text
q0[i] = q[i] - (A+B+C+D)/4.
```

With tetrahedral basis vectors `A=(1,1,1)`, `B=(1,-1,-1)`, `C=(-1,1,-1)`, `D=(-1,-1,1)`, the exact Cartesian map is

```text
x = A + B - C - D
y = A - B + C - D
z = A - B - C + D.
```

The squared distance is the Quadray quadrance `sum_(i<j) (q[i]-q[j])^2`; the same result is obtained from the Cartesian difference. Active component permutations send source basis index `i` to target index `permutation[i]`. The determinant on physical 3-space is the permutation sign: 12 of the 24 maps are proper rotations and 12 reverse orientation. The demo keeps vertex labels visible so an unlabelled match is not confused with a label-preserving match.

## Exact view and finite pixel boundary

The orthographic view is the rational rotation

```text
       [ 1   8   4 ]
R = 1/9[ 8   1  -4 ]
       [-4   4  -7 ]
```

For view point `(u,v,d)`, the scene compiler maps

```text
pixel_x = round_even(319.5 + 80*u)
pixel_y = round_even(239.5 - 80*v)
depth   = round_even(32768 + 1000*d)
```

with exact rational arithmetic and nearest-integer, ties-to-even rounding. The resulting T1d scene contains pixel coordinates and depth only. Quadray coordinates, the rational view and rasterization are separate stages.

## Reproduce the host-CPU T1d software model scene

Both preview commands run on the host CPU: one uses the exact reference
rasterizer, and the other models finite-width T1d datapath behavior. They do
not execute compute shaders. Use an ordinary image viewer to display the
resulting PPM files.

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/golden_core_quadray_covariance.json --out build/gpu_evaluation/quadray_covariance_preview
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_quadray_covariance.json --out build/gpu_evaluation/quadray_covariance_device_preview
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/golden_core_quadray_covariance.json --x 435 --y 195
```

The preview command creates a deterministic PPM plus packet, pixel-decision and source manifest artifacts. The inspect command reports the ideal exact reference and finite-width T1d device model at a selected pixel. Neither command qualifies the FPGA rasterizer or establishes a performance advantage.

The independent expected projections, signed areas, sample pixels, and weighted covariance vectors are frozen in `fixtures/golden_core_quadray_projection_reference.json`. Run the focused regression with:

```bash
python3 software/tests/test_gpu_quadray_covariance_scene.py
```

## Edit lesson

The two faces in the scene share vertex C. Moving only triangle 0's C vertex changes the overlap at pixel `(346,266)` into a triangle-1-only sample. Keep the source scene unchanged and make an editable copy:

```bash
mkdir -p build/gpu_evaluation/quadray_covariance_lesson
cp examples/gpu/golden_core_quadray_covariance.json build/gpu_evaluation/quadray_covariance_lesson/scene.json
python3 -c 'import json; from pathlib import Path; p=Path("build/gpu_evaluation/quadray_covariance_lesson/scene.json"); d=json.loads(p.read_text()); d["triangles"][0]["vertices"][2]=[150,350,34435]; p.write_text(json.dumps(d,indent=2)+"\n")'
python3 -m software.spu_gpu_eval.cli preview examples/gpu/golden_core_quadray_covariance.json --out build/gpu_evaluation/quadray_covariance_lesson/baseline
python3 -m software.spu_gpu_eval.cli preview build/gpu_evaluation/quadray_covariance_lesson/scene.json --out build/gpu_evaluation/quadray_covariance_lesson/edited
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/golden_core_quadray_covariance.json --x 346 --y 266
python3 -m software.spu_gpu_eval.cli inspect build/gpu_evaluation/quadray_covariance_lesson/scene.json --x 346 --y 266
```

The baseline pixel is an equal-depth overlap won by triangle 0; after the edit triangle 1 alone covers that pixel. Both decisions are checked by the ideal reference and the finite-width device model.

## Exact labelled tetrahedron views through T1d

The frozen view bundle exercises the actual T1d software scene path with one
labelled Quadray tetrahedron under identity, a proper BCD rotation, and a BC
reflection. The pipeline is exact until the explicit finite-pixel boundary:

```text
Quadray basis and S4 map
  → Cartesian coordinates
  → rational orthographic view
  → ties-to-even pixel/depth quantization
  → two T1d triangle records
  → ideal reference and finite-width device-model frames
```

T1d's current `t1d-two-triangle-v1` profile accepts exactly two triangles.
Each view therefore rasterizes the labelled faces ABC and ADC, using all four
labelled vertices; it does not render the tetrahedron's complete closed
surface. The browser Quadray lesson can show the complete interactive
tetrahedron, but that browser drawing is not this rasterizer result.

Run the exact transform/projection and frozen pixel regression:

```bash
python3 software/tests/test_gpu_quadray_tetra_views.py
```

Render each frozen view in both the ideal path and the finite-width T1d device
model. Each output directory must be new; select fresh suffixes if these names
already exist.

```bash
python3 -m software.spu_gpu_eval.cli preview examples/gpu/golden_core_tetra_views/identity.json --out build/gpu_evaluation/gc_tetra_20261017/identity_ideal
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_tetra_views/identity.json --out build/gpu_evaluation/gc_tetra_20261017/identity_device
python3 -m software.spu_gpu_eval.cli preview examples/gpu/golden_core_tetra_views/rotate_bcd.json --out build/gpu_evaluation/gc_tetra_20261017/rotate_bcd_ideal
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_tetra_views/rotate_bcd.json --out build/gpu_evaluation/gc_tetra_20261017/rotate_bcd_device
python3 -m software.spu_gpu_eval.cli preview examples/gpu/golden_core_tetra_views/reflect_bc.json --out build/gpu_evaluation/gc_tetra_20261017/reflect_bc_ideal
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/golden_core_tetra_views/reflect_bc.json --out build/gpu_evaluation/gc_tetra_20261017/reflect_bc_device
```

The [reference fixture](../../fixtures/golden_core_t1d_tetra_views_reference.json)
freezes transformed vertex pixels, signed screen areas, scene and packet hashes,
and diagnostic pixel outcomes. The test independently recomputes projection
from the four basis vectors and checks both renderers against the frozen pixel
expectations. It also perturbs a vertex as a negative control. These results
qualify the specified software path only; they do not claim physical FPGA
execution or GPU acceleration of Golden Core arithmetic.

## C++ renderer identities

The standalone C++17 [SIM-1 package](../../../spu-sim/README.md) is a separate
renderer that accepts the frozen two-triangle T1d packet and returns a complete
RGB8 frame. Its three Golden Core outputs match the Python finite-width T1d
device-model frames byte-for-byte; see the [comparison report](../../docs/GOLDEN_CORE_T1D_SIM1_COMPARISON_2026-10-17.md).

Do not confuse it with either of these tools:

- The root-checkout legacy C++ VM at `software/vm/spu_vm` accepts SAS or VM
  binary input and has no T1d packet/frame interface.
- The C++ Vulkan utility `software/gpu_vulkan/gpu_raster_compute.cpp` evaluates
  one triangle's coverage and reports covered-pixel coordinates. It has no
  T1d depth, color, or complete-frame output.

The Python exact reference and finite-width model remain host-CPU programs as
well; none of these results are physical FPGA observations or compute-shader
execution. See the [project status](../../docs/PROJECT_STATUS_2026-10-17.md#gpu-paths)
for the release capability table.
