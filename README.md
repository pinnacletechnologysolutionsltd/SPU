# SPU-13 Synergetic Processing Unit

**A deterministic exact-arithmetic FPGA platform: no floating point, no
division and no transcendentals anywhere in the RTL. Arithmetic is exact over
`Q(√3)`, `A₃₁` and `Z[φ]/L_p`, and correctness is decided by bit-exact
agreement with an independent software oracle rather than by code review.**

**Current direction: graphics.** A framebuffer-less streaming rasterizer that
reached silicon across three consecutive days — first video output (§3.8),
first rasterized geometry (§3.9) and depth-resolved geometry (§3.10) in
[`docs/hardware_evidence.md`](docs/hardware_evidence.md) — each measured
against a prediction registered before the bitstream was built.

[![CI](https://github.com/pinnacletechnologysolutionsltd/SPU/actions/workflows/ci.yml/badge.svg)](https://github.com/pinnacletechnologysolutionsltd/SPU/actions/workflows/ci.yml)
[![Hardware: CERN-OHL-W-2.0](https://img.shields.io/badge/Hardware-CERN--OHL--W--2.0-blue.svg)](hardware/LICENSE)
[![Software: MIT](https://img.shields.io/badge/Software-MIT-green.svg)](software/LICENSE)
[![Docs: CC0](https://img.shields.io/badge/Docs-CC0_1.0-lightgrey.svg)](docs/LICENSE)
[![RPLU paper DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21446712.svg)](https://doi.org/10.5281/zenodo.21446712)
[![LUCAS paper DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21447440.svg)](https://doi.org/10.5281/zenodo.21447440)

**Not an engineer? [Start with the two-minute explanation.](docs/WHAT_IS_SPU13.md)**

## How this was built

SPU-13 is designed, specified and directed by John Curley. Much of the RTL,
tooling and documentation was **written with AI assistance** under a contract-and-audit process.

Nothing here is claimed to be hand-written.

What is the author's: the architecture and the mathematics — exact arithmetic
over `Q(√3)`, `A₃₁` and `Z[φ]/L_p`, the Davis Gate as an exact zero test rather
than an epsilon comparison, Fibonacci-gated dispatch — and the rule below.

**The oracle is normative.** Correctness here is not decided by reviewing
generated code. It is decided by bit-exact agreement between the RTL and an
independent software implementation, checked by a testbench gate that must pass
100% before anything merges. If the RTL and the oracle disagree, the RTL is
wrong. That rule is what makes AI-written hardware checkable at all, and it is
the reason this repository can show you results instead of asking you to trust
its authorship.

Two consequences you can verify rather than take on faith:

- **Hardware claims cite their evidence.** Any statement that something was
  observed on physical hardware cites a section of
  [`docs/hardware_evidence.md`](docs/hardware_evidence.md) — date, build and
  load commands, bitstream SHA-256, raw captured proof lines. Claims that have
  no such section are labelled `[NO ENTRY]` in place rather than quietly
  asserted.
- **Negative results stay published.** Failed hypotheses, retracted
  conclusions and measurements that did not go our way are kept in the record,
  not deleted. See `AGENTS.md` for the standing example.

## Start here

- **[Your first hour](docs/FIRST_HOUR.md)** — anonymous clone, full regression,
  software VM, one small Forge program, then optional Tang hardware
- **[Quadray for programmers](docs/QUADRAY_FOR_PROGRAMMERS.md)** — four-axis
  representation, normalization conventions, and a worked exact rotation
- **[Hardware-free demo tour](docs/DEMO_TOUR.md)** — robotics, LUCAS, Iris SOM,
  and exact Voronoi decision evidence, each with an explicit claim boundary

## Current direction — graphics

The active work is a rasterizer that streams pixels synchronously with the
display beam and holds **no framebuffer at all**. Three results on the Wukong
Artix-7, each with its bitstream pinned by SHA-256 and its measurement method
recorded, in [`docs/hardware_evidence.md`](docs/hardware_evidence.md):

| | result | what was measured |
|---|---|---|
| **§3.8** | First video output | 640×480 @ 60 Hz colour bars, 0.006% timing error |
| **§3.9** | First rasterized geometry | Triangle base 55% of screen width against 53% predicted; stair-stepping at the predicted ~0.607 px/row |
| **§3.10** | First depth-resolved image | Two overlapping triangles; depth boundary at 0.5062 and 0.4986 of lit width against 0.5000 predicted, across two observations either side of a power cycle |

§3.10 also states what it does **not** establish: no 3D, no projection, no
transform, no shading, no texturing, no antialiasing, no host link. The
triangles are hardcoded constants and the scene is static.

The toolchain is fully open — Yosys and nextpnr-xilinx via openXC7, no vendor
IDE. That constraint is load-bearing rather than incidental: openXC7 cannot
place differential outputs, so HDMI is unreachable and the VGA path exists
because it is what a fully open flow can actually build.

### Paused: SOM edge classification and SPU-4

The SOM/anomaly-detection sidecar was the prior product direction, and its
results stand: all 150 SOM1 records matched the exact software oracle on both
Tang Primer 25K and Wukong Artix-7, with the Iris map scoring 147/150
semantically. Development was **paused on 2026-09-03** in favour of processor
and graphics work. It is not abandoned: a retest is going ahead
(`docs/BENCH_BOM.md` §2 records it as conditional, not dead), and a return to
active development depends on that retest reaching parity — see
[`docs/SOM_V1_PRODUCT_CONTRACT.md`](docs/SOM_V1_PRODUCT_CONTRACT.md).

The **SPU-4 Sentinel** edge node was developed alongside it as a reusable
product block and is shelved on the same date. Its silicon results and claim
ledger stand — [`knowledge/SPU4_ARCHITECTURE.md`](knowledge/SPU4_ARCHITECTURE.md)
and [`docs/SPU4_PRODUCT_CLAIMS.md`](docs/SPU4_PRODUCT_CLAIMS.md). Kept linked
deliberately: shelved work stays discoverable rather than becoming
unreachable, which is how documents drift out of review in the first place.

## Boards

| Board | Role |
|---|---|
| **Wukong Artix-7 100T** | Primary silicon-evidence board; all current graphics results |
| **Tang Primer 25K** | Gowin regression and probe board |

A microcontroller southbridge (RP2350 over SPI, protocol v1.2) exists and is
documented in
[`docs/SOUTHBRIDGE_SPI_PROTOCOL.md`](docs/SOUTHBRIDGE_SPI_PROTOCOL.md). It is
**parked**, not retired: the current graphics work needs no host link, and
opening that track was deliberately deferred. See
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

## Prior art and contributions

Everything here is published openly as prior art; the licences above govern
reuse. Contributions require sign-off under the
[Developer Certificate of Origin (DCO)](CONTRIBUTING.md).

## Check it yourself (no trust required)

The commands below are the maintained reproduction surface. Their expected
outputs are explicit, and the current headline was re-run from source on
2026-08-13; hardware evidence remains pinned separately in the ledger.

```bash
# 1. Full regression — RTL testbenches, C++ and Python oracles
python3 run_all_tests.py                          # currently prints "Total PASS: 226"
                                                  # and "Total FAIL: 0"

# 2. The product path, end to end
python3 tools/som_sensor_replay.py                # SENSOR_REPLAY: PASS
                                                  # windows=18 exact=18/18
                                                  # ambiguous=0, plus dataset
                                                  # and map SHA-256
```

That second command generates unseen integer-current windows, extracts four
temporal features, crosses the explicit Cartesian-to-SOM boundary, classifies
them with the checked map, emits complete SOM1 frames, and parses those frames
through the production host consumer.

```bash
# 3. The RTL is checked against an independent oracle, not against review.
#    These six [4/4] Padé vectors were derived from software/lib/a31_field.py
#    and are re-derivable from it; the bench drives them through the RTL and
#    compares all four A₃₁ result lanes exactly, in both pipeline modes.
TB_FILTER=rplu_thimble python3 run_all_tests.py   # Verilog Tests: 2, Passed: 2
cat hardware/tests/spu13/pade_eval_vectors.mem    # the vectors, in plain hex

#    run_all_tests.py reports pass/fail, not per-check counts. To see the
#    bench's own tally, run it directly:
iverilog -g2012 -y hardware/rtl/gpu -y hardware/rtl/core/spu13 \
    -y hardware/rtl/core/shared -y hardware/rtl/math -y hardware/rtl/common \
    -I hardware/rtl/arch -s rplu_thimble_pade_tb \
    -o build/thimble.vvp hardware/tests/spu13/rplu_thimble_pade_tb.v
vvp build/thimble.vvp                             # PASS: rplu_thimble_pade_tb (33/33)

# 4. Software oracles, independently
python3 software/tests/test_rational_robotics.py  # PASS (104 checks)
python3 software/tests/test_lucas_mac_oracle.py   # COMPOSITE ZERO-DRIFT: PASS
                                                  # 166666 identity macros,
                                                  # 999996 primitive ops
python3 software/tests/test_lucas_mac_rtl_trace.py # LUCAS_TRACE: PASS cases=59
iverilog -g2012 -o build/lucas_poison.vvp \
    hardware/rtl/core/spu13/spu13_lucas_mac.v \
    hardware/tests/spu13/spu13_lucas_mac_poison_tb.v && \
    vvp build/lucas_poison.vvp                    # LUCAS_POISON: PASS
python3 software/tests/test_rotc_vm_rtl_trace.py  # VM-vs-RTL TRACE EQUIVALENCE
                                                  # (angles 0-35): PASS
```

The current headline is `Total PASS: 226`, `Total FAIL: 0`, measured
2026-09-06 via `bash tools/verify_repo.sh`. Individual hardware evidence
entries remain date- and artifact-specific.

**One caveat on that gate, recorded because it was wrong for a long time.**
Until 2026-09-05 `run_all_tests.py` had no `sys.exit` call: it printed
`Total FAIL: 2` and returned 0, so both `verify_repo.sh` and CI reported
success regardless of test failures. Fixed at both ends, with negative
controls. Test counts quoted before that date were true when measured, but the
automation behind them was not enforcing anything.

**What you cannot check from a clone, and why.** Bitstreams are build artifacts
and are not committed; `build/` is gitignored. Silicon results are therefore
recorded rather than reproduced here — each one in
[`docs/hardware_evidence.md`](docs/hardware_evidence.md) pins its bitstream by
SHA-256 and byte count and includes the raw captured output, so a claim can be
matched against a specific image rather than a description of one. Reproducing
them needs the board.

**A note on counts.** `run_all_tests.py`'s summary counts *benches and
variants*, not individual checks — a bench that goes from 8 to 33 internal
checks does not move the headline. `TB_FILTER` filters only the Verilog benches;
the C++ and Python suites run regardless. Read the per-bench lines, not just the
total.

**Read one entry to judge the rest.** §3.2e.7 is the standard the others are
held to: a hash-pinned bitstream, ten runs rather than one, an internal positive
control (the float64 arm must diverge, and does, at step 79 in every run), and
an explicit statement of what it does *not* establish.

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

### RPLU2 — Rational Projection Logic Unit

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
| 8 Full Integration | Artix-7 200T / Kintex-class | TBD | Not pursued; would need a larger part than the project owns |

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
