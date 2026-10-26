# ISA-V02-A31-R2 — Directed refusal-path verification (stale result publication)

**Status:** directed simulation PASS; **stale result publication after an A31 inversion refusal is reproduced in simulation** in the ordinary RPLU pipeline and in the SPU-13 core bridge. Hardware qualification and any repair **HOLD**. No production RTL, VM, opcode, algorithm or tool change; `inst_done` is not redefined; the Padé result registers are not reset.
**Source identity:** `dev/next` at `7d3e2e1beb492f95aa003770fc040ec6beb767ac` (derived from public RC2 `b063280`; existing VM, assembler and RTL sources unchanged from it; analysis tools, tests and documentation added in `dev/next`). Preserved evidence is added by the commit that contains this file (`git log -1 -- docs/isa/ISA_V02_A31R2_FINDINGS.md`).
**Simulator:** Icarus Verilog 11.0 (stable). Four-state simulation; uninitialised registers read `x`.
**These are simulation results, not board measurements.** They apply to the tested configurations and one zero-divisor witness.

## 1. Preserved evidence

`hardware/tests/spu13/a31_r2/`:

| File | Role |
|---|---|
| `a31r2_pipeline_probe.v` | `rplu_pipeline` alone (engine-level and pipeline-level observation) |
| `a31r2_core_probe.v` | `spu13_core` with `ENABLE_CORE_RPLU_V2` and the pipeline (core bridge) |
| `a31r2_sidecar_probe.v` | `spu13_rplu2_pade_sidecar` |
| `a31r2_spi_probe.v` | sidecar plus `spu_spi_slave` (SPI readback) |
| `run_a31_r2.py` | builds each variant in a temporary directory, runs it, compares normalized output (timestamps removed) with `expected/*.txt`; reports mismatches, never rewrites them |
| `expected/*.txt` | 11 preserved terminal outputs |

The probe file names deliberately avoid the substring `tb`, so `run_all_tests.py` (patterns `*_tb.v`, `*tb*.v`, `testbench*.v`) does not auto-discover them; they are **not** part of the regression gate. Reproduce:

```bash
python3 -I hardware/tests/spu13/a31_r2/run_a31_r2.py            # 11 variants, about 5 seconds
python3 -I hardware/tests/spu13/a31_r2/run_a31_r2.py --skip-spi
```

Expected: `RESULT: PASS` and `PASS` for `pipe_ref`, `pipe_ref_first`, `pipe_str`, `pipe_str_first`, `core_ref`, `core_ref_first`, `core_str`, `side_ref`, `side_ref_first`, `side_str`, `spi`. Variant names: `ref`/`str` = `USE_STRUCTURED_INVERTER` 0/1; `_first` = zero-divisor transaction first after reset (`FIRST_FAIL=1`). The core variant with the structured inverter and failure-first, and the sidecar likewise, were not run.

**Provenance.** The probes are copies of the scratch testbenches used for the original A31-R2 run, derived from `rplu_pipeline_tb.v`, `spu13_core_rplu2_cfg_tb.v`, `spu13_rplu2_pade_sidecar_tb.v` and `spu13_spi_rplu2_pade_tb.v`. Original scratch hashes (SHA-256): `a31r2_pipe_tb.v` `fb4a68167fb3fcea0bf1179d14ecf5eda4ab09fc467e6b93e1696518e40a46b3`; `a31r2_core_tb.v` `d996cf465a91b4a62440b3f94fa85affbf3a1532859cd14442b6ff4c641c422b`; `a31r2_side_tb.v` `b0d61e5c514dc0a6ab97e146f6c94c3054b4c5985c3f9ad4bb9ec9309596c45f`; `a31r2_spi_tb.v` `5d2fd4eddddccb5a3f2517577c48f6d2eb3501f4eeef51bb15d744d82a9c8a25`. Preserved hashes: `a31r2_pipeline_probe.v` `b3eb4b609a9c704c8af1f691a5132add1a15541a767275b7ba5c08cf60a6228b`; `a31r2_core_probe.v` `91a818a9732c7f84a6ec6a68646cca051bd7c8e2c9071e3187d14dd068d9d55e`; `a31r2_sidecar_probe.v` `6144eaffaba79feb3c43bfebf2611c614eed9541ab1b07ec6ebb824ff04e5a73`; `a31r2_spi_probe.v` `3d57e680d55f0ef051e9b1beca843efe3872fd52129a475e08e002be614157b2`; `run_a31_r2.py` `d1b016be1665b949f64a6fe3004da0cdfd2719d8cff050457af1b12f56d4ee25`. Changes from the originals: module and file names, a four-line header comment, and transaction labels shortened to fit the 32-character task argument (the originals truncated some banners). No observed signal or stimulus changed. **Verification:** the preserved probes were run against the unchanged RTL and their `EV`, `QRREAD` and `STATUS` lines (timestamps removed) are identical to the original scratch logs in all 11 variants; there were no discrepancies. The unmodified `rplu_pipeline_tb` and `spu13_core_rplu2_cfg_tb` pass under the same include-path setup. The runner was also checked to fail when an expected line is altered (and the file restored).

## 2. Stimulus

All variants use the zero-divisor witness `p − √15 + uv` (denominator constant coefficient `2CEE24B2, 0, 0, 1`, higher denominator coefficients 0), as in `rplu_thimble_pade_tb.v`. Sequence: **A** success (default denominator 1; core and sidecar numerator constant 2) → **B** zero-divisor denominator → **C** recovery (denominator restored to 1). The `_first` variants run **B** first after reset. Pipeline probe: `som_start` pulses. Core and sidecar probes: opcode `0x2A` as a one-cycle `inst_valid` strobe (`QR` destination lane 4). SPI probe: config chords and `0xB1` instruction over SPI, then `0xAC` status and `0xAE` readback.

## 3. Observed results (transaction B)

| Level | Observed | Verdict |
|---|---|---|
| Padé engine | `done` with `flags_v = 1`; `result_c*` unchanged from A | refusal signalled; previous result retained |
| Ordinary pipeline (`rplu_pipeline`) | `thimble_valid` pulses with A's result `(1,0,0,0)` while `pade_flags_v = 1`; both inverter variants | **stale publication reproduced** |
| Ordinary pipeline, B first after reset | `thimble_valid` pulses with `xxxxxxxx` in all four limbs | **undefined data published as valid** (simulation `x`) |
| Core bridge (`spu13_core`) | `qr_commit_valid` (lane 4) with A = 2 (A's result) and an `inst_done` pulse, with the same shape as success A | **reproduced** (reference and structured inverter) |
| Core bridge, B first after reset | `qr_commit_valid` with `A = 00000000xxxxxxxx` (and `B..D` the same) and `inst_done` | **reproduced**; value undefined in simulation |
| RPLU2 Padé sidecar | one `error` pulse; **no** `qr_commit_valid` | refusal gated as source-predicted |
| Sidecar, B first | `error` pulse, no commit (engine `result_c*` is `x`) | gated |
| Recovery C | normal result, no refusal | pass in the tested sequence |
| SPI readback (sidecar probe wiring) | after B, `0xAC` status bytes equal those after A (`7f 2a 13 04`) and `0xAE` returns `valid=01 lane=04 A=2`, the same as after A; a `sidecar_error` pulse occurred | **host observability gap**: neither read reveals the refusal |

## 4. Interpretation and limits

- **Telemetry, not register state.** The audited core bridge does not assert `qrf_wr_en` on this path (`spu13_core.v:1333-1341`); the confirmed problem is false result publication through the completion and commit-telemetry interface, not demonstrated corruption of the Quadray register file.
- **Result-valid versus completion versus refusal.** The failing transaction raises valid indications (`thimble_valid`, `qr_commit_valid`) together with `inst_done` in the pipeline and core paths. A refusal may legitimately complete; the defect is asserting result-valid and presenting a retained earlier result (or `x`) as a fresh commit. This document does not redefine `inst_done` or choose a protocol.
- **Absence of a fresh commit is not a refusal indication.** On the gated sidecar the host sees no new commit and the earlier commit remains readable through `0xAE`; the `error` pulse is one cycle. In the existing SPI probe wiring the status reads are unchanged. In the Artix-7 top the error also feeds a sticky debug bit (`debug_sidecar_error_seen`, cleared by the next SPI instruction); that wiring was not simulated here.
- **Source-predicted, not simulation-qualified:** the live-evaluator sidecar (`spu13_rplu2_sidecar.v`, spin `RPLU2LIVE`) commits on `thimble_valid` and shares the ordinary pipeline's exposure; it was not simulated. The SPI latch behavior on the core path is inferred from `spu_spi_slave.v:405` and the observed core outputs.
- **Limits:** four-state simulation (the first-failure value is `x` here; FPGA power-up is not asserted); one zero-divisor witness; Icarus 11.0 only; no synthesis, timing or board run; the inverter's norm check is not claimed to detect every zero divisor of A31; the O6 inventory is a non-exhaustive census.

## 5. Unresolved

1. A refusal contract: what a host must be able to observe for a failed transaction (completion, result-valid, error). Proposed direction (not authorized): carry an explicit per-transaction status, possibly with a transaction identifier or completion counter.
2. The meaning of `inst_done` for arithmetic refusal (tied to the H0 transport contract; see `ISA_V02_STATE1_FINDINGS.md`).
3. Repair of the pipeline, core bridge and live-evaluator paths, and any reset of the Padé result registers, are not authorized; resetting those registers would not by itself prevent invalid results from being committed.
