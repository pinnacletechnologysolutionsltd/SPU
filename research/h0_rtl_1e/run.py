#!/usr/bin/env python3
"""Run frozen-core controlled-reset probe and two assertion-specific mutants."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
F = "research/h0_rtl_1e/sources.f"
WRAPPER = "research/h0_rtl_1e/reset_core_probe.v"

def main():
 p=argparse.ArgumentParser(); p.add_argument("--output",required=True); args=p.parse_args()
 out=Path(args.output).resolve(); out.mkdir(parents=True,exist_ok=False)
 files=(ROOT/F).read_text().splitlines()
 manifest=[F]+[x for x in files if not x.startswith("+")]
 (out/"source_sha256.txt").write_text("\n".join(hashlib.sha256((ROOT/x).read_bytes()).hexdigest()+"  "+x for x in manifest)+"\n")
 source=(ROOT/WRAPPER).read_text(); summary=[]
 with tempfile.TemporaryDirectory(prefix="h0_rtl_1e_") as tmp:
  tmp=Path(tmp)
  for name in ("normal","short_reset","stale_completion"):
   image=tmp/(name+".vvp"); selected=list(files)
   if name!="normal":
    if name=="short_reset":
     old="if(!sampled) sampled<=1; else"; new="if(1'b0) sampled<=1; else"; expected="FAIL reset edge one"
     if source.count(old)!=1: raise RuntimeError("mutation mismatch")
     mutant=source.replace(old,new)
    else:
     old="retired_count<=0; results<=0; result_valid<=0; complete<=0;"
     if source.count(old)!=2: raise RuntimeError("mutation mismatch")
     first,second=source.rsplit(old,1); mutant=first+old.replace("complete<=0;","complete<=complete;")+second
     expected="FAIL init clears completion"
    path=tmp/(name+".v");path.write_text(mutant);selected=[str(path) if x==WRAPPER else x for x in selected]
   f=tmp/(name+".f");f.write_text("\n".join(selected)+"\n")
   comp=subprocess.run(["iverilog","-g2012","-s","probe_tb","-o",str(image),"-f",str(f)],cwd=ROOT,capture_output=True,text=True,timeout=30)
   (out/(name+"_compile.log")).write_text(comp.stdout+comp.stderr)
   if comp.returncode: raise RuntimeError("compile failed: "+name)
   run=subprocess.run(["vvp",str(image)],cwd=ROOT,capture_output=True,text=True,timeout=30)
   log=run.stdout+run.stderr;(out/(name+".log")).write_text(log)
   if name=="normal":
    if run.returncode or "H0_RTL_1E EXPERIMENTAL PASS" not in log: raise RuntimeError("normal failed")
    line="normal PASS"
   else:
    if not run.returncode or expected not in log: raise RuntimeError(name+" missing "+expected)
    line=name+" DETECTED: "+expected
   print(line,flush=True);summary.append(line)
 (out/"summary.txt").write_text("\n".join(summary)+"\n")

if __name__=="__main__":main()
