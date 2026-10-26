# SPU Software Stack & Toolchain

The software tools let you inspect arithmetic and run small programs without an
FPGA. These commands test the software model; they do not establish hardware
performance or timing.

The [simulator integration policy](SIMULATOR_INTEGRATION_POLICY.md) makes the
simulator the cumulative software reference for qualified architecture.
Capabilities require profile-specific implementation and conformance tests
before software integration is complete; physical qualification is tracked
separately. Its build capability-manifest requirement is adopted policy,
not a claim that the existing commands already emit such a manifest.

## Start from source

From the repository root, with Python 3.10 or newer:

```bash
python3 software/spu_vm_test.py
python3 software/spu_forge.py simulate software/programs/fibonacci_pulse.sas --steps 12 --quiet
```

The first command runs the VM's directed tests. Its final summary should report
`0 failed`, followed by `PASS`. The passed-test count depends on the revision
(89 on the clean base used for this editorial walkthrough).
Some tests deliberately exercise fault paths, so intermediate diagnostic lines
can show failures that are expected by the test. Read the final summary.

The second runs a short program for 12 instructions. Its output includes
`PC=12`, `steps=12`, `snap_failures=0`, and `[PASS]`.
`--quiet` reduces tracing; it still prints register and status information.
These commands use the Python standard library and require no installation.

For a small arithmetic identity and the current claim limits, return to the
[introduction](START_HERE.md). Optional installed tools follow below.

## Installation

Install the SPU toolkit in editable mode:

```bash
git clone https://github.com/pinnacletechnologysolutionsltd/SPU.git
cd SPU
pip install -e .
```

This registers the following command-line tools into your environment:

| Command | Tool | Purpose |
| :--- | :--- | :--- |
| `spu` | Unified CLI | CLI for simulation, assembly, tests and builds (`spu sim`, `spu asm`, `spu test`) |
| `spu-sim` | Sovereign VM | Exact software virtual machine emulator for SPU-13 bytecode |
| `spu-as` | Sovereign Assembler | Assembles `.sas` assembly source into 64-bit control words (`.bin`) |
| `spu-lith` | Lithic-L Compiler | Compiles high-level rational curves and kinematics into `.sas` assembly |
| `spu-host` | Southbridge Client | Serial transport client for RP2350 microcontroller southbridge |

## More examples

### 1. Simulate an Assembly Program
```bash
spu sim examples/01_scalar_fibonacci/fibonacci.sas --steps 12
```

### 2. Compile and Simulate Lithic-L
```bash
spu sim examples/04_kinematics_chain/robot_arm.lith --steps 20
```

### 3. Run the Streaming Rasterizer
```bash
python3 examples/05_streaming_triangle/render_triangle.py
```

## C++ emulator
The C++17 VM implements the bounded canonical ISA subset listed in the
[conformance report](isa/ISA_CONFORMANCE_2026-10-10.md). It is not a full
bit-exact replacement for the Python VM or RTL: arithmetic widths and several
instruction families differ, as recorded in that report.

Command names identify different implementations: the installed `spu-sim`
entry point in this repository maps to the legacy Python VM
(`software/spu_vm.py`, via `pyproject.toml`). The C++ executable is the separate
`software/vm/spu_vm` binary built below. Results from one must not be reported
as results from the other. The contract for a future standalone `spu-sim`
repository is another implementation identity and is not represented by this
Python entry point.

```bash
make -C software/vm
make -C software/vm test
./software/vm/spu_vm examples/02_quadray_orbit/quadray_orbit.sas --quiet
./software/vm/spu_vm examples/03_davis_equilibrium/equilibrium.sas --quiet
```

The two example programs halt normally in the C++ VM and were run with these
commands. These outcomes refer only to the C++ binary. In the clean package
walkthrough, the Python `spu-sim` entry point printed raw `RationalSurd`
object representations for Quadray Orbit, and Davis Equilibrium returned
status 2 after SNAP failures; those Python results are not equivalent to the
C++ results. The Fibonacci pulse is intentionally an unbounded loop; use
`--steps N` to cap it, and treat that as a step-budget stop rather than proof
that the program reached a HALT instruction. The C++ CLI returns status 3 for
that stop, while a HALT on the last permitted step returns status 0. See the
[dated release review](isa/CPP_VM_RELEASE_REVIEW_2026-10-15.md) for the exact
checks and current scope limits.
