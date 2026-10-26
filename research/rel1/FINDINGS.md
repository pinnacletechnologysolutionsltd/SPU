# REL-1 — Native relational state execution (bounded experiment)

2026-10-20. Class A host-only (AGENTS.md §4.3). New files only under `research/rel1/`; PHY-R1/R2/R3 and SSM-7 are imported
or mirrored read-only and unchanged. Shared dependencies declared: `exact.py` kernels (LDL, nullspace), `geometry.py`
(fixture constants, metric admission, Cholesky materialisation). No ISA, simulator, RTL or FPGA change.
**Result: representational capability CONFIRMED; efficiency advantage NOT shown (in this cost model it is worse).**
8 test groups pass (5.7 s); PHY-R3 review passes (0.9 s).

```bash
timeout 120 bash -c 'ulimit -v 1048576; python3 -B -I research/rel1/review_phy_r3.py && python3 -B -I research/rel1/test_rel1.py'
timeout 60  bash -c 'ulimit -v 1048576; python3 -B -I research/rel1/report.py'
```

## Machine (SSM-7 semantics over metric states)
Six opcodes: TRANSFORM metric, MOVE (≤2 nodes, non-affine), VALIDATE, QUERY, REUSE, OBSERVE. Bounds 32 commands, 8 transitions,
9 states, 36 certificates. Permanent handles; content id = hash of all 66 pairwise quadrances (so a restored geometry has a
new handle and the same id). Failed commands consume a slot and leave all stores unchanged (snapshot-tested). Certificates:
realisable, strut_lengths, equilibrium (squared law, admissible rest), stability (PHY-R3 second variation). UNRESOLVED means
"cannot decide" (missing evidence, or stability undefined off-equilibrium); refusals use SSM-7's fixed codes plus OUT_OF_FIELD.

Backends: **relational** keeps (P0, M) and evaluates everything from M (ΩP = 0, ε-space Hessian); coordinates appear only in
OBSERVE and MOVE-from-metric. **Conventional** materialises x = A P at every transition and uses explicit node force sums, the
x-space Hessian Ω⊗I + Σ2κuuᵀ, and an exact linear solve for affinity. Certificates carry across states only if dependencies
hold (equilibrium: affine image + admissible cables; strut_lengths/realisable: recomputed; stability: same geometry, or the
PHY-R3 lemma when the machine flag is on; identical geometry id rebinds anything, as in SSM-7).

## PHY-R3 review (done before use)
Method-independent, not author-independent (the same agent wrote PHY-R3): the closed-form second variation equals an exact
5-point derivative of the energy evaluated directly (reference and m₁₂ = 3/5); strut-reaction and κ-vs-2κ mutants fail it; PD
modulo rigid motions re-derived by a rigid-penalty LDL with REL-1's own kernel (rank 30, nullity 6, cross-checked against
PHY-R1's LDL); Ω PSD rank 8 and ΩP = 0 re-confirmed. REL-1 relies on the **squared law only**; Hooke was corroborated only
numerically (Decimal) and is not used.

## Results
- **Agreement.** The 30-command mixed program P1 gives identical full results, receipts and post-state in both backends, matching an
  expected table written from the design: refusals DEPENDENCIES_CHANGED (stability across different metrics, equilibrium to a
  non-affine state), INVALID_STATE (VALIDATE of the moved state), STALE_STATE, INADMISSIBLE_EDIT (non-PD, off-unit diagonal); a
  moved state is EXACT-not-equilibrium and its stability is UNRESOLVED. Observed coordinates satisfy PHY-R2's coordinate force
  sums and the PHY-R1 oracle (BALANCED); PHY-R3's code independently certifies the stable states.
- **Capability gap, explicit.** With coordinates restricted to Q (d=1), TRANSFORM to m₁₂ = 1/2 (needs √3) or M₂ (needs √2)
  COMMITS relationally and is queried exactly (equilibrium and stability True), while the conventional backend REFUSES with
  OUT_OF_FIELD, so its later commands see BAD_HANDLE. Both refuse OBSERVE of the half-metric state in Q. With d=3 the half-metric
  materialises and both agree exactly (Q(√3) receipts identical); M₂ stays relational-only.
- **Certificate reuse.** The chain program P3 (lemma on) carries all four certificates across six metric transitions with one
  observation; every lemma-reused stability certificate agrees with a fresh exact recomputation (6/6, both backends); with the
  lemma off, stability reuse is refused. Dropping the dependency check (mutant) wrongly carries equilibrium to the moved state,
  and an independent query on it returns False.
- **Controls.** Non-PD, singular, off-unit-diagonal, asymmetric, coefficient-bound metrics and bad schemas are refused atomically;
  state, certificate, transition and command limits are enforced in both backends; repeated runs are bit-identical.

## Measured (scalar-op counts from the shared kernels; a model, not hardware cost)
| Program | Backend | Materialisations | Scalar ops | State scalars | State bits |
|---|---|---:|---:|---|---:|
| P1 mixed (30 cmds, d=1) | relational | 4 | 53,428 | 6,6,36,6,6 | 178 |
| | conventional | 4 | 41,030 | 36 each | 543 |
| P3 chain (32 cmds, lemma) | relational | **1** | 31,775 | 6 each | 106 |
| | conventional | **7** | 23,435 | 36 each | 1,184 |

## Capability versus efficiency
- **Capability (confirmed):** the relational machine decides metric, equilibrium and stability questions for states the
  coordinate backend cannot represent in the chosen field, and matches it exactly everywhere both can answer.
- **Fewer materialisations and smaller state (confirmed, workload-dependent):** P3 needs 1 materialisation vs 7 and ~11× fewer
  state bits; P1 needs the same 4 because it observes and moves often.
- **Less work (FALSIFIED in this model):** the relational backend used ~1.3× more counted scalar ops in both programs
  (the ε-form multiplies by M and the 66-quadrance content id costs more than the conventional pairwise squares). The counts do not weight
  the exact square-root tests that materialisation needs, so they understate conventional cost; that weighting was not measured.
- **Not established:** hardware benefit, behaviour on larger programs, Hooke-law use, anything about dynamics.

## Limits
Shared kernels, constants and Cholesky code make the backends independent in formulation, not in every line. Unreachable divergence: a
translated affine image would be "affine" to the conventional backend but not relational; no command can create one. The lemma reuse
rests on PHY-R3's whole-path proof (checked here on six states only). Stopped after the bounded experiment.
