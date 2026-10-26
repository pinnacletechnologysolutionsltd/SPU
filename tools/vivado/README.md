# tools/vivado — native Vivado batch flow (PREPARED, NOT RUN)

Non-project mode, Tcl only; no GUI project is a source of truth. One top, one exact part, one file list, one XDC per run.
No bitstream and no hardware step exists in this directory.

```bash
OUT=build/vivado/<unique-id>; mkdir -p "$OUT"          # must be new/empty; never inside hardware/ software/ tools/ docs/ knowledge/
vivado -mode batch -log "$OUT/vivado.log" -journal "$OUT/vivado.jou" \
  -source tools/vivado/spu_vivado_flow.tcl -tclargs \
  -top spu_a7_surd_cpu_base_top -part xc7a100tfgg676-1 \
  -filelist tools/vivado/filelists/base_cpu_top.f \
  -xdc hardware/boards/artix7/spu_a7_surd_cpu_base.xdc -outdir "$OUT"
```
Anything over 60 s goes through `tools/run_detached_job.sh --output build/<new> --timeout <frozen> -- vivado ...` (AGENTS.md §4.2); the Tcl has no wall-clock limit of its own.

| Argument | Meaning |
|---|---|
| `-top -part -filelist -xdc -outdir` | required; nothing is defaulted or guessed |
| `-generic NAME=VAL` | repeatable, passed to `synth_design` |
| `-expect_clock NAME:PERIOD_NS` | repeatable; the run fails after synthesis if the clock is absent or its period differs |
| `-strict 0\|1` | when 1, also fails on constraints that resolved to nothing (log scan) and on non-zero `no_clock` / `unconstrained_internal_endpoints` / `multiple_clock` / `generated_clocks` counts in `check_timing`. The log scan reads only Vivado messages after the flow's scope marker; it also fails on `CRITICAL WARNING [Common 17-55] 'set_property' expects at least one object` (a set_property whose object query matched nothing) |
| `-stage synth` (default) | `synth_design`, reports, `synth.dcp` |
| `-stage place` / `route` | extra stages; refused unless `-ack PLACE_APPROVED` / `ROUTE_APPROVED` is supplied (an owner-authorized run only) |

Outputs in `OUT`: `run_manifest.txt` (Vivado version, UTC time, host, git HEAD, git-status hash, arguments, sha256 of file list, XDC and every source), `synth_*.rpt` (utilization flat/hierarchical, clocks, clock networks, `check_timing -verbose`, timing summary, CDC, methodology, DRC), `structure.rpt` (BUFG/DSP48E1/RAMB/LUT/FF counts), `synth.dcp`, and exactly one of `COMPLETE` / `FAILED` (message). Exit code 0 / 1. An invalid or non-empty `-outdir` is refused and nothing is written into it.

Reading the results: pre-placement timing is an estimate, not closure. A flop-divided clock is **not** derived automatically: until a correct `create_generated_clock` exists, `check_timing` will report the divided domain as unconstrained. The Base XDC keeps that line commented because the register name is unverified; add it from the synthesized netlist in a reviewed XDC, do not guess it.

File lists: `filelists/base_cpu_top.f` (the frozen 20-source Base manifest) and `filelists/tensegrity_link_top.f` (small standalone baseline recorded as working on silicon in `docs/hardware_evidence.md`; its XDC `spu_a7_tensegrity_link.xdc`).

Environment smoke test (needs Vivado; no design, no synthesis): `vivado -mode batch -source tools/vivado/tests/phase2_smoke.tcl`. Proposed, not applied: `proposals/base_cpu_generated_clock.xdc.proposal`.

Validation without Vivado: `tclsh tools/vivado/tests/dryrun_stub.tcl <scratch-dir>` runs the real script against stub Vivado commands (argument errors, stage gating, outdir refusal, ordering, markers). It proves nothing about synthesis.
`tclsh tools/vivado/tests/gate_fixture_test.tcl [OUT-dir ...]` checks the strict-gate scanners against verbatim Vivado 2026.1 log and report lines in `tests/fixtures/vivado_2026_1/` and, optionally, full preserved run directories.

G1 run evaluator (generated-clock campaigns, read-only on a finished run): `bash tools/vivado/evaluate_g1_v2.sh pos|nc OUT DETACHED IDENTITY_ENV` reports
INTEGRITY, COVERAGE (clocked/constrained endpoints), TIMING (setup/hold and, from Other Path Groups, recovery/removal; pre-placement estimates) and
GATE-POSITIVE separately. `timing_groups.py` parses every timing group and cross-checks the summary tables against the Timing Details blocks (fails
closed). It does not change the strict gate, which still does not reject timing violations. Offline tests (compact real fixtures, `PROVENANCE.txt`):
`bash tools/vivado/tests/g1_evaluator/test_g1_evaluator.sh <scratch>`, `test_g1_v1_cases.sh <scratch>`, `mutation_controls.sh <scratch>`.
`gate_fixture_test.tcl` replay assumes the unconstrained baseline (8172/28651); replaying a constrained run there is out of its scope.
