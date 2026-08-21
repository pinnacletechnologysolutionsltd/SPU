#!/usr/bin/env python3
"""run_photonic_optical_depth_sweep.py — E12 of
contract_photonics_optical_depth_2026-08-22.md: tests whether the
STOCHASTIC RESIDUAL in per-trial optical loss -- left uncorrected after a
receiver-side gain trim calibrated to the KNOWN MEAN loss L_bar(K) --
explains E9's disproportionate K=8->K=16 detector-noise collapse. (Not
raw uncompensated loss -- see contract SS0 for why that design was
abandoned.)

PhotonicQuadrayBackendWithLoss subclasses (does not modify)
PhotonicQuadrayBackend, adding 1.8 dB/op physical loss to every mirrored
op's destination lane. L_bar(K) is measured empirically (measure_L_bar,
contract SS4b) on a calibration trial range disjoint from every noisy
sweep cell (contract SS3's mandatory separation) -- TRIAL_OFFSET below.

Reuses gen_block (E9's generator) -- the residual-variance hypothesis is
specifically about gen_block's stochastic lane-mixing.
"""
import cmath
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "software", "tests"))

from run_photonic_envelope_sweep import gen_block, M_K, BAND, SEED  # noqa: E402
from test_photonic_models_smul import make_master_rng, trial_rng  # noqa: E402
from test_regen_equivalence import PhotonicQuadrayBackend, CLAMP  # noqa: E402

LOSS_DB = 1.8
LOSS_LINEAR = 10.0 ** (-LOSS_DB / 20.0)
CAL_TRIALS = 2000       # calibration trial-index range: [0, CAL_TRIALS)
TRIAL_OFFSET = CAL_TRIALS  # every noisy cell starts here (contract SS3)


class PhotonicQuadrayBackendWithLoss(PhotonicQuadrayBackend):
    """PhotonicQuadrayBackend + uncompensated per-op amplitude loss.
    Model assumption (contract SS4): every mirrored op (QLDI/QSUB/ROTC)
    carries the loss uniformly on its destination lane."""

    def _apply_op_field(self, fld, m, qr, op, angle):
        mirrored = super()._apply_op_field(fld, m, qr, op, angle)
        if mirrored:
            lane = op[1]
            fld[lane] = [z * LOSS_LINEAR for z in fld[lane]]
        return mirrored


def _replay_field(backend, block):
    """Noiseless field evolution only (no noise draws) -- for L_bar
    measurement, not scoring."""
    fld = [[0j] * 4 for _ in range(13)]
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    angle = 0.0
    for op in block:
        backend._apply_op_field(fld, m, qr, op, angle)
    return fld[0], m[0]


def measure_L_bar(K, n_trials=CAL_TRIALS):
    """Empirical mean compensation factor (contract SS2/SS4b). Paired
    noiseless replays over trial indices [0, n_trials) -- the calibration
    range, never reused by any noisy sweep cell (SS3)."""
    master_base = make_master_rng(SEED)
    master_loss = make_master_rng(SEED)
    pb_base = PhotonicQuadrayBackend(deltaT=2.0)
    pb_loss = PhotonicQuadrayBackendWithLoss(deltaT=2.0)
    ratios = []
    trial = 0
    accepted = 0
    while accepted < n_trials:
        rng_b = trial_rng(master_base, trial)
        rng_l = trial_rng(master_loss, trial)
        trial += 1
        blk = gen_block(rng_b, K)
        if blk is None:
            continue
        blk2 = gen_block(rng_l, K)
        fld_b, _ = _replay_field(pb_base, blk)
        fld_l, _ = _replay_field(pb_loss, blk2)
        norm_b = math.sqrt(sum(abs(z) ** 2 for z in fld_b))
        norm_l = math.sqrt(sum(abs(z) ** 2 for z in fld_l))
        if norm_b > 0:
            ratios.append(norm_l / norm_b)
        accepted += 1
    ratios.sort()
    n = len(ratios)
    mean = sum(ratios) / n
    std = math.sqrt(sum((r - mean) ** 2 for r in ratios) / n)
    return {
        "K": K, "n": n, "mean": mean, "std": std,
        "median": ratios[n // 2],
        "iqr": [ratios[int(0.25 * n)], ratios[int(0.75 * n)]],
        "min": ratios[0], "max": ratios[-1],
        "cv": std / mean if mean else float("nan"),
        "raw": ratios,
    }


def run_chain_compensated(pb, block, sigma_det, rng, L_bar):
    """Arm-B-only scoring with an L_bar gain trim on inphase before the
    BQE. Mirrors run_chain_noisy's field-evolution + arm-B detection
    (test_regen_equivalence.py:344-374); written fresh because that
    method doesn't expose the raw inphase. sigma_phi=sigma_amp=0 always
    (contract SS2 isolates the detector axis)."""
    if hasattr(rng, "normal"):
        draw = lambda mu, sd: float(rng.normal(mu, sd))
    else:
        draw = lambda mu, sd: rng.gauss(mu, sd)
    fld = [[0j] * 4 for _ in range(13)]
    m = [0] * 13
    qr = [[0, 0, 0, 0] for _ in range(13)]
    angle = 0.0
    nd_last = None
    for op in block:
        if pb._apply_op_field(fld, m, qr, op, angle):
            dp, ap, nd = pb._noise_per_op(0.0, 0.0, sigma_det, draw)
            for lane in range(13):
                ln = 1 if lane == 1 else 0
                rot = cmath.exp(1j * (pb.dphi + dp[ln]))
                fld[lane] = [z * rot * ap[ln] for z in fld[lane]]
            angle += pb.dphi
            nd_last = nd
    if nd_last is None:
        return True, 0
    cK = math.cos(angle)
    rec = [[0, 0, 0, 0] for _ in range(13)]
    for lane in range(13):
        ln = 1 if lane == 1 else 0
        for k in range(4):
            inphase = (fld[lane][k].real + nd_last[ln][k]) / L_bar
            v = (1 << m[lane]) * (inphase / cK) / pb.SCALE
            rec[lane][k] = max(-(2 ** 31), min(CLAMP, int(round(v))))
    return rec == qr, max(m)


def cell(K, use_loss, level, n_trials, L_bar=None):
    """One (K, condition, det_level) cell. Trial indices start at
    TRIAL_OFFSET -- disjoint from measure_L_bar's calibration range
    (contract SS3, mandatory)."""
    if use_loss:
        assert L_bar is not None, "comp-loss condition requires L_bar"
        pb = PhotonicQuadrayBackendWithLoss(deltaT=2.0)
    else:
        pb = PhotonicQuadrayBackend(deltaT=2.0)
    master = make_master_rng(SEED)
    n_ok_b = 0
    rejected = 0
    total_m_sum = 0.0
    trial = TRIAL_OFFSET
    accepted = 0
    while accepted < n_trials:
        rng = trial_rng(master, trial)
        trial += 1
        blk = gen_block(rng, K)
        if blk is None:
            rejected += 1
            continue
        if use_loss:
            ok_b, tm = run_chain_compensated(pb, blk, level, rng, L_bar)
        else:
            _, _, ok_b, tm = pb.run_chain_noisy([blk], 0.0, 0.0, level, rng)
        n_ok_b += 1 if ok_b else 0
        total_m_sum += tm
        accepted += 1
    p = n_ok_b / n_trials
    ci = 1.96 * (p * (1 - p) / n_trials) ** 0.5
    return {
        "K": K, "loss": use_loss, "level": level, "L_bar": L_bar,
        "recovery_B": p, "ci": ci, "n_trials": n_trials,
        "rejection": rejected / (rejected + n_trials),
        "mean_total_m": total_m_sum / n_trials,
    }
