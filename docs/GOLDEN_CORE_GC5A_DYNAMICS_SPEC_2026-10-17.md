# Golden Core GC-5A — exact bounded edge-state dynamics

**Status:** Executed bounded software experiment; see results report

**Date:** 2026-10-17

**Dependency:** GC-5 oriented-edge operators and GC-4 exact symmetry catalog

**Scope:** 12 exact update steps on the same 60 directed-edge states

**Hardware / ISA:** No RTL, ISA, device, or SPU-13 profile changes

## Initial state and update

Use the directed-edge state space `M = Q(√5)^D` and frozen `T_L`, `T_R` from
GC-5. Order directed edges lexicographically as in
`fixtures/golden_core_gc5_oriented_edge_turns.json`. The initial state `x_0`
is the basis vector of edge `(0,1)` with coefficient 1 and zero elsewhere.

Iterate exactly for `n=0,...,11`:

`x_(n+1) = F_(a,b)(x_n) = a T_L(x_n) + b T_R(x_n)`.

Run a parity-neutral control `(a,b)=(1,1)` and the signed asymmetric profile
`(a,b)=(3+√5, 1−√5)`. The latter is a signed linear operator: `1−√5 < 0`;
its coefficients are not probabilities.

## Mirror comparison

For each of the 60 GC-4 orientation-reversing maps `g`, transport the initial
state through its induced directed-edge permutation `P_g`. The neutral control
must satisfy `P_g x_n = x_n^g` with the same coefficients. The signed profile
must satisfy `P_g x_n = x_n^g`, where `x_n^g` evolves from `P_g x_0` using the
exchanged coefficients `(b,a)`. These are exact state-vector comparisons at
every step. Also test proper-map trajectories without exchanging coefficients.

## Measurements and controls

- Per-step exact state hash and maximum bit length of rational coefficient
  numerators/denominators.
- Exact total coefficient sum; it must scale by `a+b` each step because each
  turn is a permutation. For the asymmetric profile, `a+b=4`.
- A parity-odd, seed-relative turn-channel observable:
  `J_n = x_n[T_L(e_0)] − x_n[T_R(e_0)]`, where `e_0` is the initial edge basis
  state. Under a mirrored seed and orientation-reversing map, the transported
  left and right channels exchange, so `J_n^g = −J_n`.
- A deliberately corrupted mirror edge permutation must be rejected.
- Freeze the seeds, weights, horizon, per-step hashes, growth measures and
  observables in a fixture before reporting the result.

This observable measures the signed state amplitudes in the two selected turn
channels. It is not a probability, a generic transport rate, or an
initial-condition-independent invariant.

Results are recorded in `docs/GOLDEN_CORE_GC5A_DYNAMICS_RESULTS_2026-10-17.md`.
