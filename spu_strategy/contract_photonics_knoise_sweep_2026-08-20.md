# Engineering Contract: Step-6 K-Chain with Per-Op Stochastic Noise
# (Regeneration-Frequency Phase Diagram)

**Date:** 2026-08-20
**Contract ID:** `contract_photonics_knoise_sweep_2026-08-20.md`
**Status:** FROZEN SPEC (awaiting implementation authorization; DO NOT RUN until authorized)

**Roles:**
- Spec Author: John + Deep Code (Q1 single-factor, Q2 dT=2K conditioned locked by John)
- Halt-and-Flag Implementer: pre-review (stream alignment, Σ_total precision, paired draws)
- Integration Auditor: reproducibility gates, hygiene, evidence freeze

---

## 1. Objective

Build on Step 5 (common-mode thermal drift imposes no regeneration boundary
through K=16) by introducing the **non-common-mode** mechanisms from Step 4
per operation. Measure P_recover(K, noise) under two regeneration frequencies:

- **A — regenerate every operation:** per-op `scatter + noise → detect →
  conditioned BQE → exact integer → re-encode`. Cost K regenerations.
- **B — regenerate every K operations:** the Step-5 continuous chain with
  per-op noise → one final conditioned BQE. Cost 1 regeneration.

Deliverable: an architecture-level phase diagram
`noise budget × optical depth × regeneration frequency`, locating the
crossover K* where per-op regeneration becomes necessary, per mechanism.

## 2. Definitions (locked)

- **Optical op / chain:** as Step 5 (continuous complex state, no intermediate
  rounding). Per-op noise is applied to the continuous field:
  - **Differential phase:** channel-independent rotation `N(0, sigma_phi)`
    per op, accumulated as a random walk per channel.
  - **Amplitude:** multiplicative `N(1, sigma_amp)` per channel per op.
  - **Detector noise:** additive `N(0, detector_noise)` on each in-phase
    measurement at every detection point.
- **Common-mode thermal:** deterministic per-op rotation `delta_phi` (both
  channels), total K·delta_phi; **conditioned** in both arms
  (A: ÷cos δφ per op; B: ÷cos K·δφ final). The compensation law is NOT
  expected to remove the stochastic components.
- **Arm A (per-op regeneration):** after each op, conditioned BQE with the
  per-op scale `sigma_max_i` projects to the **exact intermediate integer
  (unclamped)** — the SurdFixed64 clamp applies only at the final output,
  matching the oracle. The state is re-encoded from the exact intermediate.
  A trial fails if ANY op's projection is wrong (intermediates may exceed the
  SurdFixed64 range; that alone is not a failure — only a wrong projection
  is).
- **Arm B (chain):** noise accumulates continuously; one conditioned BQE at
  the end with total scale `Sigma = prod(sigma_max_i)`.
- **Paired draws:** per trial, both arms consume the SAME stream in a fixed
  order: operands, then per op `(dpa, dpb, apa, apb, na, nb)`; A uses na/nb
  per op, B uses them only at the final detection. Phase/amp realizations are
  therefore identical across arms.
- **Oracle / band / rejection:** as Step 5 — exact big-int K-fold product,
  clamped once; scored iff `1000 <= max|coeff| <= 30000`; rejection reported.
- **Σ_total diagnostic:** per trial, record Sigma = ∏sigma_max_i — the
  detector-precision driver for arm B.

## 3. Locked parameters

| parameter | value |
|---|---|
| physical / ΔT | canonical silicon; **dT = 2.0 K** (δφ = 9.70e-3 rad/op), conditioned |
| K | {1, 2, 4, 8, 16}; m_K = {1:100, 2:25, 4:9, 8:4, 16:2} |
| band | [1000, 30000] (oracle-computed) |
| sigma_phi (deg) | {0, 0.25, 0.5, 1.0} |
| sigma_amp | {0, 1e-5, 2.5e-5, 5e-5} |
| detector_noise | {0, 1e-4, 3e-4, 1e-3} |
| cells | 3 factors × 4 levels × 5 K = 60 (single-factor: other two = 0) |
| draws / cell | 30,000 (valid ≥ ~2,800 at K=16; CI ~±1.8pt @ 50%) |
| seed | 13 |
| reproducibility | two runs, bit-identical (timestamps excluded); freeze + sha256 |

Levels were validated by prototype: A stable-to-mild across K; B collapses on
every axis (φ: 63→0 @0.5°; amp: 99.8→22 @1e-5; det: 92→0 @1e-4 through the
Σ_total cliff).

## 4. Procedure per cell (factor, level, K)

1. Spawn per-trial rng; draw a,b and ops uniform [-m_K, m_K].
2. Oracle big-int product → clamp → golden; reject out-of-band.
3. Draw per-op noise (fixed order) from the same rng.
4. Run arm A and arm B on the same draws.
5. Score each arm vs golden; record coordinate-wise errors, first-failed-op
   (A) / Σ_total (B), per-arm first-crossing trajectories for the subsample
   (first 200 valid trials).
6. Record rejection fraction, Σ_total stats (mean/max per K).

## 5. New model function (additive, Lithic ≤ ~150 lines)

`ModelC_NoisyOptical.smul_chain_noise(a, b, ops, delta_phi_per_op,
  sigma_phi, sigma_amp, detector_noise, rng, mode='A'|'B',
  return_debug=False)` — NEW; reuses existing primitives; does NOT modify the
frozen `smul_chain_with_noise` (Step 5) or any other function. Implements the
paired draw order and both arms as specified. Returns
`(recovered_a, recovered_b, debug)`.

## 6. Metrics & outputs

- P_A(K, factor, level) and P_B(K, factor, level) — the phase diagram.
- CIs (normal approx), MAE/RMSE/q95/q99 per arm/cell.
- Rejection fraction per K; Σ_total mean/max per K (detector-precision cost).
- First-failed-op histogram (arm A); first-crossing histogram (arm B);
  subsample trajectories (200 valid trials/cell).
- Canonical JSON + frozen copy + sha256 + README entry (results #6).

## 7. Falsification criteria

- σ=0 cells must reproduce Step 5: A = B = 100.00% at all K (gate).
- **Hypothesis under test:** the *underlying accumulation mechanism* worsens
  tolerance with K - B's recovery shows a systematic decline with K on each
  stochastic axis (phase random-walk, amplitude accumulation, Sigma_total
  detector amplification), while A is stable or mild. Small non-monotonic
  Monte Carlo wiggles at a single (K, level) are expected sampling noise, not
  evidence against the mechanism; the falsification test is whether B shows
  **no systematic decline** with K on an axis (no accumulation), or whether A
  systematically degrades faster than B on an axis (would invalidate the
  accumulation model).
- A ≥ B is EXPECTED under stochastic noise; the interesting output is the
  magnitude of the gap and whether any (K>1, B) point meets a P_target with
  fewer regenerations (economic crossover).
- Detector: B must collapse with K consistent with the Σ_total amplification
  (|error| = n·Σ_total/s ≥ 0.5); deviation from that rule = model defect.
- Saturation never scored as success.

## 8. Verification gates

1. Noiseless gate: A = B = 100.00% at all K, σ=0, band-limited.
2. Prototype parity: representative cells match the prototype table within CI.
3. Frozen #1–#5 reruns bit-identical (additive change only).
4. Two full runs bit-identical; freeze; sha256; README.

## 9. Explicit non-goals

- NO combined multi-factor cells in this pass (single-factor isolates
  mechanisms; combined grid is a follow-up).
- NO modification of the Step-5 chain or any frozen artifact.
- NO model tuning after the run; no scoring of saturated trials.
