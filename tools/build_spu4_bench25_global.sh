#!/usr/bin/env bash
# One authorised global-clock distribution attempt; preserve prior failed route.
set -euo pipefail
test ! -e build/spu4_ina226_benchmark/bench25_global
mkdir -p build/spu4_ina226_benchmark/bench25_global
yosys -Q -q -l build/spu4_ina226_benchmark/bench25_global/synth.log -p '
read_verilog -lib +/gowin/cells_xtra_gw5a.v
read_verilog -sv -I hardware/rtl/arch hardware/boards/tang_primer_25k/spu4_ina226_bench25_top.v hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v hardware/rtl/core/spu4/spu4_uart_rx_bitsync.v hardware/rtl/core/spu4/spu4_som_edge_wrapper.v hardware/rtl/core/spu4/spu4_som_edge.v hardware/rtl/core/spu4/spu4_som_flash_loader.v hardware/rtl/peripherals/storage/spu_flash_bridge.v
hierarchy -top spu4_ina226_bench25_top
synth_gowin -family gw5a -top spu4_ina226_bench25_top -run begin:map_cells
techmap -map +/gowin/cells_map.v
opt_lut_ins -tech gowin
hilomap -singleton -hicell VCC V -locell GND G
clean
hierarchy -check
check -noinit
blackbox =A:whitebox
write_json build/spu4_ina226_benchmark/bench25_global/probe.json
'
nextpnr-himbaechel --device GW5A-LV25MG121NES --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu4_ina226_benchmark/bench25_global/probe.json \
    --write build/spu4_ina226_benchmark/bench25_global/probe_pnr.json \
    --log build/spu4_ina226_benchmark/bench25_global/pnr.log \
    --report build/spu4_ina226_benchmark/bench25_global/timing.json \
    --detailed-timing-report \
    --pre-pack tools/spu4_bench25_clocks.py --freq 50
