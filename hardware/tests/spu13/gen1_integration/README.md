# Gen-1 seven-case RTL integration test

Requires a checkout containing the frozen cpu_v02 portable filelist and its RTL,
Python 3, Icarus Verilog (`iverilog`, `vvp`), and `sha256sum` on PATH.
No FPGA, Vivado, Yosys, external ROM image or device database is needed.

Tested versions: the accepted run used Python 3.14.4 and Icarus Verilog 14.0
devel `s20260301-739-gd95f2401b-dirty`. Other versions have not been qualified;
a run with them is informative but is not covered by that result.

## Running the suite

From the repository root:

```bash
python3 hardware/tests/spu13/gen1_integration/run_gen1_integration.py \
  build/gen1-integration-run \
  hardware/tests/spu13/gen1_integration/fixtures/expected_records.json \
  3268eed2b374c5fdea7e3ac9ca78ac119fad059c8d1d0c98b4f8dfdefa01b832
```

All three arguments are required:

1. `OUT_DIR`: a new output directory. It must not already exist; the runner
   refuses to reuse one. Logs, `sim.vvp` and `results.json` are written there.
2. `EXPECTED_JSON`: the pinned expected-record fixture.
3. `EXPECTED_SHA256`: the fixture's SHA-256. If the fixture differs, the run
   stops with verdict UNKNOWN before compiling.

Before compiling, the runner also checks the 17 shared RTL sources against
`fixtures/source_hashes.sha256`. Any mismatch stops the run with verdict UNKNOWN.
The suite therefore verifies only the frozen Gen-1 RTL; a modified design needs
its own reviewed fixture.

The suite compiles once, runs seven cases and six no-override mutants, and
prints one verdict line. The exit status is 0 only for PASS. Each simulation has
a 900-second subprocess timeout; the whole suite took about 40 seconds in the
accepted run.

Optional development workflow: inside this project's own process, long jobs are
launched through the detached runner, which needs `systemd --user`:

```bash
tools/run_detached_job.sh --output build/gen1-integration-local-job --timeout 3600 --notify-desktop -- python3 hardware/tests/spu13/gen1_integration/run_gen1_integration.py build/gen1-integration-local-run hardware/tests/spu13/gen1_integration/fixtures/expected_records.json 3268eed2b374c5fdea7e3ac9ca78ac119fad059c8d1d0c98b4f8dfdefa01b832
```

The detached runner records status and native output; inspect its terminal
marker afterwards. It is not required for an independent run.

The pinned expected-record fixture is never regenerated during normal execution.
`oracle.py` retains the original seven case definitions and mathematical model;
it imports the tracked software encoder and stream model. For a separately
reviewed regeneration, run `python3 hardware/tests/spu13/gen1_integration/oracle.py
<new-output.json>` and compare against the pinned fixture; never overwrite it
without review. `source_hashes.sha256` retains the original 17 shared RTL hashes.
The existing tracked portable filelist also selects five frozen board RTL files;
its two include directories supply four headers. No source is copied or patched
by the test. A verification evidence package should record hashes for all of these.

Cases: G golden raw-fit; N1 negative coefficient; N2 normalization-to-fit;
O overflow refusal; I invalid denominator; M1 reserved-bit rejection;
M2 unsupported SADD rejection. Acceptance requires seven passes, exact UART
frames, complete event parsing, all negative controls and exit 0. Negative
controls corrupt expected bytes, cross case expectations, omit ROM overrides,
and compare the golden frame with the frozen reference.

Sources derive from the frozen GEN1-ISA-COVERAGE-2 attempt-2 harness and its
CPU-BOARD-4C UART parser. Migration changes only path handling and packaging.
Historical evidence, the 349-check preflight and attempt-1 logs are not included.
The original accepted PASS remains tied to the original harness; this relocated
suite requires its own verification. Hardware material is governed by
`hardware/LICENSE` (CERN-OHL-W-2.0); imported software dependencies retain their
`software/LICENSE` (MIT) terms. Repository-root licensing also remains in force;
no original notices were removed.

This is directed RTL integration simulation, not physical exceptional-path
execution, exhaustive ISA/operand coverage, netlist equivalence, or general
reset/timing qualification. UART fault frames do not encode arithmetic fault
cause; internal simulation traces establish those causes. Publication remains
subject to release review. Generated evidence and caches do not belong here.
