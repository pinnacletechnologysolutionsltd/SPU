# T1d freeze: measured FPGA-pad to DE-15 mapping through the J10 harness.
# J10-1/G8 -> RED/DE-15 pin 1 via 270 ohm; J10-2/G7 -> GREEN/pin 2;
# J10-3/G5 -> BLUE/pin 3; J10-4/D5 -> HSYNC/pin 13;
# J10-10/E5 -> VSYNC/pin 14. J10-7/G6 is unused by this harness.

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
