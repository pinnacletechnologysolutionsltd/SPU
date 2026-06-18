# spu_a7_100t.xdc — QMTech Artix-7 XC7A100T Pin Constraints
# Adjust pin numbers to match your specific QMTech baseboard revision.

# 50 MHz oscillator
set_property PACKAGE_PIN R4  [get_ports clk_100mhz]
set_property IOSTANDARD LVCMOS33 [get_ports clk_100mhz]
create_clock -period 10.000 -name sys_clk [get_ports clk_100mhz]

# Reset (active low)
set_property PACKAGE_PIN T1  [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# ── RP2350 SPI Slave ──────────────────────────────────────
set_property PACKAGE_PIN AA3 [get_ports spi_cs_n]
set_property PACKAGE_PIN AB3 [get_ports spi_sck]
set_property PACKAGE_PIN AB1 [get_ports spi_mosi]
set_property PACKAGE_PIN AA1 [get_ports spi_miso]
set_property IOSTANDARD LVCMOS33 [get_ports {spi_cs_n spi_sck spi_mosi spi_miso}]

# ── UART TX ──────────────────────────────────────────────
set_property PACKAGE_PIN V4  [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

# ── Status LEDs ───────────────────────────────────────────
set_property PACKAGE_PIN L1  [get_ports {led_out[0]}]
set_property PACKAGE_PIN N4  [get_ports {led_out[1]}]
set_property PACKAGE_PIN P3  [get_ports {led_out[2]}]
set_property PACKAGE_PIN P5  [get_ports {led_out[3]}]
set_property PACKAGE_PIN M6  [get_ports fault_led]
set_property IOSTANDARD LVCMOS33 [get_ports {led_out[*] fault_led}]

# ── Sensor inputs ─────────────────────────────────────────
set_property PACKAGE_PIN G2  [get_ports {sensor_in[0]}]
set_property PACKAGE_PIN H2  [get_ports {sensor_in[1]}]
set_property PACKAGE_PIN J3  [get_ports {sensor_in[2]}]
set_property PACKAGE_PIN K1  [get_ports {sensor_in[3]}]
set_property PACKAGE_PIN L4  [get_ports {sensor_in[4]}]
set_property PACKAGE_PIN G1  [get_ports {sensor_in[5]}]
set_property PACKAGE_PIN H4  [get_ports {sensor_in[6]}]
set_property PACKAGE_PIN J5  [get_ports {sensor_in[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sensor_in[*]}]

# ── HDMI/DVI (TMDS differential) — 100T only ─────────────
# Replace with actual QMTech HDMI pin assignments
# set_property PACKAGE_PIN ... [get_ports {hdmi_d_p[0]}]
# set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_p[*] hdmi_clk_p}]
