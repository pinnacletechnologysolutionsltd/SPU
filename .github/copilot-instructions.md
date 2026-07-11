# SPU-13 Copilot Pointer

Use `AGENTS.md` for current project status, board evidence, and commands. This
file only records stable navigation hints so it does not become a second source
of truth.

## Layout

- `hardware/rtl/core/shared/` — shared RTL: ALU, register files, decoder,
  Davis gate, interconnect helpers.
- `hardware/rtl/core/spu13/` — SPU-13 cortex, ROTC/IROTC, RPLU2, SOM/BMU,
  Lucas, batch/series sidecars.
- `hardware/rtl/core/spu4/` — SPU-4 Sentinel.
- `hardware/boards/` — board tops, constraints, synthesis scripts.
- `hardware/tests/` — Verilog testbenches.
- `software/` — VM, assemblers, oracles, host tooling.
- `docs/`, `knowledge/` — design guides, evidence, specs, lexicon.

## Test Command

```bash
python3 run_all_tests.py
```

The runner discovers Verilog, C++, and selected Python/oracle tests. Verilog
testbenches must print `PASS` or `FAIL` and finish; the runner timeout is 15s.

## Discipline

- Exact arithmetic only for RTL and RTL-facing oracles: no float, no
  transcendental approximation.
- Do not edit generated catalogs or golden `.mem` files by hand.
- "Silicon-verified" means the bench run is recorded in
  `docs/hardware_evidence.md`; otherwise say testbench-verified, built,
  unmeasured, or pending.

## License Split

- Hardware and board files: CERN-OHL-W-2.0.
- Software, VM, firmware, tools: MIT.
- Docs and knowledge notes: CC0 1.0.
