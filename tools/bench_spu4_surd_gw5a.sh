#!/usr/bin/env bash
set -euo pipefail

out_dir="${1:?usage: bench_spu4_surd_gw5a.sh EXISTING_OUTPUT_DIRECTORY [WIDTH [LANES]]}"
[ -d "$out_dir" ] || { echo "output directory does not exist: $out_dir" >&2; exit 2; }
width="${2:-16}"
lanes="${3:-1}"
device="GW5A-LV25MG121NES"
family="GW5A-25A"
prefix="${out_dir}/w${width}_lanes_${lanes}"

yosys -Q -p "read_verilog -lib +/gowin/cells_xtra_gw5a.v; read_verilog -sv hardware/rtl/math/surd_smul_unit.v hardware/rtl/math/surd_binary_gcd3.v hardware/rtl/math/surd_exact_quotient.v hardware/rtl/math/surd_normalize_unit.v hardware/boards/tang_primer_25k/spu4_surd_portability_bench_top.v; synth_gowin -family gw5a -top spu4_surd_portability_bench_top -run begin:map_cells -json ${prefix}.json; techmap -map +/gowin/cells_map.v; opt_lut_ins -tech gowin; hilomap -singleton -hicell VCC V -locell GND G; clean; hierarchy -check; check -noinit; blackbox =A:whitebox; write_json ${prefix}.json" \
    > "${prefix}.yosys.log" 2>&1
nextpnr-himbaechel --device "$device" --vopt "family=$family" \
    --vopt sspi_as_gpio --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json "${prefix}.json" --write "${prefix}.pnr.json" \
    --freq 12 > "${prefix}.nextpnr.log" 2>&1
echo "COMPLETE: GW5A Surd W=${width} LANES=${lanes} mapped and routed at 12 MHz target"
