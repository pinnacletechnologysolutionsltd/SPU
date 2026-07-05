# PCB Test Coupon Validation — Quick Reference

## Files Created

| File | Purpose |
|:---|:---|
| `tools/pcb_coupons/generate_kicad_coupon.py` | Standalone KiCad .kicad_pcb generator (50Ω microstrip, via stitching) |
| `tools/pcb_coupons/generate_openems_coupon.py` | OpenEMS EM solver wrapper (S-parameters, 100 MHz–10 GHz) |
| `hardware/docs/test_coupon_specification.md` | Full test plan (EM sim, TDR, PDN, thermal) |
| `hardware/docs/pcb_guidelines.md` | Original exploratory doc (unchanged, kept as reference) |

## Quick Start

### 1. Generate a KiCad coupon
```bash
cd /home/john/Projects/hardware/SPU
python3 tools/pcb_coupons/generate_kicad_coupon.py \
  --out /tmp/test_coupon.kicad_pcb --length 50 --trace-w 2.8 --via-stitch
# Open in KiCad:
kicad /tmp/test_coupon.kicad_pcb &
```

### 2. Simulate S-parameters (if openEMS installed)
```bash
python3 tools/pcb_coupons/generate_openems_coupon.py \
  --length 50 --trace-w 2.8 --freq-min 100e6 --freq-max 10e9 --via-stitch \
  --out /tmp/coupon_sim
# Outputs: /tmp/coupon_sim_s11.txt, _s21.txt, _z_in.txt, _sparameters.png
```

### 3. OpenEMS not installed?
The script auto-generates a reference MATLAB/Octave script:
```bash
cat /tmp/coupon_sim_reference.m
# Run in Octave with openEMS loaded
```

## Coupon Specification Summary

| Coupon Type | Power Plane | Routing | Key Measurement | Expected Result |
|:---|:---|:---|:---|:---|
| **Baseline** | Solid | Manhattan 90° | S11, Z_PDN reference | -15 dB @ 500 MHz (control) |
| **Sierpinski-1** | Fractal (88.9% area) | Manhattan | Resonance peak reduction | S11 peaks lower by ≥2 dB |
| **Sierpinski-2** | Fractal (79.0% area) | Manhattan | Aperiodic spectrum | Flatter PDN impedance, < 2 sharp peaks |
| **60-Degree** | Solid | 60° isotropic grid | Signal integrity / smooth bends | Z discontinuity < 1 Ω; S11 > -20 dB |
| **Combined** | Sierpinski-1 | 60° isotropic | Best-case scenario | TBD (hypothesis validation) |

## Measurement Instruments (Required for Phase 4)

| Measurement | Instrument | Sensitivity | Cost |
|:---|:---|:---|:---|
| **TDR** | Tektronix DSA70404C or equivalent | ±1% @ 50 Ω | $15k–30k (rental: $500–1k/day) |
| **VNA** | Rohde & Schwarz ZNA or equivalent | ±0.5 dB @ 1 GHz | $20k–50k (rental: $1k–2k/day) |
| **Thermal** | FLIR E60 or equivalent | ±2% absolute | $3k–5k (rental: $200–300/day) |

**Alternative (lower cost):** Use open-source instruments (HackRF + gnuradio for VNA simulation, oscilloscope + pulse generator for TDR emulation).

## Risk Summary

| Risk | Mitigation | Owner |
|:---|:---|:---|
| Sierpinski vias degrade thermal performance | Measure ΔT < 1.5× baseline under 1 A load | Test |
| 60° routing EDA support limited | Validate with Altium/KiCad 6+; manual polygon method as fallback | Design |
| Measurement uncertainty dominates | Use NIST-traceable calibration; compare deltas only | Test |
| Substrate ε_r variance | Request material cert; characterize test batch with VNA | Fab |

## Next Decision Point

**After Phase 4B (TDR measurement):**
- ✅ **Adopt:** If Sierpinski-2 S11 ≥ 2 dB better AND thermal ΔT acceptable → include in Tang 25K southbridge layout
- ❌ **Shelve:** If no measurable benefit or thermal issues → keep as future exploration reference; revert to solid plane + Manhattan routing

---

**Validation pathway:** Simulation → Fabrication → Measurement → Go/No-Go decision

For detailed procedures, see `hardware/docs/test_coupon_specification.md`.
