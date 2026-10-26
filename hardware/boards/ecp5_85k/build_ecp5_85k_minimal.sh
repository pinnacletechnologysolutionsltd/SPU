#!/bin/bash
# build_ecp5_85k_minimal.sh — Minimal curated source list for SPU-13 ECP5-85F
#
# Strategy: Include only modules directly instantiated by spu_ecp5_top,
# avoiding the full RTL forest and module redefinition conflicts.
#
# Usage:
#   bash hardware/boards/ecp5_85k/build_ecp5_85k_minimal.sh [synth|pnr|bitstream|all]

set -euo pipefail

STEP="${1:-all}"
BOARD_DIR="hardware/boards/ecp5_85k"
BUILD_DIR="build"

TOP_MODULE="spu_ecp5_top"
DEVICE_FLAG="--um5g-85k"
PACKAGE="CABGA381"
NEXTPNR_HOME="${SPU_NEXTPNR_HOME:-${PWD}/${BUILD_DIR}/yosyshq_home}"

mkdir -p "$BUILD_DIR" "$NEXTPNR_HOME"

# Minimal curated Verilog source list
# Only modules actually instantiated in the dependency tree
SOURCES=(
    # Board top-level
    "${BOARD_DIR}/spu_ecp5_top.v"

    # SPU-13 core
    "hardware/rtl/core/spu13/spu13_top.v"

    # Direct dependencies of spu13_top
    "hardware/rtl/top/spu_laminar_boot.v"
    "hardware/rtl/peripherals/io/spu_node_link.v"
    "hardware/rtl/core/shared/spu_rotor_vault.v"
    "hardware/rtl/core/shared/spu_unified_alu_tdm.v"
    "hardware/rtl/core/spu13/spu13_berry_gate.v"
    "hardware/rtl/core/spu13/spu13_janus_mirror.v"

    # Architecture definitions
    "hardware/rtl/arch/spu_optional_stubs.v"
)

# Yosys synthesis
synth() {
    echo ">>> Yosys Synthesis <<<"

    # Prepare source list string
    SOURCES_STR="${SOURCES[@]}"

    # Run Yosys
    yosys -q -p "
        read_verilog -Ihardware/rtl/arch -Ihardware/common/rtl/include ${SOURCES_STR}
        synth_ecp5 -json ${BUILD_DIR}/${TOP_MODULE}.json -top ${TOP_MODULE}
    "

    echo "✓ Synthesis complete: ${BUILD_DIR}/${TOP_MODULE}.json"
}

# Nextpnr place-and-route
pnr() {
    echo ">>> Nextpnr Place-and-Route <<<"

    HOME="$NEXTPNR_HOME" nextpnr-ecp5 \
        "$DEVICE_FLAG" \
        --json "${BUILD_DIR}/${TOP_MODULE}.json" \
        --lpf "${BOARD_DIR}/spu_ecp5_85k.lpf" \
        --lpf-allow-unconstrained \
        --textcfg "${BUILD_DIR}/${TOP_MODULE}_out.config" \
        --freq 50 \
        --speed 8 \
        --package "$PACKAGE"

    echo "✓ Place-and-route complete"
}

# Bitstream generation
bitstream() {
    echo ">>> Ecppack Bitstream Generation <<<"

    ecppack --compress \
        --input "${BUILD_DIR}/${TOP_MODULE}_out.config" \
        --bit "${BUILD_DIR}/${TOP_MODULE}.bit"

    echo "✓ Bitstream complete: ${BUILD_DIR}/${TOP_MODULE}.bit"
}

case "$STEP" in
    synth)
        synth
        ;;
    pnr)
        pnr
        ;;
    bitstream)
        bitstream
        ;;
    all)
        synth
        pnr
        bitstream
        ;;
    *)
        echo "Usage: $0 [synth|pnr|bitstream|all]"
        exit 1
        ;;
esac

echo ""
echo "=== ECP5 Build Complete ==="
