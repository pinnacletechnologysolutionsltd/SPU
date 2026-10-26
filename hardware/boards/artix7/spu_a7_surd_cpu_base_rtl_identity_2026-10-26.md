# Base CPU RTL identity after the `abs_bitlen` Vivado repair

Recorded at integration, 2026-10-26. Identity only; this is not timing, routing or silicon evidence.

* Repair: `fpga_chain_arith.vh` `abs_bitlen` early-exit loop (`i = -1`) replaced by a fixed-bound
  scan (commit `47f60b6` in `spu-development-baseline`). Directed test: `hardware/tests/spu13/fpga_chain_abs_bitlen_tb.v`.
* `hardware/rtl` git tree: `3d3071e44da40a0d2019247f9771e97763f062d1` (identical in baseline `945160c`
  and in this integration branch; no RTL differs between them).
* `fpga_chain_arith.vh` blob: `d1c7af48c54239392cf1149ac963c3376a1031fe`
  (pre-repair blob `fcf6e1e3857ac34d7cdbed560f486b93fa403208`, baseline `39f319e`).
* The routed Base CPU result belongs to `hardware/rtl` tree `3d3071e` and XDC `spu_a7_surd_cpu_base.xdc`
  as of `945160c`; any change to either invalidates that association.
