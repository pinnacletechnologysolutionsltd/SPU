# Robotics chain/register model repair 01

Date: 2026-10-06 (Pacific/Auckland)
Status: OWNER-AUTHORIZED REPAIR — software-only.

Attempt 01 is preserved as FAILED, exit 1, zero timing trials. Its runner
resolved `tools/rational_robotics_unshared_demo.py` below its experiment
directory instead of from the repository root. Attempt 02 fixes that resolver
and runs in a fresh directory. Inputs remain byte-identical to the frozen
attempt 01 cohort. The runner implementation hash is frozen in attempt 02's
`plan.json`.

This authorization permits exactly one fresh attempt, with the original
900-second outer limit, two warmups, five trials, and ten repetitions per
trial. No additional repair or retry is authorized here. All arithmetic,
correctness requirements, timing scope, and software-only boundaries remain
as stated in `contract_robotics_chain_register_model_2026-10-06.md`.

Command:

```bash
tools/run_detached_job.sh --output build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/job_01 --timeout 900 --unit spu-robotics-chain-isa-20261006-02 --notify-desktop -- python3 build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_02/runner.py
```

The prior terminal record remains at
`build/spu_lossless_reduction/robotics_chain_isa_20261006/attempt_01/job_01/`.
Hardware operations remain zero; device equivalence remains untested.
