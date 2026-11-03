#!/usr/bin/env python3
"""Run independently identified non-equivalent endpoint mutants."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys

out=Path(sys.argv[1]);out.mkdir()
endpoint='research/h0_uart_1c/h0_uart_endpoint.v'
source=Path(endpoint).read_text();manifest=Path('research/h0_uart_1c/sources.f').read_text()
cases={
 'start_always_ok':("if(start_rejected)finish(8'h20,0,0);\n      else if(owned && run_id==prev_run+1'b1)","if(1'b0)finish(8'h20,0,0);\n      else if(1'b1)",'refusals','START with no valid image refused'),
 'result_no_complete':("complete && result_valid==6'h3f","result_valid==6'h3f || 1'b1",'refusals','RESULT before any run refused'),
 'result_no_busy':("else if(owned)finish(8'h22,0,0);",'', 'refusals','RESULT while owned busy'),
 'address_unchecked':('req_len==9 && req_payload[7:0]<14','req_len==9','refusals','address 0x10 refused'),
 'validate_on_accept':('if(command==2)state<=WAIT_VALIDATION;else finish(0,0,0);','finish(0,0,0);','serial_check','response cmd=02 status=20'),
 'reject_ignored':("end else if(bank_reject)finish(8'h20,0,0);","end else if(1'b0)finish(8'h20,0,0);",'refusals','VALIDATE without load refused: response timeout'),
 'status_bits_swapped':('fault,complete,owned,active_valid','fault,owned,complete,active_valid','refusals','STATUS owned flags'),
}
def run(item):
 name,(old,new,top,expected)=item
 if source.count(old)!=1:raise RuntimeError(f'{name}: mutation target not unique')
 d=out/name;d.mkdir();mutant=d/'endpoint.v';mutant.write_text(source.replace(old,new))
 fl=d/'sources.f';fl.write_text(manifest.replace(endpoint,str(mutant)))
 exe=d/'test.vvp';tb=f'research/h0_uart_1c/{top}.v'
 p=subprocess.run(['iverilog','-g2012','-s',top,'-o',str(exe),'-f',str(fl),tb],capture_output=True,text=True,timeout=30)
 if p.returncode:raise RuntimeError(f'{name}: compile failed: {p.stderr}')
 p=subprocess.run(['vvp',str(exe)],capture_output=True,text=True,timeout=50)
 log=p.stdout+p.stderr;(d/'test.log').write_text(log)
 if p.returncode==0 or expected not in log:raise RuntimeError(f'{name}: expected {expected!r}; return={p.returncode}, log={log[-500:]}')
 return f'{name}: DETECTED ({expected})'
with ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(run,cases.items()):print(result,flush=True)
