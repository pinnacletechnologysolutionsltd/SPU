# SPU-SYMREG-2 — sparse relationships and canonical transformations

**PASS — BOUNDED DISCOVERY.** Sparse and canonical representations derive
useful checked relationships without storing every conclusion, with explicit
and significant completeness trade-offs. This is software research, not a
performance, ISA, RTL or hardware claim. The
[specification](SPECIFICATION.md) defines the trusted inputs and finite scope.
The untracked [SYMREG-1 predecessor](../qaf_symreg_1/FINDINGS.md) was inspected
and left unchanged; its explicit model is the reference in this experiment.

## Correctness and expressiveness

Eleven test groups passed, including 2,500 systematically enumerated two-edge
chains over coefficients `[-2,2]`, scales `{-2,-1,0,1,2}` and both
conjugation choices. Supported conclusions were compared with independent
`Fraction` coefficient calculations and predecessor explicit derivations.
Another 3,060 candidate value/norm queries across both new representations
produced no false `PROVEN` against the independent finite-domain oracle.
The checked example `x → conj(x) → 2·conj(x) → 2x` produces a three-edge proof;
the norm query yields `4·N(x)`. Composition, queries and proof replay perform
zero new concrete reads after base admission. Norm-only and mixed value/norm
paths, including a negative norm scale, also pass.

Tests preserve historical identities after register overwrite and reject a
stale binding, fabricated or malformed provenance, unsupported scales and
false concrete claims. A deliberately register-number-keyed negative control
continues to claim a stale relation after overwrite. Conjugate cycles are safe;
the canonical tree declines to retain a cycle. Equality of norms is not treated
as value equality. The model cannot establish facts from unchecked observations;
its proof checker trusts the predecessor's concretely checked base admissions.

Branches use the predecessor's declared-feasible-path assumptions. Common
foundational facts survive a join and can be recomposed; differing current
register bindings become unknown. A negative result is also preserved: when
both branches prove the same conclusion by different, non-common paths, their
intersection loses the conclusion and the join returns `UNKNOWN`. No claim of
branch-feasibility inference is made.

Other true but unsupported results include the chain `2×`, `2×`, then `0×`:
the intermediate `4×` lies outside the value vocabulary, so the final true
`0×` relation is not derived. The rooted canonical form also cannot answer
arbitrary non-root source queries. Capacity, depth and work limits fail closed;
the tests check explicit exhaustion and provenance-depth refusal. These are
bounded tests, not a proof of the Python implementation.

## Compactness and cost

The constructed all-pairs workload creates `n` distinct identities with the
same concrete value. The explicit baseline admits every ordered pair; sparse
and canonical store a directed `n−1`-edge chain. All ordered pairs are true,
but not all are inferable from those directed facts. The table reports one run
of three repetitions per point, with median times and allocation peaks:

| n | Explicit: facts, proven | Sparse: facts, proven | Canonical: facts + nodes, proven |
|---:|---:|---:|---:|
| 4 | 16, 16/16 | 3, 10/16 | 3 + 4, 4/16 |
| 8 | 64, 64/64 | 7, 36/64 | 7 + 8, 8/64 |
| 12 | 144, 144/144 | 11, 78/144 | 11 + 12, 12/144 |
| 16 | 256, 256/256 | 15, 136/256 | 15 + 16, 16/256 |

At `n=16`, explicit/sparse/canonical setup times were 0.002501/0.000331/
0.000393 s; all-pairs query times were 0.002922/0.011881/0.001127 s. Setup
concrete reads were 512/30/30; query concrete reads were zero for all three.
Setup peak Python allocations were 90,736/9,108/13,064 bytes; additional
query-phase peaks were 94,168/123,432/42,456 bytes. These separately traced
peaks include Python machinery and cannot be added to obtain process memory.

The explicit measurement uses direct membership in SYMREG-1's materialized
fact dictionary, rather than calling its breadth-first `query` API; this is a
strong direct-lookup baseline. For the same point, work counters were 256 dictionary lookups, 19,840 sparse
edge inspections and 120 canonical proof-link traversals, respectively; these
units are not equivalent. Reconstructed proof paths traversed 256/680/120
edges, and external proof rechecking took 0.001954/0.002882/0.000444 s within
the query times. Sparse and canonical queries also validate internally, so
timing is not a controlled apples-to-apples implementation benchmark. The
canonical query time covers only 16 proven pairs; comparing it to 256 explicit
successes would be misleading. Timings include Python and scheduling noise;
there is no claim about hardware speed, power or area. The few constructed
points do not establish asymptotic scaling.

## Solver verification record

Z3 4.15.5, QF_BV, was run with a 25-second solver limit, a 30-second external
limit and a 1-GiB process limit. Inputs are 3-bit signed coefficients and
scales, widened to 16 bits; scaling is restricted to `{-2,-1,0,1,2}`. The
formulae and scope are in [verification.smt2](verification.smt2). `UNSAT`
means no counterexample under the encoded assumptions, `SAT` provides the
specified witness, and timeout/`UNKNOWN` is inconclusive.

| Encoded property | Result | Negative control |
|---|---|---|
| Two transformations compose by multiplying scales and XORing conjugation parity. | `UNSAT` counterexample | OR in place of XOR is `SAT` for both flips true and unit scales. |
| Norm under scaling/conjugation changes by `k²`. | `UNSAT` counterexample | Using `k` is `SAT` at `a=1,b=0,k=2`. |
| Double conjugation is identity. | `UNSAT` counterexample | A proposed equality between a value and its conjugate is `SAT`-false at `b=1`. |
| One overwrite changes a 2-bit version. | `UNSAT` equality | A register-only stale match is `SAT` with old id 0 and new id 1. |

These abstract bit-vector checks do not verify the Python implementation,
unbounded integer arithmetic, multi-wrap identity behavior, branch feasibility
or the finite-width SPU ISA. No solver timeout occurred.

## Architectural interpretation

Canonical transformations are useful for a bounded rooted chain: the final
descriptor and proof can be recovered without numerical evaluation. Explicit
base relations and their provenance are still needed, especially for cycles,
joins and norm facts not implied by a value transform. The rooted restriction,
directionality and finite vocabulary lose useful queries; proof links and
replay contribute nontrivial storage and execution costs, but this experiment
does not establish that provenance dominates them. A compiler or research VM
is the appropriate initial home, rather than a hardware register extension.
For geometric work, multiple coordinate frames, branch joins, non-invertible
zero transforms and identity lifetime are particularly relevant unresolved
questions. A smallest follow-up would compare bounded common-fact preservation
at joins using two alternative proof paths, with explicit provenance and a
fixed resource budget; it is a proposal only and was not started.

## Reproduction

Repository `dev/next` baseline `d9a25d2`; SYMREG-1 remains uncommitted and is
required as a local dependency. Python 3.10.12 and OSS CAD Suite 20261027 Z3
4.15.5; no random seed. Each command has a 30-second wall limit and 1-GiB
per-process virtual-address-space limit. Output is terminal-only.

```sh
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m unittest research.qaf_symreg_2.test_model -v)
(ulimit -v 1048576; PYTHONDONTWRITEBYTECODE=1 timeout 30s python3 -m research.qaf_symreg_2.measure)
(ulimit -v 1048576; timeout 30s /home/john/.local/opt/oss-cad-suite-20261027/bin/z3 -T:25 research/qaf_symreg_2/verification.smt2)
```

Expected solver outcomes are `unsat, sat, unsat, sat, unsat, sat, unsat, sat`
with counterexample values. No timeout occurred. No predecessor, production VM,
RTL, ISA or release evidence was changed, and no follow-up was initiated.
