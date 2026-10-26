"""Fresh bounded Icarus simulation; no mapping, timing or silicon claims."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))
from sparse_jet_rtl_vectors import write_vectors

SOURCES = ["hardware/rtl/core/spu13/spu13_jet_sparse_idx.v",
           "hardware/rtl/core/spu13/spu13_jet_sparse_mac.v",
           "hardware/rtl/core/spu13/spu13_m31_multiplier.v",
           "hardware/tests/spu13/spu13_jet_sparse_mac_tb.v"]
CONTROLS = {1: "J tag promise violated", 2: "invalid J tag", 3: "noncanonical coefficient",
            4: "completion/count mismatch", 5: "result mismatch", 6: "premature fabric reuse",
            7: "early busy drop", 8: "unsolicited completion", 9: "extra multiply issue"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    parent = ROOT / "build/sparse_jet_mac"
    parent.mkdir(parents=True, exist_ok=True)
    output = args.output or Path(tempfile.mkdtemp(prefix="rtl_focused_", dir=parent))
    if args.output:
        output.mkdir(parents=True, exist_ok=False)
    output = output.resolve()
    commands, results = [], []

    def run(name, command, expected=None):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=25)
        (output / f"{name}.log").write_text(result.stdout + result.stderr)
        commands.append({"name": name, "command": command, "exit": result.returncode})
        if expected is None:
            assert result.returncode == 0, result.stdout + result.stderr
        else:
            assert result.returncode != 0 and expected in result.stdout + result.stderr, result.stdout + result.stderr
            assert "negative control did not trip" not in result.stdout
        return result.stdout

    for n in (2, 4, 15):
        fixture = output / f"n{n}.txt"
        count = write_vectors(fixture, n) if n != 15 else 0
        for delay in ((0, 3, 7) if n != 15 else (0,)):
            label = f"n{n}_delay{delay}"
            binary = output / f"{label}.vvp"
            run(label + "_compile", ["iverilog", "-g2012", "-I", str(ROOT / "hardware/tests/spu13"),
                "-s", "spu13_jet_sparse_mac_tb", f"-Pspu13_jet_sparse_mac_tb.N={n}",
                f"-Pspu13_jet_sparse_mac_tb.DELAY={delay}", "-o", str(binary), *SOURCES])
            stdout = run(label, ["vvp", str(binary), "+WIDTH_ONLY" if n == 15 else f"+VECTORS={fixture}"])
            assert "PASS:" in stdout
            if n != 15:
                assert f"vectors={count + 1} " in stdout, "fixture coverage incomplete"
            results.append({"N": n, "response_delay": delay, "vectors": count, "result": "PASS"})
            if n == 2 and delay == 7:
                for control, message in CONTROLS.items():
                    run(f"negative_{control}", ["vvp", str(binary), f"+NEGATIVE={control}"], message)
    sources = [ROOT / p for p in SOURCES] + list((ROOT / "hardware/tests/spu13").glob("spu13_jet_sparse*.vh"))
    sources += list((ROOT / "software/tests").glob("*sparse_jet*.py"))
    report = {"status": "FOCUSED_RTL_PASS", "configurations": results, "negative_controls": len(CONTROLS),
              "window_pairs": 305, "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},
              "fixture_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob("n*.txt")},
              "claims": {"arithmetic_handshake": "bounded simulation only", "reset_drain": "exclusive-owner harness only",
                         "N15": "tag width only", "full_qualification": "NOT RUN", "mapping_timing_silicon": "NOT RUN"}}
    (output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Evidence: {output}")


if __name__ == "__main__":
    main()
