# Engineering Contract: Step-6b Combined Multi-Factor K-Chain
# (Interaction Phase Diagram)

**Date:** 2026-08-20
**Contract ID:** `contract_photonics_knoise_combined_2026-08-20.md`
**Status:** FROZEN SPEC (awaiting implementation authorization; DO NOT RUN until authorized)

**Roles:**
- Spec Author: John + Deep Code (chose combined grid over K=32 probe; rationale: completes the noise-budget x depth x regeneration-frequency phase diagram; K=32 mostly re-confirms the Sigma_total wall with degenerate m_32=1 operands)
- Halt-and-Flag Implementer: pre-review (identical machinery as step 6; only the grid changes)
- Integration Auditor: reproducibility gates, freeze, evidence

---

## 1. Objective

The Step-6 single-factor pass isolated each stochastic mechanism. This pass
measures their **interaction** in the K-chain: does P_recover(K) under combined
noise follow the independent-product model, worst-axis dominance, or something
else (compounding / cancellation)? This determines whether the ISA's
regeneration-interval parameter K can be set from single-factor budgets or
needs a joint budget.

## 2. Design (locked)

Identical machinery to the frozen Step-6 experiment
(`smul_chain_noise`, arm A per-op regeneration vs arm B chain, paired draws,
independent big-int oracle, band [1000,30000], dT=2K conditioned, m_K, seed 13,
30000 draws/cell, rejection diagnostic, first-failed-op / Sigma_total
diagnostics). **Only the grid changes:**

| factor | levels (mild, moderate) |
|---|---|
| sigma_phi | 0.5 deg, 1.0 deg |
| sigma_amp | 1e-5, 5e-5 |
| detector_noise | 1e-4, 1e-3 |

All 2 x 2 x 2 = 8 combinations x K in {1,2,4,8,16} = **40 cells**.
The all-zero cell is already established (A = B = 100% at all K, step 6).

## 3. Predictions under test

For each K and arm, define from the frozen Step-6 single-factor recoveries at
the same (level, K):

- **Independent-product model:** p_pred = p_phi * p_amp * p_det
- **Worst-axis dominance:** p_min = min(p_phi, p_amp, p_det)

Falsification / classification:
- measured ~= p_pred  -> failures are statistically independent (K from
  single-factor budgets is valid).
- measured ~= p_min   -> worst axis dominates (joint budget unnecessary).
- measured << p_min   -> compounding (joint budget REQUIRED; interaction is a
  real cost).
- measured > p_min (but < p_pred is ambiguous) -> partial dominance.

## 4. Metrics & outputs

- P_A(K, combo) and P_B(K, combo), CIs, MAE/RMSE/q95/q99.
- Interaction ratios: measured / p_pred and measured / p_min per cell.
- Rejection, Sigma_total stats, first-failed-op histogram (A) per cell.
- Canonical JSON + frozen copy + sha256 + README entry (result #7).

## 5. Verification gates

1. sigma=0 gate is inherited from step 6 (all-zero cells unchanged).
2. Single-factor cells (levels 0) are NOT re-run; combined cells only.
3. Prototype parity spot-check on 2-3 cells vs step-6 single-factor anchors.
4. Two full runs bit-identical; freeze; sha256.

## 6. Explicit non-goals

- NO change to step-6 frozen cells or machinery (identical function, new grid).
- NO K=32 in this pass (deferred; m_32=1 degeneracy noted).
- NO model tuning after the run.
