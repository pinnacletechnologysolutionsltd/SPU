# Surd register execution strategy comparison

Status: one bounded software comparison authorized by the owner. S0 remains the
accepted reference; no S0 source or evidence is modified.

## Frozen comparison

Compare explicit-denominator `FIT_RESCUE` against cross-cancellation,
adaptive normalization, and both together. Use S0's exact cohort and the same
W=16, 32, and 64 lane budgets. The adaptive candidate normalizes a nonzero raw
result when the maximum signed/unsigned result width reaches W-1 and is no
greater than W. All four candidates use `FIT_RESCUE` for the same fallback
boundary.

The retained cohort is all 32 frozen S0 inputs at chain lengths 1, 3, 6, and
12. Its catalog joints have b=0. The separate synthetic Surd cohort has four
explicit operand pairs, ADD and MUL, and the same three lane widths. A boundary
cohort uses q=2^(W-3)-1, x=R(1,0,q), and y=(q,0,3) or (q+1,0,3), followed by
two sequential multiplications at each W. The first operand pattern has a
cross-cancellable common factor; the second is a coprime negative control.
Boundary commits use BOUNDARY semantics, with narrow failure and wide fallback
accounted separately. Compare each result exactly against the Fraction oracle.

Record named intermediate widths, per-operation narrow status counts, fallback
counts, re-entries, nonresident results, GCD calls and Euclidean steps, exact
divisions, cross-cancellation applications, and adaptive normalizations.
Timings are outside scope. Do not infer native throughput, register pressure,
or hardware behavior from software counts.

The frozen campaign budget is one attempt, a 60-second per-attempt timeout,
and a 60-second cumulative timeout. Any failed or unavailable run consumes the
attempt. No retry or timeout extension is authorized by this contract.

```bash
python3 software/experiments/surd_register_strategy_compare_run.py --freeze build/spu_surd_register/strategy_compare_20261007/plan_05
bash software/experiments/run_surd_register_strategy_compare_recorded.sh build/spu_surd_register/strategy_compare_20261007/plan_05/plan.json build/spu_surd_register/strategy_compare_20261007/run_05
git diff --check -- software/experiments/surd_register_strategy_compare.py software/experiments/surd_register_strategy_compare_run.py software/experiments/run_surd_register_strategy_compare_recorded.sh spu_strategy/contract_surd_register_strategy_compare_2026-10-07.md
```

The freeze records current candidate-source hashes and validates every source
hash from S0's accepted plan before comparison. The run refuses changed source
or input hashes and writes fresh results beneath `build/`. Prior comparison
attempts are retained; run_03's fallback counts are diagnostic only because
its policy-loop filter accidentally rejected the workload's BOUNDARY NORM calls.
Run_04 is retained as a failed boundary-oracle adapter attempt.
