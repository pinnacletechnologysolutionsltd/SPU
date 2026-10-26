# AOR-S3: exact boost workload preparation

**Status:** PREPARATION DRAFT — no benchmark execution or hardware authorization.

## Review commands

```bash
sed -n '1,200p' spu_strategy/contract_aor_s3_workload_preparation_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
```

Use the [AOR-S1 proof/oracle draft](contract_aor_s1_product_fragment_2026-10-13.md)
for canonical product semantics. S3 execution follows its accepted software
qualification and a separately frozen workload/budget packet.

## Exact workload domain

Use c=1 and plus-sign boost convention. Tetrahedral axes are
`E0=(1,1,1)`, `E1=(1,-1,-1)`, `E2=(-1,1,-1)`, `E3=(-1,-1,1)`.
Define `B_i=[[2,E_i^T],[E_i,I+E_i E_i^T/3]]` and its exact inverse.
Freeze multiplication/application ordering: with column events, the rightmost
matrix acts first. Word serialization must state whether it lists application
order or matrix-product order; conversion must be tested with noncommuting axes.

For axis unit vector n, retain longitudinal and transverse state separately:
`r=x_parallel*n+r_perp`, `u=t+x_parallel`, `v=t-x_parallel`.
The independently derived interval is `uv-||r_perp||^2`.
A collinear boost scales u by U^k and v by U^-k; transverse state is unchanged.
Freeze an exact event-coordinate representation before coding: rational
Cartesian inputs can have sqrt(3) longitudinal coordinates. Integer AOR-S1
mantissas alone must not be claimed to cover all such events.

## Required comparisons

| Representation | Capability to include and charge |
|---|---|
| Rational 4x4 matrices | Exact application, composition, inverse, interval/equality checking |
| Axis/exponent bookkeeping | Same-axis compression, cancellation, explicit mixed-axis escalation |
| Run-length boost words | Adjacent same-axis merging, inverse cancellation, deferred materialization |
| AOR-S1/S3 hybrid | Same reduction capabilities plus declared algebraic state and normalization |

Give symbolic candidates equivalent reduction opportunities. Include a
materialized-matrix path, but do not attribute symbolic advantages over eager
evaluation uniquely to AOR. Unsupported comparisons must remain explicit.

## Workload families and observables

| Family | Required question |
|---|---|
| Collinear chains | How does exponent storage compare with expanded coefficients? |
| Alternating axes | How do mixed-axis matrices, words and candidate state grow? |
| Random axis words | What growth occurs under frozen distributions and seeds? |
| Inverse palindromes | Does exact cancellation avoid materialization in all capable baselines? |
| Transverse events | Which portion of complete event state benefits from compression? |
| Boundaries | Are normalization, overflow, unsupported and resource refusals correct? |

Include literal `B0^1000 B1 B1^-1 B0^-1000 = I` and a noncommuting two-axis
example. Axis switching may retain a word; it does not mandate materialization.
All 24 tetrahedral permutations act on four axes; distinguish 12 rotations from
12 reflections. Boost axes and the 12 FCC transport ports are different objects.

Record retained representation bits, peak live temporary bits, exact operation
vectors, normalization work, equality/conservation proof cost and materialization
cost separately. Include parsing, validation, sharing and output conversion.
Logical encoding size and host object memory are separate metrics. Report time
with repetitions and dispersion only after freezing the measurement protocol.
Primitive vectors must remain available even if an aggregate cost is approved.

## Remaining freeze decisions

Specify word lengths, exponents, events, seeds/distributions, bit/work/node limits,
reduction order, accounting units, output requirements, independent expected
results and negative controls. Freeze an explicit practical-benefit criterion
and any accepted error rate; this exact-arithmetic comparison permits no silent
approximation. Freeze source/tool identities, commands and bounded launch budget.

Correct results with matching baseline costs are successful research outcomes.
They do not establish a hardware advantage. Qualification failure means an
incorrect result/classification or a checker missing its deliberate fault.
No speedup, network requirement or physical timing follows from this draft.
