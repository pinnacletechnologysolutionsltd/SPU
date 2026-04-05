#!/usr/bin/env python3
"""
SPU-13 Sovereign Virtual Machine (spu_vm.py) — v1.3
Pure Python interpreter for the Sovereign Assembly (SAS) ISA.

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

Usage:
    python3 spu_vm.py programs/jitterbug.sas
    python3 spu_vm.py programs/equilibrium_test.sas --proof
    python3 spu_vm.py --bin programs/jitterbug.bin
"""

import sys
import os
import struct
import argparse

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
    """
    __slots__ = ('a', 'b', 'pell_step')

    def __init__(self, a: int = 0, b: int = 0, pell_step: int = None):
        self.a = int(a)
        self.b = int(b)
        self.pell_step = pell_step  # None = not a rotor-generated surd

    def __add__(self, other: 'RationalSurd') -> 'RationalSurd':
        return RationalSurd(self.a + other.a, self.b + other.b)

    def __sub__(self, other: 'RationalSurd') -> 'RationalSurd':
        return RationalSurd(self.a - other.a, self.b - other.b)

    def __mul__(self, other: 'RationalSurd') -> 'RationalSurd':
        # (a + b√3)(c + d√3) = (ac + 3bd) + (ad + bc)√3
        return RationalSurd(
            self.a * other.a + 3 * self.b * other.b,
            self.a * other.b + self.b * other.a
        )

    def __neg__(self) -> 'RationalSurd':
        return RationalSurd(-self.a, -self.b)

    def __eq__(self, other) -> bool:
        return self.a == other.a and self.b == other.b

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
        """
        # Fundamental orbit (steps 0–7) — all fit in int16
        _PELL_ORBIT = [
            (1, 0), (2, 1), (7, 4), (26, 15),
            (97, 56), (362, 209), (1351, 780), (5042, 2911),
        ]
        if self.pell_step is not None:
            new_step = self.pell_step + 1
            oct_n, step_n = divmod(new_step, 8)
            a, b = _PELL_ORBIT[step_n]
            return RationalSurd(a, b, pell_step=new_step)
        # Fallback for surds not started from unity — full field multiply
        result = self * RationalSurd(2, 1)
        return RationalSurd(result.a, result.b, pell_step=None)

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
    "MUL":   0x03, "ROT":   0x04, "LOG":   0x05,
    # Control flow
    "JMP":   0x06, "SNAP":  0x07, "COND":  0x20,
    "CALL":  0x21, "RET":   0x22,
    # Quadray IVM operations
    "QADD":  0x10, "QROT":  0x11, "QNORM": 0x12,
    "QLOAD": 0x13, "QLOG":  0x14,
    # Geometry output
    "SPREAD":0x15, "HEX":   0x16,
    # v1.2 — Vector Equilibrium + Janus layer
    "EQUIL": 0x17, "IDNT":  0x18, "JINV":  0x19, "ANNE":  0x1A,
    # No-op
    "NOP":   0xFF,
}
OPNAMES = {v: k for k, v in OPCODES.items()}

def _parse_int16(s: str) -> int:
    v = int(s)
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

    def parse_arg(arg: str, is_first: bool) -> tuple[int, int, int]:
        """Returns (r1_val, r2_val, p1_a_val) for a single argument."""
        arg = arg.upper()
        if arg.startswith('QR'):          # Quadray register: QR0-QR12
            idx = int(arg[2:]) & 0xFF
            return (idx, 0, 0) if is_first else (0, idx, 0)
        if arg.startswith('R'):           # Scalar register: R0-R25
            idx = int(arg[1:]) & 0xFF
            return (idx, 0, 0) if is_first else (0, idx, 0)
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
        # Third operand goes into p1_b (e.g. SPREAD R1, QR0, QR1 — QR1 index)
        # Or p1_a for integer immediate (e.g. LD R0, 2, 1 — b component)
        arg = parts[3].upper()
        if arg.startswith('QR'):
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
        On leak: τ += quadrance of vector sum.
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
            # τ accumulates: add quadrance of (sa+sb+sc+sd) combined
            # Simplified: add p² of each axis sum component (no cross terms)
            tau_add_p = sa.a*sa.a + sb.a*sb.a + sc.a*sc.a + sd.a*sd.a
            self.tau  = RationalSurd(self.tau.a + tau_add_p, self.tau.b)
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
# SPU Core — the interpreter
# ---------------------------------------------------------------------------

NUM_REGS = 26  # R0–R25 (one per axis + spares)

class SPUCore:
    """
    Software model of the SPU-13 Sovereign Core.
    Executes 64-bit SAS control words in Q(√3).

    Register file:
      R0–R25  : 26 scalar RationalSurd registers
      QR0–QR12: 13 QuadrayVector registers (one per SPU-13 manifold axis)
    """

    def __init__(self, max_steps: int = 10_000, verbose: bool = True, proof: bool = False):
        self.regs: list[RationalSurd] = [RationalSurd(0, 0) for _ in range(NUM_REGS)]
        self.qregs: list[QuadrayVector] = [QuadrayVector() for _ in range(13)]
        self.call_stack: list[int] = []
        self.pc: int = 0
        self.program: list[int] = []
        self.step_count: int = 0
        self.max_steps: int = max_steps
        self.verbose: bool = verbose
        self.proof: bool = proof   # show step-by-step Q(√3) arithmetic derivations
        self.halted: bool = False
        self.snap_failures: int = 0
        self.log: list[str] = []
        # v1.3 additions — Davis Gasket + Fibonacci dispatch
        self.gasket   = DavisGasket()
        self.fib      = FibDispatch()

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
        if self.verbose:
            print(f"  SPU-VM: {len(words)} words loaded.")

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
            if self.verbose:
                print(f"  [{self.pc:04d}] QLOAD QR{r1} ← R{base}..R{base+3} = {qr!r}")

        elif opcode == OPCODES["QADD"]:
            # QADD QRd, QRs — QRd = QRd + QRs
            d, s = r1 % 13, r2 % 13
            self.qregs[d] = self.qregs[d] + self.qregs[s]
            if self.verbose:
                print(f"  [{self.pc:04d}] QADD QR{d} + QR{s} → {self.qregs[d]!r}")

        elif opcode == OPCODES["QROT"]:
            # QROT QRn — apply Pell rotor to each component + normalize
            n = r1 % 13
            prev = self.qregs[n]
            self.qregs[n] = prev.rotate()
            if self.verbose:
                hx, hy = self.qregs[n].hex_project()
                print(f"  [{self.pc:04d}] QROT QR{n} → {self.qregs[n]!r}  hex=({hx},{hy})")
            if self.proof:
                print(f"         Pell rotor (2+√3) applied to each IVM axis:")
                for i, (old_c, new_c) in enumerate(zip(prev.components(), self.qregs[n].components())):
                    a, b = old_c.a, old_c.b
                    na, nb = 2*a + 3*b, a + 2*b
                    print(f"         axis[{i}]: ({a}+{b}·√3) → ({na}+{nb}·√3)"
                          f"  Q={na*na-3*nb*nb}")

        elif opcode == OPCODES["QNORM"]:
            # QNORM QRn — normalize to canonical IVM form (min component = 0)
            n = r1 % 13
            self.qregs[n] = self.qregs[n].normalize()
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
            if self.verbose:
                print(f"  [{self.pc:04d}] ANNE QR{n}: {prev!r} → {self.qregs[n]!r}")
            if self.proof:
                print(f"         Anneal step: each component >> 1 (halved toward VE zero-point).")
                for i, (old, new) in enumerate(zip(prev.components(), new_comps)):
                    print(f"         axis[{i}]: ({old.a},{old.b}) → ({old.a>>1},{old.b>>1})")

        elif opcode == OPCODES["NOP"]:
            if self.verbose:
                print(f"  [{self.pc:04d}] NOP")

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
                    if pulses and self.verbose:
                        print(f"  [{self.pc:04d}] ✦  Henosis: {pulses} pulse(s) applied"
                              f"  τ→{self.gasket.tau!r}")
            elif self.verbose:
                print(f"  [{self.pc:04d}] ✓  Davis Gate: laminar  {self.gasket!r}")

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
    args = parser.parse_args()

    source_file = args.bin or args.source
    if not source_file:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(source_file):
        print(f"Error: file not found: {source_file}")
        sys.exit(1)

    verbose = not args.quiet
    proof   = args.proof
    core = SPUCore(max_steps=args.steps, verbose=verbose, proof=proof)

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
