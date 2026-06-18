#!/usr/bin/env bash
# build_25k_spu13_som_probe.sh — SPU-13 SOM BMU probe for Tang Primer 25K
#
# Enables: math path (rotor/Davis) + SOM BMU classifier (ENABLE_CORE_SOM=1)
# Disabled: SDRAM, RPLU, lattice
#
# The SOM probe isolates the BMU scan pipeline: QR regfile → quadrance_accum →
# spu_som_bmu → spu_cluster_reduce → hex_q/hex_r → UART telemetry.
# Opcode 0x2A SOM_CLASSIFY drives the classify FSM; result appears on UART
# as H:QQQQ RRRR (label + ambiguity flag).
#
# Usage:
#   bash build_25k_spu13_som_probe.sh          # full build
#   bash build_25k_spu13_som_probe.sh flash    # program board
#
# Requirements: oss-cad-suite in PATH.

set -euo pipefail

OSS_CAD="${OSS_CAD_SUITE_PATH:-/opt/oss-cad-suite}"
export PATH="${OSS_CAD}/bin:${PATH}"

DEVICE="GW5A-LV25MG121NES"
CST="hardware/boards/tang_primer_25k/tang_primer_25k.cst"
YS="hardware/boards/tang_primer_25k/synth_gowin_25k_spu13_som_probe.ys"
JSON="build/spu13_som_probe.json"
PNR_JSON="build/spu13_som_probe_pnr.json"
FS="build/tang_primer_25k_spu13_som_probe.fs"

STEP="${1:-all}"

synth() {
    echo "=== 1. Yosys Synthesis (SPU-13 SOM probe) ==="
    mkdir -p build
    yosys "${YS}"
}

pnr() {
    echo "=== 2. NextPNR Place & Route ==="
    mkdir -p build
    nextpnr-himbaechel \
        --device "${DEVICE}" \
        --vopt family=GW5A-25A \
        --vopt sspi_as_gpio \
        --vopt cst="${CST}" \
        --json "${JSON}" \
        --write "${PNR_JSON}" \
        --freq 12
}

pack() {
    echo "=== 3. Package Bitstream ==="
    mkdir -p build
    gowin_pack -d GW5A-25A --sspi_as_gpio --cpu_as_gpio \
        "${PNR_JSON}" -o "${FS}"
}

flash() {
    echo "=== Flash: ${FS} → Tang Primer 25K ==="
    openFPGALoader -b tangprimer25k "${FS}"
}

clean() {
    echo "=== Clean: removing SOM probe artifacts ==="
    rm -f "${JSON}" "${PNR_JSON}" "${FS}"
    echo "    Done."
}

case "${STEP}" in
    synth)  synth ;;
    pnr)    pnr ;;
    pack)   pack ;;
    flash)  flash ;;
    clean)  clean ;;
    all)
        synth
        pnr
        pack
        echo ""
        echo "=== SPU-13 SOM Probe Build Complete ==="
        echo "Bitstream: ${FS}"
        echo "To load:   bash build_25k_spu13_som_probe.sh flash"
        echo ""
        echo "Proof line (UART at 115200 baud):"
        echo "  H:QQQQ RRRR    # hex_q = cluster label, hex_r[0] = ambiguous"
        ;;
    *)
        echo "Unknown step '${STEP}'. Use: all | synth | pnr | pack | flash | clean"
        exit 1
        ;;
esac
