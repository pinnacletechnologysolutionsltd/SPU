# PHY-R2 — Exact cable actuation and equilibrium reachability

2026-10-20. Class A host-only experiment (AGENTS.md §4.3,
[execution policy](../../spu_strategy/RESEARCH_EXECUTION_POLICY.md)), selected by
the owner. It builds on [PHY-R1](../phy_r1/FINDINGS.md) and imports its fixture,
metric machine and reference checks read-only.
**Result: CONFIRMED (static scope).** The reference and a non-congruent PHY-R1 metric
are joined by a continuous one-parameter family of exact static equilibria. Along the
whole family, cable tensions are positive and rest parameters are rational, under two
distinct constitutive laws. 7 test groups passed, exit 0, 1.1 s. The PHY-R1 (7) and
field (5) regressions were re-run and pass. No simulator, RTL or earlier evidence changed.

```bash
timeout 60 bash -c 'ulimit -v 1048576; python3 -I research/phy_r2/test_phy_r2.py'
```

## Conventions recovered

The fixture has 24 cables and 6 struts. Force density is q = T/ℓ, with cables q > 0
and struts q < 0. The unique self-stress is cable 1, strut −3/2. The prestress level
λ (= 1 here) scales it, and λ is a free actuation degree of freedom.
Target densities are q* = λ·q̂.

## Constitutive laws, written through rest quadrance R = ℓ₀²

| | Hooke T = k(ℓ − ℓ₀) | Squared-length E = (κ/4)·max(Q − R, 0)² |
|---|---|---|
| Force density | q = k(1 − √(R/Q)) | q = κ(Q − R), since ∂E/∂xᵢ = κ(Q−R)(xᵢ − xⱼ) |
| Equilibrium rest | **R = Q(1 − q*/k)²** | **R = Q − q*/κ** |
| Admissible | 1 − q*/k > 0 (positive rest length) | R > 0 |
| Cable taut | R < Q ⇔ q* > 0 | R < Q ⇔ q* > 0 |
| Arithmetic | needs √Q for ℓ and T, but R and the equilibrium test are rational | polynomial throughout |

Cables are unilateral: a slack cable carries no force. Struts are bilateral.
Stiffness values (cable/strut): Hooke k = 4/40, squared κ = ½/5. They are arbitrary
fixture choices. **The two laws are different physical models**, and the squared law is
not presented as Hooke's law.

## Path and proofs

The path is M(t) = (1−t)I + t·M₁ for t ∈ [0,1]. Two targets were tested: M₁ = m₁₂ = 3/5
(non-congruent, materialisable in Q), and M₂ = (1/3, 1/4, 1/5) (relational-only).

- **Positive-definite with unit diagonal for every t.** The PD cone is convex, both
  endpoints are PD, and both have unit diagonal. So strut quadrance is 16 throughout.
- **Equilibrium for every t.** Each M(t) is an affine image of X₀, and
  Ω(X₀A(t)ᵀ) = (ΩX₀)A(t)ᵀ = 0 with the same stress.
- **Struts disjoint for every t.** An invertible affine map preserves segment
  disjointness.
- **Cable quadrances Q_e(t) are affine in t** (exact test). Their minimum on [0,1]
  is therefore at an endpoint: 18/5 for M₁ and 61/15 for M₂. Both exceed λ/κ = 2, so
  squared-law rest quadrances stay positive. The Hooke condition 1 − q*/k does not
  depend on t.
- **Rest schedules are affine in t, hence continuous and rational for rational t.**
  Hooke gives R_e(t) = c_e²·Q_e(t); squared gives R_e(t) = Q_e(t) − q*/κ.

Sampled confirmation at t ∈ {0, 7/15, 25/39, 40/51, 5/6, 1}, on both targets:

- The induced densities equal q* exactly under both laws.
- All rest parameters are positive and every cable is taut.
- Relational ΩGΩ = 0 holds.
- Where coordinates materialise, explicit node-force sums vanish under both laws:
  t ∈ {0, 7/15, 25/39, 40/51, 1} in Q, and t = 5/6 in Q(√3) only. The existing oracle
  reports BALANCED.

**Strut reaction.** Strut compression is constant at 6λ along the path, and so are the
strut rest parameters: Hooke R = 16·(83/80)² = 6889/400 and squared R = 163/10, both
above 16 (compressed). **Only the cables need actuation.**

## The laws are not equivalent

They need different rest schedules for the same equilibrium tension. Hooke holds
R/Q constant (9/16 for cables); squared holds Q − R constant (2). The cable tangent
stiffness dT/dℓ at t = 0 is 4 under Hooke and κ(3Q − R) = 7 under the squared law.

**Cross-law control.** Apply the Hooke rest schedule under the squared law:
- At t = 0 the cable densities stay uniform (21/16), but the strut level (−489/80)
  breaks the 2:−3 ratio.
- At t = 1 the cable densities become non-uniform (63/80 … 147/80). The self-stress is
  unique and requires equal cable densities, so **no** strut setting can restore
  equilibrium.

## Negative controls (all behave as required)

- **Stale rest parameters** (solved at t = 0, used at t = 1): no equilibrium under either law.
- **Slack cable** (squared R = Q; Hooke ℓ₀ = 1.5ℓ): that cable's force is 0, and there is no equilibrium.
- **Invalid parameters** (κ = 1/4, so λ/κ = 4 > 18/5; Hooke k = 1, giving zero rest length): path refused, rest solve raises.
- **Singular (m₁₂ = 1) and indefinite (m₁₂ = 6/5) endpoints**: refused, NOT_POSITIVE_DEFINITE.
- **Incorrect certificate reuse** along a strut-translation path (midpoint and end):
  - REUSE refuses with DEPENDENCY_CHANGED.
  - The mutant carry is caught both relationally and by explicit coordinate force sums.

## Corrected expectation

My first cross-law assertion predicted equilibrium at t = 0. That was wrong because it
ignored the struts' rest parameters. The assertion now tests the actual distinction:
uniform cable densities at t = 0, non-uniform at t = 1. A Hooke slack control originally
passed only through a non-square ratio, and it now exercises slack explicitly. No other
expectation changed after observing results.

## Claim boundary

Established: an exact, **quasi-static** family of equilibria. Admissible rest schedules
connect two distinct PHY-R1 metric states, the arithmetic is exact, and the relational
and coordinate evaluations agree. Not established:

- **dynamic reachability**: no masses, rates, damping or time integration;
- **stability under actuation**: the tangent stiffness matrix along the path was not
  computed, and PHY-R1's super-stability was checked on the reference only;
- **a controller**;
- **real material behaviour**: stiffness values are arbitrary, and Hooke itself is an idealisation.

PHY-R1's results and both earlier falsified rotation-controller hypotheses are unchanged.

## Smallest next mathematical question

Along M(t), is the **tangent stiffness matrix** K(t) = K_material + K_geometric
positive-definite on non-trivial motions (modulo rigid motions) for each law, with
rest lengths frozen at their equilibrium values? That decides whether each static
equilibrium on the path is stable. Under the squared law the entries are rational. Under
Hooke they involve ℓ = √Q, so an exact sign decision may need quadratic-extension predicates.
