#!/usr/bin/env python3
"""Compile isolated mutants; demand the intended assertion for each."""
from pathlib import Path
import subprocess
import tempfile

base=Path('research/h0_uart_1a')
controls=[
 ('checksum','CHECK:if(rx_data!=checksum)',"CHECK:if(1'b0)",'adapter_check','bad checksum issued'),
 ('acceptance', 'WAIT_ACCEPT:if(req_ready)begin req_valid<=0;if(done_valid)', "WAIT_ACCEPT:if(req_ready)begin req_valid<=0;if(1'b1)",'adapter_check','accept mistaken for completion'),
 ('load_length',"8'h01:valid_length=(len==4 || len==9);","8'h01:valid_length=(len==4 || len==8 || len==9);",'adapter_check','invalid LOAD length issued'),
 ('endpoint_length','WAIT_DONE:if(done_valid)begin if(done_len>24)',"WAIT_DONE:if(done_valid)begin if(1'b0)",'adapter_check','oversized endpoint response accepted'),
 ('quiet_drain','if(drain_pending)state<=DRAIN;else state<=IDLE;','state<=IDLE;','embedded_check','embedded bad-version request'),
 ('oversize_discard',"if(rx_data>9)begin discard_left<={1'b0,rx_data}+9'd1;state<=DISCARD;end",'if(rx_data>9)reply(command,BAD_LENGTH,0,0);','embedded_check','embedded oversize request'),
]
with tempfile.TemporaryDirectory(prefix='h0-uart-mut-') as tmp:
 tmp=Path(tmp)
 for name,old,new,top,expected in controls:
  source=(base/'h0_uart_adapter.v').read_text()
  if source.count(old)!=1:raise SystemExit(f'{name}: mutation target not unique')
  mutant=tmp/'mutant.v';mutant.write_text(source.replace(old,new))
  files=[str(mutant),str(base/(top+'.v'))]
  if top=='embedded_check':files += [str(base/x) for x in ('uart_rx.v','uart_tx.v','h0_uart_link.v')]
  exe=tmp/'test.vvp'
  subprocess.run(['iverilog','-g2012','-s',top,'-o',str(exe),*files],check=True,capture_output=True,text=True)
  result=subprocess.run(['vvp',str(exe)],capture_output=True,text=True,timeout=20)
  text=result.stdout+result.stderr
  if result.returncode==0 or expected not in text:raise SystemExit(f'{name}: expected assertion {expected!r}; got {text}')
  print(f'{name}: DETECTED ({expected})')
