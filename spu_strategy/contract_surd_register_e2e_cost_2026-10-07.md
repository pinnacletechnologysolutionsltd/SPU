# Surd register end-to-end cost comparison

Status: one bounded host-software campaign authorized. S0 and its accepted
evidence remain immutable. No RTL, ISA, or hardware action is included.

## Frozen paths and cases

Measure four exact two-multiply paths at W=16, 32, and 64:

* explicit denominator with FIT_RESCUE;
* cross-cancellation followed by FIT_RESCUE;
* separate normalization rescue, triggered at result width W-1 or on lane
  overflow, followed by wide fallback only if normalization cannot re-enter;
* cross-cancellation plus separate normalization rescue.

Measure three prepared-input classes: ordinary small coefficients; a
normalization-rescuable chain using q=2^(W-3)-1 and operands
R(1,0,q), R(q,0,3); and an unavoidable-fallback control using
R(1,0,q), R(q+1,0,3). Each chain multiplies by the same right operand twice.
Exactness checks run outside the timed loops. Invalid inputs raise immediately
and never enter the arithmetic fallback path.

Each row has 100 untimed warmups and five trials of 2,000 chains. Report raw
trial nanoseconds, median time per chain and multiply, normalization rescues,
wide fallback/re-entry/nonresident outcomes, intermediate widths and GCD/
division work. The input conversion cost is excluded; each end-to-end path
starts from the same prepared explicit-denominator values.

The frozen campaign budget is one attempt, a 60-second per-attempt timeout,
and a 60-second cumulative timeout. A failed or unavailable attempt consumes
the slot. No retry or timeout extension is authorized here.

```bash
python3 software/experiments/surd_register_e2e_run.py --freeze build/spu_surd_register/e2e_cost_20261007/plan_02
bash software/experiments/run_surd_register_e2e_recorded.sh build/spu_surd_register/e2e_cost_20261007/plan_02/plan.json build/spu_surd_register/e2e_cost_20261007/run_02
git diff --check -- software/experiments/surd_register_e2e.py software/experiments/surd_register_e2e_run.py software/experiments/run_surd_register_e2e_recorded.sh software/experiments/surd_register_strategy_compare.py spu_strategy/contract_surd_register_e2e_cost_2026-10-07.md
```

The freeze validates accepted S0 source hashes and records their plan/results
alongside the comparison inputs. Host timings do not estimate RTL latency,
throughput, area, energy, or pipeline structure.

Run_01 is retained, but its timings are invalid: an implementation defect left
the Fraction oracle inside the timed chain. Run_02 moves every exact oracle
comparison outside timing and records the pre-normalization result/intermediate
width peaks.
