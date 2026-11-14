# rtl0s_structure.tcl — structural checks on the open design; writes OUT_FILE. Sourced by the RTL-0S/0P flows,
# or run standalone on a checkpoint:  vivado -mode batch -source rtl0s_structure.tcl -tclargs DCP OUT_FILE
# Primitive groups (Vivado): BMEM block RAM, MULT DSP48, DMEM LUTRAM, CLK clock buffers.
# Fails (error) if the DSP or BRAM count disagrees with report_utilization, so a wrong filter cannot
# silently report zero.
proc rtl0s_structure {outfile} {
  set f [open $outfile w]
  foreach blk {core/imem core/sgn core/exu/bank core/exu/loader core/exu/arith core/exu/arith/products core/exu/arith/normalizer} {
    puts $f "cells $blk [llength [get_cells -quiet -hierarchical -filter "NAME =~ $blk/*"]]"
  }
  set n(bram)   [llength [get_cells -quiet -hierarchical -filter {PRIMITIVE_GROUP == BMEM}]]
  set n(dsp)    [llength [get_cells -quiet -hierarchical -filter {PRIMITIVE_GROUP == MULT}]]
  set n(lutram) [llength [get_cells -quiet -hierarchical -filter {PRIMITIVE_GROUP == DMEM}]]
  set n(clkbuf) [llength [get_cells -quiet -hierarchical -filter {PRIMITIVE_GROUP == CLK}]]
  set n(latch)  [llength [get_cells -quiet -hierarchical -filter {PRIMITIVE_SUBGROUP == latch}]]
  set n(bbox)   [llength [get_cells -quiet -hierarchical -filter {IS_BLACKBOX == 1}]]
  foreach k {bram dsp lutram clkbuf latch bbox} { puts $f "$k $n($k)" }
  set u [report_utilization -return_string]
  if {![regexp {\|\s*DSPs\s*\|\s*(\d+)} $u -> udsp] || ![regexp {\|\s*Block RAM Tile\s*\|\s*([0-9.]+)} $u -> ubram]} {
    close $f; error "rtl0s_structure: cannot identify DSP/BRAM rows in report_utilization"
  }
  set bram_tiles [expr {[llength [get_cells -quiet -hierarchical -filter {REF_NAME =~ RAMB36*}]] + 0.5 * [llength [get_cells -quiet -hierarchical -filter {REF_NAME =~ RAMB18*}]]}]
  puts $f "check dsp_vs_report $n(dsp) $udsp"
  puts $f "check bram_tiles_vs_report $bram_tiles $ubram"
  puts $f "clocks [get_clocks]"
  close $f
  if {$n(dsp) != $udsp || $bram_tiles != $ubram} { error "rtl0s_structure: cell counts disagree with report_utilization (dsp $n(dsp)/$udsp, bram $bram_tiles/$ubram)" }
}
if {[info exists argv] && [llength $argv] == 2 && [string match *.dcp [lindex $argv 0]]} {
  open_checkpoint [lindex $argv 0]
  rtl0s_structure [lindex $argv 1]
}
