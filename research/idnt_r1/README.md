# IDNT-R1 — IDNT (0x18) execution in QR-file RTL profiles

Owner-approved bounded experiment, 2026-11-06. Implementation commit `16af70d`
on branch `exp/idnt-r1`, based on `f35d03c` (dev/next). Disposition: simulation
PASS; synthesis UNKNOWN; hardware qualification NOT RUN; v0.2 integration
DEFERRED.

**Hypothesis.** `spu13_core` can execute canonical `IDNT QRd` (QRd ← (1,0,0,0),
lane = index mod 13, as in `software/spu_vm.py` and `software/vm/spu_vm.cpp`)
through the existing QLDI write path, without changing builds that have no QR
register file (Gen-1 surd CPU / H0 settings).

**Baseline.** `f35d03c`: the core counted IDNT for REGEN but executed nothing.
The Stage-B chain did not mirror IDNT, although
`contract_regen_stageB_2026-08-20.md` requires it.

**Change.** `HAS_QRF`-gated IDNT handler; Stage-B chain mirrors IDNT as a LOAD
of (1,0,0,0). Frozen `hardware/boards/artix7/wukong_v3/cpu_v02/` copy untouched.

## Results (Icarus 14, OSS CAD Suite 20261027; sources gathered as `run_all_tests.py` does)

| Run | Result |
|---|---|
| `spu13_core_idnt_tb.v` on the modified core | 20/20 checks PASS (`logs/negative_controls/run_modified.log`) |
| Same bench, unmodified core (`f35d03c`) | 12 checks FAIL (`run_baseline.log`) |
| Same bench, handler without chain mirror (`harness/make_handler_only_control.py`) | 2 REGEN-recovery checks FAIL (`run_nochain.log`) |
| `receipts/regress-job-01` (FAILED, exit 1) | 15/21 benches PASS, 5/5 Python gates PASS; 6 NO_VERDICT, caused by a harness defect |
| `receipts/rerun-job-01` (COMPLETE, exit 0) | the 6 benches: 6/6 PASS |

**Harness defect (job 01).** `harness/run_benches_job01_original.py` selected
the last module in a bench file as the simulation top. Six benches declare
primitive models after the top, so `SDPB` was simulated and printed nothing.
`harness/run_benches.py` uses the runner rule instead (filename-matching
module, else the first one). The 15 job-01 passes each printed their bench's
own PASS verdict.

**Source identity.** `spu13_core.v` sha256 `fdedcd13…` is identical in both job
pre-launch records (`prelaunch_hashes.txt`, `rerun_prelaunch_hashes.txt`) and
in commit `16af70d`.

**Limitations.** Simulation only; no synthesis or resource measurement; no FPGA
run. The scripts ran from `build/idnt-r1/` in the worktree, and their relative
paths assume that location. Compiled `.vvp` images are omitted (they can be
rebuilt). The bench list covers release benches that instantiate `spu13_core`
or `fpga_chain` directly or through other modules. The standard full release
regression for the branch is recorded separately.
