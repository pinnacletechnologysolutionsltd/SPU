#!/usr/bin/env bash
# Same-device Artix-7 mapping and place/route for 1/2/5 multiplier lanes.
set -euo pipefail

out_dir="${1:?usage: bench_surd_smul_a7.sh EXISTING_OUTPUT_DIRECTORY [WIDTH ...]}"
[ -d "$out_dir" ] || { echo "output directory does not exist: $out_dir" >&2; exit 2; }
shift
if [ "$#" -eq 0 ]; then widths=(16); else widths=("$@"); fi
source tools/env_openxc7.sh
chipdb=build/chipdb/xc7a100tfgg676.bin
[ -f "$chipdb" ] || { echo "missing chip database: $chipdb" >&2; exit 2; }

for width in "${widths[@]}"; do
    for lanes in 1 2 5; do
        prefix="${out_dir}/w${width}_lanes_${lanes}"
        echo "SYNTH lanes=$lanes W=$width"
        yosys -Q -p "read_verilog -sv hardware/rtl/math/surd_smul_unit.v hardware/boards/artix7/surd_smul_bench_top.v; chparam -set W $width -set LANES $lanes surd_smul_bench_top; hierarchy -check -top surd_smul_bench_top; synth_xilinx -family xc7 -top surd_smul_bench_top -json ${prefix}.json; stat -top surd_smul_bench_top" \
            > "${prefix}.yosys.log" 2>&1
        echo "PNR lanes=$lanes W=$width target=25MHz"
        nextpnr-xilinx --chipdb "$chipdb" --xdc hardware/boards/artix7/surd_smul_bench.xdc \
            --json "${prefix}.json" --write "${prefix}.pnr.json" \
            --fasm "${prefix}.fasm" \
            --log "${prefix}.nextpnr.log" \
            --freq 25 --seed 1 > "${prefix}.nextpnr.stdout" 2>&1
    done
done
echo "COMPLETE: all requested widths and lane variants mapped and routed"
