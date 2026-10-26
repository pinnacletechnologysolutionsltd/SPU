# AOR-S1: canonical integer product fragment

**Status:** DRAFT — proof and oracle contract for review; implementation and execution gated.  
**Contract ID:** `contract_aor_s1_product_fragment_2026-10-13.md`  
**Roles:** Spec author drafts; implementer reviews boundaries; auditor checks independent evidence.

## Review commands and scope

```bash
sed -n '1,240p' spu_strategy/contract_aor_s1_product_fragment_2026-10-13.md
sed -n '1,200p' spu_strategy/contract_aor_s3_workload_preparation_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_aor_s1_product_fragment_2026-10-13.md spu_strategy/contract_aor_s3_workload_preparation_2026-10-13.md spu_strategy/AOR_SYMBOLIC_PROCESSOR_ROADMAP_2026-10-13.md docs/README.md
```

These commands review documentation. The audit count follows AGENTS.md and is
not a new suite result. This draft allocates no implementation or experiment
budget. Existing AOR-1 evidence, CPU sources, ISA and Artix-7 inputs are unchanged.
The [roadmap](AOR_SYMBOLIC_PROCESSOR_ROADMAP_2026-10-13.md) remains open.

## Domain and bounded profile

Represent `z=(a+b sqrt(3)) U^k`, where `U=2+sqrt(3)` and `a,b,k` are integers.
There is no rational mantissa or sum/product DAG in this canonical fragment.
Canonical zero is `(0,0,0)`. Nonzero integer mantissas have nonzero embeddings
`x=a+b sqrt(3)` and `x'=a-b sqrt(3)` and nonzero norm `N=a*a-3*b*b`.

Proposed stored profile: signed64 coefficients, signed32 exponent and signed128
norm output with explicit overflow. Temporary calculations must be exact and
separately bounded; signed128 alone is insufficient for every signed64 product.
An otherwise valid descriptor need not have a signed128 norm: norm-output
overflow does not make value equality false or invalidate the descriptor.
The [finite-profile amendment](contract_aor_s1_finite_profile_amendment_2026-10-13.md)
proposes temporary widths, work limits and first-failure evaluation order.
Ratification of those numbers, exact comparator kernels and logical schedules
remains required before implementation.

Validate exact integer types, tuple length, coefficient and exponent bounds.
Reject booleans and malformed operands. Record normalized-input validity
separately from mathematical value and raw tuple validity.

## Canonicalization theorem and local proofs

For nonzero mantissas require `U^-1 <= |x/x'| < U`. Scaling the mantissa by
`U^t` multiplies this ratio by `U^(2t)`, while changing the stored exponent to
`k-t`. The half-open interval spans exactly a factor `U^2`; every positive ratio
has exactly one representative in it. Since the embeddings are injective,
every represented nonzero value has exactly one balanced integer descriptor.
This is mathematical uniqueness, not guaranteed success in a bounded profile.

Let `s=sqrt(|x/x'|)` and `|N|=|x*x'|`. Then
`|a| <= sqrt(|N|)(s+1/s)/2` and
`|b| <= sqrt(|N|)(s+1/s)/(2 sqrt(3))`.
On the balanced interval, `s+1/s <= sqrt(6)`. Therefore
`a*a <= 3|N|/2` and `b*b <= |N|/2`.
Storage is bounded by norm size plus exponent size. Norms multiply; arbitrary
products do not preserve a fixed norm bound. Norm-one products do.

For balanced nonzero operands, product ratio lies in `[U^-2,U^2)`.
One adjustment suffices: if ratio is below `U^-1`, multiply the mantissa by U
and decrement k; if ratio is at least U, multiply by `U^-1` and increment k.
Otherwise retain it. The adjusted ratio is inside `[U^-1,U)`.
Conjugation reverses the ratio, giving `(U^-1,U]`; only the upper endpoint
needs one adjustment. Equal-exponent addition has no one-adjustment guarantee.

Exact unit adjustments are:

| Mantissa change | Coefficients | Exponent change |
|---|---|---|
| Multiply by U | `(2a+3b,a+2b)` | `k-1` |
| Multiply by U^-1 | `(2a-3b,-a+2b)` | `k+1` |

Both preserve the represented value and norm. Endpoint tests must use exact
algebraic comparisons, without floating-point logarithms or approximations.
For the sign of `a+b sqrt(3)`, use coefficient signs and comparison of
`a*a` with `3*b*b`; squares alone lose sign information.

## Operation obligations

| Operation | Domain and required outcome |
|---|---|
| General canonicalize | Valid raw descriptor; exact canonical result or named bounded refusal |
| Local rebalance | Certified product/conjugation ratio interval; zero or at most one adjustment |
| Multiply | Exact `(ac+3bd,ad+bc,k+m)`, then local rebalance for canonical operands |
| Step | Add increment to k; nonzero balanced mantissa unchanged; zero stays canonical zero |
| Conjugate | Raw `(a,-b,-k)`, then boundary rebalance |
| Norm | Exact `a*a-3*b*b`, independent of k; checked output width |
| Sign | Exact embedding sign; U is positive, so independent of k |
| Unit inverse | Conjugate and rebalance when N=1; N=-1 impossible modulo 3 |
| General inverse | Non-unit integer-ring inverse unsupported; zero inversion invalid domain |
| Equal-exponent sum | Exact coefficient addition, zero handling, then general canonicalize |
| Unequal-exponent sum | Outside initial compact operations; separate symbolic/materialized contract |
| Canonical equality | Validate canonical descriptors, then decisive tuple equality |
| DAG equality | Outside this fragment; separate equal/unequal/unresolved proof-budget contract |

The local adjustment count bounds unit adjustments, not bit complexity or all
primitive work. Canonical operands are required for decisive canonical equality;
raw tuple inequality must never be reported as mathematical inequality.

Every mutating operation computes into private temporary state and commits the
complete tuple only on success. Overflow, refusal or unsupported operation leaves
the destination and aliased sources unchanged. A canonical result may be outside
stored coefficient or exponent bounds even when the raw input fits.

Proposed first-failure evaluation sequence (not global error ranking): malformed input; unsupported domain/operation;
checked raw exponent arithmetic; exact result/rebalance computation within
resource limits; canonical exponent and coefficient bounds; operation-specific
output width. Raw exponent overflow is reported even if later rebalancing could
rescue it; any rescue policy requires a separate amendment. Temporary bit/work
limits produce `RESOURCE_LIMIT`, not a claim of numerical overflow. Final norm
overflow is `NORM_OVERFLOW`. Freeze exact status names and overlapping boundary
fixtures before implementation. Zero exceptions must be specified before
exponent checks: zero stepping returns zero for any valid integer increment.

## Independent oracle and falsification contract

Keep the implementation, semantic oracle and obligations checker independent.
Use an independent Pell recurrence for expanded fixture values, literal endpoint
expectations and a separately derived exact algebraic comparator. Do not import
the candidate reducer or use its rewrite rules as the sole source of labels.
Record what each proof establishes without expansion and what each expansion
checks within its declared resource limit.

Required fixture classes:

1. `(5,2,0) -> (4,-1,1)`; `(1,1,0) -> (-1,1,1)`.
2. Conjugate `(-1,1,1) -> (1,-1,0)`, exercising the excluded upper endpoint.
3. `(5,2,1000)` times its conjugate gives `(13,0,0)`, norm169, without expansion.
4. Products requiring zero, positive and negative unit adjustments; enforce
   the one-adjustment bound with an observed counter, including negative norms.
5. Equivalent raw tuples, negative-valued units, zero, signed coefficient
   extrema and both signed32 exponent endpoints.
6. A valid descriptor whose norm exceeds signed128; norm fails, equality remains
   decisive. Canonical exponent overflow, temporary-limit refusal and aliasing.
7. Equal-exponent cancellation and sums requiring general normalization;
   attempted use of the local one-step contract outside its certified domain.
8. Malformed types and lengths; unsupported inverse and unequal-exponent sum.

Inject dropped `3bd`, wrong exponent sign, wrong half-open endpoint, changed norm,
false equality verdict, wrong adjustment count and partial destination writes.
Each injection must trigger its frozen, named checker rejection. Budget exhaustion
is a refusal outcome; a checker accepting an injected error is qualification failure.

The prior [focused exact audit](../build/aor_symbolic_claims/20261013_01/REVIEW.md)
supports the literals, canonical bounds and geometry. It did not qualify this
bounded profile, local-adjustment instrumentation or its independent checker.
Retain its hashes and scope; do not recast it as a new tranche PASS.

## Freeze and execution gate

Before coding, freeze numeric/work profiles, failure precedence, independent
algorithms, fixture identities, exact commands and expected rejection reasons.
Before execution, freeze source/tool hashes and owner-approved attempt,
per-attempt and cumulative budgets. Long runs use the repository detached runner.
No command to implement or launch this proposed tranche is allocated here.
Hardware and SGN integration remain separately gated.
