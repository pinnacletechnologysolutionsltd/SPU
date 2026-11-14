# rtl0p_impl.tcl — RTL-0P bounded place-and-route of the RTL-0S synthesized core (no RTL change).
# usage: vivado -mode batch -source rtl0p_impl.tcl -tclargs REPO_ROOT SYNTH_DCP OUT_DIR
# Default flow only: opt_design, place_design, route_design (no phys_opt, no directives, no retries).
# Out-of-context: the clock is modelled from a global buffer (HD.CLK_SRC). Ports have no I/O delay
# constraints, so port-to-register paths are unconstrained by design; the timing scope is internal
# register-to-register paths on clk (40.000 ns). Not a board-level timing qualification.
set root [lindex $argv 0]; set dcp [lindex $argv 1]; set out [lindex $argv 2]
file mkdir $out
open_checkpoint $dcp
set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports clk]
opt_design
place_design
report_utilization -file [file join $out util_placed.rpt]
route_design
write_checkpoint -force [file join $out routed.dcp]
report_route_status -file [file join $out route_status.rpt]
report_timing_summary -max_paths 20 -report_unconstrained -file [file join $out timing_summary_routed.rpt]
report_timing -setup -max_paths 20 -sort_by slack -file [file join $out timing_setup_paths.rpt]
report_timing -hold -max_paths 20 -sort_by slack -file [file join $out timing_hold_paths.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
report_clock_utilization -file [file join $out clock_utilization.rpt]
report_drc -file [file join $out drc_routed.rpt]
report_methodology -file [file join $out methodology_routed.rpt]
report_utilization -hierarchical -hierarchical_depth 4 -file [file join $out util_hier_routed.rpt]
set f [open [file join $out placement_dsp_bram.txt] w]
foreach c [get_cells -hierarchical -filter {PRIMITIVE_GROUP == MULT || PRIMITIVE_GROUP == BMEM}] {
  puts $f "[get_property PRIMITIVE_GROUP $c] [get_property LOC $c] $c"
}
close $f
source [file join $root hardware/boards/artix7/psurd_rtl0s/rtl0s_structure.tcl]
rtl0s_structure [file join $out structure_routed.txt]
set f [open [file join $out timing_routed.txt] w]
puts $f "wns [get_property SLACK [get_timing_paths -max_paths 1 -setup]]"
puts $f "whs [get_property SLACK [get_timing_paths -max_paths 1 -hold]]"
puts $f "route_errors [llength [get_nets -quiet -hierarchical -filter {ROUTE_STATUS == CONFLICTS || ROUTE_STATUS == UNROUTED}]]"
close $f
