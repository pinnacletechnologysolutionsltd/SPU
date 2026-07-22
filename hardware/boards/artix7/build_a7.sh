#!/usr/bin/env bash
# build_a7.sh — SPU-13 Artix-7 Build Script (v1.1)
#
# Usage:
#   bash build_a7.sh                           # FULL spin on 100T
#   bash build_a7.sh 200t multimedia            # MULTIMEDIA spin on 200T
#   bash build_a7.sh 35t robotics synth          # synth only, ROBOTICS spin on 35T
#   bash build_a7.sh 100t intelligence           # INTELLIGENCE spin on 100T
#   A7_FREQ=2 bash build_a7.sh 100t lucas all    # Wukong pinned low-speed bring-up
#   ZPHI_KARATSUBA=1 A7_SEED=2 bash build_a7.sh 100t tensegrityprobe synth
#
# Spins: multimedia | intelligence | robotics | full | sensor | lucas | su3 | su3share | rplucfg | rplu2core | rplu2 | rplu2live | rplu2pade | irotc | som | somprobe | somsidecar | tensegrityprobe | tensegritylink | custom
#
# somprobe is a standalone top (not a spu_a7_top spin): the Tang-25K-proven
# SOM/BMU fixture on its own synthesis path + minimal XDC.  Golden UART line
# at 115200: "SOM:P T:2 B:6 E:00".
# tensegrityprobe is likewise standalone.  It runs all seven TGR1-derived
# guard fixtures and reports "TGR:P V:7 E:00".

set -euo pipefail

# Keep the documented one-command build path working in a fresh shell.  The
# helper only prepends the repo-local OpenXC7 install; it leaves an existing
# PATH/toolchain selection untouched.
if ! command -v nextpnr-xilinx >/dev/null 2>&1; then
    OPENXC7_ROOT_CANDIDATE="${OPENXC7_ROOT:-$HOME/.local/openxc7}"
    if [ -d "$OPENXC7_ROOT_CANDIDATE" ] && [ -f tools/env_openxc7.sh ]; then
        OPENXC7_ROOT="$OPENXC7_ROOT_CANDIDATE" source tools/env_openxc7.sh
    elif [ -f "$OPENXC7_ROOT_CANDIDATE/export.sh" ]; then
        source "$OPENXC7_ROOT_CANDIDATE/export.sh"
    fi
    unset OPENXC7_ROOT_CANDIDATE
fi

DEVICE_CHIP="${1:-100t}"
SPIN="${2:-full}"
STEP="${3:-all}"
A7_FREQ_ENV="${A7_FREQ:-}"
# TEMPORARY bring-up aid, explicit opt-in only, no spin defaults this to 1 --
# see spu_a7_top.v's A7_UART_DIAG parameter doc.
A7_UART_DIAG="${A7_UART_DIAG:-0}"

# Resolve spin to uppercase
SPIN=$(echo "$SPIN" | tr '[:lower:]' '[:upper:]')

# A7_FREQ default, spin-aware.  IROTC's current routed timing closes at low
# bring-up speed. TENSEGRITYPROBE and TENSEGRITYLINK have a 50 MHz board domain
# but intentionally advance their generated guard clock at 25 MHz; nextpnr
# applies --freq to that otherwise-unconstrained generated clock. An explicit
# A7_FREQ env var still overrides these defaults.
case "$SPIN" in
    IROTC)            A7_FREQ_DEFAULT=2;;
    TENSEGRITYPROBE|TENSEGRITYLINK) A7_FREQ_DEFAULT=25;;
    *)                A7_FREQ_DEFAULT=50;;
esac
A7_FREQ="${A7_FREQ_ENV:-$A7_FREQ_DEFAULT}"

# Make nextpnr's seed explicit in logs and metrics. A7_SEED remains available
# for deterministic placement exploration without changing the default flow.
A7_SEED="${A7_SEED:-1}"

# Selector for the two tensegrity A/B spins, defaulting to the Phase 5
# production candidate (Karatsuba three-product multiplier). Reject invalid
# values before constructing any artifact path, and reject opt-in use on
# unrelated spins so a recorded ZPHI_KARATSUBA setting cannot be silently
# ignored. The reference implementation remains selectable with ZPHI_KARATSUBA=0.
ZPHI_KARATSUBA="${ZPHI_KARATSUBA:-1}"
case "$ZPHI_KARATSUBA" in
    0|1) ;;
    *) echo "Invalid ZPHI_KARATSUBA: $ZPHI_KARATSUBA (use 0|1)"; exit 1;;
esac

TENSEGRITY_VARIANT=""
case "$SPIN" in
    TENSEGRITYPROBE|TENSEGRITYLINK)
        TENSEGRITY_VARIANT="_ZK${ZPHI_KARATSUBA}_S${A7_SEED}";;
    *)
        if [ "$ZPHI_KARATSUBA" != "0" ]; then
            echo "ZPHI_KARATSUBA applies only to TENSEGRITYPROBE or TENSEGRITYLINK"
            exit 1
        fi;;
esac

# A7_CLK_DIV_LOG2 default, spin-aware — mirrors the _CORE ternary in
# spu_a7_top.v (keep this list in sync with that one). Coreless sidecar
# spins (no spu13_core instance) run the raw fabric clock; every
# core-based spin needs clk_fast divided down to the Piranha Pulse
# dispatch cadence or QR telemetry corrupts silently with no synthesis
# or sim-side warning (root-caused in docs/hardware_evidence.md
# §3.2e.4, recurred on the IROTC spin's first build — §3.2k.1). An
# explicit A7_CLK_DIV_LOG2 env var still overrides this default.
case "$SPIN" in
    LUCAS|SU3|RPLUCFG|RPLU2LIVE|RPLU2PADE|SOMPROBE|SOMSIDECAR|TENSEGRITYPROBE|TENSEGRITYLINK) A7_CLK_DIV_LOG2_DEFAULT=0;;
    *)                                     A7_CLK_DIV_LOG2_DEFAULT=6;;
esac
A7_CLK_DIV_LOG2="${A7_CLK_DIV_LOG2:-$A7_CLK_DIV_LOG2_DEFAULT}"

case "$DEVICE_CHIP" in
    35t)
        PART="xc7a35tcsg324-1"; XDC="hardware/boards/artix7/spu_a7_35t.xdc"
        DEVICE_PARAM="A7_35T"
        CHIPDB="build/chipdb/xc7a35t.bin"
        JSON="build/spu_a7_35t_${SPIN}${TENSEGRITY_VARIANT}.json"
        BITSTREAM="build/spu_a7_35t_${SPIN}${TENSEGRITY_VARIANT}.bit";;
    100t)
        PART="xc7a100tfgg676-1"; XDC="hardware/boards/artix7/spu_a7_100t.xdc"
        DEVICE_PARAM="A7_100T"
        CHIPDB="build/chipdb/xc7a100tfgg676.bin"
        JSON="build/spu_a7_100t_${SPIN}${TENSEGRITY_VARIANT}.json"
        BITSTREAM="build/spu_a7_100t_${SPIN}${TENSEGRITY_VARIANT}.bit";;
    200t)
        PART="xc7a200tsbg484-1"; XDC="hardware/boards/artix7/spu_a7_200t.xdc"
        DEVICE_PARAM="A7_200T"
        CHIPDB="build/chipdb/xc7a200t.bin"
        JSON="build/spu_a7_200t_${SPIN}${TENSEGRITY_VARIANT}.json"
        BITSTREAM="build/spu_a7_200t_${SPIN}${TENSEGRITY_VARIANT}.bit";;
    *) echo "Unknown device: $DEVICE_CHIP (use 35t|100t|200t)"; exit 1;;
esac

YS="hardware/boards/artix7/synth_a7.ys"
TOP="spu_a7_top"

if [ "$SPIN" = "SOMPROBE" ]; then
    YS="hardware/boards/artix7/synth_a7_som_probe.ys"
    XDC="hardware/boards/artix7/spu_a7_som_probe.xdc"
    TOP="spu_a7_som_probe_top"
elif [ "$SPIN" = "SOMSIDECAR" ]; then
    YS="hardware/boards/artix7/synth_a7_som_sidecar.ys"
    XDC="hardware/boards/artix7/spu_a7_som_sidecar.xdc"
    TOP="spu_a7_som_sidecar_top"
elif [ "$SPIN" = "TENSEGRITYPROBE" ]; then
    YS="hardware/boards/artix7/synth_a7_tensegrity_probe.ys"
    XDC="hardware/boards/artix7/spu_a7_tensegrity_probe.xdc"
    TOP="spu_a7_tensegrity_probe_top"
elif [ "$SPIN" = "TENSEGRITYLINK" ]; then
    YS="hardware/boards/artix7/synth_a7_tensegrity_link.ys"
    XDC="hardware/boards/artix7/spu_a7_tensegrity_link.xdc"
    TOP="spu_a7_tensegrity_link_top"
fi

echo "=== SPU-13 Artix-7 Build ==="
echo "  Device: $DEVICE_CHIP ($PART)"
echo "  Spin:   $SPIN"
echo "  Step:   $STEP"
echo "  Freq:   ${A7_FREQ} MHz"
echo "  Seed:   ${A7_SEED}"
echo "  ClkDiv: /$((1 << A7_CLK_DIV_LOG2))"
if [ -n "$TENSEGRITY_VARIANT" ]; then
    echo "  ZPHI:   Karatsuba=${ZPHI_KARATSUBA} (0=reference, 1=candidate)"
    echo "  Tag:    ${TENSEGRITY_VARIANT#_}"
fi
if [ "$A7_UART_DIAG" != "0" ]; then
    echo "  UART:   DIAGNOSTIC MODE (real hex telemetry disabled)"
fi
echo ""

synth() {
    echo ">>> Yosys Synthesis <<<"
    mkdir -p build
    if [ "$SPIN" = "TENSEGRITYPROBE" ] || [ "$SPIN" = "TENSEGRITYLINK" ]; then
        yosys -p "script $YS; \
            hierarchy -check -top $TOP \
                      -chparam USE_ZPHI_KARATSUBA $ZPHI_KARATSUBA; \
            synth_xilinx -family xc7 -top $TOP -json \"$JSON\"; \
            stat -top $TOP"
    elif [ "$TOP" != "spu_a7_top" ]; then
        yosys -p "script $YS; \
            synth_xilinx -family xc7 -top $TOP -json \"$JSON\"; \
            stat -top $TOP"
    else
        yosys -p "script $YS; \
            chparam -set DEVICE \"$DEVICE_PARAM\" \
                    -set SPIN \"$SPIN\" \
                    -set A7_CLK_DIV_LOG2 $A7_CLK_DIV_LOG2 \
                    -set A7_UART_DIAG $A7_UART_DIAG \
                    spu_a7_top; \
            hierarchy -check -top spu_a7_top; \
            synth_xilinx -family xc7 -top spu_a7_top -json \"$JSON\"; \
            stat -top spu_a7_top"
    fi
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
        --seed "$A7_SEED"
    )
    if nextpnr-xilinx --help 2>&1 | grep -q -- "--report"; then
        NEXTPNR_ARGS+=(
            --report "${JSON}.timing_report.json"
            --detailed-timing-report
        )
    fi

    nextpnr-xilinx "${NEXTPNR_ARGS[@]}"

    METRICS_NAME="artix7_${DEVICE_CHIP}_${SPIN}${TENSEGRITY_VARIANT}"
    METRICS_NOTE="A7_FREQ=${A7_FREQ} MHz; A7_SEED=${A7_SEED}; post-route metrics from nextpnr-xilinx."
    if [ -n "$TENSEGRITY_VARIANT" ]; then
        METRICS_NOTE="A7_FREQ=${A7_FREQ} MHz; A7_SEED=${A7_SEED}; ZPHI_KARATSUBA=${ZPHI_KARATSUBA}; post-route metrics from nextpnr-xilinx."
    fi
    METRICS_REPORT_ARGS=()
    if [ -f "${JSON}.timing_report.json" ]; then
        METRICS_REPORT_ARGS=(--report "${JSON}.timing_report.json")
    else
        echo "  nextpnr build has no native JSON timing report; collecting log-backed metrics."
    fi
    python3 tools/collect_fpga_metrics.py \
        --name "$METRICS_NAME" \
        --board "QMTech Wukong Artix-7" \
        --device "$PART" \
        --toolchain "Yosys + nextpnr-xilinx + Project X-Ray" \
        --top "$TOP" \
        "${METRICS_REPORT_ARGS[@]}" \
        --log "${JSON}.nextpnr.log" \
        --out-json "build/metrics/${METRICS_NAME}.json" \
        --out-md "build/metrics/${METRICS_NAME}.md" \
        --note "$METRICS_NOTE"
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
