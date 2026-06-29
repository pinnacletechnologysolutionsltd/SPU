# Repository Guidelines

## Project Structure & Module Organization

```
hardware/               FPGA RTL (Verilog)
  common/rtl/           Shared cores — ALU, sequencer, mem, protocols, GPU
  spu13/rtl/            SPU-13 Cortex (13-axis manifold engine)
    core/spu13/         SPU-13 pipeline: M31/A31 arithmetic, unit inverter, SOM, BTU, register file
  spu4/rtl/             SPU-4 Sentinel (Quadray satellite)
  boards/               Per-target synthesis scripts & board tops
  tests/                Verilog testbenches (*_tb.v)
software/               Host-side tooling
  spu_vm.py             Soft-CPU emulator
  spu_forge.py          Unified CLI — simulate, assemble, test, build
  programs/             .sas demonstration programs
  lib/                  Sovereign Geometry Library (Q(√3,√5,√15))
tools/                  ROM generators, RPLU loaders, visualizer
hardware/rp2040/        RP2040 bench utilities, including SPI flash PMOD programmer
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
| `bash build_25k_spu13_southbridge.sh` | Full southbridge build (MATH=1 + RPLU_V2=1 — too large for 25K at 89% LUT) |
| `bash build_25k_spu13_southbridge_link.sh` | SPI link-only probe (~350 LUTs) — validates RP2350↔FPGA SPI |
| `bash build_25k_spu13_rplu2_arith_probe.sh` | RPLU2 arithmetic probe (6,282 LUTs, 27%) — QLDI/QSUB/RPLU2 config |
| `bash build_25k_spu13_lucas_mac_probe.sh` | Lucas Phinary MAC standalone probe (~200 LUTs) — zero-drift proof |
| `bash build_25k_spu13_rplu2_consume_probe.sh` | RPLU2 flash consume-probe (149-record table verification) |
| `openFPGALoader -b tangprimer25k -f build/tang_primer_25k_spu13_math_probe.fs` | Flash bitstream to Tang Primer 25K |
| `python3 tools/flash_layout.py` | Generate SPI flash image from .bin files (Wildberger library) |
| `minipro -p W25Q128JV -r build/flash_backup.bin` | Read SPI flash backup (preserve bootloader) |
| `cmake --build build/rp2040_flash_pmod --target rp2040_flash_pmod -j` | Build RP2040 USB-to-SPI flash PMOD programmer |
| `picotool load -f build/rp2040_flash_pmod/rp2040_flash_pmod.uf2 && picotool reboot` | Load RP2040 flash PMOD programmer |
| `tools/rp2040_flash_pmod.py --port /dev/ttyACM3 id` | Read PMOD SPI flash JEDEC through RP2040; must report `EF4018` before writes |
| `python3 tools/gen_rplu2_tables.py --profile default --output tools/build/rplu2_boot_tables.bin` | Generate corrected 149-record RPLU2 default table blob |
| `tools/rp2040_flash_pmod.py --port /dev/ttyACM3 write tools/build/rplu2_boot_tables.bin --offset 0x110000` | Program corrected RPLU2 table blob to PMOD SPI flash at the bootloader offset |
| `bash build_25k_spu13_rplu2_consume_probe.sh` | Build Tang 25K RPLU2 flash consume-probe bitstream and corrected consume-profile table |
| `python3 software/tests/test_rational_robotics.py` | Run rational robotics oracle tests (56 checks) |
| `python3 software/tests/test_rational_som.py` | Run rational SOM/BMU oracle tests (24 checks) |
| `python3 software/tests/test_rotc_vm_rtl_trace.py` | VM-vs-RTL trace equivalence for all 6 ROTC angles |
| `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` | Set up Python environment |
| `bash hardware/boards/artix7/build_a7.sh 100t full` | Synthesise, P&R, bitstream for Wukong Artix-7 100T (full spin) |
| `python3 software/tests/test_lucas_mac_oracle.py` | Run Lucas Phinary MAC oracle (PSCALE/PCHIRAL/PMUL/PINV + 1M-step zero-drift) |
| `iverilog -I hardware/rtl/arch -o build/lucas_mac_tb.vvp hardware/rtl/core/spu13/spu13_lucas_mac.v hardware/tests/spu13/spu13_lucas_mac_tb.v && vvp build/lucas_mac_tb.vvp` | Run Lucas MAC RTL testbench (11 ops + 100-period zero-drift) |

Synthesis uses the [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) (Yosys + nextpnr-himbaechel). No vendor IDE required.

## Hardware Test Status (June 2026)

**Proven in silicon on Tang Primer 25K:**
- FPGA configuration via openFPGALoader
- Laminar boot (SPI flash read, RPLU table hydration)
- Fibonacci-synchronized manifold (phi_8/13/21 pulses)
- Davis Gate quadrance monitoring (Q: UART telemetry)
- VE (Vector Equilibrium) QR init hydration (12 vertices)
- QR register file read path (6 distinct hex values verified)
- **QLDI opcode** — immediate Quadray load → writes correctly to QR regfile
- **QSUB opcode** — QR subtraction (QLDI operands → QSUB → QR commit readback)
- Hex coordinate projection → UART output (H: FFFE 0002)
- Instruction sequencer with inter-instruction delay
- RP2040 USB-to-SPI flash PMOD programmer — JEDEC, pin diagnostics, sector erase, page program, verify
- RPLU v2 PMOD J4 flash boot-table hydration proof — Tang Primer 25K reads external W25Q128-class flash over J4
- **RPLU2 consume proof over southbridge** — 149 records consumed via RP2350 SPI, count verified, checksum 0x0AA480E7
- **Southbridge SPI protocol** — 0xAC status, 0xA0 manifold, 0xAE QR commit, 0xB1 instruction write, 0xA5 config write
- RP2350 southbridge diag firmware — USB CDC console for SPI bring-up
- **RP2350 arithmetic test driver** — QLDI+QSUB 6-test suite via SPI, byte-swap fix applied

**RTL testbench-verified (awaiting silicon test):**
- **ROTC opcode** — all 6 corrected ROTC angles pass (TDM rotor core)
- **SOM/BMU pipeline** — 7-node parallel array with WTA comparator
- **RPLU v2 — Thimble-Padé Engine** — A31 arithmetic, Padé evaluator, BTU collision resolver
- **Lucas Phinary MAC** — PSCALE (1c, 0 DSP), PCHIRAL (1c, 0 DSP), PMUL (3c), PINV (O(log L_p) Euclidean GCD). 100-period zero-drift marathon PASS. ~200 LUTs, ready for Wukong Artix-7 synthesis.
- GPU rasterizer + fragment pipe (testbench passes)
- Bio stack (annealer, active inference, soul metabolism, proprioception)

**Rational Robotics & SOM Oracles (software-verified):**
- Rational robotics oracle — 56 checks
- Rational SOM/BMU oracle — 24 checks
- C++ parity for both oracles
- Lucas Phinary MAC oracle — 1M-step zero-drift, all 4 ops verified

**Known board limitations:**
- SDRAM module (W9825G6KH) retired — DQ[10] fault confirmed, not an FPGA issue
- Tang 25K FPGA board is healthy; SDRAM fault was on the external module
- RPLU2 full pipeline (MATH=1 + RPLU_V2=1) too large for 25K (89% LUT) — needs Wukong Artix-7
- Split-build strategy: 4 independent probes fit on 25K (southbridge_link, math_probe, rplu2_arith_probe, lucas_mac_probe)
- USB 3.0 port on BL616 bridge unreliable — use USB 2.0 only

**RP2040 SPI Flash PMOD Programmer (bench-proven):**
- Purpose: reliable replacement for bad SOIC clips / ambiguous XGECU ICSP wiring. Use it to program and verify W25Q-style PMOD flash before FPGA-side J4 probes.
- Default wiring: `PMOD SLK -> Pico GP2`, `PMOD D1 -> Pico GP3`, `PMOD DO -> Pico GP4`, `PMOD CS -> Pico GP5`, `PMOD VCC -> Pico 3V3 OUT`, `PMOD GND -> Pico GND`.
- Safety rule: never erase or program unless repeated `id` reads return `JEDEC: EF4018`. `000000` means no valid flash response; `171717` usually indicates bad CS framing.
- Useful diagnostics: `tools/rp2040_flash_pmod.py --port <tty> diag`, `... drive --cs 1 --sck 0 --mosi 0`, and `... wren`. `WREN` should report `RDSR=02` before program/erase.
- Common wiring failure found in bring-up: cracked `/CS` solder joint. Meter W25Q pin 1 while using the `drive` command; it must switch between 0 V and 3.3 V. Add pullups on `/CS`, `/WP`, and `/HOLD` for custom PCBs.
- Corrected RPLU2 table programming command: generate with `python3 tools/gen_rplu2_tables.py --profile default --output tools/build/rplu2_boot_tables.bin`, then program with `tools/rp2040_flash_pmod.py --port <tty> write tools/build/rplu2_boot_tables.bin --offset 0x110000`. Corrected default/consume-profile blobs are 149 records / 2384 bytes.
- Legacy note: the first J4 hydration proof used an obsolete 81-record blob (`count=0x51`, checksum `0x35DE2068`) before the Padé high-lane and BTU row packing bugs were fixed. Do not use that blob for RPLU2 consumption tests.

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

### Corrected ROTC 0–5 Angle Catalog (June 2026)

The legacy ROTC table had three defects: angle 2 was documented with thirds coefficients
while hardware bypassed it as P5 permutation; angle 3 was singular (`det=0`); angle 5
duplicated angle 1. The corrected catalog is:

| ROTC angle | Name | F | G | H | Period | Inverse |
|---:|---|---:|---:|---:|---:|---:|
| 0 | identity | 1 | 0 | 0 | 1 | 0 |
| 1 | thirds period-6 | 2/3 | 2/3 | -1/3 | 6 | 4 |
| 2 | P5 forward cycle | 0 | 1 | 0 | 3 | 5 |
| 3 | thirds period-2 | -1/3 | 2/3 | 2/3 | 2 | 3 |
| 4 | thirds period-6 inverse | 2/3 | -1/3 | 2/3 | 6 | 1 |
| 5 | P5 inverse cycle | 0 | 0 | 1 | 3 | 2 |

**RTL encoding:** Angles 0-3 use the TDM circulant path (`F,G,H` surd multiplies + optional `/3`).
Angles 2 and 5 use hardware bypass (`bypass_p5`, `bypass_p5_inv`) — pure bit permutation, zero multiplies.

**VM-vs-RTL trace equivalence:** `python3 software/tests/test_rotc_vm_rtl_trace.py` — exercises all
6 angles on a canonical test vector and asserts bit-exact match between Python VM and Verilog simulation.

### Rational Robotics & SOM Oracles

| Layer | File | Purpose |
|---|---|---|
| Python robotics oracle | `software/lib/rational_robotics.py` | Exact Q(√3) robotics: Pell, F/G/H circulant, FK chains, inverse closure |
| Python robotics tests | `software/tests/test_rational_robotics.py` | 56 checks — determinant, period, inverse, closure, no-float audit |
| C++ robotics oracle | `software/common/include/spu_rational_robotics.h` | C++17 parity for all robotics primitives |
| C++ robotics tests | `software/common/tests/spu_rational_robotics_test.cpp` | C++ parity for closure tests |
| Python SOM oracle | `software/lib/rational_som.py` | Weighted quadrance BMU, surd-field path, stable tie-breaking |
| Python SOM tests | `software/tests/test_rational_som.py` | 24 checks — integer/surd BMU, field-square, tie-breaking |
| C++ SOM oracle | `software/common/include/spu_rational_som.h` | C++17 parity for SOM BMU classifier |
| C++ SOM tests | `software/common/tests/spu_rational_som_test.cpp` | C++ parity for BMU scenarios |
| Rational curves spec | `knowledge/RATIONAL_CURVES_SPEC.md` | Type 1–6 curve primitives, kinematics, correction |
| Nguyen weight partitioning | `knowledge/NGUYEN_WEIGHT_PARTITIONING.md` | Laminar weight → IVM wedge allocation → BRAM tiering |
| SOM Nguyen cluster notes | `knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md` | Kohonen/SOM direction, BMU RTL staging, hex topology |
| Lucas Phinary MAC oracle | `software/tests/test_lucas_mac_oracle.py` | PSCALE/PCHIRAL/PMUL/PINV, 1M-step zero-drift over L_521 |
| Lucas MAC architecture | `knowledge/LUCAS_PHINARY_MAC.md` | Ring separation, Barrett bridge, BTU integration, opcode map |
| Lucas MAC paper | `docs/LUCAS_MAC_PAPER.md` | 7-section paper draft with empirical results |

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
