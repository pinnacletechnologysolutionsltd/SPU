# Read-only: for each RAMB output pin print its net and that net's load pins (argv0 = dcp, argv1 = out file).
open_checkpoint [lindex $argv 0]
set f [open [lindex $argv 1] w]
foreach c [get_cells -hierarchical -filter {REF_NAME =~ RAMB*}] {
 foreach pin [get_pins -of_objects $c -filter {DIRECTION == OUT && (REF_PIN_NAME =~ DOADO* || REF_PIN_NAME =~ DOBDO* || REF_PIN_NAME =~ DOPADOP* || REF_PIN_NAME =~ DOPBDOP*)}] {
  set n [get_nets -quiet -of_objects $pin]
  set loads {}
  if {$n ne ""} { foreach l [get_pins -quiet -leaf -of_objects $n -filter {DIRECTION == IN}] { lappend loads $l } }
  puts $f "LOAD [get_property REF_PIN_NAME $pin] net=$n loads=[lsort $loads]"
 }
}
close $f
exit
