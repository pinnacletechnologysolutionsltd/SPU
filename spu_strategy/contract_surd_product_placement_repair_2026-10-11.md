# Surd product placement repair — 2026-10-11

Run the frozen checks before submission:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_01/test_placement.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_01/test_launch.py
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_01/worker.py preflight
python3 tools/doc_audit.py --actual-pass 243
git diff --check -- spu_strategy/contract_surd_product_placement_repair_2026-10-11.md
```

Launch exactly once:

```bash
python3 build/spu_surd_register/product_placement_repair_20261011/preparation_01/launch.py
```

## Scope and reviewed mechanism

Constrain only the five existing Surd product DSP groups to disjoint DSP-site regions. Each group contains 16 packed DSPs and receives 32 candidate sites within one column and a bounded vertical band. Leave fabric LUTs, carry logic, registers and other units unconstrained. Preserve existing packed relative constraints; do not assign individual DSP BELs.

This is a placement hypothesis motivated by observed product-net conflict incidence and DSP endpoint spans. It does not establish the cause of congestion. It narrows the earlier placement-review proposal to DSP-only regions, avoiding constraints on surrounding fabric whose feasible placement has not been demonstrated.

Reuse the frozen mapped CPU, constraints, chip database, observer tool, seed 1 and 25 MHz target. Do not edit RTL, resynthesize, change the ISA, alter the five-lane arithmetic, signed correction, widths, normalization, state transitions, latency, reset or retirement. REGEN and other concurrent work remain outside this repair.

Validate all lane membership, site capacity and disjointness before adding constraints. Require packed cell parameters, attributes and connectivity to remain identical across constraint application. Before routing, verify the functional topology digest and all 80 actual DSP placements against their permitted sites; export the full placed-net census for conflict-share comparisons. Reject changed frozen inputs before submission and check them again following successful execution.

## Evidence and budget

Use preparation and evidence under `build/spu_surd_register/product_placement_repair_20261011/`. `preparation_01/inputs.json` records frozen input hashes. `packed_preflight_04/result.json` records PASS on the actual CPU pack; its placement report records all 80 DSP assignments and unchanged packed topology. Placement controls cover one positive and five negative cases; launch controls cover one positive and four negative cases.

The earlier foreground setup probes tested hook/API compatibility; they did not launch routing attempts. Placement feasibility and routing improvement remain experimental.

Owner instructions “Repair and relaunch.” and “Continue.” renew one attempt at the previously reviewed diagnostic bound: maximum attempts 1, per-attempt wall clock 1,800 seconds, cumulative 1,800 seconds. Reserve its slot before invoking the detached runner. No retries or timeout extension are authorized by this contract.

The original three-slot diagnostic campaign is exhausted. The separate 14,400-second timing job has its identity recorded in `other_timing_job_identity.json`; do not restart, modify or charge this diagnostic against it. Concurrent host use prevents an exclusive-host runtime comparison.

## Interpretation

Record the detached unit and evidence directory after LAUNCHED and end the agent turn. Interpret only exactly one durable COMPLETE, FAILED or TIMEOUT marker. TIMEOUT is an infrastructure outcome, not a functional verdict. Retain complete observer iterations and reject incomplete captures.

An exit-zero routing run still requires independent review of legal routing, complete required timing coverage and PASS at 25 MHz. Neither placement preflight nor this diagnostic budget qualifies integrated timing or silicon. Historical frozen regression and Padé results retain their existing scopes; no new full qualification is claimed. Any subsequent RTL or arithmetic repair requires the full AGENTS.md gates and separately authorized expensive-job budget.
