# Engineering Contract: Step-5 K-Operation Regeneration Experiment

**Date:** 2026-08-20
**Contract ID:** `contract_photonics_ksweep_2026-08-20.md`
**Status:** FROZEN SPEC (awaiting implementation authorization; DO NOT RUN until authorized)

**Roles:**
- Spec Author: John + Deep Code (this document; decisions Q1–Q3 locked by John)
- Halt-and-Flag Implementer: reviews before coding (RNG/stream alignment, saturation, vacuous scoring)
- Integration Auditor: reproducibility gates, hygiene, evidence freeze

---

## 1. Objective

Measure **regeneration depth** K_max: how many optical operations the SPU-13 SMUL
chain can compose in the *continuous optical domain* before an exact BQE
regeneration is required, under the frozen canonical physical-channel model.
This is the first experiment that tests the architecture (amortizing
regeneration) rather than a single optical operation.

**Two questions answered by one sweep:**
1. Can the continuous optical chain stay physically valid over K ops (no hidden
   digital correction between ops)?
2. Does the final regeneration recover the exact SurdFixed64 result of the
   *entire sequence* (oracle = digital K-fold product), and at what
   probability?

## 2. Definitions (locked)

- **Optical operation (op):** one normalized scattering transform
  `scattering_transform(state, c_i, d_i)` applied to the *continuous complex
  WDMState* (E_a, E_b complex fields). No rounding, quantization, or digital
  projection between ops. The state is carried forward as complex field
  amplitudes (normalized by each op's sigma_max_i).
- **K:** number of ops between BQE regenerations. K ∈ {1, 2, 4, 8, 16}.
- **Chain:** `state_0 = encode_wdm(a, b)`; `state_i = scatter(state_{i-1}, c_i, d_i)`
  with per-op physical noise (below); after K ops, one coherent detection +
  one calibrated BQE with **total scale** `Sigma = prod(sigma_max_i)`.
- **Oracle (independent):** exact integer K-fold surd product via Python
  big-ints, *no intermediate clamping*, clamped once to SurdFixed64
  [-32768, 32767] at the end. Built independently of the optical chain.
- **Output-magnitude band (confound control):** a trial is scored iff
  `1000 <= max(|a'_K|, |b'_K|) <= 30000` (the exact, oracle-computed final
  coefficients). Trials outside are rejected and counted
  (rejection fraction is a reported diagnostic). Rationale (locked Q1):
  isolates the K-effect from the magnitude-effect; the K=1 population
  reproduces the frozen baseline regime.
- **Regeneration policies (locked Q2), evaluated from the SAME trial state:**
  - **Unconditioned (A):** final BQE with `Sigma` only; `lo_phase = 0`.
  - **Conditioned (B):** gain trim `inphase /= cos(K * dphi)` before BQE,
    i.e. ε* = cos(K·δφ) − 1 (compensation law from frozen result #3).
    Valid only while `cos(K·δφ) > 0`; holds for all K,ΔT here
    (K·δφ ≤ 0.388 rad @ ΔT=5K, K=16).
- **Noise (locked Q2):** thermal-only, deterministic. Per op, both channels
  rotate by δφ = (2π/λ₀)·ΔL·dn_eff_dT·ΔT (canonical constants below);
  total rotation = K·δφ. No stochastic sigma_phi/sigma_amp/detector/loss.

## 3. Locked parameters

| parameter | value |
|---|---|
| physical base | canonical silicon: n_eff=2.45, dn_eff_dT=1.86e-4, ΔL_a=ΔL_b=6.4322e-6 m, λ₀=1550 nm |
| δφ / K per ΔT | δφ(2K)=9.70e-3 rad, δφ(5K)=2.42e-2 rad (per op) |
| ΔT (locked Q3) | {2.0, 5.0} K |
| K | {1, 2, 4, 8, 16} |
| operand ranges m_K (a,b and c_i,d_i uniform in [-m_K, m_K]) | K=1:100, K=2:25, K=4:9, K=8:4, K=16:2 |
| band | [1000, 30000] (exact final coeffs, oracle-computed) |
| draws per cell | 60,000 (valid ≥ 5,600 at K=16; expected valid fractions 95/86/50/22/9%) |
| seed | 13 (per-trial streams; K=1,m=100 reproduces frozen #1 operand stream) |
| cells | 2 ΔT × 5 K = 10 cells; both policies per cell (paired) |
| reproducibility | two runs, bit-identical (timestamps excluded) |

## 4. Procedure per cell (K, ΔT)

1. Spawn per-trial rng: `trial_rng(master(13), trial)`.
2. Draw a,b uniform [-m_K, m_K]; for i in 1..K draw (c_i, d_i) uniform [-m_K, m_K].
3. Exact oracle: big-int product → clamp once → golden (a'_K, b'_K).
4. Reject if golden out of band; count rejected.
5. Optical chain with per-op rotation by δφ (channel-a and channel-b), tracking
   Sigma = ∏σmax_i; record per-op lattice-deviation trajectory:
   `dev_i = |round(Sigma_i * inphase_i / s) - exact_i|` (exact_i = big-int
   intermediate, unclamped) and the first op index where dev_i ≥ 1
   ("first boundary crossing").
6. Final coherent detection; evaluate **both** policies on the same inphase:
   A: a_rec = bqe(inphase, Sigma, s); B: a_rec = bqe(inphase/cos(K·δφ), Sigma, s).
   Clamp to SurdFixed64.
7. Score: recovery iff (a_rec, b_rec) == golden (per policy).
8. Diagnostics subsample: retain full intermediate complex states for the first
   1,000 valid trials per cell (for post-hoc gradual/catastrophic/instability
   classification).

## 5. New model function (additive, Lithic ≤ 150 lines)

`ModelC_NoisyOptical.smul_chain_with_noise(a, b, ops, delta_phi_per_op,
  lo_track=False, return_debug=False)` — NEW function; **reuses** existing
primitives (`encode_wdm`, `scattering_transform`, `coherent_inphase`,
`bqe_quantize_coherent`); **does not modify** any existing function. Returns
(unconditioned_result, conditioned_result, debug) with debug carrying
Sigma, per-op deviation trajectory, first-crossing index, and (optionally)
intermediate states for the subsample. Tracked in `software/tests/`.

**Do NOT** implement by chaining `smul_with_noise` (that regenerates per op).
The chain must keep the continuous complex state and apply noise as field
rotations per op.

## 6. Metrics & outputs

- P_recover(K) for ΔT ∈ {2,5}, policy ∈ {A, B} — the primary artifact.
- 95% CI (normal approx) per cell/policy; MAE/RMSE/q95/q99 over errors
  (coordinate-wise).
- Rejection (out-of-band) fraction per K — the dynamic-range cost diagnostic.
- Diagnostics: distribution of first-crossing op index; mean/max lattice
  deviation per K; classification counts (gradual / catastrophic / per-op
  instability / stable) over the subsample.
- **Cost framing:** regeneration overhead ∝ 1/K reported alongside P_recover —
  "K=8 at P_target" is the architectural deliverable.
- Output: canonical JSON per sweep (full params per cell), frozen copy with
  sha256, README entry — same discipline as results #1–#4.

## 7. Falsification criteria (non-vacuous)

- The sweep must show **monotone (or at least non-increasing) P_recover(K)**
  under policy A; a flat 100% at all K would indicate the magnitude confound
  leaked (rejected design) — guard: K=1, ΔT=2K, policy A must reproduce the
  heavy-tail mechanism of frozen #1 (recovery strictly < 100% on the band).
- Policy B must show **strictly higher** P_recover than A at K ≥ 2
  (the compensation law must actually compensate) and the deviation
  trajectories must confirm error is dominated by the accumulated rotation,
  not per-op instability.
- Saturation must never be scored as success (band filter + oracle clamp both
  enforced; a trial is invalid if the exact result is out of band).

## 8. Verification gates (implementer/auditor)

1. Noiseless chain unit check: optical chain vs exact oracle, K ∈ {1,2,4,8,16},
   band-filtered, must match 100% (already validated in exploration).
2. Frozen #1–#4 reruns must stay bit-identical (chain function is additive;
   existing functions untouched).
3. Two full sweep runs → bit-identical (timestamps excluded).
4. Reproducibility discipline, freeze, sha256, README entry.

## 9. Explicit non-goals / traps avoided

- NO implicit per-op rounding/regeneration (chain is continuous).
- NO scoring of saturated trials as success (band filter + oracle clamp).
- NO fixed-alphabet degenerate control as the main curve ([-2,2] arm optional
  later, documented as weak test).
- NO stochastic amp/det in this first pass (deferred second pass).
- NO model tuning during the run; frozen baseline preserved.
