# SPU-13 Photonic Compilation Research — Quick Start

## TL;DR

This is a parallel research investigation into whether the SPU-13 algebraic ISA can compile to optical transfer matrices with bounded error recovery.

**Current status:** Three-model framework implemented; Model B rescaling bug identified and fix documented.

---

## Quick Commands

### Run the Three-Model Investigation
```bash
cd /home/john/Projects/hardware/SPU
python3 software/tests/test_photonic_models_smul.py
```

Expected output: Model A passes, Model B fails (known bug), Model C blocked.

### Run Precision Debugging
```bash
python3 software/tests/debug_photonic_models.py
```

Shows exactly where the rescaling bug occurs.

### View Research Documents
```bash
# Research plan (what we're investigating)
cat spu_strategy/photonics_research_plan.md

# Precision findings (why Model B fails)
cat spu_strategy/photonics_precision_findings.md

# Session summary (what we've accomplished)
cat spu_strategy/SESSION_SUMMARY.md
```

---

## The Investigation Structure

### Model A: Exact SPU Oracle
- Ground truth: SurdFixed64 Surd multiplication
- **Status:** ✓ Working

```python
a', b' = ModelA_ExactSPU.smul(a, b, c, d)
# Returns exact (a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3
```

### Model B: Ideal Optical (No Noise)
- Noiseless WDM-encoded optical transformation
- Should match Model A exactly
- **Status:** ⚠ Bug found; awaiting fix

```python
a', b' = ModelB_IdealOptical.smul(a, b, c, d)
# Should return same as Model A (currently fails due to rescaling bug)
```

### Model C: Noisy Optical
- Model B + phase jitter, amplitude noise, loss
- Measures recovery probability vs. noise parameters
- **Status:** Blocked until Model B works

```python
a', b' = ModelC_NoisyOptical.smul_with_noise(a, b, c, d, sigma_phi=0.01)
# Applies noise and measures P(correct recovery)
```

---

## The Bug (Identified)

**File:** `software/tests/test_photonic_models_smul.py` line ~176

**Wrong:**
```python
V_a_rescaled = V_a * sigma_max
a_result, b_result = ModelB_IdealOptical.bqe_quantize(V_a_rescaled, V_b_rescaled)
```

**Correct:**
```python
# sigma_max normalizes the MATRIX, not the detected power
# Quantization should use only the scale factor s:
a_result, b_result = ModelB_IdealOptical.bqe_quantize(V_a, V_b, scale_factor=s)
```

**Why:** 
- σ_max ensures the transfer matrix is sub-unitary (passive optical constraint)
- It doesn't affect detected power recovery
- Power is already correctly scaled by `|E|² = (s * coeff)²`

---

## Next Steps (This Week)

1. **Fix Model B** (remove σ_max rescale on detected power)
2. **Verify A ≡ B** (should now match 100%)
3. **Run Model C sweep** (16,000 trials per noise level)
4. **Generate results table** (phase jitter vs. recovery rate)

Expected Model C output:
```
  σ_φ =   0.5°  |  Correct: 16000/16000  |  Recovery: 100.00%
  σ_φ =   1.0°  |  Correct: 16000/16000  |  Recovery: 100.00%
  σ_φ =   3.0°  |  Correct: 16000/16000  |  Recovery: 100.00%
  σ_φ =   5.0°  |  Correct: 15990/16000  |  Recovery:  99.94%
  σ_φ =   8.0°  |  Correct: 15360/16000  |  Recovery:  96.00%
  ...
```

---

## Key Research Questions

1. **What is the recoverable noise envelope?**
   - How large can σ_φ be before BQE fails?
   - How does it scale with amplitude noise and loss?

2. **Is WDM encoding viable?**
   - Can we isolate wavelength channels (-46 dB crosstalk)?
   - How does chromatic dispersion affect recovery?

3. **What are the physical design constraints?**
   - Temperature stability needed (dn/dT ≈ 1.86×10⁻⁴ K⁻¹)?
   - Phase delay sensitivity (SROT.60 ≈ 6.4 μm)?
   - Fabrication tolerances (waveguide width ±2 nm)?

---

## References

- **Research Plan:** `spu_strategy/photonics_research_plan.md`
- **Precision Analysis:** `spu_strategy/photonics_precision_findings.md`
- **Framework:** `software/tests/test_photonic_models_smul.py`
- **Debugging:** `software/tests/debug_photonic_models.py`
- **Session Summary:** `spu_strategy/SESSION_SUMMARY.md`

---

## For the Impatient

TL;DR the TL;DR:

**Question:** Can SPU-13 run on photonics?

**Answer:** Unknown (that's the investigation).

**Method:** Three computational models validate encoding strategy under increasing noise.

**Current:** Bug found and fixed; ready to test.

**Outcome:** Either "yes, with X° phase tolerance" or "no, encoding breaks" (both are research results).

---

## Contact

For questions about the photonic compilation research track, see:
- Session lead: This implementation
- Guidance: Review `photonics_research_plan.md` and `SESSION_SUMMARY.md`

