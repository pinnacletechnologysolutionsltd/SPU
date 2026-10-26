# QCG-0 independent fixture review packet

Date: 2026-10-22. Status: **issued for an independent reviewer; review NOT performed; fixture NOT certified.**
Author of this packet: Claude (QCG-0 author). Reviewer: to be appointed by the owner (fresh context; not the QCG-0
authoring context; not the HEX-SOM acceptance context; the owner suggests GPT-6.1 only if its SOM work stays isolated).

**Independence rules.** The reviewer receives this packet and `QCG0_PREREGISTRATION.md` §§2–6, 9–10, 12. The reviewer must
not receive the author's drafting-calculator output (scratch, not preserved in the repository). The reviewer chooses the
quintic by the neutral rule below and derives every number themselves. Numbers already printed in the pre-registration
(the PH3 values taken from `docs/QSG2_PH_CURVE_SPECIFICATION.md`; φ_sq = (4t+18t²+27t³)/49 with φ′=((2+9t)/7)²;
the curvature formula; the join table) are *claims to verify*, not inputs.

## 1. Neutral selection rule for the quintic (R-SEL) — fixed before any candidate code or cost exists

Primitive form, h = 1, interval [0,1], domain Q, arithmetic exact. A fixture is a tuple of integers
(u₀,u₁,u₂,v₀,v₁,v₂) with U = u₀+u₁t+u₂t², V = v₀+v₁t+v₂t². Constraints:

* **K1 (dense):** all six coefficients are nonzero, each in {−2,…,2}\{0}; so deg U = deg V = 2 and no arm gains from sparsity.
* **K2 (primitive):** gcd(U,V) = 1 in Q[t], certified by a nonzero integer resultant Res(U,V). This also certifies regularity:
  U²+V² = 0 at a real t would force a common root, so σ = U²+V² > 0 on all of R (no approximate roots).
* **K3 (non-trivial curvature):** N(t) = U V′ − U′ V has degree ≥ 1 (curvature is not of the trivial form).
* **K4 (non-degenerate direction):** the tangent direction changes over [0,1] (U/V is not constant there).
* **Order:** enumerate tuples by (max|cᵢ|, Σ|cᵢ|, then lexicographic order on (u₀,u₁,u₂,v₀,v₁,v₂)); the fixture is the first
  tuple satisfying K1–K4. If none exists with entries in {−2,…,2}, widen to {−3,…,3} and say so.
* The reviewer may propose a different neutral rule, but must file its text and hash before any candidate implementation
  exists, justify neutrality (no knowledge of operation counts), and state that the rule was fixed before it was applied.

(Existence of dense all-±1 solutions was observed by the author; no selection was made.)

## 2. What the reviewer must establish and file

All values as exact rationals, canonical (reduced numerator, positive denominator), in a versioned UTF-8 JSON file plus a
short certificate. Filing: `research/qcg_0/QUINTIC_FIXTURE_CERTIFICATE.md` and `QUINTIC_FIXTURE_VALUES.json` (neither exists
yet), SHA-256 of both recorded in the pre-registration before any implementation.

**F-A. The quintic PH5.** The selected tuple; the selection log (which earlier tuples failed which constraint);
power-basis coefficient lists of U, V, U′, V′, x′ = U²−V², y′ = 2UV, σ = U²+V², σ², x, y (with r(0) = (0,0)), S = ∫σ
(S(0)=0), N = UV′−U′V, D = σ²; degrees; the resultant; coefficientwise verification of x′²+y′² = σ² and S′ = σ;
Bernstein control points of x and y (degree 5) and of x′, y′ (degree 4); endpoints r(1) and S(1); κ(0), κ(1) as (N,D)
pairs; exact verification that κ = N/D equals cross(r′,r″)/σ³ at at least five rational points computed by a different
route (second derivative from the coefficient lists).

**F-B. Cell A expected outputs.** For the 16-value tape in the pre-registration §9.1, in order, the nine values per query:
r (2), r′ (2), σ², σ, S(t)−S(0), N(t), D(t), plus the flag D ≠ 0.
Also the dyadic sequential tape t = k/16, k = 0..16, S1–S3 observables, as the negative-control reference.

**F-C. Cell B expected outputs.** On PH3 = (U,V)=(1,t), h=1 and φ_sq: the retimed generator (Ũ,Ṽ,h̃) in the h-form and in the
primitive form, with the polynomial identity check against φ′·(r′∘φ); degrees of the composite position and arc length;
for the 16-value tape the seven values per query (ψ, ψ′, signed speed, speed, S(φ(τ))−S(φ(0))); behaviour under φ_bad = 4t−4t²
(oriented arc length exact; total traversal length outside the exact class; the sign change location).

**F-D. Proof obligations.** Independently re-derive R1 (PH-class closure under polynomial retiming), R2 (nonnegative speed
condition), R3 (primitive closure iff φ′ = ±q²), and the reversal rule; state any error. Classify the completeness claim
(h-form covers every polynomial PH curve over Q) as proved, cited with an exact reference, or unverified; the pre-registration
treats it as **unverified within this experiment** unless established here.

**F-E. Controls to derive.** Join predicates for the table in pre-registration §9 and §5; the E2 harmonic-law residual
(A = −P, order 4, h = 1/4: forward step then backward step, exact rational residual from an independent closed-form
Taylor-polynomial composition); E1a (C4 word closure) and E1b (3-4-5 rotation, denominator 5ᵏ) expectations.

## 3. Items the reviewer must scrutinize (checklist)

1. The generalized h-form: statement, scope and where it relies on the literature.
2. Separation of PH-class closure, primitive-generator closure and the nonnegative-speed condition.
3. That the quintic was chosen by a rule fixed before cost evaluation, and that nothing in K1–K4 favours any arm.
4. That the Cell A observable set is identical for every arm and contains no quotient.
5. That the equal precomputation and caching rights (pre-registration §8.1) are implementable for every arm.
6. That sequential forward differencing is treated as a negative control, not an advantage cell.
7. Exactness classes: no E2 output is labelled exact; no A31 residue is used as geometry.

## 4. Disposition (to be filled by the reviewer)

Choose one: **CERTIFIED**, **CERTIFIED WITH CORRECTIONS** (list each; the author amends the pre-registration), or
**REJECTED**. Record: reviewer context and identity as the owner chooses to describe it; whether the author's calculator
output was seen (must be "no"); method used for each value; every discrepancy with the pre-registration; hashes of the
two filed artifacts; the date. A fixture is frozen only after certification and hash recording.

## 5. Source identities (author side, 2026-10-22)

Repository HEAD `66bdc789c67e99658c0fa27cab1c01121117f4d5`; the working tree is dirty from other agents and QCG-0 reads no
repository source file. Pinned documents (SHA-256), to be re-computed by the reviewer:

    b33205e92370a41de5d1b7806f8435057065ea5272ea21866f5700be99025fa8  research/qcg_0/QCG0_PREREGISTRATION.md (409 lines)
    e64af826a304f9d73095a486e9fc9be75eab61ce42adb64c006b4c429f76e2a9  docs/QSG2_PH_CURVE_SPECIFICATION.md (PH3 inputs and values)
    f7b876e77ef2b5e1b9ec914d2a4dae9c834058f46aa5fec1c4899863c13529bb  docs/QSG2_SOFTWARE_RESULTS.md

Interpreter for the later pilot: `/usr/bin/python3` 3.14.8. This packet's own hash is recorded by the owner when it is issued.
