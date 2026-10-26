# Golden Core Reading Map — Synergetics Cookbook

**Date:** 2026-10-16
**Status:** Research reference; no implementation or qualification claim
**Source:** `Synergetics-Cookbook.pdf` in the repository root

## 1. Source preservation and identity

The root PDF is preserved as read-only source material. This map does not edit,
rewrite, or import its contents into the SPU-13 implementation.

| Field | Recorded value |
|---|---|
| Printed title/version | *The Synergetics Cookbook*, v0.19 |
| Printed date | 2026-08-06 |
| Printed author | Andy Thomson, ABCD.EARTH Project |
| Printed DOI | 10.13140/RG.2.2.14110.91207 |
| Printed license | CC BY-NC-SA 4.0 |
| PDF pages / size | 108 pages / 4,862,612 bytes |
| PDF metadata creation time | 2026-09-25 03:16:34 NZST |
| SHA-256 at review | `35d27542883461232472d9192406a7c9763839a4f25d54ae42c88239863999cc` |

The printed edition date and PDF metadata creation date differ; both are
recorded as source metadata, not reconciled by assumption. The PDF is the
author's technical source. Its claims are not, by that fact alone, independently
proved or implemented in this repository.

## 2. How to use the map

Read the cookbook as a collection of mathematical constructions and software
design ideas. For Golden Core, keep three evidence levels distinct:

1. **Mathematical identity:** follows from stated definitions and can be
   checked symbolically or with exact arithmetic.
2. **Repository implementation:** the named code, oracle, tests, or device
   evidence demonstrate that a specific implementation realizes the identity
   over a stated domain.
3. **Interpretation or architecture hypothesis:** suggests a useful model,
   physical interpretation, or future instruction, but needs a separate
   experiment and evidence.

Exact coordinates can improve classification and reproducibility without
establishing that the chosen coordinates are physically fundamental or faster
on a processor. Keep spatial dimension, coordinate count, embedding dimension,
and configuration-space dimension separate.

## 3. Annotated chapter map

| Cookbook section and pages | Contents | Golden Core connection and review note |
|---|---|---|
| **1 — Introduction, pp. 9–10** | Quadray-native computational geometry and the proposed no-Cartesian-roundtrip workflow. | Use as motivation for representation choice. Treat “self-sufficient” and performance implications as claims to measure per workload. |
| **2 — Quadray foundations, pp. 10–13** | Tetrahedral basis, coordinate conventions, integer polyhedra, number tower, normalization and relaxed coordinates. | High priority for GC-0/GC-2. Record exactly which model is used: ordinary 3D Quadray points modulo common offset, a selected zero-sum representative, or an unconstrained four-coordinate extension. These are not interchangeable. §2.7 is a useful field-inventory template for Golden Core's domain ledger. |
| **3 — Three dimensions, four axes, pp. 13–15** | Separates parameterization from spatial dimension; introduces Strüppi-Up. | Useful terminology and a reminder to distinguish dimensions. World-up is a convention, not an intrinsic chirality result. Broader Synergetics interpretations remain hypotheses. |
| **4 — Translation, scaling and mirrors, pp. 16–18** | Central inversion, single-coordinate negation, coordinate swaps, signed regions and Janus scaling. | Essential orientation reading, but scope each map to its state space. Central inversion has determinant −1 on the 3D zero-sum space and +1 on unconstrained R⁴. A single-coordinate sign flip does not preserve the zero-sum subspace; it cannot be called a physical 3D mirror there without a separately defined projection and metric check. Coordinate permutations do preserve zero-sum and have determinant equal to permutation parity. Keep Janus/negative-dimensional interpretations separate from these linear-algebra facts. |
| **5 — Inner product and metric, pp. 19–28** | Metric tensor, quadrance, edge values, bounds, tetrahedral Pythagoras and links to Fuller constants. | Candidate GC-2 reference for exact metric and length ordering. Re-derive the metric on the chosen state space, check gauge invariance, positive definiteness on the physical quotient, and exact comparison. Do not reuse an algebraic norm as a distance without proving the metric properties. The philosophical “structural constant” discussion is not a computational theorem. |
| **6 — Cartesian bridge, pp. 29–30** | Pseudoinverse, height functions and grid construction. | Useful as an explicit conversion boundary for CPU/GPU interoperability. It qualifies as a coordinate bridge, not evidence that Cartesian execution is unnecessary in every pipeline. Compare exact source-side calculations with the actual GPU input contract. |
| **7 — Height functions and plane constraints, pp. 31–32** | Plane equations, projection and constrained interpolation. | Strong candidates for exact geometry predicates and constructions. Reproduce small fixtures with exact incidence, plane membership, projection residual, and interpolation invariants before integrating with a renderer. |
| **8 — Polyhedra catalogue, pp. 33–40** | Platonic, Archimedean and Catalan solids; great-circle and geodesic families; coordinate-field summary. | Useful source of finite exact geometry fixtures. Start with a tetrahedron, octahedron, cube and icosahedral data. Validate vertex/edge/face incidence and exact edge quadrances. The book's catalogue counts and exact-field claims need fixture-level confirmation before becoming Golden Core dependencies. |
| **9 — Rotations, pp. 40–54** | F/G/H rotations, rational parametrization, K(u), Rodrigues, nine-product apply kernel, V4 edge half-turns, rotor storage/composition/interpolation and numerical validation. | Highest priority for transform research. Separate finite ROTC catalog transforms from generic K(u) rotations and from the paper's rotor storage/composition model. Verify determinant +1 on the 3D subspace, metric preservation, composition order, inverses, and coefficient growth. The nine-product kernel is an algebraic cost claim; count field operations separately from integer multiplies and compare with the current specialized F/G/H path. Gimbal-lock and Janus interpretations are not accepted solely from this chapter. |
| **10 — Projection, pp. 55–60** | ABCD-to-clip path, CPU projector, instance rotation, inverse cursor projection, validation and GPU boundary. | Directly relevant to CPU/GPU architecture. The cookbook describes an ABCD-native pipeline; the maintained SPU GPU scene format currently accepts integer screen-space x/y and depth, while the Vulkan example evaluates screen-space triangle edges. Thus the cookbook pipeline is a candidate for a separate comparison, not a description of the current T1d GPU path. Test forward/inverse round trips and compare rendered results at a clearly stated precision boundary. |
| **11 — Convex hull, pp. 60–62** | Orientation determinant, distance comparison, incremental hull, Cayley–Menger and surd-exact future work. | Excellent GC-2 experiment source. Reproduce the signed orientation predicate on zero-sum-normalized coordinates; verify degeneracies return zero and canonical min-zero normalization is not substituted. Compare hull topology on integer fixtures against an independent exact oracle. The sign of one tetrahedron's volume is orientation, not a complete test of global shape chirality. |
| **12 — Computational techniques, pp. 62–67** | Deferred radicals, rational multiplier, grid snap, metric, spread, cross product, normals, precision boundary. | Use as an implementation-candidate inventory. For each primitive, freeze input domain, canonical representation, overflow or denominator behavior, and an exact reference. Separate algebraic operation count from hardware latency/resource cost. |
| **13 — Why exact coordinates matter, pp. 68–70** | Continuous versus discrete geometry and precision arguments. | Helpful for motivating exact predicates near degeneracies. Treat examples as workload-specific; establish when the exact representation prevents a wrong classification and measure storage/runtime costs. Do not infer universal superiority over floating point. |
| **14 — Anti-patterns, pp. 70–72** | Coordinate roundtrips, premature radicals, off-plane interpolation, orientation normalization, rotation storage and cursor-picking cautions. | A practical checklist for the future demo and oracle. Particularly useful: preserve the chosen gauge, avoid hidden conversion boundaries, and test forward and inverse transforms independently. Some statements about unrestricted four-coordinate rotation need to be reconciled with the 3D zero-sum model before reuse. |
| **15 — CCP and volumetric grid, pp. 72–74** | Close-packed lattice identities, frequency and nested CCP. | Candidate discrete substrate for future geometry experiments. Specify the graph/cell complex and its incidence before relating it to Penrose or Golden Core inflation; this chapter does not itself define an aperiodic tiling. |
| **16 — Units and conversions, pp. 74–76** | Rational unit choices and conversion ladder. | Useful for documenting scale conventions and avoiding hidden factors in exact fixtures. A unit convention is not an invariant or physical measurement. |
| **17 — Geodesic subdivision, pp. 76–81** | Quadrance-based subdivision, target values, face handling, counts and Weierstrass geodesics. | Strong candidate for a controlled exact-construction demo: freeze a small seed polyhedron and frequency, then compare expected vertex/face counts, edge classes and projection modes. The φ-algebraic examples are useful Golden Core inputs, but subdivision is not Penrose inflation. |
| **18 — Tetravolumes, pp. 81–88** | Determinant volume formulas, cross-validation and hierarchy accounting. | Useful for orientation-sensitive invariants and exact volume checks. Verify dimensions and normalization constants independently; the 3D physical determinant and any 4D structural “tetravolume” must not share a name without definitions. |
| **19 — Synergetics constants, pp. 88–90** | Algebraic presentations of S₁/S₂/S₃ and interpretation. | Mine exact identities only after independently deriving them. Historical or philosophical significance is not evidence that the constants are processor primitives or physical laws. |
| **20 — Jitterbug, pp. 90–93** | Rational conic sweep, rigid-strut construction, mirror-related octahedra and pulsating tetrahedra. | Rich deterministic animation fixture. Verify rigid lengths, vertex correspondence, orientation and endpoint geometry exactly. Treat claims about “momentum” or natural dynamics as interpretation unless a dynamical model and units are specified. |
| **21 — Snub fields, pp. 93–95** | Cubic fields for chiral snub solids, mirror pairing and a continuous sweep. | A promising later chirality test case because it provides explicit enantiomer candidates and exact algebraic fields. First validate minimal polynomial reductions, coordinate identities, incidence, edge lengths, and the mirror map. This is beyond GC-1's initial Z[φ] arithmetic and must not be called verified from the manuscript alone. |
| **22 — Rational calculus, pp. 96–97** | Rational parametrization of conics/quadrics and limits of rational parametrization. | Useful methodology for discovering exact parameterizations. A parameterization must include its domain, excluded points, inverse, and singular cases; it does not imply every trajectory or surface is rationally parameterizable. |
| **23 — Knowledge graph, pp. 97–99** | Self-describing codebase and nested conceptual shell. | Treat as a software/documentation organization proposal, not as a mathematical property of geometric space. Golden Core can use a provenance graph linking each definition, implementation, oracle, fixture and result without adopting the cosmological framing. |
| **24 — Conclusion, p. 100; glossary and version history, pp. 103–108** | Summary, terminology, references and document history. | Use for attribution and source tracking. Preserve quotations and reuse within the printed CC BY-NC-SA 4.0 terms; record the exact edition. The printed v0.19 date and PDF metadata date are both retained above. |

## 4. Crosswalk to Golden Core

| Golden Core question | Cookbook entry points | Proposed use | Qualification boundary |
|---|---|---|---|
| **GC-0 — Provenance** | Front matter, references, §24 version history | Preserve the PDF, hash it, record attribution, edition and claims to investigate. | A PDF is source evidence for what the author wrote, not evidence that repository code or history implemented it. |
| **GC-1 — Exact arithmetic** | §§2.7, 5, 9.4–9.5, 9.18, 12, 16, 21–22 | Catalogue Z, Q, Q(√3), Q(φ), and the cubic extensions; extract small identities and field reductions. | Do not combine fields or treat algebraic numbers as fixed-width hardware values without a separate profile and overflow/denominator contract. |
| **GC-2A — Controlled chirality** | §§4.3, 9.3, 9.9, 11.1, 20.6, 21 | Test transformations on explicitly typed state spaces; use determinant, covariance, labels and mirror correspondence. | Algebraic conjugation, coordinate parity, spatial reflection and chirality of a labelled object are different operations. |
| **GC-2B — Weighted geometry** | §§5, 7, 11, 17–18 | Recover exact metric/edge quantities and compare geometry-derived weights with independent law coefficients. | A quadrance or edge length is not automatically a dynamical weight. Define the relation explicitly. |
| **GC-3 — Aperiodic dynamics** | §§8, 15, 17, 20–21 | Reuse finite exact cells/polyhedra as substrate fixtures and geometry generators. | The cookbook does not provide a Penrose tiling Life model or evidence of aperiodic temporal behavior. Aperiodic tiling work remains a separate research track. |
| **GC-4 — Cost comparisons** | §§9–10, 12–14 | Compare operation counts, exact coefficient growth, storage, runtime and rendering-boundary conversion. | Mathematical operation counts alone do not establish CPU, GPU, FPGA, speed or energy advantages. |
| **GC-5/6 — ISA and hardware** | §§9–10 | Use validated recurring transforms to inform a later simulator or ISA proposal. | No cookbook content authorizes changing the qualified SPU-13 ISA/RTL or starting hardware work. |

## 5. Orientation and transformation ledger

Use the physical state space

```text
H = {(a,b,c,d) ∈ R⁴ : a+b+c+d=0}
```

with a fixed orientation and the inherited Quadray metric. For a permutation
matrix Pπ, the all-ones direction is fixed and H is invariant, so

```text
det(Pπ restricted to H) = sign(π).
```

Thus even coordinate permutations preserve orientation and odd permutations
reverse it. The active map and a passive relabelling must be distinguished: a
passive relabelling changes coordinate names and labels together and is not a
physical reflection. Central inversion −I has determinant −1 on H but +1 on
unconstrained R⁴. A single-coordinate sign flip has determinant −1 in R⁴ but
does not preserve H, so its restriction to physical 3D is undefined without an
additional, separately justified map.

This ledger is a mathematical review rule, not a ratification of every
transformation described in §§4 or 9. In particular, the code comment calling
`Quadray::cycle()` a “90° discrete rotation” needs its intended domain made
explicit: the bare four-cycle permutation is odd on H. It may be a coordinate
cycle, or it may need an accompanying operation to represent a proper spatial
rotation.

Do not use the sign of a quaternion or rotor coordinate as a handedness flag.
For Golden Core, record independently:

1. the linear map and its determinant on the physical subspace;
2. whether it preserves the exact metric;
3. its action on vertex/face labels;
4. its composition and inverse laws;
5. whether the operation is active, passive, or a map between two distinct
   substrates.

## 6. Optional reproduction menu

The following candidates are an optional menu, not a batch commitment or a
schedule. Select and authorize them individually or as a named tranche after
reviewing dependencies and available evidence. The expected checks define the
mathematical shape of each possible experiment; they do not assert that a run
has occurred or authorize implementation.

### Recommended first foundations tranche: SC-1 through SC-3

Treat these three candidates as one proposed, bounded foundations tranche:

1. SC-1 fixes Quadray gauge equivalence and the physical metric.
2. SC-2 establishes permutation parity, composition, and active versus passive
   label behavior on that physical space.
3. SC-3 checks which mirror and inversion operations are valid on each declared
   state domain.

Together they provide a mathematical base for Golden Core and a future “Baby’s
First Quadray” educational demo. This recommendation does not authorize
implementation or test execution.

SC-4 is a separate, later arithmetic-cost comparison. Its execution depends on
the foundations identities and a separately frozen cost model. SC-5 through
SC-8 remain optional follow-on candidates.

| ID | Construction | Inputs and exact expected checks | Existing-work connection |
|---|---|---|---|
| **SC-1: Gauge and metric** | Four tetrahedral basis vectors and a few rational points. | Add a common scalar to a point tuple and check unchanged physical position and quadrance. Check the metric matrix on H and exact positivity for nonzero physical vectors. | `software/common/include/spu_quadray.h`; `docs/QUADRAY_FOR_PROGRAMMERS.md`. |
| **SC-2: Labelled transform group** | A labelled tetrahedron; enumerate all 24 coordinate permutations. | Verify permutation composition, inverse, determinant sign on H, metric preservation, and the final locations of labels. Include an even rotation, an odd transposition, a 4-cycle, and active/passive relabelling controls. | Compare with the determinant claims and ROTC catalog in `docs/ROTC_KINEMATICS_PAPER.md`; resolve `Quadray::cycle()` terminology. |
| **SC-3: Mirror-operation domain** | Central inversion, one-coordinate negation, and a coordinate transposition. | Check which maps preserve H, which descend to the physical quotient, exact determinant where defined, and metric residual. Reject a map when it leaves the declared state space. | Cookbook §4.3; standard Quadray versus relaxed R⁴ distinction. |
| **SC-4: Rotation specialization** | One basis-axis F/G/H rotation and one generic zero-sum K(u) fixture. | Compare exact matrix application with an independent Fraction oracle. Verify determinant +1, metric preservation, composition order, inverse, output zero-sum, and exact operation counts. Compare generic 4×4 cost with the reduced 3×3 kernel; report field operations separately from scalar integer multiplies. | `software/lib/rational_robotics.py`; `software/common/include/spu_rational_robotics.h`; `ROTC` RTL/catalog. |
| **SC-5: Orientation predicate** | Four labelled rational points, including a coplanar case and odd/even relabellings. | Signed determinant is exact; zero iff degenerate; odd relabelling flips sign; even relabelling preserves sign; common gauge shifts do not change the result. | Cookbook §11.1 and future exact convex-hull/GC-2 geometry work. |
| **SC-6: CPU-to-GPU boundary** | A small tetrahedral/triangular mesh transformed in exact Quadray arithmetic. | Compare exact CPU transformed vertices against an independently specified Cartesian or clip-space boundary conversion; compare raster input/output under a fixed scene. Record quantization and depth behavior. | Current T1d consumes integer screen-space x/y/depth; this experiment would test a new software adapter, not silently change the device protocol. |
| **SC-7: Golden-field geometry** | A minimal φ-coordinate icosahedral or Penrose-related fixture. | Check φ²=φ+1 reductions, conjugation, exact incidence and edge quadrances; separately verify spatial parity and mirrored labels. | Existing IROTC/φ-plane work is a starting point for exact rotations, not a qualification of arbitrary φ-coordinate geometry. |
| **SC-8: Chiral snub pair** | One snub-cube or snub-dodecahedron fixture from §21, tested first as an unlabelled geometric point set and then with declared labels. | First test geometric superposability: does any orientation-preserving isometry map the unlabelled shape onto its mirror? Then test whether the same isometry can preserve the labels. Report these as separate outcomes; failure of label-preserving matching alone does not establish geometric chirality. Independently verify the stated minimal polynomial, coordinate identities, vertex/edge/face counts, and mirror correspondence. | Later than GC-1; the cubic field is not part of the initial Z[φ] baseline. |

## 7. Existing SPU work and compatibility

| Area | Existing repository evidence | Relationship to the cookbook |
|---|---|---|
| **CPU Quadray arithmetic** | `software/common/include/spu_quadray.h`, `software/spu_vm.py`, `software/common/include/spu_surd.h` | Provides exact Q(√3) operations and selected Quadray utilities. Its canonical `min=0` point representation and zero-sum ROTC displacement representation are distinct; conversions must be explicit. |
| **CPU robotics oracle** | `software/lib/rational_robotics.py`, `software/common/include/spu_rational_robotics.h` | Fraction-based F/G/H transforms, determinant/inverse/composition checks. The 104-check `software/tests/test_rational_robotics.py` passed during the preceding review; it does not by itself qualify the cookbook's generic K(u) kernel or every cookbook chapter. |
| **ROTC** | `docs/ROTC_KINEMATICS_PAPER.md`, `hardware/rtl/core/spu13/spu13_rotor_core_tdm.v`, `software/tests/test_rotc_vm_rtl_trace.py` | Qualified finite rotation catalog with exactness/alignment constraints. It is not the cookbook's complete arbitrary-axis floating-point rotor pipeline. Keep the catalog's det +1 transformations separate from impropers and coordinate relabellings. |
| **Golden φ transforms** | `docs/IROTC_SPEC.md`, `docs/ICOSAHEDRAL_QUADRAY_CATALOG.md`, `software/lib/irotc_catalog.py` | Exact φ-based icosahedral rotation catalog, with doubled-state/typestate and conjugate-catalog rules. Galois conjugation is an algebra automorphism, not automatically a spatial mirror. |
| **CPU graphics research** | `software/graphics/conventional_cpu/`, `software/graphics/rational_cpu/`, `docs/COMPARATIVE_GRAPHICS_LAB.md` | Offers conventional and rational comparison surfaces. A cookbook-style ABCD-native transform can be compared here before connecting it to hardware. |
| **Current GPU evaluation path** | `software/spu_gpu_eval/`, `software/gpu_vulkan/gpu_raster.comp`, `docs/gpu_scene_preview.md` | T1d scene vertices are integer screen coordinates plus depth; the Vulkan example rasterizes triangle edge functions. The cookbook's “GPU never sees XYZ” is specific to its described pipeline and is not the current SPU GPU data path. |

Golden Core should begin as a separate exact reference and geometry library.
Reusing a cookbook algorithm in the existing SPU path requires a named data
format, exactness/overflow profile, conversion boundary, independent oracle and
compatibility review. This reading map does not authorize any such integration.

## 8. Claims to keep as hypotheses

- That tetrahedral coordinates are universally more natural or efficient than
  Cartesian coordinates.
- That a coordinate representation removes every singularity of the chosen
  rotation parametrization.
- That a 9-multiplication count predicts fewer hardware resources or lower
  latency without a representation-aware cost model.
- That Janus polarity or negative-coordinate regions imply a physical extra
  arena or negative dimensionality.
- That exact construction of chiral solids explains natural chirality or
  morphogenesis.
- That the Cookbook's polyhedra, geodesics or jitterbug trajectories establish
  a physical law.
- That the cookbook's ABCD-native projection pipeline is already present in
  the maintained SPU GPU.

Negative results are useful: a failed metric-preservation check, a conversion
cost larger than the saved transform, or a missing orientation-preserving
labelled isomorphism should be recorded rather than repaired by changing the
fixture after observing the result.

## 9. Suggested reading order

1. §§2, 4 and 5 to freeze coordinate, quotient, metric and sign conventions.
2. §§9 and 11 to study transforms, determinant tests and exact predicates.
3. §§6, 10 and 14 to identify conversion boundaries and engineering controls.
4. §§8, 17, 20 and 21 for finite geometry fixtures, then qualify each claim
   independently.
5. §§15–19 and 22–23 as exploratory material after the basic arithmetic and
   geometry specifications are stable.

**Disposition:** This map adds the cookbook to Golden Core's reference set. The
reproduction menu remains optional; SC-1–SC-3 are the recommended first
foundations tranche, with SC-4 separate. This document
does not ratify a physical interpretation, qualify untested cookbook code,
modify the PDF, or change SPU-13.
