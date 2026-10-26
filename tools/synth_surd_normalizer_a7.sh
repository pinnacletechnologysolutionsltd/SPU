#!/usr/bin/env bash
set -euo pipefail

out_dir="${1:?usage: bash tools/synth_surd_normalizer_a7.sh EXISTING_OUTPUT_DIRECTORY [WIDTH ...]}"
[ -d "$out_dir" ] || { echo "output directory does not exist: $out_dir" >&2; exit 2; }
shift
if [ "$#" -eq 0 ]; then widths=(16 32 64); else widths=("$@"); fi
source tools/env_openxc7.sh

for width in "${widths[@]}"; do
    json="${out_dir}/w${width}.json"
    yosys -Q -p "read_verilog -sv hardware/rtl/math/surd_binary_gcd3.v hardware/rtl/math/surd_exact_quotient.v hardware/rtl/math/surd_normalize_unit.v; chparam -set W $width surd_normalize_unit; hierarchy -check -top surd_normalize_unit; proc; opt; select -assert-none t:\$div t:\$mod; synth_xilinx -family xc7 -top surd_normalize_unit -json $json; stat -top surd_normalize_unit" \
        > "${out_dir}/w${width}.yosys.log" 2>&1
    echo "PASS W=$width XC7 synthesis: ${json}"
done
echo "COMPLETE: exact normalizer XC7 synthesis widths ${widths[*]}"
