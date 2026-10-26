# QSG-1 reviewed bounded software tranche

Date: 2026-10-19. Status: completed isolated software tranche, fixture PASS.
Authorized by owner's instruction to proceed with QSG-1 subject to mathematical
review and a bounded execution contract. Two software invocations consumed;
no further run currently needed. See [results](../docs/QSG1_SOFTWARE_RESULTS.md).
Analytical review: Codex; owner previously checked the primary algebraic examples.
This is not a designated independent QSG-0 acceptance decision.

## Mathematical disposition

PASS for this isolated software scope: H,K>0 and W>0, W²=4HK are necessary
and sufficient for the fixed planar opposite-side model. Gram determinant and
negative Schur residual provide an independently organized conventional oracle.
No unresolved geometric contradiction was found. Freeze the two review items
below before implementation. QSG-0 remains 0/5; the owner explicitly permits
QSG-1 to proceed independently of that acceptance decision.

## Execute from the repository root

```bash
timeout 30s cc -std=gnu89 -shared -fPIC -O2 -fno-fast-math -ffp-contract=off -fexcess-precision=standard build/qsg1/dependencies_01/predicates.c -lm -o build/qsg1/dependencies_01/predicates.so
timeout 30s python3 research/qsg1/run.py --output build/qsg1/experiment_02 --predicates build/qsg1/dependencies_01/predicates.so
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- research/qsg1 docs/QSG1_INTRINSIC_GEOMETRY_SPECIFICATION.md docs/QSG1_SOFTWARE_RESULTS.md spu_strategy/contract_qsg1_software_2026-10-19.md
```

Keep foreground work below 30 seconds per command. Allow at most three tiny
software invocations for corrective implementation checks, each with a new
output directory and a 30-second limit (90 seconds cumulative run budget).
Do not extend a timeout, expand inputs or start a fourth run under this contract.
Compile the external predicate once with a separate 30-second limit. Snapshot
sources, dependency source/binary, compiler, commands, Python/platform and raw
results. Keep QSG-0 sources and all prior evidence untouched.

Dependency: Shewchuk's original public-domain predicates.c, downloaded from
https://www.cs.cmu.edu/afs/cs/project/quake/public/code/predicates.c
SHA-256: `f8662c3f407d1c1c5dcd4dd49ea8b8ddd801a71827d65734206ddc3741792029`.
Call exactinit once, then orient2d with binary64 triples; no fast math or FMA
contraction. This is the established predicate baseline, not QSG-0's local
filter. Robust signs alone do not decide metric closure.

## Freeze exact error precedence

1. Check schema/arity; INVALID_SCHEMA on a malformed metric/edit tuple.
   V, E and R are separate functions; no arbitrary opcode dispatcher is exposed.
   Validate all encoded rationals in field order
   AB,a,b,d,e,f (edit a,b); INVALID_ENCODING precedes all geometric errors.
2. If supplied, validate the duplicate shared-AB encoding, then exact agreement;
   SHARED_EDGE_MISMATCH precedes geometric tests. No duplicate ID repair.
3. In field order require positive quadrances (INVALID_EDGE); then AB=1
   (INVALID_ANCHOR). No floating tolerance.
4. Evaluate exactly the specification's ordered R32 DAG: x,z,H,K; then inspect
   H before K, reporting DEGENERATE_FACE for zero or INVALID_FACE for negative.
   An earlier arithmetic refusal wins over a later geometric test, even if an
   unbounded oracle could diagnose that geometry. Never relabel refusal invalid.
5. Compute v,W; W<=0 is WRONG_ORIENTATION_BRANCH by this operational precedence.
   Otherwise compute L=W² then P=(4H)K; inequality is
   INCOMPATIBLE_PLANAR_CLOSURE. Preserve RESULT_OUT_OF_RANGE,
   INTERMEDIATE_OVERFLOW and DIVISION_BY_ZERO at their first primitive.
6. R first validates the committed metric, then sqrt(H), sqrt(K), coordinates;
   the first nonsquare gives DOMAIN_ESCAPE. No coordinates or cache changes
   publish on failure. Successful edits invalidate coordinate caches.

This operational classification is not a theorem that every W<=0 metric has
a valid other planar embedding. Report the exact mathematical oracle result
and bounded operational outcome separately if they differ.

## Freeze matched semantics and fixture scope

V accepts valid real planar metrics without requiring rational coordinates.
Both the metric-first candidate and exact Gram baseline accept the nonsquare
fixture (1,1,1,1,1,3). Both exact R queries refuse its rational coordinates.
E proposes only a,b; all other metric fields are preserved. Both admission
paths use these same inputs, preservation rules and exact accepted metric set.
The coordinate comparison is restricted explicitly to Q-reconstructible inputs;
do not treat its DOMAIN_ESCAPE as failed geometry or claim a full-domain speedup.

Numerical coordinates use the exact Gram admission guard and original
Shewchuk orientation; their approximate constructions are reported with exact
residuals. This is a guarded numerical path, not an exact coordinate competitor.
Metric V is compared directly with Gram V without forcing reconstruction.
Report V, E, R and update/query workload costs separately. Constants, caches,
conversion and rejected inputs must be charged consistently.

Freeze the specification's nine primary examples; include noncanonical values,
nonpositive edge, wrong AB, malformed arity, conflicting shared AB, invalid
edits with atomic refusal and repeated successful edits with cache invalidation.
Use a=d=b=e=2^29, f=2^31-1, AB=1 as a valid real metric whose R32 validation
refuses in the first subtraction forming W; compare exact validity separately.
Run 01's contract incorrectly named W² as the refusal stage. Preserve that run;
run 02 adds an explicit stage assertion and corrects only that interpretation.
Also include an algebraically reduced Gram/Schur baseline, so comparison is
not restricted to a literal full 3x3 determinant implementation.
Also freeze a=b=2^31-1,
d=2,e=1,f=5 to exercise an earlier x-stage arithmetic refusal. Include a
mixed invalid encoding/negative edge to falsify classification precedence.
This does not claim an intermediate-only QSG-0 scalar transform fixture.

Use three timing samples of 100 repetitions of the same declared workload,
one warm-up, no timing-based adoption assertion. Count bounded primitive work,
integer sizes and exact residuals; record absent dimensions as unmeasured.
The independent Fraction/Gram oracle imports no metric-first implementation.
Reuse QSG-0's checked rational primitives read-only with a pinned source hash.

## Scope and stop

Only `research/qsg1/`, QSG documentation and this contract may change.
No production arithmetic, shared tests, simulator/ISA, RTL, pipeline, hardware
run or Gen 1 constraint changes. On a contradiction, halt and flag a minimal
correction. On a failed check, fix only this implementation within the budget;
never weaken expected geometry. Stop after recording results; QSG-2 execution
requires a separate justified question and authorization. No QSG gate is
automatically accepted by this run or by specification approval.
