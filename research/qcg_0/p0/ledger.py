"""Instrumented exact rational `Q` (contract §2/§3). Counting classification is syntactic, never value-based."""
from math import gcd
from account import Ledger, bn, _p2
from events import Invalid, Refusal


class Q:
    """Canonical rational (reduced n, positive d). All counting rules are the contract's."""
    __slots__ = ("n", "d", "L")

    def __init__(self, n, d, L):
        self.n, self.d, self.L = n, d, L

    @staticmethod
    def imp(n, d, L, name):
        """Import a source/constant rational: reduced and within the reduced bound (administrative)."""
        if d <= 0 or gcd(abs(n), d) != 1:
            raise Invalid("MALFORMED", "import.%s" % name)
        for v, sub in ((n, "e1"), (d, "e2")):
            L.peak("W_peak_red", abs(v).bit_length())
            if abs(v).bit_length() > L.profile.red:
                raise Refusal("ARITH_LIMIT", "%s.%s.import.%s.%s" % (L.arm, L.phase, name, sub))
        return Q(n, d, L)

    def pair(self):
        return [self.n, self.d]

    def __neg__(self):  # free, uncounted
        return Q(-self.n, self.d, self.L)

    def _norm(self, n, d):
        L = self.L
        L.c["G_calls"] += 1
        L.c["G_bits"] += max(bn(n), bn(d))
        g = gcd(abs(n), d) if n else d
        n, d = n // g, d // g
        L.check(n, "red", "e1")
        L.check(d, "red", "e2")
        return Q(n, d, L)

    def __mul__(self, o):
        L = self.L
        L.tick()
        L.c["M"] += 1
        L.c["M2"] += _p2(self) or _p2(o)
        L.c["W_bits"] += bn(self.n) * bn(o.n) + bn(self.d) * bn(o.d)
        n = self.n * o.n
        L.check(n, "raw", "r1")
        d = self.d * o.d
        L.check(d, "raw", "r2")
        return self._norm(n, d)

    def _addsub(self, o, sign):
        L = self.L
        L.tick()
        L.c["A"] += 1
        L.c["W_bits"] += bn(self.n) * bn(o.d) + bn(o.n) * bn(self.d) + bn(self.d) * bn(o.d)
        r1 = self.n * o.d
        L.check(r1, "raw", "r1")
        r2 = o.n * self.d
        L.check(r2, "raw", "r2")
        r3 = r1 + sign * r2
        L.check(r3, "raw", "r3")
        r4 = self.d * o.d
        L.check(r4, "raw", "r4")
        return self._norm(r3, r4)

    def __add__(self, o):
        return self._addsub(o, 1)

    def __sub__(self, o):
        return self._addsub(o, -1)

    def __truediv__(self, o):
        L = self.L
        L.tick()
        if o.n == 0:  # administrative zero-divisor guard: no ledger entry, not a counted operation
            Ledger.GRAND[0] -= 1
            raise Invalid("DIV_ZERO", L.event())
        L.c["D"] += 1
        L.c["W_bits"] += bn(self.n) * bn(o.d) + bn(self.d) * bn(o.n)
        r1 = self.n * o.d
        L.check(r1, "raw", "r1")
        r2 = self.d * o.n
        L.check(r2, "raw", "r2")
        if r2 < 0:
            r1, r2 = -r1, -r2
        return self._norm(r1, r2)

    def twice(self):   # literal x2 (S): parity normalization, no gcd
        L = self.L
        L.tick()
        L.c["S"] += 1
        n, d = (0, 1) if self.n == 0 else ((self.n, self.d // 2) if self.d % 2 == 0 else (2 * self.n, self.d))
        L.check(n, "red", "e1")
        L.check(d, "red", "e2")
        return Q(n, d, L)

    def half(self):    # literal /2 (S)
        L = self.L
        L.tick()
        L.c["S"] += 1
        n, d = (0, 1) if self.n == 0 else ((self.n // 2, self.d) if self.n % 2 == 0 else (self.n, 2 * self.d))
        L.check(n, "red", "e1")
        L.check(d, "red", "e2")
        return Q(n, d, L)

    def cmp(self, o):  # semantic comparison of two rationals: -1, 0, 1
        L = self.L
        L.tick()
        L.c["K"] += 1
        L.c["W_bits"] += bn(self.n) * bn(o.d) + bn(o.n) * bn(self.d)
        r1 = self.n * o.d
        L.check(r1, "raw", "r1")
        r2 = o.n * self.d
        L.check(r2, "raw", "r2")
        return (r1 > r2) - (r1 < r2)

    def sgn(self):     # semantic sign/zero test against 0: no products, no checks
        L = self.L
        L.tick()
        L.c["K"] += 1
        return (self.n > 0) - (self.n < 0)


def lit(n, L, d=1):
    """A literal constant of the algorithm text or an index/degree constant: uncounted, canonical."""
    g = gcd(abs(n), d) or 1
    return Q(n // g, d // g, L)
