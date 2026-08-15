#!/usr/bin/env bash
# build_25k_spu13_som_probe.sh — SOM classification probe for Tang Primer 25K
#
# ── RETIRED AS A TANG 25K TARGET, 2026-08-16 ──────────────────────
#   This spin does not fit the GW5A-25A: 23,891 LUT4 = 103% of 23,040.
#   Retired by decision, not by defect: it is absent from
#   hardware/boards/board_build_manifest.json because a target that
#   cannot fit cannot be a regression signal.
#   The closest of the five to fitting, and the most plausible trim candidate
#   if Tang SOM classification is wanted back. Tang SOM coverage meanwhile
#   survives via som_sidecar, som_bmu_probe and som_hydrate_probe.
#   Rationale and re-entry conditions: docs/hardware_evidence.md 3.6g.
#   Re-add to the manifest if trimmed under 23,040 LUT4 and rebuilt.
#
#   The script is left working and unmodified below.
# ─────────────────────────────────────────────────────────────────
set -e

mkdir -p build

echo "--- 1. Yosys Synthesis (SOM probe) ---"
yosys hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_probe.ys

echo "--- 2. NextPNR (Place & Route) ---"
nextpnr-himbaechel --device GW5A-LV25MG121NES \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio \
    --vopt cst=hardware/boards/tang_primer_25k/tang_primer_25k_som_probe.cst \
    --json build/spu13_som_probe.json \
    --write build/spu13_som_probe_pnr.json \
    --freq 12

echo "--- 3. Package Bitstream ---"
gowin_pack -d GW5A-25A \
    --sspi_as_gpio \
    --mspi_as_gpio \
    --cpu_as_gpio \
    build/spu13_som_probe_pnr.json \
    -o build/tang_primer_25k_spu13_som_probe.fs

echo ""
echo "=== SOM Probe Build Complete ==="
echo "Bitstream: build/tang_primer_25k_spu13_som_probe.fs"
echo "SRAM load: openFPGALoader -b tangprimer25k build/tang_primer_25k_spu13_som_probe.fs"
echo ""
echo "Connect USB-UART to C3 (TX) + GND at 115200 baud."
echo "Receives hex_q telemetry on SOM_CLASSIFY results."
