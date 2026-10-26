# D4/E8 symmetry discovery: documentation preparation

```bash
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_d4_e8_symmetry_discovery_preparation_2026-10-13.md docs/ALGEBRAIC_GEOMETRIC_MACHINE_RESEARCH_DIRECTION.md
```

Date: 2026-10-13. Status: DRAFT / PREPARATION ONLY; D0–D3 NOT RUN.
Scope: this document and the architectural research-direction note only.
Roles: specification, analytical review and documentation audit performed
sequentially. No new oracle implementation, training, RTL or FPGA campaign.

## Purpose and relationship to existing evidence

Investigate whether higher-dimensional lattice symmetries provide useful native
operations or compact transformation representations for future SPU generations.
Organize AOR as representation, SGN as communication, and D4/E8 as symmetry.
These are complementary research questions; no integrated machine is established.

Retain the [D4 canonical-decision evidence](../docs/D4_CANONICAL_DECISION_RESEARCH_NOTE.md)
and [P1b results](../docs/D4_CANONICAL_DECISION_P1B_RESULTS_2026-10-10.md).
The [structured-head comparison](contract_d4_structured_head_fusion_p1_2026-09-28.md)
closed its frozen retrieval construction without hardware promotion. The
[equal-norm directional decision proposal](contract_d4_equal_norm_direction_p2_2026-10-11.md)
is a separate task with its own authority and gates. This draft neither restarts
closed experiments nor changes their budgets or evidence status.

## Mathematical representation and falsifiers

Propose an independent reference in Q^4 for D4 and Q^8 for E8, with exact
rational arithmetic and explicit coordinate ordering. Root coordinates have
squared length 2. Freeze the coordinate convention, root enumeration and a
separate defining-lattice membership predicate before implementation.
Reference constructions must not depend on an SPU packing or Quadray converter.

Use [Sage's type-D reference](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/type_D.html)
and [type-E reference](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/type_E.html)
as mathematical source references, not installed runtime dependencies or local
campaign evidence. Type-E ambient coordinates include half-integers; this
requires exact rational handling or a proven scaled-integer encoding.

Two independent four-component zero-sum Quadray blocks have dimension six.
An invertible rank-eight E8 encoding cannot be inferred from that constrained
domain. Require an explicit rank-eight basis and reversible representation map;
retain the rank-six construction as a negative control. D4 likewise requires
four independent dimensions; one zero-sum Quadray block alone is insufficient.

For a normalized root alpha, use s_alpha(x)=x-(x dot alpha)*alpha.
Independently compare with the exact matrix I-alpha*alpha^T. No floating point.
For doubled coordinates X=2x and A=2alpha, derive
X'=X-((X dot A)/4)*A. Define and check divisibility and lattice membership
before treating this as integer-only execution. Never apply the normalized
formula unchanged to roots whose squared norm became 8 after scaling.

Closure means reflection permutes the complete root set and preserves lattice
membership. It does not mean roots are closed under arbitrary addition.
Finite coordinate boxes are generally not reflection-closed: compare outputs
exactly without clipping and freeze intermediate-growth limits separately.
Weyl reflections, outer automorphisms and triality operations require separate
definitions; do not assume a selected reflection set implements all three.

## Proposed gates

| Gate | Bounded deliverable | Acceptance evidence |
|---|---|---|
| D0 algebra | Independent D4/E8 reference root sets | Exact counts 24/240, squared norms 2, opposite roots, inner-product distributions, rank 4/8 and lattice membership |
| D1 symmetry | Exact reflections and named generators | All 24×24 and 240×240 root/reflection pairs; closure, norm preservation, involution, explicit inverse and matrix agreement |
| D2 SPU mapping | Reviewed subset expressed with existing primitives | Reversible conversion, exact operation equivalence, rank preservation, failure semantics and conversion costs |
| D3 comparison | Immediate vectors, matrices, words and proposed descriptors | Identical transformations/inputs; actual operation counts, growth, storage, normalization and materialization costs |

D0 root-set reflection closure is reported with D1; rank/count checks alone
do not establish it. Exhaustive root checks establish a finite-domain result;
extend claims to arbitrary lattice vectors only with a separate proof or a
declared bounded vector corpus. Do not enumerate the full E8 symmetry group
merely to establish these root/reflection checks.

For D1, freeze generator IDs/order, word lengths, vector corpus and composition
convention before running. Include zero, roots, negative roots, sums and
non-root lattice vectors. Check linear-action equivalence and reversals.
Controls must reject missing/duplicated roots, wrong sign/parity, rank loss,
wrong scaling, nonintegral quotient, transposed composition order and a
non-involutive candidate. A passing root count cannot substitute for rank.

## Fair comparison and AOR connection

Use a conventional signed-permutation baseline for the corresponding D4 Weyl
actions; prior D4 word results already warn against charging one representation
less for the same transformation. AOR's Pell representation does not automatically
encode these groups. Any new descriptor needs its own semantics and equality rule.

Compare applying each reflection, composing a matrix, retaining generator words,
and a compact descriptor only if one is defined. Include construction, reduction,
equality, inverse, composition and materialization costs at identical endpoints.
Preserve orientation metadata when the task is equivariant; arbitrary canonical
tie-breaking does not establish stabilizer-compatible action reconstruction.

Report scalar-operation vectors and operand widths, denominator/coefficient
growth, live and stored bits, normalization, lookup tables and temporary space.
Charge deferred work when a word is evaluated or a descriptor materialized.
Word length is not bounded merely because the represented group is finite.
Require a proof of any compactness/worst-case-operation bound, plus software
comparisons; report no advantage when conventional representations match or win.

## Priority, execution authority and evidence

Keep backend legality/CPU placement first, AOR-S1 proof/oracle review next,
the separately authorized SGN mesh/cost gate separate, and this track in
documentation preparation. Change no active source manifest or campaign budget.

Before D0 execution, freeze isolated source/test paths, independent reference
boundaries, fixtures, negative controls, exact runnable commands and an
owner-authorized attempt/time budget. This draft grants none of those executions.
Use the detached runner for work expected to exceed 60 seconds, with durable
terminal markers and no implicit retries. No launch command is proposed yet.

Mathematical correspondence, comparative software cost and physical realization
are separate claims. No ISA extension, integration, resource, timing, power or
board claim follows from D0–D3. E8 is optional discovery scope for future
generations, not a requirement for the existing SPU-13 CPU or GPU.
