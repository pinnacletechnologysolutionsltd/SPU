#!/usr/bin/env python3
#
# Copyright 2026 John Curley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
SPU-13 Sovereign Virtual Machine (spu_vm.py) — Legacy Linear Architecture v3.2
Pure Python interpreter for the Legacy Sovereign Assembly (SAS) ISA.

Executes 64-bit control words in Q(√3) — the rational surd field.
No floating point. No approximation. Bit-exact by construction.

v1.1 additions:
  - QuadrayVector: 4-axis IVM tetrahedral coordinates in Q(√3)⁴
  - 13 Quadray registers (QR0–QR12, one per SPU-13 axis)
  - Opcodes: QADD, QROT, QNORM, QLOAD, QLOG, SPREAD, HEX
  - Control: COND (conditional branch), CALL/RET (subroutine stack)
  - Exact integer ordering for RationalSurd (rs_lt — no floats)

v1.2 additions (Vector Equilibrium + Janus layer):
  - EQUIL : assert sum of all 13 QR registers = zero vector (VE health check)
  - IDNT  : reset QR[n] to canonical unity [1,0,0,0]
  - JINV  : Janus bit — negate surd component of scalar R[n] (single XOR in hw)
  - ANNE  : anneal QR[n] one step toward Vector Equilibrium (halve each component)

v1.3 additions (Davis Gasket + Fibonacci dispatch):
  - DavisGasket class: tracks manifold tension τ, stiffness K, cubic leak state
    gasket_tick()      — one Davis Gate cycle: check Σ QR[0..12] == 0
    henosis_pulse()    — soft recovery: halve all QR components (≡ ANNE)
    henosis_recover()  — loop until laminar or max_pulses
  - FibDispatch class: Sierpinski 34-cycle frame tracker
    tick()             — advance one cycle, return gate label (φ₈/φ₁₃/φ₂₁/'')
    at_gate()          — True when frame_pos is a Fibonacci position
  - SPUCore integration: gasket + fib wired into step() tail
    • Gate announcement at every φ₈/φ₁₃/φ₂₁ cycle boundary
    • Davis Gate check on every gate tick
    • Henosis recovery on φ₁₃ / φ₂₁ if cubic leak detected
    • Gasket + FibDispatch state printed in dump_registers()

v1.4 additions (SDF Layer 7 — Rational Distance Field):
  - SdfState class: mirrors spu_sdf.h Layer 7 in pure Python
    nearest()          — nearest QR register by min Quadrance (sdf_nearest)
    grad()             — gradient vector from QR0 to nearest register (sdf_grad)
    snap_check()       — conflict if grad·vec_sum ≠ 0 (sdf_snap)
    evaluate()         — run all of the above at every SNAP boundary
  - SPUCore: sdf_trace flag; sdf.evaluate() in SNAP handler
  - SNAP handler: SDF CONFLICT reported separately from scalar cubic leak
  - dump_registers(): SdfState summary line added
  - --sdf-trace CLI flag added to main()

v1.5 additions (SOM/BMU classification):
  - SOM (0x2A) opcode: weighted quadrance BMU with 7-node hex fixture
  - Stable tie-breaking, confidence gap, ambiguity flag
  - Matches spu_som_bmu.v + spu_cluster_reduce.v RTL bit-for-bit
  - Hex telemetry: label in hex_q, ambiguous flag in hex_r[0]

Usage:
    python3 spu_vm.py programs/jitterbug.sas
    python3 spu_vm.py programs/equilibrium_test.sas --proof
    python3 spu_vm.py --bin programs/jitterbug.bin
"""

import sys
import os
import struct
import argparse

# Optional phinary helpers (pack/unpack/add)
try:
    import importlib.util as _il
    _tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
    _ph_path = os.path.join(_tools_dir, 'phinary_vm_helpers.py')
    if os.path.exists(_ph_path):
        _spec = _il.spec_from_file_location('phinary_vm_helpers', _ph_path)
        phinary_helpers = _il.module_from_spec(_spec)
        _spec.loader.exec_module(phinary_helpers)  # type: ignore
    else:
        phinary_helpers = None
except Exception:
    phinary_helpers = None


class RotcUnverifiedAngleError(Exception):
    """Raised when ROTC is issued with an angle beyond ROTC_MAX_VERIFIED_ANGLE.

    Mirrors the RTL fault in spu13_core.v: angles 12+ were placeholder
    stubs (some literally F=G=H=0, which would silently zero the
    destination's B/C/D). Detect and refuse instead of computing a wrong
    or corrupted result -- same "detect, never silently corrupt" idiom
    as A31 FLAGS.V and the ROTC tagged core's MISALIGNED/OVERFLOW/INEXACT
    faults. (Angles 6-11 — the axis-permutation conjugates — were behind
    this gate until 2026-07-10, when the VM gained matching permutation
    logic and the cross-verified oracle pass moved the boundary to 11.)
    """


class IrotcBadIndexError(Exception):
    """IROTC_ERR_BADIDX — sel[5:0] beyond the 60-entry A₅ catalog.

    Dispatch-time guard (IROTC_SPEC.md §4): the destination register must
    be left bit-identically untouched, same idiom as the ROTC angle gate.
    """


class IrotcUntaggedError(Exception):
    """IROTC_ERR_UNTAGGED — source register's DOUBLED tag is clear.

    The unguarded >>>1 in the IROTC micro-program is licensed by the
    doubling theorem only for doubled data (IROTC_SPEC.md §3); refuse at
    dispatch instead of silently truncating. Destination untouched.
    """


class IrotcCatalogMixError(Exception):
    """IROTC_ERR_CATMIX — source register is catalog-locked the other way.

    The doubling theorem composes only WITHIN one catalog: main x conjugate
    matrix products leave ½Z[φ] (denominators reach 4 — machine-checked in
    test_icosahedral_catalog.py, found 2026-07-10 when 101/200 random
    main→conj VM chains tripped the evenness assert). A register that has
    passed through a main-catalog IROTC is only main-safe (PHI_MAIN), and
    vice versa (PHI_CONJ); only fresh doubled data (PHI_FRESH — output of
    LOAD2X/SCALE2, componentwise even) is safe for either catalog.
    Re-condition with SCALE2 to return to PHI_FRESH. Destination untouched.
    """


# φ-plane typestate per QR register (2 bits in RTL). Values chosen so
# truthiness == "tagged" and bool True == PHI_FRESH.
PHI_UNTAGGED = 0   # no license — IROTC faults
PHI_FRESH    = 1   # componentwise even (LOAD2X/SCALE2) — either catalog safe
PHI_MAIN     = 2   # produced by a main-catalog IROTC — main-safe only
PHI_CONJ     = 3   # produced by a conjugate-catalog IROTC — conj-safe only


def _phi_tag_join(x: int, y: int) -> int:
    """Tag of a linear combination (QADD/QSUB) of two tagged registers.

    Lattice: FRESH ⊑ MAIN and FRESH ⊑ CONJ (even vectors are safe either
    way); MAIN and CONJ are incompatible; anything with UNTAGGED is
    UNTAGGED (scale incoherence — IROTC_SPEC.md §3).
    """
    if x == PHI_UNTAGGED or y == PHI_UNTAGGED:
        return PHI_UNTAGGED
    if x == y:
        return x
    if x == PHI_FRESH:
        return y
    if y == PHI_FRESH:
        return x
    return PHI_UNTAGGED  # MAIN + CONJ


# Generated IROTC catalog (software/lib/irotc_catalog.py) — lazy import,
# checksum-verified against the oracle's pinned SHA before first use.
_irotc_catalog_mod = None


def _irotc_catalog():
    global _irotc_catalog_mod
    if _irotc_catalog_mod is None:
        import importlib.util as _il2
        _path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'lib', 'irotc_catalog.py')
        _spec2 = _il2.spec_from_file_location('irotc_catalog', _path)
        _mod = _il2.module_from_spec(_spec2)
        _spec2.loader.exec_module(_mod)
        _mod.verify_checksum()
        _irotc_catalog_mod = _mod
    return _irotc_catalog_mod


# ---------------------------------------------------------------------------
# Q(√3) Arithmetic — the only math the SPU does
# ---------------------------------------------------------------------------

class RationalSurd:
    """
    An element of the rational field Q(√3): value = a + b·√3
    a and b are Python integers — no floating point, ever.
    All arithmetic is closed in this field.

    pell_step: optional Pell Octave tracker — counts how many ROT operations
    have been applied.  Encodes as (octave, step) where octave = pell_step // 8
    and step = pell_step % 8.  The stored (a, b) is always the fundamental-
    domain value orbit[step], so a² − 3b² = 1 for any rotor-generated surd.
    For surds not on the Pell orbit, pell_step is None.

    polarity: Janus polarity flag (Thomson SQR §9).  +1 for θ ∈ [0°,90°],
    −1 for θ ∈ (90°,180°].  None if this surd is not a rotor.  Resolves the
    sign ambiguity in spread→cos conversion: cos θ = polarity · √(1−s).
    Compose under rotor multiplication: p_ab = p_a × p_b.
    """
    __slots__ = ('a', 'b', 'pell_step', 'polarity')

    def __init__(self, a: int = 0, b: int = 0, pell_step: int = None,
                 polarity: int = None):
        self.a = int(a)
        self.b = int(b)
        self.pell_step = pell_step  # None = not a Pell-rotor-generated surd
        self.polarity = polarity     # None = not a rotor; +1 or −1 for rotors

    def __add__(self, other: 'RationalSurd') -> 'RationalSurd':
        return RationalSurd(self.a + other.a, self.b + other.b)

    def __sub__(self, other: 'RationalSurd') -> 'RationalSurd':
        return RationalSurd(self.a - other.a, self.b - other.b)

    def __mul__(self, other: 'RationalSurd') -> 'RationalSurd':
        # (a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3
        p = None
        if self.polarity is not None and other.polarity is not None:
            p = self.polarity * other.polarity  # Janus: polarities multiply
        elif self.polarity is not None:
            p = self.polarity
        elif other.polarity is not None:
            p = other.polarity
        return RationalSurd(
            self.a * other.a + 3 * self.b * other.b,
            self.a * other.b + self.b * other.a,
            polarity=p,
        )

    def __neg__(self) -> 'RationalSurd':
        return RationalSurd(-self.a, -self.b,
                            polarity=self.polarity)

    def __eq__(self, other) -> bool:
        if not isinstance(other, RationalSurd):
            return NotImplemented
        return (self.a == other.a and self.b == other.b and
                self.polarity == other.polarity)

    def quadrance(self) -> int:
        """Q = a² - 3b²  (the Davis Gate check — must be ≥ 0 for stability)"""
        return self.a * self.a - 3 * self.b * self.b

    def davis_c(self) -> str:
        """Davis Ratio C = a/b (manifold tension indicator)"""
        if self.b == 0:
            return "∞" if self.a != 0 else "0/0"
        # Keep exact as fraction string — no float
        from math import gcd
        g = gcd(abs(self.a), abs(self.b))
        return f"{self.a//g}/{self.b//g}"

    def is_laminar(self) -> bool:
        """Laminar (stable) if quadrance > 0 — no cubic leak."""
        return self.quadrance() > 0

    def rotate_phi(self) -> 'RationalSurd':
        """
        Phi-Rotor: multiply by the unit element (2 + 1·√3).
        Q(2,1) = 4 - 3 = 1 — unit quadrance, so this rotation PRESERVES
        laminar stability. Generates the Pell sequence 1→(2,1)→(7,4)→(26,15)→...

        Pell Octave: tracks (octave, step) so the stored (a,b) stays in the
        16-bit fundamental domain (orbit[0..7]).  step wraps at 8; octave
        increments.  This preserves P²−3Q²=1 for arbitrarily many rotations.

        Janus polarity: Pell steps 0–3 have cos(θ/2) > 0 → p = +1.
        Steps 4–7 have cos(θ/2) < 0 → p = −1 (θ > 90° half-angle).
        """
        # Fundamental orbit (steps 0–7) — all fit in int16
        # Polarity for each step: p = sign of cos(n·φ/2) where φ = 2·arctan(√3/2)
        _PELL_ORBIT = [
            (1, 0, +1),    # r⁰: cos(0) = 1 → p = +1
            (2, 1, +1),    # r¹: cos ≈ 0.87 → p = +1
            (7, 4, +1),    # r²: cos ≈ 0.51 → p = +1
            (26, 15, +1),  # r³: cos ≈ 0.02 → p = +1 (barely)
            (97, 56, -1),  # r⁴: cos ≈ −0.48 → p = −1
            (362, 209, -1),# r⁵: cos ≈ −0.87 → p = −1
            (1351, 780, -1),# r⁶: cos ≈ −0.99 → p = −1
            (5042, 2911, -1),# r⁷: cos ≈ −1.00 → p = −1
        ]
        if self.pell_step is not None:
            new_step = self.pell_step + 1
            step_n = new_step % 8
            a, b, p = _PELL_ORBIT[step_n]
            return RationalSurd(a, b, pell_step=new_step, polarity=p)
        # Fallback for surds not started from unity — full field multiply
        result = self * RationalSurd(2, 1)
        return RationalSurd(result.a, result.b, pell_step=None)

    def janus_invert(self) -> 'RationalSurd':
        """
        Janus inversion: flip the polarity flag.  Maps a rotor to its
        double-cover partner.  For the S³ double cover of SO(3), q and −q
        represent the same rotation; Janus polarity makes this explicit.
        The underlying surd value (a,b) is unchanged — only p flips.
        """
        if self.polarity is None:
            return RationalSurd(self.a, self.b, self.pell_step)
        return RationalSurd(self.a, self.b, self.pell_step,
                            polarity=-self.polarity)


# ---------------------------------------------------------------------------
# Triple Quadrance Formula — rational analogue of cosine rule / Pythagorean
# ---------------------------------------------------------------------------

def triple_quadrance(Q1: int, Q2: int, spread_s3: 'RationalSurd') -> tuple:
    """
    Compute Q₃ from Q₁, Q₂ and spread s₃ using the Triple Quadrance Formula.
    Returns (Q3_acute, Q3_obtuse) — the two possible Q₃ values.

    (Q₃ − Q₁ − Q₂)² = 4·Q₁·Q₂·(1−s₃)

    For right triangles (s₃=1): Q₃ = Q₁ + Q₂  (both values equal).
    For parallel lines (s₃=0): Q₃ = |Q₁−Q₂| or Q₁+Q₂.
    """
    # spread_s3 is a RationalSurd representing s = sin²θ.
    # 1−s₃ = (den − num)/den, but since spread_s3 has integer a,b,
    # we interpret s₃ as the rational a/b → wait, it's a surd (a+b√3).
    # For exact spread as rational fraction, s₃.a is the numerator
    # and the denominator must be tracked externally.
    # Simplification: treat spread_s3 as the exact rational value s₃.
    # The formula: rhs² = 4·Q₁·Q₂·(1−s₃)
    # Since 1−s₃ is positive for valid spreads, rhs² ≥ 0.
    rhs_sq = 4 * Q1 * Q2 * (1 - spread_s3.a)  # assumes denom=1 for now
    # Q₃ = Q₁ + Q₂ ± √(rhs_sq)
    # We return the squared form — caller compares squared, never sqrt.
    q_sum = Q1 + Q2
    # The two solutions: (Q₃ − q_sum)² = rhs_sq
    return (q_sum, rhs_sq)  # Q₃ = q_sum ± √rhs_sq, caller selects via polarity


def spread_from_quadrances(Q1: int, Q2: int, Q3: int) -> tuple:
    """
    Compute spread s₃ from three quadrances (inverse of triple_quadrance).
    Returns (numer, denom) as integer pair.

    s₃ = 1 − (Q₃ − Q₁ − Q₂)² / (4·Q₁·Q₂)
    numer = 4·Q₁·Q₂ − (Q₃ − Q₁ − Q₂)²
    denom = 4·Q₁·Q₂
    """
    denom = 4 * Q1 * Q2
    diff = Q3 - Q1 - Q2
    numer = denom - diff * diff
    return (numer, denom)


def is_right_triangle(Q1: int, Q2: int, Q3: int) -> bool:
    """True if the three quadrances form a right triangle (s=1 at Q₃ vertex)."""
    return Q3 == Q1 + Q2


def delta_curve(Q1: int, Q2: int, spread_steps: int) -> list:
    """
    Generate a delta curve: family of Q₃ values as spread varies from 0 to 1.
    Returns list of (s₃, Q3_acute, Q3_obtuse) for each step.
    """
    curve = []
    for k in range(spread_steps + 1):
        # s₃ = k / spread_steps (rational)
        rhs_sq_num = 4 * Q1 * Q2 * (spread_steps - k)
        rhs_sq_den = spread_steps
        # Q₃ = Q₁ + Q₂ ± √(rhs_sq_num / rhs_sq_den)
        q_sum = Q1 + Q2
        # Since we can't sqrt, we store the squared form:
        # (Q₃ − q_sum)² = rhs_sq_num / rhs_sq_den
        curve.append((k, spread_steps, q_sum, rhs_sq_num, rhs_sq_den))
    return curve

    def __repr__(self) -> str:
        if self.b == 0:
            return f"{self.a}"
        if self.b < 0:
            return f"({self.a} - {-self.b}·√3)"
        return f"({self.a} + {self.b}·√3)"


# ---------------------------------------------------------------------------
# Exact ordering for RationalSurd — integer arithmetic only, no floats
# ---------------------------------------------------------------------------

def rs_lt(s1: 'RationalSurd', s2: 'RationalSurd') -> bool:
    """
    Exact comparison: returns True if s1 < s2 in Q(√3).
    Never uses floating point — works by case analysis on sign of (s1 - s2).
    """
    da = s1.a - s2.a
    db = s1.b - s2.b
    if da == 0 and db == 0:
        return False
    if da <= 0 and db <= 0:
        return True                       # both terms push negative
    if da >= 0 and db >= 0:
        return False                      # both terms push positive
    if da < 0 and db > 0:
        return 3 * db * db < da * da      # |da| > db√3 iff da² > 3db²
    return da * da < 3 * db * db          # da > 0, db < 0: da < |db|√3


def rs_min(*vals: 'RationalSurd') -> 'RationalSurd':
    """Return the minimum of any number of RationalSurd values (exact)."""
    result = vals[0]
    for v in vals[1:]:
        if rs_lt(v, result):
            result = v
    return result


# ---------------------------------------------------------------------------
# QuadrayVector — 4-axis IVM tetrahedral coordinates in Q(√3)⁴
# ---------------------------------------------------------------------------

class QuadrayVector:
    """
    A point in IVM (tetrahedral) space: (a, b, c, d) where each component
    is a RationalSurd element of Q(√3).

    The 4 axes point to the 4 vertices of a regular tetrahedron.
    Canonical (normalized) form: min component = 0.
    """
    __slots__ = ('a', 'b', 'c', 'd')

    def __init__(self,
                 a: RationalSurd = None,
                 b: RationalSurd = None,
                 c: RationalSurd = None,
                 d: RationalSurd = None):
        z = RationalSurd(0, 0)
        self.a = a if a is not None else RationalSurd(0, 0)
        self.b = b if b is not None else RationalSurd(0, 0)
        self.c = c if c is not None else RationalSurd(0, 0)
        self.d = d if d is not None else RationalSurd(0, 0)

    def components(self) -> tuple:
        return (self.a, self.b, self.c, self.d)

    def __add__(self, other: 'QuadrayVector') -> 'QuadrayVector':
        return QuadrayVector(
            self.a + other.a, self.b + other.b,
            self.c + other.c, self.d + other.d
        )

    def __sub__(self, other: 'QuadrayVector') -> 'QuadrayVector':
        return QuadrayVector(
            self.a - other.a, self.b - other.b,
            self.c - other.c, self.d - other.d
        )

    def normalize(self) -> 'QuadrayVector':
        """
        Subtract the minimum component from all axes.
        Produces canonical IVM form where min component = 0.
        Uses exact rs_min — no floating point.
        """
        m = rs_min(self.a, self.b, self.c, self.d)
        return QuadrayVector(
            self.a - m, self.b - m, self.c - m, self.d - m
        )

    def rotate(self) -> 'QuadrayVector':
        """
        Phi-Rotor applied to each component: multiply each by (2 + 1·√3).
        This is the Pell step — scales the Quadray by the unit element.
        Quadrance is preserved: Q(result) = Q(self) × Q(2,1)⁴ = Q(self).
        Normalize after to maintain canonical form.
        """
        return QuadrayVector(
            self.a.rotate_phi(), self.b.rotate_phi(),
            self.c.rotate_phi(), self.d.rotate_phi()
        ).normalize()

    def cycle(self) -> 'QuadrayVector':
        """
        Cyclic permutation: (a,b,c,d) → (b,c,d,a).
        One discrete 90° rotation in IVM space. Exact and zero-cost.
        """
        return QuadrayVector(self.b, self.c, self.d, self.a)

    def quadrance(self) -> RationalSurd:
        """
        IVM quadrance (squared distance from origin), exact in Q(√3).
        Formula: Σᵢ<ⱼ (cᵢ - cⱼ)²  for all 6 pairs.
        Returns a RationalSurd (may have surd component if inputs do).
        """
        comps = self.components()
        q = RationalSurd(0, 0)
        for i in range(4):
            for j in range(i + 1, 4):
                diff = comps[i] - comps[j]
                q = q + diff * diff
        return q

    def dot(self, other: 'QuadrayVector') -> RationalSurd:
        """
        Euclidean inner product: Σ aᵢ·bᵢ (component-wise in Q(√3)).
        Used as the numerator term in spread calculations.
        """
        a, b, c, d = self.components()
        p, q, r, s = other.components()
        return a*p + b*q + c*r + d*s

    def spread(self, other: 'QuadrayVector') -> tuple[RationalSurd, RationalSurd]:
        """
        Wildberger spread between two Quadray directions (from origin).
        s = 1 - (P·Q)² / (P·P × Q·Q)
          = (P·P × Q·Q - (P·Q)²) / (P·P × Q·Q)
        Returns (numerator, denominator) as RationalSurd pair — exact fraction.
        Zero denominator = one or both vectors is the zero vector.
        """
        pp = self.quadrance()
        qq = other.quadrance()
        pq = self.dot(other)
        denom = pp * qq
        numer = denom - pq * pq
        return numer, denom

    def hex_project(self) -> tuple[int, int]:
        """
        Project normalized Quadray to axial hex grid coordinates (q, r).
        Uses the rational part (a-field) of each component.
        With d=0 (canonical): q_hex = a.a, r_hex = b.a.
        For non-zero d: q_hex = a.a - d.a, r_hex = b.a - d.a.
        Returns integer (q, r) — the pixel address in the hex lattice.
        """
        norm = self.normalize()
        d_offset = norm.d.a
        return (norm.a.a - d_offset, norm.b.a - d_offset)

    def circulant_rotate(self, F: 'RationalSurd', G: 'RationalSurd',
                          H: 'RationalSurd') -> 'QuadrayVector':
        """
        F,G,H circulant rotation (Thomson SQR §6, spu13_rotor_core.v).
        Applies the 3×3 circulant matrix to B,C,D; A is invariant.
          B' = F·B + H·C + G·D
          C' = G·B + F·C + H·D
          D' = H·B + G·C + F·D
        F,G,H must satisfy F³+G³+H³−3FGH = 1 (circulant determinant).
        At {60°,120°,240°,300°} every entry is rational in {−1/3, 2/3}.
        At 120° with (F,G,H) = (−1/3, 2/3, 2/3): B'=D, C'=B, D'=C — pure permutation.
        """
        b2 = F * self.b + H * self.c + G * self.d
        c2 = G * self.b + F * self.c + H * self.d
        d2 = H * self.b + G * self.c + F * self.d
        return QuadrayVector(self.a, b2, c2, d2)

    def lerp_spread(self, other: 'QuadrayVector',
                    t_num: int, t_den: int) -> 'QuadrayVector':
        """
        Rational linear interpolation between self (t=0) and other (t=1).
        Parameter t = t_num / t_den is an exact rational fraction.
        Each component is interpolated linearly in the Q(√3) field.
        The result coefficients may be rational (non-integer) but stay in Q(√3).
        """
        # Scale each surd component: c0 + (c1 - c0) * tn / td
        def _lerp_surd(s0: RationalSurd, s1: RationalSurd) -> RationalSurd:
            da = s1.a - s0.a
            db = s1.b - s0.b
            return RationalSurd(
                s0.a * t_den + da * t_num,
                s0.b * t_den + db * t_num,
            )
            # Note: result represents (numer_a + numer_b·√3) / t_den.
            # Caller tracks denominator t_den externally when comparing.

        return QuadrayVector(
            _lerp_surd(self.a, other.a),
            _lerp_surd(self.b, other.b),
            _lerp_surd(self.c, other.c),
            _lerp_surd(self.d, other.d),
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, QuadrayVector):
            return NotImplemented
        return (self.a == other.a and self.b == other.b and
                self.c == other.c and self.d == other.d)

    def scale(self, s: 'RationalSurd') -> 'QuadrayVector':
        """Multiply each component by scalar s. No normalization.
        Quadrance is preserved up to factor s². Used for spatial rotation
        where normalization would break quadrance invariance."""
        return QuadrayVector(
            self.a * s, self.b * s, self.c * s, self.d * s,
        )

    def is_zero(self) -> bool:
        z = RationalSurd(0, 0)
        return all(c == z for c in self.components())

    def __repr__(self) -> str:
        a, b, c, d = self.components()
        return f"[{a!r}, {b!r}, {c!r}, {d!r}]"


# ---------------------------------------------------------------------------
# Assembler (inline — mirrors spu13_asm.py, so VM can load .sas directly)
# ---------------------------------------------------------------------------

OPCODES = {
    # Scalar Q(√3) arithmetic
    "LD":    0x00, "ADD":   0x01, "SUB":   0x02,
    "MUL":   0x03, "PHADD": 0x30, "PHCFG": 0x31, "ROT":   0x04, "LOG":   0x05,
    # Control flow
    "JMP":   0x06, "SNAP":  0x07, "COND":  0x20,
    "CALL":  0x21, "RET":   0x22,
    # Quadray IVM operations
    "QADD":  0x10, "QROT":  0x11, "QNORM": 0x12,
    "QLOAD": 0x13, "QLOG":  0x14, "QSUB":  0x1B, "ROTC":  0x1C, "QLDI":  0x1D, "DELTA": 0x1E,
    # Icosahedral A₅ φ-plane ops (IROTC_SPEC.md, Lucas MAC sidecar space)
    "IROTC": 0xD6, "LOAD2X": 0xD7, "SCALE2": 0xD8,
    "CALL":  0x20, "RET":   0x21,
    "MIN4":  0x1F, "QREAD": 0x22,
    # Geometry output
    "SPREAD":0x15, "HEX":   0x16,
    # SOM / BMU classification (v1.5)
    "SOM":   0x2A,
    "SOM_TRAIN": 0x2B,   # dyadic weight update after BMU
    # v1.2 — Vector Equilibrium + Janus layer
    "EQUIL": 0x17, "IDNT":  0x18, "JINV":  0x19, "ANNE":  0x1A,
    # Padé / RPLU ISA extensions
    "POLY_STEP": 0x60, "RATIO_CMP": 0x61,
    # POLY_STEP: emit RPLU Artery chord for a single Horner step (simulation helper)
    "POLY_STEP": 0xE0,
    # No-op
    "NOP":   0xFF,
}
OPNAMES = {v: k for k, v in OPCODES.items()}

def _parse_int16(s: str) -> int:
    v = int(s, 0)  # base 0: auto-detect hex (0x) / decimal
    return v & 0xFFFF

def assemble_line(line: str, line_no: int, labels: dict) -> int | None:
    clean = line.split(';')[0].strip()
    if not clean:
        return None
    parts = clean.replace(',', ' ').split()
    if not parts:
        return None

    mnemonic = parts[0].upper()

    # Label definition — handled in two-pass, skip here
    if mnemonic.endswith(':'):
        return None

    if mnemonic not in OPCODES:
        print(f"  ASM error line {line_no}: unknown mnemonic '{mnemonic}'")
        return None

    opcode = OPCODES[mnemonic]
    r1 = r2 = p1_a = p1_b = 0

    if mnemonic == "QSUB":
        if len(parts) < 3:
            print(f"  ASM error line {line_no}: QSUB requires QRd, QRs or QRd, QRa, QRb")
            return None

        def parse_qr(tok: str) -> int:
            tok = tok.upper()
            if not tok.startswith('QR'):
                raise ValueError(f"expected QR register, got {tok}")
            return int(tok[2:]) & 0xFF

        try:
            r1 = parse_qr(parts[1])
            if len(parts) > 3:
                r2 = parse_qr(parts[2])
                p1_b = parse_qr(parts[3])
            else:
                r2 = r1
                p1_b = parse_qr(parts[2])
        except ValueError as exc:
            print(f"  ASM error line {line_no}: {exc}")
            return None

        word = (opcode << 56) | (r1 << 48) | (r2 << 40) | (p1_a << 24) | (p1_b << 8)
        return word

    if mnemonic == "LOAD2X":
        # LOAD2X QRd, A, B, C, D (5-arg, matches spu13_asm.py) or
        # LOAD2X QRd, AB, CD (packed 16-bit halves, QLDI-style)
        tok = parts[1].upper()
        if not tok.startswith('QR'):
            print(f"  ASM error line {line_no}: LOAD2X expects a QR register")
            return None
        r1 = int(tok[2:]) & 0xFF
        try:
            vals = [int(p, 0) for p in parts[2:]]
        except ValueError as exc:
            print(f"  ASM error line {line_no}: {exc}")
            return None
        if len(vals) == 4:
            p1_a = ((vals[0] & 0xFF) << 8) | (vals[1] & 0xFF)
            p1_b = ((vals[2] & 0xFF) << 8) | (vals[3] & 0xFF)
        elif len(vals) == 2:
            p1_a = vals[0] & 0xFFFF
            p1_b = vals[1] & 0xFFFF
        else:
            print(f"  ASM error line {line_no}: LOAD2X takes 4 components "
                  f"or 2 packed halves")
            return None
        return (opcode << 56) | (r1 << 48) | (p1_a << 24) | (p1_b << 8)

    def parse_arg(arg: str, is_first: bool) -> tuple[int, int, int]:
        """Returns (r1_val, r2_val, p1_a_val) for a single argument."""
        arg = arg.upper()
        if arg.startswith('QR'):          # Quadray register: QR0-QR12
            idx = int(arg[2:]) & 0xFF
            return (idx, 0, 0) if is_first else (0, idx, 0)
        if arg.startswith('R'):           # Scalar register: R0-R25
            idx = int(arg[1:]) & 0xFF
            return (idx, 0, 0) if is_first else (0, idx, 0)
        if arg.startswith('PH'):          # Packed phinary immediate: PH0xNNNN
            try:
                val = int(arg[2:], 0)
            except Exception:
                val = _parse_int16(arg[2:])
            return (0, 0, val & 0xFFFF)
        if arg in labels:                  # Label reference
            return (0, 0, labels[arg] & 0xFFFF)
        return (0, 0, _parse_int16(arg))  # Immediate

    if len(parts) > 1:
        rv1, rv2, pa = parse_arg(parts[1], True)
        r1 |= rv1; r2 |= rv2; p1_a |= pa

    if len(parts) > 2:
        rv1, rv2, pa = parse_arg(parts[2], False)
        r1 |= rv1; r2 |= rv2
        if pa: p1_a = pa  # label/immediate in arg2 overrides p1_a

    if len(parts) > 3:
        # Third operand routing:
        #   ROTC QRd, QRs, angle → angle goes in p1_a[5:0] (RTL: saved_p1a[5:0])
        #   DELTA QRd, Q1, Q2, steps → Q2 in p1_b, steps in r2
        #   QLDI QRd, AB, CD → CD in p1_b
        #   SPREAD Rd, QRa, QRb → QRb index in p1_b
        arg = parts[3].upper()
        if mnemonic in ("ROTC", "IROTC"):
            p1_a = _parse_int16(arg)
        elif arg.startswith('QR'):
            p1_b = int(arg[2:]) & 0xFFFF
        elif arg.startswith('R'):
            p1_b = int(arg[1:]) & 0xFFFF
        else:
            p1_b = _parse_int16(arg)

    # [Op:8][R1:8][R2:8][P1_A:16][P1_B:16][00:8]
    word = (opcode << 56) | (r1 << 48) | (r2 << 40) | (p1_a << 24) | (p1_b << 8)
    return word

def assemble_source(source: str) -> list[int]:
    """Two-pass assembler: first pass collects labels, second emits words."""
    lines = source.splitlines()
    labels: dict[str, int] = {}
    words: list[int] = []

    # Pass 1: collect labels
    addr = 0
    for line in lines:
        clean = line.split(';')[0].strip()
        if clean.endswith(':'):
            labels[clean[:-1].upper()] = addr
        elif clean and clean.split()[0].upper() in OPCODES:
            addr += 1

    # Pass 2: emit
    line_no = 0
    for line in lines:
        line_no += 1
        word = assemble_line(line, line_no, labels)
        if word is not None:
            words.append(word)

    return words


# ---------------------------------------------------------------------------
# Davis Gasket — manifold tension tracker (mirrors spu_physics.h DavisGasket)
# ---------------------------------------------------------------------------

class DavisGasket:
    """
    Tracks manifold tension τ and stiffness K across execution.
    Mirrors the C++ DavisGasket struct in spu_physics.h exactly.

    tau   : RationalSurd — manifold tension; grows on cubic leak, halves on recovery
    K     : RationalSurd — stiffness constant (default unity)
    leak  : bool         — True if last gasket_tick() detected a cubic leak
    tick_count    : int  — total gasket ticks executed
    henosis_count : int  — total Henosis recovery pulses applied
    """
    def __init__(self, tau: RationalSurd = None, K: RationalSurd = None):
        self.tau           = tau if tau is not None else RationalSurd(0, 0)
        self.K             = K   if K   is not None else RationalSurd(1, 0)
        self.leak          = False
        self.tick_count    = 0
        self.henosis_count = 0

    def is_laminar(self) -> bool:
        return not self.leak

    def gasket_tick(self, qregs: list) -> bool:
        """
        One Davis Gate cycle.
        Checks if Σ QR[0..12] == zero vector (cubic leak test).
        On leak: τ += stiffness of vector sum, where stiffness =
            ivm_quadrance + gasket_sum² = 4·Σc².
        On stable: τ >>= 1 (halve toward zero, ANNE mechanic).
        Returns True if a cubic leak was detected this tick.
        """
        self.tick_count += 1
        # Sum all 13 QR registers component-wise
        sa = sb = sc = sd = RationalSurd(0, 0)
        for qr in qregs[:13]:
            sa = sa + qr.a
            sb = sb + qr.b
            sc = sc + qr.c
            sd = sd + qr.d

        # Cubic leak: vector sum ≠ zero
        is_zero_sum = (sa == RationalSurd(0,0) and sb == RationalSurd(0,0)
                       and sc == RationalSurd(0,0) and sd == RationalSurd(0,0))
        self.leak = not is_zero_sum

        if self.leak:
            # τ accumulates: stiffness = ivm_quadrance + gasket_sum² = 4·Σc²
            # (normative formula: knowledge/SPU_LEXICON.md "Davis Gate" entry)
            gs = sa + sb + sc + sd
            vs_ivm = RationalSurd(0, 0)
            comps = [sa, sb, sc, sd]
            for i in range(4):
                for j in range(i + 1, 4):
                    diff = comps[i] - comps[j]
                    vs_ivm = vs_ivm + diff * diff
            self.tau = self.tau + vs_ivm + gs * gs
        else:
            # Stable: halve τ (exact integer >>1)
            self.tau = RationalSurd(self.tau.a >> 1, self.tau.b >> 1)

        return self.leak

    def henosis_pulse(self, qregs: list) -> None:
        """
        Soft recovery: halve each component of every QR register toward zero.
        Matches ANNE opcode semantics in spu_vm.py.
        """
        self.henosis_count += 1
        for qr in qregs[:13]:
            qr.a = RationalSurd(qr.a.a >> 1, qr.a.b >> 1)
            qr.b = RationalSurd(qr.b.a >> 1, qr.b.b >> 1)
            qr.c = RationalSurd(qr.c.a >> 1, qr.c.b >> 1)
            qr.d = RationalSurd(qr.d.a >> 1, qr.d.b >> 1)

    def henosis_recover(self, qregs: list, max_pulses: int = 8) -> int:
        """
        Apply Henosis pulses until the manifold is laminar or max_pulses exhausted.
        Returns number of pulses applied.
        """
        for pulse in range(max_pulses):
            if not self.gasket_tick(qregs):
                return pulse  # already laminar
            self.henosis_pulse(qregs)
        return max_pulses

    def ratio_str(self) -> str:
        """Davis Ratio C = τ/K as a readable string (cross-multiply form)."""
        return f"τ=({self.tau.a},{self.tau.b}√3)  K=({self.K.a},{self.K.b}√3)"

    def __repr__(self) -> str:
        state = "LAMINAR" if self.is_laminar() else "CUBIC-LEAK"
        return (f"DavisGasket({state}  {self.ratio_str()}"
                f"  ticks={self.tick_count}  henosis={self.henosis_count})")


# ---------------------------------------------------------------------------
# Fibonacci Dispatch — Sierpinski-frame gate tracker
# ---------------------------------------------------------------------------

class FibDispatch:
    """
    Tracks the Sierpinski 34-cycle frame and fires phi_8 / phi_13 / phi_21 gates.
    Mirrors fibonacci_gate() in spu_physics.h.

    cycle     : global cycle counter (increments every step() call)
    frame_pos : position within the 34-cycle Sierpinski frame (0–33)

    Gates fire when frame_pos hits the Fibonacci positions:
      phi_8  at frame_pos == 8   (micro gate)
      phi_13 at frame_pos == 13  (meso gate)
      phi_21 at frame_pos == 21  (macro gate)
    """
    FRAME_LEN = 34
    PHI_8     = 8
    PHI_13    = 13
    PHI_21    = 21

    def __init__(self):
        self.cycle     = 0
        self.frame_pos = 0

    def tick(self) -> str:
        """
        Advance one cycle. Returns gate label string or '' if no gate.
        """
        gate = ''
        if self.frame_pos == self.PHI_21:
            gate = 'φ₂₁'
        elif self.frame_pos == self.PHI_13:
            gate = 'φ₁₃'
        elif self.frame_pos == self.PHI_8:
            gate = 'φ₈ '
        self.cycle     += 1
        self.frame_pos  = (self.frame_pos + 1) % self.FRAME_LEN
        return gate

    def is_phi8(self)  -> bool: return self.frame_pos == self.PHI_8
    def is_phi13(self) -> bool: return self.frame_pos == self.PHI_13
    def is_phi21(self) -> bool: return self.frame_pos == self.PHI_21

    def at_gate(self) -> bool:
        return self.frame_pos in (self.PHI_8, self.PHI_13, self.PHI_21)

    def gate_name(self) -> str:
        if self.frame_pos == self.PHI_21: return 'φ₂₁(macro)'
        if self.frame_pos == self.PHI_13: return 'φ₁₃(meso)'
        if self.frame_pos == self.PHI_8:  return 'φ₈ (micro)'
        return '—'

    def __repr__(self) -> str:
        return f"FibDispatch(cycle={self.cycle}  frame={self.frame_pos}/33  gate={self.gate_name()})"


# ---------------------------------------------------------------------------
# SDF State — rational distance field tracker (mirrors spu_sdf.h)
# ---------------------------------------------------------------------------

class SdfState:
    """
    Tracks the SDF-layer state across SNAP boundaries.
    Mirrors the key functions of spu_sdf.h Layer 7 in pure Python.

    nearest_axis  : index of the QR register closest to the current impact
                    (= sdf_nearest applied to each active QR register pair)
    min_q         : minimum Quadrance distance found at last SNAP
    snap_conflict : True if grad · vec_sum ≠ 0 (sdf_snap equivalent)
    snap_count    : total SNAP boundaries evaluated
    conflict_count: total times a snap conflict was detected
    """

    def __init__(self):
        self.nearest_axis   = 0
        self.min_q          = 0
        self.snap_conflict  = False
        self.snap_count     = 0
        self.conflict_count = 0

    # ── sdf_q equivalent ─────────────────────────────────────────────────
    @staticmethod
    def qr_quadrance(qv: 'QuadrayVector') -> int:
        """Quadrance of a QuadrayVector from the zero vector.
        Uses pairwise-difference formula matching spu_quadray.h::quadrance().
        Returns integer (rational part only — b=0 for all IVM-canonical axes).
        """
        comps = [qv.a.a, qv.b.a, qv.c.a, qv.d.a]
        q = 0
        for i in range(4):
            for j in range(i + 1, 4):
                diff = comps[i] - comps[j]
                q += diff * diff
        return q

    @staticmethod
    def qr_dist_q(qa: 'QuadrayVector', qb: 'QuadrayVector') -> int:
        """sdf_q: Quadrance distance between two QuadrayVectors."""
        diff = qa - qb
        return SdfState.qr_quadrance(diff)

    # ── sdf_nearest equivalent ────────────────────────────────────────────
    @staticmethod
    def nearest(target: 'QuadrayVector', qregs: list) -> tuple[int, int]:
        """
        Returns (nearest_idx, min_q) — the QR register index closest to
        target and the Quadrance distance.  Skips zero registers.
        """
        best_idx = -1
        best_q   = None
        for i, qr in enumerate(qregs[:13]):
            if qr.is_zero():
                continue
            q = SdfState.qr_dist_q(target, qr)
            if best_q is None or q < best_q:
                best_q   = q
                best_idx = i
        return (best_idx if best_idx >= 0 else 0,
                best_q   if best_q  is not None else 0)

    # ── sdf_grad equivalent ───────────────────────────────────────────────
    @staticmethod
    def grad(target: 'QuadrayVector', qregs: list) -> 'QuadrayVector':
        """Gradient: vector from target toward nearest QR register."""
        idx, _ = SdfState.nearest(target, qregs)
        return qregs[idx] - target

    # ── sdf_snap equivalent ───────────────────────────────────────────────
    @staticmethod
    def snap_check(grad: 'QuadrayVector', qregs: list) -> bool:
        """
        Returns True if grad · vec_sum ≠ 0 (Henosis needed).
        vec_sum = Σ QR[0..12] (the Davis cubic leak vector).
        dot = component-wise Σ grad_i · vec_sum_i (integer parts).
        """
        # Compute vec_sum
        sa = sb = sc = sd = 0
        for qr in qregs[:13]:
            sa += qr.a.a;  sb += qr.b.a
            sc += qr.c.a;  sd += qr.d.a
        # dot product (integer parts only — b=0 for canonical axes)
        dot = (grad.a.a * sa + grad.b.a * sb +
               grad.c.a * sc + grad.d.a * sd)
        return dot != 0

    # ── Called at every SNAP boundary ─────────────────────────────────────
    def evaluate(self, qregs: list, sdf_trace: bool = False,
                 pc: int = 0) -> None:
        """
        Full SDF evaluation at a SNAP boundary:
          1. Find nearest QR axis to QR0 (the canonical 'impact origin')
          2. Compute gradient toward nearest axis
          3. Check for snap conflict (grad · vec_sum ≠ 0)
        """
        self.snap_count += 1

        if all(qr.is_zero() for qr in qregs[:13]):
            self.nearest_axis  = 0
            self.min_q         = 0
            self.snap_conflict = False
            if sdf_trace:
                print(f"  [{pc:04d}] SDF  (all QR zero — no surface)")
            return

        # Use QR0 as the reference "impact point"
        target = qregs[0]
        self.nearest_axis, self.min_q = self.nearest(target, qregs[1:])
        self.nearest_axis += 1  # offset back to full qregs index

        gradient = self.grad(target, qregs)
        self.snap_conflict = self.snap_check(gradient, qregs)

        if self.snap_conflict:
            self.conflict_count += 1

        if sdf_trace:
            state = "⚠ CONFLICT" if self.snap_conflict else "✓ coherent"
            print(f"  [{pc:04d}] SDF  nearest=QR{self.nearest_axis}"
                  f"  Q={self.min_q}  {state}"
                  f"  (snap#{self.snap_count}  conflicts={self.conflict_count})")

    def __repr__(self) -> str:
        state = "CONFLICT" if self.snap_conflict else "coherent"
        return (f"SdfState({state}  nearest=QR{self.nearest_axis}"
                f"  Q={self.min_q}"
                f"  snaps={self.snap_count}  conflicts={self.conflict_count})")



NUM_REGS = 26  # R0–R25 (one per axis + spares)

class SPUCore:
    """
    Software model of the SPU-13 Sovereign Core.
    Executes 64-bit SAS control words in Q(√3).

    Register file:
      R0–R25  : 26 scalar RationalSurd registers
      QR0–QR12: 13 QuadrayVector registers (one per SPU-13 manifold axis)
    """

    def __init__(self, max_steps: int = 10_000, verbose: bool = True,
                 proof: bool = False, sdf_trace: bool = False,
                 gasket_trace: bool = False):
        self.regs: list[RationalSurd] = [RationalSurd(0, 0) for _ in range(NUM_REGS)]
        self.qregs: list[QuadrayVector] = [QuadrayVector() for _ in range(13)]
        # φ-plane DOUBLED typestate (IROTC_SPEC.md §3) — PHI_UNTAGGED /
        # PHI_FRESH / PHI_MAIN / PHI_CONJ per QR register, living with the
        # register file (load() preserves qregs, so tags too).
        self.qr_doubled: list[int] = [PHI_UNTAGGED] * 13
        self.call_stack: list[int] = []
        self.pc: int = 0
        self.program: list[int] = []
        self.step_count: int = 0
        self.max_steps: int = max_steps
        self.verbose: bool = verbose
        self.proof: bool = proof       # show step-by-step Q(√3) arithmetic derivations
        self.sdf_trace: bool = sdf_trace  # per-SNAP SDF nearest-axis + conflict trace
        self.gasket_trace: bool = gasket_trace  # per-gate Davis Ratio table
        self.halted: bool = False
        self.snap_failures: int = 0
        self.log: list[str] = []
        # v1.3 additions — Davis Gasket + Fibonacci dispatch
        self.gasket   = DavisGasket()
        self.fib      = FibDispatch()
        # v1.4 additions — SDF Layer 7 state
        self.sdf      = SdfState()
        # phinary configuration (SPU-4 compatibility)
        self.phinary_cfg = 0
        self.phinary_void_state = False

        # ── SOM writable weight memory (for training) ──────────
        # Mirrors spu_som_train.v BRAM.  7 nodes, 4 features each.
        self._som_best_id = -1
        self._som_last_features = None
        def _rs(a, b=0): return RationalSurd(a, b)
        self._som_weights = [
            (_rs(0), _rs(0), _rs(0), _rs(0)),          # node 0
            (_rs(2), _rs(0), _rs(0), _rs(0)),          # node 1
            (_rs(0), _rs(2), _rs(0), _rs(0)),          # node 2
            (_rs(0), _rs(0), _rs(2), _rs(0)),          # node 3
            (_rs(-2), _rs(0), _rs(0), _rs(0)),         # node 4
            (_rs(0), _rs(-2), _rs(0), _rs(0)),         # node 5
            (_rs(0), _rs(0), _rs(-2), _rs(1, 1)),     # node 6
        ]

    @staticmethod
    def _q_proof(r: 'RationalSurd', label: str = "") -> str:
        """Return a human-readable Q = a² - 3b² derivation string."""
        a, b = r.a, r.b
        q = a*a - 3*b*b
        stable = "✓ laminar" if q > 0 else ("∅ zero" if q == 0 else "✗ CUBIC")
        prefix = f"{label}  " if label else "  "
        return f"{prefix}Q({r!r}) = {a}² - 3·{b}² = {a*a} - {3*b*b} = {q}  {stable}"

    def load(self, words: list[int]):
        self.program = words
        self.pc = 0
        self.halted = False
        self.step_count = 0
        self.gasket = DavisGasket()
        self.fib    = FibDispatch()
        self.sdf    = SdfState()
        if self.verbose:
            print(f"  SPU-VM: {len(words)} words loaded.")

    # ── gasket-trace helper ───────────────────────────────────────────────
    def _gasket_trace_line(self, gate: str) -> None:
        """Print a compact Davis Ratio table row."""
        # C = τ/K — show as cross-multiply comparison τ·1 vs K·? (K=1 default)
        tau_p = self.gasket.tau.a
        tau_q = self.gasket.tau.b
        K_p   = self.gasket.K.a   if self.gasket.K.a != 0 else 1
        state = "LEAK" if self.gasket.leak else "ok  "
        # SDF nearest axis
        sdf_info = f"near=QR{self.sdf.nearest_axis} Q={self.sdf.min_q}"
        print(f"  GASKET  {gate:<6s}  cyc={self.fib.cycle:3d}"
              f"  τ=({tau_p:+5d},{tau_q:+3d}√3)  K={K_p}"
              f"  {state}"
              f"  {sdf_info}"
              f"  h={self.gasket.henosis_count}")

    def decode(self, word: int) -> tuple:
        opcode = (word >> 56) & 0xFF
        r1     = (word >> 48) & 0xFF
        r2     = (word >> 40) & 0xFF
        p1_a   = (word >> 24) & 0xFFFF
        p1_b   = (word >>  8) & 0xFFFF
        # Sign-extend 16-bit values
        if p1_a & 0x8000: p1_a -= 0x10000
        if p1_b & 0x8000: p1_b -= 0x10000
        return opcode, r1, r2, p1_a, p1_b

    def _reg_str(self, idx: int) -> str:
        r = self.regs[idx]
        q = r.quadrance()
        stable = "✓" if q > 0 else ("∅" if q == 0 else "✗")
        return f"R{idx:02d}={r!r:24s} Q={q:>8d} {stable} C={r.davis_c()}"

    def _qreg_str(self, idx: int) -> str:
        qr = self.qregs[idx]
        q = qr.quadrance()
        hx, hy = qr.hex_project()
        return f"QR{idx:02d}={qr!r:50s} Q={q!r:16s} hex=({hx:>4d},{hy:>4d})"

    def step(self) -> bool:
        """Execute one instruction. Returns False if halted."""
        if self.halted or self.pc >= len(self.program):
            self.halted = True
            return False

        word = self.program[self.pc]
        opcode, r1, r2, p1_a, p1_b = self.decode(word)
        next_pc = self.pc + 1

        imm = RationalSurd(p1_a, p1_b)
        # Seed pell_step=0 when loading the Pell unity seed (1,0) — enables
        # octave tracking for subsequent ROT instructions on this register.
        if p1_a == 1 and p1_b == 0:
            imm = RationalSurd(1, 0, pell_step=0)

        # ------------------------------------------------------------------
        # Scalar Q(√3) arithmetic
        # ------------------------------------------------------------------
        if opcode == OPCODES["LD"]:
            self.regs[r1] = imm
            if self.verbose:
                print(f"  [{self.pc:04d}] LD    R{r1} ← {imm!r}")
            if self.proof:
                print(f"         {self._q_proof(imm, f'R{r1}:')}")

        elif opcode == OPCODES["ADD"]:
            prev = self.regs[r1]
            self.regs[r1] = self.regs[r1] + self.regs[r2]
            if self.verbose:
                print(f"  [{self.pc:04d}] ADD   R{r1} + R{r2} → {self.regs[r1]!r}")
            if self.proof:
                a1, b1 = prev.a, prev.b
                a2, b2 = self.regs[r2].a, self.regs[r2].b
                print(f"         ({a1} + {b1}·√3) + ({a2} + {b2}·√3)"
                      f"  →  a={a1}+{a2}={a1+a2}  b={b1}+{b2}={b1+b2}")

        elif opcode == OPCODES["SUB"]:
            prev = self.regs[r1]
            # SUB Rd, Rs  — Rd = Rd - Rs
            self.regs[r1] = self.regs[r1] - self.regs[r2]
            if self.verbose:
                print(f"  [{self.pc:04d}] SUB  R{r1} - R{r2} → {self.regs[r1]!r}")
            if self.proof:
                a1, b1 = prev.a, prev.b
                a2, b2 = self.regs[r2].a, self.regs[r2].b
                print(f"         ({a1} + {b1}·√3) - ({a2} + {b2}·√3)"
                      f"  →  a={a1}-{a2}={a1-a2}  b={b1}-{b2}={b1-b2}")

        elif opcode == OPCODES["MUL"]:
            # MUL Rd, Rs  — Rd = Rd × Rs  (closed in Q(√3))
            prev = self.regs[r1]
            self.regs[r1] = self.regs[r1] * self.regs[r2]
            if self.verbose:
                print(f"  [{self.pc:04d}] MUL  R{r1} × R{r2} → {self.regs[r1]!r}")
            if self.proof:
                a1, b1 = prev.a, prev.b
                a2, b2 = self.regs[r2].a, self.regs[r2].b
                ra = a1*a2 + 3*b1*b2
                rb = a1*b2 + b1*a2
                print(f"         ({a1} + {b1}·√3) × ({a2} + {b2}·√3)")
                print(f"         a = {a1}·{a2} + 3·{b1}·{b2} = {a1*a2} + {3*b1*b2} = {ra}")
                print(f"         b = {a1}·{b2} + {b1}·{a2}   = {a1*b2} + {b1*a2}   = {rb}")
                print(f"         {self._q_proof(self.regs[r1])}")

        elif opcode == OPCODES["ROT"]:
            # ROT Rn — apply Phi-Rotor (×(2+√3)) — Pell orbit step
            # Uses Pell Octave representation: step wraps at 8, octave increments.
            # Stored (a,b) stays in fundamental domain (fits int16), norm always 1.
            prev = self.regs[r1]
            self.regs[r1] = prev.rotate_phi()
            new_r = self.regs[r1]
            if self.verbose:
                oct_info = ""
                if new_r.pell_step is not None:
                    oct_n, step_n = divmod(new_r.pell_step, 8)
                    oct_info = f"  [oct={oct_n}, step={step_n}, total=r^{new_r.pell_step}]"
                print(f"  [{self.pc:04d}] ROT  R{r1}: {prev!r} → {new_r!r}{oct_info}")
            if self.proof:
                a, b = prev.a, prev.b
                na, nb = 2*a + 3*b, a + 2*b
                print(f"         Pell step: (2+√3) × ({a} + {b}·√3)")
                print(f"         a = 2·{a} + 3·{b} = {2*a} + {3*b} = {na}")
                print(f"         b = {a} + 2·{b}   = {nb}")
                print(f"         {self._q_proof(self.regs[r1])}")

        elif opcode == OPCODES["LOG"]:
            msg = self._reg_str(r1)
            self.log.append(msg)
            print(f"  [{self.pc:04d}] LOG  {msg}")

        elif opcode == OPCODES["JMP"]:
            target = p1_a & 0xFFFF
            if self.verbose:
                print(f"  [{self.pc:04d}] JMP  → {target}")
            next_pc = target

        elif opcode == OPCODES["SNAP"]:
            # SNAP — Davis Gate: assert all non-zero scalar regs are Laminar (norm > 0)
            # For Pell-octave registers: norm is trivially 1 (stored mantissa from vault).
            # For general surds: check a²-3b² > 0 as usual.
            failures = []
            for i in range(NUM_REGS):
                r = self.regs[i]
                if r.a != 0 or r.b != 0:
                    if not r.is_laminar():
                        failures.append(i)
            if failures:
                self.snap_failures += 1
                print(f"  [{self.pc:04d}] SNAP ✗ CUBIC LEAK — unstable regs: {failures}")
                if self.proof:
                    for i in failures:
                        print(f"         {self._q_proof(self.regs[i], f'R{i}:')}")
            else:
                if self.verbose:
                    # Show octave info for any tracked rotor registers
                    oct_summary = []
                    for i in range(NUM_REGS):
                        r = self.regs[i]
                        if r.pell_step is not None and (r.a != 0 or r.b != 0):
                            oct_n, step_n = divmod(r.pell_step, 8)
                            oct_summary.append(f"R{i}=r^{r.pell_step}(oct={oct_n},s={step_n})")
                    oct_str = "  " + ", ".join(oct_summary) if oct_summary else ""
                    print(f"  [{self.pc:04d}] SNAP ✓ Manifold stable{oct_str}")
                if self.proof:
                    for i in range(NUM_REGS):
                        r = self.regs[i]
                        if r.a != 0 or r.b != 0:
                            print(f"         {self._q_proof(r, f'R{i}:')}")

            # Layer 7 SDF evaluation — runs regardless of scalar laminar result.
            # Checks QR-manifold coherence (grad · vec_sum) and tracks nearest axis.
            self.sdf.evaluate(self.qregs, sdf_trace=self.sdf_trace, pc=self.pc)
            if self.sdf.snap_conflict and not failures:
                # QR conflict not caught by scalar check — report separately
                self.snap_failures += 1
                print(f"  [{self.pc:04d}] SNAP ✗ SDF CONFLICT — QR manifold"
                      f" grad·sum≠0  nearest=QR{self.sdf.nearest_axis}"
                      f"  Q={self.sdf.min_q}")

        # ------------------------------------------------------------------
        # Control flow
        # ------------------------------------------------------------------
        elif opcode == OPCODES["COND"]:
            # COND Rn, addr — jump to addr if Rn.quadrance() > 0 (laminar test)
            q = self.regs[r1].quadrance()
            if q > 0:
                next_pc = p1_a & 0xFFFF
                if self.verbose:
                    print(f"  [{self.pc:04d}] COND R{r1} Q={q}>0 ✓ → {next_pc}")
            else:
                if self.verbose:
                    print(f"  [{self.pc:04d}] COND R{r1} Q={q}≤0 ✗ fall-through")

        elif opcode == OPCODES["CALL"]:
            # CALL addr — push return address, jump
            self.call_stack.append(next_pc)
            next_pc = p1_a & 0xFFFF
            if self.verbose:
                print(f"  [{self.pc:04d}] CALL → {next_pc}  (ret={self.call_stack[-1]})")

        elif opcode == OPCODES["RET"]:
            # RET — pop and return
            if self.call_stack:
                next_pc = self.call_stack.pop()
                if self.verbose:
                    print(f"  [{self.pc:04d}] RET  → {next_pc}")
            else:
                if self.verbose:
                    print(f"  [{self.pc:04d}] RET  (empty stack — halting)")
                self.halted = True

        # ------------------------------------------------------------------
        # Quadray IVM operations  (QR registers)
        # ------------------------------------------------------------------
        elif opcode == OPCODES["QLOAD"]:
            # QLOAD QRn, Rbase — pack R[base..base+3] into QRn
            base = r2
            qr = QuadrayVector(
                self.regs[(base + 0) % NUM_REGS],
                self.regs[(base + 1) % NUM_REGS],
                self.regs[(base + 2) % NUM_REGS],
                self.regs[(base + 3) % NUM_REGS],
            )
            self.qregs[r1 % 13] = qr
            self.qr_doubled[r1 % 13] = PHI_UNTAGGED  # raw load clears DOUBLED
            if self.verbose:
                print(f"  [{self.pc:04d}] QLOAD QR{r1} ← R{base}..R{base+3} = {qr!r}")

        elif opcode == OPCODES["QLDI"]:
            # QLDI QRd, A, B, C, D — load integer Quadray from immediate
            # P1_A[15:8]=A, P1_A[7:0]=B, P1_B[15:8]=C, P1_B[7:0]=D
            a = (p1_a >> 8) & 0xFF
            b = p1_a & 0xFF
            c = (p1_b >> 8) & 0xFF
            d = p1_b & 0xFF
            # Sign-extend from 8-bit to signed int
            A = a - 256 if a >= 128 else a
            B = b - 256 if b >= 128 else b
            C = c - 256 if c >= 128 else c
            D = d - 256 if d >= 128 else d
            self.qregs[r1 % 13] = QuadrayVector(
                RationalSurd(A, 0), RationalSurd(B, 0),
                RationalSurd(C, 0), RationalSurd(D, 0),
            )
            self.qr_doubled[r1 % 13] = PHI_UNTAGGED  # raw load clears DOUBLED
            if self.verbose:
                print(f"  [{self.pc:04d}] QLDI QR{r1} ← ({A},{B},{C},{D}) "
                      f"→ {self.qregs[r1 % 13]!r}")

        elif opcode == OPCODES["DELTA"]:
            # DELTA QRd, Q1, Q2, steps — triple quadrance parameterization
            # P1_A[15:0] = Q1, P1_B[15:0] = Q2, R2 = steps
            # Computes (Q3 − Q1 − Q2)² = 4·Q1·Q2·(1−s) for s = k/steps.
            # Stores q_sum in QRd.A, last rhs² in QRd.B (num) and QRd.C (den).
            Q1 = p1_a & 0xFFFF
            Q2 = p1_b & 0xFFFF
            steps = r2 if r2 > 0 else 4
            d = r1 % 13
            q_sum = Q1 + Q2
            rhs_sq = 4 * Q1 * Q2  # for k=0 (collapsed), rhs² is maximal

            # Iterate through steps to find the last meaningful rhs²
            for k in range(steps + 1):
                rhs = (4 * Q1 * Q2 * (steps - k)) // steps
                if k == steps:
                    rhs_sq = rhs  # right triangle: rhs² = 0

            self.qregs[d] = QuadrayVector(
                RationalSurd(q_sum, 0),
                RationalSurd(rhs_sq, 0),
                RationalSurd(steps, 0),
                RationalSurd(0, 0),
            )
            self.qr_doubled[d] = PHI_UNTAGGED  # raw load clears DOUBLED
            if self.verbose:
                print(f"  [{self.pc:04d}] DELTA QR{d} Q1={Q1} Q2={Q2} "
                      f"steps={steps} → q_sum={q_sum} rhs²={rhs_sq}/{steps}")


        elif opcode == OPCODES["QADD"]:
            # QADD QRd, QRs — QRd = QRd + QRs
            d, s = r1 % 13, r2 % 13
            self.qregs[d] = self.qregs[d] + self.qregs[s]
            # φ-plane typestate: lattice join (linearity; mixed catalogs or
            # an untagged operand clear the tag — IROTC_SPEC.md §3).
            self.qr_doubled[d] = _phi_tag_join(self.qr_doubled[d],
                                               self.qr_doubled[s])
            if self.verbose:
                print(f"  [{self.pc:04d}] QADD QR{d} + QR{s} → {self.qregs[d]!r}")

        elif opcode == OPCODES["QSUB"]:
            # QSUB QRd, QRa, QRb — QR[d] = QR[a] - QR[b]
            # Two-operand assembly is encoded as QSUB QRd, QRd, QRs.
            d, a, b = r1 % 13, r2 % 13, p1_b % 13
            self.qregs[d] = self.qregs[a] - self.qregs[b]
            self.qr_doubled[d] = _phi_tag_join(self.qr_doubled[a],
                                               self.qr_doubled[b])
            if self.verbose:
                print(f"  [{self.pc:04d}] QSUB QR{d} ← QR{a} - QR{b} → {self.qregs[d]!r}")

        elif opcode == OPCODES["QROT"]:
            # QROT QRn — apply Pell rotor to each component + normalize
            n = r1 % 13
            prev = self.qregs[n]
            self.qregs[n] = prev.rotate()
            self.qr_doubled[n] = PHI_UNTAGGED  # Q(√3) Pell rotor — wrong plane
            if self.verbose:
                hx, hy = self.qregs[n].hex_project()

        elif opcode == OPCODES["ROTC"]:
            # ROTC QRd, QRs, angle — F,G,H circulant rotation or pure
            # coordinate permutation (zero multiplies, no /3).
            #
            # Format for circulant entries: (Fa,Fb, Ga,Gb, Ha,Hb, denom, field)
            #   field: 0=Q(√3), 1=Q(√5), 2=Q(√15)
            #
            # Angles 0-11 and 12-14 are circulant (thirds or identity).
            # Angles 2,5,15-20 are 3-cycle permutations (bypass_p5/bypass_p5_inv
            #   conjugated by an axis permutation).
            # Angles 21-23 are double-transposition permutations
            #   ((AB)(CD), (AC)(BD), (AD)(BC)) — direct wire swaps.
            #
            # Group structure: 24 distinct rotations, det +1, inverse-closed.
            # Tranche 1 (12-14): missing thirds conjugates, supply the inverses
            #   of 9 (→13) and 10 (→14), plus the self-inverse 12 (180°@B).
            # Tranche 2 (15-23): remaining A₄ pure permutations.
            # Cross-verified 2026-07-10 against an independent exact-Fraction
            # oracle and the RTL (test_rotc_vm_rtl_trace.py + core opcode TB).
            ROTC_MAX_VERIFIED_ANGLE = 35
            _ROTC_TABLE = {
                # Angles 0-5 (circulant, A-invariant)
                0:  (1,  0,  0, 0,  0, 0, 1, 0),    # identity
                1:  (2,  0,  2, 0, -1, 0, 3, 0),    # thirds period-6
                2:  (0,  0,  1, 0,  0, 0, 1, 0),    # P5 forward  (also bypass)
                3:  (-1, 0,  2, 0,  2, 0, 3, 0),    # thirds period-2
                4:  (2,  0, -1, 0,  2, 0, 3, 0),    # thirds period-6 inv
                5:  (0,  0,  0, 0,  1, 0, 1, 0),    # P5 inverse  (also bypass)
                # Angles 6-11 (thirds, B/C/D conjugates)
                6:  (2,  0, -1, 0,  2, 0, 3, 0),    # 240° about B
                7:  (2,  0,  2, 0, -1, 0, 3, 0),    #  60° about B
                8:  (-1, 0,  2, 0,  2, 0, 3, 0),    # 180° about C
                9:  (2,  0,  2, 0, -1, 0, 3, 0),    #  60° about C
                10: (2,  0, -1, 0,  2, 0, 3, 0),    # 240° about D
                11: (-1, 0,  2, 0,  2, 0, 3, 0),    # 180° about D
                # Tranche 1: missing thirds conjugates
                12: (-1, 0,  2, 0,  2, 0, 3, 0),    # 180° about B (self-inverse)
                13: (2,  0, -1, 0,  2, 0, 3, 0),    # 240° about C (inverse of 9)
                14: (2,  0,  2, 0, -1, 0, 3, 0),    #  60° about D (inverse of 10)
                # Tranche 2: bypass entries use F/G/H for informational purposes
                # only — the handler below skips the circulant path for these.
                15: (0,  0,  1, 0,  0, 0, 1, 0),    # P5 fwd about B
                16: (0,  0,  0, 0,  1, 0, 1, 0),    # P5 inv about B
                17: (0,  0,  1, 0,  0, 0, 1, 0),    # P5 fwd about C
                18: (0,  0,  0, 0,  1, 0, 1, 0),    # P5 inv about C
                19: (0,  0,  1, 0,  0, 0, 1, 0),    # P5 fwd about D
                20: (0,  0,  0, 0,  1, 0, 1, 0),    # P5 inv about D
                21: (0,  0,  0, 0,  0, 0, 1, 0),    # (AB)(CD)
                22: (0,  0,  0, 0,  0, 0, 1, 0),    # (AC)(BD)
                23: (0,  0,  0, 0,  0, 0, 1, 0),    # (AD)(BC)
            }
            angle = p1_a & 0x3F       # 6-bit angle (0-63)
            field_sel = (p1_a >> 6) & 0x3  # 2-bit field selector
            if angle > ROTC_MAX_VERIFIED_ANGLE:
                raise RotcUnverifiedAngleError(
                    f"ROTC angle {angle} is not implemented/verified "
                    f"(only 0-{ROTC_MAX_VERIFIED_ANGLE} are); refusing "
                    f"rather than silently corrupting QR{r1 % 13}"
                )
            d, s = r1 % 13, r2 % 13

            # ── Pure permutation bypass path ──────────────────────────
            # Angles 2,5,15-20: perm_sel + bypass_p5/bypass_p5_inv + inv_perm.
            # Angles 21-23: direct double-transposition wire swap.
            _BYPASS_P5     = {2, 15, 17, 19}     # B'=D, C'=B, D'=C
            _BYPASS_P5_INV = {5, 16, 18, 20}     # B'=C, C'=D, D'=B
            _BYPASS_DOUBLE = {21, 22, 23}
            _ALL_BYPASS    = _BYPASS_P5 | _BYPASS_P5_INV | _BYPASS_DOUBLE

            if angle in _ALL_BYPASS:
                src = self.qregs[s]
                comps = (src.a, src.b, src.c, src.d)

                if angle in _BYPASS_DOUBLE:
                    # Direct component swap — no perm_sel needed.
                    if angle == 21:       # (AB)(CD): A↔B, C↔D
                        result = QuadrayVector(src.b, src.a, src.d, src.c)
                    elif angle == 22:     # (AC)(BD): A↔C, B↔D
                        result = QuadrayVector(src.c, src.d, src.a, src.b)
                    else:                 # (AD)(BC): A↔D, B↔C
                        result = QuadrayVector(src.d, src.c, src.b, src.a)
                else:
                    # 3-cycle via perm_sel + bypass.
                    # Perm_sel: 0=A-inv(2,5), 1=B-inv(15,16), 2=C-inv(17,18), 3=D-inv(19,20)
                    if angle in (2, 5):
                        perm_sel = 0
                    elif angle in (15, 16):
                        perm_sel = 1
                    elif angle in (17, 18):
                        perm_sel = 2
                    else:  # 19, 20
                        perm_sel = 3
                    pf = comps[perm_sel:] + comps[:perm_sel]
                    if angle in _BYPASS_P5:
                        bp = (pf[0], pf[3], pf[1], pf[2])   # B'=D, C'=B, D'=C
                    else:
                        bp = (pf[0], pf[2], pf[3], pf[1])   # B'=C, C'=D, D'=B
                    inv_sel = (-perm_sel) % 4
                    result = QuadrayVector(*(bp[inv_sel:] + bp[:inv_sel]))

                self.qregs[d] = result
                # Pure component permutation: bit-identical shuffle, so the
                # DOUBLED tag rides along (enables A₄ alias interop with IROTC).
                self.qr_doubled[d] = self.qr_doubled[s]
                if self.verbose:
                    _angles_names = {
                        2: "120°D", 5: "300°D",
                        15: "120°@B", 16: "300°@B",
                        17: "120°@C", 18: "300°@C",
                        19: "120°@D", 20: "300°@D",
                        21: "(AB)(CD)", 22: "(AC)(BD)", 23: "(AD)(BC)",
                    }
                    print(f"  [{self.pc:04d}] ROTC QR{d} ← QR{s} "
                          f"@{_angles_names[angle]} → {self.qregs[d]!r}")

            elif angle >= 24 and angle <= 35:
                # ── Octahedral group (angles 24-35): integer 3×3 on BCD ──
                # Entries are 0 or ±1 — zero multiplies, zero /3.
                # Hardwired in RTL via angle_scalar_*_sum (spu13_rotor_core_tdm.v).
                # Angles 24,25,28,31,32,34: period-2 self-inverse (180° edge
                #   rotations = negation ∘ diagonal transposition).
                # Angles 26↔27, 29↔30, 33↔35: period-4 inverse pairs
                #   (90°/270° face rotations about x, z, y respectively).
                _OCT_MATRIX = {
                    24: ((-1,0,0),(0,0,-1),(0,-1,0)),  # B'=-B, C'=-D, D'=-C
                    25: ((1,1,1),(0,-1,0),(0,0,-1)),    # B'=B+C+D, C'=-C, D'=-D
                    26: ((0,-1,0),(1,1,1),(-1,0,0)),    # B'=-C, C'=B+C+D, D'=-B
                    27: ((0,0,-1),(-1,0,0),(1,1,1)),    # B'=-D, C'=-B, D'=B+C+D
                    28: ((0,-1,0),(-1,0,0),(0,0,-1)),   # B'=-C, C'=-B, D'=-D
                    29: ((1,1,1),(0,0,-1),(-1,0,0)),    # B'=B+C+D, C'=-D, D'=-B
                    30: ((0,0,-1),(1,1,1),(0,-1,0)),    # B'=-D, C'=B+C+D, D'=-C
                    31: ((-1,0,0),(0,-1,0),(1,1,1)),    # B'=-B, C'=-C, D'=B+C+D
                    32: ((0,0,-1),(0,-1,0),(-1,0,0)),   # B'=-D, C'=-C, D'=-B
                    33: ((1,1,1),(-1,0,0),(0,-1,0)),    # B'=B+C+D, C'=-B, D'=-C
                    34: ((-1,0,0),(1,1,1),(0,0,-1)),    # B'=-B, C'=B+C+D, D'=-D
                    35: ((0,-1,0),(0,0,-1),(1,1,1)),    # B'=-C, C'=-D, D'=B+C+D
                }
                rows = _OCT_MATRIX[angle]
                src = self.qregs[s]
                B_val = src.b  # RationalSurd
                C_val = src.c
                D_val = src.d
                # Compute B', C', D' from the 3×3 matrix
                Bp = (RationalSurd(rows[0][0], 0) * B_val +
                      RationalSurd(rows[0][1], 0) * C_val +
                      RationalSurd(rows[0][2], 0) * D_val)
                Cp = (RationalSurd(rows[1][0], 0) * B_val +
                      RationalSurd(rows[1][1], 0) * C_val +
                      RationalSurd(rows[1][2], 0) * D_val)
                Dp = (RationalSurd(rows[2][0], 0) * B_val +
                      RationalSurd(rows[2][1], 0) * C_val +
                      RationalSurd(rows[2][2], 0) * D_val)
                # A' = -(B'+C'+D') from zero-sum
                Ap = RationalSurd(-(Bp.a + Cp.a + Dp.a), -(Bp.b + Cp.b + Dp.b))
                self.qregs[d] = QuadrayVector(Ap, Bp, Cp, Dp)
                # Octahedral matrices are integer but NOT in A₅: evenness
                # (FRESH) survives, but catalog safety does not — sandwich
                # products M₂·O·M₁ reach denominator 4, so MAIN/CONJ demote
                # to UNTAGGED (machine-checked 2026-07-10).
                self.qr_doubled[d] = (PHI_FRESH
                                      if self.qr_doubled[s] == PHI_FRESH
                                      else PHI_UNTAGGED)
                if self.verbose:
                    _oct_names = {
                        24: "180°edge(CD)", 25: "180°edge(AB)",
                        26: "90°face(x)",   27: "270°face(x)",
                        28: "180°edge(BC)", 29: "90°face(z)",
                        30: "270°face(z)",  31: "180°edge(AD)",
                        32: "180°edge(BD)", 33: "270°face(y)",
                        34: "180°edge(AC)", 35: "90°face(y)",
                    }
                    print(f"  [{self.pc:04d}] ROTC QR{d} ← QR{s} "
                          f"@{_oct_names[angle]} → {self.qregs[d]!r}")

            elif angle in _ROTC_TABLE:
                # ── Circulant path (thirds + identity) ─────────────────
                Fa, Fb, Ga, Gb, Ha, Hb, denom, _field = _ROTC_TABLE[angle]
                F = RationalSurd(Fa, Fb)
                G = RationalSurd(Ga, Gb)
                H = RationalSurd(Ha, Hb)

                # Axis permutation for conjugated angles (mirrors
                # spu_quadray_permute u_perm_fwd/u_perm_inv in spu13_core.v).
                #   0-5,21-23: sel 0 (identity or direct bypass)
                #   6-7,12,15-16: sel 1 (B→A)
                #   8-9,13,17-18: sel 2 (C→A)
                #   10-11,14,19-20: sel 3 (D→A)
                # Bypass angles are handled above, so only 0-14 reach here;
                # this keeps the range check simple.
                perm_sel = 0 if angle < 6 else \
                           1 if angle in (6, 7, 12) else \
                           2 if angle in (8, 9, 13) else 3
                src = self.qregs[s]
                comps = (src.a, src.b, src.c, src.d)
                pA, pB, pC, pD = comps[perm_sel:] + comps[:perm_sel]

                # Q12 fixed-point scaling (matching hardware surd_multiplier >>16).
                Q12 = 4096
                B = RationalSurd(pB.a * Q12, pB.b * Q12)
                C = RationalSurd(pC.a * Q12, pC.b * Q12)
                D = RationalSurd(pD.a * Q12, pD.b * Q12)

                # Apply circulant with scaled coefficients
                b2 = F * B + H * C + G * D
                c2 = G * B + F * C + H * D
                d2 = H * B + G * C + F * D

                # Scale result down by Q12*denom with proper rounding
                scale = Q12 * denom
                half = scale // 2
                def rdiv(num):
                    if num >= 0:
                        return (num + half) // scale
                    else:
                        return -((-num + half) // scale)
                b2 = RationalSurd(rdiv(b2.a), rdiv(b2.b))
                c2 = RationalSurd(rdiv(c2.a), rdiv(c2.b))
                d2 = RationalSurd(rdiv(d2.a), rdiv(d2.b))

                # Inverse permutation.
                out = (pA, b2, c2, d2)
                inv_sel = (-perm_sel) % 4
                self.qregs[d] = QuadrayVector(
                    *(out[inv_sel:] + out[:inv_sel])
                )
                # Thirds (/3) output breaks A₅ divisibility safety — the
                # DOUBLED→cleared harness transition (IROTC_SPEC.md §3).
                # Only angle 0 (identity) through this path preserves.
                self.qr_doubled[d] = (self.qr_doubled[s] if angle == 0
                                      else PHI_UNTAGGED)
                if self.verbose:
                    _angles_names = {
                        0: "0°id", 1: "60°D", 3: "180°D", 4: "240°D",
                        6: "240°@B", 7: "60°@B", 8: "180°@C",
                        9: "60°@C", 10: "240°@D", 11: "180°@D",
                        12: "180°@B", 13: "240°@C", 14: "60°@D",
                    }
                    name = _angles_names.get(angle, f"angle{angle}")
                    print(f"  [{self.pc:04d}] ROTC QR{d} ← QR{s} "
                          f"@{name} → {self.qregs[d]!r}")
            if self.proof:
                print(f"         Pell rotor (2+√3) applied to each IVM axis:")
                for i, (old_c, new_c) in enumerate(zip(prev.components(), self.qregs[n].components())):
                    a, b = old_c.a, old_c.b
                    na, nb = 2*a + 3*b, a + 2*b
                    print(f"         axis[{i}]: ({a}+{b}·√3) → ({na}+{nb}·√3)"
                          f"  Q={na*na-3*nb*nb}")

        # ------------------------------------------------------------------
        # Icosahedral A₅ φ-plane ops (IROTC_SPEC.md; opcodes 0xD6-0xD8)
        # QR registers overlay the φ-plane: components are Z[φ] pairs (a, b)
        # meaning a + b·φ, stored in the same RationalSurd (a, b) slots
        # (decided 2026-07-10 — same registers, tag-disciplined, so the
        # thirds-ROTC tag-clear and QADD linearity rules are enforceable).
        # ------------------------------------------------------------------
        elif opcode == OPCODES["LOAD2X"]:
            # LOAD2X QRd, A, B, C, D — QLDI immediate format, each component
            # loaded shifted left 1; DOUBLED tag set. The doubling is not
            # preprocessing: the catalog matrices are N = 2M, so φ-plane
            # data lives in doubled representation (IROTC_SPEC.md §3).
            a = (p1_a >> 8) & 0xFF
            b = p1_a & 0xFF
            c = (p1_b >> 8) & 0xFF
            dl = p1_b & 0xFF
            A = (a - 256 if a >= 128 else a) << 1
            B = (b - 256 if b >= 128 else b) << 1
            C = (c - 256 if c >= 128 else c) << 1
            D = (dl - 256 if dl >= 128 else dl) << 1
            d = r1 % 13
            self.qregs[d] = QuadrayVector(
                RationalSurd(A, 0), RationalSurd(B, 0),
                RationalSurd(C, 0), RationalSurd(D, 0),
            )
            self.qr_doubled[d] = PHI_FRESH
            if self.verbose:
                print(f"  [{self.pc:04d}] LOAD2X QR{d} ← ({A},{B},{C},{D}) [FRESH]")

        elif opcode == OPCODES["SCALE2"]:
            # SCALE2 QRd, QRs — QRd = QRs + QRs; DOUBLED tag set. Runtime
            # conditioning for φ-plane data that arrives undoubled (e.g.
            # via the southbridge). Componentwise add is plane-agnostic.
            d, s = r1 % 13, r2 % 13
            src = self.qregs[s]
            self.qregs[d] = src + src
            self.qr_doubled[d] = PHI_FRESH
            if self.verbose:
                print(f"  [{self.pc:04d}] SCALE2 QR{d} ← 2·QR{s} [FRESH]")

        elif opcode == OPCODES["IROTC"]:
            # IROTC QRd, QRs, sel — icosahedral A₅ rotation on (B,C,D) as
            # Z[φ] pairs; A recomputed from zero-sum. sel[5:0] = catalog
            # index (0-59), sel[6] = conjugate-catalog flag (Galois
            # φ → 1−φ, i.e. PCHIRAL ∘ R ∘ PCHIRAL — the dual icosahedron).
            # Exactly two guards, both at dispatch; no divisibility check
            # in the accumulate/shift path (IROTC_SPEC.md §4, §6).
            idx = p1_a & 0x3F
            conj = (p1_a >> 6) & 1
            d, s = r1 % 13, r2 % 13
            if idx > 59:
                raise IrotcBadIndexError(
                    f"IROTC index {idx} beyond the 60-entry A₅ catalog "
                    f"(IROTC_ERR_BADIDX); refusing rather than corrupting QR{d}"
                )
            if self.qr_doubled[s] == PHI_UNTAGGED:
                raise IrotcUntaggedError(
                    f"IROTC source QR{s} lacks the DOUBLED tag "
                    f"(IROTC_ERR_UNTAGGED); the unguarded >>1 is only "
                    f"licensed by the doubling theorem on doubled data"
                )
            want = PHI_CONJ if conj else PHI_MAIN
            if self.qr_doubled[s] not in (PHI_FRESH, want):
                raise IrotcCatalogMixError(
                    f"IROTC source QR{s} is locked to the "
                    f"{'main' if self.qr_doubled[s] == PHI_MAIN else 'conjugate'} "
                    f"catalog (IROTC_ERR_CATMIX); the doubling theorem does "
                    f"not compose across catalogs — SCALE2 to re-condition"
                )
            N = _irotc_catalog().IROTC_NUMS[idx]
            if conj:
                N = tuple((na + nb, -nb) for (na, nb) in N)
            src = self.qregs[s]
            w = ((src.b.a, src.b.b), (src.c.a, src.c.b), (src.d.a, src.d.b))
            out = []
            for i in range(3):
                ta = tb = 0
                for j in range(3):
                    na, nb = N[3 * i + j]
                    wa, wb = w[j]
                    # Z[φ] product: (na+nb·φ)(wa+wb·φ), φ² = φ+1
                    ta += na * wa + nb * wb
                    tb += na * wb + nb * wa + nb * wb
                # Doubling theorem: every pre-shift sum on tagged data is
                # even (machine-checked in test_icosahedral_catalog.py).
                # RTL shifts unguarded; this assert only documents the
                # licensed invariant and cannot fire on tagged inputs.
                assert (ta & 1) == 0 and (tb & 1) == 0, \
                    "doubling theorem violated — tag discipline bug"
                out.append((ta >> 1, tb >> 1))
            Bp = RationalSurd(out[0][0], out[0][1])
            Cp = RationalSurd(out[1][0], out[1][1])
            Dp = RationalSurd(out[2][0], out[2][1])
            Ap = RationalSurd(-(Bp.a + Cp.a + Dp.a), -(Bp.b + Cp.b + Dp.b))
            self.qregs[d] = QuadrayVector(Ap, Bp, Cp, Dp)
            # Doubling theorem licenses further rotations in THIS catalog
            # only — the output is catalog-locked, not FRESH.
            self.qr_doubled[d] = want
            if self.verbose:
                cat = "conj" if conj else "main"
                print(f"  [{self.pc:04d}] IROTC QR{d} ← QR{s} "
                      f"idx={idx} [{cat}] → {self.qregs[d]!r}")

        elif opcode == OPCODES["QNORM"]:
            # QNORM QRn — normalize to canonical IVM form (min component = 0)
            n = r1 % 13
            self.qregs[n] = self.qregs[n].normalize()
            self.qr_doubled[n] = PHI_UNTAGGED  # rs_min compare is Q(√3)-plane only
            if self.verbose:
                print(f"  [{self.pc:04d}] QNORM QR{n} → {self.qregs[n]!r}")

        elif opcode == OPCODES["QLOG"]:
            # QLOG QRn — log Quadray register state
            n = r1 % 13
            msg = self._qreg_str(n)
            self.log.append(msg)
            print(f"  [{self.pc:04d}] QLOG {msg}")

        # ------------------------------------------------------------------
        # Geometry output
        # ------------------------------------------------------------------
        elif opcode == OPCODES["SPREAD"]:
            # SPREAD Rd, QRa, QRb — compute spread; store numerator in Rd
            # Denominator stored in R(r1+1). Exact rational fraction.
            # Encoding: r2=QRa index, p1_b=QRb index
            qa, qb = r2 % 13, p1_b % 13
            numer, denom = self.qregs[qa].spread(self.qregs[qb])
            self.regs[r1] = numer
            self.regs[(r1 + 1) % NUM_REGS] = denom
            if self.verbose:
                print(f"  [{self.pc:04d}] SPREAD QR{qa}∧QR{qb} → {numer!r}/{denom!r}"
                      f"  (→ R{r1}/R{(r1+1)%NUM_REGS})")
            if self.proof:
                v = self.qregs[qa]
                w = self.qregs[qb]
                # dot product: sum of component-wise a-values (integer parts)
                dot = sum(v.components()[i].a * w.components()[i].a for i in range(4))
                v2  = sum(c.a * c.a for c in v.components())
                w2  = sum(c.a * c.a for c in w.components())
                print(f"         QR{qa} = ({', '.join(str(c.a) for c in v.components())})")
                print(f"         QR{qb} = ({', '.join(str(c.a) for c in w.components())})")
                dot_terms = '+'.join(f"{v.components()[i].a}·{w.components()[i].a}" for i in range(4))
                print(f"         dot    = {dot_terms} = {dot}")
                print(f"         |v|²   = {'+'.join(str(c.a*c.a) for c in v.components())} = {v2}")
                print(f"         |w|²   = {'+'.join(str(c.a*c.a) for c in w.components())} = {w2}")
                if v2 > 0 and w2 > 0:
                    n_val = v2 * w2 - dot * dot
                    d_val = v2 * w2
                    from math import gcd
                    g = gcd(abs(n_val), abs(d_val))
                    print(f"         spread = 1 - {dot}²/({v2}·{w2})"
                          f" = ({d_val}-{dot*dot})/{d_val}"
                          f" = {n_val//g}/{d_val//g}  ✓ exact rational")


        elif opcode == OPCODES["MIN4"]:
            # MIN4 QRd — normalize QRd by subtracting min(A,B,C,D)
            d = r1 % 13
            v = self.qregs[d]
            m = min(v.a.a, v.b.a, v.c.a, v.d.a)
            self.qregs[d] = QuadrayVector(
                RationalSurd(v.a.a - m, v.a.b),
                RationalSurd(v.b.a - m, v.b.b),
                RationalSurd(v.c.a - m, v.c.b),
                RationalSurd(v.d.a - m, v.d.b),
            )
            self.qr_doubled[d] = PHI_UNTAGGED  # Q(√3)-plane normalize
            if self.verbose:
                print(f"  [{self.pc:04d}] MIN4 QR{d}  min={m} → "
                      f"({v.a.a-m}, {v.b.a-m}, {v.c.a-m}, {v.d.a-m})")

        elif opcode == OPCODES["QREAD"]:
            # QREAD QRd, lane — read QR lane into another QR
            d = r1 % 13
            lane = r2 % 13
            self.qregs[d] = self.qregs[lane]
            self.qr_doubled[d] = self.qr_doubled[lane]  # bit-identical copy
            if self.verbose:
                print(f"  [{self.pc:04d}] QREAD QR{d} ← QR{lane}")

        elif opcode == OPCODES["HEX"]:
            # HEX Rd, QRn — project QRn to hex pixel (q,r); store q in Rd, r in R(d+1)
            n = r2 % 13
            hq, hr = self.qregs[n].hex_project()
            self.regs[r1]                   = RationalSurd(hq, 0)
            self.regs[(r1 + 1) % NUM_REGS]  = RationalSurd(hr, 0)
            if self.verbose:
                print(f"  [{self.pc:04d}] HEX  QR{n} → pixel ({hq:>4d}, {hr:>4d})"
                      f"  (→ R{r1}, R{(r1+1)%NUM_REGS})")

        # ------------------------------------------------------------------
        # v1.2 — Vector Equilibrium + Janus layer
        # ------------------------------------------------------------------
        elif opcode == OPCODES["EQUIL"]:
            # EQUIL — Vector Equilibrium check.
            # Sum all active QR hex projections: balanced manifold = (0,0) total.
            # This is the physically meaningful condition: all IVM tension forces cancel.
            active = [i for i in range(13) if not self.qregs[i].is_zero()]
            sum_hx = sum(self.qregs[i].hex_project()[0] for i in active)
            sum_hy = sum(self.qregs[i].hex_project()[1] for i in active)
            is_balanced = (sum_hx == 0 and sum_hy == 0)
            if is_balanced:
                if self.verbose:
                    print(f"  [{self.pc:04d}] EQUIL ✓ Vector Equilibrium — hex sum=(0,0)"
                          f"  ({len(active)} active axes)")
            else:
                self.snap_failures += 1
                print(f"  [{self.pc:04d}] EQUIL ✗ MANIFOLD TENSION"
                      f" — hex residual=({sum_hx},{sum_hy})"
                      f"  ({len(active)} active axes)")
            if self.proof and active:
                print(f"         Active QR axes: {active}")
                for i in active:
                    hx, hy = self.qregs[i].hex_project()
                    print(f"           QR{i}: {self.qregs[i]!r}  hex=({hx:+d},{hy:+d})")
                print(f"         Σ hex = ({sum_hx:+d},{sum_hy:+d})"
                      f"  VE condition → {'PASS' if is_balanced else 'FAIL'}")
            if self.proof and active:
                print(f"         Active QR axes: {active}")
                total = QuadrayVector()
                for i in active:
                    total = total + self.qregs[i]
                print(f"         Sum vector: {total!r}")
                print(f"         VE condition: Σ QR[i] = 0 → {'PASS' if is_balanced else 'FAIL'}")

        elif opcode == OPCODES["IDNT"]:
            # IDNT QRn — reset to canonical IVM unity [1,0,0,0]
            n = r1 % 13
            prev = self.qregs[n]
            self.qregs[n] = QuadrayVector(
                RationalSurd(1, 0), RationalSurd(0, 0),
                RationalSurd(0, 0), RationalSurd(0, 0),
            )
            self.qr_doubled[n] = PHI_UNTAGGED  # raw load clears DOUBLED
            if self.verbose:
                print(f"  [{self.pc:04d}] IDNT QR{n} → [1,0,0,0]  (was {prev!r})")
            if self.proof:
                print(f"         Identity reset: canonical IVM origin vector.")
                print(f"         In Quadray space (1,0,0,0) is the +A tetrahedral vertex.")

        elif opcode == OPCODES["JINV"]:
            # JINV Rn — Janus bit: negate surd component (single XOR in hardware)
            prev = self.regs[r1]
            self.regs[r1] = RationalSurd(prev.a, -prev.b)
            if self.verbose:
                print(f"  [{self.pc:04d}] JINV R{r1}: {prev!r} → {self.regs[r1]!r}")
            if self.proof:
                print(f"         Janus flip: b-component sign inverted.")
                print(f"         {prev.a} + {prev.b}·√3  →  {prev.a} + {-prev.b}·√3")
                print(f"         {self._q_proof(self.regs[r1])}")

        elif opcode == OPCODES["ANNE"]:
            # ANNE QRn — anneal one step toward Vector Equilibrium (halve each component)
            # Models the IVM lattice relaxation: each axis moves toward zero-tension state.
            n = r1 % 13
            prev = self.qregs[n]
            new_comps = [RationalSurd(c.a >> 1, c.b >> 1) for c in prev.components()]
            self.qregs[n] = QuadrayVector(*new_comps).normalize()
            self.qr_doubled[n] = PHI_UNTAGGED  # halving un-doubles
            if self.verbose:
                print(f"  [{self.pc:04d}] ANNE QR{n}: {prev!r} → {self.qregs[n]!r}")
            if self.proof:
                print(f"         Anneal step: each component >> 1 (halved toward VE zero-point).")
                for i, (old, new) in enumerate(zip(prev.components(), new_comps)):
                    print(f"         axis[{i}]: ({old.a},{old.b}) → ({old.a>>1},{old.b>>1})")

        elif opcode == OPCODES["SOM"]:
            # SOM_CLASSIFY QRs: classify QR[s] through 7-node hex BMU.
            # Layout: op=0x2A, r1=dest(ignored in RTL), r2=src QR lane.
            # Output: label → R[r1], ambiguous → R[r1+1].
            # Mirrors spu13_core.v SOM_CLASSIFY handler and spu_som_bmu.v.
            s = r2 % 13
            src = self.qregs[s]
            features = [src.a, src.b, src.c, src.d]  # [f0=A, f1=B, f2=C, f3=D]

            # 7-node fixture (mirrors spu_som_bmu.v lines 59-99)
            # Node weights stored as (f0_w_a, f0_w_b, f1_w_a, f1_w_b, ...)
            # where each weight is a RationalSurd(wa, wb)
            def _rs(a, b=0): return RationalSurd(a, b)
            NODES = [
                (0, 0, list(self._som_weights[0])),          # node 0: label 0
                (1, 1, list(self._som_weights[1])),          # node 1: label 1
                (2, 1, list(self._som_weights[2])),          # node 2: label 1
                (3, 2, list(self._som_weights[3])),          # node 3: label 2
                (4, 2, list(self._som_weights[4])),          # node 4: label 2
                (5, 3, list(self._som_weights[5])),          # node 5: label 3
                (6, 3, list(self._som_weights[6])),          # node 6: label 3
            ]
            # Unit feature weights (mirrors spu13_core.v line 1164) — all ones,
            # so the weighted quadrance simplifies to Σ (x_j - w_j)²

            # Integer-only Q(√3) ordering — mirrors spu_som_bmu.v cand_better
            def _cand_better(cand_q, cand_id, ref_q, ref_id, has_ref):
                if not has_ref:
                    return True
                da = cand_q.a - ref_q.a
                db = cand_q.b - ref_q.b
                if da == 0 and db == 0:
                    return cand_id < ref_id
                if da <= 0 and db <= 0:
                    return True
                if da >= 0 and db >= 0:
                    return False
                if da < 0 and db > 0:
                    return da*da > 3*db*db
                return da*da < 3*db*db

            have_best = False
            have_second = False
            best_id = -1
            second_id = -1
            best_label = 0
            best_a = best_b = 0
            second_a = second_b = 0

            for nid, label, w in NODES:
                # weighted_quadrance: Q = Σ r_j * (x_j - w_j)²
                # With unit feature weights (all 1), this simplifies to Σ (x_j - w_j)²
                q_a = 0; q_b = 0
                for j in range(4):
                    delta_a = features[j].a - w[j].a
                    delta_b = features[j].b - w[j].b
                    # delta² = (da + db√3)² = (da²+3db²) + (2·da·db)√3
                    q_a += delta_a*delta_a + 3*delta_b*delta_b
                    q_b += 2*delta_a*delta_b

                cand_q = RationalSurd(q_a, q_b)
                if _cand_better(cand_q, nid,
                                RationalSurd(best_a, best_b), best_id, have_best):
                    if have_best:
                        second_id = best_id
                        second_a, second_b = best_a, best_b
                        have_second = True
                    best_id = nid
                    best_a, best_b = q_a, q_b
                    best_label = label
                    have_best = True
                elif _cand_better(cand_q, nid,
                                  RationalSurd(second_a, second_b),
                                  second_id, have_second):
                    second_id = nid
                    second_a, second_b = q_a, q_b
                    have_second = True

            if not have_best:
                label_out = 0xFFFF
                ambiguous = 1
            else:
                label_out = best_label
                gap_a = second_a - best_a if have_second else 0
                gap_b = second_b - best_b if have_second else 0
                ambiguous = 1 if (have_second and gap_a == 0 and gap_b == 0) else 0

            # Record BMU for SOM_TRAIN
            self._som_best_id = best_id
            self._som_last_features = features

            self.regs[r1] = RationalSurd(label_out, 0)
            self.regs[(r1 + 1) % NUM_REGS] = RationalSurd(ambiguous, 0)

            # ── Axiomatic Gatekeeper (mirrors spu13_axiomatic_gatekeeper.v) ──
            # axiomatic_level from phinary_cfg[3:2]: 00=RCA₀ 01=WKL₀ 10=ACA₀ 11=OFF
            axiomatic_level = (self.phinary_cfg >> 2) & 0x3
            if axiomatic_level != 3 and have_best:
                # Overflow check: coefficients exceed 24-bit signed range
                # (matches RTL accum_overflow)
                MAX_VAL = (1 << 23) - 1
                is_overflow = (abs(best_a) > MAX_VAL) or (abs(best_b) > MAX_VAL)
                # Fractional check: reserved for fixed-point mode (SHIFT > 0).
                # In pure integer arithmetic, small values like Q=1 have low
                # bits set legitimately — not fractional leakage.
                is_fractional = False  # reserved

                if axiomatic_level == 0:  # RCA₀: trap overflow
                    fault_kind = "OVERFLOW" if is_overflow else None
                elif axiomatic_level == 1:  # WKL₀: trap overflow
                    fault_kind = "OVERFLOW" if is_overflow else None
                else:  # ACA₀: no traps
                    fault_kind = None

                if fault_kind and self.verbose:
                    print(f"         ⚠  GATEKEEPER FAULT [{['RCA₀','WKL₀','ACA₀'][axiomatic_level]}]: "
                          f"{fault_kind}  Q=({best_a}+{best_b}√3)")

            if self.verbose:
                qs = f"Q={best_a}+{best_b}√3" if have_best else "N/A"
                amb = "AMBIGUOUS" if ambiguous else "clear"
                print(f"  [{self.pc:04d}] SOM  QR{s} → label={label_out} {amb}  ({qs})")

        elif opcode == OPCODES["SOM_TRAIN"]:
            # SOM_TRAIN shift — dyadic weight update after BMU classification.
            # shift_amount from p1_a[3:0].
            # Updates the BMU found by the most recent SOM_CLASSIFY.
            shift = p1_a & 0xF
            if not hasattr(self, '_som_best_id') or self._som_best_id < 0:
                if self.verbose:
                    print(f"  [{self.pc:04d}] SOM_TRAIN: no valid BMU to update")
            else:
                nid = self._som_best_id
                # Get features from last SOM classification
                src = self._som_last_features
                # Current weights from writable memory
                old_w = list(self._som_weights[nid])
                # Dyadic update
                new_w = []
                for j in range(4):
                    delta = src[j] - old_w[j]
                    update = RationalSurd(delta.a >> shift, delta.b >> shift)
                    new_w.append(old_w[j] + update)
                self._som_weights[nid] = tuple(new_w)
                if self.verbose:
                    print(f"  [{self.pc:04d}] SOM_TRAIN node={nid} shift={shift}: "
                          f"w=({old_w[0].a},{old_w[1].a},{old_w[2].a},{old_w[3].a}) "
                          f"→ ({new_w[0].a},{new_w[1].a},{new_w[2].a},{new_w[3].a})")

        elif opcode == OPCODES["NOP"]:
            if self.verbose:
                print(f"  [{self.pc:04d}] NOP")

        elif opcode == OPCODES.get("PHCFG"):
            # Set phinary configuration register (16-bit)
            cfg = p1_a & 0xFFFF
            self.phinary_cfg = cfg
            if self.verbose:
                en = bool(cfg & 0x1)
                chir = bool(cfg & 0x2)
                thr = (cfg >> 2)
                print(f"  [{self.pc:04d}] PHCFG ← 0x{cfg:04X}  enable={en} chirality={chir} thr={thr}")

        elif opcode == OPCODES.get("PHADD"):
            if phinary_helpers is None:
                raise RuntimeError("PHADD requested but phinary_vm_helpers not available")
            # default width/int_bits for packed phinary (can be adjusted)
            _w = 16
            _ib = 8
            # determine laminar_thr and chirality from phinary_cfg
            _chir = bool(self.phinary_cfg & 0x2)
            _thr = (self.phinary_cfg >> 2) & 0xFFFF
            # pack: surd <- b, integer <- a
            _a_packed = phinary_helpers.pack_phinary(self.regs[r1].b & ((1 << (_w - _ib)) - 1), self.regs[r1].a & ((1 << _ib) - 1), width=_w, int_bits=_ib)
            _b_packed = phinary_helpers.pack_phinary(self.regs[r2].b & ((1 << (_w - _ib)) - 1), self.regs[r2].a & ((1 << _ib) - 1), width=_w, int_bits=_ib)
            out_packed, void_out, ovf = phinary_helpers.add_phinary(_a_packed, _b_packed, width=_w, int_bits=_ib, laminar_thr=_thr if _thr != 0 else None, chirality=_chir, void_state=self.phinary_void_state)
            out_surd, out_int = phinary_helpers.unpack_phinary(out_packed, width=_w, int_bits=_ib)
            # interpret fields as signed two's-complement
            if out_int & (1 << (_ib - 1)):
                out_int = out_int - (1 << _ib)
            if out_surd & (1 << ((_w - _ib) - 1)):
                out_surd = out_surd - (1 << (_w - _ib))
            self.regs[r1] = RationalSurd(out_int, out_surd)
            self.phinary_void_state = void_out
            if self.verbose:
                print(f"  [{self.pc:04d}] PHADD R{r1} + R{r2} → packed=0x{out_packed:04X} => {self.regs[r1]!r} void={void_out} ovf={ovf}")

        elif opcode == OPCODES.get("POLY_STEP"):
            # POLY_STEP Rbase, Rx — evaluate Padé P(x) and Q(x) (4/4 Q32) in VM
            # Encoding: r1 = destination base register (numer→R[r1], denom→R[r1+1])
            #           r2 = source register holding x as signed integer in .a (Q32 fixed)
            #           p1_a selects coefficient set (0 = default)
            coef_sel = p1_a & 0xFFFF
            # Load coefficient ROMs (cached per coef_sel)
            if not hasattr(self, '_pade_cache'):
                self._pade_cache = {}
            if coef_sel not in self._pade_cache:
                num_path = 'hardware/common/rtl/gpu/pade_num_4_4_q32.mem'
                den_path = 'hardware/common/rtl/gpu/pade_den_4_4_q32.mem'
                def read_mem_signed(path):
                    vals = [0]*5
                    try:
                        with open(path, 'r') as f:
                            lines = [l.strip() for l in f if l.strip()]
                            for i, l in enumerate(lines[:5]):
                                v = int(l, 16)
                                if v & (1 << 63):
                                    v = v - (1 << 64)
                                vals[i] = v
                    except Exception:
                        # missing mems: fall back to zeros
                        vals = [0,0,0,0,0]
                    return vals
                num_arr = read_mem_signed(num_path)
                den_arr = read_mem_signed(den_path)
                self._pade_cache[coef_sel] = (num_arr, den_arr)
            else:
                num_arr, den_arr = self._pade_cache[coef_sel]

            # Extract x from source register (expect signed integer in .a field representing Q32)
            x_reg = self.regs[r2]
            x_q32 = int(x_reg.a)

            # Helper: truncate to signed 'bits' (two's complement)
            def to_signed(val, bits):
                mask = (1 << bits) - 1
                v = val & mask
                if v & (1 << (bits - 1)):
                    v = v - (1 << bits)
                return v

            # Horner evaluation matching hardware (acc widths/truncation)
            def horner_q32(coeffs, x):
                acc = coeffs[4]
                acc = to_signed(acc, 128)
                for i in (3,2,1,0):
                    prod = acc * x
                    shifted = prod >> 32
                    acc = shifted + coeffs[i]
                    acc = to_signed(acc, 128)
                return acc

            accn = horner_q32(num_arr, x_q32)
            accd = horner_q32(den_arr, x_q32)

            # Store results as RationalSurd(rational, 0) to match SPREAD/VM conventions
            self.regs[r1] = RationalSurd(int(accn), 0)
            self.regs[(r1 + 1) % NUM_REGS] = RationalSurd(int(accd), 0)
            if self.verbose:
                print(f"  [{self.pc:04d}] POLY_STEP R{r1}, Rx{r2} -> num={accn} den={accd}")

        elif opcode == OPCODES.get("RATIO_CMP"):
            # RATIO_CMP Rbase, Rcompare — compare P/Q at Rbase..Rbase+1 with P'/Q' at Rcompare..Rcompare+1
            p1 = self.regs[r1]
            q1 = self.regs[(r1 + 1) % NUM_REGS]
            p2 = self.regs[r2]
            q2 = self.regs[(r2 + 1) % NUM_REGS]
            # Cross-multiply: compare p1*q2 ? p2*q1 in Q(√3)
            left = p1 * q2
            right = p2 * q1
            if left == right:
                cmp_res = 0
            elif rs_lt(left, right):
                cmp_res = -1
            else:
                cmp_res = 1
            # Store integer comparison result into R[r1] as a RationalSurd (overwrite numerator)
            self.regs[r1] = RationalSurd(cmp_res, 0)
            if self.verbose:
                cmp_str = '<' if cmp_res == -1 else ('=' if cmp_res == 0 else '>')
                print(f"  [{self.pc:04d}] RATIO_CMP R{r1}, R{r2} -> p1/q1 {cmp_str} p2/q2 (res={cmp_res})")
        else:
            print(f"  [{self.pc:04d}] ??? unknown opcode 0x{opcode:02X} — NOP")

        self.pc = next_pc
        self.step_count += 1

        # ── Fibonacci dispatch tick ───────────────────────────────────────
        gate = self.fib.tick()
        if gate and self.verbose:
            print(f"  [{self.pc:04d}] ··· {gate} gate  (cycle={self.fib.cycle}  τ={self.gasket.tau!r})")

        # ── Davis Gasket periodic check ───────────────────────────────────
        # Run at every phi gate; attempt Henosis recovery at phi_13/phi_21
        if gate:
            had_leak = self.gasket.gasket_tick(self.qregs)
            if had_leak:
                if self.verbose:
                    print(f"  [{self.pc:04d}] ⚠  Davis Gate: CUBIC LEAK  {self.gasket!r}")
                # Attempt Henosis recovery on meso/macro gates
                if gate.startswith('φ₁₃') or gate.startswith('φ₂₁'):
                    pulses = self.gasket.henosis_recover(self.qregs, max_pulses=3)
                    if pulses:
                        # Henosis halves every QR component in place — any
                        # doubled φ-plane data is un-doubled by the pulse.
                        self.qr_doubled = [PHI_UNTAGGED] * 13
                    if pulses and self.verbose:
                        print(f"  [{self.pc:04d}] ✦  Henosis: {pulses} pulse(s) applied"
                              f"  τ→{self.gasket.tau!r}")
            elif self.verbose:
                print(f"  [{self.pc:04d}] ✓  Davis Gate: laminar  {self.gasket!r}")

            if self.gasket_trace:
                self._gasket_trace_line(gate)

        if self.step_count >= self.max_steps:
            if self.verbose:
                print(f"\n  SPU-VM: max_steps ({self.max_steps}) reached. Halting.")
            self.halted = True
            return False

        return not self.halted

    def run(self):
        while self.step():
            pass

    def dump_registers(self):
        print("\n  ── Scalar Registers ───────────────────────────────────────")
        any_scalar = False
        for i in range(NUM_REGS):
            r = self.regs[i]
            if r.a != 0 or r.b != 0:
                print(f"  {self._reg_str(i)}")
                any_scalar = True
        if not any_scalar:
            print("  (all zero)")

        print("\n  ── Quadray Registers (IVM Axes) ───────────────────────────")
        any_quad = False
        for i in range(13):
            if not self.qregs[i].is_zero():
                print(f"  {self._qreg_str(i)}")
                any_quad = True
        if not any_quad:
            print("  (all zero)")

        print(f"\n  ── PC={self.pc}  steps={self.step_count}"
              f"  snap_failures={self.snap_failures}"
              f"  call_depth={len(self.call_stack)}")
        print(f"  ── Davis Gasket: {self.gasket!r}")
        print(f"  ── Fib Dispatch: {self.fib!r}")
        print(f"  ── SDF Layer 7:  {self.sdf!r}")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SPU-13 Sovereign VM — Q(√3) interpreter"
    )
    parser.add_argument('source', nargs='?', help='.sas source or .bin file')
    parser.add_argument('--bin', metavar='FILE', help='Load pre-assembled .bin directly')
    parser.add_argument('--steps', type=int, default=256, help='Max execution steps (default: 256)')
    parser.add_argument('--quiet', action='store_true', help='Suppress per-instruction trace')
    parser.add_argument('--proof', action='store_true',
                        help='Show step-by-step Q(√3) arithmetic derivations (sceptic mode)')
    parser.add_argument('--sdf-trace', action='store_true',
                        help='Show SDF nearest-axis and snap-conflict state at every SNAP')
    parser.add_argument('--gasket-trace', action='store_true',
                        help='Show Davis Ratio table row at every Fibonacci gate boundary')
    args = parser.parse_args()

    source_file = args.bin or args.source
    if not source_file:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(source_file):
        print(f"Error: file not found: {source_file}")
        sys.exit(1)

    verbose      = not args.quiet
    proof        = args.proof
    sdf_trace    = args.sdf_trace
    gasket_trace = args.gasket_trace
    core = SPUCore(max_steps=args.steps, verbose=verbose, proof=proof,
                   sdf_trace=sdf_trace, gasket_trace=gasket_trace)

    if source_file.endswith('.bin') or args.bin:
        with open(source_file, 'rb') as f:
            data = f.read()
        words = [int.from_bytes(data[i:i+8], 'big') for i in range(0, len(data), 8)]
        print(f"\n  SPU-13 Sovereign VM  |  {source_file}  |  binary")
    else:
        with open(source_file, 'r') as f:
            source = f.read()
        words = assemble_source(source)
        if not words:
            print("Error: no instructions assembled.")
            sys.exit(1)
        print(f"\n  SPU-13 Sovereign VM  |  {source_file}  |  {len(words)} words")

    print("  ──────────────────────────────────────────────────────────")
    core.load(words)
    core.run()
    core.dump_registers()

    if core.snap_failures:
        print(f"  ⚠  {core.snap_failures} SNAP failure(s) — cubic leak detected")
        sys.exit(2)
    else:
        print("  ✓  Execution complete — manifold laminar")


if __name__ == '__main__':
    main()
