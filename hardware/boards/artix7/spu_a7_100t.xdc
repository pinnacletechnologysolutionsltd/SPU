# spu_a7_100t.xdc — QMTech Wukong Artix-7 XC7A100T-FGG676 V02 constraints
# Pins are derived from QMTECH-XC7A100T_200T-Wukong-Board-V02-20210426.pdf.

# 50 MHz oscillator
set_property PACKAGE_PIN M21 [get_ports clk_100mhz]
set_property IOSTANDARD LVCMOS33 [get_ports clk_100mhz]
create_clock -period 20.000 -name sys_clk [get_ports clk_100mhz]

# Reset (active low): KEY0 has a board pull-up and shorts low when pressed.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# ── RP2350 SPI Slave ──────────────────────────────────────
# Wukong J11 PMOD, VCCO_35 = 3V3. Wire RP2350 GP1/GP2/GP3/GP0 to
# J11-1/J11-2/J11-3/J11-4 for the existing header-friendly southbridge pinset.
set_property PACKAGE_PIN H4 [get_ports spi_cs_n]
set_property PACKAGE_PIN F4 [get_ports spi_sck]
set_property PACKAGE_PIN A4 [get_ports spi_mosi]
set_property PACKAGE_PIN A5 [get_ports spi_miso]
set_property IOSTANDARD LVCMOS33 [get_ports spi_cs_n]
set_property IOSTANDARD LVCMOS33 [get_ports spi_sck]
set_property IOSTANDARD LVCMOS33 [get_ports spi_mosi]
set_property IOSTANDARD LVCMOS33 [get_ports spi_miso]

# ── Onboard CP2102N USB-UART ────────────────────────────
# CP2102N RXD is the FPGA transmit path. CP2102N TXD is available on F3, but
# spu_a7_top currently exposes TX only.
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

# ── Status LEDs ───────────────────────────────────────────
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
