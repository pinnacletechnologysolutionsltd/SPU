# spu_a7_som_probe.xdc — Wukong Artix-7 100T pins for the SOM/BMU probe.
# Pin sites copied from spu_a7_100t.xdc; only the probe's minimal footprint.

# 50 MHz board oscillator
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

# Reset button (active low)
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# UART TX (115200 baud status line)
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

# LEDs: [0]=heartbeat [1]=off=PASS [2]=off=FAIL (active low, as Tang probe)
set_property PACKAGE_PIN V17 [get_ports {led[0]}]
set_property PACKAGE_PIN W21 [get_ports {led[1]}]
set_property PACKAGE_PIN Y21 [get_ports {led[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[2]}]
