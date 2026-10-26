# SPU-13 Photonic Compilation Research Plan

## Executive Summary

This is a parallel research investigation into whether the **SPU-13 algebraic ISA can be compiled into physically realizable optical transfer matrices** such that a Boundary Quantization Engine (BQE) recovers exact digital state from noisy photonic outputs with measurable, bounded error probability.

**This is not a hardware specification.** It is a falsifiable investigation proceeding through three computational models: exact digital, ideal optical, and noise-corrupted optical. Success means identifying the recoverable noise envelope; failure means discovering where the compilation strategy breaks down.

---

## Central Hypothesis

> Discrete algebraic representations (Q(√3) and Quadray coordinates) may provide natural error-tolerance thresholds that allow photonic physical transformations to serve as computational primitives without requiring continuous numerical precision at the architectural level.

Formally:

$$P_{\text{correct}} = P\left( Q(F_{\text{optical}}(\mathbf{x})) = F_{\text{SPU}}(\mathbf{x}) \right)$$

where:
- $F_{\text{SPU}}$ = exact digital operation (SurdFixed64)
- $F_{\text{optical}}$ = physical photonic transformation
- $Q$ = Boundary Quantization Engine (lattice snapping)
- The research question: **For what noise envelope is $P_{\text{correct}} \ge 1 - \epsilon$?**

---

## Wavelength-Encoded Representation

Rather than spatial dual-rail (two waveguides), we investigate **wavelength-encoded coefficients**:

$$a + b\sqrt{3} \rightarrow \{\lambda_a, \lambda_b\}$$

where:
- Channel λ_a carries the rational component (a)
- Channel λ_b carries the algebraic component (b)
- Both channels use dual-polarity encoding: $E = s(x^+ - x^-)$
- Wavelength-division multiplexing (WDM) keeps signals co-routed through the same optical path

**Advantages over spatial dual-rail:**
- Single waveguide path reduces crosstalk between (a) and (b)
- WDM is standard silicon photonics practice
- Wavelength selectivity provides natural filtering
- Temperature/fabrication drift affects both channels similarly
- Scales naturally to Quadray 4-channel operation

**Disadvantages:**
- Requires tunable or broadband source
- Wavelength filters must be sufficiently sharp
- Chromatic dispersion becomes relevant
- Requires phase coherence across wavelength channels

---

## Three-Model Investigation

### Model A: Exact SPU-13 (Digital Oracle)

**Purpose:** Establish the golden-truth target.

**Inputs:** 
- Operand vectors $(a, b, c, d)$ with $a, b, c, d \in [-32768, 32767]$ (SurdFixed64)
- Operation: `SMUL` — Surd multiplication

**Computation:**
$$\text{result} = (a + b\sqrt{3})(c + d\sqrt{3}) = (ac + 3bd) + (ad + bc)\sqrt{3}$$

**Output:**
- Exact $(a', b')$ result in $\mathbb{Z}[\sqrt{3}]$
- No rounding, no approximation
- Overflow handling per SPU-13 spec

**Implementation:** Direct integer arithmetic in Python (sympy or custom).

---

### Model B: Ideal Optical (Noiseless Scattering)

**Purpose:** Verify that the ideal photonic transformation, when perfectly realized, recovers the exact digital result.

**Architecture:**

```
Input WDM state
    ↓
┌─────────────────────────────────────┐
│  Complex Field Scattering Network   │
│  - Wavelength channels λ_a, λ_b     │
│  - Coherent combiners (MMI/coupler) │
│  - Fixed phase delays (Δ L_60, etc) │
│  - Dual-rail encoding per channel   │
└─────────────────────────────────────┘
    ↓
Calibrated Transfer Matrix H_ideal
    ↓
Dual-rail detector pairs
    ↓
Differential photocurrent (I_+ - I_-)
    ↓
Ideal ADC (no quantization error)
    ↓
BQE: Round to nearest SurdFixed64 lattice point
    ↓
Output: (a', b')
```

**Key Constraint:** The matrix $\mathbf{M}_{\text{SMUL}} = \begin{bmatrix} c & 3d \\ d & c \end{bmatrix}$ is not unitary. Therefore, the optical realization must include:

- **Normalization:** Scaling by $\sigma_{\max} = \max(|c| + 3|d|, |d| + |c|, 1)$
- **Decomposition:** Express normalized matrix as cascade of passive optical components
- **Field-vs-power distinction:** Derived from complex scattering matrices, NOT power ratios

**Computation:**

1. Encode $(a, b)$ as dual-rail optical state on wavelengths ($\lambda_a$, $\lambda_b$):
   $$\mathbf{E}_{\text{in}} = s \begin{bmatrix} a^+ - a^- \\ b^+ - b^- \end{bmatrix}$$

2. Apply ideal transfer matrix (normalized):
   $$\mathbf{E}_{\text{out}} = \frac{1}{\sigma_{\max}} \begin{bmatrix} c & 3d \\ d & c \end{bmatrix} \mathbf{E}_{\text{in}}$$

3. Measure power and convert to voltage (no detector noise):
   $$V_i \propto |E_i|^2 = \text{ideal photodetector output}$$

4. Rescale by $\sigma_{\max}$ to recover logical amplitude

5. BQE: Quantize to nearest SurdFixed64 point

**Success:** Model B output exactly matches Model A output.

---

### Model C: Noisy Optical (Physical Realism)

**Purpose:** Determine the noise envelope under which BQE successfully recovers the exact digital state.

**Noise Sources:**

| Mechanism | Model | Magnitude / Std Dev |
| --- | --- | --- |
| **Phase jitter (thermal/fab)** | $\delta\phi \sim \mathcal{N}(0, \sigma_\phi^2)$ | $\sigma_\phi \in [0.5°, 5.0°]$ |
| **Amplitude fluctuation (fab tolerance)** | $\delta A \sim \mathcal{N}(1, \sigma_A^2)$ | $\sigma_A \in [0.25\%, 2.0\%]$ |
| **Optical insertion loss** | Fixed attenuation | $A_{\text{loss}} \approx 1.8$ dB |
| **Wavelength crosstalk (channel isolation)** | $X_{\text{xtalk}} = E_{\lambda_b} \rightarrow \lambda_a$ | $X_{\text{xtalk}} \approx -46$ dB |
| **Chromatic dispersion** | $\delta\phi(\lambda) = \frac{2\pi}{\lambda^2} \beta_2 L$ | Sweep over 1–10 nm BW |
| **Detector shot noise** | $\sigma_{\text{shot}} = \sqrt{2qI_{\text{sig}}B}$ | $I_{\text{sig}} \sim 1$ mA, $B = 1$ GHz |
| **Detector thermal noise** | $\sigma_{\text{th}} = \sqrt{4k_B T B / R}$ | $T = 300$ K, $R = 50$ Ω |

**Computation:**

```
Input operands (a, b, c, d)
    ↓
Encode as WDM dual-rail state
    ↓
Apply ideal scattering matrix
    ↓
Add noise:
    • Phase jitter on each rail
    • Amplitude variation
    • Wavelength crosstalk
    • Loss (multiplicative)
    • Shot noise (additive)
    ↓
Photodetector (intensity squared)
    ↓
Detector noise + ADC quantization (12-bit, ±10V)
    ↓
BQE: Round to nearest SurdFixed64
    ↓
Compare with Model A output
    ↓
Record: correct / incorrect
```

**Sweep Parameters:**

Run 16,000 independent trials for each noise configuration:

$$\sigma_\phi \in \{0.5°, 1.0°, 2.0°, 3.0°, 5.0°, 8.0°, 12.0°\}$$

$$\sigma_A \in \{0.25\%, 0.5\%, 1.0\%, 1.5\%, 2.0\%\}$$

$$A_{\text{loss}} = 1.8 \text{ dB (fixed)}$$

$$X_{\text{xtalk}} = -46 \text{ dB (fixed)}$$

Input vectors: uniform random from $[-32768, 32767]^4$.

**Output:** Recovery probability table with 95% confidence intervals.

---

## Critical Phase-2 Questions (Not Yet Resolved)

### Q1: Scattering Matrix Decomposition

The matrix $\mathbf{M}_{\text{SMUL}}$ is not unitary. How should it be realized optically?

**Candidates:**
1. Normalization (divide by $\sigma_{\max}$; BQE rescales)
2. Auxiliary modes (embed into larger unitary matrix)
3. Attenuation (absorb excess energy in dummy outputs)
4. Asymmetric encoding (encode coefficients differently)

**Investigation:** Derive explicit MMI/coupler cascade for each approach. Model C will measure which approach has the best recovery envelope.

### Q2: Wavelength Channel Isolation

WDM crosstalk at -46 dB is aggressive. Is this realistic?

**Investigation:** 
- Spec actual demux/mux components (OSA, Yenista, etc.)
- Calculate crosstalk from asymmetric directionality
- Does chromatic dispersion over 1 nm bandwidth matter?

### Q3: Phase Tolerance

The SROT.60 delay line requires $\Delta L_{60} \approx 6.4$ μm for π/3 phase shift. How sensitive is this to:
- Fabrication (waveguide width ±2 nm)?
- Temperature (dn/dT ≈ 1.86×10⁻⁴ K⁻¹)?
- Wavelength (chromatic dispersion)?

**Investigation:** Full tolerance budget. May constrain thermal stability requirements.

### Q4: BQE Decision Boundaries

Lattice snapping works if noise keeps signals in "distinct decision regions." What is the actual decision margin?

**Investigation:** Model C will empirically measure the noise envelope. If recovery fails sharply at σ_φ ≈ 5°, that's a sign the decision regions are too narrow.

---

## Success Criteria

### Phase 1 (Current): Software Model Validation

- [ ] Model A: Exact SPU oracle implemented and verified against known test vectors
- [ ] Model B: Ideal optical model built; verify it matches Model A exactly
- [ ] Model C: Noise model implemented; sweep noise parameters and measure P(correct)
- [ ] Generate results table: σ_φ vs P(recovery) with 95% CI

**Success:** Model B ≡ Model A. Model C shows a clear recoverable regime (e.g., σ_φ ≤ 3° → 100% recovery).

**Failure mode:** Model C shows immediate collapse (e.g., σ_φ > 0.5° → <50% recovery) → optical encoding strategy needs fundamental revision.

### Phase 2 (Follow-on): Physical Derivation

- [ ] Derive explicit scattering-matrix decomposition for SMUL
- [ ] Calculate waveguide length tolerance for SROT.60
- [ ] Specify actual WDM component requirements (isolation, bandwidth)
- [ ] Define full noise budget (phase, amplitude, loss, crosstalk, dispersion)

### Phase 3 (Follow-on): Photonic Compiler

- [ ] Automatic compilation from SPU-13 ISA to scattering matrices
- [ ] Verify all operations (SADD, SMUL, SROT, GSTEP, etc.)
- [ ] Extend Model C to multi-instruction sequences

### Phase 4 (Hardware – CONDITIONAL)

Only if Phase 1 and 2 show a robust recoverable regime:

- [ ] 3D FDTD simulation of candidate layout
- [ ] PDK verification (imec, AIM Photonics, or AMF)
- [ ] Design minimal test chip (fixed 2×2 transform + BQE)
- [ ] MPW tape-out

---

## Falsifiability & Publication

**Claim:** "SPU-13 algebraic operations can be compiled to photonic primitives and recovered with bounded error."

**Test:** Measure P(correct) as function of noise. If P(correct) ≥ 1−ε for a non-trivial noise envelope, hypothesis is **supported**. If P(correct) → 0 for any realistic noise level, hypothesis is **falsified**.

**Publication venue:** This is suitable for:
- Journal: IEEE JETCAI, Optics Express (rigorous noise analysis + measurements)
- Conference: OFC, IPCO (discrete photonics track)
- Preprint: arXiv (while under review)

**Key advantage:** The three-model structure makes it **reproducible and independently verifiable**. Anyone can run Models A, B, C with their own noise assumptions.

---

## Workstream Organization

```
software/tests/
  ├── test_surd_photonic_oracle.py           [Model A]
  ├── test_photonic_ideal_wdm.py             [Model B]
  ├── test_photonic_noisy_recovery.py        [Model C]
  ├── test_smul_wdm_encoding.py              [encoding validation]
  └── test_scattering_decomposition.py       [Phase 2 prep]

software/lib/
  ├── photonic_compiler.py                   [SPU → H_optical]
  ├── wdm_encoder.py                         [wavelength encoding]
  └── bqe_decoder.py                         [lattice snapping]

photonics/
  ├── photonics_research_plan.md             [this file]
  ├── photonics_models.md                    [detailed math]
  └── photonics_results.md                   [results table + interpretation]
```

---

## Expected Timeline

**Parallel to FPGA/hardware development:**

- **Week 1:** Model A (oracle) + Model B (ideal) complete. Verify equivalence.
- **Week 2:** Model C framework; implement noise sweep. Collect initial results table.
- **Week 3:** Analyze failure modes. Iterate on encoding if needed.
- **Week 4:** Document Phase-2 questions. Submit research plan for feedback.

All work is **CPU-only** (no hardware dependency).

---

## References

- Jordan, H. F., et al. (1994). SPOC: Stored-program optical computer.
- Recent all-optical CPU work (2024/25): Akhetonics, reconfigurable RFU architecture.
- SPU-13 ISA specification: `knowledge/isa_reference.md`
- SurdFixed64 golden model: `software/lib/surd.py`
- Quadray basis: `knowledge/SPU_LEXICON.md`

