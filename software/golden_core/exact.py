"""Exact arithmetic in Q(sqrt(5)), kept separate from the SPU profiles."""

from dataclasses import dataclass
from fractions import Fraction
from typing import SupportsInt


@dataclass(frozen=True)
class Q5:
    """Canonical ``a + b*sqrt(5)`` with rational coefficients."""

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "a", Fraction(self.a))
        object.__setattr__(self, "b", Fraction(self.b))

    @classmethod
    def from_phi(cls, a: SupportsInt | Fraction, b: SupportsInt | Fraction) -> "Q5":
        """Convert ``a + b*phi`` to the sqrt(5) basis."""
        a, b = Fraction(a), Fraction(b)
        return cls(a + b / 2, b / 2)

    def to_phi(self) -> tuple[Fraction, Fraction]:
        """Return canonical coefficients ``(c,d)`` for ``c + d*phi``."""
        return self.a - self.b, 2 * self.b

    def __add__(self, other: "Q5") -> "Q5":
        if not isinstance(other, Q5):
            return NotImplemented
        return Q5(self.a + other.a, self.b + other.b)

    def __sub__(self, other: "Q5") -> "Q5":
        if not isinstance(other, Q5):
            return NotImplemented
        return Q5(self.a - other.a, self.b - other.b)

    def __neg__(self) -> "Q5":
        return Q5(-self.a, -self.b)

    def __mul__(self, other: "Q5") -> "Q5":
        if not isinstance(other, Q5):
            return NotImplemented
        return Q5(self.a * other.a + 5 * self.b * other.b,
                  self.a * other.b + self.b * other.a)

    def conjugate(self) -> "Q5":
        return Q5(self.a, -self.b)

    def norm(self) -> Fraction:
        return self.a * self.a - 5 * self.b * self.b

    def inverse(self) -> "Q5":
        norm = self.norm()
        if norm == 0:
            raise ZeroDivisionError("zero has no inverse in Q(sqrt(5))")
        return Q5(self.a / norm, -self.b / norm)

    def __truediv__(self, other: "Q5") -> "Q5":
        if not isinstance(other, Q5):
            return NotImplemented
        return self * other.inverse()

    def sign(self) -> int:
        """Sign in the positive real embedding, using rational squares only."""
        a, b = self.a, self.b
        if b == 0:
            return (a > 0) - (a < 0)
        if a == 0:
            return (b > 0) - (b < 0)
        if a > 0 and b > 0:
            return 1
        if a < 0 and b < 0:
            return -1
        if a > 0:  # a - |b|*sqrt(5)
            return (a * a > 5 * b * b) - (a * a < 5 * b * b)
        # -|a| + b*sqrt(5)
        return (5 * b * b > a * a) - (5 * b * b < a * a)

    def __lt__(self, other: "Q5") -> bool:
        if not isinstance(other, Q5):
            return NotImplemented
        return (self - other).sign() < 0

    def __le__(self, other: "Q5") -> bool:
        if not isinstance(other, Q5):
            return NotImplemented
        return (self - other).sign() <= 0


ZERO = Q5()
ONE = Q5(Fraction(1))
PHI = Q5.from_phi(0, 1)

