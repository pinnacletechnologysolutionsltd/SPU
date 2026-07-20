# Your first hour with SPU-13

This path starts from an anonymous clone and stays hardware-free until the
last, optional section. It uses only checked-in data and deterministic tests.

## Before you clone

Install Git, Python 3.10 or newer, Icarus Verilog (`iverilog` and `vvp`), and a
C++17 compiler (`g++`). The hardware-free commands below need no Python package
installation. The FPGA toolchain is not required.

## 1. Clone the repository

From a directory in which you want the new `SPU/` directory:

```bash
git clone https://github.com/pinnacletechnologysolutionsltd/SPU.git
cd SPU
```

Expected clone output begins with:

```text
Cloning into 'SPU'...
```

`cd` is silent on success. All remaining commands run from the repository
root.

## 2. Run the merge gate

```bash
python3 run_all_tests.py
```

The suite compiles and runs Verilog, C++, and Python checks. The final summary
at this revision is:

```text
Verilog Tests: 130
Passed:      130
Failed:      0
...
Total PASS:  173
Total FAIL:  0
```

A missing compiler is an environment error, not a test failure; install the
prerequisite named by the first error and rerun the same command.

## 3. Exercise the software CPU

The VM test constructs instructions directly, executes them without an FPGA,
and checks every legacy opcode plus the manifold helpers:

```bash
python3 software/spu_vm_test.py
```

Expected final output:

```text
==================================================
spu_vm_test.py: 89 passed, 0 failed
PASS
```

This proves the checked software model on your machine. It is not a hardware
timing or silicon proof.

## 4. Run a small Forge program

`fibonacci_pulse.sas` is a 13-word program made from `LD`, `ADD`, `LOG`, and
`JMP`. Run twelve VM steps and retain the stable completion lines:

```bash
python3 software/spu_forge.py simulate software/programs/fibonacci_pulse.sas --steps 12 --quiet | grep -E 'PC=|Execution complete|\[PASS\]'
```

Expected output:

```text
  ── PC=12  steps=12  snap_failures=0  call_depth=0
  ✓  Execution complete — manifold laminar
[PASS]
```

Open `software/programs/fibonacci_pulse.sas` beside the output. The arithmetic
is integer arithmetic in the `P + Q·√3` representation; this particular program
keeps `Q=0`, so its Fibonacci values are ordinary integers embedded in that
field.

Use `.sas` for this first pass. Forge also accepts `.lith`, but compiling a
`.lith` source intentionally regenerates its adjacent `.sas` and `.bin` files.

## Where next?

- [Quadray for programmers](QUADRAY_FOR_PROGRAMMERS.md) explains the data
  representation behind the geometry instructions.
- [Demo tour](DEMO_TOUR.md) gives one reproducible command for robotics,
  LUCAS, Iris classification, and exact Voronoi evidence.
- [Current status](CURRENT_STATUS.md) separates software, RTL, and silicon
  proof levels.

## Optional: Tang Primer 25K SOM proof

This section requires a Tang Primer 25K, an RP2350 southbridge, and safe shared
power/ground handling. Never leave the RP2350 powered and driving an unpowered
FPGA. Complete the build, wiring, and load steps in the
[SOM-SIDECAR evaluator quickstart](SOM_SIDECAR_QUICKSTART.md), then run its
corpus proof from the repository root:

```bash
python3 tools/iris_som_demo.py --hardware --console-port /dev/ttyACM0 --uart-port /dev/ttyUSB1
```

On the proven port assignment, the final output is:

```text
IRIS_SOM_V1: PASS (150/150 FPGA winners bit-exact to oracle)
```

The semantic result in the same run is `147/150 (98.0%)`. The 150/150 figure
means complete FPGA decision records match the software oracle; it does not
mean all 150 class labels are correct.
