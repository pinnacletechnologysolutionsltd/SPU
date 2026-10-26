# ROUTE-ALG-3 preparation (nothing built or executed)

Private copy: `build/route_alg3/source` (from the fixture's `capture_source`; original untouched).
Change: `common/router2.cc` (+1 include, policy switch, counters) and new `common/route_alg3.h`; diff `build/route_alg3/router2.alg3.diff`.

Hashes (sha256):
- before `router2.cc`  e205fb76861a26bf2db77138a90d0381438904d6abc548c6c4315b2c317a2221 (identical to pinned f681eb3a)
- after  `router2.cc`  fadf94a7632e8a7968c65edee62b167ffe2a83b930127ccf659ce2fa9c1c1fd4
- `route_alg3.h`       067ed94951937dc8646b47d6b0c4503490443de78f96d297b0b639217ce17572
- diff                 71652e9b4d9e4056b3237a70910639f7b510afb4d0a84f669e29d2fade4cd149
- original binary      68af6c61810a9d62f4e212e7c9dc8662963710699442f47a97b8d2fd145c05f2
- original fixture     native.json 79033474...056d, routed.json e8810ce5...6102, fixture.fasm a277e731...55c7

Behavior: env `SPU_ALG3_POLICY` unset = original code path, no counters. `fd` = original policy + counters.
`fd_shadow` = original policy + a read-only check of whether each skipped already-visited arrival would have scored lower
(counts missed improvements WITHOUT changing routing, so it is free of the congestion-evolution confound).
`reopen` = drops the early `was_visited` skip, so the existing `!visited || score.total() > next` test applies.
Counters per arc-route call: pops, pushes, revisits, stale pops, shadow_missed, final cost/delay, bb mode, iter+5 stop rule.
The fixture has 42 nets (<200), so router2 runs one serial ThreadContext: deterministic, no thread races.
Not compile-checked yet (a compile is a native execution).

## Proposed execution limits (NOT granted; need your approval)
Build, 1 detached job via `tools/run_detached_job.sh`, 2 attempts max (second only to fix a compile error), no other retries:
- 900 s per attempt (reference build 279.6 s at -j 2), 1,800 s cumulative; ~270 MB output under `build/route_alg3/build`; `ulimit -c 0`; memory cap 6 GiB (MemoryMax on the unit).
Fixture runs, foreground, <= 6 runs total, 30 s wall each, 4 GiB address space (chipdb ~160 MB mapped), 16 MiB per file, no core, no retries:
1. R0 original binary, policy unset: reproduces the retained outputs (determinism baseline)
2. R1 new binary, unset: patch is inert
3. R2 new, `fd`: counters do not change routing
4. R3 new, `fd_shadow`: missed-improvement counts on the unchanged route
5. R4 new, `reopen`
6. R5 new, `reopen` again: determinism of the variant
Gate: R0-R3 must be byte/graph-exact against the retained fixture (`compare.py exact`); if not, stop, no reopening interpretation.
Commands: `build.sh`; `run_fixture.py BINARY RUN_ID [POLICY]`; `compare.py exact RUN` / `compare.py calls FD_SHADOW_RUN REOPEN_RUN`.
Reopen run diverges from the baseline once any call picks a different path; `compare.py calls` reports the first divergent call and compares only the identical-state prefix like-for-like.
