# Wukong Artix-7 100T pins for the transactional TGR1 southbridge sidecar.

# 50 MHz board oscillator and active-low KEY0 reset.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
# rst_n (H7) has no external pull on this board. Without a pull it floats,
# and the design that fed it straight into async resets was dead on silicon
# for three weeks (hardware_evidence.md 3.2m). spu_a7_top now debounces the
# pin, so this is belt-and-braces -- it removes the floating condition
# instead of only surviving it. Active-low reset, so PULLUP = not reset.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]

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

# --- Stage G1 (Vivado timing analysis only): the flop-divided 25 MHz clock --------------------------------------------------------
# Everything above is spu_a7_tensegrity_link.xdc unchanged. This file adds exactly one constraint and no timing exceptions.
# spu_a7_tensegrity_link_top.v: guard_clk_div toggles on every sys_clk rising edge (held at 0 while the reset count runs) and drives
# BUFG u_guard_clk_buf -> guard_clk (u_spi, u_sidecar). Vivado does not derive a clock through a flip-flop, so without this line the
# 25 MHz domain (8172 clock pins in the Step 7V synthesis) is unclocked and untimed. Defined on the flop output, sourced from its clock pin.
# Netlist names checked in the synthesized checkpoint (build/vivado/dcp_inspect_01): FDRE guard_clk_div_reg, pins C and Q.
# Not for the open-source board build (build_a7.sh uses spu_a7_tensegrity_link.xdc).
create_generated_clock -name guard_clk -source [get_pins guard_clk_div_reg/C] -divide_by 2 [get_pins guard_clk_div_reg/Q]
