#!/bin/bash
# build_25k_spu_whisper_v1_probe.sh
# Synthesise, place-and-route, and generate bitstream for the
# Whisper v1 emitter+listener loopback probe on Tang Primer 25K.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOARD_DIR="$SCRIPT_DIR/hardware/boards/tang_primer_25k"
BUILD_DIR="build"

mkdir -p "$BUILD_DIR"

echo "=== Whisper v1 probe: synthesis ==="
yosys "$BOARD_DIR/synth_gowin_25k_spu_whisper_v1_probe.ys"

echo "=== Whisper v1 probe: place-and-route ==="
nextpnr-himbaechel \
    --json "$BUILD_DIR/tang_primer_25k_whisper_v1_probe.json" \
    --write "$BUILD_DIR/tang_primer_25k_whisper_v1_probe_pnr.json" \
    --device GW5A-LV25MG121NES \
    --vopt cst="$BOARD_DIR/tang_primer_25k_som_probe.cst" \
    --vopt family=GW5A-25A \
    --vopt sspi_as_gpio

echo "=== Whisper v1 probe: pack ==="
gowin_pack \
    -d GW5A-25A \
    --sspi_as_gpio --mspi_as_gpio --cpu_as_gpio \
    -o "$BUILD_DIR/tang_primer_25k_whisper_v1_probe.fs" \
    "$BUILD_DIR/tang_primer_25k_whisper_v1_probe_pnr.json"

echo "=== Done: $BUILD_DIR/tang_primer_25k_whisper_v1_probe.fs ==="
echo "Flash: openFPGALoader -b tangprimer25k -f $BUILD_DIR/tang_primer_25k_whisper_v1_probe.fs"
