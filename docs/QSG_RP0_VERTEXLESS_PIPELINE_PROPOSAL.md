# QSG-RP0: vertexless relational pipeline feasibility

Date: 2026-10-19. Status: software research proposal; implementation and
measurements NOT RUN. A [bounded pilot](../research/qsg_rp0/README.md) is prepared,
with authored tests pending execution. No architecture, ISA, RTL or hardware qualification.

## Question and scope

Test whether evaluating mathematical scene relationships can avoid geometry
materialization while retaining certified visibility decisions at useful cost.
Keep Gen 1 unchanged. Begin with static, opaque objects, a rational camera,
a finite rational near/far interval and flat object colors. Defer illumination,
transparency, animation, general constraint solving and FPGA work.

The [QSG-1 results](QSG1_SOFTWARE_RESULTS.md) demonstrate, within their fixture,
that metric admission can succeed while a coordinate query escapes its domain.
They establish neither a visibility algorithm nor an architectural advantage.
RP0 must measure those questions separately.

## Mathematical contract to settle before implementation

Use rational scene coefficients and exact integer/rational predicates. Start
with a sphere and a plane clipped to a rational box; add a bounded convex solid
represented by half-spaces only after the first comparison works. Define the
Cartesian quadratic form explicitly before introducing a Quadray encoding;
verify any later encoding preserves the same form and scene semantics.

For each camera ray P(t)=O+tD, restrict t to the closed near/far interval.
Sphere substitution yields at²+bt+c. A nonsquare discriminant is an expected
domain escape from Q, not invalid geometry. Represent roots by defining
polynomials and rational isolating intervals, or retain certified rational
bounds. Never round a root into an exact coordinate claim. Handle zero ray
direction, linear/constant degeneracy, tangency, parallel and coplanar planes,
camera-inside objects, clipping and coincident first hits explicitly.

Separate three query types:

* Solid membership: an entire bounded viewing volume is outside, inside or
  undecided with respect to a specified solid.
* Boundary intersection: a boundary is excluded, an intersection is proved,
  or the query is unresolved. An interval containing zero alone does not prove
  an intersection. An entirely interior volume can exclude a boundary without
  being empty solid space.
* Visibility ordering: prove the nearest eligible boundary hit, prove a miss,
  or return unresolved. Disjoint root intervals can prove ordering; overlapping
  intervals require refinement, an exact equality/order predicate, or refusal.

Use conservative bounds over the complete finite viewing volume of a tile.
Point samples cannot certify tile exclusion. Retain object identity and t bounds
through subdivision. An empty tile requires exclusion of every candidate.
Set a deterministic refinement/work limit; exhaustion returns UNRESOLVED and
must never silently become background or an arbitrary depth winner.

Define the image observation before comparing paths: begin with one rational
center ray per pixel and nearest opaque boundary hit in the clipping interval.
This measures sampled visibility, not continuous area coverage. Use an explicit
object-ID rule for equal-depth ties. Keep unresolved pixels in a separate mask.
Any later antialiasing comparison needs its own common coverage/error contract.

## Comparison design

Implement an independently formulated exact per-ray reference, a relational
tile/subdivision candidate and an explicit triangle approximation. Give all
paths the same camera, clipping, object identities, tie rules and colors.
Include a direct analytic per-ray baseline so a win over tessellation alone
cannot be attributed to SPU or region classification.

Specify a certified world-space surface approximation tolerance for the mesh
and report tessellation construction/storage separately from frame evaluation.
Surface-distance tolerance alone does not bound silhouette pixel differences
or visibility changes near tangencies and occlusion ties. Report those cases
separately; do not require unconditional framebuffer equality between different
geometries or treat mesh error as relational error.

Test misses, tangent rays, near tangencies, camera-inside views, clipped hits,
equal-depth ties, nearly coincident surfaces, overlapping interval bounds and
intentional work-limit exhaustion. Verify that tile exclusion loses no reference
hits and that each resolved candidate pixel agrees with the exact reference.
Include a deliberately unsound point-sampling exclusion control that the
fixtures must reject. Check retained exclusion/order certificates independently.

Record resolved/miss/unresolved counts, framebuffer disagreements and their
causes, arithmetic operations by kind, predicate refinements, maximum integer
bit lengths, intermediate and persistent storage, and construction costs.
Record the execution dependency graph, critical dependency depth under stated
operation costs, and bytes communicated between proposed stages. Python time
is an exploratory implementation measurement; operation counts and graph models
are not FPGA cycle, area, power or bandwidth measurements.

Track certificate reuse explicitly: per-certificate object-ray queries avoided,
whole-ray queries avoided, construction effort including unsuccessful attempts,
and retained certificate bytes. Report rays avoided / construction cost with
the cost unit named; it is a heuristic, not a speedup. Allow the analytic
baseline matched spatial acceleration and caching before architectural comparisons.

## Execution and decision boundary

Keep a future pilot under `research/qsg_rp0/` with its own tests and one findings
note, following the [research execution policy](../spu_strategy/RESEARCH_EXECUTION_POLICY.md).
Before running it, specify exact commands and local resource limits in that
pilot's reviewed scope. This proposal launches no job, modifies no frozen QSG
contract and adds no dependency on QSG acceptance counters.

Proceed toward architecture only if correctness, unresolved rates and matched
cost comparisons identify a useful workload and a concrete storage/scheduling
benefit. A useful software renderer, a workload-specific optimization and a
negative architectural result are all valid outcomes. Vertex elimination alone
does not establish novelty or architectural value.
