# J10 pin-identification positive control. Every J10 IO pin toggles.
#
# j10[N] maps to the J10 header in the QMTech README's pin order:
#   j10[0] G8 = J10 pin 1      j10[4] G6 = J10 pin 7
#   j10[1] G7 = J10 pin 2      j10[5] D6 = J10 pin 8
#   j10[2] G5 = J10 pin 3      j10[6] E6 = J10 pin 9
#   j10[3] D5 = J10 pin 4      j10[7] E5 = J10 pin 10
#   (J10 pins 5 and 11 are GND, pins 6 and 12 are 3V3)
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
set_property PACKAGE_PIN G8 [get_ports {j10[0]}]
set_property PACKAGE_PIN G7 [get_ports {j10[1]}]
set_property PACKAGE_PIN G5 [get_ports {j10[2]}]
set_property PACKAGE_PIN D5 [get_ports {j10[3]}]
set_property PACKAGE_PIN G6 [get_ports {j10[4]}]
set_property PACKAGE_PIN D6 [get_ports {j10[5]}]
set_property PACKAGE_PIN E6 [get_ports {j10[6]}]
set_property PACKAGE_PIN E5 [get_ports {j10[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {j10[7]}]
