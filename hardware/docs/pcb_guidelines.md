# SPU-13 PCB Physical Layer Guidelines (Experimental)

**Status:** Exploratory / Experimental — Do not use in production boards
without thorough simulation and measurement validation.

This document captures geometric concepts inspired by the project's 60°
coordination, IVM lattice, and deterministic philosophy. These ideas are
**hypotheses**, not proven design rules.

## 1. Sierpinski Carpet Power Distribution (Exploratory)

**Concept**
Apply a Sierpinski carpet pattern to power and/or ground planes at selected
iteration depths to reduce effective copper area and modify return current
paths.

**Area Scaling**
Remaining copper fraction after *n* iterations:

$$A_n = A_0 \left( \frac{8}{9} \right)^n$$

**Intended Exploration**
- Reduce parallel-plate capacitance.
- Increase perimeter length to potentially distribute high-frequency return currents.
- Modify PDN impedance profile and cavity resonances.

**Risks & Limitations**
- Increased DC resistance and potential thermal hotspots.
- Broken return paths → possible increase in inductance, EMI, and ground bounce
  if not properly stitched.
- Isolated copper islands at n ≥ 2 have no DC path to the rest of the plane.
  These cause fabrication issues (acid trapping, floating copper). Mitigations:
  limit to n ≤ 1, add thin connecting tabs, or use a grid/lattice structure.
- **Never use under high-current regions, analog sections, ADCs, clock generators,
  or sensitive analog circuits.** Keep solid ground planes under these areas.

**Requirements Before Use**
- Full PDN simulation (ANSYS SIwave, CST, or equivalent).
- Via stitching strategy (dense via arrays connecting planes across layers).
- Thermal analysis for current-carrying capacity.
- Comparison against solid-plane baseline.

## 2. 60° Isotropic Routing and Controlled Bends (Exploratory)

**Concept**
Prefer 60° routing angles aligned with triangular/hexagonal lattice symmetry.
Replace sharp 90° corners with controlled-radius arcs where practical.

**Guidelines (Subject to Validation)**
- Minimum bend radius: R ≥ 3 × trace width (w) for high-speed signals.
- Use consistent 60° increments for routing grid where possible.
- For differential pairs: maintain symmetry and controlled impedance.
- Consider hexagonal bucking-loop return paths for critical high-speed nets.

**Intended Benefits**
- Reduced impedance discontinuities compared to abrupt 90° corners.
- Improved geometric consistency with project's algebraic and spatial foundations.
- Potential reduction in reflections and timing jitter on critical buses.

**Practical Considerations**
- EDA tool support for 60° routing is limited (manual or scripted routing often required).
- BGA breakout and fanout become more complex.
- Via stubs and back-drilling may still be needed for high-speed SERDES.
- Differential impedance control must be maintained across bends.

**Risks**
- Longer trace lengths possible.
- Routing density tradeoffs in dense areas.
- No guarantee of superior signal integrity without simulation.

## Validation Requirements (Mandatory)

**Simulation**
- Tools: HFSS, CST Studio, ANSYS SIwave, ADS, or OpenEMS.
- Metrics: PDN impedance (0.1 MHz – ≥10 GHz), S-parameters, time-domain
  transients, eye diagrams, reflection coefficients.
- Always include solid-plane baseline comparison.
- Mesh convergence studies and proper port setup required.

**Test Coupons**
- Fabricate dedicated coupons for PDN and routing variants.
- Measure with VNA (S-parameters) and TDR/TDT.
- Correlate simulation vs. hardware before committing to main board.

**Manufacturability (DFM)**
- Minimum copper pour features, annular rings, and thermal relief per fab house rules.
- Avoid isolated copper islands (add stitching tabs or remove).
- Ensure adequate via arrays for current return and thermal relief.
- High-current nets must use wide traces or multiple vias.

**Best Practices (Always Follow)**
- Proper decoupling capacitor placement and values.
- Bulk capacitance + high-frequency decoupling.
- Via stitching every few mm on ground planes.
- Solid ground under analog, clock, and sensitive circuitry.
- Careful stackup design for controlled impedance.

## Summary Position

The Sierpinski carpet power mesh and 60° routing concepts are
**architecturally interesting explorations** that align with SPU-13's
geometric principles. However, they introduce non-trivial SI/PI, thermal,
and manufacturing risks. They must be treated as experimental until
validated with proper electromagnetic simulation and hardware measurement.

**Do not apply these techniques to production or bring-up boards without
completing the validation plan.**

## When To Revisit

These guidelines apply to a **custom SPU-13 carrier board** considered after
the FPGA spin ladder is complete and commercial dev-kits are no longer
sufficient. The current Tang 25K and Wukong Artix-7 boards are fixed —
they cannot benefit from fractal planes or 60-degree routing.
