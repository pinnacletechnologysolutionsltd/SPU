# Session handover — 2026-08-13

This session moved the project from release completion into the SPU-4
commercial product track. The recommended strategy is an open architecture
with paid implementation, integration, verification, and training expertise.
SPU-13 remains an experimental research platform developed in parallel.

## 1. Repository state

- Worktree is clean at handoff.
- Published typestate v1.2 remains frozen at tag `v1.2-typestate`.
- Zenodo v1.2 record: <https://zenodo.org/records/21912306>.
- Fresh-clone regression provenance is recorded in commit `1a9c96e`:
  141 discovered Verilog benches, 148 Verilog executions including variants,
  12 C++ tests, all auxiliary suites; total 193 PASS and 0 FAIL.

Latest product-track commits:

| Commit | Change |
|---|---|
| `7a2bf9b` | Distinguish SPU-4 synthesis/P&R resource estimate from silicon proof |
| `9d65c64` | Record T7.0/T7.1 product-direction decisions |
| `f2e743f` | Add `docs/SPU4_PRODUCT_CLAIMS.md` |
| `6d5d7ab` | Add `docs/SPU4_FAULT_REPORTING_CONTRACT.md` and close T7.3 |
| `53bbf2f` | Add `spu_strategy/spu4_open_ip_services_outreach_strategy_2026-08-13.md` |

## 2. T7 decisions

### T7.0 — resource claim: resolved

The approximately 400-LUT figure is a synthesis/P&R estimate including the
UART probe fixture, not a resource count observed in silicon. The exact probe
build was rerun with:

```text
bash build_25k_spu4_probe.sh
```

The generated bitstream SHA-256 is
`9599f5e420f46515d99b57d2b256489440341166941be3bc9992b0b827222664`, matching
the silicon ledger entry in `docs/hardware_evidence.md` §3.2j. Current P&R
closed at 168.58 MHz against a 12 MHz constraint. The silicon claim remains
functional and scoped to the documented probe path.

### T7.1 — product boundary: resolved

SPU-4 is being developed as a reusable FPGA IP block. Tang Primer 25K is the
reference-validation vehicle, not the product. A board kit may follow as a
reference design.

### T7.2 — claim ledger: resolved

`docs/SPU4_PRODUCT_CLAIMS.md` separates RTL, scoped silicon,
synthesis/P&R, and open claims. It excludes cluster integration, SOM/BMU,
cross-vendor guarantees, and unverified universal timing/resource claims.

### T7.3 — fault reporting: resolved

`docs/SPU4_FAULT_REPORTING_CONTRACT.md` defines the base core as deterministic
arithmetic plus bounded telemetry, not comprehensive self-fault detection:

- `busy` and `done` are execution status;
- `henosis_pulse` is a normalization event;
- `dissonance` is the saturating Quadray residual;
- `debug_status` is wrapper status, not a universal fault bitmap;
- the chiral-adder overflow is currently local and not exported by the
  standalone wrapper.

A hardened fault-detection wrapper is a future optional package requiring its
own RTL, oracle, poison, and silicon evidence.

## 3. Outreach strategy

The committed strategy is
`spu_strategy/spu4_open_ip_services_outreach_strategy_2026-08-13.md`.

Recommended positioning:

> Open architecture, paid implementation expertise.

Initial offer: architecture modelling, FPGA porting, integration, verification,
board bring-up, application development, and team training. Public outreach
should begin as an educational pilot campaign:

1. Homepage as the canonical product and evidence source.
2. LinkedIn for engineering and commercial discovery.
3. YouTube for short build/flash/telemetry demonstrations.
4. X as a secondary open-source FPGA channel.

The first application demonstrator should be a narrow SPU-4 Sentinel/SOM path,
while keeping the SOM edge tier clearly marked as incomplete until its upload,
board, synthesis, and silicon path exists.

## 4. Next work

### T7.4 — next active tranche

Define the customer integration package:

- minimal customer-facing wrapper;
- instruction and latency ABI;
- supported target matrix;
- constraints and build commands;
- clean-checkout regression;
- reference bring-up procedure;
- training and handover material.

The product package should test every externally advertised claim on silicon,
but does not require full SPU-13 closure first.

### Parallel background work

- T1: harness honesty sweep;
- T2: count-provenance audit and corrections;
- T3: axiomatic gatekeeper product decision;
- T8: A7 reset post-mortem;
- optional SOM/BMU strict-bar verification;
- SPU-13 experimental hardware and research applications.

The current source of truth for tranche ordering is
`spu_strategy/tranche_plan_2026-08-12.md`.

## 5. Recommended next session

Start T7.4 by selecting the minimal `spu4_standalone_top` customer interface,
then write a one-page integration contract before adding new features.
