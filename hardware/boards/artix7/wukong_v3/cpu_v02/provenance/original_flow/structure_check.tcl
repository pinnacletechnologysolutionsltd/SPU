# Read-only structural analysis of the Phase S checkpoint (argv0 = synth.dcp, argv1 = output dir). Pre-placement estimates only.
open_checkpoint [lindex $argv 0]
set out [lindex $argv 1]
set f [open "$out/ports.txt" w]
foreach p [get_ports] { puts $f "PORT [get_property NAME $p] DIR=[get_property DIRECTION $p] PIN=[get_property PACKAGE_PIN $p] STD=[get_property IOSTANDARD $p] PULL=[get_property PULLTYPE $p]" }
puts $f "PORT_COUNT [llength [get_ports]]"
puts $f "CFGBVS [get_property CFGBVS [current_design]] CONFIG_VOLTAGE [get_property CONFIG_VOLTAGE [current_design]]"
close $f
set f [open "$out/async_inventory.txt" w]; set count 0; set unsafe 0; set pk 0
foreach cell [get_cells -hierarchical -filter {IS_PRIMITIVE}] {
 foreach pin [get_pins -quiet -of_objects $cell -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}] {
  incr count
  set nets [get_nets -quiet -segments -of_objects $pin]
  set drivers [get_pins -quiet -leaf -of_objects $nets -filter {DIRECTION == OUT}]
  puts $f "PIN=$pin TYPE=[get_property REF_NAME $cell] DRIVERS=$drivers"
  if {[string first "/packet/" "/$pin"] >= 0 || [string first "packet/" $pin] == 0} { incr pk; puts $f "HOLD packetizer async pin $pin" }
  if {[llength $drivers] != 1} { puts $f "HOLD ambiguous driver"; incr unsafe; continue }
  foreach obj [all_fanin -quiet -flat -to $pin] {
   if {[get_property CLASS $obj] ne "pin"} { continue }
   set cc [get_cells -quiet -of_objects $obj]
   if {[llength $cc] != 1} { continue }
   if {[regexp {^LUT([2-6])$} [get_property REF_NAME $cc]]} { puts $f "HOLD multi-input async logic $cc [get_property REF_NAME $cc]"; incr unsafe }
  }
 }
}
puts $f "COUNT=$count UNSAFE=$unsafe PACKETIZER_ASYNC_PINS=$pk"
close $f
set f [open "$out/tx_chain.txt" w]
set port [get_ports uart_tx]; set net [get_nets -quiet -of_objects $port]
puts $f "uart_tx net: $net"
foreach l [get_pins -quiet -leaf -of_objects $net] { puts $f "  port-net pin $l ref=[get_property REF_NAME [get_cells -of_objects $l]] dir=[get_property DIRECTION $l]" }
set ob [get_cells -quiet -of_objects [get_pins -quiet -leaf -of_objects $net -filter {DIRECTION == IN}]]
foreach o $ob {
 puts $f "output buffer: $o ref=[get_property REF_NAME $o]"
 set ipin [get_pins -of_objects $o -filter {REF_PIN_NAME == I}]
 set inet [get_nets -of_objects $ipin]
 foreach d [get_pins -quiet -leaf -of_objects $inet -filter {DIRECTION == OUT}] { puts $f "OBUF I driver: $d ref=[get_property REF_NAME [get_cells -of_objects $d]]" }
}
close $f
set f [open "$out/asyncreg.txt" w]
foreach c [get_cells -hierarchical -filter {NAME =~ *packet/rs_reg*}] { puts $f "CELL $c ref=[get_property REF_NAME $c] ASYNC_REG=[get_property ASYNC_REG $c]" }
close $f
set f [open "$out/packet_cells.txt" w]
foreach t {LUT FD CARRY RAMB DSP MUXF} { puts $f "packet_$t [llength [get_cells -quiet -hierarchical -filter "NAME =~ *packet/* && REF_NAME =~ ${t}*"]]" }
puts $f "total_LUT [llength [get_cells -quiet -hierarchical -filter {REF_NAME =~ LUT*}]] total_FF [llength [get_cells -quiet -hierarchical -filter {REF_NAME =~ FD*}]]"
close $f
set rp [get_pins -quiet -hierarchical -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}]
report_timing -delay_type min -to $rp -max_paths 20 -nworst 1 -file "$out/est_removal.rpt"
report_timing -delay_type max -to $rp -max_paths 20 -nworst 1 -file "$out/est_recovery.rpt"
exit
