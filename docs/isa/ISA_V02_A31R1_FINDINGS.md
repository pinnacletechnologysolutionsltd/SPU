# ISA-V02-A31-R1 — A31 inverter refusal and result-publication paths

**Status:** read-only source characterization PASS. The ordinary RPLU pipeline path is **POTENTIALLY UNSAFE** at source level; this is **not** a demonstrated simulation or FPGA failure. Normative refusal semantics and any repair **HOLD**. No RTL, VM, test, tool or inventory change.
**Baseline identity:** `dev/next` at `19b35fa821159b2625ae2b06ab6f049d18e09d7e` (clean). Existing VM, assembler and RTL sources are unchanged from public RC2 `b063280` (`b0632806621ed6fe44c9c72f4e0adbd8ee8df776`); analysis tools and tests were added in `dev/next`. Line numbers are at `19b35fa`.
**Method:** signal-flow reading only. Nothing was elaborated, simulated, synthesized or run on a board. `flags_v` is an internal signal; no architectural FLAGS register is inferred from it (see `ISA_V02_SNAP1_FINDINGS.md`). This document does not claim that the inverter's norm check detects every zero divisor of A31; that mathematical audit remains HOLD.

## 1. Signal flow

Terms: *retained output* = a register that keeps its previous value on a refused operation; *refusal signal* = `flags_v`; *result-valid* = `done`, `thimble_valid`, `qr_commit_valid`; *commit telemetry* = the `qr_commit_*` outputs read by the host; *register-file write* = `qrf_wr_en` into the Quadray register file.

1. **Inverter** `hardware/rtl/core/spu13/spu13_fp4_inverter.v`. `flags_v` clears on an accepted `start` (`:110`). Stage B sets `flags_v` and enters `S_EXCEPTION` when the norm is zero (`:162-164`); `S_EXCEPTION` (`:294`) pulses `done` and drops `busy`, so `flags_v` is already high when `done` is visible and stays high until the next `start`. `inv0..3` are written only in stage D2 (`:244-284`) and are not in the reset branch (`:95-99`): on an exception they retain the previous transaction's values. The structured inverter (`spu13_fp4_inverter_structured.v`) resets `inv0..3` to 0 and has the same exception shape (retention afterward). The Artix-7 top defaults `USE_STRUCTURED_INVERTER = 0` (`spu_a7_top.v:56`).
2. **Padé engine** `hardware/rtl/gpu/rplu_thimble_pade.v`. In `S_INVERT`, `inv_done` with `inv_flags_v` sets `flags_v`, pulses `done`, clears `busy` and returns to idle (`:361-367`). The `inv_r*` outputs are not read on that branch, so stale inverter outputs do not reach the final multiply. `result_c0..3` are assigned only in `S_MULTIPLY` (`:389`) and are not in the reset branch (`:236-244`): on an exception they retain the previous success; for the first transaction after reset their value is whatever the register holds, which the RTL does not define. `flags_v` clears at `start` (`:255`).
3. **Ordinary RPLU pipeline** `hardware/rtl/core/spu13/rplu_pipeline.v`. The Padé instance (`:212-242`) exports `.flags_v(pade_flags_v)` (`:225`); `pade_flags_v` (`:111`) has no consumer in the module and the pipeline has no flag output port. On `pade_done` the pipeline latches `phi4_c* <= pade_result_*` and sets `phi4_valid` (`:537-543`), and `thimble_valid = phi4_valid` (`:555`), with no flag check. `phi4_c*` themselves are reset to 0 (`:469-475`), but the value latched on a failed transaction is the Padé engine's retained `result_c*`. Launch gating is `pade_launch = !btu_fifo_empty && !pade_inflight && !pade_busy && !pade_done` (`:459`).
4. **SPU-13 core bridge** `hardware/rtl/core/spu13/spu13_core.v:1333-1341`. On `rplu2_result_valid` (`= rplu2_thimble_valid`, `:2310`) the core sets `qr_commit_valid_r`, `qr_commit_lane_r <= rplu2_result_lane`, `qr_commit_A..D_r <= {32'd0, rplu2_result_c0..3}` and `inst_done_r <= 1`. This branch does **not** assert `qrf_wr_en`: the Quadray register file is not written. The observable effects are the commit telemetry and `inst_done`.
5. **SPI latch** `hardware/rtl/peripherals/io/spu_spi_slave.v:405`. The `0xAE` data latch updates only when `qr_commit_valid` is high.
6. **RPLU2 Padé sidecar** `spu13_rplu2_pade_sidecar.v:449-461`. On `pade_done`: `error <= pade_flags_v` and `qr_commit_valid <= !pade_flags_v`; `qr_commit_A..D` are loaded unconditionally from `result_c*` (stale on failure), so the data lines carry retained values with `valid` low. `qr_commit_valid` and `error` default to 0 every cycle (`:402-403`, one-cycle pulses). A second instruction while `busy` raises `error` (`:444`). The Padé engine sets `flags_v` on the same edge as `done`, so `pade_flags_v` is valid in the cycle the sidecar samples `pade_done`.
7. **RPLU2 live-evaluator sidecar** `spu13_rplu2_sidecar.v` (spin `RPLU2LIVE`, coreless; instantiates `rplu_pipeline` at `:135`). On `thimble_valid` it sets `qr_commit_valid` and loads `qr_commit_A..D` from `thimble_c*` (`:293-300`). Its `error` sources are Quadray incoherence, `rns_error`, `pipeline_stall` and a second instruction while busy (`:268-290`); none is the inverter exception. This is the same exposure as the ordinary pipeline and was not mentioned in the earlier A31-R1 report.
8. **Artix-7 top** `spu_a7_top.v:427-456` selects the sidecar or core commit lines by their valid signals; the SPI slave then latches per item 5.

## 2. Internal stale data versus observable publication

- **Internal retained outputs** (not by themselves a defect): `inv0..3`, Padé `result_c0..3`, and the sidecar's `qr_commit_A..D` data lines on failure.
- **Refusal signal:** `flags_v` is produced by the inverter and propagated by the Padé engine; it is consumed only by the RPLU2 Padé sidecar.
- **Result-valid assertion:** `thimble_valid` (pipeline), `qr_commit_valid_r` and `inst_done_r` (core bridge), `qr_commit_valid` (live sidecar) are asserted after a refused operation on paths 3, 4 and 7. This is the potential contract violation: a valid indication accompanying a retained earlier result.
- **Commit telemetry:** affected on paths 4 and 7. **Register-file writes:** none on any traced path.
- **Second transaction.** On paths 3, 4 and 7 a refused transaction N+1 republishes the result of the last success N as if new; if none has occurred since reset, it publishes the unreset register contents. On path 6 a refused transaction publishes nothing new and the earlier commit stays in the SPI latch; a later success overwrites it. Stale inverter outputs are never reused by the next transaction.
- **Host distinguishability.** On paths 4 and 7 the host sees a fresh commit and `inst_done` with no error indication tied to the inverter. On path 6 the host sees no new commit and an `error` pulse that survives only in sticky debug status (`debug_sidecar_error_seen`, cleared by the next SPI instruction); `0xAE` alone does not reveal the refusal. Host-visible refusal signaling is **UNRESOLVED**.

## 3. Dispositions

| Path | Disposition | Basis |
|---|---|---|
| Inverter output retention (internal) | expected internal behavior | `:244-284`, `:294` |
| Stale `inv0..3` into the Padé multiply | SAFE BY CONSTRUCTION | `rplu_thimble_pade.v:361-367` |
| Ordinary pipeline `phi4`/`thimble_valid` | POTENTIALLY UNSAFE | `rplu_pipeline.v:537-543`, `pade_flags_v` unconsumed |
| Core bridge commit telemetry and `inst_done` | POTENTIALLY UNSAFE | `spu13_core.v:1333-1341` |
| Live-evaluator sidecar commit | POTENTIALLY UNSAFE | `spu13_rplu2_sidecar.v:293-300` |
| RPLU2 Padé sidecar `qr_commit_valid` | SAFE BY CONSTRUCTION | `spu13_rplu2_pade_sidecar.v:454-455` |
| SPI result latch | SAFE BY CONSTRUCTION | `spu_spi_slave.v:405` |
| Host-visible refusal signaling (all paths) | UNRESOLVED | §2 |
| Batch inverter `spu13_batch_inverter.v` | UNRESOLVED (not traced) | per-lane `inv_singular`, poison testbench; no instantiation found outside tests |

## 4. Configuration conditions on the Artix-7

- The ordinary pipeline path (3, 4) exists when the core has `ENABLE_CORE_RPLU_V2 && ENABLE_CORE_RPLU_V2_PIPELINE`: Artix-7 spins `MULTIMEDIA`, `INTELLIGENCE`, `RPLU2` and `FULL` by the D1 spin table (`spu_a7_top.v:113-118`). `RPLU2CORE` and `SU3SHARE` disable the pipeline (config/QR only). The live-evaluator sidecar (7) is the coreless spin `RPLU2LIVE`; the gated Padé sidecar (6) is the coreless spin `RPLU2PADE`. The Colorlight RPLU2 top also enables the pipeline; other tops were not enumerated.
- A zero-norm denominator requires host-written coefficients or a saddle input: the default denominator is the constant 1 (`rplu_thimble_pade.v` `initial` block) and cannot be singular. Padé coefficients are host-writable through the RPLU config path (`spu13_core.v:204-242`). Whether any shipped coefficient set can produce a zero divisor was not evaluated. The Padé testbench constructs one (`p − √15 + uv`).
- All paths assume one synchronous clock per module (A7 `clk_fast`, divided), asynchronous active-low reset on the FSM registers, one-cycle `done`/`valid` pulses, and `flags_v` as a level cleared on `start`. The data registers named in §1 are not reset.

## 5. Existing evidence and missing tests

- `singular_absorber_tb.v` and `spu13_fp4_inverter_tb.v` cover inverter `flags_v`, re-arm and alternation.
- `rplu_thimble_pade_tb.v:224` checks `done && flags_v` for a zero-divisor denominator; it does **not** check `result_c*` preservation or any downstream signal.
- `spu13_rplu2_pade_sidecar_tb.v` asserts that `error` is never raised; the `!pade_flags_v` gating is untested. `rplu_pipeline_tb.v` has no singular or zero-denominator case. No test exercises the core bridge or the live sidecar with a zero-norm denominator.
- `docs/hardware_evidence.md` has no zero-norm, `FLAGS.V` or singular-refusal entry; nothing here is a silicon claim.
- **Smallest directed simulations that would distinguish the outcomes (not run):** (1) engine level: extend `rplu_thimble_pade_tb.v` with a success followed by the zero-divisor case, asserting `done && flags_v` and unchanged `result_c*`; (2) pipeline level: drive `rplu_pipeline` with the zero-divisor denominator through one BTU transaction and observe `thimble_valid`/`thimble_c*` against `u_pade.flags_v`; (3) core level: issue `0x2A` with a zero-divisor denominator and observe `qr_commit_valid_r` and `inst_done_r`; (4) sidecar level: add the zero-divisor case to the Padé sidecar testbench and expect an `error` pulse with no `qr_commit_valid`.

## 6. Remaining blockers and limitations

1. Stale publication on paths 3, 4 and 7 is a source-level reading; it is not reproduced in simulation or on hardware.
2. Host-visible refusal signaling and the contract between `inst_done`, `qr_commit_valid` and arithmetic refusal are undefined.
3. Coverage of the inverter's single-norm check against all A31 zero divisors is an open mathematical audit (HOLD).
4. Unreset `result_c*` registers make the first-failure value undefined in simulation.
5. Limitations: source reading only; no elaboration, simulation, synthesis, timing or board qualification; SPU-4 and non-Artix-7 tops not examined; the O6 inventory is a non-exhaustive census (see `ISA_V02_O6_FINDINGS.md`). Conclusions apply to the identity above.
