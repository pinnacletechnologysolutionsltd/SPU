# Offline logical clock target: externally supplied 25 MHz at sys_clk.
# No divider or generated clock. This image has not been loaded on a board;
# M21's physical clock frequency is not established by this build constraint.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 40.000 -name sys_clk [get_ports sys_clk]
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
