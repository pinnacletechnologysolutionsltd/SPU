#!/usr/bin/env bash
# build_20k.sh — Full open-source build flow for Tang Primer 20K (GW2A-LV18PG256C8/I7)
#
# Flow: yosys (synth_gowin) → nextpnr-himbaechel → gowin_pack → openFPGALoader
#
# Usage:
#   ./build_20k.sh           # synthesise + place-and-route + pack
#   ./build_20k.sh synth     # synthesis only (resource report)
#   ./build_20k.sh pnr       # PnR only (assumes build/tang_primer_20k.json exists)
#   ./build_20k.sh pack      # pack only (assumes build/tang_primer_20k_pnr.json exists)
#   ./build_20k.sh flash     # program board via USB (assumes build/*.fs exists)
#   ./build_20k.sh clean     # remove all build artifacts
#
# Requirements: oss-cad-suite in PATH (yosys, nextpnr-himbaechel, gowin_pack,
#               openFPGALoader). Crystal: 27 MHz. Target: GW2A-LV18PG256C8/I7.
# CC0 1.0 Universal.

set -euo pipefail

DEVICE="GW2A-LV18PG256C8/I7"
FAMILY="GW2A-18"
YS="hardware/boards/tang_primer_20k/synth_gowin_20k.ys"
JSON="build/tang_primer_20k.json"
CST="hardware/boards/tang_primer_20k/tang_primer_20k.cst"
PNR_JSON="build/tang_primer_20k_pnr.json"
FS="build/tang_primer_20k.fs"

STEP="${1:-all}"

synth() {
    echo "=== Synthesise: tang_primer_20k ==="
    mkdir -p build
    yosys -l /dev/null "${YS}"
}

pnr() {
    echo "=== Place & Route: ${JSON} → ${PNR_JSON} ==="
    mkdir -p build
    nextpnr-himbaechel \
        --device "${DEVICE}" \
        --json  "${JSON}"    \
        -o cst="${CST}"      \
        -o family="${FAMILY}" \
        --write "${PNR_JSON}"
}

pack() {
    echo "=== Pack: ${PNR_JSON} → ${FS} ==="
    mkdir -p build
    gowin_pack -d "${FAMILY}" "${PNR_JSON}" -o "${FS}"
}

flash() {
    echo "=== Flash: ${FS} → board ==="
    openFPGALoader -b tang_primer_20k "${FS}"
}

clean() {
    echo "=== Clean: removing build/ artifacts ==="
    rm -rf build/tang_primer_20k.json \
           build/tang_primer_20k_pnr.json \
           build/tang_primer_20k.fs
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
        echo "    Program board with:  ./build_20k.sh flash"
        ;;
    *)
        echo "Unknown step '${STEP}'. Use: all | synth | pnr | pack | flash | clean"
        exit 1
        ;;
esac
