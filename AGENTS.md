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
- Hex coordinate projection → UART output (H: FFFE 0002)
- Instruction sequencer with inter-instruction delay
- RP2040 USB-to-SPI flash PMOD programmer (`hardware/rp2040/rp2040_flash_pmod.c`, `tools/rp2040_flash_pmod.py`) — JEDEC, pin diagnostics, sector erase, page program, verify; used to program `tools/build/rplu2_boot_tables.bin` at flash offset `0x110000`
- RPLU v2 PMOD J4 flash boot-table hydration proof — Tang Primer 25K reads external W25Q128-class flash over `J4[0]=CS#`, `J4[1]=SCK`, `J4[2]=MOSI/D1`, `J4[3]=MISO/DO`; legacy boot probe confirms `JEDEC EF4018`, 81 records, checksum `0x35DE2068`

**RTL testbench-verified (awaiting silicon test):**
- **ROTC opcode** — all 5 ROTC cases pass (TDM rotor core, `spu13_rotc_tdm_tb`)
- **SOM/BMU pipeline** — 7-node parallel array with WTA comparator; individual node 3-stage quadrance pipeline; training port with 36-bit widened multiply. (`spu_som_node_tb`, `btu_collision_tb`)
- **RPLU v2 — Thimble-Padé Engine** — A31 split-biquadratic arithmetic over Mersenne prime M31; conjugate-reduction unit/non-unit detection (~76 cycles); Horner-evaluated [4/4] Padé rational approximant; BTU collision resolver (64→6 priority encoder + backlog queue); 4R2W multi-port register file with write-forwarding bypass. (`spu13_m31_multiplier_tb`, `spu13_m31_inverter_tb`, `spu13_fp4_inverter_tb`, `singular_absorber_tb`)
- **RPLU v2 corrected flash table consumption probe** — `tools/gen_rplu2_tables.py` now emits 149 records: 5 Padé numerator coeffs, 5 denominator coeffs, 64 BTU rows as two lane-pair records each, and one Quadray kappa record. `build_25k_spu13_rplu2_consume_probe.sh` routes/packs a Tang 25K decode probe; pending PMOD hardware capture with `--expect-rplu2-consume`.
- QSUB, DELTA opcodes (VM-handlers ready, RTL FSM pending)
- CALL/RET/JMP (sequencer return stack designed)
- GPU rasterizer + fragment pipe (testbench passes)
- Bio stack (annealer, active inference, soul metabolism, proprioception)
- I2S audio output, toroidal regfile, quadray permuter

**Rational Robotics & SOM Oracles (software-verified):**
- Rational robotics oracle (`software/lib/rational_robotics.py`) — Pell inverse closure, F/G/H circulant inverse, FK chains, arc closure, 56 checks
- Rational SOM/BMU oracle (`software/lib/rational_som.py`) — weighted quadrance BMU, surd-field path, stable tie-breaking, hex neighbor deltas, 24 checks
- C++ parity for both oracles (`software/common/include/spu_rational_robotics.h`, `spu_rational_som.h`)
- Nguyen weight partitioning knowledge (`knowledge/NGUYEN_WEIGHT_PARTITIONING.md`)
- Rational SOM Nguyen cluster notes (`knowledge/RATIONAL_SOM_NGUYEN_CLUSTER_NOTES.md`)

**Known limitations on damaged 25K:**
- SDRAM non-functional — manifold state resets each power cycle
- Bio modules stubbed (zero-LUT) to fit 25K logic budget
- SPI flash program loader bypassed (sequencer uses hardcoded ROM)
- Hex telemetry: hex_valid must be cleared each cycle (one-pulse pattern)
- USB 3.0 port on BL616 bridge unreliable — use USB 2.0 only
- Place-and-route near 96% LUT utilization with full rotor core

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
