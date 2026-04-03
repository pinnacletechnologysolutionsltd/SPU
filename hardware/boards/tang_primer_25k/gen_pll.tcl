# gen_pll.tcl — Generate rPLL IP for Tang Primer 25K
#
# Run this ONCE to generate the correct GOWIN rPLL instantiation.
# Output: hardware/boards/tang_primer_25k/pll_gowin.v
#
# After running, update spu_tang_top.v to replace the stub instantiation
# with the generated pll_gowin.v module.
#
# Usage (Windows, from repo root):
#   "C:\Gowin\Gowin_V1.9.x\IDE\bin\gw_sh.exe" hardware/boards/tang_primer_25k/gen_pll.tcl
#
# Input clock:  50 MHz (sys_clk from Tang Primer 25K oscillator)
# Output clock: 24 MHz (clk_fast for SPU core)
#
# GW5A rPLL parameters for 50 → 24 MHz:
#   Reference divider IDIV_SEL = 1   → ref = 50/2  = 25 MHz
#   Feedback mult     FBDIV_SEL = 23 → VCO = 25×24 = 600 MHz
#   Output divider    ODIV_SEL  = 25 → out = 600/25 = 24 MHz
#   VCO 600 MHz is within GW5A spec (400–800 MHz).
#
# CC0 1.0 Universal.

set OUT_FILE "hardware/boards/tang_primer_25k/pll_gowin.v"

set ip_handle [create_ip_core -name rPLL -version 1.0 -module_name pll_gowin]

set_ip_core_attribute $ip_handle -attr IDIV_SEL   -value 1
set_ip_core_attribute $ip_handle -attr FBDIV_SEL  -value 23
set_ip_core_attribute $ip_handle -attr ODIV_SEL   -value 25
set_ip_core_attribute $ip_handle -attr CLKOUT_FT_DIR  -value 1
set_ip_core_attribute $ip_handle -attr CLKOUT_DLY_STEP -value 0
set_ip_core_attribute $ip_handle -attr CLKOUTP_EN  -value false
set_ip_core_attribute $ip_handle -attr CLKOUTD_EN  -value false
set_ip_core_attribute $ip_handle -attr CLKOUTD3_EN -value false
set_ip_core_attribute $ip_handle -attr RESET_I_EN  -value false
set_ip_core_attribute $ip_handle -attr RESET_O_EN  -value false
set_ip_core_attribute $ip_handle -attr DEVICE      -value GW5A-25

generate_ip_core $ip_handle -file $OUT_FILE

puts "=== rPLL IP generated: $OUT_FILE ==="
puts "Add pll_gowin.v to build.tcl and remove pll_gowin_stub.v"
