# PHY-R3 — Exact tangent stability of the PHY-R2 equilibrium family

2026-10-20. Class A host-only experiment (AGENTS.md §4.3). Imports the PHY-R1 fixture and
PHY-R2 constitutive code read-only; no result or material law changed. No RTL, simulator or FPGA work.
**Result: CONFIRMED (static scope): every sampled equilibrium is strictly stable, and the whole path is
proved stable, under both cable laws.** 8 test groups pass, 9.6 s. The PHY-R1 (7), field (5) and PHY-R2 (7)
regressions still pass.

```bash
timeout 60 bash -c 'ulimit -v 1048576; python3 -B -I research/phy_r3/test_phy_r3.py'
```

## Derivation (all entries rational; no square roots appear)

Lagrangian L = Σ cable energies + Σ strut μ_s(Q_s − 16), μ_s = q_s/2. Struts are holonomic constraints; their
reaction enters only as geometric stiffness q_s (no axial term). With δ_i = Aε_i, AᵀA = M, the second form is

  H(ε) = Σ_members q_e (Δε)ᵀM(Δε) + Σ_cables s_c (Δpᵀ M Δε)²,  tangent space N: Δpᵀ M Δε = 0 per strut.

| Law | axial stiffness a | s_c = (a − q)/Q |
|---|---|---|
| Squared, E = (κ/4)(Q−R)² | q + 2κQ | **2κ** (constant) |
| Hooke, T = k(ℓ−ℓ₀) | k | **(k − q)/Q = kℓ₀/(ℓQ)** |

Rigid motions are ε_i = c + M⁻¹S p_i (S skew); they lie in N and in ker H exactly (a built-in check of the assembly).

## Independent checks
- The closed-form H equals the s² coefficient of the Lagrangian computed from the energies themselves along
  exact rational lines (polynomial for squared; exact √(1+u) series for Hooke with ℓ₀/ℓ = √(R/Q) rational), on the
  reference and on M₁ = (m₁₂ = 3/5) with rational coordinates; the first variation vanishes there. Two
  mutants (s = κ instead of 2κ; flipped strut-reaction sign) fail this identity.
- Rigid motions in ker H and N for all tested states (including relational-only M₂).

## Results, reported separately
1. **Static equilibrium** (PHY-R2 code): holds for the reference, M₁ and M₂ at t ∈ {0, 7/15, 25/39, 40/51, 5/6, 1}, both laws.
2. **Infinitesimal stability:** on N (dim 30, strut-constraint rank 6) H|N is PSD with nullity exactly 6 (= rigid motions), rank 24 — at the reference, at M₁, and at every sample, both laws, both targets. Exact LDLᵀ over ℚ.
3. **Strict constrained local stability:** justified for those states by the second-order sufficient condition (Lagrange equilibrium + regular constraints, PD on the tangent space modulo the rigid-motion symmetry, cables taut so the energy is smooth). The theorem is cited, not re-derived.
   **Whole path, all t ∈ [0,1], proved** (exact lemmas checked in the tests): Ω is PSD with nullity 4 and does not depend on t, so Ω⊗M ⪰ 0 with kernel = affine ε = c + Bp; s_c > 0 for every t (squared: 2κ = 1; Hooke: k = 4 > q = 1 and Q_c > 0 since M(t) is PD); the 24 cable directions alone satisfy the conic condition (rank 6), which forces the symmetric part of MB to vanish, so B is rigid. Hence H is positive definite on R³⁶ modulo rigid motions, a fortiori on N. This leans on PHY-R2's proved equilibrium/tautness along the path.
4. **Dynamic stability:** not addressed (no masses, damping or time stepping).

## Do the two laws differ in stability?
Same equilibria, same verdict, different quantities:
- Squared: s_c = 2κ, so it is stable for every admissible κ > 0, independent of t and shape.
- Hooke: s_c = k ℓ₀/(ℓ Q) > 0 exactly when ℓ₀ > 0, i.e. **stability coincides with PHY-R2's admissibility**; s_c varies with t (range 1/2 at t=0; 5/14–5/6 at t=1).
- Curvature along the three strut-preserving shear modes (the tangent of the PHY-R1 family) is 288 under the squared law at every t, and 144 (t=0) to 3550/21 ≈ 169.0 (m₁₂ mode) and 3400/21 ≈ 161.9 (the other two) at t=1 under Hooke. Magnitudes depend on the ε normalisation, so compare laws at a fixed mode, not across t.
- Consequence: those modes cost nothing in the prestress term, so the PHY-R1 family is a flat direction **only if rest parameters are retuned**. With frozen rest parameters each equilibrium is isolated and stiffened by the material term; moving along the family requires actuation.

## Negative controls (all rejected for the intended reason)
- **Prestress only (s = 0):** Ω⊗M is PSD but nullity is 9 = 6 rigid + 3 shear (each shear in ker H). PSD prestress does not give a PD tangent stiffness.
- **Negative stiffness** (Hooke k = 1/2 < q, ℓ₀ < 0; refused by PHY-R2, computed diagnostically): H is not PSD and the shear witness has negative curvature.
- **Stale rest parameters** (t=0 values used at t=1): densities ≠ stress, not an equilibrium, so no Hessian is certified.
- **Strut reaction omitted:** rigid rotations leave ker H, so the Hessian is wrong.
- **Conic test on a 5-cable subset:** rank < 6, rejected.
- State refusals unchanged: m₁₂ = 1 and 6/5 → NOT_POSITIVE_DEFINITE; M₂ still OUT_OF_FIELD in Q.

## Claim boundary
Exact static and infinitesimal results for rigid struts modelled as constraints. Not covered: struts with finite compressive stiffness (a different system), slack or unilateral cable switching away from the taut region, dynamics, finite perturbations beyond second order, real materials (stiffnesses are the arbitrary PHY-R2 fixtures). Coordinate oracles are used on the Q-materialisable states only; M₂ is checked relationally.

## Smallest next question
The family is stable at fixed actuation, so the open step is the dynamic/actuated one: does quasi-static retuning of rest parameters along M(t) keep the system on this branch (no other equilibria nearby, no loss of tautness) when cable rest parameters change at a finite rate?
