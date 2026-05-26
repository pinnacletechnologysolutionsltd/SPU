# Repository Guidelines

## Project Structure & Module Organization

```
hardware/               FPGA RTL (Verilog)
  common/rtl/           Shared cores — ALU, sequencer, mem, protocols, GPU
  spu13/rtl/            SPU-13 Cortex (13-axis manifold engine)
  spu4/rtl/             SPU-4 Sentinel (Quadray satellite)
  boards/               Per-target synthesis scripts & board tops
  tests/                Verilog testbenches (*_tb.v)
software/               Host-side tooling
  spu_vm.py             Soft-CPU emulator
  spu_forge.py          Unified CLI — simulate, assemble, test, build
  programs/             .sas demonstration programs
  lib/                  Sovereign Geometry Library (Q(√3,√5,√15))
tools/                  ROM generators, RPLU loaders, visualizer
knowledge/              Architecture specs, ISA reference, math foundations
docs/                   Design guides and bring-up runbooks
```

## Build, Test, and Development Commands

| Command | Purpose |
|---|---|
| `python3 run_all_tests.py` | Discover and run all Verilog `*_tb.v` testbenches via `iverilog`/`vvp`, plus C++ `*_test.cpp` and Python VM tests |
| `TB_FILTER=spu13 python3 run_all_tests.py` | Run only testbenches matching a prefix for faster triage |
| `bash build_25k.sh` | Synthesise, place-and-route, and generate bitstream for Tang Primer 25K |
| `bash build_gw1n1.sh` | Full bitstream for Tang Nano 1K |
| `python3 software/spu_forge.py simulate <program.sas>` | Simulate a .sas program on the Python VM |
| `bash build_25k_spu13_math_probe.sh` | Synthesise, P&R, bitstream for SPU-13 math probe on Tang 25K |
| `openFPGALoader -b tangprimer25k -f build/tang_primer_25k_spu13_math_probe.fs` | Flash bitstream to Tang Primer 25K |
| `python3 tools/flash_layout.py` | Generate SPI flash image from .bin files (Wildberger library) |
| `minipro -p W25Q128JV -r build/flash_backup.bin` | Read SPI flash backup (preserve bootloader) |
| `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Set up Python environment |

Synthesis uses the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) (Yosys + nextpnr-himbaechel). No vendor IDE required.

## Hardware Test Status (May 2026)

**Proven in silicon on Tang Primer 25K:**
- FPGA configuration via openFPGALoader
- Laminar boot (SPI flash read, RPLU table hydration)
- Fibonacci-synchronized manifold (phi_8/13/21 pulses)
- Davis Gate quadrance monitoring (Q: UART telemetry)
- VE (Vector Equilibrium) QR init hydration (12 vertices)
- QR register file read path (6 distinct hex values verified)
- **QLDI opcode** — immediate Quadray load → writes correctly to QR regfile
- Hex coordinate projection → UART output (H: FFFE 0002)
- Instruction sequencer with inter-instruction delay

**RTL-complete, awaiting silicon test:**
- ROTC opcode (TDM rotor core with surd_multiplier, SHIFT=0)
- QSUB, DELTA opcodes (VM-handlers ready, RTL FSM pending)
- CALL/RET/JMP (sequencer return stack designed)
- GPU rasterizer + fragment pipe (testbench passes)
- Bio stack (annealer, active inference, soul metabolism, proprioception)
- I2S audio output, toroidal regfile, quadray permuter

**Known limitations on damaged 25K:**
- SDRAM non-functional — manifold state resets each power cycle
- Bio modules stubbed (zero-LUT) to fit 25K logic budget
- SPI flash program loader bypassed (sequencer uses hardcoded ROM)
- Hex telemetry: hex_valid must be cleared each cycle (one-pulse pattern)
- USB 3.0 port on BL616 bridge unreliable — use USB 2.0 only
- Place-and-route near 96% LUT utilization with full rotor core

**Wildberger Rational Trigonometry Library (7 files, 30+ primitives):**
- `wildberger_spread.lith` — spread + collinearity via Delta opcode
- `wildberger_geometry.lith` — 5 geometry primitives
- `wildberger_calculus.lith` — tangents + Faulhaber areas
- `wildberger_layer2.lith` — quadrance_between, normalize, Pell polynomials
- `wildberger_chromogeometry.lith` — blue/red/green triple, Pell-quintic connection
- `wildberger_higher_dim.lith` — cross matrix, diagonal rule, 2-subspaces
- `call_demo.lith` — CALL/RET subroutine test

## ISA Reference

Full ISA documentation: `knowledge/isa_reference.md` (26 opcodes, 19 hardware-verified)
VM opcode table: `software/spu_vm.py` lines 493–515
Assembler opcode table: `software/tools/spu13_asm.py`

## Coding Style & Naming Conventions

- **Verilog RTL:** 4-space indentation. Modules use `snake_case`. Testbenches end in `_tb.v`. Top-level headers in `hardware/common/rtl/include/` (e.g., `spu_arch_defines.vh`).
- **Python:** Follow PEP 8. Use `snake_case` for functions and variables. Scripts under `software/` and `tools/`.
- **C++:** C++17. Test files named `*_test.cpp`. Include path: `software/common/include/`.

## Testing Guidelines

- **Hardware:** Icarus Verilog (`iverilog`/`vvp`) is the primary simulator; Verilator serves as fallback for GPU sources containing SystemVerilog constructs. Every testbench must print `PASS` or `FAIL`. Use `$finish` to prevent timeout.
- **Python VM:** Run `python3 software/spu_vm_test.py` and `python3 software/cross_validate.py` to verify VM correctness against the C++ reference.
- **C++:** Tests discovered automatically from `*_test.cpp` files. Compile with `g++ -std=c++17`.
- **Coverage:** All 95+ Verilog testbenches must pass before merging.

## Commit & Pull Request Guidelines

- **Commit style:** Use lowercase, imperative-mood summaries. Prefix with area when helpful: `spu13:`, `tang25k:`, `feat:`, `fix:`.
- **PR requirements:** All tests must pass (`run_all_tests.py`). Include a description of what changed and why. Link related issues. For hardware changes, note which board targets were tested.
- **Constraints:** The architecture prohibits floating-point, division, and branches in hot paths. Changes violating these are rejected.
