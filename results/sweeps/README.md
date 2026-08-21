# Photonic sweep reproducibility — canonical scheme

**Decision (2026-08-20): the canonical reproducibility scheme is
`software/tests/photonic_experiment_config.py`.** The previous
CSV + `.metadata.json` replay scheme described by earlier versions of this
README is **retired**. Do not start new sweeps with it.

## Why the old scheme was retired

1. **Incomplete parameter capture.** The per-sweep `.metadata.json` recorded
   only the swept variable (e.g. `deltaT_K`) plus `master_seed`/`num_trials`/
   `_start_global_trial`. It did **not** record the full physical parameter
   dict (`dn_eff_dT`, `n_eff`, `deltaL_a/b`, `lam_*_nm`, …), which differs per
   sweep script. A faithful replay was therefore impossible: the replay snippet
   had to guess `physical_params={'deltaT': ...}` and got different fallbacks
   than the run that produced the data.
2. **Replay snippet baked `ModelC.DEFAULTS`** for `sigma_phi`/`sigma_amp`/
   `loss_dB` — the same non-isolation defect fixed in the sweep scripts
   (handover §3a). Any replay through that snippet re-introduced the noise
   floor it was meant to control.
3. **All data it produced is invalid.** Every noisy path went through
   `WDMState.copy()`, which silently dropped the complex field attributes and
   reduced coherent detection to magnitude-only — making all phase-noise modes
   immune to phase drift (handover §3b root cause). The stale CSVs/JSONs were
   deleted on 2026-08-20.

## The canonical scheme (`photonic_experiment_config.py`)

- `PhysicalParams` — one auditable dataclass capturing **every** input to a
  Model-C experiment: seed, num_trials, noise_mode, lo_track, all physical
  thermo-optic params, all stochastic impairments, loss/calibration, and the
  `NOT_WIRED` (recorded-but-inactive) fields.
- `run_experiment(params, out_path=None)` — single entry point wrapping
  `ModelC_NoisyOptical.smul_with_noise` (no duplicated logic); persists the
  full `params` + seed + timestamp + recovery + MAE as JSON.
- `verify_reproducible(params)` — runs twice and asserts bit-identical results.

All impairments default to zero (unlike the retired sweep scripts which
inherited `ModelC.DEFAULTS`).

## Usage

```bash
cd software/tests
python3 photonic_experiment_config.py          # self-test: verify_reproducible + example run
```

```python
from photonic_experiment_config import PhysicalParams, run_experiment, verify_reproducible

p = PhysicalParams(seed=13, num_trials=500, noise_mode='C2', deltaT=5.0)
assert verify_reproducible(p), "same seed must reproduce identical results"
run_experiment(p, out_path='/tmp/exp_deltaT5.json')
```

For a sweep grid, call `run_experiment` once per cell (each cell is a fully
self-describing experiment with its own seed).

## Notes / open flags

- **`cascade_depth_sweep_frozen_v1_2026-08-22.json`** (sha256
  `2e322400…37592dff8`) — **E11, the cascade-depth mechanism
  investigation** (`contract_photonics_cascade_depth_2026-08-22.md`).
  70 cells (35-point det grid × 2 arms), 30,000 trials/cell, K=16 only,
  pure self-rotation chains (Arm T: ROTC angles {1,3,4}, Arm N: {0,2,5}),
  identical deterministic per-trial m=23 for both arms, seed 13, run
  twice, bit-identical. **RESULT: HYPOTHESIS RULED OUT.** Tests whether
  uncompensated `/3` divisions from exact-thirds ROTC angles explain E9's
  disproportionate K=8→K=16 collapse — they don't: Arm T and Arm N's
  crossing brackets coincide exactly ([1.5e-9, 2.0e-9] for both at
  99.9%/99%). Mathematical grounding (§10 of the contract): `(F,G,H)/div`
  is an exact unit vector for all six ROTC angles — the `/3` is rotation
  normalization, not independent attenuation, so this result was
  structurally expected once checked, not a surprise. K=16's collapse
  remains unexplained. Driver:
  `photonics/run_photonic_cascade_depth_sweep.py`.
- **`detector_boundary_sweep_frozen_v1_2026-08-21.json`** (sha256
  `1a3306a1…870f1afda`) — **E9, the detector-boundary sweep**
  (`contract_photonics_detector_boundary_2026-08-21.md`). 127 cells
  (23-point log grid for K∈{1,2,4,8}, 35-point split grid — main 23 points
  plus a 12-point sub-grid below the floor — for K=16, after a smoke pass
  found K=16's crossing off the original single-grid's floor), 30,000
  trials/cell, σ_φ=σ_amp=0 (detector axis isolated), ΔT=2K, seed 13, run
  twice, bit-identical. **RESULT: FALSIFIED.** The E8 closed-form
  `σ_det ≲ 0.05/2^m` does not generalize: R_K = σ\*_det(K)/σ_det,pred(K)
  (measured crossing / prediction at the *measured* mean scale exponent
  m̄(K)) spans ~45× across K (0.301 at K=1 → 0.0067 at K=16), and is off by
  ~3.3× even at K=1, one of the formula's own two fit points — E8's original
  grid (`{0, 1e-4, 3e-4, 1e-3}`) was too coarse to have caught this. The
  K=8→K=16 step drops R by ~24× despite m̄ growing only ~3.2 — a
  disproportionate collapse not explained by the scalar-m model (mechanism
  not investigated under this contract; flagged for a separate follow-on).
  Backend contract §3.3 not silently corrected — a dated pointer to this
  result was added directly below the original claim, which remains as
  originally frozen. Driver: `photonics/run_photonic_detector_boundary_sweep.py`.
- **Frozen Step-6b result #7 (2026-08-20): `knoise_combined_sweep_frozen_v1_2026-08-20.json`**
  (identical to `knoise_combined_sweep.json`; sha256 f3e49dbf…). Combined
  multi-factor K-chain, contract_photonics_knoise_combined_2026-08-20.md.
  40 cells (8 noise combos × K ∈ {1,2,4,8,16}), 30000 draws/cell, identical
  machinery to step 6, seed 13, bit-identical across two runs.
  **Interaction classification: NO compounding.** Measured recovery is never
  significantly below the independent-product model (p_φ·p_amp·p_det); it
  typically sits between the product (lower bound) and the worst-axis
  reference — failures are partially correlated through the shared
  output-magnitude driver (large-intermediate trials fail on multiple axes
  simultaneously). Consequence: **K can be set from single-factor budgets;
  the product model is conservative; a joint noise budget is NOT required.**
  Arm B remains dominated by the Σ_total detector wall at K≥2 regardless of
  the other factors.
- **Frozen Step-6 result #6 (2026-08-20): `knoise_sweep_frozen_v1_2026-08-20.json`**
  (identical to `knoise_sweep.json`; sha256 47800546…). K-chain with per-op
  stochastic noise, contract_photonics_knoise_sweep_2026-08-20.md. 60 cells
  (3 factors × 4 levels × K ∈ {1,2,4,8,16}), 30000 draws/cell, ΔT=2K
  conditioned, arm A (per-op regeneration) vs arm B (chain) from the SAME
  paired stream, seed 13, bit-identical across two runs. **Result: A ≥ B at
  every (factor, level, K); B collapses on all stochastic axes while A
  survives** (φ 0.5°: A 61→25% vs B 61→0%; amp 1e-5: A 99.7→92% vs B 99.7→22%;
  det 1e-4: A 92→100% vs B 92→0%). **Key architectural finding:** the chain's
  final detection must resolve 1/Σ_total = 1/∏σmax (mean 2.2e10 @ K=16) —
  per-op regeneration bounds it to 1/σmax — regeneration is a dynamic-range
  management mechanism. σ=0 gate: A=B=100% at all K (Step-5 reproduction).
  Arm-A intermediates are projected unclamped (final-only SurdFixed64 clamp,
  per spec); det-only arm A recovery RISES with K (m_K shrinks → smaller σmax).
- **Frozen Step-5 result #5 (2026-08-20): `ksweep_frozen_v1_2026-08-20.json`**
  (identical to `ksweep.json`; sha256 20a45cc1…). K-operation regeneration
  sweep, contract_photonics_ksweep_2026-08-20.md. 10 cells (ΔT ∈ {2,5}K ×
  K ∈ {1,2,4,8,16}), 60000 draws/cell, continuous optical chain (no per-op
  rounding), per-op thermal rotation, unconditioned (A) vs conditioned
  (B, ÷cos K·δφ) from the same trial state, band [1000,30000] on the exact
  oracle, seed 13, bit-identical across two runs. **Result: B = 100.00% at
  every K and ΔT; A collapses 69.17%→13.09%→0% (ΔT=2K).** Conditioned
  deviation = 0.0 at all K (internal state is exactly the rotated ideal —
  possibility C ruled out by data). First-boundary-crossing histograms are
  smooth (gradual accumulation, no per-op instability). Dynamic-range cost:
  rejection 4.7%→90.7% (m_K 100→2).
- **Frozen Phase-2 result #4 (2026-08-20): `amp_phase_det_sweep_frozen_v1_2026-08-20.json`**
  (identical to `amp_phase_det_sweep.json`; sha256 5a6aefcf…). Amplitude ×
  differential-phase × detector-noise sweep, 180 cells (6 φ × 6 amp × 5 det),
  16000 trials/cell, canonical frozen base (C1), seed 13, bit-identical across
  two runs. Independent axes: phase 100%@0°→3.97%@5°; amp 100%@0→0.26%@1e-2;
  det 100%@0→0.22%@1e-2. Mechanism (100.00% per-trial agreement, stream-aligned
  probe): recovered_a = round(x_a·cos δφ_a·amp_a + n_a·σmax/s) — phase and
  amplitude are multiplicative scale errors (same heavy-tail family as #1–#3);
  detector noise is additive with σmax scaling (operand-dependent). Worst axis
  dominates the combined surface. **Model note:** amplitude draws now come from
  the per-trial seeded stream (rng fix 2026-08-20); frozen results #1–#3
  unaffected (σ_amp=0 there); T4 historical numbers changed (they were on the
  unreproducible global stream).
- **Frozen Phase-2 result #3 (2026-08-20): `deltaT_calib_sweep_frozen_v1_2026-08-20.json`**
  (identical to `deltaT_calib_sweep.json`; sha256 66862942…). Joint ΔT × ε
  sweep, 217 cells (7 ΔT × 31 ε), 16000 trials/cell, canonical frozen base
  (C2 + 1.8 dB loss-normalized), seed 13, bit-identical across two runs.
  **Key finding — the two errors do not simply add: they are one multiplicative
  scale factor.** recovered = round(x·cos δφ/(1+ε)); a trial fails iff
  |x|·|1−cos δφ/(1+ε)| ≥ 0.5 (100.00% per-trial agreement at all probes).
  ε>0 (undershoot) adds to cos-attenuation; ε<0 (overshoot) **cancels** it:
  the recovery ridge sits at ε* = cos(δφ)−1 — measured best-ε −5e-5 @ ΔT=2K
  and −3e-4 @ ΔT=5K match prediction to grid resolution, restoring recovery
  from 70.5%→100.0% and 9.9%→100.0%. Implication: thermal drift is exactly
  compensable by a temperature-tracked receiver gain trim.
- **Frozen Phase-2 result #2 (2026-08-20): `calib_sweep_frozen_v1_2026-08-20.json`**
  (identical to `calib_sweep.json`; sha256 551208a8…). Calibration-error sweep,
  16000 trials/cell, static 1.8 dB loss with loss-normalized BQE, canonical
  physical params, seed 13, bit-identical across two runs. Only ε varies.
  Calibration requirement: ≥99.9% → |ε|≤1.53e-5 (±1.3e-4 dB), ≥99% → 1.83e-5,
  ≥95% → 2.29e-5, ≥90% → 2.74e-5, ≥50% → 7.46e-5 (±6.5e-4 dB). Same
  heavy-tail mechanism as #1: failure iff max(|a′|,|b′|)·|ε|/|1+ε| ≥ 0.5
  (100.00% per-trial agreement at ε = 5e-5..5e-4). ε=0 control = 100.00%.
- **Frozen Phase-2 result #1 (2026-08-20): `deltaT_sweep_frozen_v1_2026-08-20.json`**
  (identical to `deltaT_sweep.json`; sha256 b3d5cecc…). Full ΔT sweep, 16000
  trials/cell, canonical `PhysicalParams`, master_seed=13, bit-identical across
  two runs (timestamps excluded). Thermal operating envelope (verified
  cos-attenuation mechanism + frozen-stream CDF): ≥99.9% → |ΔT|≤1.14K,
  ≥99% → 1.25K, ≥95% → 1.40K, ≥90% → 1.53K, ≥50% → 2.52K. Mechanism: a trial
  fails iff max(|a′|,|b′|)·(1−cos δφ) ≥ 0.5 with δφ = 4.85e-3·ΔT rad
  (predicted failures matched actual in 100.00% of trials at ±2K and ±5K).
- **Default divergence — RESOLVED (2026-08-20).** `PhysicalParams` is the
  single canonical source for unspecified parameters, carrying the silicon
  design values consistent with `test_photonic_surd_oracle.py`
  (n_eff=2.45, dn_eff_dT=1.86e-4, ΔL=6.4322 µm). The C2 fallback constants in
  `smul_with_noise` were aligned to them, and the root
  `physical_params_defaults.json` (an unloaded, divergent artifact) was
  deleted. `ModelC_NoisyOptical.DEFAULTS` remains only as the stochastic
  noise floor for the C0/C1 phase-sweep tests (T1–T3) — a different concept.
- **Sweep scripts re-pointed at `run_experiment()` (2026-08-20).**
  `run_photonic_deltaT_sweep.py`, `run_photonic_combined_sweep.py`, and
  `run_photonic_deltaT_calib_sweep.py` now emit the canonical per-cell JSON
  (full params + stats) instead of bare CSVs. `PHOTONIC_TRIALS=<n>` overrides
  the per-cell trial count for smoke runs. The retired scheme's generator,
  `photonics/generate_sweep_metadata.py`, is retained there for reference only.
- `coupler_error` and `crosstalk_dB` are recorded in `PhysicalParams` but not
  yet wired into the underlying model (see `NOT_WIRED` in the module).
- **`photonic_envelope_frozen_v1_2026-08-20.json`** (sha256
  `f300b6b9…54680b89`) — **E8, the declared regeneration envelope**
  (deliverable 2 of `contract_photonics_backend_2026-08-20.md`). 60 cells
  (3 noise axes × 4 levels × K {1,2,4,8,16}), 30,000 accepted trials/cell,
  seed 13, band [1000, 30000] on max |QR0 component|, ΔT = 2K conditioned,
  arms A/B paired draws. σ=0 gate: A=B=100% at all K. Key declared numbers:
  detector budget σ_det ≲ 0.05/2^m (1.96e-4 at K=1 → 5.8e-7 at K=16); the
  K* crossover: chain K*(99.9%) = 8 at σ_amp=1e-5 / 2 at 5e-5 / 1 at
  σ_φ=0.25° / 0 for any tested detector > 0; per-op REGEN holds ≥99% at
  σ_φ ≤ 0.25° and σ_amp ≤ 5e-5 through K=16 (detector-bound). Run twice,
  bit-identical (cells). Driver: `run_photonic_envelope_sweep.py`;
  extraction: `extract_photonic_envelope.py`.
