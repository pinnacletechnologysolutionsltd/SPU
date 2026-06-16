# Rational SOM and Nguyen Cluster Notes

Recovered conversation notes from the Mac-to-Linux migration loss. These notes are
not yet a hardware specification; they preserve the market framing, algorithm
direction, and candidate RTL staging for a deterministic topological classifier
built around SPU-13, Nguyen-style rational weighting, and a Kohonen/SOM layer.

## Recovered Conversation Outline

1. Market question: the multicluster quadrant plus rational Nguyen-weight layer
   gives SPU-13 a path into deterministic classification, not only exact
   rasterization.
2. Kohonen/SOM question: a SOM can help if it is rationalized into a
   quadrance-based, deterministic topological map.
3. RTL question: implement inference/BMU first, then optional topology memory
   and only later on-chip learning.
4. Hardware mapping question: quadrance, dyadic update factors, and hex/quadray
   neighborhoods turn SOM from a floating-point algorithm into a lean integer
   pipeline.

## Market Position

SPU-13 should not be positioned as a general GPU replacement. The plausible
market is narrower and more defensible:

> SPU-13 is a deterministic rational-geometry and information-classification
> accelerator for edge, embedded, safety-critical, and explainable systems.

The multicluster quadrant plus rational Nguyen-weight layer moves the machine
beyond rasterization. It suggests useful workloads in classification, clustering,
semantic partitioning, information-granule computation, and exact geometry.

The strongest positioning:

> SPU-13 is a deterministic rational coprocessor for exact geometric and
> granular classification workloads, deployable first on FPGA and later as
> RISC-V-adjacent accelerator IP.

The commercial claim should avoid competing on TOPS. SPU-13 competes on:

- exactness
- deterministic replay
- low-latency structure
- rational weights
- explainable classification
- custom geometric/classification operators
- bounded arithmetic behavior

## Nguyen Weight Caveat

The phrase "rational Nguyen weight algorithm" is ambiguous in public references.
Two nearby meanings were identified:

- Nguyen-Widrow weight initialization for neural-network convergence.
- Hung Son Nguyen-related tolerance rough set / document clustering work,
  including weighted similarity, approximate classification, and information
  granules.

For SPU-13, the second interpretation is more relevant because rough sets,
tolerance models, and granular computing map naturally onto deterministic
weighted similarity and cluster membership.

## Beachhead Applications

### Deterministic Edge Classification

A small explainable classifier for documents, telemetry, sensor events, safety
states, or symbolic streams. Rational weights and bit-exact decisions provide
the sales claim: same input, same classification, every platform, every time.

### Information-Granule and Rough-Set Acceleration

Hardware for exact granule membership, weighted tolerance, quadrant partitioning,
and deterministic cluster evolution. This is the strongest extension of the
Nguyen partitioning work into information classification.

### Safety-Critical Geometry and Classification

Medical, industrial, robotics, aerospace, simulation, and verification-adjacent
systems can value deterministic timing plus deterministic arithmetic.

### CAD, EDA, and Simulation Kernels

Exact collision, projection, lattice traversal, rational barycentrics,
constraint solving, snapping, geometric verification, and topology inspection.

### FPGA/ASIC IP Licensing

The near-term product should be FPGA demonstrator and licensable RTL/IP, not a
finished chip. Package as Verilog/SystemVerilog IP, simulator, benchmarks, and
demo workloads.

## Required Benchmark Pack

| Demo | Why it matters |
| --- | --- |
| Rational multicluster classifier | Explainable, reproducible classification |
| Quadray/Bresenham raster path | Exact geometry plus visual proof |
| Rotor closure / zero drift | Deterministic simulation credibility |
| Rough/tolerance set membership | Document, sensor, and event classification |
| FPGA latency/area/power report | Makes the design legible to hardware people |
| CPU/GPU float comparison | Shows why SPU-13 exists |

## Kohonen/SOM Direction

A Kohonen map or Self-Organizing Map can help, but it should be used first as a
diagnostic and topology layer rather than as the immediate core classifier.

The useful interpretation is:

> A deterministic topological classifier where clusters, weights, distances, and
> neighborhood updates are rational or surd-rational.

The SOM bridges:

- information classification
- spatial topology
- deterministic hardware

This makes SPU-13 easier to describe:

> SPU-13 is a deterministic rational processor for geometric and informational
> topology. It can rasterize exact quadray geometry and organize
> high-dimensional information into exact topological maps.

Avoid framing this primarily as an AI accelerator. The better framing is:

- deterministic topological classification
- rational self-organizing cluster fabric
- exact, inspectable, replayable, low-power classification and geometry

## Rational Quadrance SOM

Use SOM structure, but remove floating-point assumptions.

| Standard SOM | SPU-13 version |
| --- | --- |
| Euclidean distance | quadrance / rational weighted quadrance |
| float weights | rational Nguyen weights / fixed-denominator weights |
| 2D square or hex grid | quadrant, hex, quadray, tetrahedral, or IVM lattice |
| continuous learning rate | dyadic or rational schedule |
| approximate convergence | deterministic replayable convergence |
| opaque cluster map | inspectable topological memory |

For node `i`, feature `j`, input vector `x`, node weight `w`, and rational
tolerance/Nguyen weight `r`, score with weighted quadrance:

```text
Q_i = sum_j r_j * (x_j - w_ij)^2
```

The best matching unit is the node with minimum `Q_i`. This needs no square
root and no floating point.

The optional update rule remains SOM-like:

```text
w_i <- w_i + alpha * h_ci * (x - w_i)
```

But `alpha` and `h_ci` should be dyadic, rational, or LUT-based so the update is
deterministic and replayable.

The most SPU-native SOM should use hexagonal or quadray-neighborhood adjacency,
not only a conventional square grid. This aligns with 60-degree coordination,
quadrance, spread, and lattice topology.

## Hardware Efficiency Analysis

The rational quadrance formulation removes the heaviest hardware costs in a
standard SOM:

- no floating-point unit
- no square-root or CORDIC distance stage
- no transcendental decay function
- no branchy approximation path in the hot loop
- no Cartesian projection requirement for the topology layer

### Metric Path

A standard SOM uses Euclidean distance. The SPU-13 path uses quadrance:

```text
Q_i = sum_j r_j * (x_j - w_ij)^2
```

Silicon effect:

- `x_j - w_ij` is a subtractor.
- Squaring is an integer multiply.
- `r_j` is a rational/fixed-denominator feature weight.
- Accumulation is a MAC tree.
- BMU selection is a minimum comparator tree.

The rational Nguyen/tolerance weight `r_j` gives per-feature scaling without
leaving the integer/rational domain.

### Update Path

The SOM update remains:

```text
w_i <- w_i + alpha * h_ci * (x - w_i)
```

But the product `alpha * h_ci` should be encoded as either:

- a dyadic rational, where multiply becomes arithmetic shift plus optional add,
  or
- a small rational LUT value selected by training phase and neighborhood ring.

This makes training replayable. Given the same seeds, input sequence, LUT, and
rounding rule, the map evolves bit-for-bit the same way.

### Hexagonal and Quadray Topology

A square SOM has directional bias: axial and diagonal neighbors are not
equivalent. A hex map gives each internal 2D node six immediate neighbors in
natural 60-degree rings.

A quadray/IVM topology extends this into the SPU-13 geometric thesis. Logical
node coordinates can be represented as quadray tuples `[a,b,c,d]` with the usual
canonical form, and neighborhood steps follow tetrahedral/IVM adjacency instead
of Cartesian grid offsets.

The hardware claim:

> A quadray/hex rational SOM treats data topology as a discrete coordinated
> lattice rather than a floating-point approximation of a smooth manifold.

### Candidate Training-Step Pipeline

```text
Input vector x
    -> subtractor: x - w
    -> squaring ALU
    -> rational feature weight multiply: * r
    -> accumulator
    -> BMU selection: min Q
    -> neighborhood LUT
    -> dyadic/rational update scale
    -> updated weights
```

The BMU path is parallel across nodes. The update path only touches the BMU
neighborhood selected by topology radius and ring weights.

## Suggested Development Stages

### Stage 1: Visualization and Topology Test

Use the SOM to organize multicluster quadrant outputs into a map. If the
Nguyen-style rational weighting is meaningful, nearby cells should represent
semantically or structurally related information.

Demo claim:

> The information space organizes itself into rational geometric regions.

### Stage 2: Deterministic Classifier Front-End

Once the map stabilizes, every input can be assigned to a best matching unit:

```text
input -> rational weighted quadrance -> best map cell -> cluster label
```

This makes a replayable and inspectable edge classifier.

### Stage 3: Hardware Topology / Map Memory

Treat the SOM as a spatial layout of memory:

```text
rational feature vectors stored in lattice cells,
with neighborhood relations encoded directly in hardware
```

At this stage, the multicluster quadrant becomes a geometric memory fabric, not
only a software model.

### Stage 4: Optional On-Chip Learning

Do not implement this first. On-chip learning makes verification much harder.
For early demos, train or update the map offline, quantize to rational weights,
and load the trained map into FPGA memory.

If added later, the update datapath is:

```text
delta        = x - w_i
scaled_delta = rational_alpha * rational_neighbor_weight * delta
w_i_next     = w_i + scaled_delta
```

Candidate modules:

- `spu_som_update.v`
- `spu_neighbor_kernel.v`
- `spu_rational_decay.v`

## First RTL Target

The first practical RTL block should be:

```text
spu_som_bmu.v
```

Its job:

1. For each node, compute weighted quadrance to the input.
2. Select the node with minimum quadrance.
3. Emit `best_node_id`, `best_quadrance`, and confidence gap.

Confidence gap:

```text
gap = second_best_Q - best_Q
```

A large gap means strong classification. A small gap means ambiguity or boundary
case.

Candidate module breakdown:

- `spu_feature_ingest.v`
- `spu_rational_normalize.v`
- `spu_quadrance_accum.v`
- `spu_nguyen_weight.v`
- `spu_som_node.v`
- `spu_som_bmu.v`
- `spu_cluster_reduce.v`
- `spu_nguyen_cluster.v`
- `spu_quadrant_router.v`
- `spu_class_emit.v`

Candidate pipeline:

```text
spu_feature_ingest
    -> spu_rational_normalize
    -> spu_som_bmu
    -> spu_nguyen_cluster
    -> spu_quadrant_router
    -> spu_class_emit
```

Roles:

- SOM BMU finds the topological region.
- Nguyen cluster applies rational class weighting.
- Quadrant router maps the result into SPU-13 geometric/information quadrant.
- Class emit produces label, confidence, ambiguity flag, and optional
  visualization coordinate.

## Node Indexing Decision

Use a hybrid design:

> Store nodes in flat BRAM/SRAM arrays, but preserve native hex/quadray
> coordinates as sidecar metadata for neighborhood and visualization logic.

This is the best hardware compromise. Flat arrays are simple to synthesize,
burst, bank, and compare in parallel. Native coordinates keep the topology exact
without forcing memory to be physically addressed as a complicated lattice.

### Stage 1 Hex Map

For the first RTL BMU demo, use a fixed-size hex map inside a rectangular
envelope:

```text
node_id -> {valid, axial_q, axial_r, cluster_label, weight_base}
weights[node_id][feature_id]
```

Neighbor deltas for axial hex coordinates:

```text
{+1,  0}
{+1, -1}
{ 0, -1}
{-1,  0}
{-1, +1}
{ 0, +1}
```

Each `node_id` remains a flat address. The axial coordinates are used for:

- neighborhood ring lookup
- visualization position
- ambiguity/boundary reporting
- optional update eligibility

For small maps, `coord -> node_id` can be a ROM table or simple scan over valid
nodes in simulation. For hardware, prefer a generated inverse table:

```text
hex_index[q][r] -> node_id or INVALID
```

### Stage 2 Quadray/IVM Map

For a quadray map, keep the same flat storage model:

```text
node_id -> {valid, qa, qb, qc, qd, cluster_label, weight_base}
weights[node_id][feature_id]
```

Neighborhood deltas should be stored in a small topology ROM. The exact delta
set depends on whether the map uses tetrahedral vertex adjacency, IVM shell
adjacency, or a constrained quadray simplex.

Use:

```text
neighbor_delta_lut[topology_mode][dir] -> {da, db, dc, dd}
```

Then canonicalize after addition:

```text
candidate_q = canonicalize(q + delta)
candidate_id = quadray_index[candidate_q] or INVALID
```

For early FPGA builds, avoid a dynamic coordinate hash. Generate the inverse
index table offline and load it as ROM. That keeps timing predictable and makes
testbench comparison straightforward.

### Why Not Pure Native Addressing First

Pure native coordinate addressing is elegant, but it complicates:

- BRAM banking
- dense weight storage
- multi-node parallel reads
- synthesis-time map resizing
- comparator tree layout
- deterministic test vectors

Flat `node_id` addressing keeps the BMU datapath boring and fast. Native
coordinates remain authoritative for topology, but not for physical memory
layout.

## Architecture Sentence

Use this as the compact design claim:

> SPU-13 organizes information into rational topological regions using
> quadrance-based Kohonen mapping, then classifies those regions through a
> deterministic Nguyen-weighted multicluster engine.
