#!/usr/bin/env bash
# One matched Artix-7 P2 route for the D4 reflection comparison.
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <specialized|generic> <evidence-dir>" >&2
    exit 2
fi
candidate="$1"
evidence_dir="$2"
case "$candidate" in
    specialized) generic=0 ;;
    generic) generic=1 ;;
    *) echo "unknown candidate: $candidate" >&2; exit 2 ;;
esac
mkdir -p "$evidence_dir"
source tools/env_openxc7.sh

json="$evidence_dir/design.json"
pnr_json="$evidence_dir/design.pnr.json"
yosys -p "read_verilog hardware/rtl/math/spu_d4_reflection_unit.v; read_verilog hardware/rtl/math/spu_d4_reflection_generic.v; read_verilog hardware/boards/artix7/spu_a7_d4_reflection_bench_top.v; chparam -set GENERIC_REFLECTION $generic spu_a7_d4_reflection_bench_top; synth_xilinx -family xc7 -top spu_a7_d4_reflection_bench_top -json $json" \
    >"$evidence_dir/yosys.log" 2>&1

nextpnr-xilinx \
    --chipdb build/chipdb/xc7a100tfgg676.bin \
    --xdc hardware/boards/artix7/spu_a7_d4_reflection_bench.xdc \
    --json "$json" \
    --write "$pnr_json" \
    --fasm "$evidence_dir/design.fasm" \
    --log "$evidence_dir/nextpnr.log" \
    --freq 50 \
    --seed 1 \
    --timing-allow-fail
