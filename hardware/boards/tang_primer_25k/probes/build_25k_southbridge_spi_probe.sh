#!/usr/bin/env bash
# build_25k_southbridge_spi_probe.sh — Tang 25K SPI-only southbridge telemetry probe
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SPI-only southbridge probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_southbridge_spi_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_southbridge.cst \
    --json build/southbridge_spi_probe.json \
    --write build/southbridge_spi_probe_pnr.json \
    --log build/southbridge_spi_probe_nextpnr.log \
    --report build/southbridge_spi_probe_timing_report.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/southbridge_spi_probe_pnr.json \
    -o build/tang_primer_25k_southbridge_spi_probe.fs

echo "Bitstream: build/tang_primer_25k_southbridge_spi_probe.fs"
