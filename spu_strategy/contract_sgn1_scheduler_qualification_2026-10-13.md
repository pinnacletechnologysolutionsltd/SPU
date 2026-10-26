# SGN-1 synchronous scheduler: bounded FCC qualification

Date: 2026-10-13. Status: COMPLETE for bounded FCC scheduler qualification;
artifact PASS and detached repository/software sequence COMPLETE (exit 0).
Roles: draft, halt-and-flag, audit.

## Commands

```bash
python3 software/tests/test_sgn1_scheduler_preflight.py
python3 software/tests/test_sgn1_scheduler_qualification.py --help
python3 tools/doc_audit.py --actual-pass 238
git diff --check -- software/research/sgn1 software/tests/test_sgn1_scheduler_qualification.py spu_strategy/contract_sgn1_scheduler_qualification_2026-10-13.md
```

Freeze selected source and fixture copies in
`build/sgn1/scheduler_20261013/qualification_preparation_01/snapshot/`, retaining
relative source names and a SHA256 manifest. Run the short preflight from that
snapshot. Preserve its exit/output, all sixteen negative-control reasons and
the generated fixture-case count before launch. No all-pair qualification runs
in the agent foreground. Launch this one exact detached sequence:

```bash
tools/run_detached_job.sh \
  --output build/sgn1/scheduler_20261013/qualification_01 \
  --timeout 3000 --notify-desktop -- bash -c 'set -e
python3 build/sgn1/scheduler_20261013/qualification_preparation_01/snapshot/software/tests/test_sgn1_scheduler_qualification.py --output build/sgn1/scheduler_20261013/qualification_01/artifacts
bash tools/verify_repo.sh
python3 software/tests/test_rotc_vm_rtl_trace.py
python3 software/tests/test_irotc_vm_trace.py
python3 software/tests/test_rational_robotics.py
python3 software/tests/test_rational_som.py
python3 software/tests/test_lucas_mac_oracle.py
python3 software/tests/test_pade_batch_inversion.py'
```

Budget: one attempt, 3,000-second external wall-clock limit and cumulative
budget 3,000 seconds, including qualification and required repository/software
gates. No retry, substitute method or timeout extension after consumption.
Stop the agent turn after LAUNCHED; interpret one terminal marker later.
Timeout is infrastructure, not a falsified scheduler. Host-only isolated changes
do not require FPGA synthesis; no production RTL or arithmetic kernel changes.

## Entry conditions and numerical scope

Require COMPLETE exit 0 for both serialized symmetry and routing regressions.
The owner's continued software instructions authorize this next bounded tranche;
earlier fixture-plan null budgets remain historical, not execution authority.
Bind the protocol/fixture hashes in the scheduler preparation packet unchanged.
Use unbounded exact integer payloads and queues on FCC_R1/R2 only.
No mesh, stencil, reductions, hierarchy, AOR, finite-buffer or hardware scope.

Qualification adds `scheduler_controls.py`, `scheduler_qualification.py` and
`software/tests/test_sgn1_scheduler_qualification.py`. The checker caches only
immutable reference-graph/BFS tuples; node state and accounting are fresh per
case. Recheck the short preflight after this scoped checker change.

## Frozen qualification and acceptance

Run all 4,138 all-pair cases, fresh-state each, plus eight frozen traffic cases
and two literal scheduling fixtures: 4,148 cases per node order per seed.
Run seeds 0,1,17 independently and both forward/reversed node iteration.
Every case must drain within its original tick cap, match independent tick
transitions and per-identity conservation, preserve exact application sums,
respect service/link capacity and satisfy all available literal checkpoints.

Retain every canonical full trace in gzip JSON-lines files. Compare semantic
SHA256 digests across all six runs, excluding host duration/compression headers.
Retain per-fixture latency ticks, storage peaks, service operations, suppression
counts and admission-sort comparisons; host runtime is separate observational
cost. Freeze/check source hashes before and after each child and coordinator.

Sixteen controls must each retain the specified named first counterexample:
wrong accumulator, premature seen, dropped fanout, wrong preference, free duplicate
service, hidden link drop, missing observations, same-tick fanout, wrong FIFO,
duplicate application, missing/extra unicast copies, duplicate delivery,
missing/extra wavefront copies and redundant post-drain tick.
Any mismatch, missing observation or escaped control halts qualification.

The artifact PASS_SCHEDULER_FCC_HOST_ONLY does not itself establish full job
success: the detached sequence must also have its sole COMPLETE marker and
exit 0. Phase A closeout is NOT ACHIEVED by this tranche; the original mesh
baseline/cost boundary still requires a separately reviewed disposition.

## Retained result

The sole terminal marker in `build/sgn1/scheduler_20261013/qualification_01/`
is COMPLETE. `result.json` records exit 0 and 1,142 seconds against the
3,000-second limit. The coordinator artifact records 24,888 case executions,
identical semantic hashes for both node orders across seeds 0,1,17, and all
sixteen control types rejected under each seed. The repository/trace/math
commands in the frozen sequence all succeeded. No physical claim follows.
Preserve the original execution contract in the frozen source snapshot and
source manifests; this live status update does not rewrite executed inputs.
