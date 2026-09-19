# SPU Software Stack & Toolchain

The SPU software stack provides complete simulation, compilation, and assembly tools that run on any standard PC without an FPGA board.

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
| `spu` | Unified CLI | Command centre for simulation, assembly, tests, and synthesis (`spu sim`, `spu asm`, `spu test`) |
| `spu-sim` | Sovereign VM | Exact software virtual machine emulator for SPU-13 bytecode |
| `spu-as` | Sovereign Assembler | Assembles `.sas` assembly source into 64-bit control words (`.bin`) |
| `spu-lith` | Lithic-L Compiler | Compiles high-level rational curves and kinematics into `.sas` assembly |
| `spu-host` | Southbridge Client | Serial transport client for RP2350 microcontroller southbridge |

## Fast Onboarding (60 Seconds)

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

## High-Performance C++ Emulator
For high-speed simulation or embedding into host applications, a bit-exact C++17 virtual machine is available:

```bash
cd software/vm
make
./spu_vm ../../examples/01_scalar_fibonacci/fibonacci.sas --quiet
```
