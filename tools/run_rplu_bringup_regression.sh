#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BUILD_DIR="build/rplu_regression"
mkdir -p "$BUILD_DIR"

run_tb() {
    local name="$1"
    shift
    local out="$BUILD_DIR/${name}.vvp"
    local log="$BUILD_DIR/${name}.log"

    echo "--- ${name}: compile ---"
    iverilog -g2012 \
        -I hardware/rtl/arch \
        -I hardware/rtl/gpu \
        -I hardware/rtl/core/shared \
        -I hardware/rtl/core/spu13 \
        -I hardware/rtl/math \
        -o "$out" "$@"

    echo "--- ${name}: run ---"
    timeout 20 vvp "$out" | tee "$log"
    if ! grep -q "^PASS" "$log" || grep -q "FAIL\\|ERROR" "$log"; then
        echo "${name}: regression failed"
        exit 1
    fi
}

FLASH_ARGS=(--output build/tang25k_j4_rplu_flash.bin)
if [[ -n "${RPLU_BASE_IMAGE:-}" ]]; then
    FLASH_ARGS=(--base-image "$RPLU_BASE_IMAGE" --output build/tang25k_j4_rplu_flash_merged.bin)
fi

echo "--- flash image: build RPLU payload ---"
python3 tools/build_tang25k_j4_rplu_flash.py "${FLASH_ARGS[@]}"

echo "--- RPLU metric reference ---"
python3 tools/rplu_metric_reference.py --require-payload

run_tb davis_to_rplu \
    hardware/rtl/core/shared/davis_gate_dsp.v \
    hardware/rtl/gpu/pade_eval_4_4.v \
    hardware/rtl/gpu/rplu_poly_step.v \
    hardware/rtl/gpu/rplu_exp.v \
    hardware/rtl/gpu/davis_to_rplu.v \
    hardware/tests/common/davis_to_rplu_tb.v

run_tb rplu_exp \
    hardware/rtl/gpu/pade_eval_4_4.v \
    hardware/rtl/gpu/rplu_poly_step.v \
    hardware/rtl/gpu/rplu_exp.v \
    hardware/tests/common/rplu_exp_tb.v

run_tb rplu_metric_vectors \
    hardware/rtl/gpu/pade_eval_4_4.v \
    hardware/rtl/gpu/rplu_poly_step.v \
    hardware/rtl/gpu/rplu_exp.v \
    hardware/tests/common/rplu_metric_vectors_tb.v

run_tb spu_rotor_vault \
    hardware/tests/common/spu_rotor_vault_tb.v

run_tb spu13_rplu_addr \
    hardware/rtl/math/rational_surd5_scale_manager.v \
    hardware/rtl/core/shared/davis_gate_dsp.v \
    hardware/rtl/gpu/pade_eval_4_4.v \
    hardware/rtl/gpu/rplu_poly_step.v \
    hardware/rtl/gpu/rplu_exp.v \
    hardware/rtl/gpu/davis_to_rplu.v \
    hardware/rtl/core/spu13/spu13_core.v \
    hardware/tests/common/spu13_rplu_addr_tb.v

run_tb spu_laminar_boot_rplu \
    hardware/rtl/top/spu_laminar_boot.v \
    hardware/tests/common/spu_laminar_boot_rplu_tb.v

echo "RPLU bring-up regression PASS"
