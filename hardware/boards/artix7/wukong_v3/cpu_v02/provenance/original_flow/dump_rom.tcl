# Read-only: dump every RAMB cell's initialization-relevant properties from a checkpoint (argv0 = dcp, argv1 = out file).
open_checkpoint [lindex $argv 0]
set f [open [lindex $argv 1] w]
foreach c [get_cells -hierarchical -filter {REF_NAME =~ RAMB*}] {
 puts $f "CELL [get_property NAME $c] REF [get_property REF_NAME $c]"
 foreach p {READ_WIDTH_A READ_WIDTH_B WRITE_WIDTH_A WRITE_WIDTH_B RAM_MODE WRITE_MODE_A WRITE_MODE_B DOA_REG DOB_REG} { puts $f "PROP $p [get_property $p $c]" }
 foreach p [lsort [list_property $c INIT_*]] { puts $f "PROP $p [get_property $p $c]" }
 foreach p [lsort [list_property $c INITP_*]] { puts $f "PROP $p [get_property $p $c]" }
 foreach pin [get_pins -of_objects $c -filter {DIRECTION == IN && (REF_PIN_NAME =~ ADDR* || REF_PIN_NAME =~ ENARD* || REF_PIN_NAME =~ EN*)}] { puts $f "PIN [get_property REF_PIN_NAME $pin] [get_nets -quiet -of_objects $pin]" }
 foreach pin [get_pins -of_objects $c -filter {DIRECTION == OUT}] { puts $f "OUT [get_property REF_PIN_NAME $pin] [get_nets -quiet -of_objects $pin]" }
}
close $f
exit
