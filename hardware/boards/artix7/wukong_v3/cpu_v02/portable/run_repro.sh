#!/usr/bin/env bash
# CPU-REPRO-1 portable build: synthesis -> route -> bitstream as three separate Vivado 2026.1 invocations, mirroring the original
# CPU-BOARD-3 Phase S / Phase P / CPU-BOARD-4B hand-off through checkpoints. NO programming. Usage: run_repro.sh RUN_ID
# Launch (detached; AGENTS.md 4.2):
#   VIVADO_SETTINGS=/path/to/settings64.sh tools/run_detached_job.sh --output build/cpu-repro-1/<RUN_ID>-job --timeout <frozen-seconds> -- \
#     bash hardware/boards/artix7/wukong_v3/cpu_v02/portable/run_repro.sh <RUN_ID>
set -u
RUN_ID=${1:?usage: run_repro.sh RUN_ID}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); PKG=$(cd "$HERE/.." && pwd); REPO=$(cd "$PKG/../../../../.." && pwd)
REL=${PKG#"$REPO"/}; cd "$REPO" || exit 90
bash "$HERE/preflight.sh" "$RUN_ID" || exit $?
B=$REPO/build/cpu-repro-1/$RUN_ID; M=$B/meta
mkdir -p "$B"/{synth,route,bit,meta,analysis,work} || exit 98
( set -o noclobber; date -u +%FT%TZ > "$M/STARTED" ) || exit 98
source "$VIVADO_SETTINGS" > /dev/null 2>&1
source "$PKG/provenance/original_flow/guard.sh"          # byte-identical to the original memory guard
{ date -u +%FT%TZ; free -m; cat /proc/pressure/memory; uname -r; git rev-parse HEAD; git status --porcelain | sha256sum; } > "$M/host_before.txt" 2>&1
( cd "$PKG" && sha256sum -c PACKAGE_SHA256.txt; sha256sum -c portable/PORTABLE_SHA256.txt ) > "$M/package_verify.txt" 2>&1
run_phase() {   # name, then the vivado -source script and its -tclargs
  local name=$1; shift
  /usr/bin/time -v -o "$M/time_v_$name.txt" vivado -mode batch -log "$B/$name/vivado.log" -journal "$B/$name/vivado.jou" "$@" &
  local vpid=$!
  guard_loop $vpid "$M/rss_$name.csv" "$M"; local rc=$?
  [ $rc -eq 97 ] && { echo "vivado_exit=97 (guard) phase=$name" > "$M/vivado_exit_$name.txt"; exit 97; }
  wait $vpid; rc=$?; echo "vivado_exit=$rc" > "$M/vivado_exit_$name.txt"; [ $rc -eq 0 ] || exit $rc
}
cd "$B/work" || exit 90      # Vivado writes clockInfo.txt/journals into its cwd; keep them out of the checkout
# Phase S (original: run_board3.sh)
run_phase synth -source "$HERE/synth_wrap.tcl" -tclargs -top cpu_board_2r_top -part xc7a100tfgg676-1 \
  -filelist "$REL/filelists/candidate_portable.f" -xdc "$REL/constraints/cpu_board_3.xdc" -outdir "$B/synth" \
  -expect_clock sys_clk:20.000 -expect_clock cpu_clk:40.000
[ -f "$B/synth/COMPLETE" ] && [ ! -f "$B/synth/FAILED" ] || exit 91
( cd "$B/analysis" && vivado -mode batch -nojournal -log structure.log -source "$PKG/provenance/original_flow/structure_check.tcl" -tclargs "$B/synth/synth.dcp" "$B/analysis" > /dev/null 2>&1; echo "structure_rc=$?" > analysis_rc.txt
  vivado -mode batch -nojournal -log dump_rom.log -source "$PKG/provenance/original_flow/dump_rom.tcl" -tclargs "$B/synth/synth.dcp" "$B/analysis/synth_rom_props.txt" > /dev/null 2>&1; echo "synth_dump_rom_rc=$?" >> analysis_rc.txt
  vivado -mode batch -nojournal -log dump_loads.log -source "$PKG/provenance/original_flow/dump_rom_loads.tcl" -tclargs "$B/synth/synth.dcp" "$B/analysis/synth_rom_loads.txt" > /dev/null 2>&1; echo "synth_dump_loads_rc=$?" >> analysis_rc.txt )
# Phase P (original: run_board3p.sh; no hash gate on the new synth checkpoint, it is compared afterwards)
run_phase route -source "$HERE/route.tcl" -tclargs "$B/route" "$B/synth/synth.dcp"
( cd "$B/analysis" && vivado -mode batch -nojournal -log dump_rom_r.log -source "$PKG/provenance/original_flow/dump_rom.tcl" -tclargs "$B/route/routed.dcp" "$B/analysis/route_rom_props.txt" > /dev/null 2>&1; echo "route_dump_rom_rc=$?" >> analysis_rc.txt
  vivado -mode batch -nojournal -log dump_loads_r.log -source "$PKG/provenance/original_flow/dump_rom_loads.tcl" -tclargs "$B/route/routed.dcp" "$B/analysis/route_rom_loads.txt" > /dev/null 2>&1; echo "route_dump_loads_rc=$?" >> analysis_rc.txt )
# Phase 4B (original: run_board4b.sh): write_bitstream only
run_phase bit -source "$HERE/bitstream.tcl" -tclargs "$B/bit/out" "$B/route/routed.dcp"
( cd "$B" && sha256sum synth/synth.dcp route/routed.dcp bit/out/cpu_board_2r_top.bit bit/out/cpu_board_2r_top.bin ) > "$M/output_hashes.txt" 2>&1
{ date -u +%FT%TZ; free -m; } > "$M/host_after.txt" 2>&1
python3 -I "$HERE/compare.py" "$B" > "$B/COMPARE_RESULT.txt" 2>&1; echo "compare_rc=$?" > "$M/compare_rc.txt"
exit 0
