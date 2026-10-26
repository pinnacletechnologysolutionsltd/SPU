# Exact Symmetry-Canonical Memory and Transformation Consistency in the \(D_4\) Weyl Group

**Working manuscript — 2026-10-14. Internal draft; not submission-ready.**

**Authors and affiliations:** to be completed by the human contributors after
reviewing contribution records. No authorship is implied by this placeholder.

**Status:** Results below are tied to the source and artifact hashes in
Section 8. The experiments are bounded software references. This manuscript
does not claim a new form of machine intelligence, a general memory advantage,
or hardware acceleration.

## Abstract

We describe a small deterministic software reference for exact symmetry-aware
associative retrieval and transformation-cycle checks under the Weyl group
\(W(D_4)\). The implementation enumerates the 192 even signed permutations of
four coordinates, selects a lexicographically canonical representative for
each orbit, and retains a transformation witness so orientation-sensitive
actions can be reconstructed. A stabilizer condition rejects actions that
cannot be defined consistently on a symmetric input. A separate typed
relationship layer checks exact ordered products along explicitly supplied
closed paths, with declared expectations that may be identity or nonidentity.

Three deterministic studies are reported. D4-SYM-0 checks canonical invariance
and witness reconstruction over 3,281 bounded integer states and tests one
generic 192-element orbit. D4-MEM-1 compares raw exact-key, symmetry-augmented,
canonical, and query-time group-aware associative memory on two fixed orbits.
All three symmetry-aware strategies retrieve all 242 supported query
occurrences and reject the one non-equivalent query. D4-CYCLE-0 checks seven
cycles in a consistent four-frame graph, a controlled edge corruption, and a
prescribed nonidentity holonomy. These results establish exact behavior for
the specified finite fixtures. The memory comparison exposes tradeoffs in
the selected serialization and operation-count models; it does not establish
latency, energy, general compression, learning, or hardware benefit.

## 1. Introduction

When a task treats transformed configurations as equivalent, storing each
configuration independently can duplicate associations. A finite group
action offers a precise way to define that equivalence. If responses depend on
orientation, however, discarding the transformation can discard information
needed to reconstruct the response. Separately, relationships between local
coordinate frames can be checked by composing their transformations around
closed paths. These are established mathematical ideas, used in areas
including equivariant learning and group synchronization [2, 3].

This paper records an exact, auditable implementation of three related
operations for the rank-four root system \(D_4\): canonical orbit addressing,
witness-based action reconstruction, and exact cycle-product checking. The
work is motivated by a longer-term SPU research programme on persistent
adaptive state, but no learning algorithm or persistent soul is evaluated
here.

The contribution is an implementation and a frozen finite-workload
comparison, not a new group-theoretic result. The reference makes conventions
that are easy to leave implicit—group meaning, action order, witness
tie-breaking, stabilizer validity, edge direction, and expected holonomy—
executable and testable. Its negative and limiting results are part of the
record: canonical memory is compact relative to explicit augmentation in this
fixture, but not relative to the two-entry raw or group-aware serialization;
its enumeration costs are substantial under the declared operation model.

## 2. Mathematical setting

### 2.1 The group \(W(D_4)\)

Here \(D_4\) denotes the rank-four root system, not the eight-element
dihedral group of a square. Its roots are

\[
  \Phi(D_4)=\{\pm e_i \pm e_j : 1\leq i<j\leq4\}.
\]

The Weyl group is represented as the even signed permutations of four
coordinates. A descriptor is \(g=(p,b)\), where \(p\in S_4\),
\(b\in\{0,1\}^4\), and \(\sum_i b_i\) is even. Its action on an integer
vector is

\[
  (g x)_i=(-1)^{b_i}x_{p_i}.
\]

Thus \(|W(D_4)|=4!\,2^3=192\). These transformations are exact on the integer
vectors used in the experiments. Standard background on finite reflection
and Weyl groups is given by Humphreys [1].

Composition is written \(g h\), meaning apply \(h\) first and then \(g\).
The implementation names this operation `compose(g, h)`. This convention is
used consistently in both memory witnesses and directed frame edges.

### 2.2 Orbits, canonical representatives, and stabilizers

For \(x\in\mathbb Z^4\), its orbit and stabilizer are

\[
  \operatorname{Orb}(x)=\{gx:g\in W(D_4)\},\qquad
  \operatorname{Stab}(x)=\{g\in W(D_4):gx=x\}.
\]

The canonical key is the lexicographically smallest orbit member,

\[
  C(x)=\min_{g\in W(D_4)} gx.
\]

The implementation also returns the first descriptor in a frozen sorted
group order that maps \(x\) to \(C(x)\). Call this witness \(w_x\). Sorting
fixes a deterministic choice where several witnesses exist.

If an observed action \(a_x\) is to be retrieved equivariantly, it is stored
in canonical coordinates as \(a_c=w_x a_x\). For a query \(y\) with witness
\(w_y\), the returned action is \(a_y=w_y^{-1}a_c\). When the canonical
state has a nontrivial stabilizer, an action is valid only if every
\(h\in\operatorname{Stab}(C(x))\) also fixes \(a_c\). Otherwise, the same
canonical state would imply conflicting actions.

### 2.3 Frame relationships and cycle products

A directed edge \(u\to v\) carries an element \(g_{vu}\) mapping source-frame
coordinates to target-frame coordinates. A path product is composed in path
order: for \(u\to v\to w\), the transform is \(g_{wv}g_{vu}\). A closed path
is checked against an explicit expected product.

If every node \(v\) has a frame assignment \(q_v\) relative to a common
reference, and each edge is defined as

\[
  g_{vu}=q_v q_u^{-1},
\]

then products around closed paths telescope to the identity. This is the
consistent-graph fixture. Other applications can specify a nonidentity
expected product; nonidentity holonomy is not labelled erroneous merely for
being nonidentity. Cycle-based consistency is also used in the broader group
synchronization literature [3], where algorithms infer or recover latent
group assignments from noisy or corrupted edge data. D4-CYCLE-0 does not
perform that inference or recovery.

## 3. Reference implementation

The implementation is Python 3 and uses integer tuples for coordinates and
permutation/sign descriptors for group elements. It does not use floating
point, randomized choices, or learned parameters. Three separately specified
contracts and test modules keep the canonical primitive, memory comparison,
and cycle fixtures independently inspectable.

### 3.1 Canonical addressing and action reconstruction

`canonicalize(x)` evaluates all 192 images, selects the lexicographic minimum,
and chooses the first sorted witness producing it. The explicit enumeration
is deliberately simple and serves as a finite reference algorithm; the study
does not claim that it is an efficient general canonicalization method.

`OrbitMemory` maps each canonical key to an invariant payload and optional
canonical action. It rejects conflicting payloads assigned to equivalent
inputs. Before storing an action, it enumerates the canonical state's
stabilizer and verifies that each stabilizer element fixes the action. Lookup
canonicalizes the query and applies the inverse witness to reconstruct the
action in query coordinates.

### 3.2 Typed relationship edges and cycle evaluation

D4-CYCLE-0 adds immutable runtime-validated values for four-coordinate
symmetry states, group elements, frame identifiers, transform witnesses,
orbit keys, and directed relation edges. Composition checks that adjacent
edge endpoints match and that a cycle returns to its initial frame. The path
product uses the same right-first group convention as the canonicalizer.

Cycle evaluation is restricted to explicit frozen paths. There is no
automatic graph-cycle enumeration, statistical corruption estimator,
edge-localization procedure, relationship learning, or persistence layer in
this version. The corrupted fixture reports the union of edges appearing in
inconsistent cycles as candidates; it does not infer a unique faulty edge.

## 4. Experimental methodology

All three studies are software-only and deterministic. Their fixture values,
ordering conventions, thresholds, and output paths are fixed in contracts
dated 2026-10-14. Results are stored as JSON. Output commands refuse to
overwrite existing artifacts. The experiments are not statistical trials and
have no sampling-based uncertainty estimates.

### 4.1 D4-SYM-0: bounded exact orbit checks

The symmetry reference uses the bounded set

\[
  B=\{x\in\mathbb Z^4:-4\le x_i\le4,\;\sum_i x_i\equiv0\pmod2\},
\]

which contains 3,281 states. The focused checks establish that the generated
descriptors contain 192 unique group elements, verify identity, closure and
two-sided inverses, and test the composition/action law. For each bounded
state, witness reconstruction returns the original vector. For each state
and each group element, transformed inputs receive the same canonical key.

The demonstration uses \(x=(1,2,4,7)\), whose orbit has 192 distinct
members. It stores one payload and one orientation-sensitive action and
retrieves both across the orbit. The stored action is valid for this generic
orbit because the input stabilizer is trivial.

### 4.2 D4-MEM-1: four retrieval strategies

The comparison uses two source associations: the generic vector
\((1,2,4,7)\), with orbit size 192, and the stabilizer-bearing vector
\((1,1,2,2)\), with orbit size 48. Each payload is invariant over its orbit;
the source vector itself is the equivariant action. The queries contain all
distinct members of both orbits, one repeated representative query per
source, and the non-equivalent vector \((1,2,4,8)\). Thus there are 242
supported query occurrences and one designed miss.

The strategies are:

1. **Raw:** store only the two source vectors and perform exact-key lookup.
2. **Augmented:** materialize each distinct transformed input and transformed
   action during preparation.
3. **Canonical:** store one canonical key and canonical action per source;
   canonicalize each query and reconstruct the action with the inverse witness.
4. **Group-aware:** store only representatives, scan all 192 transforms for
   each query, and check all matching actions to expose stabilizer conflicts.

All methods receive the same source associations and the same group. The
serialized-byte measure is the UTF-8 length of canonical compact JSON for the
association records. It is not Python heap usage, allocator overhead, or a
hardware storage estimate. Operation counters count the declared events
(vector transforms, comparisons, witness candidates, inverse candidates,
action transforms, and dictionary probes); their unweighted sum is not a
latency model.

### 4.3 D4-CYCLE-0: declared cycle expectations

The consistent fixture assigns four fixed group elements to frames A–D and
derives both directed transforms for every frame pair. Seven simple paths are
checked: four triangles and three quadrilaterals. For the corruption fixture,
the A→B transform is replaced by a different valid element and B→A is set to
its exact inverse. Each of the same seven cycles is checked against identity.
The final fixture uses a three-edge cycle with two identity edges and a fixed
nonidentity third edge. It is checked once against that declared product and
once against identity.

## 5. Results

### 5.1 Canonicalization and witness checks

The bounded-state suite contains 3,281 states and checks canonical invariance
for all 192 transformations of each state, for 629,952 state/transform
combinations. Witness reconstruction and group-law assertions are also part
of the focused suite. In the generic demonstration, 192 distinct orbit
members map to one key and one association; all payloads are retrieved and
all actions reconstructed. These counts establish the tested finite
properties, not behavior over unbounded inputs or an application workload.

### 5.2 Retrieval comparison

| Strategy | Serialized association bytes | Payload correct / supported | Action correct / supported | Misses | False aliases | Counted events (unweighted sum) |
|---|---:|---:|---:|---:|---:|---:|
| Raw exact-key | 68 | 4 / 242 | 4 / 242 | 239 | 0 | 243 |
| Symmetry-augmented | 8,785 | 242 / 242 | 242 / 242 | 1 | 0 | 1,395 |
| Canonical with witness | 84 | 242 / 242 | 242 / 242 | 1 | 0 | 138,490 |
| Group-aware scan | 68 | 242 / 242 | 242 / 242 | 1 | 0 | 187,013 |

All strategies miss the single non-equivalent query. Raw exact-key memory also
misses transformed orientations, as expected. The three symmetry-aware
strategies correctly retrieve every supported payload and action, including
the stabilizer-bearing case.

Canonical serialization is 8,701 bytes smaller than the explicit augmented
representation in this fixture. It is 16 bytes larger than the two-entry raw
and group-aware records. Its declared event count is lower than the
query-time group-aware scan but much higher than augmentation. These results
do not identify a winner: storage uses one specific JSON accounting scheme,
and operation counters assign no relative cost to different operations.
The machine-readable result contains preparation/query counter breakdowns
and definitions.

### 5.3 Cycle products

All seven consistent-graph cycles produce identity. After the A→B corruption,
four of seven cycles fail the identity expectation, while the other three
remain identity. The evaluator reports the inconsistent cycles and candidate
edges in their union; the fixture does not establish unique fault
localization. The prescribed nonidentity cycle returns exactly its declared
group element, matches that expectation, and fails the identity expectation.

## 6. Limitations and interpretation

The demonstrated mechanisms are exact over the finite integer vectors and
finite group represented by the reference implementation. They do not show
that a useful real task has the assumed symmetry. Applying a symmetry to a
task where it changes the correct response would produce an invalid alias;
the non-equivalent miss and stabilizer tests are narrow controls, not a
complete semantic validation procedure.

D4-MEM-1 is a fixed two-association orbit workload. It does not test
data-driven learning, held-out task generalization, variable memory budgets,
large association sets, noisy observations, elapsed time, energy, or actual
memory use on a target device. Its operation events are explicit counts, not
weighted instructions or measured runtime. D4-CYCLE-0 checks seven supplied
cycles; it neither enumerates all graph cycles nor identifies the source of a
corruption. A nonidentity product is meaningful only relative to the
application's declared cycle model.

No experiment in this paper integrates the primitives with Soul-0, infers
relationships from observations, evolves a memory, uses Whisper, maps an
operation to SPU hardware, or evaluates an E8 representation. Therefore,
terms such as *adaptive intelligence*, *portable soul*, and *symmetry-native
inference* describe motivation and future research, not measured results.

## 7. Future work

The immediate extension is a persistence-only relational-memory reference:
serialize typed frame IDs and exact group-valued edges, restore them, and
recheck declared cycles. Learning should remain disabled until the
serialization and replay contract is stable. A subsequent experiment can
inject inconsistent observations and study detection separately from
localization. Other required work includes larger workloads, representation
and cost models suited to actual deployments, and comparisons with additional
symmetry-aware baselines.

Only after these reference semantics are stable should the work investigate
learned relations, adaptation, different finite groups, or native SPU
implementations. Existing literature on equivariant models and group
synchronization supplies important conventional comparisons [2, 3]. The
present implementation does not establish an advantage over those methods.

## 8. Reproducibility record

### 8.1 Commands

Run the focused checks from the repository root:

```bash
python3 -m unittest software.tests.test_d4_sym0 -v
python3 -m unittest software.tests.test_d4_mem1 -v
python3 -m unittest software.tests.test_d4_cycle0 -v
python3 -m software.research.d4_symmetry.demo --output build/research/d4_sym0/demo_01/result.json
python3 -m software.research.d4_symmetry.mem1 --output build/research/d4_mem1/eval_03/result.json
python3 -m software.research.d4_symmetry.cycle_demo --output build/research/d4_cycle0/demo_01/result.json
```

Each demo command refuses to overwrite its output. For a fresh replay, choose
new output directories and update the record accordingly. The first two
commands and their fixtures are specified in the D4-SYM-0 and D4-MEM-1
contracts; D4-CYCLE-0 is specified in its own contract. The focused tests
were observed passing during development: 5 D4-SYM-0 tests, 2 D4-MEM-1 tests,
and 7 D4-CYCLE-0 tests. These counts are not a coverage percentage.

### 8.2 Source and artifact identity

The repository base revision at draft preparation was
`4e51d2f1169c5a30c5e42fbf0b8bb67b7e36219f`. The relevant D4 research files
were untracked in the working tree at that point, so the Git revision alone
does not identify them. SHA-256 hashes below identify the exact files and
retained outputs used for this draft.

| File | SHA-256 |
|---|---|
| `software/research/lattice_comparison/d4.py` | `6f8bd0f2f935aa31312ec19e8594de477c2bb0f99ebbf0b7cf1425575a99ffd2` |
| `software/research/d4_symmetry/canonical.py` | `a6d0ac1ffbd680e627598246c7ce910e3462f312edd910d297b2f1131f41a465` |
| `software/research/d4_symmetry/memory.py` | `01cc51769ea8c8534df6fae011a336c68812e030c9d481b8af85916e768b5120` |
| `software/research/d4_symmetry/demo.py` | `97aabc4abb75eb1ad5becf944dec42b81acfac0b405adae9ec939fdbcbfef846` |
| `software/research/d4_symmetry/mem1.py` | `7dc1b3d7ace990ae296a8136790937fd2700a338e60f28f038ea78193ce0515b` |
| `software/research/d4_symmetry/types.py` | `e83dc773c1d17a76fef218e1fcb0ba3d49458cdf3298541a2b987dcf63235e94` |
| `software/research/d4_symmetry/cycle.py` | `f20b7248685e28470b8607a8aed0bb7bffee0fa8a7019a181238052bd5050e7a` |
| `software/research/d4_symmetry/cycle_demo.py` | `52486f93d4e3d90ceecaafa7aca6f7bcba661668ad8f17a7c9908289b08ddfa1` |
| `software/tests/test_d4_sym0.py` | `568590b13b70ffaeceecaa89935fe67bfac23e09c0665a24be18ba4e97085f1f` |
| `software/tests/test_d4_mem1.py` | `0f63d1a97cf01fc89355ea664f87cd700ac94e65cfeb386bc4072f5764777717` |
| `software/tests/test_d4_cycle0.py` | `41e65f28b5cb2cce80a9068a0f1436ffd175c1a9d13536ff9f47f925a6da6646` |
| `spu_strategy/contract_d4_sym0_2026-10-14.md` | `61602ceca4e675fe3351a77d3efac448374381bc2d1fcd3b41125ff7a31683d6` |
| `spu_strategy/contract_d4_mem1_2026-10-14.md` | `a6f0817a20eeeda7d108b09a8a6263e98beb067545cc673d1a93617f5fa01f4e` |
| `spu_strategy/contract_d4_cycle0_2026-10-14.md` | `884e3f61538a973397ab5ee171384992ddc7c9f939a2e466a9de0b7f5ce33aca` |
| `build/research/d4_sym0/demo_01/result.json` | `9587f37998aa63e3ec1919ab27c806cd21a5fb0a47d997cbd52143582853f306` |
| `build/research/d4_mem1/eval_03/result.json` | `504aae6cab4e8331aa258cdc82bccf32fb081628b41d6a43d9ced1ddf202b49b` |
| `build/research/d4_cycle0/demo_01/result.json` | `854b6553597d44737555d8243007c79adfd6c09684be4ec7e0d8784ae32f3983` |

Re-running a test or demo against later
source does not reproduce these hashes unless the source is identical.

## Acknowledgements, funding, and AI assistance

**Acknowledgements and funding:** to be completed by the human authors.

**AI assistance disclosure (draft):** An OpenAI Codex assistant contributed
to source inspection, experiment-result summarization, and drafting/editing
of this manuscript; earlier assistant contributions also include code and
focused test scaffolding in the D4-CYCLE-0 reference. Before any submission,
the human authors must confirm the tools and exact model versions used,
review and validate all AI-assisted text and code, make the final design and
authorship decisions, and update this disclosure to the target venue's
requirements.

## References

1. J. E. Humphreys. *Reflection Groups and Coxeter Groups*. Cambridge Studies
   in Advanced Mathematics 29. Cambridge University Press, 1990.
2. T. Cohen and M. Welling. “Group Equivariant Convolutional Networks.” In
   *Proceedings of the 33rd International Conference on Machine Learning*,
   Proceedings of Machine Learning Research 48, pp. 2990–2999, 2016.
   <https://proceedings.mlr.press/v48/cohenc16.html>.
3. G. Lerman and Y. Shi. “Robust Group Synchronization via Cycle-Edge Message
   Passing.” *Foundations of Computational Mathematics*, 22, pp. 1665–1741,
   2022. <https://doi.org/10.1007/s10208-021-09532-w>.
