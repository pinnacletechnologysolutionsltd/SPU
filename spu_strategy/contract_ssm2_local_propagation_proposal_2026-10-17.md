# SSM-2 proposal: exact local propagation versus a global affine solve

Date: 2026-10-17
Status: ACTIVE — owner approved bounded implementation and one verification attempt
Roles: current agent performs specification, implementation and audit sequentially.

## 1. Scope, predecessor and dimensional review

Preserve SSM-1 and every predecessor unchanged. Qualified source/evidence baseline:
`research/ssm1_baseline_20261017/`. Future implementation is restricted to
`research/ssm2/` and this contract. Leave GPU-W1C and SIM-G1 work independent.
Do not launch or alter their jobs under this proposal.

Use three scalar nodes A,B,C over Q: one independent coordinate per node, with
a three-dimensional global baseline. Three full Q4 nodes would require Q12,
exceeding the existing eight-dimensional limit; they are explicitly out of scope.
This scalar experiment tests relation propagation, not full spatial dynamics.

Freeze at most three distinct undirected edges, no self-edges or parallel edges.
Each edge has exact relation a*x_i+b*x_j=c with a,b nonzero rationals. Allow
at most three exact scalar observations, including contradictory repeated
observations. Zero edge coefficients and malformed graph inputs are rejected,
not silently promoted into new constraint classes. No nonlinear equations,
inequalities, learning, Soul memory, graph discovery or hardware changes.

## 2. Representations and operation semantics

Global baseline: use existing S2-P `full_space(3).observe(A,y)` on all edge and
observation rows. Report its empty/unique/family classification and dimension.
It is the joint solution set; do not replace it with a product of marginals.

Local solver: retain three immutable one-dimensional affine domains, each
exactly Q, a singleton, or empty. Store the original binary edge relationships
persistently and separately. No samples or finite enumeration represent Q.
For an edge a*x_i+b*x_j=c, revise

```
D_i <- D_i intersect ((c - b*D_j)/a)
```

using exact affine image/intersection. Revise the reverse direction analogously.
Use the qualified affine-family operations to represent domains; implement only
the narrow binary propagation rule. No call to the global solve is permitted
inside local propagation or its stopping decision. Compare the paths afterward.

Before iteration, intersect observations into their node domains. Scan edges in
lexicographic endpoint order, first i from j, then j from i, using immediate
updates. Repeat complete sweeps until one causes no changes or a domain empties.
Keep a replayable immutable trace of directed updates with edge, old/new domains
and sweep index. Identical inputs must produce identical order and result bytes.

## 3. Local result contract: do not overclaim completeness

Use distinct labels:

- `CONTRADICTION`: an empty local domain, a sound certificate of no joint solution.
- `SOLVED`: every domain is a singleton and every original edge/observation has
  exact zero residual. This certifies the unique joint state for this model.
- `UNRESOLVED`: a fixed point with at least one Q domain. This does not certify
  global feasibility, positive global dimension, or absence of a unique solution.
- `BUDGET_EXHAUSTED`: unfinished resource outcome, not any consistency conclusion.

Do not reuse FAMILY status to imply a global solution exists when the local
result is unresolved. Trace/result records are research reports, not new SSM-0
register kinds, ABI fields or a change to SSM0_V1 serialization.

## 4. Frozen positive and negative controls

| Case | Edges / observations | Global result | Required local result |
|---|---|---|---|
| Anchored chain | A+B=0, B+C=0; A=11 | unique (11,-11,11) | SOLVED, same exact state |
| Unanchored chain | A+B=0, B+C=0 | dimension-one family | UNRESOLVED, three Q domains |
| Anchored consistent cycle | A+B=0, B+C=0, C-A=0; A=11 | unique (11,-11,11) | SOLVED |
| Anchored contradictory chain | A+B=0, B+C=0; A=11,C=12 | empty | CONTRADICTION |
| Unanchored inconsistent cycle | B-A=0, C-B=0, C-A=1 | empty | UNRESOLVED, three Q domains |
| Unanchored uniquely solvable cycle | A+B=0, B+C=0, C+A=1 | unique (1/2,-1/2,1/2) | UNRESOLVED, three Q domains |
| Repeated contradictory observation | A+B=0, B+C=0; A=11,A=12 | empty | CONTRADICTION |

The last two unanchored cycles are essential. They establish that unary-domain
local consistency is weaker than solving the global relations. A local fixed
point can conceal either an inconsistency or a unique rational solution.
Do not add cycle elimination to make these controls pass as SOLVED; that would
change the local algorithm under investigation.

On the anchored chain, a repeated sweep must propagate information to C through
B without consulting the global solver. Add a reversed edge-input ordering
control: canonical sorting must yield the same trace and result.

## 5. Falsifiable acceptance and software bounds

1. Verify each trace reduction equals the declared directed rule and is a subset
   of its preceding domain. Snapshots of prior states/edges stay unchanged.
2. On every nonempty global control, verify local domains contain the exact
   global marginals at each trace step. This is a soundness test with nonvacuous
   positive controls; it is not a proof from empty global sets.
3. For each CONTRADICTION, verify the global baseline is empty. For SOLVED,
   verify all exact residuals and equality with the global singleton.
4. Keep the local/global outcome discrepancy on unanchored cycles visible in
   the demo/report. Establish limits of the local representation rather than
   treating incomplete propagation as an implementation failure.
5. Reject floats, unknown nodes, zero coefficients, duplicate/self edges,
   dimension overflow and resource exhaustion without mutating previous objects.
6. Require reproducible canonical result/trace JSON in two fresh processes with
   different hash seeds. Represent rational coefficients as reduced decimal-
   string numerator/positive-denominator pairs; no handles or timestamps.

Freeze three nodes, three edges, three observations, 4096-bit completed rational
coefficients and 64 directed revisions. Full->singleton->empty is the only
strict domain descent, at most two changes per node. With at most six directed
revisions per sweep and at most six changed sweeps plus one final sweep, 42
revisions suffice; the 64 cap is conservative. A budget result under the frozen
valid controls is therefore a failed acceptance condition. Resource rejection
is explicit and is not evidence of mathematical inconsistency.

Use ordinary domain objects; do not add a second register file or store. If
SSM-0 handles are used in demonstrations, retain its eight registers, 128-object
cap and independent underlying-store limits. No allocation growth is hidden
behind symbolic notation. Arithmetic temporaries remain host-managed.

## 6. Future implementation and verification commands

After owner authorization, create a small local propagator, an independent
execution-path global baseline wrapper, frozen examples, trace serialization,
focused tests, demo and a check script under `research/ssm2/`. Reuse exact
arithmetic and affine families; do not copy a general elimination engine.
Global and local paths may share the rational representation kernel; do not
claim independent mathematical oracles. The local path must not consult global
rank/solutions during propagation.

Future commands, not runnable until that package exists:

```bash
python3 -m unittest discover -s research/ssm2 -p 'test_*.py' -v
python3 -m research.ssm2.demo
```

Before launch, capture source hashes/archive, including untracked research code;
verify at gate entry and exit. Inspect qualified predecessor terminal markers and
exclude concurrent shared regressions. Proposed budget: one detached attempt,
1800 seconds, no retry or extension. The future check script must run the new
focused tests/demo and SSM-1's existing full check script once.

```bash
tools/run_detached_job.sh \
  --output build/ssm2/local_propagation_20261017_01 \
  --timeout 1800 --notify-desktop \
  -- bash research/ssm2/check_repo.sh
```

Refuse existing output. End turn at LAUNCHED; interpret exactly one terminal
marker in a later invocation. This draft authorizes no implementation/campaign.

## 7. Stop conditions and interpretation

Halt on unsound pruning, a lost original edge, global-solver use inside the local
algorithm, nonzero residual classified SOLVED, mutation on rejection, or scope
expansion to Q12/nonlinear constraints. Preserve the counterexample and report
it; do not silently strengthen the solver or weaken controls.

A pass would establish bounded, exact local deductions through persistent binary
relations and their explicitly demonstrated incompleteness on cyclic networks.
It would not establish a complete distributed constraint solver, novel linear
algebra, neural learning, hardware efficiency or general symbolic intelligence.


## 8. Ratification and implementation record

Owner reviewed/approved the design and requested proceeding within the frozen
scope, including the first-class directed-revision trace refinement. This
supersedes the proposal-only wording in section 6; no technical scope or budget
is expanded. SSM-1 prerequisite has exactly one COMPLETE marker and exit 0;
its 49-file prelaunch source manifest matches current predecessors.

Implementation is restricted to `research/ssm2/` and this contract. There is no
new register/store interface. Local execution imports only scalar affine-family
operations, exact arithmetic and the immutable Problem type, never the global
baseline wrapper. Completed reports retain the original edges and observations,
post-observation initial domains and every directed revision, including no-ops.

Eight focused methods passed before source capture. All seven frozen local/global
outcomes match section 4. Anchored chain needs eight directed revisions; cyclic
negative controls remain unresolved locally after six revisions. Budget exhaustion
is tested by an explicitly reduced budget, not misclassified as contradiction.

The gate captures seven local trace JSON files, a global comparison summary and
trace hashes inside its evidence directory. Trace reports use a research-only
SSM2_LOCAL_RESEARCH_V1 schema; SSM0_V1 is unchanged. Prelaunch provenance captures
research sources and named gate entry points, then checks them at gate entry/exit.
Repository qualification remains pending the one authorized detached campaign.
