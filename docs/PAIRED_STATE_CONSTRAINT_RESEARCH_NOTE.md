# Paired-state constraint computation — parked research note

**Status:** PROPOSED RESEARCH QUESTION — ACCEPTED FOR PARKING; NOT AN ISA SPECIFICATION
**Profile ownership:** None; independent of ISA-A and archived ISA-B
**Implementation status:** None authorized or implied
**Date:** 2026-10-17

This note parks a clean mathematical question suggested by the historical
ISA-B twin-register experiment. It does not revive that instruction set or
adopt Wheeler–Feynman physics as an architectural premise.

## Candidate state model

Choose state spaces \(O\) and \(C\) over a declared coefficient domain
\(K\), and define a paired state

\[
S=(o,c)\in O\times C.
\]

Specify a constraint map

\[
F:O\times C\to Y,
\qquad
\mathcal A=\{(o,c):F(o,c)=0\},
\]

where \(Y\), equality, domains, and exceptional cases are explicit. The
admissible paired states are \(\mathcal A\). The symbols \(o\) and \(c\) do
not intrinsically mean past-directed and future-directed physical signals;
they are labels for the two mathematical components until a model assigns
them operational meaning.

## Candidate exact Quadray predicate

For three Euclidean points with side quadrances \(Q_1,Q_2,Q_3\) and triangle
area \(A\), the squared Heron/Gram identity is

\[
(Q_1+Q_2+Q_3)^2
=2(Q_1^2+Q_2^2+Q_3^2)+16A^2.
\]

Thus the Triple Quad equality without the area term holds only in the
degenerate, zero-area case in the ordinary positive-definite Euclidean
setting. It is not a general triangle-closure condition.

For the first reference, use the recovered tetrahedral Quadray basis
\(A=(1,1,1)\), \(B=(1,-1,-1)\), \(C=(-1,1,-1)\),
\(D=(-1,-1,1)\), and the corresponding Cartesian bridge. In the four
redundant coordinates, fix the canonical metric matrix

\[
G_Q=4I_4-\mathbf 1\mathbf 1^T.
\]

This matrix has a gauge null direction along \(\mathbf 1=(1,1,1,1)^T\);
restricted to the zero-sum subspace \(\mathbf 1^Tq=0\), it is
positive-definite. It gives

\[
q^TG_Qq=\sum_{i<j}(q_i-q_j)^2=4\sum_iq_i^2
\quad\text{when }\sum_iq_i=0.
\]

This normalization and basis are fixed for G1/G2. Alternative Quadray scales
or metrics belong to later comparisons, not the initial oracle. Begin with
coordinates in \(\mathbb Q\), represented by arbitrary-precision reduced
fractions; introduce algebraic extensions only in a separate experiment.

For nonzero displacement vectors \(o,c\) in this three-dimensional
zero-sum subspace, define

\[
Q_O=o^TG_Qo,\qquad Q_C=c^TG_Qc,\qquad D=o^TG_Qc,
\]

and the Gram determinant

\[
F(o,c)=Q_OQ_C-D^2.
\]

Over the standard real embedding and this positive-definite restricted metric,
\(F=0\) exactly when the two nonzero vectors are linearly dependent. The sign of \(D\) can
separate same-direction from opposite-direction dependence; its sign test
requires an explicitly chosen ordered real embedding. The predicate uses
products and equality only, so no square root or trigonometric evaluation is
needed. The exact reference must still specify coefficient growth and any
finite-width overflow boundary.

For a frozen near-degenerate control family, choose
\(o=(1,-1,0,0)\), \(e=(1,0,-1,0)\), and
\(c_N=No+e=(N+1,-N,-1,0)\) for positive integer \(N\). Under \(G_Q\),
\(Q_O=8\), \(D(o,c_N)=8N+4\), \(Q_C=8(N^2+N+1)\), and
\(F(o,c_N)=48\) for every \(N\). Thus the exact predicate remains nonzero
while the normalized determinant
\(F/(Q_OQ_C)=3/[4(N^2+N+1)]\) tends to zero. G2 should verify the exact
positive value for a declared sequence of \(N\), and separately report any
finite-precision comparison behavior rather than treating floating-point
classification as authoritative.

This predicate means linear dependence of two displacements. It does not by
itself mean that two rays or segments intersect, that a transaction is
physically coherent, or that quantum amplitudes interfere correctly.

## Properties that must be distinguished

1. **Constraint satisfaction:** a state belongs to \(\mathcal A\) exactly
   when \(F(o,c)=0\).
2. **Constraint-preserving evolution:** a map \(U\) preserves the admissible
   set when \(U(\mathcal A)\subseteq\mathcal A\).
3. **Reversibility:** \(U\) is bijective on its declared state domain and an
   explicit inverse \(U^{-1}\) is provided and checked.
4. **Time-reversal covariance:** for a declared involution \(J\), a discrete
   reversible evolution satisfies \(J U J^{-1}=U^{-1}\). Involution alone,
   \(J^2=I\), is insufficient.
5. **Boundary-value solving:** given independently specified boundary data,
   an algorithm finds admissible states and states whether existence,
   uniqueness, or multiplicity is guaranteed. This is not implied by paired
   storage or reversible stepping.

These are separate acceptance questions. A constraint need not be conserved
by every update; if not, the intended relation between \(U\) and \(F\) must be
specified instead of presumed.

## Minimum future specification

Before software implementation, a future proposal must state:

- the exact state and coefficient domains, canonical encodings, and overflow
  or growth policy;
- the map \(F\), its codomain, and a nontrivial satisfying and failing state;
- the evolution map \(U\), its domain, and whether it preserves \(\mathcal A\);
- a candidate reversal map \(J\), its action on both components, and a
  proof or counterexample for \(J U J^{-1}=U^{-1}\);
- whether the task is an initial-value evolution or a boundary-value solve;
- independent small cases, negative controls, and a conventional exact
  software baseline before any performance claim.

Exact arithmetic may avoid rounding in the reference model, but does not
automatically make the algorithm cheaper, reversible, physically meaningful,
or suitable for fixed-width hardware. Those are measured or separately
argued properties.

## Research boundary

This is a parked question for post-stabilization research. It authorizes no
ISA encoding, RTL, hardware campaign, physical interpretation, or changes to
the current SPU-13 profile. The [ISA-B semantic audit](ISA_B_SEMANTIC_AUDIT_2026-10-17.md)
records why the historical `INVJ`/`PHSLK` semantics are not a foundation for
such claims without a new contract.

## Proposed staged experiment

This is a candidate research sequence, not an implementation authorization:

| Stage | Question | Bounded acceptance evidence |
|---|---|---|
| G1 — Paired quadrance | Are the canonical Quadray metric and paired-state quadrances computed exactly? | Arbitrary-precision oracle agreement on frozen vectors, including zero, gauge shifts, scale changes, and metric invariants under \(G_Q\). |
| G2 — Gram coherence | Does \(F(o,c)=0\) classify nonzero collinear pairs exactly? | Collinear and noncollinear controls plus the near-degenerate \(c_N\) family; direction uses exact sign in the standard real embedding. |
| G3 — Reversible evolution | Is a specified state update invertible and time-reversal covariant? | Exact round-trip and \(J U J^{-1}=U^{-1}\) checks on a finite declared domain, or a counterexample. |
| G4 — Two-boundary solve | Can an algorithm satisfy independently supplied endpoint constraints? | Frozen instances with explicit existence/uniqueness status and exact residual checks. |
| G5 — Amplitude comparison | Does a declared geometric model reproduce any selected complex-amplitude predictions? | Side-by-side cases against a conventional complex-amplitude reference, including relative-phase and probability outcomes. A match on selected cases is not equivalence to quantum mechanics. |

G1/G2 are the smallest sensible first tranche. G3–G5 remain separate
decisions after their models and observables are specified. In particular,
G5 must represent relative phase and probability explicitly; equal spatial
quadrance alone cannot encode the interference behavior of arbitrary complex
amplitudes. The three independent zero-sum Quadray coordinates also do not
constitute a spacetime coordinate or establish a \(D_4\) root-lattice
identification.
