# SPU-13 Photonic Three-Model Investigation: Status Report

**Date:** 2025-01-20  
**Phase:** Model A & B Complete; Model C Requires Architecture Refinement

---

## Executive Summary

- ✅ **Model A (Exact SPU)**: Fully functional. Validates SurdFixed64 arithmetic.
- ✅ **Model B (Ideal Optical)**: 100% equivalence with Model A achieved after fixing:
  - Dual-rail encoding to preserve sign information
  - Sigma_max normalization compensation in BQE
  - Signed amplitude extraction from complex fields
- 🔧 **Model C (Noisy Optical)**: Framework complete, but noise model requires review.

---

## Model A: Exact SPU-13 Oracle

**Status**: ✅ PASS (6/6 known vectors verified)

The digital golden model computes SurdFixed64 multiplication correctly:

```
(a + b√3) × (c + d√3) = (ac + 3bd) + (ad + bc)√3
```

All verification test vectors pass without error.

---

## Model B: Ideal Optical (Noiseless)

**Status**: ✅ PASS (100/100 random vectors verified)

### Architecture

1. **WDM Dual-Rail Encoding** (Wavelength Division Multiplexing):
   - λ_a carries coefficient a in dual-polarity: E_a = s·(a⁺ - a⁻)
   - λ_b carries coefficient b in dual-polarity: E_b = s·(b⁺ - b⁻)
   - Scale factor s = 0.1

2. **Transfer Matrix** (Passive optical):
   ```
   M(c,d) = (1/σ_max) · [c    3d]
                         [d    c ]
   ```
   where σ_max = max(|c| + 3|d|, |d| + |c|, 1) ensures energy conservation.

3. **Complex Field Propagation**:
   - Input complex fields E_a, E_b
   - Matrix multiply: E_out = M · E_in
   - Preserve signed amplitude using sign(Re(E)) · |E|

4. **Dual-Rail Photodetection**:
   - Measure positive and negative rails separately
   - P_pos = |E_pos|², P_neg = |E_neg|²

5. **BQE Quantization** with σ_max Compensation:
   ```
   coeff = σ_max · round(√(P_pos)/s - √(P_neg)/s)
   ```

### Key Fix: Sigma_max Normalization

The transfer matrix is normalized by σ_max to ensure passivity (energy conservation). This scaling reduces output power by factor σ_max². The BQE must undo this:

```python
# CORRECT:
a_recovered = σ_max · (√(P_pos)/s - √(P_neg)/s)

# WRONG (pre-fix):
a_recovered = √(P_pos)/s - √(P_neg)/s  # Missing σ_max multiplication
```

Without this compensation, Model B produced results 0.814x–0.001x too small, depending on σ_max.

### Verification Results

100/100 random test cases match Model A exactly:
- Operand range: [-100, 100]
- No noise, perfect precision
- All 16-bit signed magnitudes preserved

---

## Model C: Noisy Optical

**Status**: 🔧 REQUIRES REFINEMENT

### Current Issue

Model C reports 0/500 recoveries even at minimal noise levels (σ_φ = 0.5°). However:

1. With **zero noise** (σ_φ = 0, σ_amp = 0, loss = 0), Model C matches Model A perfectly ✓
2. With **tiny noise** (σ_φ = 0.5°), deterministic random-seeded runs show ~18% amplitude error:
   - Golden result: (-25146, 12375)
   - Noisy result: (-20460, 10091)
   - Error: 18.6% absolute

### Root Cause Analysis

The phase jitter model adds random phase rotations to the optical field:

```python
phi_a += GaussianNoise.normal(0, sigma_phi)
phi_b += GaussianNoise.normal(0, sigma_phi)
```

This affects the complex field representation:
```
E = |E| · (cos(φ) + i·sin(φ))
```

The signed amplitude extraction uses sign(Re(E)) · |E|, which is **sensitive to phase changes**:
- When φ = 0: Re(E) = |E| (positive)
- When φ = π/2: Re(E) = 0 (ambiguous)
- When φ = π: Re(E) = -|E| (negative)

**Phase jitter of even 0.5° can cause sign-flip or magnitude errors in the reconstructed amplitude**.

### Test Observations

For test case (63, -72) × (-94, 89):
- Ideal optical: (-25146, 12375) ✓
- With 0.5° jitter: (-20460, 10091)  ← 18.6% error
- Random seed 42 produces Gaussian multipliers that compound errors

---

## Recommended Actions

### Immediate (This Session)

1. **Clarify Test Objectives**:
   - Is the 0% recovery rate a test artifact (seeding issue) or a real problem?
   - What recovery rate do we expect at 0.5° phase jitter?

2. **Refine Noise Model**:
   Options:
   - A) Use phase errors that preserve sign (e.g., small perturbations only)
   - B) Switch to amplitude-domain noise (avoid phase representation)
   - C) Model phase errors as wavelength drift (more physical)

3. **Test with Seeded Reproducibility**:
   - Reset random seed PER TRIAL, not per noise level
   - Ensure noise is statistically independent across trials
   - Report statistics: mean error, std dev, quartiles (not just "0 passes")

### Phase 2 (After Characterization)

1. **Physical Noise Model**:
   - Temperature fluctuations → path-length drift → phase drift
   - Coupling efficiency variation → amplitude noise
   - Detector shot noise → measurement precision limit

2. **Scattering Matrix Robustness**:
   - Which operations (SMUL, SROT, GSTEP) are most noise-sensitive?
   - Is passive-only realization (σ_max normalization) sufficient?
   - Do we need auxiliary modes or active gain?

3. **BQE Optimization**:
   - Should we measure not just power, but phase as well?
   - Can we use maximum-likelihood or other decoders instead of rounding?
   - What is the information-theoretic limit for recovery?

---

## Code Status

### Files Updated

- `software/tests/test_photonic_models_smul.py` (1600+ lines)
  - Model A: Exact SurdFixed64 oracle ✅
  - Model B: Ideal optical scattering ✅ (with σ_max fix)
  - Model C: Noisy optical framework ✓ (functional, requires noise model review)
  - Test harness: 100/100 Model B equivalence verified

### Known Issues

- **Model C Determinism**: Random seed behavior needs clarification
- **Phase Sensitivity**: Small phase changes cause large amplitude errors
- **Recovery Statistics**: Currently reports binary (0/N) instead of error distribution

---

## Next Steps for Continuation

1. **Run Model C with fresh random seeds per trial** and report error distributions
2. **Implement alternative noise models** (pure amplitude, or physical temperature/wavelength drift)
3. **Extend to other operations**: SADD, SROT.60, GSTEP, full ISA
4. **Prepare publication draft** with Table 2: recovery envelope vs. noise parameters

---

## References

- `photonics/photonics.md` (MVP and encoding specification)
- `spu_strategy/photonics_research_plan.md` (research hypothesis and Phase 1/2/3 roadmap)
- `spu_strategy/photonics_precision_findings.md` (σ_max normalization root cause)
