#!/usr/bin/env bash
set -euo pipefail

out_dir="${1:?usage: bench_surd_mul_normalize_a7.sh EXISTING_OUTPUT_DIRECTORY [WIDTH [LANES]]}"
[ -d "$out_dir" ] || { echo "output directory does not exist: $out_dir" >&2; exit 2; }
width="${2:-64}"
lanes="${3:-5}"
source tools/env_openxc7.sh
chipdb=build/chipdb/xc7a100tfgg676.bin
[ -f "$chipdb" ] || { echo "missing chip database: $chipdb" >&2; exit 2; }

prefix="${out_dir}/w${width}_lanes_${lanes}"
yosys -Q -p "read_verilog -sv hardware/rtl/math/surd_smul_unit.v hardware/rtl/math/surd_binary_gcd3.v hardware/rtl/math/surd_exact_quotient.v hardware/rtl/math/surd_normalize_unit.v hardware/boards/artix7/surd_mul_normalize_bench_top.v; chparam -set W ${width} -set LANES ${lanes} surd_mul_normalize_bench_top; hierarchy -check -top surd_mul_normalize_bench_top; proc; opt; select -assert-none t:\$div t:\$mod; synth_xilinx -family xc7 -top surd_mul_normalize_bench_top -json ${prefix}.json; stat -top surd_mul_normalize_bench_top" \
    > "${prefix}.yosys.log" 2>&1
nextpnr-xilinx --chipdb "$chipdb" --xdc hardware/boards/artix7/surd_smul_bench.xdc \
    --json "${prefix}.json" --write "${prefix}.pnr.json" \
    --fasm "${prefix}.fasm" --log "${prefix}.nextpnr.log" \
    --freq 25 --seed 1 > "${prefix}.nextpnr.stdout" 2>&1
echo "COMPLETE: combined multiplier/normalizer W=${width} LANES=${lanes} mapped and routed at 25 MHz target"
