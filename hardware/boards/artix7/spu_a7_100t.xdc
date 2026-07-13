# spu_a7_100t.xdc — QMTech Wukong Artix-7 XC7A100T-FGG676 V02 constraints
# Pins are derived from QMTECH-XC7A100T_200T-Wukong-Board-V02-20210426.pdf.
#
# KNOWN DAMAGE ON THIS UNIT (2026-07-13, multimeter-confirmed) — see AGENTS.md
# "Known board limitations" for full detail. J11 pins 1-3 (H4/F4/A4 below,
# spi_cs_n/spi_sck/spi_mosi) are permanently damaged from RP2350 backfeed and
# must not be reused for new signals. led_out[3:0] (V17/W21/Y21/V26) misbehave
# by a still-unresolved mechanism — do not trust them for new claims without a
# fresh loopback/probe check first. clk_100mhz, core logic, uart_tx (E3), and
# spi_miso (A5) are the confirmed-healthy paths on this unit; treat this board
# as UART-tier constrained compute/proof only until a full peripheral
# inventory says otherwise.

# 50 MHz oscillator
set_property PACKAGE_PIN M21 [get_ports clk_100mhz]
set_property IOSTANDARD LVCMOS33 [get_ports clk_100mhz]
create_clock -period 20.000 -name sys_clk [get_ports clk_100mhz]

# Reset (active low): KEY0 has a board pull-up and shorts low when pressed.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# ── RP2350 SPI Slave ──────────────────────────────────────
# Wukong J11 PMOD, VCCO_35 = 3V3. J11 is a 12-pin (2x6) connector, per the
# QMTECH-XC7A100T_200T-Wukong-Board-V02-20210426.pdf schematic:
#   J11 pin 1  BANK35_H4   J11 pin 7  BANK35_J4
#   J11 pin 2  BANK35_F4   J11 pin 8  BANK35_G4
#   J11 pin 3  BANK35_A4   J11 pin 9  BANK35_B4
#   J11 pin 4  BANK35_A5   J11 pin 10 BANK35_B5
#   J11 pin 5  GND         J11 pin 11 GND
#   J11 pin 6  3V3         J11 pin 12 3V3
# REMAPPED 2026-07-13 to the bottom row (pins 7-10 / J4-G4-B4-B5) after
# confirmed backfeed damage to the top row (pins 1-3 / H4-F4-A4, see below).
# The bottom row was never connected to anything before this, same bank
# (35, same VCCO/IOSTANDARD), so no exposure to the backfeed event. Wire
# RP2350 GP1/GP2/GP3/GP0 to J11-7/J11-8/J11-9/J11-10 (GND from J11-11).
# No RTL/firmware change needed — spi_cs_n/spi_sck/spi_mosi/spi_miso are
# just port names; only the physical J11 pin they land on changed.
#
# Top row (pins 1-4 / H4-F4-A4-A5), RETIRED, DAMAGED, DO NOT REUSE:
# H4/F4/A4 (spi_cs_n/spi_sck/spi_mosi) took confirmed RP2350 backfeed
# damage (multimeter: 1.0V, not clean logic levels). A5 (spi_miso) itself
# reads healthy but sits on the same now-abandoned connector row.
set_property PACKAGE_PIN J4 [get_ports spi_cs_n]
set_property PACKAGE_PIN G4 [get_ports spi_sck]
set_property PACKAGE_PIN B4 [get_ports spi_mosi]
set_property PACKAGE_PIN B5 [get_ports spi_miso]
set_property IOSTANDARD LVCMOS33 [get_ports spi_cs_n]
set_property IOSTANDARD LVCMOS33 [get_ports spi_sck]
set_property IOSTANDARD LVCMOS33 [get_ports spi_mosi]
set_property IOSTANDARD LVCMOS33 [get_ports spi_miso]

# ── Onboard CP2102N USB-UART ────────────────────────────
# CP2102N RXD is the FPGA transmit path. CP2102N TXD is available on F3, but
# spu_a7_top currently exposes TX only.
# CONFIRMED HEALTHY on this unit (2026-07-13): same bank as damaged J11
# (Bank 35), but E3 itself ran a clean, correctly-timed UART stream —
# proves clk_100mhz and core logic execution are genuinely intact. This is
# the recommended path for proof-of-life/core-execution demonstrations
# until a fuller peripheral inventory is done.
# RE-CONFIRMED 2026-07-13 (same day, after DirtyJTAG rewiring + inline
# series resistors added to TCK/TMS/TDI/TDO): JTAG detect passed with the
# correct IDCODE post-rewire, and a fresh reflash of spu_a7_100t_UARTPROBE.bit
# repeated `UART:P` cleanly on E3 — checklist §5.3a steps 1-2 both pass
# today, not just carried over from the prior session.
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

# ── Status LEDs ───────────────────────────────────────────
# UNRESOLVED on this unit (2026-07-13): these 4 pins stayed non-blinking
# across multiple proven-good bitstreams (including a pre-dated, silicon-
# verified design) while clk_100mhz/core logic/uart_tx on the same bank
# (E3) ran correctly in the same test. Mechanism unknown — they were never
# externally driven, unlike J11. Do not trust led_out for a new claim on
# this unit without a fresh isolated loopback/probe check first.
# CLOSED, NOT FIXED (2026-07-13, same day): reproduced again on a fresh
# spu_a7_100t_BLINKY.bit reflash — no blinking, and multimeter reads
# non-logic-level voltages (2 pins clean 3.3V, one 2.65V, one 1.85V; the
# 1.85V figure exactly repeats a reading from the prior session on a
# different bitstream, ruling out random floating-pin noise). This is a
# real, stable, reproducible I/O anomaly, but a multimeter can't diagnose
# it further — needs a scope on the actual pin waveform. Not investigating
# further without better equipment; does not block using this board
# (UART/E3 already covers proof-of-life/status duty).
set_property PACKAGE_PIN V17 [get_ports {led_out[0]}]
set_property PACKAGE_PIN W21 [get_ports {led_out[1]}]
set_property PACKAGE_PIN Y21 [get_ports {led_out[2]}]
set_property PACKAGE_PIN V26 [get_ports {led_out[3]}]
set_property PACKAGE_PIN V16 [get_ports fault_led]
set_property IOSTANDARD LVCMOS33 [get_ports {led_out[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led_out[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led_out[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led_out[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports fault_led]

# ── Sensor inputs ─────────────────────────────────────────
set_property PACKAGE_PIN AA24 [get_ports {sensor_in[0]}]
set_property PACKAGE_PIN AB25 [get_ports {sensor_in[1]}]
set_property PACKAGE_PIN AA22 [get_ports {sensor_in[2]}]
set_property PACKAGE_PIN AA23 [get_ports {sensor_in[3]}]
set_property PACKAGE_PIN Y25  [get_ports {sensor_in[4]}]
set_property PACKAGE_PIN AA25 [get_ports {sensor_in[5]}]
set_property PACKAGE_PIN W25  [get_ports {sensor_in[6]}]
set_property PACKAGE_PIN Y26  [get_ports {sensor_in[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[7]}]

# ── HDMI/DVI (TMDS differential) ─────────────────────────
# LUCAS/ROBOTICS bring-up drives these low, but nextpnr still emits PADs.
# The video spin should revisit these as real TMDS constraints.
set_property PACKAGE_PIN E1 [get_ports {hdmi_d_p[0]}]
set_property PACKAGE_PIN D1 [get_ports {hdmi_d_n[0]}]
set_property PACKAGE_PIN F2 [get_ports {hdmi_d_p[1]}]
set_property PACKAGE_PIN E2 [get_ports {hdmi_d_n[1]}]
set_property PACKAGE_PIN G2 [get_ports {hdmi_d_p[2]}]
set_property PACKAGE_PIN G1 [get_ports {hdmi_d_n[2]}]
set_property PACKAGE_PIN D5 [get_ports {hdmi_d_p[3]}]
set_property PACKAGE_PIN E5 [get_ports {hdmi_d_n[3]}]
set_property PACKAGE_PIN D4 [get_ports hdmi_clk_p]
set_property PACKAGE_PIN C4 [get_ports hdmi_clk_n]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_p[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_n[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_p[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_n[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_p[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_n[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_p[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hdmi_d_n[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports hdmi_clk_p]
set_property IOSTANDARD LVCMOS33 [get_ports hdmi_clk_n]

# ── I2S placeholders ─────────────────────────────────────
# Routed to J10 PMOD pins for deterministic pad placement.
set_property PACKAGE_PIN G5 [get_ports i2s_bclk]
set_property PACKAGE_PIN E6 [get_ports i2s_lrclk]
set_property PACKAGE_PIN G7 [get_ports i2s_dout]
set_property IOSTANDARD LVCMOS33 [get_ports i2s_bclk]
set_property IOSTANDARD LVCMOS33 [get_ports i2s_lrclk]
set_property IOSTANDARD LVCMOS33 [get_ports i2s_dout]
