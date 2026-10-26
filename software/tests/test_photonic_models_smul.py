"""
test_photonic_models_smul.py — Three-Model Investigation of SMUL Compilation to Photonics

Implements Models A, B, C to evaluate whether the SPU-13 algebraic ISA can be compiled
into physically realizable optical transfer matrices with bounded error recovery.

Model A: Exact SPU-13 (Digital Oracle)
  - SurdFixed64 multiplication
  - Ground truth target

Model B: Ideal Optical (Noiseless Scattering)
  - Complex field scattering matrix
  - Normalized transfer matrix (addresses non-unitarity)
  - WDM wavelength encoding (λ_a for a, λ_b for b)
  - Ideal photodetector (no noise)
  - BQE quantization to nearest SurdFixed64 point

Model C: Noisy Optical (Physical Realism)
  - Model B + noise sources:
    * Phase jitter (Gaussian)
    * Amplitude fluctuation (Gaussian)
    * Optical loss (fixed dB)
    * Wavelength crosstalk (fixed dB)

Research Question:
  For what noise envelope is P(correct) = P(Q(F_optical(x)) = F_SPU(x)) ≥ 1 - ε?

Wavelength Encoding:
  Surd element (a + b√3) is encoded as two WDM channels:
    - Channel λ_a (rational component): dual-rail E_a = s(a+ - a-)
    - Channel λ_b (algebraic component): dual-rail E_b = s(b+ - b-)
  where a+ = max(a, 0), a- = max(-a, 0), etc.
"""

import math
import random
from typing import Tuple

# Optional numpy RNG utilities (preferred). Fall back to Python's random if numpy not available.
try:
    import numpy as np
    from numpy.random import SeedSequence, default_rng
    _HAS_NUMPY = True
except Exception:
    np = None
    _HAS_NUMPY = False


def make_master_rng(seed: int = 13):
    """Return a master RNG object with spawnable per-trial generators.

    If numpy is available, use SeedSequence and default_rng.spawn-like behavior.
    Otherwise fall back to a deterministic Python RNG factory using hashing.
    """
    if _HAS_NUMPY:
        ss = SeedSequence(seed)
        return ss
    else:
        # Return seed integer to use with hashlib in per-trial generator
        return seed


def trial_rng(master, trial_index: int):
    """Return a per-trial RNG instance with independent sequence.

    If numpy is available, spawn from SeedSequence; otherwise create Python
    random.Random seeded from a stable hash of master and trial_index.
    """
    if _HAS_NUMPY:
        child_ss = SeedSequence(master.entropy, spawn_key=(trial_index,))
        return default_rng(child_ss)
    else:
        # Deterministic fallback
        import hashlib
        seed_bytes = f"{master}-{trial_index}".encode('utf-8')
        h = hashlib.sha256(seed_bytes).digest()
        seed_int = int.from_bytes(h[:8], 'big')
        r = random.Random(seed_int)
        return r


def coherent_inphase(E_real: float, E_imag: float, lo_phase: float = 0.0, lo_amp: float = 1.0) -> float:
    """Compute the in-phase coherent detector output: Re(E * conj(LO)) / |LO|.

    LO = lo_amp * exp(i lo_phase)
    E = E_real + i E_imag
    Re(E * conj(LO)) = E_real * lo_amp * cos(lo_phase) + E_imag * lo_amp * sin(lo_phase)
    Dividing by lo_amp gives E_real*cos(lo_phase) + E_imag*sin(lo_phase)
    """
    return E_real * math.cos(lo_phase) + E_imag * math.sin(lo_phase)


def bqe_quantize_coherent(inphase_a: float, inphase_b: float, sigma_max: float, scale_factor: float = 0.1) -> Tuple[int, int]:
    """Quantize signed in-phase measurements to integer coefficients.

    inphase_* are proportional to s * (coeff) * cos(φ_rel). For ideal LO phase=0,
    inphase ≈ s * coeff. We invert with coeff = sigma_max * round(inphase / s).
    """
    s = scale_factor
    a_rec = int(round(sigma_max * (inphase_a / s)))
    b_rec = int(round(sigma_max * (inphase_b / s)))
    MAX_VAL = 32767
    MIN_VAL = -32768
    a_rec = max(MIN_VAL, min(a_rec, MAX_VAL))
    b_rec = max(MIN_VAL, min(b_rec, MAX_VAL))
    return a_rec, b_rec



class WDMState:
    """Wavelength-encoded dual-rail optical state."""
    
    def __init__(self):
        self.lambda_a = 1550.0  # nm, rational component
        self.lambda_b = 1551.0  # nm, algebraic component (offset for WDM isolation)
        
        # Dual-rail amplitudes (real-valued, non-negative)
        self.E_a_pos = 0.0  # amplitude (rational component, positive)
        self.E_a_neg = 0.0  # amplitude (rational component, negative)
        self.E_b_pos = 0.0  # amplitude (algebraic component, positive)
        self.E_b_neg = 0.0  # amplitude (algebraic component, negative)
        
        # Phase (per rail, in radians)
        self.phi_a = 0.0
        self.phi_b = 0.0
    
    def field_a_complex(self) -> Tuple[float, float]:
        """Complex field for rational component (as real, imag pair)."""
        amp = self.E_a_pos - self.E_a_neg
        real = amp * math.cos(self.phi_a)
        imag = amp * math.sin(self.phi_a)
        return real, imag
    
    def field_b_complex(self) -> Tuple[float, float]:
        """Complex field for algebraic component (as real, imag pair)."""
        amp = self.E_b_pos - self.E_b_neg
        real = amp * math.cos(self.phi_b)
        imag = amp * math.sin(self.phi_b)
        return real, imag
    
    def power_a(self) -> float:
        """Optical power, rational component."""
        real, imag = self.field_a_complex()
        return real**2 + imag**2
    
    def power_b(self) -> float:
        """Optical power, algebraic component."""
        real, imag = self.field_b_complex()
        return real**2 + imag**2
    
    def copy(self):
        """Return a copy of this state."""
        new_state = WDMState()
        new_state.E_a_pos = self.E_a_pos
        new_state.E_a_neg = self.E_a_neg
        new_state.E_b_pos = self.E_b_pos
        new_state.E_b_neg = self.E_b_neg
        new_state.phi_a = self.phi_a
        new_state.phi_b = self.phi_b
        # Preserve complex output fields when present. scattering_transform() sets
        # E_*_real/_imag and coherent detection depends on them; dropping them in a
        # copy silently reduced detection to magnitude-only (0/pi phase), making every
        # phase-noise mode (C0/C1/C2) immune to phase drift for the wrong reason.
        for attr in ('E_a_real', 'E_a_imag', 'E_b_real', 'E_b_imag'):
            if hasattr(self, attr):
                setattr(new_state, attr, getattr(self, attr))
        return new_state


class ModelA_ExactSPU:
    """Model A: Exact SPU-13 SurdFixed64 oracle."""
    
    @staticmethod
    def smul(a: int, b: int, c: int, d: int) -> Tuple[int, int]:
        """
        Surd multiplication: (a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3
        
        Inputs:  (a, b, c, d) ∈ [-32768, 32767]  (SurdFixed64 16-bit signed)
        Output:  (a', b') exact result
        """
        a_prime = a * c + 3 * b * d
        b_prime = a * d + b * c
        
        MAX_VAL = 32767
        MIN_VAL = -32768
        a_prime = max(MIN_VAL, min(a_prime, MAX_VAL))
        b_prime = max(MIN_VAL, min(b_prime, MAX_VAL))
        
        return int(a_prime), int(b_prime)
    
    @staticmethod
    def test_known_vectors() -> bool:
        """Validate against known test vectors."""
        test_cases = [
            (1, 0, 1, 0, 1, 0),      # 1 * 1 = 1
            (1, 1, 1, 1, 4, 2),      # (1+√3)² = 4 + 2√3
            (2, 1, 2, 1, 7, 4),      # (2+√3)² = 7 + 4√3
            (1, 0, 0, 1, 0, 1),      # 1 * √3 = √3
            (3, 0, 3, 0, 9, 0),      # 3 * 3 = 9
            (0, 1, 0, 1, 3, 0),      # √3 * √3 = 3
        ]
        
        all_pass = True
        for a, b, c, d, expected_a, expected_b in test_cases:
            result_a, result_b = ModelA_ExactSPU.smul(a, b, c, d)
            if (result_a, result_b) != (expected_a, expected_b):
                print("FAIL: ({0}+{1}√3)×({2}+{3}√3) = ({4}+{5}√3), "
                      "expected ({6}+{7}√3)".format(a, b, c, d, result_a, result_b, expected_a, expected_b))
                all_pass = False
        
        return all_pass


class ModelB_IdealOptical:
    """Model B: Ideal optical scattering (noiseless, normalized, WDM-encoded)."""
    
    SCALE_FACTOR = 0.1
    
    @staticmethod
    def encode_wdm(a: int, b: int) -> WDMState:
        """Encode (a, b) as WDM dual-rail state."""
        state = WDMState()
        
        if a >= 0:
            state.E_a_pos = ModelB_IdealOptical.SCALE_FACTOR * a
            state.E_a_neg = 0.0
        else:
            state.E_a_pos = 0.0
            state.E_a_neg = ModelB_IdealOptical.SCALE_FACTOR * (-a)
        
        if b >= 0:
            state.E_b_pos = ModelB_IdealOptical.SCALE_FACTOR * b
            state.E_b_neg = 0.0
        else:
            state.E_b_pos = 0.0
            state.E_b_neg = ModelB_IdealOptical.SCALE_FACTOR * (-b)
        
        return state
    
    @staticmethod
    def normalized_smul_matrix(c: int, d: int) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Compute normalized transfer matrix for SMUL."""
        sigma_max = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
        H00 = float(c) / sigma_max
        H01 = (3.0 * float(d)) / sigma_max
        H10 = float(d) / sigma_max
        H11 = float(c) / sigma_max
        return ((H00, H01), (H10, H11))
    
    @staticmethod
    def matrix_vector_multiply(matrix: Tuple[Tuple[float, float], Tuple[float, float]],
                               E_a: Tuple[float, float],
                               E_b: Tuple[float, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Complex matrix-vector multiply: H @ [E_a, E_b]"""
        H00, H01 = matrix[0]
        H10, H11 = matrix[1]
        
        E_a_real, E_a_imag = E_a
        E_b_real, E_b_imag = E_b
        
        E_a_prime_real = H00 * E_a_real + H01 * E_b_real
        E_a_prime_imag = H00 * E_a_imag + H01 * E_b_imag
        
        E_b_prime_real = H10 * E_a_real + H11 * E_b_real
        E_b_prime_imag = H10 * E_a_imag + H11 * E_b_imag
        
        return ((E_a_prime_real, E_a_prime_imag), (E_b_prime_real, E_b_prime_imag))
    
    @staticmethod
    def scattering_transform(state_in: WDMState, c: int, d: int) -> WDMState:
        """Apply ideal optical scattering (noiseless).

        Returns a WDMState containing both the dual-rail amplitudes (for
        compatibility) and the complex output fields (E_real, E_imag) for
        coherent detection.
        """
        E_a_in = state_in.field_a_complex()
        E_b_in = state_in.field_b_complex()
        
        H_norm = ModelB_IdealOptical.normalized_smul_matrix(c, d)
        (E_a_out, E_b_out) = ModelB_IdealOptical.matrix_vector_multiply(H_norm, E_a_in, E_b_in)
        
        state_out = WDMState()
        
        # Store complex field directly for coherent detection
        E_a_real, E_a_imag = E_a_out[0], E_a_out[1]
        E_b_real, E_b_imag = E_b_out[0], E_b_out[1]
        state_out.E_a_real = E_a_real
        state_out.E_a_imag = E_a_imag
        state_out.E_b_real = E_b_real
        state_out.E_b_imag = E_b_imag
        
        # Also populate dual-rail amplitudes (use signed amplitude split) for compatibility
        def split_signed_to_dual(Er: float, Ei: float):
            # Represent complex field as magnitude on a phase-bearing dual-rail channel.
            # Choose nonnegative rails so that reconstruction via (pos-neg)*exp(i phi)
            # reproduces the original complex field when using coherent detection.
            mag = math.sqrt(Er**2 + Ei**2)
            pos = mag
            neg = 0.0
            phase = math.atan2(Ei, Er)
            return pos, neg, phase

        state_out.E_a_pos, state_out.E_a_neg, state_out.phi_a = split_signed_to_dual(E_a_real, E_a_imag)
        state_out.E_b_pos, state_out.E_b_neg, state_out.phi_b = split_signed_to_dual(E_b_real, E_b_imag)
        
        return state_out
    
    @staticmethod
    def ideal_photodetector(state: WDMState) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Ideal photodetector: measure positive and negative rails separately.
        
        Returns ((P_a_pos, P_a_neg), (P_b_pos, P_b_neg)) for dual-rail recovery.
        """
        # Positive and negative rails are on separate wavelengths, detected independently
        P_a_pos = state.E_a_pos ** 2
        P_a_neg = state.E_a_neg ** 2
        P_b_pos = state.E_b_pos ** 2
        P_b_neg = state.E_b_neg ** 2
        
        return ((P_a_pos, P_a_neg), (P_b_pos, P_b_neg))

    @staticmethod
    def ideal_coherent_receiver(state: WDMState, lo_phase: float = 0.0, lo_amp: float = 1.0) -> Tuple[float, float]:
        """Ideal coherent receiver: return in-phase measurement for each channel.

        Computes Re(E_sig * conj(LO)) / |LO| for each of the two channels.
        Uses the complex fields stored in state_out.E_*_real/_imag.
        """
        # Ensure complex fields are available
        if not hasattr(state, 'E_a_real') or not hasattr(state, 'E_a_imag'):
            # Fall back to reconstructing from dual-rail amplitudes
            E_a_real, E_a_imag = state.field_a_complex()
            E_b_real, E_b_imag = state.field_b_complex()
        else:
            E_a_real, E_a_imag = state.E_a_real, state.E_a_imag
            E_b_real, E_b_imag = state.E_b_real, state.E_b_imag

        inphase_a = coherent_inphase(E_a_real, E_a_imag, lo_phase, lo_amp)
        inphase_b = coherent_inphase(E_b_real, E_b_imag, lo_phase, lo_amp)
        return inphase_a, inphase_b
    
    @staticmethod
    def bqe_quantize(P_a_pos: float, P_a_neg: float, P_b_pos: float, P_b_neg: float, 
                     sigma_max: float = 1.0, scale_factor: float = None) -> Tuple[int, int]:
        """Boundary Quantization Engine: recover signed coefficients from dual-rail powers.
        
        In dual-rail encoding:
        - E_a_pos = max(a, 0) * scale_factor → P_a_pos = E_a_pos²
        - E_a_neg = max(-a, 0) * scale_factor → P_a_neg = E_a_neg²
        - The transfer matrix is normalized by sigma_max for passivity
        - Output power is scaled by 1/sigma_max²
        - Recovered coefficient: a = sigma_max * (sqrt(P_a_pos) / s - sqrt(P_a_neg) / s)
        """
        if scale_factor is None:
            scale_factor = ModelB_IdealOptical.SCALE_FACTOR
        
        # Recover signed coefficients, accounting for sigma_max normalization
        a_pos_val = math.sqrt(P_a_pos) / scale_factor if P_a_pos > 0 else 0
        a_neg_val = math.sqrt(P_a_neg) / scale_factor if P_a_neg > 0 else 0
        a_recovered = int(round(sigma_max * (a_pos_val - a_neg_val)))
        
        b_pos_val = math.sqrt(P_b_pos) / scale_factor if P_b_pos > 0 else 0
        b_neg_val = math.sqrt(P_b_neg) / scale_factor if P_b_neg > 0 else 0
        b_recovered = int(round(sigma_max * (b_pos_val - b_neg_val)))
        
        MAX_VAL = 32767
        MIN_VAL = -32768
        a_recovered = max(MIN_VAL, min(a_recovered, MAX_VAL))
        b_recovered = max(MIN_VAL, min(b_recovered, MAX_VAL))
        
        return a_recovered, b_recovered
    
    @staticmethod
    def smul(a: int, b: int, c: int, d: int) -> Tuple[int, int]:
        """Full SMUL pipeline: encode -> scattering -> coherent detect -> quantize."""
        state_in = ModelB_IdealOptical.encode_wdm(a, b)
        state_out = ModelB_IdealOptical.scattering_transform(state_in, c, d)
        
        # Coherent detection (ideal LO phase = 0)
        inphase_a, inphase_b = ModelB_IdealOptical.ideal_coherent_receiver(state_out, lo_phase=0.0, lo_amp=ModelB_IdealOptical.SCALE_FACTOR)
        
        # Compute sigma_max (same normalization factor used in the transfer matrix)
        sigma_max = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
        
        a_result, b_result = bqe_quantize_coherent(inphase_a, inphase_b, sigma_max, ModelB_IdealOptical.SCALE_FACTOR)
        
        return a_result, b_result


class GaussianNoise:
    """Simple Gaussian noise generator using Box-Muller transform."""
    
    @staticmethod
    def normal(mu: float = 0.0, sigma: float = 1.0) -> float:
        """Generate Gaussian random variable."""
        u1 = random.random()
        u2 = random.random()
        z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        return mu + sigma * z0


class ModelC_NoisyOptical:
    """Model C: Noisy optical with sweep parameters."""
    
    DEFAULTS = {
        'sigma_phi': 0.5 * math.pi / 180.0,
        'sigma_amp': 0.0025,
        'loss_dB': 1.8,
    }

    @staticmethod
    def compute_physical_phase_drift(deltaT: float, deltaL: float, dn_eff_dT: float, n_eff: float, dDeltaL_dT: float, lam_nm: float, dphi_dlambda: float, delta_lambda: float) -> float:
        """Compute approximate phase drift (radians) for a path given thermal and wavelength perturbations.

        Uses the linearized expression:
            δφ = (2π/λ) * [ ΔL * (dn_eff/dT) + n_eff * dΔL/dT ] * ΔT  +  (∂φ/∂λ) * δλ

        Inputs:
          - deltaT: temperature change (K)
          - deltaL: static path length difference (m)
          - dn_eff_dT: derivative of effective index with respect to T (1/K)
          - n_eff: effective index (unitless)
          - dDeltaL_dT: derivative of path length mismatch with respect to T (m/K)
          - lam_nm: nominal wavelength in nm
          - dphi_dlambda: derivative of phase with respect to wavelength (rad/nm)
          - delta_lambda: wavelength perturbation (nm)

        Returns phase shift in radians.
        """
        # Convert nm to meters
        lam_m = lam_nm * 1e-9
        term = (deltaL * dn_eff_dT) + (n_eff * dDeltaL_dT)
        delta_phi_thermal = (2.0 * math.pi / lam_m) * term * deltaT
        delta_phi_wavelength = dphi_dlambda * delta_lambda
        return delta_phi_thermal + delta_phi_wavelength

    @staticmethod
    def add_phase_jitter(state: WDMState, sigma_phi: float) -> WDMState:
        """Add Gaussian phase jitter to each rail."""
        state_noisy = state.copy()
        state_noisy.phi_a += GaussianNoise.normal(0, sigma_phi)
        state_noisy.phi_b += GaussianNoise.normal(0, sigma_phi)
        return state_noisy
    
    @staticmethod
    def add_amplitude_noise(state: WDMState, sigma_amp: float, draw=None) -> WDMState:
        """Add Gaussian amplitude fluctuation.

        draw: per-trial RNG callable (mu, sd) -> sample, on the same seeded
        stream as phase and detector noise. Falls back to the global random
        module only when draw is None (keeps amplitude bit-reproducible when
        the per-trial stream is supplied).
        """
        state_noisy = state.copy()
        if draw is None:
            amp_a = GaussianNoise.normal(1.0, sigma_amp)
            amp_b = GaussianNoise.normal(1.0, sigma_amp)
        else:
            amp_a = draw(1.0, sigma_amp)
            amp_b = draw(1.0, sigma_amp)
        
        state_noisy.E_a_pos *= amp_a
        state_noisy.E_a_neg *= amp_a
        state_noisy.E_b_pos *= amp_b
        state_noisy.E_b_neg *= amp_b
        
        # Also scale complex fields if present
        if hasattr(state_noisy, 'E_a_real') and hasattr(state_noisy, 'E_a_imag'):
            state_noisy.E_a_real *= amp_a
            state_noisy.E_a_imag *= amp_a
        if hasattr(state_noisy, 'E_b_real') and hasattr(state_noisy, 'E_b_imag'):
            state_noisy.E_b_real *= amp_b
            state_noisy.E_b_imag *= amp_b
        
        return state_noisy
    
    @staticmethod
    def add_optical_loss(state: WDMState, loss_dB: float) -> WDMState:
        """Apply fixed optical insertion loss."""
        state_noisy = state.copy()
        loss_linear = 10.0 ** (-loss_dB / 20.0)
        
        state_noisy.E_a_pos *= loss_linear
        state_noisy.E_a_neg *= loss_linear
        state_noisy.E_b_pos *= loss_linear
        state_noisy.E_b_neg *= loss_linear
        
        # Also scale complex fields if present
        if hasattr(state_noisy, 'E_a_real') and hasattr(state_noisy, 'E_a_imag'):
            state_noisy.E_a_real *= loss_linear
            state_noisy.E_a_imag *= loss_linear
        if hasattr(state_noisy, 'E_b_real') and hasattr(state_noisy, 'E_b_imag'):
            state_noisy.E_b_real *= loss_linear
            state_noisy.E_b_imag *= loss_linear
        
        return state_noisy
    
    @staticmethod
    def smul_with_noise(a: int, b: int, c: int, d: int, 
                       sigma_phi: float = None,
                       sigma_amp: float = None,
                       loss_dB: float = None,
                       noise_mode: str = 'C1',
                       lo_track: bool = False,
                       detector_noise: float = 0.0,
                       trial_rng_obj=None,
                       loss_normalize: bool = False,
                       calibration_error: float = 0.0,
                       physical_params: dict = None,
                       debug: bool = False,
                       return_debug: bool = False) -> Tuple[int, int]:
        """Full SMUL pipeline with noise.

        noise_mode: 'C0' = common-phase, 'C1' = differential-phase, 'C2' = physical drift
        lo_track: if True, LO phase follows common-phase (coherent tracking)
        trial_rng_obj: per-trial RNG to draw noise samples (numpy.Generator or random.Random)
        """
        if sigma_phi is None:
            sigma_phi = ModelC_NoisyOptical.DEFAULTS['sigma_phi']
        if sigma_amp is None:
            sigma_amp = ModelC_NoisyOptical.DEFAULTS['sigma_amp']
        if loss_dB is None:
            loss_dB = ModelC_NoisyOptical.DEFAULTS['loss_dB']
        
        # Encode and scatter
        state_in = ModelB_IdealOptical.encode_wdm(a, b)
        state_out = ModelB_IdealOptical.scattering_transform(state_in, c, d)
        
        # Draw phase perturbations
        if trial_rng_obj is None:
            rng = random
            draw = lambda mu, sd: rng.gauss(mu, sd)
        else:
            if _HAS_NUMPY and isinstance(trial_rng_obj, (np.random.Generator,)):
                rng = trial_rng_obj
                draw = lambda mu, sd: float(rng.normal(mu, sd))
            else:
                rng = trial_rng_obj
                draw = lambda mu, sd: rng.gauss(mu, sd)
        
        if noise_mode == 'C0':
            # Common-phase perturbation applied to all rails
            delta_phi = draw(0.0, sigma_phi)
            # Apply same phase to both channels
            # Multiply complex fields by e^{i delta_phi}
            ea_r, ea_i = state_out.E_a_real, state_out.E_a_imag
            eb_r, eb_i = state_out.E_b_real, state_out.E_b_imag
            ca_r = ea_r * math.cos(delta_phi) - ea_i * math.sin(delta_phi)
            ca_i = ea_r * math.sin(delta_phi) + ea_i * math.cos(delta_phi)
            cb_r = eb_r * math.cos(delta_phi) - eb_i * math.sin(delta_phi)
            cb_i = eb_r * math.sin(delta_phi) + eb_i * math.cos(delta_phi)
            state_out.E_a_real, state_out.E_a_imag = ca_r, ca_i
            state_out.E_b_real, state_out.E_b_imag = cb_r, cb_i
            lo_phase = delta_phi if lo_track else 0.0
            _delta_info = ('C0', delta_phi)
        elif noise_mode == 'C1':
            # Independent differential phase per channel
            delta_phi_a = draw(0.0, sigma_phi)
            delta_phi_b = draw(0.0, sigma_phi)
            # Apply independently
            ea_r, ea_i = state_out.E_a_real, state_out.E_a_imag
            eb_r, eb_i = state_out.E_b_real, state_out.E_b_imag
            ca_r = ea_r * math.cos(delta_phi_a) - ea_i * math.sin(delta_phi_a)
            ca_i = ea_r * math.sin(delta_phi_a) + ea_i * math.cos(delta_phi_a)
            cb_r = eb_r * math.cos(delta_phi_b) - eb_i * math.sin(delta_phi_b)
            cb_i = eb_r * math.sin(delta_phi_b) + eb_i * math.cos(delta_phi_b)
            state_out.E_a_real, state_out.E_a_imag = ca_r, ca_i
            state_out.E_b_real, state_out.E_b_imag = cb_r, cb_i
            lo_phase = 0.0
            _delta_info = ('C1', delta_phi_a, delta_phi_b)
        else:
            # C2: physical wavelength/temperature-derived phase drift
            # If physical_params provided, compute deterministic phase drift per-path
            if physical_params and isinstance(physical_params, dict):
                # Expected keys: deltaT (K), deltaL_a (m), deltaL_b (m),
                # dn_eff_dT (1/K), n_eff (unitless), dDeltaL_dT_a (m/K), dDeltaL_dT_b (m/K),
                # lam_a_nm, lam_b_nm (nm), dphi_dlambda_a (rad/nm), dphi_dlambda_b (rad/nm), delta_lambda (nm)
                dp = physical_params
                deltaT = float(dp.get('deltaT', 0.0))
                # Canonical silicon design constants (single source:
                # photonic_experiment_config.PhysicalParams); used only when a
                # partial physical_params dict omits these keys.
                dn_eff_dT = float(dp.get('dn_eff_dT', 1.86e-4))
                n_eff = float(dp.get('n_eff', 2.45))
                dDeltaL_dT_a = float(dp.get('dDeltaL_dT_a', 0.0))
                dDeltaL_dT_b = float(dp.get('dDeltaL_dT_b', 0.0))
                lam_a = float(dp.get('lam_a_nm', state_out.lambda_a))
                lam_b = float(dp.get('lam_b_nm', state_out.lambda_b))
                dphi_dlambda_a = float(dp.get('dphi_dlambda_a', 0.0))
                dphi_dlambda_b = float(dp.get('dphi_dlambda_b', 0.0))
                delta_lambda = float(dp.get('delta_lambda', 0.0))
                deltaL_a = float(dp.get('deltaL_a', 6.4322e-6))  # m, m=10 delay-line
                deltaL_b = float(dp.get('deltaL_b', 6.4322e-6))

                delta_phi_a_base = ModelC_NoisyOptical.compute_physical_phase_drift(deltaT, deltaL_a, dn_eff_dT, n_eff, dDeltaL_dT_a, lam_a, dphi_dlambda_a, delta_lambda)
                delta_phi_b_base = ModelC_NoisyOptical.compute_physical_phase_drift(deltaT, deltaL_b, dn_eff_dT, n_eff, dDeltaL_dT_b, lam_b, dphi_dlambda_b, delta_lambda)
            else:
                # Fall back to independent small random phase per channel
                delta_phi_a_base = draw(0.0, sigma_phi)
                delta_phi_b_base = draw(0.0, sigma_phi)

            # Add stochastic residual around the physical drift if sigma_phi > 0
            residual_a = draw(0.0, sigma_phi) if sigma_phi and sigma_phi > 0.0 else 0.0
            residual_b = draw(0.0, sigma_phi) if sigma_phi and sigma_phi > 0.0 else 0.0
            delta_phi_a = delta_phi_a_base + residual_a
            delta_phi_b = delta_phi_b_base + residual_b

            # Apply phases to complex fields
            ea_r, ea_i = state_out.E_a_real, state_out.E_a_imag
            eb_r, eb_i = state_out.E_b_real, state_out.E_b_imag
            ca_r = ea_r * math.cos(delta_phi_a) - ea_i * math.sin(delta_phi_a)
            ca_i = ea_r * math.sin(delta_phi_a) + ea_i * math.cos(delta_phi_a)
            cb_r = eb_r * math.cos(delta_phi_b) - eb_i * math.sin(delta_phi_b)
            cb_i = eb_r * math.sin(delta_phi_b) + eb_i * math.cos(delta_phi_b)
            state_out.E_a_real, state_out.E_a_imag = ca_r, ca_i
            state_out.E_b_real, state_out.E_b_imag = cb_r, cb_i
            # C0-parity LO semantics: tracking LO phase-locks to the channel-a
            # physical drift (common-mode rejection); fixed LO = ideal reference.
            lo_phase = delta_phi_a if lo_track else 0.0
            _delta_info = ('C2', delta_phi_a, delta_phi_b)
        
        # Apply amplitude noise and loss
        state_out = ModelC_NoisyOptical.add_amplitude_noise(state_out, sigma_amp, draw)
        state_out = ModelC_NoisyOptical.add_optical_loss(state_out, loss_dB)
        
        # Coherent detection with LO
        lo_amp = ModelB_IdealOptical.SCALE_FACTOR
        inphase_a, inphase_b = ModelB_IdealOptical.ideal_coherent_receiver(state_out, lo_phase=lo_phase, lo_amp=lo_amp)
        
        # Detector noise (additive) in the in-phase channel
        if detector_noise and detector_noise > 0.0:
            # draw is defined above closure
            n_a = draw(0.0, detector_noise)
            n_b = draw(0.0, detector_noise)
            inphase_a += n_a
            inphase_b += n_b

        # Optionally undo optical insertion loss (loss-normalized BQE)
        if loss_normalize and loss_dB and loss_dB > 0.0:
            loss_linear = 10.0 ** (-loss_dB / 20.0)
            # Apply calibration error: assumed_loss = loss_linear * (1 + calibration_error)
            assumed_loss = loss_linear * (1.0 + calibration_error)
            if assumed_loss > 0:
                inphase_a = inphase_a / assumed_loss
                inphase_b = inphase_b / assumed_loss
            if debug:
                print(f"  loss_linear={loss_linear:.6f}, calibration_error={calibration_error:.6f}, assumed_loss={assumed_loss:.6f}")

        # Compute sigma_max
        sigma_max = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)

        # Prepare debug_info if requested
        debug_info = {}
        if '_delta_info' in locals():
            debug_info['delta_info'] = _delta_info
        if hasattr(state_out, 'E_a_real'):
            debug_info['E_a_complex'] = (state_out.E_a_real, state_out.E_a_imag)
            debug_info['E_b_complex'] = (state_out.E_b_real, state_out.E_b_imag)
        debug_info['dual_rail'] = {'E_a_pos': state_out.E_a_pos, 'E_a_neg': state_out.E_a_neg, 'E_b_pos': state_out.E_b_pos, 'E_b_neg': state_out.E_b_neg}
        debug_info['inphase'] = {'inphase_a': inphase_a, 'inphase_b': inphase_b}
        if 'loss_linear' in locals():
            debug_info['loss_linear'] = loss_linear
            debug_info['assumed_loss'] = locals().get('assumed_loss', None)

        # Debugging prints
        if debug:
            print("DEBUG SMUL_WITH_NOISE:")
            print(f"  operands a,b,c,d = {a},{b},{c},{d}")
            print(f"  sigma_max = {sigma_max}")
            # complex fields
            if 'E_a_complex' in debug_info:
                ea = debug_info['E_a_complex']; eb = debug_info['E_b_complex']
                print(f"  E_a_complex = ({ea[0]:.6f}, {ea[1]:.6f})")
                print(f"  E_b_complex = ({eb[0]:.6f}, {eb[1]:.6f})")
            print(f"  dual-rail E_a_pos, E_a_neg = {state_out.E_a_pos:.6f}, {state_out.E_a_neg:.6f}")
            print(f"  dual-rail E_b_pos, E_b_neg = {state_out.E_b_pos:.6f}, {state_out.E_b_neg:.6f}")
            print(f"  inphase_a = {inphase_a:.6f}, inphase_b = {inphase_b:.6f}")
            if 'delta_info' in debug_info:
                print(f"  delta_info = {debug_info['delta_info']}")

        a_result, b_result = bqe_quantize_coherent(inphase_a, inphase_b, sigma_max, lo_amp)

        if debug:
            print(f"  quantized -> a_result={a_result}, b_result={b_result}\n")

        if return_debug:
            return a_result, b_result, debug_info
        return a_result, b_result

    @staticmethod
    def smul_chain_with_noise(a: int, b: int, ops, delta_phi_per_op: float,
                              return_states: bool = False):
        """K-op continuous optical chain (contract_photonics_ksweep_2026-08-20).

        Encodes (a,b) and applies `ops` (list of (c,d)) as normalized
        scattering transforms on the continuous complex field — no rounding
        between ops — with a deterministic per-op thermal rotation of
        delta_phi_per_op (rad) on both channels (total rotation K*dphi).
        Returns the unconditioned (A) and conditioned (B, gain-trimmed by
        cos(K*dphi)) BQE recoveries using the total normalization product,
        plus diagnostics: per-op lattice-deviation trajectories (raw and
        rotation-conditioned projections vs the exact big-int intermediate),
        the first boundary-crossing op index, and optionally the intermediate
        complex states.

        Returns (A_a, A_b, B_a, B_b, debug); debug = {
          'total_scale': int, 'K': int, 'first_cross': int|None,
          'dev_uncond': [float], 'dev_cond': [float], 'states': [WDMState]|None}
        """
        s = ModelB_IdealOptical.SCALE_FACTOR
        state = ModelB_IdealOptical.encode_wdm(a, b)
        total_scale = 1
        exact_a, exact_b = a, b
        dev_uncond, dev_cond = [], []
        first_cross = None
        states = [] if return_states else None
        angle = 0.0
        for c, d in ops:
            state = ModelB_IdealOptical.scattering_transform(state, c, d)
            sigma_i = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
            total_scale *= sigma_i
            # deterministic per-op thermal rotation, kept coherent in both
            # representations (dual-rail phase drives the next scatter).
            angle += delta_phi_per_op
            state.phi_a += delta_phi_per_op
            state.phi_b += delta_phi_per_op
            state.E_a_real = (state.E_a_pos - state.E_a_neg) * math.cos(state.phi_a)
            state.E_a_imag = (state.E_a_pos - state.E_a_neg) * math.sin(state.phi_a)
            state.E_b_real = (state.E_b_pos - state.E_b_neg) * math.cos(state.phi_b)
            state.E_b_imag = (state.E_b_pos - state.E_b_neg) * math.sin(state.phi_b)
            # exact intermediate (big int, unclamped) and lattice deviation
            exact_a, exact_b = exact_a * c + 3 * exact_b * d, exact_a * d + exact_b * c
            ia, ib = ModelB_IdealOptical.ideal_coherent_receiver(state, 0.0, s)
            proj_u = (int(round(total_scale * ia / s)), int(round(total_scale * ib / s)))
            dev_uncond.append(max(abs(proj_u[0] - exact_a), abs(proj_u[1] - exact_b)))
            cos_i = math.cos(angle)
            if cos_i > 1e-12:
                proj_c = (int(round(total_scale * ia / (s * cos_i))),
                          int(round(total_scale * ib / (s * cos_i))))
            else:
                proj_c = (0, 0)
            dev_cond.append(max(abs(proj_c[0] - exact_a), abs(proj_c[1] - exact_b)))
            if first_cross is None and dev_uncond[-1] >= 1:
                first_cross = len(dev_uncond)
            if states is not None:
                states.append(state.copy())
        # final coherent detection; evaluate both policies on the same state
        inphase_a, inphase_b = ModelB_IdealOptical.ideal_coherent_receiver(state, 0.0, s)
        K = len(ops)
        cosK = math.cos(K * delta_phi_per_op)
        a_A, b_A = bqe_quantize_coherent(inphase_a, inphase_b, total_scale, s)
        if cosK > 0:
            a_B, b_B = bqe_quantize_coherent(inphase_a / cosK, inphase_b / cosK,
                                             total_scale, s)
        else:  # sign-flip regime (outside the frozen grid): report flipped
            a_B, b_B = bqe_quantize_coherent(inphase_a / abs(cosK), inphase_b / abs(cosK),
                                             total_scale, s)
            a_B, b_B = -a_B, -b_B
        debug = {'total_scale': total_scale, 'K': K, 'first_cross': first_cross,
                 'dev_uncond': dev_uncond, 'dev_cond': dev_cond, 'states': states}
        return a_A, b_A, a_B, b_B, debug

    @staticmethod
    def smul_chain_noise(a: int, b: int, ops, delta_phi_per_op: float,
                         sigma_phi: float, sigma_amp: float,
                         detector_noise: float, rng, mode: str = 'B',
                         return_debug: bool = False):
        """K-op chain with per-op stochastic noise
        (contract_photonics_knoise_sweep_2026-08-20.md).

        Both arms consume the SAME per-trial draw stream in a fixed order:
        operands, then per op (dpa,dpb) differential phase N(0,sigma_phi),
        (apa,apb) amplitude N(1,sigma_amp), (na,nb) detector N(0,det).

        mode 'A' (regenerate every op): per-op detect + conditioned BQE
        (div cos(delta_phi_per_op)) with per-op sigma_max, re-encode exact
        integer; a trial fails if any op's projection is wrong.
        mode 'B' (chain): noise accumulates continuously; one conditioned BQE
        (div cos(K*delta_phi_per_op)) with total scale prod(sigma_max).

        Returns (rec_a, rec_b, debug); debug = {'K', 'mode',
          'total_scale' (B), 'first_failed_op' (A, 0 if none)}.
        """
        s = ModelB_IdealOptical.SCALE_FACTOR
        if _HAS_NUMPY and isinstance(rng, (np.random.Generator,)):
            draw = lambda mu, sd: float(rng.normal(mu, sd))
        else:
            draw = lambda mu, sd: rng.gauss(mu, sd)
        dpa_l, dpb_l, apa_l, apb_l, na_l, nb_l = [], [], [], [], [], []
        for _ in ops:
            dpa_l.append(draw(0.0, sigma_phi)); dpb_l.append(draw(0.0, sigma_phi))
            apa_l.append(draw(1.0, sigma_amp)); apb_l.append(draw(1.0, sigma_amp))
            na_l.append(draw(0.0, detector_noise)); nb_l.append(draw(0.0, detector_noise))
        first_failed = 0
        if mode == 'A':
            state = ModelB_IdealOptical.encode_wdm(a, b)
            cosA = math.cos(delta_phi_per_op)
            for i, (c, d) in enumerate(ops):
                state = ModelB_IdealOptical.scattering_transform(state, c, d)
                sigma_i = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
                state.phi_a += delta_phi_per_op + dpa_l[i]
                state.phi_b += delta_phi_per_op + dpb_l[i]
                state.E_a_real = (state.E_a_pos - state.E_a_neg) * math.cos(state.phi_a)
                state.E_a_imag = (state.E_a_pos - state.E_a_neg) * math.sin(state.phi_a)
                state.E_b_real = (state.E_b_pos - state.E_b_neg) * math.cos(state.phi_b)
                state.E_b_imag = (state.E_b_pos - state.E_b_neg) * math.sin(state.phi_b)
                state.E_a_pos *= apa_l[i]; state.E_a_neg *= apa_l[i]
                state.E_b_pos *= apb_l[i]; state.E_b_neg *= apb_l[i]
                state.E_a_real *= apa_l[i]; state.E_a_imag *= apa_l[i]
                state.E_b_real *= apb_l[i]; state.E_b_imag *= apb_l[i]
                ia, ib = ModelB_IdealOptical.ideal_coherent_receiver(state, 0.0, s)
                ia += na_l[i]; ib += nb_l[i]
                # exact-state projection (final-only SurdFixed64 clamp, per
                # spec): intermediates are NOT clamped here.
                ra = int(round(sigma_i * (ia / cosA) / s))
                rb = int(round(sigma_i * (ib / cosA) / s))
                exact = (a, b)
                for cc, dd in ops[:i + 1]:
                    exact = (exact[0] * cc + 3 * exact[1] * dd,
                             exact[0] * dd + exact[1] * cc)
                if first_failed == 0 and (ra, rb) != (exact[0], exact[1]):
                    first_failed = i + 1
                state = ModelB_IdealOptical.encode_wdm(ra, rb)
            rec = (ra, rb)
            debug = {'K': len(ops), 'mode': 'A', 'first_failed_op': first_failed,
                     'total_scale': None}
            if return_debug:
                return rec[0], rec[1], debug
            return rec[0], rec[1]
        # mode 'B'
        state = ModelB_IdealOptical.encode_wdm(a, b)
        angle = 0.0
        total_scale = 1
        for i, (c, d) in enumerate(ops):
            state = ModelB_IdealOptical.scattering_transform(state, c, d)
            sigma_i = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
            total_scale *= sigma_i
            angle += delta_phi_per_op
            state.phi_a += delta_phi_per_op + dpa_l[i]
            state.phi_b += delta_phi_per_op + dpb_l[i]
            state.E_a_real = (state.E_a_pos - state.E_a_neg) * math.cos(state.phi_a)
            state.E_a_imag = (state.E_a_pos - state.E_a_neg) * math.sin(state.phi_a)
            state.E_b_real = (state.E_b_pos - state.E_b_neg) * math.cos(state.phi_b)
            state.E_b_imag = (state.E_b_pos - state.E_b_neg) * math.sin(state.phi_b)
            state.E_a_pos *= apa_l[i]; state.E_a_neg *= apa_l[i]
            state.E_b_pos *= apb_l[i]; state.E_b_neg *= apb_l[i]
            state.E_a_real *= apa_l[i]; state.E_a_imag *= apa_l[i]
            state.E_b_real *= apb_l[i]; state.E_b_imag *= apb_l[i]
            if i == len(ops) - 1:
                ia, ib = ModelB_IdealOptical.ideal_coherent_receiver(state, 0.0, s)
                ia += na_l[i]; ib += nb_l[i]
        cosK = math.cos(angle)
        if cosK > 0:
            ra, rb = bqe_quantize_coherent(ia / cosK, ib / cosK, total_scale, s)
        else:
            ra, rb = bqe_quantize_coherent(ia / abs(cosK), ib / abs(cosK), total_scale, s)
            ra, rb = -ra, -rb
        ra = max(-32768, min(32767, ra)); rb = max(-32768, min(32767, rb))
        debug = {'K': len(ops), 'mode': 'B', 'first_failed_op': None,
                 'total_scale': total_scale}
        if return_debug:
            return ra, rb, debug
        return ra, rb


def test_model_a():
    """Test Model A (exact oracle)."""
    print("\n=== Model A: Exact SPU Oracle ===")
    success = ModelA_ExactSPU.test_known_vectors()
    print("Known vector tests: " + ("PASS" if success else "FAIL"))
    return success


def test_model_b_equivalence():
    """Test that Model B (ideal optical) matches Model A (exact) with no noise."""
    print("\n=== Model B: Ideal Optical vs Model A ===")
    
    num_trials = 100
    matches = 0
    
    random.seed(42)
    for _ in range(num_trials):
        a, b, c, d = [random.randint(-100, 100) for _ in range(4)]
        
        result_a = ModelA_ExactSPU.smul(a, b, c, d)
        result_b = ModelB_IdealOptical.smul(a, b, c, d)
        
        if result_a == result_b:
            matches += 1
        else:
            print("  Mismatch: ({0}+{1}√3)×({2}+{3}√3)".format(a, b, c, d))
            print("    Model A: {0}".format(result_a))
            print("    Model B: {0}".format(result_b))
    
    pct = 100.0 * matches / num_trials
    print("Model B agreement with Model A: {0}/{1} ({2:.1f}%)".format(matches, num_trials, pct))
    return matches == num_trials


def test_model_c_sweep(num_trials=500, master_seed=13):
    """Sweep Model C (noisy optical) across a set of diagnostic tests (T0-T6).

    Uses a master SeedSequence (numpy if available) to spawn independent per-trial RNGs.
    Returns a list of (test_name, sigma_or_param, recovery_rate, n_fail, stats)
    where stats include MAE, RMSE, median, Q95, Q99.
    """
    print("\n=== Model C: Noisy Optical Recovery Sweep ({0} trials per config) ===".format(num_trials))

    # Define test matrix T0..T6
    tests = [
        { 'name': 'T0_no_noise', 'mode': 'C0', 'sigma_phi': 0.0, 'sigma_amp': 0.0, 'loss_dB': 0.0, 'lo_track': True, 'detector_noise': 0.0 },
        { 'name': 'T1_common_phase_LO_tracked', 'mode': 'C0', 'sigma_phi': None, 'sigma_amp': 0.0, 'loss_dB': 0.0, 'lo_track': True, 'detector_noise': 0.0 },
        { 'name': 'T2_common_phase_fixed_LO', 'mode': 'C0', 'sigma_phi': None, 'sigma_amp': 0.0, 'loss_dB': 0.0, 'lo_track': False, 'detector_noise': 0.0 },
        { 'name': 'T3_diff_phase', 'mode': 'C1', 'sigma_phi': None, 'sigma_amp': 0.0, 'loss_dB': 0.0, 'lo_track': False, 'detector_noise': 0.0 },
        { 'name': 'T4_amplitude_only', 'mode': 'C1', 'sigma_phi': 0.0, 'sigma_amp': 0.01, 'loss_dB': 0.0, 'lo_track': False, 'detector_noise': 0.0 },
        { 'name': 'T5_loss_only', 'mode': 'C1', 'sigma_phi': 0.0, 'sigma_amp': 0.0, 'loss_dB': 3.0, 'lo_track': False, 'detector_noise': 0.0 },
        { 'name': 'T6_detector_noise', 'mode': 'C1', 'sigma_phi': 0.0, 'sigma_amp': 0.0, 'loss_dB': 0.0, 'lo_track': False, 'detector_noise': 0.01 },
    ]

    # Phase jitter sweep values (degrees) for tests that use sigma_phi=None
    phase_jitters_deg = [0.5, 1.0, 2.0, 3.0, 5.0]

    master = make_master_rng(master_seed)

    overall_results = []

    for test in tests:
        # For tests that declare sigma_phi = None, iterate phase_jitters
        sigma_list = phase_jitters_deg if test['sigma_phi'] is None else [test['sigma_phi']]
        for sigma in sigma_list:
            sigma_phi_rad = sigma * math.pi / 180.0
            correct = 0
            errors_a = []
            errors_b = []

            for trial in range(num_trials):
                rng = trial_rng(master, trial)
                # draw operands using rng
                if _HAS_NUMPY:
                    a = int(rng.integers(-100, 101))
                    b = int(rng.integers(-100, 101))
                    c = int(rng.integers(-100, 101))
                    d = int(rng.integers(-100, 101))
                else:
                    a = rng.randint(-100, 100)
                    b = rng.randint(-100, 100)
                    c = rng.randint(-100, 100)
                    d = rng.randint(-100, 100)

                result_golden = ModelA_ExactSPU.smul(a, b, c, d)

                sigma_phi_use = sigma_phi_rad
                if test['sigma_phi'] is not None:
                    sigma_phi_use = test['sigma_phi']

                result_noisy = ModelC_NoisyOptical.smul_with_noise(
                    a, b, c, d,
                    sigma_phi=sigma_phi_use,
                    sigma_amp=test['sigma_amp'],
                    loss_dB=test['loss_dB'],
                    noise_mode=test['mode'],
                    lo_track=test['lo_track'],
                    detector_noise=test['detector_noise'],
                    trial_rng_obj=rng
                )

                if result_noisy == result_golden:
                    correct += 1
                else:
                    # record relative error for statistics
                    err_a = abs(result_noisy[0] - result_golden[0])
                    err_b = abs(result_noisy[1] - result_golden[1])
                    errors_a.append(err_a)
                    errors_b.append(err_b)

            recovery_rate = 100.0 * correct / num_trials
            # Basic 95% CI (normal approx)
            p = correct / num_trials
            se = math.sqrt(max(p * (1 - p), 0.0) / num_trials)
            ci_low = max(0.0, (p - 1.96 * se) * 100.0)
            ci_high = min(100.0, (p + 1.96 * se) * 100.0)

            # Error statistics
            combined_errors = errors_a + errors_b
            if combined_errors:
                mae = sum(combined_errors) / len(combined_errors)
                rmse = math.sqrt(sum(e * e for e in combined_errors) / len(combined_errors))
                median = sorted(combined_errors)[len(combined_errors) // 2]
                q95 = sorted(combined_errors)[max(0, int(0.95 * len(combined_errors)) - 1)]
                q99 = sorted(combined_errors)[max(0, int(0.99 * len(combined_errors)) - 1)]
            else:
                mae = rmse = median = q95 = q99 = 0.0

            print("{test:30s} | σ_φ={sigma:5s} | Correct: {c:4d}/{n:4d} | Recovery: {p:6.2f}% | 95% CI [{lo:4.1f}%, {hi:4.1f}%] | MAE={mae:.1f} RMSE={rmse:.1f} Q95={q95:.1f} Q99={q99:.1f}".format(
                test=test['name'], sigma=str(sigma), c=correct, n=num_trials, p=recovery_rate, lo=ci_low, hi=ci_high, mae=mae, rmse=rmse, q95=q95, q99=q99
            ))

            overall_results.append((test['name'], sigma, recovery_rate, correct, (mae, rmse, median, q95, q99, ci_low, ci_high)))

    return overall_results


if __name__ == "__main__":
    print("=" * 70)
    print("SPU-13 PHOTONIC THREE-MODEL INVESTIGATION: SMUL")
    print("=" * 70)
    
    success_a = test_model_a()
    success_b = test_model_b_equivalence()
    results = test_model_c_sweep(num_trials=500)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Model A (exact):  Baseline for all comparisons")
    print("Model B (ideal):  Noiseless optical should match Model A exactly")
    print("Model C (noisy):  Measure recovery envelope vs phase jitter")
    print("")
    print("Next steps:")
    print("  - Extend to full 16,000 trials per noise level")
    print("  - Sweep amplitude, loss, crosstalk parameters")
    print("  - Generate publication-ready results table with 95% CI")
    print("  - Identify critical noise thresholds for physical design")
    print("=" * 70)
