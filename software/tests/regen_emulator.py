"""
regen_emulator.py — REGEN ISA proof-of-concept emulator
(ISA_REGEN_ARCHITECTURE_PROPOSAL_2026-08-20.md).

Three-layer model:

  1. Exact oracle  — big-int SurdFixed64 ops, clamped once at the end.
  2. Continuous backend — per-op transformation on a CONTINUOUS state, no
     intermediate regeneration. Backends: Photonic (frozen chain), FPGA
     reference (different internal scale + normalization), Digital (exact).
  3. REGEN — consumes (continuous measurement, K, backend metadata) and
     projects to the exact Surd state. Backend-agnostic; the ISA exposes
     only REGEN + .block K.

The semantic contract under test:
    REGEN(OpticalChain_K(S)) == Oracle_K(S)
for the frozen experimental conditions, and identical architectural state
regardless of which backend realizes the block.
"""
import math

from test_photonic_models_smul import (
    ModelB_IdealOptical, bqe_quantize_coherent,
)

# ---------------------------------------------------------------------------
# Layer 1: exact oracle (big-int, final-only clamp)
# ---------------------------------------------------------------------------

def surd_mul(xa, xb, c, d):
    return xa * c + 3 * xb * d, xa * d + xb * c

def _op_multiplier(op):
    """Resolve an op to its (c, d) surd multiplier.
    'srot60' is a scalar-surd placeholder for the geometric SROT.60 rotor
    (the order-6 geometry lives on the Quadray state; the PoC uses the Pell
    unit (2+sqrt3), an exact Q(sqrt3) multiplier)."""
    if op[0] == 'smul':
        return op[1][0], op[1][1]
    if op[0] == 'srot60':
        return 2, 1
    raise ValueError(op)

def oracle_exact(S0, ops):
    """Exact K-fold result, unclamped (for band filtering)."""
    xa, xb = S0
    for op in ops:
        c, d = _op_multiplier(op)
        xa, xb = surd_mul(xa, xb, c, d)
    return xa, xb

def oracle_block(S0, ops):
    """Exact K-fold result, clamped once to SurdFixed64."""
    xa, xb = oracle_exact(S0, ops)
    return (max(-32768, min(32767, xa)), max(-32768, min(32767, xb)))

# ---------------------------------------------------------------------------
# Layer 2: continuous backends (no intermediate regeneration)
# ---------------------------------------------------------------------------

def _encode(s, a, b):
    """Encode (a, b) with scale s as a complex-field state."""
    st = ModelB_IdealOptical.encode_wdm(a, b)
    st.E_a_pos *= s / ModelB_IdealOptical.SCALE_FACTOR
    st.E_a_neg *= s / ModelB_IdealOptical.SCALE_FACTOR
    st.E_b_pos *= s / ModelB_IdealOptical.SCALE_FACTOR
    st.E_b_neg *= s / ModelB_IdealOptical.SCALE_FACTOR
    return st

def _rotate_sync(st, da, db):
    """Rotate both channels by (da, db), keeping dual-rail and complex-field
    representations coherent for the next scatter."""
    st.phi_a += da
    st.phi_b += db
    st.E_a_real = (st.E_a_pos - st.E_a_neg) * math.cos(st.phi_a)
    st.E_a_imag = (st.E_a_pos - st.E_a_neg) * math.sin(st.phi_a)
    st.E_b_real = (st.E_b_pos - st.E_b_neg) * math.cos(st.phi_b)
    st.E_b_imag = (st.E_b_pos - st.E_b_neg) * math.sin(st.phi_b)


class PhotonicBackend:
    """Frozen photonic chain: WDM encode, normalized scattering per op,
    deterministic per-op common-mode thermal rotation (canonical silicon).
    The state stays continuous between ops; no BQE until REGEN."""

    K_RAD = (2 * math.pi / 1550e-9) * 6.4322e-6 * 1.86e-4  # rad / K

    def __init__(self, deltaT=2.0):
        self.dphi = self.K_RAD * deltaT

    def run(self, S0, ops):
        s = ModelB_IdealOptical.SCALE_FACTOR
        st = _encode(s, S0[0], S0[1])
        total = 1
        angle = 0.0
        for op in ops:
            c, d = _op_multiplier(op)
            st = ModelB_IdealOptical.scattering_transform(st, c, d)
            total *= max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
            angle += self.dphi
            _rotate_sync(st, self.dphi, self.dphi)
        ia, ib = ModelB_IdealOptical.ideal_coherent_receiver(st, 0.0, s)
        return (ia, ib), {'scale': s, 'Sigma': total, 'angle_K': angle,
                          'K': len(ops)}


class FpgaReferenceBackend:
    """Reference backend: same block semantics on a continuous fixed-point
    model with a DIFFERENT internal scale (s=0.25) and power-of-two
    normalization (different Sigma_total than the photonic backend). REGEN
    must recover the identical exact state anyway — Sigma is backend
    metadata, not ISA state."""

    SCALE = 0.25

    def run(self, S0, ops):
        st = _encode(self.SCALE, S0[0], S0[1])
        _rotate_sync(st, 0.0, 0.0)   # init complex fields from dual-rail
        total = 1
        for op in ops:
            c, d = _op_multiplier(op)
            s2 = max(abs(c) + 3 * abs(d), abs(d) + abs(c), 1)
            s2 = 1 << (s2 - 1).bit_length()          # ceil power of two
            total *= s2
            h00, h01 = c / s2, 3.0 * d / s2
            h10, h11 = d / s2, c / s2
            ea_r, ea_i = st.E_a_real, st.E_a_imag
            eb_r, eb_i = st.E_b_real, st.E_b_imag
            st.E_a_real = h00 * ea_r + h01 * eb_r
            st.E_a_imag = h00 * ea_i + h01 * eb_i
            st.E_b_real = h10 * ea_r + h11 * eb_r
            st.E_b_imag = h10 * ea_i + h11 * eb_i
            st.E_a_pos = abs(st.E_a_real); st.E_a_neg = 0.0
            st.E_b_pos = abs(st.E_b_real); st.E_b_neg = 0.0
            st.phi_a = math.atan2(st.E_a_imag, st.E_a_real)
            st.phi_b = math.atan2(st.E_b_imag, st.E_b_real)
        ia, ib = ModelB_IdealOptical.ideal_coherent_receiver(st, 0.0, self.SCALE)
        return (ia, ib), {'scale': self.SCALE, 'Sigma': total, 'angle_K': 0.0,
                          'K': len(ops)}


class DigitalSurdBackend:
    """Exact big-int backend: the continuous state surrogate is the exact
    value itself; REGEN is a pass-through. Demonstrates the same ISA contract
    on a conventional digital implementation."""

    def run(self, S0, ops):
        xa, xb = S0
        for op in ops:
            c, d = _op_multiplier(op)
            xa, xb = surd_mul(xa, xb, c, d)
        return (float(xa), float(xb)), {'scale': 1.0, 'Sigma': 1,
                                        'angle_K': 0.0, 'K': len(ops)}


# ---------------------------------------------------------------------------
# Layer 3: REGEN (backend-agnostic projection to the exact Surd state)
# ---------------------------------------------------------------------------

def regen(measurement, meta, calibration='conditioned'):
    """Consume the backend measurement + internal metadata; apply the
    compensation law (per experiment #3) when conditioned; project via BQE
    to the exact Surd state. Calibration/compensation are REGEN internals,
    invisible to the program."""
    ia, ib = measurement
    s = meta['scale']
    Sigma = meta['Sigma']
    angleK = meta['angle_K']
    if calibration == 'conditioned' and abs(angleK) > 1e-12:
        c = math.cos(angleK)
        ia, ib = ia / c, ib / c
    a, b = bqe_quantize_coherent(ia, ib, Sigma, s)
    return (max(-32768, min(32767, a)), max(-32768, min(32767, b)))


def run_block(backend, S0, ops, calibration='conditioned'):
    """Execute a K-op block on a backend and regenerate."""
    meas, meta = backend.run(S0, ops)
    return regen(meas, meta, calibration)


# ---------------------------------------------------------------------------
# Block assembly / legality (Gate 3)
# ---------------------------------------------------------------------------

class BlockValidationError(Exception):
    pass


def parse_block(text):
    """Parse `.block K=n` ... `.regen`. Enforces op-count legality: the block
    must contain exactly K ops (fewer or more is an assembly error)."""
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip() and not ln.strip().startswith(';')]
    ops = []
    K = None
    for ln in lines:
        if ln.startswith('.block'):
            try:
                K = int(ln.split('=')[1].strip())
            except (IndexError, ValueError):
                raise BlockValidationError(f'malformed .block: {ln!r}')
        elif ln.startswith('.regen'):
            break
        elif ln.startswith('smul'):
            parts = ln.split()
            if len(parts) != 3:
                raise BlockValidationError(f'malformed smul: {ln!r}')
            ops.append(('smul', (int(parts[1]), int(parts[2]))))
        elif ln.startswith('srot60'):
            ops.append(('srot60', None))
        else:
            raise BlockValidationError(f'unrecognized line: {ln!r}')
    if K is None:
        raise BlockValidationError('missing .block directive')
    if len(ops) != K:
        raise BlockValidationError(
            f'block declares K={K} but contains {len(ops)} ops')
    return ops, K


def regen_idempotent(backend, exact_state):
    """REGEN(REGEN(S)) == S: regenerate an already-exact architectural state
    (zero-op block) and require it unchanged."""
    meas, meta = backend.run(exact_state, [])
    return regen(meas, meta, 'conditioned')
