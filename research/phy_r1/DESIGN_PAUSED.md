# PHY-R1 — paused design note (2026-10-20)

Status: design record. **Executed 2026-10-20 — see [FINDINGS.md](FINDINGS.md).**
(Originally paused before any run so the `knowledge/` review could go first.)

## Prior results this must not overturn

- Single-strut octahedral rotation: FALSIFIED as a balancing controller
  (`spu_strategy/contract_tensegrity_active_control_2026-09-04.md` §11).
- Option A paired-strut rotation: FALSIFIED, 1/24 balanced = identity
  (commit `8f3922e`, `software/tools/tensegrity_group_rotation_sweep.py`).
- Gate inherited from both: **non-congruent new geometry**, not "BALANCED".

## Planned question (new, not a rerun)

Does a metric (Gram) state representation reach a non-trivial family of
balanced, non-congruent configurations of the *same* canonical fixture
(`make_tensegrity_six_strut()`), where the integer-coordinate ABI cannot?

Mechanism (Connelly): if a framework is super stable (stress matrix PSD,
nullity d+1, member directions not on a conic at infinity), every affine
image `p -> A p` is in equilibrium with the **same** stress. The canonical
struts are axis-aligned, so strut quadrances are preserved iff
`M = A^T A` has unit diagonal. State = fixed reference X0 + metric M
(6 rationals); edge quadrances are `d^T M d`; coordinates need `A = chol(M)`,
which needs square roots.

Predicted (to be tested, not assumed):
- integer-coordinate ABI: unit-column integer A are signed permutations only ->
  congruent copies only (consistent with both falsifications);
- metric state: 3-parameter rational family of balanced non-congruent shapes;
- materialisation depends on field: m12=3/5 -> Q, m12=1/2 -> Q(sqrt3),
  m12=1/3 -> needs sqrt2 -> refusal in Q / Q(sqrt3) / Q(phi).

## Planned checks

1. Coordinate model: exact stress solve on materialised coordinates (Q(sqrt d)).
2. Relational model: certificates (stress, super stability, conic condition,
   strut disjointness) carried across affine transitions by declared dependency.
3. Hybrid: relational state, materialise only on observation, refuse out of field.
4. Independent reference: full pairwise quadrances -> centred Gram G;
   equilibrium iff `Omega G Omega = 0`; 3D realisable iff G PSD rank 3;
   strut pairs disjoint if Cayley-Menger volume != 0. Plus the existing
   oracle `verify_balance` on every rational-materialisable state.
5. Negative controls: non-affine node move (must fail), non-PD / singular M
   (refuse), off-unit diagonal (strut length change, refuse), certificate-carry
   mutant on a non-affine edit (reference must catch it), coefficient bound.
6. Perturb -> restore sequence: I -> shears -> I, final identity equals initial.

Scope limits to state in findings: static equilibrium and prestress (super)
stability only; no masses, velocities or dynamic stability; force-density
model, not a constitutive material law; cable rest-length actuation implied
but not modelled.
