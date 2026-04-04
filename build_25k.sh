#!/usr/bin/env bash
# build_25k.sh — Open-source bitstream build for Tang Primer 25K (GW5A-LV25MG121C1/I0)
#
# Flow: yosys (synth_gowin) → nextpnr-himbaechel → gowin_pack → openFPGALoader
#
# Usage:
#   ./build_25k.sh           # synthesise + place-and-route + pack
#   ./build_25k.sh synth     # synthesis only (resource report)
#   ./build_25k.sh pnr       # PnR only (assumes tang_primer_25k.json exists)
#   ./build_25k.sh flash     # program board via USB (assumes .fs exists)
#
# Requirements: oss-cad-suite in PATH (yosys, nextpnr-himbaechel, gowin_pack,
#               openFPGALoader).
#
# CC0 1.0 Universal.

set -euo pipefail

DEVICE="GW5A-LV25MG121C1/I0"
TOP="spu_tang_top"
YS="hardware/boards/tang_primer_25k/synth_gowin_25k.ys"
CST="hardware/boards/tang_primer_25k/tang_primer_25k.cst"
JSON="tang_primer_25k.json"
PNR_JSON="tang_primer_25k_pnr.json"
FS="tang_primer_25k.fs"

STEP="${1:-all}"

synth() {
    echo "=== Synthesis: ${TOP} → ${JSON} ==="
    yosys "${YS}"
}

pnr() {
    echo "=== Place & Route: ${JSON} → ${PNR_JSON} ==="
    nextpnr-himbaechel \
        --device "${DEVICE}" \
        --json  "${JSON}"    \
        --cst   "${CST}"     \
        --write "${PNR_JSON}"
}

pack() {
    echo "=== Pack: ${PNR_JSON} → ${FS} ==="
    gowin_pack "${PNR_JSON}" -o "${FS}"
}

flash() {
    echo "=== Flash: ${FS} → board ==="
    openFPGALoader -b tang_primer_25k "${FS}"
}

case "${STEP}" in
    synth)  synth ;;
    pnr)    pnr ;;
    flash)  flash ;;
    all)
        synth
        pnr
        pack
        echo ""
        echo "=== Build complete: ${FS} ==="
        echo "    Program board with:  ./build_25k.sh flash"
        ;;
    *)
        echo "Unknown step '${STEP}'. Use: all | synth | pnr | flash"
        exit 1
        ;;
esac
