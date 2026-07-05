# SPU-13 Test Coupon Specification & Validation Plan

**Document Version:** 0.2 (June 2026)
**Status:** Draft — Experimental validation pathway
**Scope:** Galileo validation (Sierpinski power plane, 60° routing) via TDR, EM, and thermal measurement

---

## 1. Overview

This document specifies a family of **test coupons** (miniature PCB samples) designed to validate the exploratory geometries defined in `hardware/docs/pcb_guidelines.md`:

- **Sierpinski carpet power plane** (fractal via stitching, area reduction)
- **60-degree signal routing** (smooth bends, impedance discontinuity)
- **Baseline (solid plane, Manhattan)** — control

Each coupon is measured via:
- **EM simulation** (S-parameters: return loss S11, insertion loss S21, 100 MHz – 10 GHz)
- **Time-domain reflectometry (TDR)** (impedance discontinuity, reflection coefficient)
- **PDN impedance** (frequency response, resonance peaks)
- **Thermal imaging** (hot spots under sustained load, validation of thermal distribution)

---

## 2. Coupon Family Matrix

| Coupon | Power Plane | Signal Routing | Via Stitching | Purpose |
|:---|:---|:---|:---|:---|
| **Baseline** | Solid | Manhattan (90°/45°) | Standard (2 mm pitch) | Control |
| **Sierpinski-1** | Fractal (n=1, 88.9% area) | Manhattan | Standard | Power plane resonance (shallow fractal) |
| **Sierpinski-2** | Fractal (n=2, 79.0% area) | Manhattan | Standard | Power plane resonance (deeper fractal) |
| **60-Degree** | Solid | 60° isotropic grid | Standard | Signal integrity / impedance matching |
| **Sierpinski + 60°** | Fractal (n=1) | 60° isotropic | Standard | Combined topology |

All coupons share:
- **Substrate:** FR-4, 1.6 mm, ε_r ≈ 4.3, tan_δ ≈ 0.025 @ 1 GHz
- **Layers:** 4 (signal, ground, power, signal)
- **Trace:** 50 Ω microstrip (width ≈ 2.8 mm for 1.6 mm FR-4)
- **Connectors:** SMA (female) or pogo pads for easy connection to measurement instruments
- **Dimensions:** ~80 mm × 20 mm (fits in standard EVM envelope)

---

## 3. Electrical Specifications

### 3.1 Microstrip Trace

**Goal:** Validate trace impedance and insertion loss.

| Parameter | Value | Justification |
|:---|:---|:---|
| Trace length | 50 mm | Short coupon (TDR rise time ~3.3 ns @ c_eff ≈ c/√4.3) |
| Trace width | 2.8 mm | 50 Ω nominal on 1.6 mm FR-4 (calculated via TL formulas) |
| Trace thickness | 35 µm | Standard copper foil (1 oz) |
| Ground plane | Solid (baseline), Sierpinski (test) | 6.35 mm separation (reference) |
| Material | FR-4 | Industrial standard, well-characterized |

**Impedance calculation (Hammerstad-Jensen, 1981):**
```
Z₀ = (120 / π√ε_r) · ln((4h + 0.61w) / (0.81w + t))
where: h = 1.6 mm, w = 2.8 mm, t = 0.035 mm, ε_r = 4.3
=> Z₀ ≈ 50.2 Ω (acceptable tolerance ±5%)
```

### 3.2 Power/Ground Vias (Sierpinski)

**Goal:** Measure resonance shift due to fractal plane geometry.

| Parameter | Value | Note |
|:---|:---|:---|
| Via diameter | 0.8 mm | Standard 28mil drill |
| Via pad | 1.2 mm | Standard 45mil pad |
| Via-to-via pitch (baseline) | 2 mm | Dense stitching (every ~0.5 λ @ 1 GHz) |
| Via-to-via pitch (fractal) | Adaptive per Sierpinski layer | See Section 3.3 |
| Via inductance | ~15 pH per via pair | Typical for 1.6 mm board |

### 3.3 Sierpinski Carpet Geometry

**Fractal definition:** At depth n, remove the center 1/9th of a 3×3 grid recursively.

**Layout mapping (on 50 mm × 20 mm coupon):**

| Depth | Area fraction | Repeat pattern | Via hole size | Purpose |
|:---|:---|:---|:---|:---|
| n=0 | 1.000 | Solid (baseline) | N/A | Control |
| n=1 | 0.889 | 3×3 grid, center removed | 6.7 mm per cell | Moderate resonance shift |
| n=2 | 0.790 | 9×9 grid (nested 3×3×3) | 2.2 mm per cell | Stronger aperiodicity |

**Mechanical implementation:** Use **copper pour zones** in KiCad with exclusion polygons (no-pour regions define the fractal holes). Via arrays remain in place but with reduced copper connect-point area per via.

---

## 4. Test Plan

### 4.1 Simulation (EM — openEMS)

**Goal:** Baseline S-parameter vs. geometry before physical build.

**Setup:**
- **Solver:** openEMS FDTD (Yee grid, 0.2 mm mesh)
- **Port impedance:** 50 Ω (SMA reference)
- **Frequency:** 100 MHz – 10 GHz (501 points logarithmic)
- **Excitation:** Gaussian pulse (bandwidth covers full range)
- **Domain size:** ±50 mm in x, ±25 mm in y, +1 mm in z (air above) to –2 mm (below via plane)

**Output metrics:**
| Metric | Spec | Acceptance |
|:---|:---|:---|
| S11 (return loss) | < –10 dB (VSWR < 2) @ 50 MHz – 1 GHz | Target: Baseline achieves > –15 dB @ DC–500 MHz |
| S21 (insertion loss) | < –1 dB @ 100 MHz – 1 GHz | Target: < –0.5 dB (low loss) |
| S11 peaks (Sierpinski) | Compare resonance signature @ n=1 vs n=2 | Fractal should show diffuse, lower peaks vs. baseline |
| Input impedance Z_in | Real(Z) ≈ 50 Ω ± 5 Ω over DC–500 MHz | Validation of trace design |

**Simulation commands:**
```bash
# Baseline coupon
python3 tools/pcb_coupons/generate_openems_coupon.py \
  --length 50 --trace-w 2.8 --via-stitch \
  --out sim/baseline_50mm

# Sierpinski-2 coupon (fractal plane, 79% copper)
python3 tools/pcb_coupons/generate_openems_coupon.py \
  --length 50 --trace-w 2.8 --via-stitch \
  --sierpinski-depth 2 \
  --out sim/sierpinski2_50mm

# 60-degree routing (curved traces)
python3 tools/pcb_coupons/generate_openems_coupon.py \
  --length 50 --trace-w 2.8 --routing-angle 60 \
  --out sim/angle60_50mm
```

### 4.2 TDR Measurement (Physical Coupon)

**Goal:** Measure impedance discontinuities, rise time, reflection coefficient in real hardware.

**Equipment:**
- **TDR instrument:** Tektronix DSA70404C or equivalent (picosecond rise time, Z₀ characterization)
- **Calibration:** Full 2-port calibration (open, short, load @ SMA)
- **Test points:** Port 1 (input), Port 2 (output)
- **Differential setup (optional):** Measure differential pairs on 60° coupon

**Measurement procedure:**
1. Connect TDR Port 1 to J1 (input SMA).
2. Terminate Port 2 with 50 Ω SMT load or open (measure both).
3. Step input: amplitude 500 mV, rise time < 50 ps.
4. Capture waveform: 10 ns window, 2 GHz sample rate.
5. Extract impedance profile Z(t) via TDR algorithm.

**Output data:**
```
time (ps) | impedance (Ω) | reflection coeff | standing wave magnitude
-10       | 50.2          | 0.00             | 1.0
0         | 50.3          | 0.00             | 1.0
10        | 51.5          | 0.015            | 1.015
...
500       | 49.8 (reflection from load) | ...
```

**Acceptance criteria:**
| Metric | Baseline | Sierpinski-2 | 60-Degree | Delta Target |
|:---|:---|:---|:---|:---|
| Mean Z(t) | 50 ± 1 Ω | 50 ± 1.5 Ω | 50 ± 0.5 Ω | < 2% variation |
| Peak ΔZ | < 1 Ω | < 3 Ω | < 0.5 Ω (smooth bends) | Sierpinski OK if ≤ 3× baseline |
| Rise time @ 10–90% | ≈ 3 ns | ≈ 3–3.2 ns | ≈ 2.9 ns | Propagation delay Δ < 100 ps |
| Reflection (return) | < –20 dB | < –15 dB | < –22 dB | All acceptable |

### 4.3 PDN Impedance (VNA Sweep)

**Goal:** Measure power delivery impedance Z_PDN(f) and detect resonance peaks.

**Equipment:**
- **VNA:** Rohde & Schwarz or equivalent (S-parameter measurement)
- **Calibration:** Port 1 to SMA-J1, Port 2 to 50 Ω load (or open for return-path impedance)
- **Frequency:** 1 MHz – 2 GHz (1001 points)

**Measurement:**
1. **S11 (return impedance):**
   ```
   Z_in(f) = Z₀ · (1 + S11(f)) / (1 – S11(f))
   where Z₀ = 50 Ω
   ```
2. **S21 (insertion loss):**
   ```
   |S21(f)| in dB = 20 log₁₀ |S21|
   ```

**Analysis (post-processing):**
```python
import numpy as np
import matplotlib.pyplot as plt

# Load VNA data (S1P or Touchstone)
freqs, s11 = load_s1p('baseline_s11.s1p')

# Compute impedance
z_in = 50 * (1 + s11) / (1 - s11)
z_real = np.real(z_in)
z_imag = np.imag(z_in)
z_magnitude = np.abs(z_in)

# Find resonance peaks
peaks = find_peaks(z_magnitude)[0]
for peak in peaks:
    print(f"Resonance @ {freqs[peak]/1e9:.3f} GHz: Z = {z_magnitude[peak]:.1f} Ω")

# Plot
plt.figure(figsize=(12,8))
plt.subplot(2,1,1); plt.semilogx(freqs/1e9, z_real); plt.ylabel('Re(Z) Ω'); plt.title('PDN Impedance')
plt.subplot(2,1,2); plt.semilogx(freqs/1e9, z_imag); plt.ylabel('Im(Z) Ω'); plt.xlabel('Freq (GHz)'); plt.grid()
plt.tight_layout(); plt.savefig('pdn_impedance.png'); plt.show()
```

**Acceptance criteria:**
| Coupon | Target | Tolerance | Note |
|:---|:---|:---|:---|
| Baseline | Z_PDN(1 GHz) = 50 ± 2 Ω | ±2 Ω | Reference |
| Sierpinski-1 | Z_PDN(1 GHz) = 50 ± 3 Ω | ±3 Ω | Acceptable (slightly broader, lower Q) |
| Sierpinski-2 | Z_PDN(1 GHz) = 50 ± 4 Ω | ±4 Ω | Acceptable (fractal aperiodicity) |
| 60-Degree | Z_PDN(1 GHz) = 50 ± 2 Ω | ±2 Ω | Smooth routing → lower discontinuity |

**Resonance peaks (detect via derivative or peak finder):**
- Baseline: Sharp peaks at ~400 MHz, ~900 MHz (cavity resonances in solid plane)
- Sierpinski-1: Peaks broader, lower amplitude (fractal dampens sharp modes)
- Sierpinski-2: Flatter spectrum, minimal peaks (deep fractal → aperiodic scattering)

---

## 5. Thermal Measurement (Optional — Phase 2)

**Goal:** Validate thermal distribution under sustained high-current operation.

**Setup:**
- **Stimulus:** 1 A DC current through trace for 5 minutes (sustained high current)
- **Measurement:** Thermal camera (FLIR, Keysight, etc.) capture at 30 Hz
- **Coupon mounting:** Held at ambient (25°C) with thermal paste contact on bottom copper to reference

**Metrics:**
| Coupon | ΔT (peak–ambient) | Hot spot location | Uniformity (std dev of T map) |
|:---|:---|:---|:---|
| Baseline | ~8°C | Center of trace (uniform) | 0.5°C |
| Sierpinski-2 | ~9–12°C | Via-stitch regions (clustered heating) | 1.5–2°C (non-uniform due to fractal) |
| 60-Degree | ~7°C | Smooth bends (more uniform than baseline) | 0.3°C |

**Interpretation:**
- Sierpinski fractal may concentrate current in remaining copper islands → local hot spots.
- 60° routing with smooth bends distributes heating more uniformly (lower peak ΔT, lower variance).

---

## 6. Manufacturing & Bill of Materials

### PCB Fabrication
- **Quantity:** 5 coupons per type (Baseline, Sierpinski-1, Sierpinski-2, 60-Degree, Combined)
- **Vendor:** OSH Park, PCBWay, or Prototype Lab (sub-$100 for 25 total coupons)
- **Lead time:** 2–3 weeks for first batch
- **Gerber package:** Auto-generated from KiCad via `pcbnew` or `generate_kicad_coupon.py` + Gerber writer

### Components (per coupon)
| Part | Value | Package | Qty | Cost |
|:---|:---|:---|:---|:---|
| SMA connector | Female, Receptacle | SMD-J | 2 | $0.50 |
| 50 Ω terminator (SMT) | 50 Ω, 1% | 0603 | 1 (optional load) | $0.10 |
| Fiducials | - | 1 mm copper | 3 | N/A |

**Total cost per coupon:** ~$8–15 (PCB + components + assembly)

---

## 7. Expected Outcomes & Success Criteria

| Hypothesis | Prediction | Success Metric | Status |
|:---|:---|:---|:---|
| **Sierpinski plane reduces cavity resonance** | Peak S11 @ 400–900 MHz narrower, lower amplitude | S11 peak reduction ≥ 2 dB vs. baseline | TBD (measurement) |
| **Fractal geometry scatters EM uniformly** | PDN impedance spectrum flatter (lower Q, fewer sharp peaks) | Resonance peaks < –5 dB across 100 MHz–2 GHz | TBD |
| **60° routing improves signal integrity** | Smoother impedance profile, lower discontinuity | S11 > –20 dB @ 100 MHz–1 GHz; Z variation < 1 Ω | TBD |
| **Sierpinski increases local thermal stress** | Hot spots at via-stitch clusters | ΔT(Sierpinski) < 1.5× ΔT(baseline); std dev < 2°C | TBD (thermal imaging) |

---

## 8. Risk Mitigation

| Risk | Mitigation |
|:---|:---|
| Fabrication tolerance on trace width | Use KiCad DRC to verify ±0.05 mm tolerance; add test pads for post-fab SEM inspection |
| SMA connector parasitics dominate | Use low-loss connectors; baseline coupon validates reference; compare deltas only |
| Substrate variability (ε_r, tan_δ) | Request material cert from fab; use VNA calibration kit to measure dielectric @ coupon frequency |
| Via stub resonances (Sierpinski) | Simulate stub length via openEMS; backdrilling optional for deeper coupons |
| Measurement uncertainty | Cross-validate TDR + VNA + EM simulation; use calibrated instruments (NIST-traceable) |

---

## 9. Timeline & Next Steps

| Phase | Task | Duration | Owner | Status |
|:---|:---|:---|:---|:---|
| **Phase 1: Design** | Generate KiCad layouts, EM simulation | 1 week | Design | ✅ In progress |
| **Phase 2: Fabrication** | Order PCBs, components | 3 weeks | Fab vendor | ⏳ Pending Phase 1 |
| **Phase 3: Assembly** | Solder SMA, test connectivity | 1 week | Lab | ⏳ Pending Phase 2 |
| **Phase 4A: EM Validation** | VNA + openEMS simulation correlation | 1 week | Test | ⏳ Pending Phase 3 |
| **Phase 4B: TDR Measurement** | Impedance profile + reflection data | 1 week | Test | ⏳ Pending Phase 3 |
| **Phase 4C: Thermal (optional)** | FLIR thermal imaging under load | 1 week | Test | ⏳ Optional Phase 4 |
| **Phase 5: Analysis & Report** | Synthesis, final recommendations | 2 weeks | Analysis | ⏳ Pending Phase 4 |

**Go/No-Go decision point:** After Phase 4B (TDR), decide whether fractal plane / 60° routing should be adopted for Tang 25K pilot board or shelved for future exploration.

---

## 10. References

1. **Hammerstad, E., & Jensen, Ø.** (1981). Accurate Models for Microstrip Computer-Aided Design. *IEEE Trans. Microwave Theory Tech.*, MTT-28(5), 349–359.
2. **Thliebig, C., et al.** openEMS — open electromagnetic simulator. https://github.com/thliebig/openEMS
3. **IPC-2221B:** Generic Standard on Printed Board Design.
4. **CAEBAT:** FR-4 material properties database. https://caebat.fcc.chtsec.org/
5. **Maksimovic, D., & Wood, P.** (2007). Design and Optimization of Low-EMI Switching Power Supplies. In *High-Frequency Power Conversion* (pp. 224–251).

---

## Appendix A: KiCad Coupon Generator Usage

```bash
# Generate baseline coupon
python3 tools/pcb_coupons/generate_kicad_coupon.py \
  --out coupons/baseline_50mm.kicad_pcb --length 50 --trace-w 2.8 --via-stitch

# Generate Sierpinski-2 coupon (with fractal power plane exclusions)
python3 tools/pcb_coupons/generate_kicad_coupon.py \
  --out coupons/sierpinski2_50mm.kicad_pcb --length 50 --trace-w 2.8 \
  --sierpinski-depth 2 --via-stitch

# Open in KiCad
kicad coupons/baseline_50mm.kicad_pcb &
```

---

## Appendix B: OpenEMS Simulation Template

```bash
python3 tools/pcb_coupons/generate_openems_coupon.py \
  --length 50 --trace-w 2.8 --substrate-h 1.6 \
  --freq-min 100e6 --freq-max 10e9 --freq-points 501 \
  --via-stitch --via-pitch 5 \
  --out sim/baseline_s11

# View results
# - sim/baseline_s11_s11.txt — S11 vs freq
# - sim/baseline_s11_s21.txt — S21 vs freq
# - sim/baseline_s11_z_in.txt — Z_in vs freq
# - sim/baseline_s11_sparameters.png — plots
```

---

**Document prepared by:** Hardware Validation Team
**Last updated:** 2026-07-04
**Next review:** After Phase 1 completion (design validation)
