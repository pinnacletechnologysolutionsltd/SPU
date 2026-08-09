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
# Spins: multimedia | intelligence | robotics | full | sensor | lucas | su3 | su3share | rplucfg | rplu2core | rplu2 | rplu2live | rplu2pade | fp4evidence | irotc | som | somprobe | somsidecar | tensegrityprobe | tensegritylink | custom
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
# Capture-only RPLU2PADE pipeline observability. Default off and artifact-
# tagged when enabled so it cannot overwrite a production/evidence image.
PADE_DEBUG_TRACE="${PADE_DEBUG_TRACE:-0}"
PADE_PIPELINED="${PADE_PIPELINED:-0}"
case "$PADE_DEBUG_TRACE" in
    0|1) ;;
    *) echo "Invalid PADE_DEBUG_TRACE: $PADE_DEBUG_TRACE (use 0|1)"; exit 1;;
esac
case "$PADE_PIPELINED" in
    0|1) ;;
    *) echo "Invalid PADE_PIPELINED: $PADE_PIPELINED (use 0|1)"; exit 1;;
esac
# Per-lane RNS residue check inside the shared structured multiplier. Default
# off; at 1 rns_error is one cycle later than done (audited safe for the Pade
# sidecar only -- see spu13_rplu2_pade_sidecar.v).
PIPELINED_RNS_CHECK="${PIPELINED_RNS_CHECK:-0}"
case "$PIPELINED_RNS_CHECK" in
    0|1) ;;
    *) echo "Invalid PIPELINED_RNS_CHECK: $PIPELINED_RNS_CHECK (use 0|1)"; exit 1;;
esac

# Fp4 tower candidate selector. Default-ON again since 2026-08-05: the parallel
# structured inverter (v2) is the production path. Set FP4_STRUCTURED=0 to build
# the historical v1 tower.
#
# The case for v2, from the twenty-seed matrix in
# docs/FP4_STRUCTURED_INVERTER.md: it costs ~7.4% MORE LUT (10,121 vs 9,421) and
# ~3.6% median Fmax, and wins 7-10% median WALL-CLOCK because it retires a unit
# in 74 clocks against v1's 83 -- ahead on 19 of 20 seeds. The trade is area and
# Fmax for throughput. That evaluation always stood and none of it was withdrawn.
#
# WHY IT WAS REVERTED ON 2026-08-03, AND WHY THAT REASON IS NOW VOID:
# v2 was blamed for RPLU2PADE's seven_over_three returning a wrong value on
# silicon. That attribution was WRONG. The 2026-08-05 divided-clock campaign
# (build/pade_campaigns/20260805_083400) showed BOTH towers fail at
# clk_fast = 50 MHz and BOTH pass 10/10 at 25 MHz, against a positive control
# that failed 0/10 in the same session. The fault was a setup violation on the
# Padé datapath, not a property of either inverter -- reported Fmax was a poor
# proxy because it describes the worst path, not the path the test exercises.
# See docs/SESSION_HANDOVER_2026-08-04-EVENING.md.
#
# At the RPLU2PADE spin's operating point (A7_CLK_DIV_LOG2=1, clk_fast 25 MHz)
# v2's Fmax cost is immaterial -- v2 builds closed at 35.53 and 40.81 MHz -- so
# the throughput win applies with the penalty absorbed by margin.
#
# The known Fmax exception is seed 59, ~30% SLOWER on a 15.7 ns routing
# critical path: a placement-lottery tail, not noise, so expect it rather than
# diagnose it fresh. The sequential setting selects the one-product backend for
# matched A/B runs and stays default-off (it failed its gate at 1.57x LUT).
FP4_STRUCTURED="${FP4_STRUCTURED:-1}"
FP4_STRUCTURED_SEQUENTIAL="${FP4_STRUCTURED_SEQUENTIAL:-0}"
FP4_BACKEND_SEQUENTIAL="${FP4_BACKEND_SEQUENTIAL:-$FP4_STRUCTURED_SEQUENTIAL}"
FP4_EVIDENCE="${FP4_EVIDENCE:-0}"
A7_SYNTH_ABC9="${A7_SYNTH_ABC9:-0}"
case "$FP4_STRUCTURED:$FP4_STRUCTURED_SEQUENTIAL" in
    0:0|1:0|1:1) ;;
    *) echo "Invalid FP4 selector: FP4_STRUCTURED=$FP4_STRUCTURED FP4_STRUCTURED_SEQUENTIAL=$FP4_STRUCTURED_SEQUENTIAL"; exit 1;;
esac
case "$FP4_BACKEND_SEQUENTIAL:$FP4_EVIDENCE" in
    0:0|0:1|1:0|1:1) ;;
    *) echo "Invalid FP4 evidence selector: backend=$FP4_BACKEND_SEQUENTIAL evidence=$FP4_EVIDENCE"; exit 1;;
esac
case "$A7_SYNTH_ABC9" in
    0|1) ;;
    *) echo "Invalid A7_SYNTH_ABC9: $A7_SYNTH_ABC9 (use 0|1)"; exit 1;;
esac
if [ "$FP4_STRUCTURED_SEQUENTIAL" = "1" ] && [ "$FP4_BACKEND_SEQUENTIAL" != "1" ]; then
    echo "Structured sequential requests require FP4_BACKEND_SEQUENTIAL=1"
    exit 1
fi
# Artifact tagging exists so evaluation runs cannot collide with production
# builds. It must therefore tag whatever is NOT production. This value tracks
# the FP4_STRUCTURED default above and must be changed with it -- it inverted
# on 2026-08-01 when the default moved 0 -> 1, and back on 2026-08-03 when it
# moved 1 -> 0. Getting it wrong does not fail the build: it silently emits
# spu_a7_100t_<SPIN>_FI?B0_S1.bit instead of spu_a7_100t_<SPIN>.bit, which
# breaks every documented build/load path in docs/ and AGENTS.md and bakes the
# burned seed 1 into the production name.
#
# Correct rule: the production configuration gets the canonical name; explicit
# evidence runs and the non-production tower get tagged.
FP4_PRODUCTION_STRUCTURED=1
INVERTER_VARIANT=""
if [ "$FP4_EVIDENCE" = "1" ] || [ "$FP4_STRUCTURED" != "$FP4_PRODUCTION_STRUCTURED" ] \
   || [ "$FP4_BACKEND_SEQUENTIAL" != "0" ]; then
    INVERTER_VARIANT="_FI${FP4_STRUCTURED}B${FP4_BACKEND_SEQUENTIAL}_S${A7_SEED:-1}"
fi
SYNTH_XILINX_FLOW=""
if [ "$A7_SYNTH_ABC9" = "1" ]; then
    INVERTER_VARIANT="${INVERTER_VARIANT}_A9"
    SYNTH_XILINX_FLOW="-abc9"
fi
if [ "$PADE_DEBUG_TRACE" = "1" ]; then
    INVERTER_VARIANT="${INVERTER_VARIANT}_PT1"
fi
# Same rule as _PT1: a non-production datapath option must tag the artifact, or
# an A/B pair silently overwrites itself. On 2026-08-09 an untagged
# PADE_PIPELINED run destroyed its own baseline netlist, log and FASM.
if [ "$PADE_PIPELINED" = "1" ]; then
    INVERTER_VARIANT="${INVERTER_VARIANT}_PP1"
fi
if [ "$PIPELINED_RNS_CHECK" = "1" ]; then
    INVERTER_VARIANT="${INVERTER_VARIANT}_RC1"
fi

# Resolve spin to uppercase
SPIN=$(echo "$SPIN" | tr '[:lower:]' '[:upper:]')
if [ "$PADE_DEBUG_TRACE" = "1" ] && [ "$SPIN" != "RPLU2PADE" ]; then
    echo "PADE_DEBUG_TRACE=1 applies only to RPLU2PADE (spin is $SPIN)"
    exit 1
fi

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
# Distinguish "user asked for this" from "we defaulted it". The rejection below
# is meant to stop a *recorded* setting being silently ignored on a spin that
# cannot honour it -- but applying it to the default made every non-tensegrity
# spin unbuildable, because the default is 1 and only the tensegrity spins
# accept a non-zero value. That broke `build_a7.sh 100t lucas all` and every
# other documented non-tensegrity build command from 2026-07-23 (c1fe58f, which
# moved the default 0 -> 1) until 2026-07-31. It surfaced only when someone next
# tried to rebuild a non-tensegrity spin, which is why it went unnoticed: the
# stale bitstreams on disk kept working for load-only bench sessions.
if [ -n "${ZPHI_KARATSUBA+x}" ]; then
    ZPHI_KARATSUBA_EXPLICIT=1
else
    ZPHI_KARATSUBA_EXPLICIT=0
fi
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
        # Only reject an EXPLICIT non-zero request. A defaulted 1 on a spin that
        # ignores the setting is not a user error and must not block the build.
        if [ "$ZPHI_KARATSUBA_EXPLICIT" = "1" ] && [ "$ZPHI_KARATSUBA" != "0" ]; then
            echo "ZPHI_KARATSUBA=$ZPHI_KARATSUBA applies only to TENSEGRITYPROBE or TENSEGRITYLINK (spin is $SPIN)"
            exit 1
        fi
        # Not applicable to this spin; normalise so it cannot reach an artifact
        # name or a metrics note and imply the option was in effect.
        ZPHI_KARATSUBA=0;;
esac

# A7_CLK_DIV_LOG2 default, spin-aware — mirrors the _CORE ternary in
# spu_a7_top.v (keep this list in sync with that one, EXCEPT for the
# RPLU2PADE exception documented below). Coreless sidecar
# spins (no spu13_core instance) run the raw fabric clock; every
# core-based spin needs clk_fast divided down to the Piranha Pulse
# dispatch cadence or QR telemetry corrupts silently with no synthesis
# or sim-side warning (root-caused in docs/hardware_evidence.md
# §3.2e.4, recurred on the IROTC spin's first build — §3.2k.1). An
# explicit A7_CLK_DIV_LOG2 env var still overrides this default.
#
# RPLU2PADE is the exception among the coreless spins: it defaults to /2
# (clk_fast 25 MHz) since 2026-08-05, because its datapath does not meet 50 MHz
# and fails FUNCTIONALLY there. Measured, campaign 20260805_083400: at 50 MHz
# builds land 0/10 or 10/10 with no correlation to reported Fmax -- a placement
# lottery, because Fmax describes the worst path rather than the path the test
# exercises. At 25 MHz all four measured builds pass 10/10, against a positive
# control that failed 0/10 in the same session. Both inverter towers behave
# identically, so this is the datapath, not the inverter.
#
# The cost is real and must be quoted wherever the Pade pipeline is presented:
# HALF THROUGHPUT for this spin. A correct slow build beats a fast unreliable
# one; the proper fix is to pipeline the Pade datapath, after which this line
# can go back to 0. See docs/SESSION_HANDOVER_2026-08-04-EVENING.md.
case "$SPIN" in
    RPLU2PADE)                             A7_CLK_DIV_LOG2_DEFAULT=1;;
    LUCAS|SU3|RPLUCFG|RPLU2LIVE|SOMPROBE|SOMSIDECAR|TENSEGRITYPROBE|TENSEGRITYLINK) A7_CLK_DIV_LOG2_DEFAULT=0;;
    *)                                     A7_CLK_DIV_LOG2_DEFAULT=6;;
esac
A7_CLK_DIV_LOG2="${A7_CLK_DIV_LOG2:-$A7_CLK_DIV_LOG2_DEFAULT}"

case "$DEVICE_CHIP" in
    35t)
        PART="xc7a35tcsg324-1"; XDC="hardware/boards/artix7/spu_a7_35t.xdc"
        DEVICE_PARAM="A7_35T"
        CHIPDB="build/chipdb/xc7a35t.bin"
        JSON="build/spu_a7_35t_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}.json"
        BITSTREAM="build/spu_a7_35t_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}.bit";;
    100t)
        PART="xc7a100tfgg676-1"; XDC="hardware/boards/artix7/spu_a7_100t.xdc"
        DEVICE_PARAM="A7_100T"
        CHIPDB="build/chipdb/xc7a100tfgg676.bin"
        JSON="build/spu_a7_100t_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}.json"
        BITSTREAM="build/spu_a7_100t_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}.bit";;
    200t)
        PART="xc7a200tsbg484-1"; XDC="hardware/boards/artix7/spu_a7_200t.xdc"
        DEVICE_PARAM="A7_200T"
        CHIPDB="build/chipdb/xc7a200t.bin"
        JSON="build/spu_a7_200t_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}.json"
        BITSTREAM="build/spu_a7_200t_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}.bit";;
    *) echo "Unknown device: $DEVICE_CHIP (use 35t|100t|200t)"; exit 1;;
esac

YS="hardware/boards/artix7/synth_a7.ys"
TOP="spu_a7_top"

if [ "$FP4_BACKEND_SEQUENTIAL" = "1" ]; then
    YS="hardware/boards/artix7/synth_a7_seq.ys"
fi

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
elif [ "$SPIN" = "FP4EVIDENCE" ]; then
    YS="hardware/boards/artix7/synth_a7_fp4_inverter_evidence.ys"
    XDC="hardware/boards/artix7/spu_a7_fp4_inverter_evidence.xdc"
    TOP="spu_a7_fp4_inverter_evidence_top"
fi

echo "=== SPU-13 Artix-7 Build ==="
echo "  Device: $DEVICE_CHIP ($PART)"
echo "  Spin:   $SPIN"
echo "  Step:   $STEP"
echo "  Freq:   ${A7_FREQ} MHz"
echo "  Seed:   ${A7_SEED}"
echo "  ClkDiv: /$((1 << A7_CLK_DIV_LOG2))"
echo "  Fp4Inv: structured=${FP4_STRUCTURED} request-sequential=${FP4_STRUCTURED_SEQUENTIAL} backend-sequential=${FP4_BACKEND_SEQUENTIAL}"
echo "  Trace:  PADE_DEBUG_TRACE=${PADE_DEBUG_TRACE}"
echo "  Pipelined: PADE_PIPELINED=${PADE_PIPELINED} PIPELINED_RNS_CHECK=${PIPELINED_RNS_CHECK}"
echo "  Synth:  abc9=${A7_SYNTH_ABC9}"
echo "  Artifact: ${BITSTREAM}"
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
            synth_xilinx -family xc7 $SYNTH_XILINX_FLOW -top $TOP -json \"$JSON\"; \
            stat -top $TOP"
    elif [ "$SPIN" = "FP4EVIDENCE" ]; then
        yosys -p "script $YS; \
            hierarchy -check -top $TOP \
                      -chparam USE_STRUCTURED $FP4_STRUCTURED \
                      -chparam SEQUENTIAL $FP4_BACKEND_SEQUENTIAL; \
            synth_xilinx -family xc7 $SYNTH_XILINX_FLOW -top $TOP -json \"$JSON\"; \
            stat -top $TOP"
    elif [ "$TOP" != "spu_a7_top" ]; then
        yosys -p "script $YS; \
            synth_xilinx -family xc7 $SYNTH_XILINX_FLOW -top $TOP -json \"$JSON\"; \
            stat -top $TOP"
    else
        yosys -p "script $YS; \
            chparam -set DEVICE \"$DEVICE_PARAM\" \
                    -set SPIN \"$SPIN\" \
                    -set A7_CLK_DIV_LOG2 $A7_CLK_DIV_LOG2 \
                    -set A7_UART_DIAG $A7_UART_DIAG \
                    -set USE_STRUCTURED_INVERTER $FP4_STRUCTURED \
                    -set STRUCTURED_INVERTER_SEQUENTIAL $FP4_STRUCTURED_SEQUENTIAL \
                    -set PADE_DEBUG_TRACE $PADE_DEBUG_TRACE \
                    -set PADE_PIPELINED $PADE_PIPELINED \
                    -set PIPELINED_RNS_CHECK $PIPELINED_RNS_CHECK \
                    spu_a7_top; \
            hierarchy -check -top spu_a7_top; \
            synth_xilinx -family xc7 $SYNTH_XILINX_FLOW -top spu_a7_top -json \"$JSON\"; \
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

    METRICS_NAME="artix7_${DEVICE_CHIP}_${SPIN}${TENSEGRITY_VARIANT}${INVERTER_VARIANT}"
    METRICS_NOTE="A7_FREQ=${A7_FREQ} MHz; A7_SEED=${A7_SEED}; FP4_STRUCTURED=${FP4_STRUCTURED}; FP4_BACKEND_SEQUENTIAL=${FP4_BACKEND_SEQUENTIAL}; PADE_DEBUG_TRACE=${PADE_DEBUG_TRACE}; post-route metrics from nextpnr-xilinx."
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
        echo "  xc7frames2bit not found. Source the toolchain first:"
        echo "    source tools/env_openxc7.sh"
        echo "  (This adds \$OPENXC7_ROOT/bin to PATH; default ~/.local/openxc7.)"
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
        elif [ -f "$HOME/toolchains/prjxray/utils/fasm2frames.py" ]; then
            # Bench default. Discovery previously required PRJXRAY_ROOT to be
            # exported, so `pack` failed on this machine with "Missing
            # fasm2frames.py" despite a complete install being present.
            FASM2FRAMES="$HOME/toolchains/prjxray/utils/fasm2frames.py"
        fi
    fi

    # fasm2frames.py needs the `fasm` and `textx` modules, which live in a
    # dedicated venv rather than the system interpreter. Without this, packing
    # fails with ModuleNotFoundError even after fasm2frames.py itself is found.
    # An explicit OPENXC7_PYTHON always wins.
    if [ "$OPENXC7_PYTHON" = "python3" ] \
       && [ -x "$HOME/.local/venvs/prjxray/bin/python" ] \
       && ! python3 -c "import fasm" >/dev/null 2>&1; then
        OPENXC7_PYTHON="$HOME/.local/venvs/prjxray/bin/python"
    fi

    # fasm2frames.py also imports the `prjxray` package from its own checkout
    # root, which is not installed into any interpreter. Put that root on
    # PYTHONPATH when the script we resolved lives inside one; without it
    # packing fails with "No module named 'prjxray'" after clearing the `fasm`
    # import.
    if [ -n "$FASM2FRAMES" ]; then
        _f2f_root="$(cd "$(dirname "$FASM2FRAMES")/.." && pwd)"
        if [ -d "$_f2f_root/prjxray" ]; then
            case ":${PYTHONPATH:-}:" in
                *":$_f2f_root:"*) ;;
                *) export PYTHONPATH="$_f2f_root${PYTHONPATH:+:$PYTHONPATH}" ;;
            esac
        fi
        unset _f2f_root
    fi

    [ -f "$FASM" ] || { echo "Missing routed FASM: $FASM"; exit 1; }
    [ -f "$JSON" ] || { echo "Missing synthesized JSON: $JSON"; exit 1; }
    [ "$FASM" -nt "$JSON" ] || {
        echo "Stale routed FASM: $FASM"
        echo "It is not newer than its synthesized JSON: $JSON"
        echo "Rerun the pnr step before packing."
        exit 1
    }
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
