# rtl0c_route.tcl — RTL-0C gate C3, stage 2: opt, place and route of the stage-1 checkpoint, default directives
# only (no phys_opt, no retries). One run of this script is one route attempt of the D7 budget.
# usage: vivado -mode batch -source rtl0c_route.tcl -tclargs REPO_ROOT SYNTH_DCP OUT_DIR
# Fails (after writing every report) if routing has errors or any of setup, hold, recovery or removal slack
# is not positive, or a structural or pin check no longer holds. Tool reports, not measurements.
set root [lindex $argv 0]; set dcp [lindex $argv 1]; set out [lindex $argv 2]
file mkdir $out
source [file join $root hardware/boards/artix7/psurd_rtl0c/rtl0c_checks.tcl]
open_checkpoint $dcp
opt_design
place_design
report_utilization -file [file join $out util_placed.rpt]
route_design
write_checkpoint -force [file join $out routed.dcp]
report_route_status -file [file join $out route_status.rpt]
report_timing_summary -delay_type min_max -max_paths 20 -report_unconstrained -file [file join $out timing_summary_routed.rpt]
report_timing -setup -max_paths 20 -sort_by slack -file [file join $out timing_setup_paths.rpt]
report_timing -hold -max_paths 20 -sort_by slack -file [file join $out timing_hold_paths.rpt]
set rp [get_pins -quiet -hierarchical -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
report_timing -delay_type max -to $rp -max_paths 50 -file [file join $out timing_recovery_paths.rpt]
report_timing -delay_type min -to $rp -max_paths 50 -file [file join $out timing_removal_paths.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
report_clocks -file [file join $out clocks.rpt]
report_clock_utilization -file [file join $out clock_utilization.rpt]
report_clock_interaction -file [file join $out clock_interaction.rpt]
report_drc -file [file join $out drc_routed.rpt]
report_methodology -file [file join $out methodology_routed.rpt]
report_utilization -hierarchical -hierarchical_depth 5 -file [file join $out util_hier_routed.rpt]
report_io -file [file join $out io.rpt]
set s(wns) [get_property SLACK [get_timing_paths -max_paths 1 -setup]]
set s(whs) [get_property SLACK [get_timing_paths -max_paths 1 -hold]]
set s(recovery) [get_property SLACK [get_timing_paths -max_paths 1 -delay_type max -to $rp]]
set s(removal)  [get_property SLACK [get_timing_paths -max_paths 1 -delay_type min -to $rp]]
set s(route_errors) [llength [get_nets -quiet -hierarchical -filter {ROUTE_STATUS == CONFLICTS || ROUTE_STATUS == UNROUTED}]]
foreach {k filt} {bram {PRIMITIVE_GROUP == BMEM} dsp {PRIMITIVE_GROUP == MULT} lutram_cells {PRIMITIVE_GROUP == DMEM}
                  latch {PRIMITIVE_SUBGROUP == latch} bbox {IS_BLACKBOX == 1} bufg {REF_NAME == BUFG}} {
  set s($k) [llength [get_cells -quiet -hierarchical -filter $filt]]
}
set f [open [file join $out timing_routed.txt] w]
foreach k {wns whs recovery removal route_errors bram dsp lutram_cells latch bbox bufg} { puts $f "$k $s($k)" }
close $f
rtl0c_structure routed $out
rtl0c_pins routed $out
foreach k {wns whs recovery removal} {
  if {$s($k) eq "" || $s($k) <= 0} { error "RTL-0C HOLD: $k slack is not positive ($s($k))" }
}
if {$s(route_errors) != 0 || $s(latch) != 0 || $s(bbox) != 0} { error "RTL-0C HOLD: route errors, latches or black boxes present" }
