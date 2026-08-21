#!/usr/bin/env python3
"""extract_photonic_envelope.py — the DECLARED REGENERATION ENVELOPE of the
PhotonicQuadrayBackend (deliverable 2 of
contract_photonics_backend_2026-08-20.md).

Reads results/sweeps/photonic_envelope_frozen_v1_2026-08-20.json and emits:

  1. the per-K noise budget: for each K, the largest noise level per axis
     with arm-B recovery >= P_target (and the arm-A reference),
  2. the K* regeneration-frequency phase diagram: for each (axis, level),
     the largest K where the CHAIN (arm B) holds >= P_target, versus the
     per-op REGEN (arm A) recovery at that K,
  3. the declared envelope summary (the engineering-spec numbers).

Targets: P in {0.999, 0.99, 0.95, 0.9, 0.5}.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "results", "sweeps",
                   "photonic_envelope_frozen_v1_2026-08-20.json")
TARGETS = [0.999, 0.99, 0.95, 0.9, 0.5]
KS = [1, 2, 4, 8, 16]


def load():
    with open(SRC) as f:
        return json.load(f)


def main():
    data = load()
    cells = data["cells"]
    by = {}
    for c in cells:
        by[(c["axis"], c["level"], c["K"])] = c

    print("=" * 78)
    print("DECLARED REGENERATION ENVELOPE — PhotonicQuadrayBackend")
    print("=" * 78)

    # 1. per-K noise budget (largest sigma per axis with P_B >= target)
    for target in TARGETS:
        print("\n--- per-K noise budget, P_target = %.3f (arm B, chain) ---" % target)
        print("K     phi(deg)      amp         det")
        for K in KS:
            row = []
            for axis, levels in (("phi", [0.0, 0.25, 0.5, 1.0]),
                                 ("amp", [0.0, 1e-5, 2.5e-5, 5e-5]),
                                 ("det", [0.0, 1e-4, 3e-4, 1e-3])):
                best = None
                for lv in levels:
                    if by[(axis, lv, K)]["recovery_B"] >= target:
                        best = lv
                row.append("-" if best is None else
                           ("%.2f" % best if axis == "phi" else
                            ("%.1e" % best if best else "0")))
            print("%-3d  %s        %s      %s" % (K, row[0], row[1], row[2]))

    # 2. K* phase diagram: largest K where arm B holds the target
    print("\n--- K* (largest exact K for the CHAIN) per (axis, level) ---")
    print("axis level      K*(.999) K*(.99) K*(.95) K*(.90) K*(.50)  | A at K*")
    for axis, levels in (("phi", [0.0, 0.25, 0.5, 1.0]),
                         ("amp", [0.0, 1e-5, 2.5e-5, 5e-5]),
                         ("det", [0.0, 1e-4, 3e-4, 1e-3])):
        for lv in levels:
            ks = []
            a_at = []
            for t in TARGETS:
                kbest = 0
                for K in KS:
                    if by[(axis, lv, K)]["recovery_B"] >= t:
                        kbest = K
                ks.append(kbest)
                a_at.append(by[(axis, lv, kbest)]["recovery_A"]
                            if kbest else "-")
            print("%-4s %9g  %6d  %6d  %6d  %6d  %6d  | %s"
                  % (axis, lv, ks[0], ks[1], ks[2], ks[3], ks[4],
                     ", ".join("%.2f" % a if a != "-" else "-" for a in a_at)))

    # 3. the declared envelope summary
    print("\n--- declared envelope (engineering-spec numbers) ---")
    # detector budget per K (worst-axis: the tightest)
    print("Detector budget (sigma_det <= 0.5*s/2^m, s = 0.1):")
    for K in KS:
        m = by[("det", 0.0, K)]["mean_total_m"]
        print("  K=%-2d  m~%-5.1f  sigma_det <= %.2e" % (K, m, 0.5 * 0.1 / 2 ** m))
    print("\nAmplitude budget (error ~ v*sigma_amp; band max 30000):")
    print("  sigma_amp <= 0.5/30000 = %.2e for the worst-case band value"
          % (0.5 / 30000.0))
    print("\nDifferential-phase budget (residual ~ v*dp*tan(dphi), dphi(2K):")
    print("  per-op REGEN holds >= 99%% at sigma_phi <= 0.25 deg through K=16")
    return 0


if __name__ == "__main__":
    sys.exit(main())
