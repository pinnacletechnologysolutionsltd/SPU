# SYMREG-3 — semantic joins with path-covering provenance

**PASS — BOUNDED DISCOVERY.** A fixed-set semantic join preserved a conclusion
lost by syntactic fact intersection, with independently replayed witnesses for
every declared-feasible path. The result is a bounded software experiment, not
an ISA, production VM, hardware symbolic register, general theorem prover or
Soul-memory claim. The [specification](SPECIFICATION.md) defines the rules and
trust boundary. The earlier SYMREG-1 and SYMREG-2 files remain untracked and
unchanged; this experiment imports them directly.

## Correctness and expressiveness

The focused suite's **12 test groups** passed. For shared identities `x=(1,2)`,
`y=(1,-2)`, `z=(2,-4)`, `w=(2,4)`, branch A proves
`y=conj(x); z=2y`, and branch B proves `w=2x; z=conj(w)`. Syntactic fact
intersection returns `UNKNOWN`; semantic join returns `PROVEN` for
`z=2conj(x)` with the `ALL_FEASIBLE_PATHS` rule, both branch IDs and distinct
two-edge witness paths. Independent `Fraction` arithmetic confirms both the
value and `N(z)=4N(x)`.

For 49 coefficient pairs in `[-3,3]²`, the two alternate paths were checked
against exact results. Across the same 49 cases, 16 candidate value and norm
queries each produced **784 checked outcomes**; every emitted `PROVEN` was
compared against the independent oracle and none was false. These are finite
fixtures, not a universal implementation proof. A deliberate any-branch
mutant promoted a one-path-only proposition; the real join returned `UNKNOWN`.
Zero, negative scale, conjugation and an out-of-vocabulary intermediate were
tested; the latter remains `UNKNOWN` even where the final zero relation is true.

Two- and three-branch proofs, repeated equivalent queries, a third direct
witness, missing coverage, swapped branch witnesses, malformed proof data,
roster changes and stale bindings were exercised. A historical proposition can
remain proven after one path overwrites a register, while the corresponding
current-register query is `UNKNOWN`. The W=8 integer-denominator SMUL overflow
case preserves destination and facts while updating status; a fresh join after
refusal remains valid. No claim is made for other instruction refusals.

## Completeness and limits

Only configured candidates are considered. Every declared-feasible path must
produce a predecessor-supported proof for the exact same proposition and
identities. Unknown, missing or unsupported evidence never becomes `PROVEN` or
`DISPROVEN`. This join emits no `DISPROVEN` result; a single concrete
counterexample is not represented as a universal post-join conclusion.
Feasibility is supplied externally, not inferred. The optional canonical
comparator was not implemented; SYMREG-2's rooted representation is not a
general semantic join.

Resource tests cover the inherited 64-identity and 256-fact limits, a maximum
of three branches and 16 queries, zero work budget, too-small proof-edge
budget, proof-retention exhaustion and a synthetic overlarge provenance graph.
Limits return `RESOURCE_LIMIT`, `UNKNOWN` or the predecessor's explicit
capacity exception; no partial branch coverage is reported as `PROVEN`. Proof
objects are bound to one in-process context and its snapshots, not portable
certificates. Stale contexts fail closed and must be rebuilt. No claim is made
about hostile mutation of Python internals or concurrent execution.

## Proof cost and runtime/memory observations

The deterministic workload has the same four candidate keys for both
comparators: value and norm consequences of E1, a one-path-only value fact,
and an unsupported common equality. Thirty repetitions used Python 3.10.12;
times below are medians for the complete four-query set, not per-query latency.

| Feasible branches | Stored branch facts | Common base facts | Syntactic proven | Semantic proven | Bundle edges / DAG nodes | Semantic edge inspections |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 0 | 0/4 | 2/4 | 8 / 8 | 29 |
| 3 | 5 | 0 | 0/4 | 2/4 | 10 / 10 | 31 |

The three-path case adds a direct one-edge proof of the same conclusion. Bundle
edge and node counts are summed separately for the two emitted proofs; shared
objects across separate proof bundles are counted again. Setup times were
0.000244/0.000277 s, syntactic query-set times 0.000150/0.000172 s, semantic
times 0.000331/0.000383 s, and separate full-bundle revalidation times
0.000121/0.000134 s for two/three paths. Fact admission occurs during setup;
the join and validation made **zero numerical reads**. Setup peak Python
allocation was 7,824/9,592 bytes, and the separately traced semantic-query
phase peaked at 13,760/18,440 bytes. These `tracemalloc` values include Python
objects and are not total process memory or additive peaks. Setup was timed
with tracing; query timings were not. Semantic queries perform branch proof
validation in addition to search, so this is a descriptive comparison, not an
apples-to-apples speed claim. No hardware cost is inferred.

## Solver verification record

The [SMT file](verification.smt2) uses Z3 4.15.5, QF_BV, with Boolean branch
guards and 3-bit signed coefficients widened to 16 bits; the bounded `×2`
arithmetic used here cannot overflow 16 bits. It models abstract rules, not
the Python implementation, real branch feasibility or finite-width SPU ISA.

| Property and assumptions | Result | Deliberate negative control |
|---|---|---|
| A nonempty universal join, with every covered branch proof assumed sound, cannot contain a false feasible branch. | `UNSAT` counterexample | An existential join is `SAT`: A is proven/true while feasible B is unproven/false. |
| The two E1 symbolic paths produce the same widened coefficient pair. | `UNSAT` mismatch | Omitting conjugation in B is `SAT` at `b=1`. |
| A two-bit identity increment cannot equal its prior value after one write. | `UNSAT` equality | Register-only matching ignores the changed identity; old `0`, new `1` is `SAT`. |

These are bounded formulas under explicit assumptions. `UNSAT` is not proof
of code; `SAT` is a witness for the deliberately defective formula; timeout or
`UNKNOWN` is inconclusive. No timeout occurred.

## Reproduction and remaining work

Worktree `dev/next` at `d9a25d2` with unrelated dirty/untracked files. Both
predecessor directories were already untracked; neither was edited, staged or
committed. Their model SHA-256 values were
`2e14cfb154ac888236bb72ae7dc6e4ab71cb32cff50b71d045d06baefbfd83e4`
(SYMREG-1) and `b9e12446e5c573218ff4c5e4e4543abcd346f8642d3a4c2a6d9f13b1bffc7ba4`
(SYMREG-2). Python 3.10.12 and OSS CAD Suite 20261027 Z3 4.15.5 were used;
no random seed. Commands run from repository root with 30-second wall and
1-GiB process limits:

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_symreg_3.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_3.measure)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_3/verification.smt2)
```

Expected solver outcomes are `unsat, sat, unsat, sat, unsat, sat`, plus the
negative-control witnesses. The smallest proposed next investigation is
portable, independently replayable join certificates with bounded lifetime and
explicit branch-set binding. It has not been started and needs separate
authorization. No changes to RTL, ISA, production VM or release status are
implied by this result.
