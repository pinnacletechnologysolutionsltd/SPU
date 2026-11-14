# psurd_board.xdc — v0.3 RTL-0C constraints, QMTECH Wukong XC7A100T-FGG676 (plan SPU_V03_RTL0C_PLAN.md §2-§3).
# Pins as spu_a7_surd_cpu_base.xdc (M21, H7) and spu_a7_uart_loopback.xdc (F3, E3). No LED or header pins.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
# rst_n (H7, KEY0) has no external pull on this board; PULLUP = not reset.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
set_property PACKAGE_PIN F3 [get_ports uart_rx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_rx]
set_property PULLTYPE PULLUP [get_ports uart_rx]
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property BITSTREAM.CONFIG.UNUSEDPIN PULLNONE [current_design]
# The generated 25 MHz clock (cpu_clk) and the exceptions from the two asynchronous pads to their first
# synchronizer stage are applied by the flow script after synthesis, once the exact pins have been checked
# (psurd_rtl0c/rtl0c_impl.tcl). Reset is not false-pathed beyond that first stage; no I/O delay is invented.
