# SPU Software Stack & Toolchain

The software tools let you inspect arithmetic and run small programs without an
FPGA. These commands test the software model; they do not establish hardware
performance or timing.

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
For high-speed simulation or embedding into host applications, a bit-exact C++17 virtual machine is available:

```bash
cd software/vm
make
./spu_vm ../../examples/01_scalar_fibonacci/fibonacci.sas --quiet
```
