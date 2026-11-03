#!/usr/bin/env python3
"""Focused successor simulations, mutation controls and independent oracle."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE="research/h0_phys_1a/"
CASES=("normal","stopped","collisions","stale_issue","before_accept","duplicate","held_start","immediate_restart")

def run(command, log):
 p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=30)
 log.write_text(p.stdout+p.stderr)
 if p.returncode: raise RuntimeError("failed: "+" ".join(map(str,command)))
 return p.stdout

def main():
 p=argparse.ArgumentParser();p.add_argument("--output",required=True);a=p.parse_args()
 out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
 files=[x for x in (ROOT/(BASE+"sources.f")).read_text().splitlines() if x and not x.startswith("+")]
 files += [BASE+"sources.f",BASE+"board_check.v",BASE+"bank_reset_gate_check.v",BASE+"board_oracle.py",BASE+"controls.py",BASE+"run.py",
           "hardware/rtl/arch/spu_arch_defines.vh","hardware/rtl/arch/spu_isa_defines.vh",
           "hardware/rtl/core/spu13/fpga_chain_arith.vh","hardware/rtl/core/spu13/spu13_regen_arith.vh"]
 (out/"source_sha256.txt").write_text("".join(hashlib.sha256((ROOT/x).read_bytes()).hexdigest()+"  "+x+"\n" for x in files))
 cpu=out/"cpu.vvp";board=out/"board.vvp"
 run(["iverilog","-g2012","-s","cpu_check","-o",str(cpu),"-f",BASE+"sources.f"],out/"cpu_compile.log")
 for name in CASES:
  output=run(["vvp",str(cpu)]+([] if name=="normal" else ["+"+name]),out/("cpu_"+name+".log"))
  marker="H0_RTL_1F EXPERIMENTAL PASS" if name=="normal" else "CONTROL "+name+" PASS"
  if marker not in output:raise RuntimeError("missing marker "+name)
  print("CPU",name,"PASS",flush=True)
 run(["iverilog","-g2012","-s","board_check","-o",str(board),"-f",BASE+"sources.f",BASE+"board_check.v"],out/"board_compile.log")
 output=run(["vvp",str(board)],out/"board.log")
 if "H0_PHYS_1A BOARD PASS" not in output:raise RuntimeError("board marker missing")
 print("BOARD PASS",flush=True)
 output=run([sys.executable,BASE+"board_oracle.py",str(out/"board.log")],out/"oracle.log")
 if "BOARD_ORACLE PASS" not in output:raise RuntimeError("oracle marker missing")
 print("ORACLE PASS",flush=True)
 bank=out/"bank_gate.vvp"
 run(["iverilog","-g2012","-s","bank_reset_gate_check","-o",str(bank),BASE+"h0_program_banks.v",BASE+"bank_reset_gate_check.v"],out/"bank_gate_compile.log")
 output=run(["vvp",str(bank)],out/"bank_gate.log")
 if "BANK_RESET_GATE PASS" not in output:raise RuntimeError("bank gate marker missing")
 print("BANK RESET PRIORITY PASS",flush=True)
 output=run([sys.executable,BASE+"controls.py","--output",str(out/"controls")],out/"controls.log")
 if len([x for x in output.splitlines() if " DETECTED:" in x])!=8:raise RuntimeError("control count")
 print("EIGHT CONTROLS DETECTED",flush=True)
 (out/"PASS").write_text("H0_PHYS_1A focused simulation PASS\n")

if __name__=="__main__":main()
