#!/usr/bin/env python3
# pio_timing_budget.py — RP2350 PIO -> ECP5 parallel bus timing analysis.
#
# Calculates setup/hold margins for the 8-bit half-duplex PIO transport.
# All numbers are estimates using typical FR4 propagation, not simulation.
# Actual margins must be measured on hardware.
#
# Usage:  python3 tools/pio_timing_budget.py

import math

# ─── Configuration ──────────────────────────────────────────────
FREQ_MHZ = 12              # PIO bus clock frequency (MHz)
PCB_TRACE_MM = 40.0        # Max trace length from RP2350 to ECP5 (mm)
PCB_PROP_PS_MM = 6.7       # FR4 propagation delay ~6.7 ps/mm (er ~4.5)
SERIES_R_OHM = 22          # Series termination resistor (Ohm)
FPGA_IO_CAP_PF = 8.0       # ECP5 I/O pin capacitance + PCB via (pF)
RP2350_IO_CAP_PF = 5.0     # RP2350 I/O pin capacitance (pF)
DRIVE_STRENGTH_MA = 8      # RP2350 GPIO drive strength (mA)
VOLTAGE_V = 3.3            # I/O voltage

# ECP5 timing (from datasheet, typical)
T_SETUP_ECP5_NS = 2.5      # ECP5 IOB setup time (ns)
T_HOLD_ECP5_NS = 0.0       # ECP5 IOB hold time (ns)
T_CLK2OUT_RP2350_NS = 3.0  # RP2350 GPIO output valid after clock (ns)

# ─── Calculations ───────────────────────────────────────────────

def main():
    T_CLK_NS = 1000.0 / FREQ_MHZ
    trace_delay_ps = PCB_TRACE_MM * PCB_PROP_PS_MM
    trace_delay_ns = trace_delay_ps / 1000.0

    # RC time constant for series termination
    r_time_constant_ns = SERIES_R_OHM * (FPGA_IO_CAP_PF + RP2350_IO_CAP_PF) / 1000.0

    # Rise time (10%-90%) ~ 2.2 * RC
    t_rise_ns = 2.2 * r_time_constant_ns

    # Total data valid window
    t_valid_ns = T_CLK_NS - T_CLK2OUT_RP2350_NS - trace_delay_ns - t_rise_ns

    # Setup margin
    t_setup_margin_ns = t_valid_ns - T_SETUP_ECP5_NS

    # Hold margin
    t_hold_margin_ns = T_HOLD_ECP5_NS - trace_delay_ns / 1000.0  # conservative
    t_hold_margin_ns = abs(t_hold_margin_ns)  # hold is usually 0 or negative

    print("=" * 60)
    print("  SPU-13 RP2350 PIO -> ECP5 Parallel Bus Timing Budget")
    print("=" * 60)
    print(f"\n  Clock frequency:        {FREQ_MHZ} MHz")
    print(f"  Clock period:           {T_CLK_NS:.2f} ns")
    print(f"  Max PCB trace length:   {PCB_TRACE_MM} mm")
    print(f"  Trace delay:            {trace_delay_ns:.3f} ns ({trace_delay_ps:.0f} ps)")
    print(f"  Series R:               {SERIES_R_OHM} Ohm")
    print(f"  RC rise time (10-90%):  {t_rise_ns:.3f} ns")

    print(f"\n  {'─'*50}")
    print(f"  {'Parameter':<30} {'Value':<12} {'Margin':<12}")
    print(f"  {'─'*50}")
    print(f"  {'Clock period (T_CLK)':<30} {T_CLK_NS:<12.2f} ns")
    print(f"  {'RP2350 clk2out':<30} {T_CLK2OUT_RP2350_NS:<12.2f} ns")
    print(f"  {'Trace delay':<30} {trace_delay_ns:<12.3f} ns")
    print(f"  {'Rise time':<30} {t_rise_ns:<12.3f} ns")
    print(f"  {'Data valid window':<30} {t_valid_ns:<12.3f} ns")
    print(f"  {'ECP5 setup req.':<30} {T_SETUP_ECP5_NS:<12.2f} ns")
    print(f"  {'ECP5 hold req.':<30} {T_HOLD_ECP5_NS:<12.2f} ns")
    print(f"  {'─'*50}")
    print(f"  {'SETUP MARGIN':<30} {t_setup_margin_ns:<12.3f} ns  {t_setup_margin_ns/T_CLK_NS*100:<11.1f}% of period")
    print(f"  {'HOLD MARGIN':<30} {t_hold_margin_ns:<12.3f} ns")
    print(f"  {'─'*50}")

    # Status
    if t_setup_margin_ns > 0 and t_hold_margin_ns > 0:
        print(f"\n  {chr(9632)} PASS: Timing budget closed with margin.")
    else:
        print(f"\n  {chr(9632)} FAIL: Timing budget not closed.")
        if t_setup_margin_ns <= 0:
            print(f"      Setup margin is negative ({t_setup_margin_ns:.3f} ns).")
            print(f"      Options: reduce trace length, increase drive strength,")
            print(f"               reduce frequency, or use DDR mode.")
        if t_hold_margin_ns <= 0:
            print(f"      Hold margin is negative ({t_hold_margin_ns:.3f} ns).")
            print(f"      Options: add delay on data lines, use IOB flip-flops.")

    print(f"\n  {'─'*50}")
    print(f"  Sensitivity Analysis (trace length vs setup margin):")
    print(f"  {'Trace (mm)':<15} {'Delay (ns)':<15} {'Setup Margin (ns)':<20}")
    print(f"  {'─'*15} {'─'*15} {'─'*20}")
    for length_mm in [25, 40, 60, 80, 100]:
        d = length_mm * PCB_PROP_PS_MM / 1000.0
        valid = T_CLK_NS - T_CLK2OUT_RP2350_NS - d - t_rise_ns
        margin = valid - T_SETUP_ECP5_NS
        status = "OK" if margin > 0 else "FAIL"
        print(f"  {length_mm:<15} {d:<15.3f} {margin:<20.3f} {status}")

    print(f"\n  {'─'*50}")
    print(f"  Notes:")
    print(f"  - All numbers are estimates. Measure actual margins on hardware.")
    print(f"  - Add 22 Ohm series resistors on DATA/STB near RP2350 driver.")
    print(f"  - Route DATA[7:0] + STROBE with matched skew < 0.5 ns.")
    print(f"  - Use ground guard traces between adjacent PIO lanes.")
    print(f"  - ECP5 IOB input delay elements can add up to 2 ns adjust.")

if __name__ == "__main__":
    main()
