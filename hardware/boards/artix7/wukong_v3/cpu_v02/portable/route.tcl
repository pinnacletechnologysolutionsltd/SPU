# CPU-BOARD-3 Phase P: one place-and-route attempt on the frozen Phase S checkpoint. Adds NO constraints or exceptions. argv0 = out dir.
set_param general.maxThreads 2
set out [lindex $argv 0]
proc check_async {phase out} {
 set chan [open "$out/async_${phase}.txt" w]; set count 0; set unsafe 0; set pk 0
 foreach cell [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
  foreach pin [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}] {
   incr count
   set nets [get_nets -quiet -segments -of_objects $pin]
   set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
   puts $chan "PIN=$pin TYPE=[get_property REF_NAME $cell] DRIVERS=$drivers"
   if {[string first "packet/" $pin] == 0} { puts $chan "HOLD packetizer async pin"; incr pk }
   if {[llength $drivers] != 1} { puts $chan "HOLD ambiguous driver"; incr unsafe; continue }
   foreach obj [all_fanin -quiet -flat -to $pin] {
    if {[get_property CLASS $obj] ne "pin"} { continue }
    set cc [get_cells -quiet -of_objects $obj]
    if {[llength $cc] != 1} { continue }
    if {[regexp {^LUT([2-6])$} [get_property REF_NAME $cc]]} { puts $chan "HOLD multi-input async logic $cc"; incr unsafe }
   }
  }
 }
 puts $chan "COUNT=$count UNSAFE=$unsafe PACKETIZER_ASYNC_PINS=$pk"; close $chan
 if {$count == 0 || $unsafe != 0 || $pk != 0} { error "RESET HOLD: incomplete, multi-input or packetizer async-reset structure at $phase" }
}
open_checkpoint [lindex $argv 1]
if {[llength [get_ports]] != 3} { error "HOLD: expected exactly 3 ports" }
foreach {c p} {sys_clk 20.000 cpu_clk 40.000} { set cl [get_clocks -quiet $c]; if {[llength $cl] != 1 || abs([get_property PERIOD $cl] - $p) > 1e-6} { error "HOLD: clock $c missing or wrong period" } }
check_async pre_opt $out
opt_design
check_async post_opt $out
place_design
check_async placed $out
route_design
check_async routed $out
write_checkpoint -force "$out/routed.dcp"
report_route_status -file "$out/routed_route_status.rpt"
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file "$out/routed_timing_summary.rpt"
report_methodology -file "$out/routed_methodology.rpt"
report_drc -file "$out/routed_drc.rpt"
report_cdc -details -file "$out/routed_cdc.rpt"
report_clock_interaction -file "$out/routed_clock_interaction.rpt"
report_clocks -file "$out/routed_clocks.rpt"
report_clock_networks -file "$out/routed_clock_networks.rpt"
report_utilization -file "$out/routed_utilization.rpt"
report_utilization -hierarchical -file "$out/routed_utilization_hier.rpt"
set rp [get_pins -quiet -hierarchical -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
if {[llength $rp] == 0} { error "RESET HOLD: no async reset endpoints for timing report" }
report_timing -delay_type min -to $rp -max_paths 100 -nworst 3 -path_type full_clock_expanded -file "$out/routed_reset_removal.rpt"
report_timing -delay_type max -to $rp -max_paths 100 -nworst 3 -path_type full_clock_expanded -file "$out/routed_reset_recovery.rpt"
report_timing -delay_type min -max_paths 5 -path_type full_clock_expanded -file "$out/routed_hold_worst.rpt"
catch {
set f [open "$out/ports.txt" w]
foreach p [get_ports] { puts $f "PORT [get_property NAME $p] DIR=[get_property DIRECTION $p] PIN=[get_property PACKAGE_PIN $p] STD=[get_property IOSTANDARD $p] PULL=[get_property PULLTYPE $p]" }
puts $f "PORT_COUNT [llength [get_ports]]"; puts $f "CFGBVS [get_property CFGBVS [current_design]] CONFIG_VOLTAGE [get_property CONFIG_VOLTAGE [current_design]]"; close $f
}
catch {
set f [open "$out/tx_chain.txt" w]
set d [get_pins -leaf -of_objects [get_nets uart_tx] -filter {DIRECTION == OUT}]; set ob [get_cells -of_objects $d]
puts $f "OBUF [get_property NAME $ob] ref=[get_property REF_NAME $ob]"
foreach dd [get_pins -leaf -of_objects [get_nets -of_objects [get_pins -of_objects $ob -filter {REF_PIN_NAME == I}]] -filter {DIRECTION == OUT}] { puts $f "OBUF_I_DRIVER $dd ref=[get_property REF_NAME [get_cells -of_objects $dd]]" }
close $f
}
catch {
set f [open "$out/asyncreg.txt" w]
foreach c [get_cells -hierarchical -filter {NAME =~ *packet/rs_reg*}] { puts $f "CELL $c ref=[get_property REF_NAME $c] ASYNC_REG=[get_property ASYNC_REG $c]" }
close $f
}
puts "BOARD3_PHASE_P_REPORTS_COMPLETE"
exit
