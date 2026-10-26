# Newcomer software walkthrough — October 7, 2026

The walkthrough completed with a durable `COMPLETE`, exit 0, in 22 seconds.
That exit means collection completed; it does **not** mean every demo passed.
Individual exits and raw output are in
[the walkthrough results](../build/newcomer_walkthrough_20261007/walkthrough_01/walkthrough_results.json).

## Two checkout states

The committed state was an independent local clone of revision
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`. The candidate was a second clone
with 113 explicitly hashed working files overlaid from
[the frozen source manifest](../build/newcomer_walkthrough_20261007/freeze_01/source_manifest.json).
Neither was an anonymous remote clone. The candidate was intentionally dirty;
the main checkout and all historical evidence were preserved.

Each used a fresh Python virtual environment, with user site packages and
`PYTHONPATH` disabled. No third-party packages were installed. VM, robotics and
GPU evaluation ran in software; no hardware traffic or FPGA build occurred.

| Documented command | Committed clone | Working candidate |
|---|---|---|
| VM checks | Exit 0; 89 passed, 0 failed | Exit 0; same result |
| Twelve-step Fibonacci program | Exit 0; `[PASS]` | Exit 0; `[PASS]` |
| Exact six-joint robotics demo | Exit 2; script absent | Exit 0; reference agreement and closure |
| GPU ideal preview | Exit 1; module absent | Exit 0; artifacts generated |
| GPU device preview | Exit 1; module absent | Exit 0; artifacts generated |
| GPU pixel inspection | Exit 1; module absent | Exit 0; expected decisions |

The blocker is publication completeness, not a missing third-party dependency.
The committed tree lacks `tools/rational_robotics_unshared_demo.py`,
`software/lib/rational_robotics_unshared.py`, `software/spu_gpu_eval/`, and
`examples/gpu/`, along with the new candidate guides. The source manifest records
the complete overlay; it is not a proposed bulk commit. Review the required
files and their licenses/tests before publishing a focused change.

## Runnable software path

From the repository root:

```bash
python3 software/spu_vm_test.py
python3 software/spu_forge.py simulate software/programs/fibonacci_pulse.sas --steps 12 --quiet
```

Expected VM summary: `spu_vm_test.py: 89 passed, 0 failed`, followed by `PASS`.
The program reports `PC=12`, `steps=12`, `snap_failures=0`, and `[PASS]`.
Git and Python 3.10+ are sufficient for this path. Icarus Verilog and a C++17
compiler are prerequisites for the separate full regression, not these demos.

With the candidate demo files present:

```bash
python3 tools/rational_robotics_unshared_demo.py
python3 -m software.spu_gpu_eval.cli preview examples/gpu/t1d_two_triangle.json --out build/gpu_evaluation/quickstart/ideal_01
```

The robotics command compares the exact six 60-degree joints and recovery
against the maintained reference, then prints
`PASS: fused six-joint chain matches reference and closes exactly`.
The GPU command requires a new output directory and writes `scene_packet.bin`,
`preview.ppm`, `pixel_decisions.json`, and `manifest.json`.

The pixel inspector at `(320,0)` selected primitive 0, RGB `[15,0,0]`, in both
paths. Ideal depth was 2000 and finite-width model depth was 1999, as documented.
Image and model agreement do not establish physical display or clock behavior.

## Findings and limits

The README now starts with the tested direct-source VM commands, gives explicit
expected output, and labels the unpublished candidate demos. The first-hour
guide separates quick software prerequisites from the optional full suite.
The supported-demo page distinguishes Python arithmetic from CPU RTL evidence.

This walkthrough did not validate editable installation, the installed console
scripts, every example, the full regression, or a remote checkout. Packaging
and publication remain separate reviewable work. CPU timing, GPU hardware holds,
archive qualification and production pruning are unaffected by these results.
