# Owner-supplied V03 schematic, sheets 1, 2 and 6. No J11 pins.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
set_property PACKAGE_PIN H7 [get_ports raw_rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports raw_rst_n]
set_property PULLTYPE PULLUP [get_ports raw_rst_n]
set_property PACKAGE_PIN F3 [get_ports uart_rx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_rx]
set_property PULLTYPE PULLUP [get_ports uart_rx]
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
# Only the asynchronous input-to-first-synchronizer-stage exceptions are
# applied after synthesis, once the exact D pins have been checked. Reset is
# not false-pathed; no external reset or UART I/O delay is invented.
