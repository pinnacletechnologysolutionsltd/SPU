# QSG-1: Intrinsic Geometry and Local Constraints

Date: 2026-10-19. Status: mathematical review complete for isolated software.
The owner authorized continuation subject to review and a bounded contract;
the [execution contract](../spu_strategy/contract_qsg1_software_2026-10-19.md)
now freezes classification precedence, matched semantics and software limits.
The [software results](QSG1_SOFTWARE_RESULTS.md) record the completed bounded
fixture. No independent acceptance or hardware promotion is inferred.
Read the [QSG-0 evidence review](QSG0_EVIDENCE_REVIEW.md) first. QSG-0 acceptance
remains 0/5; this draft neither closes its gates nor promotes a native primitive.

## 1. Freeze the embedding model and smallest closure question

Use vertices A,B,C,D and oriented faces (A,B,C), (B,A,D), sharing AB.
Fix topology and dimension: a planar disk in Euclidean R², z=0 if displayed in
3D. Anchor A=(0,0), B=(1,0), C above AB and D below AB. Individual faces are
rigid under a fixed face metric; local edits may change their metrics. There
is no dihedral freedom, growth, fracture or topology change in this model.

Two triangles with only a shared edge can be embedded independently on opposite
sides. Add the prescribed cross-patch quadrance CD to create a nontrivial
compatibility question. CD is a pairwise constraint, not another mesh edge or
face. Do not require its segment to lie inside a possibly concave boundary.

Use six rational quadrances with unique undirected pair IDs:
AB=1, AC=a, BC=b, AD=d, BD=e, CD=f. The four incident lengths are independent
inputs; closure constrains f. There is no rectangle, symmetry or global target
parameterization. Require positive values and reject conflicting copies of AB
when importing per-face data. Shared-edge agreement alone proves no closure.

## 2. Test compatibility directly on metric state

For a triangle with squared side lengths p,q,r, require p,q,r>0 and
Delta=4pq-(p+q-r)²>0. Equality is degeneracy; negativity is invalidity.
For the two faces, derive the following rational quantities:

```text
x=(1+a-b)/2             z=(1+d-e)/2
H=a-x²                 K=d-z²
W=f-(x-z)²-H-K
```

Local validity requires H>0 and K>0 (the face discriminants are 4H and 4K).
The selected planar opposite-side branch requires W>0 and W²=4HK.
Indeed C=(x,sqrt(H)) and D=(z,-sqrt(K)) give
f=(x-z)²+H+K+2sqrt(HK). The positive W test retains the orientation information
lost by squaring. These conditions are necessary and sufficient for this
restricted real planar embedding; they do not establish rational coordinates.

Rejecting this branch is not a proof of impossibility in three dimensions.
With a free dihedral angle, f ranges from (x-z)²+H+K-2sqrt(HK) to
(x-z)²+H+K+2sqrt(HK). QSG-1 selects the upper endpoint, not that 3D range.
Half-plane separation makes the two accepted nondegenerate face interiors
disjoint; the boundary cycle A,D,B,C,A is simple but need not be convex.

## 3. Make relationships the primary state

Store the six canonical rational metrics and fixed topology/orientation schema;
coordinates are optional derived outputs, never authoritative hidden state.
Operation V validates all metric relationships without taking square roots.
Operation E proposes (a',b') at C, preserving AB,d,e,f and all pair IDs exactly.
Stage both replacements; commit only if encoding, bounded evaluation, local
validity and closure succeed. Failed edits preserve all prior state and caches.
E is constraint admission, not a solver that finds a',b', or a deformation group.

Operation R reconstructs on request: C=(x,+sqrt(H)), D=(z,-sqrt(K)). Choose
positive roots deterministically. Over Q, each reduced H and K must have
perfect-square numerator and denominator; otherwise report DOMAIN_ESCAPE.
A globally valid rational metric may be committed even when R cannot produce
rational coordinates. Failed R leaves committed metrics unchanged and exposes
no partial coordinates. Successful E invalidates any old coordinate cache.
Keep full validation, edit validation and reconstruction costs separate.

## 4. Freeze rational arithmetic and proposed falsifiers

Use an arbitrary-precision rational oracle independent of the bounded model.
Use QSG-R32 for the bounded research model: canonical signed 32-bit numerator,
positive denominator <=2³¹-1, checked signed 64-bit primitive intermediates,
gcd reduction and atomic RESULT_OUT_OF_RANGE or INTERMEDIATE_OVERFLOW refusal.
Import noncanonical values as INVALID_ENCODING, with no silent normalization.
Retain QSG-0's primitive rules; this draft imports no production arithmetic.

Freeze validation order: encoding and pair-ID agreement; positive metrics and
AB=1; x=((1+a)-b)/2; z=((1+d)-e)/2; H=a-(x*x); K=d-(z*z);
local signs; v=x-z; W=((f-(v*v))-H)-K; W>0; L=W*W; P=(4*H)*K; L=P.
All steps use canonical bounded primitives. Compare reduced L,P by their
numerator/denominator pairs. Arithmetic refusal is an undecided bounded
evaluation, not a proof of an invalid real metric. Do not reassociate to fit.
Reconstruction computes sqrt(H), then sqrt(K), then coordinates in that order.

Use (AB,a,b,d,e,f) order for the proposed metric fixtures below. These are
hand-derived expectations, not executed results or software golden outputs.

| Input or request | Required interpretation |
|---|---|
| (1,1,2,2,1,5) | Valid; C=(0,1), D=(1,-1) |
| Previous state, E=(17/5,8/5) | Accept; C=(7/5,6/5); D and f=5 preserved |
| (1,5/4,5/4,5/9,8/9,101/36) | Valid independent face metrics; C=(1/2,1), D=(1/3,-2/3) |
| (1,1,2,2,1,4) | Each face valid, but planar closure fails: W²=1, 4HK=4 |
| (1,1,2,2,1,1) | Squared closure holds but W=-2; wrong planar orientation branch |
| (1,1,4,2,1,5) | First face degenerate: H=0 |
| (1,1,9,2,1,5) | First face invalid: H<0 |
| (1,1,1,1,1,3) | Real planar closure valid; R escapes Q via sqrt(3)/2 |
| Duplicate AB with unequal values | Reject shared-edge inconsistency before geometry |

The f=4 counterexample is compatible with a 3D hinge, so label its rejection
INCOMPATIBLE_PLANAR_CLOSURE. Distinguish WRONG_ORIENTATION_BRANCH,
DEGENERATE_FACE, INVALID_FACE and invalid edge/schema errors from DOMAIN_ESCAPE
and bounded arithmetic refusal. The execution contract freezes exact error
precedence and near-boundary R32 fixtures before execution. No hardware work
or QSG-2 execution is authorized by this specification or its approval.

## 5. Freeze the five research questions and comparisons

| Question | Required future evidence |
|---|---|
| Validity | Local, shared-edge and global failures discriminated; wrong squared-closure branch detected |
| Transformation | E changes admitted local metrics and preserves AB,d,e,f exactly; refusal is atomic |
| Reconstruction | Deterministic orientation and round trips; valid-but-unrepresentable metrics retained |
| Arithmetic | Exact rational agreement, intermediate bit growth, bounded refusals and domain escapes reported separately |
| Utility | An identified metric-state operation compared with conventional exact and numerical paths under matched semantics |

Include an ordinary exact squared-distance/Gram baseline: with g=(a+d-f)/2,
form G=[[1,x,z],[x,a,g],[z,g,d]]. Require the AB pivot 1, the two face
principal minors H,K>0, zero determinant and negative residual g-x*z for
the opposite-side branch. These conditions make G positive semidefinite of
rank two; do not require every other principal minor to be strictly positive.
This supplies a conventional rational consistency test without forcing either
baseline to reconstruct coordinates. Equivalent algebra may erase any advantage.
Also compare rational Cartesian updates/reconstruction on the Q-representable
subset and numerical coordinates with established adaptive robust orientation
predicates from [Shewchuk](https://www.cs.cmu.edu/~quake/robust.html). Pin the
actual source, compiler settings and initialization in a future execution
contract; QSG-0's local filter is not a substitute for this baseline.
Robust orientation alone does not certify squared-distance closure.

Measure V, E and R separately, then matched update/query workloads including
conversion, validation, caches, storage, refusal rates and exact residuals.
Charge common anchors consistently: six R32 metrics occupy 48 bytes (40 if
constant AB is shared); the four free Cartesian scalars occupy 32 bytes.
Cached free coordinates add 32 bytes to metric state. This is logical payload,
not Python memory or evidence of a storage advantage.
Compare the same accepted metric set; a coordinate baseline restricted to Q
cannot silently reject valid nonsquare metrics and claim equivalent semantics.
No speed, determinism, verification or energy benefit is assumed. A result
with no advantage is acceptable. The owner's revised instruction allows this
reviewed software tranche to proceed independently of QSG-0's pending gate
decision, under its own authorized bounded contract. General symbolic geometry,
arbitrary reconstruction, simulator/ISA
extensions, FPGA acceleration and Gen 1 changes remain outside scope.
