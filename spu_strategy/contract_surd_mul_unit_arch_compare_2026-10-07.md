# Surd multiply unit architecture comparison

## Scope

Implement a standalone, parameterized exact multiply unit for `Q(√3)` with one, two, or five integer multiplier lanes. Compare identical inputs and semantics. Do not add a register bank, change S0, promote cancellation, or combine arithmetic with normalization.

The result is `(a*c+3*b*e, a*e+b*c, d*f)`. Keep exact products in wide registers. Commit only when all three values fit the W-bit destination representation. On raw overflow, hold the destination, present the exact wide tuple to a separate normalization handshake, and commit only if the returned normalized tuple fits. Otherwise preserve destination and assert overflow. Invalid zero denominators are rejected before operation; they are not fallback requests.

## Commands

1. `iverilog -g2012 -s surd_mul_arch_tb -o build/spu_surd_register/mul_arch_20261007/surd_mul_arch_tb.vvp hardware/rtl/math/surd_smul_unit.v hardware/tests/math/surd_mul_arch_tb.v`
2. `vvp build/spu_surd_register/mul_arch_20261007/surd_mul_arch_tb.vvp`
3. `yosys -Q -p 'read_verilog -sv hardware/rtl/math/surd_smul_unit.v; chparam -set W 16 -set LANES 1 surd_smul_unit; hierarchy -top surd_smul_unit; synth -top surd_smul_unit; stat'`
4. Repeat command 3 with `LANES 2` and `LANES 5`; preserve logs and compare operator/logic counts. These are generic synthesis statistics, not board timing or FPGA resource evidence.
5. Run mandatory repository gates: `bash tools/verify_repo.sh`, `TB_FILTER=surd_register python3 run_all_tests.py`, the §4 ROTC/IROTC and math oracle commands, and `A7_FREQ=25 bash hardware/boards/artix7/build_a7.sh 100t rplu2pade all`.

The short simulation and generic Yosys runs may execute in foreground only if expected under 60 seconds. For longer jobs use `tools/run_detached_job.sh` with a new `build/` output directory, desktop notification, and owner-authorized frozen maximum attempts, per-attempt timeout, and cumulative budget. Do not relaunch or extend a frozen campaign without renewed authorization.

## Acceptance

- All lane counts produce identical exact wide tuples and status/commit behavior for the same vectors.
- Latency/II are measured from RTL handshakes, not inferred from multiplier count.
- Resource comparisons come from the same Yosys flow and parameters. Report multiplication operators before mapping and mapped cells separately if available.
- Simulation covers fitting products, raw overflow rescued by a supplied normalized result, unrescued overflow, destination preservation, and zero-denominator rejection.
- No speed or FPGA resource claim is made from the architectural estimate or generic synthesis alone.
