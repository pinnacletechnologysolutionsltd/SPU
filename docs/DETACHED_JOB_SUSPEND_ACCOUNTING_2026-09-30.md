# Detached Job Suspend Accounting Finding

**Date:** 2026-09-30  
**Scope:** T1q Artix-7 route recovery, seed 1  
**Classification:** Completed route with suspend-inflated elapsed metadata

## Evidence

The detached result at
`build/gpu/t1q_truth_table_20260929/build_seed1/run_02/result.json` has one
`COMPLETE` marker, exit code 0, timeout 1,800 seconds, and recorded duration
39,754 seconds. The build produced
`build/spu_a7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.bit`; post-route metrics
at `build/metrics/artix7_100t_GPUVGA_T1Q_TRUTH_TABLE_MATERIAL_Q1.json` report
`clk_pixel=36.92 MHz`, `PASS` against 25.00 MHz.

The recorded interval is 2026-09-29 21:05:37 UTC through 2026-09-30 08:08:11
UTC. In the machine's Pacific/Auckland timezone this is 10:05:37 through
21:08:11 on 2026-09-30. The journal records:

- 10:18:44 NZST: system suspend began; `user.slice` was frozen.
- 21:05:22 NZST: the system resumed; `user.slice` was thawed.
- 21:08:11 NZST: the detached unit completed.
- systemd accounting: 15m57.803s service wall time and 18m14.870s CPU time.

The suspend interval was 10h46m38s. The run had executed for about 13m07s
before suspend and completed about 2m49s after resume. The systemd service
wall-time accounting therefore places active service runtime below the
1,800-second timeout. The 39,754-second result duration differs because
`tools/run_detached_job_worker.sh` records `date +%s` before and after the
command, which includes the system-suspend interval. The command returned
exit 0; the detached runner wrote `COMPLETE`, not `TIMEOUT`.

## Decision

The T1q route, pack, and 25 MHz pixel-clock checks pass for this exact source
and profile. The recorded wall interval includes a confirmed host suspend;
the 39,754-second field must not be presented as active build runtime. No
hardware programming, UART transmission, or visual observation is implied.

## Runner policy follow-up

No detached-runner code changed for this finding. Future contracts should
state whether their budget is suspend-inclusive elapsed time or active
service runtime. The runner should record both values. If budgets remain
suspend-inclusive, suspend should invalidate the attempt or a
suspend-aware deadline should be used; if budgets are active-runtime, name
that clock explicitly. Do not silently reinterpret existing frozen budgets.
