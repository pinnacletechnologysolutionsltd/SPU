# Wukong Artix-7 100T pins for the transactional TGR1 southbridge sidecar.

# 50 MHz board oscillator and active-low KEY0 reset.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# J11 bottom row remap (pins 7-10). Top-row H4/F4/A4 is damaged on this unit.
# Bench wiring: RP2350 GP1/GP2/GP3/GP0 -> J11-7/8/9/10, common GND on J11-11,
# with 100 ohm series resistance on all four signal wires.
set_property PACKAGE_PIN J4 [get_ports spi_cs_n]
set_property PACKAGE_PIN G4 [get_ports spi_sck]
set_property PACKAGE_PIN B4 [get_ports spi_mosi]
set_property PACKAGE_PIN B5 [get_ports spi_miso]
set_property IOSTANDARD LVCMOS33 [get_ports spi_cs_n]
set_property IOSTANDARD LVCMOS33 [get_ports spi_sck]
set_property IOSTANDARD LVCMOS33 [get_ports spi_mosi]
set_property IOSTANDARD LVCMOS33 [get_ports spi_miso]
