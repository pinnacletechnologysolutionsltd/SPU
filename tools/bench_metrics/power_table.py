#!/usr/bin/env python3
"""power_table.py — aggregate power_log.py CSVs into paper-ready tables.

Groups samples by (probe, phase), computes mean/std current, mean bus
voltage, and mean power (per-sample V*I, not mean-V times mean-I), and emits
a markdown table (default) or LaTeX booktabs rows (--latex) matching the
style used in docs/spu13_central_paper.tex.

    python3 tools/bench_metrics/power_table.py build/metrics/*.csv
    python3 tools/bench_metrics/power_table.py --latex build/metrics/*.csv
    python3 tools/bench_metrics/power_table.py --selftest

--trim SECONDS (default 0.5) drops samples at each phase boundary to exclude
connect/reconfigure transients. stdlib only.
"""

import argparse
import csv
import math
import sys
from collections import defaultdict


def load_rows(paths):
    """Yield (probe, phase, t_ms, bus_mV, current_uA) from capture CSVs."""
    for path in paths:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    yield (row["probe"], row["phase"], int(row["t_ms"]),
                           int(row["bus_mV"]), int(row["current_uA"]))
                except (KeyError, ValueError):
                    continue


def trim_group(samples, trim_s):
    """Drop trim_s seconds off each end of a phase's samples (by device time)."""
    if not samples or trim_s <= 0:
        return samples
    t0, t1 = samples[0][0], samples[-1][0]
    lo, hi = t0 + trim_s * 1000, t1 - trim_s * 1000
    kept = [s for s in samples if lo <= s[0] <= hi]
    return kept if kept else samples


def summarize(paths, trim_s):
    groups = defaultdict(list)
    for probe, phase, t_ms, bus_mV, current_uA in load_rows(paths):
        groups[(probe, phase)].append((t_ms, bus_mV, current_uA))

    rows = []
    for (probe, phase), samples in sorted(groups.items()):
        samples.sort()
        samples = trim_group(samples, trim_s)
        n = len(samples)
        i_mA = [s[2] / 1000 for s in samples]
        v_V = [s[1] / 1000 for s in samples]
        p_mW = [s[1] * s[2] / 1e6 for s in samples]  # mV * uA / 1e6 = mW
        mean_i = sum(i_mA) / n
        std_i = math.sqrt(sum((x - mean_i) ** 2 for x in i_mA) / n) if n > 1 else 0.0
        rows.append({
            "probe": probe, "phase": phase,
            "v": sum(v_V) / n, "i": mean_i, "i_std": std_i,
            "p": sum(p_mW) / n, "n": n,
            "dur_s": (samples[-1][0] - samples[0][0]) / 1000 if n > 1 else 0.0,
        })
    return rows


def emit_markdown(rows):
    out = ["| Probe | Phase | V_bus (V) | I (mA) | I std | P (mW) | Samples | Duration (s) |",
           "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        out.append(f"| {r['probe']} | {r['phase']} | {r['v']:.3f} | "
                   f"{r['i']:.1f} | {r['i_std']:.1f} | {r['p']:.1f} | "
                   f"{r['n']} | {r['dur_s']:.0f} |")
    return "\n".join(out)


def emit_latex(rows):
    out = [r"% Probe & Phase & $V_\mathrm{bus}$ (V) & $I$ (mA) & $P$ (mW) \\"]
    for r in rows:
        probe = r["probe"].replace("_", r"\_")
        phase = r["phase"].replace("_", r"\_")
        out.append(f"{probe} & {phase} & {r['v']:.3f} & "
                   f"{r['i']:.1f} $\\pm$ {r['i_std']:.1f} & {r['p']:.1f} \\\\")
    return "\n".join(out)


def selftest():
    """Synthesize a capture, aggregate it, and assert the numbers."""
    import io, tempfile, os
    lines = ["host_iso,probe,phase,t_ms,bus_mV,shunt_uV,current_uA"]
    # 10 s at 10 Hz: idle 100.0 mA then active 250.0 mA, both at 5.000 V
    for k in range(100):
        lines.append(f"x,tprobe,idle,{k * 100},5000,10000,100000")
    for k in range(100):
        lines.append(f"x,tprobe,active,{10000 + k * 100},5000,25000,250000")
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("\n".join(lines))
        path = f.name
    try:
        rows = summarize([path], trim_s=0.5)
        assert len(rows) == 2, rows
        by = {r["phase"]: r for r in rows}
        assert abs(by["idle"]["i"] - 100.0) < 1e-9, by["idle"]
        assert abs(by["active"]["i"] - 250.0) < 1e-9, by["active"]
        assert abs(by["idle"]["p"] - 500.0) < 1e-9, by["idle"]      # mW
        assert abs(by["active"]["p"] - 1250.0) < 1e-9, by["active"]
        assert by["idle"]["i_std"] == 0.0
        # trim: 100 samples spanning 9.9 s, minus 0.5 s each end -> 90 kept
        assert by["idle"]["n"] == 90, by["idle"]["n"]
        print(emit_markdown(rows))
        print()
        print(emit_latex(rows))
        print("\nSELFTEST PASS")
    finally:
        os.unlink(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csvs", nargs="*", help="capture CSVs from power_log.py")
    ap.add_argument("--trim", type=float, default=0.5,
                    help="seconds trimmed at each phase boundary (default 0.5)")
    ap.add_argument("--latex", action="store_true", help="emit LaTeX rows")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    if not args.csvs:
        ap.error("no capture CSVs given (or use --selftest)")

    rows = summarize(args.csvs, args.trim)
    if not rows:
        sys.exit("no valid samples found")
    print(emit_latex(rows) if args.latex else emit_markdown(rows))


if __name__ == "__main__":
    main()
