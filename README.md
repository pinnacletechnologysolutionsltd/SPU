# SPU-13 Synergetic Processing Unit

**A deterministic FPGA edge-classification sidecar: labeled CSV in,
checksummed rational SOM map out, followed by bit-exact hardware inference and
a CRC-protected decision-evidence frame. The same writable seven-node model is
silicon-proven on Gowin and Xilinx FPGAs with no software-to-hardware accuracy
loss.**

[![CI](https://github.com/pinnacletechnologysolutionsltd/SPU/actions/workflows/ci.yml/badge.svg)](https://github.com/pinnacletechnologysolutionsltd/SPU/actions/workflows/ci.yml)
[![Hardware: CERN-OHL-W-2.0](https://img.shields.io/badge/Hardware-CERN--OHL--W--2.0-blue.svg)](hardware/LICENSE)
[![Software: MIT](https://img.shields.io/badge/Software-MIT-green.svg)](software/LICENSE)
[![Docs: CC0](https://img.shields.io/badge/Docs-CC0_1.0-lightgrey.svg)](docs/LICENSE)
[![RPLU paper DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21446713.svg)](https://doi.org/10.5281/zenodo.21446713)
[![LUCAS paper DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21447441.svg)](https://doi.org/10.5281/zenodo.21447441)

## Start here

- **[Your first hour](docs/FIRST_HOUR.md)** — anonymous clone, full regression,
  software VM, one small Forge program, then optional Tang hardware
- **[Quadray for programmers](docs/QUADRAY_FOR_PROGRAMMERS.md)** — four-axis
  representation, normalization conventions, and a worked exact rotation
- **[Hardware-free demo tour](docs/DEMO_TOUR.md)** — robotics, LUCAS, Iris SOM,
  and exact Voronoi decision evidence, each with an explicit claim boundary

## Proven SOM Product Path

The current product-shaped artifact is the SPU-13 SOM sidecar:

```text
labeled CSV -> deterministic integer trainer -> checksummed SOM map
            -> writable FPGA sidecar -> 52-byte SOM1 evidence frame
```

The checked Iris model achieves 147/150 semantic classifications. More
importantly, all 150 complete SOM1 records match the exact software oracle on
both Tang Primer 25K and Wukong Artix-7 hardware: winner, runner-up,
quadrances, confidence gap, ambiguity, generations, status, and CRC. The
synthetic current-signature replay provides the hardware-independent path for
the first anomaly-monitoring demo; physical INA226 acquisition remains the
next sensor bench step. See [`docs/SOM_V1_PRODUCT_CONTRACT.md`](docs/SOM_V1_PRODUCT_CONTRACT.md).

## Current Hardware Direction

The SPU-13 bench stack is split across a microcontroller southbridge and an
FPGA target connected by SPI:

```
SD Card → RP2350 (RISC-V southbridge) → SPI @ 2 MHz → FPGA SPU-13 core
```

- **RP2350** does: boot, filesystem, chord streaming, USB CDC telemetry
- **FPGA** does: rational arithmetic, QR register file, RPLU2 pipeline control

The Tang Primer 25K remains the proven regression/probe board. The Wukong
Artix-7 100T is the primary Artix silicon-evidence and constrained integration
board. Full concurrent integration with live RPLU2, sidecars, and safety layers
is an Artix-7 200T / Kintex-class funding target. See
[`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md).

## Experimental ISA Profile (Wheeler–Feynman v1.0)

The Wheeler–Feynman twin-register profile is an architecture study with
isolated model and RTL coverage. It is not the canonical silicon ISA and is not
a declared replacement for it. Offer/Confirmation terminology denotes paired
boundary-data slots, not physical retrocausality. The canonical encoding used
by active Tang/Wukong images is documented in
[`knowledge/isa_reference.md`](knowledge/isa_reference.md).

| Component | Status | Tests |
|-----------|--------|-------|
| ISA decoder (RTL) | ✅ Completed | 34 iverilog PASS |
| Twine-register file (RTL) | ✅ Completed | 16 iverilog PASS |
| Rational Arithmetic Unit (RTL) | ✅ Completed | 16 iverilog PASS |
| Pipeline controller (RTL) | ✅ Completed | 10 iverilog PASS |
| Isolated Yosys build | ✅ 11,125 LUTs (46%) | Not an active core image |
| Python simulator | ✅ 35 PASS | cross-validated C++ |
| C++ simulator | ✅ 40 PASS | cross-validated Python |
| Active silicon-core dispatch | Not integrated | Canonical ISA remains active |

## Licensing

| Layer | License | Directory |
|-------|---------|-----------|
| Hardware (RTL, board files) | [CERN-OHL-W-2.0](hardware/LICENSE) | `hardware/` |
| Software | [MIT](software/LICENSE) | `software/` |
| Documentation | [CC0 1.0](docs/LICENSE) | `docs/`, `knowledge/` |
| Root fallback | [Apache-2.0](LICENSE) | root-level files and `tools/` without a nearer notice |

See [LICENSING.md](LICENSING.md) for precedence and mixed-directory details.

---

## Defensive Publication Notice

The SPU-13 architecture, including the dual-ring arithmetic framework, the Barycentric Transmutation Unit (BTU) bridge, the $\mathbb{Z}/M_{31}$ Mersenne-ring core, and the $\mathbb{Z}[\phi]/L_p$ Lucas Phinary co-processor, is publicly disclosed in this repository and associated publications as **defensive prior art**.

The intended disclosure scope includes:
1. **Dual-Ring Execution Topology:** The co-processor coupling of a $\mathbb{Z}/M_{31}$ binary ring with a $\mathbb{Z}[\phi]/L_p$ phinary ring, connected via a spatial routing bridge (BTU).
2. **Lucas Barrett Reduction in Hardware:** The hardware-native remainder calculation for Lucas prime moduli ($q = (x \cdot \mu) \gg 31$, $r = x - q \cdot L_p$) using elaboration-time precalculated scale constants ($\mu = \lfloor 2^k / L_p \rfloor$).
3. **Chirality & Scaling Intercepts:** The instruction intercept (`lucas_inst_claimed`) and register commit override path mapped in [spu_a7_top.v](hardware/boards/artix7/spu_a7_top.v) for `0xD0` (PSCALE) and `0xD1` (PCHIRAL).

This notice records publication intent; it is not legal advice or a guarantee of
the treatment any patent office will give a particular claim. Contributions
require sign-off under the [Developer Certificate of Origin (DCO)](CONTRIBUTING.md).


## Quick Start (30 seconds to proof)

```bash
# Replay the complete deterministic current-signature classification ABI
python3 tools/som_sensor_replay.py
```

This generates unseen integer-current windows, extracts four temporal features,
crosses the explicit Cartesian-to-SOM boundary, classifies them with the checked
map, emits complete SOM1 frames, and parses those frames through the production
host consumer. Expected result: 18/18 with zero ambiguity.

```bash
# Deterministic fresh-clone regression
python3 run_all_tests.py                  # 173/173 at this revision

# Rational robotics remains available as a second software demonstration
python3 software/tests/test_rational_robotics.py  # PASS (104 checks)
```

---

## Architecture

### Two cores

| Core | Axes | Role |
|------|------|------|
| **SPU-4 Sentinel** | 4 (Quadray) | Euclidean satellite, sensory input |
| **SPU-13 Cortex** | 13 (cuboctahedral) | Synergetic manifold engine |

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

### RPLU2 — Rational Polynomial Look-Up

RPLU2 uses corrected 149-record boot/config profiles for Padé coefficients, BTU
rows, and Quadray constants. SD/RP2350/FPGA table hydration is proven in
silicon; lean live-evaluator proofs target Artix-7 while full concurrent
integration is reserved for a larger FPGA.

---

## Hardware Targets

| Tier | Board | FPGA | Status |
|------|-------|------|--------|
| 1 Micro | Tang Nano 1K | GW1NZ-1 | ✅ Bitstream |
| 2 Small | iCESugar v1.5 | iCE40UP5K | ✅ Bitstream |
| 3 Mid | Tang Nano 9K | GW1N-9C | ✅ Synthesis |
| 4 Mid | Tang Primer 20K | GW2A-18 | ✅ Synthesis |
| 5 Regression | **Tang Primer 25K** | GW5A-25A | ✅ Split probes + southbridge |
| 6 Evidence / Constrained Integration | **Wukong Artix-7 100T** | XC7A100T | J11 silicon proofs, sidecars, shared-multiplier baseline |
| 7 Open HW | **SPU-13 ECP5 Evaluator** | LFE5U-85F / LFE5U-44F | Draft OSHWA concept; KiCad ERC/DRC audit pending |
| 8 Full Integration | Artix-7 200T / Kintex-class | TBD | Funding-dependent full concurrent target |

---

## ECP5 OSHWA Physical Layout & Verification (Symmetry-Informed Heuristic)

To secure open-source toolchain portability and move toward official OSHWA self-certification, the SPU-13 architecture includes a draft custom physical evaluator concept with point-symmetric layout constraints. The current KiCad package is not yet fab-ready; see `hardware/docs/ecp5_oshwa_deliverable_audit.md`.

* **Symmetric Hexagonal Board Outline:** The PCB profile utilizes a mathematically generated $60^\circ$ isotropic bounding polygon in KiCad to align trace propagation paths with the triangular symmetry of the Isotropic Vector Matrix (IVM).
* **Point-Symmetric Radial Node Placement:** High-speed control lines and register file macros are routed radially from a fixed central coordinate origin $(X_0, Y_0)$ on the ECP5-85F to 12 point-symmetric ring nodes at exact $30^\circ$ increments, establishing an identical nominal path length of $25.0\text{ mm}$ without serpentine tuning.
* **Simulation-Estimated Skew Verification:** Wavefront propagation is verified programmatically via `tools/simulate_synergetic_routing.py` using an idealized microstrip model ($v = 150\text{ mm/ns}$, $\varepsilon_r \approx 4.0$), demonstrating a nominal time-of-flight of $166.67\text{ ps}$ with $0.0\text{ ps}$ of geometric path-length skew.
* **Physical Validation Pending Verification:** These layout parameters remain structural simulation models until subjected to post-layout parasitic extraction (OpenEMS/SIwave), high-speed Time-Domain Reflectometry (TDR) measurement of test coupons, and physical active-probing capture of live silicon skew.

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

Licensing is layer-specific: CERN-OHL-W-2.0 for hardware, MIT for software,
CC0 1.0 for general documentation, and Apache-2.0 as the root fallback. See
[LICENSING.md](LICENSING.md); individual papers may carry an explicit CC BY
4.0 notice for deposit.
