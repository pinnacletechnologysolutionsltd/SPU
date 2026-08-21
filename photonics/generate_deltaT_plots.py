#!/usr/bin/env python3
"""
Generate plots and markdown summary for the deltaT sweep.
Creates:
 - results/figures/recovery_vs_deltaT.png
 - results/sweeps/deltaT_sweep_summary.md
"""
import os, csv
import numpy as np
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCSV = os.path.join(ROOT, 'results', 'sweeps', 'deltaT_sweep_full.csv')
OUTDIR = os.path.join(ROOT, 'results', 'figures')
SUMDIR = os.path.join(ROOT, 'results', 'sweeps')
os.makedirs(OUTDIR, exist_ok=True)

if not os.path.exists(INCSV):
    print('Input CSV not found:', INCSV)
    raise SystemExit(1)

deltaT = []
recovery = []
ci_low = []
ci_high = []
mae = []
rmse = []
with open(INCSV,'r') as f:
    r = csv.reader(f)
    header = next(r)
    for row in r:
        try:
            dT = float(row[0])
            trials = int(row[1])
            correct = int(row[2])
            rec = float(row[3])
            low = float(row[4])
            high = float(row[5])
            m = float(row[6]); rm = float(row[7])
        except Exception:
            continue
        deltaT.append(dT)
        recovery.append(rec)
        ci_low.append(low)
        ci_high.append(high)
        mae.append(m)
        rmse.append(rm)

if not deltaT:
    print('No data rows found')
    raise SystemExit(1)

# Sort by deltaT
idx = np.argsort(deltaT)
deltaT = np.array(deltaT)[idx]
recovery = np.array(recovery)[idx]
ci_low = np.array(ci_low)[idx]
ci_high = np.array(ci_high)[idx]
mae = np.array(mae)[idx]
rmse = np.array(rmse)[idx]

# Plot recovery vs deltaT with CI error bars
plt.figure(figsize=(6,4))
plt.errorbar(deltaT, recovery, yerr=[recovery - ci_low, ci_high - recovery], fmt='-o')
plt.xlabel('ΔT (K)')
plt.ylabel('Recovery (%)')
plt.title('Recovery vs Temperature Change ΔT (C2 physical drift)')
plt.grid(True)
plt.tight_layout()
png = os.path.join(OUTDIR, 'recovery_vs_deltaT.png')
plt.savefig(png, dpi=150)
plt.close()

# Summary markdown
md = []
md.append('# DeltaT sweep summary')
md.append('')
md.append('Input CSV: `{}`'.format(INCSV))
md.append('')
md.append('Generated figure: `{}`'.format(png))
md.append('')
md.append('## Statistics')
md.append('')
md.append('- Points: {}'.format(len(deltaT)))
md.append('- deltaT range: [{:.3f}, {:.3f}] K'.format(deltaT.min(), deltaT.max()))
md.append('- Recovery (mean): {:.3f}%'.format(recovery.mean()))
md.append('- Recovery (min): {:.3f}% at ΔT = {:.3f} K'.format(recovery.min(), deltaT[recovery.argmin()]))
md.append('- Recovery (max): {:.3f}% at ΔT = {:.3f} K'.format(recovery.max(), deltaT[recovery.argmax()]))
md.append('')
md.append('## Per-point results')
md.append('')
md.append('| ΔT (K) | Recovery (%) | 95% CI low | 95% CI high | MAE | RMSE |')
md.append('|---:|---:|---:|---:|---:|---:|')
for d, r, lo, hi, m, rm in zip(deltaT, recovery, ci_low, ci_high, mae, rmse):
    md.append('| {:.3f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |'.format(d, r, lo, hi, m, rm))

outmd = os.path.join(SUMDIR, 'deltaT_sweep_summary.md')
with open(outmd, 'w') as f:
    f.write('\n'.join(md))

print('Wrote:', png)
print('Wrote:', outmd)
