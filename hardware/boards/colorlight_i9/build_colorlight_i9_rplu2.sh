#!/bin/bash
# build_colorlight_i9_rplu2.sh — Build SPU-13 + RPLU2 pipeline for Colorlight i9
#
# Target: LFE5U-44F (caBGA-381) via SODIMM breakout
# Includes: spu13_core with RPLU2 pipeline, SPI southbridge, UART telemetry
#
# Usage:
#   bash hardware/boards/colorlight_i9/build_colorlight_i9_rplu2.sh [synth|pnr|bitstream|all]

set -euo pipefail

STEP="${1:-all}"
BOARD_DIR="hardware/boards/colorlight_i9"
BUILD_DIR="build"

TOP_MODULE="spu_colorlight_i9_rplu2_top"
DEVICE_FLAG="--45k"
PACKAGE="CABGA381"
NEXTPNR_HOME="${SPU_NEXTPNR_HOME:-${PWD}/${BUILD_DIR}/yosyshq_home}"

mkdir -p "$BUILD_DIR" "$NEXTPNR_HOME"

# Curated source list — spu13_core + RPLU2 pipeline + SPI slave + UART
# Excludes: sidecars (Lucas/SU3/neuro), ECC, GPU, Xilinx primitives
SOURCES=(
    # Board top
    "${BOARD_DIR}/spu_colorlight_i9_rplu2_top.v"

    # Architecture defines (included via -I, but referenced for clarity)
    # hardware/rtl/arch/spu_arch_defines.vh  (included via `include directive)
    # hardware/rtl/arch/spu_optional_stubs.v

    # SPU-13 core
    "hardware/rtl/core/spu13/spu13_core.v"

    # Legacy RPLU modules (referenced in core generate blocks even when disabled)
    "hardware/rtl/gpu/davis_to_rplu.v"
    "hardware/rtl/gpu/rplu_exp.v"
    "hardware/rtl/gpu/pade_eval_4_4.v"
    "hardware/rtl/gpu/rplu_poly_step.v"

    # Math primitives (surds, extensions — referenced by core)
    "hardware/rtl/math/rational_surd5_add.v"
    "hardware/rtl/math/rational_surd5_mul.v"
    "hardware/rtl/math/rational_surd5_mul64.v"
    "hardware/rtl/math/rational_surd5_norm.v"
    "hardware/rtl/math/rational_surd5_scale_manager.v"

    # RPLU v2 Thimble-Padé pipeline
    "hardware/rtl/core/spu13/rplu_pipeline.v"
    "hardware/rtl/gpu/rplu_thimble_pade.v"
    "hardware/rtl/core/spu13/spu_som_bmu.v"
    "hardware/rtl/core/spu13/spu13_btu_core_top.v"
    "hardware/rtl/core/spu13/spu_btu_collision_resolver.v"
    "hardware/rtl/core/spu13/spu_bram_32x64_array.v"
    "hardware/rtl/core/spu13/spu13_m31_multiplier.v"
    "hardware/rtl/core/spu13/spu13_fp4_inverter.v"
    "hardware/rtl/core/spu13/spu13_multi_port_regfile.v"
    "hardware/rtl/core/spu13/spu_som_train.v"
    "hardware/rtl/core/spu13/spu13_quadray_variety.v"
    "hardware/rtl/core/spu13/spu_cluster_reduce.v"

    # Core shared modules
    "hardware/rtl/core/spu13/spu_sequencer.v"
    "hardware/rtl/core/spu13/spu_quadrance_accum.v"
    "hardware/rtl/core/spu13/spu13_rotor_core_tdm.v"
    "hardware/rtl/core/spu13/spu13_lattice.v"
    "hardware/rtl/core/spu13/laminar_node.v"
    "hardware/rtl/core/shared/spu_rotor_vault.v"
    "hardware/rtl/core/shared/spu_cross_rotor.v"
    "hardware/rtl/core/shared/davis_gate_dsp.v"
    "hardware/rtl/core/shared/spu_quadray_permute.v"
    "hardware/rtl/core/shared/spu_quadray_regfile.v"
    "hardware/rtl/core/shared/spu_quadray_regfile_ecc.v"
    "hardware/rtl/common/prim/spu_hamming_72_64.v"
    "hardware/rtl/common/prim/surd_multiplier.v"
    "hardware/rtl/core/shared/spu_unified_alu_tdm.v"
    "hardware/rtl/core/shared/toroidal_regfile.v"
    "hardware/rtl/core/spu13/spu13_berry_gate.v"
    "hardware/rtl/core/spu13/spu13_janus_mirror.v"

    # ECP5-compatible behavioral multipliers (replace Gowin DSP primitives)
    "hardware/tests/common/sim_spu_gowin_mult32.v"
    "hardware/tests/common/sim_spu_gowin_multiplier.v"

    # SPI southbridge + UART (not in minimal probe -- ties off at top)
    # hardware/rtl/peripherals/io/spu_spi_slave.v
    # hardware/rtl/peripherals/io/surd_uart_tx.v

    # Top-level modules
    "hardware/rtl/top/spu_ve_qr_init.v"
    "hardware/rtl/top/spu_sierpinski_clk.v"

    # Stubs (for ROM-less unused modules)
    "hardware/rtl/arch/spu_optional_stubs.v"
)

# Remove `spu_xilinx_prim.v` — not used on ECP5.
# The ECP5 toolchain (yosys + nextpnr) handles clock distribution natively.

# Yosys synthesis
synth() {
    echo ">>> Yosys Synthesis (RPLU2 pipeline) <<<"
    echo "  Target: LFE5U-45F-class ($PACKAGE)"
    echo "  Top:    $TOP_MODULE"

    SOURCES_STR="${SOURCES[@]}"

    yosys -q -p "
        read_verilog -Ihardware/rtl/arch -Ihardware/common/rtl/include ${SOURCES_STR}
        synth_ecp5 -json ${BUILD_DIR}/${TOP_MODULE}.json -top ${TOP_MODULE}
        stat -top ${TOP_MODULE}
    "

    echo "✓ Synthesis complete: ${BUILD_DIR}/${TOP_MODULE}.json"
}

# Nextpnr place-and-route
pnr() {
    echo ">>> Nextpnr Place-and-Route <<<"

    HOME="$NEXTPNR_HOME" nextpnr-ecp5 \
        "$DEVICE_FLAG" \
        --json "${BUILD_DIR}/${TOP_MODULE}.json" \
        --lpf "${BOARD_DIR}/colorlight_i9.lpf" \
        --lpf-allow-unconstrained \
        --textcfg "${BUILD_DIR}/${TOP_MODULE}_out.config" \
        --freq 25 \
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
echo "=== ECP5 RPLU2 Build Complete ==="
