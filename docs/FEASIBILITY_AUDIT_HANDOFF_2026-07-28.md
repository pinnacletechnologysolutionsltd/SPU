# SPU-13 Candidate-Tranche Feasibility Audit Handoff

**Date:** 2026-07-28  
**Intended auditor:** Claude, working independently from this session  
**Status:** Read-only decision audit; no RTL, paper, roadmap, or build changes
are authorized by this handoff  
**Decision requested:** A separate verdict and priority for each of three
candidate work tranches

**Post-audit status (2026-07-29):** Complete. The independent verdict and the
two load-bearing corrections are recorded in
`docs/FEASIBILITY_AUDIT_VERDICT_2026-07-29.md`. Candidate B is `GO_ORACLE`, A
is `HOLD`, and C and Chaitin are `DOC_ONLY`.

## 1. Purpose and audit posture

This handoff asks for an evidence-backed feasibility audit of three ideas that
were discussed together but must not be treated as one architectural claim:

1. locality-aware FPGA floorplanning using a connectivity-derived order and a
   Hilbert mapping;
2. cyclotomic arithmetic for exact Fibonacci/Ising anyon calculations; and
3. exact tetrahedral-cage barycentrics and relative-4D BVH reconstruction.

The desired output is a decision that can be used to choose the next tranche,
not an implementation. Inspect the current working tree and primary sources,
challenge all claims, and prefer a bounded negative verdict over a speculative
positive one.

Do not infer that shared words or dimensions establish a structural mapping.
In particular:

- a categorical Hexagon equation is not hexagonal spatial geometry;
- a rank-4 cyclotomic coefficient vector is not a Quadray spatial vector;
- relative four-coordinate barycentrics inside an arbitrary tetrahedron are
  not automatically the SPU's fixed IVM basis; and
- an abstract floorplan anchor is not a legal FPGA primitive placement.

## 2. Required verdict format

Return one of these verdicts for each candidate:

| Verdict | Meaning |
|---|---|
| `GO_ORACLE` | The idea is coherent enough for a bounded software oracle and cost model, but not RTL. |
| `GO_EXPERIMENT` | Existing oracle/evidence is sufficient for a tightly scoped physical-design or RTL experiment. |
| `HOLD` | Plausible, but a named mathematical, toolchain, data, or resource dependency must be resolved first. |
| `DOC_ONLY` | Worth retaining as context or future work, but it does not presently justify engineering effort. |
| `NO_GO` | The proposed mapping is incorrect, duplicative, or lacks a credible SPU-specific advantage. |

For every candidate, report:

1. the strongest defensible claim;
2. every material correction or false premise;
3. the smallest mathematical/data domain closed under the proposed workload;
4. existing SPU components that are genuinely reusable;
5. missing components and likely resource/bandwidth bottlenecks;
6. the first falsifiable experiment;
7. a predeclared pass/fail gate;
8. the main reason not to proceed; and
9. confidence (`low`, `medium`, or `high`) with the evidence that would change
   the verdict.

Finish with a ranked recommendation across all three. Do not return a single
combined verdict.

## 3. Candidate A — locality-aware FPGA floorplanning

### Proposed claim

A weighted connectivity graph can be reduced to a declared one-dimensional
order and mapped to locality-preserving Hilbert anchors. After heterogeneous
resource legalization, that placement may reduce routing cost or variance on
selected SPU builds.

This is a placement heuristic, not a theorem and not an existing production
floorplan.

### Current repository state

The current worktree contains an uncommitted audit and repair of
`tools/floorplanner/`:

- `coordinate_transformer.py` now emits abstract CSV anchors and implements a
  genuine discrete Hilbert traversal;
- `generate_spu4_floorplan.py` emits the historical centre-plus-12-neighbour
  projection as abstract anchors only;
- `gowin_tang25k_grid.json` records a nextpnr X/Y bounding box, not a BEL
  legality database;
- `floorplanner_test.py` pins traversal, bounds, collision, and exact packed
  cell-name validation behavior;
- invalid generated Gowin `INS_LOC` files were removed; and
- the README states the missing graph-ordering, packed-cell association,
  resource legalization, application, and matched-build stages.

Primary repository anchors:

- `tools/floorplanner/README.md`
- `tools/floorplanner/coordinate_transformer.py`
- `tools/floorplanner/generate_spu4_floorplan.py`
- `tools/floorplanner/gowin_tang25k_grid.json`
- `tools/floorplanner/floorplanner_test.py`
- `hardware/boards/artix7/spu_a7_top.v`

Focused check:

```bash
python3 tools/floorplanner/floorplanner_test.py
```

### Known corrections that must survive the audit

- Bartholdi's `MOW` case study means **Meals on Wheels**. The cited primary
  paper does not define a `MOW-tree` data structure.
- A space-filling curve does not derive a useful netlist order. Connectivity
  extraction and partitioning are separate obligations.
- The FPGA fabric is heterogeneous. An X/Y bounding box does not establish a
  legal LUT, DSP, BSRAM, clock, or I/O site.
- The removed CST files did not target valid packed primitive names or complete
  Gowin BEL locations and were not consumed by an active build.
- No improvement claim is permitted without matched, multi-seed P&R evidence.

### Questions for the auditor

1. Is there a practical nextpnr pre-place or constraint path for the current
   Gowin and/or XC7 flows that can preserve a legal seeded placement without
   creating a private fork?
2. At what representation stage can stable packed-cell names and resource
   types be extracted?
3. Is recursive hypergraph partitioning plus Hilbert placement meaningfully
   different from, or likely to improve on, nextpnr's existing placement
   initialization for an SPU target?
4. Which one existing, rebuildable spin is small enough for a controlled
   experiment and large enough for the result to matter?
5. What metrics and seed count prevent an attractive single-seed anecdote?

### Minimum acceptable experiment gate

Before `GO_EXPERIMENT`, identify a build flow that can apply and report the
placement. A later experiment must compare the same synthesized netlist and
declared seeds, with at least:

- route completion;
- Fmax/WNS;
- total or critical-net wirelength;
- congestion/overuse;
- P&R runtime; and
- seed variance.

References:

- John J. Bartholdi III, *A Routing System Based on Spacefilling Curves*:
  <https://www2.isye.gatech.edu/~jjb/research/mow/mow.pdf>
- P. Banerjee et al., *FPGA Placement Using Space-Filling Curves: Theory Meets
  Practice*: <https://doi.org/10.1145/1596543.1596546>

## 4. Candidate B — cyclotomic anyon arithmetic

### Proposed claim

A typed polynomial-extension sidecar could evaluate selected anyon braid
coefficients exactly in a declared algebraic or modular domain, reusing the
SPU's deterministic multiplier, residue, and typestate methodology.

The proposed benefit is exact coefficient arithmetic. It is not based on a
spatial correspondence between Quadray geometry and a categorical Hexagon
diagram.

### Current repository state

The Lucas paper already states the limited, defensible future-work claim:

- `docs/LUCAS_MAC_PAPER.tex`, lines approximately 292-313, distinguishes
  `Q(phi)` from `Q(zeta_5)` and proposes a rank-4 cyclotomic MAC for Fibonacci
  `R` phases;
- `hardware/rtl/core/spu13/spu13_lucas_mac.v` is the existing rank-2 modular
  `Z[phi]/L_p` arithmetic block;
- `docs/IROTC_SPEC.md` and `knowledge/THEOREM_LICENSED_TYPESTATE.md` document
  denominator/catalog typestate lessons that must be reused rather than
  rediscovered; and
- `docs/SU3_COPROCESSOR_PAPER.tex` contains a modular complex-extension path,
  but that is not automatically characteristic-zero cyclotomic arithmetic.

Useful focused checks include:

```bash
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_icosahedral_catalog.py
python3 software/tests/test_irotc_chains.py
```

### Field-closure facts that must be independently rechecked

| Workload element | Candidate exact home | Consequence |
|---|---|---|
| Fibonacci `R` phases | `Q(zeta_5)` | Rank 4; canonical multiplication by `zeta_5` includes reduction, not a pure four-lane rotation. |
| Complete Fibonacci representation, integral gauge | `Z[zeta_5]` | Rank 4 with no denominators; requires the explicit weighted metric rather than the ordinary Euclidean metric. |
| Standard unitary Fibonacci `F` | contains `phi^(-1/2)`, outside `Q(zeta_5)` | Requires an additional radical/compositum or a carefully specified non-unitary gauge and metric. |
| Ising `F` | `1/sqrt(2)` in `Q(zeta_8)`, not an algebraic integer | Requires dyadic denominator/exponent tracking. |
| Full absolute Ising `R` phases | `Q(zeta_16)` | Rank 8 unless a precisely declared projective/global-phase quotient is sufficient. |

The existing real biquadratic domain
`Q(sqrt(3),sqrt(5)) = Q + Qsqrt(3) + Qsqrt(5) + Qsqrt(15)` does not contain
the required fifth-, eighth-, or sixteenth-root phase data merely by adding
`sqrt(15)`.

### Known corrections that must survive the audit

- Number fields are finite-degree extensions, not finite sets or finite fields.
- Exact unbounded symbolic arithmetic and exact fixed-width quotient-ring
  arithmetic have different semantics. A modular implementation can alias
  characteristic-zero amplitudes and needs new zero-divisor and period
  analysis.
- Minimal-polynomial reduction is representation semantics, not a parity
  check.
- Complex conjugation supports Hermitian norm checks; arbitrary Galois
  conjugation is not automatically a physical unitarity check or an error
  syndrome.
- Exact coefficient arithmetic does not remove exponential fusion-state growth
  in a general classical simulation.
- The `F` symbols are constrained by Pentagon coherence and `F/R`
  compatibility by Hexagon coherence; neither equation is a spatial lattice
  identity.

### Questions for the auditor

1. For one frozen Fibonacci convention/gauge, what is the smallest field or
   typed ring closed under the exact braid-generator workload?
2. Does a degree-4 `R`-phase sidecar have a useful standalone workload, or is a
   larger full-unitary engine required before it provides value?
3. Should the first oracle use characteristic-zero coefficients, modular
   images, or both with reconstruction bounds?
4. What coefficient-width and denominator growth occurs on representative
   braid words?
5. Which operations warrant dedicated instructions: root multiply,
   convolution/reduction, conjugation, norm/trace, denominator shift, or
   typestate checks?
6. Does this duplicate readily available exact-arithmetic software without a
   credible latency, determinism, or verification advantage?

### Minimum acceptable experiment gate

`GO_ORACLE` requires a frozen gauge and an independently derived exact model
that:

- encodes every required `F` and `R` coefficient without silent projection;
- verifies the relevant Pentagon and Hexagon identities exactly;
- verifies inverses and the intended unitary or weighted-metric invariant;
- reports field/ring type after every operation;
- measures coefficient and denominator growth over a declared braid corpus;
  and
- distinguishes characteristic-zero truth from any modular image.

If the modular image is required to be a field, its prime must satisfy
`p == 2 or 3 (mod 5)`, which makes `Phi_5` irreducible. The existing Lucas
modulus 521 is prohibited for that role: `521 == 1 (mod 5)`, `Phi_5` splits
completely, and the quotient contains zero divisors. M31 satisfies the
irreducibility condition.

Do not recommend RTL before that oracle and a cycle/resource cost model exist.

Primary references:

- Field and Simula, *Introduction to topological quantum computation with
  non-Abelian anyons*: <https://arxiv.org/abs/1802.06176>
- Kawagoe and Levin, *Microscopic definitions of anyon data*:
  <https://arxiv.org/abs/1910.11353>
- Experimental Fibonacci braid matrices in *Nature Physics*:
  <https://www.nature.com/articles/s41567-024-02529-6>

## 5. Candidate C — exact tetrahedral cages and relative-4D BVHs

### Proposed claim

The relative four-coordinate barycentric representation in AMD's
tetrahedral-cage ray-tracing paper has a genuine algebraic relationship to a
four-lane SPU datapath. A bounded oracle should test whether homogeneous exact
barycentrics, shared-face predicates, and 4D-bound projection offer a useful
SPU geometry or validation kernel.

The target is not a claim that the current FPGA replaces a modern GPU or can
ray trace hundreds of millions of triangles.

### Primary paper

Holger Gruen, Carsten Benthin, Michael Kern, and David McAllister, *Ray Tracing
Massive Amounts of Animated Geometry*, PACMCGIT 9(4), Article 49, July 2026,
DOI `10.1145/3820014`:

- author manuscript:
  <https://gpuopen.com/download/TetrahedralMeshes_AuthorsVersion.pdf>
- DOI: <https://doi.org/10.1145/3820014>

The repository should store a citation/link, not redistribute the author PDF;
its copyright notice permits personal use and disallows redistribution.

### Paper facts to recheck

- A coarse tetrahedral cage controls dense, connectivity-preserving animated
  triangle geometry; static per-tetrahedron micro-BLAS data can be reused.
- The fast instance-transform variant uses an epsilon to mitigate cracks and
  does not guarantee watertightness.
- The watertight variant stores local four-coordinate barycentrics and a 4D
  BVH, reconstructing 3D bounds and triangle vertices during traversal.
- On the reported workloads, that software fallback costs approximately
  2.3-3.2 times the memory and 19-80 times the render time of the fast variant.
- The paper obtains bitwise-consistent reconstruction through shared vertex
  IDs, fixed evaluation order, snapping, and floating-point execution. It does
  not present characteristic-zero rational arithmetic.

### Candidate exact representation

For barycentric coordinates `b_i` with `sum(b_i)=1`, centred coordinates

```text
q_i = 4*b_i - 1
```

satisfy `sum(q_i)=0`. To avoid division, use homogeneous integer weights
`w_i` and `W=sum(w_i)`:

```text
q_i = 4*w_i - W
W*p = sum_i(w_i*v_i)
```

Then `sum(q_i)=0` and `b_i=w_i/W`. This is only a candidate bridge:

- the four barycentric lanes are local to each arbitrary cage tetrahedron,
  not the fixed global IVM basis;
- `W` or an equivalent affine scale must be stored and typed;
- arbitrary input meshes and bone weights require a declared quantization or
  rational-input contract;
- coefficient growth, clipping, orientation tests, and memory traffic may
  dominate; and
- the current Davis Gate's 16-bit modular zero-sum check is not by itself a
  watertightness proof.

Relevant repository anchors:

- `knowledge/SPU_LEXICON.md`, Quadray and Davis Gate entries;
- `knowledge/MATHEMATICAL_FOUNDATIONS.md`;
- `knowledge/RATIONAL_SHADER.md` (treat status notes as claims to audit against
  the active RTL tree);
- `hardware/rtl/gpu/`;
- `hardware/rtl/core/shared/spu_quadray_regfile.v`; and
- `hardware/rtl/core/shared/davis_gate_dsp.v`.

### Questions for the auditor

1. Is homogeneous rational/dyadic barycentric encoding materially better than
   ordered float32 for the paper's actual watertightness failure modes?
2. Can exact face/edge/vertex ownership and clipping be achieved with bounded
   integer predicates without prohibitive bit growth?
3. Is the centred zero-sum encoding useful, or does a direct `w[4]+W`
   representation avoid unnecessary conversion?
4. Which kernel is realistically accelerable on the current FPGA: cage update,
   barycentric reconstruction, 4D-bound projection, exact clipping, or a
   validation/reference stream?
5. What BRAM bandwidth and multiplier count would one ray/node traversal need?
6. Is the plausible role an online accelerator, an offline preprocessing
   engine, or only an oracle/reference checker?
7. Does the proposed kernel offer publishable differentiation from standard
   robust predicates and fixed-point barycentric hardware?

### Minimum acceptable experiment gate

`GO_ORACLE` requires a small exact host model with adversarial adjacent
tetrahedra that:

- reconstructs the same shared face/edge vertex through both tetrahedra;
- tests exact face ownership and triangle clipping;
- treats Appendix A's interval-enclosure result as representation-independent
  background, not as evidence for exact arithmetic;
- compares exact/dyadic and float32 paths on crack-producing cases;
- records numerator/denominator and bit-width growth; and
- includes a bandwidth/cycle estimate for one narrowly selected FPGA kernel.

Do not recommend a full ray tracer as the first implementation.

## 6. Context item — Chaitin paper

Gregory Chaitin's *How Real Are Real Numbers?* may be retained as philosophical
context for finite description and computability. It is not a technical
foundation for replacing IEEE-754, evidence that physical reality is discrete,
or an engineering tranche. Unless the auditor finds a concrete missing use,
classify it `DOC_ONLY` and exclude it from the priority ranking above.

Reference: <https://arxiv.org/abs/math/0411418>

## 7. Cross-candidate questions

After the individual verdicts, answer:

1. Which candidate is most native to the implemented SPU-13 rather than merely
   compatible with exact arithmetic in general?
2. Which has the smallest credible experiment and shortest path to a decisive
   negative or positive result?
3. Which would consume scarce RTL, P&R, BRAM, DSP, documentation, or
   publication capacity needed by already open milestones?
4. Are any candidates better implemented entirely in host software?
5. What order, if any, should be used: documentation, oracle, cost model,
   synthesis experiment, silicon?
6. Name one candidate that should explicitly not be started now, even if it is
   mathematically interesting.

The final recommendation must respect current project priorities and known
toolchain limitations in `AGENTS.md`, `docs/SESSION_HANDOVER_2026-07-28.md`,
and `docs/SPU13_IDENTITY_AND_BOUNDARIES.md`.

## 8. Copy-ready prompt for Claude

```text
Perform the read-only feasibility audit specified in
docs/FEASIBILITY_AUDIT_HANDOFF_2026-07-28.md.

Inspect the current worktree and every listed repository anchor. Read the three
primary-source sets linked by the handoff where needed. Do not implement code,
edit documentation, run long synthesis/P&R jobs, or accept the handoff's
mathematical claims without independently checking them.

Return a separate verdict for Candidate A (floorplanning), Candidate B
(cyclotomic anyon arithmetic), and Candidate C (tetrahedral cages) using only
GO_ORACLE, GO_EXPERIMENT, HOLD, DOC_ONLY, or NO_GO. For each, provide the nine
required findings, a first falsifiable experiment, and a predeclared pass/fail
gate. Then rank the candidates against current SPU priorities and name one that
should not start now.

Treat Chaitin as a context item, not a fourth engineering candidate, unless you
find concrete evidence to the contrary. Clearly distinguish verified repository
capabilities, mathematical derivations, inferences, and speculation. Cite exact
file paths/lines and primary sources for material claims.
```

## 9. Acceptance criteria for the audit

The handoff is complete only if the returned audit:

- gives three independent verdicts rather than endorsing a theme;
- catches the known category/spatial, coefficient/coordinate, and
  anchor/placement type errors;
- checks current source and test status rather than trusting prose summaries;
- proposes no RTL before the relevant oracle and cost gates;
- identifies a smallest falsifiable next step for every non-`NO_GO` verdict;
- reports evidence that could reverse each verdict; and
- ranks the work against existing open milestones rather than assuming all
  attractive ideas should proceed.
