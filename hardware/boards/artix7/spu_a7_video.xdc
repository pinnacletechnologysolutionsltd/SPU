# Wukong Artix-7 100T pins for the 640x480 DVI test-pattern spin.
#
# Pinout verified 2026-09-04 against the LiteX qmtech_wukong platform file
# (litex-hub/litex-boards, board revs 1-3) and cross-checked with prjxray
# package_pins.csv for xc7a100tfgg676-1: all eight TMDS pins are genuine
# differential pairs in bank 35 (RIOB33) with correct P/N polarity.

# 50 MHz board oscillator. The port in spu_a7_100t.xdc is misleadingly named
# clk_100mhz; the oscillator is 50 MHz, confirmed by measurement 2026-07-31.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

# rst_n (H7) has no external pull on this board. Without a pull it floats,
# and the design that fed it straight into async resets was dead on silicon
# for three weeks (hardware_evidence.md 3.2m). spu_a7_video_top debounces the
# pin and gates every reset on MMCM lock. Active-low reset, so PULLUP = not
# reset.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]

# ── HDMI connector, driven as DVI ────────────────────────────────────────
# TMDS_33 is a DIFFERENTIAL standard: these pins must be owned by an OBUFDS.
# spu_a7_video_top drives them through hal_hdmi_serdes_a7's OBUFDS, so the
# standard is correct here. Do NOT copy TMDS_33 into spu_a7_100t.xdc, whose
# tops tie the same pins low as two independent single-ended outputs.
#
# There is deliberately no fourth data pair. spu_a7_100t.xdc carried one on
# D5/E5 until 2026-09-04; those pins belong to the J10 expansion header, not
# the HDMI socket.
set_property PACKAGE_PIN D4 [get_ports hdmi_clk_p]
set_property PACKAGE_PIN C4 [get_ports hdmi_clk_n]
set_property PACKAGE_PIN E1 [get_ports {hdmi_d_p[0]}]
set_property PACKAGE_PIN D1 [get_ports {hdmi_d_n[0]}]
set_property PACKAGE_PIN F2 [get_ports {hdmi_d_p[1]}]
set_property PACKAGE_PIN E2 [get_ports {hdmi_d_n[1]}]
set_property PACKAGE_PIN G2 [get_ports {hdmi_d_p[2]}]
set_property PACKAGE_PIN G1 [get_ports {hdmi_d_n[2]}]
set_property IOSTANDARD TMDS_33 [get_ports hdmi_clk_p]
set_property IOSTANDARD TMDS_33 [get_ports hdmi_clk_n]
set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_p[0]}]
set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_n[0]}]
set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_p[1]}]
set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_n[1]}]
set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_p[2]}]
set_property IOSTANDARD TMDS_33 [get_ports {hdmi_d_n[2]}]

# DDC (B2/A2), hot-plug detect (A3) and CEC (B1) exist on the connector but
# are not constrained: this spin transmits blind and reads no EDID.
