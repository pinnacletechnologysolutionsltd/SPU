#!/usr/bin/env python3
"""Compile isolated source mutants and require their designated assertions."""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = "research/h0_rtl_1f_r3/cpu_program_probe.v"
CONTROLS = {
    "short_reset": ("if(!sampled)sampled<=1;else", "if(1'b0)sampled<=1;else", "FAIL two reset edges"),
    "early_issue": ("wire valid=(state==ISSUE)", "wire valid=(state==ISSUE || state==WAIT_BOOT)", "FAIL premature issue"),
    "stale_completion": ("owned<=1;complete<=0;fault<=0;pc<=0;", "owned<=1;complete<=complete;fault<=0;pc<=0;", "FAIL owned before init"),
    "replayed_start": ("wire start_ok=start && !start_seen &&", "wire start_ok=start &&", "START not replayed"),
}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    source=(ROOT/WRAPPER).read_text();filelist=(ROOT/"research/h0_rtl_1f_r3/sources.f").read_text()
    summary=[]
    with tempfile.TemporaryDirectory(prefix="h0_r3_") as temp:
        temp=Path(temp)
        for name,(old,new,expected) in CONTROLS.items():
            if source.count(old)!=1:raise RuntimeError("nonunique mutation: "+name)
            mutant=temp/(name+".v");mutant.write_text(source.replace(old,new))
            listing=temp/(name+".f");listing.write_text(filelist.replace(WRAPPER,str(mutant)))
            image=temp/(name+".vvp")
            compile_run=subprocess.run(["iverilog","-g2012","-s","cpu_check","-o",str(image),"-f",str(listing)],cwd=ROOT,text=True,capture_output=True,timeout=30)
            (out/(name+"_compile.log")).write_text(compile_run.stdout+compile_run.stderr)
            if compile_run.returncode:raise RuntimeError("compile failed: "+name)
            run=subprocess.run(["vvp",str(image)]+(["+held_start"] if name=="replayed_start" else []),cwd=ROOT,text=True,capture_output=True,timeout=30)
            text=run.stdout+run.stderr;(out/(name+".log")).write_text(text)
            if run.returncode==0 or expected not in text:raise RuntimeError(name+" did not hit "+expected)
            line=name+" DETECTED: "+expected;print(line,flush=True);summary.append(line)
    (out/"summary.txt").write_text("\n".join(summary)+"\n")

if __name__=="__main__":main()
