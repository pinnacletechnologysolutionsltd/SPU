#!/usr/bin/env bash
# CPU-BOARD-3 Phase S: exactly one Vivado 2026.1 synthesis-only invocation under the memory guard (exit 97 = resource termination = HOLD),
# followed by read-only checkpoint analysis (no second synthesis). Requires >= 5 GiB MemAvailable at launch.
G=/home/john/.local/gate/spu-int3b-c3efc18; B=$G/build/vivado/board3_01; X=$G/experiment/cpu-board-3
cd $G || exit 90
avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$avail" -ge 5242880 ] || { echo "LAUNCH_MEMORY_HOLD avail_kb=$avail" > $B/meta/launch_hold.txt; exit 96; }
if ! (set -o noclobber; date -u +%FT%TZ > $B/meta/STARTED); then echo 'attempt already started; refusing'; exit 98; fi
source /home/john/2026.1/Vivado/settings64.sh
source $X/guard.sh
{ date -u +%FT%TZ; free -m; cat /proc/pressure/memory; uname -r; } > $B/meta/host_before.txt 2>&1
/usr/bin/time -v -o $B/meta/time_v.txt vivado -mode batch -log $B/synth/vivado.log -journal $B/synth/vivado.jou -source $X/wrap.tcl -tclargs \
  -top cpu_board_2r_top -part xc7a100tfgg676-1 -filelist experiment/cpu-board-3/candidate.f \
  -xdc experiment/cpu-board-3/cpu_board_3.xdc -outdir $B/synth -expect_clock sys_clk:20.000 -expect_clock cpu_clk:40.000 &
VPID=$!
guard_loop $VPID $B/meta/rss_samples.csv $B/meta; rc=$?
if [ $rc -eq 97 ]; then echo "vivado_exit=97 (guard)" > $B/meta/vivado_exit.txt; exit 97; fi
wait $VPID; rc=$?
echo "vivado_exit=$rc" > $B/meta/vivado_exit.txt; { date -u +%FT%TZ; free -m; } > $B/meta/host_after.txt 2>&1
[ $rc -eq 0 ] || exit $rc
mkdir -p $B/analysis; A=$B/analysis
( cd $A && vivado -mode batch -nojournal -log structure.log -source $X/structure_check.tcl -tclargs $B/synth/synth.dcp $A > /dev/null 2>&1; echo "structure_rc=$?" > analysis_rc.txt
  vivado -mode batch -nojournal -log dump_rom.log -source $X/dump_rom.tcl -tclargs $B/synth/synth.dcp $A/rom_props.txt > /dev/null 2>&1; echo "dump_rom_rc=$?" >> analysis_rc.txt
  vivado -mode batch -nojournal -log dump_loads.log -source $X/dump_rom_loads.tcl -tclargs $B/synth/synth.dcp $A/rom_loads.txt > /dev/null 2>&1; echo "dump_loads_rc=$?" >> analysis_rc.txt
  python3 -I $X/rom_check.py $A/rom_props.txt $A/rom_loads.txt $G/experiment/cpu-integrate-4/frontend.v /home/john/spu-public-v0.2-rc2/build/cpu-board-2r-isolated/board_tb.v $A/rom_check.txt > /dev/null 2>&1; echo "rom_check_rc=$?" >> analysis_rc.txt ) || true
exit 0
