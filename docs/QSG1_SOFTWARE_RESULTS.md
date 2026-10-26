# QSG-1: metric admission and coordinate queries

Date: 2026-10-19. Status: EXPERIMENTAL implementation; isolated fixture PASS.
No designated independent QSG gate acceptance is implied. QSG-0 remains 0/5.

The [saved-evidence review](QSG1_EVIDENCE_REVIEW.md) audits source integrity,
matched semantics and measurement qualifications, including counter coverage
and the untested arithmetic-refusal edit case. It performs no rerun and does
not substitute for designated independent acceptance.

## Scope and preserved evidence

The owner's revised instruction authorized inexpensive QSG-1 work independently
of QSG-0 acceptance, subject to mathematical review and a bounded contract.
The [contract](../spu_strategy/contract_qsg1_software_2026-10-19.md) records
that review, exact error precedence, matched semantics and execution limits.
This tranche changes no production software, shared runner, RTL, ISA or timing.

Executed from the repository root:

```bash
timeout 30s cc -std=gnu89 -shared -fPIC -O2 -fno-fast-math -ffp-contract=off -fexcess-precision=standard build/qsg1/dependencies_01/predicates.c -lm -o build/qsg1/dependencies_01/predicates.so
timeout 30s python3 research/qsg1/run.py --output build/qsg1/experiment_02 --predicates build/qsg1/dependencies_01/predicates.so
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- research/qsg1 docs/QSG1_INTRINSIC_GEOMETRY_SPECIFICATION.md docs/QSG1_SOFTWARE_RESULTS.md spu_strategy/contract_qsg1_software_2026-10-19.md
```

Final evidence: [results](../build/qsg1/experiment_02/results.json),
[provenance](../build/qsg1/experiment_02/provenance.json) and
[COMPLETE](../build/qsg1/experiment_02/COMPLETE). Copied inputs include all QSG-1
sources, the unchanged QSG-0 rational primitive module, reviewed specification,
execution contract, original predicates.c and its compiled shared library.
Hashes, compiler command/version, Python/platform, git identity/dirty state,
sample settings and raw timings are recorded. Output directories are new and
refuse overwrite. Build artifacts are local evidence, not presumed published
with a checkout. Dependency acquisition URL and source digest are in the
contract; compiling the predicate requires that pinned download first.

Two of the three allowed tiny software invocations were used. Both exited 0
within their 30-second limits; no timeout or expensive hardware job occurred.
Run 01 is preserved; run 02 adds explicit bounded-refusal stage assertions
and the reduced Gram/Schur comparison. Reported timings are from run 02 only.

## What passed

Four primary records are accepted by both independent Fraction/Gram and
metric-first validators; the bounded model also admits all four. Nine negative
records distinguish schema/encoding, edge/anchor, local degeneracy/invalidity,
wrong orientation and incompatible planar closure. Shared-AB mismatch and
invalid duplicate encoding are checked separately. E preserves AB,d,e,f,
admits the specified local change, and invalidates cached coordinates even on
repeated edits. Eight refused edit checks preserve committed metrics and caches.

The squared-closure branch control rejects W=-2 even though W²=4HK.
The f=4 control has two valid faces but fails the selected planar closure;
this remains compatible with a free 3D hinge and is not globally impossible
geometry. Three rational reconstructions match independently stated coordinates,
recover all six quadrances, retain positive face orientation and repeat exactly.

For (AB,a,b,d,e,f)=(1,1,1,1,1,3), H=K=3/4 and W=3/2.
V admits the real planar metric without square roots. Its committed state
survives R returning DOMAIN_ESCAPE over Q. Both the bounded and unbounded
candidate paths exhibit this behavior, and the independent exact Gram path
has the same acceptance and reconstruction outcome. This is the central
functional result, not evidence that ordinary exact algebra lacks this ability.

## Bounded arithmetic and correction

Primary V evaluations use 2 rational additions, 8 subtractions, 2 divisions
and 6 multiplications, with no square root. Primitive instrumentation records
160 Arithmetic.check calls, 27 gcd calls and 42 exact integer reductions per
record. These counters exclude Python schema and geometric branch guards.
Largest observed integer magnitude is 3 bits for the seed, 12 for the edited
and independent examples and 6 for the nonsquare metric. These are fixture
measurements, not worst-case bounds or general expression-growth results.

For a=b=d=e=2^29 and f=2^31-1, the exact metric is valid, but R32 refuses
during W computation. Here H=K=(2^31-1)/4; the first subtraction f-H has
reduced numerator 3*(2^31-1), already outside R32. Run 01's contract and
fixture name incorrectly anticipated refusal at W². The geometry and refusal
outcome were correct, but that stage interpretation was wrong. Run 02 corrects
the label and asserts the actual W stage; original inputs/results remain intact.

The second arithmetic control refuses at x's addition before the later exact
oracle's WRONG_ORIENTATION_BRANCH diagnosis. This confirms that operational
error precedence differs from unbounded geometric classification. A bounded
refusal is not a declaration of invalid geometry. Neither control establishes
an intermediate-only QSG-0 scalar transform failure.

## Comparison with conventional computation

Each timing is the median of three 100-repetition samples, one warm-up, GC
disabled. R includes validation; E includes initialization and two edits.

| Workload | Metric Fraction, microseconds | Gram Fraction, microseconds | Checked R32, microseconds |
|---|---:|---:|---:|
| V on all four primary metrics | 164.00 | 228.24 | 533.85 |
| Initialization plus two edits | 127.41 | 181.17 | 415.78 |
| R on three rationally reconstructible records | 136.22 | 194.53 | 458.29 |
| Initialization plus two edit/query pairs | 222.48 | 315.98 | 727.77 |

The reduced conventional Gram/Schur V costs 198.54 microseconds on all four
records, versus the full determinant's 228.24. The candidate's simpler metric
formula is faster in this local Python sample. Both formulas perform exact
admission without square roots, so this supplies no unique metric-state
capability or native architectural advantage. Further algebraic optimization,
runtime overhead and the tiny workload limit comparative conclusions.

Coordinate-to-metric conversion on three precomputed rational point sets costs
194.30 microseconds; the corresponding metric-coordinate-metric round trip
costs 394.40. Rational reconstruction timing excludes the explicitly named
nonsquare record. Admission comparisons include it on both sides. There is
no full-domain speedup claim against a Q-only coordinate path.

The guarded binary64 path, including exact Gram admission and original
Shewchuk orient2d, costs 301.83 microseconds on all four records. This path
produces approximate coordinates, so that timing is not an equal-output exact
construction comparison. Exact quadrance residuals of its finite stored
coordinates are recorded as rational fractions in the JSON. No tolerance is
used to silently accept invalid metric relationships.

Six R32 metric fields occupy 48 logical bytes (40 excluding shared constant
AB). The four free Cartesian scalars occupy 32 bytes; a metric coordinate cache
adds 32. Common anchors and topology are excluded consistently. This is not
Python heap or FPGA resource use, and establishes no metric storage advantage.

## Established predicate baseline and limits

The original public-domain [Shewchuk predicates](https://www.cs.cmu.edu/~quake/robust.html)
were downloaded, source-hashed and compiled under the frozen strict arithmetic
flags. exactinit precedes orient2d. Eighteen predicate cross-checks on target
triples, near-collinearity and exact collinearity agree with Fraction signs on
the same stored binary64 coordinates; eight additional face calls bring total
predicate calls during checks to 26. This is an established robust-decision
baseline, not exact coordinate construction or a closure proof by orientation.

Correctness remains limited to the fixed planar two-face model, frozen input
records and tested bounded behavior. No generic solver, arbitrary embedding,
physical law, dynamics, topology mutation, symbolic ISA or hardware qualification
has been implemented. The implementer wrote both Python paths; source/formula
separation is not designated independent authorship or acceptance.

## Disposition

QSG-1 establishes tested metric admission, local constraint preservation and
deferred coordinate queries, including valid state outside rational Cartesian
representability. Conventional exact Gram algebra supports the same separation.
Native adoption, energy, system-wide simplicity and hardware value remain
unmeasured. This tranche is complete; no further run is currently needed.
QSG-2 remains a possible separately scoped comparison, not an automatic next
implementation. Gen 1 priorities and the separate Vivado preparation remain
independent; QSG-0 gate decisions remain with the designated reviewer.
