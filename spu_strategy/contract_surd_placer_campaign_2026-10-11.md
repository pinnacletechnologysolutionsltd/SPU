# Authorized serialized alternate-placer campaign

Run the frozen checks:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_03/test_launch.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_03/test_placement.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_03/worker.py preflight
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_surd_placer_campaign_2026-10-11.md
```

Submit the next reviewed attempt with:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_03/launch.py
```

Apply the scope and qualification boundaries of `contract_surd_placer_restart_2026-10-11.md`. The owner instruction “Authorized, 3 attempts, repairs and audits authorized. Begin.” replaces its proposed one-slot budget with **three attempts, 7,200 seconds each, 21,600 seconds cumulative**. Record authorization in `campaign_sa_budget.json`. Do not extend any limit or pool earlier campaign allocations.

Keep the existing four-hour timing run intact. Refuse launch unless it has exactly one terminal marker, prior attempts in this campaign have unique terminal markers, and no Yosys/nextpnr process is active. Recheck before and after hashing. This is a guarded launcher, not a host-wide atomic scheduler; other callers must also observe the single-job policy.

Schedule only the first submission using a local systemd timer at the existing job's frozen deadline plus 120 seconds. Timer waiting performs no synthesis, placement or routing and consumes no attempt. A missing or ambiguous predecessor result, busy host, changed input or failed preflight refuses submission without reserving a slot. Preserve schedule metadata and submission stdout under `launch_queue_01`. Its terminal marker and `trigger_result.json` describe submission only; never interpret them as routing qualification. The queue trigger has a 60-second subprocess bound; a later actual tool job has its own external 7,200-second detached-runner bound.

Actual submission reserves a slot before invoking `tools/run_detached_job.sh`; even a submission failure leaves that reservation consumed. Use distinct `routing_02`, `routing_03`, `routing_04` evidence directories. Do not overwrite attempts. After LAUNCHED record unit/evidence and end the agent turn. Linux owns waiting and execution.

Do not automatically retry. Interpret each unique terminal result and audit its stage, constraints, topology, routing and required timing coverage before preparing a further attempt. Repairs and audits are authorized within the existing placement/tool-flow scope, preserving arithmetic and retirement semantics. Refreeze changed inputs for every repaired candidate. Any RTL, arithmetic, pipeline or architecture change requires a separately reviewed contract and full applicable qualification gates.

The 80-DSP reduced probe and actual packed-CPU preflight remain the existing evidence; their source hashes are reused. No redundant full regression or synthesis is claimed. Legal routing and 25 MHz remain unqualified until independently reviewed complete evidence supports them.
