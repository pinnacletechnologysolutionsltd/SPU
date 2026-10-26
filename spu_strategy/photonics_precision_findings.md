# Precision Investigation Findings

**Date:** 2026-08-19  
**Status:** Root cause identified; fix in progress

## The Problem (Quantified)

From `debug_photonic_models.py`:

```
Matrix Scaling & Renormalization Results:
  (1, 1) × (1, 1)
    Expected: (4, 2)
    Recovered: (4, 1)  ← WRONG
  
  (100, 100) × (100, 100)
    Expected: (32767, 20000)  [saturated]
    Recovered: (4000000, 1000000)  ← WAY OFF
```

## Root Cause

The rescaling step in ModelB is **mathematically incorrect**:

```python
# WRONG:
V_a_rescaled = V_a * sigma_max
a_recovered = int(round(V_a_rescaled / scale_factor))
```

This tries to rescale power by σ_max, but:

1. **Power scales as (field)²**, not linearly
2. **σ_max normalizes the matrix elements**, not the power
3. **The relationship should be:**
   - Output field: `E_out = (normalized_matrix @ input_field)`
   - Output power: `P_out = |E_out|²`
   - Recovered coefficient: `c = round(P_out / (scale_factor²))`

The rescaling by σ_max makes no sense unless σ_max itself is absorbed into the field scaling during the matrix multiply.

## Correct Formulation

The normalized scattering matrix is:

$$H_{\text{norm}} = \frac{1}{\sigma_{\max}} \begin{bmatrix} c & 3d \\ d & c \end{bmatrix}$$

The output field is:

$$\mathbf{E}_{\text{out}} = H_{\text{norm}} \cdot \mathbf{E}_{\text{in}}$$

The detected power is:

$$\mathbf{P}_{\text{out}} = |\mathbf{E}_{\text{out}}|^2$$

Recovered coefficients are:

$$\text{coeff} = \text{round}\left( \frac{P_{\text{out}}}{s^2} \right)$$

**There is NO rescale by σ_max on the output.** The normalization affects the matrix operation itself.

## Fix

Replace the photonic model architecture:

**Before (WRONG):**
```
Operands → Encode → Apply H_norm → Measure Power → Rescale by σ_max → Quantize
```

**After (CORRECT):**
```
Operands → Encode → Apply H_norm → Measure Power → Quantize (using s² denominator)
```

The point of σ_max is to make the matrix norm-bounded (sub-unitary) so passive optical realization is possible. It doesn't affect the recovery stage.

## Revised Algorithm

```python
def smul_ideal(a, b, c, d):
    # 1. Encode
    s = 0.1  # scale factor
    E_a_in = s * a
    E_b_in = s * b
    
    # 2. Compute normalized matrix
    sigma_max = max(abs(c) + 3*abs(d), abs(d) + abs(c), 1)
    M = [
        [c / sigma_max, 3*d / sigma_max],
        [d / sigma_max, c / sigma_max]
    ]
    
    # 3. Apply scattering (complex fields; simplified to real for no phase)
    E_a_out = M[0][0] * E_a_in + M[0][1] * E_b_in
    E_b_out = M[1][0] * E_a_in + M[1][1] * E_b_in
    
    # 4. Measure power
    P_a = E_a_out ** 2
    P_b = E_b_out ** 2
    
    # 5. Quantize (no rescale)
    a_recovered = int(round(P_a / (s ** 2)))
    b_recovered = int(round(P_b / (s ** 2)))
    
    return a_recovered, b_recovered
```

## Impact

Once fixed, Model B should match Model A exactly (noiseless optical recovery is perfect).

Then Model C can proceed with noise injection.

## Status

- [x] Problem identified
- [x] Root cause found
- [ ] Fix implemented in test_photonic_models_smul.py
- [ ] Retest to verify A ≡ B
- [ ] Proceed with Model C sweep

