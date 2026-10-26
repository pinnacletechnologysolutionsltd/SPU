# QSG proposed research stages

Date: 2026-10-19. Status: research direction, not an implementation commitment.
Gen 1 GPU, simulator and CPU qualification remain primary. These stages reserve
no hardware budget or new ISA/RTL work. The owner's revised instruction
authorized a reviewed, bounded QSG-1 software tranche independently of QSG-0
acceptance; that tranche is now complete under its separate execution contract.

| Stage | Question | Current disposition |
|---|---|---|
| [QSG-0: exact reconstruction and bounded arithmetic](QSG0_SOFTWARE_RESULTS.md) | Can a restricted family reconstruct exactly with explicit refusals? | Fixture PASS, frozen; formal acceptance 0/5 pending designated independent result review |
| [QSG-1: Intrinsic Geometry and Local Constraints](QSG1_INTRINSIC_GEOMETRY_SPECIFICATION.md) | Can local metric relationships be primary state with nontrivial compatibility? | Reviewed planar two-triangle scope; [authorized software fixture PASS](QSG1_SOFTWARE_RESULTS.md); no architectural advantage or independent gate acceptance inferred |
| [QSG-2: PH curves and algebraic arc length](QSG2_PH_CURVE_SPECIFICATION.md) | Does factored hodograph state help exact curve/tangent/arc-length operations? | [Separately authorized bounded software tranche PASS](QSG2_SOFTWARE_RESULTS.md); operation-specific comparisons, no SPU-specific speed advantage; independent acceptance pending |
| [QSG-3: relational geometry machine model](QSG3_GEOMETRIC_MACHINE_SPECIFICATION.md) | Can validated geometric objects support composable updates, dependencies and selective observations? | Exploratory specification; implementation and execution not started; generative dynamics and changing topology deferred |
| QSG-4: SPU architectural evaluation | Do qualified kernels justify native machine primitives? | Exploratory; simulator instructions, FPGA or Gen 2 adoption conditional on comparative evidence and Gen 1 milestones |

QSG-0's designated evidence review remains pending; it no longer blocks
separately authorized cheap software research. QSG-1's mathematical review and
bounded experiment are recorded in its contract and results. The
[QSG-1 saved-evidence audit](QSG1_EVIDENCE_REVIEW.md) records provenance and
coverage limits without granting independent acceptance. The
[QSG-0 audit](QSG0_EVIDENCE_REVIEW.md) checks preserved evidence and corrects
an overflow interpretation; it does not mark any acceptance gate verified.
Keep failed hypotheses and negative comparative results visible at every stage.

The revised QSG-3 direction first studies machine semantics and computation
structure. Growth, fracture, relaxation and topology changes remain future
extensions requiring their own laws and contracts. An inconclusive Python speed
comparison does not settle this architectural question. Conversely, fewer
object-level commands do not establish less underlying computation or cheaper
hardware. QSG-4 retains responsibility for evaluating possible native realization.

QSG-1 fixes planar opposite-side embedding before testing closure; a rejected
cross-patch distance may be valid for a 3D hinge. Metric validity and rational
coordinate representability remain distinct. Later stages must independently
justify any change of embedding domain, arithmetic, topology or dynamics.

For QSG-2, begin with the [PH survey](https://www.cs.rug.nl/~jiri/papers/14KoLa.pdf)
already identified in the [QSG-0 reading map](QSG0_GENERATIVE_GEOMETRY_RESEARCH.md).
Compare defined operations with established curve families, rather than
presuming quadrance/spread notation supplies a new curve theory.

Possible outcomes include a useful geometry library, a computation model,
an uncompetitive representation or a qualified native kernel. None is the
presumed endpoint. Follow the [public maturity vocabulary](RESEARCH_IDENTITY.md):
correctness within a fixture, comparative utility and hardware qualification
are independent claims. Each stage may falsify the architectural hypothesis
before additional engineering or hardware resources are spent.
