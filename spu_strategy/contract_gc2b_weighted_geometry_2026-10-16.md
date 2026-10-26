# GC-2B — Exact Geometric Edge Weighting Contract

**Date:** 2026-10-16  
**Contract ID:** `GC2B-EDGE-WEIGHT-20261016`
**Status:** FROZEN FOR OWNER REVIEW — PROPOSED, NOT RATIFIED  
**Dependencies:** Bounded GC-2A H1/H2 evidence; owner review  
**Authority:** Owner review is complete for this bounded tranche. The current user instruction authorizes exactly one software implementation/run attempt under the command limits below. RTL, ISA, hardware, and SPU architecture changes remain outside scope.

**Revision:** Amendment 03, 2026-10-16. Supersedes the orientation wording in the initial draft; preserves its fixtures, intended observables, and bounded-run controls.

## 0. Command packet for a later, separately authorized run

Owner authorization recorded 2026-10-16. The single bounded software experiment command is:

```bash
tools/run_detached_job.sh \
  --output build/gc2b_qualification/20261016_run01 \
  --timeout 300 \
  --notify-desktop \
  -- timeout --signal=TERM 60s python3 software/tests/test_gc2b_weighted_covariance.py \
       --manifest software/tests/fixtures/gc2b_weighted_cycle.json \
       --report build/gc2b_qualification/20261016_run01/report.json
```

One attempt only; each command is capped at 60 seconds and the detached job at 300 seconds. A timeout, failure, or unavailable result consumes the attempt. No retry or extension without renewed authorization. This is the authorized command; launch status and terminal result are recorded separately.

## 1. Objective and scoped files

**Hypothesis:** Exact positive weights attached to unoriented substrate edges can be kept independent of law coefficients, while parity transports the weights and exchanges the two directed operators. Consequently, covariance holds even when the weighted substrate has no orientation-preserving isomorphism to its mirror; internal parity symmetry is defined only when such an isomorphism exists.

**Measured observables:** (1) exact covariance residual, the matrix difference between the two sides of the covariance identity; (2) exact internal-symmetry commutator (QF-FQ) when Q exists; (3) admissible-rotation enumeration; and (4) paired trajectory equality through eight steps under correctly transported initial states. Exact zero/nonzero is determined in K. Runtime and coefficient sizes are recorded as descriptive data only, not as evidence of an architectural advantage.

If a later implementation is separately authorized, limit new files to:

- `software/lib/gc2b_weighted_cycle.py` — exact fixture, field, transport, and matrix definitions.
- `software/tests/fixtures/gc2b_weighted_cycle.json` — frozen fixture and expected-check manifest.
- `software/tests/test_gc2b_weighted_covariance.py` — exact exhaustive checks and report writer.

Do not edit existing CPU/GPU RTL, simulator profiles, ISA files, generated files, or qualified SPU arithmetic. Do not import the prototype into the maintained SPU implementation.

## 2. Exact domain and substrate

Use (K=\mathbb Q(\sqrt3)), with canonical elements (p+q\sqrt3), (p,q\in\mathbb Q), and the fixed real embedding (\sqrt3\mapsto+\sqrt3). Use the H1-qualified exact oracle/profile for equality, operations, and positivity. No floating-point decision is permitted.

The substrate is the oriented four-cycle (C_4):

- Vertices (V=\mathbb Z/4\mathbb Z).
- Unoriented edges (e_i=\{i,i+1\pmod4\}).
- The stored chart order on both the original and mirrored copies is (0\to1\to2\to3\to0). This is an indexing convention used to define the operators on each copy; it is not a claim that the mirrored embedding preserves spatial orientation.
- The orientation-preserving equivalence group (\mathcal H) consists exactly of cyclic rotations (i\mapsto i+k\pmod4), preserving incidence, cyclic order, boundaries, labels, and weights.
- There are no boundary cells and no additional vertex or edge labels in these fixtures. Parity transport is (P(i)=-i\pmod4); it reverses orientation relative to the stored chart and maps (e_i) to (e^P_{-i-1}). It transports edge weights by (w^P_{-i-1}=w_i), while preserving incidence. The mirrored copy retains the same indexed chart order; do not reverse its stored cyclic order a second time. This is the sole orientation reversal in the covariance construction. It is not Galois conjugation.
- The state space is (M_G=K^4). State transport (P_*:M_G\to M_{G^P}) is the exact vertex permutation induced by (P), hence a (K)-linear bijection.
- An admissible (h), when it exists, is an orientation-preserving weighted-structure isomorphism (h:G^P\to G) induced by one of the four rotations; it preserves incidence and transported weights. Its state map is (h_*:M_{G^P}\to M_G). The composite (Q=h_*P_*:M_G\to M_G) is orientation-reversing. Enumerate every admissible rotation; for the uniform fixture, test internal symmetry for each induced Q.

Weights are exact positive substrate attributes on unoriented edges. They are not called metric lengths, and no physical metric interpretation is claimed.

### Frozen fixtures

1. **Uniform control:** (w=(1,1,1,1)). The mirrored weighted cycle admits an (h\in\mathcal H).
2. **Weighted substrate:** (w=(1,2,3,2+\sqrt3)), ordered by (e_0,e_1,e_2,e_3). All weights are positive and pairwise distinct under the fixed embedding. The reflected sequence is not a cyclic rotation of the original, so no admissible (h) exists. Exhaust all four rotations rather than relying on the sequence argument alone.
3. In both fixtures define (w^P(P(e_i))=w(e_i)). Do not conjugate the coefficients during parity transport.

### Frozen orientation convention and basis check

Write (e_i) for the standard basis vector at vertex (i), and define the state transport componentwise by ((P_*x)_j=x_{-j}). On each copy, define (T_L) as advance in its stored chart and (T_R) as retreat in that same stored chart, using the equations below. The geometric parity transport reverses orientation once; the mirrored copy is not separately re-indexed or reoriented.

Check the operator-exchange identities on the single basis vector (e_0) before any broader finite check. The edge-weight transport gives (w^P_3=w_0) and (w^P_0=w_3). Thus:

- ((P_*T_L^{G,w}e_0)=w_0e_3=(T_R^{G^P,w^P}P_*e_0));
- ((P_*T_R^{G,w}e_0)=w_3e_1=(T_L^{G^P,w^P}P_*e_0)).

This fixes the direction of each map and demonstrates that the mirrored chart order must not be reversed again. The implementation must still check both identities on all four basis vectors; linearity then establishes the corresponding operator identities for the finite (K)-vector spaces.

## 3. Operators and required identities

For a state (x\in K^4), define edge-weighted directed transports by

\[
(T_L^{G,w}x)_{i+1}=w_i x_i,\qquad
(T_R^{G,w}x)_i=w_i x_{i+1}.
\]

The operators are (K)-linear matrices. On the mirrored substrate, use the transported weights and the same indexed chart order. Require the exact operator-exchange identities

\[
P_*T_L^{G,w}=T_R^{G^P,w^P}P_*,\qquad
P_*T_R^{G,w}=T_L^{G^P,w^P}P_*.
\]

For law coefficients (a,b\in K), define

\[
F_{a,b}^{G,w}=aT_L^{G,w}+bT_R^{G,w}.
\]

Then check

\[
P_*F_{a,b}^{G,w}=F_{b,a}^{G^P,w^P}P_*.
\]

For each admissible (h), check internal parity symmetry using (Q=h_*P_*):

\[
QF_{a,b}^{G,w}=F_{a,b}^{G,w}Q.
\]

The orientation-preserving map (h_*) preserves the named left/right operators; the parity transport exchanges them exactly once. Therefore (QF_{a,b}=F_{b,a}Q). Internal symmetry (commutation with (F_{a,b})) is expected for (a=b); for unequal coefficients the commutator is expected to be nonzero when (T_L\ne T_R). Do not encode a second left/right swap in the mirrored operator definitions.

Run these distinct controls:

- **Parity-neutral law:** (a=b=1), on both substrate fixtures.
- **Law-bias control:** (a=2+\sqrt3,\ b=1), then exchange coefficients under parity and verify covariance.
- **Internal symmetry:** report only for the uniform fixture with an admissible (h). For the nonuniform weighted fixture, report `NOT_APPLICABLE_NO_ADMISSIBLE_H`; covariance does not imply internal symmetry.

Use exact matrix equality, or apply both sides to all four basis vectors. Define the internal-symmetry observable as the matrix commutator (QF-FQ); do not infer broken operator symmetry from unequal raw trajectories launched from different states. For each applicable (Q), check the paired trajectories through eight update steps from the frozen state (1,0,√3,2). Under the parity-neutral law compare (F^n(Qx)) with (QF^n(x)); under the law-biased control compare (F_{b,a}^{G,w,n}(Qx)) with (QF_{a,b}^{G,w,n}(x)). For substrate covariance, compare (F_{b,a}^{G^P,w^P,n}(P_*x)) with (P_*F_{a,b}^{G,w,n}(x)). Never compare either mirrored trajectory with the untransformed trajectory from (x) as a symmetry criterion. The frozen state is not invariant under the tested parity maps; omitting its required transport is a separate negative control and must be detected at step zero. State-level chirality remains outside scope. Also include a negative control that deliberately fails to transport one edge weight: add exactly 1 to the transported weight on (e_0) in (G^P), leave all other data fixed, and require a nonzero covariance residual.

Freeze these independent negative controls:

- `NC_DOUBLE_SWAP`: deliberately apply an additional left/right swap to the mirrored operator names. On input (e_0), require the first operator-exchange identity to fail; the correct result is supported on (e_3), while the double-swapped result is supported on (e_1).
- `NC_WEIGHT_TRANSPORT`: add exactly 1 to the transported weight on mirrored edge (e^P_0), leave all other data fixed, and check the second operator-exchange identity on input (e_0). Require a nonzero exact residual; the correct coefficient is (w_3), while the corrupted coefficient is (w_3+1).
- `NC_STATE_TRANSPORT`: omit (P_*) on the mirrored initial state and compare at step zero with the correctly transported pair. For the frozen state (x=(1,0,√3,2)), require the mismatch to be detected; the correctly transported state is (P_*x=(1,2,√3,0)).

These are separate fault injections; do not combine them in one case. The substrate fixture checks remain independent of these controls.

## 4. Manifest and evidence rules

Freeze the expected fixture/check IDs in the fixture JSON before execution. At runtime:

1. Exhaustively enumerate all four candidate rotations for each fixture and record the result for (h).
2. Execute covariance on both fixtures. Execute `NC_DOUBLE_SWAP` and `NC_WEIGHT_TRANSPORT` independently on each fixture, and `NC_STATE_TRANSPORT` on the uniform fixture; require detection for every injected defect.
3. Execute internal-symmetry commutator checks for every admissible (h) on the uniform fixture; record the no-(h) status for the weighted fixture.
4. Compare the set of declared fixture IDs and required check IDs with the set actually executed. Fail the run if they differ in either direction.
5. Write the fixture definitions, exact weights, (h) enumeration, covariance residuals, internal commutators, trajectory-pair results, negative-control results, executed manifest, frozen initial state, source hashes, and command/result metadata to the report.

A pass qualifies only these finite fixtures and exact operators. Record failures as results; do not alter fixture definitions or expected manifests after seeing outcomes.

## 5. Acceptance conditions

- Both edge-weight vectors are exactly positive and canonically represented in (K).
- The uniform control admits (h); the nonuniform weighted control does not, with all rotations exhaustively checked.
- Exact covariance passes for equal and unequal law coefficients on both fixtures.
- Internal symmetry passes only where an admissible (h) exists and the law is parity-neutral; unequal law coefficients fail internal symmetry as expected and pass covariance after coefficient exchange.
- All three independent negative controls (`NC_DOUBLE_SWAP`, `NC_WEIGHT_TRANSPORT`, `NC_STATE_TRANSPORT`) are detected.
- A deliberate second left/right swap on the mirrored operators is detected as a convention-error negative control; it must fail the e_0 basis identity above.
- The missing-state-transport negative control is detected, and correctly transformed seed pairs satisfy the specified trajectory identities.
- Declared fixture/check IDs equal executed IDs exactly.
- The report distinguishes substrate weights, law coefficients, parity covariance, and internal symmetry; it records the fixed initial state and states that state-level chirality is outside this experiment's scope.

Any unmet item leaves GC-2B unqualified. A pass does not ratify GC-2A/GC-2B, establish a general theorem beyond the finite model, establish a physical metric or physical chirality, or authorize an SPU extension.

## 6. Roles and stop conditions

- **Spec Author:** freeze this mathematical model and manifest.
- **Halt-and-Flag Implementer:** after separate authorization, halt if the implementation cannot represent (K) exactly, if the weighted maps are not (K)-linear, or if the mirror/weight transport types are ambiguous.
- **Integration Auditor:** after separate authorization, verify the exact fixture manifest, hashes, one terminal runner marker, and bounded outcome. Do not run unrelated RTL, synthesis, or repository-wide gates for this isolated software experiment.

Stop on any undefined comparison, missing fixture check, manifest mismatch, covariance mismatch, unexpected isomorphism, or negative control that fails to detect the injected defect. Report operator symmetry through the commutator separately from trajectory comparisons; a raw difference between trajectories from different initial states is not a symmetry failure. No repair-and-rerun is permitted under the single-attempt budget without renewed authorization.
