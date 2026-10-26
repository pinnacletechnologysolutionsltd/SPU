# Phase 2 environment smoke test (needs a Vivado installation). Reads NO design, runs NO synthesis/implementation, touches no hardware.
#   vivado -mode batch -source tools/vivado/tests/phase2_smoke.tcl
puts "version: [version]"
set part xc7a100tfgg676-1
set p [get_parts -quiet $part]
puts "part_found: [expr {[llength $p] == 1}]  ($part)"
if {[llength $p] == 1} { foreach prop {FAMILY DEVICE PACKAGE SPEED} { puts "  $prop = [get_property $prop $p]" } }
set missing {}
foreach c {read_verilog read_xdc synth_design opt_design place_design route_design report_utilization report_clocks report_clock_networks check_timing report_timing_summary report_cdc report_methodology report_drc report_route_status write_checkpoint get_parts get_clocks get_cells create_generated_clock} {
    if {[llength [info commands $c]] == 0} { lappend missing $c }
}
puts "commands_missing: [expr {[llength $missing] ? $missing : {none}}]"
set opts_missing {}
foreach {cmd opt} {synth_design -include_dirs synth_design -verilog_define synth_design -generic synth_design -top synth_design -part check_timing -verbose check_timing -file report_timing_summary -delay_type report_timing_summary -max_paths write_checkpoint -force} {
    set h [expr {[catch {help $cmd} txt] ? "" : $txt}]
    if {[string first $opt $h] < 0} { lappend opts_missing "$cmd $opt" }
}
puts "options_not_found_in_help: [expr {[llength $opts_missing] ? $opts_missing : {none}}]"
set f [open [file join [file dirname [file normalize [info script]]] .. spu_vivado_flow.tcl]] ; set s [read $f] ; close $f
puts "flow_script_syntax_balanced: [info complete $s]"
exit 0
