# rtl0c_bitstream.tcl — RTL-0C gate C4: write_bitstream from the routed C3 checkpoint, after re-checking pins,
# standards, unused-pin behaviour and structure (plan R4). SRAM image only; no flash file is produced.
# usage: vivado -mode batch -source rtl0c_bitstream.tcl -tclargs REPO_ROOT ROUTED_DCP OUT_DIR
set root [lindex $argv 0]; set dcp [lindex $argv 1]; set out [lindex $argv 2]
file mkdir $out
source [file join $root hardware/boards/artix7/psurd_rtl0c/rtl0c_checks.tcl]
open_checkpoint $dcp
rtl0c_structure bitstream $out
rtl0c_pins bitstream $out
report_io -file [file join $out io.rpt]
report_drc -file [file join $out drc_bitstream.rpt]
write_bitstream -force [file join $out psurd_board.bit]
set f [open [file join $out identity.txt] w]
puts $f "routed_dcp_sha256 [lindex [exec sha256sum $dcp] 0]"
puts $f "bitstream_sha256 [lindex [exec sha256sum [file join $out psurd_board.bit]] 0]"
puts $f "bitstream_bytes [file size [file join $out psurd_board.bit]]"
close $f
