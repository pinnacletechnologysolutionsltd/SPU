#!/usr/bin/env bash
set -euo pipefail
mkdir -p build/spu4_ina226_benchmark
for profile in 0 1; do
    iverilog -g2012 -I hardware/rtl/arch -s spu4_som_edge_interactive_probe_tb \
        -Pspu4_som_edge_interactive_probe_tb.BENCH25="$profile" \
        -o "build/spu4_ina226_benchmark/checked_bench25_$profile.vvp" \
        hardware/tests/spu4/spu4_som_edge_interactive_probe_tb.v \
        hardware/boards/tang_primer_25k/spu4_ina226_bench25_top.v \
        hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v \
        hardware/rtl/core/spu4/spu4_uart_rx_bitsync.v \
        hardware/rtl/core/spu4/spu4_som_edge_wrapper.v \
        hardware/rtl/core/spu4/spu4_som_edge.v \
        hardware/rtl/core/spu4/spu4_som_flash_loader.v \
        hardware/rtl/peripherals/storage/spu_flash_bridge.v
    vvp "build/spu4_ina226_benchmark/checked_bench25_$profile.vvp" \
        > "build/spu4_ina226_benchmark/checked_bench25_$profile.log"
    if rg -q 'FAIL|FATAL' "build/spu4_ina226_benchmark/checked_bench25_$profile.log"; then
        echo "FAIL bench25 profile $profile"; exit 1
    fi
    rg '^50 checks, 50 passed, 0 failed$' "build/spu4_ina226_benchmark/checked_bench25_$profile.log"
done
