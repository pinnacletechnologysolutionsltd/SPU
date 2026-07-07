#!/usr/bin/env bash
# build_a7.sh — SPU-13 Artix-7 Build Script (v1.1)
#
# Usage:
#   bash build_a7.sh                           # FULL spin on 100T
#   bash build_a7.sh 200t multimedia            # MULTIMEDIA spin on 200T
#   bash build_a7.sh 35t robotics synth          # synth only, ROBOTICS spin on 35T
#   bash build_a7.sh 100t intelligence           # INTELLIGENCE spin on 100T
#   A7_FREQ=2 bash build_a7.sh 100t lucas all    # Wukong pinned low-speed bring-up
#
# Spins: multimedia | intelligence | robotics | full | sensor | lucas | su3 | su3share | rplucfg | rplu2core | rplu2 | rplu2live | rplu2pade | som | custom

set -euo pipefail

DEVICE_CHIP="${1:-100t}"
SPIN="${2:-full}"
STEP="${3:-all}"
A7_FREQ="${A7_FREQ:-50}"
A7_CLK_DIV_LOG2="${A7_CLK_DIV_LOG2:-0}"

# Resolve spin to uppercase
SPIN=$(echo "$SPIN" | tr '[:lower:]' '[:upper:]')

case "$DEVICE_CHIP" in
    35t)
        PART="xc7a35tcsg324-1"; XDC="hardware/boards/artix7/spu_a7_35t.xdc"
        DEVICE_PARAM="A7_35T"
        CHIPDB="build/chipdb/xc7a35t.bin"
        JSON="build/spu_a7_35t_${SPIN}.json"
        BITSTREAM="build/spu_a7_35t_${SPIN}.bit";;
    100t)
        PART="xc7a100tfgg676-1"; XDC="hardware/boards/artix7/spu_a7_100t.xdc"
        DEVICE_PARAM="A7_100T"
        CHIPDB="build/chipdb/xc7a100tfgg676.bin"
        JSON="build/spu_a7_100t_${SPIN}.json"
        BITSTREAM="build/spu_a7_100t_${SPIN}.bit";;
    200t)
        PART="xc7a200tsbg484-1"; XDC="hardware/boards/artix7/spu_a7_200t.xdc"
        DEVICE_PARAM="A7_200T"
        CHIPDB="build/chipdb/xc7a200t.bin"
        JSON="build/spu_a7_200t_${SPIN}.json"
        BITSTREAM="build/spu_a7_200t_${SPIN}.bit";;
    *) echo "Unknown device: $DEVICE_CHIP (use 35t|100t|200t)"; exit 1;;
esac

YS="hardware/boards/artix7/synth_a7.ys"

echo "=== SPU-13 Artix-7 Build ==="
echo "  Device: $DEVICE_CHIP ($PART)"
echo "  Spin:   $SPIN"
echo "  Step:   $STEP"
echo "  Freq:   ${A7_FREQ} MHz"
echo "  ClkDiv: /$((1 << A7_CLK_DIV_LOG2))"
echo ""

synth() {
    echo ">>> Yosys Synthesis <<<"
    mkdir -p build
    yosys -p "script $YS; \
        chparam -set DEVICE \"$DEVICE_PARAM\" \
                -set SPIN \"$SPIN\" \
                -set A7_CLK_DIV_LOG2 $A7_CLK_DIV_LOG2 \
                spu_a7_top; \
        hierarchy -check -top spu_a7_top; \
        synth_xilinx -family xc7 -top spu_a7_top -json \"$JSON\"; \
        stat -top spu_a7_top"
}

pnr() {
    echo ">>> NextPNR Place & Route <<<"
    [ -f "$CHIPDB" ] || {
        echo "Missing chip database: $CHIPDB"
        echo "Run: tools/generate_a7_chipdb.sh $DEVICE_CHIP"
        exit 1
    }
    NEXTPNR_ARGS=(
        --chipdb "$CHIPDB"
        --xdc "$XDC"
        --json "$JSON"
        --write "${JSON}.pnr.json"
        --fasm "${JSON}.pnr.fasm"
        --log "${JSON}.nextpnr.log"
        --freq "$A7_FREQ"
    )
    if nextpnr-xilinx --help 2>&1 | grep -q -- "--report"; then
        NEXTPNR_ARGS+=(
            --report "${JSON}.timing_report.json"
            --detailed-timing-report
        )
    fi

    nextpnr-xilinx "${NEXTPNR_ARGS[@]}"

    if [ -f "${JSON}.timing_report.json" ]; then
        python3 tools/collect_fpga_metrics.py \
            --name "artix7_${DEVICE_CHIP}_${SPIN}" \
            --board "QMTech Wukong Artix-7" \
            --device "$PART" \
            --toolchain "Yosys + nextpnr-xilinx + Project X-Ray" \
            --top spu_a7_top \
            --report "${JSON}.timing_report.json" \
            --log "${JSON}.nextpnr.log" \
            --out-json "build/metrics/artix7_${DEVICE_CHIP}_${SPIN}.json" \
            --out-md "build/metrics/artix7_${DEVICE_CHIP}_${SPIN}.md" \
            --note "A7_FREQ=${A7_FREQ} MHz; post-route metrics from nextpnr-xilinx."
    else
        echo "  nextpnr build has no JSON timing report; skipping metrics collection."
    fi
}

pack() {
    echo ">>> Bitstream Generation <<<"
    command -v xc7frames2bit &>/dev/null || {
        echo "  Install Project X-Ray tools for bitstream generation."
        echo "  Or open Vivado and run: source hardware/boards/artix7/pack_a7.tcl"
        exit 1
    }

    FASM="${JSON}.pnr.fasm"
    FRAMES="${JSON}.pnr.frames"
    OPENXC7_ROOT="${OPENXC7_ROOT:-$HOME/.local/openxc7}"
    OPENXC7_PYTHON="${OPENXC7_PYTHON:-python3}"
    XRAY_DB_ROOT="${XRAY_DB_ROOT:-$OPENXC7_ROOT/share/nextpnr/prjxray-db/artix7}"
    PART_FILE="${XRAY_DB_ROOT}/${PART}/part.yaml"
    FASM2FRAMES="${FASM2FRAMES:-}"

    if [ -z "$FASM2FRAMES" ]; then
        if command -v fasm2frames.py &>/dev/null; then
            FASM2FRAMES="$(command -v fasm2frames.py)"
        elif command -v fasm2frames &>/dev/null; then
            FASM2FRAMES="$(command -v fasm2frames)"
        elif [ -n "${PRJXRAY_ROOT:-}" ] && [ -f "$PRJXRAY_ROOT/tools/fasm2frames.py" ]; then
            FASM2FRAMES="$PRJXRAY_ROOT/tools/fasm2frames.py"
        elif [ -n "${PRJXRAY_ROOT:-}" ] && [ -f "$PRJXRAY_ROOT/utils/fasm2frames.py" ]; then
            FASM2FRAMES="$PRJXRAY_ROOT/utils/fasm2frames.py"
        fi
    fi

    [ -f "$FASM" ] || { echo "Missing routed FASM: $FASM"; exit 1; }
    [ -f "$PART_FILE" ] || { echo "Missing Project X-Ray part file: $PART_FILE"; exit 1; }
    [ -n "$FASM2FRAMES" ] || {
        echo "Missing fasm2frames.py. Set FASM2FRAMES=/path/to/fasm2frames.py or PRJXRAY_ROOT=/path/to/prjxray."
        exit 1
    }

    PRJXRAY_PYTHONPATH="${PRJXRAY_ROOT:-}"
    if [ -n "$PRJXRAY_PYTHONPATH" ] && [ -n "${PYTHONPATH:-}" ]; then
        PRJXRAY_PYTHONPATH="$PRJXRAY_PYTHONPATH:$PYTHONPATH"
    elif [ -z "$PRJXRAY_PYTHONPATH" ]; then
        PRJXRAY_PYTHONPATH="${PYTHONPATH:-}"
    fi

    PYTHONPATH="$PRJXRAY_PYTHONPATH" "$OPENXC7_PYTHON" "$FASM2FRAMES" \
        --db-root "$XRAY_DB_ROOT" \
        --part "$PART" \
        --sparse \
        "$FASM" \
        "$FRAMES"
    xc7frames2bit \
        --part_file "$PART_FILE" \
        --part_name "$PART" \
        --frm_file "$FRAMES" \
        --output_file "$BITSTREAM"
    echo "  Frames:    $FRAMES"
    echo "  Bitstream: $BITSTREAM"
}

flash() {
    [ -f "$BITSTREAM" ] || { echo "No bitstream. Build first."; exit 1; }
    openFPGALoader -b arty_a7 "$BITSTREAM"
}

case "$STEP" in
    synth) synth;;  pnr) pnr;;  pack) pack;;  flash) flash;;
    all) synth && pnr && pack;;
    *) echo "Unknown step: $STEP"; exit 1;;
esac
