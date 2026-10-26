# SGN-1 scheduler preparation: frozen inputs and checker requirements

Date: 2026-10-13. Status: PREPARATION ONLY; implementation/qualification pending
successful serialized symmetry and routing regressions. Roles: draft, review, audit.

## Preparation commands

```bash
sha256sum spu_strategy/contract_sgn1_phase_a_2026-10-12.md spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json
python3 -m json.tool spu_strategy/sgn1_phase_a_fixture_plan_2026-10-12.json > /dev/null
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- spu_strategy/contract_sgn1_scheduler_preparation_2026-10-13.md
```

These inspect preparation; no packet simulator is executed. A subsequent bounded
execution packet must freeze implementation/checker sources and runnable commands.
Do not infer qualification authority from proposed fixture-plan budgets, which
remain null. No scheduler execution attempt has been launched.

## Bound inputs

| Artifact | SHA256 |
|---|---|
| `contract_sgn1_phase_a_2026-10-12.md` | `ebdf883e6afa9d53ac3eaf29272a86eec6f1a15e4c9f84b4592925260a29bf96` |
| `sgn1_phase_a_fixture_plan_2026-10-12.json` | `289c2860aca4ea4607151e181da3995b2adda2e7e88b5816104bd9cde97bac8b` |

Both files reside in `spu_strategy/`. Freeze every existing injection row,
endpoint-ID mapping, ordinal, payload, checkpoint and expected accumulator.
Any hash mismatch halts preparation for review; do not silently refresh bindings.
Expected labels are preparation, not evidence of a scheduler run.

## First implementation scope

Use the existing 13/63-node exact graphs and qualified local port selector.
Keep packet validation/state, admission, node service, synchronous commit and
independent checking in separate small modules. Freeze their source paths in
the execution packet. No hierarchy, reduction, stencil, AOR payload, RTL or CPU
integration is included. Ordinary state updates are exact integer additions.

Bind the seven tick phases and packet-key definitions in the original contract.
Preserve the inbox prefix, append sorted link arrivals, then ordinal-sorted host
injections. Service one inbox item or one oldest fanout task per node per tick.
Use the specified alternating preference, initially INBOX; idle preserves it.
First visits mark seen, add once and append fanout, without same-tick transmission.
Duplicates consume inbox service without application updates or new fanout.
Include the reverse ingress port in fanout. Commit all sends after every node
has serviced; arrivals occur next tick. Check node-iteration-order independence.

## Frozen fixture scope and termination

For each graph, use every all-pair case with fresh state, plus many-to-one,
crossing, burst and wavefront fixtures. The fixture plan also freezes
`FIFO_ARRIVAL_BEFORE_INJECTION` and `WAVEFRONT_SHARED_SERVICE` checkpoints.
Retain full queue prefixes, selected services, preference and pending-fanout
observations, not just totals. The mixed wavefront fixture ends with accumulator
8 at node 6 and 3 elsewhere; the FIFO fixture has five deliveries.

All-pair/admission fixtures have the existing 64-tick limit; traffic/wavefront
fixtures have 4,096 ticks. Stop only after all scheduled injections are admitted
and inboxes, pending fanout and in-flight links are empty. SIMULATION_TICK_LIMIT
is non-delivery, distinct from an external wall-clock TIMEOUT.

## Independent checker and falsification

At each post-commit boundary, check unicast identity accounting, unique delivery,
legal hops, exact destination and application sums. Check injected roots plus
created fanout tasks against queued, pending, in-flight, first-visit-consumed and
duplicate-suppressed wavefront copies. Sending moves a task; it creates no copy.
Use component traversal for reached nodes and independent payload accounting
for expected sums; neither may call the scheduler's update/service functions.

Report link/service capacity, peak inbox/fanout storage and seen-set size. Retain
canonical full traces and require identical hashes under seeds 0,1,17, plus
reversed node iteration. Missing required observations mean UNVERIFIED.

Inject hidden drop, duplicate delivery, wrong accumulator, premature seen marking,
duplicate suppression without service cost, same-tick fanout transmission and
incorrect FIFO/preference order. Each must fail a named checker with a retained
first counterexample. Halt on a positive mismatch or escaped negative control.
Unbounded queues establish no finite-buffer backpressure or deadlock guarantee.
Phase A closeout remains unachieved until all original required observations and
any remaining baseline/cost obligations are explicitly resolved.
