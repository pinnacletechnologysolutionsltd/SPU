# GPU tranche T1 gate step 1: UART RX on F3, proven in isolation.
#
# F3 is the USB-UART bridge's TXD line (host -> FPGA). The bridge on this
# unit is a CH340 (1a86:7523), not the CP2102N named elsewhere -- corrected
# 2026-09-06, see hardware_evidence.md 3.11. spu_a7_100t.xdc documents it as
# available but unused: TXD "is available on F3, but spu_a7_top currently
# exposes TX only." This spin is the first use of it.
#
# E3 (FPGA -> bridge RXD) is the transmit line already proven in silicon --
# hardware_evidence.md records UARTPROBE repeating "UART:P" cleanly on it.
set_property PACKAGE_PIN M21 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
create_clock -period 20.000 -name sys_clk [get_ports sys_clk]

set_property PACKAGE_PIN H7 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]
set_property PULLTYPE PULLUP [get_ports rst_n]

set_property PACKAGE_PIN F3 [get_ports uart_rx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_rx]
set_property PULLTYPE PULLUP [get_ports uart_rx]

set_property PACKAGE_PIN E3 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports uart_tx]

# NO LED CONSTRAINTS, deliberately. spu_a7_100t.xdc documents led_out[3:0]
# (V17/W21/Y21/V26) as a real, reproducible I/O anomaly on this unit --
# non-logic-level voltages across multiple known-good bitstreams, closed but
# not fixed. The positive control for this probe is the UART banner on E3,
# which is silicon-proven for exactly that duty.
