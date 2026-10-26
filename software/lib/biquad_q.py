"""BQ-0: exact characteristic-zero biquadratic field Q(sqrt3, sqrt5).

Software oracle only. Arbitrary-precision Fractions; no fixed-width/overflow
semantics. NOT A31: A31 = F_p[x,y]/(x^2-3,y^2-5) at p=M31 is a split algebra
with zero divisors (FLAGS.V traps them). Here Q(sqrt3,sqrt5) is a field, so
norm(x)==0 iff x==0 and every nonzero x has an inverse (rational coefficients).
Do not reuse either invertibility contract for the other.

Rational basis  R: [1, s3, s5, s15]
Integral basis  G: [1, s3, phi, s3*phi],  phi=(1+s5)/2  (full ring of integers)
Stored internally in R. R->G: (a-c, b-d, 2c, 2d); G->R: (A+C/2, B+D/2, C/2, D/2).
"""
from fractions import Fraction as Fr


class BQ:
    __slots__ = ("c",)

    def __init__(self, a=0, b=0, c=0, d=0):
        self.c = (Fr(a), Fr(b), Fr(c), Fr(d))

    @classmethod
    def from_golden(cls, A, B, C, D):
        C, D = Fr(C) / 2, Fr(D) / 2
        return cls(Fr(A) + C, Fr(B) + D, C, D)

    def to_golden(self):
        a, b, c, d = self.c
        return (a - c, b - d, 2 * c, 2 * d)

    def is_integral(self):
        return all(t.denominator == 1 for t in self.to_golden())

    def __eq__(self, o):
        return self.c == o.c

    def __hash__(self):
        return hash(self.c)

    def __repr__(self):
        return "BQ(%s,%s,%s,%s)" % self.c

    def __add__(self, o):
        return BQ(*(x + y for x, y in zip(self.c, o.c)))

    def __sub__(self, o):
        return BQ(*(x - y for x, y in zip(self.c, o.c)))

    def __neg__(self):
        return BQ(*(-x for x in self.c))

    def __mul__(self, o):
        a, b, c, d = self.c
        e, f, g, h = o.c
        return BQ(a*e + 3*b*f + 5*c*g + 15*d*h, a*f + b*e + 5*(c*h + d*g),
                  a*g + c*e + 3*(b*h + d*f), a*h + d*e + b*g + c*f)

    def conj(self, k):
        """k=0 id, 1 flip s3, 2 flip s5, 3 flip both."""
        a, b, c, d = self.c
        return BQ(*[(a, b, c, d), (a, -b, c, -d), (a, b, -c, -d), (a, -b, -c, d)][k])

    def norm(self):
        p = self * self.conj(1) * self.conj(2) * self.conj(3)
        assert p.c[1:] == (0, 0, 0)
        return p.c[0]

    def inv(self):
        n = self.norm()
        if n == 0:
            raise ZeroDivisionError("norm 0 (only x == 0 in char 0)")
        r = self.conj(1) * self.conj(2) * self.conj(3)
        return BQ(*(t / n for t in r.c))
