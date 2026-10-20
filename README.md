# SPU

An experimental project exploring exact arithmetic and geometric computation
in software and on FPGAs: integer-coefficient arithmetic over Q(√3), Z[φ] and
related rings, with no floating point and explicit failure instead of overflow.

Architectural invention is the ambition; demonstrated utility is the test.

## What is here

- **A software stack.** A Python virtual machine, an assembler, an exact robotics
  chain and an offline GPU model, all runnable without any hardware.
- **Verilog and FPGA builds** for Tang Primer 25K and Wukong Artix-7 boards. Some
  blocks have recorded board observations; the integrated CPU does not.
- **Exact-geometry and classification work**, with its limits stated in the
  [capability matrix](docs/CAPABILITY_MATRIX.md), which separates mathematical
  argument, host software, RTL simulation, FPGA synthesis and physical hardware,
  because none implies another.

## Try it in two minutes

You need Python 3.10 or newer and Git. No board, no installation, no network.

```bash
git clone https://github.com/pinnacletechnologysolutionsltd/SPU.git && cd SPU
python3 software/spu_vm_test.py          # ends with "N passed, 0 failed" and PASS
python3 -m software.spu_gpu_eval.cli device-preview examples/gpu/t1d_two_triangle.json \
    --out build/gpu_evaluation/first_run
python3 -m software.spu_gpu_eval.cli inspect examples/gpu/t1d_two_triangle.json --x 320 --y 0
```

The second command renders a two-triangle scene twice: once as an exact mathematical
reference and once through a finite-width model of the GPU's depth arithmetic. Open
`build/gpu_evaluation/first_run/device_preview.ppm` in any image viewer. The last command
shows one pixel where both paths agree on the winner and colour but differ in depth
(2000 versus 1999). The [software quickstart](docs/NEWCOMER_SOFTWARE_QUICKSTART.md) lists more
commands, including a robotics chain and a scene edit, with expected output. Use a new
`--out` directory for each run.

## Known limitations

State these before citing any result:

- **The CPU is not qualified.** The integrated Surd CPU has no board result. Its placement
  passed an audit; routing and 25 MHz timing are not qualified.
- **The SOM RTL has a full-domain arithmetic defect.** For some inputs the uploader accepts, the
  current classifier RTL can return wrong distances without a flag. The Iris board evidence lies
  inside the safe region. An exact portable C reference that detects the unsafe cases has been written but is
  not part of this release; the RTL itself is not repaired.
- **A negative memory-layout result.** In a model-only cache study, hierarchical hexagonal layouts
  did not beat dense axial addressing overall, and the proposed adaptive weighting did not beat LRU/LFU.
- **Relational and hexagonal geometry are experimental, not a demonstrated speedup.** Fewer exact
  tests were counted in bounded fixtures; no runtime, energy or hardware advantage over a strong
  conventional baseline is shown.
- **Software is not hardware.** The VM and the GPU model run on a host CPU. Physical claims exist only
  in the [hardware evidence ledger](docs/hardware_evidence.md).

Details and evidence boundaries: [capability matrix](docs/CAPABILITY_MATRIX.md#known-limitations).

## Reproduce, review, contribute

Independent checks are the most useful contribution right now: run the quickstart, try to break an
oracle or a bound, or add a ledger entry for hardware you own. See
[CONTRIBUTING.md](CONTRIBUTING.md#ways-to-help). Questions and results are welcome on the
[issue tracker](https://github.com/pinnacletechnologysolutionsltd/SPU/issues).

## Where to go next

- [Short introduction](docs/START_HERE.md): the ideas, a worked example, current results and their limits.
- [Documentation index](docs/index.md) and the [capability matrix](docs/CAPABILITY_MATRIX.md).

Licensing varies by component; see [LICENSING.md](LICENSING.md).
