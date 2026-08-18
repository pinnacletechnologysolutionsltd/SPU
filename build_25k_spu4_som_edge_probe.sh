#!/usr/bin/env bash
# build_25k_spu4_som_edge_probe.sh -- Tang 25K silicon probe for the SPU-4
# edge SOM product, spu4_som_edge_wrapper (edge-node programme step 4,
# docs/SESSION_HANDOVER_2026-08-16.md 9).
#
# Before flashing this bitstream, the fixture it expects must be on the
# PMOD J4 SPI flash chip at FLASH_SPU4_SOM_BASE (0x120000) -- the same chip
# already proven for RPLU2's boot tables at 0x110000, no new wiring:
#   python3 tools/gen_spu4_som_boot_image.py --profile oracle_fixture \
#       --output tools/build/spu4_som_boot_image.bin
#   tools/rp2040_flash_pmod.py --port <tty> id     # must report JEDEC EF4018 first
#   tools/rp2040_flash_pmod.py --port <tty> write tools/build/spu4_som_boot_image.bin \
#       --offset 0x120000
#
# Golden UART line at 115200 baud (see spu13_tang25k_spu4_som_edge_probe.v's
# header for the full field reference):
#   SOM:P N=1 Q=00001900 S=06 L=xxx I=1020
# L is the MEASURED latency in clocks. The query is deliberately the
# oracle fixture's feature-3-dependent case -- see the probe's header for
# why an exact-match query could not have caught the bug this proves fixed.
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-4 SOM edge probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu4_som_edge_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu4_som_edge_probe.json \
    --write build/spu4_som_edge_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu4_som_edge_probe_pnr.json \
    -o build/tang_primer_25k_spu4_som_edge_probe.fs

echo ""
echo "=== SPU-4 SOM Edge Probe Build Complete ==="
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_som_edge_probe.fs"
echo "Expect:    SOM:P N=1 Q=00001900 S=06 L=xxx I=1020"
echo "(flash the oracle_fixture boot image at 0x120000 first -- see this"
echo " script's header comment)"
