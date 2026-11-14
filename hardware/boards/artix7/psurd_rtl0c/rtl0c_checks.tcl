# rtl0c_checks.tcl — fail-closed structural and pin checks for the RTL-0C board flow (plan R1, R4).
# Sourced by rtl0c_synth.tcl, rtl0c_route.tcl and rtl0c_bitstream.tcl. Each proc writes a text report into
# OUT and raises an error (job FAILED) if a check does not hold. These are netlist facts, not timing claims.
proc rtl0c_names {objs} { set r {}; foreach o $objs { lappend r [get_property NAME $o] }; return [lsort -unique $r] }
proc rtl0c_one {kind name} {
  set o [expr {$kind eq "cell" ? [get_cells -quiet $name] : [get_pins -quiet $name]}]
  if {[llength $o] != 1} { error "RTL-0C HOLD: expected exactly one $kind $name, found [llength $o]" }
  return $o
}
proc rtl0c_structure {phase out} {
  set f [open [file join $out structure_${phase}.txt] w]; set bad 0
  # 1. Raw reset pad: only the first reset-synchronizer flop.
  set e [rtl0c_names [all_fanout -quiet -flat -endpoints_only -from [get_ports rst_n]]]
  puts $f "rst_n endpoints: $e"
  if {$e ne [list {rst_sync_reg[0]/D}]} { puts $f "HOLD rst_n pad fan-out"; incr bad }
  foreach c {rst_sync_reg[0] rst_sync_reg[1]} {
    if {[string toupper [get_property ASYNC_REG [rtl0c_one cell $c]]] ni {1 TRUE}} { puts $f "HOLD ASYNC_REG missing on $c"; incr bad }
  }
  # 2. UART receive pad: only rx_s1, whose only load is rx_s2; both ASYNC_REG, both on cpu_clk.
  set e [rtl0c_names [all_fanout -quiet -flat -endpoints_only -from [get_ports uart_rx]]]
  puts $f "uart_rx endpoints: $e"
  if {$e ne [list u_sys/urx/rx_s1_reg/D]} { puts $f "HOLD uart_rx pad fan-out"; incr bad }
  set e [rtl0c_names [all_fanout -quiet -flat -endpoints_only -from [rtl0c_one pin u_sys/urx/rx_s1_reg/Q]]]
  puts $f "rx_s1 endpoints: $e"
  if {$e ne [list u_sys/urx/rx_s2_reg/D]} { puts $f "HOLD rx_s1 has loads other than rx_s2"; incr bad }
  foreach c {u_sys/urx/rx_s1_reg u_sys/urx/rx_s2_reg} {
    set cell [rtl0c_one cell $c]
    set a [string toupper [get_property ASYNC_REG $cell]]; set ck [get_clocks -quiet -of_objects [get_pins $c/C]]
    puts $f "$c ASYNC_REG=$a clock=$ck"
    if {$a ni {1 TRUE} || $ck ne "cpu_clk"} { puts $f "HOLD synchronizer flop $c"; incr bad }
  }
  # 3. Asynchronous clear/preset pins: driven only from the approved reset flops, through LUT/buffer cells.
  set n 0
  foreach pin [get_pins -quiet -hierarchical -filter {REF_PIN_NAME == CLR || REF_PIN_NAME == PRE}] {
    incr n
    foreach s [all_fanin -quiet -flat -startpoints_only $pin] {
      set sn [get_property NAME $s]
      if {![regexp {^(rst_count_reg\[[0-7]\]|cpu_rst_sync_reg\[1\])/C$} $sn]} { puts $f "HOLD async pin $pin has start point $sn"; incr bad }
    }
    foreach c [all_fanin -quiet -flat -only_cells $pin] {
      set ref [get_property REF_NAME $c]
      if {![regexp {^(FD[A-Z]*|LUT[1-6]|BUFG|IBUF)$} $ref]} { puts $f "HOLD async pin $pin fan-in cell $c ($ref)"; incr bad }
    }
  }
  puts $f "async clear/preset pins: $n"
  if {$n == 0} { puts $f "HOLD no asynchronous reset pins found"; incr bad }
  # 4. Clocks: sys_clk 20 ns, cpu_clk 40 ns, and no v0.3 flop on anything but cpu_clk.
  foreach {c p} {sys_clk 20.000 cpu_clk 40.000} {
    set cl [get_clocks -quiet $c]
    if {[llength $cl] != 1 || abs([get_property PERIOD $cl] - $p) > 1e-6} { puts $f "HOLD clock $c"; incr bad }
  }
  set off 0
  # Flops, block RAM and LUTRAM must be on cpu_clk. Other clock pins (the CLK of a DSP48 used purely
  # combinationally carries no clock) fail only if they carry a clock that is not cpu_clk.
  foreach pin [get_pins -quiet -hierarchical -filter {NAME =~ u_sys/* && IS_CLOCK == 1 && DIRECTION == IN}] {
    set ck [get_clocks -quiet -of_objects $pin]; set ref [get_property REF_NAME [get_cells -of_objects $pin]]
    set storage [regexp {^(FD|RAMB|RAMD|RAMS|RAM[0-9]|SRL)} $ref]
    if {($storage && $ck ne "cpu_clk") || (!$storage && $ck ne "" && $ck ne "cpu_clk")} {
      incr off; if {$off < 6} { puts $f "HOLD $pin ($ref) clock='$ck', not cpu_clk" }
    }
  }
  puts $f "u_sys clock pins not on cpu_clk: $off"; incr bad $off
  set bufg [get_cells -quiet -hierarchical -filter {REF_NAME == BUFG}]
  puts $f "BUFG cells: [rtl0c_names $bufg]"
  if {[llength $bufg] < 1} { puts $f "HOLD cpu_clk is not on a global buffer"; incr bad }
  puts $f "VERDICT [expr {$bad ? "HOLD ($bad)" : "PASS"}]"; close $f
  if {$bad} { error "RTL-0C HOLD: structural check failed at $phase (see structure_${phase}.txt)" }
}
proc rtl0c_pins {phase out} {
  set f [open [file join $out pins_${phase}.txt] w]; set bad 0
  array set want {sys_clk {M21 IN} rst_n {H7 IN} uart_rx {F3 IN} uart_tx {E3 OUT}}
  set ports [get_ports]
  puts $f "ports: [rtl0c_names $ports]"
  if {[rtl0c_names $ports] ne [lsort [array names want]]} { puts $f "HOLD port list"; incr bad }
  foreach p $ports {
    set n [get_property NAME $p]; set loc [get_property PACKAGE_PIN $p]; set std [get_property IOSTANDARD $p]; set dir [get_property DIRECTION $p]
    puts $f "$n pin=$loc standard=$std direction=$dir pull=[get_property PULLTYPE $p]"
    if {![info exists want($n)] || $loc ne [lindex $want($n) 0] || $dir ne [lindex $want($n) 1] || $std ne "LVCMOS33"} { puts $f "HOLD port $n"; incr bad }
  }
  foreach {prop val} {BITSTREAM.CONFIG.UNUSEDPIN PULLNONE CFGBVS VCCO CONFIG_VOLTAGE 3.3} {
    set v [get_property $prop [current_design]]; puts $f "$prop = $v"
    if {[string toupper $v] ne [string toupper $val]} { puts $f "HOLD design property $prop"; incr bad }
  }
  puts $f "VERDICT [expr {$bad ? "HOLD ($bad)" : "PASS"}]"; close $f
  if {$bad} { error "RTL-0C HOLD: pin check failed at $phase (see pins_${phase}.txt)" }
}
