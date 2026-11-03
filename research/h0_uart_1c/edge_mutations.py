#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
source=Path('research/h0_uart_1a/h0_uart_adapter.v').read_text()
cases=[
 ('simultaneous_length','WAIT_ACCEPT:if(req_ready)begin req_valid<=0;if(done_valid)begin if(done_len>24)',"WAIT_ACCEPT:if(req_ready)begin req_valid<=0;if(done_valid)begin if(1'b0)",'simultaneous oversized response'),
 ('line_activity','rx_valid || rx_error || rx_activity','rx_valid || rx_error','line activity drain'),
]
with tempfile.TemporaryDirectory(prefix='h0-uart-edge-') as d:
 d=Path(d)
 for name,old,new,assertion in cases:
  if old not in source:raise SystemExit(name+': missing mutation target')
  mutant=d/'mutant.v';mutant.write_text(source.replace(old,new));exe=d/'test.vvp'
  subprocess.run(['iverilog','-g2012','-s','edge_check','-o',str(exe),str(mutant),'research/h0_uart_1c/edge_check.v'],check=True,capture_output=True)
  r=subprocess.run(['vvp',str(exe)],capture_output=True,text=True,timeout=10)
  if r.returncode==0 or assertion not in r.stdout+r.stderr:raise SystemExit(name+': intended assertion missing: '+r.stdout+r.stderr)
  print(name,'DETECTED:',assertion)
