# D4 Canonical Decisions: Symmetry Reduction Before SOM

Date: 2026-09-28  
Status: **EXACT SOFTWARE P0/P1 PASS — synthetic decision only; no hardware claim**

## Research question

When a required decision is invariant under a known D4 Weyl symmetry, can
exact orbit canonicalization reduce deterministic decision/codebook state
without changing that decision?

This is a separate branch from the closed fixed-head D4 retrieval experiment.
The role of symmetry here is quotienting and bounded decision routing, not
imitating learned attention projections. The proposed order is exact
canonicalization, then decision usefulness, then RTL architecture and timing.

## When folding is legitimate

Let `W = W(D4)` act on state `x`. A scalar action label can be decided on a
canonical representative `C(x)` only when its intended meaning is invariant:

```text
a(w x) = a(x)  for every relevant w in W.
```

Mathematical symmetry of coordinates alone does not establish this task
condition. If coordinates identify physical motors, a coordinate permutation
also permutes which motor is addressed. A complete fold that discards the
orientation loses information needed for a labelled motor command.

For a vector or otherwise equivariant action, retain a transform `g_x` with
`g_x x = C(x)` and reconstruct the physical action as

```text
A(x) = g_x^-1 F(C(x)).
```

**Wall condition:** If several transforms map `x` to the same chamber
representative `c`, their difference lies in `Stab(c)`. A deterministic
tie rule gives reproducible metadata but does not alone make `A` equivariant.
The canonical action `F(c)` must be fixed by every element of `Stab(c)`, or
the action definition must retain additional task-specific orientation
information. Under the stabilizer condition, changing the valid metadata
does not change the reconstructed action.

## Exact D4 P0 domain

Use the root order already established by the
[D4 reflection probe](../spu_strategy/contract_spu_d4_root_reflection_probe_2026-09-14.md):

```text
alpha0 = e0-e1    alpha1 = e1-e2
alpha2 = e2-e3    alpha3 = e2+e3
```

Choose the closed fundamental chamber with
`<c,alpha_i> >= 0`, equivalently
`c0 >= c1 >= c2 >= |c3|`. Start with the bounded lattice domain

```text
D4_B = {x in Z^4 : each x_i in [-4,4], sum_i x_i even}.
```

It has 3,281 states and is closed under the 192 even signed permutations of
`W(D4)`. This bound includes generic full-size orbits as well as repeated
coordinates, zeros, walls, and nontrivial stabilizers. Use unbounded Python
integers for the P0 oracle; RTL widths and overflow are later questions.

Enumerate all 192 signed permutations and their even sign patterns. For
every `x`, enumerate its transformed states, select the unique vector in
the closed chamber as `C(x)`, and choose the lexicographically first
transform among those mapping `x` to `C(x)` as deterministic metadata.
The [P0 contract](../spu_strategy/contract_d4_canonical_decision_p0_2026-09-28.md)
freezes the transform encoding and exact checks.

P0 must establish exact orbit invariance `C(wx)=C(x)`, idempotence,
chamber membership, lattice parity and norm preservation, inverse-metadata
reconstruction, and orbit/stabilizer counts satisfying
`|Orb(x)|*|Stab(x)|=192`. A failed equality is a specification or
implementation defect, not a statistical accuracy miss.

The group order is an upper bound on a generic orbit size, not a promised
codebook reduction. Wall and repeated-coordinate states have larger
stabilizers and smaller orbits. SOM node count also depends on the task,
distribution, noise, decision boundary, and training objective.

## Separate later decision experiment

Do not mix nearest-lattice quantization into P0. Compare the following in
a later, separately frozen P1 on tasks with explicit label symmetry:

```text
raw state -> SOM
raw state + symmetry augmentation -> SOM
canonical state -> SOM
canonical state -> non-SOM prototype/codebook classifier
raw state -> capacity-matched decision model
```

Freeze base chamber representatives and invariant action labels, then make
observations `w c_i` with controlled transformations. Split by **base
representative**, so held-out observations include unseen underlying states.
Measure codebook entries at a fixed target decision error; report training
cost, BMU arithmetic, confidence/runner-up gap, and memory traffic. An
off-lattice noisy branch with explicit `Q_D4(x)` belongs after the exact
on-lattice result, so quantization and folding effects remain separable.

The D4 fold may compile to comparisons, swaps, and sign operations. Nearest
lattice-point quantization and conventional squared-distance BMU scoring
can still require products. No multiplier-free pipeline, 192-fold SOM
compression, single-cycle 100 MHz operation, or 120-LUT implementation is
claimed. Hardware work follows only if the decision experiment is useful.

## P0 observed result

The [P0 contract](../spu_strategy/contract_d4_canonical_decision_p0_2026-09-28.md)
records the 2026-09-29 exact-oracle run. All 3,281 bounded states reduce to
57 unique closed-chamber representatives under the 192 signed permutations.
Every state/action pair passed canonical invariance and equivariant-action
reconstruction. The non-stabilizer-fixed `F(0)=e0` control was rejected.
This is a property of the frozen bounded domain and action, not a SOM
compression or hardware-cost measurement.

The separate [P1 decision contract](../spu_strategy/contract_d4_canonical_decision_p1_2026-09-29.md)
freezes a five-fold, base-representative-held-out comparison of raw,
augmented, and canonical SOM/codebook learners on an exact three-class
invariant task. Its primary measure is representative-weighted decision
error against stored codebook bits. P1's exact software run passed: at
`K=32`, canonical SOM had 22.8% representative-weighted held-out error,
canonical codebook 28.1%, raw codebook 39.7%, and augmented raw SOM 44.6%.
Canonical SOM did not lead at every capacity. The direct norm-threshold
rule solved this synthetic label exactly with zero prototypes, so the
learned curves are a controlled storage/learning comparison, not evidence
of a general architectural advantage. The off-lattice task remains a
separate follow-on.


## P1b noisy-input tranche (2026-10-10)

The [P1b contract](../spu_strategy/contract_d4_canonical_decision_p1b_2026-09-29.md)
is now authorized for preparation and one 1,800-second software experiment.
A fresh [P0 oracle](../build/d4_canonical_decision_p1b/p0_preflight_01.json) passes.
The defining quantizer visits all 3,281 bounded candidates for each of 114
seeds; an independent parity-based oracle checks all 21,888 transformed
observations. Both reject a deliberately tied nearest point. The frozen
28 projection changes, 16 norm-label crossings and seed collision counts agree
with the contract. These are corpus checks, not learned-model results.

Eight arms retain the same five folds and six capacities. Quantized codebooks
use 18 bits per node; raw noisy controls use 34. Report both profile curves,
their equal-weight mean and the separate base-orbit-weighted metric. Matched
capacity comparisons do not establish matched-bit comparisons. The direct
noisy and quantized norm rules and empirical quantized-input majority error
remain controls. Canonicalizer, quantizer, training workspace and hardware
costs are unmeasured. No RTL or silicon evidence is claimed.

The full experiment completed: [P1b results and complete curves](D4_CANONICAL_DECISION_P1B_RESULTS_2026-10-10.md). Canonical codebooks improve over raw quantized codebooks at larger capacities, but the simple norm controls beat all learned arms. Full tranche qualification passed for the frozen software snapshot; no hardware promotion follows.
