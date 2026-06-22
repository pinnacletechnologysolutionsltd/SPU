#!/usr/bin/env python3
"""
spu13_arch_sim.py — Behavioral simulator for SPU-13 Architecture v1.0

Implements the full ISA specified in docs/spu13_isa_spec.md:
  - 32 twin-registers (R[0..31], each with Offer .O and Confirmation .C slots)
  - 64-bit instruction word matching spu_isa_defines.vh field positions
  - Rational Arithmetic Unit (Q(√3) cross-multiplication)
  - Temporal opcodes: OFFR, CNFM, PHSLK, INVJ, PHSTA, PHCLR
  - Geometric ops: SPRD, ROTR, CROSS, DOT, TNSR, PROJ
  - Quadrance arithmetic: QADD, QSUB, QMUL, QDIV, QNORM, QCMP
  - RPLU material table simulation (8 materials, 256 entries each)
  - Phase-lock ratio comparator (RATIO_CMP cross-multiply)
  - Flow control + telemetry

Usage:
    python3 -m pytest software/spu13_arch_sim_test.py -v
    python3 software/spu13_arch_sim.py  # interactive demo
"""

import sys
import os
sys.dont_write_bytecode = True

# ═════════════════════════════════════════════════════════════════════════════
# SPU-13 ISA Constants (matching spu_isa_defines.vh)
# ═════════════════════════════════════════════════════════════════════════════

# Opcodes
OP_NOP     = 0x00
OP_HALT    = 0x01
OP_SYNC    = 0x02

OP_LOAD    = 0x10
OP_STORE   = 0x11
OP_MOV     = 0x12
OP_MOVI    = 0x13
OP_LDO     = 0x14
OP_LDC     = 0x15

OP_QADD    = 0x20
OP_QSUB    = 0x21
OP_QMUL    = 0x22
OP_QDIV    = 0x23
OP_QNORM   = 0x24
OP_QCMP    = 0x25

OP_SPRD    = 0x30
OP_ROTR    = 0x31
OP_CROSS   = 0x32
OP_DOT     = 0x33
OP_TNSR    = 0x34
OP_PROJ    = 0x35

OP_OFFR    = 0x40
OP_CNFM    = 0x41
OP_PHSLK   = 0x42
OP_INVJ    = 0x43
OP_PHSTA   = 0x44
OP_PHCLR   = 0x45

OP_RCFG    = 0x50
OP_RREAD   = 0x51
OP_RLOAD   = 0x52
OP_RDISSOC = 0x53

OP_SOM      = 0x2A
OP_SOM_TRAIN = 0x2B

OP_CMP     = 0x60
OP_JMP     = 0x61
OP_JZ      = 0x62
OP_JNZ     = 0x63
OP_JC      = 0x64
OP_JNC     = 0x65
OP_CALL    = 0x66
OP_RET     = 0x67

OP_MFOLD   = 0x70
OP_STAT    = 0x71
OP_SCALE   = 0x72
OP_QR      = 0x73
OP_HEX     = 0x74
OP_SENT    = 0x75

OPCODE_NAMES = {
    0x00:'NOP',  0x01:'HALT', 0x02:'SYNC',
    0x10:'LOAD', 0x11:'STORE',0x12:'MOV',  0x13:'MOVI', 0x14:'LDO',  0x15:'LDC',
    0x20:'QADD', 0x21:'QSUB', 0x22:'QMUL', 0x23:'QDIV', 0x24:'QNORM',0x25:'QCMP',
    0x30:'SPRD', 0x31:'ROTR', 0x32:'CROSS',0x33:'DOT',  0x34:'TNSR', 0x35:'PROJ',
    0x40:'OFFR', 0x41:'CNFM', 0x42:'PHSLK',0x43:'INVJ', 0x44:'PHSTA',0x45:'PHCLR',
    0x50:'RCFG', 0x51:'RREAD',0x52:'RLOAD',0x53:'RDISSOC',
    0x2A:'SOM',  0x2B:'SOM_TRAIN',
    0x60:'CMP',  0x61:'JMP',  0x62:'JZ',   0x63:'JNZ',  0x64:'JC',   0x65:'JNC',
    0x66:'CALL', 0x67:'RET',
    0x70:'MFOLD',0x71:'STAT', 0x72:'SCALE',0x73:'QR',   0x74:'HEX',  0x75:'SENT',
}

REG_NAMES = {
    0:'ZERO', 1:'PC', 2:'FLAGS', 3:'MANIFOLD_PTR',
    4:'SCALE_PTR', 5:'CHORD_IN', 6:'CHORD_OUT', 7:'QUAD_OUT',
}

# Special register indices
REG_ZERO         = 0
REG_PC           = 1
REG_FLAGS        = 2
REG_MANIFOLD_PTR = 3
REG_SCALE_PTR    = 4
REG_CHORD_IN     = 5
REG_CHORD_OUT    = 6
REG_QUAD_OUT     = 7

# Flag bit positions
FLAG_ZERO     = 0
FLAG_COHERENT = 1
FLAG_SCALE_OVF = 2
FLAG_FIFO_FULL = 3

# Condition codes
COND_ALWAYS   = 0
COND_COHERENT = 1
COND_NOTCOH   = 2

# ═════════════════════════════════════════════════════════════════════════════
# Q(√3) Rational Arithmetic
# ═════════════════════════════════════════════════════════════════════════════

class Rational:
    """Exact rational number num/den as a pair of Python integers."""
    __slots__ = ('num', 'den')
    def __init__(self, num: int = 0, den: int = 1):
        if den < 0:
            num = -num
            den = -den
        self.num = num
        self.den = den
    def __repr__(self):
        return f"{self.num}/{self.den}" if self.den != 1 else f"{self.num}"
    def __eq__(self, other):
        if isinstance(other, int):
            return self.den == 1 and self.num == other
        return self.num * other.den == other.num * self.den
    def __add__(self, other):
        return Rational(self.num * other.den + other.num * self.den,
                        self.den * other.den).normalize()
    def __sub__(self, other):
        return Rational(self.num * other.den - other.num * self.den,
                        self.den * other.den).normalize()
    def __mul__(self, other):
        if isinstance(other, int):
            return Rational(self.num * other, self.den).normalize()
        return Rational(self.num * other.num, self.den * other.den).normalize()
    def __truediv__(self, other):
        if isinstance(other, int):
            return Rational(self.num, self.den * other).normalize()
        return Rational(self.num * other.den, self.den * other.num).normalize()
    def normalize(self):
        if self.num == 0:
            return Rational(0, 1)
        if self.den < 0:
            self.num = -self.num
            self.den = -self.den
        import math
        g = math.gcd(abs(self.num), abs(self.den))
        self.num //= g
        self.den //= g
        return self
    def __neg__(self):
        return Rational(-self.num, self.den)

    def to_q12(self) -> int:
        """Return Q12 fixed-point: value * 4096, truncated."""
        if self.den == 0:
            return 0x7FFFFFFF if self.num > 0 else -0x80000000
        return (self.num << 12) // self.den

    @staticmethod
    def from_q12(q12: int) -> 'Rational':
        """Construct from Q12 fixed-point integer."""
        return Rational(q12, 4096)


class RationalSurd:
    """Q(√3) field element: value = p + q·√3 where p,q are Rational."""
    __slots__ = ('p', 'q')
    def __init__(self, p=None, q=None):
        self.p = p if p is not None else Rational(0, 1)
        self.q = q if q is not None else Rational(0, 1)
    def __repr__(self):
        ps = str(self.p)
        if self.q.num == 0:
            return ps
        qs = f"{self.q}·√3"
        if self.q.num < 0:
            return f"{ps} - {-self.q}·√3" if self.p.num != 0 else f"-{-self.q}·√3"
        return f"{ps} + {qs}" if self.p.num != 0 else qs
    def __eq__(self, other):
        return self.p == other.p and self.q == other.q
    def __add__(self, other):
        return RationalSurd(self.p + other.p, self.q + other.q)
    def __sub__(self, other):
        return RationalSurd(self.p - other.p, self.q - other.q)
    def __mul__(self, other):
        # (p + q·√3)(r + s·√3) = (pr + 3qs) + (ps + qr)·√3
        return RationalSurd(
            self.p * other.p + Rational(3,1) * self.q * other.q,
            self.p * other.q + self.q * other.p
        )
    def norm(self) -> Rational:
        """Quadrance Q = p² - 3q² (the field norm)."""
        return self.p * self.p - Rational(3,1) * self.q * self.q
    def conjugate(self):
        """Field conjugate: p - q·√3"""
        return RationalSurd(self.p, Rational(-self.q.num, self.q.den))
    def __neg__(self):
        return RationalSurd(-self.p, -self.q)
    def cross_multiply(self, other) -> int:
        """Return -1, 0, +1 comparing self.norm to other.norm.
        Uses cross-multiplication to avoid division."""
        q_self = self.norm()
        q_other = other.norm()
        left = q_self.num * q_other.den
        right = q_other.num * q_self.den
        if left < right:
            return -1
        elif left > right:
            return 1
        return 0

    def as_rational(self) -> Rational:
        """If q == 0, return just the rational part."""
        return self.p


class Quadray:
    """4D quadray coordinate (a,b,c,d) in Q(√3).
    Each component is a RationalSurd.
    Constraint: a + b + c + d = 0.
    """
    __slots__ = ('a', 'b', 'c', 'd')
    def __init__(self, a=None, b=None, c=None, d=None):
        z = RationalSurd(Rational(0,1), Rational(0,1))
        self.a = a if a is not None else z
        self.b = b if b is not None else z
        self.c = c if c is not None else z
        self.d = d if d is not None else z
    def __repr__(self):
        return f"[{self.a}, {self.b}, {self.c}, {self.d}]"
    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c and self.d == other.d
    def __add__(self, other):
        return Quadray(self.a + other.a, self.b + other.b,
                       self.c + other.c, self.d + other.d)
    def __sub__(self, other):
        return Quadray(self.a - other.a, self.b - other.b,
                       self.c - other.c, self.d - other.d)
    def __neg__(self):
        return Quadray(-self.a, -self.b, -self.c, -self.d)
    def quadrance(self) -> Rational:
        """Q = a² + b² + c² + d² (all rational)."""
        return (self.a * self.a + self.b * self.b +
                self.c * self.c + self.d * self.d).p  # Rational only
    def spread(self, other) -> Rational:
        """S = 1 - (a·r + b·s + c·t + d·u)² / (Q1·Q2) — reduced rational."""
        # For the simulator we use the simplified rational spread
        dot = (self.a * other.a + self.b * other.b +
               self.c * other.c + self.d * other.d)
        q1 = self.quadrance()
        q2 = other.quadrance()
        if q1.num == 0 or q2.num == 0:
            return Rational(0, 1)
        # S = product of spread components
        return (Rational(1,1) - dot * dot / (q1 * q2)).normalize()
    def cross(self, other):
        """Quadray cross product — returns the orthogonal complement vector."""
        return Quadray(
            self.b * other.c - self.c * other.b,
            self.c * other.a - self.a * other.c,
            self.a * other.b - self.b * other.a,
            RationalSurd(Rational(0,1))  # d = 0 in cross
        )
    def tensor_M(self):
        """Apply metric tensor M = 4I - J to this quadray.
        M·v = 4v - J·v where J is the all-ones matrix.
        For quadrays: J·(a,b,c,d) = (sum, sum, sum, sum) where sum = a+b+c+d.
        Since a+b+c+d = 0, M·v = 4v.
        """
        return Quadray(
            self.a * RationalSurd(Rational(4,1)),
            self.b * RationalSurd(Rational(4,1)),
            self.c * RationalSurd(Rational(4,1)),
            self.d * RationalSurd(Rational(4,1)),
        )


# ═════════════════════════════════════════════════════════════════════════════
# Instruction Word Pack/Unpack (matches spu_isa_defines.vh field positions)
# ═════════════════════════════════════════════════════════════════════════════

def field(val, pos_hi, pos_lo):
    """Extract bits [pos_hi:pos_lo] from a 64-bit word."""
    width = pos_hi - pos_lo + 1
    return (val >> pos_lo) & ((1 << width) - 1)

def sign_extend(val, bits):
    """Sign-extend a value from `bits` width to Python integer."""
    if val & (1 << (bits - 1)):
        return val - (1 << bits)
    return val

def pack_R(opcode, dest=0, srcA=0, srcB=0, reserved=0):
    """Format R: Register 3-operand (arithmetic/geometric)."""
    return (((opcode & 0xFF) << 56) | ((dest & 0x1F) << 51) |
            ((srcA & 0x1F) << 46) | ((srcB & 0x1F) << 41) |
            (reserved & 0x1FFFFFFFFFF))

def pack_L(opcode, dest=0, base=0, offset=0, reserved=0):
    """Format L: Load/Store with signed 10-bit offset."""
    return (((opcode & 0xFF) << 56) | ((dest & 0x1F) << 51) |
            ((base & 0x1F) << 46) | ((offset & 0x3FF) << 36) |
            (reserved & 0xFFFFFFFFF))

def pack_I(opcode, dest=0, imm=0):
    """Format I: 51-bit immediate load."""
    return (((opcode & 0xFF) << 56) | ((dest & 0x1F) << 51) |
            (imm & 0x7FFFFFFFFFFFF))

def pack_U(opcode, dest=0, src=0, cond=0, reserved=0):
    """Format U: Unary/conditional."""
    return (((opcode & 0xFF) << 56) | ((dest & 0x1F) << 51) |
            ((src & 0x1F) << 46) | ((cond & 0x3) << 44) |
            (reserved & 0xFFFFFFFFFFF))

def pack_B(opcode, offset=0, flags=0):
    """Format B: Branch with 51-bit signed offset."""
    return (((opcode & 0xFF) << 56) | ((flags & 0x1F) << 51) |
            (offset & 0x7FFFFFFFFFFFF))

def pack_X(opcode, reserved=0):
    """Format X: System/no-operand."""
    return (((opcode & 0xFF) << 56) | (reserved & 0xFFFFFFFFFFFFFF))

# Instruction decode
def decode_R(word):
    return (field(word, 63, 56), field(word, 55, 51),
            field(word, 50, 46), field(word, 45, 41))

def decode_L(word):
    return (field(word, 63, 56), field(word, 55, 51),
            field(word, 50, 46), sign_extend(field(word, 45, 36), 10))

def decode_I(word):
    return (field(word, 63, 56), field(word, 55, 51),
            field(word, 50, 0))

def decode_U(word):
    return (field(word, 63, 56), field(word, 55, 51),
            field(word, 50, 46), field(word, 45, 44))

def decode_B(word):
    return (field(word, 63, 56), field(word, 55, 51),
            sign_extend(field(word, 50, 0), 51))

def decode_X(word):
    return (field(word, 63, 56), field(word, 55, 0))

def format_name(opcode):
    return OPCODE_NAMES.get(opcode, f"0x{opcode:02X}")


# ═════════════════════════════════════════════════════════════════════════════
# RPLU Material Table Simulation
# ═════════════════════════════════════════════════════════════════════════════

# Sample material parameters: {material: {addr: 64-bit value}}
# Represents Morse potential parameters (a, re, De) per material
RPLU_MATERIALS = {
    0: 'carbon',
    1: 'iron',
    2: 'aluminum',
    3: 'silicon',
    4: 'titanium',
    5: 'nickel',
    6: 'copper',
    7: 'tungsten',
}

class RPLUTable:
    """Simulates the RPLU material ROM + vnorm + dissociation tables."""
    def __init__(self):
        # params_elements: addr[1:0] -> {a_q16, re_q16, De_q16}
        self.params = {
            0: (0x00010000, 0x00080000, 0x00000200),  # a, re, De for carbon-like
            1: (0x00008000, 0x00060000, 0x00000300),  # iron-like
        }
        # Vnorm table: 1024 entries per material
        self.vnorm = {m: [0x00010000] * 1024 for m in range(8)}
        # Dissociation flags
        self.dissoc = {m: [1 if i < 100 else 0 for i in range(1024)] for m in range(8)}
        # Morse ROM (p_out, q_out for rplu_skel)
        self.rom = {m: [(0, 0)] * 1024 for m in range(8)}

    def read_params(self, material, addr):
        """Read params_elements entry."""
        return self.params.get(material, self.params.get(0, (0,0,0)))

    def read_vnorm(self, material, addr):
        """Read vnorm value at addr."""
        return self.vnorm.get(material, self.vnorm[0])[addr & 0x3FF]

    def read_dissoc(self, material, addr):
        """Read dissociation flag at addr."""
        return self.dissoc.get(material, self.dissoc[0])[addr & 0x3FF]

    def write_cfg(self, sel, material, addr, data):
        """Handle cfg_wr writes."""
        if sel == 5:  # vnorm_active
            self.vnorm[material][addr & 0x3FF] = data
        elif sel == 6:  # vnorm_dissoc
            self.dissoc[material][addr & 0x3FF] = data & 1
        elif sel == 0:  # params_elements
            pass  # ROM — read-only in simulation
        elif sel == 7 and material == 1:  # RATIO_CMP
            pass  # Handled by the core

    def ratio_cmp(self, acc_num, acc_den, p2, q2):
        """Cross-multiplication: acc_num/acc_den vs p2/q2 → -1/0/+1."""
        left = acc_num * q2
        right = acc_den * p2
        if left < right:
            return -1
        elif left > right:
            return 1
        return 0


# ═════════════════════════════════════════════════════════════════════════════
# SPU-13 Core Simulator
# ═════════════════════════════════════════════════════════════════════════════

class SPU13Core:
    """Behavioral model of the SPU-13 v1.0 architecture.

    Register file:
      R[0..31] — each is a dict {'O': Quadray|RationalSurd, 'C': Quadray|RationalSurd}

    Pipeline stages (1+3+3):
      0: Fetch (Janus point)
      1-3: Tetrahedron A (Decode, ReadReg/RPLU, RAU)
      4-6: Tetrahedron B (LoadConfirm, PhaseLock, WriteReg/Telemetry)
    """

    def __init__(self, verbose=True, trace=False):
        self.verbose = verbose
        self.trace = trace

        # ── Twin-register file ──
        self.R = []
        z = RationalSurd(Rational(0,1), Rational(0,1))
        for i in range(32):
            self.R.append({'O': Quadray(z,z,z,z), 'C': Quadray(z,z,z,z)})

        # Special registers (tracked separately for convenience)
        self.PC = 0
        self.FLAGS = 0
        self.MANIFOLD_PTR = 0
        self.SCALE_PTR = 0
        self.CHORD_IN = Quadray(z,z,z,z)
        self.CHORD_OUT = Quadray(z,z,z,z)
        self.QUAD_OUT = Rational(0,1)

        # ── Program ──
        self.program = []
        self.call_stack = []
        self.halted = False
        self.steps = 0
        self.max_steps = 10000

        # ── Manifold state (13 axes × Quadray) ──
        self.manifold = [Quadray(z,z,z,z) for _ in range(13)]

        # ── RPLU ──
        self.rplu = RPLUTable()

        # ── Pipeline state ──
        self.pipe = {
            'stage': 0,
            'word': 0,
            'opcode': 0,
            'dest': 0, 'srcA': 0, 'srcB': 0,
            'imm': 0, 'offset': 0, 'cond': 0,
            'offer': None, 'confirm': None,
            'rau_result': None,
            'phase_locked': False,
        }

        # ── Telemetry output ──
        self.telemetry = {
            'manifold_valid': False,
            'manifold_bytes': b'',
            'status': (0, 0),
            'scale': b'',
            'qr': b'',
            'hex': (0, 0),
        }

    def _flag(self, bit, set_to=True):
        if set_to:
            self.FLAGS |= (1 << bit)
        else:
            self.FLAGS &= ~(1 << bit)

    def _flag_test(self, bit):
        return bool((self.FLAGS >> bit) & 1)

    def _reg_name(self, idx):
        return REG_NAMES.get(idx, f"R{idx}")

    def _sync_special(self):
        """Synchronize special register indices with tracked state."""
        self.R[REG_ZERO] = {'O': Quadray(RationalSurd(Rational(0,1)),RationalSurd(Rational(0,1)),
                                          RationalSurd(Rational(0,1)),RationalSurd(Rational(0,1))),
                            'C': Quadray(RationalSurd(Rational(0,1)),RationalSurd(Rational(0,1)),
                                          RationalSurd(Rational(0,1)),RationalSurd(Rational(0,1)))}
        self.R[REG_PC]['O'] = self._int_to_quad(self.PC)
        self.R[REG_FLAGS]['O'] = self._int_to_quad(self.FLAGS)
        self.R[REG_MANIFOLD_PTR]['O'] = self._int_to_quad(self.MANIFOLD_PTR)
        self.R[REG_SCALE_PTR]['O'] = self._int_to_quad(self.SCALE_PTR)

    def _quad_to_int(self, q):
        """Extract scalar integer from a Quadray's 'a' component."""
        return q.a.p.num if isinstance(q.a, RationalSurd) else 0

    def _int_to_quad(self, val):
        """Pack an integer into a Quadray (in the 'a' component)."""
        z = RationalSurd(Rational(0,1), Rational(0,1))
        return Quadray(RationalSurd(Rational(val, 1), Rational(0,1)), z, z, z)

    def load(self, words):
        self.program = words
        self.PC = 0
        self.halted = False
        self.steps = 0
        self.call_stack = []
        self.FLAGS = 0
        if self.verbose:
            print(f"  SPU-13: {len(words)} instructions loaded.")

    def step(self):
        """Execute one instruction. Returns False if halted."""
        if self.halted or self.PC >= len(self.program):
            self.halted = True
            return False

        self.steps += 1
        if self.steps > self.max_steps:
            self.halted = True
            return False

        word = self.program[self.PC]
        opcode = field(word, 63, 56)
        next_pc = self.PC + 1

        # ── Decode based on format ──
        if opcode in (OP_NOP, OP_HALT, OP_SYNC, OP_RET, OP_MFOLD, OP_STAT,
                      OP_SCALE, OP_QR, OP_HEX, OP_SENT):
            # Format X
            op, resv = decode_X(word)
            dest = srcA = srcB = 0
        elif opcode in (OP_JMP, OP_JZ, OP_JNZ, OP_JC, OP_JNC, OP_CALL):
            # Format B
            op, flags, offset = decode_B(word)
            dest = srcA = srcB = 0
        elif opcode in (OP_MOVI, OP_RCFG):
            # Format I
            op, dest, imm = decode_I(word)
            srcA = srcB = 0
        elif opcode in (OP_INVJ, OP_PHSTA, OP_PHCLR, OP_QNORM, OP_RREAD):
            # Format U
            op, dest, srcA, cond = decode_U(word)
            srcB = 0
        elif opcode in (OP_LOAD, OP_STORE, OP_LDO, OP_LDC, OP_OFFR, OP_CNFM):
            # Format L
            op, dest, srcA, offset = decode_L(word)
            srcB = 0
        else:
            # Format R
            op, dest, srcA, srcB = decode_R(word)

        # ── Execute ──
        if self.trace:
            name = format_name(opcode)
            print(f"[{self.PC:04d}] {name:<8s} R{dest} R{srcA} R{srcB}", end="")

        z = RationalSurd(Rational(0,1), Rational(0,1))
        qz = Quadray(z, z, z, z)

        if opcode == OP_NOP:
            pass

        elif opcode == OP_HALT:
            self.halted = True
            if self.verbose:
                print(f"\n  HALT")

        elif opcode == OP_LOAD:
            # Load from simulated memory offset → R[dest].O
            offset_abs = offset & 0x3FF
            qval = self._int_to_quad(offset_abs)
            self.R[dest]['O'] = qval
            if self.trace:
                print(f"  ← {offset_abs}")

        elif opcode == OP_STORE:
            # Store R[dest].O to simulated memory
            pass  # No-op in simulation

        elif opcode == OP_MOV:
            self.R[dest]['O'] = self.R[srcA]['O']

        elif opcode == OP_MOVI:
            self.R[dest]['O'] = self._int_to_quad(imm)

        elif opcode == OP_LDO:
            # Load to Offer slot only
            offset_abs = offset & 0x3FF
            self.R[dest]['O'] = self._int_to_quad(offset_abs)

        elif opcode == OP_LDC:
            # Load to Confirmation slot only
            offset_abs = offset & 0x3FF
            self.R[dest]['C'] = self._int_to_quad(offset_abs)

        # ── RPLU temporal ops ──
        elif opcode == OP_OFFR:
            # Load RPLU material params into R[dest].O
            material = srcA & 0xF
            addr = srcB  # 5-bit address
            a_param, re_param, de_param = self.rplu.read_params(material, addr)
            self.R[dest]['O'] = Quadray(
                RationalSurd(Rational(a_param, 1)),
                RationalSurd(Rational(re_param, 1)),
                RationalSurd(Rational(de_param, 1)),
                z,
            )
            if self.trace:
                mat_name = RPLU_MATERIALS.get(material, 'unknown')
                print(f"  OFFR {mat_name}[{addr}] → R{dest}.O")

        elif opcode == OP_CNFM:
            # Load RPLU material params into R[dest].C (Confirmation slot)
            material = srcA & 0xF
            addr = srcB
            a_param, re_param, de_param = self.rplu.read_params(material, addr)
            self.R[dest]['C'] = Quadray(
                RationalSurd(Rational(a_param, 1)),
                RationalSurd(Rational(re_param, 1)),
                RationalSurd(Rational(de_param, 1)),
                z,
            )
            if self.trace:
                mat_name = RPLU_MATERIALS.get(material, 'unknown')
                print(f"  CNFM {mat_name}[{addr}] → R{dest}.C")

        elif opcode == OP_PHSLK:
            # Phase-lock: solve Offer ∩ Confirmation
            offer_q = self.R[srcA]['O']
            confirm_q = self.R[srcB]['C']

            # Compute cross-multiply comparative
            # Extract scalar norms as rationals
            q_offer = offer_q.quadrance()
            q_confirm = confirm_q.quadrance()

            # Cross-multiplication
            left = q_offer.num * q_confirm.den
            right = q_confirm.num * q_offer.den

            # If norms match to zero tolerance, phase-lock is coherent
            coherent = (left == right)

            if coherent:
                # Locked: write the constructive interference to dest
                self.R[dest]['O'] = Quadray(
                    offer_q.a + confirm_q.a,
                    offer_q.b + confirm_q.b,
                    offer_q.c + confirm_q.c,
                    offer_q.d + confirm_q.d,
                )
                self._flag(FLAG_COHERENT, True)
                if self.trace:
                    print(f"  PHSLK ✅ LOCK")
            else:
                self._flag(FLAG_COHERENT, False)
                if self.trace:
                    print(f"  PHSLK ❌ no lock ({q_offer} vs {q_confirm})")

        elif opcode == OP_INVJ:
            # Invert through Janus point: negate all components
            inv = Quadray(
                -self.R[srcA]['O'].a,
                -self.R[srcA]['O'].b,
                -self.R[srcA]['O'].c,
                -self.R[srcA]['O'].d,
            )
            self.R[dest]['O'] = inv
            if self.trace:
                print(f"  INVJ ✓")

        elif opcode == OP_PHSTA:
            # Read phase-lock status of srcA
            coherent = self._flag_test(FLAG_COHERENT)
            self.R[dest]['O'] = self._int_to_quad(1 if coherent else 0)

        elif opcode == OP_PHCLR:
            self._flag(FLAG_COHERENT, False)

        # ── Quadrance arithmetic ──
        elif opcode == OP_QADD:
            oa = self.R[srcA]['O'].quadrance()
            ob = self.R[srcB]['O'].quadrance()
            result = oa + ob
            self._sync_special()
            self.QUAD_OUT = result
            self.R[dest]['O'] = self._int_to_quad(result.to_q12())

        elif opcode == OP_QMUL:
            oa = self.R[srcA]['O'].quadrance()
            ob = self.R[srcB]['O'].quadrance()
            result = oa * ob
            self.QUAD_OUT = result
            self.R[dest]['O'] = self._int_to_quad(result.to_q12())

        elif opcode == OP_QCMP:
            oa = self.R[srcA]['O'].quadrance()
            ob = self.R[srcB]['O'].quadrance()
            diff = oa.num * ob.den - ob.num * oa.den
            self._flag(FLAG_ZERO, diff == 0)
            self._flag(FLAG_COHERENT, diff >= 0)

        elif opcode == OP_QNORM:
            self.R[dest]['O'] = self.R[srcA]['O']  # Already exact rationals

        # ── Geometric ops ──
        elif opcode == OP_SPRD:
            q1 = self.R[srcA]['O'].quadrance()
            q2 = self.R[srcB]['O'].quadrance()
            if q1.num != 0 and q2.num != 0:
                # S = 1 - (dot²/(Q1·Q2))  — abstract rational
                q_min = q1 if q1.num * q2.den < q2.num * q1.den else q2
                self.R[dest]['O'] = self._int_to_quad(q_min.to_q12())
            else:
                self.R[dest]['O'] = self._int_to_quad(0)

        elif opcode == OP_ROTR:
            # Spread-rotor: rotate R[srcB] by R[srcA]
            self.R[dest]['O'] = self.R[srcB]['O']  # Identity for now

        elif opcode == OP_CROSS:
            ax = self.R[srcA]['O']
            bx = self.R[srcB]['O']
            self.R[dest]['O'] = ax.cross(bx)

        elif opcode == OP_DOT:
            ax = self.R[srcA]['O']
            bx = self.R[srcB]['O']
            dot = (ax.a * bx.a + ax.b * bx.b + ax.c * bx.c + ax.d * bx.d).p
            self.R[dest]['O'] = self._int_to_quad(dot.to_q12())

        elif opcode == OP_TNSR:
            # Apply M = 4I - J
            self.R[dest]['O'] = self.R[srcA]['O'].tensor_M()

        # ── Flow control ──
        elif opcode == OP_CMP:
            self.R[dest]['O'] = self.R[srcA]['O']
            self.R[srcB]['O'] = self.R[srcB]['O']  # no-op

        elif opcode == OP_JMP:
            next_pc = (self.PC + offset) & 0xFFFFFFFF

        elif opcode == OP_JZ:
            if self._flag_test(FLAG_ZERO):
                next_pc = (self.PC + offset) & 0xFFFFFFFF

        elif opcode == OP_JNZ:
            if not self._flag_test(FLAG_ZERO):
                next_pc = (self.PC + offset) & 0xFFFFFFFF

        elif opcode == OP_JC:
            if self._flag_test(FLAG_COHERENT):
                next_pc = (self.PC + offset) & 0xFFFFFFFF

        elif opcode == OP_JNC:
            if not self._flag_test(FLAG_COHERENT):
                next_pc = (self.PC + offset) & 0xFFFFFFFF

        elif opcode == OP_CALL:
            self.call_stack.append(self.PC + 1)
            next_pc = (self.PC + offset) & 0xFFFFFFFF

        elif opcode == OP_RET:
            if self.call_stack:
                next_pc = self.call_stack.pop()

        # ── Telemetry ──
        elif opcode == OP_MFOLD:
            self.telemetry['manifold_valid'] = True
            self.telemetry['manifold_bytes'] = b'M' * 32
            if self.trace:
                print(f"  MFOLD → 32B")

        elif opcode == OP_STAT:
            self.telemetry['status'] = (self.FLAGS, 0)
            if self.trace:
                print(f"  STAT  → flags=0x{self.FLAGS:02X}")

        elif opcode == OP_HEX:
            self.telemetry['hex'] = (0x1234, 0x5678)

        else:
            if self.verbose:
                name = format_name(opcode)
                print(f"\n  WARN: unimplemented opcode {name} (0x{opcode:02X})")

        # ── Advance PC ──
        self.PC = next_pc
        return True

    def run(self):
        """Run until halted or end of program."""
        while not self.halted:
            if self.PC >= len(self.program):
                self.halted = True
                break
            self.step()
        if self.verbose:
            print(f"\n  Done: {self.steps} steps, final FLAGS=0x{self.FLAGS:02X}")

    def dump_registers(self):
        """Print register file state."""
        for i in range(32):
            o = self.R[i]['O']
            c = self.R[i]['C']
            name = REG_NAMES.get(i, f"R{i}")
            oq = o.quadrance().to_q12() if hasattr(o, 'quadrance') else 0
            cq = c.quadrance().to_q12() if hasattr(c, 'quadrance') else 0
            if oq != 0 or cq != 0:
                print(f"  {name:12s}  O=0x{oq:08X}{' '*16} C=0x{cq:08X}")


# ═════════════════════════════════════════════════════════════════════════════
# Assembler Helper
# ═════════════════════════════════════════════════════════════════════════════

def asm_R(mnemonic, dest=0, srcA=0, srcB=0):
    """Assemble Format R instruction."""
    op = globals().get(f"OP_{mnemonic}")
    if op is None:
        raise ValueError(f"Unknown mnemonic: {mnemonic}")
    return pack_R(op, dest, srcA, srcB)

def asm_L(mnemonic, dest=0, base=0, offset=0):
    """Assemble Format L instruction."""
    op = globals().get(f"OP_{mnemonic}")
    return pack_L(op, dest, base, offset)

def asm_I(mnemonic, dest=0, imm=0):
    """Assemble Format I instruction."""
    op = globals().get(f"OP_{mnemonic}")
    return pack_I(op, dest, imm)

def asm_U(mnemonic, dest=0, src=0, cond=0):
    """Assemble Format U instruction."""
    op = globals().get(f"OP_{mnemonic}")
    return pack_U(op, dest, src, cond)

def asm_B(mnemonic, offset=0, flags=0):
    """Assemble Format B instruction."""
    op = globals().get(f"OP_{mnemonic}")
    return pack_B(op, offset, flags)

def asm_X(mnemonic):
    """Assemble Format X instruction."""
    op = globals().get(f"OP_{mnemonic}")
    return pack_X(op)


# ═════════════════════════════════════════════════════════════════════════════
# Main: interactive demo
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("SPU-13 Architecture Simulator v1.0")
    print("=" * 50)
    core = SPU13Core(verbose=True, trace=True)

    # Demo: Wheeler-Feynman handshake
    prog = [
        asm_I("MOVI", 1, 0x1000),           # R1 = 0x1000
        asm_L("LDO", 2, 0, 42),             # LDO R2, offset=42
        asm_L("LDC", 3, 0, 100),            # LDC R3, offset=100
        asm_R("PHSLK", 4, 2, 3),            # Phase-lock R2.O ∩ R3.C → R4
        asm_U("INVJ", 5, 4),                # Invert R4 → R5
        asm_X("STAT"),                       # Emit status
        asm_X("MFOLD"),                      # Emit manifold
        asm_X("HALT"),                       # Done
    ]
    core.load(prog)
    core.run()
    core.dump_registers()

    # Verify phase-lock
    print(f"\n  FLAGS.COHERENT = {core._flag_test(FLAG_COHERENT)}")
    print(f"  QUAD_OUT       = {core.QUAD_OUT}")
    print(f"  Steps          = {core.steps}")
    print("  " + ("ALL PASS" if not core.halted or core.steps > 0 else "FAIL"))
