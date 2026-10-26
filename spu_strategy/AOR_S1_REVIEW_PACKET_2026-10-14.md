# AOR-S1 review packet: canonical product fragment

Date: 2026-10-14. Schedule amendment ratified; implementation contract preparation only.

The [final owner decision](AOR_S1_FINAL_RATIFICATION_2026-10-14.md) ratifies
reconciliation after the independent fixture-count review. Candidate implementation
and qualification remain HOLD; only the separate contract preparation is authorized.
The checked 1a charge is a disclosed modeling convention.
The [independent review disposition](AOR_S1_INDEPENDENT_REVIEW_DISPOSITION_2026-10-14.md)
now records a pass for all submitted counts and mathematical labels, with
explicit additional coverage recommendations. Final ratification follows the owner's
explicit decision, not an inference from REVIEW_PASS.

```bash
sed -n '1,240p' spu_strategy/contract_aor_s1_product_fragment_2026-10-13.md
sed -n '1,240p' spu_strategy/contract_aor_s1_finite_profile_amendment_2026-10-13.md
sed -n '1,240p' spu_strategy/AOR_S1_COMPARATOR_WIDTH_PROOF_2026-10-13.md
sed -n '1,240p' spu_strategy/AOR_S1_OPERATION_SCHEDULES_2026-10-13.md
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/AOR_S1_REVIEW_PACKET_2026-10-14.md docs/PARALLEL_TRANCHES_2026-10-14.md
```

Begin with the existing integer product fragment rather than expanding the
expression grammar. This packet adds review obligations, not numerical limits,
candidate code or a qualification allocation. Preserve completed AOR-1 evidence.

## Review subjects and required records

| Subject | Existing specification | Required review record |
|---|---|---|
| Value/canonical identity | Product-fragment draft: `(a+b sqrt(3)) U^k`, canonical zero and half-open balance interval. | Uniqueness argument, exact endpoint witnesses, negative-norm and both-sign witnesses. |
| Finite profile | Amendment: signed64 stored coefficients, signed32 exponent, signed136 coefficient temporaries, signed280 comparator workspace. | Check each intermediate bound and first failure; a temporary refusal must not be labeled final numerical overflow. |
| Comparator | Width proof: coefficient signs and exact squared comparisons. | Review input preconditions, signed minimum promotion and inclusive lower/exclusive upper endpoints; no floating-point oracle. |
| Local rebalance | Product/conjugation ratio proofs. | Certify at most one adjustment only for validated canonical operands; sums retain general normalization. |
| Work accounting | Operation schedules and hand-derived seeds. | Independently count every branch/path, including failed validation, adjustment scans and commit. Logical primitive counts and kernel arithmetic counts remain distinct. |
| State preservation | Immutable inputs and atomic tuple writes. | Destination/source alias witnesses, refusal immediately before commit and absence of published partial read-only results. |
| Domain limits | Same-k sums and norm-one inverse only. | Unequal-k sum, nonunit inverse and zero inverse have distinct declared outcomes. |

## Fixture packet still required

Build a machine-readable fixture packet only after reviewing the above schedule.
Each row must identify operation, exact arguments, initial destination, diagnostic
budget, expected result/status, charged units, and its independent derivation.
Do not obtain expected counts from the eventual candidate counter.

Required families are canonical zero and malformed zero; four embedding-sign
combinations; both normalization directions and exact endpoints; product,
conjugation and unit-inverse adjustment/no-adjustment paths; same-k cancellation;
unsupported operations; signed minima/maxima; exponent, norm and temporary
refusals; aliasing; and budget exhaustion before validation, arithmetic and commit.

Explicitly resolve the 64-adjustment terminal-scan obligation. Stored signed64
inputs may not reach every algorithmic path: classify any wider internal fixture
as a kernel diagnostic rather than inventing a public operand that violates the
profile. Assertions must exercise reachable changing state.

The [initial fixture review](AOR_S1_FIXTURE_REVIEW_2026-10-14.md) now records
83 hand-derived operation rows, comparator/alias/control proposals and a
reachability bound for public normalization.
It is a review draft with no candidate execution or independent sign-off.
The [schedule reconciliation](contract_aor_s1_schedule_reconciliation_2026-10-14.md)
flags a three-versus-four multiplication contradiction and proposes the smallest
explicit correction preserving drafted counts. Candidate implementation remains
HOLD pending separate implementation authorization. The correction and status/codec
boundaries are now ratified; executable qualification remains a separate gate.
The schedule's original literal seeds are useful review inputs, not a complete
qualification corpus. Preserve their original identities; any corrected seed
requires a named defect and minimal amendment before implementation.

## Independent oracle and fault controls

Use an expansion-backed exact integer pair oracle for bounded exponents, with
its own declared bit/work refusal outcomes. Large-exponent witnesses may use
independently proved unit identities; they must not silently force expansion
beyond checker bounds. Oracle exhaustion is infrastructure, never a candidate
arithmetic status or an inequality verdict.

The later qualification contract must name mutations of exponent, coefficient,
adjustment direction, endpoint inclusion, equality result, budget charge and
partial destination write. Each mutation must fail a named falsifiable check.
Require a separate derivation of expected outcomes and charges; candidate
rewrite/counter code cannot serve as its own expected-answer generator.

## Exit from this preparation

Keep S1 implementation HOLD under the owner's authorization boundary. The
[isolated contract draft](contract_aor_s1_isolated_implementation_2026-10-14.md)
now specifies source separation, coverage additions, commands and proposed budgets.
Review and separate execution authorization are required. No new opcode, RTL width
or hardware benefit follows.
S3 workload preparation can refine input/baseline definitions, but benchmark
execution depends on accepted S1 qualification and its own budget.
