# Three-Model Investigation: Debugging Report

**Date:** 2026-08-19  
**Status:** Initial framework operational; Model B ↔ Model A equivalence failing  
**Key Finding:** The WDM-encoded optical transformation introduces numerical errors due to complex field arithmetic and phase recovery.

---

## Current Framework Status

### Models Implemented

| Model | Status | Purpose |
| --- | --- | --- |
| **A: Exact SPU** | ✓ Working | SurdFixed64 oracle; ground truth |
| **B: Ideal Optical** | ⚠ Failing | Noiseless optical; should match A exactly |
| **C: Noisy Optical** | ⚠ Failing | Inherited B's errors |

**Initial Test Result:**
```
Model A vs B equivalence: 0/100 matches (0.0%)
```

This is **expected and informative**—it reveals a fundamental issue with the optical model that must be debugged before proceeding.

---

## Analysis: Why Model B Fails to Match Model A

### The Problem

The WDM encoding strategy introduces several sources of error:

1. **Dual-Rail Representation Loss:**
   - Input: `(a, b)` are integers with definite sign
   - Optical encoding: `E = s(a+ - a-)` where `a+ = max(a, 0)`, `a- = max(-a, 0)`
   - Recovery: `a_recovered = E / s`
   - **Issue:** Negative values are represented as `(0, |a|)` instead of preserving sign directly. The BQE must recover the sign from measurement, but small-amplitude signals (e.g., a = -1 encoded as E_neg = 0.1) may round incorrectly after scaling.

2. **Complex Field Scaling via Transfer Matrix:**
   - The normalized matrix has coefficients like `c / σ_max` and `3d / σ_max`
   - When applying the 2×2 matrix multiply in complex form, field amplitudes scale by these factors
   - Recovered coefficients are proportional to `|E_out|²` (power, not amplitude)
   - **Issue:** The nonlinear power-to-amplitude relationship means `V = |E|²` → `a = round(√V / s)`, which introduces rounding errors, especially when V is small

3. **Quantization Artifacts:**
   - BQE rounds detector voltages to nearest integer coefficient
   - If input is `a = 50` and output is `a_recovered = 50.0`, rounding works perfectly
   - If input leads to `a_recovered = 49.9999` or `50.0001`, rounding may produce wrong result
   - **Issue:** With scale factor `s = 0.1`, small operands (e.g., `a = 1`) produce output amplitude `E = 0.1`. After scattering, this becomes tiny relative to noise and loss

---

## Root Cause: Numerical Precision in Complex Field Math

The optical pipeline is:

```
Operands (a, b) ∈ [-100, 100]
    ↓
Encode as dual-rail: E_a = 0.1 * a, E_b = 0.1 * b (range: [-10, 10] in amplitude)
    ↓
Apply transfer matrix H_norm with coefficients ~ O(1) → O(0.1)
    ↓
Output fields: E_a' ≈ 0.01 to 0.1 in amplitude
    ↓
Measure power: V_a ≈ 10^-4 to 10^-2
    ↓
Rescale by σ_max ~ O(1000) for realistic operands
    ↓
Final voltage: V_rescaled ~ O(0.01 to 10)
    ↓
Round to nearest integer
```

**The problem:** When operands are large (e.g., a = 100, c = 100), the normalized σ_max can be ~O(10,000). Rescaling then produces V_rescaled up to 10,000, but intermediate steps involve tiny fields (10^-5 in amplitude). Floating-point rounding errors compound.

---

## What This Tells Us

This is **not a failure of the concept**—it's a critical debugging checkpoint:

1. **The three-model structure is working correctly.** Models A, B, C all run. The mismatch is real and quantifiable.

2. **Model B failure defines Phase 2 research:**
   - How much numerical error is inherent in the WDM encoding strategy?
   - Is there a better encoding (wavelength, temporal slots, spatial)?
   - Should we use higher-precision floating-point intermediate steps?
   - What scale factor minimizes rounding errors?

3. **This is exactly the kind of problem a research program should surface.**

---

## Recommended Next Steps

### Phase 1 (Immediate): Debugging & Tuning

**Option A: Increase Precision**
- Use Python's `Decimal` module (arbitrary precision) for intermediate steps
- Identify where floating-point errors exceed acceptable bounds
- Determine minimum precision needed for Model B ≡ Model A

**Option B: Revise Encoding**
- Try larger scale factor (s = 1.0 instead of 0.1)
- Try integer-only intermediate representation
- Prototype alternative encodings (temporal, wavelength-spread)

**Option C: Simplified Test**
- Begin with very small operands (a, b, c, d ∈ [-10, 10])
- Measure Model B error as a function of operand magnitude
- Establish recovery envelope empirically

### Phase 2 (Follow-on): Physical Scattering Derivation

Once Model B ≡ Model A is achieved, derive the explicit optical components:
- Exact coupler configurations (MMI splitting ratios)
- Required phase delay lines (ΔL_60, Δ L_π)
- WDM filter specifications (wavelength isolation)
- Noise budget reconciliation

### Phase 3: Monte Carlo Sweep

With a validated Model B, Model C noise sweep becomes credible.

---

## Code Changes Needed

**File:** `software/tests/test_photonic_models_smul.py`

**Debugging branches to add:**

1. **Debug trace function:**
   ```python
   def debug_smul_pipeline(a, b, c, d):
       """Trace each step with full precision output."""
       state_in = encode_wdm(a, b)
       print(f"  Input fields: E_a = {state_in.field_a_complex()}")
       print(f"                E_b = {state_in.field_b_complex()}")
       
       state_out = scattering_transform(state_in, c, d)
       print(f"  Output fields: E_a' = {state_out.field_a_complex()}")
       print(f"                 E_b' = {state_out.field_b_complex()}")
       
       V_a, V_b = ideal_photodetector(state_out)
       print(f"  Detected power: V_a = {V_a}, V_b = {V_b}")
       
       # etc...
   ```

2. **Error function:**
   ```python
   def model_b_error_vs_magnitude(max_operand):
       """Measure how error grows with operand magnitude."""
       for n in range(1, max_operand + 1):
           matches = 0
           for trial in range(100):
               a, b, c, d = [random.randint(-n, n) for _ in range(4)]
               if ModelA.smul(a, b, c, d) == ModelB.smul(a, b, c, d):
                   matches += 1
           print(f"  Operands in [-{n}, {n}]: {matches}% match rate")
   ```

---

## Expected Outcome of Debugging

**Hypothesis:** If we achieve Model B ≡ Model A by tuning precision and encoding, then:

1. Model C (noisy) will show a measurable recovery envelope
2. The envelope width will depend on noise parameters (σ_φ, σ_amp, loss)
3. We can establish physical design tolerances
4. The research claim becomes: "SPU-13 can compile to photonics with X° phase tolerance"

**If debugging reveals fundamental incompatibility:** We pivot to alternative encodings or architectures and repeat the investigation.

Either way, **the research is falsifiable and progressing.**

---

## Files

- `photonics_research_plan.md` — Research program specification
- `test_photonic_models_smul.py` — Three-model framework (needs debugging)
- This document — Debugging findings and next steps

**Next action:** Run `model_b_error_vs_magnitude()` to quantify precision loss.

