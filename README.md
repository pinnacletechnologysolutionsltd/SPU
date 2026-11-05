# SPU

SPU is an experimental computing architecture exploring how exact algebraic
arithmetic, geometric representations and deterministic transformations can
support useful native computational primitives.

The [research identity](docs/RESEARCH_IDENTITY.md) defines **Demonstrated**,
**Experimental** and **Exploratory** claims and the evidence needed for utility
in correctness, determinism, speed, energy, verification or system complexity.

Architectural invention is the ambition; demonstrated utility is the test.

## What is here

- **A software stack.** A Python virtual machine, an assembler, an exact robotics
  chain and an offline GPU model, all runnable without any hardware.
- **Verilog and FPGA builds** for Tang Primer 25K and Wukong Artix-7 boards.
  The experimental H0 programmable Gen-1 Surd CPU has a limited board observation
  described below; it is not a qualified CPU release.
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

- **The CPU is not qualified.** One experimental H0 image ran two UART-loaded
  programs in one Wukong session, with oracle-matching results and a subsequent
  reset observation. This is a single-session result, not qualification of the
  CPU, UART or timing margins. See [hardware evidence §3.46](docs/hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc).
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
The [H0 overview](docs/H0_OVERVIEW.md) separates the earlier simulation from
the later board observation.

## Recent development

- The experimental H0 work includes a host transaction model, RTL controller and
  UART loading path. The board observation above covers only the stated image and
  session; simulation, tool timing and physical evidence remain separate.
- Symbolic representation, geometry and nonlinear relational bounds are being
  investigated under [research](research/). These are bounded experiments, not
  architectural guarantees or demonstrated performance gains.
- The [simulator integration policy](docs/SIMULATOR_INTEGRATION_POLICY.md)
  sets conformance and capability-manifest requirements for future releases;
  the policy itself does not establish that current builds satisfy them.

## Reproduce, review, contribute

Independent checks are the most useful contribution right now: run the quickstart, try to break an
oracle or a bound, or add a ledger entry for hardware you own. See
[CONTRIBUTING.md](CONTRIBUTING.md#ways-to-help). Questions and results are welcome on the
[issue tracker](https://github.com/pinnacletechnologysolutionsltd/SPU/issues).

## How this project is developed

The SPU repository is directed and maintained by its owner. Much of the code, tests and documentation were drafted with AI coding assistants
(for example Claude and DeepSeek models) working from specifications and tasks written by the maintainer. Assistant output is run against the
repository's tests and oracles and reviewed by the maintainer before it is committed, and the maintainer is responsible for what is published.
The depth of review has varied across the project's history; the test suite, the evidence ledger and the capability matrix, not the use of any
particular tool, are the basis for what this repository claims.

Commits made with an assistant may carry a `Co-Authored-By` trailer. That trailer records the tooling used. It is not a statement about who owns
copyright and it is not a certification of origin; this project does not retroactively add `Signed-off-by` lines to earlier commits.

### Historical Git Identity and AI-Assisted Development

In the original development repository, some historical commits use the Git identity `john@spu13.local`; this release has a fresh, squashed history that does not include them.

This was a local Git identity used during AI-assisted development sessions. It does not represent an independently verified human contributor, nor should it be interpreted as evidence of independent review or approval.

As project maintainer, I accept responsibility for the changes I select and publish, including AI-assisted contributions. AI assistance does not transfer responsibility for the project's published code, documentation, research claims, or licensing obligations.

Historical commits have been preserved without rewriting Git history, maintaining the continuity of commit identities, validated release artifacts, and existing references.

This disclosure does not imply that another person authored or signed off on these changes.

## Where to go next

- [Short introduction](docs/START_HERE.md): the ideas, a worked example, current results and their limits.
- [Documentation index](docs/index.md) and the [capability matrix](docs/CAPABILITY_MATRIX.md).

Licensing varies by component; see [LICENSING.md](LICENSING.md).
