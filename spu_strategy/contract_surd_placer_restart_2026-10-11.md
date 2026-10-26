# Surd DSP-region alternate placer restart

Run preparation checks:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_02/test_placement.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_02/test_launch.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_02/worker.py preflight
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_surd_placer_restart_2026-10-11.md
```

After explicit fresh budget authorization and exactly one terminal marker for the existing timing job, submit:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_02/launch.py
```

## Reviewed correction

Select the existing tool's `--placer sa` implementation instead of the default analytical placer. Keep the previous five DSP-only regions, mapped CPU, chip database, XDC, seed 1, observer and 25 MHz target unchanged. No RTL, arithmetic, instruction, clock, latency, retirement or reset change is made. Synthesis already completed for this frozen CPU; this restart resumes at placement and routing without redundant synthesis.

The prior full-CPU attempt has exactly one TIMEOUT marker, exit 124, at 1,800 seconds during analytical placement. It produced no routed design or timing result. Do not interpret this as functional failure or proof that the board cannot fit the CPU.

A reduced fixture retains the original 80 DSP primitive parameters and DSP cascade connections, ties external inputs to zero and omits surrounding fabric. It is a physical feasibility probe, not an arithmetic, clocked or CPU-equivalence test. The analytical placer reached its main loop but timed out at the probe's 55-second bound. The same fixture and regions passed simulated-annealing placement, including post-placement legality and the region checks; reported SA placement time was 22.26 seconds. Thus analytical placement is a reproducible investigation target on this reduced fixture. No stack-level cause, full-CPU speedup or routing benefit is established.

Actual full-CPU packing and constraint application must pass separately in `packed_preflight_05`. Preserve cell parameters, attributes and connectivity through region application. Before routing, verify the functional topology digest and all 80 DSP region memberships; export the placed-net census. Freeze preparation, probe results, mapped inputs, tool and dependencies in `preparation_02/inputs.json`; reject changed sources before submission and after successful tool exit.

## Budget and serialization

The proposed fresh budget is one attempt, 7,200 seconds per attempt and 7,200 seconds cumulative. `campaign_sa_budget.json` remains unauthorized until the owner approves this explicit budget. The earlier single 1,800-second attempt is exhausted; its budget is not extended or reused.

Keep the separate `spu-timing_01-20261011T012925Z-434289` campaign intact. Its evidence is under `main_cpu_integration_20261007/bottleneck_audit_20261011/timing_01`. Refuse submission until exactly one COMPLETE, FAILED or TIMEOUT marker exists there; check this condition before and after source hashing. Do not overlap expensive FPGA jobs. This launcher serializes against the known active campaign; it is not a system-wide scheduler for unrelated callers.

Reserve the new slot before submitting through the detached runner. Record unit/evidence and end the agent turn after LAUNCHED. No automatic retries, increased timeout or substitute attempts are authorized. Interpret only a unique durable terminal marker. Exit zero alone is not a timing qualification: review legal routing, complete required timing coverage and PASS at 25 MHz independently.

This preparation is experimental tool-flow work, not completed hardware qualification. No silicon, board performance, energy or integrated fit claim is made. Preserve historical regression scopes. Before declaring a hardware/build-flow repair qualified, run the full AGENTS.md gates, including the separate Padé build, under an authorized qualification budget.
