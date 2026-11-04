#!/usr/bin/env python3
"""Static order checks and negative controls; not a Vivado execution."""
from pathlib import Path
s=Path('research/h0_board_uart_1a/implement.tcl').read_text()
def check(t):
 markers=['synth_design -top','h0_uart_sync_gate pre_opt','h0_reachability_gate pre_opt',
          'check_async_reset pre_opt','\n opt_design\n','h0_uart_sync_gate post_opt',
          'h0_reachability_gate post_opt','check_async_reset post_opt','\n place_design\n',
          'check_async_reset placed','\n route_design\n','check_async_reset routed']
 if any(t.count(x)!=1 for x in markers):return False
 if [t.index(x) for x in markers]!=sorted(t.index(x) for x in markers):return False
 return all(x in t for x in ('report_timing_summary','routed_reset_recovery.rpt',
  'routed_reset_removal.rpt','report_cdc','report_clock_interaction','report_drc','report_methodology','check_timing'))
if not check(s):raise SystemExit('flow order or report requirements failed')
if check(s.replace('h0_reachability_gate post_opt','h0_reachability_omitted post_opt')):raise SystemExit('missing-gate control failed')
if check(s.replace('\n place_design\n','\n premature_placement\n',1).replace('\n opt_design\n','\n place_design\n opt_design\n',1)):raise SystemExit('premature-placement control failed')
assert 'set_property PULLTYPE PULLUP [get_ports uart_rx]' in Path('research/h0_board_uart_1a/board.xdc').read_text()
print('FLOW ORDER PASS; missing-gate and premature-placement controls detected; RX pull-up present')
