#!/usr/bin/env python3
"""
Plot SPU-13 photonic sweep results (run locally or in CI after installing deps).

Produces:
 - results/figures/recovery_vs_sigma_phi.png
 - results/figures/recovery_vs_calibration_error.png
 - results/figures/loss_normalization_comparison.png
 - results/figures/calib_vs_amp_heatmap_det0.png
Requires: numpy, matplotlib
Install: python3 -m pip install matplotlib numpy
Run: python3 plot_photonic_results.py
"""
import os, csv, math
import numpy as np
import matplotlib.pyplot as plt

os.makedirs('results/figures', exist_ok=True)

def read_col(csvpath, xcol=0, ycol=3, skip_header=True):
    xs, ys = [], []
    if not os.path.exists(csvpath):
        return None, None
    with open(csvpath,'r') as f:
        r = csv.reader(f)
        if skip_header:
            next(r, None)
        for row in r:
            try:
                xs.append(float(row[xcol])); ys.append(float(row[ycol]))
            except:
                continue
    return np.array(xs), np.array(ys)

# 1) Recovery vs sigma_phi
x,y = read_col('results/sweeps/sigma_phi_stageB.csv', 0, 3)
if x is not None:
    plt.figure(figsize=(6,4))
    plt.plot(x, y, marker='o')
    plt.xlabel('phase jitter σ_φ (deg)')
    plt.ylabel('Recovery (%)')
    plt.title('Recovery vs Phase Jitter')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/figures/recovery_vs_sigma_phi.png', dpi=150)
    plt.close()

# 2) Recovery vs calibration error
x,y = read_col('results/sweeps/calibration_error_sweep.csv', 0, 3)
if x is not None:
    plt.figure(figsize=(6,4))
    plt.plot(x, y, marker='o')
    plt.xlabel('Calibration error ε_L (fraction)')
    plt.ylabel('Recovery (%)')
    plt.title('Recovery vs Calibration Error')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/figures/recovery_vs_calibration_error.png', dpi=150)
    plt.close()

# 3) Loss normalization comparison
x1,y1 = read_col('results/sweeps/loss_dB_stageB.csv', 0, 3)
x2,y2 = read_col('results/sweeps/loss_normalized_stageB.csv', 0, 3)
if x1 is not None and x2 is not None:
    plt.figure(figsize=(6,4))
    plt.plot(x1, y1, marker='o', label='no normalization')
    plt.plot(x2, y2, marker='o', label='loss normalized')
    plt.xlabel('insertion loss (dB)')
    plt.ylabel('Recovery (%)')
    plt.title('Effect of Loss Normalization')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('results/figures/loss_normalization_comparison.png', dpi=150)
    plt.close()

# 4) Heatmap: calibration error vs amplitude (detector_noise == 0)
csvpath = 'results/sweeps/calib_amp_det_combined.csv'
if os.path.exists(csvpath):
    rows = []
    with open(csvpath,'r') as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            try:
                eps = float(row[0]); amp=float(row[1]); det=float(row[2]); pct=float(row[5])
            except:
                continue
            rows.append((eps,amp,det,pct))
    # filter det == 0
    rows0 = [r for r in rows if abs(r[2]) < 1e-12]
    if rows0:
        eps_vals = sorted(sorted(set([r[0] for r in rows0])))
        amp_vals = sorted(sorted(set([r[1] for r in rows0])))
        Z = np.zeros((len(amp_vals), len(eps_vals)))
        for (eps,amp,det,pct) in rows0:
            i = amp_vals.index(amp); j = eps_vals.index(eps)
            Z[i,j] = pct
        plt.figure(figsize=(7,5))
        im = plt.imshow(Z, origin='lower', aspect='auto',
                        extent=[min(eps_vals), max(eps_vals), min(amp_vals), max(amp_vals)],
                        cmap='viridis')
        plt.colorbar(im, label='Recovery (%)')
        plt.xlabel('ε_L (fraction)')
        plt.ylabel('σ_amp (fraction)')
        plt.title('Recovery (detector_noise=0)')
        plt.tight_layout()
        plt.savefig('results/figures/calib_vs_amp_heatmap_det0.png', dpi=150)
        plt.close()

print('Plots written to results/figures')
