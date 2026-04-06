"""
rational_field.py — Exact surd arithmetic for the sovereign geometry library.

Supports Q(√3), Q(√5), and their compositum Q(√3, √5, √15).
All coefficients are Python fractions.Fraction — zero floating point ever.

An element is:  p + q·√3 + r·√5 + s·√15
where p, q, r, s ∈ ℚ (Fraction).

The basis multiplies as:
  √3·√3  = 3      √5·√5  = 5     √15·√15 = 15
  √3·√5  = √15    √3·√15 = 3√5   √5·√15  = 5√3

Hardware compatibility note:
  The RTL RationalSurd uses integer (a, b) for a + b·√3.
  MultiSurd(p, q) is the exact software superset; use .to_rs() to
  export integer (a, b) for RTL when r == s == 0.

CC0 1.0 Universal.
"""
from __future__ import annotations
from fractions import Fraction

# ── convenience alias ───────────────────────────────────────────────────────
Frac = Fraction


class MultiSurd:
    """
    Element of Q(√3, √5): value = p + q·√3 + r·√5 + s·√15.

    p, q, r, s are Fraction — exact rational arithmetic throughout.
    """

    __slots__ = ('p', 'q', 'r', 's')

    def __init__(self,
                 p: int | Fraction = 0,
                 q: int | Fraction = 0,
                 r: int | Fraction = 0,
                 s: int | Fraction = 0):
        self.p = Frac(p)
        self.q = Frac(q)
        self.r = Frac(r)
        self.s = Frac(s)

    # ── arithmetic ──────────────────────────────────────────────────────────

    def __add__(self, other: MultiSurd | int | Fraction) -> MultiSurd:
        o = _coerce(other)
        return MultiSurd(self.p + o.p, self.q + o.q, self.r + o.r, self.s + o.s)

    def __radd__(self, other) -> MultiSurd:
        return self.__add__(other)

    def __sub__(self, other: MultiSurd | int | Fraction) -> MultiSurd:
        o = _coerce(other)
        return MultiSurd(self.p - o.p, self.q - o.q, self.r - o.r, self.s - o.s)

    def __rsub__(self, other) -> MultiSurd:
        return _coerce(other).__sub__(self)

    def __neg__(self) -> MultiSurd:
        return MultiSurd(-self.p, -self.q, -self.r, -self.s)

    def __mul__(self, other: MultiSurd | int | Fraction) -> MultiSurd:
        o = _coerce(other)
        p, q, r, s = self.p, self.q, self.r, self.s
        e, f, g, h = o.p, o.q, o.r, o.s
        # Basis multiplication:  √3·√3=3, √5·√5=5, √15·√15=15
        #                        √3·√5=√15, √3·√15=3√5, √5·√15=5√3
        return MultiSurd(
            p*e + 3*q*f + 5*r*g + 15*s*h,          # 1 coefficient
            p*f + q*e + 5*r*h + 5*s*g,              # √3 coefficient
            p*g + r*e + 3*q*h + 3*s*f,              # √5 coefficient
            p*h + s*e + q*g + r*f,                  # √15 coefficient
        )

    def __rmul__(self, other) -> MultiSurd:
        return self.__mul__(other)

    def __pow__(self, n: int) -> MultiSurd:
        if n == 0:
            return MultiSurd(1)
        result = MultiSurd(1)
        base = self
        while n > 0:
            if n & 1:
                result = result * base
            base = base * base
            n >>= 1
        return result

    def __truediv__(self, other: int | Fraction) -> MultiSurd:
        """Division by a rational scalar only (not by another MultiSurd)."""
        d = Frac(other)
        return MultiSurd(self.p / d, self.q / d, self.r / d, self.s / d)

    # ── comparisons (only meaningful when r == s == 0) ───────────────────────

    def __eq__(self, other) -> bool:
        o = _coerce(other)
        return self.p == o.p and self.q == o.q and self.r == o.r and self.s == o.s

    def __hash__(self):
        return hash((self.p, self.q, self.r, self.s))

    # ── field operations ────────────────────────────────────────────────────

    def conjugate_3(self) -> MultiSurd:
        """Conjugate over √3: negate the q and s components."""
        return MultiSurd(self.p, -self.q, self.r, -self.s)

    def conjugate_5(self) -> MultiSurd:
        """Conjugate over √5: negate the r and s components."""
        return MultiSurd(self.p, self.q, -self.r, -self.s)

    def norm_sq(self) -> MultiSurd:
        """
        Norm squared in Q(√3,√5): self × conj3(self) × conj5(self) × conj35(self).
        Result is rational (a pure Fraction) for surds that arise geometrically.
        """
        return self * self.conjugate_3() * self.conjugate_5() * (self.conjugate_3().conjugate_5())

    def is_rational(self) -> bool:
        """True if the value is a pure rational (no surd component)."""
        return self.q == 0 and self.r == 0 and self.s == 0

    def is_q3(self) -> bool:
        """True if the value lives in Q(√3) — no √5 or √15 component."""
        return self.r == 0 and self.s == 0

    def to_fraction(self) -> Fraction:
        """Extract rational value — only valid when is_rational() is True."""
        if not self.is_rational():
            raise ValueError(f"Cannot convert non-rational {self!r} to Fraction")
        return self.p

    def approx(self) -> float:
        """Float approximation — for display/debugging only. Never used in computation."""
        return float(self.p) + float(self.q) * 3.0 ** 0.5 + float(self.r) * 5.0 ** 0.5 + float(self.s) * 15.0 ** 0.5

    # ── display ─────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        terms = []
        if self.p:
            terms.append(str(self.p))
        for coeff, label in ((self.q, '√3'), (self.r, '√5'), (self.s, '√15')):
            if coeff:
                if coeff == 1:
                    terms.append(label)
                elif coeff == -1:
                    terms.append(f'-{label}')
                else:
                    terms.append(f'({coeff})·{label}')
        return ' + '.join(terms).replace(' + -', ' - ') if terms else '0'


# ── internal coercion ────────────────────────────────────────────────────────

def _coerce(x) -> MultiSurd:
    if isinstance(x, MultiSurd):
        return x
    return MultiSurd(Frac(x))


# ── named constants ──────────────────────────────────────────────────────────

ZERO  = MultiSurd(0)
ONE   = MultiSurd(1)

# √3 and √5 as MultiSurd elements
S3    = MultiSurd(0, 1)          # √3
S5    = MultiSurd(0, 0, 1)       # √5
S15   = MultiSurd(0, 0, 0, 1)    # √15

# Golden ratio φ = (1 + √5)/2  — fundamental to icosahedron geometry
PHI     = MultiSurd(Frac(1, 2), 0, Frac(1, 2))      # (1 + √5)/2
PHI_SQ  = PHI * PHI                                  # φ² = φ + 1 = (3 + √5)/2
PHI_INV = PHI - 1                                    # 1/φ = φ - 1 = (√5 - 1)/2

# Fundamental spreads — rational (no surd needed)
SPREAD_0   = MultiSurd(0)            # s(0°)  = 0
SPREAD_30  = MultiSurd(Frac(1, 4))   # s(30°) = 1/4
SPREAD_60  = MultiSurd(Frac(3, 4))   # s(60°) = 3/4  — the IVM fundamental
SPREAD_90  = MultiSurd(1)            # s(90°) = 1

# IVM unit quadrance — tetrahedron edge Q in Quadray coords
IVM_Q_UNIT = MultiSurd(2)            # canonical tetrahedron edge Q = 2
