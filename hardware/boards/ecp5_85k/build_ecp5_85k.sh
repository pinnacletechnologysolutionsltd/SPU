#!/bin/bash

# Build script for SPU-13 Core + RPLU v2 on ECP5-85F

# Exit on error
set -e

BOARD_DIR=$(dirname "$0")
BUILD_DIR="build"

TOP_MODULE="spu_ecp5_top"
DEVICE_FLAG="--um5g-85k"
PACKAGE="CABGA381"
NEXTPNR_HOME="${SPU_NEXTPNR_HOME:-${PWD}/${BUILD_DIR}/yosyshq_home}"

# Create build directory if it doesn't exist
mkdir -p "${BUILD_DIR}" "${NEXTPNR_HOME}"

# Verilog source files
COMMON_RTL_DIR="hardware/common/rtl"
SPU13_CORE_RTL_DIR="hardware/rtl/core/spu13"
GPU_RTL_DIR="hardware/rtl/gpu"

VERILOG_SOURCES=(
    "${BOARD_DIR}/${TOP_MODULE}.v"
    "${SPU13_CORE_RTL_DIR}/spu13_top.v"
    "${SPU13_CORE_RTL_DIR}/rplu_pipeline.v"
    "${GPU_RTL_DIR}/rplu_thimble_pade.v"

    # Include all other necessary SPU-13 core and RPLU dependencies
    # from hardware/rtl/core/spu13/
    "${SPU13_CORE_RTL_DIR}/laminar_node.v"
    "${SPU13_CORE_RTL_DIR}/spu13_axiomatic_gatekeeper.v"
    "${SPU13_CORE_RTL_DIR}/spu13_berry_gate.v"
    "${SPU13_CORE_RTL_DIR}/spu13_btu_core_top.v"
    "${SPU13_CORE_RTL_DIR}/spu13_core.v"
    "${SPU13_CORE_RTL_DIR}/spu13_fp4_inverter.v"
    "${SPU13_CORE_RTL_DIR}/spu13_janus_dual_mode.v"
    "${SPU13_CORE_RTL_DIR}/spu13_janus_mirror.v"
    "${SPU13_CORE_RTL_DIR}/spu13_janus_screw_lines.v"
    "${SPU13_CORE_RTL_DIR}/spu13_jet_inv.v"
    "${SPU13_CORE_RTL_DIR}/spu13_jet_mac.v"
    "${SPU13_CORE_RTL_DIR}/spu13_lattice.v"
    "${SPU13_CORE_RTL_DIR}/spu13_lucas_mac.v"
    "${SPU13_CORE_RTL_DIR}/spu13_lucas_sidecar.v"
    "${SPU13_CORE_RTL_DIR}/spu13_m31_inverter.v"
    "${SPU13_CORE_RTL_DIR}/spu13_m31_multiplier.v"
    "${SPU13_CORE_RTL_DIR}/spu13_multi_port_regfile.v"
    "${SPU13_CORE_RTL_DIR}/spu13_neuro_epoch_sidecar.v"
    "${SPU13_CORE_RTL_DIR}/spu13_neuro_sidecar_adapter.v"
    "${SPU13_CORE_RTL_DIR}/spu13_nsa_core.v"
    "${SPU13_CORE_RTL_DIR}/spu13_nsa_dual_alu.v"
    "${SPU13_CORE_RTL_DIR}/spu13_nsa_regfile_wrapper.v"
    "${SPU13_CORE_RTL_DIR}/spu13_permute_13.v"
    "${SPU13_CORE_RTL_DIR}/spu13_phslk_core.v"
    "${SPU13_CORE_RTL_DIR}/spu13_quadray_variety.v"
    "${SPU13_CORE_RTL_DIR}/spu13_rotary_gate.v"
    "${SPU13_CORE_RTL_DIR}/spu13_rotor_core.v"
    "${SPU13_CORE_RTL_DIR}/spu13_rotor_core_tdm.v"
    "${SPU13_CORE_RTL_DIR}/spu13_rplu2_sidecar.v"
    "${SPU13_CORE_RTL_DIR}/spu13_scoreboard.v"
    "${SPU13_CORE_RTL_DIR}/spu13_sequencer.v"
    "${SPU13_CORE_RTL_DIR}/spu13_som_classify.v"
    "${SPU13_CORE_RTL_DIR}/spu13_southbridge_token_parser.v"
    "${SPU13_CORE_RTL_DIR}/spu13_su3_mult.v"
    "${SPU13_CORE_RTL_DIR}/spu13_su3_sidecar.v"
    "${SPU13_CORE_RTL_DIR}/spu13_topology6_state.v"
    "${SPU13_CORE_RTL_DIR}/spu_bram_32x64_array.v"
    "${SPU13_CORE_RTL_DIR}/spu_btu_collision_resolver.v"
    "${SPU13_CORE_RTL_DIR}/spu_cluster_reduce.v"
    "${SPU13_CORE_RTL_DIR}/spu_instr_decode.v"
    "${SPU13_CORE_RTL_DIR}/spu_quadrance_accum.v"
    "${SPU13_CORE_RTL_DIR}/spu_sequencer.v"
    "${SPU13_CORE_RTL_DIR}/spu_som_bmu.v"
    "${SPU13_CORE_RTL_DIR}/spu_som_node.v"
    "${SPU13_CORE_RTL_DIR}/spu_som_node_array.v"
    "${SPU13_CORE_RTL_DIR}/spu_som_train.v"

    # Include all other necessary GPU/RPLU dependencies
    # from hardware/rtl/gpu/
    "${GPU_RTL_DIR}/davis_to_rplu.v"
    "${GPU_RTL_DIR}/pade_eval_4_4.v"
    "${GPU_RTL_DIR}/rplu_exp.v"
    "${GPU_RTL_DIR}/rplu_poly_step.v"
    "${GPU_RTL_DIR}/spu4_bram_ip.v"
    "${GPU_RTL_DIR}/spu_bresenham_raster.v"
    "${GPU_RTL_DIR}/spu_dual_raster.v"
    "${GPU_RTL_DIR}/spu_edge_stepper.v"
    "${GPU_RTL_DIR}/spu_gpu_top.v"
    "${GPU_RTL_DIR}/spu_raster_unit.v"
    "${GPU_RTL_DIR}/spu_texture_dma.v"
    "${GPU_RTL_DIR}/spu_video_timing.v"
)

# Yosys synthesis
# Exclude known SystemVerilog-heavy modules that Yosys cannot parse directly
# These will be treated as blackboxes (inferred from instantiations)
EXCLUDES=(
    "${SPU13_CORE_RTL_DIR}/spu13_jet_mac.v"
    "${SPU13_CORE_RTL_DIR}/spu13_phslk_core.v"
    "${SPU13_CORE_RTL_DIR}/spu13_som_classify.v"
    "hardware/rtl/common/prim/spu_gowin_prim.v"
    "hardware/rtl/common/prim/spu_xilinx_prim.v"
)

# Append shared/core/common RTL directories (expand wildcard lists)
shopt -s nullglob
for f in hardware/rtl/core/shared/*.v; do
    VERILOG_SOURCES+=("$f")
done
for f in hardware/common/rtl/*.v; do
    VERILOG_SOURCES+=("$f")
done
for f in hardware/common/rtl/core/*.v; do
    VERILOG_SOURCES+=("$f")
done
shopt -u nullglob

# Also include all Verilog under hardware/rtl recursively to avoid missing modules
while IFS= read -r -d '' f; do
    VERILOG_SOURCES+=("$f")
done < <(find hardware/rtl -name '*.v' -print0)

# Build filtered source list
VERILOG_SOURCES_FINAL=()
for src in "${VERILOG_SOURCES[@]}"; do
    skip=0
    for ex in "${EXCLUDES[@]}"; do
        if [ "${src}" = "${ex}" ]; then skip=1; break; fi
    done
    if [ ${skip} -eq 0 ]; then
        VERILOG_SOURCES_FINAL+=("${src}")
    else
        echo "Excluding ${src} from synthesis (blackbox)"
    fi
done

# Deduplicate final list (preserve order)
declare -A _seen_files
VERILOG_SOURCES_UNIQ=()
for f in "${VERILOG_SOURCES_FINAL[@]}"; do
    if [ -z "${_seen_files[$f]}" ]; then
        VERILOG_SOURCES_UNIQ+=("$f")
        _seen_files[$f]=1
    fi
done

# Combine final unique list into a string for yosys read_verilog
VERILOG_SOURCES_STR="${VERILOG_SOURCES_UNIQ[@]}"

yosys -q -p "read_verilog -Ihardware/rtl/arch -Ihardware/common/rtl/include -sv ${VERILOG_SOURCES_STR}; synth_ecp5 -json ${BUILD_DIR}/${TOP_MODULE}.json -top ${TOP_MODULE}"

# Nextpnr place-and-route
HOME="${NEXTPNR_HOME}" nextpnr-ecp5 "${DEVICE_FLAG}" --json "${BUILD_DIR}/${TOP_MODULE}.json" \
    --lpf "${BOARD_DIR}/spu_ecp5_85k.lpf" \
    --lpf-allow-unconstrained \
    --textcfg "${BUILD_DIR}/${TOP_MODULE}_out.config" \
    --freq 50 --speed 8 \
    --package "${PACKAGE}"

# Ecppack bitstream generation
ecppack --compress --input "${BUILD_DIR}/${TOP_MODULE}_out.config" \
    --bit "${BUILD_DIR}/${TOP_MODULE}.bit"

echo "ECP5 build complete. Bitstream: ${BUILD_DIR}/${TOP_MODULE}.bit"
