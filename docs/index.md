# SPU-13 Synergetic Processing Unit

An experimental FPGA coprocessor for **exact, deterministic geometric
computation** — all arithmetic in rational fields (Q(√3), A₃₁ over the
Mersenne prime M31, Z[φ]/L_p), zero floating-point, zero division, bounded
deterministic latency, bit-exact replay across Python, C++, and RTL.

Pick your door:

## 🧭 New here?

- **[Glossary & conversions](glossary.md)** — every term in plain English,
  angle↔spread and distance↔quadrance tables, and the reading list
  (Wildberger, Fuller, Urner) the ideas come from
- **[Spin catalog](SPIN_CATALOG.md)** — every named bitstream: what it does,
  what board it fits, and its silicon status

## 🔬 For researchers

- **[Current status](CURRENT_STATUS.md)** — board roles, silicon proof level, priorities
- **[Hardware evidence ledger](hardware_evidence.md)** — every claim tied to a command and a result
- **[Hydraulic pump SOM truth gate](HYDRAULIC_PUMP_SOM_CASE_STUDY.md)** —
  predeclared real-data folds, exact features, baselines, and the recorded
  negative result
- **Papers (preprints in preparation):** central architecture, RPLU v2 jet algebra,
  Lucas phinary MAC, SU(3) coprocessor — LaTeX sources in `docs/`, built PDFs
  in CI artifacts
- **[Identity and claim boundaries](SPU13_IDENTITY_AND_BOUNDARIES.md)** — what this
  architecture is and deliberately is not
- **[Mathematical foundations](../knowledge/MATHEMATICAL_FOUNDATIONS.md)** and the
  **[ISA reference](../knowledge/isa_reference.md)**

## 🔧 For builders

- **[Build and bring-up guide](build_and_bringup_guide.md)** — commands, wiring, board procedures
- **[SOM-SIDECAR evaluator quickstart](SOM_SIDECAR_QUICKSTART.md)** — Tang/RP2350 wiring, firmware, bitstream, and the 150-sample proof
- **[LUCAS evaluator quickstart](LUCAS_QUICKSTART.md)** — Wukong/RP2350 wiring and the exact-integer versus float64 replay
- **[Toolchain setup](toolchain_setup.md)** — OSS CAD Suite + OpenXC7; no vendor IDE
- **[Southbridge SPI protocol](SOUTHBRIDGE_SPI_PROTOCOL.md)** — the RP2350↔FPGA control plane
- **[Board scaling strategy](fpga_board_scaling_strategy.md)** — Tang 25K → Artix-7 → ECP5 → Kintex ladder
- Bench adapter board and INA226 metrics harness: `hardware/pcb/bench_adapter/`,
  `tools/bench_metrics/` in the repository

## 🤝 For contributors

- `AGENTS.md` (repo root) — living source of truth for test/silicon status
- `CONTRIBUTING.md` — DCO sign-off required
- Run everything: `python3 run_all_tests.py` — 100% pass is the merge gate
- Licensing: see the repository `LICENSING.md` map; hardware
  CERN-OHL-W-2.0 · software MIT · docs/knowledge CC0 1.0

---

*The architecture prohibits floating-point, division, and branches in hot
paths. Timing deviations are design flaws, not FIFO fodder. Every testbench
prints PASS or FAIL.*
