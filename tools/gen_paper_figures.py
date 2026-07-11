#!/usr/bin/env python3
"""Generate the synthesis comparison figure for THEOREM_LICENSED_TYPESTATE.

Provenance-driven: every number is PARSED from the named evidence source
at generation time — probe metrics from `build/<name>_nextpnr.log`
(regenerate with the named build script), guard metrics by re-running
`yosys hardware/boards/tang_primer_25k/synth_guard_compare.ys`. Nothing
is hand-embedded, so the figure can never drift from the logs the paper's
Appendix A cites. Missing logs are a hard error naming the build script
to run, never a silently stale bar.

Output: docs/fig_synthesis_comparison.pdf
"""

import os
import re
import subprocess
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# (label, nextpnr log stem, silicon proven, build script)
PROBES = [
    ("Lucas\nPHSLK",    "spu13_lucas_phslk_probe", True,  "build_25k_spu13_lucas_phslk_probe.sh"),
    ("Lucas\nMAC",      "spu13_lucas_mac_probe",   True,  "build_25k_spu13_lucas_mac_probe.sh"),
    ("SPI link\nprobe", "southbridge_spi_probe",   True,  "build_25k_southbridge_spi_probe.sh"),
    ("IROTC\nprobe",    "spu13_irotc_probe",       True,  "build_25k_spu13_irotc_probe.sh"),
    ("IROTC\nSPI core", "spu13_irotc_spi",         False, "build_25k_spu13_irotc_spi.sh"),
    ("RPLU2\narith",    "spu13_rplu2_arith_probe", True,  "build_25k_spu13_rplu2_arith_probe.sh"),
]

GUARD_SYNTH = "hardware/boards/tang_primer_25k/synth_guard_compare.ys"
GUARDS = ["spu13_typestate_guard", "spu13_sva_guard"]


def parse_nextpnr_log(stem, script):
    path = os.path.join(ROOT, "build", f"{stem}_nextpnr.log")
    if not os.path.exists(path):
        sys.exit(f"ERROR: {path} missing — regenerate with `bash {script}`")
    text = open(path).read()
    lut = int(re.findall(r"LUT4:\s+(\d+)/", text)[-1])
    dff = int(re.findall(r"\bDFF:\s+(\d+)/", text)[-1])
    # last report per clock, then the worst clock governs
    fmax_by_clk = {}
    for clk, mhz in re.findall(r"Max frequency for clock\s+'([^']+)': ([0-9.]+) MHz", text):
        fmax_by_clk[clk] = float(mhz)
    if not fmax_by_clk:
        sys.exit(f"ERROR: no Fmax lines in {path}")
    return lut, dff, min(fmax_by_clk.values())


def synth_guards():
    r = subprocess.run(["yosys", os.path.join(ROOT, GUARD_SYNTH)],
                       capture_output=True, text=True, cwd=ROOT)
    if r.returncode:
        sys.exit(f"ERROR: guard synthesis failed:\n{r.stdout[-500:]}")
    metrics = {}
    for mod in GUARDS:
        block = r.stdout.split(f"=== {mod} ===")[1]
        cells = int(re.search(r"(\d+) cells", block).group(1))
        m = re.search(r"(\d+)\s+LUT4", block)
        metrics[mod] = (cells, int(m.group(1)) if m else 0)
    return metrics


probe_rows = [parse_nextpnr_log(stem, script) for _, stem, _, script in PROBES]
labels   = [p[0] for p in PROBES]
silicon  = [p[2] for p in PROBES]
lut4     = [r[0] for r in probe_rows]
dff      = [r[1] for r in probe_rows]
fmax     = [r[2] for r in probe_rows]
guard_metrics = synth_guards()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5),
                               gridspec_kw={'width_ratios': [3, 1]})

x = np.arange(len(labels))
width = 0.35
colors_lut = ['#4472C4' if s else '#D9E2F3' for s in silicon]
colors_dff = ['#ED7D31' if s else '#FCE4D6' for s in silicon]

ax1.bar(x - width/2, lut4, width, label='LUT4', color=colors_lut, edgecolor='white')
ax1.bar(x + width/2, dff, width, label='DFF', color=colors_dff, edgecolor='white')
ax1.set_ylabel('Cell count')
ax1.set_title('Probe-top resource utilization (Tang 25K, post-route)')
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=8)
ax1.legend(loc='upper left', fontsize=8)
ax1.set_yscale('log')
ax1.grid(axis='y', alpha=0.3)

for i, (l, d, f) in enumerate(zip(lut4, dff, fmax)):
    ax1.annotate(f'{f:.0f} MHz', (x[i], max(l, d)), textcoords="offset points",
                 xytext=(0, 5), ha='center', fontsize=7, color='#555555')
for i, s in enumerate(silicon):
    if s:
        ax1.annotate('✓', (x[i], lut4[i] * 1.15), ha='center', fontsize=10,
                     color='#2E7D32', fontweight='bold')

# ── Guard comparison inset: identical total cells is the headline ──
gx = np.arange(len(GUARDS))
gcells = [guard_metrics[m][0] for m in GUARDS]
glut = [guard_metrics[m][1] for m in GUARDS]
ax2.bar(gx, gcells, color=['#4472C4', '#A5A5A5'], edgecolor='white', width=0.5)
ax2.set_ylabel('Post-synth cells (total)')
ax2.set_title('Guard comparison\n(identical area)')
ax2.set_xticks(gx)
ax2.set_xticklabels(['Typestate\nlattice', 'SVA-style\nflags'], fontsize=9)
ax2.grid(axis='y', alpha=0.3)
for i, (c, l) in enumerate(zip(gcells, glut)):
    ax2.annotate(f'{c} cells\n({l} LUT4)', (gx[i], c), textcoords="offset points",
                 xytext=(0, 5), ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
out = os.path.join(ROOT, 'docs', 'fig_synthesis_comparison.pdf')
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved {out}")
print("Sources:", ", ".join(f"build/{stem}_nextpnr.log" for _, stem, _, _ in PROBES),
      f"+ live yosys run of {GUARD_SYNTH}")
for lbl, l, d, f in zip(labels, lut4, dff, fmax):
    print(f"  {lbl.replace(chr(10), ' '):16s} LUT4={l:6d} DFF={d:6d} Fmax={f:6.1f}")
for m in GUARDS:
    print(f"  {m:32s} cells={guard_metrics[m][0]} LUT4={guard_metrics[m][1]}")
