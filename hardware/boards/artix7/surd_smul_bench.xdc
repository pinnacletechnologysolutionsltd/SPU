# Standalone Surd multiplier timing wrapper on the Wukong XC7A100T.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 40.000 -name sys_clk [get_ports sys_clk]
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
