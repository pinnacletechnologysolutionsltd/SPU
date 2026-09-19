#!/usr/bin/env bash
# build_25k_spu4_abi_probe.sh -- Tang 25K silicon probe for SPU-4 ABI v1.0
#
# The first build that instantiates spu4_customer_wrapper, the module a
# customer integrates against. Deliberately SEPARATE from
# build_25k_spu4_probe.sh: that probe's bitstream is pinned by
# docs/hardware_evidence.md 3.2j and by a pre-registered bench procedure with
# images already staged, so adding the wrapper to it would void that prep.
#
# Golden UART line at 115200 baud:
#   ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7 I=1110
# L is the MEASURED latency in clocks (0xB7 = 183), which closes the bounded
# latency product gate with hardware evidence rather than a simulation figure.
# I is ABI v1.1's id port (SPU4_ABI.md 2a) -- wired through here for the
# first time, so a matching I=1110 off real silicon is what this build adds.
set -e
mkdir -p build

echo "--- 1. Yosys Synthesis (SPU-4 ABI probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu4_abi_probe.ys

echo "--- 2. NextPNR ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k.cst \
    --json build/spu4_abi_probe.json \
    --write build/spu4_abi_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    build/spu4_abi_probe_pnr.json \
    -o build/tang_primer_25k_spu4_abi_probe.fs

echo ""
echo "=== SPU-4 ABI Probe Build Complete ==="
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu4_abi_probe.fs"
echo "Expect:    ABI:P B=0155 C=0155 D=0155 R=FF S=0A L=0B7 I=1110"
