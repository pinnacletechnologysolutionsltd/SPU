# REVERSED-ORDER variant of spu_a7_vga.xdc, 2026-09-04.
#
# The QMTech README and the LiteX platform file list J10's pins in OPPOSITE
# orders and neither states which is physical. This variant assumes the
# README order (G8 G7 G5 D5 / G6 D6 E6 E5 for positions 1-4 / 7-10); the
# primary spu_a7_vga.xdc assumes the LiteX order. Load whichever produces a
# picture -- that settles which listing is physical.
#
# Wukong Artix-7 100T pins for the 640x480@60 VGA test-pattern spin.
#
# Uses connector J10, NOT JP2. Two reasons:
#   1. All J10 pins are in BANK 35 -- the same bank as uart_tx (E3) and
#      spi_miso (B5), both documented confirmed-healthy on this unit. JP2 is
#      bank 15, which has never been exercised on this board at all.
#   2. J10's physical pinout is documented; JP2's is not.
#
# J10 is a 12-pin Pmod-style header, laid out exactly like J11 (whose mapping
# is recorded in spu_a7_100t.xdc):
#   J10 pin 1  G8     J10 pin 7  G6
#   J10 pin 2  G7     J10 pin 8  D6
#   J10 pin 3  G5     J10 pin 9  E6
#   J10 pin 4  D5     J10 pin 10 E5
#   J10 pin 5  GND    J10 pin 11 GND
#   J10 pin 6  3V3    J10 pin 12 3V3
# Pin order is from the QMTech board README (G8 G7 G5 D5 G6 D6 E6 E5); the
# 1-4 / GND / 3V3 / 7-10 / GND / 3V3 layout is by analogy with J11's
# documented mapping. Verify against the silkscreen before soldering.

set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

# rst_n (H7) has no external pull on this board -- see hardware_evidence 3.2m.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]

# ── VGA resistor DAC on J10 ──────────────────────────────────────────────
#
#   J10-1 (G8) --[ 270R ]--> VGA pin 1   RED
#   J10-2 (G7) --[ 270R ]--> VGA pin 2   GREEN
#   J10-3 (G5) --[ 270R ]--> VGA pin 3   BLUE
#   J10-4 (D5) ------------> VGA pin 13  HSYNC   no resistor
#   J10-7 (G6) ------------> VGA pin 14  VSYNC   no resistor
#   J10-5 or J10-11 (GND) -> VGA pins 5,6,7,8,10
#
# VGA expects 0-0.7 V into a 75 ohm termination; 3.3 V * 75/(270+75) = 0.72 V.
# 220R (0.84 V) and 330R (0.61 V) both work fine. Sync lines are digital and
# connect directly. Do NOT connect VGA pin 9 (+5V) or the DDC lines (12, 15)
# to anything -- nothing on the monitor side should drive current back into
# bank 35.
#
# J10-8/9/10 (D6/E6/E5) are left free.
set_property PACKAGE_PIN D5 [get_ports vga_r]
set_property PACKAGE_PIN G5 [get_ports vga_g]
set_property PACKAGE_PIN G7 [get_ports vga_b]
set_property PACKAGE_PIN G8 [get_ports vga_hsync]
set_property PACKAGE_PIN E5 [get_ports vga_vsync]
set_property IOSTANDARD LVCMOS33 [get_ports vga_r]
set_property IOSTANDARD LVCMOS33 [get_ports vga_g]
set_property IOSTANDARD LVCMOS33 [get_ports vga_b]
set_property IOSTANDARD LVCMOS33 [get_ports vga_hsync]
set_property IOSTANDARD LVCMOS33 [get_ports vga_vsync]
