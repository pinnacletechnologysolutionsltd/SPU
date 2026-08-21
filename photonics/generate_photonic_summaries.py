#!/usr/bin/env python3
"""
Generate summary heatmaps and tables from calib_amp_det_combined_full.csv
Outputs:
 - results/figures/calib_amp_heatmap_det{det}.png (one per detector_noise)
 - results/sweeps/calib_amp_det_summary.csv
 - results/sweeps/calib_amp_det_summary.md
"""
import os, csv, math
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCSV = os.path.join(ROOT, 'results', 'sweeps', 'calib_amp_det_combined_full.csv')
OUTDIR = os.path.join(ROOT, 'results', 'figures')
SUMDIR = os.path.join(ROOT, 'results', 'sweeps')
os.makedirs(OUTDIR, exist_ok=True)

if not os.path.exists(INCSV):
    print('Input CSV not found:', INCSV)
    raise SystemExit(1)

rows = []
with open(INCSV,'r') as f:
    r = csv.reader(f)
    header = next(r)
    for row in r:
        try:
            eps = float(row[0]); amp = float(row[1]); det = float(row[2]); trials=int(row[3]); correct=int(row[4]); recovery=float(row[5]); ci_low=float(row[6]); ci_high=float(row[7])
            rows.append({'eps':eps,'amp':amp,'det':det,'trials':trials,'correct':correct,'recovery':recovery,'ci_low':ci_low,'ci_high':ci_high})
        except Exception as e:
            continue

# write summary CSV (flat)
summary_csv = os.path.join(SUMDIR, 'calib_amp_det_summary.csv')
with open(summary_csv, 'w') as f:
    w = csv.writer(f)
    w.writerow(['eps_L','sigma_amp','detector_noise','trials','correct','recovery_pct','ci_low','ci_high'])
    for r in rows:
        w.writerow([r['eps'], r['amp'], r['det'], r['trials'], r['correct'], r['recovery'], r['ci_low'], r['ci_high']])

# Organize by detector noise slices
slices = defaultdict(list)
for r in rows:
    slices[r['det']].append(r)

report_lines = []
report_lines.append('# Photonic combined sweep summary')
report_lines.append('')

for det, rlist in sorted(slices.items()):
    eps_vals = sorted(sorted(set([r['eps'] for r in rlist])))
    amp_vals = sorted(sorted(set([r['amp'] for r in rlist])))
    Z = np.zeros((len(amp_vals), len(eps_vals)))
    # build mapping
    mapping = {(r['eps'], r['amp']): r['recovery'] for r in rlist}
    for i, a in enumerate(amp_vals):
        for j, e in enumerate(eps_vals):
            Z[i,j] = mapping.get((e,a), 0.0)
    # save heatmap
    plt.figure(figsize=(6,4))
    im = plt.imshow(Z, origin='lower', aspect='auto', cmap='viridis', extent=[min(eps_vals), max(eps_vals), min(amp_vals), max(amp_vals)])
    plt.colorbar(im, label='Recovery (%)')
    plt.xlabel('Calibration error ε_L (fraction)')
    plt.ylabel('σ_amp (fraction)')
    plt.title(f'Recovery (detector_noise={det})')
    fn = os.path.join(OUTDIR, f'calib_amp_heatmap_det{det}.png')
    plt.tight_layout()
    plt.savefig(fn, dpi=150)
    plt.close()

    # compute thresholds: for each eps, find max amp with recovery >=95%
    thresholds = []
    for j, e in enumerate(eps_vals):
        col = Z[:,j]
        # find max amp index where recovery >=95
        good_idxs = [i for i,v in enumerate(col) if v >= 95.0]
        if good_idxs:
            max_good_amp = amp_vals[max(good_idxs)]
        else:
            max_good_amp = None
        thresholds.append((e, max_good_amp))

    report_lines.append(f'## detector_noise = {det}')
    report_lines.append('')
    report_lines.append('Top 5 cells by recovery:')
    top5 = sorted(rlist, key=lambda x: x['recovery'], reverse=True)[:5]
    for t in top5:
        report_lines.append(f"- eps={t['eps']}, amp={t['amp']}, recovery={t['recovery']:.2f}% (CI {t['ci_low']:.1f}-{t['ci_high']:.1f})")
    report_lines.append('')
    report_lines.append('Worst 5 cells by recovery:')
    bot5 = sorted(rlist, key=lambda x: x['recovery'])[:5]
    for t in bot5:
        report_lines.append(f"- eps={t['eps']}, amp={t['amp']}, recovery={t['recovery']:.2f}% (CI {t['ci_low']:.1f}-{t['ci_high']:.1f})")
    report_lines.append('')
    report_lines.append('95% recovery thresholds by eps (max sigma_amp that achieves >=95% recovery):')
    for e, ma in thresholds:
        report_lines.append(f"- eps={e}: max_sigma_amp_for_95pct={ma}")
    report_lines.append('')

# write markdown report
summary_md = os.path.join(SUMDIR, 'calib_amp_det_summary.md')
with open(summary_md, 'w') as f:
    f.write('\n'.join(report_lines))

print('Wrote summary CSV:', summary_csv)
print('Wrote markdown summary:', summary_md)
print('Wrote heatmaps to', OUTDIR)
