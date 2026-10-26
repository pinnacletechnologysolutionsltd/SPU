# QSG-0 mathematical specification: rational rectangle fan

Date: 2026-10-19. Status: owner review PASS for the experimental direction;
geometry amendment incorporated; authorized isolated software fixture completed.
Research acceptance: **0/5 verified**, pending independent result review.
See [software results](QSG0_SOFTWARE_RESULTS.md). QSG-0 is now FROZEN.

Review record: the owner independently reviewed the specification and requested
the rectangle naming correction and perpendicular-edge invariant below.
This records specification review, not a completed software or research gate.

## Review commands and scope

Run from the repository root:

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/QSG0_MATHEMATICAL_SPECIFICATION.md docs/QSG0_GENERATIVE_GEOMETRY_RESEARCH.md
```

Review this specification before implementing an isolated software oracle.
Preserve [QSG-0's priority boundary](QSG0_GENERATIVE_GEOMETRY_RESEARCH.md).
Change no production software, shared runner, RTL, ISA, hardware build or timing
constraints. This deliverable launches no experiment or hardware campaign.
The separate execution contract and results note record the authorized software
run. The definitions below remain the reviewed mathematical contract; evidence
and its limits are recorded separately in that results note.

## 1. Fix topology and metric

Use five labeled vertices O,A,B,C,D and oriented faces
(O,A,B), (O,B,C), (O,C,D), (O,D,A).
Use edges OA,OB,OC,OD,AB,BC,CD,DA. The boundary cycle is A,B,C,D,A.
AC and BD are diagnostic diagonals, not mesh edges. Connectivity never changes.

Use the Euclidean dot product on Q², embedded in Q³ with z=0.
Define Q(X,Y)=(X-Y)·(X-Y). Fix a dimensionless unit scale.
Let the intrinsic metric parameter be u with 0<u<4:

```text
Q(O,A)=Q(O,B)=Q(O,C)=Q(O,D)=1
Q(A,B)=Q(C,D)=u
Q(B,C)=Q(D,A)=4-u
```

Store u as the minimal relationship descriptor, with topology and schema
version fixed. The equivalent eight-edge metric is a separate representation
for comparison; charge its storage separately. On expanded-metric import,
check all eight values against this schema; refuse inconsistent redundancy.
This describes a restricted one-parameter family, not arbitrary patch metrics.

## 2. Fix reconstruction and orientation

Anchor O=(0,0), A=(1,0), C=(-1,0), and require B to have positive y.
Derive c=1-u/2, r=1-c², s=positive_sqrt(r), then set
B=(c,s), D=(-c,-s). This fixes a planar embedding and its reflection choice;
planarity and anchors are additional embedding constraints, not intrinsic data.
Recover u from coordinates as Q(A,B) when testing the reverse conversion.

For 0<u<4, r=u(4-u)/4>0. Each ordered face has doubled signed area s;
its triangle discriminant is 4r. The boundary is a convex rectangle centered
at O: central opposition makes it a parallelogram, and its equal diagonals
make it a rectangle. It is a square only at u=2. In particular,
(B-A)·(C-B)=(c-1)(-1-c)-s²=1-c²-s²=0.
Check perpendicularity independently at all four boundary corners, using
coordinate differences rather than a stored rectangle tag. Proposed
consequences to check independently are: positive
face orientation, no crossing boundary edges, disjoint face interiors and
shared-edge agreement. Adjacent faces may intersect at their shared edge;
opposite faces may intersect only at O.

The reconstruction is deterministic only under these conventions. Metric
validity over the reals and representability over Q are separate outcomes.

## 3. Define the nontrivial transform family

Use rational t>0 and the circle parameterization

```text
c(t)=(1-t²)/(1+t²)
s(t)=2t/(1+t²)
u(t)=4t²/(1+t²)
```

Start at t=1: A=(1,0), B=(0,1), C=(-1,0), D=(0,-1), u=2.
Freeze primary targets t in {1/2, 1, 2}, with expected u in {4/5, 2, 16/5}.
Define T_t as replacement of u by u(t), followed by canonical reconstruction.
It is a target-setting operation, not an additive parameter update or a group
action. Repeated application at the same t is idempotent. Returning to t=1
restores the starting family state; it does not invert arbitrary prior states.

Preserve all four spoke quadrances, both diagnostic diagonal quadrances
Q(A,C)=Q(B,D)=4, central opposition C=-A and D=-B, and topology.
Preserve perpendicular adjacent boundary edges and boundary corner spreads of 1.
Allow the boundary quadrances, area and central spoke spreads to change. At t=1/2
or 2 the boundary quadrances differ from their initial values, which rules out
a label-preserving rigid motion. This family therefore tests constrained
nonrigid changes between reconstructed targets, without claiming to preserve
the full intrinsic metric. T_t is not a general local deformation operator;
preservation checks compare target states, not an independently evolving
constraint solver or composable transformation group.

Compute the central spread between OA and OB as 1-c²=r; it loses the sign
of c and cannot replace u as the full descriptor. Report this ambiguity.
Use identity, translation by (1/3,-2/5), and the rational rotation matrix
[[3/5,-4/5],[4/5,3/5]] as separate rigid controls on reconstructed coordinates.
These controls preserve every pairwise quadrance; undo their known frame
transform before comparing canonical coordinates.

## 4. Freeze the exact and bounded arithmetic contracts

Use arbitrary-precision reduced rational fractions as the independent oracle.
For a positive reduced rational n/d, accept a rational square root exactly when
both n and d are integer perfect squares. Use integer square roots and equality
checks; never infer exactness from a floating approximation. Reject r<=0 here.
The oracle constructs target coordinates directly from c(t),s(t); separately
derive squared distances from those coordinates to check metric reconstruction.
Do not reuse bounded arithmetic or its expected-output generation in the oracle.

Use a software format named QSG-R32: reduced n/d, signed 32-bit n, positive
d<=2³¹-1, gcd(|n|,d)=1; canonical zero is 0/1. Reject noncanonical imports.
Store a fixed 8 bytes per rational (two 32-bit words); this format is not an
existing SPU instruction or register encoding. Record oracle integer sizes too.

Evaluate each primitive +,-,*,/ using unreduced signed 64-bit integer
intermediates: ad+bc, ad-bc, ac,bd, or ad,bc respectively for a/b and c/d.
Check every product, sum, negation and sign normalization before reduction.
Reject division by zero. Reduce by integer gcd, then require QSG-R32 bounds.
No wraparound, saturation, hidden wider fallback or algebraic reassociation.
For sqrt, use the same perfect-square criterion on canonical n,d, then check
the result bounds. Integer gcd/division in this software model implies no RTL
algorithm or permission to introduce hardware dividers.

Freeze evaluation order: reconstruction computes u/2, 1-(u/2), c*c, 1-(c*c),
sqrt(r), then coordinates. Transform computes t*t, 1+(t*t), 4*(t*t), and
their quotient u, then reconstruction. Direct-oracle coordinates use the
formulas in section 3 independently. Count every primitive, including checks.
Intermediate refusal is an outcome even if an algebraically equivalent formula
would fit. Check rigid-control arithmetic under the same format rules.

Classify refusals as INVALID_ENCODING, INVALID_PARAMETER, INVALID_METRIC, DIVISION_BY_ZERO,
INTERMEDIATE_OVERFLOW, RESULT_OUT_OF_RANGE or DOMAIN_ESCAPE, in evaluation
order (encoding, t>0 parameter validation when applicable, metric-schema
validation, then the ordered operation stream).
For a positive nonsquare r, return DOMAIN_ESCAPE, not INVALID_METRIC.
Stage every update; commit u and any cached coordinates only after all checks.
Refusal leaves the entire previous state unchanged. Do not cache coordinates
in the minimal relationship representation unless charging the extra storage.

Q(sqrt(3)), Quadray encoding, A31, symbolic expression grammars and generic
constraint solvers are excluded from this first format. A future Quadray path
needs a separately reviewed map, scale and gauge. This rational probe does not
test the benefit of those representations.

## 5. Freeze falsifiers and comparative measurements

Test every ordered pair of the three primary targets, repeat each target,
and reconstruct each state twice. Check all eight metric values, both diagonal
quadrances, exact coordinates, perpendicular adjacent boundary edges at all
four corners, orientation, nonintersection and unchanged
topology against independent rational calculations. Include these controls:

| Input or mutation | Required outcome |
|---|---|
| u=0 or 4; u=-1 or 5 | INVALID_METRIC; degenerate or invalid patch |
| u=1 | DOMAIN_ESCAPE: s=sqrt(3)/2 is outside Q |
| u=1/2 | DOMAIN_ESCAPE: s=sqrt(7)/4 is outside Q |
| t=0 | INVALID_PARAMETER; its formal u=0 limit is degenerate |
| t=-1 | INVALID_PARAMETER: this family requires t>0; do not silently reflect |
| Zero denominator or unreduced imported fraction | INVALID_ENCODING |
| Expanded edge AB changed without matching CD | INVALID_METRIC |
| Swap B and D in reconstructed output | Orientation check fails |
| t=32768 | RESULT_OUT_OF_RANGE at 4*(t*t) before division |
| Primitive (2³¹-1)/1 + 1/1 | RESULT_OUT_OF_RANGE |
| Primitive division by canonical zero | DIVISION_BY_ZERO |

No single binary primitive on valid R32 operands is expected to overflow signed
64-bit intermediates; verify that bound analytically and test endpoints. Do not
invent an unreachable overflow fixture. Test atomic refusal for every reachable
failure above. Treat valid metrics rejected by the domain as measured coverage
limits, not as successes or geometric invalidity.

Compare the minimal descriptor, expanded edge metric, rational Cartesian
coordinates and binary64 Cartesian coordinates under identical topology,
targets, anchors and required outputs. Include coordinate-to-metric and
metric-to-coordinate costs, stored/cached bytes, peak temporary bits, operation
counts, gcd/sqrt work, refusals and end-to-end runtime separately. Charge frame
metadata consistently. Report binary64 coordinate errors and exact constraint
residuals by converting its finite stored values to rationals for measurement.
Use adaptive robust orientation predicates on those same binary64 inputs;
record their implementation/version and input-conversion limitations. They do
not certify exact constructions or recover information lost on conversion.

Freeze implementations, commands, repetition counts and software limits in a
later execution contract before collecting timings. No timing or storage
advantage is assumed; no unbounded symbolic expressions occur in this format.
This document satisfies no acceptance gate without independent review and
experiment evidence. Preserve acceptance at **0/5**.
