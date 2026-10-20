# VM, exact robotics, and offline GPU quickstart

Run from a source checkout with Git and Python 3.10 or newer. All commands use
the Python standard library. No package installation, FPGA toolchain, serial
port, or board is needed. Python's optional `venv` support must be installed
to create the isolated environment below. A PPM-compatible viewer is optional
for looking at the generated images.

```bash
python3 -m venv build/newcomer_venv
build/newcomer_venv/bin/python software/spu_vm_test.py
build/newcomer_venv/bin/python software/spu_forge.py simulate software/programs/fibonacci_pulse.sas --steps 12 --quiet
build/newcomer_venv/bin/python tools/rational_robotics_unshared_demo.py
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/quickstart/ideal_01
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/quickstart/device_01
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

The VM summary is `spu_vm_test.py: 89 passed, 0 failed`, followed by `PASS`.
The Fibonacci program reports `PC=12`, `steps=12`, `snap_failures=0`, and
`[PASS]`. The robotics demo prints
`PASS: fused six-joint chain matches reference and closes exactly` after
comparing its endpoint and recovery with the maintained exact reference.

The ideal GPU preview writes `scene_packet.bin`, `preview.ppm`,
`pixel_decisions.json`, and `manifest.json`. The device preview writes the same
packet plus `ideal_preview.ppm`, `device_preview.ppm`, `pixel_comparison.json`,
and `manifest.json`. Each output directory must be new; choose another name
for a rerun. At `(320,0)` both paths select triangle 0 with RGB `[15,0,0]`;
ideal depth is 2000 and the finite-width model's depth is 1999.

## Make one saved scene edit

The second checked-in JSON scene changes triangle 0's third vertex from
`[120,460,700]` to `[120,240,700]`. Its red triangle becomes shorter while
the green triangle stays in place. Preview and inspect it without modifying
the original scene:

```bash
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle_vertex_b.json --out build/gpu_evaluation/quickstart/edited_01
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle_vertex_b.json --out build/gpu_evaluation/quickstart/edited_device_01
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle_vertex_b.json --x 100 --y 200
build/newcomer_venv/bin/python -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle_vertex_b.json --x 300 --y 200
```

The edited scene has background at `(100,200)` and only green triangle 1 at
`(300,200)`. The [GPU tutorial](gpu_scene_preview.md) shows how to save your
own edit and explain the changed pixels.

## Dependencies and evidence boundaries

Run directly from the checkout; the installed `spu` console scripts do not
expose this GPU module. Git is needed for preview provenance. The preview
package reads the frozen T1d fixture and reciprocal ROM under `fixtures/`
and `hardware/rtl/arch/`, and hashes selected checked-in RTL sources. Keep
these files with the checkout even though no RTL is compiled here.

The VM checks its software model. Robotics demonstrates the checked exact
six-joint software chain. Ideal GPU output is a mathematical reference;
device output is a settled finite-width software model, without cycle timing.
These commands make no new physical claims. See the
[hardware evidence ledger](hardware_evidence.md) for physical observations.

Missing scripts, modules, fixtures or provenance files are publication gaps.
Missing Python, Git or `venv` support is an environment prerequisite failure.
An assertion, wrong result, or wrong artifact from a complete checkout is a
functional failure. Record the failing command, exit code, and output before
assigning a category. Documentation checks do not authorize archive pruning.
