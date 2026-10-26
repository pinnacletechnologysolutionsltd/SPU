# CPU-BASE-TOP-1 Base SPU CPU (ENABLE_REGEN=0) on Wukong XC7A100T-FGG676-1. Contract A1.
# M21 / H7 lines are those of the silicon-proven spu_a7_tensegrity_link.xdc; E3 is the telemetry pin
# of spu_a7_uart_loopback.xdc. The 20 ns value of M21 is re-checked on the board in the S5 diagnostic.
# E3 carries checksum_parity_out (parity of the workload checksum), NOT UART serial data.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
# Derived 40 ns CPU clock (cpu_clk), divided by cpu_clk_div and distributed by u_cpu_clk_buf.
# Define it at the divider flop output, sourced from the flop's 50 MHz clock pin, matching the
# established G1 constraint pattern. This is Vivado timing only; nextpnr-xilinx uses one --freq.
create_generated_clock -name cpu_clk -source [get_pins cpu_clk_div_reg/C] -divide_by 2 [get_pins cpu_clk_div_reg/Q]
# rst_n (H7) has no external pull on this board; PULLUP = not reset.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
