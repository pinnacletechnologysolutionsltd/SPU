# SPU-13 Sovereign Processing Unit

**A bit-exact, division-free, rational-field processor for geometric manifold arithmetic.**

[![License: CC0](https://img.shields.io/badge/License-CC0_1.0-lightgrey)](LICENSE)
[![Hardware: CERN-OHL-P](https://img.shields.io/badge/Hardware-CERN--OHL--P-blue)](hardware/LICENSE)
[![Software: MIT](https://img.shields.io/badge/Software-MIT-green)](software/LICENSE)

## Architecture

The SPU-13 is split across two chips connected by SPI:

```
SD Card → RP2350 (RISC-V Southbridge) → SPI @ 2 MHz → Tang 25K FPGA (SPU-13 Core)
```

- **RP2350** does: boot, filesystem, chord streaming, USB CDC telemetry
- **FPGA** does: Rational Arithmetic Unit, twine-register file, pipeline control

## Next-Gen ISA Status (Wheeler-Feynman v1.0)

| Component | Status | Tests |
|-----------|--------|-------|
| ISA decoder (RTL) | ✅ Completed | 34 iverilog PASS |
| Twine-register file (RTL) | ✅ Completed | 16 iverilog PASS |
| Rational Arithmetic Unit (RTL) | ✅ Completed | 16 iverilog PASS |
| Pipeline controller (RTL) | ✅ Completed | 10 iverilog PASS |
| Yosys synthesis | ✅ 11,125 LUTs (46%) | 0 errors |
| Python simulator | ✅ 35 PASS | cross-validated C++ |
| C++ simulator | ✅ 40 PASS | cross-validated Python |
| RP2350 SPI firmware | ✅ Ready | waiting on cables |
| SD card hydration | ✅ Ready | waiting on SD reader |

## Licensing

| Layer | License | Directory |
|-------|---------|-----------|
| Hardware (RTL, board files) | [CERN-OHL-P](hardware/LICENSE) | `hardware/` |
| Software (VM, tools, firmware) | [MIT](software/LICENSE) | `software/` |
| Documentation | [CC0 1.0](LICENSE) | `docs/`, `knowledge/` |

---

## Quick Start (30 seconds to proof)

```bash
# One command: compile a rational curve program and simulate it
python3 software/spu_forge.py simulate programs/robot_arm_demo.lith
```

This runs a 2-joint kinematic chain with a 12-step Pell-orbit trajectory through
the SPU-13 soft-CPU. The `.lith` source compiles to `.sas` assembly, assembles to
`.bin`, and executes in the Python VM — all exact Q(√3) arithmetic, no float.

```bash
# Run the full test suite
python3 software/spu_vm_test.py          # 85 VM tests
python3 software/rational_curves_test.py # 94 rational curve tests
python3 software/cross_validate.py       # 5/5 snaps matched (VM vs C++)
```

---

## Architecture

### Two cores

| Core | Axes | Role |
|------|------|------|
| **SPU-4 Sentinel** | 4 (Quadray) | Euclidean satellite, sensory input |
| **SPU-13 Cortex** | 13 (cuboctahedral) | Sovereign manifold engine |

Both synthesized with [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) (Yosys + nextpnr-himbaechel). No vendor IDE required.
For Artix-7 / Wukong, use the repo OpenXC7 setup in [`docs/toolchain_setup.md`](docs/toolchain_setup.md).

### Data representation — Q(√3) surds

Every register holds a pair `(P, Q)` representing the exact value `P + Q·√3`.
Arithmetic is closed in this field:
```
add : (P₁+P₂,  Q₁+Q₂)
sub : (P₁-P₂,  Q₁-Q₂)
mul : (P₁P₂ + 3Q₁Q₂,  P₁Q₂ + Q₁P₂)     ; √3·√3 = 3, stays in field
```

The Pell rotor `r = (2 + √3)` satisfies `P² − 3Q² = 1` for all powers.
After 8 rotations, the mantissa resets and the octave counter increments —
infinite rotor range in 16-bit registers. See [`knowledge/PELL_OCTAVE.md`](knowledge/PELL_OCTAVE.md).

### Stability — Davis Gate

Every cycle the hardware checks `ΣABCD = 0`. On failure, **Henosis** fires a
one-cycle correction pulse. This is a bit-exact zero test, not an epsilon comparison.

### Rotation — F,G,H Circulant

The `spu13_rotor_core.v` module implements Thomson's Spread-Quadray Rotor circulant:
B' = F·B + H·C + G·D (cyclic). At {60°, 120°, 240°, 300°} every matrix entry is
rational in {−1/3, 2/3}. At 120° the hardware uses a pure bit-permutation bypass.

### RPLU — Rational Polynomial Look-Up

2051-entry flash-loaded response surface. Maps axis state to correction vectors.
Proven on hardware: address walk covers full table (0x000–0x3FF), checksum `0x1D971036`.

---

## Hardware Targets

| Tier | Board | FPGA | Status |
|------|-------|------|--------|
| 1 Micro | Tang Nano 1K | GW1NZ-1 | ✅ Bitstream |
| 2 Small | iCESugar v1.5 | iCE40UP5K | ✅ Bitstream |
| 3 Mid | Tang Nano 9K | GW1N-9C | ✅ Synthesis |
| 4 Mid | Tang Primer 20K | GW2A-18 | ✅ Synthesis |
| 5 Large | **Tang Primer 25K** | GW5A-25A | ✅ Bitstream + probe |
| 6 Mega | Gowin Mega | GW5AST-138C | Planned |

---

## Mathematical Lineage

The SPU builds on 70 years of geometric insight:

| Contributor | Contribution | Reference |
|---|---|---|
| R. Buckminster Fuller | Synergetics, IVM, tetrahedral accounting | *Synergetics* (1975) |
| Kirby Urner / Tom Ace | Quadray coordinates, basis matrix | grunch.net, minortriad.com (1997) |
| Norman J. Wildberger | Rational trigonometry (spread/quadrance) | *Divine Proportions* (2005) |
| Andy Ross Thomson | Spread-Quadray Rotors, ABCD-native pipeline | *Quadray-Rotors-v5* (2026) |
| Leo Murillo | K³=−K cubic identity (closed-form Rodrigues) | Zenodo 19689050 (2026) |
| Bee Rosa Davis | Davis Law C=τ/K, cache/bin/barrier architecture | *Navier-Stokes Regularity* (2026) |

SPU original contributions: Q(√3)/Q(√5)/Q(√15) field extensions as FPGA arithmetic,
RPLU as hardware correction surface, Pell octave, progressive probe ladder.

Full credits: [`docs/ATTRIBUTION.md`](docs/ATTRIBUTION.md)
Math derivation: [`knowledge/MATHEMATICAL_FOUNDATIONS.md`](knowledge/MATHEMATICAL_FOUNDATIONS.md)

---

## Constraints

- **No floating-point** in the core ALU or RTL
- **No division** — spread/quadrance stored as `(numerator, denominator)` integer pairs
- **No transcendentals** — sin, cos, atan2 replaced by spread, quadrance, Pell rotor
- **No branches** in hot paths — control flow compiles to Boolean MUX polynomials

---

## License

CC0 1.0 Universal — public domain.
