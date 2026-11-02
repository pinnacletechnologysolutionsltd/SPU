#!/usr/bin/env python3
"""Run frontend checks and named source-mutation controls; preserve transcripts."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "hardware/boards/artix7/wukong_v3/cpu_v02/rtl/cpu_fetch_1b.v"
TEST = "hardware/tests/cpu_frontend_v02/frontend_check.v"
FILELIST = "hardware/tests/cpu_frontend_v02/sources.f"
EXPECTED_SHA256 = "d1f1cb408ba59f02b3faf8256d491b54b4661faeb5c536cdf658be34fe9b7780"
MUTANTS = {
    "rom_word": ("rom[2]=64'h7000020000000200", "rom[2]=64'h7000020000000300", "FAIL instruction word"),
    "pc_skip": ("pc<=pc+1'b1;state<=FETCH", "pc<=pc+2'd2;state<=FETCH", "FAIL pc progression pc=2"),
    "early_halt": ("if(pc==13)", "if(pc==12)", "FAIL pc progression pc=13"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="new evidence directory")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = FRONTEND.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError("frontend source hash does not match frozen manifest: " + digest)
    version = subprocess.check_output(["iverilog", "-V"], text=True,
                                      stderr=subprocess.STDOUT).splitlines()[0]
    summary = ["frontend sha256 " + digest, version]
    print("\n".join(summary), flush=True)
    with tempfile.TemporaryDirectory(prefix="cpu_frontend_v02_") as tmp:
        tmp = Path(tmp)
        for name in ("normal", *MUTANTS):
            image = tmp / (name + ".vvp")
            if name == "normal":
                compile_cmd = ["iverilog", "-g2012", "-s", "tb", "-o", str(image), "-f", FILELIST]
            else:
                old, new, expected = MUTANTS[name]
                text = source.decode("utf-8")
                if text.count(old) != 1:
                    raise RuntimeError(name + ": mutation point is not unique")
                mutant = tmp / (name + ".v")
                mutant.write_text(text.replace(old, new), encoding="utf-8")
                compile_cmd = ["iverilog", "-g2012", "-s", "tb", "-o", str(image), str(mutant), TEST]
            compiled = subprocess.run(compile_cmd, cwd=ROOT, text=True, capture_output=True)
            (output / (name + "_compile.log")).write_text(compiled.stdout + compiled.stderr)
            if compiled.returncode:
                raise RuntimeError(name + ": compilation failed, not a detected mutant")
            run = subprocess.run(["vvp", str(image)], cwd=ROOT, text=True,
                                 capture_output=True, timeout=20)
            transcript = run.stdout + run.stderr
            (output / (name + ".log")).write_text(transcript)
            if name == "normal":
                if run.returncode != 0 or "CPU_FRONTEND PASS:" not in transcript:
                    raise RuntimeError("normal simulation failed")
            elif run.returncode == 0 or not re.search(re.escape(expected) + r"(?=\s|$)", transcript):
                raise RuntimeError(name + ": missing designated detection " + expected)
            line = name + (" PASS" if name == "normal" else " DETECTED: " + expected)
            summary.append(line)
            print(line, flush=True)
    summary.append("CPU_FRONTEND_TEST_1 PASS")
    (output / "summary.txt").write_text("\n".join(summary) + "\n")
    print(summary[-1], flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print("CPU_FRONTEND_TEST_1 FAIL:", exc, file=sys.stderr)
        sys.exit(1)
