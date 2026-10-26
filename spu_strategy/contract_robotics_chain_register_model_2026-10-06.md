# Robotics chain and logical Surd-register model

Date: 2026-10-06 (Pacific/Auckland)
Status: ACTIVE — software-only experiment.

## Commands

```bash
timeout --signal=KILL 60s python3 software/tests/test_rational_robotics_unshared.py
timeout --signal=KILL 60s python3 tools/rational_robotics_unshared_demo.py
tools/run_detached_job.sh --output build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_01/job_01 --timeout 900 --unit spu-robotics-chain-isa-20261006-01 --notify-desktop -- python3 build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_01/runner.py
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- docs/DEMO_TOUR.md software/lib/rational_robotics_unshared.py software/tests/test_rational_robotics_unshared.py software/experiments/rational_robotics_isa_adapter.py tools/rational_robotics_unshared_demo.py spu_strategy/contract_robotics_chain_register_model_2026-10-06.md
```

## Frozen workload and semantics

Use all 32 retained vectors from the frozen C1 retained input corpus. Preserve
each source identity and hash. Joint chains use the maintained exact rotation
catalog in the frozen order: lengths 1, 3, 6, and 12. Length 12 repeats the
catalog twice. This experiment therefore measures retained vector × rational
joint chains; it does not claim retained Surd × Surd joint inputs.

The reference is `fk_chain` followed by `inverse_fk_chain`, including the
maintained adjugate behavior. The opt-in chain API retains unshared integer
triples across all joints and constructs exact output `Q3` fractions at the
boundary. Exact output equality is mandatory before timing.

## Logical register models

1. **Fixed scale:** one corpus-derived implicit denominator for every value.
   Fused MAC/MSUB results must divide exactly by that scale. A non-divisible
   result is reported as out of domain; the model never rounds. Numerator
   overflow uses exact wide fallback.
2. **Explicit denominator:** independent `(a,b,d)` values; exact LCM alignment
   for addition; canonical output materialization only at the chain boundary.
   Intermediate numerator and denominator overflow uses exact wide fallback.
3. **Shared scale:** one scale for the four vector components and one for each
   three-coefficient joint. Scales multiply through forward and recovery
   stages; output fractions are materialized only at the boundary. Overflow
   uses exact wide fallback.

All models use unbounded Python integers for the fallback oracle and report
observed signed widths. Width budgets 16, 32, and 64 bits count arithmetic
stages needing the declared exact-wide fallback. Instruction counts are the
frozen logical/component operation model in `results.json`; they are not cycle
counts or a claim about an implemented ISA. No physical CPU/SPU register, RTL,
opcode, firmware, synthesis, or device operation is changed or tested.

## Timing and evidence

For each chain length, time the complete 32-vector batch through the reference
and fused API, including fixture decode, wrapper construction, output
materialization, and coefficient serialization. Use two warmups, five
`perf_counter_ns()` trials, and ten repetitions per trial. Collect arithmetic
width traces separately from timed runs. The runner records frozen code/input
hashes, output digests, trial totals, model instruction counts, width profiles,
fallback events, and terminal status. One detached attempt; 900-second outer
limit; no automatic retry.
