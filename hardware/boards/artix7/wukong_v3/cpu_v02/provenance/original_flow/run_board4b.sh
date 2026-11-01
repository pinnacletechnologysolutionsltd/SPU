#!/usr/bin/env bash
# CPU-BOARD-4B: exactly one Vivado 2026.1 write_bitstream invocation on the frozen routed checkpoint under the memory guard (exit 97 = resource termination = HOLD). No programming.
G=/home/john/.local/gate/spu-int3b-c3efc18; R=/home/john/spu-public-v0.2-rc2; P=$G/build/vivado/board3p_01; B=$G/build/vivado/board4b_01; X=$G/experiment/cpu-board-4b; XP=$G/experiment/cpu-board-3p; X3=$G/experiment/cpu-board-3
CK=$P/route/routed.dcp; CKSHA=48e0e1613a76315592852d8462bf2f91680c2ed87bfa5575ea690a941988a5c8; M=$B/meta
hold() { echo "$2" > $M/launch_hold.txt; exit $1; }
cd $G || exit 90
avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$avail" -ge 5242880 ] || hold 96 "MEMORY_HOLD avail_kb=$avail"
[ "$(df -k --output=avail /home/john | tail -1)" -ge 20971520 ] || hold 93 DISK_HOLD
[ "$(sha256sum $CK | cut -c1-64)" = "$CKSHA" ] || hold 95 CHECKPOINT_IDENTITY_HOLD
( cd $P && head -32 meta/OUTPUT_SHA256.txt | sha256sum -c - ; cd $R/build/cpu-board-3-route-01 && tail -6 $P/meta/OUTPUT_SHA256.txt | sha256sum -c - ; cd $XP && sha256sum -c PREFLIGHT_P.sha256 ) > $M/preflight_verify.txt 2>&1 || hold 94 EVIDENCE_IDENTITY_HOLD
[ "$(grep -cE 'H7 STD=LVCMOS33 PULL=PULLUP|PIN=M21 STD=LVCMOS33|PIN=E3 STD=LVCMOS33|PORT_COUNT 3|CFGBVS VCCO CONFIG_VOLTAGE 3.3' $P/route/ports.txt)" = 5 ] || hold 92 PORT_PROPERTY_HOLD
[ "$(grep -v '^\s*#' $X3/cpu_board_3.xdc | grep -cE 'false_path|input_delay|output_delay|max_delay|min_delay|clock_groups|multicycle|waiver')" = 0 ] || hold 91 EXCEPTION_HOLD
[ ! -e $B/bit ] || hold 89 OUTPUT_EXISTS_HOLD
pgrep -f "[v]ivado -mode" > /dev/null && hold 88 CONFLICTING_VIVADO_HOLD
if ! (set -o noclobber; date -u +%FT%TZ > $M/STARTED); then echo 'attempt already started; refusing'; exit 98; fi
source /home/john/2026.1/Vivado/settings64.sh
source $X3/guard.sh
{ sha256sum $CK $G/build/vivado/board3_01/synth/synth.dcp; stat -c '%n %Y %s' $CK; vivado -version | head -1; sha256sum $X/gen_bitstream.tcl $X/bit_check.py $X/run_board4b.sh $X3/guard.sh; } > $M/identities_before.txt 2>&1
{ date -u +%FT%TZ; free -m; cat /proc/pressure/memory; uname -r; } > $M/host_before.txt 2>&1
mkdir -p $B/log
/usr/bin/time -v -o $M/time_v.txt vivado -mode batch -log $B/log/vivado.log -journal $B/log/vivado.jou -source $X/gen_bitstream.tcl -tclargs $B/bit &
VPID=$!
guard_loop $VPID $M/rss_samples.csv $M; rc=$?
if [ $rc -eq 97 ]; then echo "vivado_exit=97 (guard)" > $M/vivado_exit.txt; exit 97; fi
wait $VPID; rc=$?
echo "vivado_exit=$rc" > $M/vivado_exit.txt; { date -u +%FT%TZ; free -m; } > $M/host_after.txt 2>&1
[ $rc -eq 0 ] || exit $rc
A=$B/analysis; mkdir -p $A
( sha256sum $B/bit/cpu_board_2r_top.bit $B/bit/cpu_board_2r_top.bin; stat -c '%n %s' $B/bit/cpu_board_2r_top.bit $B/bit/cpu_board_2r_top.bin ) > $A/output_hashes.txt 2>&1
python3 -I $X/bit_check.py $B/bit/cpu_board_2r_top.bit $B/bit/cpu_board_2r_top.bin $A/bit_check.txt > /dev/null 2>&1; echo "bit_check_rc=$?" > $A/analysis_rc.txt
{ sha256sum $CK $G/build/vivado/board3_01/synth/synth.dcp; stat -c '%n %Y %s' $CK; } > $M/identities_after.txt 2>&1
( cd $P && head -32 meta/OUTPUT_SHA256.txt | sha256sum -c - ) > $M/post_verify.txt 2>&1; echo "post_verify_rc=$?" >> $A/analysis_rc.txt
ls -la $B/bit > $A/bit_dir_listing.txt 2>&1; find $G/build/vivado -newer $M/STARTED -type f -not -path "$B/*" > $A/files_modified_outside_output.txt 2>&1
exit 0
