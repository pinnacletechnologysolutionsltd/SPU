#!/usr/bin/env bash
# CPU-BOARD-3 Phase P: one opt/place/route on the frozen Phase S checkpoint under the memory guard (exit 97 = resource termination = HOLD), then read-only analysis.
G=/home/john/.local/gate/spu-int3b-c3efc18; R=/home/john/spu-public-v0.2-rc2; B=$G/build/vivado/board3p_01; X=$G/experiment/cpu-board-3; P=$G/experiment/cpu-board-3p
CK=$G/build/vivado/board3_01/synth/synth.dcp; CKSHA=938f0772eb82f5f4bcbdb33def00b4363b11bfdb8749a257d592aab2ffd42f20
cd $G || exit 90
avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$avail" -ge 5242880 ] || { echo "LAUNCH_MEMORY_HOLD avail_kb=$avail" > $B/meta/launch_hold.txt; exit 96; }
[ "$(sha256sum $CK | cut -c1-64)" = "$CKSHA" ] || { echo "CHECKPOINT_IDENTITY_HOLD" > $B/meta/launch_hold.txt; exit 95; }
( head -12 $X/PREFLIGHT.sha256 | sha256sum -c - ) > $B/meta/preflight_verify.txt 2>&1 || { echo "SOURCE_IDENTITY_HOLD" > $B/meta/launch_hold.txt; exit 94; }
[ "$(df -k --output=avail /home/john | tail -1)" -ge 20971520 ] || { echo "DISK_HOLD" > $B/meta/launch_hold.txt; exit 93; }
if ! (set -o noclobber; date -u +%FT%TZ > $B/meta/STARTED); then echo 'attempt already started; refusing'; exit 98; fi
source /home/john/2026.1/Vivado/settings64.sh
source $X/guard.sh
{ date -u +%FT%TZ; free -m; cat /proc/pressure/memory; uname -r; } > $B/meta/host_before.txt 2>&1
/usr/bin/time -v -o $B/meta/time_v.txt vivado -mode batch -log $B/route/vivado.log -journal $B/route/vivado.jou -source $P/route_phase_p.tcl -tclargs $B/route &
VPID=$!
guard_loop $VPID $B/meta/rss_samples.csv $B/meta; rc=$?
if [ $rc -eq 97 ]; then echo "vivado_exit=97 (guard)" > $B/meta/vivado_exit.txt; exit 97; fi
wait $VPID; rc=$?
echo "vivado_exit=$rc" > $B/meta/vivado_exit.txt; { date -u +%FT%TZ; free -m; } > $B/meta/host_after.txt 2>&1
[ $rc -eq 0 ] || exit $rc
mkdir -p $B/analysis; A=$B/analysis
( cd $A && vivado -mode batch -nojournal -log dump_rom.log -source $X/dump_rom.tcl -tclargs $B/route/routed.dcp $A/rom_props.txt > /dev/null 2>&1; echo "dump_rom_rc=$?" > analysis_rc.txt
  vivado -mode batch -nojournal -log dump_loads.log -source $X/dump_rom_loads.tcl -tclargs $B/route/routed.dcp $A/rom_loads.txt > /dev/null 2>&1; echo "dump_loads_rc=$?" >> analysis_rc.txt
  python3 -I $X/rom_check.py $A/rom_props.txt $A/rom_loads.txt $G/experiment/cpu-integrate-4/frontend.v $R/build/cpu-board-2r-isolated/board_tb.v $A/rom_check.txt > /dev/null 2>&1; echo "rom_check_rc=$?" >> analysis_rc.txt ) || true
exit 0
