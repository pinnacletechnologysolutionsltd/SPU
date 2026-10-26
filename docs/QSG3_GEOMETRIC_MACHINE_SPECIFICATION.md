# QSG-3: relational geometry machine model

Date: 2026-10-19. Status: exploratory specification for review. No implementation
or execution performed under this specification. QSG-2's completed execution
allowance does not extend to a new experiment.

## Research question

Can a finite machine retain validated geometric relationships as authoritative
state, compose nontrivial admissible updates, and selectively materialize
observations while preserving deterministic semantics and explicit refusals?

Here, native means an object and its legal transitions belong to the abstract
machine's semantics. It does not mean one cycle, one physical register, a new ISA
instruction or an established hardware advantage. A software interpreter is an
architecture model, not a physical implementation.

## Relationship to existing work

QSG-0 established restricted exact reconstruction within its recorded fixture.
QSG-1 separated metric validity from rational coordinate reconstruction. QSG-2
tested factored PH curves and validated query certificates. Their acceptance
boundaries and negative comparative results remain unchanged.

The [SSM architecture](SSM_ARCHITECTURE_2026-10-18.md) already investigates typed
handles, relational state and certificates. The
[SSM-4 design](SSM4_CERTIFIED_GEOMETRIC_STATE_DESIGN_2026-10-18.md) addresses
certified geometric families and selective observation; the
[SG-0 interface design](SG0_SYMBOLIC_GPU_INTERFACE_DESIGN_2026-10-18.md) addresses
materialization and rendering provenance. These are overlapping foundations,
not evidence that QSG-3 is implemented. Initially compare their concepts without
modifying or integrating their implementations.

## Proposed smallest machine

Use eight object slots, at most eight dependency edges, and at most 64 submitted
commands per fixture. Fix topology. Retain canonical rational source values;
freeze coefficient and intermediate bounds in an execution contract before code.
General symbolic expressions and additional algebraic domains are deferred.

Two object types reuse already specified mathematics:

- A QSG-1 planar patch with intrinsic metrics, fixed incidence and opposite-side
  orientation. Real metric validity does not require rational coordinates.
- A QSG-2 regular PH curve with authoritative factors and validated derived
  coefficients. Query caches never become independent sources of truth.

Observation records name an object slot, its revision and a typed query. Each
depends directly on one source object. This initial dependency graph is acyclic;
it models observation invalidation, not a general constraint solver or a
distributed execution fabric. No slot deletion or reuse occurs in a fixture.

Commands admit an object, apply a typed validated edit, register an observation,
or evaluate an observation. Patch edits retain the QSG-1 preserved relationships;
curve edits replace factors subject to QSG-2 regularity and certificate rules.
Sequences of these edits constitute composition. They are partial state
transitions, not an assumed transformation group. Include repeated successful
edits and intervening refusals rather than only forward/inverse identities.

## State and transition obligations

Each successful edit increments its source revision and atomically invalidates
all dependent cached observations. Derived certificates bind to that revision.
Evaluation uses current state and records the revision it observed. A stale
cached value cannot be returned as current. Process invalidations in ascending
observation-slot order; serialize commands in submitted order.

Validate proposed state before publication. A refused edit preserves source
values, revisions, certificates and observation caches. Diagnostic trace events
may record the refusal. Observation failure preserves the valid source object:
for example, rational coordinate reconstruction can return `DOMAIN_ESCAPE`
without invalidating a real-planar metric state.

The execution contract must freeze error precedence and arithmetic evaluation
order separately for every command. In particular, invalid references and types,
invalid geometry or certificates, arithmetic refusal and observation-domain
escape must not depend on dictionary order or interpreter scheduling. It must
also distinguish a request exceeding a machine bound from an invalid object.

## Matched conventional model

Implement an object interpreter and a conventional scalar lowering only after
their shared observable semantics and execution contract are reviewed. Give both
the same mathematical inputs, certificates, validation-once permissions,
revision tracking, caching, deferred reconstruction and arithmetic bounds.
The scalar path may use metric or Gram algebra directly; it is never required
to reconstruct coordinates merely to validate relationships.

Check both against independent exact expected values and negative controls.
Agreement between interpreters alone is insufficient. Compare normalized
observable outcomes, refusals, retained state and revisions; internal traces
may differ. Record differences in arithmetic order and refusal behavior rather
than treating unequal accepted workloads as a speedup.

Report object commands separately from expanded scalar arithmetic, comparisons,
normalization, certificate checks, cache operations and coordinate constructions.
Count logical state reads/writes and rational payload bits under an explicit
accounting convention; these are not physical memory traffic or energy estimates.
Record peak intermediate bit lengths and temporary state. Include admission,
invalidation and query costs. No unweighted object instruction count is evidence
of reduced hardware work. Equivalent optimized scalar work is a valid result.

## First milestone and falsifiers

The first milestone is a bounded composable system, with independently checked
invariants after each successful edit, deterministic observation and refusal
traces, and no stale observations or partial commits through mixed sequences.
Include a valid metric whose Cartesian observation escapes the rational domain,
a closure-invalid edit, a nonregular curve edit, a stale-cache control and a
bounded arithmetic refusal with populated observations.

Demonstrate that controls detect deliberately wrong certificates, omitted
invalidation and partial publication. Report coverage limits; finite traces do
not prove arbitrary-length composition or general surface consistency.

A model may be correct yet add bookkeeping without reducing expanded work.
That result constrains adoption without exhausting the broader design space.
Any claimed simplification must identify the workload and retained costs.

## Preparation boundary

### First sequence probe

The [selective-observation fixture](../research/selective_observation/README.md)
now supplies a tested interface precedent. Its immutable SSM parent/child
identities are distinct from the proposed QSG-3 mutable slot revisions. It has
no cache and therefore supplies no cache-invalidation evidence.

Before implementing both object types, isolate one planar patch slot and two
dependent observation slots: a metric query and rational coordinate
reconstruction. Use the existing QSG-1 metric order `(AB, AC, BC, AD, BD, CD)`
and frozen anchor/orientation conventions. A proposed minimal trace is:

| Step | Operation | Required state and observation behavior |
|---|---|---|
| 1 | Admit `(1,1,2,2,1,5)` | Revision 0; valid metric, no coordinates required at admission |
| 2 | Evaluate both observations | Populate both caches, explicitly bound to revision 0 |
| 3 | Replace `(AC,BC)` with `(17/5,8/5)` | Revision 1; preserve AB, AD, BD, CD; invalidate both observations atomically |
| 4 | Evaluate both again | Independently check `C=(7/5,6/5)`, `D=(1,-1)` and cached revision 1 |
| 5 | Propose `(AC,BC)=(1,1)` | Local triangles valid but opposite-side closure fails with the preserved other metrics; refuse and retain revision 1 and both caches |
| 6 | Replace `(AC,BC)` with `(1,2)` | Revision 2; restore initial metric; invalidate both caches even though an earlier revision had equal geometry |
| 7 | Attempt to reuse a revision-0 receipt | Reject it as current evidence; independently reconstructed equal coordinates do not make an old receipt current |

Check the exact closure relation and retained metrics after every accepted edit.
Step 5 must use the same populated cache state as step 4; checking only an empty
cache is insufficient. A conventional exact implementation gets the same
relationships, revisions, cache permissions and deferred queries.

This sequence is a proposed first probe, not the entire QSG-3 milestone.
Separate controls must still cover bounded arithmetic refusal with populated
caches and valid metrics with rational reconstruction escape. The PH object,
cross-object dependencies and topology changes remain outside this first probe.
Freeze error precedence, source identities and a single small execution budget
in the implementation contract; the earlier selective-observation allocation
is consumed and is not reused here.

Next deliverable: a command-first implementation/execution contract with exact
source inventory, arithmetic bounds, oracle separation, fixtures, accounting
rules, source freeze and a proposed single 30-second correctness/accounting run.
No timing campaign is needed for this first milestone. Implementation and
execution require their own authorization; this document starts neither.

No production simulator, ISA, RTL, FPGA campaign or Gen 1 change is included.
Later compositional object dependencies, generative rules, topology changes and
representation transitions need separately specified semantics and evidence.
The research horizon remains open; each implementation remains finite.
