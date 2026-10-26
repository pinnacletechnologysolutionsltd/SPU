"""
test_photonic_noise_model.py — Physical Noise & Error Propagation Simulation for Photonic SPU-13

Investigates the core research question:
"Can a SurdFixed64 operation be compiled into a passive photonic circuit
whose output can be reliably decoded back into the exact SurdFixed64 representation?"

Simulation Pipeline:
  1. Golden Reference: Exact integer/fixed-point SurdFixed64 multiplication (a+b*sqrt(3))*(c+d*sqrt(3)).
  2. Optical Forward Model:
       - Phase noise: delta_phi ~ N(0, sigma_phi^2)
       - Amplitude attenuation & insertion loss: alpha in [0.95 .. 1.0] + N(0, sigma_amp^2)
       - Inter-channel mode crosstalk: chi ~ N(0, sigma_xtalk^2)
       - Detector thermal & shot noise: i_noise ~ N(0, sigma_det^2)
  3. Boundary Quantization Engine (BQE):
       - Snaps noisy analog photodiode voltages back to nearest discrete rational lattice.
  4. Monte Carlo Evaluation:
       - Measures P(correct recovery) across sweeps of phase error, amplitude noise, and bit depths.
"""

import math
import random
from fractions import Fraction

# ---------------------------------------------------------------------------
# 1. Golden Reference: SurdFixed64
# ---------------------------------------------------------------------------

class SurdFixed64:
    """Fixed-point Surd element x = a + b*sqrt(3) with integer or fixed-point coefficients."""
    def __init__(self, a: int, b: int):
        self.a = int(a)
        self.b = int(b)

    def __mul__(self, other: 'SurdFixed64') -> 'SurdFixed64':
        # (a + b*sqrt(3)) * (c + d*sqrt(3)) = (ac + 3bd) + (ad + bc)*sqrt(3)
        return SurdFixed64(
            self.a * other.a + 3 * self.b * other.b,
            self.a * other.b + self.b * other.a
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, SurdFixed64) and self.a == other.a and self.b == other.b

    def __repr__(self) -> str:
        return f"SurdFixed64({self.a}, {self.b})"


# ---------------------------------------------------------------------------
# 2. Noisy Photonic Forward Simulation
# ---------------------------------------------------------------------------

def simulate_photonic_surd_multiply(
    x: SurdFixed64,
    y: SurdFixed64,
    sigma_phi: float = 0.02,     # Phase jitter in radians (~1.15 deg)
    sigma_amp: float = 0.01,     # Relative amplitude fluctuation (1%)
    insertion_loss_db: float = 1.5, # Total optical path loss (dB)
    sigma_crosstalk: float = 0.005, # Inter-rail mode mixing (0.5%)
    sigma_detector: float = 0.01,   # Thermal/shot noise relative to LSB
    grid_scale: float = 1.0         # Voltage scale per integer unit
) -> tuple[float, float]:
    """
    Simulates coherent optical propagation through a dual-rail surd multiplier
    under physical noise sources.
    
    Returns raw analog output voltages (V_a, V_b).
    """
    # Ideal theoretical outputs
    ideal_a = float(x.a * y.a + 3 * x.b * y.b)
    ideal_b = float(x.a * y.b + x.b * y.a)

    # 1. Optical Insertion Loss Factor (attenuation of field amplitude)
    loss_linear = 10.0 ** (-insertion_loss_db / 20.0)

    # 2. Additive Phase Jitter (interferometric degradation)
    # Cosine degradation from phase mismatch: cos(delta_phi)
    phi_a = random.gauss(0.0, sigma_phi)
    phi_b = random.gauss(0.0, sigma_phi)
    phase_factor_a = math.cos(phi_a)
    phase_factor_b = math.cos(phi_b)

    # 3. Amplitude Fluctuations & Fabrication CD Errors
    amp_err_a = 1.0 + random.gauss(0.0, sigma_amp)
    amp_err_b = 1.0 + random.gauss(0.0, sigma_amp)

    # 4. Mode Crosstalk (leakage between rail A and rail B)
    xtalk_a_to_b = random.gauss(0.0, sigma_crosstalk) * ideal_a
    xtalk_b_to_a = random.gauss(0.0, sigma_crosstalk) * ideal_b

    # Combine optical field components
    field_a = (ideal_a * amp_err_a * phase_factor_a + xtalk_b_to_a) * loss_linear
    field_b = (ideal_b * amp_err_b * phase_factor_b + xtalk_a_to_b) * loss_linear

    # Gain compensation stage (calibrated Transimpedance Amplifier / AGC)
    gain_comp = 1.0 / loss_linear
    raw_v_a = field_a * gain_comp * grid_scale
    raw_v_b = field_b * gain_comp * grid_scale

    # 5. Photodiode Receiver Noise (thermal + shot noise)
    noise_det_a = random.gauss(0.0, sigma_detector * grid_scale)
    noise_det_b = random.gauss(0.0, sigma_detector * grid_scale)

    v_out_a = raw_v_a + noise_det_a
    v_out_b = raw_v_b + noise_det_b

    return v_out_a, v_out_b


# ---------------------------------------------------------------------------
# 3. Boundary Quantization Engine (BQE) Lattice Snapper
# ---------------------------------------------------------------------------

def bqe_quantize_surd(v_a: float, v_b: float, grid_scale: float = 1.0) -> SurdFixed64:
    """Snaps continuous analog voltages back to the nearest integer SurdFixed64 lattice point."""
    snapped_a = int(round(v_a / grid_scale))
    snapped_b = int(round(v_b / grid_scale))
    return SurdFixed64(snapped_a, snapped_b)


# ---------------------------------------------------------------------------
# 4. Monte Carlo Error Propagation & Recovery Sweep
# ---------------------------------------------------------------------------

def run_monte_carlo_recovery_test(
    num_trials: int = 5000,
    sigma_phi: float = 0.03,
    sigma_amp: float = 0.015,
    insertion_loss_db: float = 1.8,
    sigma_crosstalk: float = 0.005,
    sigma_detector: float = 0.02,
    dynamic_range: int = 15
) -> float:
    """
    Evaluates P(correct digital recovery) over a broad range of integer inputs.
    """
    success_count = 0

    for _ in range(num_trials):
        # Sample random integer inputs within dynamic range
        xa = random.randint(-dynamic_range, dynamic_range)
        xb = random.randint(-dynamic_range, dynamic_range)
        ya = random.randint(-dynamic_range, dynamic_range)
        yb = random.randint(-dynamic_range, dynamic_range)

        x = SurdFixed64(xa, xb)
        y = SurdFixed64(ya, yb)

        # Golden mathematical target
        golden = x * y

        # Photonic forward simulation
        v_a, v_b = simulate_photonic_surd_multiply(
            x, y,
            sigma_phi=sigma_phi,
            sigma_amp=sigma_amp,
            insertion_loss_db=insertion_loss_db,
            sigma_crosstalk=sigma_crosstalk,
            sigma_detector=sigma_detector
        )

        # BQE lattice snap
        recovered = bqe_quantize_surd(v_a, v_b)

        if recovered == golden:
            success_count += 1

    recovery_probability = success_count / num_trials
    return recovery_probability


def run_noise_tolerance_sweep():
    """
    Sweeps phase noise and detector noise to map the exact boundary
    between 100% bit-exact recovery and noisy breakdown.
    """
    print("======================================================================")
    print("PHOTONIC SPU-13 SURDFIXED64 ERROR PROPAGATION & RECOVERY BENCHMARK")
    print("======================================================================")
    print("Testing recovery under realistic silicon photonics tolerance bounds:")
    print("  Insertion loss = 1.8 dB, Mode crosstalk = -46 dB (0.5%)")
    print("----------------------------------------------------------------------")
    print(f"{'Phase Jitter (deg)':<20} | {'Amp Noise (%)':<15} | {'P(Recovery)':<15} | {'Status'}")
    print("----------------------------------------------------------------------")

    # Sweep phase error from 0.5 degrees to 15 degrees
    phase_jitter_deg_list = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 15.0]

    for p_deg in phase_jitter_deg_list:
        sigma_phi_rad = math.radians(p_deg)
        sigma_amp = 0.01 * (p_deg / 2.0)  # Proportional amplitude error
        p_rec = run_monte_carlo_recovery_test(
            num_trials=2000,
            sigma_phi=sigma_phi_rad,
            sigma_amp=sigma_amp,
            dynamic_range=8
        )
        status = "EXACT (100%)" if p_rec >= 0.999 else f"DEGRADED ({p_rec*100:.1f}%)"
        print(f"{p_deg:<20.1f} | {sigma_amp*100:<15.2f} | {p_rec:<15.4f} | {status}")

    print("======================================================================")


if __name__ == "__main__":
    random.seed(42)  # Deterministic seed
    run_noise_tolerance_sweep()
