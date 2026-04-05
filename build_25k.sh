#!/usr/bin/env bash
# build_25k.sh — Open-source bitstream build for Tang Primer 25K (GW5A-LV25MG121NES)
#
# Flow: yosys (synth_gowin) → nextpnr-himbaechel → gowin_pack → openFPGALoader
#
# Usage:
#   ./build_25k.sh           # synthesise + place-and-route + pack
#   ./build_25k.sh synth     # synthesis only (resource report)
#   ./build_25k.sh pnr       # PnR only (assumes build/tang_primer_25k.json exists)
#   ./build_25k.sh pack      # pack only (assumes build/tang_primer_25k_pnr.json exists)
#   ./build_25k.sh flash     # program board via USB (assumes build/*.fs exists)
#   ./build_25k.sh clean     # remove all build artifacts
#
# Requirements: oss-cad-suite in PATH (yosys, nextpnr-himbaechel, gowin_pack,
#               openFPGALoader).
#
# CC0 1.0 Universal.

set -euo pipefail

DEVICE="GW5A-LV25MG121NES"
TOP="spu_tang_top"
YS="hardware/boards/tang_primer_25k/synth_gowin_25k.ys"
CST="hardware/boards/tang_primer_25k/tang_primer_25k.cst"
JSON="build/tang_primer_25k.json"
PNR_JSON="build/tang_primer_25k_pnr.json"
FS="build/tang_primer_25k.fs"

STEP="${1:-all}"

synth() {
    echo "=== Synthesis: ${TOP} → ${JSON} ==="
    mkdir -p build
    yosys "${YS}"
}

pnr() {
    echo "=== Place & Route: ${JSON} → ${PNR_JSON} ==="
    mkdir -p build
    nextpnr-himbaechel \
        --device "${DEVICE}" \
        --json  "${JSON}"    \
        -o cst="${CST}"      \
        -o sspi_as_gpio      \
        --write "${PNR_JSON}"
}

pack() {
    echo "=== Pack: ${PNR_JSON} → ${FS} ==="
    mkdir -p build
    gowin_pack -d GW5A-25A --sspi_as_gpio "${PNR_JSON}" -o "${FS}"
}

flash() {
    echo "=== Flash: ${FS} → board ==="
    openFPGALoader -b tang_primer_25k "${FS}"
}

clean() {
    echo "=== Clean: removing build/ artifacts ==="
    rm -rf build/tang_primer_25k.json \
           build/tang_primer_25k_pnr.json \
           build/tang_primer_25k.fs
    echo "    Done. (build/vcd/ and build/sim/ preserved)"
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
        echo "=== Build complete: ${FS} ==="
        echo "    Program board with:  ./build_25k.sh flash"
        ;;
    *)
        echo "Unknown step '${STEP}'. Use: all | synth | pnr | pack | flash | clean"
        exit 1
        ;;
esac
