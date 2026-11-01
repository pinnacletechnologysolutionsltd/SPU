# CPU-BOARD-4B: one write_bitstream on the frozen routed checkpoint. Applies only the approved BITSTREAM.* properties. argv0 = output dir (must not exist).
set_param general.maxThreads 2
set out [lindex $argv 0]
if {[file exists $out]} { error "HOLD: output dir already exists" }
file mkdir $out
open_checkpoint [lindex $argv 1]
set_property BITSTREAM.GENERAL.COMPRESS FALSE [current_design]
set_property BITSTREAM.CONFIG.UNUSEDPIN PULLNONE [current_design]
set_property BITSTREAM.CONFIG.USR_ACCESS 0x48E0E161 [current_design]
set f [open "$out/bitstream_properties.txt" w]
foreach p [lsort [list_property [current_design] BITSTREAM.*]] { puts $f "$p [get_property $p [current_design]]" }
puts $f "CFGBVS [get_property CFGBVS [current_design]] CONFIG_VOLTAGE [get_property CONFIG_VOLTAGE [current_design]]"
puts $f "PART [get_property PART [current_design]] TOP [get_property TOP [current_design]]"
close $f
catch { report_drc -ruledecks {bitstream_checks} -file "$out/pre_bitstream_drc.rpt" }
catch { report_waivers -file "$out/waivers.rpt" }
write_bitstream -bin_file "$out/cpu_board_2r_top.bit"
puts "BOARD4B_WRITE_BITSTREAM_COMPLETE"
exit
