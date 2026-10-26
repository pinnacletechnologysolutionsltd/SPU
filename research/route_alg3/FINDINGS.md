# ROUTE-ALG-3 findings (native, 42-net fixture; preliminary research result)

Build: private copy, detached job `build/route_alg3_jobs/build_attempt01`, COMPLETE exit 0, 297 s (attempt 1 of 2).
New binary sha256 579c54af...9985. Source hashes unchanged after the build (router2.cc fadf94a7..., see PLAN.md).
Runs (all exit 0, < 30 s, limits per PLAN.md) in `build/route_alg3/runs/`: R0 original binary; R1 new/unset; R2 `fd`; R3 `fd_shadow`; R4 `reopen`; R5 `reopen` repeat. 6 of 6 executions used.

## Gate (exact correspondence with retained fixture)
R0, R1, R2, R3: native.json, routed.json and fixture.fasm byte-identical to the retained originals; 0/42 nets differ; retained `route_audit` PASS (465 resources).
=> patched binary is inert when unset, counters do not change routing, `fd_shadow` is observation-only.

## Results
- Fixture is tiny: 20 route calls (every call hit the iter+5 stop rule).
- `fd_shadow` (routing unchanged): 4 of 20 calls had skipped arrivals that would have scored lower, 5,506 candidate arrivals in total (344, 48, 4,973, 141; largest gap 1.24 cost units). Candidate arrival improvements are common in the busy calls.
- Those better candidate arrivals did NOT improve completed routes in the shared prefix: calls 0-11 are in the identical state in both policies and all 12 final costs are identical to 9 digits (sum 33.2097), including the 3 calls that had 344 / 48 / 4,973 missed improvements. Better candidates were off the winning path.
- Reopening cost: 28,205 pops vs 11,350 on the 20 common calls (2.5x); one call alone went 8,562 -> 24,758. 24,032 revisits and 3,913 stale pops in total.
- `reopen` diverges from the baseline after call 11: one extra route call (`state[2]` arc 5) and 6/42 nets differ. Cause is not a better path: each push draws `t.rng.rng()` (router2.cc line 897), so extra pushes change the RNG stream and ordering. This is the congestion/RNG-evolution confound, observed directly.
- Among 20 common (net,arc) calls only 3 have different final cost: 2 slightly better (-0.005, -0.00007), 1 worse (+0.143, from a different state). Net: reopen sum 51.075 vs fd 50.938 (+0.3%), so no cost advantage, and it is not a like-for-like comparison after divergence.
- Legality: reopen routes (R4, R5) pass the retained native-ID connectivity/ownership audit (466 resources, 99 sinks). That audit is not timing, DRC or bitstream signoff.
- Determinism: R4 and R5 produced identical alg3.jsonl and native.json.

## Conclusions
- CONFIRMED: first-discovery rejects better candidate arrivals in real router state (5,506 events on 4 calls), exactly as the synthetic model predicted.
- CONFIRMED: reopening is ~2.5x more search work on this fixture, deterministically, with legal routes.
- CONFIRMED: policy changes alter RNG consumption and so downstream call order/state; later comparisons are not like-for-like.
- FALSIFIED (on this fixture): that first-discovery's rejected arrivals translate into worse completed routes. In the identical-state prefix, 12/12 routes had the same cost; overall reopening showed no cost advantage.
- FALSIFIED (on this fixture): that the ALG-1 6-7% path-cost excess carries over. Real scoring + the iter+5 rule + weighted heuristic left no visible excess here.
- INCONCLUSIVE: effect on convergence, iteration count, congestion resolution, or the CPU timeouts. 20 calls, one iteration, almost no congestion: the fixture cannot test PathFinder dynamics. Nothing here is evidence about the CPU.

## Decision input
No benefit beyond noise and 2.5x search cost: this is your "no meaningful benefit / more work" branch. It does not justify modifying production router2 or a larger OpenXC7 reopening experiment. Remaining open only if you want a congested fixture (more calls than 20) to test dynamics; I would not spend more on that without a new reason.
