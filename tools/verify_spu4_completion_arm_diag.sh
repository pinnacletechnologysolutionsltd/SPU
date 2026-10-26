#!/usr/bin/env bash
# Validate the single completion-arm diagnostic derivative before hardware use.
set -euo pipefail

[ "$#" -eq 1 ] || { echo "usage: $0 EVIDENCE_DIR" >&2; exit 2; }
evidence_dir=$(realpath -m -- "$1")
[ -d "$evidence_dir" ] || { echo "missing evidence directory" >&2; exit 2; }

git diff -- \
    hardware/rtl/core/spu4/spu4_som_edge.v \
    hardware/rtl/core/spu4/spu4_som_edge_wrapper.v \
    hardware/boards/tang_primer_25k/spu4_ina226_bench25_top.v \
    hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v \
    hardware/tests/spu4/spu4_som_edge_interactive_probe_tb.v \
    tools/build_spu4_completion_arm_diag.sh \
    tools/verify_spu4_completion_arm_diag.sh > "$evidence_dir/source.diff"

iverilog -g2012 \
    -Pspu4_som_edge_interactive_probe_tb.DIAGNOSTIC=1 \
    -Pspu4_som_edge_interactive_probe_tb.FROZEN_CASE=1 \
    -s spu4_som_edge_interactive_probe_tb -o "$evidence_dir/diag_sim.vvp" \
    hardware/rtl/core/spu4/spu4_som_edge.v \
    hardware/rtl/core/spu4/spu4_som_flash_loader.v \
    hardware/rtl/core/spu4/spu4_som_edge_wrapper.v \
    hardware/rtl/core/spu4/spu4_uart_rx_bitsync.v \
    hardware/rtl/peripherals/storage/spu_flash_bridge.v \
    hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v \
    hardware/boards/tang_primer_25k/spu4_ina226_bench25_top.v \
    hardware/tests/spu4/spu4_som_edge_interactive_probe_tb.v
vvp "$evidence_dir/diag_sim.vvp" | tee "$evidence_dir/diag_sim.log"

bash tools/build_spu4_completion_arm_diag.sh "$evidence_dir"
bash tools/verify_repo.sh | tee "$evidence_dir/repo_gate.log"
