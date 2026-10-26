#!/usr/bin/env bash
# Build the one authorized completion-arm observation-only diagnostic variant.
set -euo pipefail

[ "$#" -eq 1 ] || { echo "usage: $0 EVIDENCE_DIR" >&2; exit 2; }
evidence_dir=$(realpath -m -- "$1")
repo_root=$(git rev-parse --show-toplevel)
case "$evidence_dir" in
    "$repo_root"/build/*) ;;
    *) echo "evidence directory must be below $repo_root/build" >&2; exit 2;;
esac

diag_dir="$evidence_dir/diagnostic_build"
[ ! -e "$diag_dir" ] || { echo "refusing to overwrite $diag_dir" >&2; exit 1; }
mkdir -p "$diag_dir"

sources="hardware/boards/tang_primer_25k/spu4_ina226_bench25_top.v \
hardware/boards/tang_primer_25k/spu13_tang25k_spu4_som_edge_interactive_probe.v \
hardware/rtl/core/spu4/spu4_uart_rx_bitsync.v \
hardware/rtl/core/spu4/spu4_som_edge_wrapper.v \
hardware/rtl/core/spu4/spu4_som_edge.v \
hardware/rtl/core/spu4/spu4_som_flash_loader.v \
hardware/rtl/peripherals/storage/spu_flash_bridge.v"

passes="synth_gowin -family gw5a -top spu4_ina226_bench25_top -run begin:map_cells; \
techmap -map +/gowin/cells_map.v; opt_lut_ins -tech gowin; \
hilomap -singleton -hicell VCC V -locell GND G; clean; hierarchy -check; \
check -noinit; blackbox =A:whitebox"

# Default-disabled instrumentation must optimize back to B's exact netlist.
yosys -Q -q -l "$diag_dir/baseline_check_synth.log" -p "
read_verilog -lib +/gowin/cells_xtra_gw5a.v
read_verilog -sv -I hardware/rtl/arch $sources
hierarchy -top spu4_ina226_bench25_top
$passes
write_json $diag_dir/baseline_check.json"
cmp build/spu4_ina226_benchmark/bench25_completion_arm/probe.json \
    "$diag_dir/baseline_check.json"

yosys -Q -q -l "$diag_dir/synth.log" -p "
read_verilog -lib +/gowin/cells_xtra_gw5a.v
read_verilog -sv -I hardware/rtl/arch $sources
hierarchy -chparam DIAGNOSTIC 1 -top spu4_ina226_bench25_top
$passes
write_json $diag_dir/probe.json"

nextpnr-himbaechel --device GW5A-LV25MG121NES --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json "$diag_dir/probe.json" --write "$diag_dir/probe_pnr.json" \
    --log "$diag_dir/pnr.log" --report "$diag_dir/timing.json" \
    --detailed-timing-report --pre-pack tools/spu4_bench25_clocks.py --freq 50

gowin_pack -d GW5A-25A --sspi_as_gpio -o "$diag_dir/probe.fs" \
    "$diag_dir/probe_pnr.json"
sha256sum "$diag_dir/probe.fs" "$diag_dir/probe.json" \
    "$diag_dir/baseline_check.json"
