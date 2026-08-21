"""
test_smul_photonic_experiment.py — Three-Model Verification Experiment for Photonic SMUL

Evaluates the central hypothesis:
"Under what physical noise conditions does a passive optical decomposition of SMUL
remain reliably recoverable as the exact digital SurdFixed64 state?"

Architecture:
  Model A (Exact SPU):       Golden digital integer ring multiplication (ac+3bd) + (ad+bc)*sqrt(3).
  Model B (Ideal Optics):    Normalized complex scattering matrix decomposition:
                             y = S_unitary * x  with projective scaling factor.
  Model C (Noisy Optics):    Physical scattering under phase jitter, amplitude error,
                             insertion loss, mode crosstalk, and photodiode thermal noise.

Objective:
  Determine P_correct = P( BQE(F_optical(x, y)) == F_SPU(x, y) ) across parameter sweeps.
"""

import math
import random
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Model A: Golden SPU-13 Exact Digital Reference
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SurdFixed64:
    a: int
    b: int

    def smul(self, other: 'SurdFixed64') -> 'SurdFixed64':
        """Exact integer ring multiplication in Z[sqrt(3)]."""
        # (a + b*sqrt(3)) * (c + d*sqrt(3)) = (ac + 3bd) + (ad + bc)*sqrt(3)
        return SurdFixed64(
            a=self.a * other.a + 3 * self.b * other.b,
            b=self.a * other.b + self.b * other.a
        )


# ---------------------------------------------------------------------------
# Model B: Ideal Optical Scattering Decomposition
# ---------------------------------------------------------------------------

class IdealPhotonicSMUL:
    """
    Implements SMUL via normalized linear transfer matrix decomposition.
    
    The field transformation:
      [ a' ]   [ c  3d ] [ a ]
      [ b' ] = [ d   c ] [ b ]
    
    To implement this passively without violating energy conservation (unitarity S^dagger*S <= I),
    the matrix is normalized by max singular value s_max = |c| + sqrt(3)*|d|,
    and mapped to normalized optical field amplitudes.
    """
    def __init__(self, c: float, d: float):
        self.c = float(c)
        self.d = float(d)
        # Bounding norm for passive scattering
        self.norm = max(abs(self.c) + 3.0 * abs(self.d), abs(self.d) + abs(self.c), 1.0)

    def forward(self, a: float, b: float) -> tuple[float, float, float]:
        """Returns (normalized_field_a, normalized_field_b, scale_norm)."""
        field_a = (self.c * a + 3.0 * self.d * b) / self.norm
        field_b = (self.d * a + self.c * b) / self.norm
        return field_a, field_b, self.norm

    def decode(self, field_a: float, field_b: float, norm: float) -> tuple[float, float]:
        """Projective rescale back to standard field amplitude units."""
        return field_a * norm, field_b * norm


# ---------------------------------------------------------------------------
# Model C: Noisy Physical Optical Propagation & BQE Snapping
# ---------------------------------------------------------------------------

def simulate_noisy_smul(
    x: SurdFixed64,
    y: SurdFixed64,
    sigma_phi: float,          # Phase jitter (radians)
    sigma_amp: float,          # Amplitude fluctuation (relative fraction)
    insertion_loss_db: float,  # Insertion loss (dB)
    sigma_xtalk: float,        # Inter-channel mode crosstalk
    sigma_detector: float      # Detector thermal & shot noise (normalized to LSB)
) -> SurdFixed64:
    """
    Propagates operands through the noisy optical model and snaps state at the BQE.
    """
    model_b = IdealPhotonicSMUL(y.a, y.b)
    field_a, field_b, norm = model_b.forward(float(x.a), float(x.b))

    # 1. Insertion Loss Attenuation
    loss_linear = 10.0 ** (-insertion_loss_db / 20.0)

    # 2. Phase Jitter
    phi_a = random.gauss(0.0, sigma_phi)
    phi_b = random.gauss(0.0, sigma_phi)
    field_a *= math.cos(phi_a)
    field_b *= math.cos(phi_b)

    # 3. Amplitude Noise / Splitting Error
    field_a *= (1.0 + random.gauss(0.0, sigma_amp))
    field_b *= (1.0 + random.gauss(0.0, sigma_amp))

    # 4. Mode Crosstalk
    xtalk_a_to_b = random.gauss(0.0, sigma_xtalk) * field_a
    xtalk_b_to_a = random.gauss(0.0, sigma_xtalk) * field_b
    field_a = (field_a + xtalk_b_to_a) * loss_linear
    field_b = (field_b + xtalk_a_to_b) * loss_linear

    # 5. Electronic Receiver Amplification (Gain = 1 / loss_linear)
    rec_a = field_a / loss_linear
    rec_b = field_b / loss_linear

    # 6. Detector Noise
    rec_a += random.gauss(0.0, sigma_detector)
    rec_b += random.gauss(0.0, sigma_detector)

    # Projective decoding
    v_a, v_b = model_b.decode(rec_a, rec_b, norm)

    # 7. Boundary Quantization Engine (BQE Lattice Snapping)
    snapped_a = int(round(v_a))
    snapped_b = int(round(v_b))

    return SurdFixed64(snapped_a, snapped_b)


# ---------------------------------------------------------------------------
# Monte Carlo Noise Tolerance Surface Evaluation
# ---------------------------------------------------------------------------

def run_three_model_experiment(
    num_trials: int = 5000,
    dynamic_range: int = 7
) -> None:
    print("======================================================================")
    print("THREE-MODEL PHOTONIC SMUL EXPERIMENT: RECOVERY BOUNDARY MAPPING")
    print("======================================================================")
    print(f"Number of Monte Carlo trials per condition: {num_trials}")
    print(f"Dynamic Range: coefficients in [{-dynamic_range} .. {dynamic_range}]")
    print("----------------------------------------------------------------------")
    print(f"{'Phase Jitter σ_φ':<18} | {'Amp Noise σ_A':<15} | {'Loss (dB)':<10} | {'P(Correct)':<12} | {'State'}")
    print("----------------------------------------------------------------------")

    # Sweep phase jitter across realistic to degraded bounds
    test_conditions = [
        (math.radians(0.5), 0.005, 1.5, 0.002, 0.01),
        (math.radians(1.0), 0.010, 1.5, 0.005, 0.02),
        (math.radians(2.0), 0.015, 1.8, 0.005, 0.03),
        (math.radians(3.0), 0.020, 1.8, 0.008, 0.04),
        (math.radians(5.0), 0.030, 2.0, 0.010, 0.05),
        (math.radians(8.0), 0.050, 2.5, 0.015, 0.08),
        (math.radians(12.0), 0.080, 3.0, 0.020, 0.12),
    ]

    for sigma_phi, sigma_amp, loss_db, xtalk, det_noise in test_conditions:
        correct_count = 0
        deg_str = f"{math.degrees(sigma_phi):.1f}°"

        for _ in range(num_trials):
            xa = random.randint(-dynamic_range, dynamic_range)
            xb = random.randint(-dynamic_range, dynamic_range)
            ya = random.randint(-dynamic_range, dynamic_range)
            yb = random.randint(-dynamic_range, dynamic_range)

            x = SurdFixed64(xa, xb)
            y = SurdFixed64(ya, yb)

            # Model A target
            target = x.smul(y)

            # Model C simulated execution
            result = simulate_noisy_smul(
                x, y,
                sigma_phi=sigma_phi,
                sigma_amp=sigma_amp,
                insertion_loss_db=loss_db,
                sigma_xtalk=xtalk,
                sigma_detector=det_noise
            )

            if result == target:
                correct_count += 1

        p_correct = correct_count / num_trials
        regime = "RECOVERABLE" if p_correct >= 0.999 else ("MARGINAL" if p_correct >= 0.95 else "DEGRADED")
        print(f"{deg_str:<18} | {sigma_amp*100:<13.1f}% | {loss_db:<10.1f} | {p_correct:<12.4f} | {regime}")

    print("======================================================================")


if __name__ == "__main__":
    random.seed(1337)
    run_three_model_experiment()
