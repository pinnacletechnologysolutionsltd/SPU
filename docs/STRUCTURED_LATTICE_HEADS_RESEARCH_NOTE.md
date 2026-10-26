# Exact Structured Lattice Heads: A D4-First Research Probe

Date: 2026-09-28  
Status: **PARKED — research note only**

This note defines a falsifiable research question. It authorizes no RTL,
training, synthesis, route, or hardware run. An experiment needs a separate
contract with frozen data, commands, budgets, and stop conditions.

> Can a small family of exact structured lattice maps replace some learned
> dense head projections on a named retrieval task, while retaining useful
> rankings and reducing measured implementation cost?

The proposal is a partial replacement hypothesis. It does not assert a
Transformer equivalent or a general quality or cost improvement.

## Mathematical boundaries

Let `L` be a declared integral lattice with a chosen basis and metric.
The following constructions have different types and must be specified
separately:

| Construction | Output | Exactness condition |
|---|---|---|
| Choose a subset of simple roots | A root subsystem and parabolic subgroup | This choice alone defines no projection map. |
| Orthogonally project onto a real root span | A point in that real span | It need not lie in `L` or a selected sublattice. |
| Form `L / L_sub` | A coset | A coset is not an orthogonally projected vector. |
| Select integral basis coordinates | An integer tuple | The basis and output lattice must be declared. |
| Apply a Weyl element `w` | A lattice vector when `w` preserves `L` | Inverse and metric preservation do not compress dimension. |
| Canonicalize a Weyl orbit | A representative or descriptor | Generally a piecewise map, not a linear projection. |

For example, take `L = Z^2` and `L_sub = Z(1,1)`. The orthogonal
projection of `(1,0)` onto the line spanned by `(1,1)` is
`(1/2,1/2)`, outside `L`. Meanwhile `Z^2 / L_sub` contains cosets,
which are different objects from points on that line. Calling either
operation an *integral projection* would need an additional construction
and proof.

An integral linear head can be specified as `P_h: L -> M_h`, with an
integer matrix in the declared integral bases. Coordinate selection,
permutation, sign changes, sparse root operations, and direct-sum component
selection where an actual integral direct sum exists are candidates.
Coset labels and chamber descriptors are exact discrete outputs, but are
not generally linear homomorphisms. Any normalization, rounding, or
divisibility restriction must be explicit.

## A necessary head-diversity falsifier

For a Weyl isometry `w` and Euclidean inner product,

```text
<wq, wk> = <q, k>                 ||wq - wk||² = ||q - k||²
```

Thus applying the same `w` to both query and key before an unchanged
full-dimensional score yields exactly the same ranking. Multiple such
"heads" have no ranking diversity. Likewise, if `C` is a *complete*
canonical representative of a Weyl orbit, then `C(wx) = C(x)`; a
`C(w_h x)` head is independent of `h`.

A useful structured head needs a declared information-changing or
asymmetric step, such as coordinate selection after `w_h`, a bounded
non-invariant descriptor, a head-specific metric, or distinct query/key
maps. Its exactness and hardware cost then have to be assessed as a
whole. Chamber canonicalization may still be useful for routing or
invariance, but cannot by itself create distinct views of one orbit.

For D4's signed permutations, coordinate selection after a shared word is
exactly selection of a **pulled-back input mask**. For asymmetric words with
output mask `S`, the masked score depends on both `T=w_Q^{-1}(S)` and the
relative transform `R=w_Q^{-1}w_K`; recording `R` alone loses the mask.
The [software P0 audit](../spu_strategy/contract_d4_structured_head_retrieval_p0_2026-09-28.md)
tests these identities exactly. Complete chamber folding is reserved for a
separate invariance/routing study.

## First experiment: D4 structured views

Use the existing [D4 root-reflection probe](../spu_strategy/contract_spu_d4_root_reflection_probe_2026-09-14.md)
as the arithmetic starting point. Its fixed simple reflections are swaps
and a signed swap in four integer coordinates. The probe does not yet
establish a useful attention head or a routed D4 head accelerator.
Every D4 reflection word is an even signed permutation. Thus any benefit
over a matched even signed-permutation baseline must come from word encoding,
selection, or search, rather than a larger transform family.

Freeze a small four-coordinate integer embedding and a retrieval dataset.
For each candidate head, define a short fixed reflection word `w_h`, an
ordered coordinate subset `S_h`, and an exact score, for example:

```text
H_h(x) = select_S_h(w_h x)
score_h(q,k) = -sum_i (H_h(q)_i - H_h(k)_i)^2
```

This score still contains products. The reflection and selection can be
cheap; the full retrieval circuit is not automatically multiplier-free.
If an exact comparison can use a smaller arithmetic domain, prove its
ranking equivalence and width bounds first. Do not hide quantization or
overflow in the score.

The first software probe should freeze the data split, embedding, word
length, coordinate subsets, score, integer widths, tie rule, and top-k.
Compare at least:

1. identity and full-dimensional isometric views (zero-diversity controls);
2. coordinate selection without reflections;
3. random even signed permutations plus the same selection;
4. D4 reflection words plus selection;
5. a matched dense integer projection, with a learned version only when
   the search or training budget is also frozen.

Measure top-k recall, nearest-neighbour agreement, ranking correlation,
ties, and per-query overlap among heads. Count distinguishing winners or
neighbours, not only aggregate accuracy. Test whether distinct reflection
words actually give distinct rankings after selection. A failed diversity
test closes the multi-head claim for that construction even if all exact
arithmetic checks pass.

The frozen [P0 audit](../spu_strategy/contract_d4_structured_head_retrieval_p0_2026-09-28.md)
found distinct asymmetric rankings but weak reference retrieval. The subsequent
[P1 candidate-fusion audit](../spu_strategy/contract_d4_structured_head_fusion_p1_2026-09-28.md)
held those heads fixed and tested top-1/2/5/10/20 intake with union, voting,
reciprocal-rank fusion, and rank-sum selection before exact full-space reranking.
All 20 D4 points used more mean candidates while capturing fewer reference
top-5 neighbours than their matched mask-only controls; signed-permutation
controls matched D4 exactly. This **closes the fixed D4 retrieval construction
on the frozen task**. It is no basis for D4 retrieval hardware or an E8
retrieval advance. Canonicalization for invariance/routing and compact word
encoding remain separate questions.

Before a hardware claim, measure LUTs, FFs, DSPs, BRAM, critical path,
latency, throughput, state bytes, and data movement on the same target.
Include reflection word length, selection muxes, control, scoring, and
top-k logic. A fixed word may compile to wiring; runtime-selected words
need control and muxes. Chamber reduction has comparison and routing cost.
Physical energy is reported only when measured.

## Staged decision path

```text
D4 exact-map and retrieval probe
  -> E8 structured views, if D4 gives useful distinct rankings
  -> exact similarity and top-k hardware comparison
  -> SOM or bounded decision layer
  -> scoped softmax-free attention comparison
  -> separate Lorentzian/hyperbolic hierarchy probe
```

At the E8 stage, specify the integral basis, root action, descriptor,
widths, and overflow behavior before claiming sparse hardware. E8 has
more possible symmetry actions, but their utility and circuit cost remain
experimental.

For a later Lorentzian probe, compare exact Lorentzian and Euclidean
ranking on a frozen hierarchy or tree-retrieval task. Record retrieval
quality, depth preservation, arithmetic width, products, overflow, and
hardware cost. An integer Lorentzian inner product is generally a sum of
products. Sparse constrained roots might reduce that cost, but this must
be demonstrated.

Affine Weyl translations are deferred. They supply group actions, not
Transformer positional encoding or shift invariance automatically. Any
such property needs a specified encoding and an equivariance or
invariance test.

Leech-lattice work is deferred as well. The Leech lattice is rootless;
it cannot contain an ordinary norm-2 `E8 ⊕ E8 ⊕ E8` root sublattice.
The root system `E8^3` belongs to a different 24-dimensional Niemeier
lattice. This does not exclude *scaled* E8 embeddings in the Leech
lattice, which are a different construction. No ready-made three-head
Leech decomposition is claimed here.

## Sources

- [Existing SPU D4 reflection probe](../spu_strategy/contract_spu_d4_root_reflection_probe_2026-09-14.md)
- [Attention Is All You Need](https://papers.neurips.cc/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf)
- [Borcherds, *The Leech lattice*](https://math.berkeley.edu/~reb/papers/leech/leech.pdf)
- [Griess and Lam, *Rootless pairs of EE8-lattices*](https://arxiv.org/abs/0806.2375)
