# RTL-0S out-of-context synthesis constraint: 40.000 ns (25 MHz), the Gen-1 cpu_clk period.
create_clock -period 40.000 -name clk [get_ports clk]
