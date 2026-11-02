# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Development Ethos

See "Development Ethos" in the imported `AGENTS.md`; it applies here unchanged.

## Directives for Claude

1. **Role Portability:** You may serve as **Spec Author** (drafting architectures and bounded contracts in `spu_strategy/` using [`spu_strategy/contract_template.md`](spu_strategy/contract_template.md)), or as **Halt-and-Flag Implementer** on assigned tasks.
2. **Commands, Not Prose:** When specifying implementations or findings, provide exact shell commands and file diffs rather than conversational narrative.
3. **No Speculative Abstractions:** Do not create wrapper layers, extra helper classes, or unrequested generic infrastructure. Keep modules Lithic (50–150 lines).
4. **Repository Hygiene:** Clean up any temporary test scripts (`tmp_*.v`, `scratch_*.py`) or waveform dumps before declaring a task complete.
5. **Silicon Claims Discipline:** Never state that a feature or fix is "verified in silicon" unless citing the exact section in [`docs/hardware_evidence.md`](docs/hardware_evidence.md).
6. **Shared Worktree:** Other agents edit this same tree. Never `git add -A` / `git add .`; stage explicit paths only, and check `git status` before attributing uncommitted changes to yourself.

## Running Tests

`run_all_tests.py` is the single regression runner (CI runs exactly this). It has three stages, run in order:

1. **Verilog testbenches** — the default **release** set is exactly the tracked benches listed in `tools/release_tests.txt` (the `*_tb.v` / `*tb*.v` / `testbench*.v` files under `hardware/tests/`), each run with `iverilog -g2012` + `vvp`. Before running anything the runner exits 2 if a listed bench is absent or untracked, an eligible tracked bench is missing from the list, or an untracked/ignored `.v`/`.vh`/`.sv` exists under `hardware/`; so a clean and a research-filled checkout select the same tests. A new bench under `hardware/tests/` must be added to the manifest (kept sorted). Benches outside the manifest (untracked `spu_strategy/` and other research benches) are **not** release tests: run them with `SPU_TEST_SET=research`, which runs only those, prints a separate summary (never merged into release totals) and classifies each against `tools/known_failures.txt` (`KNOWN-FAIL`, `NEW-FAIL` — nonzero exit, `RESOLVED` — informational). `TB_FILTER` on its own is legacy triage: repo-wide discovery, manifest not enforced, not release results.
2. **C++** — auto-discovers `*_test.cpp`, builds with `g++ -std=c++17 -Isoftware/common/include`.
3. **Python** — an **explicit list** inside `run_all_tests.py` (`spu_vm_test.py`, `cross_validate.py`, selected `software/tests/test_*.py`). A new Python test in `software/tests/` is *not* part of the gate until it is added there. The Gen-1 CPU frontend simulation (`hardware/tests/cpu_frontend_v02/run.py`) is a separately registered **required** test (a missing script, nonzero exit or timeout is a failure); its bench is named `frontend_check.v` on purpose so the `*tb*.v` patterns do not treat it as a generic-runner bench, and it is not in the manifest.

```bash
python3 run_all_tests.py                          # full release regression (default SPU_TEST_SET=release)
SPU_TEST_SET=research python3 run_all_tests.py    # research-only benches, classified against tools/known_failures.txt
TB_FILTER=spu_depth python3 run_all_tests.py      # legacy triage: only TBs whose filename contains the substring (not release results)
python3 software/tests/test_<name>.py             # one Python test directly
SKIP_TESTS=1 bash tools/verify_repo.sh            # hygiene + citation checks without the regression
```

Testbench conventions the runner depends on:

* Verdict is a **stdout string match**: any `FAIL` → failed, else any `PASS` → passed, else "NO VERDICT" (counted as a failure). A TB must print one.
* Default per-TB timeout is 15 s; slower TBs need an entry in `TEST_TIMEOUTS`. Compile-time defines go in `TEST_DEFINES`; non-default parameter runs go in `PARAM_VARIANTS` (each adds a counted variant run).
* Sources are not listed per TB: the runner gathers every module from a curated directory list and dedups by module name, **first-seen wins in sorted order**. Two files defining the same module name means one is silently dropped — check before adding a same-named module anywhere under `hardware/`.
* TBs `$dumpfile` into `build/` (gitignored); never into the repo root.

Board bitstreams are not covered by simulation. `python3 tools/board_build_check.py [--only TARGET]` rebuilds board targets and compares hashes against `hardware/boards/board_build_manifest.json`. Builds over 60 s must go through `tools/run_detached_job.sh` (AGENTS.md §4.2).

## Architecture Map

* `hardware/rtl/` — synthesizable RTL. `core/spu13/` (13-axis cortex), `core/spu4/` (Sentinel edge node, incl. the customer ABI wrapper `spu4_som_edge_wrapper.v`), `core/shared/`, `math/` (exact surd/rational arithmetic units: GCD, exact quotient, normalize), `gpu/` (rasterizer, depth, scene loader, Padé/RPLU evaluators), `hal/` (VGA/HDMI), `arch/` (`.vh` defines and `.mem` tables — some `.mem` files are generated, see AGENTS.md §3.4).
* `hardware/boards/` — board tops, constraints and build scripts per target (`artix7/` = Wukong A7-100T, the primary silicon board; `tang_primer_25k/` = Gowin probe board). A7 builds: `hardware/boards/artix7/build_a7.sh <part> <spin> [stage]` (usage in the script header); for VGA use the measured `spu_a7_vga_fix.xdc`.
* `hardware/tests/` — testbenches by subsystem (`spu13/`, `spu4/`, `math/`, `peripherals/`, `common/` for behavioral primitive models).
* `software/spu_vm.py` — Python ISA VM, the simulator reference; `software/cross_validate.py` checks it against the C++ reference in `software/common/include/`. Oracles that RTL must match bit-exactly live in `software/tests/` and `software/lib/`.
* `software/spu_host/` — host-side Python client library for talking to boards (installed via `pip install -e .`; see its README).
* `knowledge/` — normative specs (ISA, ROTC tables, lexicon, math foundations). `docs/` — narrative docs, papers (`docs/papers/*.tex`), and the evidence ledger `docs/hardware_evidence.md`.
* `spu_strategy/` — **gitignored** active contracts and tranche plans; check here before starting work, since in-flight tasks are invisible to `git log`.
* `archive/` — superseded implementations; excluded from the regression.

The usual verification chain for an arithmetic or ISA feature is: Python oracle → RTL testbench matching the oracle bit-exactly → (optionally) board build → bench run recorded in `docs/hardware_evidence.md`. Report each layer separately (AGENTS.md §4.4).
