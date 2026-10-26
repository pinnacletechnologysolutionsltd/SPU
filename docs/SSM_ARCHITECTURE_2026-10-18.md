# Symbolic state machines: SSM-0 through SSM-3

Status: consolidated account of four repository-qualified, bounded software
experiments. Date: 2026-10-18. No SSM-4, unified processor ISA or symbolic FPGA
implementation is introduced by this document.

SSM investigates a small execution vocabulary whose objects denote transformations,
affine possibilities and exact relationships. The progression changes what the
software retains: individual symbolic maps, correlated sets, local domains, then
relations with replayable derivations. It is established rational linear algebra
expressed through explicit persistent-state and verification contracts.

## Qualified components and evidence

Each row has its own COMPLETE/exit 0 record and 244 repository passes, zero
failures. Focused counts below are tranche tests, not additional repository totals.

| Tranche | Demonstrated software behavior | Focused tests | Primary record |
|---|---|---:|---|
| SSM-0 | Typed adapter connects symbolic composition, family images, projection, observation and recovery | 8 | [906-second qualification](../build/ssm0/integration_20261017_01/result.json) |
| SSM-1 | Two Q4 nodes share a Q8 family; retained correlations support cross-node inference and constraint transport | 8 | [996-second qualification](../build/ssm1/correlated_families_20261017_01/result.json) |
| SSM-2 | Three scalar domains propagate through binary relations; cyclic incompleteness stays explicit | 8 | [928-second qualification](../build/ssm2/local_propagation_20261017_01/result.json) |
| SSM-3 | Persistent sparse equations, exact original-row certificates and independently replayed complete reduction | 14 | [990-second qualification](../build/ssm3/relational_messages_20261018_01/result.json) |

S1 transformation words, S2-P affine projection/observability, the typed family
store and G3 rational isometries are independently qualified predecessors.
SSM-0 adapts their APIs; SSM-1 reuses it. SSM-2 and SSM-3 add separate bounded
research executors. They are not one generalized VM with interchangeable opcodes.
The S3 family-store name is unrelated to the previously suggested neural S3 study.

## State types and exact domains

| Object | Meaning and implementation boundary |
|---|---|
| S1 TRANSFORM | Immutable reduced execution-order word over R,r,H; adjacent inverse cancellation is sound but not a complete semantic normal form |
| FAMILY | Canonical origin plus row basis over Q^n, or explicit empty set; denotes all rational parameter choices |
| MAP | Exact matrix with declared input/output dimensions; rectangular projection is not implicitly invertible |
| OBSERVATION | Exact matrix/measurement pair defining an affine intersection |
| SSM-2 Problem/domain | Persistent binary edges and scalar Q/point/empty domains; marginals do not encode all joint correlations |
| SSM-3 Message | Sparse equation, original-row certificate, immutable ID and backward parent references |
| SSM-3 active system | References to a complete equation system, updated only by replayable invertible row operations |

An affine family a+span_Q(B) represents infinitely many possibilities without
enumerating them. Canonical RREF basis and reduced origin make equality decidable
within this supported class. The representation is a set, not a probability
distribution, sampled population or model of measurement uncertainty.

Four redundant Quadray coordinates have only three independent zero-sum spatial
coordinates. S1 VALUE removes gauge. Independent Q4 families must never pass
through that canonicalization. SSM-0 imports only explicitly tagged full 4x4 S1
transformation actions, retaining independent coordinates. SSM-1 uses Q8 for two
Q4 nodes. SSM-2/3 use three scalar variables, not three full spatial nodes.
No E8, surd, Pell or Golden Core domain has been silently added to these executors.

## Operations and observable outcomes

SSM-0 stores typed local handles in eight registers. Compose(a,b) means a after b;
composition/inversion manipulate words without evaluating coordinates. Applying
an operation materializes an exact matrix and images the entire family. Projection
may lose information; observe intersects a family with an exact measurement.
Resolve reports empty, unique or family without choosing an arbitrary representative.

S2-P demonstrates why observing a projection is not always enough to predict it.
For P(x1,x2,x3,h)=(x1,x2,x3), swapping x1 and h exposes previously hidden variation.
For linear surjective P, observable dynamics close precisely when T(ker P) is
contained in ker P. Retaining hidden state permits reconstruction from sufficient
observations; projecting and discarding it does not.

SSM-1 retains hA+hB=0 in its joint family. Reversible evolution transports the
relation to xA+xB=0. Observing xA=11 implies xB=-11, while two individually feasible
observations can be jointly contradictory. In general a row constraint L becomes
L'=L*E^-1; L'*E=L. This transports its expression. G3's shared-isometry result
instead preserves specified quadrances, inner products and Gram values. These
are different claims, as is time-reversal covariance under a separately declared J.

SSM-2's directed domain revision is D_i intersect ((c-b*D_j)/a). Its outcomes are:

| Outcome | Permitted conclusion |
|---|---|
| SOLVED | Singleton domains satisfy every original equation/observation |
| CONTRADICTION | Empty domain proves no joint solution |
| UNRESOLVED | Fixed point; global feasibility and uniqueness remain unknown |
| BUDGET_EXHAUSTED | Unfinished computation; no consistency conclusion |

A+B=0,B+C=0,C+A=1 has unique solution (1/2,-1/2,1/2), yet unary propagation
leaves all domains Q. B-A=0,C-B=0,C-A=1 is inconsistent and leaves the same local
fixed point. SSM-3 resolves both by combining relational rows, not by changing
SSM-2 or treating its result as an error.

## What a proof establishes

For original augmented equations r_i, every SSM-3 message has exact certificate
lambda with r=sum(lambda_i*r_i). This certifies a consequence of those inputs.
It does not establish that the inputs describe physical reality, nor that a
selected subset of derived rows retains all original constraints.

Complete-system equivalence therefore has a second check. The verifier rebuilds
inputs from the frozen Problem, independently reconstructs each parent operation,
checks original-row combinations and replays active references from every original
row. Nonzero scales and distinct-target elimination retain equivalence; no rows
may disappear. It checks the final reduced structure, affine dimension and all
original origin/basis residuals. A contradiction requires certified normalized 0=1.
The JSON loader reconstructs these objects and does not trust a stored pass flag.

Ten durable proofs include the two cycles, a correlated family, a redundant 0=0,
nonunit rational coefficients, repeated conflicting observations and all Q3.
Tamper tests reject altered rows/certificates/inputs, forward or missing parents,
dropped active rows and false classifications. This is a narrow rational-equation
proof system sharing representation code, not a general theorem prover or a
formal verification of Python and the complete operating system.

## Resource, identity and failure semantics

SSM-0/1 retain eight registers, 128 public objects and separate underlying-store
caps; transformations have 64 expanded symbols and family dimension is at most
eight. SSM-2 has three nodes/edges/observations and 64 directed revisions. SSM-3
has three variables, six inputs, 64 messages and 64 row operations. Completed
rational coefficients/certificate entries have a 4096-bit guard.

Fraction arithmetic is exact within admitted work; encoding sizes can grow.
Coefficient overflow and allocation/revision limits are explicit resource outcomes,
not mathematical contradictions. Validation precedes publication and failed
operations preserve prior objects. These are host-managed software guards, not
fixed hardware latencies or hard memory isolation.

Handle identity, syntactic word identity and semantic equality differ. Family
and proof reports use deterministic rational JSON. SSM0_V1 object bytes,
SSM2_LOCAL_RESEARCH_V1 traces and SSM3_PROOF_RESEARCH_V1 proofs are distinct formats;
none is a ratified binary machine encoding or cross-process handle ABI.

## Reproduce and reuse

From repository root:

```bash
python3 -m research.ssm0.demo
python3 -m research.ssm1.demo
python3 -m research.ssm2.demo
python3 -m research.ssm3.demo
python3 -m research.ssm3.verify_artifact build/ssm3/relational_messages_20261018_01/proofs/unique_cycle.json
```

Component contracts and limits: [SSM-0](../research/ssm0/README.md),
[SSM-1](../research/ssm1/README.md), [SSM-2](../research/ssm2/README.md),
[SSM-3](../research/ssm3/README.md). Full check scripts are historical campaign
recipes; do not blindly rerun scripts with fixed artifact paths. New qualification
needs a new authorized contract, budget and fresh output directory.

The [SSM-3 Class A index and restored replay](../research/ssm3_baseline_20261018/README.md)
preserve its prelaunch sources, ten proofs and campaign evidence under the
[retention policy](BUILD_ARTIFACT_RETENTION.md). SSM-0's baseline was captured
post-run and retains that provenance limitation. Later source manifests were
captured before launch and checked at entry/exit, within their declared scopes.
External archival placement and two independent storage copies remain pending;
no deletion is authorized.

## Hardware implications and the next design boundary

These prototypes identify possible hardware work: tagged immutable references,
bounded exact arithmetic, explicit failure/status channels, sparse row execution
and proof replay. None establishes useful register widths, memory architecture,
cycle counts, energy costs or an ISA allocation. The hypothetical 128-bit symbolic
descriptor remains illustrative. A certificate engine would still need source
admission rules, overflow behavior, memory ownership and independent qualification.

The next integration experiment is [SG-0: symbolic state to GPU geometry](SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md),
using Python and the existing T1d scene boundary. [SSM-4 design](SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md)
starts now; implementation waits for the frozen SG-0 interface and identified
requirements, then needs its own qualification before C++/FPGA promotion.
The [SOM interface design](SOM_SYMBOLIC_INTERFACE_DESIGN_2026-10-18.md) follows:
adaptive ordering remains separate from exact proof validation. No bridge,
SSM-4, learning, Soul or symbolic FPGA implementation is introduced here.
