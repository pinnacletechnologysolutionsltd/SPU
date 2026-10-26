# QSG-0: Generative Geometry Research

Date: 2026-10-19. Status: scope frozen; literature triage begun;
mathematical specification reviewed and amended; authorized isolated software
experiment completed, with independent result review pending.
Research gate: **0/5 verified**.

The [mathematical specification](QSG0_MATHEMATICAL_SPECIFICATION.md) records
the owner's PASS for the proposed experimental direction and incorporates the
rectangle naming and perpendicular-edge amendment. It fixes a rational
rectangle fan, constrained reconstructed targets and QSG-R32 software arithmetic.
Specification review is not experimental evidence or gate acceptance.
The [software results](QSG0_SOFTWARE_RESULTS.md) record the authorized rectangle
fixture and comparative limits. QSG-0 is now frozen pending renewed authorization;
the experiment does not change the acceptance count.

The [evidence review](QSG0_EVIDENCE_REVIEW.md) corrects the interpretation of
the t=32768 refusal without changing the experiment. The
[proposed QSG stage map](QSG_RESEARCH_ROADMAP.md) links QSG-1's planar closure
specification. The owner's subsequent instruction authorized a separate bounded
QSG-1 software tranche; its results do not advance QSG-0 acceptance.

## Priority decision

SPU-13 Gen 1 remains primary: deterministic GPU, CPU integration, simulator,
development tools and an independently reproducible hardware demonstration.
QSG-0 must not delay, redesign or destabilize it. Preserve active Artix-7 CPU
routing/timing and GPU visual qualification contracts, inputs and budgets.

| Horizon | Scope | Promotion condition |
|---|---|---|
| Gen 1 | Existing execution and visualization platform | Existing independent qualification gates |
| QSG-0 | Literature review, mathematical specification, one tiny software experiment | Frozen scope below |
| SPU-G2: Algebraic Geometry and Dynamics | Intrinsic representations, constraints, curves, surface evolution and possible acceleration | Completed Gen 1 milestones and convincing comparative software results |
| Future generative morphology processor | Growth, regeneration, fracture and dynamic topology | Research possibility; no architectural commitment |

Planning attention targets are 70% current GPU/CPU qualification, 25% simulator,
documentation and ecosystem, 5% QSG-0. These are not reserved resources or a
reason to interrupt an active campaign. Allocate no FPGA budget, hardware time,
new RTL branch, ISA instructions, pipeline changes or timing-constraint edits.

## Literature triage

Read intrinsic rendering, PH curves and rational trigonometry first. The table
records relevance, not a completed systematic review or a novelty finding.

| Primary reference | Established contribution relevant here | Boundary for QSG-0 |
|---|---|---|
| Celes, [Direct Rendering of Intrinsic Triangulations](https://doi.org/10.1145/3716314), 2025; [author implementation](https://github.com/wceles/intrinsic-triangulation) | Intrinsic data structures supporting direct rendering and data transfer | Rendering precedent; no proof of SPU arithmetic benefit |
| Kosinka and Lávička, [Pythagorean Hodograph Curves: A Survey of Recent Advances](https://www.cs.rug.nl/~jiri/papers/14KoLa.pdf), 2014 | Polynomial planar PH curves have polynomial arc length and rational offsets | Does not establish closure for arbitrary curves, reconstruction or trimming |
| Wildberger, [The ancient Greeks present: Rational Trigonometry](https://arxiv.org/abs/0806.3481), 2008 | Quadrance and spread as algebraic geometric quantities | Define the actual quadratic form and nondegeneracy assumptions locally |
| Crane, Weischedel and Wardetzky, [Geodesics in Heat](https://arxiv.org/abs/1204.6216), 2013 | Surface distance computation using heat flow | Numerical reference; no exactness claim |
| Prusinkiewicz and Lindenmayer, [The Algorithmic Beauty of Plants](https://algorithmicbotany.org/papers/abop/abop.pdf), 1990 | Generative rewriting and branching models | Growth is outside the first experiment |
| Bouaziz et al., [Projective Dynamics](https://users.cs.utah.edu/~ladislav/bouaziz14projective/bouaziz14projective.html), 2014 | Geometric constraint projections for simulation | Numerical projections need separate exact-domain analysis |
| Shewchuk, [Adaptive Precision Floating-Point Arithmetic and Fast Robust Predicates for Computational Geometry](https://www.cs.cmu.edu/~quake/robust.html), 1997 | Adaptive arithmetic for robust geometric decisions | Compare predicate correctness with a robust baseline, not only naive floating point |

Source check: primary abstracts/pages and the PH survey were consulted on
2026-10-19. The ACM full page refused direct access; its indexed abstract and
author repository provide initial discovery only. Full algorithm review remains
part of the literature deliverable. Omit decorative image/proxy links.

The proposed intersection is intrinsic geometry, rational trigonometry,
generative rules, exact predicates and native computation. Its usefulness and
originality remain open. Squared edge lengths are already conventional mesh
data; renaming them quadrances establishes no efficiency advantage.

## Frozen first experiment: specification requirements

Deliver exactly one review, one mathematical specification and one independent
reference experiment. Keep software isolated from production paths and the
shared regression runner. Freeze after these deliverables until a completed
Gen 1 milestone is recorded and the owner resumes research.

Define topology as labeled vertices, edges and four oriented triangular faces
of a disk with fixed connectivity. Define the intrinsic metric as consistent
positive edge quadrances with valid face metrics. Define the embedding
separately as coordinates realizing those quadrances in a specified quadratic
form. A Quadray representation requires an explicit coordinate map, scale and
gauge convention; four stored components alone do not define that metric.

**Pre-execution correction:** an intrinsic metric does not uniquely specify a
3D embedding. Fix anchors, orientation and a planar realization convention for
the first patch, or provide explicit additional embedding data. Do not claim
general reconstruction from edge quadrances. Square roots can leave the chosen
domain even when all quadrances are rational; refuse such cases explicitly.

Start the oracle in arbitrary-precision rationals. Qualify any extension to
Q(sqrt(3)) independently using rational coefficient pairs. Do not interpret
finite modular residues or the split algebra A31 as ordered Euclidean lengths.
The bounded software model must name its numerical format, intermediate widths,
normalization rules and atomic overflow/unrepresentable-value refusal. It is
not evidence of execution by existing SPU instructions.

For a Euclidean triangle with squared side lengths u, v, w, require u,v,w > 0
and D = 2(uv+vw+wu)-u²-v²-w² > 0, where D is sixteen times squared area.
Check shared-edge consistency, orientation and nonintersection separately;
valid individual faces do not establish a valid patch embedding.
For nonzero vectors a,b, define spread as
1-(a·b)²/((a·a)(b·b)); reject zero denominators.

Specify a finite family of constrained transforms and exactly which quadrances
they preserve. Begin with rational rigid transforms as controls; distinguish
their trivial metric invariance from any useful local deformation. A failed
nontrivial family is an acceptable research result. Never silently weaken
preserved constraints to obtain a successful example.

Test deterministic reconstruction, exact metric preservation, invalid triangles,
inconsistent shared edges, reflections/orientation, domain escape, overflow and
refusal without partial state changes. Independent rational calculations must
not call the bounded implementation to construct expected answers.

Compare identical operations and inputs against rational Cartesian coordinates
and binary64 coordinates. Include adaptive robust predicates for matching
orientation/validity decisions; robustness does not make floating-point
constructions exact. Report stored bits, peak intermediate sizes, arithmetic
operation counts, normalization costs, reconstruction cost and measured runtime
separately. Include rejected cases and expression growth; establish no hardware
speed, energy or storage advantage from software timing alone.

## Research acceptance record

| Criterion | Evidence status |
|---|---|
| Definitions distinguish intrinsic geometry, embedding and topology | Proposed above; specification unverified |
| Exact oracle and bounded arithmetic behavior specified | Software fixture run; independent result review pending |
| Four-triangle patch passes geometry validity tests | Fixture PASS; independent result review pending |
| Conventional arithmetic baseline included | Comparative measurements recorded; independent result review pending |
| No Gen 1 RTL, ISA or timing constraints modified | Experiment scope preserved; independent result review pending |

Keep the count at 0/5 until evidence is reviewed. Existing AOR, SGN, symbolic
state or geometry results do not automatically satisfy these gates. Link future
results here, including negative results and explicit limitations. Related
context: [algebraic–geometric machine direction](ALGEBRAIC_GEOMETRIC_MACHINE_RESEARCH_DIRECTION.md)
and [graphics roadmap](../spu_strategy/GPU_EVALUATION_ROADMAP_2026-10-03.md).

## Documentation validation

Run from the repository root:

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/QSG0_GENERATIVE_GEOMETRY_RESEARCH.md spu_strategy/GPU_EVALUATION_ROADMAP_2026-10-03.md
```

The specification and separate software execution contract now supply the
numerical format, patch, targets, command and limits. See the results note for
the executed invocation. This record authorizes no additional experiment,
hardware or long-running campaign.
