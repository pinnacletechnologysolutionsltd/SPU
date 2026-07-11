# SPU-13 Agent Pointer

This file is intentionally thin. Treat `AGENTS.md` as the source of truth for
current board status, silicon-vs-testbench claims, build commands, and active
architecture notes.

## Current Shape

SPU-13 is a deterministic exact-arithmetic FPGA coprocessor over Q(sqrt3),
A31/M31, and Z[phi]/L_p arithmetic. It has two active core families:

- `hardware/rtl/core/spu13/` — SPU-13 cortex arithmetic, ROTC/IROTC, RPLU2,
  SOM/BMU, Lucas, batch/series sidecars.
- `hardware/rtl/core/spu4/` — SPU-4 Sentinel satellite/edge core.
- `hardware/rtl/core/shared/` — shared ALU, register files, decoders, Davis
  gate, interconnect helpers.

Board tops and synthesis scripts live under `hardware/boards/`; software
oracles, VM, assemblers, and host tools live under `software/`.

## Commands

Run the full regression:

```bash
python3 run_all_tests.py
```

`run_all_tests.py` uses a 15 second Verilog testbench timeout. Use
`TB_FILTER=<name> python3 run_all_tests.py` for focused triage.

## Rules

- No floating point in RTL or RTL-facing oracles.
- Do not hand-edit generated catalogs or `.mem` golden files.
- A claim is "silicon-verified" only when recorded in
  `docs/hardware_evidence.md`.
- Check `AGENTS.md` before making status claims.

## License Split

- `hardware/`: CERN-OHL-W-2.0
- `software/`: MIT
- `docs/`, `knowledge/`: CC0 1.0
