# Golden Core GC-5 — oriented edge-turn operator

**Status:** Executed bounded software experiment; see results report

**Scope:** Exact software model on the frozen GC-3 icosahedron only

**Hardware / ISA:** No RTL, ISA, device, or SPU-13 profile changes

## Question

Can an orientation-sensitive local operator be defined exactly on the GC-4
icosahedron, and can its law-level covariance be distinguished from internal
symmetry by exhaustive finite checks?

This experiment is about a mathematical operator on a finite graph. It makes
no claim about physical chirality, emergent dynamics, computational advantage,
or general golden geometries.

## Frozen construction

Use the exact `Q(√5)` vertex vectors and the ambient orientation already fixed
by the GC-3 coordinate order. At each vertex `v`, its five adjacent vertices
form a 5-cycle (the vertex link). Orient that cycle so that

`det(v, n_k, n_(k+1)) > 0`

for every consecutive pair, where the determinant is evaluated exactly in the
positive real embedding. Choose the least vertex index only to select a
canonical starting point; cyclic successor and predecessor do not depend on
that start.

Let `D` be the 60 directed edges of the icosahedron and let the state space be
`M = Q(√5)^D`. On basis states define two directed-edge turns:

`T_L e_(u,v) = e_(v, succ_v(u))`

`T_R e_(u,v) = e_(v, pred_v(u))`.

Extend both operators linearly over `Q(√5)`. For exact coefficients `a,b`,
define `F_(a,b) = a T_L + b T_R`. A spatial symmetry `g` transports directed
edge basis states by `P_g e_(u,v) = e_(g(u),g(v))`.

## Required identities and outcomes

For each of the 120 GC-4 symmetries, verify on the directed-edge basis:

- determinant `+1`: `P_g T_L = T_L P_g` and `P_g T_R = T_R P_g`;
- determinant `−1`: `P_g T_L = T_R P_g` and `P_g T_R = T_L P_g`.

Therefore `P_g F_(a,b) = F_(a,b) P_g` for proper maps, and
`P_g F_(a,b) = F_(b,a) P_g` for orientation-reversing maps. Equal weights give
internal symmetry under the full 120-map group. Unequal weights are expected
to retain the 60 proper internal symmetries while remaining covariant under all
120 maps when the weights are exchanged under orientation reversal.

Tests must independently reconstruct the oriented links, include at least one
equal-weight and one unequal-weight profile, and include a deliberately
misoriented-link negative control that is detected. Freeze all directed edge
indices, link cycles, and left/right permutations before reporting results.
The resulting evidence is recorded in
`docs/GOLDEN_CORE_GC5_RESULTS_2026-10-17.md`.

## Boundaries

The edge-state model is distinct from a vertex-state cellular automaton. No
time evolution, thresholding, labels, or state-dependent weights are included
in this tranche. GC-4 substrate labels and weights remain separate from the
operator coefficients. Any later dynamics require a new specification.
