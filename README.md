# SPU-13 Sovereign Processing Unit

**A bit-exact, division-free, rational-field processor for geometric manifold arithmetic.**

The SPU-13 operates entirely within Q(√3) — the algebraic field of rational surds —
eliminating floating-point error at the hardware level. All values are exact. All
stability checks are integer comparisons. There is no epsilon, no rounding, no drift.

**Hardware proof:** Running on Tang Primer 25K (GW5A-25A), the full probe produces
these reproducible UART telemetry lines — same values, every power cycle:

```
B:D0EF4018 A:C              # SPI flash JEDEC ID confirmed
R:D28003FF A:D              # RPLU: marker=0x1A5, mask=0x0000, addr=0x3FF
R:00000803 A:E              # RPLU: 2051 records loaded
R:1D971036 A:F              # RPLU: checksum verified
SDRAM: 0x5D005D33 / 0x0012E92E   # SDRAM write/read self-test
```

See [`docs/hardware_evidence.md`](docs/hardware_evidence.md) for the full evidence ledger.

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
