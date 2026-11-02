#!/usr/bin/env python3
"""Run partial bank simulation and targeted mutants; not a CPU acceptance run."""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research/h0_rtl_1/program_banks.v"
TB = "research/h0_rtl_1/banks_check.v"
MUTANTS = {
    "bank_select": ("active_sel<=!active_sel", "active_sel<=active_sel", "FAIL active word preserved"),
    "early_promote": ("if (check_index==13)", "if (check_index==12)", "FAIL no premature promotion"),
}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--output", required=True); args = p.parse_args()
    out = Path(args.output).resolve(); out.mkdir(parents=True, exist_ok=False)
    text = SRC.read_text(); summary = []
    with tempfile.TemporaryDirectory(prefix="h0_rtl_1_") as tmp:
        tmp = Path(tmp)
        for name in ("normal", *MUTANTS):
            image = tmp / (name + ".vvp")
            if name == "normal":
                sources = ["-f", "research/h0_rtl_1/banks.f"]
            else:
                old, new, expected = MUTANTS[name]
                if text.count(old) != 1: raise RuntimeError("invalid mutation point")
                mutant = tmp / (name + ".v"); mutant.write_text(text.replace(old, new))
                sources = [str(mutant), TB]
            comp = subprocess.run(["iverilog", "-g2012", "-s", "banks_check", "-o", str(image), *sources],
                                  cwd=ROOT, capture_output=True, text=True, timeout=20)
            (out / (name + "_compile.log")).write_text(comp.stdout + comp.stderr)
            if comp.returncode: raise RuntimeError("compile failed: " + name)
            run = subprocess.run(["vvp", str(image)], cwd=ROOT, capture_output=True, text=True, timeout=20)
            log = run.stdout + run.stderr; (out / (name + ".log")).write_text(log)
            if name == "normal":
                if run.returncode or "H0_PROGRAM_BANKS PARTIAL PASS" not in log: raise RuntimeError("normal failed")
                line = "normal PASS"
            else:
                if run.returncode == 0 or expected not in log: raise RuntimeError("mutant not detected: " + name)
                line = name + " DETECTED: " + expected
            print(line); summary.append(line)
    (out / "summary.txt").write_text("\n".join(summary) + "\n")

if __name__ == "__main__": main()
