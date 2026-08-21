#!/usr/bin/env python3
"""run_photonic_optical_depth_sweep.py — E12 of
contract_photonics_optical_depth_2026-08-22.md: tests whether an
independently-established, uncompensated per-op physical loss (1.8 dB,
the existing single-op model's default -- ModelC_NoisyOptical.DEFAULTS,
never carried into the K-chain backend) explains E9's disproportionate
K=8->K=16 detector-noise collapse (R_8/R_16 ~ 23.7x).

PhotonicQuadrayBackendWithLoss subclasses (does not modify)
PhotonicQuadrayBackend, adding the loss to every mirrored op's
destination lane after the parent's exact field update -- a stated model
assumption (contract SS4), not an established physical fact.

Reuses gen_block (E9's generator, not E11's) so baseline conditions can be
checked against E9's own numbers before the loss conditions are trusted.
K in {8, 16}, condition in {baseline, loss}. Grid is NOT locked in advance
(contract SS3) -- PHOTONIC_TRIALS overrides the per-cell trial count for
the smoke/exploration phase; the grid is filled in once located.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_envelope_sweep import gen_block, M_K, BAND, SEED  # noqa: E402
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend  # noqa: E402

LOSS_DB = 1.8
LOSS_LINEAR = 10.0 ** (-LOSS_DB / 20.0)


class PhotonicQuadrayBackendWithLoss(PhotonicQuadrayBackend):
    """PhotonicQuadrayBackend + uncompensated per-op amplitude loss.
    Model assumption (contract SS4): every mirrored op (QLDI/QSUB/ROTC)
    carries the loss uniformly on its destination lane, not just
    QSUB/ROTC. Report results as testing THIS model, not loss in general.
    """

    def _apply_op_field(self, fld, m, qr, op, angle):
        mirrored = super()._apply_op_field(fld, m, qr, op, angle)
        if mirrored:
            lane = op[1]
            fld[lane] = [z * LOSS_LINEAR for z in fld[lane]]
        return mirrored


def cell(K, use_loss, level, n_trials):
    """One (K, condition, det_level) cell: n_trials accepted, arms A/B
    paired, same convention as E8/E9/E11's cell()."""
    master = make_master_rng(SEED)
    backend_cls = PhotonicQuadrayBackendWithLoss if use_loss else PhotonicQuadrayBackend
    pb = backend_cls(deltaT=2.0)
    n_ok_a = n_ok_b = 0
    rejected = 0
    first_failed_hist = [0] * K
    total_m_sum = 0.0
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, K)
        if blk is None:
            rejected += 1
            continue
        ok_a, ff, ok_b, tm = pb.run_chain_noisy([blk], 0.0, 0.0, level, rng)
        n_ok_a += 1 if ok_a else 0
        n_ok_b += 1 if ok_b else 0
        if ff:
            first_failed_hist[min(ff, K) - 1] += 1
        total_m_sum += tm
        accepted += 1
    pa = n_ok_a / n_trials
    pb_ = n_ok_b / n_trials
    ci = 1.96 * (max(pa, pb_) * (1 - max(pa, pb_)) / n_trials) ** 0.5
    return {
        "K": K, "loss": use_loss, "level": level,
        "recovery_A": pa, "recovery_B": pb_,
        "ci": ci, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "first_failed_A_hist": first_failed_hist,
        "mean_total_m": total_m_sum / n_trials,
    }
