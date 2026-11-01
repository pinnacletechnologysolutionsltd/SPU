# CPU-BOARD-3 Phase S: board-facing constraints, V03-derived (spu_strategy/cpu_phy_p0/board_evidence/V03_SCHEMATIC_EVIDENCE.md, sha256 d3680a6d...).
# Deliberately NOT carried over from the old r2 XDC: set_false_path on the reset port, ASYNC_REG on rst_sync_reg/cpu_rst_sync_reg, names rst_n / cpu_clk_div_reg.
# raw_rst_n is an asynchronous pushbutton with NO input-delay constraint by owner decision (P3 Option A): an unconstrained external input is a reported limitation.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]
# divide-by-two CPU clock from the supervisor's cpu_clk_reg (instance path cpu/s/cpu_clk_reg in this top); the pin filter keeps the match path-independent
create_generated_clock -name cpu_clk -source [get_pins -hierarchical -filter {NAME =~ */cpu_clk_reg/C}] -divide_by 2 [get_pins -hierarchical -filter {NAME =~ */cpu_clk_reg/Q}]
set_property PACKAGE_PIN H7 [get_ports raw_rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports raw_rst_n]
set_property PULLTYPE PULLUP [get_ports raw_rst_n]
set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
