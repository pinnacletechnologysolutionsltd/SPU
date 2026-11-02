# Gen-1 Wukong v0.2 CPU frontend regression

This test instantiates the frozen `cpu_fetch_1b` directly and supplies a
deterministic mock execution endpoint. It checks instruction words and PC at
each issue, boot and issue stalls, immediate and delayed retire, per-read result
capture, final PC 14 and stable HALT, reset during issue and after completion,
and an unexpected retirement causing a sticky FAULT followed by reset. Checks
use case equality where data may contain unknowns. A bounded watchdog catches
missing progress. Expected words are explicit constants in `frontend_check.v`, independent
of the DUT ROM; they match the recorded `rom_check_int4.txt` evidence.

The checked 14 words are six SLI loads (slots 0–5), SLD, SMUL, then six SRD
reads (slots 0–5). The silicon program's recorded mathematical result is
`(13 + 4√3)/9`, but **this is not an arithmetic test**: the mock supplies
distinct synthetic read data. It does not instantiate `cpu_integrate_1_top`,
the supervisor, core, board wrapper or UART; it does not establish reset CDC,
processor arithmetic, timing, synthesis, SPI, or physical FPGA behavior.

## Source identity

`sources.f` names the frozen frontend and testbench explicitly, relative to the
repository root. The frontend SHA-256 is
`d1f1cb408ba59f02b3faf8256d491b54b4661faeb5c536cdf658be34fe9b7780`, as in
`hardware/boards/artix7/wukong_v3/cpu_v02/SOURCE_MANIFEST.md`. The original
synthesis `filelists/candidate_original.f` lists `experiment/cpu-integrate-4/frontend.v`;
the manifest maps that origin path to the committed frontend. The original
filelist is provenance, not the runnable simulation filelist. The runner checks
the frozen frontend hash before compiling; it does not depend on the historical
clone, untracked strategy files or any pre-existing temporary files.

## Run

From the repository root, with Python 3 and Icarus Verilog (`iverilog`, `vvp`):

```bash
python3 hardware/tests/cpu_frontend_v02/run.py --output build/cpu-frontend-test-1/<new-run>
```

The output directory must not exist. The normal simulation compiles using
`iverilog -g2012 -s tb -f hardware/tests/cpu_frontend_v02/sources.f` with an
explicit output image. The runner saves compilation and simulation transcripts
and a summary there. Three controls create temporary mutated copies of the
frontend, leaving frozen RTL untouched: alter ROM word 2, skip a PC, and halt
one instruction early. Each must compile and fail at its named assertion;
compile failures, unrelated assertions and timeouts do not count as detection.
The testbench file is deliberately not named `*tb*.v`, so repository-wide bench discovery does not mistake this self-driven test for a generic-runner bench. Its top module is still `tb` (`-s tb`). The test is registered separately as required in `run_all_tests.py`, which retains its transcripts under `build/`.
