# Read-only post-synthesis inventory; invoke separately with checkpoint and NEW directory.
# This produces evidence for review, not a proof of functional dependence.
if {$argc != 2} {error "usage: vivado -mode batch -source inspect_synth.tcl -tclargs checkpoint output_dir"}
lassign $argv checkpoint out
set root [file normalize [file join [file dirname [info script]] ../..]]
set build [file normalize [file join $root build]]
set out [file normalize $out]
if {![string match "${build}/*" $out]} {error "output must be a new build/ child"}
if {[file exists $out]} {error "output directory exists"}
file mkdir $out
open_checkpoint $checkpoint
set f [open [file join $out cells.txt] w]
foreach c [get_cells -hierarchical -filter {IS_PRIMITIVE}] {puts $f "[get_property NAME $c] [get_property REF_NAME $c]"}
close $f
set f [open [file join $out ports.txt] w]
foreach p [get_ports] {puts $f "[get_property NAME $p] [get_property DIRECTION $p] [get_property PACKAGE_PIN $p]"}
close $f
set f [open [file join $out instruction_paths.tsv] w]
proc named_pin {name} {get_pins -quiet -hierarchical -filter [format {NAME == "%s"} $name]}
proc paths {f label pinname} {
 set p [named_pin $pinname]
 if {[llength $p] != 1} {puts $f "$label\tMISSING_OR_AMBIGUOUS\t$p";return}
 set roots [all_fanin -quiet -flat -startpoints_only -to $p]
 set names {};foreach x $roots {lappend names [get_property NAME $x]}
 puts $f "$label\tOK\t[join $names ,]"
}
# Record all supported payload paths: each of six load words, two banks,
# and 32 variable bits. Names or optimized storage may require manual review.
foreach bank {0 1} {
 for {set word 0} {$word < 6} {incr word} {
  for {set bit 8} {$bit < 40} {incr bit} {
   paths $f "bank,$bank,$word,$bit" [format {board/cpu/cpu/banks/bank%d_reg[%d][%d]/D} $bank $word $bit]
  }
 }
}
for {set bit 0} {$bit < 64} {incr bit} {
 paths $f "fetch,$bit" [format {board/cpu/cpu/banks/fetch_data_reg[%d]/D} $bit]
 paths $f "held,$bit" [format {board/cpu/cpu/held_word_reg[%d]/D} $bit]
}
# Capture each sequential stage of the serial input path; startpoint tracing
# stops at flops, so cross-cycle functional propagation is reviewed separately.
for {set bit 0} {$bit < 8} {incr bit} {
 paths $f "rx_shift,$bit" [format {board/link/rx/shift_reg[%d]/D} $bit]
 paths $f "rx_data,$bit" [format {board/link/rx/data_reg[%d]/D} $bit]
}
for {set bit 0} {$bit < 72} {incr bit} {
 paths $f "parser_payload,$bit" [format {board/link/adapter/payload_reg[%d]/D} $bit]
 paths $f "request_payload,$bit" [format {board/link/adapter/req_payload_reg[%d]/D} $bit]
}
for {set bit 0} {$bit < 192} {incr bit} {
 paths $f "result,$bit" [format {board/cpu/cpu/result_reg[%d]/D} $bit]
}
close $f
report_utilization -hierarchical -file [file join $out utilization_hierarchical.rpt]
report_cdc -details -file [file join $out cdc.rpt]
set f [open [file join $out INSPECTION_FINISHED] w];puts $f "Raw fan-in evidence only; review missing pins and signal roots.";close $f
exit
