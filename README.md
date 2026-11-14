# SPU

SPU is an experimental computing architecture exploring how exact algebraic
arithmetic, geometric representations and deterministic transformations can
support useful native computational primitives.

The [research identity](docs/RESEARCH_IDENTITY.md) defines **Demonstrated**,
**Experimental** and **Exploratory** claims and the evidence needed for utility
in correctness, determinism, speed, energy, verification or system complexity.

Architectural invention is the ambition; demonstrated utility is the test.

## SPU v0.2: canonical machine, the Gen-1 Surd CPU

Each SPU release identifies one canonical machine, its architectural contract and
the evidence for it. For v0.2 that machine is the **Gen-1 Surd CPU**. It is
deliberately narrow, and it is the reference point for everything this release
claims about the processor.

| Property | SPU v0.2 |
|---|---|
| Machine | Frozen Gen-1 Surd CPU ([architectural contract](docs/GEN1_ARCHITECTURAL_CONTRACT.md); [source package](hardware/boards/artix7/wukong_v3/cpu_v02/README.md)) |
| Arithmetic | Exact multiplication in Q(√3), (a + b√3)/d with 64-bit fields: raw results that fit are committed unreduced, otherwise exact normalization-to-fit, otherwise refusal |
| Programming model | One architectural register (S0); four accepted instruction forms (SLI, SLD, SMUL, SRD); a fixed 14-instruction ROM program built into the bitstream; no control flow |
| Output | One 33-byte UART frame per reset (success or fault) |
| FPGA | Artix-7 XC7A100T on a Wukong V3 board, configured over JTAG into SRAM |
| Simulator | C++ `spu_vm --profile gen1-surd` ([usage](docs/software_guide.md)); conforms to the registered RTL fixtures and recorded silicon frames (software conformance only) |
| Physical status | Experimental single-unit observations: golden program and operand variants, repeated reloads, scoped reset recovery (ledger §3.40–3.43, §3.47–3.49, §3.51–3.52, starting at [§3.40](docs/hardware_evidence.md#340--cpu-board-4c-r1-first-fixed-program-surd-cpu-run-over-uart-2026-10-30)); nominal routed timing analysis; bit-exact rebuild of the configuration payload |
| Not established | General CPU qualification, flash boot, I/O and reset timing, metastability, multiple units |
| Release status | SPU v0.2.0, experimental Gen-1 Surd CPU; see the [v0.2.0 release](https://github.com/pinnacletechnologysolutionsltd/SPU/releases/tag/v0.2.0) and the [readiness record](docs/V02_RELEASE_READINESS.md#12-publication-record-2026-11-11) |

## SPU v0.3: programmable-surd CPU (in preparation)

This branch adds the v0.3 `programmable-surd` machine beside the v0.2 Gen-1 CPU above. v0.3 is a
programmable exact-arithmetic processor with a verified toolchain. It is experimental, it makes no
performance claim, and this branch has not been published as a release.

| Property | SPU v0.3 (`programmable-surd`) |
|---|---|
| Contract | [Frozen v0.3 contract](docs/design/SPU_V03_CONTRACT_CANDIDATE.md): the authoritative ISA. The other `SPU_V03_*` design records in `docs/design/` are historical provenance, not current requirements |
| Machine | Sequential, multicycle, in-order; eight Surd registers S0–S7; programs of 1–256 words; no data memory |
| Arithmetic | Bounded exact Q(√3), (a + b√3)/d with 64-bit fields. A refused `SMUL`, `SADD` or `SSUB` leaves its destination unchanged and sets the refusal flags; the program must check them |
| Inputs | A program image and an instruction budget, supplied by the host. There is no general runtime operand input: input values are part of the image |
| Tools | [SDK](software/sdk/README.md) (assembler, disassembler, `spu` CLI), C++ `spu_vm --profile programmable-surd`, a Python oracle and a UART host client |
| Examples | [`software/sdk/examples/`](software/sdk/examples/): exact √3 arithmetic (Pell K=33), exact orientation, and a refusal-and-recovery branch (Pell K=34) |
| Physical status | One recorded session on one Wukong unit and one SDK-driven run (ledger §3.53 and §3.54 in [`docs/hardware_evidence.md`](docs/hardware_evidence.md)): observations, not a qualification |
| Not established | Qualification of the UART interface, timing margin or reset behaviour; operation across reloads, supply or temperature; multiple units |

The rational GPU, HEX-SOM, the experimental H0 programmable image and the wider
mathematical research below are **experimental components**. They are not
features of the canonical CPU.

Where any historical document in this repository (for example earlier ISA, rotor or accelerator descriptions) conflicts with the Gen-1 architectural contract, the contract is authoritative for v0.2; historical documents are kept for provenance, not as descriptions of supported hardware.

## What is here

- **A software stack.** A Python virtual machine, a C++ VM with the `gen1-surd`
  profile for the canonical machine, an assembler, an exact robotics chain and an
  offline GPU model, all runnable without any hardware.
- **Verilog and FPGA builds** for Tang Primer 25K and Wukong Artix-7 boards. The
  canonical v0.2 machine is the Gen-1 Surd CPU above. The experimental H0
  programmable image is a separate configuration with its own single-session
  observation, not part of the canonical release.
- **Exact-geometry and classification work**, with its limits stated in the
  [capability matrix](docs/CAPABILITY_MATRIX.md), which separates mathematical
  argument, host software, RTL simulation, FPGA synthesis and physical hardware,
  because none implies another.

## Try it in two minutes

You need Python 3.10 or newer and Git. Cloning requires network access; the
commands that follow run locally without a board or package installation.
This README describes the curated `release/v0.3` branch, which carries the v0.2 release
content plus the v0.3 additions listed above; other branches may contain a different snapshot.

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

- **The CPU is not qualified.** The Gen-1 evidence consists of single-unit board
  observations of a fixed program, plus nominal timing analysis. It does not cover
  general correctness, flash boot, I/O or reset timing, or more than one board. The
  separate experimental H0 image ran two UART-loaded programs in one session
  ([§3.46](docs/hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)).
  That is not a qualification of the CPU, UART or timing margins.
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

## Gen-1 CPU progress

The preserved Wukong CPU sources include a board-local core copy with a
driver-conflict fix. That fix has not been promoted to the shared core; see the
[source package](hardware/boards/artix7/wukong_v3/cpu_v02/README.md). The
fixed-program CPU and ROM variants produced expected UART records in separate,
limited board runs ([ledger §3.40–3.43, §3.49](docs/hardware_evidence.md#340--cpu-board-4c-r1-first-fixed-program-surd-cpu-run-over-uart-2026-10-30)).
Later entries record repeated reloads, KEY0 restarts and scoped timed-pulse reset
recovery of the golden image (§3.47, §3.48, [§3.52](docs/hardware_evidence.md#352--gen1-reset-edge-1-timed-key0-reset-recovery-of-the-golden-gen-1-image-2026-11-08-utc)). Nominal routed
static timing analysis passed ([GEN1-STA-1](docs/GEN1_STA_1_CLOSURE_2026-11-07.md)).
The later experimental H0 image accepted two 14-word programs over UART and
returned oracle-matching results in one session ([§3.46](docs/hardware_evidence.md#346--h0-board-uart-3b-first-uart-loaded-programmable-h0-cpu-run-on-wukong-2026-11-03-utc)).

A separate Vivado rebuild reproduced the fixed-program image's configuration
payload bit-for-bit in one attempt; it was not a new board run ([reproduction
record](hardware/boards/artix7/wukong_v3/cpu_v02/portable/REPRO_1B_RESULT.md)).
A second single run on a different host produced the same payload, with no
report differences against the golden build ([desktop
record](docs/CPU_REPRO_DESKTOP_2026-11-06.md)).
That later result supersedes the source package README's earlier statement that
the package had not been rebuilt.
These results demonstrate the recorded programs and images, not general CPU
correctness, interface qualification or measured timing margins.

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
