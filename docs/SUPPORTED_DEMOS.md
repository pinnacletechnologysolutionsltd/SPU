# Supported demonstrations

This page links the current software walkthroughs and optional Wukong physical
demonstration. The software demonstrations use browser rendering unless a
T1d simulator command is named explicitly; neither implies FPGA execution.
Start with software; use the Wukong procedure only when the board, monitor and
UART wiring are available. See the
[project status page](PROJECT_STATUS_2026-10-17.md) for release boundaries.

## Checkout availability

The October 7 [newcomer walkthrough](NEWCOMER_WALKTHROUGH_2026-10-07.md)
passed the VM commands from a clean local clone. Robotics and the offline GPU
preview passed in the frozen working candidate, but their source files were
absent from the tested committed revision. Inclusion remains a publication
prerequisite; candidate results are not an anonymous-clone qualification.

These software commands need Python 3.10 or newer and its standard library.
They need no FPGA, serial port, or Python package installation. Run them from
the repository root.

## First graphics run: matching Python and SIM-1 frames

The first graphics entry point generates one frozen labelled tetrahedron
scene, renders its T1d packet through Python and standalone SIM-1, compares the
complete RGB8 frames, and saves a viewable PPM:

```bash
python3 tools/run_gc_t1d_newcomer.py --out build/gpu_evaluation/newcomer_run_01
```

Open `build/gpu_evaluation/newcomer_run_01/sim1_frame.ppm` in an image viewer.
The JSON evidence records packet/frame hashes and both repository revisions.
Each run needs a new output directory. To check pinned, clean source trees,
use the released commit IDs for both checkouts:

```bash
python3 tools/run_gc_t1d_newcomer.py \
  --expected-spu-revision <SPU_COMMIT> \
  --expected-sim1-revision <SIM1_COMMIT> \
  --require-clean-checkouts \
  --out build/gpu_evaluation/newcomer_pinned_run_01
```

The identity-scene acceptance is: the runner exits successfully, reports
`complete-frame comparison: PASS`, records `byte_exact_match: true` for all
921,600 bytes, and the PPM opens in an image viewer. The expected RGB8 SHA-256
is `434e6b5525fcfc75ddb8e5888a1e6cda0c4e877c5d08518af90a5aa01ba90691`.
Record the operating system, compiler, two pinned revisions and whether the
image opened as part of the newcomer review.

The clean-checkout newcomer review is **pending**. The current SPU source
changes are uncommitted, and the separate SIM-1 checkout has no configured
remote. The local comparison is useful evidence but is not a clean-checkout
release review. Record the source URLs and immutable commits before asking a
newcomer to run the pinned command. This example exercises SIM-1's bounded
two-triangle T1d packet renderer; it does not run Golden Core arithmetic on a
GPU or establish FPGA pixel equality.

When the two pinned source checkouts are available as sibling directories,
build SIM-1 from its checkout using the documented C++17/CMake path:

```bash
cmake -S ../spu-sim -B ../spu-sim/build/release -DCMAKE_BUILD_TYPE=Release
cmake --build ../spu-sim/build/release --parallel
ctest --test-dir ../spu-sim/build/release --output-on-failure
```

These are the build and unit-test commands in the standalone [SIM-1
README](../../spu-sim/README.md). The exact clone URL and release commits must
be recorded before this becomes a clean-checkout instruction; currently only
the SPU checkout has a configured Git remote. The documented configure, build,
and CTest commands passed against the available SIM-1 checkout on 17 October;
this did not test a fresh clone or another person's environment.

## Exact robotics in software

From the repository root, run:

```bash
python3 tools/rational_robotics_unshared_demo.py
```

The example applies six exact 60-degree joints through the opt-in unshared
kernel, materializes the endpoint and recovery, and compares both with the
maintained robotics reference. The expected terminal line is
`PASS: fused six-joint chain matches reference and closes exactly`.

This demonstrates software arithmetic for the checked chain, independently of
the experimental CPU RTL integration and its FPGA resource/timing results.

Surd Register S0 is accepted for its tested software scope: the October 7
amendment (attempt 04) resolved the zero canonicalization defect, passing
focused synthetic verification and retained-corpus checks (`PASS_RETAINED`) with
terminal status recorded in
`build/spu_surd_register/s0_20261007_attempt04/run_01/terminal.txt`. Hardware
synthesis and ISA encoding remain separate future work.

## T1G GPU scene sequence on Wukong

The frozen T1G image can display the three checked scenes in order A → B → C.
Run [the Wukong GPU bring-up runbook](GPU_BRINGUP_RUNBOOK.md), which covers
image hash verification, SRAM loading, stable VGA lock, UART sends, expected
observations and recovery. Scene A should show red-left/green-right inverted
triangles. B and C should each visibly change the image while signal lock
remains stable. The one-command runner sends A/B/C twice and writes a packet
transcript and command output for each scene; stop at the first sender failure.

Before connecting to hardware, validate the sender and all fixture hashes
offline:

```bash
for scene in A B C; do
  python3 tools/send_gpu_t1g_scene.py --scene "$scene" --validate-only
done
```

The recorded evidence is operator-observed display output. A successful host
write and UART drain do not establish FPGA receipt, CRC acceptance or scene
activation. This is visual evidence, not captured-pixel evidence.

## Quadray to Golden Core

This research walkthrough has three steps. It is software-only unless you
separately choose the optional T1d simulator commands.

1. Open [`baby_quadray_covariance.html`](../examples/gpu/baby_quadray_covariance.html)
   in a browser. Change a coordinate and compare it with adding a common
   offset; the page illustrates gauge equivalence and orientation changes.
2. Open [`icosahedron_phi.html`](../examples/golden_core/icosahedron_phi.html)
   to inspect exact `Q(√5)` coordinate readouts and symmetry classification.
   The camera and pixel placement are approximate browser display values.
3. Open [`gc5b_seed_dynamics.html`](../examples/golden_core/gc5b_seed_dynamics.html)
   to compare four seed profiles, update laws, and frozen observables. Python
   produced the exact states and fixture; the page only visualizes that data.

Run the exact Golden Core checks from the repository root:

```bash
python3 software/tests/test_golden_core_gc3.py
python3 software/tests/test_golden_core_gc4.py
python3 software/tests/test_golden_core_gc5.py
python3 software/tests/test_golden_core_gc5a.py
python3 software/tests/test_golden_core_gc5b.py
python3 software/tests/test_golden_core_gc6.py
```

The Quadray scene also has an optional T1d Python software-simulator path. Its
preview, device-preview, inspect, and editable-copy commands are in the
[GPU lesson guide](../examples/gpu/README_golden_core_quadray.md). That
finite-width graphics model does not execute the Golden Core edge operator.
The first-run command above exercises one identity scene. Four tool identities
matter: the **Python T1d** reference and finite-width device model both run on
the host CPU; the **standalone SIM-1 C++ renderer** accepts the frozen T1d
packet and returns a full frame; the root-checkout **legacy C++ VM** has no
T1d scene interface; and the **C++ Vulkan utility** only evaluates one
triangle's coverage. The browser Quadray lesson is a separate interactive
visualization. See the [comparison report](GOLDEN_CORE_T1D_SIM1_COMPARISON_2026-10-17.md)
for all three frozen views, limits, and renderer hashes. See the [Golden Core
research snapshot](GOLDEN_CORE_RESEARCH_SNAPSHOT_2026-10-17.md) for exact
results and claim limits.

For an end-to-end rasterizer example, the same guide has three frozen labelled
tetrahedron views: identity, a proper Quadray rotation, and a reflection. The
exact projection fixture is checked against both the ideal renderer and the
finite-width T1d device model by
`python3 software/tests/test_gpu_quadray_tetra_views.py`; the guide also gives
commands to render both model paths. T1d currently rasterizes two selected
tetrahedron faces per view, not the complete closed solid. This is software
GPU-path evidence, separate from the browser lesson and physical FPGA results.

## Development and research evidence

- [GPU software evaluation](gpu_scene_preview.md) covers the offline T1d
  preview, edit and inspect path.
- [Development status](CURRENT_STATUS.md) and the
  [GPU runbook](GPU_BRINGUP_RUNBOOK.md) describe supported configurations and
  recovery.
- [Archived research and session evidence](archive/bench_sessions/) preserves
  failed attempts and superseded plans. The
  [documentation index](index.md) points to current sources of truth.

Adaptive materials, SOM-generated choices, and broader register-architecture
proposals remain research work rather than supported demonstrations. Dated
plans stay in the archive; the newcomer path above links only to the current
examples and their evidence boundaries.
