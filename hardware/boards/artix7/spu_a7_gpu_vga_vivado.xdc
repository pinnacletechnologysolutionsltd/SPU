# Vivado timing companion for spu_a7_gpu_vga.xdc. Keep the existing XDC used
# by the OpenXC7 build unchanged; this copy adds the known 50/25 MHz clock
# relationship for the standalone GPU timing run.

set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]

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

# clk_div toggles on each 50 MHz sys_clk rising edge and feeds BUFG u_bufg_pix.
# Use the divider flop's clock pin as the master source and its Q as the divide-by-2 output.
create_generated_clock -name clk_pixel -source [get_pins clk_div_reg/C] -divide_by 2 [get_pins clk_div_reg/Q]
