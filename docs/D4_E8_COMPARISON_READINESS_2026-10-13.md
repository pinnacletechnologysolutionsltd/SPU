# D4/E8 comparison readiness — 2026-10-13

Preparation increment only. Qualification remains HOLD; the120-case comparison
has not run. The Surd CPU backend remains the hardware priority.

The [comparison contract](../spu_strategy/contract_d4_e8_comparison_readiness_2026-10-13.md)
freezes proposed accounting rules for validation, arithmetic, Euclid normalization,
conversion, table setup, deferred evaluation, complete logical storage and atomic
refusal. It adds a conventional D4 baseline, rather than attributing compact
transformation storage only to an SPU-oriented encoding.

The original [mathematical preparation](D4_E8_MATHEMATICAL_PREPARATION_2026-10-13.md)
and its16-source manifest remain intact. The existing58,176 root/reflection checks
are original preparation evidence, not newly qualified results.

## Preparation results

The new isolated `software/research/lattice_comparison` package implements the
conventional192-element even signed-permutation domain. A descriptor stores four
2-bit permutation indices and four signs:12 meaningful bits. An8-bit information
lower bound exists, but no8-bit rank/unrank encoding is implemented here.

Seven focused tests cover encoding/rejection, noncommuting composition order,
inverse restoration, four simple generators against the independent rational
formula, signed-minimum overflow without input mutation, explicit Euclid and
raw cancellation accounting, and work/storage/type/quotient refusals.
These tests do not establish that every comparison arm enforces these limits.

Additional short review witnesses compare both root sets with the separate
rational norm-shell oracle, compute Cartan Gram determinants4 for D4 and1 for
E8 using Bareiss elimination, generate all192 D4 descriptors from the four
simple generators, and check their4,608 root actions. They inspect120 fixture
identities and the256-token maximum without executing comparative cases.
No new full root/reflection sweep or substantial comparison campaign is run.

Construction conventions were cross-checked against the primary
[Sage D documentation](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/type_D.html)
and [Sage E documentation](https://doc.sagemath.org/html/en/reference/combinat/sage/combinat/root_system/type_E.html).
Sage was not executed and is not a dependency. The algorithmic review was
performed by the same preparer; independent reviewer sign-off remains PENDING.

## Mapping review

For each doubled-coordinate block X, retain t=sum(X) and q_i=4X_i-t.
Then sum(q)=0 and X_i=(q_i+t)/4. The physical Euclidean metric is

    ||x||² = sum_blocks (sum_i q_i²/64 + t²/16),   x=X/2.

This follows by expanding sum(q_i+t)²; the cross term vanishes because sum(q)=0.
It supplies the pulled-back metric for the ten-coefficient rank-eight encoding.
A non-root lattice witness with both sums nonzero checks inversion and norm6.
Dropping both sums still leaves rank6. Ten stored coefficients and conversion
work remain a cost, not an advantage established by the reversible map.

For coefficient packing z_j=a_j+b_j sqrt(3), with the eight physical rational
coordinates assigned to four pairs, the pulled-back Euclidean norm is
sum_j(a_j²+b_j²). It differs from sum_j(a_j²-3b_j²), the sum of field norms.
Defining this metric does not make ordinary Surd multiplication an E8 reflection.
Coefficient projection and exact transformed operators still need a reviewed
implementation. The existing B=0 bridge remains the comparison arm.

The AOR-S1 audit conclusion is unchanged: no integration evidence was found in
the inspected explicit-denominator CPU/build path. Pell units and proposed
balanced mantissa/exponent registers remain distinct representations.

## Remaining prerequisites

| Prerequisite | Preparation state |
|---|---|
| Complete cost/storage rules | Written; proposed limits and schedules await review |
| Conventional D4 baseline | Implemented; focused witnesses pass |
| Finite profile/refusal rules | Defined; arithmetic/boundary witnesses implemented |
| Every arm fully instrumented | NOT IMPLEMENTED; original partial counters cannot qualify full costs |
| Serialization and live-workspace ledger | Specified; complete decoder/ledger NOT IMPLEMENTED |
| Independent reviewer | PENDING; same-author algorithmic checks are supplemental |
| Frozen qualification command and owner budget | NOT AUTHORIZED |

The proposed domain contains120 cases,60 D4 and60 E8. Four general arms plus
the D4-only baseline yield540 applicable arm evaluations per execution condition.
The cyclic words are limited correctness/cost fixtures; they cannot establish
representative computational advantage. Zero inputs and inverse pairs are
intentionally retained, and must not be presented as useful workload throughput.

Evidence: `build/d4_e8_math_20261013/comparison_readiness_01/`. Preparation and
identity checks are recorded there separately from qualification. No CPU/RTL/ISA
source edits or hardware commands were made. Existing unrelated documentation
audit findings are reported separately; no clean repository-wide result is claimed.
