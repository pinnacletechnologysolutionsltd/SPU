# Wukong Artix-7 100T pins for the standalone tensegrity admission probe.
# UART E3 is the sole acceptance output; LEDs are kept quiescent in RTL.

# 50 MHz board oscillator.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

# Active-low reset button.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# 115200-baud verdict line.
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

# Present in the top-level interface but electrically non-evidentiary on this
# particular board; all three are constant zero in the probe RTL.
set_property PACKAGE_PIN V17 [get_ports {led[0]}]
set_property PACKAGE_PIN W21 [get_ports {led[1]}]
set_property PACKAGE_PIN Y21 [get_ports {led[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[2]}]
