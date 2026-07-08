# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

An `AGENTS.md` in the repo root also exists and is kept up to date with the current
hardware test/silicon status and build command list — check it for the latest
per-board proof status before making claims about what is "verified in silicon"
vs. "testbench-only." `GEMINI.md` and `.github/copilot-instructions.md` contain
older architectural notes (some directory paths in them are stale — trust the
structure documented below and verified with `find`, not those files, when they
disagree).

## What this project is

SPU-13 is a deterministic rational-field FPGA coprocessor: exact arithmetic over
`Q(√3)` and `Z[φ]/L_p`, zero floating-point, zero division, zero branches in hot
paths. Two cores exist:

- **SPU-4 Sentinel** — 4-axis (Quadray), 32-bit, Euclidean satellite/sensory core.
  Dual-role by design: a standalone edge-compute node (~400 LUT — fits the
  smallest fabrics, no manifold, optional Hamming SEC) and the per-axis cluster
  satellite for an SPU-13 (cluster-bridge frames report Davis dissonance upward).
  Deployment architecture: `knowledge/ARLINGHAUS_SPATIAL_SYNTHESIS.md` §7.
- **SPU-13 Cortex** — 13-axis (cuboctahedral) manifold engine, the main compute core.

Applications are downstream of the same exact arithmetic: rational robotics/kinematics
(Pell forward/inverse chains), rational SOM/BMU clustering, RPLU v2 Padé approximants
over `A₃₁` (Mersenne prime M31 field), and Lucas Phinary MAC (`Z[φ]/L_p` arithmetic).

**Hard constraints — changes violating these are rejected:**
- No floating-point in the core ALU or RTL — all arithmetic is exact in `Q(√3)` / `A₃₁` / `Z[φ]/L_p`.
- No division; no transcendental approximations.
- No branches in hot paths — control flow compiles to `MUX` Boolean polynomials.
- Timing deviations are design flaws, not to be papered over with FIFOs/skew buffers.

## Build & test commands

```bash
python3 run_all_tests.py                        # discover + run every *_tb.v (iverilog/vvp), *_test.cpp, and Python VM test
TB_FILTER=spu13_m31 python3 run_all_tests.py     # restrict to testbenches matching a prefix (faster triage)
```
100% pass is required across all `hardware/tests/**/*_tb.v` before merging.

Run a single testbench manually:
```bash
iverilog -I hardware/rtl/arch -o build/foo_tb.vvp hardware/rtl/core/spu13/spu13_lucas_mac.v hardware/tests/spu13/spu13_lucas_mac_tb.v
vvp build/foo_tb.vvp
```
Testbenches must print `PASS`/`FAIL` and call `$finish` (otherwise `run_all_tests.py` times out at 5s).

Python/C++ oracle tests (software-side reference models the RTL must match bit-exactly):
```bash
python3 software/tests/test_rational_robotics.py     # 56 checks, Pell/FGH circulant robotics oracle
python3 software/tests/test_rational_som.py          # 24 checks, SOM/BMU oracle
python3 software/tests/test_rotc_vm_rtl_trace.py     # VM-vs-RTL trace equivalence, all 6 ROTC angles
python3 software/tests/test_lucas_mac_oracle.py      # Lucas Phinary MAC, 1M-step zero-drift
python3 software/tests/test_pade_batch_inversion.py  # A31 Montgomery batch inversion, 25 checks + cost tables
python3 software/tests/test_hyper_catalan_oracle.py  # hyper-Catalan series + jet ring, 21 checks vs published tables
python3 software/spu_vm_test.py                      # VM correctness
python3 software/cross_validate.py                   # VM vs C++ parity
```
C++ oracle parity headers live in `software/common/include/`; tests are `*_test.cpp` under `software/common/tests/`.

Board builds (root-level scripts; each drives yosys + nextpnr-himbaechel against a `.ys`/`.cst` in `hardware/boards/<board>/`):
```bash
bash build_25k_spu13_math_probe.sh                  # Tang Primer 25K, math-only probe
bash build_25k_spu13_rplu2_arith_probe.sh           # Tang Primer 25K, RPLU2 arithmetic probe (~27% LUT)
bash build_25k_spu13_lucas_mac_probe.sh             # Tang Primer 25K, Lucas MAC standalone
bash build_25k_spu13_southbridge_link.sh            # Tang Primer 25K, SPI link-only probe
A7_FREQ=2 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade synth/pnr/pack   # Wukong Artix-7 100T
```
The full RPLU2 pipeline (MATH=1 + RPLU_V2=1) does not fit on the Tang 25K (89% LUT) — that's why probes
are split; the Wukong Artix-7 100T is the target for full concurrent integration. Synthesis uses the
[OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) (Yosys + nextpnr-himbaechel) — no vendor IDE.

Simulate a `.sas`/`.lith` program on the Python VM:
```bash
python3 software/spu_forge.py simulate programs/robot_arm_demo.lith
```

Flash/bench tooling (RP2040 USB-to-SPI PMOD programmer, used to bring up external flash before FPGA J4 probes):
```bash
tools/rp2040_flash_pmod.py --port /dev/ttyACM3 id      # must report JEDEC EF4018 before any write
tools/rp2040_flash_pmod.py --port /dev/ttyACM3 write tools/build/rplu2_boot_tables.bin --offset 0x110000
```

## Architecture

### Directory layout (verified against the working tree — some docs elsewhere in the repo describe an older layout)
```
hardware/
  rtl/
    core/
      shared/     ALU, sequencer, register files, Davis gate, ISA decoder — shared between cores
      spu13/      SPU-13 Cortex: M31/A31 arithmetic, A31 inverter, BTU, SOM, RPLU2/Padé, Lucas MAC, sidecars
      spu4/       SPU-4 Sentinel: Euclidean ALU, decoder, boot master, sovereign bus
    arch/         ISA/architecture-level defines
    common/       shared protocol/utility RTL
    gpu/          rasterizer + fragment pipe
    hal/          hardware abstraction (display/IO)
    math/         math primitives
    peripherals/  I/O peripherals
    top/          system orchestrator (spu_system.v), clocking, power sequencing
  common/rtl/gpu/ small shared GPU RTL
  boards/         per-target synth scripts (.ys), constraints (.cst), board top modules
    tang_primer_25k/  artix7/  ecp5_85k/  colorlight_i9/
  tests/          testbenches, organized common/ spu13/ spu4/ peripherals/
  rp2040/         RP2040 bench firmware (flash PMOD programmer, visualiser)
  rp2350/         RP2350 southbridge firmware (SPI bridge to FPGA)
software/
  spu_vm.py           Python soft-CPU emulator (opcode table ~line 493-515)
  spu_forge.py         unified CLI: simulate / assemble / test / build
  lib/                 Sovereign Geometry Library + Python oracles (rational_robotics.py, rational_som.py)
  common/include/      C++17 oracle headers (parity with software/lib)
  common/tests/        C++ oracle parity tests
  tools/               assembler (spu13_asm.py) etc.
  tests/               Python oracle/VM/trace-equivalence tests
  programs/            .sas / .lith demonstration programs
tools/            ROM generators, RPLU table generators, RP2040 flash tooling, visualizer
knowledge/        architecture specs, ISA reference, math foundations (read before touching arithmetic RTL)
docs/             design guides, bring-up runbooks, paper drafts
```

### Data representation
Registers hold rational surds `(P, Q)` meaning `P + Q·√3`, packed as 32-bit `RationalSurd`
(upper 16 bits `P`, lower 16 bits `Q`). Field arithmetic stays closed:
```
add : (P1+P2, Q1+Q2)
sub : (P1-P2, Q1-Q2)
mul : (P1P2 + 3Q1Q2, P1Q2 + Q1P2)     ; √3·√3 = 3
```
The RPLU2/Padé pipeline extends this to `A₃₁` (basis `[1, √3, √5, √15]` over Mersenne prime
M31 = 2³¹−1); the Lucas MAC extends it to `Z[φ]/L_p` (Lucas-prime modulus, Barrett-style reduction).
Never encode `RationalSurd` constants as raw signed decimal literals — use explicit bit-packing,
e.g. identity = `{32'd0, 32'd1}`, negative = `{32'd0, 32'hFFFFFFFF}`.

### Stability — Davis Gate
Every cycle the hardware checks `ΣABCD = 0` (Davis Ratio / quadrance identity). A nonzero sum
("cubic leak") triggers **Henosis** — a one-cycle soft-recovery pulse — instead of a hard reset.
This is an exact zero test, not an epsilon comparison (`davis_gate_dsp.v`).

### Timing — Fibonacci-gated dispatch
Instructions dispatch at Fibonacci intervals (8/13/21 cycles); the system reference clock is
the 61.44 kHz "Piranha Pulse" (`spu_sierpinski_clk.v`). This is a deliberate design constraint,
not an artifact to optimize away.

### Bring-up stack
`SD card → RP2350 (RISC-V southbridge, SPI @ ~2 MHz) → FPGA SPU-13 core`. RP2350 handles boot,
filesystem, chord streaming, USB CDC telemetry; the FPGA does rational arithmetic, the QR register
file, and RPLU2 pipeline control. Southbridge SPI opcodes: `0xAC` status, `0xA0` manifold, `0xAE`
QR commit, `0xB1` instruction write, `0xA5` config write. Tang Primer 25K is the regression/probe
board; Wukong Artix-7 100T is the primary silicon-evidence board (J11 SPI southbridge).

### ISA
Full opcode reference: `knowledge/isa_reference.md`. VM opcode table: `software/spu_vm.py:493-515`.
Assembler: `software/tools/spu13_asm.py`. Corrected ROTC 0-5 angle catalog (F/G/H circulant
coefficients, periods, inverses) is documented in `AGENTS.md` — check there before touching
`spu13_rotor_core_tdm.v` or the VM's ROTC table, they must stay bit-identical
(verify with `python3 software/tests/test_rotc_vm_rtl_trace.py`).

## Coding conventions

- **Verilog:** 4-space indent, `snake_case` modules, testbenches end in `_tb.v` and live under
  `hardware/tests/{common,spu13,spu4,peripherals}/` (auto-discovered by `run_all_tests.py`).
  Modules are single-purpose ("Lithic") — typically 50-150 lines; split concerns rather than
  growing one file.
- **Python:** PEP 8, `snake_case`.
- **C++:** C++17, test files named `*_test.cpp`, includes from `software/common/include/`.
- **Adding RTL:** place it under the matching `hardware/rtl/core/{shared,spu13,spu4}/` subdir,
  add a `_tb.v` testbench, wire it into the relevant board's `.ys` synth script if it needs to
  reach a bitstream, then run `python3 run_all_tests.py` before committing.

## Commits & licensing

- Commit style: lowercase imperative summaries, area-prefixed (`spu13:`, `tang25k:`, `feat:`, `fix:`).
- Three-way license split: hardware RTL/board files under `hardware/` are CERN-OHL-W-2.0; software
  (VM/tools/firmware) under `software/` is MIT; docs/`knowledge/` are CC0 1.0. Contributions require
  DCO sign-off (see `CONTRIBUTING.md`).
