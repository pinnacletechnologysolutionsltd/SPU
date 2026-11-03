#!/usr/bin/env python3
"""Compile isolated source mutants and require their designated assertions."""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = "research/h0_phys_1a/h0_cpu_controller.v"
CONTROLS = {
    "short_reset": ("if(!sampled)sampled<=1;else", "if(1'b0)sampled<=1;else", "FAIL registered reset hold edges"),
    "release_early": ("held_word<=0;run_id<=run_id+1'b1;sampled<=0;exec_release<=0;state<=INIT;end", "held_word<=0;run_id<=run_id+1'b1;sampled<=0;exec_release<=1;state<=INIT;end", "FAIL registered reset hold edges"),
    "early_issue": ("wire valid=(state==ISSUE)", "wire valid=(state==ISSUE || state==WAIT_BOOT)", "FAIL premature issue"),
    "stale_completion": ("owned<=1;complete<=0;fault<=0;pc<=0;", "owned<=1;complete<=complete;fault<=0;pc<=0;", "FAIL owned before init"),
    "replayed_start": ("wire start_ok=start && !start_seen &&", "wire start_ok=start &&", "START not replayed"),
}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    source=(ROOT/WRAPPER).read_text();filelist=(ROOT/"research/h0_phys_1a/sources.f").read_text()
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
        # Deliberately bypass reset gating by writing storage inside reset branch.
        bank="research/h0_phys_1a/h0_program_banks.v"
        text=(ROOT/bank).read_text()
        old="if(!base_rst_n) begin\n"
        new=(old+"   if(write_valid) begin if(active_sel) bank0[write_addr]<=write_data; "
             "else bank1[write_addr]<=write_data; end\n")
        if text.count(old)!=1:raise RuntimeError("bank mutation point not unique")
        mutant=temp/"write_during_reset.v";mutant.write_text(text.replace(old,new))
        listing=temp/"write_during_reset.f";listing.write_text(filelist.replace(bank,str(mutant)))
        image=temp/"write_during_reset.vvp"
        compile_run=subprocess.run(["iverilog","-g2012","-s","board_check","-o",str(image),"-f",str(listing),"research/h0_phys_1a/board_check.v"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        (out/"write_during_reset_compile.log").write_text(compile_run.stdout+compile_run.stderr)
        if compile_run.returncode:raise RuntimeError("bank control compile failed")
        run=subprocess.run(["vvp",str(image)],cwd=ROOT,text=True,capture_output=True,timeout=30)
        transcript=run.stdout+run.stderr;(out/"write_during_reset.log").write_text(transcript)
        if run.returncode==0 or "FAIL no write while base reset" not in transcript:
            raise RuntimeError("bank reset write control not detected")
        line="write_during_reset DETECTED: FAIL no write while base reset"
        print(line,flush=True);summary.append(line)
        # Bypass reset priority only when a normal write is presented. The
        # dedicated bench forces loading/count to isolate this condition.
        old="if(!base_rst_n) begin\n"
        new="if(!base_rst_n && !write_valid) begin\n"
        mutant=temp/"normal_write_bypass.v";mutant.write_text(text.replace(old,new))
        image=temp/"normal_write_bypass.vvp"
        compile_run=subprocess.run(["iverilog","-g2012","-s","bank_reset_gate_check","-o",str(image),str(mutant),"research/h0_phys_1a/bank_reset_gate_check.v"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        (out/"normal_write_bypass_compile.log").write_text(compile_run.stdout+compile_run.stderr)
        if compile_run.returncode:raise RuntimeError("normal-path control compile failed")
        run=subprocess.run(["vvp",str(image)],cwd=ROOT,text=True,capture_output=True,timeout=30)
        transcript=run.stdout+run.stderr;(out/"normal_write_bypass.log").write_text(transcript)
        if run.returncode==0 or "FAIL reset blocks normal write" not in transcript:
            raise RuntimeError("normal-path reset bypass not detected")
        line="normal_write_bypass DETECTED: FAIL reset blocks normal write"
        print(line,flush=True);summary.append(line)
        # First START remains intact; only a later START releases reset early.
        original=(ROOT/WRAPPER).read_text()
        old="held_word<=0;run_id<=run_id+1'b1;sampled<=0;exec_release<=0;state<=INIT;end"
        new="held_word<=0;run_id<=run_id+1'b1;sampled<=0;exec_release<=(run_id!=0);state<=INIT;end"
        if original.count(old)!=1:raise RuntimeError("restart mutation point not unique")
        mutant=temp/"restart_short_reset.v";mutant.write_text(original.replace(old,new))
        listing=temp/"restart_short_reset.f";listing.write_text(filelist.replace(WRAPPER,str(mutant)))
        image=temp/"restart_short_reset.vvp"
        compile_run=subprocess.run(["iverilog","-g2012","-s","cpu_check","-o",str(image),"-f",str(listing)],cwd=ROOT,text=True,capture_output=True,timeout=30)
        (out/"restart_short_reset_compile.log").write_text(compile_run.stdout+compile_run.stderr)
        if compile_run.returncode:raise RuntimeError("restart control compile failed")
        run=subprocess.run(["vvp",str(image),"+immediate_restart"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        transcript=run.stdout+run.stderr;(out/"restart_short_reset.log").write_text(transcript)
        if run.returncode==0 or "FAIL restart sampled reset edges" not in transcript:
            raise RuntimeError("short restart reset not detected")
        line="restart_short_reset DETECTED: FAIL restart sampled reset edges"
        print(line,flush=True);summary.append(line)
    (out/"summary.txt").write_text("\n".join(summary)+"\n")

if __name__=="__main__":main()
