# T1d diagnostic freeze: normal VGA mapping plus independent telemetry on
# Wukong J10-7 / FPGA G6. G6 is unused by the measured VGA harness.

set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]

set_property PACKAGE_PIN F3 [get_ports uart_rx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_rx]
set_property PULLTYPE PULLUP [get_ports uart_rx]

set_property PACKAGE_PIN G8 [get_ports vga_r]
set_property PACKAGE_PIN G7 [get_ports vga_g]
set_property PACKAGE_PIN G5 [get_ports vga_b]
set_property PACKAGE_PIN D5 [get_ports vga_hsync]
set_property PACKAGE_PIN E5 [get_ports vga_vsync]
set_property IOSTANDARD LVCMOS33 [get_ports vga_r]
set_property IOSTANDARD LVCMOS33 [get_ports vga_g]
set_property IOSTANDARD LVCMOS33 [get_ports vga_b]
set_property IOSTANDARD LVCMOS33 [get_ports vga_hsync]
set_property IOSTANDARD LVCMOS33 [get_ports vga_vsync]

set_property PACKAGE_PIN G6 [get_ports diag_tx]
set_property IOSTANDARD LVCMOS33 [get_ports diag_tx]
