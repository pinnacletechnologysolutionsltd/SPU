# SSM-1 proposal: two correlated symbolic state families

Date: 2026-10-17
Status: ACTIVE — owner approved bounded software implementation and one campaign
Roles: current agent performs specification, implementation and audit sequentially.

## 1. Scope and frozen predecessor

Preserve SSM-0 and its dependencies. Baseline source/evidence archives and hashes:
`research/ssm0_baseline_20261017/`. Retain its documented post-run provenance
limit. This proposal creates no new instructions, serialization version or SSM-0
interface. Future code is scoped to `research/ssm1/` and this contract only.

Use two Q4 nodes A,B, represented jointly in Q8. Store this joint Family via
SSM-0's existing public store. Use existing MAP/image/observation operations for
8D actions and local marginal projections. Never treat two independent marginals
as the authoritative joint state. Exclude Soul, learning, nonlinear constraints,
probability, lattice domains, GPU and RTL.

## 2. Frozen mathematical case

Order coordinates (xA,yA,zA,hA,xB,yB,zB,hB). Start with

```
a = (1,2,3,0,4,5,6,0)
b = (0,0,0,1,0,0,0,-1)
S0 = a + span_Q(b)
L0 = (0,0,0,1,0,0,0,1)
L0*x = 0
```

Each node's marginal is a one-dimensional family, but the joint family has
dimension one, not two. Their Cartesian product loses hA+hB=0.

Construct local symbolic B transformations using the unchanged SSM-0 public
transform API. Their evaluated block-diagonal Q8 action E=diag(B,B) is invertible
and self-inverse. Materialization can use the existing public words evaluator;
do not access predecessor private storage or change apply's Q4 contract.
Store E as a MAP and act on the joint family through existing project/image
semantics. Projection here means general linear image; E is separately certified
invertible. Do not call the machine's inverse operation on a MAP.

The evolved family is

```
S1 = (0,2,3,1,0,5,6,4) + span_Q((1,0,0,0,-1,0,0,0))
L1 = (1,0,0,0,1,0,0,0)
L1*E = L0
```

This transports a relation: L1=L0*E^-1. The unchanged expression L0*x=0 is
not generally preserved. Explicitly distinguish transported constraints from
fixed invariants; do not label all reversible updates constraint-preserving.

## 3. Required acceptance branches

1. Project the joint family onto each node. Both remain unresolved initially.
2. Evolve the joint family by E. Observe node A's visible coordinates as
   (11,2,3). The joint family becomes unique; node B's visible coordinates
   must be (-11,5,6), although B was not directly observed.
3. Apply E^-1 to recover the unique initial state
   (1,2,3,11,4,5,6,-11).
4. On a fresh S1 branch, observe only yA=2. Keep a one-dimensional family.
5. Observe A=(11,2,3) and B=(7,5,6) on another branch. Each observation is
   feasible against its original marginal; the conjunction is empty in the
   joint family. This is the essential pairwise-versus-joint negative control.
6. Observe A=(11,2,3), B=(-11,5,6): unique joint state, not empty.
7. Show that the product of the marginals wrongly admits hA=11,hB=7 at the
   initial level; that product is a deliberately weaker baseline, not a solver.

## 4. Sequences, baselines and limits

Compose at most eight frozen local steps, using only existing Q4 generators
and their certified inverses. Lift each to block diagonal Q8. For every step:

- Check two-sided inverse identities by exact matrix multiplication.
- Transport link rows by the inverse map and verify L_next*E_step=L_previous.
- Check joint family membership in the transported link set through exact image.
- Compare composed and stepwise family images and reverse-order inverse recovery.
- Compare sequential evolution/observation with stacked initial-state equations.
- Retain previous immutable family/observation objects and empty/unique/family
  distinctions. No arbitrary witness selection, graph search or convergence claim.

Use a direct S2-P joint affine solve as an independent execution-path baseline;
it shares the rational elimination kernel, so do not call it an independent
mathematical oracle. Freeze explicit expected states and residual identities as
additional controls. A network of two nodes is the entire scope, not a generic
graph engine. A transported linear link is not nonlinear Gram-zero propagation.

Keep predecessor software budgets: eight registers, 128 public adapter objects,
64-symbol local transformations, at most eight joint coordinates, 4096-bit
completed rational coefficients. Reject overflow and dimensions without mutations.
Retain SSM0_V1 semantic serialization and require reproducible result bytes.

## 5. Future command-first implementation and verification

After owner authorization, create `research/ssm1/` with a small network adapter,
frozen example/demo and tests; reuse SSM-0's public APIs. Do not copy its store,
rewrite predecessors, or add a nonlinear solver. Record source hashes before
launch, including untracked code, to avoid the prior provenance gap.

Commands below are proposed and not runnable until that package exists:

```bash
python3 -m unittest discover -s research/ssm1 -p 'test_*.py' -v
python3 -m research.ssm1.demo
```

Proposed verification budget: one detached attempt, 1800 seconds, no retry or
timeout extension. Inspect predecessor terminal evidence before launch and
exclude concurrent shared regressions. The future check script must execute
SSM-1 tests/demo followed by SSM-0's existing full check script exactly once.

```bash
tools/run_detached_job.sh \
  --output build/ssm1/correlated_families_20261017_01 \
  --timeout 1800 --notify-desktop \
  -- bash research/ssm1/check_repo.sh
```

Refuse existing evidence output. End turn at LAUNCHED; inspect exactly one
terminal marker in a later invocation. No campaign is authorized by this draft.

## 6. Stop conditions and claims

Halt on lost cross-node correlation, local-versus-joint feasibility confusion,
undeclared changes of domain, failing exact identities, mutations on rejection,
or attempts to expand beyond Q8. Report counterexamples; do not relax acceptance.

A pass would demonstrate exact correlated-family evolution and observation
through the existing machine interface for this bounded affine system. It would
not establish new observability theory, autonomous local message passing,
general constraint networks, neural learning, new physics or hardware efficiency.


## 7. Owner ratification and prelaunch record

The owner approved the design and authorized the frozen implementation scope
and one 1800-second campaign. This supersedes the proposal-only wording in
section 5 without expanding any mathematical or resource boundary.

SSM-0 source hashes match the preserved baseline. SSM-0 and family-store
prerequisites each have exactly one COMPLETE marker and exit 0. An unrelated
GPU repository regression was active during preparation; do not launch this
campaign until its terminal evidence and shared-regression availability permit.

Implemented `research/ssm1/` only, plus this contract update. Eight focused test
methods PASS before launch. The demo infers B=(-11,5,6) from A=(11,2,3), then
recovers (1,2,3,11,4,5,6,-11). Separate branches distinguish unresolved, unique
and empty joint families; a marginal-product control loses the link.

A read-only Step compiler uses SSM-0 public local transformation payloads and
its public words evaluator to construct/certify block-diagonal Q8 maps. Existing
SSM-0 MAP instructions publish images and observations one instruction at a
time. There is no multi-instruction transaction or new register/store interface.
Every individual rejected instruction retains inherited failure atomicity.

Prelaunch provenance is kept under `research/ssm1/provenance/`: source hashes,
source archive, metadata and artifact hashes. The gate logs the manifest/archive
digests and checks research source hashes before and after the regression.
This captures the research sources and named gate entry points, not every
external tool, full regression input or system library. Do not alter captured
sources between provenance capture and campaign completion. Repository
qualification remains pending the campaign's own terminal marker.
