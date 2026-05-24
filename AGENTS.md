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
| `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Set up Python environment |

Synthesis uses the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) (Yosys + nextpnr-himbaechel). No vendor IDE required.

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
