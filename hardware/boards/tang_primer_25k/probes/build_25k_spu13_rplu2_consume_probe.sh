#!/usr/bin/env bash
# build_25k_spu13_rplu2_consume_probe.sh -- Tang 25K RPLU2 table-consumption proof
set -e

mkdir -p build

echo "--- 1. Generate corrected RPLU2 consume-probe flash table ---"
python3 tools/gen_rplu2_tables.py \
    --profile consume_probe \
    --output tools/build/rplu2_consume_probe_tables.bin

echo "--- 2. Yosys synthesis ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_rplu2_consume_probe.ys

echo "--- 3. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/flash_rplu2_read_probe.cst \
    --json build/spu13_rplu2_consume_probe.json \
    --write build/spu13_rplu2_consume_probe_pnr.json \
    --freq 12

echo "--- 4. Package bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_rplu2_consume_probe_pnr.json \
    -o build/tang_primer_25k_spu13_rplu2_consume_probe.fs

echo ""
echo "=== RPLU2 consume probe build complete ==="
echo "Flash image: tools/build/rplu2_consume_probe_tables.bin"
echo "Bitstream:   build/tang_primer_25k_spu13_rplu2_consume_probe.fs"
echo "Program flash:"
echo "  tools/rp2040_flash_pmod.py --port <tty> write tools/build/rplu2_consume_probe_tables.bin --offset 0x110000"
echo "Run probe:"
echo "  tools/probe_tang25k_rplu_flash.py --bitstream build/tang_primer_25k_spu13_rplu2_consume_probe.fs --expected-rplu-loaded 0x95 --expected-rplu-checksum 0x0AA480E7 --expect-rplu2-consume"
