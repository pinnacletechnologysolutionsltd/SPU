"""Exact quadratic fields Q(sqrt d) and exact linear algebra for PHY-R1.

Elements are a + b*sqrt(d) with Fraction coefficients; d = 1 means plain Q.
No floating point anywhere. Sign is decided by integer-square comparison.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt


@dataclass(frozen=True)
class QF:
    a: Fraction
    b: Fraction
    d: int

    def __post_init__(self):
        if self.d < 1 or (self.d > 1 and isqrt(self.d) ** 2 == self.d):
            raise ValueError("d must be 1 or a non-square integer > 1")
        if self.d == 1 and self.b:          # sqrt(1) = 1: keep one canonical form
            object.__setattr__(self, "a", self.a + self.b)
            object.__setattr__(self, "b", Fraction(0))

    @staticmethod
    def of(x, d: int) -> "QF":
        return x if isinstance(x, QF) else QF(Fraction(x), Fraction(0), d)

    def _c(self, o) -> "QF":
        """Coerce o into self's field. Only rationals convert implicitly."""
        o = QF.of(o, self.d)
        if o.d == self.d:
            return o
        if o.b == 0:
            return QF(o.a, Fraction(0), self.d)
        raise ValueError(f"mixed fields Q(sqrt{self.d}) and Q(sqrt{o.d})")

    def _join(self, o) -> "QF":
        """Field for a binary result: a rational self adopts o's field."""
        o = QF.of(o, self.d)
        if o.d != self.d and self.b == 0 and o.b != 0:
            return QF(self.a, Fraction(0), o.d)
        return self

    def __add__(self, o):
        s = self._join(o)
        o = s._c(o)
        return QF(s.a + o.a, s.b + o.b, s.d)

    __radd__ = __add__

    def __neg__(self):
        return QF(-self.a, -self.b, self.d)

    def __sub__(self, o):
        return self + (-QF.of(o, self.d))

    def __rsub__(self, o):
        return self._c(o) - self

    def __mul__(self, o):
        s = self._join(o)
        o = s._c(o)
        return QF(s.a * o.a + s.d * s.b * o.b,
                  s.a * o.b + s.b * o.a, s.d)

    __rmul__ = __mul__

    def inv(self) -> "QF":
        n = self.a * self.a - self.d * self.b * self.b
        if n == 0:
            raise ZeroDivisionError("zero (or zero divisor) in Q(sqrt d)")
        return QF(self.a / n, -self.b / n, self.d)

    def __truediv__(self, o):
        return self * QF.of(o, self.d).inv()

    def is_zero(self) -> bool:
        return self.a == 0 and self.b == 0

    def sign(self) -> int:
        a, b = self.a, self.b
        sa, sb = (a > 0) - (a < 0), (b > 0) - (b < 0)
        if sb == 0 or self.d == 1:
            return (a + b > 0) - (a + b < 0) if self.d == 1 else sa
        if sa == 0 or sa == sb:
            return sb
        return sa if a * a > self.d * b * b else sb


def _rat_sqrt(x: Fraction):
    if x < 0:
        return None
    n, m = isqrt(x.numerator), isqrt(x.denominator)
    return Fraction(n, m) if n * n == x.numerator and m * m == x.denominator else None


def sqrt_in_field(x: QF):
    """Return y in the same field with y*y == x and y >= 0, else None."""
    if x.sign() < 0:
        return None
    if x.b == 0:
        r = _rat_sqrt(x.a)
        if r is not None:
            return QF(r, Fraction(0), x.d)
        if x.d == 1:
            return None
        s = _rat_sqrt(x.a / x.d)  # x = s^2 * d  ->  sqrt = s*sqrt(d)
        return QF(Fraction(0), s, x.d) if s is not None else None
    disc = _rat_sqrt(x.a * x.a - x.d * x.b * x.b)
    if disc is None:
        return None
    for p2 in ((x.a + disc) / 2, (x.a - disc) / 2):
        p = _rat_sqrt(p2)
        if p:
            y = QF(p, x.b / (2 * p), x.d)
            return y if y.sign() >= 0 else -y
    return None


def rank_and_psd(mat):
    """Exact symmetric LDL^T with pivoting on the diagonal.

    Returns (rank, is_psd). Works for QF or Fraction entries.
    """
    a = [row[:] for row in mat]
    n = len(a)
    rank, psd = 0, True
    alive = list(range(n))
    while alive:
        piv = next((i for i in alive if not _zero(a[i][i])), None)
        if piv is None:
            # all remaining diagonals zero: PSD only if remaining block is zero
            if any(not _zero(a[i][j]) for i in alive for j in alive):
                psd = False
                rank += _offdiag_rank(a, alive)
            break
        if _sign(a[piv][piv]) < 0:
            psd = False
        rank += 1
        alive.remove(piv)
        p = a[piv][piv]
        for i in alive:
            f = a[i][piv] / p
            for j in alive:
                a[i][j] = a[i][j] - f * a[piv][j]
    return rank, psd


def _zero(x) -> bool:
    return x.is_zero() if isinstance(x, QF) else x == 0


def _sign(x) -> int:
    return x.sign() if isinstance(x, QF) else (x > 0) - (x < 0)


def _offdiag_rank(a, alive) -> int:
    rows = [[a[i][j] for j in alive] for i in alive]
    return len(nullspace_rank(rows)[1])


def det(mat) -> Fraction:
    """Exact determinant of a rational square matrix (Gaussian elimination)."""
    a = [[Fraction(v) for v in row] for row in mat]
    n, sign, out = len(a), 1, Fraction(1)
    for c in range(n):
        k = next((i for i in range(c, n) if a[i][c] != 0), None)
        if k is None:
            return Fraction(0)
        if k != c:
            a[c], a[k], sign = a[k], a[c], -sign
        out *= a[c][c]
        for i in range(c + 1, n):
            f = a[i][c] / a[c][c]
            a[i] = [x - f * y for x, y in zip(a[i], a[c])]
    return sign * out


def nullspace_rank(rows):
    """Row-reduce exactly. Returns (nullspace basis, pivot columns)."""
    m = [r[:] for r in rows]
    ncol = len(m[0]) if m else 0
    pivots, r = [], 0
    for c in range(ncol):
        k = next((i for i in range(r, len(m)) if not _zero(m[i][c])), None)
        if k is None:
            continue
        m[r], m[k] = m[k], m[r]
        inv = m[r][c].inv() if isinstance(m[r][c], QF) else Fraction(1) / m[r][c]
        m[r] = [v * inv for v in m[r]]
        for i in range(len(m)):
            if i != r and not _zero(m[i][c]):
                f = m[i][c]
                m[i] = [vi - f * vr for vi, vr in zip(m[i], m[r])]
        pivots.append(c)
        r += 1
    free = [c for c in range(ncol) if c not in pivots]
    basis = []
    for fc in free:
        v = [0] * ncol
        v[fc] = 1
        for i, pc in enumerate(pivots):
            v[pc] = -m[i][fc]
        basis.append(v)
    return basis, pivots
