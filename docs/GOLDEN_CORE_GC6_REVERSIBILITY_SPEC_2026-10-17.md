# Golden Core GC-6 — operator reversibility and paired-state construction

**Status:** Executed bounded software experiment; see
[`GOLDEN_CORE_GC6_REVERSIBILITY_RESULTS_2026-10-17.md`](GOLDEN_CORE_GC6_REVERSIBILITY_RESULTS_2026-10-17.md)

**Date:** 2026-10-17

**Dependencies:** GC-4 exact symmetry catalog; GC-5 oriented-edge operators

**Scope:** Exact linear algebra for two 60-dimensional operators and a separate
120-dimensional paired-state rule

**Hardware / ISA:** No RTL, ISA, device, or SPU-13 profile changes

## 1. Existing operators

Use the frozen directed-edge basis and maps `T_L`, `T_R` from GC-5. Over
`K = Q(√5)`, qualify

`F_(a,b) = a T_L + b T_R`

for the equal profile `(a,b)=(1,1)` and signed profile
`(a,b)=(3+√5, 1−√5)`.

For each profile, compute exact rank and a basis for the kernel. Use exact
Gaussian elimination over `K` and independently check the result using the
relative permutation `U = T_L^−1 T_R` and its cycle decomposition. For an
invertible operator, provide an exact inverse representation and verify both
compositions on every basis vector. For a singular operator, provide a
nonzero exact kernel vector and verify its image is zero.

The domain is the full 60-dimensional `K` vector space on directed edges.
Report no claim about invertibility on other state spaces or projections.

## 2. Reversible paired-state rule

Study this construction separately from `F`:

`J_(a,b)(x,y) = (F_(a,b)x − y, x)`.

Its proposed inverse is

`J_(a,b)^−1(u,v) = (v, F_(a,b)v − u)`.

Verify both compositions exactly on every basis vector in the 120-dimensional
paired state space. Check mirror covariance with each of the 120 GC-4 spatial
maps, applying the same vertex-induced transport to both state components
and exchanging `a,b` for orientation-reversing maps.

This is a new second-order paired-state dynamics. Reversibility alone does not
define a Janus point, and this tranche does not choose a distinguished time,
boundary condition, or physical interpretation.

## 3. Acceptance criteria

- Exact rank agrees between field elimination and the permutation-cycle
  calculation.
- Every reported kernel basis vector is nonzero and maps exactly to zero.
- Every reported inverse composes to identity on both sides.
- The paired rule and proposed inverse compose to identity on all paired basis
  vectors for both coefficient profiles.
- Paired-state mirror covariance passes for all 120 frozen spatial maps with
  the required coefficient exchange.
- Results distinguish the existing one-state update from the paired-state
  construction and make no long-term, physical, or hardware claim.
