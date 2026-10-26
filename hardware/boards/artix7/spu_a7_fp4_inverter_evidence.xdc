set_property PACKAGE_PIN M21 [get_ports clk_100mhz]
set_property IOSTANDARD LVCMOS33 [get_ports clk_100mhz]
create_clock -period 20.000 -name sys_clk [get_ports clk_100mhz]

# rst_n (H7) has no external pull on this board. Without a pull it floats,
# and the design that fed it straight into async resets was dead on silicon
# for three weeks (hardware_evidence.md 3.2m). spu_a7_top now debounces the
# pin, so this is belt-and-braces -- it removes the floating condition
# instead of only surviving it. Active-low reset, so PULLUP = not reset.
set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]
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
